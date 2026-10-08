// Full-text search over SEC filing chunks, patents and profiles
// (py/derive/search.py BM25 index), as a live ratatui screen. The fzf picker
// in ui/search.lua is the other front end over the same engine.
//
//   ┌ search › t:MRVL guidance▏                              searching… ┐
//   │ facets    │ results                 │ preview (chunk ± 1 context) │
//   │ TICKER    │ MRVL 10K 2026-03-11 mda │ ── MRVL 10-K mda ◀ match    │
//   │ ● MRVL 22 │   …package of guidance… │ …guidance…                  │
//   ├───────────┴─────────────────────────┴─────────────────────────────┤
//   │ source: MRVL 10-K mda 2026-03-11  sec.gov/…/…-index.htm           │
//   └ keys ─────────────────────────────────────────────────────────────┘
//
// Data: client::Client (search.py --serve). Typing restarts a DEBOUNCE
// timer; tick() sends the query once it expires, so only typing pauses hit
// DuckDB. Replies carry the request id and anything but the newest query /
// preview request is dropped. Nothing here blocks on IO.
//
// Parts: client (server process), query (facet token rewriting, term
// highlighting, snippets), view (rendering), history (input history file).

mod client;
mod history;
mod query;
mod view;

use std::collections::HashMap;
use std::io;
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{Event, KeyCode, KeyEvent, KeyModifiers};
use ratatui::widgets::ListState;
use tui_input::Input;
use tui_input::backend::crossterm::EventHandler;

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::model::Source;
use crate::ui::command_palette::{self, Command, Entry, Palette};
use crate::ui::help::{Key, key};
use crate::ui::theme::Theme;

use client::{Client, Hit, Reply, Request};
use history::History;
use query::Dim;

/// Quiet period after the last keystroke before a query is sent.
const DEBOUNCE: Duration = Duration::from_millis(150);
/// Selection must rest this long before its context is fetched.
const PREVIEW_DELAY: Duration = Duration::from_millis(60);
/// Hits per query.
const K: usize = 60;
/// Neighbouring chunks either side shown in the preview.
const CONTEXT: u32 = 1;
/// Words of the chunk used as the docview jump quote.
const QUOTE_WORDS: usize = 10;
const FLASH_FOR: Duration = Duration::from_secs(2);

