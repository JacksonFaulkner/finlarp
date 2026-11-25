//! 10-K / 20-F / 10-Q HTML -> the typed block list the reader lays out: a Rust
//! port of py/sources/filing_blocks.py `document()` (PARSER_VERSION 2) that
//! produces the same JSON, so docview can parse a cached filing in-process
//! instead of starting Python. `tools/filing_blocks_parity.py` diffs the two
//! on every cached filing (via `fl filing-blocks FILE URL`); change both together.

pub mod cached;
mod entities;
pub mod html;

use std::collections::{BTreeSet, HashMap};
use std::sync::LazyLock;

use regex::Regex;
use serde_json::{Map, Value, json};

use html::{Attrs, Sink, py_pat, py_ws};

pub const PARSER_VERSION: u64 = 2;

fn re(p: &str) -> Regex {
    Regex::new(&py_pat(p)).expect("regex")
}

macro_rules! rx {
    ($name:ident, $p:expr) => {
        static $name: LazyLock<Regex> = LazyLock::new(|| re($p));
    };
}

rx!(BOLD, r"(?i)font-weight\s*:\s*(bold|bolder|[6-9]00)");
rx!(ITAL, r"(?i)font-style\s*:\s*italic");
rx!(UNDER, r"(?i)text-decoration[^;]*underline");
rx!(HIDDEN, r"(?i)display\s*:\s*none");
rx!(PB_BEFORE, r"(?i)(page-)?break-before\s*:\s*(always|page)");
rx!(PB_AFTER, r"(?i)(page-)?break-after\s*:\s*(always|page)");
rx!(
    INDENT,
    r"(?i)(padding-left|margin-left|text-indent)\s*:\s*(-?[\d.]+)\s*(pt|px|em|in|%)?"
);
rx!(FSIZE, r"(?i)font-size\s*:\s*([\d.]+)\s*(pt|px)?");
rx!(BORDER, r#"(?i)border-(top|bottom)(-style)?\s*:\s*([^;"]*)"#);
rx!(RULE_ZERO, r"\b0(px|pt)?\b");
rx!(RULE_LINE, r"solid|dotted|dashed|\dpx|\dpt");
rx!(
    NUM,
    r"^\(?\s*[$€£¥]?\s*\(?\s*-?[\d,]*\.?\d+\s*\)?\s*%?\s*\)?$"
);
rx!(DASH, r"^[—–-]+$");
rx!(
    ITEM,
    r"(?i)^\s*item\s+(\d{1,2}[a-d]?|\d\.[a-z])\b[\s.:\-–—]*(.*)$"
);
rx!(PART, r"(?i)^\s*part\s+([ivx]+)\b");
rx!(
    PAGE_NO,
    r"(?i)^(?:page\s+)?(?:[A-Z]-)?\d{1,3}$|^[ivxlc]{1,6}$|^-\s*\d+\s*-$"
);
rx!(
    UNITS,
    r"(?i)\(?\s*((?:[\w$]+\s+){0,3}in\s+(?:millions|thousands|billions)\b[^)]*?)\s*\)?$"
);
rx!(PAGE_OF, r"(?i)^page \d+ of \d+$");
rx!(SGML_STUB, r"(?i)^EX-\d+(\.\d+)?\s+\d+\s+\S+\.html?\b");
rx!(FOOTNOTE, r"^(\(\d{1,2}\)|\(\w\)|\*{1,3}|\d{1,2}\)|[†‡§])\s");
rx!(MARKER, r"^\(?\w{1,2}[.)]$");
rx!(EXHIBIT_NO, r"^\d{1,3}(\.\d{1,3})+[a-z*]?$");
rx!(EXHIBIT, r"(?i)exhibit");
rx!(YEARISH, r"^(19|20)\d\d$");
rx!(TOC_PAGE, r"^(?:[A-Z]?-?\d{1,3})$");

const BLOCK: &[&str] = &[
    "p",
    "div",
    "br",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "section",
    "article",
    "header",
    "footer",
    "blockquote",
    "hr",
    "pre",
    "center",
    "dt",
    "dd",
    "title",
    "table",
    "tr",
];
const VOID: &[&str] = &[
    "br", "hr", "img", "input", "meta", "link", "col", "area", "base", "wbr", "param", "source",
];
const SKIP: &[&str] = &["script", "style", "ix:header", "head", "title"];
const SYMBOL: &[&str] = &["$", "%", ")", "(", "€", "£", "¥", "%)"];
const BULLETS: &str = "•●▪◦·‣∙○■□➢➤►-–—";

// ---------------------------------------------------------------------------
// Python string helpers
// ---------------------------------------------------------------------------

fn strip(s: &str) -> &str {
    s.trim_matches(py_ws)
}

fn nchars(s: &str) -> usize {
    s.chars().count()
}

fn first(s: &str) -> Option<char> {
    s.chars().next()
}

/// `str.isupper()`: some cased char, none lowercase.
fn isupper(s: &str) -> bool {
    let mut cased = false;
    for c in s.chars() {
        if c.is_lowercase() {
            return false;
        }
        cased |= c.is_uppercase();
    }
    cased
}

fn split_join(s: &str) -> String {
    s.split(py_ws)
        .filter(|w| !w.is_empty())
        .collect::<Vec<_>>()
        .join(" ")
}

/// `_clean`.
fn clean(s: &str) -> String {
    split_join(&s.replace('\u{a0}', " ").replace('\u{200b}', ""))
}

/// `re.sub(r"\s+", " ", s)`.
fn collapse_ws(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    let mut in_ws = false;
    for c in s.chars() {
        if py_ws(c) {
            if !in_ws {
                out.push(' ');
            }
            in_ws = true;
        } else {
            out.push(c);
            in_ws = false;
        }
    }
    out
}

fn py_float(s: &str) -> Result<f64, String> {
    s.parse::<f64>()
        .map_err(|_| format!("could not convert string to float: {s:?}"))
}

/// Python `round()` of a float: ties to even.
fn py_round(v: f64) -> i64 {
    v.round_ties_even() as i64
}

// ---------------------------------------------------------------------------
// Spans
// ---------------------------------------------------------------------------

#[derive(Clone, Debug, Default)]
struct Span {
    s: String,
    b: bool,
    i: bool,
    u: bool,
    x: Option<String>,
}

impl Span {
    fn plain(s: &str) -> Self {
        Span {
            s: s.into(),
            ..Default::default()
        }
    }
    fn same_style(&self, o: &Span) -> bool {
        self.b == o.b && self.i == o.i && self.u == o.u && self.x == o.x
    }
    fn json(&self) -> Value {
        let mut m = Map::new();
        m.insert("s".into(), json!(self.s));
        if self.b {
            m.insert("b".into(), json!(1));
        }
        if self.i {
            m.insert("i".into(), json!(1));
        }
        if self.u {
            m.insert("u".into(), json!(1));
        }
        if let Some(x) = &self.x {
            m.insert("x".into(), json!(x));
        }
        Value::Object(m)
    }
}

fn spans_json(spans: &[Span]) -> Value {
    Value::Array(spans.iter().map(Span::json).collect())
}

fn text(spans: &[Span]) -> String {
    spans.iter().map(|s| s.s.as_str()).collect()
}

fn tidy(spans: &[Span]) -> Vec<Span> {
    let mut out: Vec<Span> = Vec::new();
    for sp in spans {
        let mut s = collapse_ws(&sp.s.replace('\u{200b}', ""));
        if s.is_empty() {
            continue;
        }
        if out.last().is_some_and(|l| l.s.ends_with(' ')) && s.starts_with(' ') {
            s.remove(0);
        }
        if s.is_empty() {
            continue;
        }
        match out.last_mut() {
            Some(l) if l.same_style(sp) => l.s.push_str(&s),
            _ => out.push(Span { s, ..sp.clone() }),
        }
    }
    if let Some(f) = out.first_mut() {
        f.s = f.s.trim_start_matches(py_ws).to_string();
    }
    if let Some(l) = out.last_mut() {
        l.s = l.s.trim_end_matches(py_ws).to_string();
    }
    out.retain(|s| !s.s.is_empty());
    out
}

fn share(spans: &[Span], flag: fn(&Span) -> bool) -> f64 {
    let total: usize = spans.iter().map(|s| nchars(strip(&s.s))).sum();
    let total = if total == 0 { 1 } else { total };
    let hit: usize = spans
        .iter()
        .filter(|s| flag(s))
        .map(|s| nchars(strip(&s.s)))
        .sum();
    hit as f64 / total as f64
}

fn bold(s: &Span) -> bool {
    s.b
}
fn ital(s: &Span) -> bool {
    s.i
}

fn para(spans: Vec<Span>, size: f64) -> Value {
    let t = text(&spans);
    let len = nchars(&t);
    let mut cs = t.chars();
    let c0 = cs.next();
    let c1 = cs.next();
    if c0.is_some_and(|c| BULLETS.contains(c)) && len > 2 && matches!(c1, Some(' ' | '\t')) {
        let mut head = spans[0].clone();
        head.s = head.s.chars().skip(1).collect();
        let mut v = vec![head];
        v.extend_from_slice(&spans[1..]);
        let rest = tidy(&v);
        return json!({"t": "li", "marker": c0.unwrap().to_string(), "spans": spans_json(&rest)});
    }
    if len <= 200 && !t.ends_with([',', ';']) {
        if PART.is_match(&t) && len < 60 {
            return json!({"t": "h", "level": 0, "text": t});
        }
        if let Some(m) = ITEM.captures(&t)
            && len < 180
            && (share(&spans, bold) > 0.5 || isupper(&t) || len < 100)
        {
            return json!({"t": "h", "level": 1, "text": t, "item": m[1].to_uppercase()});
        }
        if share(&spans, bold) > 0.9 && len < 160 {
            let level = if isupper(&t) || size >= 11.0 { 2 } else { 3 };
            return json!({"t": "h", "level": level, "text": t});
        }
        if share(&spans, ital) > 0.9 && len < 120 && !t.ends_with('.') {
            return json!({"t": "h", "level": 3, "text": t, "italic": 1});
        }
    }
    json!({"t": "p", "spans": spans_json(&spans)})
}

// ---------------------------------------------------------------------------
// Parser
// ---------------------------------------------------------------------------

type Rule = Option<&'static str>;

#[derive(Clone)]
struct Frame {
    tag: String,
    b: bool,
    i: bool,
    u: bool,
    hidden: bool,
    x: Option<String>,
    indent: f64,
    size: f64,
    pb_after: bool,
    rule_top: Rule,
    rule_bot: Rule,
    note: Option<String>,
}

#[derive(Clone)]
struct Cell {
    spans: Vec<Span>,
    span: usize,
    indent: f64,
    top: Rule,
    bot: Rule,
}

struct Row {
    cells: Vec<Cell>,
    top: Rule,
    bot: Rule,
}

fn pt(val: &str, unit: Option<&str>) -> Result<f64, String> {
    let v = py_float(val)?;
    Ok(match unit.unwrap_or("pt").to_lowercase().as_str() {
        "px" => v * 0.75,
        "em" => v * 10.0,
        "in" => v * 72.0,
        "%" => v * 0.5,
        _ => v,
    })
}

fn rule(style: &str) -> (Rule, Rule) {
    let (mut top, mut bot) = (None, None);
    for c in BORDER.captures_iter(style) {
        let val = c[3].to_lowercase();
        if val.contains("none")
            || val.contains("hidden")
            || RULE_ZERO.is_match(&val) && !val.contains("solid")
        {
            continue;
        }
        let kind = if val.contains("double") {
            "double"
        } else if RULE_LINE.is_match(&val) {
            "single"
        } else {
            continue;
        };
        if c[1].to_lowercase() == "top" {
            top = Some(kind);
        } else {
            bot = Some(kind);
        }
    }
    (top, bot)
}

fn attr<'a>(attrs: &'a Attrs, k: &str) -> Option<&'a str> {
    attrs
        .iter()
        .rev()
        .find(|(n, _)| n == k)
        .and_then(|(_, v)| v.as_deref())
}

