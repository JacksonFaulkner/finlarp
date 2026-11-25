//! A port of CPython 3.12's `html.parser.HTMLParser` (convert_charrefs=True,
//! fed the whole document then closed), so the blocks parser sees exactly the
//! tags and text runs py/sources/filing_blocks.py sees. The tolerant start-tag
//! regexes are copied verbatim (fancy-regex: they use lookbehind/lookahead).

use std::sync::LazyLock;

use fancy_regex::Regex as Fancy;
use regex::Regex;

use super::entities::{HTML5, INVALID_CHARREFS, INVALID_CODEPOINTS};

/// Python's `\s` (str.isspace) is Unicode White_Space plus \x1c-\x1f.
pub fn py_ws(c: char) -> bool {
    c.is_whitespace() || ('\x1c'..='\x1f').contains(&c)
}

/// A pattern written with Python's `\s` / `\S`, made to match the same chars.
pub fn py_pat(p: &str) -> String {
    p.replace(r"\s", r"[\s\x1c-\x1f]")
        .replace(r"\S", r"[^\s\x1c-\x1f]")
}

fn re(p: &str) -> Regex {
    Regex::new(&py_pat(p)).expect("regex")
}

fn fancy(p: &str) -> Fancy {
    Fancy::new(&py_pat(p)).expect("fancy regex")
}

static CHARREF: LazyLock<Regex> =
    LazyLock::new(|| re(r"&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\x0c <&#;]{1,32};?)"));

static TAGFIND: LazyLock<Fancy> =
    LazyLock::new(|| fancy(r"^([a-zA-Z][^\t\n\r\x0c />\x00]*)(?:\s|/(?!>))*"));
static ATTRFIND: LazyLock<Fancy> = LazyLock::new(|| {
    fancy(
        r#"((?<=['"\s/])[^\s/>][^\s/=>]*)(\s*=+\s*('[^']*'|"[^"]*"|(?!['"])[^>\s]*))?(?:\s|/(?!>))*"#,
    )
});
static LOCATE: LazyLock<Fancy> = LazyLock::new(|| {
    fancy(concat!(
        r#"^<[a-zA-Z][^\t\n\r\x0c />\x00]*"#,
        r#"(?:[\s/]*(?:(?<=['"\s/])[^\s/>][^\s/=>]*"#,
        r#"(?:\s*=+\s*(?:'[^']*'|"[^"]*"|(?!['"])[^>\s]*)\s*)?(?:\s|/(?!>))*)*)?\s*"#,
    ))
});
static ENDTAGFIND: LazyLock<Regex> = LazyLock::new(|| re(r"^</\s*([a-zA-Z][-.a-zA-Z0-9:_]*)\s*>"));
static COMMENTCLOSE: LazyLock<Regex> = LazyLock::new(|| re(r"--\s*>"));
static DECLNAME: LazyLock<Regex> = LazyLock::new(|| re(r"^[a-zA-Z][-_.a-zA-Z0-9]*\s*"));
static MARKED_CLOSE: LazyLock<Regex> = LazyLock::new(|| re(r"]\s*]\s*>"));
static MS_MARKED_CLOSE: LazyLock<Regex> = LazyLock::new(|| re(r"]\s*>"));
static SCRIPT_CLOSE: LazyLock<Regex> = LazyLock::new(|| re(r"(?i)</\s*script\s*>"));
static STYLE_CLOSE: LazyLock<Regex> = LazyLock::new(|| re(r"(?i)</\s*style\s*>"));

/// `html.unescape`.
pub fn unescape(s: &str) -> String {
    if !s.contains('&') {
        return s.to_string();
    }
    CHARREF
        .replace_all(s, |c: &regex::Captures| replace_charref(&c[1]))
        .into_owned()
}

fn html5(name: &str) -> Option<&'static str> {
    HTML5
        .binary_search_by(|(k, _)| k.cmp(&name))
        .ok()
        .map(|i| HTML5[i].1)
}

