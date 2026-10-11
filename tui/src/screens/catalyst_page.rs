// Catalyst page: the detail view behind an event on the catalyst calendar.
// Header (tickers, when, how sure the date is), an optional ratio strip, then
// a left pane of tabbed text and a right pane of bar groups. Data lives in
// fixtures/catalyst_pages.json, one page per (date, label) of catalysts.json.
//
//   h/l  ←/→      previous / next tab
//   j/k  ↓/↑      scroll the bars
//   space         page down
//   [ ]           previous / next page
//   q  esc        back to the calendar

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use serde::Deserialize;

use crate::ui::help::{Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

pub const KEYS: &[Key] = &[
    key("h/l", "tab"),
    key("j/k", "scroll"),
    key("space", "page"),
    key("[ ]", "prev / next page"),
    key("q", "back"),
];

#[derive(Debug, Deserialize)]
pub struct Page {
    date: String,
    label: String,
    title: String,
    tickers: String,
    when: String,
    /// "confirmed" | "estimated" | "unconfirmed"
    status: String,
    strip: Option<Strip>,
    tabs: Vec<Tab>,
    groups: Vec<Group>,
}

#[derive(Debug, Deserialize)]
struct Strip {
    label: String,
    left: (String, f64),
    right: (String, f64),
    note: String,
}

#[derive(Debug, Deserialize)]
struct Tab {
    name: String,
    text: String,
}

#[derive(Debug, Deserialize)]
struct Group {
    title: String,
    rows: Vec<Row>,
    foot: Option<String>,
}

#[derive(Debug, Deserialize)]
struct Row {
    label: String,
    value: f64,
    unit: String,
    /// "actual" | "guide" | anything else (consensus, derived, estimate)
    kind: String,
    note: Option<String>,
}

pub fn load() -> Vec<Page> {
    let mut pages: Vec<Page> = serde_json::from_str(include_str!("fixtures/catalyst_pages.json"))
        .expect("catalyst_pages.json");
    pages.sort_by(|a, b| a.date.cmp(&b.date));
    pages
}

/// Index of the page for a calendar event; a leading `~` (estimated date) on
/// the label is ignored.
pub fn find(pages: &[Page], date: NaiveDate, label: &str) -> Option<usize> {
    let date = date.format("%Y-%m-%d").to_string();
    let label = label.trim_start_matches('~');
    pages
        .iter()
        .position(|p| p.date == date && p.label == label)
}

#[derive(Debug, PartialEq, Eq)]
pub enum Outcome {
    Stay,
    Close,
}

pub struct View {
    idx: usize,
    tab: usize,
    scroll: u16,
    /// Rows the bar pane can show, set at draw time for paging and clamping.
    pane_h: u16,
    total: u16,
}

impl View {
    pub fn new(idx: usize) -> Self {
        Self {
            idx,
            tab: 0,
            scroll: 0,
            pane_h: 0,
            total: 0,
        }
    }

    fn goto(&mut self, idx: usize) {
        self.idx = idx;
        self.tab = 0;
        self.scroll = 0;
    }

    fn max_scroll(&self) -> u16 {
        self.total.saturating_sub(self.pane_h)
    }

    pub fn on_key(&mut self, pages: &[Page], key: KeyEvent) -> Outcome {
        let tabs = pages[self.idx].tabs.len();
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Outcome::Close,
            KeyCode::Char('l') | KeyCode::Right => self.tab = (self.tab + 1) % tabs,
            KeyCode::Char('h') | KeyCode::Left => self.tab = (self.tab + tabs - 1) % tabs,
            KeyCode::Char('j') | KeyCode::Down => {
                self.scroll = (self.scroll + 1).min(self.max_scroll())
            }
            KeyCode::Char('k') | KeyCode::Up => self.scroll = self.scroll.saturating_sub(1),
            KeyCode::Char(' ') | KeyCode::PageDown => {
                self.scroll = (self.scroll + self.pane_h.max(1)).min(self.max_scroll())
            }
            KeyCode::PageUp => self.scroll = self.scroll.saturating_sub(self.pane_h.max(1)),
            KeyCode::Char('g') => self.scroll = 0,
            KeyCode::Char('G') => self.scroll = self.max_scroll(),
            KeyCode::Char(']') if self.idx + 1 < pages.len() => self.goto(self.idx + 1),
            KeyCode::Char('[') if self.idx > 0 => self.goto(self.idx - 1),
            _ => {}
        }
        Outcome::Stay
    }

    pub fn draw(&mut self, pages: &[Page], frame: &mut Frame, area: Rect, th: &Theme) {
        let page = &pages[self.idx];
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(th.accent())
            .title(Span::styled(
                format!(" {} ", page.title),
                th.accent().add_modifier(Modifier::BOLD),
            ))
            .style(th.base());
        let inner = block.inner(area);
        frame.render_widget(block, area);
        if inner.width < 20 || inner.height < 6 {
            return;
        }
        let inner = Rect {
            x: inner.x + 1,
            width: inner.width - 2,
            ..inner
        };

        let strip_h = u16::from(page.strip.is_some());
        let [head, strip, _, rule, body] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(strip_h),
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .areas(inner);

        frame.render_widget(Paragraph::new(header_line(page, th)).style(th.base()), head);
        if let Some(s) = &page.strip {
            frame.render_widget(Paragraph::new(strip_line(s, th)).style(th.base()), strip);
        }
        let line = "─".repeat(rule.width as usize);
        frame.render_widget(
            Paragraph::new(Line::styled(line, th.border())).style(th.base()),
            rule,
        );

        let [left, _, right] = Layout::horizontal([
            Constraint::Percentage(42),
            Constraint::Length(3),
            Constraint::Min(0),
        ])
        .areas(body);
        self.draw_left(page, frame, left, th);
        self.draw_right(page, frame, right, th);
    }

    fn draw_left(&self, page: &Page, frame: &mut Frame, area: Rect, th: &Theme) {
        let [tabs, _, text_area] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(0),
        ])
        .areas(area);
        let mut spans = Vec::new();
        for (i, t) in page.tabs.iter().enumerate() {
            let label = format!(" {} ", t.name);
            spans.push(if i == self.tab {
                Span::styled(label, th.selected().add_modifier(Modifier::BOLD))
            } else {
                Span::styled(label, th.dim())
            });
            spans.push(Span::raw(" "));
        }
        frame.render_widget(Paragraph::new(Line::from(spans)).style(th.base()), tabs);
        let body = &page.tabs[self.tab].text;
        frame.render_widget(
            Paragraph::new(body.as_str())
                .style(th.base())
                .wrap(Wrap { trim: false }),
            text_area,
        );
    }

    fn draw_right(&mut self, page: &Page, frame: &mut Frame, area: Rect, th: &Theme) {
        let lines = bar_lines(page, area.width as usize, th);
        self.pane_h = area.height;
        self.total = lines.len() as u16;
        self.scroll = self.scroll.min(self.max_scroll());
        frame.render_widget(
            Paragraph::new(lines)
                .style(th.base())
                .scroll((self.scroll, 0)),
            area,
        );
    }
}

