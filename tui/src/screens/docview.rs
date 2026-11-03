// Document viewer. Search pushes it for alt-v / Enter (search/mod.rs).
//
// Arg encodings (main's router passes the string through unchanged):
//   <url>                    a source document
//   <url>#:~:text=<quote>    same, jumping to the quote (percent-encoded, the
//                            form dossier and search links already carry)
//   chunk:<id>               one search chunk with two neighbours either side
//
// Loading is off-thread: py/derive/docview.py (fetch, cache, SEC HTML to
// markdown, pdftotext) or `search.py get`, then the text is read here. A PDF
// shows its extracted text; an image has no text view. `o` opens the original
// in the browser from any state.
//
// SEC HTML also comes back as typed blocks (docview.py --blocks, parser in
// py/sources/filing_blocks.py); when present the reader lays those out with
// ui::doc_blocks (prose column, headings, financial tables) instead of the
// markdown text. A search chunk with an SEC url opens its real document at
// the hit; other chunks keep the plain neighbourhood view.
//
// Keys: a Neovim-style cursor (ui::text_cursor): hjkl, w/b/e, 0/^/$, gh/gl,
// f/t/F/T ; ,, gg/G, vip/viw text objects,
// {/} paragraphs, ^d/^u, counts; v / V visual mode, y or <space>y copies the
// selection. Here: n/N next/previous match of the quote, ]]/[[ next/previous
// Item, ]h/[h next/previous heading, o open in browser, y copy url (normal
// mode), q/esc back.

use std::io;
use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Paragraph, Wrap};
use serde::Deserialize;

use crate::app::{Action, Ctx, Screen};
use crate::model::Source;
use crate::pyrun;
use crate::ui::doc_blocks::{self, Block};
use crate::ui::help::{self, Key, key, section};
use crate::ui::text_cursor::{Outcome, TextCursor};
use crate::ui::theme::Theme;

const FLASH_FOR: Duration = Duration::from_secs(2);
const DOCVIEW_PY: &str = "py/derive/docview.py";
const SEARCH_PY: &str = "py/derive/search.py";
/// Marks the hit inside a chunk's neighbourhood.
const MATCH_MARK: &str = ">>> match";
const HINT: &str = "? keys  hjkl wbe  v/V select  ␣y copy  n/N match  o browser  y url  q back";
const BLOCK_HINT: &str = "? keys  hjkl wbe  v/V select  ␣y copy  ]]/[[ item  ]h/[h heading  n/N match  q back";

/// Docview's own keys; the `?` overlay shows these after the cursor's.
const DOC_KEYS: &[Key] = &[
    section("document"),
    key("]] [[", "next / previous Item"),
    key("]h [h", "next / previous heading"),
    key("n N", "next / previous quote match"),
    key("o", "open the source in the browser"),
    key("y", "copy the source URL (normal mode)"),
    key("spc t o", "lazygit in a new tmux window"),
    key("?", "this help"),
    key("q esc", "back"),
];

/// What an arg asks for.
#[derive(Debug, Clone, PartialEq)]
pub enum Target {
    Url { url: String, quote: Option<String> },
    Chunk(i64),
}

/// Parses an arg (see the module comment). None for an empty or malformed one.
pub fn parse_arg(arg: &str) -> Option<Target> {
    let arg = arg.trim();
    if let Some(id) = arg.strip_prefix("chunk:") {
        return id.trim().parse().ok().map(Target::Chunk);
    }
    // model::Source already knows the #:~:text= fragment format
    let src = Source::url("", arg);
    let url = src.doc_url().filter(|u| !u.is_empty())?.to_string();
    let quote = src.quote().filter(|q| !q.trim().is_empty());
    Some(Target::Url { url, quote })
}

/// Arg for a search chunk by id.
pub fn chunk_arg(id: impl std::fmt::Display) -> String {
    format!("chunk:{id}")
}

/// A loaded document: plain text lines (or typed blocks) plus where to look
/// in them. With blocks, "logical line" below means block index.
#[derive(Debug, Clone, Default)]
struct Doc {
    title: String,
    subtitle: String,
    /// Browser target for `o` and `y`.
    url: Option<String>,
    lines: Vec<String>,
    blocks: Option<Vec<Block>>,
    /// Logical lines that hold the quote (or a chunk's hit), ascending.
    matches: Vec<usize>,
    /// Logical line to centre on when first shown.
    jump: Option<usize>,
}

enum State {
    Loading,
    Failed(String),
    Ready(Doc),
}

