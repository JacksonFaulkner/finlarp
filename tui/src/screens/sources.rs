// Data sources as tiles, like the AI universe (vu): one tile per provider.
// Enter opens that provider's datasets as tiles (its sub-categories); Enter on
// a dataset opens its detail card. Esc steps back one level, and closes the
// screen from the top level.
//
// Static text: keep it in step with the py/sources docstrings, the imports
// under py/derive and py/jobs, and py/jobs/refresh.py when a puller moves.
// SEC rows follow the SEC's own pages (fair-access rules, bulk data set
// cadences); see the comments on those rows.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::ui::help::{self, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

const KEYS: &[Key] = &[
    key("hjkl", "move"),
    key("enter", "open provider / search dataset"),
    key("i", "dataset details"),
    key("/", "search SEC EDGAR text"),
    key("esc", "back"),
    key("?", "help"),
    key("q", "close"),
];

const TILE_W: u16 = 36;
const TILE_H: u16 = 6;
/// The search filters for SEC EDGAR text: 10-K/20-F sections, risk-factor sentences,
/// earnings releases and their guidance lines. Yahoo profiles and patents are left out.
/// Where Enter on a searchable dataset goes: the search screen, scoped to it.
fn search_action(s: &Source) -> Action {
    match &s.search {
        Search::Text(scope) => Action::Nvim(NvimAction::Screen {
            screen: "search".into(),
            arg: Some((*scope).into()),
        }),
        Search::Filings => Action::Nvim(NvimAction::Screen {
            screen: "filings".into(),
            arg: None,
        }),
        Search::Off => Action::None,
    }
}

const EDGAR_SEARCH: &str = "type:10k type:new_risk type:earnings type:guidance ";

/// Tile colours: dark backgrounds so the white title and line read clearly.
const TILE_SELECTED: Color = Color::Rgb(0x2a, 0x4a, 0x73);
const TILE_IDLE: Color = Color::Rgb(0x2b, 0x2d, 0x3a);
const TILE_TEXT: Color = Color::Rgb(0xff, 0xff, 0xff);
const TILE_NOTE: Color = Color::Rgb(0xa9, 0xb0, 0xc0);

/// One dataset: where it comes from, what reads it, and how to pull it.
pub struct Source {
    pub provider: &'static str,
    pub name: &'static str,
    /// What reads this dataset: screens, dossier tabs, MCP tools.
    pub feeds: &'static str,
    pub endpoint: &'static str,
    pub pulled_by: &'static str,
    /// Env var the puller needs, or "none".
    pub key: &'static str,
    pub runs: &'static str,
    /// How this dataset can be searched from its detail card.
    pub search: Search,
}

