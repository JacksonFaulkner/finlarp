// Type-to-filter list picker: the Rust replacement for the fzf-lua pickers.
// Every item carries a `value`; Enter opens `target` (a screen name) with
// that value as its argument. With `free_entry`, text that matches nothing
// can still be submitted (any ticker, not just the listed ones).
//
//   Dossier ›  nv█
//   > NVDA   NVIDIA Corp
//     NVTS   Navitas
//   ^n/^p move · ↵ open · esc back

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Clone)]
pub struct Item {
    pub label: String,
    pub detail: String,
    pub value: String,
}

pub struct Pick {
    prompt: String,
    target: &'static str,
    items: Vec<Item>,
    free_entry: bool,
    /// Shown when `items` is empty (nothing cached, etc.).
    empty_msg: String,
    query: String,
    shown: Vec<usize>,
    state: ListState,
    theme: Theme,
}

impl Pick {
    pub fn new(
        prompt: &str,
        target: &'static str,
        items: Vec<Item>,
        free_entry: bool,
        empty_msg: &str,
        theme: Theme,
    ) -> Self {
        let mut p = Self {
            prompt: prompt.to_string(),
            target,
            items,
            free_entry,
            empty_msg: empty_msg.to_string(),
            query: String::new(),
            shown: Vec::new(),
            state: ListState::default(),
            theme,
        };
        p.refilter();
        p
    }

    /// Items matching every whitespace-separated term of the query
    /// (case-insensitive substring over label + detail), in original order.
    fn refilter(&mut self) {
        let q = self.query.to_lowercase();
        let terms: Vec<&str> = q.split_whitespace().collect();
        self.shown = self
            .items
            .iter()
            .enumerate()
            .filter(|(_, it)| {
                let hay = format!("{} {}", it.label, it.detail).to_lowercase();
                terms.iter().all(|t| hay.contains(t))
            })
            .map(|(i, _)| i)
            .collect();
        self.state
            .select(if self.shown.is_empty() { None } else { Some(0) });
    }

    fn step(&mut self, delta: isize) {
        let n = self.shown.len();
        if n == 0 {
            return;
        }
        let cur = self.state.selected().unwrap_or(0) as isize;
        self.state
            .select(Some((cur + delta).rem_euclid(n as isize) as usize));
    }

    /// What Enter submits: the highlighted item, else (free entry) the typed text.
    fn submit(&self) -> Option<String> {
        if let Some(i) = self.state.selected().and_then(|s| self.shown.get(s)) {
            return Some(self.items[*i].value.clone());
        }
        let typed = self.query.trim();
        (self.free_entry && !typed.is_empty()).then(|| typed.to_uppercase())
    }
}

