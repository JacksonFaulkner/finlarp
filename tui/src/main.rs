// Entry point for every finlarp TUI: one binary (`fl`), one DuckDB file,
// several screens (src/screens/*).
//
//   fl                    home menu (same as `fl .`)
//   fl <screen> [arg]     open a screen directly: fl dossier NVDA
//   flags                 --bg/--up/--down #rrggbb: colours to use instead of
//                         the terminal default background; omitted = terminal
//                         default background
//
// Screens: home | chart | portfolio | canslim | dossier | earnings | search
// | universe | diagrams | events | chat. canslim/dossier without a ticker open a ticker picker.
//
// A screen that wants another screen returns a `Route`; `run_session` below
// opens it in-process and returns to the previous screen when it quits (or to
// home, if you started there).
// Env: FINLARP_DB overrides the DuckDB path.

mod app;
mod claude_popup;
mod db;
#[cfg(test)]
mod mock;
mod model;
mod pyrun;
mod remote;
mod screens;
mod tmux_title;
mod ui;

use std::env;
use std::path::PathBuf;

use crate::ui::theme::Theme;

/// Parsed command line.
#[derive(Debug, PartialEq)]
struct Cli {
    bg: Option<String>,
    fg_up: Option<String>,
    fg_down: Option<String>,
    screen: String,
    arg: Option<String>,
}

const SCREENS: &[&str] = &[
    "home",
    "chart",
    "portfolio",
    "canslim",
    "dossier",
    "memory",
    "earnings",
    "search",
    "filings",
    "universe",
    "diagrams",
    "events",
    "chat",
    "candles",
    "intraday",
    "breadth",
    "godel",
    "menu",
    "notes",
    "sources",
    "rows",
    "note",
    "docview",
    "transactions",
    "watchlists",
    "onboard",
    "claude_history",
    "claude_log",
    "keys",
    "video",
    "scratch",
    "figgie",
    "z",
];

/// `[--bg C] [--up C] [--down C] [screen [arg...]]`. No screen or `.` is
/// home; empty colour values are treated as absent (Lua passes "" for "no
/// explicit colour"); the rest of the line is the screen argument, so
/// `fl search t:MRVL guidance` works unquoted.
fn parse_args(args: &[String]) -> Result<Cli, String> {
    let mut cli = Cli {
        bg: None,
        fg_up: None,
        fg_down: None,
        screen: "home".to_string(),
        arg: None,
    };
    let mut rest: Vec<&str> = Vec::new();
    let mut it = args.iter();
    while let Some(a) = it.next() {
        let (flag, inline) = match a.split_once('=') {
            Some((f, v)) if f.starts_with("--") => (f, Some(v.to_string())),
            _ => (a.as_str(), None),
        };
        let slot = match flag {
            "--bg" => &mut cli.bg,
            "--up" => &mut cli.fg_up,
            "--down" => &mut cli.fg_down,
            _ if rest.is_empty() && flag.starts_with("--") => {
                return Err(format!("unknown flag {flag}\n{USAGE}"));
            }
            _ => {
                rest.push(a);
                continue;
            }
        };
        let v = match inline {
            Some(v) => v,
            None => it.next().cloned().ok_or(format!("{flag} needs a value"))?,
        };
        *slot = Some(v).filter(|v| !v.is_empty());
    }
    if let Some((screen, arg)) = rest.split_first() {
        cli.screen = if *screen == "." { "home" } else { screen }.to_string();
        if !SCREENS.contains(&cli.screen.as_str()) {
            return Err(format!("unknown screen {screen:?}\n{USAGE}"));
        }
        let arg = arg.join(" ");
        cli.arg = Some(arg).filter(|a| !a.trim().is_empty());
    }
    Ok(cli)
}

const USAGE: &str = "usage: fl [--bg #rrggbb] [--up #rrggbb] [--down #rrggbb] \
[home|chart|portfolio|canslim|dossier|earnings|search|filings|universe|diagrams|events|chat|candles|intraday|breadth|godel|menu|notes|sources] [arg]";

/// Finlarp's data directory: the repo's `data/` folder, or `FINLARP_DATA`.
/// The Python side resolves the same directory from its own location.
pub fn data_dir() -> PathBuf {
    if let Some(p) = env::var_os("FINLARP_DATA") {
        return PathBuf::from(p);
    }
    let home = env::var_os("HOME").map(PathBuf::from).unwrap_or_default();
    home.join(FINLARP_ROOT).join("data")
}

