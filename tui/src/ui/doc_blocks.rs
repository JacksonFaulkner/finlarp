// Typed filing blocks (py/sources/filing_blocks.py) laid out as styled lines
// for a reader: a centred prose column, headings by level, real bullets,
// financial tables as aligned grids, and boilerplate dimmed.
//
//   blocks.json ─ load() ─> Vec<Block> ─ layout(width) ─> rows of Line + the
//   first row of each block (for jumps: quote match, next heading).
//
// Design rules (Tufte / glamour): prose stays greyscale and ~80 columns wide;
// colour is for data (amounts, negatives) and structure (headings); tables
// have no vertical rules, only a header rule and subtotal/total rules.

use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use serde::Deserialize;
use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

use crate::ui::theme::Theme;

/// Widest prose column; wider terminals get side margins instead.
pub const MEASURE: usize = 84;
const GAP: usize = 2;

#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct TSpan {
    pub s: String,
    #[serde(default)]
    pub b: Option<u8>,
    #[serde(default)]
    pub i: Option<u8>,
    #[serde(default)]
    pub u: Option<u8>,
    #[serde(default)]
    pub x: Option<String>,
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct HCell {
    pub s: String,
    pub c: usize,
    #[serde(default = "one")]
    pub span: usize,
}

fn one() -> usize {
    1
}

