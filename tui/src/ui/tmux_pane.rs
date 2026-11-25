// A program running in its own tmux session, drawn inside a ratatui area. The session
// lives on its own tmux server (`-L <socket>`), so it keeps running when fl closes and
// the next open shows the same conversation. Each draw captures the visible screen with
// its colours (`capture-pane -e`); keys go in with `send-keys`. The program's own cursor
// is the one on screen, so fl never places one of its own while the pane has focus.

use std::io;
use std::path::Path;
use std::process::{Command, Stdio};

use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};

pub struct TmuxPane {
    socket: &'static str,
    session: &'static str,
    /// The size the session was last given, in cells.
    size: Option<(u16, u16)>,
    /// Set once the session is known to be running.
    started: bool,
}

impl TmuxPane {
    pub fn new(socket: &'static str, session: &'static str) -> Self {
        Self {
            socket,
            session,
            size: None,
            started: false,
        }
    }

    /// `tmux` aimed at this pane's server, with fl's own tmux environment left out so a
    /// nested server does not think it is inside the outer one.
    fn server(&self) -> Command {
        let mut cmd = Command::new("tmux");
        cmd.args(["-L", self.socket]).env_remove("TMUX");
        cmd
    }

    fn run(&self, args: &[&str]) -> io::Result<String> {
        let out = self.server().args(args).stderr(Stdio::piped()).output()?;
        if out.status.success() {
            Ok(String::from_utf8_lossy(&out.stdout).into_owned())
        } else {
            Err(io::Error::other(
                String::from_utf8_lossy(&out.stderr).trim().to_string(),
            ))
        }
    }

    /// Starts `program` in `dir` at `cols` x `rows`, unless the session already runs.
    pub fn ensure(&mut self, dir: &Path, program: &str, cols: u16, rows: u16) -> io::Result<()> {
        if self.started {
            return Ok(());
        }
        if cfg!(test) {
            return Err(io::Error::other("no tmux in tests"));
        }
        let exists = self
            .server()
            .args(["has-session", "-t", self.session])
            .stderr(Stdio::null())
            .status()?
            .success();
        if !exists {
            let dir = dir.to_string_lossy().into_owned();
            let (cols, rows) = (cols.max(2).to_string(), rows.max(2).to_string());
            self.run(&[
                "new-session",
                "-d",
                "-s",
                self.session,
                "-c",
                &dir,
                "-x",
                &cols,
                "-y",
                &rows,
                // keep the program out of the alternate screen, so its output is the
                // visible screen that gets captured
                "-e",
                "CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1",
                program,
            ])?;
            self.run(&["set-option", "-t", self.session, "status", "off"])?;
            self.size = Some((cols.parse().unwrap_or(2), rows.parse().unwrap_or(2)));
        }
        self.started = true;
        Ok(())
    }

    /// Gives the session the area's size when it changed.
    pub fn resize(&mut self, cols: u16, rows: u16) {
        let (cols, rows) = (cols.max(2), rows.max(2));
        if self.size == Some((cols, rows)) || !self.started {
            return;
        }
        let (c, r) = (cols.to_string(), rows.to_string());
        if self
            .run(&["resize-window", "-t", self.session, "-x", &c, "-y", &r])
            .is_ok()
        {
            self.size = Some((cols, rows));
        }
    }

    /// The visible screen, with its colours, as ANSI text. None when the session is not up.
    pub fn capture(&self) -> Option<String> {
        if !self.started {
            return None;
        }
        self.run(&["capture-pane", "-p", "-e", "-t", self.session]).ok()
    }

    /// Where the program's cursor is on the pane, when it is shown.
    pub fn cursor(&self) -> Option<(u16, u16)> {
        if !self.started {
            return None;
        }
        let out = self
            .run(&[
                "display-message",
                "-p",
                "-t",
                self.session,
                "#{cursor_flag} #{cursor_x} #{cursor_y}",
            ])
            .ok()?;
        let mut parts = out.split_whitespace();
        let shown = parts.next()? == "1";
        let x = parts.next()?.parse().ok()?;
        let y = parts.next()?.parse().ok()?;
        shown.then_some((x, y))
    }

    /// Sends one key to the program. Returns false for keys with no tmux name.
    pub fn send_key(&self, key: KeyEvent) -> bool {
        if !self.started {
            return false;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let alt = key.modifiers.contains(KeyModifiers::ALT);
        let mut literal = false;
        let name = match key.code {
            KeyCode::Char(c) if ctrl => format!("C-{}", c.to_ascii_lowercase()),
            KeyCode::Char(c) if alt => format!("M-{c}"),
            KeyCode::Char(c) => {
                literal = true;
                c.to_string()
            }
            KeyCode::Enter => "Enter".into(),
            KeyCode::Tab => "Tab".into(),
            KeyCode::BackTab => "BTab".into(),
            KeyCode::Backspace => "BSpace".into(),
            KeyCode::Esc => "Escape".into(),
            KeyCode::Up => "Up".into(),
            KeyCode::Down => "Down".into(),
            KeyCode::Left => "Left".into(),
            KeyCode::Right => "Right".into(),
            KeyCode::Home => "Home".into(),
            KeyCode::End => "End".into(),
            KeyCode::PageUp => "PPage".into(),
            KeyCode::PageDown => "NPage".into(),
            KeyCode::Delete => "DC".into(),
            KeyCode::Insert => "IC".into(),
            KeyCode::F(n) => format!("F{n}"),
            _ => return false,
        };
        let mut args = vec!["send-keys", "-t", self.session];
        if literal {
            args.push("-l");
        }
        args.push(&name);
        self.run(&args).is_ok()
    }

    /// Types `text` into the program as it is (no Enter).
    pub fn send_text(&self, text: &str) -> bool {
        self.started
            && self
                .run(&["send-keys", "-t", self.session, "-l", text])
                .is_ok()
    }
}