fn db_path() -> PathBuf {
    if let Some(p) = env::var_os("FINLARP_DB") {
        return PathBuf::from(p);
    }
    data_dir().join("finlarp.duckdb")
}

fn upper(arg: Option<String>) -> Option<String> {
    arg.map(|a| a.trim().to_uppercase())
        .filter(|a| !a.is_empty())
}

/// Builds one screen (running the Python cache build first for canslim/dossier
/// when a ticker is given). No ticker opens a ticker picker.
fn build_screen(
    ctx: &app::Ctx,
    screen: &str,
    arg: Option<String>,
) -> std::io::Result<Box<dyn app::Screen>> {
    use screens::{
        candles, canslim, chart, chat, claude_history, claude_log, diagrams, docview, dossier,
        earnings_report, events, figgie, filings, godel, home, intraday, keys, menu, note, notes,
        onboard,
        pick, portfolio, rebuild, rows, scratch, search, sources, transactions, universe, video,
        watchlists,
    };
    Ok(match (screen, upper(arg.clone())) {
        ("canslim", None) => Box::new(pick::open_symbols(ctx, "canslim")?),
        ("dossier", None) => Box::new(pick::open_symbols(ctx, "dossier")?),
        // Open from cache right away; the screen refreshes itself in the background.
        ("canslim", Some(sym)) => Box::new(canslim::open(ctx, Some(sym))?),
        ("dossier", Some(sym)) => Box::new(dossier::open(ctx, Some(sym))?),
        // memory R&D company page (diagrams Memory tab), cached as "MEM:<TICKER>"
        ("memory", Some(sym)) => Box::new(dossier::open(ctx, Some(format!("MEM:{sym}")))?),
        ("chat", _) => Box::new(chat::open(ctx, arg)?),
        ("candles", _) => Box::new(candles::open(ctx, arg)?),
        ("notes", _) => Box::new(notes::open(ctx, arg)?),
        ("menu", _) => Box::new(menu::open(ctx, arg)?),
        ("godel", _) => Box::new(godel::open(ctx, arg)?),
        ("intraday", _) => Box::new(intraday::open(ctx, arg)?),
        ("breadth", _) => Box::new(intraday::breadth::open(ctx, arg)?),
        ("home", _) => Box::new(home::open(ctx)?),
        ("portfolio", _) => Box::new(portfolio::open(ctx, arg)?),
        ("earnings", _) => Box::new(earnings_report::open(ctx, arg)?),
        ("search", _) => Box::new(search::open(ctx, arg)?),
        ("filings", _) => Box::new(filings::open(ctx, arg)?),
        ("universe", _) => Box::new(universe::open(ctx, arg)?),
        ("events", _) => Box::new(events::open(ctx, arg)?),
        ("diagrams", _) => Box::new(diagrams::open(ctx, arg)?),
        ("video", _) => Box::new(video::open(ctx, arg)?),
        ("sources", _) => Box::new(sources::open(ctx, arg)?),
        ("rows", _) => Box::new(rows::open(ctx, arg)?),
        ("note", _) => Box::new(note::open(ctx, arg)?),
        ("docview", _) => Box::new(docview::open(ctx, arg)?),
        ("transactions", _) => Box::new(transactions::open(ctx, arg)?),
        ("watchlists", _) => Box::new(watchlists::open(ctx, arg)?),
        ("onboard", _) => Box::new(onboard::open(ctx, arg)?),
        ("claude_history", _) => Box::new(claude_history::open(ctx, arg)?),
        ("claude_log", _) => Box::new(claude_log::open(ctx, arg)?),
        ("keys", _) => Box::new(keys::open(ctx, arg)?),
        ("scratch", _) => Box::new(scratch::open(ctx, arg)?),
        ("figgie", _) => Box::new(figgie::open(ctx, arg)?),
        ("z", _) => Box::new(screens::z::open(ctx, arg)?),
        // Reached only through Route::Rebuild (`<space>wq`), not the CLI.
        ("rebuild", _) => Box::new(rebuild::open(ctx, arg)?),
        _ => Box::new(chart::open(ctx, arg)?),
    })
}

/// `fl diagrams pdf [dir]`: exports and exits, no screen.
fn export_diagram_pdfs(ctx: &app::Ctx, arg: &str) -> std::io::Result<()> {
    let dir = Some(arg.trim())
        .filter(|d| !d.is_empty())
        .unwrap_or("diagrams-pdf");
    for p in screens::diagrams::export_pdfs(std::path::Path::new(dir), &ctx.theme)? {
        println!("{p}");
    }
    Ok(())
}