pub struct Docview {
    theme: Theme,
    /// Header text while loading or after a failure.
    label: String,
    /// Browser target known before loading (the URL itself, for documents).
    source: Option<String>,
    rx: Option<Receiver<Result<Doc, String>>>,
    state: State,
    /// Cursor, visual selection and scroll position over `rows`.
    cur: TextCursor,
    /// First key of a `]]` / `[[` / `]h` / `[h` jump.
    bracket: Option<char>,
    /// `?` key overlay showing.
    help: bool,
    /// Laid-out rows for `wrapped_at` columns: (logical line, styled line).
    rows: Vec<(usize, Line<'static>)>,
    /// First visual row of each logical line.
    starts: Vec<usize>,
    wrapped_at: usize,
    /// Logical line to centre on at the next draw.
    pending: Option<usize>,
    flash: Option<(String, Instant)>,
}

pub fn open(_ctx: &Ctx, arg: Option<String>) -> io::Result<Docview> {
    let arg = arg.unwrap_or_default();
    let Some(target) = parse_arg(&arg) else {
        return Ok(Docview::with(
            "docview".into(),
            State::Failed(
                "no document: docview <url>[#:~:text=quote] or docview chunk:<id>".into(),
            ),
            None,
            None,
        ));
    };
    let (label, source) = match &target {
        Target::Url { url, .. } => (url.clone(), Some(url.clone())),
        Target::Chunk(id) => (format!("chunk {id}"), None),
    };
    let (tx, rx) = mpsc::channel();
    thread::spawn(move || {
        let _ = tx.send(load(&target));
    });
    Ok(Docview::with(label, State::Loading, source, Some(rx)))
}

impl Docview {
    fn with(
        label: String,
        state: State,
        source: Option<String>,
        rx: Option<Receiver<Result<Doc, String>>>,
    ) -> Self {
        Self {
            theme: Theme::default(),
            label,
            source,
            rx,
            state,
            cur: TextCursor::skipping_blanks().centered(),
            bracket: None,
            help: false,
            rows: Vec::new(),
            starts: Vec::new(),
            wrapped_at: 0,
            pending: None,
            flash: None,
        }
    }

    fn is_ready(&self) -> bool {
        matches!(self.state, State::Ready(_))
    }

    fn open_url(&self) -> Option<String> {
        match &self.state {
            State::Ready(doc) => doc.url.clone().or_else(|| self.source.clone()),
            _ => self.source.clone(),
        }
    }

    fn open_browser(&mut self) -> Action {
        match self.open_url() {
            Some(u) => Action::OpenBrowser(u),
            None => {
                self.flash_msg("no source url".into());
                Action::None
            }
        }
    }

    fn copy_url(&mut self) -> Action {
        match self.open_url() {
            Some(u) => Action::Copy(u),
            None => {
                self.flash_msg("no source url".into());
                Action::None
            }
        }
    }

    /// Moves the cursor to the next (or previous) match, wrapping at the ends.
    fn jump_match(&mut self, forward: bool) {
        let State::Ready(doc) = &self.state else {
            return;
        };
        let rows: Vec<usize> = doc
            .matches
            .iter()
            .filter_map(|m| self.starts.get(*m).copied())
            .collect();
        let at = self.cur.pos.row;
        let target = if forward {
            rows.iter().copied().find(|r| *r > at).or(rows.first().copied())
        } else {
            rows.iter().copied().rev().find(|r| *r < at).or(rows.last().copied())
        };
        if let Some(row) = target {
            self.cur.goto_row(row);
        }
    }

    fn flash_msg(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
    }

    /// Moves the cursor to the next (or previous) heading at `max_level` or above.
    fn jump_heading(&mut self, forward: bool, max_level: u8) {
        let State::Ready(doc) = &self.state else {
            return;
        };
        let Some(blocks) = &doc.blocks else {
            return;
        };
        let rows: Vec<usize> = blocks
            .iter()
            .enumerate()
            .filter(|(_, b)| doc_blocks::is_heading(b, max_level))
            .filter_map(|(i, _)| self.starts.get(i).copied())
            .collect();
        let at = self.cur.pos.row;
        let target = if forward {
            rows.iter().copied().find(|r| *r > at)
        } else {
            rows.iter().copied().rev().find(|r| *r < at)
        };
        if let Some(row) = target {
            self.cur.goto_row(row);
        }
    }

    /// The visual selection framed for a Claude prompt: document, section
    /// and source URL, then the excerpt in a fence. None without a selection.
    fn claude_excerpt(&self) -> Option<String> {
        let text = self.cur.selected_text()?;
        let State::Ready(doc) = &self.state else {
            return Some(text);
        };
        let mut head = format!("From {}", doc.title);
        if let Some(sec) = self.section() {
            head.push_str(&format!(" § {sec}"));
        }
        if let Some(url) = &doc.url {
            head.push_str(&format!(" ({url})"));
        }
        Some(format!("{head}:\n```\n{text}\n```\n"))
    }