fn replace_charref(s: &str) -> String {
    if let Some(num) = s.strip_prefix('#') {
        let (digits, radix) = match num.strip_prefix(['x', 'X']) {
            Some(h) => (h, 16),
            None => (num, 10),
        };
        let digits = digits.trim_end_matches(';');
        // Python ints don't overflow: anything past u64 is past 0x10FFFF too
        let n = u64::from_str_radix(digits, radix).unwrap_or(u64::MAX);
        if let Ok(k) = u32::try_from(n)
            && let Some((_, v)) = INVALID_CHARREFS.iter().find(|(c, _)| *c == k)
        {
            return (*v).to_string();
        }
        if (0xD800..=0xDFFF).contains(&n) || n > 0x10FFFF {
            return "\u{FFFD}".into();
        }
        if INVALID_CODEPOINTS.contains(&(n as u32)) {
            return String::new();
        }
        return char::from_u32(n as u32).map_or_else(|| "\u{FFFD}".into(), |c| c.to_string());
    }
    if let Some(v) = html5(s) {
        return v.to_string();
    }
    // longest prefix that is an entity (only the ;-less legacy ones can be)
    let chars: Vec<(usize, char)> = s.char_indices().collect();
    for x in (2..chars.len()).rev() {
        let cut = chars[x].0;
        if let Some(v) = html5(&s[..cut]) {
            return format!("{v}{}", &s[cut..]);
        }
    }
    format!("&{s}")
}

pub type Attrs = Vec<(String, Option<String>)>;

/// The handler hooks; an `Err` stops the parse (Python raising).
pub trait Sink {
    fn start(&mut self, tag: &str, attrs: &Attrs) -> Result<(), String>;
    fn startend(&mut self, tag: &str, attrs: &Attrs) -> Result<(), String>;
    fn end(&mut self, tag: &str);
    fn data(&mut self, s: &str);
}

fn py_strip(s: &str) -> &str {
    s.trim_matches(py_ws)
}

fn find_from(raw: &str, pat: char, from: usize) -> Option<usize> {
    raw.get(from..)?.find(pat).map(|p| p + from)
}

/// `feed(raw); close()`.
pub fn feed(raw: &str, sink: &mut dyn Sink) -> Result<(), String> {
    let b = raw.as_bytes();
    let n = raw.len();
    let mut i = 0usize;
    let mut cdata: Option<&'static str> = None;
    while i < n {
        let j = match cdata {
            None => find_from(raw, '<', i).unwrap_or(n),
            Some(el) => {
                let rx = if el == "script" {
                    &SCRIPT_CLOSE
                } else {
                    &STYLE_CLOSE
                };
                match rx.find_at(raw, i) {
                    Some(m) => m.start(),
                    None => break,
                }
            }
        };
        if i < j {
            if cdata.is_none() {
                sink.data(&unescape(&raw[i..j]));
            } else {
                sink.data(&raw[i..j]);
            }
        }
        i = j;
        if i == n {
            break;
        }
        let rest = &raw[i..];
        let k: Option<usize> = if b.get(i + 1).is_some_and(u8::is_ascii_alphabetic) {
            parse_starttag(raw, i, sink, &mut cdata)?
        } else if rest.starts_with("</") {
            parse_endtag(raw, i, sink, &mut cdata)
        } else if rest.starts_with("<!--") {
            parse_comment(raw, i)
        } else if rest.starts_with("<?") {
            find_from(raw, '>', i + 2).map(|p| p + 1)
        } else if rest.starts_with("<!") {
            parse_html_declaration(raw, i)?
        } else if i + 1 < n {
            sink.data("<");
            Some(i + 1)
        } else {
            break;
        };
        let k = match k {
            Some(k) => k,
            None => {
                // an incomplete construct at close(): its text is data
                let k = match find_from(raw, '>', i + 1) {
                    Some(p) => p + 1,
                    None => find_from(raw, '<', i + 1).unwrap_or(i + 1),
                };
                if cdata.is_none() {
                    sink.data(&unescape(&raw[i..k]));
                } else {
                    sink.data(&raw[i..k]);
                }
                k
            }
        };
        i = k;
    }
    if i < n && cdata.is_none() {
        sink.data(&unescape(&raw[i..n]));
    }
    Ok(())
}

fn check_for_whole_start_tag(raw: &str, i: usize) -> Option<usize> {
    let m = LOCATE
        .find(&raw[i..])
        .ok()
        .flatten()
        .expect("we should not get here!");
    let j = i + m.end();
    let next = raw[j..].chars().next();
    match next {
        Some('>') => Some(j + 1),
        Some('/') => raw[j..].starts_with("/>").then_some(j + 2),
        None => None,
        Some(c) if c.is_ascii_alphabetic() || c == '=' => None,
        Some(_) => Some(if j > i { j } else { i + 1 }),
    }
}