#[derive(Default)]
struct Parser {
    base: String,
    blocks: Vec<Value>,
    stack: Vec<Frame>,
    skip: usize,
    spans: Vec<Span>,
    para_size: f64,
    /// open tables; nested ones flatten into the outer cell
    tables: Vec<Vec<Row>>,
    cell: Option<Cell>,
    row: Option<Row>,
}

impl Parser {
    fn push(&mut self, tag: &str, attrs: &Attrs) -> Result<Frame, String> {
        let style = attr(attrs, "style").unwrap_or("");
        let name = attr(attrs, "name").unwrap_or("");
        let par = self.stack.last();
        let mut x = par.and_then(|p| p.x.clone());
        let mut note = None;
        if tag == "ix:nonfraction" {
            x = Some(name.to_string());
        } else if tag == "ix:nonnumeric" && name.ends_with("TextBlock") {
            note = Some(name.to_string());
        }
        // the regexes are case-insensitive: a lowercase substring test skips most of them
        let low = style.to_ascii_lowercase();
        let has = |k: &str| low.contains(k);
        let mut ind = 0.0;
        let indents = if has("left") || has("indent") {
            INDENT.captures_iter(style).collect()
        } else {
            Vec::new()
        };
        for c in indents {
            let keep = c[1].to_lowercase() != "text-indent" || py_float(&c[2])? > 0.0;
            if keep {
                ind += pt(&c[2], c.get(3).map(|m| m.as_str()))?;
            }
        }
        let size = match has("font-size").then(|| FSIZE.captures(style)).flatten() {
            Some(c) => pt(&c[1], c.get(2).map(|m| m.as_str()))?,
            None => par.map_or(0.0, |p| p.size),
        };
        let (rule_top, rule_bot) = if has("border-") {
            rule(style)
        } else {
            (None, None)
        };
        let f = Frame {
            tag: tag.to_string(),
            b: par.is_some_and(|p| p.b)
                || matches!(tag, "b" | "strong")
                || has("font-weight") && BOLD.is_match(style),
            i: par.is_some_and(|p| p.i)
                || matches!(tag, "i" | "em")
                || has("italic") && ITAL.is_match(style),
            u: par.is_some_and(|p| p.u) || tag == "u" || has("underline") && UNDER.is_match(style),
            hidden: par.is_some_and(|p| p.hidden) || has("none") && HIDDEN.is_match(style),
            x: x.filter(|s| !s.is_empty()),
            indent: par.map_or(0.0, |p| p.indent) + ind,
            size,
            pb_after: has("break-after") && PB_AFTER.is_match(style),
            rule_top,
            rule_bot,
            note: note.filter(|s| !s.is_empty()),
        };
        if has("break-before") && PB_BEFORE.is_match(style) && self.tables.is_empty() {
            self.flush();
            self.page();
        }
        Ok(f)
    }

