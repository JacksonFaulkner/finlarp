// `<space>ac` / `<space>as`: a floating Claude Code session over the current
// screen. Claude runs in its own detached tmux session, so closing the popup
// (prefix-d) leaves it running and the next `<space>ac` shows the same conversation.
// Needs fl to run inside tmux; the popup is a `tmux display-popup -E`, which
// blocks fl until it closes.
//
// The session lives on its own tmux server (`-L fl-claude`), so the keys in
// KEYS and `jk_bindings` stay off the user's tmux and only apply to this popup.

use std::env;
use std::io::{self, Write};
use std::process::{Command, Stdio};

/// Detached tmux session that holds the Claude Code process.
pub const SESSION: &str = "finlarp-claude";

/// Tmux server socket for the Claude session.
const SOCKET: &str = "fl-claude";

/// Sourced into the Claude server when the session starts (after the copied
/// copy-mode keys, see `source_keys`).
///
/// `jk`: a `j` is held (not shown) until the next key, using the `@fl_jk`
/// flag and the `fl-jk` key table. `k` enters copy-mode (normal mode) and
/// drops the `j`. Any other key sends the `j` first, so typing stays in order.
/// A held `j` that is not followed by a key flushes after 0.25s, so a lone
/// `j` still shows up. In copy-mode, `i` leaves it.
///
/// `g` in copy-mode opens the `fl-g` table: `gg` top, `gh` first non-blank,
/// `gl` last column. Every other key in that table runs its normal copy-mode
/// action, and each key returns the client to copy-mode-vi.
///
/// `space a c` in copy-mode closes the popup (the session keeps running).
const KEYS: &str = r##"
set -g mode-keys vi
bind-key -n j if -F '#{pane_in_mode}' { send-keys -X cursor-down } { set -g @fl_jk 1 ; switch-client -T fl-jk ; run-shell -b 'sleep 0.25 ; c=$(tmux display -p "#{client_name}") ; if [ "$(tmux show -gv @fl_jk)" = 1 ]; then tmux set -g @fl_jk 0 ; tmux send-keys -l j ; tmux switch-client -c "$c" -T root ; fi' }
bind-key -T fl-jk j set -g @fl_jk 1 \; send-keys -l j \; switch-client -T fl-jk \; run-shell -b 'sleep 0.25 ; c=$(tmux display -p "#{client_name}") ; if [ "$(tmux show -gv @fl_jk)" = 1 ]; then tmux set -g @fl_jk 0 ; tmux send-keys -l j ; tmux switch-client -c "$c" -T root ; fi'
bind-key -T fl-jk k copy-mode \; set -g @fl_jk 0 \; switch-client -T root
bind-key -T copy-mode-vi g switch-client -T fl-g
bind-key -T fl-g g send-keys -X history-top \; switch-client -T copy-mode-vi
bind-key -T fl-g h send-keys -X back-to-indentation \; switch-client -T copy-mode-vi
bind-key -T fl-g l send-keys -X end-of-line \; switch-client -T copy-mode-vi
bind-key -T copy-mode-vi i send-keys -X cancel
bind-key -T copy-mode-vi Space switch-client -T fl-sp
bind-key -T fl-sp a switch-client -T fl-spa
bind-key -T fl-spa c detach-client
"##;

/// Table `fl-jk` for the key after a held `j`: every other printable key (and
/// the common named keys) sends the held `j` and then itself, and clears the
/// flag. `j` and `k` are bound in KEYS.
fn jk_bindings() -> String {
    let mut out = String::new();
    for c in ' '..='~' {
        if c == 'j' || c == 'k' {
            continue;
        }
        let key = match c {
            ' ' => "Space".to_string(),
            '\'' => "\"'\"".to_string(),
            _ => format!("'{c}'"),
        };
        let arg = match c {
            '\'' => "\"'\"".to_string(),
            _ => format!("'{c}'"),
        };
        out.push_str(&format!(
            "bind-key -T fl-jk {key} send-keys -l j \\; send-keys -l {arg} \\; set -g @fl_jk 0 \\; switch-client -T root\n"
        ));
    }
    for key in ["Enter", "Tab", "BSpace", "Escape", "Up", "Down", "Left", "Right"] {
        out.push_str(&format!(
            "bind-key -T fl-jk {key} send-keys -l j \\; send-keys {key} \\; set -g @fl_jk 0 \\; switch-client -T root\n"
        ));
    }
    out
}

