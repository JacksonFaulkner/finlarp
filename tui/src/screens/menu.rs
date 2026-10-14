// `<leader>v?` menu: every nvim finlarp keymap with what it does. Type to
// filter, Enter runs the highlighted map. nvim owns the list (its `maps`
// table) and passes it as JSON in $FINLARP_MENU_FILE:
//   [{"lhs": "<leader>vf", "name": "search filings", "desc": "...", "mode": "n"}]
// Enter hands the lhs back as `NvimAction::Keys`, so the real keymap fires.
//
//   finlarp › sea█
//   > ␣vf   search filings
//   Full-text search over 10-K/20-F text ...

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph, Wrap};
use serde::Deserialize;

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

pub const MENU_FILE_ENV: &str = "FINLARP_MENU_FILE";

#[derive(Debug, Clone, Deserialize)]
pub struct Entry {
    pub lhs: String,
    pub name: String,
    #[serde(default)]
    pub desc: String,
    /// "n" (default) or "x" (needs a visual selection first).
    #[serde(default)]
    pub mode: String,
}

impl Entry {
    fn visual(&self) -> bool {
        self.mode == "x"
    }

    /// `<leader>vf` shown as `␣vf`.
    fn keys_label(&self) -> String {
        self.lhs.replace("<leader>", "␣")
    }
}

pub struct Menu {
    entries: Vec<Entry>,
    query: String,
    shown: Vec<usize>,
    state: ListState,
    flash: Option<String>,
    theme: Theme,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Menu> {
    let entries = match std::env::var_os(MENU_FILE_ENV) {
        Some(p) => {
            let s = std::fs::read_to_string(p)?;
            serde_json::from_str(&s).map_err(io::Error::other)?
        }
        None => Vec::new(),
    };
    Ok(Menu::new(entries, ctx.theme))
}

impl Menu {
    pub fn new(entries: Vec<Entry>, theme: Theme) -> Self {
        let mut m = Self {
            entries,
            query: String::new(),
            shown: Vec::new(),
            state: ListState::default(),
            flash: None,
            theme,
        };
        m.refilter();
        m
    }

    /// Entries matching every whitespace-separated query term
    /// (case-insensitive over keys + name + description), in original order.
    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        let terms: Vec<&str> = q.split_whitespace().collect();
        self.shown = self
            .entries
            .iter()
            .enumerate()
            .filter(|(_, e)| {
                let hay = format!("{} {} {}", e.keys_label(), e.name, e.desc).to_lowercase();
                terms.iter().all(|t| hay.contains(t))
            })
            .map(|(i, _)| i)
            .collect();
        self.state
            .select(if self.shown.is_empty() { None } else { Some(0) });
    }

    fn step(&mut self, delta: isize) {
        let n = self.shown.len();
        if n > 0 {
            let cur = self.state.selected().unwrap_or(0) as isize;
            self.state
                .select(Some((cur + delta).rem_euclid(n as isize) as usize));
        }
    }

    fn current(&self) -> Option<&Entry> {
        self.state
            .selected()
            .and_then(|s| self.shown.get(s))
            .map(|&i| &self.entries[i])
    }

    fn run(&mut self) -> Action {
        let Some(e) = self.current() else {
            return Action::None;
        };
        if e.visual() {
            self.flash = Some(format!("select text first, then press {}", e.keys_label()));
            return Action::None;
        }
        Action::Nvim(NvimAction::Keys {
            keys: e.lhs.clone(),
        })
    }
}

impl Screen for Menu {
    fn leader_ok(&self) -> bool {
        false
    }

    fn needs_redraw(&self) -> bool {
        false
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [input, list, detail, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(3),
            Constraint::Length(1),
        ])
        .areas(area);

