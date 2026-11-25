// `fl chats` (L on home): every Claude chat fl started, from the shared registry
// (crate::chats): `<space>ac` popups, `C` in the x diagrams, the Z chats, the chat screen.
//
//   Chats  14
//   / to filter
//   11-23 14:02  z:explain    opus    $0.84   6t  why is HBM stacked on the interposer
//   11-23 13:40  x diagrams   -       $0.12   2t  what does the TSV carry
//   ──────────────────────────────────────────────
//   session 3f2a9c1e-…  ·  cwd ~/code/finlarp  ·  in 120.4k  out 3.2k
//   started 11-23 13:58  ·  file data/z/.chat-explain.json
//
// enter resumes the chat in a Claude popup of its own · D forgets it (the Claude
// transcript stays) · r reloads · / filters (source, title, model).

use std::io;
use std::path::PathBuf;

use chrono::{DateTime, Local};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Paragraph};

use super::claude_history;
use crate::app::{Action, Ctx, Route, Screen};
use crate::chats::{self, Entry};
use crate::ui::help::{Help, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

const SOURCE_COL: usize = 12;
const MODEL_COL: usize = 7;

pub struct Chats {
    all: Vec<Entry>,
    shown: Vec<usize>,
    query: String,
    filtering: bool,
    state: ListState,
    page: usize,
    width: u16,
    /// `D` pressed once: the next `D` forgets the chat.
    arm_forget: bool,
    flash: Option<String>,
    dirty: bool,
    theme: Theme,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Chats> {
    Ok(Chats::new(load_titled(), ctx.theme))
}

/// The registry, with a title read from the Claude transcript for chats that had none
/// when they were recorded (the `<space>ac` popup is started before anything is typed).
fn load_titled() -> Vec<Entry> {
    let mut v = chats::load();
    if v.iter().all(|e| !e.title.is_empty()) {
        return v;
    }
    let root = claude_history::projects_dir();
    for e in v.iter_mut().filter(|e| e.title.is_empty()) {
        if let Some(p) = transcript(&root, &e.session) {
            let mut s = claude_history::Session::at(p, &e.session);
            s.load();
            e.title = s.prompt;
        }
    }
    v
}

/// `<projects>/<any dir>/<id>.jsonl`, if Claude kept it.
fn transcript(root: &std::path::Path, id: &str) -> Option<PathBuf> {
    std::fs::read_dir(root)
        .ok()?
        .flatten()
        .map(|d| d.path().join(format!("{id}.jsonl")))
        .find(|p| p.is_file())
}

fn when(secs: u64) -> String {
    DateTime::from_timestamp(secs as i64, 0)
        .map(|d| d.with_timezone(&Local).format("%m-%d %H:%M").to_string())
        .unwrap_or_else(|| "-".into())
}

fn tokens(n: u64) -> String {
    match n {
        n if n >= 1_000_000 => format!("{:.1}M", n as f64 / 1e6),
        n if n >= 1_000 => format!("{:.1}k", n as f64 / 1e3),
        n => n.to_string(),
    }
}

fn tilde(p: &str) -> String {
    match std::env::var("HOME") {
        Ok(h) if !h.is_empty() && p.starts_with(&h) => format!("~{}", &p[h.len()..]),
        _ => p.to_string(),
    }
}

impl Chats {
    fn new(all: Vec<Entry>, theme: Theme) -> Self {
        let mut s = Self {
            all,
            shown: Vec::new(),
            query: String::new(),
            filtering: false,
            state: ListState::default(),
            page: 10,
            width: 80,
            arm_forget: false,
            flash: None,
            dirty: true,
            theme,
        };
        s.refilter();
        s
    }

    fn selected(&self) -> Option<&Entry> {
        self.state
            .selected()
            .and_then(|p| self.shown.get(p))
            .map(|&i| &self.all[i])
    }

    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        self.shown = (0..self.all.len())
            .filter(|&i| {
                let e = &self.all[i];
                q.is_empty()
                    || e.source.to_lowercase().contains(&q)
                    || e.title.to_lowercase().contains(&q)
                    || e.model.as_deref().unwrap_or("").contains(&q)
            })
            .collect();
        let pos = self
            .state
            .selected()
            .unwrap_or(0)
            .min(self.shown.len().saturating_sub(1));
        self.state.select((!self.shown.is_empty()).then_some(pos));
    }

    fn step(&mut self, d: isize) {
        let n = self.shown.len();
        if n > 0 {
            let cur = self.state.selected().unwrap_or(0) as isize;
            self.state
                .select(Some((cur + d).clamp(0, n as isize - 1) as usize));
        }
    }

    fn reload(&mut self) {
        self.all = load_titled();
        self.refilter();
    }

    fn row(&self, e: &Entry) -> Line<'static> {
        let t = self.theme;
        let head = format!(
            "{}  {}  {}  {:>6}  {:>3}t  ",
            when(e.updated),
            text::fit(&e.source, SOURCE_COL, false),
            text::fit(e.model.as_deref().unwrap_or("-"), MODEL_COL, false),
            format!("${:.2}", e.cost),
            e.turns,
        );
        let w = (self.width as usize).saturating_sub(head.chars().count());
        let title = if e.title.is_empty() { "(nothing asked yet)" } else { &e.title };
        Line::from(vec![
            Span::styled(head, t.dim()),
            Span::styled(text::fit(title, w, false), t.base()),
        ])
    }

    fn detail(&self) -> Vec<Line<'static>> {
        let t = self.theme;
        let Some(e) = self.selected() else {
            return Vec::new();
        };
        let mut a = vec![
            format!("session {}", e.session),
            format!("in {}  out {}", tokens(e.input), tokens(e.output)),
        ];
        if !e.cwd.is_empty() {
            a.push(format!("cwd {}", tilde(&e.cwd)));
        }
        let mut b = vec![
            format!("started {}", when(e.started)),
            format!("last {}", when(e.updated)),
        ];
        if let Some(f) = &e.file {
            b.push(format!("file {}", tilde(f)));
        }
        vec![
            Line::styled(a.join("  ·  "), t.dim()),
            Line::styled(b.join("  ·  "), t.dim()),
            Line::styled(text::fit(&e.title, self.width as usize, false), t.base()),
        ]
    }
}

