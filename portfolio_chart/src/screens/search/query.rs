// Query-string helpers for the search screen. Parsing proper stays in
// views/search.py (one parser); this only does the lexical work the UI
// needs without a round trip:
//
//   toggle()      facet click -> rewrite the t: / type: / sec: / since:+until:
//                 tokens in the query string, keeping everything else as typed
//   is_active()   whether a facet value is already selected by the query
//   highlight()   split text into plain / matched spans for the terms the
//                 server echoes back (same stem-prefix rule as search.py _hl_re)
//   snippet()     window of the text around the first matched term

use std::ops::Range;

/// Facet dimensions, in sidebar order. `key` is the token written on toggle,
/// `keys` every spelling search.py accepts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Dim {
    Ticker,
    Type,
    Section,
    Year,
}

impl Dim {
    pub const ALL: [Dim; 4] = [Dim::Ticker, Dim::Type, Dim::Section, Dim::Year];

    /// Name used in the facets object of a search.py reply.
    pub fn name(self) -> &'static str {
        match self {
            Dim::Ticker => "ticker",
            Dim::Type => "type",
            Dim::Section => "section",
            Dim::Year => "year",
        }
    }

    fn keys(self) -> &'static [&'static str] {
        match self {
            Dim::Ticker => &["t", "ticker"],
            Dim::Type => &["type"],
            Dim::Section => &["sec", "section"],
            Dim::Year => &["since", "until"],
        }
    }
}

/// Short badge for a chunk type (mirrors TYPE_BADGE in search.py).
pub fn badge(kind: &str) -> &str {
    match kind {
        "filing" => "10K",
        "new_risk" => "NEW",
        "earnings" => "ERN",
        "guidance" => "GUI",
        "profile" => "PRF",
        "patent" => "PAT",
        other => other.get(..3).unwrap_or(other),
    }
}

