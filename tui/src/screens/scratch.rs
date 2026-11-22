// Scratch pad (home board key `y`): a one-off research page for a term that
// has no screen of its own (HBF, CoWoS, "high bandwidth flash"). Type a term
// and every ticker whose filings, earnings releases, profiles or patents match
// is listed, ranked by matching chunks, with the best passage for the selected
// ticker on the right. Enter opens its dossier, c its CANSLIM, b its candles,
// m pins it to the term's pad. Pads are kept in data/scratch/pads.json, one per
// term, so each term keeps its own pins and reopening the screen returns to
// the last term. The file is data/pads.json: data/scratch is the SQL scratch
// dir for parquet output.
//
//   scratch › hbf▏                                  12 tickers · 340 chunks
//   pad hbf · pinned SNDK, SKHY · other pads: cowos (5)
//   ┌ tickers ───────┬ SIMO · 61 chunks ────────────────────────────────┐
//   │ ● SNDK      97 │ 10k filing risk_factors 2026-08-01               │
//   │   SIMO      61 │ …passage that matched the term…                  │
//   ├────────────────┴──────────────────────────────────────────────────┤
//   │ source: https://www.sec.gov/…                                     │
//   └ keys ─────────────────────────────────────────────────────────────┘
//
// Data: the search server (screens::search::client, search.py --serve). The
// query goes out with facet_n raised so every matching ticker comes back, not
// the top 12, and k hits so each ticker can show a passage.

use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent};
use ratatui::layout::Rect;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, List, ListItem, ListState, Paragraph, Wrap};
use serde::{Deserialize, Serialize};
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::app::{Action, Ctx, Route, Screen};
use crate::screens::search::client::{Client, Hit, Reply, Request};
use crate::ui::help::{Help, Key, key};
use crate::ui::layout::{self, Focus, FrameTitles, PaneOpts};
use crate::ui::text;
use crate::ui::theme::Theme;

/// Quiet period after the last keystroke before a query is sent.
const DEBOUNCE: Duration = Duration::from_millis(250);
/// Hits per query; the source of each ticker's passage.
const K: usize = 200;
/// Tickers per query (search.py caps facets at 12 by default).
const FACET_N: usize = 500;
/// Nav column width (ticker list).
const NAV_WIDTH: u16 = 30;

const KEYS: &[Key] = &[
    key("↵", "dossier"),
    key("c", "canslim"),
    key("b", "candles"),
    key("m", "pin to pad"),
    key("y", "copy source url"),
    key("/ tab", "type a term"),
    key("j k", "move"),
    key("esc", "back"),
    key("q", "close"),
];

const TYPING_KEYS: &[Key] = &[
    key("↵ tab", "search, then move to tickers"),
    key("esc", "back"),
];

const HELP: &str = "Type a term: a product, technology or line item (CoWoS, 800G optics, \
bandwidth flash).\n\nEvery ticker whose filings, earnings releases, profiles or patents \
mention it is listed here, ranked by matching chunks. Search syntax works: \"exact phrase\", \
-word, sec:mda, since:2025.\n\nAcronyms can be thin: \"hbf\" alone matches one filing, while \
\"bandwidth flash\" surfaces SNDK. Try the spelled-out words too.";

/// Pads on disk: the term last open, and pinned tickers per term.
#[derive(Debug, Default, PartialEq, Serialize, Deserialize)]
struct Pads {
    #[serde(default)]
    last: String,
    /// term -> pinned tickers, in pin order.
    #[serde(default)]
    pads: BTreeMap<String, Vec<String>>,
}