/// What `/` searches on a dataset's detail card.
pub enum Search {
    /// Full-text search over a corpus in derive/search.py, scoped by these filters.
    Text(&'static str),
    /// Filing index and 8-K / 6-K events: the filing search screen (derive/filing_search.py).
    Filings,
    /// No search for this dataset yet (structured data, or not indexed).
    Off,
}

/// SEC rows: the SEC asks for at most 10 requests per second and a
/// User-Agent with a contact address ("Company Name admin@domain.com"), and
/// its bulk data sets are posted quarterly (FSDS, insider transactions) or in
/// 3-month windows by filing date (13F).
const SOURCES: &[Source] = &[
    Source {
        provider: "SEC EDGAR",
        name: "Filing index and 8-K / 6-K events",
        feeds: "dossier filings, earnings, news; events calendar; MCP",
        endpoint: "data.sec.gov/submissions",
        pulled_by: "sources/sec_events.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily; intraday for the watchlist",
        search: Search::Filings,
    },
    Source {
        provider: "SEC EDGAR",
        name: "XBRL companyfacts (15+ years)",
        feeds: "dossier financials, peers; canslim; godel; MCP",
        endpoint: "data.sec.gov/api/xbrl/companyfacts",
        pulled_by: "sources/sec_financials.py, edgar.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily",
        search: Search::Off,
    },
    Source {
        provider: "SEC EDGAR",
        name: "Segment and geography revenue",
        feeds: "dossier financials; MCP",
        endpoint: "per-filing XBRL instance (_htm.xml)",
        pulled_by: "sources/sec_segments.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily",
        search: Search::Off,
    },
    Source {
        provider: "SEC EDGAR",
        name: "Financial Statement Data Sets",
        feeds: "DuckDB only (no direct reader found)",
        endpoint: "sec.gov/dera quarterly zips",
        pulled_by: "sources/edgar_fsds.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily check; new zip once per quarter",
        search: Search::Off,
    },
    Source {
        provider: "SEC EDGAR",
        name: "10-K / 20-F / 40-F text, Exhibit 21",
        feeds: "search (business, risk, MD&A); patents",
        endpoint: "sec.gov Archives",
        pulled_by: "sources/sec_filing_text.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily",
        search: Search::Text("type:10k type:new_risk "),
    },
    Source {
        provider: "SEC EDGAR",
        name: "Earnings releases and guidance",
        feeds: "dossier earnings; search (guidance)",
        endpoint: "sec.gov Archives (8-K Item 2.02 Ex. 99.1, 6-K)",
        pulled_by: "sources/sec_earnings.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily",
        search: Search::Text("type:earnings type:guidance "),
    },
    Source {
        provider: "SEC EDGAR",
        name: "Insider Forms 3/4/5 (bulk quarterly)",
        feeds: "dossier ownership",
        endpoint: "sec.gov insider transactions data sets",
        pulled_by: "sources/sec_insiders.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily check; new set once per quarter",
        search: Search::Off,
    },
    Source {
        provider: "SEC EDGAR",
        name: "Form 4 live XML",
        feeds: "dossier ownership, until the bulk set lands",
        endpoint: "data.sec.gov submissions",
        pulled_by: "sources/sec_form4_live.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "not scheduled",
        search: Search::Off,
    },
    Source {
        provider: "SEC EDGAR",
        name: "13F institutional holdings (~11k managers)",
        feeds: "dossier ownership; canslim I",
        endpoint: "sec.gov 13F data sets (3-month windows)",
        pulled_by: "sources/sec_13f.py",
        key: "none (User-Agent needs SEC_CONTACT)",
        runs: "daily check; new window each quarter",
        search: Search::Off,
    },
    Source {
        provider: "Databento",
        name: "Daily and 1-min bars, NBBO quotes",
        feeds: "candles; squeeze scan; korea signal",
        endpoint: "EQUS.SUMMARY, XNAS.BASIC",
        pulled_by: "sources/databento_bars.py",
        key: "DATABENTO_API_KEY",
        runs: "daily, $15 cap",
        search: Search::Off,
    },
    Source {
        provider: "Yahoo",
        name: "Price history and chart bars",
        feeds: "dossier price, valuation; canslim M; chart; portfolio closes",
        endpoint: "query1.finance.yahoo.com/v8/finance/chart",
        pulled_by: "sources/yahoo.py, intraday.py, market.py",
        key: "none",
        runs: "on demand (breadth cached 6h)",
        search: Search::Off,
    },
    Source {
        provider: "Yahoo",
        name: "Live trades into 1-min bars",
        feeds: "intraday grid",
        endpoint: "Yahoo websocket",
        pulled_by: "sources/intraday_stream.py",
        key: "none",
        runs: "live while the grid is open",
        search: Search::Off,
    },
    Source {
        provider: "Yahoo",
        name: "Company profiles",
        feeds: "universe sectors; search; dossier price, valuation, earnings",
        endpoint: "Yahoo quoteSummary",
        pulled_by: "sources/yahoo_profile.py",
        key: "none",
        runs: "daily",
        search: Search::Text("type:profile "),
    },
    Source {
        provider: "Yahoo",
        name: "Market-cap screener",
        feeds: "report_top50 company list",
        endpoint: "Yahoo screener (cookie + crumb)",
        pulled_by: "sources/yahoo.py",
        key: "none",
        runs: "on demand",
        search: Search::Off,
    },
    Source {
        provider: "Yahoo",
        name: "Live quote, pre/post market, headlines",
        feeds: "MCP live_* tools; dossier news",
        endpoint: "Yahoo chart and search",
        pulled_by: "sources/yahoo_live.py",
        key: "none",
        runs: "on demand",
        search: Search::Off,
    },
    Source {
        provider: "Nasdaq / FINRA",
        name: "Short interest by settlement date",
        feeds: "dossier positioning; canslim S; squeeze scan",
        endpoint: "api.nasdaq.com (Yahoo fallback for NYSE)",
        pulled_by: "sources/short_interest.py interest",
        key: "none",
        runs: "daily",
        search: Search::Off,
    },
    Source {
        provider: "Nasdaq / FINRA",
        name: "Daily short-sale volume (Reg SHO)",
        feeds: "dossier positioning; canslim S; squeeze scan",
        endpoint: "cdn.finra.org",
        pulled_by: "sources/short_interest.py volume",
        key: "none",
        runs: "daily",
        search: Search::Off,
    },
    Source {
        provider: "E*TRADE",
        name: "Positions, orders, transactions, balance",
        feeds: "portfolio; transaction search; MCP etrade_*",
        endpoint: "api.etrade.com",
        pulled_by: "sources/etrade.py, etrade_live.py",
        key: "PROD_KEY, PROD_SECRET",
        runs: "$ refresh (positions 5 min, transactions 1 h)",
        search: Search::Off,
    },
    Source {
        provider: "E*TRADE",
        name: "Option chain snapshots",
        feeds: "DuckDB only (no screen yet)",
        endpoint: "api.etrade.com",
        pulled_by: "sources/etrade_options.py",
        key: "PROD_KEY, PROD_SECRET",
        runs: "manual snapshot",
        search: Search::Off,
    },
    Source {
        provider: "X (Apify)",
        name: "Posts from followed research accounts",
        feeds: "dossier sentiment; events (T); MCP tweets",
        endpoint: "api.apify.com (xquik tweet scraper)",
        pulled_by: "jobs/pull_recent_tweets.py, pull_tweets.py, fill_tweets.py",
        key: "APIFY_TOKEN",
        runs: "daily ($1 cap); intraday ($0.5 cap)",
        search: Search::Off,
    },
    Source {
        provider: "X (Apify)",
        name: "$CASHTAG posts with author metadata",
        feeds: "botcheck (bot signals)",
        endpoint: "api.apify.com",
        pulled_by: "jobs/pull_cashtags.py",
        key: "APIFY_TOKEN",
        runs: "manual",
        search: Search::Off,
    },
    Source {
        provider: "X (Apify)",
        name: "Who the tracked accounts follow",
        feeds: "pull_following ranking (no screen yet)",
        endpoint: "api.apify.com (xquik follower scraper)",
        pulled_by: "jobs/pull_following.py",
        key: "APIFY_TOKEN",
        runs: "manual",
        search: Search::Off,
    },
    Source {
        provider: "OpenAI",
        name: "Stance labels per ticker (LLM)",
        feeds: "dossier sentiment; events; MCP sentiment",
        endpoint: "api.openai.com/v1/responses",
        pulled_by: "sources/tweet_sentiment.py",
        key: "OPENAI_API_KEY",
        runs: "daily and intraday",
        search: Search::Off,
    },
    Source {
        provider: "ROIC",
        name: "Company news: title, link, snippet",
        feeds: "dossier news",
        endpoint: "api.roic.ai/v2/company/news",
        pulled_by: "sources/roic_news.py",
        key: "ROIC_TOKEN",
        runs: "manual (not in refresh)",
        search: Search::Off,
    },
    Source {
        provider: "USPTO",
        name: "Granted US patents (~1.5M, through 2025)",
        feeds: "search (patents)",
        endpoint: "data.uspto.gov PatentsView bulk; USPTO ODP",
        pulled_by: "sources/bulk_pull.py pv, patents.py",
        key: "USPTO_API_KEY",
        runs: "manual",
        search: Search::Text("type:patent "),
    },
    Source {
        provider: "USPTO",
        name: "AI patent classifier (ECOPATAI)",
        feeds: "search (patent AI flags)",
        endpoint: "data.uspto.gov bulk datasets",
        pulled_by: "sources/patents_ai.py via bulk_pull.py",
        key: "USPTO_API_KEY",
        runs: "manual",
        search: Search::Off,
    },
    Source {
        provider: "arXiv",
        name: "Paper metadata (AI, ML, signal processing)",
        feeds: "DuckDB only (not linked to tickers yet)",
        endpoint: "oaipmh.arxiv.org/oai",
        pulled_by: "sources/arxiv.py",
        key: "none",
        runs: "daily",
        search: Search::Off,
    },
    Source {
        provider: "DOL",
        name: "Labor certification (LCA) disclosures",
        feeds: "DuckDB only (no screen yet)",
        endpoint: "dol.gov foreign-labor performance",
        pulled_by: "sources/bulk_pull.py",
        key: "none",
        runs: "manual",
        search: Search::Off,
    },
    Source {
        provider: "OpenFIGI",
        name: "CUSIP to ticker mapping",
        feeds: "13F holdings (ticker join)",
        endpoint: "api.openfigi.com",
        pulled_by: "sources/sec_13f.py",
        key: "none (keyless, cached)",
        runs: "with each 13F pull",
        search: Search::Off,
    },
    Source {
        provider: "Exa + OpenAI",
        name: "Top-50 issuer reports: web search + LLM",
        feeds: "JSON reports (no screen yet)",
        endpoint: "api.exa.ai, api.openai.com",
        pulled_by: "jobs/report_top50.py",
        key: "EXA_API_KEY, OPENAI_API_KEY",
        runs: "manual",
        search: Search::Off,
    },
];

/// True when the puller needs an API key or token (not just the SEC contact).
fn needs_key(s: &Source) -> bool {
    !s.key.starts_with("none")
}

/// One provider's tile: its datasets are the sub-categories.
struct Provider {
    name: &'static str,
    /// Indices into SOURCES, in declaration order.
    items: Vec<usize>,
}

fn providers() -> Vec<Provider> {
    let mut out: Vec<Provider> = Vec::new();
    for (i, s) in SOURCES.iter().enumerate() {
        match out.iter_mut().find(|p| p.name == s.provider) {
            Some(p) => p.items.push(i),
            None => out.push(Provider {
                name: s.provider,
                items: vec![i],
            }),
        }
    }
    out
}

#[derive(Clone, Copy, PartialEq)]
enum View {
    /// One tile per provider.
    Providers,
    /// The sub-categories (datasets) of one provider, by index into providers().
    Datasets(usize),
    /// One dataset's detail card, by index into SOURCES.
    Detail(usize),
}

/// One tile's three lines of text.
struct Tile {
    title: String,
    line2: String,
    line3: String,
}

pub struct Sources {
    theme: Theme,
    providers: Vec<Provider>,
    view: View,
    /// Selected tile in the current view.
    sel: usize,
    /// Tile columns in the last frame; j/k step a whole row by this.
    cols: usize,
    help: bool,
}

pub fn open(ctx: &Ctx, _arg: Option<String>) -> io::Result<Sources> {
    Ok(Sources {
        theme: ctx.theme,
        providers: providers(),
        view: View::Providers,
        sel: 0,
        cols: 1,
        help: false,
    })
}

impl Sources {
    fn tiles(&self) -> Vec<Tile> {
        match self.view {
            View::Providers => self
                .providers
                .iter()
                .map(|p| {
                    let keyed = p.items.iter().filter(|&&i| needs_key(&SOURCES[i])).count();
                    Tile {
                        title: p.name.to_string(),
                        line2: format!("{} datasets", p.items.len()),
                        line3: if keyed == 0 {
                            "no key needed".into()
                        } else {
                            format!("{keyed} need a key")
                        },
                    }
                })
                .collect(),
            View::Datasets(g) => self.providers[g]
                .items
                .iter()
                .map(|&i| {
                    let s = &SOURCES[i];
                    Tile {
                        title: s.name.into(),
                        line2: s.feeds.into(),
                        line3: s.runs.into(),
                    }
                })
                .collect(),
            View::Detail(_) => Vec::new(),
        }
    }