/// Runs a stack of live screens. A screen/picker request pushes the new screen
/// on top (a picker is replaced by what it picks, so back skips it); q/esc in
/// the top screen pops to the one beneath with its state intact. The session
/// ends when the bottom screen quits, or on a nonzero exit code.
/// Window label for a screen: "dossier MRVL", "home".
fn label(screen: &str, arg: Option<&str>) -> String {
    match arg.map(str::trim).filter(|a| !a.is_empty()) {
        Some(a) => format!("{screen} {a}"),
        None => screen.to_string(),
    }
}

/// A screen on the session stack: (screen, is_picker, window label,
/// (screen name, arg) to restart into after a rebuild).
type Entry = (Box<dyn app::Screen>, bool, String, (String, Option<String>));

/// How a session ended: exit with a code, or exec the rebuilt binary into
/// this screen and argument.
enum End {
    Code(i32),
    Restart { screen: String, arg: Option<String> },
}

fn run_session(ctx: &app::Ctx, start: &str, arg: Option<String>) -> std::io::Result<End> {
    use app::Route;
    if start == "diagrams" {
        if let Some(rest) = arg.as_deref().and_then(|a| a.strip_prefix("pdf")) {
            export_diagram_pdfs(ctx, rest)?;
            return Ok(End::Code(0));
        }
    }
    // Restores the tmux window name when this session ends (drop, not exit(),
    // so it runs before main calls process::exit).
    let title = tmux_title::WindowTitle::claim();
    let mut stack: Vec<Entry> = vec![(
        build_screen(ctx, start, arg.clone())?,
        upper(arg.clone()).is_none() && matches!(start, "canslim" | "dossier"),
        label(start, arg.as_deref()),
        (start.to_string(), arg.clone()),
    )];
    // One tape for the whole session: handing off to another screen keeps its data.
    let mut tape = ui::tape::Tape::new();
    loop {
        let top = stack.last_mut().expect("stack never empty here");
        if let Some(t) = &title {
            t.set(&top.2);
        }
        let exit = app::run(top.0.as_mut(), &mut tape, ctx.theme)?;
        let next = match exit.handoff {
            Some(Route::Restart) => {
                // The rebuild screen is on top; restart into the one beneath.
                stack.pop();
                let (screen, arg) = stack
                    .last()
                    .map(|e| e.3.clone())
                    .unwrap_or_else(|| ("home".to_string(), None));
                return Ok(End::Restart { screen, arg });
            }
            Some(Route::Rebuild) => Some(("rebuild".to_string(), None)),
            Some(Route::Screen { screen, arg }) => Some((screen, arg)),
            Some(Route::Picker { screen }) => Some((screen, None)),
            _ => None,
        };
        match next {
            Some((screen, arg)) => {
                let is_picker = upper(arg.clone()).is_none()
                    && matches!(screen.as_str(), "canslim" | "dossier");
                let child_label = label(&screen, arg.as_deref());
                let restart = (screen.clone(), arg.clone());
                let child = match build_screen(ctx, &screen, arg) {
                    Ok(c) => c,
                    // A rebuild that cannot start (no cargo) should not end the session.
                    Err(e) if screen == "rebuild" => {
                        top_flash(&mut stack, e.to_string());
                        continue;
                    }
                    Err(e) => return Err(e),
                };
                if stack.last().is_some_and(|t| t.1) {
                    stack.pop(); // replace the picker with its pick
                }
                stack.push((child, is_picker, child_label, restart));
            }
            None => {
                stack.pop();
                if exit.code != 0 || stack.is_empty() {
                    return Ok(End::Code(exit.code));
                }
            }
        }
    }
}

fn top_flash(stack: &mut [Entry], msg: String) {
    if let Some(top) = stack.last_mut() {
        top.0.set_flash(msg);
    }
}

/// Replaces this process with the freshly built fl: same colour flags, the
/// screen that was open. Only returns if the exec failed.
fn exec_rebuilt(args: &[String], screen: &str, arg: Option<&str>) -> std::io::Error {
    use std::os::unix::process::CommandExt;
    let mut flags: Vec<String> = Vec::new();
    let mut it = args.iter();
    while let Some(a) = it.next() {
        let f = a.split_once('=').map_or(a.as_str(), |(f, _)| f);
        if matches!(f, "--bg" | "--up" | "--down") {
            flags.push(a.clone());
            if f == a {
                flags.extend(it.next().cloned());
            }
        }
    }
    let mut cmd = std::process::Command::new(screens::rebuild::built_binary());
    cmd.args(flags).arg(screen);
    if let Some(a) = arg {
        cmd.args(a.split_whitespace());
    }
    cmd.exec()
}

