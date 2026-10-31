// `fl note [ticker | text]`: standalone twin of `<leader>vn` (lua/finlarp/ui/note.lua).
// Type a note and press ↵: it is saved to mind.duckdb with `py/mind/cli.py add`,
// then `py/mind/cli.py answer` runs detached (headless Claude with the finlarp
// MCP tools). The saved id shows here; read the answer later with `fl notes`
// (or `fl notes last`).
//
//   note on MRVL
//   › why did capex guidance drop?█
//
//   saved 20261101-093012-a1b2c3 · answering in the background
//
// ↵ save · esc back

use std::io;
use std::process::{Command, Stdio};
use std::sync::mpsc::{Receiver, TryRecvError};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Wrap};
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::app::{Action, Ctx, Screen};
use crate::pyrun;
use crate::ui::text;
use crate::ui::theme::Theme;

/// The mind CLI, repo-relative.
pub const CLI: &str = "py/mind/cli.py";
/// anchor_screen for notes taken in `fl` (nvim stores the buffer's filetype).
const SCREEN: &str = "note";

/// `TICKER` (all caps, 1-5 letters) or `$ticker` as an explicit `ticker:` anchor.
/// Anything else is left to mind's entity extraction on the context, as nvim does.
pub fn ticker_anchor(text: &str) -> Option<String> {
    let t = text.trim();
    let dollar = t.starts_with('$');
    let bare = t.trim_start_matches('$');
    let shape = (1..=5).contains(&bare.len()) && bare.chars().all(|c| c.is_ascii_alphabetic());
    let caps = bare.chars().all(|c| c.is_ascii_uppercase());
    (shape && (dollar || caps)).then(|| format!("ticker:{}", bare.to_ascii_uppercase()))
}

/// Argv (after the script) for `mind add`. `--flag=value` keeps text that starts
/// with "-" from being read as an option.
pub fn add_args(body: &str, context: &str, anchor: Option<&str>) -> Vec<String> {
    let mut args = vec![
        "add".to_string(),
        format!("--body={body}"),
        format!("--screen={SCREEN}"),
        format!("--context={context}"),
    ];
    if let Some(anchor) = anchor {
        args.push(format!("--anchor={anchor}"));
    }
    args
}

/// The `id` field of `mind add`'s JSON output.
fn note_id(json: &str) -> Option<String> {
    let v: serde_json::Value = serde_json::from_str(json).ok()?;
    v.get("id")?.as_str().map(str::to_string)
}

/// `mind answer <id>`, detached: it outlives this screen and records its result on the note.
fn start_answer(id: &str) -> io::Result<()> {
    let plugin = pyrun::plugin_dir();
    Command::new(pyrun::python(&plugin))
        .arg(plugin.join(CLI))
        .args(["answer", id])
        .current_dir(&plugin)
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map(drop)
}

/// A note being saved. `mind add` runs on a background thread; once it returns
/// an id, `mind answer` is started detached.
pub struct Save {
    rx: Receiver<Result<String, String>>,
}

impl Save {
    /// None for a blank body (nothing is saved).
    pub fn start(body: &str, context: &str, anchor: Option<&str>) -> Option<Self> {
        let body = body.trim();
        if body.is_empty() {
            return None;
        }
        let args = add_args(body, context, anchor);
        let refs: Vec<&str> = args.iter().map(String::as_str).collect();
        Some(Self {
            rx: pyrun::spawn_script(CLI, &refs),
        })
    }

    /// None while `mind add` is still running. Once it finishes, Some(Ok(id))
    /// means saved and answering; Some(Err) carries the failure. Starts the
    /// answer on the first Some, so call it until it returns Some.
    pub fn poll(&self) -> Option<Result<String, String>> {
        match self.rx.try_recv() {
            Err(TryRecvError::Empty) => None,
            Err(TryRecvError::Disconnected) => Some(Err("save: worker thread died".into())),
            Ok(Err(e)) => Some(Err(format!("save failed: {e}"))),
            Ok(Ok(json)) => Some(match note_id(&json) {
                Some(id) => match start_answer(&id) {
                    Ok(()) => Ok(id),
                    Err(e) => Err(format!("saved {id}, but the answer did not start: {e}")),
                },
                None => Err("save: no note id in mind output".into()),
            }),
        }
    }
}