impl Pads {
    fn load(path: &Path) -> Self {
        fs::read_to_string(path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    fn save(&self, path: &Path) -> io::Result<()> {
        if let Some(dir) = path.parent() {
            fs::create_dir_all(dir)?;
        }
        let body = serde_json::to_string_pretty(self).map_err(io::Error::other)?;
        fs::write(path, body + "\n")
    }

    fn pinned(&self, term: &str) -> &[String] {
        self.pads.get(term).map_or(&[], Vec::as_slice)
    }

    /// Pins `ticker` to the pad for `term`, or unpins it. True = now pinned.
    /// An emptied pad is dropped from the file.
    fn toggle(&mut self, term: &str, ticker: &str) -> bool {
        let pad = self.pads.entry(term.to_string()).or_default();
        let now = match pad.iter().position(|t| t == ticker) {
            Some(i) => {
                pad.remove(i);
                false
            }
            None => {
                pad.push(ticker.to_string());
                true
            }
        };
        if self.pads.get(term).is_some_and(Vec::is_empty) {
            self.pads.remove(term);
        }
        now
    }
}

/// One nav row: a ticker with the chunks that match the term.
#[derive(Debug, Clone, PartialEq)]
struct Row {
    ticker: String,
    chunks: u64,
    /// Best-ranked hit for this ticker among the query's top K.
    sample: Option<Hit>,
    pinned: bool,
}

/// Ticker rows for a term: matching tickers by chunk count, then pinned
/// tickers that do not match right now (count 0), so pins never disappear.
fn build_rows(counts: &[(String, u64)], hits: &[Hit], pinned: &[String]) -> Vec<Row> {
    let mut rows: Vec<Row> = counts
        .iter()
        .map(|(t, c)| Row {
            ticker: t.clone(),
            chunks: *c,
            sample: hits.iter().find(|h| h.ticker == *t).cloned(),
            pinned: pinned.contains(t),
        })
        .collect();
    for p in pinned {
        if !rows.iter().any(|r| r.ticker == *p) {
            rows.push(Row {
                ticker: p.clone(),
                chunks: 0,
                sample: None,
                pinned: true,
            });
        }
    }
    rows
}

pub struct Scratch {
    theme: Theme,
    input: Input,
    /// True while the term is being typed; false = the ticker list has focus.
    typing: bool,
    client: Client,
    path: PathBuf,
    pads: Pads,
    /// Term of the newest query sent: the pad in use.
    term: String,
    next_id: u64,
    /// (request id, term) of the newest query sent.
    sent: Option<(u64, String)>,
    /// Set by edits; the query goes out DEBOUNCE after the last one.
    edited_at: Option<Instant>,
    loading: bool,
    /// Ticker counts and top hits from the newest reply.
    counts: Vec<(String, u64)>,
    hits: Vec<Hit>,
    rows: Vec<Row>,
    /// Chunks matching the term (all matches, not just the K hits).
    total: u64,
    error: Option<String>,
    list: ListState,
    flash: Option<String>,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Scratch> {
    let path = crate::data_dir().join("pads.json");
    Ok(Scratch::new(ctx.theme, Client::spawn(), path, arg))
}

fn normalize(term: &str) -> String {
    term.trim().to_lowercase()
}

impl Scratch {
    fn new(theme: Theme, client: Client, path: PathBuf, arg: Option<String>) -> Self {
        let pads = Pads::load(&path);
        let term = arg
            .map(|a| normalize(&a))
            .unwrap_or_else(|| pads.last.clone());
        let mut s = Self {
            theme,
            input: Input::new(term.clone()),
            typing: term.is_empty(),
            client,
            path,
            pads,
            term: String::new(),
            next_id: 0,
            sent: None,
            edited_at: None,
            loading: false,
            counts: Vec::new(),
            hits: Vec::new(),
            rows: Vec::new(),
            total: 0,
            error: None,
            list: ListState::default(),
            flash: None,
        };
        // pins show at once; the query fills in the counts when it returns
        s.run_query();
        s
    }

    fn next_id(&mut self) -> u64 {
        self.next_id += 1;
        self.next_id
    }

    /// Sends the typed term as the pad's query, unless it is the one in flight.
    fn run_query(&mut self) {
        self.edited_at = None;
        let q = normalize(self.input.value());
        if self.sent.as_ref().is_some_and(|(_, t)| *t == q) {
            return;
        }
        self.term = q.clone();
        if q.is_empty() {
            self.sent = None;
            self.loading = false;
            self.counts.clear();
            self.hits.clear();
            self.total = 0;
            self.error = None;
            self.refresh();
            return;
        }
        let id = self.next_id();
        let sent = self.client.tx.send(Request::Query {
            id,
            q: q.clone(),
            k: K,
            facet_n: Some(FACET_N),
        });
        if sent.is_ok() {
            self.sent = Some((id, q));
            self.loading = true;
        }
        self.save();
        self.refresh();
    }

    fn apply(&mut self, r: Reply) {
        let Some(id) = r.id else {
            // no id: server-level failure (spawn error, server exited)
            self.error = r.error;
            self.loading = false;
            return;
        };
        if !self.sent.as_ref().is_some_and(|(sid, _)| *sid == id) {
            return; // stale: a newer query is in flight
        }
        self.loading = false;
        self.error = r.error.clone();
        if self.error.is_some() {
            return;
        }
        self.total = r
            .facets
            .get("type")
            .map_or(0, |v| v.iter().map(|(_, c)| c).sum());
        self.counts = r
            .facets
            .get("ticker")
            .map(|v| {
                v.iter()
                    .filter_map(|(t, c)| Some((t.clone()?, *c)))
                    .collect()
            })
            .unwrap_or_default();
        self.hits = r.results;
        self.refresh();
    }

    /// Rebuilds the rows from counts, hits and the pad's pins, keeping the
    /// selected ticker selected when it is still listed.
    fn refresh(&mut self) {
        let keep = self.selected().map(|r| r.ticker.clone());
        let pinned = self.pads.pinned(&self.term).to_vec();
        self.rows = build_rows(&self.counts, &self.hits, &pinned);
        let idx = keep
            .and_then(|t| self.rows.iter().position(|r| r.ticker == t))
            .or((!self.rows.is_empty()).then_some(0));
        self.list.select(idx);
    }

    fn selected(&self) -> Option<&Row> {
        self.rows.get(self.list.selected()?)
    }

    fn save(&mut self) {
        self.pads.last = self.term.clone();
        if let Err(e) = self.pads.save(&self.path) {
            self.flash = Some(format!("pads not saved: {e}"));
        }
    }

    fn step(&mut self, delta: isize) {
        let n = self.rows.len();
        if n == 0 {
            return;
        }
        let cur = self.list.selected().unwrap_or(0) as isize;
        self.list
            .select(Some((cur + delta).clamp(0, n as isize - 1) as usize));
    }

    fn open_ticker(&self, screen: &str) -> Action {
        match self.selected() {
            Some(r) => Action::Route(Route::Screen {
                screen: screen.into(),
                arg: Some(r.ticker.clone()),
            }),
            None => Action::None,
        }
    }

    /// Pins or unpins the selected ticker in the current term's pad.
    fn pin_selected(&mut self) {
        let Some(ticker) = self.selected().map(|r| r.ticker.clone()) else {
            return;
        };
        if self.term.is_empty() {
            return;
        }
        let now = self.pads.toggle(&self.term, &ticker);
        self.save();
        self.refresh();
        self.flash = Some(format!(
            "{ticker} {} pad {}",
            if now { "pinned to" } else { "unpinned from" },
            self.term
        ));
    }

    fn on_typing_key(&mut self, key: KeyEvent) -> Action {
        match key.code {
            KeyCode::Esc => Action::Quit,
            KeyCode::Enter | KeyCode::Tab | KeyCode::Down => {
                self.typing = false;
                self.run_query();
                Action::None
            }
            _ => {
                let before = self.input.value().to_string();
                self.input.handle_event(&Event::Key(key));
                if self.input.value() != before {
                    self.edited_at = Some(Instant::now());
                }
                Action::None
            }
        }
    }

    fn on_list_key(&mut self, key: KeyEvent) -> Action {
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
            KeyCode::Char('/' | 'i') | KeyCode::Tab => {
                self.typing = true;
                Action::None
            }
            KeyCode::Down | KeyCode::Char('j') => {
                self.step(1);
                Action::None
            }
            KeyCode::Up | KeyCode::Char('k') => {
                self.step(-1);
                Action::None
            }
            KeyCode::Char('g') => {
                if !self.rows.is_empty() {
                    self.list.select(Some(0));
                }
                Action::None
            }
            KeyCode::Char('G') => {
                if let Some(last) = self.rows.len().checked_sub(1) {
                    self.list.select(Some(last));
                }
                Action::None
            }
            KeyCode::Enter => self.open_ticker("dossier"),
            KeyCode::Char('c') => self.open_ticker("canslim"),
            KeyCode::Char('b') => self.open_ticker("candles"),
            KeyCode::Char('m') => {
                self.pin_selected();
                Action::None
            }
            KeyCode::Char('y') => self
                .selected()
                .and_then(|r| r.sample.as_ref())
                .and_then(|h| h.url.clone())
                .map_or(Action::None, Action::Copy),
            _ => Action::None,
        }
    }

    fn pad_line(&self) -> String {
        let pinned = self.pads.pinned(&self.term);
        let pinned = if pinned.is_empty() {
            "none yet".to_string()
        } else {
            pinned.join(", ")
        };
        let others: Vec<String> = self
            .pads
            .pads
            .iter()
            .filter(|(t, _)| **t != self.term)
            .map(|(t, p)| format!("{t} ({})", p.len()))
            .collect();
        let mut line = if self.term.is_empty() {
            "no pad open".to_string()
        } else {
            format!("pad {} · pinned {pinned}", self.term)
        };
        if !others.is_empty() {
            line.push_str(&format!(" · other pads: {}", others.join(", ")));
        }
        line
    }

    fn status(&self) -> String {
        if self.loading {
            "searching…".into()
        } else if self.term.is_empty() {
            String::new()
        } else {
            let n = self.counts.len();
            format!(
                "{n} ticker{} · {} chunk{}",
                if n == 1 { "" } else { "s" },
                self.total,
                if self.total == 1 { "" } else { "s" }
            )
        }
    }

    fn draw_nav(&mut self, frame: &mut Frame, area: Rect, empty: &str) {
        let t = self.theme;
        if self.rows.is_empty() {
            frame.render_widget(Paragraph::new(empty.to_string()).style(t.dim()), area);
            return;
        }
        let items: Vec<ListItem> = self
            .rows
            .iter()
            .map(|r| {
                let mark = if r.pinned { "● " } else { "  " };
                let line = format!("{mark}{:<6} {:>5}", r.ticker, r.chunks);
                ListItem::new(Line::from(Span::styled(line, t.base())))
            })
            .collect();
        frame.render_stateful_widget(
            List::new(items)
                .style(t.base())
                .highlight_style(t.selected()),
            area,
            &mut self.list,
        );
    }

    fn draw_detail(&self, frame: &mut Frame, area: Rect) {
        let t = self.theme;
        let width = area.width.max(1) as usize;
        let lines: Vec<Line> = match self.selected() {
            Some(Row {
                sample: Some(hit), ..
            }) => {
                let meta = [
                    Some(hit.kind.clone()),
                    hit.form.clone(),
                    hit.section.clone(),
                    hit.date.clone(),
                ]
                .into_iter()
                .flatten()
                .filter(|s| !s.is_empty())
                .collect::<Vec<_>>()
                .join(" · ");
                let mut out = vec![Line::styled(meta, t.dim()), Line::from("")];
                out.extend(
                    text::wrap(&hit.text, width)
                        .into_iter()
                        .map(|l| Line::styled(l, t.base())),
                );
                out
            }
            Some(_) => vec![Line::styled(
                "No passage among the top matches. ↵ opens the dossier.",
                t.dim(),
            )],
            None => HELP
                .lines()
                .map(|l| Line::styled(l.to_string(), t.dim()))
                .collect(),
        };
        frame.render_widget(
            Paragraph::new(lines)
                .style(t.base())
                .wrap(Wrap { trim: false }),
            area,
        );
    }
}

impl Screen for Scratch {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);

        let detail_title = match self.selected() {
            Some(r) => format!(
                "{} · {} chunk{}",
                r.ticker,
                r.chunks,
                if r.chunks == 1 { "" } else { "s" }
            ),
            None => "scratch".to_string(),
        };
        let panes = layout::render_frame(
            frame,
            area,
            PaneOpts {
                nav_width: NAV_WIDTH,
                source_height: 3,
                header_height: 2,
                tabs_height: 0,
            },
            &FrameTitles {
                nav: Line::from("tickers"),
                detail: Line::from(detail_title),
                detail_right: Line::default(),
                source: Line::from("source"),
                focus: Focus::Nav,
            },
            &t,
        );

        // header: the term (with the cursor while typing), then the pad line
        let status = self.status();
        let prompt = " scratch › ";
        let mut first = vec![Span::styled(prompt, t.accent())];
        if self.typing {
            frame.set_cursor_position((
                panes.header.x + (text::width(prompt) + self.input.visual_cursor()) as u16,
                panes.header.y,
            ));
            first.push(Span::styled(self.input.value().to_string(), t.base()));
        } else {
            first.push(Span::styled(self.term.clone(), t.base()));
        }
        let status_line = Line::styled(status, t.dim()).right_aligned();
        let head_left = Paragraph::new(Line::from(first)).style(t.base());
        frame.render_widget(head_left, panes.header);
        frame.render_widget(
            status_line,
            Rect {
                y: panes.header.y,
                height: 1,
                ..panes.header
            },
        );
        let pad = match (&self.error, &self.flash) {
            (Some(e), _) => Line::styled(format!(" {e}"), t.down()),
            (None, Some(f)) => Line::styled(format!(" {f}"), t.accent()),
            (None, None) => Line::styled(format!(" {}", self.pad_line()), t.dim()),
        };
        frame.render_widget(
            Paragraph::new(pad),
            Rect {
                y: panes.header.y + 1,
                height: 1,
                ..panes.header
            },
        );

        let nav_empty = if self.term.is_empty() {
            "type a term"
        } else if self.loading {
            "searching…"
        } else {
            "no tickers match this term"
        };
        self.draw_nav(frame, panes.nav, nav_empty);
        self.draw_detail(frame, panes.detail);

        let source = self
            .selected()
            .and_then(|r| r.sample.as_ref())
            .and_then(|h| h.url.clone())
            .unwrap_or_default();
        frame.render_widget(
            Paragraph::new(format!(" source: {source}")).style(t.dim()),
            panes.source,
        );
    }