    fn emit_text(&mut self, t: &str) {
        let f = self.stack.last();
        let span = Span {
            s: t.to_string(),
            b: f.is_some_and(|f| f.b),
            i: f.is_some_and(|f| f.i),
            u: f.is_some_and(|f| f.u),
            x: f.and_then(|f| f.x.clone()),
        };
        let size = f.map(|f| f.size);
        let target = match self.cell.as_mut() {
            Some(c) => &mut c.spans,
            None => &mut self.spans,
        };
        match target.last_mut() {
            Some(l) if l.same_style(&span) => l.s.push_str(t),
            _ => target.push(span),
        }
        if self.cell.is_none()
            && self.para_size == 0.0
            && let Some(sz) = size
        {
            self.para_size = sz;
        }
    }

    fn flush(&mut self) {
        let spans = tidy(&std::mem::take(&mut self.spans));
        let size = std::mem::take(&mut self.para_size);
        if !spans.is_empty() {
            self.blocks.push(para(spans, size));
        }
    }

    fn page(&mut self) {
        let mut n: Option<String> = None;
        // the printed page number is the last short numeric line before the break
        if let Some(last) = self.blocks.last()
            && last["t"] == "p"
        {
            let txt = block_text_spans(last);
            if PAGE_NO.is_match(&txt) {
                n = Some(txt);
                self.blocks.pop();
            }
        }
        if let Some(last) = self.blocks.last_mut()
            && last["t"] == "page"
        {
            if let Some(n) = n
                && !truthy(last.get("n"))
            {
                last["n"] = json!(n);
            }
            return;
        }
        let mut b = json!({"t": "page"});
        if let Some(n) = n {
            b["n"] = json!(n);
        }
        self.blocks.push(b);
    }

    fn cell_text_blank(&self) -> bool {
        self.cell
            .as_ref()
            .is_some_and(|c| strip(&text(&c.spans)).is_empty())
    }
}

fn truthy(v: Option<&Value>) -> bool {
    match v {
        None | Some(Value::Null) => false,
        Some(Value::String(s)) => !s.is_empty(),
        Some(Value::Bool(b)) => *b,
        Some(Value::Number(n)) => n.as_f64() != Some(0.0),
        Some(Value::Array(a)) => !a.is_empty(),
        Some(Value::Object(o)) => !o.is_empty(),
    }
}

fn block_text_spans(b: &Value) -> String {
    b["spans"]
        .as_array()
        .map(|a| a.iter().filter_map(|s| s["s"].as_str()).collect())
        .unwrap_or_default()
}

