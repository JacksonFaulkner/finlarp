// fl-loader: starts the newest good `fl` and rebuilds it in the background.
//
//   fl-loader [screen args...]   run the staged `fl` with the same args
//   fl-loader --rollback         swap staged fl with the previous one (fl.prev)
//   fl-loader --build-worker     (internal) build + promote, detached
//
// Isolation: nothing here links against or runs through `fl`. The Claude
// Code window is a plain tmux window (`just claude`), so a broken `fl` never
// blocks fixing it. `cargo build --release --bin fl-loader` always works.
//
// Why: `fl` is the only thing a popup runs, and a release build takes
// minutes. The loader never waits on cargo. It runs the last *successful*
// build and starts a detached worker that rebuilds `fl` and promotes the
// result by atomic rename. A running `fl` keeps its old inode, so a rebuild
// never changes a screen that is already open, and a failed build never
// replaces the last good binary. The next popup picks up the new code.
//
// Std-only on purpose: this binary compiles in seconds and never pulls in
// DuckDB, so it's safe to rebuild by hand.
//
// Layout: <crate>/target/release/fl (cargo output) -> ~/.cache/finlarp/tui/fl
// (staged, what runs), plus build.log and build.pid next to it.
// Env: FINLARP_TUI_DIR overrides the crate dir (default: compile-time path).

use std::env;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

struct Paths {
    crate_dir: PathBuf,
    built: PathBuf,
    cache: PathBuf,
    current: PathBuf,
    prev: PathBuf,
    log: PathBuf,
    pid: PathBuf,
}

impl Paths {
    fn new() -> Self {
        let crate_dir = env::var_os("FINLARP_TUI_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")));
        let home = env::var_os("HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("."));
        let cache = home.join(".cache/finlarp/tui");
        Paths {
            built: crate_dir.join("target/release/fl"),
            current: cache.join("fl"),
            prev: cache.join("fl.prev"),
            log: cache.join("build.log"),
            pid: cache.join("build.pid"),
            cache,
            crate_dir,
        }
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    let paths = Paths::new();
    if args.first().map(String::as_str) == Some("--build-worker") {
        return build_worker(&paths);
    }
    if let Err(e) = fs::create_dir_all(&paths.cache) {
        eprintln!("fl-loader: cannot create {}: {e}", paths.cache.display());
        return ExitCode::from(1);
    }
    if args.first().map(String::as_str) == Some("--rollback") {
        return rollback(&paths);
    }
    if !paths.current.exists() && !seed(&paths) {
        return ExitCode::from(1);
    }
    spawn_worker_if_idle(&paths);

    match Command::new(&paths.current).args(&args).status() {
        Ok(status) => ExitCode::from(status.code().map(|c| c as u8).unwrap_or(1)),
        Err(e) => {
            eprintln!("fl-loader: cannot run {}: {e}", paths.current.display());
            ExitCode::from(1)
        }
    }
}

/// First run only: nothing staged yet, so there is nothing to run while the
/// worker builds. Use an existing cargo output if there is one, else build
/// in the foreground once.
fn seed(paths: &Paths) -> bool {
    if paths.built.exists() {
        return promote(&paths.built, &paths.current);
    }
    eprintln!("fl-loader: first build of fl, this takes a few minutes...");
    if !cargo_build(paths) {
        eprintln!("fl-loader: cargo build failed, see {}", paths.log.display());
        return false;
    }
    promote(&paths.built, &paths.current)
}

/// Starts a detached worker unless one is already running. Returns at once.
fn spawn_worker_if_idle(paths: &Paths) {
    let running = fs::read_to_string(&paths.pid)
        .ok()
        .and_then(|text| text.trim().parse::<u32>().ok())
        .is_some_and(pid_alive);
    if running {
        return;
    }
    let log = match OpenOptions::new()
        .create(true)
        .append(true)
        .open(&paths.log)
    {
        Ok(f) => f,
        Err(_) => return,
    };
    let Ok(log_err) = log.try_clone() else { return };
    let spawned = Command::new(env::current_exe().unwrap_or_else(|_| "fl-loader".into()))
        .arg("--build-worker")
        .env("FINLARP_TUI_DIR", &paths.crate_dir)
        .stdin(Stdio::null())
        .stdout(Stdio::from(log))
        .stderr(Stdio::from(log_err))
        // own process group: closing the popup or tmux window must not kill the build
        .process_group(0)
        .spawn();
    if let Ok(child) = spawned {
        let _ = fs::write(&paths.pid, child.id().to_string());
        // dropping `child` detaches it; the worker removes the pid file when done
    }
}

/// Swaps `fl` and `fl.prev`. Use it when a successful build crashes at
/// runtime: `fl-loader --rollback`, then fix in the claude window. Rolling
/// back twice gets you the build you started from.
fn rollback(paths: &Paths) -> ExitCode {
    if !paths.prev.exists() {
        eprintln!("fl-loader: no previous build to roll back to");
        return ExitCode::from(1);
    }
    let swap = paths.current.with_extension("swap");
    let ok = fs::rename(&paths.current, &swap)
        .and_then(|_| fs::rename(&paths.prev, &paths.current))
        .and_then(|_| fs::rename(&swap, &paths.prev))
        .is_ok();
    if ok {
        println!("fl-loader: rolled back, staged fl is now the previous build");
        ExitCode::SUCCESS
    } else {
        eprintln!("fl-loader: rollback failed");
        ExitCode::from(1)
    }
}

fn build_worker(paths: &Paths) -> ExitCode {
    // keep the build being replaced as fl.prev, so `--rollback` can undo this one
    let ok = cargo_build(paths) && {
        if paths.current.exists() {
            let _ = fs::copy(&paths.current, &paths.prev);
        }
        promote(&paths.built, &paths.current)
    };
    let _ = fs::remove_file(&paths.pid);
    if ok {
        println!("fl-loader: promoted new fl build");
        ExitCode::SUCCESS
    } else {
        println!("fl-loader: build failed, keeping last good fl");
        ExitCode::from(1)
    }
}

/// Runs `cargo build --release --bin fl`. Output goes to the inherited
/// stdio, which the worker has pointed at build.log.
fn cargo_build(paths: &Paths) -> bool {
    let cargo = cargo_bin();
    let manifest = paths.crate_dir.join("Cargo.toml");
    println!("== {} build --release --bin fl", cargo.display());
    Command::new(cargo)
        .args(["build", "--release", "--bin", "fl", "--manifest-path"])
        .arg(&manifest)
        .stdin(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Tmux popups and detached workers may not inherit the shell PATH, so fall
/// back to rustup's default install location.
fn cargo_bin() -> PathBuf {
    if let Some(home) = env::var_os("HOME") {
        let rustup = PathBuf::from(home).join(".cargo/bin/cargo");
        if rustup.exists() {
            return rustup;
        }
    }
    PathBuf::from("cargo")
}

/// Copies `src` to a temp file beside `dst`, then renames it over `dst`.
/// Rename is atomic, so a running `fl` keeps its inode and nothing ever
/// sees a half-written binary.
fn promote(src: &Path, dst: &Path) -> bool {
    let tmp = dst.with_extension("tmp");
    let copied = fs::copy(src, &tmp).and_then(|_| fs::rename(&tmp, dst));
    match copied {
        Ok(()) => true,
        Err(e) => {
            let _ = writeln!(std::io::stderr(), "fl-loader: promote failed: {e}");
            let _ = fs::remove_file(&tmp);
            false
        }
    }
}

fn pid_alive(pid: u32) -> bool {
    Command::new("kill")
        .arg("-0")
        .arg(pid.to_string())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}
