// The Claude window in the Diagrams screen: `C` opens the real Claude Code, running in
// its own tmux session (`ui::tmux_pane`), over the description column on the right of
// the picture. The session keeps running when the window closes, so the next `C` shows
// the same conversation.
//
// Keys: while the window has focus every key goes to Claude, except ctrl-/, which hands the
// keys back to browse mode. Browse mode: `i` or enter gives Claude the keys again, esc or q
// closes the window.

use std::env;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::Rect;
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{Block, Borders, Clear, Paragraph};

use crate::ui::theme::Theme;
use crate::ui::tmux_pane::TmuxPane;

/// The tmux server and session the Claude window keeps. Separate from the full-screen
/// Claude popup (`fl-claude`), so the two never resize each other.
const SOCKET: &str = "fl-diagram";
const SESSION: &str = "finlarp-diagram-claude";
/// The quiz rules, passed to Claude as an appended system prompt when the session starts.
const QUIZ_RULES: &str = concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/src/screens/diagrams_quiz_rules.md"
);

/// The command the window's tmux session runs: Claude in quiz mode. tmux runs it through a
/// shell, so the rules file is read with `$(cat ...)`.
fn claude_command() -> String {
    format!("claude --append-system-prompt \"$(cat '{QUIZ_RULES}')\"")
}

pub struct ClaudeWindow {
    theme: Theme,
    /// The window is on screen.
    pub open: bool,
    /// Keys go to Claude (otherwise they are browse keys for the window).
    pub focus: bool,
    pane: TmuxPane,
    /// The shell command the tmux session runs when it starts.
    command: String,
    /// The last screen Claude drew, as styled lines.
    screen: Vec<Line<'static>>,
    /// Why Claude is not on screen, when it is not.
    error: Option<String>,
}

impl ClaudeWindow {
    pub fn new(theme: Theme) -> Self {
        Self::with(theme, SOCKET, SESSION, claude_command())
    }

    /// A window on its own tmux session, running `command` (the Z screen keeps one per mode).
    pub fn with(
        theme: Theme,
        socket: &'static str,
        session: &'static str,
        command: String,
    ) -> Self {
        Self {
            theme,
            open: false,
            focus: false,
            pane: TmuxPane::new(socket, session),
            command,
            screen: Vec::new(),
            error: None,
        }
    }

    /// Opens the window with focus on Claude.
    pub fn show(&mut self) {
        self.open = true;
        self.focus = true;
    }

    /// Keys while the window is open.
    pub fn key(&mut self, key: KeyEvent) {
        if self.focus {
            // ctrl-/ is byte 0x1f, which crossterm reports as `7` with ctrl
            if key.code == KeyCode::Char('7') && key.modifiers.contains(KeyModifiers::CONTROL) {
                self.focus = false;
            } else {
                self.pane.send_key(key);
            }
            return;
        }
        match key.code {
            KeyCode::Char('i') | KeyCode::Enter => self.focus = true,
            KeyCode::Esc | KeyCode::Char('q') => self.open = false,
            _ => {}
        }
    }

    /// Draws the window over `r` with `borders` (the diagrams screen's right-hand column
    /// leaves out the left edge; the Z screen's chat sits under the canvas, all four).
    pub fn draw(&mut self, frame: &mut Frame, r: Rect, label: &str, t: &Theme, borders: Borders) {
        frame.render_widget(Clear, r);
        let block = Block::new()
            .borders(borders)
            .border_style(t.accent())
            .title(Span::styled(
                format!(" claude \u{00b7} {label} "),
                t.title(),
            ))
            .padding(ratatui::widgets::Padding::new(1, 0, 0, 0));
        let inner = block.inner(r);
        frame.render_widget(block, r);

        if self.error.is_none() {
            let dir = env::current_dir().unwrap_or_default();
            if let Err(e) = self
                .pane
                .ensure(&dir, &self.command, inner.width, inner.height)
            {
                self.error = Some(format!("can't start claude: {e}"));
            }
        }
        if let Some(e) = &self.error {
            frame.render_widget(
                Paragraph::new(Span::styled(e.clone(), t.down())).style(t.base()),
                inner,
            );
            return;
        }
        self.pane.resize(inner.width, inner.height);
        if let Some(screen) = self.pane.capture() {
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
        }
        frame.render_widget(
            Paragraph::new(Text::from(self.screen.clone())).style(self.theme.base()),
            inner,
        );
        // the program's own cursor, where Claude has its input: only while Claude has focus
        if self.focus {
            if let Some((x, y)) = self.pane.cursor() {
                if x < inner.width && y < inner.height {
                    block_cursor(frame, inner.x + x, inner.y + y);
                }
            }
        }
    }
}

/// Draws a cursor as a reversed cell, leaving the terminal's own cursor hidden. Ghostty's
/// H.264 playback moved a shown cursor onto the picture (under the caption's ▶), so the
/// diagrams screen never shows the real one.
pub(super) fn block_cursor(frame: &mut Frame, x: u16, y: u16) {
    if let Some(cell) = frame.buffer_mut().cell_mut((x, y)) {
        cell.set_style(
            ratatui::style::Style::default().add_modifier(ratatui::style::Modifier::REVERSED),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn window() -> ClaudeWindow {
        let mut w = ClaudeWindow::with(Theme::default(), "fl-test", "fl-test", "true".into());
        w.show();
        w
    }

    fn ctrl_slash() -> KeyEvent {
        KeyEvent::new(KeyCode::Char('7'), KeyModifiers::CONTROL)
    }

    #[test]
    fn ctrl_slash_hands_the_keys_back() {
        let mut w = window();
        w.key(ctrl_slash());
        assert!(!w.focus, "ctrl-/ leaves the chat");
        assert!(w.open, "the window stays on screen");
    }

    #[test]
    fn plain_j_and_space_are_typed_into_claude() {
        let mut w = window();
        w.key(KeyEvent::new(KeyCode::Char('j'), KeyModifiers::NONE));
        w.key(KeyEvent::new(KeyCode::Char(' '), KeyModifiers::NONE));
        w.key(KeyEvent::new(KeyCode::Char('k'), KeyModifiers::NONE));
        assert!(w.focus, "plain keys never leave the chat");
    }
}
