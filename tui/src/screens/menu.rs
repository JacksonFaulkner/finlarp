// `fl menu`: every standalone `fl` command from the keys table (keys.rs), with
// what it does. Type to filter; Enter shows the highlighted command so it can
// be typed at the prompt.
//
//   finlarp › sea█
//   > fl search QUERY   search 10-K/20-F text, releases, guidance, patents
//   Search

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph, Wrap};

use crate::app::{Action, Ctx, Screen};
use crate::screens::keys::{self, Standalone};
use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Entry {
    /// The fl command (or key chord) that does it.
    pub cmd: String,
    /// What it does.
    pub name: String,
    /// The keys-table group it sits in.
    pub group: String,
}

/// Every row of the keys table that works in standalone `fl`.
fn entries() -> Vec<Entry> {
    keys::GROUPS
        .iter()
        .flat_map(|g| {
            g.rows
                .iter()
                .filter(|r| r.standalone == Standalone::Yes)
                .map(move |r| Entry {
                    cmd: r.cmd.into(),
                    name: r.what.into(),
                    group: g.title.into(),
                })
        })
        .collect()
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
    Ok(Menu::new(entries(), ctx.theme))
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
    /// (case-insensitive over command + name + group), in original order.
    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        let terms: Vec<&str> = q.split_whitespace().collect();
        self.shown = self
            .entries
            .iter()
            .enumerate()
            .filter(|(_, e)| {
                let hay = format!("{} {} {}", e.cmd, e.name, e.group).to_lowercase();
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

    fn show_command(&mut self) -> Action {
        if let Some(e) = self.current() {
            self.flash = Some(format!("type: {}", e.cmd));
        }
        Action::None
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
            frame.render_widget(Paragraph::new("  no match").style(t.dim()), list);
        } else {
            let cmd_w = self
                .shown
                .iter()
                .map(|&i| text::width(&self.entries[i].cmd))
                .max()
                .unwrap_or(0);
            let rows: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| {
                    let e = &self.entries[i];
                    let pad = " ".repeat(cmd_w.saturating_sub(text::width(&e.cmd)));
                    ListItem::new(Line::from(vec![
                        Span::styled(format!("  {}{pad}  ", e.cmd), t.accent()),
                        Span::styled(e.name.clone(), t.base()),
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
                Paragraph::new(format!(" {}", e.group))
                    .style(t.dim())
                    .wrap(Wrap { trim: false }),
                detail,
            );
        }
        let foot_text = self
            .flash
            .clone()
            .unwrap_or_else(|| " ^n/^p move · ↵ show command · esc close".to_string());
        frame.render_widget(Paragraph::new(foot_text).style(t.dim()), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => Action::Quit,
            KeyCode::Enter => self.show_command(),
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

    fn entry(cmd: &str, name: &str, group: &str) -> Entry {
        Entry {
            cmd: cmd.into(),
            name: name.into(),
            group: group.into(),
        }
    }

    fn menu() -> Menu {
        Menu::new(
            vec![
                entry("fl search QUERY", "search 10-K text", "Search"),
                entry("fl dossier TICKER", "one-ticker dossier", "Search"),
                entry("fl onboard", "onboard a ticker", "Other"),
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
    fn entries_come_from_the_standalone_keys() {
        let all = entries();
        assert!(!all.is_empty());
        assert!(
            all.iter()
                .all(|e| e.cmd.starts_with("fl ") || e.cmd.starts_with("space"))
        );
        assert!(all.iter().any(|e| e.cmd == "fl onboard"));
    }

    #[test]
    fn enter_shows_the_command() {
        let mut m = menu();
        assert_eq!(press(&mut m, KeyCode::Enter), Action::None);
        assert!(
            m.flash
                .as_deref()
                .is_some_and(|f| f.contains("fl search QUERY"))
        );
    }

    #[test]
    fn typing_filters_over_command_name_and_group() {
        let mut m = menu();
        type_str(&mut m, "ticker");
        assert_eq!(m.shown, vec![1, 2]);
        press(&mut m, KeyCode::Backspace);
        press(&mut m, KeyCode::Backspace);
        press(&mut m, KeyCode::Backspace);
        press(&mut m, KeyCode::Backspace);
        press(&mut m, KeyCode::Backspace);
        press(&mut m, KeyCode::Backspace);
        assert_eq!(m.shown, vec![0, 1, 2]);
        type_str(&mut m, "other");
        assert_eq!(m.shown, vec![2]);
    }

    #[test]
    fn esc_quits_and_no_match_enter_is_noop() {
        let mut m = menu();
        type_str(&mut m, "zzzz");
        assert_eq!(press(&mut m, KeyCode::Enter), Action::None);
        assert!(m.flash.is_none());
        assert_eq!(press(&mut m, KeyCode::Esc), Action::Quit);
    }
}
