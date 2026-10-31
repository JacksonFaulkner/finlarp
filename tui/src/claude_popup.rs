// `<space>ac` / `<space>as`: a floating Claude Code session over the current
// screen. Claude runs in its own detached tmux session, so closing the popup
// (prefix-d) leaves it running and the next `<space>ac` shows the same conversation.
// Needs fl to run inside tmux; the popup is a `tmux display-popup -E`, which
// blocks fl until it closes.

use std::env;
use std::io;
use std::process::Command;

/// Detached tmux session that holds the Claude Code process.
pub const SESSION: &str = "finlarp-claude";

/// Shows Claude in a popup. `text` is typed into Claude's prompt first
/// (not submitted), for `<space>as`.
pub fn open(text: Option<&str>) -> io::Result<()> {
    if env::var_os("TMUX").is_none() {
        return Err(io::Error::other("Claude popup needs fl run inside tmux"));
    }
    ensure_session()?;
    if let Some(t) = text.map(|t| t.replace(['\n', '\r'], " ")).filter(|t| !t.trim().is_empty()) {
        tmux(&["send-keys", "-t", SESSION, "-l", &t])?;
    }
    // Popup targets the pane fl runs in, so it lands on the right client.
    let mut args = vec!["display-popup", "-E", "-w", "90%", "-h", "90%", "-b", "rounded"];
    let pane = env::var("TMUX_PANE").ok();
    if let Some(p) = pane.as_deref() {
        args.extend(["-t", p]);
    }
    // The popup inherits TMUX from the server; unset it so attach nests cleanly.
    let attach = format!("env -u TMUX tmux attach -t {SESSION}");
    args.push(&attach);
    let status = Command::new("tmux").args(&args).status()?;
    if status.success() {
        Ok(())
    } else {
        Err(io::Error::other("tmux display-popup failed"))
    }
}

/// Starts `claude` in the current directory unless the session already runs.
fn ensure_session() -> io::Result<()> {
    let exists = Command::new("tmux")
        .args(["has-session", "-t", SESSION])
        .status()?
        .success();
    if exists {
        return Ok(());
    }
    let dir = env::current_dir()?;
    let dir = dir.to_string_lossy();
    // Keep Claude out of the alternate screen so its output lands in tmux's
    // scrollback; otherwise there is no history to scroll with copy-mode.
    tmux(&[
        "new-session",
        "-d",
        "-s",
        SESSION,
        "-c",
        &dir,
        "-e",
        "CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1",
        "claude",
    ])
}

fn tmux(args: &[&str]) -> io::Result<()> {
    let out = Command::new("tmux").args(args).output()?;
    if out.status.success() {
        Ok(())
    } else {
        Err(io::Error::other(
            String::from_utf8_lossy(&out.stderr).trim().to_string(),
        ))
    }
}