fn header_line(page: &Page, th: &Theme) -> Line<'static> {
    let status_style = match page.status.as_str() {
        "confirmed" => th.up(),
        "unconfirmed" => th.down(),
        _ => th.dim(),
    };
    Line::from(vec![
        Span::styled(
            page.tickers.clone(),
            th.accent().add_modifier(Modifier::BOLD),
        ),
        Span::styled("   ·   ", th.dim()),
        Span::styled(page.when.clone(), th.base()),
        Span::styled("   ", th.dim()),
        Span::styled(format!("[{}]", page.status), status_style),
    ])
}

/// A proportional two-colour bar, like the mass strip on the diagrams pages.
fn strip_line(s: &Strip, th: &Theme) -> Line<'static> {
    const W: usize = 36;
    let total = (s.left.1 + s.right.1).max(f64::EPSILON);
    let l = ((s.left.1 / total) * W as f64).round() as usize;
    let l = l.min(W);
    Line::from(vec![
        Span::styled(format!("{:<14}", s.label), th.dim()),
        Span::styled("█".repeat(l), Style::new().fg(th.accent)),
        Span::styled("█".repeat(W - l), Style::new().fg(th.up)),
        Span::styled(
            format!(
                "  {} {:.0}%  {} {:.0}%  ({})",
                s.left.0, s.left.1, s.right.0, s.right.1, s.note
            ),
            th.dim(),
        ),
    ])
}