    /// The Item and nearest heading above the cursor, for the footer.
    fn section(&self) -> Option<String> {
        let State::Ready(doc) = &self.state else {
            return None;
        };
        let blocks = doc.blocks.as_ref()?;
        let (block, _) = self.rows.get(self.cur.pos.row)?;
        let mut item = None;
        let mut sub = None;
        for b in blocks[..=(*block).min(blocks.len() - 1)].iter().rev() {
            if let Block::H { level, text, .. } = b {
                if *level <= 1 {
                    item = Some(text.clone());
                    break;
                }
                if sub.is_none() && *level <= 3 {
                    sub = Some(text.clone());
                }
            }
        }
        match (item, sub) {
            (Some(i), Some(s)) => Some(format!("{i} › {s}")),
            (i, s) => i.or(s),
        }
    }
}

/// Runs the loader for `target`. Blocking; called on a worker thread.
fn load(target: &Target) -> Result<Doc, String> {
    match target {
        Target::Url { url, quote } => load_url(url, quote.as_deref()),
        Target::Chunk(id) => load_chunk(*id),
    }
}

#[derive(Deserialize)]
struct Located {
    path: String,
    kind: String,
    text_path: Option<String>,
    /// 1-based line of the quote in the file that was read.
    line: Option<usize>,
    title: Option<String>,
    url: Option<String>,
    index_url: Option<String>,
    blocks_path: Option<String>,
    /// Index of the block holding the quote.
    block: Option<usize>,
}

fn load_url(url: &str, quote: Option<&str>) -> Result<Doc, String> {
    let mut args = vec![url];
    if let Some(q) = quote {
        args.extend(["--quote", q]);
    }
    args.extend(["--json", "--blocks"]);
    let out = pyrun::run_script(DOCVIEW_PY, &args)?;
    let loc: Located = serde_json::from_str(&out).map_err(|e| format!("docview.py output: {e}"))?;
    let open_url = loc.index_url.clone().or(loc.url.clone()).or_else(|| Some(url.to_string()));
    let title = loc
        .title
        .clone()
        .filter(|t| !t.is_empty())
        .unwrap_or_else(|| url.to_string());
    if let Some(blocks) = loc.blocks_path.as_deref().and_then(|p| doc_blocks::load(p).ok()) {
        if !blocks.is_empty() {
            let matches: Vec<usize> = loc.block.into_iter().collect();
            return Ok(Doc {
                title,
                subtitle: loc.url.clone().unwrap_or_else(|| url.to_string()),
                url: open_url,
                lines: Vec::new(),
                jump: matches.first().copied(),
                matches,
                blocks: Some(blocks),
            });
        }
    }

    let text = match loc.kind.as_str() {
        "md" | "text" => read_text(&loc.path),
        "pdf" => loc.text_path.as_deref().and_then(read_text),
        "image" => None,
        other => return Err(format!("no text viewer for {other} documents")),
    };
    let subtitle = if loc.kind == "pdf" {
        format!("pdf text · {url}")
    } else {
        url.to_string()
    };
    Ok(match text {
        Some(text) => {
            let lines: Vec<String> = text.lines().map(str::to_string).collect();
            let matches = quote.map(|q| quote_matches(&lines, q)).unwrap_or_default();
            let jump = loc
                .line
                .and_then(|l| l.checked_sub(1))
                .filter(|i| *i < lines.len())
                .or_else(|| matches.first().copied());
            Doc {
                title,
                subtitle,
                url: open_url,
                lines,
                matches,
                jump,
                blocks: None,
            }
        }
        None => Doc {
            title,
            subtitle,
            url: open_url,
            lines: vec![format!(
                "No text to show for this {}. Press o to open it in the browser.",
                loc.kind
            )],
            ..Doc::default()
        },
    })
}

fn read_text(path: &str) -> Option<String> {
    let bytes = std::fs::read(path).ok()?;
    let text = String::from_utf8_lossy(&bytes).into_owned();
    (!text.trim().is_empty()).then_some(text)
}

#[derive(Deserialize)]
struct ChunkRow {
    id: i64,
    ticker: Option<String>,
    #[serde(rename = "type")]
    kind: Option<String>,
    section: Option<String>,
    form: Option<String>,
    date: Option<String>,
    url: Option<String>,
    text: Option<String>,
}

fn opt(s: &Option<String>) -> &str {
    s.as_deref().unwrap_or("")
}

/// The chunk with two neighbours either side: a header, the source url, then
/// each chunk with the hit marked.
fn load_chunk(id: i64) -> Result<Doc, String> {
    let id_s = id.to_string();
    let out = pyrun::run_script(
        SEARCH_PY,
        &["get", id_s.as_str(), "--context", "2", "--json"],
    )?;
    let rows: Vec<ChunkRow> =
        serde_json::from_str(&out).map_err(|e| format!("search.py get output: {e}"))?;
    let hit = rows
        .iter()
        .find(|r| r.id == id)
        .or(rows.first())
        .ok_or_else(|| format!("chunk {id} not found"))?;
    if let Some(url) = hit.url.as_deref().filter(|u| u.contains("sec.gov")) {
        // The hit's opening words locate it in the real document.
        // Chunk text joins table cells and bullets with "·" / "|": not in the doc.
        let quote: String = opt(&hit.text)
            .split_whitespace()
            .filter(|w| !matches!(*w, "·" | "|" | "•"))
            .take(12)
            .collect::<Vec<_>>()
            .join(" ");
        if let Ok(mut doc) = load_url(url, Some(&quote)) {
            if doc.blocks.is_some() {
                doc.title = format!(
                    "{} · {} {} · {}",
                    opt(&hit.ticker),
                    opt(&hit.form),
                    opt(&hit.date),
                    opt(&hit.section)
                );
                return Ok(doc);
            }
        }
    }
    let head = format!(
        "{} — {} / {} ({}, {})",
        opt(&hit.ticker),
        opt(&hit.kind),
        opt(&hit.section),
        opt(&hit.form),
        opt(&hit.date)
    );
    let mut lines = vec![head.clone(), opt(&hit.url).to_string(), String::new()];
    let mut matches = Vec::new();
    for row in &rows {
        if row.id == id {
            matches.push(lines.len());
            lines.push(MATCH_MARK.to_string());
        }
        lines.extend(opt(&row.text).lines().map(str::to_string));
        lines.push(String::new());
    }
    Ok(Doc {
        title: head,
        subtitle: opt(&hit.url).to_string(),
        url: hit.url.clone(),
        jump: matches.first().copied(),
        lines,
        matches,
        blocks: None,
    })
}

/// Lowercases, drops markdown escapes and table bars, and collapses spaces, so
/// a quote from the chunk text matches the converted document.
fn norm(s: &str) -> String {
    let mapped: String = s
        .chars()
        .filter(|c| *c != '\\')
        .map(|c| match c {
            '\u{2019}' => '\'',
            '\u{201c}' | '\u{201d}' => '"',
            '*' | '_' | '`' | '•' | '|' => ' ',
            c => c,
        })
        .collect();
    mapped
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .to_lowercase()
}

/// Lines containing the quote's opening words. Tries 8, 6, 4 then 3 words and
/// takes the first length that matches anywhere (markup can split a long quote).
fn quote_matches(lines: &[String], quote: &str) -> Vec<usize> {
    let norm_lines: Vec<String> = lines.iter().map(|l| norm(l)).collect();
    let quote = norm(quote);
    let words: Vec<&str> = quote.split(' ').filter(|w| !w.is_empty()).collect();
    for n in [8, 6, 4, 3] {
        let needle = words[..n.min(words.len())].join(" ");
        if needle.len() < 8 {
            break;
        }
        let hits: Vec<usize> = norm_lines
            .iter()
            .enumerate()
            .filter(|(_, l)| l.contains(&needle))
            .map(|(i, _)| i)
            .collect();
        if !hits.is_empty() {
            return hits;
        }
    }
    Vec::new()
}

/// Greedy word wrap to `width` columns. Continuation rows keep the line's
/// leading spaces (capped at a quarter of the width); words longer than a row
/// are split.
fn wrap(line: &str, width: usize) -> Vec<String> {
    let indent_len = line
        .chars()
        .take_while(|c| *c == ' ')
        .count()
        .min(width / 4);
    let indent = " ".repeat(indent_len);
    let avail = width.saturating_sub(indent_len).max(1);
    let mut rows: Vec<String> = Vec::new();
    let mut cur = String::new();
    for word in line.split_whitespace() {
        let mut word = word;
        loop {
            let wl = word.chars().count();
            let cl = cur.chars().count();
            if cur.is_empty() && wl <= avail {
                cur.push_str(word);
                break;
            }
            if !cur.is_empty() && cl + 1 + wl <= avail {
                cur.push(' ');
                cur.push_str(word);
                break;
            }
            if !cur.is_empty() {
                rows.push(format!("{indent}{cur}"));
                cur.clear();
                continue;
            }
            let cut = word
                .char_indices()
                .nth(avail)
                .map_or(word.len(), |(i, _)| i);
            rows.push(format!("{indent}{}", &word[..cut]));
            word = &word[cut..];
            if word.is_empty() {
                break;
            }
        }
    }
    if !cur.is_empty() || rows.is_empty() {
        rows.push(format!("{indent}{cur}"));
    }
    rows
}

fn wrap_all(lines: &[String], width: usize) -> (Vec<(usize, Line<'static>)>, Vec<usize>) {
    let mut rows = Vec::new();
    let mut starts = Vec::with_capacity(lines.len());
    for (i, line) in lines.iter().enumerate() {
        starts.push(rows.len());
        rows.extend(wrap(line, width).into_iter().map(|r| (i, Line::from(r))));
    }
    (rows, starts)
}

/// A matched block's rows get an accent bar in the left margin.
fn gutter(line: &Line<'static>, style: Style) -> Line<'static> {
    let mut spans = line.spans.clone();
    match spans.first_mut() {
        Some(first) if first.content.starts_with(' ') => {
            first.content = first.content[1..].to_string().into();
        }
        _ => {}
    }
    let mut out = vec![Span::styled("▌", style)];
    out.extend(spans);
    Line::from(out)
}

fn doc_has_blocks(state: &State) -> bool {
    matches!(state, State::Ready(Doc { blocks: Some(_), .. }))
}

impl Screen for Docview {
    fn draw(&mut self, frame: &mut Frame) {
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(frame.area());
        let width = body.width.max(1) as usize;

        if let State::Ready(doc) = &self.state {
            if self.wrapped_at != width {
                let (rows, starts) = match &doc.blocks {
                    Some(blocks) => doc_blocks::layout(blocks, width, &self.theme),
                    None => wrap_all(&doc.lines, width),
                };
                // Keep the cursor on the same logical line across a reflow.
                let (old_rows, old_starts) = (&self.rows, &self.starts);
                let remap = |r: usize| match old_rows.get(r) {
                    Some((line, _)) => {
                        let off = r - old_starts.get(*line).copied().unwrap_or(r);
                        let start = starts.get(*line).copied().unwrap_or(0);
                        let end = starts.get(line + 1).copied().unwrap_or(rows.len());
                        (start + off).min(end.saturating_sub(1).max(start))
                    }
                    None => 0,
                };
                self.cur.remap(remap);
                let texts: Vec<String> = rows.iter().map(|(_, l)| TextCursor::line_text(l)).collect();
                (self.rows, self.starts) = (rows, starts);
                self.cur.set_rows(&texts);
                self.wrapped_at = width;
            }
        }
        self.cur.set_height(body.height.max(1) as usize);
        if let Some(line) = self.pending.take() {
            let row = self.starts.get(line).copied().unwrap_or(0);
            self.cur.goto_row(row);
        }

        let dim = Style::default().fg(self.theme.dim);
        let accent = Style::default()
            .fg(self.theme.accent)
            .add_modifier(Modifier::BOLD);
        let (title, subtitle) = match &self.state {
            State::Ready(doc) => (doc.title.as_str(), doc.subtitle.as_str()),
            State::Loading => (self.label.as_str(), "loading…"),
            State::Failed(_) => (self.label.as_str(), "failed"),
        };
        frame.render_widget(
            Paragraph::new(vec![
                Line::from(Span::styled(title.to_string(), accent)),
                Line::from(Span::styled(subtitle.to_string(), dim)),
            ]),
            head,
        );

        match &self.state {
            State::Loading => {
                frame.render_widget(Paragraph::new(Span::styled("loading source…", dim)), body);
            }
            State::Failed(err) => {
                let style = Style::default().fg(self.theme.down);
                frame.render_widget(
                    Paragraph::new(err.as_str())
                        .style(style)
                        .wrap(Wrap { trim: false }),
                    body,
                );
            }
            State::Ready(doc) => {
                let blocks = doc.blocks.is_some();
                let visible: Vec<Line> = self
                    .cur
                    .visible()
                    .map(|r| {
                        let (line, text) = &self.rows[r];
                        let hit = doc.matches.binary_search(line).is_ok() && text.width() > 0;
                        let drawn = match (hit, blocks) {
                            (true, true) => gutter(text, accent),
                            (true, false) => text.clone().style(accent),
                            _ => text.clone(),
                        };
                        self.cur.decorate(r, drawn, &self.theme)
                    })
                    .collect();
                frame.render_widget(Paragraph::new(visible), body);
            }
        }

        let footer = match &self.flash {
            Some((msg, _)) => msg.clone(),
            None if self.is_ready() => {
                let total = self.rows.len().max(1);
                let pos = format!("{}%", (self.cur.pos.row + 1) * 100 / total);
                let lead = match self.cur.status() {
                    Some(st) => st,
                    None if doc_has_blocks(&self.state) => BLOCK_HINT.to_string(),
                    None => HINT.to_string(),
                };
                match self.section() {
                    Some(sec) => format!("{lead}  {pos}  § {sec}"),
                    None => format!("{lead}  {pos}"),
                }
            }
            None => HINT.to_string(),
        };
        frame.render_widget(Paragraph::new(Span::styled(footer, dim)), foot);
        if self.help {
            let keys: Vec<Key> = [crate::ui::text_cursor::KEYS, DOC_KEYS].concat();
            help::render_overlay(frame, frame.area(), "reader keys", &keys, &self.theme);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        // ? opens the key overlay; any key closes it
        if self.help {
            self.help = false;
            return Action::None;
        }
        if key.code == KeyCode::Char('?') {
            self.help = true;
            return Action::None;
        }
        if !self.is_ready() {
            return match key.code {
                KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
                KeyCode::Char('o') => self.open_browser(),
                KeyCode::Char('y') => self.copy_url(),
                _ => Action::None,
            };
        }
        if let Some(first) = self.bracket.take() {
            let forward = first == ']';
            match key.code {
                KeyCode::Char(c) if c == first => self.jump_heading(forward, 1),
                KeyCode::Char('h') => self.jump_heading(forward, 3),
                _ => {}
            }
            return Action::None;
        }
        if matches!(key.code, KeyCode::Char('[' | ']')) && key.modifiers.is_empty() {
            if let KeyCode::Char(c) = key.code {
                self.bracket = Some(c);
            }
            return Action::None;
        }
        match self.cur.on_key(key) {
            Outcome::Handled => return Action::None,
            Outcome::Yank(text) => return Action::Copy(text),
            Outcome::Unhandled => {}
        }
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => Action::Quit,
            KeyCode::Char('o') => self.open_browser(),
            KeyCode::Char('y') => self.copy_url(),
            KeyCode::Char('n') => {
                self.jump_match(true);
                Action::None
            }
            KeyCode::Char('N') => {
                self.jump_match(false);
                Action::None
            }
            _ => Action::None,
        }
    }

    fn take_selection(&mut self) -> Option<String> {
        self.cur.take_selection()
    }

    /// `<space>ac` with a selection: the excerpt plus where it came from.
    fn take_claude_selection(&mut self) -> Option<String> {
        let text = self.claude_excerpt();
        self.cur.take_selection();
        text
    }

    /// `<space>as` sends the visual selection (with its source) to Claude.
    fn claude_context(&self) -> Option<String> {
        self.claude_excerpt()
    }

    fn tick(&mut self) -> Action {
        if let Some(rx) = &self.rx {
            let res = match rx.try_recv() {
                Ok(res) => Some(res),
                Err(TryRecvError::Empty) => None,
                Err(TryRecvError::Disconnected) => Some(Err("loader stopped".to_string())),
            };
            if let Some(res) = res {
                self.rx = None;
                self.state = match res {
                    Ok(doc) => {
                        self.pending = doc.jump;
                        self.wrapped_at = 0;
                        State::Ready(doc)
                    }
                    Err(e) => State::Failed(e),
                };
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

    fn needs_redraw(&self) -> bool {
        self.rx.is_some() || self.flash.is_some()
    }

    fn set_flash(&mut self, msg: String) {
        self.flash_msg(msg);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    fn press(v: &mut Docview, code: KeyCode) -> Action {
        v.on_key(KeyEvent::new(code, KeyModifiers::NONE))
    }

    fn screen_text(v: &mut Docview, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).expect("terminal");
        t.draw(|f| v.draw(f)).expect("draw");
        let b = t.backend().buffer();
        (0..b.area.height)
            .map(|y| {
                (0..b.area.width)
                    .map(|x| b[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn doc(lines: Vec<String>, matches: Vec<usize>, url: Option<&str>) -> Docview {
        let jump = matches.first().copied();
        Docview::with(
            "label".into(),
            State::Ready(Doc {
                title: "Title".into(),
                subtitle: "sub".into(),
                url: url.map(str::to_string),
                lines,
                matches,
                jump,
                blocks: None,
            }),
            None,
            None,
        )
    }

    #[test]
    fn parses_url_quote_and_chunk_forms() {
        assert_eq!(
            parse_arg("https://a/b.htm"),
            Some(Target::Url {
                url: "https://a/b.htm".into(),
                quote: None
            })
        );
        assert_eq!(
            parse_arg("https://a/b.htm#:~:text=Q2%20Net%20Revenue%3A%20%242.739"),
            Some(Target::Url {
                url: "https://a/b.htm".into(),
                quote: Some("Q2 Net Revenue: $2.739".into())
            })
        );
        assert_eq!(parse_arg("chunk:149731"), Some(Target::Chunk(149731)));
        assert_eq!(parse_arg("chunk: 7 "), Some(Target::Chunk(7)));
        assert_eq!(parse_arg("chunk:x"), None);
        assert_eq!(parse_arg("  "), None);
        assert_eq!(
            parse_arg("https://a#:~:text="),
            Some(Target::Url {
                url: "https://a".into(),
                quote: None
            })
        );
    }

    #[test]
    fn chunk_arg_is_the_chunk_id() {
        assert_eq!(chunk_arg(42), "chunk:42");
    }

    #[test]
    fn quote_matches_fall_back_to_fewer_words_and_ignore_markup() {
        let quote = "Net revenue for the year grew sharply across all segments";
        let lines: Vec<String> = [
            "Intro",
            "**Net revenue** for the year grew sharply in every segment.",
        ]
        .iter()
        .map(|s| s.to_string())
        .collect();
        // the 8-word needle is absent; the 6-word one hits, markup ignored
        assert_eq!(quote_matches(&lines, quote), vec![1]);

        let more: Vec<String> = [
            "Intro",
            "**Net revenue** for the year grew sharply in every segment.",
            "Net revenue for the year grew sharply across all segments and more",
        ]
        .iter()
        .map(|s| s.to_string())
        .collect();
        // with the full 8 words present, only that line counts
        assert_eq!(quote_matches(&more, quote), vec![2]);
        assert_eq!(
            quote_matches(&more, "nothing like this in the doc"),
            Vec::<usize>::new()
        );
    }

    #[test]
    fn wrap_breaks_words_and_splits_long_ones() {
        assert_eq!(wrap("aaa bbb ccc", 7), vec!["aaa bbb", "ccc"]);
        assert_eq!(wrap("abcdefghij", 4), vec!["abcd", "efgh", "ij"]);
        assert_eq!(wrap("", 10), vec![""]);
        let (rows, starts) = wrap_all(&["aa bb".into(), "cc".into()], 3);
        assert_eq!(starts, vec![0, 2]);
        assert_eq!(rows.len(), 3);
        assert_eq!(rows[2], (1, Line::from("cc")));
    }

    #[test]
    fn cursor_jumps_to_matches_and_moves_like_vim() {
        let lines: Vec<String> = (0..200).map(|i| format!("line {i}")).collect();
        let mut v = doc(lines, vec![50, 120], Some("https://a/b.htm"));
        let text = screen_text(&mut v, 40, 13);
        assert!(text.contains("Title"), "{text}");
        v.pending = Some(50);
        screen_text(&mut v, 40, 13);
        assert_eq!(v.cur.pos.row, 50, "first draw lands the cursor on the match");
        assert!(v.cur.visible().contains(&50));
        press(&mut v, KeyCode::Char('n'));
        assert_eq!(v.cur.pos.row, 120);
        press(&mut v, KeyCode::Char('n'));
        assert_eq!(v.cur.pos.row, 50, "wraps to the first match");
        press(&mut v, KeyCode::Char('N'));
        assert_eq!(v.cur.pos.row, 120, "previous wraps to the last");
        press(&mut v, KeyCode::Char('G'));
        assert_eq!((v.cur.pos.row, v.cur.top), (199, v.cur.max_top()));
        press(&mut v, KeyCode::Char('g'));
        press(&mut v, KeyCode::Char('g'));
        assert_eq!((v.cur.pos.row, v.cur.top), (0, 0));
        press(&mut v, KeyCode::Char('j'));
        press(&mut v, KeyCode::Char('j'));
        press(&mut v, KeyCode::Char('k'));
        assert_eq!(v.cur.pos.row, 1);
        v.on_key(KeyEvent::new(KeyCode::Char('d'), KeyModifiers::CONTROL));
        assert_eq!((v.cur.pos.row, v.cur.top), (6, 1), "half page down, view centred on the cursor");
        v.on_key(KeyEvent::new(KeyCode::Char('u'), KeyModifiers::CONTROL));
        assert_eq!((v.cur.pos.row, v.cur.top), (1, 0));
    }

    #[test]
    fn scroll_stays_within_the_document() {
        let mut v = doc(vec!["a".into(), "b".into()], vec![], None);
        screen_text(&mut v, 20, 10);
        press(&mut v, KeyCode::Char('k'));
        assert_eq!((v.cur.pos.row, v.cur.top), (0, 0));
        press(&mut v, KeyCode::Char('G'));
        assert_eq!((v.cur.pos.row, v.cur.top), (1, 0), "short doc fits, nothing to scroll");
    }

    #[test]
    fn visual_selection_yanks_and_feeds_leader_y() {
        let lines: Vec<String> = vec!["alpha beta".into(), "gamma delta".into()];
        let mut v = doc(lines, vec![], Some("https://a/b.htm"));
        screen_text(&mut v, 40, 10);
        press(&mut v, KeyCode::Char('V'));
        press(&mut v, KeyCode::Char('j'));
        let text = screen_text(&mut v, 40, 10);
        assert!(text.contains("-- VISUAL LINE --"), "{text}");
        assert_eq!(
            v.claude_context().as_deref(),
            Some("From Title (https://a/b.htm):\n```\nalpha beta\ngamma delta\n```\n")
        );
        assert_eq!(v.take_selection().as_deref(), Some("alpha beta\ngamma delta"));
        assert!(!v.cur.is_visual(), "<space>y ends visual mode");
        // y in visual yanks; y in normal still copies the url
        press(&mut v, KeyCode::Char('g'));
        press(&mut v, KeyCode::Char('g'));
        press(&mut v, KeyCode::Char('v'));
        press(&mut v, KeyCode::Char('e'));
        assert_eq!(press(&mut v, KeyCode::Char('y')), Action::Copy("alpha".into()));
        assert_eq!(press(&mut v, KeyCode::Char('y')), Action::Copy("https://a/b.htm".into()));
        // esc leaves visual mode instead of quitting
        press(&mut v, KeyCode::Char('v'));
        assert_eq!(press(&mut v, KeyCode::Esc), Action::None);
        assert_eq!(press(&mut v, KeyCode::Esc), Action::Quit);
    }

    #[test]
    fn keys_quit_and_open_or_copy_the_source() {
        let mut v = doc(vec!["a".into()], vec![], Some("https://a/b.htm"));
        assert_eq!(
            press(&mut v, KeyCode::Char('o')),
            Action::OpenBrowser("https://a/b.htm".into())
        );
        assert_eq!(
            press(&mut v, KeyCode::Char('y')),
            Action::Copy("https://a/b.htm".into())
        );
        assert_eq!(press(&mut v, KeyCode::Esc), Action::Quit);
        assert_eq!(press(&mut v, KeyCode::Char('q')), Action::Quit);

        let mut none = doc(vec!["a".into()], vec![], None);
        assert_eq!(press(&mut none, KeyCode::Char('o')), Action::None);
        assert_eq!(
            none.flash.as_ref().map(|f| f.0.as_str()),
            Some("no source url")
        );
    }

    #[test]
    fn loading_and_failed_states_render_and_still_quit() {
        let (_tx, rx) = mpsc::channel::<Result<Doc, String>>();
        let mut loading = Docview::with(
            "https://a/b.htm".into(),
            State::Loading,
            Some("https://a/b.htm".into()),
            Some(rx),
        );
        let text = screen_text(&mut loading, 60, 6);
        assert!(text.contains("loading source"), "{text}");
        assert!(loading.needs_redraw());
        assert_eq!(
            press(&mut loading, KeyCode::Char('o')),
            Action::OpenBrowser("https://a/b.htm".into())
        );
        assert_eq!(press(&mut loading, KeyCode::Char('q')), Action::Quit);

        let mut failed = Docview::with(
            "x".into(),
            State::Failed("boom: no network".into()),
            None,
            None,
        );
        let text = screen_text(&mut failed, 60, 6);
        assert!(text.contains("boom: no network"), "{text}");
        assert!(!failed.needs_redraw());
    }

    #[test]
    fn chunk_view_marks_the_hit() {
        let lines = vec![
            "MRVL — 10K / mda (10-K, 2026-03-11)".to_string(),
            "https://a/b.htm".into(),
            String::new(),
            MATCH_MARK.into(),
            "the hit text".into(),
        ];
        let mut v = doc(lines, vec![3], Some("https://a/b.htm"));
        let text = screen_text(&mut v, 60, 8);
        assert!(text.contains(MATCH_MARK), "{text}");
        assert!(text.contains("the hit text"), "{text}");
    }

    #[test]
    fn block_docs_lay_out_and_jump_between_headings() {
        let json = r#"{"blocks":[
            {"t":"h","level":1,"text":"Item 1. Business"},
            {"t":"p","spans":[{"s":"We make chips."}]},
            {"t":"h","level":3,"text":"Products"},
            {"t":"p","spans":[{"s":"GPUs and more."}]},
            {"t":"h","level":1,"text":"Item 1A. Risk Factors"},
            {"t":"li","marker":"•","spans":[{"s":"Supply is concentrated."}]}]}"#;
        let path = std::env::temp_dir().join(format!("fl_blocks_{}.json", std::process::id()));
        std::fs::write(&path, json).expect("write");
        let blocks = doc_blocks::load(path.to_str().expect("utf8")).expect("load");
        let _ = std::fs::remove_file(&path);
        let mut v = Docview::with(
            "label".into(),
            State::Ready(Doc {
                title: "NVDA 10-K".into(),
                matches: vec![3],
                jump: Some(3),
                blocks: Some(blocks),
                ..Doc::default()
            }),
            None,
            None,
        );
        v.pending = Some(3);
        let text = screen_text(&mut v, 60, 20);
        assert!(text.contains("We make chips."), "{text}");
        assert!(text.contains("▌"), "matched block gets the gutter bar: {text}");
        assert!(text.contains("• Supply is concentrated."), "{text}");
        screen_text(&mut v, 60, 5); // short view so there is room to scroll
        press(&mut v, KeyCode::Char('g'));
        press(&mut v, KeyCode::Char('g'));
        press(&mut v, KeyCode::Char(']'));
        press(&mut v, KeyCode::Char(']'));
        assert_eq!(v.cur.pos.row, v.starts[4], "]] jumps to the next Item");
        press(&mut v, KeyCode::Char('['));
        press(&mut v, KeyCode::Char('['));
        assert_eq!(v.cur.pos.row, v.starts[0]);
        press(&mut v, KeyCode::Char(']'));
        press(&mut v, KeyCode::Char('h'));
        assert_eq!(v.cur.pos.row, v.starts[2], "]h stops at the level-3 heading");
    }

    #[test]
    fn question_mark_shows_every_binding() {
        let mut v = doc(vec!["a".into()], vec![], None);
        press(&mut v, KeyCode::Char('?'));
        let text = screen_text(&mut v, 120, 40);
        for k in ["reader keys", "gh gl", "ip ap", "spc a c", "]] [[", "half page down"] {
            assert!(text.contains(k), "{k} missing:\n{text}");
        }
        // any key closes it without acting
        assert_eq!(press(&mut v, KeyCode::Char('q')), Action::None);
        assert!(!v.help);
        // short window: two columns, still everything
        press(&mut v, KeyCode::Char('?'));
        let text = screen_text(&mut v, 120, 24);
        assert!(text.contains("move") && text.contains("document"), "{text}");
    }
}