        let prefix = " finlarp › ";
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prefix, t.accent()),
                Span::styled(self.query.clone(), t.base()),
            ])),
            input,
        );
        frame.set_cursor_position((
            input.x + (text::width(prefix) + text::width(&self.query)) as u16,
            input.y,
        ));

        if self.shown.is_empty() {
            let msg = if self.entries.is_empty() {
                "  no keymaps passed in (run from nvim: <leader>v?)"
            } else {
                "  no match"
            };
            frame.render_widget(Paragraph::new(msg).style(t.dim()), list);
        } else {
            let key_w = self
                .shown
                .iter()
                .map(|&i| text::width(&self.entries[i].keys_label()))
                .max()
                .unwrap_or(0);
            let rows: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| {
                    let e = &self.entries[i];
                    let keys = e.keys_label();
                    let pad = " ".repeat(key_w.saturating_sub(text::width(&keys)));
                    let tag = if e.visual() { " (visual)" } else { "" };
                    ListItem::new(Line::from(vec![
                        Span::styled(format!("  {keys}{pad}  "), t.accent()),
                        Span::styled(format!("{}{tag}", e.name), t.base()),
                    ]))
                })
                .collect();
            frame.render_stateful_widget(
                List::new(rows)
                    .style(t.base())
                    .highlight_style(t.selected()),
                list,
                &mut self.state,
            );
        }

        if let Some(e) = self.current() {
            frame.render_widget(
                Paragraph::new(format!(" {}", e.desc))
                    .style(t.dim())
                    .wrap(Wrap { trim: false }),
                detail,
            );
        }
        let foot_text = self
            .flash
            .clone()
            .unwrap_or_else(|| " ^n/^p move · ↵ run · esc close".to_string());
        frame.render_widget(Paragraph::new(foot_text).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => Action::Quit,
            KeyCode::Enter => self.run(),
            KeyCode::Down | KeyCode::Tab => {
                self.step(1);
                Action::None
            }
            KeyCode::Up | KeyCode::BackTab => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('n' | 'j') if ctrl => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('p' | 'k') if ctrl => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('c') if ctrl => Action::Quit,
            KeyCode::Char('u') if ctrl => {
                self.query.clear();
                self.refilter();
                Action::None
            }
            KeyCode::Backspace => {
                self.query.pop();
                self.refilter();
                Action::None
            }
            KeyCode::Char(c) if !ctrl => {
                self.query.push(c);
                self.refilter();
                Action::None
            }
            _ => Action::None,
        }
    }
}

#[cfg(test)]
mod tests {
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn entry(lhs: &str, name: &str, desc: &str, mode: &str) -> Entry {
        Entry {
            lhs: lhs.into(),
            name: name.into(),
            desc: desc.into(),
            mode: mode.into(),
        }
    }

    fn menu() -> Menu {
        Menu::new(
            vec![
                entry("<leader>vf", "search filings", "full-text", "n"),
                entry("<leader>vd", "dossier", "one ticker", "n"),
                entry("<leader>vn", "new note (selection)", "visual", "x"),
            ],
            Theme::default(),
        )
    }

    fn press(m: &mut Menu, code: KeyCode) -> Action {
        m.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn type_str(m: &mut Menu, s: &str) {
        for c in s.chars() {
            press(m, KeyCode::Char(c));
        }
    }

    #[test]
    fn enter_sends_the_keymap() {
        let mut m = menu();
        assert_eq!(
            press(&mut m, KeyCode::Enter),
            Action::Nvim(NvimAction::Keys {
                keys: "<leader>vf".into()
            })
        );
    }

    #[test]
    fn typing_filters_over_keys_name_and_desc() {
        let mut m = menu();
        type_str(&mut m, "ticker");
        assert_eq!(m.shown, vec![1]);
        press(&mut m, KeyCode::Backspace);
        type_str(&mut m, "r"); // "ticker" again after pop+push
        assert_eq!(m.shown, vec![1]);
        m.query.clear();
        m.refilter();
        type_str(&mut m, "␣vf");
        assert_eq!(m.shown, vec![0]);
    }

    #[test]
    fn visual_entry_flashes_instead_of_running() {
        let mut m = menu();
        type_str(&mut m, "note");
        assert_eq!(press(&mut m, KeyCode::Enter), Action::None);
        assert!(
            m.flash
                .as_deref()
                .is_some_and(|f| f.contains("select text"))
        );
    }

    #[test]
    fn esc_quits_and_no_match_enter_is_noop() {
        let mut m = menu();
        type_str(&mut m, "zzzz");
        assert_eq!(press(&mut m, KeyCode::Enter), Action::None);
        assert_eq!(press(&mut m, KeyCode::Esc), Action::Quit);
    }
}