pub struct Note {
    theme: Theme,
    input: Input,
    anchor: Option<String>,
    context: String,
    save: Option<Save>,
    status: String,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Note> {
    let context = arg.unwrap_or_default().trim().to_string();
    Ok(Note {
        theme: ctx.theme,
        input: Input::default(),
        anchor: ticker_anchor(&context),
        context,
        save: None,
        status: String::new(),
    })
}

impl Note {
    fn submit(&mut self) {
        let body = self.input.value().trim().to_string();
        match Save::start(&body, &self.context, self.anchor.as_deref()) {
            Some(save) => {
                self.save = Some(save);
                self.status = "saving…".into();
            }
            None => self.status = "nothing to save".into(),
        }
    }
}

impl Screen for Note {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, _, input, _, status, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let label = if self.context.is_empty() {
            "no anchor".to_string()
        } else {
            text::truncate(&self.context, (area.width as usize).saturating_sub(10).max(10))
        };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" note", t.accent()),
                Span::styled(format!(" · {label}"), t.dim()),
            ])),
            head,
        );

        let prefix = " › ";
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prefix, t.accent()),
                Span::styled(self.input.value().to_string(), t.base()),
            ])),
            input,
        );
        if self.save.is_none() {
            frame.set_cursor_position((
                input.x + (text::width(prefix) + self.input.visual_cursor()) as u16,
                input.y,
            ));
        }

        frame.render_widget(
            Paragraph::new(format!(" {}", self.status))
                .style(t.base())
                .wrap(Wrap { trim: false }),
            status,
        );

        let hint = if self.save.is_some() {
            " saving…"
        } else {
            " ↵ save · esc back"
        };
        frame.render_widget(Paragraph::new(hint).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.save.is_some() {
            // Saving: keys are ignored so the box cannot change under the save.
            if key.code == KeyCode::Esc {
                self.status = "still saving, one moment".into();
            }
            return Action::None;
        }
        match key.code {
            KeyCode::Esc => Action::Quit,
            KeyCode::Char('q')
                if self.input.value().is_empty() && !key.modifiers.contains(KeyModifiers::CONTROL) =>
            {
                Action::Quit
            }
            KeyCode::Enter => {
                self.submit();
                Action::None
            }
            _ => {
                self.input.handle_event(&Event::Key(key));
                Action::None
            }
        }
    }

    fn tick(&mut self) -> Action {
        if let Some(save) = &self.save {
            if let Some(res) = save.poll() {
                self.save = None;
                match res {
                    Ok(id) => {
                        self.status = format!("saved {id} · answering in the background (fl notes last)");
                        self.input.reset();
                    }
                    Err(e) => self.status = e,
                }
            }
        }
        Action::None
    }

    fn leader_ok(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::buffer::Buffer;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn press(n: &mut Note, code: KeyCode) -> Action {
        n.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn note(arg: Option<&str>) -> Note {
        let ctx = Ctx {
            db_path: std::path::PathBuf::new(),
            theme: Theme::default(),
        };
        open(&ctx, arg.map(str::to_string)).expect("open")
    }

    fn screen_text(buf: &Buffer) -> String {
        buf.content().iter().map(|c| c.symbol()).collect()
    }

    #[test]
    fn ticker_anchor_only_for_tickers() {
        assert_eq!(ticker_anchor("MRVL").as_deref(), Some("ticker:MRVL"));
        assert_eq!(ticker_anchor("$nvda").as_deref(), Some("ticker:NVDA"));
        assert_eq!(ticker_anchor(" AVGO ").as_deref(), Some("ticker:AVGO"));
        assert_eq!(ticker_anchor("capex"), None);
        assert_eq!(ticker_anchor("MRVL capex"), None);
        assert_eq!(ticker_anchor("BRK.B"), None);
        assert_eq!(ticker_anchor("TOOLONG"), None);
        assert_eq!(ticker_anchor("$"), None);
        assert_eq!(ticker_anchor(""), None);
    }

    #[test]
    fn add_args_pass_text_as_values_and_anchor_only_when_given() {
        let a = add_args("-why up?", "MRVL", Some("ticker:MRVL"));
        assert_eq!(
            a,
            [
                "add",
                "--body=-why up?",
                "--screen=note",
                "--context=MRVL",
                "--anchor=ticker:MRVL"
            ]
        );
        let a = add_args("why", "capex text", None);
        assert_eq!(a.len(), 4);
        assert!(a.iter().all(|x| !x.starts_with("--anchor")));
    }

    #[test]
    fn parses_note_id_and_rejects_other_json() {
        assert_eq!(
            note_id(r#"{"id": "20261101-093012-a1b2c3", "mentions": []}"#).as_deref(),
            Some("20261101-093012-a1b2c3")
        );
        assert_eq!(note_id(r#"{"error": "x"}"#), None);
        assert_eq!(note_id("not json"), None);
    }

    #[test]
    fn blank_body_saves_nothing() {
        assert!(Save::start("   ", "MRVL", None).is_none());
    }

    #[test]
    fn typing_then_q_and_esc_leave() {
        let mut n = note(Some("MRVL"));
        assert_eq!(n.anchor.as_deref(), Some("ticker:MRVL"));
        assert_eq!(press(&mut n, KeyCode::Char('q')), Action::Quit);
        assert_eq!(press(&mut n, KeyCode::Char('x')), Action::None);
        // q is text once something is typed
        assert_eq!(press(&mut n, KeyCode::Char('q')), Action::None);
        assert_eq!(n.input.value(), "xq");
        assert_eq!(press(&mut n, KeyCode::Esc), Action::Quit);
    }

    #[test]
    fn enter_on_empty_box_reports_nothing_to_save() {
        let mut n = note(None);
        assert_eq!(press(&mut n, KeyCode::Enter), Action::None);
        assert_eq!(n.status, "nothing to save");
        assert!(n.save.is_none());
    }

    #[test]
    fn renders_anchor_and_prompt() {
        let mut n = note(Some("MRVL"));
        let mut term = Terminal::new(TestBackend::new(60, 8)).expect("terminal");
        term.draw(|f| n.draw(f)).expect("draw");
        let text = screen_text(term.backend().buffer());
        assert!(text.contains("note · MRVL"), "{text}");
        assert!(text.contains("esc back"), "{text}");
    }
}