impl Screen for Pick {
    fn leader_ok(&self) -> bool {
        false
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [input, list, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let prefix = format!(" {} › ", self.prompt);
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(prefix.clone(), t.accent()),
                Span::styled(self.query.clone(), t.base()),
            ])),
            input,
        );
        frame.set_cursor_position((
            input.x + (text::width(&prefix) + text::width(&self.query)) as u16,
            input.y,
        ));

        if self.items.is_empty() && self.query.is_empty() {
            frame.render_widget(
                Paragraph::new(self.empty_msg.clone())
                    .style(t.dim())
                    .wrap(ratatui::widgets::Wrap { trim: false }),
                list,
            );
        } else if self.shown.is_empty() {
            let msg = if self.free_entry {
                format!("  no match. ↵ opens {:?}", self.query.trim().to_uppercase())
            } else {
                "  no match".to_string()
            };
            frame.render_widget(Paragraph::new(msg).style(t.dim()), list);
        } else {
            let label_w = self
                .shown
                .iter()
                .map(|&i| text::width(&self.items[i].label))
                .max()
                .unwrap_or(0)
                .min(40);
            let rows: Vec<ListItem> = self
                .shown
                .iter()
                .map(|&i| {
                    let it = &self.items[i];
                    let label = text::truncate(&it.label, label_w);
                    let pad = " ".repeat(label_w.saturating_sub(text::width(&label)));
                    let room = (list.width as usize).saturating_sub(label_w + 6);
                    ListItem::new(Line::from(vec![
                        Span::styled(format!("  {label}{pad}  "), t.base()),
                        Span::styled(text::truncate(&it.detail, room), t.dim()),
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

        frame.render_widget(
            Paragraph::new(" ^n/^p move · ↵ open · esc back").style(t.dim()),
            foot,
        );
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Esc => Action::Quit,
            KeyCode::Enter => match self.submit() {
                Some(value) => Action::Nvim(NvimAction::Screen {
                    screen: self.target.into(),
                    arg: Some(value),
                }),
                None => Action::None,
            },
            KeyCode::Down | KeyCode::Tab => {
                self.step(1);
                Action::None
            }
            KeyCode::Up | KeyCode::BackTab => {
                self.step(-1);
                Action::None
            }
            KeyCode::PageDown => {
                self.step(10);
                Action::None
            }
            KeyCode::PageUp => {
                self.step(-10);
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

    fn needs_redraw(&self) -> bool {
        false
    }
}

/// Held-ticker picker for `target` ("canslim" | "dossier"): symbols you have
/// traded, plus free entry for any other ticker.
pub fn open_symbols(ctx: &Ctx, target: &'static str) -> io::Result<Pick> {
    let (items, msg) = match super::portfolio::traded_symbols(&ctx.db_path) {
        Ok(syms) => (
            syms.into_iter()
                .map(|s| Item {
                    label: s.clone(),
                    detail: String::new(),
                    value: s,
                })
                .collect(),
            "No cached transactions yet. Type any ticker and press ↵.".to_string(),
        ),
        Err(e) => (Vec::new(), format!("{e}\n\nType any ticker and press ↵.")),
    };
    let prompt = match target {
        "canslim" => "CANSLIM",
        "dossier" => "Dossier",
        _ => "Ticker",
    };
    Ok(Pick::new(prompt, target, items, true, &msg, ctx.theme))
}

#[cfg(test)]
mod tests {
    use ratatui::crossterm::event::KeyEventState;

    use super::*;

    fn item(l: &str, d: &str) -> Item {
        Item {
            label: l.into(),
            detail: d.into(),
            value: l.into(),
        }
    }

    fn press(p: &mut Pick, code: KeyCode) -> Action {
        p.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: ratatui::crossterm::event::KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn pick(free: bool) -> Pick {
        Pick::new(
            "T",
            "dossier",
            vec![
                item("NVDA", "nvidia"),
                item("AMD", "advanced micro"),
                item("MU", "micron"),
            ],
            free,
            "",
            Theme::default(),
        )
    }

    fn typed(p: &mut Pick, s: &str) {
        for c in s.chars() {
            press(p, KeyCode::Char(c));
        }
    }

    #[test]
    fn filters_on_label_and_detail_terms() {
        let mut p = pick(false);
        assert_eq!(p.shown.len(), 3);
        typed(&mut p, "mic");
        assert_eq!(p.shown.len(), 2); // "advanced micro", "micron"
        typed(&mut p, " mu");
        assert_eq!(p.shown, vec![2]);
    }

    #[test]
    fn enter_opens_target_with_highlighted_value() {
        let mut p = pick(false);
        press(&mut p, KeyCode::Down);
        assert_eq!(
            press(&mut p, KeyCode::Enter),
            Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some("AMD".into())
            })
        );
    }

    #[test]
    fn free_entry_submits_typed_ticker_when_nothing_matches() {
        let mut p = pick(true);
        typed(&mut p, "zzz");
        assert!(p.shown.is_empty());
        assert_eq!(
            press(&mut p, KeyCode::Enter),
            Action::Nvim(NvimAction::Screen {
                screen: "dossier".into(),
                arg: Some("ZZZ".into())
            })
        );
        let mut p = pick(false);
        typed(&mut p, "zzz");
        assert_eq!(press(&mut p, KeyCode::Enter), Action::None);
    }

    #[test]
    fn selection_wraps() {
        let mut p = pick(false);
        press(&mut p, KeyCode::Up);
        assert_eq!(p.state.selected(), Some(2));
        press(&mut p, KeyCode::Down);
        assert_eq!(p.state.selected(), Some(0));
    }
}