impl Sink for Parser {
    fn start(&mut self, tag: &str, attrs: &Attrs) -> Result<(), String> {
        if SKIP.contains(&tag) {
            self.skip += 1;
            return Ok(());
        }
        if self.skip > 0 {
            return Ok(());
        }
        let f = self.push(tag, attrs)?;
        if let Some(note) = &f.note
            && !f.hidden
            && self.tables.is_empty()
        {
            self.flush();
            self.blocks.push(json!({"t": "note", "concept": note}));
        }
        if tag == "img" && !f.hidden {
            let src = attr(attrs, "src").unwrap_or("");
            if !src.is_empty() && !src.starts_with("data:") {
                let full = if src.contains("://") {
                    src.to_string()
                } else {
                    format!("{}{src}", self.base)
                };
                if !self.tables.is_empty() && self.cell.is_some() {
                    // a cell's image is kept on the cell, which the output never shows
                } else {
                    self.flush();
                    let alt = attr(attrs, "alt").unwrap_or("");
                    self.blocks
                        .push(json!({"t": "img", "src": full, "alt": alt}));
                }
            }
        }
        let one = self.tables.len() == 1;
        if tag == "table" {
            if self.tables.is_empty() {
                self.flush();
            }
            self.tables.push(Vec::new());
        } else if tag == "tr" && one {
            self.row = Some(Row {
                cells: Vec::new(),
                top: f.rule_top,
                bot: f.rule_bot,
            });
        } else if matches!(tag, "td" | "th") && one && self.row.is_some() {
            let span = attr(attrs, "colspan")
                .filter(|s| !s.is_empty())
                .unwrap_or("1");
            let span = if !span.is_empty() && span.chars().all(|c| c.is_ascii_digit()) {
                span.parse::<usize>().unwrap_or(usize::MAX).max(1)
            } else {
                1
            };
            self.cell = Some(Cell {
                spans: Vec::new(),
                span,
                indent: f.indent,
                top: f.rule_top,
                bot: f.rule_bot,
            });
        } else if self.cell.as_ref().is_some_and(|c| !c.spans.is_empty()) && BLOCK.contains(&tag) {
            let blank = {
                let c = self.cell.as_mut().unwrap();
                c.spans.push(Span::plain(" "));
                strip(&text(&c.spans)).is_empty()
            };
            let c = self.cell.as_mut().unwrap();
            if f.indent > c.indent && blank {
                c.indent = f.indent;
            }
        } else if self.cell.is_some() {
            // indent / rules often live on a div inside the td
            let blank = self.cell_text_blank();
            let c = self.cell.as_mut().unwrap();
            if f.indent > c.indent && blank {
                c.indent = f.indent;
            }
            c.top = c.top.or(f.rule_top);
            c.bot = c.bot.or(f.rule_bot);
        } else if BLOCK.contains(&tag) && self.tables.is_empty() {
            self.flush();
        }
        if VOID.contains(&tag) {
            if f.pb_after && self.tables.is_empty() {
                self.flush();
                self.page();
            }
            return Ok(());
        }
        self.stack.push(f);
        Ok(())
    }

    fn startend(&mut self, tag: &str, attrs: &Attrs) -> Result<(), String> {
        // XHTML <td /> or <div />: open and close it, so spacer cells keep their column
        self.start(tag, attrs)?;
        if !VOID.contains(&tag) {
            self.end(tag);
        }
        Ok(())
    }

    fn end(&mut self, tag: &str) {
        if SKIP.contains(&tag) {
            self.skip = self.skip.saturating_sub(1);
            return;
        }
        if self.skip > 0 || VOID.contains(&tag) {
            return;
        }
        let Some(idx) = self.stack.iter().rposition(|f| f.tag == tag) else {
            return;
        };
        let frames = self.stack.split_off(idx);
        let one = self.tables.len() == 1;
        if matches!(tag, "td" | "th") && self.cell.is_some() && one {
            let mut c = self.cell.take().unwrap();
            c.spans = tidy(&c.spans);
            if let Some(r) = self.row.as_mut() {
                r.cells.push(c);
            }
        } else if tag == "tr" && self.row.is_some() && one {
            let r = self.row.take().unwrap();
            self.tables.last_mut().unwrap().push(r);
        } else if tag == "table" && !self.tables.is_empty() {
            let t = self.tables.pop().unwrap();
            if self.tables.is_empty() {
                self.cell = None;
                self.row = None;
                self.blocks.extend(table_blocks(&t));
            }
        } else if BLOCK.contains(&tag) && self.tables.is_empty() {
            self.flush();
        }
        if frames.iter().any(|f| f.pb_after) && self.tables.is_empty() {
            self.flush();
            self.page();
        }
    }

    fn data(&mut self, d: &str) {
        if self.skip > 0 || d.is_empty() {
            return;
        }
        if self.stack.last().is_some_and(|f| f.hidden) {
            return;
        }
        if !self.tables.is_empty() && self.cell.is_none() {
            return; // whitespace between cells
        }
        self.emit_text(&d.replace('\u{a0}', " "));
    }
}

// ---------------------------------------------------------------------------
// Tables
// ---------------------------------------------------------------------------

fn cell_text(c: &Cell) -> String {
    clean(&text(&c.spans))
}

fn is_value(s: &str) -> bool {
    (NUM.is_match(s) || DASH.is_match(s)) && !SYMBOL.contains(&s)
}

/// Each row as [(start_col, end_col, cell)] with colspans expanded.
fn grid<'a>(rows: &[&'a Row]) -> Vec<Vec<(usize, usize, &'a Cell)>> {
    rows.iter()
        .map(|r| {
            let mut col = 0usize;
            r.cells
                .iter()
                .map(|c| {
                    let e = col.saturating_add(c.span) - 1;
                    let out = (col, e, c);
                    col = col.saturating_add(c.span);
                    out
                })
                .collect()
        })
        .collect()
}