#[derive(Debug, Clone, Deserialize, PartialEq, Default)]
pub struct Val {
    pub s: String,
    #[serde(default)]
    pub cur: Option<String>,
    #[serde(default)]
    pub neg: Option<u8>,
    #[serde(default)]
    pub x: Option<String>,
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct NumRow {
    #[serde(default)]
    pub label: String,
    #[serde(default)]
    pub v: Vec<Val>,
    #[serde(default)]
    pub indent: Option<u8>,
    #[serde(default)]
    pub b: Option<u8>,
    #[serde(default)]
    pub rule: Option<String>,
    #[serde(default)]
    pub rule_below: Option<String>,
    #[serde(default)]
    pub section: Option<u8>,
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
pub struct Table {
    pub kind: String,
    #[serde(default)]
    pub cols: usize,
    #[serde(default)]
    pub header: Vec<Vec<HCell>>,
    /// Num tables: [NumRow]; every other kind: [[cell text]].
    #[serde(default)]
    pub rows: serde_json::Value,
    #[serde(default)]
    pub units: Option<String>,
    #[serde(default)]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, PartialEq)]
#[serde(tag = "t")]
pub enum Block {
    #[serde(rename = "h")]
    H {
        level: u8,
        text: String,
        #[serde(default)]
        item: Option<String>,
    },
    #[serde(rename = "p")]
    P { spans: Vec<TSpan> },
    #[serde(rename = "li")]
    Li {
        spans: Vec<TSpan>,
        #[serde(default)]
        marker: String,
    },
    #[serde(rename = "table")]
    Table(Table),
    #[serde(rename = "img")]
    Img {
        #[serde(default)]
        src: String,
        #[serde(default)]
        alt: String,
    },
    #[serde(rename = "page")]
    Page {
        #[serde(default)]
        n: Option<String>,
    },
    #[serde(rename = "note")]
    Note { concept: String },
    #[serde(other)]
    Other,
}

#[derive(Deserialize)]
struct File {
    blocks: Vec<Block>,
}

/// Reads a blocks.json written by docview.py --blocks / filing_blocks.py.
pub fn load(path: &str) -> Result<Vec<Block>, String> {
    let bytes = std::fs::read(path).map_err(|e| format!("{path}: {e}"))?;
    let f: File = serde_json::from_slice(&bytes).map_err(|e| format!("{path}: {e}"))?;
    Ok(f.blocks)
}

/// Plain text of a block, for search (n/N) and tests.
pub fn block_text(b: &Block) -> String {
    match b {
        Block::H { text, .. } => text.clone(),
        Block::P { spans } | Block::Li { spans, .. } => spans.iter().map(|s| s.s.as_str()).collect(),
        Block::Table(t) => match num_rows(t) {
            Some(rows) => rows
                .iter()
                .map(|r| r.label.clone())
                .collect::<Vec<_>>()
                .join(" "),
            None => text_rows(t).concat().join(" "),
        },
        _ => String::new(),
    }
}

pub fn is_heading(b: &Block, max_level: u8) -> bool {
    matches!(b, Block::H { level, .. } if *level <= max_level)
}

fn num_rows(t: &Table) -> Option<Vec<NumRow>> {
    (t.kind == "num")
        .then(|| serde_json::from_value(t.rows.clone()).ok())
        .flatten()
}

fn text_rows(t: &Table) -> Vec<Vec<String>> {
    serde_json::from_value(t.rows.clone()).unwrap_or_default()
}

// --------------------------------------------------------------------------
// Styles
// --------------------------------------------------------------------------

struct Styles {
    body: Style,
    dim: Style,
    accent: Style,
    num: Style,
    neg: Style,
    band: Style,
}

impl Styles {
    fn new(th: &Theme) -> Self {
        let body = Style::default().fg(th.fg);
        Self {
            body,
            dim: Style::default().fg(th.dim),
            accent: Style::default().fg(th.accent),
            num: Style::default().fg(th.num),
            neg: Style::default().fg(th.down),
            band: Style::default()
                .fg(Color::Black)
                .bg(th.accent)
                .add_modifier(Modifier::BOLD),
        }
    }
}

// --------------------------------------------------------------------------
// Styled word wrap
// --------------------------------------------------------------------------

/// Words of a span list, each with its style; prose amounts ($1.2 million,
/// 12%, $(0.10)) pick up the number colour, negatives the down colour.
fn words(spans: &[TSpan], st: &Styles, base: Style) -> Vec<(String, Style)> {
    let mut out: Vec<(String, Style)> = Vec::new();
    let mut prev_num = false;
    let mut prev_color = st.num;
    for sp in spans {
        let mut style = base;
        if sp.b.is_some() {
            style = style.add_modifier(Modifier::BOLD);
        }
        if sp.i.is_some() {
            style = style.add_modifier(Modifier::ITALIC);
        }
        if sp.u.is_some() {
            style = style.add_modifier(Modifier::UNDERLINED);
        }
        // A space at a span edge separates words; glue otherwise.
        let mut first = !sp.s.starts_with(char::is_whitespace);
        for w in sp.s.split_whitespace() {
            let core = w.trim_end_matches([',', '.', ';', ':', ')']);
            let is_num = looks_amount(core) || sp.x.is_some() && core.chars().any(|c| c.is_ascii_digit());
            let is_scale = prev_num && matches!(core, "million" | "billion" | "thousand" | "trillion" | "percent");
            let ws = if is_num {
                let neg = core.contains('(') && core.chars().any(|c| c.is_ascii_digit()) || core.starts_with("-$");
                prev_color = if neg { st.neg } else { st.num };
                style.patch(prev_color)
            } else if is_scale {
                // "million" after "$(0.2)" takes the number's colour
                style.patch(prev_color)
            } else {
                style
            };
            prev_num = is_num || (is_scale && prev_num);
            if first && !out.is_empty() {
                // continue the previous word (e.g. "$" + "1.2" across spans)
                let last = out.last_mut().expect("non-empty");
                if last.1 == ws {
                    last.0.push_str(w);
                } else {
                    out.push((w.to_string(), ws));
                    // mark as glued with a zero-width join: handled by wrap via NO_SPACE
                    out.last_mut().expect("pushed").0.insert(0, NO_SPACE);
                }
            } else {
                out.push((w.to_string(), ws));
            }
            first = false;
        }
    }
    out
}

/// Prefix on a word that must not be preceded by a space.
const NO_SPACE: char = '\u{1}';

fn looks_amount(w: &str) -> bool {
    let w = w.trim_start_matches(['(', '“', '"']);
    let digits = w.chars().filter(|c| c.is_ascii_digit()).count();
    if digits == 0 {
        return false;
    }
    w.starts_with('$') || w.starts_with("-$") || w.ends_with('%') || w.starts_with("US$")
}

/// Greedy wrap of styled words into lines of `width`, the first prefixed by
/// `first` and the rest by `rest` (hanging indent for bullets).
fn wrap_words(
    words: &[(String, Style)],
    width: usize,
    first: Vec<Span<'static>>,
    rest: &str,
) -> Vec<Line<'static>> {
    let first_w: usize = first.iter().map(|s| s.content.width()).sum();
    let rest_w = rest.width();
    let mut lines = Vec::new();
    let mut cur: Vec<Span<'static>> = first;
    let mut cur_w = first_w;
    let mut start = true;
    let mut lead = first_w;
    for (word, style) in words {
        let (glue, word) = match word.strip_prefix(NO_SPACE) {
            Some(w) => (true, w),
            None => (false, word.as_str()),
        };
        let ww = word.width();
        let need = if start || glue { ww } else { ww + 1 };
        if !start && cur_w + need > width {
            lines.push(Line::from(std::mem::take(&mut cur)));
            cur.push(Span::raw(rest.to_string()));
            cur_w = rest_w;
            lead = rest_w;
            start = true;
        }
        if !start && !glue {
            cur.push(Span::raw(" "));
            cur_w += 1;
        }
        // hard-split words longer than a line
        let mut w = word.to_string();
        while cur_w + w.width() > width && width > lead + 1 {
            let room = width - cur_w;
            let cut = split_at_width(&w, room.max(1));
            cur.push(Span::styled(w[..cut].to_string(), *style));
            lines.push(Line::from(std::mem::take(&mut cur)));
            cur.push(Span::raw(rest.to_string()));
            cur_w = rest_w;
            lead = rest_w;
            w = w[cut..].to_string();
        }
        cur_w += w.width();
        cur.push(Span::styled(w, *style));
        start = false;
    }
    if !start || lines.is_empty() {
        lines.push(Line::from(cur));
    }
    lines
}

fn split_at_width(s: &str, width: usize) -> usize {
    let mut w = 0;
    for (i, c) in s.char_indices() {
        let cw = c.width().unwrap_or(0);
        if w + cw > width {
            return i.max(c.len_utf8().min(s.len()));
        }
        w += cw;
    }
    s.len()
}

fn plain_wrap(text: &str, width: usize) -> Vec<String> {
    textwrap::wrap(text, width.max(1))
        .into_iter()
        .map(|c| c.into_owned())
        .collect()
}

fn pad_left(line: Line<'static>, n: usize) -> Line<'static> {
    if n == 0 {
        return line;
    }
    let mut spans = vec![Span::raw(" ".repeat(n))];
    spans.extend(line.spans);
    Line::from(spans)
}

fn truncate(s: &str, width: usize) -> String {
    if s.width() <= width {
        return s.to_string();
    }
    let cut = split_at_width(s, width.saturating_sub(1));
    format!("{}…", &s[..cut])
}

// --------------------------------------------------------------------------
// A fixed-width row of styled cells (tables)
// --------------------------------------------------------------------------

struct Row {
    cells: Vec<(String, Style)>,
}

impl Row {
    fn new(width: usize) -> Self {
        Self {
            cells: vec![(" ".to_string(), Style::default()); width],
        }
    }

    fn put(&mut self, x: usize, s: &str, style: Style) {
        let mut x = x;
        for c in s.chars() {
            let cw = c.width().unwrap_or(0);
            if cw == 0 {
                continue;
            }
            if x + cw > self.cells.len() {
                break;
            }
            self.cells[x] = (c.to_string(), style);
            for k in 1..cw {
                self.cells[x + k] = (String::new(), style);
            }
            x += cw;
        }
    }

    fn put_right(&mut self, x: usize, width: usize, s: &str, style: Style) {
        let s = truncate(s, width);
        self.put(x + width - s.width(), &s, style);
    }

    fn put_center(&mut self, x: usize, width: usize, s: &str, style: Style) {
        let s = truncate(s, width);
        self.put(x + (width - s.width()) / 2, &s, style);
    }

    fn line(self) -> Line<'static> {
        let mut spans: Vec<Span<'static>> = Vec::new();
        let mut buf = String::new();
        let mut cur = Style::default();
        for (s, st) in self.cells {
            if st != cur && !buf.is_empty() {
                spans.push(Span::styled(std::mem::take(&mut buf), cur));
            }
            cur = st;
            buf.push_str(&s);
        }
        let trimmed = buf.trim_end().to_string();
        if !trimmed.is_empty() {
            spans.push(Span::styled(trimmed, cur));
        }
        Line::from(spans)
    }
}

// --------------------------------------------------------------------------
// Financial tables
// --------------------------------------------------------------------------

fn num_table(t: &Table, rows: &[NumRow], avail: usize, st: &Styles) -> Vec<Line<'static>> {
    let n = t.cols.max(rows.iter().map(|r| r.v.len()).max().unwrap_or(0));
    if n == 0 {
        return Vec::new();
    }
    // Value column widths: the widest value, and room for short header words.
    let mut vw = vec![4usize; n];
    for r in rows {
        for (i, v) in r.v.iter().enumerate().take(n) {
            let w = v.s.width() + if v.cur.is_some() { 2 } else { 0 };
            vw[i] = vw[i].max(w);
        }
    }
    for h in &t.header {
        for c in h.iter().filter(|c| c.c >= 1 && c.span == 1 && c.c <= n) {
            // Short headers ("February 27,") stay on one line; long ones wrap by word.
            let want = if c.s.width() <= 12 {
                c.s.width()
            } else {
                c.s.split_whitespace().map(|w| w.width()).max().unwrap_or(0).min(14)
            };
            vw[c.c - 1] = vw[c.c - 1].max(want);
        }
    }
    let label_need = rows
        .iter()
        .map(|r| r.label.width() + 2 * r.indent.unwrap_or(0) as usize + 1)
        .max()
        .unwrap_or(0)
        .clamp(10, 56);
    // Drop rightmost columns that can't fit next to a 16-wide label.
    let mut shown = n;
    let vals = |k: usize| vw[..k].iter().map(|w| w + GAP).sum::<usize>();
    while shown > 1 && 16.min(label_need) + vals(shown) > avail {
        shown -= 1;
    }
    let label_w = avail.saturating_sub(vals(shown)).clamp(8, label_need.max(8));
    let total = label_w + vals(shown);
    let col_x = |i: usize| label_w + vals(i) + GAP; // i: 0-based value column
    let mut out: Vec<Line<'static>> = Vec::new();

    if let Some(u) = &t.units {
        let mut r = Row::new(total);
        r.put_right(0, total, u, st.dim.add_modifier(Modifier::ITALIC));
        out.push(r.line());
    }

    // Header rows: a cell spanning every column with nothing else is a title.
    let hstyle = st.body.add_modifier(Modifier::BOLD);
    for h in &t.header {
        // A lone cell over every column is a table title when it's set in
        // caps or too wide to sit over the values ("CONSOLIDATED BALANCE SHEETS").
        let titles = h.len() == 1
            && h[0].c >= 1
            && h[0].span >= shown
            && (h[0].s.chars().filter(|c| c.is_alphabetic()).all(char::is_uppercase)
                || (h[0].s.starts_with('(') && h[0].s.ends_with(')'))
                || h[0].s.width() > total - label_w);
        if titles {
            let mut r = Row::new(total);
            r.put_center(0, total, &h[0].s, hstyle);
            out.push(r.line());
            continue;
        }
        let mut cells: Vec<(usize, usize, Vec<String>, Style, bool)> = Vec::new();
        for c in h {
            if c.c == 0 {
                cells.push((0, label_w.saturating_sub(1), plain_wrap(&c.s, label_w.saturating_sub(1)), st.dim, false));
                continue;
            }
            let first = c.c - 1;
            if first >= shown {
                continue;
            }
            let last = (first + c.span - 1).min(shown - 1);
            let x = col_x(first);
            let w = col_x(last) + vw[last] - x;
            cells.push((x, w, plain_wrap(&c.s, w), hstyle, c.span > 1));
        }
        let height = cells.iter().map(|c| c.2.len()).max().unwrap_or(0);
        for k in 0..height {
            let mut r = Row::new(total);
            for (x, w, lines, style, _) in &cells {
                // bottom-align so the last header line sits on the rule
                let off = height - lines.len();
                if k >= off {
                    if *x == 0 {
                        r.put(*x, &lines[k - off], *style);
                    } else {
                        r.put_center(*x, *w, &lines[k - off], *style);
                    }
                }
            }
            out.push(r.line());
        }
        if cells.iter().any(|c| c.4) {
            let mut r = Row::new(total);
            for (x, w, _, _, spans) in &cells {
                if *spans {
                    r.put(*x, &"─".repeat(*w), st.dim);
                }
            }
            out.push(r.line());
        }
    }
    let rule = |kind: &str| {
        let ch = if kind == "double" { "═" } else { "─" };
        let mut r = Row::new(total);
        for (i, w) in vw.iter().enumerate().take(shown) {
            r.put(col_x(i), &ch.repeat(*w), st.dim);
        }
        r.line()
    };
    if !t.header.is_empty() {
        out.push(rule("single"));
    }
    let mut last_rule = !t.header.is_empty();

    for row in rows {
        if let Some(kind) = &row.rule {
            if !last_rule {
                out.push(rule(kind));
            }
        }
        let indent = 2 * row.indent.unwrap_or(0) as usize;
        let lstyle = if row.section.is_some() || row.b.is_some() {
            st.body.add_modifier(Modifier::BOLD)
        } else {
            st.body
        };
        let label_lines = plain_wrap(&row.label, label_w.saturating_sub(indent + 1).max(4));
        for (k, text) in label_lines.iter().enumerate() {
            let mut r = Row::new(total);
            let hang = if k > 0 { 2 } else { 0 };
            r.put(indent + hang, text, lstyle);
            if k + 1 == label_lines.len() {
                for (i, v) in row.v.iter().enumerate().take(shown) {
                    if v.s.is_empty() {
                        continue;
                    }
                    let dash = v.s.chars().all(|c| matches!(c, '—' | '–' | '-'));
                    let mut vs = if v.neg.is_some() { st.neg } else { st.body };
                    if dash {
                        vs = st.dim;
                    }
                    if row.b.is_some() {
                        vs = vs.add_modifier(Modifier::BOLD);
                    }
                    if let Some(c) = &v.cur {
                        r.put(col_x(i), c, st.dim);
                    }
                    r.put_right(col_x(i), vw[i], &v.s, vs);
                }
            }
            out.push(r.line());
        }
        last_rule = false;
        if let Some(kind) = &row.rule_below {
            out.push(rule(kind));
            last_rule = true;
        }
    }
    for note in &t.notes {
        for l in plain_wrap(note, total.saturating_sub(2)) {
            out.push(Line::from(Span::styled(format!("  {l}"), st.dim)));
        }
    }
    if shown < n {
        out.push(Line::from(Span::styled(
            format!("  → {} more column(s): widen the window", n - shown),
            st.dim,
        )));
    }
    out
}

// --------------------------------------------------------------------------
// Text tables
// --------------------------------------------------------------------------

fn text_table(t: &Table, avail: usize, st: &Styles) -> Vec<Line<'static>> {
    let rows = text_rows(t);
    if rows.is_empty() {
        return Vec::new();
    }
    let base = match t.kind.as_str() {
        "signature" | "cover" => st.dim,
        _ => st.body,
    };
    if t.kind == "toc" {
        return toc(&rows, avail.min(MEASURE), st);
    }
    let n = rows.iter().map(Vec::len).max().unwrap_or(0);
    let mut w: Vec<usize> = (0..n)
        .map(|i| rows.iter().filter_map(|r| r.get(i)).map(|c| c.width()).max().unwrap_or(0).max(1))
        .collect();
    let budget = avail.saturating_sub(GAP * n.saturating_sub(1)).max(n);
    while w.iter().sum::<usize>() > budget {
        let (i, max) = w.iter().copied().enumerate().max_by_key(|(_, v)| *v).expect("n > 0");
        if max <= 8 {
            break;
        }
        w[i] -= 1;
    }
    let total = w.iter().sum::<usize>() + GAP * n.saturating_sub(1);
    let header = t.kind == "exhibits" || (rows.len() > 2 && rows[0].iter().all(|c| !c.is_empty() && c.width() < 30));
    let mut out = Vec::new();
    for (ri, r) in rows.iter().enumerate() {
        let cells: Vec<Vec<String>> = (0..n)
            .map(|i| plain_wrap(r.get(i).map(String::as_str).unwrap_or(""), w[i]))
            .collect();
        let h = cells.iter().map(Vec::len).max().unwrap_or(1);
        let style = if header && ri == 0 { base.add_modifier(Modifier::BOLD) } else { base };
        for k in 0..h {
            let mut row = Row::new(total);
            let mut x = 0;
            for (i, c) in cells.iter().enumerate() {
                if let Some(text) = c.get(k) {
                    let s = if text.contains('☒') || text.contains('☑') { st.accent } else { style };
                    row.put(x, text, s);
                }
                x += w[i] + GAP;
            }
            out.push(row.line());
        }
        if header && ri == 0 {
            out.push(Line::from(Span::styled("─".repeat(total), st.dim)));
        }
    }
    out
}