/// Every launch of `fl` works from the finlarp checkout, whatever directory
/// it was started from (shell, tmux popup, a split). Claude's session
/// inherits this directory too, so it always opens in the repo.
const FINLARP_ROOT: &str = "code/github_repos/finlarp";

fn enter_finlarp_root() {
    if let Some(home) = env::var_os("HOME") {
        let root = PathBuf::from(home).join(FINLARP_ROOT);
        if root.is_dir() {
            let _ = env::set_current_dir(root);
        }
    }
}

fn main() {
    enter_finlarp_root();
    let args: Vec<String> = env::args().skip(1).collect();
    // `fl diagram-mcp`: the MCP server Claude reaches an open diagram through
    // (screens::diagrams_ipc). No screen, no terminal: stdio only.
    if args.first().map(String::as_str) == Some("diagram-mcp") {
        std::process::exit(screens::diagrams_ipc::run_mcp());
    }
    // `fl render-video PAGE... --out DIR`: the diagram pages as HLS video (screens::diagrams_video).
    // Headless: no terminal, so it runs the same way in CI and over ssh.
    // `fl z check FILE...`: validates Z diagram files (screens::z_spec), for Claude to run.
    if args.first().map(String::as_str) == Some("z") && args.get(1).map(String::as_str) == Some("check") {
        std::process::exit(screens::z_spec::run_check(&args[2..]));
    }
    if args.first().map(String::as_str) == Some("z") && args.get(1).map(String::as_str) == Some("render") {
        std::process::exit(screens::z_spec::run_render(&args[2..]));
    }
    if args.first().map(String::as_str) == Some("render-video") {
        std::process::exit(screens::diagrams_video::run_cli(&args[1..]));
    }
    let cli = match parse_args(&args) {
        Ok(c) => c,
        Err(msg) => {
            eprintln!("{msg}");
            std::process::exit(2);
        }
    };
    let ctx = app::Ctx {
        db_path: db_path(),
        theme: Theme::from_args(
            cli.bg.as_deref(),
            cli.fg_up.as_deref(),
            cli.fg_down.as_deref(),
        ),
    };
    // In-place control: another process can move this screen (remote.rs). Failure to listen
    // only costs that feature, so it is not fatal.
    let _ = remote::start(SCREENS);
    let ended = run_session(&ctx, &cli.screen, cli.arg);
    remote::stop();
    match ended {
        Ok(End::Code(code)) => std::process::exit(code),
        Ok(End::Restart { screen, arg }) => {
            let e = exec_rebuilt(&args, &screen, arg.as_deref());
            eprintln!("finlarp: restart failed: {e}");
            std::process::exit(1);
        }
        Err(e) => {
            eprintln!("finlarp: {e}");
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn args(v: &[&str]) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }

    fn cli(v: &[&str]) -> Cli {
        parse_args(&args(v)).expect("parse")
    }

    #[test]
    fn no_args_and_dot_open_home() {
        for v in [&[][..], &["."][..], &["home"][..]] {
            let c = cli(v);
            assert_eq!(c.screen, "home");
            assert_eq!(c.arg, None);
            assert_eq!((c.bg, c.fg_up, c.fg_down), (None, None, None));
        }
    }

    #[test]
    fn flags_screen_and_multiword_arg() {
        let c = cli(&[
            "--bg",
            "#101010",
            "--up=#00ff00",
            "--down",
            "",
            "search",
            "t:MRVL",
            "guidance",
        ]);
        assert_eq!(c.bg.as_deref(), Some("#101010"));
        assert_eq!(c.fg_up.as_deref(), Some("#00ff00"));
        assert_eq!(c.fg_down, None); // empty = absent
        assert_eq!(c.screen, "search");
        assert_eq!(c.arg.as_deref(), Some("t:MRVL guidance"));
    }

    #[test]
    fn symbol_arg() {
        let c = cli(&["canslim", "MU"]);
        assert_eq!(
            (c.screen.as_str(), c.arg.as_deref()),
            ("canslim", Some("MU"))
        );
    }

    #[test]
    fn rejects_unknown_screen_flag_and_missing_value() {
        assert!(parse_args(&args(&["nope"])).is_err());
        assert!(parse_args(&args(&["--wat", "x"])).is_err());
        assert!(parse_args(&args(&["--bg"])).is_err());
    }
}