    /// The provider index and the position within it of dataset `i`.
    fn locate(&self, i: usize) -> (usize, usize) {
        self.providers
            .iter()
            .enumerate()
            .find_map(|(g, p)| p.items.iter().position(|&x| x == i).map(|pos| (g, pos)))
            .unwrap_or((0, 0))
    }

    fn crumb(&self) -> Line<'static> {
        let t = self.theme;
        let mut spans = vec![Span::styled(" data sources ", t.title())];
        match self.view {
            View::Providers => {}
            View::Datasets(g) => {
                spans.push(Span::styled(
                    format!(" › {}", self.providers[g].name),
                    t.accent(),
                ));
            }
            View::Detail(i) => {
                let (g, _) = self.locate(i);
                spans.push(Span::styled(
                    format!(" › {} › {}", self.providers[g].name, SOURCES[i].name),
                    t.accent(),
                ));
            }
        }
        Line::from(spans)
    }

    fn draw_tiles(&mut self, frame: &mut Frame, body: Rect) {
        let tiles = self.tiles();
        if tiles.is_empty() {
            return;
        }
        let cols = (body.width / TILE_W).max(1) as usize;
        self.cols = cols;
        let tile_w = body.width / cols as u16;
        let rows_visible = (body.height / TILE_H).max(1) as usize;
        let first_row = (self.sel / cols).saturating_sub(rows_visible - 1);
        for (i, tile) in tiles.iter().enumerate() {
            let (row, col) = (i / cols, i % cols);
            if row < first_row || row >= first_row + rows_visible {
                continue;
            }
            let r = Rect::new(
                body.x + col as u16 * tile_w,
                body.y + (row - first_row) as u16 * TILE_H,
                tile_w.saturating_sub(1),
                TILE_H - 1,
            );
            let selected = i == self.sel;
            let bg = if selected { TILE_SELECTED } else { TILE_IDLE };
            let st = Style::new().fg(TILE_TEXT).bg(bg);
            // Only the selected tile draws its border (as the universe does).
            let block = if selected {
                Block::bordered().border_style(st)
            } else {
                Block::new()
            };
            frame.render_widget(Block::new().style(st), r);
            frame.render_widget(block.style(st), r);
            let inner = Rect::new(r.x, r.y + 1, r.width, r.height - 2);
            let w = (r.width as usize).saturating_sub(2);
            let lines = vec![
                Line::styled(
                    format!(" {}", text::truncate(&tile.title, w)),
                    st.add_modifier(Modifier::BOLD),
                ),
                Line::styled(format!(" {}", text::truncate(&tile.line2, w)), st),
                Line::styled(
                    format!(" {}", text::truncate(&tile.line3, w)),
                    st.fg(TILE_NOTE),
                ),
            ];
            frame.render_widget(Paragraph::new(lines).style(st), inner);
        }
    }