/// Table of contents: entry left, page number right, dot leaders between.
fn toc(rows: &[Vec<String>], width: usize, st: &Styles) -> Vec<Line<'static>> {
    let mut out = Vec::new();
    for r in rows {
        let cells: Vec<&str> = r.iter().map(String::as_str).filter(|c| !c.is_empty()).collect();
        if cells.is_empty() {
            continue;
        }
        let (label, page) = match cells.last() {
            Some(p) if cells.len() > 1 && p.width() <= 6 => (cells[..cells.len() - 1].join("  "), *p),
            _ => (cells.join("  "), ""),
        };
        let is_item = label.to_lowercase().starts_with("item") || label.to_lowercase().starts_with("part");
        let ls = if is_item { st.body } else { st.dim };
        let room = width.saturating_sub(page.width() + 2);
        let label = truncate(&label, room);
        let dots = width.saturating_sub(label.width() + page.width() + 2);
        out.push(Line::from(vec![
            Span::styled(label, ls),
            Span::styled(format!(" {} ", "·".repeat(dots)), st.dim),
            Span::styled(page.to_string(), st.dim),
        ]));
    }
    out
}

// --------------------------------------------------------------------------
// Document layout
// --------------------------------------------------------------------------

fn humanize_concept(c: &str) -> String {
    let name = c.rsplit(':').next().unwrap_or(c);
    let name = name
        .trim_end_matches("TextBlock")
        .trim_end_matches("Disclosure")
        .trim_end_matches("PolicyTextBlock");
    let mut out = String::new();
    for (i, ch) in name.chars().enumerate() {
        if i > 0 && ch.is_uppercase() {
            out.push(' ');
        }
        out.push(ch);
    }
    out
}

