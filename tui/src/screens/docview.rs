// Standalone document viewer: the no-nvim counterpart of ui/docview.lua (and
// of ui/search.lua open_chunk). Search pushes it for alt-v / Enter when `fl`
// runs without nvim (search/mod.rs hand_off); inside nvim those keys still
// open the nvim viewer.
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
// Keys: j/k scroll, ^d/^u (space, PgDn/PgUp) page, g/G top/bottom, n/N next/
// previous match of the quote, o open in browser, y copy url, q/esc back.

use std::io;
use std::sync::mpsc::{self, Receiver, TryRecvError};
use std::thread;
use std::time::{Duration, Instant};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Paragraph, Wrap};
use serde::Deserialize;

use crate::app::{Action, Ctx, Screen};
use crate::model::Source;
use crate::pyrun;
use crate::ui::theme::Theme;

const FLASH_FOR: Duration = Duration::from_secs(2);
const DOCVIEW_PY: &str = "py/derive/docview.py";
const SEARCH_PY: &str = "py/derive/search.py";
/// Marks the hit inside a chunk's neighbourhood (same text as ui/search.lua).
const MATCH_MARK: &str = ">>> match";
const HINT: &str = "j/k scroll  ^d/^u page  g/G top/end  n/N match  o browser  y copy  q back";

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

/// Arg for a source document, with the quote as a `#:~:text=` fragment.
pub fn url_arg(url: &str, quote: Option<&str>) -> String {
    match quote.map(str::trim).filter(|q| !q.is_empty()) {
        Some(q) => format!("{url}#:~:text={}", encode(q)),
        None => url.to_string(),
    }
}

/// Arg for a search chunk by id.
pub fn chunk_arg(id: impl std::fmt::Display) -> String {
    format!("chunk:{id}")
}

/// Percent-encodes everything but unreserved ASCII (Source::quote decodes it).
fn encode(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for b in s.bytes() {
        if b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'~') {
            out.push(b as char);
        } else {
            out.push_str(&format!("%{b:02X}"));
        }
    }
    out
}

/// A loaded document: plain text lines plus where to look in them.
#[derive(Debug, Clone, Default)]
struct Doc {
    title: String,
    subtitle: String,
    /// Browser target for `o` and `y`.
    url: Option<String>,
    lines: Vec<String>,
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
    /// Top visual row.
    scroll: usize,
    /// Body height from the last draw.
    height: usize,
    /// Word-wrapped rows for `wrapped_at` columns: (logical line, text).
    rows: Vec<(usize, String)>,
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
            scroll: 0,
            height: 1,
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

    fn max_scroll(&self) -> usize {
        self.rows.len().saturating_sub(self.height)
    }