fn table_blocks(rows_all: &[Row]) -> Vec<Value> {
    let rows: Vec<&Row> = rows_all
        .iter()
        .filter(|r| r.cells.iter().any(|c| !cell_text(c).is_empty()))
        .collect();
    if rows.is_empty() {
        return vec![];
    }
    let texts: Vec<Vec<String>> = rows
        .iter()
        .map(|r| {
            r.cells
                .iter()
                .map(cell_text)
                .filter(|t| !t.is_empty() && !SYMBOL.contains(&t.as_str()))
                .collect()
        })
        .collect();
    let cells: Vec<&String> = texts.iter().flatten().collect();
    if cells.is_empty() {
        return vec![];
    }
    let flat = cells
        .iter()
        .map(|s| s.as_str())
        .collect::<Vec<_>>()
        .join(" ");

    // layout wrappers: one row / one real cell -> paragraph
    if rows.len() == 1 && texts[0].len() == 1 {
        let c = rows[0]
            .cells
            .iter()
            .find(|c| !cell_text(c).is_empty())
            .unwrap();
        return vec![para(c.spans.clone(), 0.0)];
    }

    // bullets encoded as a 2-cell table: "•" | text
    let bullet_row = |r: &Row| -> Option<Value> {
        let real: Vec<&Cell> = r
            .cells
            .iter()
            .filter(|c| !cell_text(c).is_empty())
            .collect();
        if real.len() != 2 {
            return None;
        }
        let m = cell_text(real[0]);
        let c0 = first(&m)?;
        let lead_ok = BULLETS.contains(c0) || "0123456789(abcdefghijklmnopqrstuvwxyz".contains(c0);
        if nchars(&m) <= 3 && lead_ok && (BULLETS.contains(c0) || MARKER.is_match(&m)) {
            return Some(json!({"t": "li", "marker": m, "spans": spans_json(&real[1].spans)}));
        }
        None
    };
    let lis: Vec<Option<Value>> = rows.iter().map(|r| bullet_row(r)).collect();
    if lis.iter().all(Option::is_some) {
        return lis.into_iter().flatten().collect();
    }

    if "☐☒☑¨þý".chars().any(|ch| flat.contains(ch)) {
        return vec![text_table(&rows, "cover")];
    }
    let item_rows = texts
        .iter()
        .filter(|t| t.first().is_some_and(|t0| ITEM.is_match(t0)))
        .count();
    if rows.len() >= 5 && item_rows >= 4 {
        return vec![text_table(&rows, "toc")];
    }
    if flat.contains("/s/") {
        return vec![text_table(&rows, "signature")];
    }
    let exhibit_nos = texts
        .iter()
        .filter(|t| t.first().is_some_and(|t0| EXHIBIT_NO.is_match(t0)))
        .count();
    if rows.len() > 6 && EXHIBIT.is_match(&texts[0].join(" "))
        || rows.len() > 8 && exhibit_nos as f64 > rows.len() as f64 / 2.0
    {
        return vec![text_table(&rows, "exhibits")];
    }

    let vals = cells.iter().filter(|c| is_value(c)).count();
    let widest = texts.iter().map(Vec::len).max().unwrap_or(0);
    if vals as f64 / cells.len() as f64 >= 0.3
        && widest >= 2
        && let Some(num) = num_table(&rows)
    {
        return vec![num];
    }
    vec![text_table(&rows, "text")]
}

fn text_table(rows: &[&Row], kind: &str) -> Value {
    let grid = grid(rows);
    let used: Vec<usize> = grid
        .iter()
        .flat_map(|g| {
            g.iter()
                .filter(|(_, _, c)| !cell_text(c).is_empty())
                .map(|(s, _, _)| *s)
        })
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let mut out: Vec<Vec<String>> = Vec::new();
    for g in &grid {
        let line: Vec<String> = used
            .iter()
            .map(|col| {
                g.iter()
                    .find(|(s, _, _)| s == col)
                    .map_or_else(String::new, |(_, _, c)| cell_text(c))
            })
            .collect();
        if line.iter().any(|t| !t.is_empty()) {
            out.push(line);
        }
    }
    // drop columns that ended up empty everywhere
    let keep: Vec<usize> = (0..used.len())
        .filter(|&i| out.iter().any(|r| !r[i].is_empty()))
        .collect();
    let rows: Vec<Vec<&String>> = out
        .iter()
        .map(|r| keep.iter().map(|&i| &r[i]).collect())
        .collect();
    json!({"t": "table", "kind": kind, "rows": rows})
}

struct HCell {
    s: String,
    c: usize,
    span: usize,
}

#[derive(Clone)]
struct Val {
    s: String,
    cur: Option<String>,
    x: Option<String>,
    neg: bool,
}

