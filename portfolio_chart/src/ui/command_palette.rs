use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Rect};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    Block, Clear, List, ListItem, ListState, Paragraph, StatefulWidget, Widget,
};

use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Command {
    Screen(&'static str),
    Picker(&'static str),
    Section(usize),
    Pane(u8),
    Range(u8),
}

#[derive(Debug, Clone)]
pub struct Entry {
    pub label: String,
    pub detail: String,
    pub command: Command,
}

pub fn destinations(symbol: &str, picker: &'static str) -> Vec<Entry> {
    let mut screens: Vec<&str> = if symbol.is_empty() {
        vec!["chart", "search"]
    } else {
        vec!["chart", "canslim", "dossier", "search"]
    };
    if symbol.eq_ignore_ascii_case("MRVL") {
        screens.push("earnings");
    }
    let mut entries: Vec<Entry> = screens
        .into_iter()
        .map(|screen| Entry::new(format!("Open {screen}"), symbol, Command::Screen(screen)))
        .collect();
    // the chart is the portfolio, not a ticker: nvim has no chart picker
    if picker != "chart" {
        entries.push(Entry::new(
            "Choose another ticker",
            "open symbol picker",
            Command::Picker(picker),
        ));
    }
    if symbol.is_empty() {
        entries.push(Entry::new(
            "Choose ticker for CANSLIM",
            "open symbol picker",
            Command::Picker("canslim"),
        ));
        entries.push(Entry::new(
            "Choose ticker for dossier",
            "open symbol picker",
            Command::Picker("dossier"),
        ));
        entries.push(Entry::new(
            "Open Marvell earnings report POC",
            "hard-coded structured report · MRVL",
            Command::Screen("earnings"),
        ));
    }
    entries
}

impl Entry {
    pub fn new(label: impl Into<String>, detail: impl Into<String>, command: Command) -> Self {
        Self {
            label: label.into(),
            detail: detail.into(),
            command,
        }
    }
}

#[cfg(test)]
mod earnings_poc_tests {
    use super::*;

    #[test]
    fn report_menu_entry_is_available_only_for_its_hard_coded_ticker() {
        assert!(
            destinations("MRVL", "dossier")
                .iter()
                .any(|e| e.command == Command::Screen("earnings"))
        );
        assert!(
            !destinations("NVDA", "dossier")
                .iter()
                .any(|e| e.command == Command::Screen("earnings"))
        );
        assert!(
            destinations("", "dossier")
                .iter()
                .any(|e| e.label.contains("Marvell earnings report"))
        );
    }
}

#[derive(Debug, Default)]
pub struct Palette {
    pub open: bool,
    query: String,
    entries: Vec<Entry>,
    state: ListState,
}

impl Palette {
    pub fn show(&mut self, entries: Vec<Entry>) {
        self.open = true;
        self.query.clear();
        self.entries = entries;
        self.state.select(Some(0));
    }

    pub fn handle(&mut self, key: KeyEvent) -> Option<Option<Command>> {
        if !self.open {
            return None;
        }
        match key.code {
            KeyCode::Esc => self.open = false,
            KeyCode::Enter => {
                let command = self
                    .visible()
                    .get(self.state.selected().unwrap_or(0))
                    .map(|e| e.command);
                self.open = false;
                return Some(command);
            }
            KeyCode::Up | KeyCode::Char('k') if key.modifiers.is_empty() => {
                self.state.select_previous()
            }
            KeyCode::Down | KeyCode::Char('j') if key.modifiers.is_empty() => {
                self.state.select_next()
            }
            KeyCode::Backspace => {
                self.query.pop();
                self.state.select(Some(0));
            }
            KeyCode::Char(c)
                if !key
                    .modifiers
                    .intersects(KeyModifiers::CONTROL | KeyModifiers::ALT) =>
            {
                self.query.push(c);
                self.state.select(Some(0));
            }
            _ => {}
        }
        let len = self.visible().len();
        if len == 0 {
            self.state.select(None);
        } else if self.state.selected().is_none_or(|i| i >= len) {
            self.state.select(Some(len - 1));
        }
        Some(None)
    }

    fn visible(&self) -> Vec<&Entry> {
        let q = self.query.to_lowercase();
        self.entries
            .iter()
            .filter(|e| e.label.to_lowercase().contains(&q) || e.detail.to_lowercase().contains(&q))
            .collect()
    }

    pub fn render(&mut self, frame: &mut Frame, area: Rect, theme: &Theme) {
        let q = self.query.clone();
        let visible = self.visible();
        let width = area.width.clamp(1, 72);
        let height = area.height.min((visible.len() as u16 + 4).clamp(6, 18));
        let rect = area.centered(Constraint::Length(width), Constraint::Length(height));
        let selected = self.state.selected().unwrap_or(0);
        frame.render_widget(
            PaletteWidget {
                query: &q,
                entries: visible,
                selected,
                theme,
            },
            rect,
        );
        if !rect.is_empty() {
            let query_width = text::width(&q).min(u16::MAX as usize) as u16;
            frame.set_cursor_position((
                rect.x
                    .saturating_add(2u16.saturating_add(query_width))
                    .min(rect.right().saturating_sub(1)),
                rect.y.saturating_add(1),
            ));
        }
    }
}

struct PaletteWidget<'a> {
    query: &'a str,
    entries: Vec<&'a Entry>,
    selected: usize,
    theme: &'a Theme,
}

impl Widget for PaletteWidget<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if area.is_empty() {
            return;
        }
        let th = self.theme;
        Clear.render(area, buf);
        let block = Block::bordered()
            .title(" Commands · type to filter · esc close ")
            .border_style(th.accent())
            .style(th.base());
        let inner = block.inner(area);
        block.render(area, buf);
        if inner.height == 0 {
            return;
        }
        Paragraph::new(Line::from(vec![
            Span::styled("> ", th.accent()),
            Span::styled(self.query, th.base()),
        ]))
        .render(Rect { height: 1, ..inner }, buf);
        if inner.height <= 1 {
            return;
        }
        let selected =
            (!self.entries.is_empty()).then(|| self.selected.min(self.entries.len() - 1));
        let items: Vec<ListItem> = if self.entries.is_empty() {
            vec![ListItem::new(Line::styled(
                "  no matching commands",
                th.dim(),
            ))]
        } else {
            self.entries
                .into_iter()
                .map(|e| {
                    ListItem::new(Line::from(vec![
                        Span::styled(format!("{}  ", e.label), th.title()),
                        Span::styled(e.detail.as_str(), th.dim()),
                    ]))
                })
                .collect()
        };
        let list = List::new(items)
            .highlight_style(th.selected().add_modifier(Modifier::BOLD))
            .highlight_symbol("▌ ");
        let mut state = ListState::default().with_selected(selected);
        StatefulWidget::render(
            list,
            Rect {
                y: inner.y + 1,
                height: inner.height - 1,
                ..inner
            },
            buf,
            &mut state,
        );
    }
}