/// Shows Claude in a popup. `text` goes into Claude's prompt first (not
/// submitted), for `<space>as` / `<space>ac` with a selection. One line is
/// typed; several lines are pasted (bracketed paste) so line breaks and table
/// layout survive and Enter isn't sent.
pub fn open(text: Option<&str>) -> io::Result<()> {
    if env::var_os("TMUX").is_none() {
        return Err(io::Error::other("Claude popup needs fl run inside tmux"));
    }
    ensure_session()?;
    match text.filter(|t| !t.trim().is_empty()) {
        Some(t) if t.contains('\n') => {
            let t = t.replace('\r', "");
            tmux(&["set-buffer", "-b", "fl-claude", "--", &t])?;
            tmux(&["paste-buffer", "-p", "-d", "-b", "fl-claude", "-t", SESSION])?;
        }
        Some(t) => tmux(&["send-keys", "-t", SESSION, "-l", t])?,
        None => {}
    }
    // Popup targets the pane fl runs in, so it lands on the right client.
    let mut args = vec!["display-popup", "-E", "-w", "90%", "-h", "90%", "-b", "rounded"];
    let pane = env::var("TMUX_PANE").ok();
    if let Some(p) = pane.as_deref() {
        args.extend(["-t", p]);
    }
    // The popup inherits TMUX from the server; unset it so attach nests cleanly.
    let attach = format!("env -u TMUX tmux -L {SOCKET} attach -t {SESSION}");
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
    let exists = server()
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
    ])?;
    source_keys()
}

/// Loads the Claude server's keys (piped to `source-file -`). copy-mode-vi is
/// copied to the `fl-g`, `fl-sp` and `fl-spa` tables first, so an unbound key
/// after `g` or `space` still acts as normal; then KEYS and the `fl-jk` table.
fn source_keys() -> io::Result<()> {
    let list = server().args(["list-keys", "-T", "copy-mode-vi"]).output()?;
    let script = keys_script(&String::from_utf8_lossy(&list.stdout));
    let mut child = server()
        .args(["source-file", "-"])
        .stdin(Stdio::piped())
        .spawn()?;
    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(script.as_bytes())?;
    }
    if child.wait()?.success() {
        Ok(())
    } else {
        Err(io::Error::other("could not load Claude popup keys"))
    }
}

/// The full script sourced into the Claude server. `copy_mode_vi` is the
/// output of `list-keys -T copy-mode-vi`.
fn keys_script(copy_mode_vi: &str) -> String {
    let mut script = String::new();
    // Each copied line also returns the client to copy-mode-vi, so a
    // one-key table (g, space) is used for exactly one key.
    for table in ["fl-g", "fl-sp", "fl-spa"] {
        for line in copy_mode_vi.lines().filter(|l| !l.trim().is_empty()) {
            script.push_str(&line.replace("-T copy-mode-vi ", &format!("-T {table} ")));
            script.push_str(" \\; switch-client -T copy-mode-vi\n");
        }
    }
    script.push_str(KEYS);
    script.push_str(&jk_bindings());
    script
}

/// `tmux` aimed at the Claude server.
fn server() -> Command {
    let mut cmd = Command::new("tmux");
    cmd.args(["-L", SOCKET]);
    cmd
}

fn tmux(args: &[&str]) -> io::Result<()> {
    let out = server().args(args).output()?;
    if out.status.success() {
        Ok(())
    } else {
        Err(io::Error::other(
            String::from_utf8_lossy(&out.stderr).trim().to_string(),
        ))
    }
}