/// Financial grid: label column + value columns. EDGAR splits each value
/// over spacer, "$", number and ")" cells, so value columns are keyed by the
/// END column of the cells holding a number; symbol cells fold into their
/// neighbour and header cells map to the value columns they cover.
fn num_table(rows: &[&Row]) -> Option<Value> {
    let grid = grid(rows);
    let is_val: Vec<Vec<bool>> = grid
        .iter()
        .map(|g| g.iter().map(|(_, _, c)| is_value(&cell_text(c))).collect())
        .collect();
    let mut first_body = is_val.iter().position(|v| v.iter().any(|b| *b))?;
    // a header row is one before the first value row; a row of only years also counts
    while first_body < grid.len()
        && grid[first_body].iter().all(|(_, _, c)| {
            let t = cell_text(c);
            t.is_empty() || !is_value(&t) || YEARISH.is_match(&t)
        })
        && !grid[first_body].iter().any(|(s, _, c)| {
            let t = cell_text(c);
            !t.is_empty() && !is_value(&t) && *s == 0 && !UNITS.is_match(&t)
        })
    {
        first_body += 1;
    }
    if first_body >= grid.len() {
        return None;
    }

    let mut ends: HashMap<usize, usize> = HashMap::new();
    for (g, v) in grid[first_body..].iter().zip(&is_val[first_body..]) {
        for ((s, e, _), isv) in g.iter().zip(v) {
            if *isv && *s > 0 {
                *ends.entry(*e).or_default() += 1;
            }
        }
    }
    // a stray number on the label side would add a phantom column: keep
    // columns with a real share of the values
    let top = ends.values().copied().max().unwrap_or(0);
    let floor = (top as f64 * 0.15).max(1.0);
    let mut data_cols: Vec<usize> = ends
        .iter()
        .filter(|(_, n)| **n as f64 >= floor)
        .map(|(e, _)| *e)
        .collect();
    data_cols.sort_unstable();
    if data_cols.is_empty() {
        return None;
    }
    let label_end = data_cols[0];
    let col_for = |s: usize, e: usize| -> Option<usize> {
        if let Some(i) = data_cols.iter().rposition(|d| s <= *d && *d <= e) {
            return Some(i);
        }
        data_cols.iter().position(|d| *d >= e)
    };

    let mut units: Option<String> = None;
    let mut header: Vec<Value> = Vec::new();
    for g in &grid[..first_body] {
        let mut line: Vec<HCell> = Vec::new();
        let mut label_txt: Vec<String> = Vec::new();
        for (s, e, c) in g {
            let mut txt = cell_text(c);
            if txt.is_empty() || SYMBOL.contains(&txt.as_str()) {
                continue;
            }
            if units.is_none()
                && let Some(m) = UNITS.captures(&txt)
            {
                let whole = m.get(0).unwrap();
                units = Some(m[1].to_string());
                let joined = format!("{}{}", &txt[..whole.start()], &txt[whole.end()..]);
                txt = clean(&joined).trim_matches(['(', ')', ' ']).to_string();
                if txt.is_empty() {
                    continue;
                }
            }
            if *s < label_end && *e < label_end {
                label_txt.push(txt);
                continue;
            }
            let covered: Vec<usize> = (0..data_cols.len())
                .filter(|&i| *s <= data_cols[i] && data_cols[i] <= *e)
                .collect();
            let (c0, n) = if covered.is_empty() {
                match col_for(*s, *e) {
                    Some(ci) => (ci, 1),
                    None => continue,
                }
            } else {
                (covered[0], covered.len())
            };
            line.push(HCell {
                s: txt,
                c: c0 + 1,
                span: n,
            });
        }
        if line.is_empty() && label_txt.is_empty() {
            continue;
        }
        // merge cells landing on the same column
        let mut cells_: Vec<HCell> = Vec::new();
        for cell in line {
            match cells_.iter_mut().find(|m| m.c == cell.c) {
                Some(m) => {
                    m.s.push(' ');
                    m.s.push_str(&cell.s);
                }
                None => cells_.push(cell),
            }
        }
        cells_.sort_by_key(|c| c.c);
        // a year header drawn left of its column lands in the label area: move it right
        if label_txt.len() == 1
            && YEARISH.is_match(&label_txt[0])
            && cells_.iter().all(|c| c.span == 1)
        {
            let taken: Vec<usize> = cells_.iter().map(|c| c.c).collect();
            if !taken.contains(&1) {
                cells_.insert(
                    0,
                    HCell {
                        s: label_txt.pop().unwrap(),
                        c: 1,
                        span: 1,
                    },
                );
            } else if cells_.len() + 1 == data_cols.len() {
                let mut all = vec![label_txt.pop().unwrap()];
                all.extend(cells_.drain(..).map(|c| c.s));
                cells_ = all
                    .into_iter()
                    .enumerate()
                    .map(|(i, s)| HCell {
                        s,
                        c: i + 1,
                        span: 1,
                    })
                    .collect();
            }
        }
        let mut hrow: Vec<Value> = Vec::new();
        if !label_txt.is_empty() {
            hrow.push(json!({"s": label_txt.join(" "), "c": 0, "span": 1}));
        }
        hrow.extend(
            cells_
                .iter()
                .map(|c| json!({"s": c.s, "c": c.c, "span": c.span})),
        );
        header.push(Value::Array(hrow));
    }

    struct BodyRow {
        label: String,
        v: Vec<Option<Val>>,
        ind: f64,
        b: bool,
        rule: Rule,
        rule_below: Rule,
    }
    let mut body: Vec<BodyRow> = Vec::new();
    for (r, g) in rows[first_body..].iter().zip(&grid[first_body..]) {
        let mut label_parts: Vec<String> = Vec::new();
        let mut label_bold = false;
        let mut label_indent: Option<f64> = None;
        let mut values: Vec<Option<Val>> = vec![None; data_cols.len()];
        let mut cur: Option<String> = None;
        let mut top = r.top;
        let mut bot = r.bot;
        for (s, e, c) in g {
            let txt = cell_text(c);
            if *s > 0 && *s >= label_end || *e >= label_end && is_value(&txt) {
                top = top.or(c.top);
                bot = bot.or(c.bot);
            }
            if txt.is_empty() {
                continue;
            }
            if matches!(txt.as_str(), "$" | "€" | "£" | "¥") {
                cur = Some(txt);
                continue;
            }
            if matches!(txt.as_str(), ")" | "%" | "%)") {
                let ci = col_for(*s, *e);
                let mut tgt = match ci {
                    Some(ci) if ci > 0 && values[ci - 1].is_some() => Some(ci - 1),
                    _ => None,
                };
                if tgt.is_none() {
                    tgt = values.iter().rposition(Option::is_some);
                }
                if let Some(t) = tgt {
                    let v = values[t].as_mut().unwrap();
                    if !v.s.ends_with(txt.as_str()) {
                        v.s.push_str(&txt);
                    }
                }
                continue;
            }
            if *e < label_end {
                label_bold = label_bold || share(&c.spans, bold) > 0.8;
                label_indent.get_or_insert(c.indent);
                label_parts.push(txt);
                continue;
            }
            let Some(ci) = col_for(*s, *e) else {
                continue;
            };
            let stripped = txt.replace(['$', '€', '£'], "");
            let v = Val {
                s: strip(&stripped).to_string(),
                cur: cur.take(),
                x: c.spans.iter().find_map(|sp| sp.x.clone()),
                neg: txt.contains('(') && txt.contains(')')
                    || txt.starts_with('(') && is_value(&txt),
            };
            match values[ci].as_mut() {
                Some(prev) => {
                    prev.s.push(' ');
                    prev.s.push_str(&v.s);
                }
                None => values[ci] = Some(v),
            }
        }
        if label_parts.is_empty() && values.iter().all(Option::is_none) {
            continue;
        }
        body.push(BodyRow {
            label: label_parts.join(" "),
            v: values,
            ind: label_indent.unwrap_or(0.0),
            b: label_bold,
            rule: top,
            rule_below: bot,
        });
    }
    if body.is_empty() {
        return None;
    }
    let vs = |v: &Option<Val>| v.as_ref().map_or(String::new(), |v| v.s.clone());
    // an index of statements with page numbers ("Balance Sheets ... 64")
    if data_cols.len() == 1
        && body.iter().all(|r| {
            let s = vs(&r.v[0]);
            TOC_PAGE.is_match(if s.is_empty() { "0" } else { &s })
        })
    {
        let rows: Vec<Value> = body.iter().map(|r| json!([r.label, vs(&r.v[0])])).collect();
        return Some(json!({"t": "table", "kind": "toc", "rows": rows}));
    }
    let levels: Vec<i64> = body
        .iter()
        .map(|r| py_round(r.ind))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    let rows_json: Vec<Value> = body
        .iter()
        .map(|r| {
            let mut m = Map::new();
            m.insert("label".into(), json!(r.label));
            let v: Vec<Value> =
                r.v.iter()
                    .map(|v| match v {
                        None => json!({"s": ""}),
                        Some(v) => {
                            let mut o = Map::new();
                            o.insert("s".into(), json!(v.s));
                            if let Some(c) = &v.cur {
                                o.insert("cur".into(), json!(c));
                            }
                            if let Some(x) = &v.x {
                                o.insert("x".into(), json!(x));
                            }
                            if v.neg {
                                o.insert("neg".into(), json!(1));
                            }
                            Value::Object(o)
                        }
                    })
                    .collect();
            m.insert("v".into(), Value::Array(v));
            if r.b {
                m.insert("b".into(), json!(1));
            }
            if let Some(t) = r.rule {
                m.insert("rule".into(), json!(t));
            }
            if let Some(t) = r.rule_below {
                m.insert("rule_below".into(), json!(t));
            }
            if !r
                .v
                .iter()
                .any(|v| v.as_ref().is_some_and(|v| !v.s.is_empty()))
            {
                m.insert("section".into(), json!(1));
            }
            let lvl = levels
                .iter()
                .position(|l| *l == py_round(r.ind))
                .unwrap_or(0);
            if lvl > 0 {
                m.insert("indent".into(), json!(lvl.min(4)));
            }
            Value::Object(m)
        })
        .collect();
    let mut out = json!({"t": "table", "kind": "num", "cols": data_cols.len(), "header": header, "rows": rows_json});
    if let Some(u) = units {
        out["units"] = json!(u);
    }
    Some(out)
}

