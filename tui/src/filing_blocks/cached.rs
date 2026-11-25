//! docview's in-process path for an SEC filing already in the cache: the
//! same files py/derive/docview.py `open_doc(url, quote, blocks=True)` reads
//! and writes, without starting Python. Anything it isn't sure of (not SEC,
//! not downloaded yet, an -index page, no .md yet) returns None and docview
//! asks docview.py as before.

use std::path::{Path, PathBuf};
use std::sync::LazyLock;

use regex::Regex;
use serde_json::Value;

use super::{PARSER_VERSION, document, read_text};

/// What docview.py would have answered for a cached filing.
pub struct Cached {
    pub url: String,
    pub title: String,
    pub doc: Value,
    /// Index of the block holding the quote.
    pub block: Option<usize>,
}

static SEC: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"/Archives/edgar/data/(\d+)/(\d{18})/").unwrap());
static IX: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^https?://www\.sec\.gov/ix\?doc=(/Archives/.+)").unwrap());
static UNSAFE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"[^\w.\-]").unwrap());
static INDEX_PAGE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"-index\.html?$").unwrap());

/// `urllib.parse.unquote`: %XX bytes decoded as UTF-8, bad sequences replaced.
fn unquote(s: &str) -> String {
    let b = s.as_bytes();
    let mut out = Vec::with_capacity(b.len());
    let mut i = 0;
    while i < b.len() {
        if b[i] == b'%'
            && i + 2 < b.len()
            && let Ok(v) =
                u8::from_str_radix(std::str::from_utf8(&b[i + 1..i + 3]).unwrap_or("zz"), 16)
        {
            out.push(v);
            i += 3;
            continue;
        }
        out.push(b[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).into_owned()
}

/// `split_fragment`: the url and the #:~:text= quote.
fn split_fragment(url: &str) -> (&str, Option<String>) {
    if let Some((base, frag)) = url.split_once("#:~:text=") {
        let frag = frag.split('&').next().unwrap_or("");
        let frag = frag.split(',').next().unwrap_or("");
        return (base, Some(unquote(frag)));
    }
    (url.split('#').next().unwrap_or(url), None)
}

/// `_norm`.
fn norm(s: &str) -> String {
    let s = s
        .replace('\\', "")
        .replace('\u{2019}', "'")
        .replace(['\u{201c}', '\u{201d}'], "\"")
        .replace('\u{a0}', " ")
        .replace(['*', '_', '`', '\u{2022}'], " ");
    s.split(super::html::py_ws)
        .filter(|w| !w.is_empty())
        .collect::<Vec<_>>()
        .join(" ")
        .to_lowercase()
}

/// `_block_text`.
fn block_text(b: &Value) -> String {
    let strs = |v: &Value| -> Vec<String> {
        v.as_array()
            .map(|a| {
                a.iter()
                    .filter_map(|x| x.as_str().map(str::to_string))
                    .collect()
            })
            .unwrap_or_default()
    };
    match b["t"].as_str() {
        Some("h") => b["text"].as_str().unwrap_or("").to_string(),
        Some("p" | "li") => super::block_text_spans(b),
        Some("table") if b["kind"] == "num" => b["rows"]
            .as_array()
            .map(|rows| {
                rows.iter()
                    .map(|r| {
                        let vals: Vec<&str> = r["v"]
                            .as_array()
                            .map(|v| v.iter().map(|x| x["s"].as_str().unwrap_or("")).collect())
                            .unwrap_or_default();
                        format!("{} {}", r["label"].as_str().unwrap_or(""), vals.join(" "))
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .unwrap_or_default(),
        Some("table") => b["rows"]
            .as_array()
            .map(|rows| {
                rows.iter()
                    .map(|r| strs(r).join(" "))
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .unwrap_or_default(),
        _ => String::new(),
    }
}

/// `find_block`: the first block holding the quote's opening 8/6/4/3 words.
fn find_block(blocks: &[Value], quote: Option<&str>) -> Option<usize> {
    let quote = quote?;
    let texts: Vec<String> = blocks.iter().map(|b| norm(&block_text(b))).collect();
    let words: Vec<String> = norm(quote).split(' ').map(str::to_string).collect();
    for n in [8, 6, 4, 3] {
        let needle = words[..n.min(words.len())].join(" ");
        if needle.chars().count() < 8 {
            break;
        }
        if let Some(i) = texts.iter().position(|t| t.contains(&needle)) {
            return Some(i);
        }
    }
    None
}

/// The URL path's last component, made safe the way docview.py names files.
fn file_name(url: &str) -> String {
    let after_scheme = url.split_once("://").map_or(url, |(_, r)| r);
    let path = after_scheme.find('/').map_or("", |p| &after_scheme[p..]);
    let path = path.split(['?', '#']).next().unwrap_or("");
    let last = path.rsplit('/').next().unwrap_or("");
    let name = UNSAFE.replace_all(last, "_").into_owned();
    if name.is_empty() {
        "index".into()
    } else {
        name
    }
}

pub fn open(docs: &Path, url: &str, quote: Option<&str>) -> Option<Cached> {
    let (url, frag_quote) = split_fragment(url);
    let quote = quote.map(str::to_string).or(frag_quote);
    let url = match IX.captures(url) {
        Some(c) => format!("https://www.sec.gov{}", &c[1]),
        None => url.to_string(),
    };
    let c = SEC.captures(&url)?;
    let cik: u64 = c[1].parse().ok()?;
    let dir = docs.join(format!("sec_{cik}_{}", &c[2]));
    let name = file_name(&url);
    if INDEX_PAGE.is_match(&name) {
        return None;
    }
    let mut raw = dir.join(&name);
    let ext = Path::new(&name)
        .extension()
        .map(|e| e.to_string_lossy().to_lowercase());
    if !raw.exists() {
        // an extensionless URL is cached under name + .html
        let alt = dir.join(format!("{name}.html"));
        if dir.join(format!("{name}.pdf")).exists() || !alt.exists() {
            return None;
        }
        raw = alt;
    } else if !matches!(ext.as_deref(), Some("htm" | "html")) {
        return None;
    }
    // docview.py writes the .md (and title) on the first open: leave that to it
    if !raw.with_extension("md").exists() {
        return None;
    }
    let title = std::fs::read_to_string(dir.join("title"))
        .ok()
        .map(|t| t.trim().to_string())
        .filter(|t| !t.is_empty())
        .unwrap_or_else(|| name.clone());
    let path = PathBuf::from(format!("{}.blocks.json", raw.display()));
    let saved = std::fs::read(&path)
        .ok()
        .and_then(|b| serde_json::from_slice::<Value>(&b).ok())
        .filter(|d| d["v"].as_u64() == Some(PARSER_VERSION));
    let doc = match saved {
        Some(d) => d,
        None => {
            let html = read_text(&std::fs::read(&raw).ok()?);
            let d = document(&html, &url).ok()?;
            let _ = std::fs::write(&path, d.to_string());
            d
        }
    };
    let block = find_block(doc["blocks"].as_array()?, quote.as_deref());
    Some(Cached {
        url,
        title,
        doc,
        block,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn names_and_quotes_follow_docview_py() {
        assert_eq!(
            file_name("https://www.sec.gov/Archives/edgar/data/1/000000000000000001/a b+c.htm?x=1"),
            "a_b_c.htm"
        );
        assert_eq!(file_name("https://www.sec.gov/"), "index");
        let (u, q) = split_fragment("https://x/y.htm#:~:text=Net%20revenue%E2%80%99s,end");
        assert_eq!(
            (u, q.as_deref()),
            ("https://x/y.htm", Some("Net revenue\u{2019}s"))
        );
        assert_eq!(
            norm("  It\u{2019}s *the* \u{201c}Big\u{201d}\u{a0}one "),
            "it's the \"big\" one"
        );
    }
}

#[cfg(test)]
mod parity {
    /// FL_OPEN_CASES: lines of `url\tquote`; prints `title\turl\tblock` per line.
    #[test]
    #[ignore]
    fn open_cases() {
        let cases = std::fs::read_to_string(std::env::var("FL_OPEN_CASES").unwrap()).unwrap();
        let docs = std::path::PathBuf::from(std::env::var("FL_DOCS").unwrap());
        for line in cases.lines() {
            let (url, q) = line.split_once('\t').unwrap_or((line, ""));
            let q = (!q.is_empty()).then_some(q);
            let t = std::time::Instant::now();
            let r = super::open(&docs, url, q);
            if std::env::var("FL_OPEN_TIME").is_ok() {
                let blocks = r
                    .as_ref()
                    .map(|c| crate::ui::doc_blocks::from_value(c.doc.clone()).map(|b| b.len()));
                eprintln!("TIME {:?} {url} {blocks:?}", t.elapsed());
            }
            match r {
                Some(c) => println!("OUT\t{}\t{}\t{:?}", c.title, c.url, c.block),
                None => println!("OUT\tNONE"),
            }
        }
    }
}
