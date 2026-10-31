// `fl keys`: every finlarp screen and the fl command that opens it, plus the chords that
// work in any screen. Edit GROUPS below to keep it in step with main.rs and app.rs.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{Key, key, render_footer};
use crate::ui::text;
use crate::ui::theme::Theme;

const KEYS: &[Key] = &[
    key("j/k", "scroll"),
    key("g/G", "top / bottom"),
    key("q/esc", "back"),
];

/// Whether a key works in standalone `fl`. Every row here does.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Standalone {
    Yes,
}

pub struct Row {
    pub what: &'static str,
    /// The fl command that does the same thing.
    pub cmd: &'static str,
    pub standalone: Standalone,
}

use Standalone::Yes;

pub struct Group {
    pub title: &'static str,
    pub rows: &'static [Row],
}

pub const GROUPS: &[Group] = &[
    Group {
        title: "Screens",
        rows: &[
            Row {
                what: "watchlist, full screen",
                standalone: Yes,
                cmd: "fl watchlists",
            },
            Row {
                what: "catalyst calendar",
                standalone: Yes,
                cmd: "fl events [month|week|day] [t:TICKERS]",
            },
            Row {
                what: "diagrams",
                standalone: Yes,
                cmd: "fl diagrams",
            },
            Row {
                what: "data sources",
                standalone: Yes,
                cmd: "fl sources",
            },
            Row {
                what: "portfolio: equity, positions, activity",
                standalone: Yes,
                cmd: "fl portfolio",
            },
            Row {
                what: "AI universe heatmap",
                standalone: Yes,
                cmd: "fl universe",
            },
            Row {
                what: "intraday grid, live candle tapes",
                standalone: Yes,
                cmd: "fl intraday MKSI,WDC,WULF,APLD",
            },
            Row {
                what: "candlestick chart",
                standalone: Yes,
                cmd: "fl candles TICKER",
            },
        ],
    },
    Group {
        title: "Notes",
        rows: &[
            Row {
                what: "take a note; ↵ saves it and answers in the background",
                standalone: Yes,
                cmd: "fl note [ticker | text]",
            },
            Row {
                what: "browse notes; ↵ reopens the answering chat in tmux",
                standalone: Yes,
                cmd: "fl notes",
            },
            Row {
                what: "newest answered note only",
                standalone: Yes,
                cmd: "fl notes last",
            },
        ],
    },
    Group {
        title: "Claude",
        rows: &[
            Row {
                what: "toggle the Claude window",
                standalone: Yes,
                cmd: "space a c in any screen",
            },
            Row {
                what: "add the selected value to Claude's context",
                standalone: Yes,
                cmd: "space a s in a screen with a selection",
            },
            Row {
                what: "chat with Claude Code; tickers in replies open dossier or CANSLIM",
                standalone: Yes,
                cmd: "fl chat",
            },
        ],
    },
    Group {
        title: "Search",
        rows: &[
            Row {
                what: "search 10-K/20-F text, releases, guidance, patents",
                standalone: Yes,
                cmd: "fl search QUERY",
            },
            Row {
                what: "one-ticker dossier",
                standalone: Yes,
                cmd: "fl dossier TICKER",
            },
            Row {
                what: "CANSLIM scorecard",
                standalone: Yes,
                cmd: "fl canslim TICKER",
            },
            Row {
                what: "search E*TRADE transactions",
                standalone: Yes,
                cmd: "fl transactions",
            },
        ],
    },
    Group {
        title: "Other",
        rows: &[Row {
            what: "onboard a ticker: add, pull every dataset, build its dossier",
            standalone: Yes,
            cmd: "fl onboard",
        }],
    },
];

const WHAT_W: usize = 60;

pub struct Keys {
    theme: Theme,
    offset: u16,
    max: u16,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Keys> {
    Ok(Keys {
        theme: ctx.theme,
        offset: 0,
        max: 0,
    })
}

/// The whole table as lines: legend, then each group with a column header.
fn build(t: &Theme) -> Vec<Line<'static>> {
    let mut out: Vec<Line<'static>> = vec![
        Line::from(Span::styled("finlarp keys", t.title())),
        Line::from(Span::styled(
            "each screen is an fl command; the chords work wherever the screen allows them",
            t.dim(),
        )),
        Line::from(""),
    ];
    for group in GROUPS {
        out.push(Line::from(Span::styled(group.title, t.accent())));
        out.push(Line::from(Span::styled(
            format!("{}command", text::fit("what", WHAT_W, false)),
            t.dim(),
        )));
        for r in group.rows {
            out.push(Line::from(vec![
                Span::styled(text::fit(r.what, WHAT_W, false), t.base()),
                Span::styled(r.cmd, t.accent()),
            ]));
        }
        out.push(Line::from(""));
    }
    out
}

impl Screen for Keys {
    fn needs_redraw(&self) -> bool {
        false
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [body, foot] =
            Layout::vertical([Constraint::Min(1), Constraint::Length(1)]).areas(area);
        let lines = build(&t);
        self.max = (lines.len() as u16).saturating_sub(body.height);
        self.offset = self.offset.min(self.max);
        frame.render_widget(Paragraph::new(lines).scroll((self.offset, 0)), body);
        render_footer(frame, foot, KEYS, None, &t);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        let page = 10u16;
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('j') | KeyCode::Down => self.offset = (self.offset + 1).min(self.max),
            KeyCode::Char('k') | KeyCode::Up => self.offset = self.offset.saturating_sub(1),
            KeyCode::PageDown => self.offset = (self.offset + page).min(self.max),
            KeyCode::PageUp => self.offset = self.offset.saturating_sub(page),
            KeyCode::Char('g') | KeyCode::Home => self.offset = 0,
            KeyCode::Char('G') | KeyCode::End => self.offset = self.max,
            _ => {}
        }
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_row_is_filled_in() {
        for g in GROUPS {
            assert!(!g.rows.is_empty(), "{} has no rows", g.title);
            for r in g.rows {
                assert!(
                    !r.cmd.is_empty() && !r.what.is_empty(),
                    "{}: empty row",
                    g.title
                );
            }
        }
    }

    #[test]
    fn groups_are_in_order() {
        let titles: Vec<&str> = GROUPS.iter().map(|g| g.title).collect();
        assert_eq!(titles, ["Screens", "Notes", "Claude", "Search", "Other"]);
    }
}
