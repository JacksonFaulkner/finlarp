// EDGAR filing search: the 8-K / 6-K family by default (the "Filing index and
// 8-K / 6-K events" dataset), over py/derive/filing_search.py. Type a query and
// press Enter to run it; Tab moves into the results, and Enter on a row opens
// the filing's index page in the document viewer.
//
//   ┌ filings › t:INTC item:5.02▏                              38 filings ┐
//   │ date        ticker  form   items         what                       │
//   │ 2026-04-24  INTC    8-K    5.02,9.01    5.02 Departure/Election …   │
//   └ enter run · tab results · ↵ open filing · esc close ───────────────┘
//
// The query runs in a background process (spawn_script), so typing never
// blocks on DuckDB. Results arrive on tick().

use std::io;
use std::sync::mpsc::{Receiver, TryRecvError};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};
use serde::Deserialize;

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::pyrun;
use crate::ui::text;
use crate::ui::theme::Theme;

const SCRIPT: &str = "py/derive/filing_search.py";
const LIMIT: &str = "200";

/// One filing, as filing_search.py prints it.
#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct Filing {
    pub ticker: String,
    pub form: String,
    pub filed: String,
    #[serde(default)]
    pub items: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub labels: String,
    #[serde(default)]
    pub tier: i64,
    pub url: String,
}

#[derive(PartialEq, Clone, Copy)]
enum Focus {
    Query,
    Results,
}

pub struct Filings {
    theme: Theme,
    query: String,
    /// The query that produced `rows`, so a changed query is visible until Enter.
    ran: String,
    focus: Focus,
    rows: Vec<Filing>,
    sel: usize,
    status: String,
    pending: Option<Receiver<Result<String, String>>>,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Filings> {
    let mut s = Filings {
        theme: ctx.theme,
        query: arg.unwrap_or_default(),
        ran: String::new(),
        focus: Focus::Query,
        rows: Vec::new(),
        sel: 0,
        status: "searching…".into(),
        pending: None,
    };
    s.run();
    Ok(s)
}

/// Parses the `--json` rows; any other output is an error.
pub fn parse_rows(json: &str) -> Result<Vec<Filing>, String> {
    serde_json::from_str(json).map_err(|e| format!("filing_search: {e}"))
}

impl Filings {
    fn run(&mut self) {
        self.ran = self.query.clone();
        self.status = "searching…".into();
        self.pending = Some(pyrun::spawn_script(
            SCRIPT,
            &["q", &self.query, "--json", "-k", LIMIT],
        ));
    }

    fn apply(&mut self, r: Result<String, String>) {
        match r.and_then(|json| parse_rows(&json)) {
            Ok(rows) => {
                self.status = format!("{} filings", rows.len());
                self.rows = rows;
                self.sel = 0;
            }
            Err(e) => {
                self.status = e.lines().next().unwrap_or("error").to_string();
                self.rows.clear();
            }
        }
    }

    fn selected(&self) -> Option<&Filing> {
        self.rows.get(self.sel)
    }
}

impl Screen for Filings {
    fn tick(&mut self) -> Action {
        if let Some(rx) = &self.pending {
            match rx.try_recv() {
                Ok(r) => {
                    self.pending = None;
                    self.apply(r);
                }
                Err(TryRecvError::Empty) => {}
                Err(TryRecvError::Disconnected) => {
                    self.pending = None;
                    self.status = "search process exited".into();
                }
            }
        }
        Action::None
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, cols, body, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);

