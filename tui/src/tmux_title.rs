// Window label for `fl` run standalone inside tmux. While a screen is up the
// window reads "◆ fl · dossier MRVL", so the sessionx picker (prefix-w)
// shows which window is finlarp and where in it, even with
// several finlarp windows across sessions. Uses rename-window + @title; the
// window is restored to its original name when the session ends.
//
// Off outside tmux.

use std::env;
use std::process::Command;

/// Dracula purple, the accent sessionx uses for its pointer.
const ICON_COLOR: &str = "\x1b[38;2;189;147;249m";
const RESET: &str = "\x1b[0m";

/// Holds the window's original name; restores it on drop.
pub struct WindowTitle {
    pane: Option<String>,
    original: Option<String>,
}

impl WindowTitle {
    /// Claims the current window's title, or None when not standalone in tmux.
    pub fn claim() -> Option<Self> {
        if env::var_os("TMUX").is_none() {
            return None;
        }
        let pane = env::var("TMUX_PANE").ok();
        let mut args = vec!["display-message", "-p"];
        if let Some(p) = pane.as_deref() {
            args.extend(["-t", p]);
        }
        args.push("#{window_name}");
        let original = tmux_out(&args);
        Some(Self { pane, original })
    }

    /// Sets the window name and its colored @title to "fl · <label>".
    pub fn set(&self, label: &str) {
        let plain = format!("fl · {label}");
        let colored = format!("{ICON_COLOR}◆{RESET} {plain}");
        let _ = self.tmux("rename-window", &[&plain]);
        let _ = self.tmux("set-option", &["-w", "@title", &colored]);
    }

    /// Runs `tmux <sub> -t <pane> <args>`; -t goes after the subcommand.
    fn tmux(&self, sub: &str, args: &[&str]) -> std::io::Result<std::process::ExitStatus> {
        let mut cmd = Command::new("tmux");
        cmd.arg(sub);
        if let Some(p) = self.pane.as_deref() {
            cmd.args(["-t", p]);
        }
        cmd.args(args).status()
    }
}

impl Drop for WindowTitle {
    fn drop(&mut self) {
        let _ = self.tmux("set-option", &["-wu", "@title"]);
        if let Some(name) = self.original.as_deref() {
            let _ = self.tmux("rename-window", &[name]);
        }
    }
}

fn tmux_out(args: &[&str]) -> Option<String> {
    let out = Command::new("tmux").args(args).output().ok()?;
    out.status
        .success()
        .then(|| String::from_utf8_lossy(&out.stdout).trim().to_string())
        .filter(|s| !s.is_empty())
}