// ---------------------------------------------------------------------------
// Document
// ---------------------------------------------------------------------------

fn block_line(b: &Value) -> String {
    match b["t"].as_str() {
        Some("h") => b["text"].as_str().unwrap_or("").to_string(),
        Some("p") => block_text_spans(b),
        _ => String::new(),
    }
}

/// Drop running headers/footers, attach footnotes to tables, find units
/// stated in the paragraph above a table.
fn post(blocks: Vec<Value>) -> Vec<Value> {
    let mut counts: HashMap<String, usize> = HashMap::new();
    for b in &blocks {
        if b["t"] == "p" {
            let t = block_text_spans(b);
            if nchars(&t) < 90 {
                *counts.entry(t).or_default() += 1;
            }
        }
    }
    for b in &blocks {
        if b["t"] == "h" && b["level"].as_i64().unwrap_or(9) >= 2 {
            *counts
                .entry(b["text"].as_str().unwrap_or("").to_string())
                .or_default() += 1;
        }
    }
    let count = |t: &str| counts.get(t).copied().unwrap_or(0);
    // press releases print "Title / date / Page 2 of 9" atop each page
    let mut running: std::collections::HashSet<String> = Default::default();
    for (i, b) in blocks.iter().enumerate() {
        if PAGE_OF.is_match(&block_line(b)) {
            for prev in &blocks[i.saturating_sub(2)..i] {
                let t = block_line(prev);
                if !t.is_empty() && count(&t) >= 2 {
                    running.insert(t);
                }
            }
        }
    }
    let mut out: Vec<Value> = Vec::new();
    let mut units_at: Vec<Option<String>> = Vec::new();
    for mut b in blocks {
        let line = block_line(&b);
        if !line.is_empty()
            && (PAGE_OF.is_match(&line) || running.contains(&line) || SGML_STUB.is_match(&line))
        {
            continue;
        }
        let mut my_units = None;
        if b["t"] == "p" {
            let txt = block_text_spans(&b);
            let len = nchars(&txt);
            if len < 90 && count(&txt) > 8 || PAGE_NO.is_match(&txt) && len < 6 {
                continue;
            }
            let low = txt.to_lowercase();
            if low == "table of contents" || low == "index" {
                continue;
            }
            let tail = out.len().saturating_sub(4);
            let last_tbl = (tail..out.len()).rev().find(|&k| out[k]["t"] == "table");
            if let Some(k) = last_tbl
                && FOOTNOTE.is_match(&txt)
                && k == out.len() - 1
            {
                let tbl = &mut out[k];
                if tbl.get("notes").is_none() {
                    tbl["notes"] = json!([]);
                }
                tbl["notes"].as_array_mut().unwrap().push(json!(txt));
                continue;
            }
            if let Some(m) = UNITS.captures(&txt)
                && len < 120
            {
                my_units = Some(m[1].to_string());
            }
        }
        if b["t"] == "h"
            && b["level"].as_i64().unwrap_or(0) >= 2
            && count(b["text"].as_str().unwrap_or("")) > 8
        {
            continue;
        }
        if b["t"] == "table"
            && b["kind"] == "num"
            && b.get("units").is_none()
            && let Some(Some(u)) = units_at.last()
            && !u.is_empty()
        {
            b["units"] = json!(u);
        }
        out.push(b);
        units_at.push(my_units);
    }
    // collapse runs of page markers
    let mut fin: Vec<Value> = Vec::new();
    for b in out {
        if b["t"] == "page"
            && let Some(last) = fin.last_mut()
            && last["t"] == "page"
        {
            for (k, v) in b.as_object().unwrap() {
                if truthy(Some(v)) {
                    last[k] = v.clone();
                }
            }
            continue;
        }
        fin.push(b);
    }
    let lead = fin.iter().take_while(|b| b["t"] == "page").count();
    fin.drain(..lead);
    join_across_pages(fin)
}

/// A paragraph cut by a page break continues in lowercase on the next page:
/// glue it back and keep the page marker after the joined paragraph.
fn join_across_pages(mut blocks: Vec<Value>) -> Vec<Value> {
    let mut out: Vec<Value> = Vec::new();
    let mut i = 0;
    while i < blocks.len() {
        let b = &blocks[i];
        if b["t"] == "page"
            && i + 1 < blocks.len()
            && out.last().is_some_and(|o| o["t"] == "p" || o["t"] == "li")
            && blocks[i + 1]["t"] == "p"
        {
            let nxt = &blocks[i + 1];
            let prev = out.last().unwrap();
            let head = block_text_spans(prev);
            let head = head.trim_end_matches(py_ws);
            let tail = block_text_spans(nxt);
            let tail = tail.trim_start_matches(py_ws);
            let head_end = head.chars().last();
            let joins = first(tail).is_some_and(char::is_lowercase)
                && head_end.is_some_and(|c| !".:!?\u{201d}\"".contains(c));
            if joins {
                let mut spans = spans_of(prev);
                spans.push(Span::plain(" "));
                spans.extend(spans_of(nxt));
                let last = out.last_mut().unwrap();
                last["spans"] = spans_json(&tidy(&spans));
                out.push(std::mem::take(&mut blocks[i]));
                i += 2;
                continue;
            }
        }
        out.push(std::mem::take(&mut blocks[i]));
        i += 1;
    }
    out
}