/// Whitespace tokens, keeping `"quoted phrases"` and `key:"a b"` whole.
fn tokens(q: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut quoted = false;
    for c in q.chars() {
        if c == '"' {
            quoted = !quoted;
        }
        if c.is_whitespace() && !quoted {
            if !cur.is_empty() {
                out.push(std::mem::take(&mut cur));
            }
        } else {
            cur.push(c);
        }
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

/// `key:value` split with a lowercase key, or None for free text.
fn filter(tok: &str) -> Option<(String, &str)> {
    let (k, v) = tok.split_once(':')?;
    if k.is_empty() || !k.chars().all(|c| c.is_alphanumeric() || c == '_') {
        return None;
    }
    Some((k.to_lowercase(), v))
}

/// Values of every token for `dim` (comma lists flattened, quotes stripped).
fn values(q: &str, dim: Dim) -> Vec<String> {
    tokens(q)
        .iter()
        .filter_map(|t| filter(t))
        .filter(|(k, _)| dim.keys().contains(&k.as_str()))
        .flat_map(|(_, v)| v.trim_matches('"').split(',').filter(|s| !s.is_empty()).map(str::to_string).collect::<Vec<_>>())
        .collect()
}

/// Does a token value select facet `value`? Types and sections are prefix
/// matches in search.py (type:guid, sec:risk), tickers exact.
fn selects(dim: Dim, tok: &str, value: &str) -> bool {
    let (t, v) = (tok.to_lowercase(), value.to_lowercase());
    match dim {
        Dim::Ticker => t == v,
        Dim::Type => match t.as_str() {
            "10k" | "risk" => v == "filing",
            _ => v.starts_with(&t),
        },
        Dim::Section => v.starts_with(&t),
        Dim::Year => false,
    }
}

fn since_until(q: &str) -> (Option<String>, Option<String>) {
    let mut s = (None, None);
    for t in tokens(q) {
        match filter(&t) {
            Some((k, v)) if k == "since" => s.0 = Some(v.to_string()),
            Some((k, v)) if k == "until" => s.1 = Some(v.to_string()),
            _ => {}
        }
    }
    s
}

pub fn is_active(q: &str, dim: Dim, value: &str) -> bool {
    if dim == Dim::Year {
        let next = value.parse::<i32>().map(|y| (y + 1).to_string()).unwrap_or_default();
        let (s, u) = since_until(q);
        return s.is_some_and(|s| s.starts_with(value)) && u.is_some_and(|u| u.starts_with(&next));
    }
    values(q, dim).iter().any(|t| selects(dim, t, value))
}

/// Toggle facet `value` of `dim` in query `q`. The dimension's tokens are
/// merged into one (`t:MRVL,NVDA`) at the position of the first; a new one
/// goes first so filters read left of the free text. Year sets / clears the
/// pair `since:Y until:Y+1`.
pub fn toggle(q: &str, dim: Dim, value: &str) -> String {
    let active = is_active(q, dim, value);
    let mut vals: Vec<String> = match dim {
        Dim::Year => Vec::new(),
        _ => values(q, dim).into_iter().filter(|t| !selects(dim, t, value)).collect(),
    };
    if !active {
        match dim {
            Dim::Year => vals.push(value.to_string()),
            Dim::Ticker => vals.push(value.to_uppercase()),
            _ => vals.push(value.to_string()),
        }
    }
    let replacement: Vec<String> = match dim {
        Dim::Year => match vals.first().and_then(|y| y.parse::<i32>().ok()) {
            Some(y) => vec![format!("since:{y}"), format!("until:{}", y + 1)],
            None => Vec::new(),
        },
        _ if vals.is_empty() => Vec::new(),
        _ => vec![format!("{}:{}", dim.keys()[0], vals.join(","))],
    };
    let mut out: Vec<String> = Vec::new();
    let mut placed = false;
    for t in tokens(q) {
        if filter(&t).is_some_and(|(k, _)| dim.keys().contains(&k.as_str())) {
            if !placed {
                out.extend(replacement.iter().cloned());
                placed = true;
            }
        } else {
            out.push(t);
        }
    }
    if !placed {
        out.splice(0..0, replacement);
    }
    let mut s = out.join(" ");
    // keep a trailing space so typing continues as a new word
    if q.ends_with(char::is_whitespace) && !s.is_empty() {
        s.push(' ');
    }
    s
}

/// Stem prefix a term matches on, and whether trailing word chars extend it.
/// Porter stemming means "guidance" also ranks "guided"; phrases are literal.
fn stem(term: &str) -> (String, bool) {
    let t = term.to_lowercase();
    let n = t.chars().count();
    if t.contains(' ') {
        (t, false)
    } else if n <= 4 {
        (t, true)
    } else {
        (t.chars().take((n - 2).max(4)).collect(), true)
    }
}

fn is_word(c: char) -> bool {
    c.is_alphanumeric() || c == '_'
}

/// Byte ranges of `text` matching `terms`, non-overlapping, in order.
pub fn matches(text: &str, terms: &[String]) -> Vec<Range<usize>> {
    let mut stems: Vec<(String, bool)> = terms.iter().filter(|t| !t.is_empty()).map(|t| stem(t)).collect();
    stems.sort_by_key(|(s, _)| std::cmp::Reverse(s.len()));
    if stems.is_empty() {
        return Vec::new();
    }
    let lower: String = text.chars().flat_map(char::to_lowercase).collect();
    // to_lowercase can change byte lengths (rare, non-ASCII); fall back to no
    // highlighting rather than slicing at a wrong offset.
    if lower.len() != text.len() {
        return Vec::new();
    }
    let mut out = Vec::new();
    let mut i = 0;
    let mut prev: Option<char> = None;
    while i < lower.len() {
        let Some(c) = lower[i..].chars().next() else { break };
        if prev.is_none_or(|p| !is_word(p))
            && let Some((s, ext)) = stems.iter().find(|(s, _)| lower[i..].starts_with(s.as_str()))
        {
            let mut end = i + s.len();
            if *ext {
                end += lower[end..].chars().take_while(|c| is_word(*c)).map(char::len_utf8).sum::<usize>();
            }
            out.push(i..end);
            prev = lower[..end].chars().next_back();
            i = end;
            continue;
        }
        prev = Some(c);
        i += c.len_utf8();
    }
    out
}

/// (segment, is_match) pieces of `text`, covering it exactly.
pub fn highlight<'a>(text: &'a str, terms: &[String]) -> Vec<(&'a str, bool)> {
    let mut out = Vec::new();
    let mut at = 0;
    for r in matches(text, terms) {
        if r.start > at {
            out.push((&text[at..r.start], false));
        }
        out.push((&text[r.clone()], true));
        at = r.end;
    }
    if at < text.len() || out.is_empty() {
        out.push((&text[at..], false));
    }
    out
}

/// ~`width` chars of `text` starting a quarter-width before the first match
/// ("…" prefixed when cut), whitespace collapsed.
pub fn snippet(text: &str, terms: &[String], width: usize) -> String {
    let flat: String = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let first = matches(&flat, terms).first().map_or(0, |r| r.start);
    let chars_before = flat[..first].chars().count();
    let mut start = chars_before.saturating_sub(width / 4);
    // begin on a word: skip the partial word the window cut into (never past the match)
    if start > 0 {
        let skip = flat.chars().skip(start).take(chars_before - start).take_while(|c| !c.is_whitespace()).count();
        if start + skip < chars_before {
            start += skip + 1;
        }
    }
    let body: String = flat.chars().skip(start).take(width).collect();
    if start > 0 { format!("…{body}") } else { body }
}

/// First `n` words of `text`: the docview jump quote.
pub fn first_words(text: &str, n: usize) -> String {
    text.split_whitespace().take(n).collect::<Vec<_>>().join(" ")
}

/// Percent-encode for a `#:~:text=` fragment (model::Source::quote decodes it).
pub fn encode_fragment(s: &str) -> String {
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

#[cfg(test)]
mod tests {
    use super::*;

    fn s(v: &[&str]) -> Vec<String> {
        v.iter().map(|x| x.to_string()).collect()
    }

    #[test]
    fn toggles_tickers() {
        assert_eq!(toggle("guidance", Dim::Ticker, "MRVL"), "t:MRVL guidance");
        assert_eq!(toggle("t:MRVL guidance", Dim::Ticker, "NVDA"), "t:MRVL,NVDA guidance");
        assert_eq!(toggle("t:MRVL,NVDA guidance", Dim::Ticker, "mrvl"), "t:NVDA guidance");
        assert_eq!(toggle("t:MRVL guidance", Dim::Ticker, "MRVL"), "guidance");
        assert_eq!(toggle("hbm t:MU ", Dim::Ticker, "SK"), "hbm t:MU,SK ");
    }

    #[test]
    fn toggles_types_and_sections_with_prefixes() {
        assert!(is_active("type:guid x", Dim::Type, "guidance"));
        assert!(is_active("type:10k", Dim::Type, "filing"));
        assert_eq!(toggle("type:guid x", Dim::Type, "guidance"), "x");
        assert_eq!(toggle("x", Dim::Type, "new_risk"), "type:new_risk x");
        assert_eq!(toggle("sec:risk x", Dim::Section, "risk_factors"), "x");
        assert_eq!(toggle("\"high bandwidth\" x", Dim::Section, "mda"), "sec:mda \"high bandwidth\" x");
    }

    #[test]
    fn toggles_years() {
        let q = toggle("hbm", Dim::Year, "2025");
        assert_eq!(q, "since:2025 until:2026 hbm");
        assert!(is_active(&q, Dim::Year, "2025"));
        assert_eq!(toggle(&q, Dim::Year, "2024"), "since:2024 until:2025 hbm");
        assert_eq!(toggle(&q, Dim::Year, "2025"), "hbm");
        // a bare since: is not "year 2025 selected"
        assert!(!is_active("since:2025 hbm", Dim::Year, "2025"));
    }

    #[test]
    fn highlights_stems_and_phrases() {
        let t = s(&["guidance", "high bandwidth"]);
        let h = highlight("Guided by High Bandwidth memory; misguidance", &t);
        let hits: Vec<&str> = h.iter().filter(|(_, m)| *m).map(|(x, _)| *x).collect();
        assert_eq!(hits, vec!["High Bandwidth"]);
        let h = highlight("our guidance and guided view", &s(&["guidance"]));
        let hits: Vec<&str> = h.iter().filter(|(_, m)| *m).map(|(x, _)| *x).collect();
        assert_eq!(hits, vec!["guidance"]);
        let h = highlight("HBM3E and hbm", &s(&["hbm"]));
        assert_eq!(h.iter().filter(|(_, m)| *m).count(), 2);
        assert_eq!(highlight("plain", &[]), vec![("plain", false)]);
    }

    #[test]
    fn snippets_center_on_first_match() {
        let text = format!("{} needle tail", "word ".repeat(50));
        let sn = snippet(&text, &s(&["needle"]), 40);
        assert!(sn.starts_with('…'));
        assert!(sn.contains("needle"));
        assert_eq!(snippet("short text", &[], 40), "short text");
    }

    #[test]
    fn encodes_quote_fragments() {
        let src = crate::model::Source::url("x", format!("u#:~:text={}", encode_fragment("Q3 revenue, up 5%-ish")));
        assert_eq!(src.quote().as_deref(), Some("Q3 revenue, up 5%-ish"));
        assert_eq!(first_words("a  b\nc d", 3), "a b c");
    }
}