/// A well-formed start tag scanned by hand: what the tolerant regexes give for
/// it, without their backtracking. Anything unusual (an unclosed quote, `==`,
/// a NUL, a tag that doesn't end in `>` or `/>`) returns None and the regex
/// path decides.
fn fast_starttag(raw: &str, i: usize) -> Option<(String, Attrs, usize, bool)> {
    let b = raw.as_bytes();
    let n = b.len();
    let ws = |p: usize| -> bool { raw[p..].chars().next().is_some_and(py_ws) };
    let ch_len = |p: usize| raw[p..].chars().next().map_or(1, char::len_utf8);
    // tag name: [a-zA-Z][^\t\n\r\f />\x00]*
    let mut p = i + 1;
    let name_start = p;
    p += 1;
    while p < n {
        let c = b[p];
        if matches!(c, b'\t' | b'\n' | b'\r' | 0x0c | b' ' | b'/' | b'>' | 0) {
            break;
        }
        p += ch_len(p);
    }
    if p < n && b[p] == 0 {
        return None;
    }
    let tag = raw[name_start..p].to_lowercase();
    // (?:\s|/(?!>))*
    let skip = |mut p: usize| -> usize {
        while p < n {
            if ws(p) {
                p += ch_len(p);
            } else if b[p] == b'/' && b.get(p + 1) != Some(&b'>') {
                p += 1;
            } else {
                break;
            }
        }
        p
    };
    p = skip(p);
    let mut attrs: Attrs = Vec::new();
    loop {
        if p >= n {
            return None;
        }
        let c = b[p];
        if c == b'>' {
            return Some((tag, attrs, p + 1, false));
        }
        if c == b'/' {
            // skip() stops at '/' only before '>'
            return Some((tag, attrs, p + 2, true));
        }
        // an attribute name needs a quote, space or slash before it
        let prev = raw[..p].chars().next_back();
        if !prev.is_some_and(|c| c == '\'' || c == '"' || c == '/' || py_ws(c)) {
            return None;
        }
        let a0 = p;
        p += ch_len(p);
        while p < n && !ws(p) && !matches!(b[p], b'/' | b'=' | b'>') {
            p += ch_len(p);
        }
        let name = raw[a0..p].to_lowercase();
        // (\s*=+\s*(value))?
        let mut q = p;
        while q < n && ws(q) {
            q += ch_len(q);
        }
        let mut value = None;
        if q < n && b[q] == b'=' {
            q += 1;
            if q < n && b[q] == b'=' {
                return None;
            }
            while q < n && ws(q) {
                q += ch_len(q);
            }
            if q >= n {
                return None;
            }
            let v = if b[q] == b'\'' || b[q] == b'"' {
                let close = raw[q + 1..].find(b[q] as char)? + q + 1;
                let v = &raw[q + 1..close];
                q = close + 1;
                v
            } else {
                let v0 = q;
                while q < n && !ws(q) && b[q] != b'>' {
                    q += ch_len(q);
                }
                &raw[v0..q]
            };
            value = Some(if v.is_empty() {
                String::new()
            } else {
                unescape(v)
            });
            p = q;
        }
        attrs.push((name, value));
        p = skip(p);
    }
}

fn parse_starttag(
    raw: &str,
    i: usize,
    sink: &mut dyn Sink,
    cdata: &mut Option<&'static str>,
) -> Result<Option<usize>, String> {
    if let Some((tag, attrs, endpos, selfclose)) = fast_starttag(raw, i) {
        if selfclose {
            sink.startend(&tag, &attrs)?;
        } else {
            sink.start(&tag, &attrs)?;
            match tag.as_str() {
                "script" => *cdata = Some("script"),
                "style" => *cdata = Some("style"),
                _ => {}
            }
        }
        return Ok(Some(endpos));
    }
    let Some(endpos) = check_for_whole_start_tag(raw, i) else {
        return Ok(None);
    };
    let m = TAGFIND
        .captures(&raw[i + 1..])
        .ok()
        .flatten()
        .expect("unexpected call to parse_starttag()");
    let tag = m[1].to_lowercase();
    let mut k = i + 1 + m.get(0).unwrap().end();
    let head = &raw[..endpos];
    let mut attrs: Attrs = Vec::new();
    while k < endpos {
        let Some(c) = ATTRFIND.captures_from_pos(head, k).ok().flatten() else {
            break;
        };
        let whole = c.get(0).unwrap();
        if whole.start() != k {
            break;
        }
        let name = c[1].to_lowercase();
        let value = match (c.get(2), c.get(3)) {
            (Some(rest), Some(v)) if !rest.as_str().is_empty() => {
                let v = v.as_str();
                let v = if v.len() >= 2
                    && ((v.starts_with('\'') && v.ends_with('\''))
                        || (v.starts_with('"') && v.ends_with('"')))
                {
                    &v[1..v.len() - 1]
                } else {
                    v
                };
                Some(if v.is_empty() {
                    String::new()
                } else {
                    unescape(v)
                })
            }
            _ => None,
        };
        attrs.push((name, value));
        k = whole.end();
    }
    let end = py_strip(&raw[k..endpos]);
    if end != ">" && end != "/>" {
        sink.data(&raw[i..endpos]);
        return Ok(Some(endpos));
    }
    if end.ends_with("/>") {
        sink.startend(&tag, &attrs)?;
    } else {
        sink.start(&tag, &attrs)?;
        match tag.as_str() {
            "script" => *cdata = Some("script"),
            "style" => *cdata = Some("style"),
            _ => {}
        }
    }
    Ok(Some(endpos))
}