pub const KEYS: &[Key] = &[
    key("^p", "command palette"),
    key("↵", "open chunk in nvim"),
    key("M-v", "open source doc at passage"),
    key("^o", "open in browser"),
    key("tab", "focus input/facets/results/preview"),
    key("^j ^k", "next / prev result"),
    key("y", "copy source url"),
    key("?", "help"),
    key("esc", "quit"),
    key("↑ ↓", "history (input) / move"),
    key("^a ^e ^w ^u", "line editing (input)"),
    key("space ↵", "toggle facet (facets)"),
    key("^d ^u g G", "scroll (preview)"),
    key("/ i", "back to input"),
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Pane {
    Input,
    Facets,
    Results,
    Preview,
}

impl Pane {
    fn cycle(self, back: bool, compact: bool) -> Self {
        const ALL: [Pane; 4] = [Pane::Input, Pane::Facets, Pane::Results, Pane::Preview];
        const WIDE: [Pane; 3] = [Pane::Input, Pane::Results, Pane::Preview];
        let order: &[Pane] = if compact { &ALL } else { &WIDE };
        let i = order.iter().position(|p| *p == self).unwrap_or(0);
        order[if back {
            (i + order.len() - 1) % order.len()
        } else {
            (i + 1) % order.len()
        }]
    }
}

/// Sidebar row: a dimension heading or a countable value.
#[derive(Debug, Clone, PartialEq)]
pub enum FacetRow {
    Header(Dim),
    Item { dim: Dim, value: String, count: u64 },
}

pub struct Search {
    theme: Theme,
    input: Input,
    focus: Pane,
    history: History,
    client: Client,
    debounce: Duration,

    next_id: u64,
    /// Query text of the newest request sent, and its id.
    sent: Option<(u64, String)>,
    /// Set by edits; the query goes out DEBOUNCE after the last one.
    edited_at: Option<Instant>,
    /// Waiting on the reply to `sent`.
    loading: bool,

    results: Vec<Hit>,
    terms: Vec<String>,
    facets: Vec<FacetRow>,
    /// Matches for the query (all, not just the K shown).
    total: u64,
    ms: Option<u64>,
    error: Option<String>,
    list: ListState,
    facet_state: ListState,

    /// chunk id -> chunk + neighbours, from `get` replies.
    context: HashMap<i64, Vec<Hit>>,
    /// (request id, chunk id) of the outstanding `get`.
    context_req: Option<(u64, i64)>,
    selected_at: Option<Instant>,
    preview_scroll: u16,
    /// Lines in the preview at last draw (scroll bound) and its height.
    preview_len: u16,
    preview_height: u16,
    /// Jump the preview to the matched chunk once its context arrives.
    preview_jump: bool,

    show_help: bool,
    flash: Option<(String, Instant)>,
    palette: Palette,
    last_width: u16,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Search> {
    Ok(Search::new(
        arg.unwrap_or_default(),
        ctx.theme,
        Client::spawn(),
        History::load(),
    ))
}

impl Search {
    fn new(query: String, theme: Theme, client: Client, history: History) -> Self {
        let mut s = Self {
            theme,
            input: Input::new(query),
            focus: Pane::Input,
            history,
            client,
            debounce: DEBOUNCE,
            next_id: 0,
            sent: None,
            edited_at: None,
            loading: false,
            results: Vec::new(),
            terms: Vec::new(),
            facets: Vec::new(),
            total: 0,
            ms: None,
            error: None,
            list: ListState::default(),
            facet_state: ListState::default(),
            context: HashMap::new(),
            context_req: None,
            selected_at: None,
            preview_scroll: 0,
            preview_len: 0,
            preview_height: 0,
            preview_jump: false,
            show_help: false,
            flash: None,
            palette: Palette::default(),
            last_width: 120,
        };
        // the initial query goes out immediately (server start overlaps it)
        s.send_query();
        s
    }

    fn id(&mut self) -> u64 {
        self.next_id += 1;
        self.next_id
    }

    fn send_query(&mut self) {
        let q = self.input.value().to_string();
        let id = self.id();
        if self
            .client
            .tx
            .send(Request::Query {
                id,
                q: q.clone(),
                k: K,
            })
            .is_ok()
        {
            self.sent = Some((id, q));
            self.loading = true;
        }
        self.edited_at = None;
    }

    fn edited(&mut self) {
        self.edited_at = Some(Instant::now());
    }

    fn set_query(&mut self, q: String) {
        self.input = Input::new(q);
        self.edited();
    }

    pub fn selected(&self) -> Option<&Hit> {
        self.results.get(self.list.selected()?)
    }

    /// The selected hit's Source: its document URL with the chunk's opening
    /// words as a #:~:text= quote, so docview / browser land on the passage.
    pub fn selected_source(&self) -> Option<Source> {
        self.selected().map(hit_source)
    }

    fn apply(&mut self, r: Reply) {
        let Some(id) = r.id else {
            // no id: server-level failure (spawn error, server exited)
            self.error = r.error;
            self.loading = false;
            return;
        };
        if self.sent.as_ref().is_some_and(|(sid, _)| *sid == id) {
            self.loading = false;
            self.error = r.error;
            if self.error.is_some() {
                return;
            }
            self.results = r.results;
            self.terms = r.terms;
            self.ms = r.ms;
            self.total = r
                .facets
                .get("type")
                .map_or(0, |v| v.iter().map(|(_, c)| c).sum());
            self.facets = Dim::ALL
                .iter()
                .flat_map(|d| {
                    let items: Vec<FacetRow> = r
                        .facets
                        .get(d.name())
                        .into_iter()
                        .flatten()
                        .filter_map(|(v, c)| {
                            v.clone().map(|value| FacetRow::Item {
                                dim: *d,
                                value,
                                count: *c,
                            })
                        })
                        .collect();
                    let head = (!items.is_empty()).then_some(FacetRow::Header(*d));
                    head.into_iter().chain(items)
                })
                .collect();
            self.list.select(if self.results.is_empty() {
                None
            } else {
                Some(0)
            });
            *self.list.offset_mut() = 0;
            self.clamp_facet();
            self.selection_changed();
        } else if self.context_req.is_some_and(|(rid, _)| rid == id)
            && let Some((_, chunk)) = self.context_req.take()
        {
            if r.error.is_none() && !r.rows.is_empty() {
                self.context.insert(chunk, r.rows);
            } else {
                // no context came back: fall back to the hit itself so the
                // preview doesn't sit on "loading context…" forever
                if let Some(hit) = self.results.iter().find(|h| h.id == chunk).cloned() {
                    self.context.insert(chunk, vec![hit]);
                }
            }
        }
        // anything else is a stale reply: dropped
    }

    fn selection_changed(&mut self) {
        self.selected_at = Some(Instant::now());
        self.preview_scroll = 0;
        self.preview_jump = true;
    }

    fn move_result(&mut self, delta: isize) {
        if self.results.is_empty() {
            return;
        }
        let n = self.results.len() as isize;
        let cur = self.list.selected().unwrap_or(0) as isize;
        let next = (cur + delta).clamp(0, n - 1) as usize;
        if Some(next) != self.list.selected() {
            self.list.select(Some(next));
            self.selection_changed();
        }
    }

    fn clamp_facet(&mut self) {
        let item = |i: usize| matches!(self.facets.get(i), Some(FacetRow::Item { .. }));
        let cur = self.facet_state.selected().unwrap_or(0);
        let pick = (cur..self.facets.len())
            .find(|i| item(*i))
            .or_else(|| (0..cur).rev().find(|i| item(*i)));
        self.facet_state.select(pick);
    }

    fn move_facet(&mut self, down: bool) {
        let Some(cur) = self.facet_state.selected() else {
            return self.clamp_facet();
        };
        let item = |i: &usize| matches!(self.facets.get(*i), Some(FacetRow::Item { .. }));
        let next = if down {
            (cur + 1..self.facets.len()).find(item)
        } else {
            (0..cur).rev().find(item)
        };
        if let Some(n) = next {
            self.facet_state.select(Some(n));
        }
    }

    fn toggle_facet(&mut self) {
        let Some(FacetRow::Item { dim, value, .. }) =
            self.facet_state.selected().and_then(|i| self.facets.get(i))
        else {
            return;
        };
        let q = query::toggle(self.input.value(), *dim, value);
        self.set_query(q);
        // facet clicks are deliberate: no need to wait for more typing
        self.edited_at = Some(
            Instant::now()
                .checked_sub(self.debounce)
                .unwrap_or_else(Instant::now),
        );
    }

    fn scroll_preview(&mut self, delta: i32) {
        let max = self.preview_len.saturating_sub(self.preview_height) as i32;
        self.preview_scroll = (self.preview_scroll as i32 + delta).clamp(0, max.max(0)) as u16;
        self.preview_jump = false;
    }

    fn remember(&mut self) {
        self.history.push(self.input.value());
    }

    fn open_chunk(&mut self) -> Action {
        let Some(id) = self.selected().map(|h| h.id) else {
            return Action::None;
        };
        self.remember();
        Action::Nvim(NvimAction::Chunk { id: id.to_string() })
    }

    fn open_docview(&mut self) -> Action {
        match self.selected_source() {
            Some(src) if src.url.is_some() => {
                self.remember();
                let url = src.doc_url().unwrap_or_default().to_string();
                Action::Nvim(NvimAction::Docview {
                    url,
                    quote: src.quote(),
                })
            }
            Some(_) => self.flash_msg("no source document for this hit"),
            None => Action::None,
        }
    }

    fn open_browser(&mut self) -> Action {
        match self
            .selected_source()
            .as_ref()
            .and_then(|s| s.doc_url().map(str::to_string))
        {
            Some(u) => Action::OpenBrowser(u),
            None => self.flash_msg("no source document for this hit"),
        }
    }

    fn copy_url(&mut self) -> Action {
        match self
            .selected_source()
            .as_ref()
            .and_then(|s| s.doc_url().map(str::to_string))
        {
            Some(u) => Action::Copy(u),
            None => self.flash_msg("no source url"),
        }
    }

    fn flash_msg(&mut self, m: &str) -> Action {
        self.flash = Some((m.to_string(), Instant::now()));
        Action::None
    }

    /// A printable key in a non-input pane: jump to the input and type it.
    fn type_into_input(&mut self, key: KeyEvent) -> Action {
        self.focus = Pane::Input;
        self.input_key(key)
    }

    fn input_key(&mut self, key: KeyEvent) -> Action {
        match key.code {
            KeyCode::Up => {
                if let Some(q) = self.history.prev(self.input.value()) {
                    self.set_query(q);
                }
            }
            KeyCode::Down => {
                if let Some(q) = self.history.next() {
                    self.set_query(q);
                }
            }
            _ => {
                let before = self.input.value().to_string();
                self.input.handle_event(&Event::Key(key));
                if self.input.value() != before {
                    self.history.reset();
                    self.edited();
                }
            }
        }
        Action::None
    }
}

fn hit_source(h: &Hit) -> Source {
    let date = h
        .date
        .as_deref()
        .map(|d| d.get(..10).unwrap_or(d))
        .unwrap_or("");
    let mut label = format!("{} {}", h.ticker, h.form.as_deref().unwrap_or(&h.kind));
    if let Some(s) = h.section.as_deref() {
        label.push_str(&format!(" · {s}"));
    }
    if !date.is_empty() {
        label.push_str(&format!(" · {date}"));
    }
    if let Some(a) = h.accn.as_deref() {
        label.push_str(&format!(" · {a}"));
    }
    if h.url.is_none() && h.kind == "profile" {
        label.push_str(" · Yahoo Finance profile summary");
    }
    let url = h.url.as_ref().map(|u| {
        let quote = query::first_words(&h.text, QUOTE_WORDS);
        if quote.is_empty() {
            u.clone()
        } else {
            format!("{u}#:~:text={}", query::encode_fragment(&quote))
        }
    });
    Source {
        label,
        url,
        ..Source::default()
    }
}

impl Screen for Search {
    fn draw(&mut self, frame: &mut Frame) {
        self.render(frame);
    }

    fn tick(&mut self) -> Action {
        while let Ok(r) = self.client.rx.try_recv() {
            self.apply(r);
        }
        if self.edited_at.is_some_and(|t| t.elapsed() >= self.debounce) {
            if self
                .sent
                .as_ref()
                .is_some_and(|(_, q)| q == self.input.value())
            {
                self.edited_at = None;
            } else {
                self.send_query();
            }
        }
        if self
            .selected_at
            .is_some_and(|t| t.elapsed() >= PREVIEW_DELAY)
        {
            self.selected_at = None;
            if let Some(chunk) = self.selected().map(|h| h.id) {
                let pending = self.context_req.is_some_and(|(_, c)| c == chunk);
                if !self.context.contains_key(&chunk) && !pending {
                    let id = self.id();
                    if self
                        .client
                        .tx
                        .send(Request::Get {
                            id,
                            get: chunk,
                            context: CONTEXT,
                        })
                        .is_ok()
                    {
                        self.context_req = Some((id, chunk));
                    }
                }
            }
        }
        if self
            .flash
            .as_ref()
            .is_some_and(|(_, t)| t.elapsed() > FLASH_FOR)
        {
            self.flash = None;
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.palette.open
            && let Some(command) = self.palette.handle(key)
        {
            return match command {
                // the query is only an argument for search itself; chart and
                // earnings take a range/ticker and reject free text
                Some(Command::Screen(screen)) => Action::Nvim(NvimAction::Screen {
                    screen: screen.into(),
                    arg: (screen == "search").then(|| self.input.value().to_string()),
                }),
                Some(Command::Picker(screen)) => Action::Nvim(NvimAction::Picker {
                    screen: screen.into(),
                }),
                Some(Command::Pane(pane)) => {
                    self.focus = [Pane::Input, Pane::Facets, Pane::Results, Pane::Preview]
                        [(pane as usize).min(3)];
                    Action::None
                }
                _ => Action::None,
            };
        }
        if self.show_help {
            self.show_help = false;
            return Action::None;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let alt = key.modifiers.contains(KeyModifiers::ALT);
        if key.code == KeyCode::Char('p') && ctrl {
            let mut entries = command_palette::destinations("", "search");
            entries.extend([
                Entry::new("Focus search input", "", Command::Pane(0)),
                Entry::new("Show facets", "compact view", Command::Pane(1)),
                Entry::new("Show results", "", Command::Pane(2)),
                Entry::new("Show preview", "", Command::Pane(3)),
            ]);
            self.palette.show(entries);
            return Action::None;
        }
        let compact = self.last_width < 120;
        // keys that mean the same in every pane
        match key.code {
            KeyCode::Esc => {
                self.remember();
                return Action::Quit;
            }
            KeyCode::Tab => {
                self.focus = self.focus.cycle(false, compact);
                return Action::None;
            }
            KeyCode::BackTab => {
                self.focus = self.focus.cycle(true, compact);
                return Action::None;
            }
            KeyCode::Char('j' | 'n') if ctrl => {
                self.move_result(1);
                return Action::None;
            }
            KeyCode::Char('k' | 'p') if ctrl => {
                self.move_result(-1);
                return Action::None;
            }
            KeyCode::Char('v') if alt => return self.open_docview(),
            KeyCode::Char('o') if ctrl => return self.open_browser(),
            KeyCode::Char('?') if !ctrl && !alt => {
                self.show_help = true;
                return Action::None;
            }
            KeyCode::Enter if self.focus != Pane::Facets => return self.open_chunk(),
            _ => {}
        }
        let plain_char = matches!(key.code, KeyCode::Char(_)) && !ctrl && !alt;
        match self.focus {
            Pane::Input => self.input_key(key),
            Pane::Results => match key.code {
                KeyCode::Char('j') | KeyCode::Down => {
                    self.move_result(1);
                    Action::None
                }
                KeyCode::Char('k') | KeyCode::Up => {
                    self.move_result(-1);
                    Action::None
                }
                KeyCode::Char('g') | KeyCode::Home => {
                    self.move_result(-(self.results.len() as isize));
                    Action::None
                }
                KeyCode::Char('G') | KeyCode::End => {
                    self.move_result(self.results.len() as isize);
                    Action::None
                }
                KeyCode::Char('y') => self.copy_url(),
                KeyCode::Char('v') => self.open_docview(),
                KeyCode::Char('/' | 'i') => {
                    self.focus = Pane::Input;
                    Action::None
                }
                KeyCode::Char('d') if ctrl => {
                    self.scroll_preview((self.preview_height / 2).max(1) as i32);
                    Action::None
                }
                KeyCode::Char('u') if ctrl => {
                    self.scroll_preview(-((self.preview_height / 2).max(1) as i32));
                    Action::None
                }
                _ if plain_char => self.type_into_input(key),
                _ => Action::None,
            },
            Pane::Facets => match key.code {
                KeyCode::Char('j') | KeyCode::Down => {
                    self.move_facet(true);
                    Action::None
                }
                KeyCode::Char('k') | KeyCode::Up => {
                    self.move_facet(false);
                    Action::None
                }
                KeyCode::Char(' ') | KeyCode::Enter => {
                    self.toggle_facet();
                    Action::None
                }
                KeyCode::Char('/' | 'i') => {
                    self.focus = Pane::Input;
                    Action::None
                }
                KeyCode::Char('y') => self.copy_url(),
                _ if plain_char => self.type_into_input(key),
                _ => Action::None,
            },
            Pane::Preview => {
                let half = (self.preview_height / 2).max(1) as i32;
                match key.code {
                    KeyCode::Char('j') | KeyCode::Down => self.scroll_preview(1),
                    KeyCode::Char('k') | KeyCode::Up => self.scroll_preview(-1),
                    KeyCode::Char('d') if ctrl => self.scroll_preview(half),
                    KeyCode::Char('u') if ctrl => self.scroll_preview(-half),
                    KeyCode::Char(' ') | KeyCode::PageDown => self.scroll_preview(half * 2),
                    KeyCode::PageUp => self.scroll_preview(-half * 2),
                    KeyCode::Char('g') | KeyCode::Home => self.scroll_preview(-(u16::MAX as i32)),
                    KeyCode::Char('G') | KeyCode::End => self.scroll_preview(u16::MAX as i32),
                    KeyCode::Char('y') => return self.copy_url(),
                    KeyCode::Char('v') => return self.open_docview(),
                    KeyCode::Char('/' | 'i') => self.focus = Pane::Input,
                    _ if plain_char => return self.type_into_input(key),
                    _ => {}
                }
                Action::None
            }
        }
    }
}

#[cfg(test)]
mod tests;
