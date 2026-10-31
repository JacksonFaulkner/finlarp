// `fl keys`: every finlarp key, grouped by what it does, and whether it works in standalone
// `fl` (no nvim). Source of truth: the `maps` table in the nvim config
// (~/.config/nvim/lua/plugins/finlarp.lua, which also builds the <leader>v? menu), plus the
// Claude chords routed in app.rs. Edit GROUPS below to keep it in step.
//
// Keys are written with the nvim leader shown as ␣ (space), so ␣vf is <leader>vf.

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

/// Whether a key works in standalone `fl`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Standalone {
    /// Works in fl; the row's `cmd` says how.
    Yes,
    /// Not in fl: nvim-only feature with no fl screen yet.
    No,
    /// Depends on nvim state: cursor word, visual selection, window splits, nvim's notes index or menu.
    NeedsNvim,
}

impl Standalone {
    fn label(self) -> &'static str {
        match self {
            Self::Yes => "yes",
            Self::No => "no",
            Self::NeedsNvim => "needs nvim",
        }
    }
}

pub struct Row {
    pub keys: &'static str,
    pub what: &'static str,
    pub standalone: Standalone,
    /// The fl command that does the same thing, or "" when there is none.
    pub cmd: &'static str,
}

pub struct Group {
    pub title: &'static str,
    pub rows: &'static [Row],
}

use Standalone::{NeedsNvim, No, Yes};

pub const GROUPS: &[Group] = &[
    Group {
        title: "Screens",
        rows: &[
            Row {
                keys: "␣ww",
                what: "watchlist, full screen",
                standalone: Yes,
                cmd: "fl watchlists",
            },
            Row {
                keys: "␣wl",
                what: "watchlist, left half",
                standalone: NeedsNvim,
                cmd: "",
            },
            Row {
                keys: "␣wr",
                what: "watchlist, right half",
                standalone: NeedsNvim,
                cmd: "",
            },
            Row {
                keys: "␣ve",
                what: "catalyst calendar",
                standalone: Yes,
                cmd: "fl events [month|week|day] [t:TICKERS]",
            },
            Row {
                keys: "␣vD",
                what: "diagrams",
                standalone: Yes,
                cmd: "fl diagrams",
            },
            Row {
                keys: "␣vk",
                what: "data sources",
                standalone: Yes,
                cmd: "fl sources",
            },
            Row {
                keys: "␣vp",
                what: "portfolio: equity, positions, activity",
                standalone: Yes,
                cmd: "fl portfolio",
            },
            Row {
                keys: "␣vu",
                what: "AI universe heatmap",
                standalone: Yes,
                cmd: "fl universe",
            },
            Row {
                keys: "␣vr",
                what: "intraday grid, live candle tapes",
                standalone: Yes,
                cmd: "fl intraday MKSI,WDC,WULF,APLD",
            },
            Row {
                keys: "␣vb",
                what: "candlestick chart",
                standalone: Yes,
                cmd: "fl candles TICKER",
            },
            Row {
                keys: "␣vc",
                what: "line chart of the focused symbol",
                standalone: No,
                cmd: "fl candles TICKER (candlesticks instead)",
            },
            Row {
                keys: "␣vo",
                what: "switch between open dashboards",
                standalone: NeedsNvim,
                cmd: "",
            },
            Row {
                keys: "$",
                what: "portfolio treemap",
                standalone: No,
                cmd: "",
            },
        ],
    },
    Group {
        title: "Notes",
        rows: &[
            Row {
                keys: "␣vn",
                what: "ask about the word under cursor or the selection",
                standalone: NeedsNvim,
                cmd: "",
            },
            Row {
                keys: "␣vm",
                what: "browse notes; Enter reopens the answering chat",
                standalone: NeedsNvim,
                cmd: "",
            },
            Row {
                keys: "␣vl",
                what: "last answer, in a split",
                standalone: No,
                cmd: "",
            },
        ],
    },
    Group {
        title: "Claude",
        rows: &[
            Row {
                keys: "␣ac",
                what: "toggle the Claude window",
                standalone: Yes,
                cmd: "space a c in any screen",
            },
            Row {
                keys: "␣as",
                what: "add the selected value to Claude's context",
                standalone: Yes,
                cmd: "space a s in a screen with a selection",
            },
            Row {
                keys: "␣vi",
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
                keys: "␣vf",
                what: "search 10-K/20-F text, releases, guidance, patents",
                standalone: Yes,
                cmd: "fl search QUERY",
            },
            Row {
                keys: "␣vd",
                what: "one-ticker dossier",
                standalone: Yes,
                cmd: "fl dossier TICKER",
            },
            Row {
                keys: "␣vC",
                what: "CANSLIM scorecard",
                standalone: Yes,
                cmd: "fl canslim TICKER",
            },
            Row {
                keys: "␣vt",
                what: "search E*TRADE transactions",
                standalone: Yes,
                cmd: "fl transactions",
            },
        ],
    },
    Group {
        title: "Other",
        rows: &[
            Row {
                keys: "␣va",
                what: "onboard a ticker: add, pull every dataset, build its dossier",
                standalone: Yes,
                cmd: "fl onboard",
            },
            Row {
                keys: "␣vT",
                what: "timestamped video transcript (Siltronic), scratch split",
                standalone: No,
                cmd: "",
            },
            Row {
                keys: "␣v?",
                what: "menu of every nvim key; Enter runs one",
                standalone: NeedsNvim,
                cmd: "this page lists them",
            },
        ],
    },
];

const KEY_W: usize = 6;
const WHAT_W: usize = 52;
const STATE_W: usize = 11;

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
            "yes: works in fl (command shown)   needs nvim: only inside nvim   no: no fl equivalent",
            t.dim(),
        )),
        Line::from(""),
    ];
    for group in GROUPS {
        out.push(Line::from(Span::styled(group.title, t.accent())));
        out.push(Line::from(Span::styled(
            format!(
                "{}{}{}command",
                text::fit("key", KEY_W, false),
                text::fit("what", WHAT_W, false),
                text::fit("standalone", STATE_W, false),
            ),
            t.dim(),
        )));
        for r in group.rows {
            let state_style = match r.standalone {
                Standalone::Yes => t.base(),
                Standalone::NeedsNvim => t.accent(),
                Standalone::No => t.dim(),
            };
            out.push(Line::from(vec![
                Span::styled(text::fit(r.keys, KEY_W, false), t.accent()),
                Span::styled(text::fit(r.what, WHAT_W, false), t.base()),
                Span::styled(text::fit(r.standalone.label(), STATE_W, false), state_style),
                Span::styled(r.cmd, t.dim()),
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
                    !r.keys.is_empty() && !r.what.is_empty(),
                    "{}: empty row",
                    g.title
                );
                if r.standalone == Yes {
                    assert!(
                        !r.cmd.is_empty(),
                        "{} works standalone but has no command",
                        r.keys
                    );
                }
            }
        }
    }

    #[test]
    fn groups_are_in_order() {
        let titles: Vec<&str> = GROUPS.iter().map(|g| g.title).collect();
        assert_eq!(titles, ["Screens", "Notes", "Claude", "Search", "Other"]);
    }
}