fn spans_of(b: &Value) -> Vec<Span> {
    b["spans"]
        .as_array()
        .map(|a| {
            a.iter()
                .map(|s| Span {
                    s: s["s"].as_str().unwrap_or("").to_string(),
                    b: s.get("b").is_some(),
                    i: s.get("i").is_some(),
                    u: s.get("u").is_some(),
                    x: s["x"].as_str().map(str::to_string),
                })
                .collect()
        })
        .unwrap_or_default()
}

/// The blocks of one filing's HTML (`parse` in the Python).
pub fn parse(html_text: &str, base_url: &str) -> Result<Vec<Value>, String> {
    let base = match base_url.rsplit_once('/') {
        Some((head, _)) if !base_url.is_empty() => format!("{head}/"),
        _ if !base_url.is_empty() => format!("{base_url}/"),
        _ => String::new(),
    };
    let mut p = Parser {
        base,
        ..Default::default()
    };
    html::feed(html_text, &mut p)?;
    p.flush();
    Ok(post(p.blocks))
}

fn stats(blocks: &[Value]) -> Value {
    let mut m = Map::new();
    let words: usize = blocks
        .iter()
        .filter(|b| b["t"] == "p" || b["t"] == "li")
        .map(|b| {
            block_text_spans(b)
                .split(py_ws)
                .filter(|w| !w.is_empty())
                .count()
        })
        .sum();
    m.insert("words".into(), json!(words));
    m.insert("blocks".into(), json!(blocks.len()));
    for b in blocks {
        let t = b["t"].as_str().unwrap_or("");
        let k = if t == "table" {
            format!("table_{}", b["kind"].as_str().unwrap_or(""))
        } else {
            t.to_string()
        };
        let n = m.get(&k).and_then(Value::as_u64).unwrap_or(0);
        m.insert(k, json!(n + 1));
    }
    let tagged = blocks
        .iter()
        .filter(|b| b["kind"] == "num")
        .flat_map(|b| b["rows"].as_array().into_iter().flatten())
        .flat_map(|r| r["v"].as_array().into_iter().flatten())
        .filter(|v| v.get("x").is_some())
        .count();
    m.insert("xbrl_cells".into(), json!(tagged));
    Value::Object(m)
}

/// `document(html, {"url": url})`: what docview caches as `<file>.blocks.json`.
pub fn document(html_text: &str, url: &str) -> Result<Value, String> {
    let blocks = parse(html_text, url)?;
    let outline: Vec<Value> = blocks
        .iter()
        .enumerate()
        .filter(|(_, b)| b["t"] == "h")
        .map(|(i, b)| json!({"i": i, "level": b["level"], "text": b["text"]}))
        .collect();
    Ok(json!({
        "v": PARSER_VERSION,
        "url": url,
        "stats": stats(&blocks),
        "outline": outline,
        "blocks": blocks,
    }))
}

/// `Path.read_text(errors="ignore")`: invalid UTF-8 dropped, universal newlines.
pub fn read_text(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len());
    let mut rest = bytes;
    loop {
        match std::str::from_utf8(rest) {
            Ok(v) => {
                s.push_str(v);
                break;
            }
            Err(e) => {
                let good = e.valid_up_to();
                s.push_str(std::str::from_utf8(&rest[..good]).unwrap());
                let bad = e.error_len().unwrap_or(rest.len() - good);
                rest = &rest[good + bad..];
            }
        }
    }
    if s.contains('\r') {
        s = s.replace("\r\n", "\n").replace('\r', "\n");
    }
    s
}

/// `fl filing-blocks FILE URL`: print `document()` for one HTML file.
pub fn run_cli(args: &[String]) -> i32 {
    let (Some(path), url) = (args.first(), args.get(1).map_or("", String::as_str)) else {
        eprintln!("usage: fl filing-blocks FILE [URL]");
        return 2;
    };
    let bytes = match std::fs::read(path) {
        Ok(b) => b,
        Err(e) => {
            eprintln!("{path}: {e}");
            return 1;
        }
    };
    let t = std::time::Instant::now();
    match document(&read_text(&bytes), url) {
        Ok(doc) => {
            eprintln!("parsed in {:?}", t.elapsed());
            println!("{doc}");
            0
        }
        Err(e) => {
            eprintln!("{e}");
            1
        }
    }
}

#[cfg(test)]
mod bench {
    use super::*;

    struct Null;
    impl Sink for Null {
        fn start(&mut self, _: &str, _: &Attrs) -> Result<(), String> {
            Ok(())
        }
        fn startend(&mut self, _: &str, _: &Attrs) -> Result<(), String> {
            Ok(())
        }
        fn end(&mut self, _: &str) {}
        fn data(&mut self, _: &str) {}
    }

    #[test]
    #[ignore]
    fn phases() {
        let path = std::env::var("FL_BLOCKS_FILE").unwrap();
        let bytes = std::fs::read(path).unwrap();
        let t = std::time::Instant::now();
        let s = read_text(&bytes);
        eprintln!("read {:?}", t.elapsed());
        let t = std::time::Instant::now();
        html::feed(&s, &mut Null).unwrap();
        eprintln!("tokenize {:?}", t.elapsed());
        let t = std::time::Instant::now();
        let mut p = Parser::default();
        html::feed(&s, &mut p).unwrap();
        eprintln!("tokenize+parse {:?}", t.elapsed());
        let t = std::time::Instant::now();
        let b = post(p.blocks);
        eprintln!("post {:?} ({} blocks)", t.elapsed(), b.len());
    }
}
