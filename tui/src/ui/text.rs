// Small text helpers shared by the components: display-width aware
// truncation / wrapping, URL shortening for the source bar, and number
// formatting for chart values. Pure functions, no styling.

use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

/// Terminal display width of `s` (CJK / emoji count as 2).
pub fn width(s: &str) -> usize {
    UnicodeWidthStr::width(s)
}

/// `s` cut to at most `max` columns, ending in `…` when anything was cut.
pub fn truncate(s: &str, max: usize) -> String {
    if width(s) <= max {
        return s.to_string();
    }
    if max == 0 {
        return String::new();
    }
    let mut out = String::new();
    let mut w = 0;
    for c in s.chars() {
        let cw = c.width().unwrap_or(0);
        // leave one column for the ellipsis
        if w + cw > max - 1 {
            break;
        }
        out.push(c);
        w += cw;
    }
    out.push('…');
    out
}

/// Word-wrap `s` to `max` columns (at least 1). Always returns >= 1 line.
pub fn wrap(s: &str, max: usize) -> Vec<String> {
    let lines: Vec<String> = s
        .lines()
        .flat_map(|l| {
            if l.trim().is_empty() {
                vec![String::new()]
            } else {
                textwrap::wrap(l, max.max(1))
                    .into_iter()
                    .map(|c| c.into_owned())
                    .collect()
            }
        })
        .collect();
    if lines.is_empty() {
        vec![String::new()]
    } else {
        lines
    }
}

/// Pad (or truncate) `s` to exactly `w` columns; right-aligned when `right`.
pub fn fit(s: &str, w: usize, right: bool) -> String {
    let t = truncate(s, w);
    let pad = " ".repeat(w.saturating_sub(width(&t)));
    if right {
        format!("{pad}{t}")
    } else {
        format!("{t}{pad}")
    }
}

/// "https://www.sec.gov/Archives/edgar/data/1/2/mrvl-10q.htm#:~:text=x"
///   -> "sec.gov/…/mrvl-10q.htm"
/// Handles the EDGAR inline viewer form (`/ix?doc=/Archives/...`).
pub fn short_url(url: &str) -> String {
    let u = url.split("#").next().unwrap_or(url);
    let u = u.split_once("://").map_or(u, |(_, rest)| rest);
    let (path, query) = u.split_once('?').unwrap_or((u, ""));
    let mut segs = path.split('/').filter(|s| !s.is_empty());
    let host = segs.next().unwrap_or("").trim_start_matches("www.");
    let mut rest: Vec<&str> = segs.collect();
    // `ix?doc=/Archives/.../x.htm`: the document is in the query string
    if let Some(doc) = query.split('&').find_map(|kv| kv.strip_prefix("doc=")) {
        rest = doc.split('/').filter(|s| !s.is_empty()).collect();
    }
    match rest.as_slice() {
        [] if query.is_empty() => host.to_string(),
        [] => format!("{host}/?{query}"),
        [one] => format!("{host}/{one}"),
        [.., last] => format!("{host}/…/{last}"),
    }
}

/// Compact number: thousands separators, M/B suffix from a million, and
/// precision by magnitude (>= 100: 1 decimal, >= 1: 2, below: 3) with
/// trailing zeros trimmed, so 2739.3 -> "2,739.3", 1.07 -> "1.07", 677 -> "677".
pub fn fmt_num(v: f64) -> String {
    if !v.is_finite() {
        return "–".into();
    }
    let a = v.abs();
    let (x, suf) = if a >= 1e9 {
        (v / 1e9, "B")
    } else if a >= 1e6 {
        (v / 1e6, "M")
    } else {
        (v, "")
    };
    let dec = match x.abs() {
        _ if !suf.is_empty() => 2,
        m if m >= 100.0 => 1,
        m if m >= 1.0 => 2,
        _ => 3,
    };
    let s = format!("{x:.dec$}");
    let s = if s.contains('.') {
        s.trim_end_matches('0').trim_end_matches('.').to_string()
    } else {
        s
    };
    let s = if s == "-0" { "0".to_string() } else { s };
    // thousands separators on the integer part
    let (sign, s) = s.strip_prefix('-').map_or(("", s.as_str()), |r| ("-", r));
    let (int, frac) = s.split_once('.').map_or((s, None), |(i, f)| (i, Some(f)));
    let mut grouped = String::new();
    for (i, c) in int.chars().enumerate() {
        if i > 0 && (int.len() - i) % 3 == 0 {
            grouped.push(',');
        }
        grouped.push(c);
    }
    match frac {
        Some(f) => format!("{sign}{grouped}.{f}{suf}"),
        None => format!("{sign}{grouped}{suf}"),
    }
}