fn parse_endtag(
    raw: &str,
    i: usize,
    sink: &mut dyn Sink,
    cdata: &mut Option<&'static str>,
) -> Option<usize> {
    let gtpos = find_from(raw, '>', i + 1)? + 1;
    match ENDTAGFIND.captures(&raw[i..]) {
        None => {
            if cdata.is_some() {
                sink.data(&raw[i..gtpos]);
                return Some(gtpos);
            }
            match TAGFIND.captures(&raw[i + 2..]).ok().flatten() {
                None => {
                    if raw[i..].starts_with("</>") {
                        Some(i + 3)
                    } else {
                        find_from(raw, '>', i + 2).map(|p| p + 1)
                    }
                }
                Some(nm) => {
                    let name = nm[1].to_lowercase();
                    let after = i + 2 + nm.get(0).unwrap().end();
                    let gt = find_from(raw, '>', after);
                    sink.end(&name);
                    // Python: find() of -1 plus one
                    Some(gt.map_or(0, |p| p + 1))
                }
            }
        }
        Some(m) => {
            let elem = m[1].to_lowercase();
            if let Some(el) = *cdata
                && elem != el
            {
                sink.data(&raw[i..gtpos]);
                return Some(gtpos);
            }
            sink.end(&elem);
            *cdata = None;
            Some(gtpos)
        }
    }
}

fn parse_comment(raw: &str, i: usize) -> Option<usize> {
    COMMENTCLOSE.find_at(raw, i + 4).map(|m| m.end())
}

fn parse_html_declaration(raw: &str, i: usize) -> Result<Option<usize>, String> {
    let rest = &raw[i..];
    if rest.starts_with("<!--") {
        return Ok(parse_comment(raw, i));
    }
    if rest.starts_with("<![") {
        return parse_marked_section(raw, i);
    }
    let head: String = rest.chars().take(9).collect();
    if head.to_lowercase() == "<!doctype" {
        return Ok(find_from(raw, '>', i + 9).map(|p| p + 1));
    }
    Ok(find_from(raw, '>', i + 2).map(|p| p + 1))
}

fn parse_marked_section(raw: &str, i: usize) -> Result<Option<usize>, String> {
    let at = i + 3;
    if at == raw.len() {
        return Ok(None);
    }
    let Some(m) = DECLNAME.find(&raw[at..]) else {
        return Err("expected name token in marked section".into());
    };
    if at + m.end() == raw.len() {
        return Ok(None);
    }
    let name = m.as_str().trim_matches(py_ws).to_lowercase();
    let rx = match name.as_str() {
        "temp" | "cdata" | "ignore" | "include" | "rcdata" => &MARKED_CLOSE,
        "if" | "else" | "endif" => &MS_MARKED_CLOSE,
        _ => return Err(format!("unknown status keyword {name:?} in marked section")),
    };
    Ok(rx.find_at(raw, at).map(|m| m.end()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unescape_matches_python() {
        assert_eq!(
            unescape("a&amp;b &nbsp;&#160;&#x2019;"),
            "a&b \u{a0}\u{a0}\u{2019}"
        );
        assert_eq!(unescape("&#150;"), "\u{2013}");
        assert_eq!(unescape("&ampx &notit; &zz;"), "&x \u{ac}it; &zz;");
        assert_eq!(unescape("&#0; &#xD800; &#1;"), "\u{FFFD} \u{FFFD} ");
    }
}