    fn scroll_by(&mut self, delta: isize) {
        let max = self.max_scroll() as isize;
        self.scroll = (self.scroll as isize + delta).clamp(0, max) as usize;
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

    /// Next (or previous) match whose first row lies past the view's centre,
    /// wrapping at the ends.
    fn jump_match(&mut self, forward: bool) {
        let State::Ready(doc) = &self.state else {
            return;
        };
        let anchor = self.scroll + self.height / 3;
        let rows: Vec<usize> = doc
            .matches
            .iter()
            .filter_map(|m| self.starts.get(*m).copied())
            .collect();
        let target = if forward {
            rows.iter()
                .copied()
                .find(|r| *r > anchor)
                .or(rows.first().copied())
        } else {
            rows.iter()
                .copied()
                .rev()
                .find(|r| *r < anchor)
                .or(rows.last().copied())
        };
        if let Some(row) = target {
            self.scroll = row.saturating_sub(self.height / 3).min(self.max_scroll());
        }
    }

    fn flash_msg(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
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
}

fn load_url(url: &str, quote: Option<&str>) -> Result<Doc, String> {
    let mut args = vec![url];
    if let Some(q) = quote {
        args.extend(["--quote", q]);
    }
    args.push("--json");
    let out = pyrun::run_script(DOCVIEW_PY, &args)?;
    let loc: Located = serde_json::from_str(&out).map_err(|e| format!("docview.py output: {e}"))?;

    let text = match loc.kind.as_str() {
        "md" | "text" => read_text(&loc.path),
        "pdf" => loc.text_path.as_deref().and_then(read_text),
        "image" => None,
        other => return Err(format!("no text viewer for {other} documents")),
    };
    let title = loc
        .title
        .filter(|t| !t.is_empty())
        .unwrap_or_else(|| url.to_string());
    let open_url = loc.index_url.or(loc.url).or_else(|| Some(url.to_string()));
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

/// The chunk with two neighbours either side, laid out like ui/search.lua
/// open_chunk: a header, the source url, then each chunk with the hit marked.
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

fn wrap_all(lines: &[String], width: usize) -> (Vec<(usize, String)>, Vec<usize>) {
    let mut rows = Vec::new();
    let mut starts = Vec::with_capacity(lines.len());
    for (i, line) in lines.iter().enumerate() {
        starts.push(rows.len());
        rows.extend(wrap(line, width).into_iter().map(|r| (i, r)));
    }
    (rows, starts)
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
        self.height = body.height.max(1) as usize;

        if let State::Ready(doc) = &self.state {
            if self.wrapped_at != width {
                (self.rows, self.starts) = wrap_all(&doc.lines, width);
                self.wrapped_at = width;
            }
            if let Some(line) = self.pending.take() {
                let row = self.starts.get(line).copied().unwrap_or(0);
                self.scroll = row.saturating_sub(self.height / 3);
            }
        }
        self.scroll = self.scroll.min(self.max_scroll());

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
                let end = (self.scroll + self.height).min(self.rows.len());
                let visible: Vec<Line> = self.rows[self.scroll.min(end)..end]
                    .iter()
                    .map(|(line, text)| {
                        if doc.matches.binary_search(line).is_ok() {
                            Line::from(Span::styled(text.clone(), accent))
                        } else {
                            Line::from(text.clone())
                        }
                    })
                    .collect();
                frame.render_widget(Paragraph::new(visible), body);
            }
        }

        let footer = match &self.flash {
            Some((msg, _)) => msg.clone(),
            None if self.is_ready() => {
                let total = self.rows.len();
                let pos = if total <= self.height {
                    "all".to_string()
                } else {
                    format!("{}%", self.scroll * 100 / (total - self.height).max(1))
                };
                format!("{HINT}  {pos}")
            }
            None => HINT.to_string(),
        };
        frame.render_widget(Paragraph::new(Span::styled(footer, dim)), foot);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let page = (self.height / 2).max(1) as isize;
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => return Action::Quit,
            KeyCode::Char('o') => return self.open_browser(),
            KeyCode::Char('y') => return self.copy_url(),
            _ if !self.is_ready() => {}
            KeyCode::Char('j') | KeyCode::Down => self.scroll_by(1),
            KeyCode::Char('k') | KeyCode::Up => self.scroll_by(-1),
            KeyCode::Char('d') if ctrl => self.scroll_by(page),
            KeyCode::Char('u') if ctrl => self.scroll_by(-page),
            KeyCode::Char(' ') | KeyCode::PageDown => self.scroll_by(page * 2),
            KeyCode::PageUp => self.scroll_by(-page * 2),
            KeyCode::Char('g') | KeyCode::Home => self.scroll = 0,
            KeyCode::Char('G') | KeyCode::End => self.scroll = self.max_scroll(),
            KeyCode::Char('n') => self.jump_match(true),
            KeyCode::Char('N') => self.jump_match(false),
            _ => {}
        }
        Action::None
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
    fn url_arg_round_trips_awkward_quotes() {
        for q in ["Revenue, up 50% & $2,739", "café — “quoted” a+b", "x"] {
            let arg = url_arg("https://a/b.htm", Some(q));
            assert_eq!(
                parse_arg(&arg),
                Some(Target::Url {
                    url: "https://a/b.htm".into(),
                    quote: Some(q.into())
                }),
                "{arg}"
            );
        }
        assert_eq!(url_arg("https://a", Some("  ")), "https://a");
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
        assert_eq!(rows[2], (1, "cc".to_string()));
    }

    #[test]
    fn centres_first_match_and_steps_through_matches() {
        let lines: Vec<String> = (0..200).map(|i| format!("line {i}")).collect();
        let mut v = doc(lines, vec![50, 120], Some("https://a/b.htm"));
        let text = screen_text(&mut v, 40, 13);
        assert!(text.contains("Title"), "{text}");
        // first draw applied the jump: the match row is within the view
        v.pending = Some(50);
        screen_text(&mut v, 40, 13);
        assert_eq!(v.scroll, 50 - 10 / 3);
        press(&mut v, KeyCode::Char('n'));
        assert_eq!(v.scroll, 120 - 10 / 3);
        press(&mut v, KeyCode::Char('n'));
        assert_eq!(v.scroll, 50 - 10 / 3, "wraps to the first match");
        press(&mut v, KeyCode::Char('N'));
        assert_eq!(v.scroll, 120 - 10 / 3, "previous wraps to the last");
        press(&mut v, KeyCode::Char('G'));
        assert_eq!(v.scroll, v.max_scroll());
        press(&mut v, KeyCode::Char('g'));
        assert_eq!(v.scroll, 0);
        press(&mut v, KeyCode::Char('j'));
        press(&mut v, KeyCode::Char('j'));
        assert_eq!(v.scroll, 2);
        press(&mut v, KeyCode::Char('k'));
        assert_eq!(v.scroll, 1);
        v.on_key(KeyEvent::new(KeyCode::Char('d'), KeyModifiers::CONTROL));
        assert_eq!(v.scroll, 6);
        v.on_key(KeyEvent::new(KeyCode::Char('u'), KeyModifiers::CONTROL));
        assert_eq!(v.scroll, 1);
    }

    #[test]
    fn scroll_stays_within_the_document() {
        let mut v = doc(vec!["a".into(), "b".into()], vec![], None);
        screen_text(&mut v, 20, 10);
        press(&mut v, KeyCode::Char('k'));
        assert_eq!(v.scroll, 0);
        press(&mut v, KeyCode::Char('G'));
        assert_eq!(v.scroll, 0, "short doc fits, nothing to scroll");
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
}
