// The AI universe screen's Neovim pane: the user's own nvim (their config, oil, leap,
// visual mode) running on the generated tree (universe_fs), in its own tmux server
// (ui::tmux_pane) and drawn beside the map. The session outlives the screen, so the next
// open shows the same buffers.
//
// While the pane has focus every key goes to nvim except ctrl-/ (back to the map) and
// ctrl-c (fl's quit). fl talks back through nvim's --listen socket: `reveal` opens a
// directory with the cursor on one entry (FlReveal in universe_nvim.lua).

use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant, SystemTime};

use ratatui::Frame;
use ratatui::crossterm::event::KeyEvent;
use ratatui::layout::Rect;
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{Block, Borders, Paragraph};

use crate::ui::theme::Theme;
use crate::ui::tmux_pane::TmuxPane;

const SOCKET: &str = "fl-universe";
const SESSION: &str = "finlarp-universe-nvim";
/// nvim's RPC socket, for fl -> nvim calls. Short and fixed: socket paths have a length cap.
const NVIM_SOCK: &str = "/tmp/fl-universe-nvim.sock";
const HOOKS: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/src/screens/universe_nvim.lua");

/// Single-quotes `s` for the shell tmux runs the command through.
fn sh_quote(s: &str) -> String {
    format!("'{}'", s.replace('\'', r"'\''"))
}

/// A Lua string literal for `s` (paths and tickers: no newlines).
fn lua_str(s: &str) -> String {
    format!("'{}'", s.replace('\\', r"\\").replace('\'', r"\'"))
}

pub struct NvimPane {
    pane: TmuxPane,
    root: PathBuf,
    /// The last screen nvim drew, as styled lines.
    screen: Vec<Line<'static>>,
    error: Option<String>,
    /// Set once the server has been tuned (escape-time) after the session started.
    tuned: bool,
    /// When fl started a new nvim (None: it found one already running).
    started_at: Option<SystemTime>,
    /// The session is up (started or found).
    up: bool,
    /// The last capture as tmux printed it, to tell when nvim's screen changed.
    raw: String,
    /// nvim's cursor on the pane, when shown.
    cursor: Option<(u16, u16)>,
    /// When fl last handed nvim a key: the screen is polled fast for a moment after.
    last_key: Option<Instant>,
}

/// How long after a key the pane is polled at frame rate.
const HOT: Duration = Duration::from_millis(600);

impl NvimPane {
    pub fn new(root: &Path) -> Self {
        Self {
            pane: TmuxPane::new(SOCKET, SESSION),
            root: root.to_path_buf(),
            screen: Vec::new(),
            error: None,
            tuned: false,
            started_at: None,
            up: false,
            raw: String::new(),
            cursor: None,
            last_key: None,
        }
    }

    /// A key went to nvim a moment ago: its screen is about to change.
    pub fn hot(&self) -> bool {
        self.last_key.is_some_and(|t| t.elapsed() < HOT)
    }

    /// Re-reads nvim's screen and cursor in one tmux call. True when either changed.
    pub fn refresh(&mut self) -> bool {
        if !self.up {
            return false;
        }
        let out = self
            .tmux()
            .args(["capture-pane", "-p", "-e", "-t", SESSION, ";"])
            .args(["display-message", "-p", "-t", SESSION])
            .arg("#{cursor_flag} #{cursor_x} #{cursor_y}")
            .stderr(Stdio::null())
            .output();
        let text = match out {
            Ok(o) if o.status.success() => String::from_utf8_lossy(&o.stdout).into_owned(),
            _ => {
                if !self.session_exists() {
                    // nvim quit (`:q`) and took its session with it: start a fresh one.
                    self.pane = TmuxPane::new(SOCKET, SESSION);
                    self.up = false;
                    self.tuned = false;
                    self.started_at = None;
                    self.screen.clear();
                    self.raw.clear();
                    return true;
                }
                return false;
            }
        };
        if text == self.raw {
            return false;
        }
        let body = text.trim_end_matches('\n');
        let (screen, cur) = body.rsplit_once('\n').unwrap_or(("", body));
        let mut parts = cur.split_whitespace();
        let shown = parts.next() == Some("1");
        let x = parts.next().and_then(|v| v.parse().ok());
        let y = parts.next().and_then(|v| v.parse().ok());
        self.cursor = match (shown, x, y) {
            (true, Some(x), Some(y)) => Some((x, y)),
            _ => None,
        };
        self.screen = screen
            .lines()
            .map(|l| {
                use ansi_to_tui::IntoText;
                l.into_text()
                    .ok()
                    .and_then(|t| t.lines.into_iter().next())
                    .unwrap_or_else(|| Line::raw(l.to_string()))
            })
            .collect();
        self.raw = text;
        true
    }

