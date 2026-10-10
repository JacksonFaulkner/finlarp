// `fl` / `fl .`: the front door. One list of every screen; Enter opens it,
// and q/esc inside that screen comes back here.
//
//   finlarp
//   > Portfolio          positions, risk, activity
//     History chart      daily portfolio value
//     ...

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::theme::Theme;

/// (title, screen, description, key). Screens that need a ticker open the
/// ticker picker when given none.
const ENTRIES: &[(&str, &str, &str, char)] = &[
    (
        "Portfolio",
        "portfolio",
        "positions, exposure, risk, activity",
        'p',
    ),
    ("History chart", "chart", "daily portfolio value", 'h'),
    ("CANSLIM", "canslim", "scorecard for one ticker", 'c'),
    (
        "Dossier",
        "dossier",
        "sourced research file for one ticker",
        'd',
    ),
    (
        "Filing search",
        "search",
        "full-text search over SEC filings",
        's',
    ),
    (
        "AI universe",
        "universe",
        "browse the buckets and regions",
        'u',
    ),
    (
        "Earnings report",
        "earnings",
        "latest earnings research report",
        'e',
    ),
    (
        "Diagrams",
        "diagrams",
        "chip fab, fiber optics, data center power",
        'x',
    ),
    ("Events", "events", "catalyst calendar", 'v'),
];

pub struct Home {
    state: ListState,
    theme: Theme,
}

pub fn open(ctx: &Ctx) -> io::Result<Home> {
    Ok(Home {
        state: ListState::default().with_selected(Some(0)),
        theme: ctx.theme,
    })
}

impl Home {
    fn step(&mut self, delta: isize) {
        let cur = self.state.selected().unwrap_or(0) as isize;
        self.state.select(Some(
            (cur + delta).rem_euclid(ENTRIES.len() as isize) as usize
        ));
    }

    fn open_at(&self, i: usize) -> Action {
        Action::Nvim(NvimAction::Screen {
            screen: ENTRIES[i].1.into(),
            arg: None,
        })
    }
}

impl Screen for Home {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, list, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);
        frame.render_widget(
            Paragraph::new(Line::from(Span::styled(" finlarp", t.title()))),
            head,
        );
        let rows: Vec<ListItem> = ENTRIES
            .iter()
            .map(|(title, _, desc, key)| {
                ListItem::new(Line::from(vec![
                    Span::styled(format!("  {key}  "), t.accent()),
                    Span::styled(format!("{title:<18}"), t.base()),
                    Span::styled((*desc).to_string(), t.dim()),
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
        frame.render_widget(
            Paragraph::new(" j/k move · ↵ open · letter jumps · q quit").style(t.dim()),
            foot,
        );
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if key.modifiers.contains(KeyModifiers::CONTROL) {
            return match key.code {
                KeyCode::Char('n' | 'j') => {
                    self.step(1);
                    Action::None
                }
                KeyCode::Char('p' | 'k') => {
                    self.step(-1);
                    Action::None
                }
                _ => Action::None,
            };
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => Action::Quit,
            KeyCode::Char('j') | KeyCode::Down => {
                self.step(1);
                Action::None
            }
            KeyCode::Char('k') | KeyCode::Up => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('g') | KeyCode::Home => {
                self.state.select(Some(0));
                Action::None
            }
            KeyCode::Char('G') | KeyCode::End => {
                self.state.select(Some(ENTRIES.len() - 1));
                Action::None
            }
            KeyCode::Enter => self.open_at(self.state.selected().unwrap_or(0)),
            KeyCode::Char(c) => match ENTRIES.iter().position(|e| e.3 == c) {
                Some(i) => self.open_at(i),
                None => Action::None,
            },
            _ => Action::None,
        }
    }

    fn needs_redraw(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState};

    use super::*;

    fn press(h: &mut Home, code: KeyCode) -> Action {
        h.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn opens(screen: &str) -> Action {
        Action::Nvim(NvimAction::Screen {
            screen: screen.into(),
            arg: None,
        })
    }

    #[test]
    fn enter_and_hotkeys_open_screens() {
        let mut h = open(&Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        })
        .expect("open");
        assert_eq!(press(&mut h, KeyCode::Enter), opens("portfolio"));
        press(&mut h, KeyCode::Char('j'));
        assert_eq!(press(&mut h, KeyCode::Enter), opens("chart"));
        assert_eq!(press(&mut h, KeyCode::Char('d')), opens("dossier"));
        assert_eq!(press(&mut h, KeyCode::Char('z')), Action::None);
        assert_eq!(press(&mut h, KeyCode::Char('q')), Action::Quit);
    }

    #[test]
    fn hotkeys_are_unique_and_screens_known() {
        for (i, a) in ENTRIES.iter().enumerate() {
            assert!(crate::SCREENS.contains(&a.1), "{} unknown", a.1);
            assert!(
                ENTRIES[i + 1..].iter().all(|b| b.3 != a.3),
                "dup key {}",
                a.3
            );
        }
    }
}
