// Running the Python side (py/derive/*.py, py/sources/*.py) from the binary, so
// `fl` can build a CANSLIM scorecard or dossier itself instead of leaning on
// nvim to do it first.

use std::path::{Path, PathBuf};
use std::process::Command;

/// Repo root: $FINLARP_PLUGIN_DIR, else the crate's parent (the binary is
/// always built in-tree).
pub fn plugin_dir() -> PathBuf {
    std::env::var_os("FINLARP_PLUGIN_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(".."))
}

/// $FINLARP_PYTHON, else the repo's venv, else `python3` on PATH.
pub fn python(plugin: &Path) -> PathBuf {
    if let Some(p) = std::env::var_os("FINLARP_PYTHON") {
        return PathBuf::from(p);
    }
    let venv = plugin.join(".venv/bin/python");
    if venv.exists() {
        venv
    } else {
        PathBuf::from("python3")
    }
}

/// Runs `script` (repo-relative, e.g. "py/derive/dossier.py") to completion and
/// returns its stdout. Err carries stderr (or the spawn error).
pub fn run_script(script: &str, args: &[&str]) -> Result<String, String> {
    let plugin = plugin_dir();
    let out = Command::new(python(&plugin))
        .arg(plugin.join(script))
        .args(args)
        .current_dir(&plugin)
        .output()
        .map_err(|e| format!("{script}: {e}"))?;
    if out.status.success() {
        Ok(String::from_utf8_lossy(&out.stdout).into_owned())
    } else {
        let err = String::from_utf8_lossy(&out.stderr);
        let tail: Vec<&str> = err.lines().rev().take(6).collect();
        let tail: Vec<&str> = tail.into_iter().rev().collect();
        Err(format!("{script} failed:\n{}", tail.join("\n")))
    }
}

/// Runs a snippet with the repo as cwd (`python -c`), for one-off calls
/// into py/core/db.py such as loading the universe JSON.
pub fn run_code(code: &str) -> Result<(), String> {
    let plugin = plugin_dir();
    let out = Command::new(python(&plugin))
        .args(["-c", code])
        .current_dir(&plugin)
        .output()
        .map_err(|e| format!("python: {e}"))?;
    if out.status.success() {
        Ok(())
    } else {
        Err(format!(
            "python failed:\n{}",
            String::from_utf8_lossy(&out.stderr).trim()
        ))
    }
}