        let cursor = if self.focus == Focus::Query {
            "▏"
        } else {
            ""
        };
        let stale = if self.query != self.ran {
            "  (enter to run)"
        } else {
            ""
        };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" filings › ", t.title()),
                Span::styled(format!("{}{cursor}", self.query), t.base()),
                Span::styled(format!("{stale}   {}", self.status), t.dim()),
            ])),
            head,
        );
        frame.render_widget(
            Paragraph::new(Line::styled(
                format!(
                    " {:<11} {:<6} {:<7} {:<14} what",
                    "date", "ticker", "form", "items"
                ),
                t.dim(),
            )),
            cols,
        );

        if self.rows.is_empty() {
            let msg = if self.pending.is_some() {
                ""
            } else {
                " no filings match. Default scope is 8-K and 6-K; add form:10-Q to widen it."
            };
            frame.render_widget(Paragraph::new(msg).style(t.dim()), body);
        } else {
            let width = body.width as usize;
            let rows_visible = body.height.max(1) as usize;
            let first = self.sel.saturating_sub(rows_visible - 1);
            let mut lines = Vec::new();
            for (i, f) in self.rows.iter().enumerate().skip(first).take(rows_visible) {
                let selected = i == self.sel && self.focus == Focus::Results;
                let what = if f.labels.is_empty() {
                    &f.description
                } else {
                    &f.labels
                };
                let line = format!(
                    " {:<11} {:<6} {:<7} {:<14} {}",
                    f.filed,
                    text::truncate(&f.ticker, 6),
                    text::truncate(&f.form, 7),
                    text::truncate(&f.items, 14),
                    what
                );
                let line = text::truncate(&line, width);
                let style = if selected {
                    t.selected()
                } else if f.tier >= 3 {
                    t.accent().add_modifier(Modifier::BOLD)
                } else {
                    t.base()
                };
                lines.push(Line::styled(line, style));
            }
            frame.render_widget(Paragraph::new(lines).style(t.base()), body);
        }

        let hint = match self.focus {
            Focus::Query => " enter run · tab results · esc close",
            Focus::Results => " j/k move · ↵ open filing · / or tab back to query · esc back",
        };
        frame.render_widget(Paragraph::new(Line::styled(hint, t.dim())), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        match self.focus {
            Focus::Query => match key.code {
                KeyCode::Esc => return Action::Quit,
                KeyCode::Enter => self.run(),
                KeyCode::Tab if !self.rows.is_empty() => self.focus = Focus::Results,
                KeyCode::Backspace => {
                    self.query.pop();
                }
                KeyCode::Char(c) => self.query.push(c),
                _ => {}
            },
            Focus::Results => match key.code {
                KeyCode::Esc | KeyCode::Char('q') => return Action::Quit,
                KeyCode::Char('/') | KeyCode::Tab => self.focus = Focus::Query,
                KeyCode::Char('j') | KeyCode::Down => {
                    self.sel = (self.sel + 1).min(self.rows.len().saturating_sub(1))
                }
                KeyCode::Char('k') | KeyCode::Up => self.sel = self.sel.saturating_sub(1),
                KeyCode::Char('g') => self.sel = 0,
                KeyCode::Char('G') => self.sel = self.rows.len().saturating_sub(1),
                KeyCode::Enter => {
                    if let Some(f) = self.selected() {
                        return Action::Nvim(NvimAction::Docview {
                            url: f.url.clone(),
                            quote: None,
                        });
                    }
                }
                _ => {}
            },
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.pending.is_some()
    }

    /// Typing searches: space is a plain character in the query box.
    fn leader_ok(&self) -> bool {
        self.focus == Focus::Results
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_the_json_rows_filing_search_prints() {
        let json = r#"[{"ticker":"INTC","cik":50863,"form":"8-K","filed":"2026-04-24","accn":"0000050863-26-000100",
            "primary_doc":"x.htm","items":"5.02,9.01","description":"8-K","labels":"5.02 Departure","tier":3,
            "is_predecessor":false,"url":"https://www.sec.gov/Archives/edgar/data/50863/000005086326000100/0000050863-26-000100-index.htm"}]"#;
        let rows = parse_rows(json).unwrap();
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].ticker, "INTC");
        assert_eq!(rows[0].tier, 3);
        assert!(rows[0].url.ends_with("-index.htm"));
        assert!(parse_rows("Traceback (most recent call last):").is_err());
    }
}