fn bar_lines(page: &Page, width: usize, th: &Theme) -> Vec<Line<'static>> {
    const LABEL_W: usize = 20;
    const VALUE_W: usize = 14;
    let bar_max = width.saturating_sub(LABEL_W + VALUE_W + 2).max(4);
    let mut out: Vec<Line<'static>> = Vec::new();
    for g in &page.groups {
        out.push(Line::from(vec![
            Span::styled("▌ ", th.accent()),
            Span::styled(g.title.clone(), th.accent().add_modifier(Modifier::BOLD)),
        ]));
        out.push(Line::raw(""));
        let max = g.rows.iter().map(|r| r.value).fold(f64::EPSILON, f64::max);
        for r in &g.rows {
            // a lone row has nothing to be compared against: value only, no bar
            let n = if g.rows.len() < 2 {
                0
            } else {
                (((r.value / max) * bar_max as f64).round() as usize)
                    .max(usize::from(r.value > 0.0))
            };
            let color = match r.kind.as_str() {
                "actual" => th.up,
                "guide" => th.accent,
                _ => th.dim,
            };
            out.push(Line::from(vec![
                Span::styled(text::fit(&r.label, LABEL_W - 1, false) + " ", th.base()),
                Span::styled("█".repeat(n), Style::new().fg(color)),
                Span::styled(
                    format!(
                        "{}{} {}",
                        if n > 0 { " " } else { "" },
                        text::fmt_num(r.value),
                        r.unit
                    ),
                    if n > 0 {
                        th.base()
                    } else {
                        Style::new().fg(color)
                    },
                ),
            ]));
            if let Some(note) = &r.note {
                out.push(Line::styled(
                    format!(
                        "{}{}",
                        " ".repeat(LABEL_W),
                        text::truncate(&format!("({note})"), width.saturating_sub(LABEL_W))
                    ),
                    th.dim().add_modifier(Modifier::ITALIC),
                ));
            }
        }
        if let Some(foot) = &g.foot {
            for l in text::wrap(foot, width.saturating_sub(2).max(10)) {
                out.push(Line::styled(l, th.dim().add_modifier(Modifier::ITALIC)));
            }
        }
        out.push(Line::raw(""));
    }
    out.push(Line::from(vec![
        Span::styled("█ ", Style::new().fg(th.up)),
        Span::styled("actual   ", th.dim()),
        Span::styled("█ ", Style::new().fg(th.accent)),
        Span::styled("company guide   ", th.dim()),
        Span::styled("█ ", Style::new().fg(th.dim)),
        Span::styled("consensus / derived / other", th.dim()),
    ]));
    out
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState, KeyModifiers};

    use super::*;

    fn press(v: &mut View, pages: &[Page], c: KeyCode) -> Outcome {
        v.on_key(
            pages,
            KeyEvent {
                code: c,
                modifiers: KeyModifiers::NONE,
                kind: KeyEventKind::Press,
                state: KeyEventState::NONE,
            },
        )
    }

    fn render(v: &mut View, pages: &[Page], w: u16, h: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| v.draw(pages, f, f.area(), &Theme::default()))
            .unwrap();
        let buf = term.backend().buffer().clone();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| buf[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn every_page_has_data_and_matches_a_catalyst() {
        let pages = load();
        assert_eq!(pages.len(), 10);
        let cats: Vec<(String, String)> =
            serde_json::from_str::<Vec<serde_json::Value>>(include_str!("fixtures/catalysts.json"))
                .unwrap()
                .iter()
                .map(|c| {
                    (
                        c["date"].as_str().unwrap().into(),
                        c["label"].as_str().unwrap().into(),
                    )
                })
                .collect();
        for p in &pages {
            assert!(!p.tabs.is_empty() && !p.groups.is_empty(), "{}", p.title);
            assert!(p.groups.iter().all(|g| !g.rows.is_empty()), "{}", p.title);
            assert!(
                cats.contains(&(p.date.clone(), p.label.clone())),
                "no catalyst for {}",
                p.title
            );
        }
    }

    #[test]
    fn find_ignores_estimate_marker() {
        let pages = load();
        let d = NaiveDate::from_ymd_opt(2026, 11, 3).unwrap();
        assert!(find(&pages, d, "~AMD Q3").is_some());
        assert!(find(&pages, d, "nothing").is_none());
    }

    #[test]
    fn keys_switch_tabs_scroll_and_page() {
        let pages = load();
        let mut v = View::new(0);
        render(&mut v, &pages, 100, 24);
        press(&mut v, &pages, KeyCode::Char('l'));
        assert_eq!(v.tab, 1);
        press(&mut v, &pages, KeyCode::Char('h'));
        press(&mut v, &pages, KeyCode::Char('h'));
        assert_eq!(v.tab, pages[0].tabs.len() - 1);
        press(&mut v, &pages, KeyCode::Char('j'));
        assert!(v.scroll <= v.max_scroll());
        press(&mut v, &pages, KeyCode::Char(']'));
        assert_eq!((v.idx, v.tab, v.scroll), (1, 0, 0));
        assert_eq!(press(&mut v, &pages, KeyCode::Char('q')), Outcome::Close);
    }

    #[test]
    fn renders_header_strip_tabs_and_bars() {
        let pages = load();
        let i = find(
            &pages,
            NaiveDate::from_ymd_opt(2026, 11, 3).unwrap(),
            "AMD Q3",
        )
        .unwrap();
        let mut v = View::new(i);
        let s = render(&mut v, &pages, 110, 30);
        assert!(s.contains("AMD Q3 + AI GUIDE"));
        assert!(s.contains("[confirmed]"));
        assert!(s.contains("data center 58%"));
        assert!(s.contains("Setup") && s.contains("Bull / Bear"));
        assert!(s.contains("Q2 2026") && s.contains('█'));
        // tiny areas must not panic
        render(&mut v, &pages, 10, 4);
        render(&mut v, &pages, 40, 8);
    }
}