/// Rows for `blocks` at `width` columns: (block index, line), plus the first
/// row of each block.
pub fn layout(blocks: &[Block], width: usize, th: &Theme) -> (Vec<(usize, Line<'static>)>, Vec<usize>) {
    let st = Styles::new(th);
    let width = width.max(20);
    let measure = width.saturating_sub(4).min(MEASURE).max(16);
    let margin = (width - measure) / 2;
    let table_w = width.saturating_sub(4).max(measure);
    let table_margin = (width - table_w) / 2;
    let mut rows: Vec<(usize, Line<'static>)> = Vec::new();
    let mut starts = Vec::with_capacity(blocks.len());
    let mut prev: Option<&Block> = None;

    for (bi, b) in blocks.iter().enumerate() {
        let gap = match (prev, b) {
            (None, _) => 0,
            (_, Block::Page { .. }) | (_, Block::Note { .. }) | (_, Block::Other) => 0,
            (Some(Block::Li { .. }), Block::Li { .. }) => 0,
            (Some(Block::H { level, .. }), _) if *level == 3 || *level == 1 => 0,
            (Some(Block::H { level, .. }), Block::H { .. }) if *level >= 2 => 0,
            (_, Block::H { level, .. }) if *level <= 1 => 2,
            _ => 1,
        };
        for _ in 0..gap {
            rows.push((bi, Line::default()));
        }
        starts.push(rows.len());
        let mut lines: Vec<Line<'static>> = Vec::new();
        let mut pad = margin;
        match b {
            Block::H { level: 0, text, .. } => {
                let t = format!("  {}  ", text.to_uppercase());
                let side = measure.saturating_sub(t.width()) / 2;
                lines.push(Line::from(vec![
                    Span::styled("━".repeat(side), st.accent),
                    Span::styled(t, st.accent.add_modifier(Modifier::BOLD)),
                    Span::styled("━".repeat(side), st.accent),
                ]));
            }
            Block::H { level: 1, text, .. } => {
                for l in plain_wrap(text, measure.saturating_sub(2)) {
                    let fill = measure.saturating_sub(l.width() + 1);
                    lines.push(Line::from(Span::styled(format!(" {l}{}", " ".repeat(fill)), st.band)));
                }
                lines.push(Line::default());
            }
            Block::H { level: 2, text, .. } => {
                let s = st.accent.add_modifier(Modifier::BOLD);
                let wrapped = plain_wrap(text, measure);
                let w = wrapped.iter().map(|l| l.width()).max().unwrap_or(0);
                lines.extend(wrapped.into_iter().map(|l| Line::from(Span::styled(l, s))));
                lines.push(Line::from(Span::styled("─".repeat(w), st.dim)));
            }
            Block::H { text, .. } => {
                let s = st.body.add_modifier(Modifier::BOLD);
                lines.extend(plain_wrap(text, measure).into_iter().map(|l| Line::from(Span::styled(l, s))));
            }
            Block::P { spans } => {
                lines = wrap_words(&words(spans, &st, st.body), measure, Vec::new(), "");
            }
            Block::Li { spans, marker } => {
                let m = if marker.chars().count() == 1 && !marker.chars().all(char::is_alphanumeric) {
                    "•".to_string()
                } else {
                    marker.clone()
                };
                let lead = format!("  {m} ");
                let hang = " ".repeat(lead.width());
                lines = wrap_words(
                    &words(spans, &st, st.body),
                    measure,
                    vec![Span::raw("  "), Span::styled(m, st.accent), Span::raw(" ")],
                    &hang,
                );
            }
            Block::Table(t) => {
                lines = match num_rows(t) {
                    Some(r) => num_table(t, &r, table_w, &st),
                    None => text_table(t, table_w, &st),
                };
                // Tables sit centred under the prose column.
                let w = lines.iter().map(Line::width).max().unwrap_or(0);
                pad = if w <= measure { margin } else { (width.saturating_sub(w) / 2).max(table_margin) };
            }
            Block::Img { alt, src } => {
                let name = if alt.is_empty() { src.rsplit('/').next().unwrap_or(src) } else { alt };
                lines.push(Line::from(Span::styled(format!("▣ image · {name}"), st.dim)));
            }
            Block::Page { n } => {
                let label = n.as_deref().map(|n| format!("─ {n}")).unwrap_or_else(|| "─".into());
                let s = truncate(&label, measure);
                lines.push(Line::from(Span::styled(
                    format!("{}{s}", " ".repeat(measure.saturating_sub(s.width()))),
                    st.dim,
                )));
            }
            Block::Note { concept } => {
                lines.push(Line::from(Span::styled(
                    format!("◇ note · {}", humanize_concept(concept)),
                    st.dim.add_modifier(Modifier::ITALIC),
                )));
            }
            Block::Other => {}
        }
        rows.extend(lines.into_iter().map(|l| (bi, pad_left(l, pad))));
        prev = Some(b);
    }
    (rows, starts)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn text(rows: &[(usize, Line<'static>)]) -> Vec<String> {
        rows.iter()
            .map(|(_, l)| l.spans.iter().map(|s| s.content.as_ref()).collect::<String>())
            .collect()
    }

    fn parse(json: &str) -> Vec<Block> {
        serde_json::from_str::<File>(json).expect("json").blocks
    }

    #[test]
    fn deserializes_every_block_kind_and_ignores_unknown_ones() {
        let b = parse(
            r#"{"blocks":[
            {"t":"h","level":1,"text":"Item 7. MD&A","item":"7"},
            {"t":"p","spans":[{"s":"Revenue was "},{"s":"$1.2","x":"us-gaap:Revenues"},{"s":" billion."}]},
            {"t":"li","marker":"•","spans":[{"s":"one"}]},
            {"t":"table","kind":"num","cols":1,"header":[[{"s":"2025","c":1,"span":1}]],
             "rows":[{"label":"Revenue","v":[{"s":"1,200","cur":"$"}]}]},
            {"t":"table","kind":"text","rows":[["a","b"]]},
            {"t":"img","src":"x.jpg","alt":""},{"t":"page","n":"12"},
            {"t":"note","concept":"us-gaap:LeasesTextBlock"},{"t":"weird"}]}"#,
        );
        assert_eq!(b.len(), 9);
        assert!(matches!(b[0], Block::H { level: 1, .. }));
        assert_eq!(b[8], Block::Other);
        assert_eq!(block_text(&b[1]), "Revenue was $1.2 billion.");
    }

    #[test]
    fn prose_wraps_to_the_measure_and_centres() {
        let long = "word ".repeat(60);
        let b = parse(&format!(r#"{{"blocks":[{{"t":"p","spans":[{{"s":"{long}"}}]}}]}}"#));
        let (rows, starts) = layout(&b, 120, &Theme::default());
        assert_eq!(starts, vec![0]);
        let lines = text(&rows);
        let margin = (120 - MEASURE) / 2;
        assert!(lines.iter().all(|l| l.starts_with(&" ".repeat(margin))));
        assert!(lines.iter().all(|l| l.trim_end().width() <= margin + MEASURE));
    }

    #[test]
    fn amounts_in_prose_get_the_number_colour() {
        let th = Theme::default();
        let st = Styles::new(&th);
        let ws = words(
            &[TSpan { s: "Net loss was $(2.9) million, revenue $18.8 million.".into(), b: None, i: None, u: None, x: None }],
            &st,
            st.body,
        );
        let style_of = |w: &str| ws.iter().find(|(s, _)| s.starts_with(w)).map(|(_, s)| s.fg).flatten();
        assert_eq!(style_of("$(2.9)"), Some(th.down));
        assert_eq!(style_of("$18.8"), Some(th.num));
        assert_eq!(style_of("revenue"), Some(th.fg));
        assert_eq!(style_of("million,"), Some(th.down), "scale word follows a negative amount");
    }

    #[test]
    fn num_table_aligns_values_and_draws_rules() {
        let b = parse(
            r#"{"blocks":[{"t":"table","kind":"num","cols":2,"units":"in millions",
            "header":[[{"s":"Year Ended","c":1,"span":2}],[{"s":"2025","c":1,"span":1},{"s":"2024","c":2,"span":1}]],
            "rows":[{"label":"Revenue","v":[{"s":"1,200","cur":"$"},{"s":"900","cur":"$"}]},
                    {"label":"Cost","indent":1,"v":[{"s":"(300)","neg":1},{"s":"(250)","neg":1}]},
                    {"label":"Gross profit","b":1,"rule":"single","rule_below":"double","v":[{"s":"900"},{"s":"650"}]}]}]}"#,
        );
        let (rows, _) = layout(&b, 60, &Theme::default());
        let lines = text(&rows);
        let joined = lines.join("\n");
        assert!(joined.contains("in millions"), "{joined}");
        assert!(joined.contains("Year Ended"), "{joined}");
        assert!(joined.contains("═"), "{joined}");
        let rev = lines.iter().find(|l| l.contains("Revenue")).expect("revenue row");
        let gp = lines.iter().find(|l| l.contains("Gross profit")).unwrap_or_else(|| panic!("{joined}"));
        // values right-align: both rows end their first value at the same column
        let end = |l: &str, v: &str| l.find(v).map(|i| i + v.len());
        assert_eq!(end(rev, "1,200"), end(gp, "900 ").map(|e| e - 1));
        let cost = lines.iter().find(|l| l.contains("Cost")).expect("cost row");
        assert!(cost.trim_start().starts_with("Cost") && cost.find("Cost") > rev.find("Revenue"), "indented");
    }

    #[test]
    fn narrow_windows_drop_columns_with_a_note() {
        let vals: Vec<String> = (0..12).map(|i| format!(r#"{{"s":"{},000,000"}}"#, i + 1)).collect();
        let json = format!(
            r#"{{"blocks":[{{"t":"table","kind":"num","cols":12,"header":[],"rows":[{{"label":"Revenue","v":[{}]}}]}}]}}"#,
            vals.join(",")
        );
        let (rows, _) = layout(&parse(&json), 60, &Theme::default());
        let joined = text(&rows).join("\n");
        assert!(joined.contains("more column"), "{joined}");
        assert!(text(&rows).iter().all(|l| l.width() <= 60), "{joined}");
    }

    #[test]
    fn toc_uses_dot_leaders() {
        let b = parse(r#"{"blocks":[{"t":"table","kind":"toc","rows":[["Item 1.","Business","4"],["Item 1A.","Risk Factors","12"]]}]}"#);
        let (rows, _) = layout(&b, 80, &Theme::default());
        let lines = text(&rows);
        assert!(lines[0].contains("Item 1.  Business") && lines[0].contains("·") && lines[0].trim_end().ends_with('4'));
    }
}