const KEYS: &[Key] = &[
    key("/", "filter (source, title, model)"),
    key("j/k", "move"),
    key("^d/^u", "page down / up"),
    key("g/G", "first / last"),
    key("↵", "resume the chat in a Claude popup"),
    key("r", "reload"),
    key("D D", "forget the chat (transcript stays)"),
    key("esc/q", "back"),
];

impl Screen for Chats {
    fn draw(&mut self, frame: &mut Frame) {
        self.dirty = false;
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [title, filter, list_area, detail] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(4),
        ])
        .areas(area);
        self.page = list_area.height.max(1) as usize;
        self.width = list_area.width;
        let cost: f64 = self.shown.iter().map(|&i| self.all[i].cost).sum();
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled("Chats", t.accent().add_modifier(Modifier::BOLD)),
                Span::styled(
                    format!("  {} of {}  ·  ${cost:.2}", self.shown.len(), self.all.len()),
                    t.dim(),
                ),
            ])),
            title,
        );
        let fl = if self.filtering {
            Line::from(vec![
                Span::styled("/ ", t.accent()),
                Span::styled(format!("{}█", self.query), t.base()),
            ])
        } else if !self.query.is_empty() {
            Line::styled(format!("/ {}", self.query), t.dim())
        } else {
            Line::styled("/ to filter", t.dim())
        };
        frame.render_widget(Paragraph::new(fl), filter);
        if self.shown.is_empty() {
            let msg = if self.all.is_empty() {
                "no chats yet: space ac, C in the diagrams, or Z start one"
            } else {
                "no matches"
            };
            frame.render_widget(Paragraph::new(Span::styled(msg, t.dim())), list_area);
        } else {
            let items: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| ListItem::new(self.row(&self.all[i])))
                .collect();
            let list = List::new(items).highlight_style(t.selected());
            frame.render_stateful_widget(list, list_area, &mut self.state);
        }
        frame.render_widget(
            Paragraph::new(self.detail())
                .block(Block::new().borders(Borders::TOP).border_style(t.border())),
            detail,
        );
    }

    fn takes_text(&self) -> bool {
        self.filtering
    }

    fn help(&self) -> Help {
        Help::new("chats", KEYS)
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        self.dirty = true;
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        if self.filtering {
            match key.code {
                KeyCode::Esc => {
                    self.filtering = false;
                    self.query.clear();
                }
                KeyCode::Enter => self.filtering = false,
                KeyCode::Backspace => {
                    self.query.pop();
                }
                KeyCode::Char(c) if !ctrl => self.query.push(c),
                _ => return Action::None,
            }
            self.refilter();
            return Action::None;
        }
        let arm = std::mem::take(&mut self.arm_forget);
        let half = (self.page / 2).max(1) as isize;
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => return Action::Quit,
            KeyCode::Char('/') => self.filtering = true,
            KeyCode::Char('j') | KeyCode::Down if !ctrl => self.step(1),
            KeyCode::Char('k') | KeyCode::Up if !ctrl => self.step(-1),
            KeyCode::Char('d') if ctrl => self.step(half),
            KeyCode::Char('u') if ctrl => self.step(-half),
            KeyCode::Char('g') => self.state.select((!self.shown.is_empty()).then_some(0)),
            KeyCode::Char('G') => self.step(isize::MAX / 2),
            KeyCode::Char('r') => self.reload(),
            KeyCode::Char('D') => {
                if let Some(id) = self.selected().map(|e| e.session.clone()) {
                    if arm {
                        chats::forget(&id);
                        self.reload();
                        self.flash = Some("forgotten".into());
                    } else {
                        self.arm_forget = true;
                        self.flash = Some("D again to forget this chat".into());
                    }
                }
            }
            KeyCode::Enter => {
                if let Some(e) = self.selected() {
                    return Action::Route(Route::ClaudeResume {
                        session: e.session.clone(),
                        cwd: e.cwd.clone(),
                    });
                }
            }
            _ => {}
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.dirty
    }

    fn flash_text(&self) -> Option<&str> {
        self.flash.as_deref()
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
        self.dirty = true;
    }

    fn leader_ok(&self) -> bool {
        !self.filtering
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    use super::*;

    fn e(session: &str, source: &str, title: &str, cost: f64) -> Entry {
        Entry {
            session: session.into(),
            source: source.into(),
            title: title.into(),
            cost,
            turns: 2,
            updated: 1_700_000_000,
            ..Entry::default()
        }
    }

    #[test]
    fn lists_filters_and_resumes() {
        let mut c = Chats::new(
            vec![
                e("aaaa", "z:explain", "why HBM", 0.5),
                e("bbbb", "x diagrams", "what is a TSV", 0.25),
            ],
            Theme::from_args(None, None, None),
        );
        let mut term = Terminal::new(TestBackend::new(100, 12)).unwrap();
        term.draw(|f| c.draw(f)).unwrap();
        let screen = format!("{:?}", term.backend().buffer());
        assert!(screen.contains("why HBM") && screen.contains("$0.75"));
        c.on_key(KeyEvent::from(KeyCode::Char('/')));
        for ch in "tsv".chars() {
            c.on_key(KeyEvent::from(KeyCode::Char(ch)));
        }
        c.on_key(KeyEvent::from(KeyCode::Enter));
        assert_eq!(c.shown.len(), 1);
        assert_eq!(
            c.on_key(KeyEvent::from(KeyCode::Enter)),
            Action::Route(Route::ClaudeResume {
                session: "bbbb".into(),
                cwd: String::new()
            })
        );
    }
}