    fn help(&self) -> Help {
        Help::new("scratch", &if self.typing { TYPING_KEYS } else { KEYS })
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        if self.typing {
            self.on_typing_key(key)
        } else {
            self.on_list_key(key)
        }
    }

    fn tick(&mut self) -> Action {
        while let Ok(r) = self.client.rx.try_recv() {
            self.apply(r);
        }
        if self.edited_at.is_some_and(|t| t.elapsed() >= DEBOUNCE) {
            self.run_query();
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }

    fn leader_ok(&self) -> bool {
        !self.typing
    }

    fn takes_text(&self) -> bool {
        self.typing
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::crossterm::event::KeyModifiers;
    use std::sync::mpsc;

    fn press(s: &mut Scratch, c: KeyCode) -> Action {
        s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
    }

    fn hit(id: i64, ticker: &str, text: &str) -> Hit {
        Hit {
            id,
            ticker: ticker.into(),
            kind: "filing".into(),
            text: text.into(),
            url: Some(format!("https://example.test/{ticker}")),
            ..Hit::default()
        }
    }

    /// A screen wired to in-memory channels instead of search.py.
    fn harness(
        arg: Option<&str>,
    ) -> (
        Scratch,
        mpsc::Receiver<Request>,
        mpsc::Sender<Reply>,
        PathBuf,
    ) {
        let (req_tx, req_rx) = mpsc::channel();
        let (rep_tx, rep_rx) = mpsc::channel();
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_or(0, |d| d.as_nanos());
        let path =
            std::env::temp_dir().join(format!("scratch-test-{}-{nanos}.json", std::process::id()));
        let client = Client {
            tx: req_tx,
            rx: rep_rx,
        };
        let s = Scratch::new(
            Theme::default(),
            client,
            path.clone(),
            arg.map(str::to_string),
        );
        (s, req_rx, rep_tx, path)
    }

    fn reply(id: u64, counts: &[(&str, u64)], hits: Vec<Hit>) -> Reply {
        let mut r = Reply {
            id: Some(id),
            results: hits,
            ..Reply::default()
        };
        r.facets.insert(
            "ticker".into(),
            counts
                .iter()
                .map(|(t, c)| (Some(t.to_string()), *c))
                .collect(),
        );
        r
    }

    #[test]
    fn pads_toggle_and_round_trip() {
        let mut p = Pads::default();
        assert!(p.toggle("hbf", "SNDK"));
        assert!(p.toggle("hbf", "SKHY"));
        assert!(!p.toggle("hbf", "SNDK"));
        assert_eq!(p.pinned("hbf"), ["SKHY".to_string()]);
        assert!(!p.toggle("hbf", "SKHY"));
        assert!(p.pads.is_empty(), "an emptied pad is dropped");

        let path = std::env::temp_dir().join(format!("pads-rt-{}.json", std::process::id()));
        p.toggle("cowos", "TSM");
        p.last = "cowos".into();
        p.save(&path).expect("save");
        assert_eq!(Pads::load(&path), p);
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn rows_rank_by_chunks_and_keep_pins() {
        let counts = vec![("SNDK".to_string(), 97), ("SIMO".to_string(), 61)];
        let hits = vec![hit(1, "SIMO", "simo text"), hit(2, "SNDK", "sndk text")];
        let rows = build_rows(&counts, &hits, &["SKHY".to_string(), "SIMO".to_string()]);
        let names: Vec<&str> = rows.iter().map(|r| r.ticker.as_str()).collect();
        assert_eq!(names, ["SNDK", "SIMO", "SKHY"]);
        assert!(rows[1].pinned && !rows[0].pinned);
        assert_eq!(rows[0].sample.as_ref().map(|h| h.id), Some(2));
        assert_eq!(rows[2].chunks, 0, "a pin with no match stays listed at 0");
    }

    #[test]
    fn typing_sends_query_and_reply_fills_rows() {
        let (mut s, req, rep, path) = harness(None);
        assert!(s.typing, "an empty screen opens in typing mode");
        for c in "hbf".chars() {
            press(&mut s, KeyCode::Char(c));
        }
        press(&mut s, KeyCode::Enter);
        let Ok(Request::Query { id, q, facet_n, .. }) = req.try_recv() else {
            panic!("no query sent");
        };
        assert_eq!(q, "hbf");
        assert_eq!(facet_n, Some(FACET_N));
        rep.send(reply(
            id,
            &[("SNDK", 97), ("SIMO", 61)],
            vec![hit(1, "SNDK", "hbf")],
        ))
        .expect("send");
        s.tick();
        assert!(!s.loading);
        assert_eq!(s.rows.len(), 2);
        assert_eq!(s.selected().map(|r| r.ticker.as_str()), Some("SNDK"));
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn retyping_a_term_edits_in_place() {
        let (mut s, _req, _rep, path) = harness(Some("hbf"));
        press(&mut s, KeyCode::Char('/'));
        for _ in 0..3 {
            press(&mut s, KeyCode::Backspace);
        }
        for c in "bandwidth flash".chars() {
            press(&mut s, KeyCode::Char(c));
        }
        assert_eq!(s.input.value(), "bandwidth flash");
        press(&mut s, KeyCode::Enter);
        assert_eq!(s.term, "bandwidth flash");
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn pin_persists_for_the_term() {
        let (mut s, _req, _rep, path) = harness(Some("HBF"));
        assert_eq!(s.term, "hbf", "terms are normalized to lower case");
        assert!(!s.typing);
        s.rows = build_rows(&[("SNDK".into(), 97)], &[], &[]);
        s.list.select(Some(0));
        press(&mut s, KeyCode::Char('m'));
        assert_eq!(Pads::load(&path).pinned("hbf"), ["SNDK".to_string()]);
        assert!(s.rows[0].pinned);
        let _ = fs::remove_file(&path);
    }

    #[test]
    fn enter_opens_dossier_for_selected_ticker() {
        let (mut s, _req, _rep, path) = harness(Some("hbf"));
        s.rows = build_rows(&[("SNDK".into(), 97)], &[], &[]);
        s.list.select(Some(0));
        assert_eq!(
            press(&mut s, KeyCode::Enter),
            Action::Route(Route::Screen {
                screen: "dossier".into(),
                arg: Some("SNDK".into()),
            })
        );
        let _ = fs::remove_file(&path);
    }
}