    fn draw_detail(&self, frame: &mut Frame, area: Rect, s: &Source) {
        let t = self.theme;
        let rows = [
            ("provider", s.provider),
            ("feeds", s.feeds),
            ("endpoint", s.endpoint),
            ("pulled by", s.pulled_by),
            ("key", s.key),
            ("runs", s.runs),
            (
                "search",
                match s.search {
                    Search::Text(scope) => scope.trim(),
                    Search::Filings => "8-K and 6-K filings (form:, item:, signal:, since:)",
                    Search::Off => "not searchable yet",
                },
            ),
        ];
        let mut lines = vec![Line::styled(s.name, t.title()), Line::default()];
        for (label, value) in rows {
            lines.push(Line::from(vec![
                Span::styled(format!("  {label:<10}"), t.dim()),
                Span::styled(value, t.base()),
            ]));
        }
        frame.render_widget(Paragraph::new(lines).style(t.base()), area);
    }
}

impl Screen for Sources {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(self.crumb()), head);
        let hint = match self.view {
            View::Providers => " hjkl move · ↵ open provider · / search SEC EDGAR · esc close",
            View::Datasets(_) => {
                " hjkl move · ↵ search (i details) · / search SEC EDGAR · esc back"
            }
            View::Detail(i) => match SOURCES[i].search {
                Search::Off => " esc back · not searchable yet",
                _ => " / search this dataset · esc back",
            },
        };
        frame.render_widget(Paragraph::new(Line::styled(hint, t.dim())), foot);
        match self.view {
            View::Detail(i) => self.draw_detail(frame, body, &SOURCES[i]),
            _ => self.draw_tiles(frame, body),
        }
        if self.help {
            help::render_overlay(frame, area, "data sources", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        let last = self.tiles().len().saturating_sub(1);
        match key.code {
            KeyCode::Char('q') => return Action::Quit,
            KeyCode::Char('/') => {
                if let View::Detail(i) = self.view {
                    return search_action(&SOURCES[i]);
                }
                let group = match self.view {
                    View::Providers => Some(self.sel),
                    View::Datasets(g) => Some(g),
                    View::Detail(_) => None,
                };
                if group.is_some_and(|g| self.providers[g].name == "SEC EDGAR") {
                    return Action::Nvim(NvimAction::Screen {
                        screen: "search".into(),
                        arg: Some(EDGAR_SEARCH.into()),
                    });
                }
            }
            KeyCode::Char('i') if matches!(self.view, View::Datasets(_)) => {
                if let View::Datasets(g) = self.view {
                    self.view = View::Detail(self.providers[g].items[self.sel]);
                }
            }
            KeyCode::Esc => match self.view {
                View::Providers => return Action::Quit,
                View::Datasets(g) => {
                    self.view = View::Providers;
                    self.sel = g;
                }
                View::Detail(i) => {
                    let (g, pos) = self.locate(i);
                    self.view = View::Datasets(g);
                    self.sel = pos;
                }
            },
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char('h') | KeyCode::Left => self.sel = self.sel.saturating_sub(1),
            KeyCode::Char('l') | KeyCode::Right => self.sel = (self.sel + 1).min(last),
            KeyCode::Char('k') | KeyCode::Up => self.sel = self.sel.saturating_sub(self.cols),
            KeyCode::Char('j') | KeyCode::Down => self.sel = (self.sel + self.cols).min(last),
            KeyCode::Char('g') => self.sel = 0,
            KeyCode::Char('G') => self.sel = last,
            KeyCode::Enter => match self.view {
                View::Providers => {
                    self.view = View::Datasets(self.sel);
                    self.sel = 0;
                }
                View::Datasets(g) => {
                    let i = self.providers[g].items[self.sel];
                    match SOURCES[i].search {
                        Search::Off => self.view = View::Detail(i),
                        _ => return search_action(&SOURCES[i]),
                    }
                }
                View::Detail(_) => {}
            },
            _ => {}
        }
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    use super::*;

    fn screen() -> Sources {
        Sources {
            theme: Theme::default(),
            providers: providers(),
            view: View::Providers,
            sel: 0,
            cols: 1,
            help: false,
        }
    }

    fn render(s: &mut Sources, w: u16, h: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(w, h)).expect("terminal");
        term.draw(|f| s.draw(f)).expect("draw");
        term.backend().to_string()
    }

    fn press(s: &mut Sources, code: KeyCode) -> Action {
        s.on_key(KeyEvent::new(code, KeyModifiers::NONE))
    }

    #[test]
    fn one_tile_per_provider_with_key_counts() {
        let mut s = screen();
        let out = render(&mut s, 120, 40);
        assert!(out.contains("SEC EDGAR"), "{out}");
        assert!(
            out.contains("1 need a key"),
            "Databento key count missing:\n{out}"
        );
        assert!(out.contains("no key needed"), "{out}");
    }

    #[test]
    fn enter_opens_the_provider_sub_categories() {
        let mut s = screen();
        render(&mut s, 120, 40);
        press(&mut s, KeyCode::Enter);
        assert!(matches!(s.view, View::Datasets(0)));
        let out = render(&mut s, 120, 40);
        assert!(out.contains("Filing index"), "{out}");
        assert!(out.contains("XBRL companyfacts"), "{out}");
    }

    #[test]
    fn enter_on_a_searchable_dataset_opens_its_search() {
        let mut s = screen();
        render(&mut s, 120, 40);
        press(&mut s, KeyCode::Enter);
        // the first SEC EDGAR dataset is the filing index, which has a filings search
        match press(&mut s, KeyCode::Enter) {
            Action::Nvim(NvimAction::Screen { screen, .. }) => assert_eq!(screen, "filings"),
            _ => panic!("expected the filings screen"),
        }
        assert!(matches!(s.view, View::Datasets(0)));
    }

    #[test]
    fn i_on_a_dataset_shows_details_and_esc_steps_back() {
        let mut s = screen();
        render(&mut s, 120, 40);
        press(&mut s, KeyCode::Enter);
        press(&mut s, KeyCode::Char('i'));
        assert!(matches!(s.view, View::Detail(0)));
        let out = render(&mut s, 120, 40);
        assert!(out.contains("sources/sec_events.py"), "{out}");
        press(&mut s, KeyCode::Esc);
        assert!(matches!(s.view, View::Datasets(0)));
        press(&mut s, KeyCode::Esc);
        assert!(matches!(s.view, View::Providers));
        assert!(matches!(press(&mut s, KeyCode::Esc), Action::Quit));
    }

    #[test]
    fn slash_on_sec_edgar_opens_search_scoped_to_its_text() {
        let mut s = screen();
        render(&mut s, 120, 40);
        // on the provider tiles: SEC EDGAR is the first provider
        match press(&mut s, KeyCode::Char('/')) {
            Action::Nvim(NvimAction::Screen { screen, arg }) => {
                assert_eq!(screen, "search");
                let arg = arg.unwrap();
                assert!(
                    arg.contains("type:10k") && arg.contains("type:earnings"),
                    "{arg}"
                );
                assert!(!arg.contains("profile") && !arg.contains("patent"), "{arg}");
            }
            other => panic!(
                "expected a search action, got {:?}",
                std::mem::discriminant(&other)
            ),
        }
        // inside the SEC EDGAR datasets too
        press(&mut s, KeyCode::Enter);
        assert!(matches!(
            press(&mut s, KeyCode::Char('/')),
            Action::Nvim(NvimAction::Screen { .. })
        ));
        // on another provider, nothing happens
        let mut other = screen();
        render(&mut other, 120, 40);
        press(&mut other, KeyCode::Char('l'));
        assert!(matches!(
            press(&mut other, KeyCode::Char('/')),
            Action::None
        ));
    }

    #[test]
    fn slash_on_a_dataset_searches_its_own_corpus_or_says_it_cannot() {
        let mut s = screen();
        render(&mut s, 120, 40);
        let index = |name: &str| SOURCES.iter().position(|x| x.name == name).unwrap();
        // 10-K text searches the filings, scoped to the 10-K and new-risk sentences
        s.view = View::Detail(index("10-K / 20-F / 40-F text, Exhibit 21"));
        match press(&mut s, KeyCode::Char('/')) {
            Action::Nvim(NvimAction::Screen { screen, arg }) => {
                assert_eq!(screen, "search");
                assert_eq!(arg.as_deref(), Some("type:10k type:new_risk "));
            }
            _ => panic!("expected the search screen"),
        }
        assert!(render(&mut s, 120, 40).contains("type:10k type:new_risk"));
        // structured data has no search yet, and says so
        s.view = View::Detail(index("Insider Forms 3/4/5 (bulk quarterly)"));
        assert!(matches!(press(&mut s, KeyCode::Char('/')), Action::None));
        assert!(render(&mut s, 120, 40).contains("not searchable yet"));
    }

    #[test]
    fn j_steps_a_whole_row_of_tiles() {
        let mut s = screen();
        render(&mut s, 120, 40);
        assert_eq!(s.cols, 3);
        press(&mut s, KeyCode::Char('j'));
        assert_eq!(s.sel, 3);
    }
}