    /// Whether nvim can take a `reveal`: the hooks have run, which the first `.cursor`
    /// write after start shows (an nvim found running loaded them long ago).
    pub fn ready(&self) -> bool {
        if !self.up {
            return false;
        }
        let Some(start) = self.started_at else {
            return true;
        };
        std::fs::metadata(self.root.join(super::tree_fs::CURSOR))
            .and_then(|m| m.modified())
            .is_ok_and(|m| m >= start)
    }

    fn tmux(&self) -> Command {
        let mut cmd = Command::new("tmux");
        cmd.args(["-L", SOCKET]).env_remove("TMUX");
        cmd
    }

    fn session_exists(&self) -> bool {
        self.tmux()
            .args(["has-session", "-t", SESSION])
            .stderr(Stdio::null())
            .status()
            .is_ok_and(|s| s.success())
    }

    /// The command the session runs: nvim on the tree, listening for fl, with the hooks
    /// loaded after the user's config.
    fn command(&self) -> String {
        let root = self.root.to_string_lossy();
        format!(
            "COLORTERM=truecolor FL_UNIVERSE_ROOT={r} nvim --listen {s} -c {hooks} {r}",
            r = sh_quote(&root),
            s = sh_quote(NVIM_SOCK),
            hooks = sh_quote(&format!("luafile {HOOKS}")),
        )
    }

    fn start(&mut self, cols: u16, rows: u16) {
        if self.error.is_some() || self.up {
            return;
        }
        if !self.session_exists() {
            // A socket left by an nvim that died would make --listen fail.
            let _ = std::fs::remove_file(NVIM_SOCK);
            // filesystem clock, a second back: mtimes can be coarser than SystemTime
            self.started_at = Some(SystemTime::now() - std::time::Duration::from_secs(1));
        }
        let cmd = self.command();
        if let Err(e) = self.pane.ensure(&self.root, &cmd, cols, rows) {
            self.error = Some(format!("can't start nvim: {e}"));
            return;
        }
        self.up = true;
        if !self.tuned {
            // tmux waits 500ms after Esc for a meta sequence by default: nvim would lag on it.
            let _ = self
                .tmux()
                .args(["set-option", "-s", "escape-time", "0"])
                .status();
            self.tuned = true;
        }
    }

    /// Hands one key to nvim. Returns false for keys tmux has no name for.
    pub fn send_key(&mut self, key: KeyEvent) -> bool {
        self.last_key = Some(Instant::now());
        self.pane.send_key(key)
    }

    /// Opens `rel` (a directory relative to the root) in oil with the cursor on `name`.
    pub fn reveal(&mut self, rel: &str, name: Option<&str>) {
        self.last_key = Some(Instant::now());
        let keys = format!(
            "<C-\\><C-N>:lua FlReveal({}, {})<CR>",
            lua_str(rel),
            lua_str(name.unwrap_or(""))
        );
        let _ = Command::new("nvim")
            .args(["--server", NVIM_SOCK, "--remote-send", &keys])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
    }

    /// Draws the pane into `r`, starting nvim on the first draw.
    pub fn draw(&mut self, frame: &mut Frame, r: Rect, focus: bool, t: &Theme) {
        let block = Block::new()
            .borders(Borders::LEFT)
            .border_style(if focus { t.accent() } else { t.dim() })
            .title(Span::styled(
                " nvim ",
                if focus { t.title() } else { t.dim() },
            ));
        let inner = block.inner(r);
        frame.render_widget(block, r);
        self.start(inner.width, inner.height);
        if let Some(e) = &self.error {
            frame.render_widget(
                Paragraph::new(Span::styled(e.clone(), t.down())).style(t.base()),
                inner,
            );
            return;
        }
        self.pane.resize(inner.width, inner.height);
        if self.raw.is_empty() {
            self.refresh();
        }
        frame.render_widget(
            Paragraph::new(Text::from(self.screen.clone())).style(t.base()),
            inner,
        );
        if focus {
            if let Some((x, y)) = self.cursor {
                if x < inner.width && y < inner.height {
                    crate::screens::diagrams_window::block_cursor(frame, inner.x + x, inner.y + y);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quoting_survives_quotes() {
        assert_eq!(sh_quote("a'b"), r"'a'\''b'");
        assert_eq!(lua_str(r"x'y\z"), r"'x\'y\\z'");
    }

    #[test]
    fn command_loads_hooks_after_config_on_the_root() {
        let p = NvimPane::new(Path::new("/d/universe"));
        let c = p.command();
        assert!(c.starts_with("COLORTERM=truecolor FL_UNIVERSE_ROOT='/d/universe' nvim"));
        assert!(c.contains("--listen '/tmp/fl-universe-nvim.sock'"));
        assert!(c.contains("universe_nvim.lua'"));
        assert!(c.ends_with(" '/d/universe'"));
    }
}