/// `fmt_num` over a column of values with one shared number of decimals,
/// so they line up when right-aligned (1.07 / 1.1 -> 1.07 / 1.10).
/// Columns that use an M/B suffix keep `fmt_num`'s own formatting.
pub fn fmt_nums(vals: &[f64]) -> Vec<String> {
    let base: Vec<String> = vals.iter().map(|&v| fmt_num(v)).collect();
    if vals.iter().any(|v| v.abs() >= 1e6) {
        return base;
    }
    let dec = base
        .iter()
        .filter_map(|s| s.split_once('.').map(|(_, f)| f.len()))
        .max()
        .unwrap_or(0);
    vals.iter()
        .zip(base)
        .map(|(&v, b)| {
            if !v.is_finite() || dec == 0 {
                return b;
            }
            let int = fmt_num(v.trunc()); // thousands separators
            let frac = format!("{:.dec$}", v.abs().fract());
            // rounding can carry (0.999 -> "1.00"): fall back to the plain format
            match frac.strip_prefix("0.") {
                Some(f) => format!(
                    "{}{int}.{f}",
                    if v < 0.0 && v.trunc() == 0.0 { "-" } else { "" }
                ),
                None => format!("{v:.dec$}"),
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn truncates_with_ellipsis() {
        assert_eq!(truncate("hello world", 5), "hell…");
        assert_eq!(truncate("hi", 5), "hi");
        assert_eq!(truncate("hello", 0), "");
        assert_eq!(truncate("hello", 1), "…");
        assert_eq!(fit("ab", 4, true), "  ab");
    }

    #[test]
    fn shortens_urls() {
        assert_eq!(
            short_url("https://www.sec.gov/Archives/edgar/data/1/2/mrvl-10q.htm#:~:text=x"),
            "sec.gov/…/mrvl-10q.htm"
        );
        assert_eq!(
            short_url(
                "https://www.sec.gov/ix?doc=/Archives/edgar/data/1835632/0001/mrvl-20260801.htm"
            ),
            "sec.gov/…/mrvl-20260801.htm"
        );
        assert_eq!(
            short_url("https://patents.google.com/patent/US1"),
            "patents.google.com/…/US1"
        );
        assert_eq!(short_url("https://finance.yahoo.com"), "finance.yahoo.com");
        assert_eq!(short_url(""), "");
    }

    #[test]
    fn formats_numbers() {
        assert_eq!(fmt_num(2739.3), "2,739.3");
        assert_eq!(fmt_num(677.0), "677");
        assert_eq!(fmt_num(-74_320_000.0), "-74.32M");
        assert_eq!(fmt_num(1.07), "1.07");
        assert_eq!(fmt_num(0.745), "0.745");
        assert_eq!(fmt_num(12.2), "12.2");
        assert_eq!(fmt_num(13.0), "13");
        assert_eq!(fmt_num(-0.0001), "0");
        assert_eq!(fmt_num(f64::NAN), "–");
    }

    #[test]
    fn aligned_decimals() {
        assert_eq!(fmt_nums(&[1.07, 1.1, 2.0]), vec!["1.07", "1.10", "2.00"]);
        assert_eq!(fmt_nums(&[1516.1, 677.0]), vec!["1,516.1", "677.0"]);
        assert_eq!(fmt_nums(&[-0.5, 0.25]), vec!["-0.50", "0.25"]);
        assert_eq!(fmt_nums(&[5e6, 1.5]), vec!["5M", "1.5"]);
        assert_eq!(fmt_nums(&[]), Vec::<String>::new());
    }

    #[test]
    fn wraps() {
        assert_eq!(wrap("", 10), vec![String::new()]);
        assert_eq!(wrap("aaa bbb", 3), vec!["aaa", "bbb"]);
    }
}
