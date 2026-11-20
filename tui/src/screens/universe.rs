// AI-universe treemap (ai_universe / ai_universe_category, loaded from
// data/ai_stocks_reviewed.json by db.load_universe). Every basket is a box on
// one plain-ASCII map: its colour is the return over the range (green up, red
// down), its size is its share of the view. Market cap by default; `w` switches
// to equal weights, where every tile gets the same area (five tiles, a fifth
// each) and the map always fills the body. Sub-sectors nest under their
// primary, one treemap per primary with a label row above it. Funds sit outside
// the sector tree; Enter on a fund opens its page: the returns summary on top,
// a map of its top holdings below. Enter on a ticker opens its dossier.
// Prices are the Databento daily bars (parquet beside the DuckDB), with Yahoo
// history as the fallback for funds the bars don't cover.
//
//   hjkl / arrows  move to the neighbouring box      g / G   largest / smallest
//   [ ]            step range preset                  r       edit range (30d, 6m, ytd, 2026-01-01[..2026-03-01])
//   w              cap / equal / exposure weight      H / L   primary / sub / region / funds / favorites
//   enter          drill in, or dossier / fund page   esc     back

use std::collections::HashMap;
use std::io;
use std::path::Path;

use chrono::{Datelike, Months, NaiveDate};
use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, Route, Screen};
use crate::screens::portfolio::data::parse_closes;
use crate::ui::text;
use crate::ui::theme::Theme;

const GROUPS_SQL: &str = "
    SELECT 'primary' AS level, c.category, NULL AS parent, u.ticker, u.name, c.weight,
           coalesce(t.primary_label, c.category) AS label, t.primary_sort AS sort
    FROM ai_universe_category c JOIN ai_universe u USING (ticker)
    LEFT JOIN (SELECT DISTINCT primary_category, primary_label, primary_sort FROM ai_taxonomy) t
      ON t.primary_category = c.category
    WHERE c.level = 'primary' AND u.eligible IS DISTINCT FROM false
    UNION ALL
    SELECT 'sub', c.category, coalesce(t.primary_label, t.primary_category), u.ticker, u.name, c.weight,
           coalesce(t.label, c.category), t.sort
    FROM ai_universe_category c
    JOIN ai_universe u USING (ticker)
    LEFT JOIN ai_taxonomy t ON t.sub_category = c.category
    WHERE c.level = 'sub' AND u.eligible IS DISTINCT FROM false
    UNION ALL
    SELECT 'region', region, NULL, ticker, name, 1.0, region, NULL
    FROM ai_universe WHERE eligible IS DISTINCT FROM false AND region IS NOT NULL
    UNION ALL
    SELECT 'fund', 'funds', NULL, ticker, name, 1.0, 'Funds', NULL
    FROM ai_universe WHERE kind = 'etf' AND eligible IS DISTINCT FROM false
    UNION ALL
    SELECT 'favorites', 'favorites', NULL, ticker, name, 1.0, 'Favorites', NULL
    FROM ai_universe WHERE ticker IN ('NVDA', 'MU', 'SNDK', 'MRVL', 'LITE', '005930.KS', '000660.KS')
      AND eligible IS DISTINCT FROM false";

const NOT_LOADED: &str = "The AI universe isn't loaded into DuckDB yet.\n\n  \
    python -c 'from core import db; db.load_universe()'   (from the repo root)";

const PRESETS: [&str; 8] = ["1d", "1w", "1m", "3m", "6m", "ytd", "1y", "max"];
const LEVELS: [(&str, &str); 5] = [
    ("primary", "Primary"),
    ("sub", "Sub-sector"),
    ("region", "Region"),
    ("fund", "Funds"),
    ("favorites", "Favorites"),
];
/// The fund page's returns summary: name, last close, blank, then one line per preset.
const FUND_SUMMARY_H: u16 = 3 + PRESETS.len() as u16;
const NO_HOLDINGS: &str = "No fund holdings loaded yet.\n\n  \
    uv run sources/yahoo.py universe holdings   (from py/)";
/// How much of an unselected tile's colour survives.
const DIM: f64 = 0.55;
/// The smallest box a tile gets, in cells, so a tiny weight still shows its label.
const MIN_CELLS: f64 = 12.0;
/// A terminal cell is about twice as tall as it is wide: the layout works in square units.
const CELL_ASPECT: f64 = 2.0;

#[derive(Debug, Clone)]
struct Member {
    ticker: String,
    name: String,
    weight: f64,
}

#[derive(Debug, Clone)]
struct Group {
    level: String,
    name: String,
    /// Display label (the taxonomy label for primary/sub, the key for regions).
    label: String,
    /// Stack order from the taxonomy; ties between equal sizes break on it.
    order: i32,
    parent: Option<String>,
    members: Vec<Member>,
}

/// One box on the map: a basket or a ticker, with its return over the range.
struct Tile {
    title: String,
    sub: String,
    order: i32,
    ret: Option<f64>,
    value: String,
    /// Share of the view: market cap, equal (1 per tile) or category weight.
    weight: f64,
    /// Nested view: the primary this sub-sector sits under.
    parent: Option<String>,
}

/// A filled box on the map: its cells inside the separators, and what it shows.
enum Plate {
    /// A tile, by its index in `tiles`.
    Tile(Rect, usize),
    /// A primary's label row above its sub-sector tiles: name and its return.
    Label(Rect, String, Option<f64>),
}

/// How members weigh in a basket's return and in the map. `w` cycles.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Weighting {
    /// Market cap in USD (the default): real size.
    Cap,
    /// Every tile the same size.
    Equal,
    /// The category weight from the taxonomy: how much of a name is in the bucket.
    Exposure,
}

impl Weighting {
    fn next(self) -> Self {
        match self {
            Weighting::Cap => Weighting::Equal,
            Weighting::Equal => Weighting::Exposure,
            Weighting::Exposure => Weighting::Cap,
        }
    }

    fn label(self) -> &'static str {
        match self {
            Weighting::Cap => "cap-wt ",
            Weighting::Equal => "equal-wt ",
            Weighting::Exposure => "exposure-wt ",
        }
    }
}

#[derive(PartialEq)]
enum View {
    Groups,
    Members(usize),
    /// One fund's returns page, by ticker.
    Fund(String),
}

pub struct Universe {
    theme: Theme,
    groups: Vec<Group>,
    returns: HashMap<String, f64>,
    /// Daily closes per fund (bars, else Yahoo history), oldest first.
    fund_series: HashMap<String, Vec<(NaiveDate, f64)>>,
    /// Top holdings per fund, heaviest first.
    holdings: HashMap<String, Vec<Member>>,
    db_path: std::path::PathBuf,
    spec: String,
    from: NaiveDate,
    to: NaiveDate,
    latest: NaiveDate,
    weighting: Weighting,
    /// Market cap in USD per universe name, from `ai_market_cap`.
    caps: HashMap<String, f64>,
    level: usize,
    view: View,
    tiles: Vec<Tile>,
    sel: usize,
    editing: Option<String>,
    flash: String,
    /// The map's body as last drawn; cursor moves read its geometry.
    body: Rect,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Universe> {
    let mut u = Universe {
        theme: ctx.theme,
        groups: Vec::new(),
        returns: HashMap::new(),
        fund_series: HashMap::new(),
        holdings: HashMap::new(),
        db_path: ctx.db_path.clone(),
        spec: "1m".into(),
        from: NaiveDate::MIN,
        to: NaiveDate::MIN,
        latest: NaiveDate::MIN,
        weighting: Weighting::Cap,
        caps: HashMap::new(),
        level: 0,
        view: View::Groups,
        tiles: Vec::new(),
        sel: 0,
        editing: None,
        flash: String::new(),
        body: Rect::default(),
    };
    match load_groups(ctx) {
        Ok(g) => u.groups = g,
        Err(e) => u.flash = e,
    }
    let funds: Vec<String> = u
        .groups
        .iter()
        .filter(|g| g.level == "fund")
        .flat_map(|g| g.members.iter().map(|m| m.ticker.clone()))
        .collect();
    match load_fund_series(&u.db_path, &funds) {
        Ok(s) => u.fund_series = s,
        Err(e) => u.flash = e,
    }
    match load_holdings(&u.db_path) {
        Ok(h) => u.holdings = h,
        Err(e) => u.flash = e,
    }
    // Without the latest bar date there is no range to price against; keep
    // its error on screen rather than letting the range step overwrite it.
    match latest_bar(&u.db_path) {
        Ok(d) => {
            u.latest = d;
            u.apply_spec("1m");
        }
        Err(e) => u.flash = e,
    }
    // "level|category" opens that basket's members directly.
    if let Some((level, cat)) = arg.as_deref().and_then(|a| a.split_once('|')) {
        if let Some(i) = u
            .groups
            .iter()
            .position(|g| g.level == level && g.name == cat)
        {
            u.level = LEVELS.iter().position(|(l, _)| *l == level).unwrap_or(0);
            u.view = View::Members(i);
        }
    }
    match load_caps(&u.db_path) {
        Ok(c) => u.caps = c,
        Err(e) => {
            // No sizes yet: fall back to equal weights rather than a map of slivers.
            u.weighting = Weighting::Equal;
            u.flash = e;
        }
    }
    u.rebuild();
    Ok(u)
}

/// Market cap in USD per name, from the `ai_market_cap` table that
/// py/sources/market_caps.py writes.
fn load_caps(db_path: &Path) -> Result<HashMap<String, f64>, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let mut stmt = conn
        .prepare("SELECT ticker, market_cap_usd FROM ai_market_cap WHERE market_cap_usd > 0")
        .map_err(|e| format!("no market caps ({e}). Run py/sources/market_caps.py."))?;
    let rows = stmt
        .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, f64>(1)?)))
        .map_err(|e| e.to_string())?;
    Ok(rows.flatten().collect())
}

/// The Parquet glob of one Databento bar table (bars_1d, bars_1m, ...) beside the DuckDB.
pub fn bars_glob_for(db_path: &Path, table: &str) -> String {
    let root = db_path.parent().unwrap_or(Path::new(".")).join("finlarp");
    format!("{}/market/databento/{table}/*.parquet", root.display())
}

fn with_load<T>(
    ctx: &Ctx,
    f: impl Fn(&duckdb::Connection) -> Result<Vec<T>, String>,
) -> Result<Vec<T>, String> {
    let read = |ctx: &Ctx| f(&crate::db::open_read_only(&ctx.db_path)?);
    if let Ok(rows) = read(ctx)
        && !rows.is_empty()
    {
        return Ok(rows);
    }
    crate::pyrun::run_code("from core import db; db.load_universe()")?;
    let rows = read(ctx)?;
    if rows.is_empty() {
        Err(NOT_LOADED.to_string())
    } else {
        Ok(rows)
    }
}

fn load_groups(ctx: &Ctx) -> Result<Vec<Group>, String> {
    let rows = with_load(ctx, |conn| {
        let mut stmt = conn.prepare(GROUPS_SQL).map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map([], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, Option<String>>(2)?,
                    r.get::<_, String>(3)?,
                    r.get::<_, Option<String>>(4)?,
                    r.get::<_, Option<f64>>(5)?,
                    r.get::<_, Option<String>>(6)?,
                    r.get::<_, Option<i32>>(7)?,
                ))
            })
            .map_err(|e| e.to_string())?;
        Ok(rows.flatten().collect())
    })?;
    let mut groups: Vec<Group> = Vec::new();
    let mut index: HashMap<(String, String), usize> = HashMap::new();
    for (level, name, parent, ticker, tname, weight, label, order) in rows {
        let i = *index
            .entry((level.clone(), name.clone()))
            .or_insert_with(|| {
                groups.push(Group {
                    level: level.clone(),
                    label: label.unwrap_or_else(|| name.clone()),
                    order: order.unwrap_or(i32::MAX),
                    name: name.clone(),
                    parent,
                    members: Vec::new(),
                });
                groups.len() - 1
            });
        groups[i].members.push(Member {
            ticker,
            name: tname.unwrap_or_default(),
            weight: weight.unwrap_or(1.0).max(0.0),
        });
    }
    Ok(groups)
}

fn latest_bar(db_path: &Path) -> Result<NaiveDate, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let s: Option<String> = conn
        .query_row(
            "SELECT CAST(max((ts_event AT TIME ZONE 'UTC')::DATE) AS VARCHAR) FROM bars_1d_adj",
            [],
            |r| r.get(0),
        )
        .map_err(|e| format!("no daily bars ({e}). Run the databento bars_1d pull."))?;
    s.and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok())
        .ok_or_else(|| "no daily bars. Run the databento bars_1d pull.".to_string())
}

/// Top holdings per fund, heaviest first. Errors (no table yet) come back as a
/// hint to run the holdings pull.
fn load_holdings(db_path: &Path) -> Result<HashMap<String, Vec<Member>>, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let mut stmt = conn
        .prepare(
            "SELECT fund, ticker, coalesce(name, ticker), weight FROM fund_holdings \
             ORDER BY fund, weight DESC",
        )
        .map_err(|_| NO_HOLDINGS.to_string())?;
    let rows = stmt
        .query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, f64>(3)?,
            ))
        })
        .map_err(|e| e.to_string())?;
    let mut out: HashMap<String, Vec<Member>> = HashMap::new();
    for (fund, ticker, name, weight) in rows.flatten() {
        out.entry(fund).or_default().push(Member {
            ticker,
            name,
            weight: weight.max(0.0),
        });
    }
    Ok(out)
}

/// Return per ticker between `from` and `to`: last close on/before `to`
/// against the last close on/before `from` (first close in the window for
/// names that listed after `from`). `extra` adds tickers beyond the universe,
/// such as fund holdings.
fn load_returns(
    db_path: &Path,
    from: NaiveDate,
    to: NaiveDate,
    extra: &[String],
) -> Result<HashMap<String, f64>, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let extra = match sql_list(extra) {
        list if list.is_empty() => String::new(),
        list => format!(" OR symbol IN ({list})"),
    };
    let sql = format!(
        "WITH b AS (
            SELECT symbol, (ts_event AT TIME ZONE 'UTC')::DATE AS d, close
            FROM bars_1d_adj
            WHERE close > 0 AND (symbol IN (SELECT ticker FROM ai_universe){extra})
         )
         SELECT symbol,
                arg_max(close, d) FILTER (WHERE d <= CAST(? AS DATE)) AS last,
                coalesce(arg_max(close, d) FILTER (WHERE d <= CAST(? AS DATE)),
                         arg_min(close, d) FILTER (WHERE d > CAST(? AS DATE))) AS base
         FROM b GROUP BY symbol"
    );
    let (f, t) = (from.to_string(), to.to_string());
    let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([&t, &f, &f], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, Option<f64>>(1)?,
                r.get::<_, Option<f64>>(2)?,
            ))
        })
        .map_err(|e| e.to_string())?;
    Ok(rows
        .flatten()
        .filter_map(|(s, last, base)| match (last, base) {
            (Some(l), Some(b)) if b > 0.0 => Some((s, (l / b - 1.0) * 100.0)),
            _ => None,
        })
        .collect())
}

/// `'A','B'` for an IN list, quotes escaped.
fn sql_list(xs: &[String]) -> String {
    xs.iter()
        .map(|t| format!("'{}'", t.replace('\'', "''")))
        .collect::<Vec<_>>()
        .join(",")
}

/// Daily closes for each fund, oldest first: the Databento bars, or the Yahoo
/// daily history when the bars have none (SOXX, say).
fn load_fund_series(
    db_path: &Path,
    tickers: &[String],
) -> Result<HashMap<String, Vec<(NaiveDate, f64)>>, String> {
    let mut out: HashMap<String, Vec<(NaiveDate, f64)>> = HashMap::new();
    if tickers.is_empty() {
        return Ok(out);
    }
    let conn = crate::db::open_read_only(db_path)?;
    let sql = format!(
        "SELECT symbol, CAST((ts_event AT TIME ZONE 'UTC')::DATE AS VARCHAR), close \
         FROM bars_1d_adj \
         WHERE close > 0 AND symbol IN ({}) ORDER BY symbol, ts_event",
        sql_list(tickers)
    );
    // No bars pull yet is not an error here: the Yahoo history below still covers the funds.
    if let Ok(mut stmt) = conn.prepare(&sql)
        && let Ok(rows) = stmt.query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, f64>(2)?,
            ))
        })
    {
        for (sym, day, close) in rows.flatten() {
            if let Ok(d) = NaiveDate::parse_from_str(&day, "%Y-%m-%d") {
                out.entry(sym).or_default().push((d, close));
            }
        }
    }
    for v in out.values_mut() {
        v.dedup_by_key(|(d, _)| *d);
    }

    let missing: Vec<String> = tickers
        .iter()
        .filter(|t| out.get(*t).is_none_or(|v| v.is_empty()))
        .cloned()
        .collect();
    if !missing.is_empty() {
        let sql = format!(
            "SELECT symbol, points_json FROM history_cache WHERE interval = '1d' AND symbol IN ({}) \
             QUALIFY row_number() OVER (PARTITION BY symbol ORDER BY length(points_json) DESC) = 1",
            sql_list(&missing)
        );
        let mut stmt = conn.prepare(&sql).map_err(|e| e.to_string())?;
        let rows = stmt
            .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))
            .map_err(|e| e.to_string())?;
        for (sym, json) in rows.flatten() {
            out.insert(sym, parse_closes(&json));
        }
    }
    Ok(out)
}

/// Return over [from, to] for one daily series: the last close on or before
/// `to` against the last close on or before `from` (the first close after
/// `from` when the series starts later). Returns the percent and the base date.
fn span_return(
    series: &[(NaiveDate, f64)],
    from: NaiveDate,
    to: NaiveDate,
) -> Option<(f64, NaiveDate)> {
    let (_, last) = series.iter().rev().find(|(d, _)| *d <= to)?;
    let (base_day, base) = series
        .iter()
        .rev()
        .find(|(d, _)| *d <= from)
        .or_else(|| series.iter().find(|(d, _)| *d > from))?;
    (*base > 0.0).then(|| ((last / base - 1.0) * 100.0, *base_day))
}

/// "30d" / "6m" / "1y" / "ytd" / "max" / "2026-01-01" / "2026-01-01..2026-03-01"
/// -> (from, to), relative to the latest bar.
fn parse_range(spec: &str, latest: NaiveDate) -> Option<(NaiveDate, NaiveDate)> {
    let s = spec.trim().to_lowercase();
    if s.is_empty() {
        return None;
    }
    if let Some((a, b)) = s.split_once("..").or_else(|| s.split_once(' ')) {
        let a = NaiveDate::parse_from_str(a.trim(), "%Y-%m-%d").ok()?;
        let b = NaiveDate::parse_from_str(b.trim(), "%Y-%m-%d").ok()?;
        return (a < b).then_some((a, b));
    }
    if let Ok(d) = NaiveDate::parse_from_str(&s, "%Y-%m-%d") {
        return (d < latest).then_some((d, latest));
    }
    match s.as_str() {
        "ytd" => return NaiveDate::from_ymd_opt(latest.year() - 1, 12, 31).map(|d| (d, latest)),
        "max" => return Some((NaiveDate::from_ymd_opt(2000, 1, 1)?, latest)),
        _ => {}
    }
    let (n, unit) = s.split_at(s.len().checked_sub(1)?);
    let n: u32 = n.parse().ok().filter(|n| *n > 0)?;
    let from = match unit {
        "d" => latest.checked_sub_days(chrono::Days::new(n.into()))?,
        "w" => latest.checked_sub_days(chrono::Days::new(u64::from(n) * 7))?,
        "m" => latest.checked_sub_months(Months::new(n))?,
        "y" => latest.checked_sub_months(Months::new(n * 12))?,
        _ => return None,
    };
    Some((from, latest))
}

/// Blend `a` toward `b` by t in 0..=1 (RGB only; named colours pass through).
pub(crate) fn mix(a: Color, b: Color, t: f64) -> Color {
    let rgb = |c: Color| match c {
        Color::Rgb(r, g, b) => Some((r as f64, g as f64, b as f64)),
        Color::Black => Some((0.0, 0.0, 0.0)),
        Color::White => Some((255.0, 255.0, 255.0)),
        _ => None,
    };
    match (rgb(a), rgb(b)) {
        (Some(x), Some(y)) => {
            let m = |p: f64, q: f64| (p + (q - p) * t).round().clamp(0.0, 255.0) as u8;
            Color::Rgb(m(x.0, y.0), m(x.1, y.1), m(x.2, y.2))
        }
        _ => b,
    }
}

/// Drops corporate suffixes ("Inc", "Corp.", "Holdings") that eat tile width.
fn short_name(name: &str) -> String {
    const SUFFIX: [&str; 12] = [
        "inc",
        "inc.",
        "corp",
        "corp.",
        "corporation",
        "co",
        "co.",
        "ltd",
        "ltd.",
        "plc",
        "holdings",
        "limited",
    ];
    let mut words: Vec<&str> = name.split_whitespace().collect();
    while words.len() > 1
        && words
            .last()
            .is_some_and(|w| SUFFIX.contains(&w.trim_end_matches(',').to_lowercase().as_str()))
    {
        words.pop();
    }
    words.join(" ").trim_end_matches(',').to_string()
}

/// Share of a fund the loaded holdings cover (Yahoo lists the top 10 only).
fn covered(members: &[Member]) -> f64 {
    members.iter().map(|m| m.weight).sum()
}

/// Splits at a word boundary: the longest prefix within `width` columns, and
/// the remainder. A first word wider than `width` goes wholly to the remainder.
fn split_words(s: &str, width: usize) -> (String, String) {
    let mut head = String::new();
    let mut words = s.split_whitespace().peekable();
    while let Some(w) = words.peek() {
        let next = if head.is_empty() {
            w.to_string()
        } else {
            format!("{head} {w}")
        };
        if text::width(&next) > width {
            break;
        }
        head = next;
        words.next();
    }
    (head, words.collect::<Vec<_>>().join(" "))
}

/// Shares of the whole for `weights` (they sum to 1), each at least `min`. Items under the floor
/// take the floor; the rest split what is left in proportion to their weights. Zero weights
/// everywhere make every item equal.
fn shares(weights: &[f64], min: f64) -> Vec<f64> {
    let n = weights.len();
    let mut w: Vec<f64> = weights
        .iter()
        .map(|x| if x.is_finite() { x.max(0.0) } else { 0.0 })
        .collect();
    if w.iter().sum::<f64>() <= 0.0 {
        w = vec![1.0; n];
    }
    let min = min.min(1.0 / n as f64);
    let mut fixed = vec![false; n];
    loop {
        let n_fixed = fixed.iter().filter(|f| **f).count();
        let free_total = 1.0 - min * n_fixed as f64;
        let free_sum: f64 = (0..n).filter(|&i| !fixed[i]).map(|i| w[i]).sum();
        let mut grew = false;
        for i in 0..n {
            if !fixed[i] && free_sum > 0.0 && w[i] / free_sum * free_total < min {
                fixed[i] = true;
                grew = true;
            }
        }
        if !grew {
            return (0..n)
                .map(|i| {
                    if fixed[i] {
                        min
                    } else {
                        w[i] / free_sum * free_total
                    }
                })
                .collect();
        }
    }
}

/// Squarified treemap (Bruls, Huizing and van Wijk): `areas` laid into the rectangle (x, y, w, h)
/// as [x, y, w, h] per area, in the order given. The areas must sum to w * h.
fn squarify(areas: &[f64], x: f64, y: f64, w: f64, h: f64) -> Vec<[f64; 4]> {
    let mut order: Vec<usize> = (0..areas.len()).collect();
    order.sort_by(|&a, &b| areas[b].total_cmp(&areas[a]));
    let mut out = vec![[0.0; 4]; areas.len()];
    let mut free = [x, y, w, h];
    let mut row: Vec<usize> = Vec::new();
    for &next in &order {
        let side = free[2].min(free[3]);
        let mut with = row.clone();
        with.push(next);
        if row.is_empty() || worst(areas, &with, side) <= worst(areas, &row, side) {
            row = with;
        } else {
            lay_row(areas, &row, &mut out, &mut free);
            row = vec![next];
        }
    }
    if !row.is_empty() {
        lay_row(areas, &row, &mut out, &mut free);
    }
    out
}

/// The worst aspect ratio of `row` laid along a side of length `side` (lower is squarer).
fn worst(areas: &[f64], row: &[usize], side: f64) -> f64 {
    let s: f64 = row.iter().map(|&i| areas[i]).sum();
    let mx = row.iter().map(|&i| areas[i]).fold(0.0, f64::max);
    let mn = row.iter().map(|&i| areas[i]).fold(f64::MAX, f64::min);
    if s <= 0.0 || mn <= 0.0 || side <= 0.0 {
        return f64::MAX;
    }
    let (s2, w2) = (s * s, side * side);
    (w2 * mx / s2).max(s2 / (w2 * mn))
}

/// Lays a finished row along the short side of the free rectangle, then shrinks the free part.
fn lay_row(areas: &[f64], row: &[usize], out: &mut [[f64; 4]], free: &mut [f64; 4]) {
    let [x, y, w, h] = *free;
    let (w, h) = (w.max(1e-9), h.max(1e-9));
    let s: f64 = row.iter().map(|&i| areas[i]).sum();
    if w >= h {
        // A column down the left side, as tall as the free part.
        let cw = s / h;
        let mut top = y;
        for &i in row {
            let ch = areas[i] / cw;
            out[i] = [x, top, cw, ch];
            top += ch;
        }
        *free = [x + cw, y, w - cw, h];
    } else {
        // A strip across the top, as wide as the free part.
        let rh = s / w;
        let mut left = x;
        for &i in row {
            let rw = areas[i] / rh;
            out[i] = [left, y, rw, rh];
            left += rw;
        }
        *free = [x, y + rh, w, h - rh];
    }
}

/// Tiles `area` with one box per weight, in the order given. The boxes share their edges and
/// cover `area` exactly, so the map is always full. Each box is at least MIN_CELLS however small
/// its weight, so a tiny name still shows its label.
fn treemap(area: Rect, weights: &[f64]) -> Vec<Rect> {
    if area.width == 0 || area.height == 0 || weights.is_empty() {
        return vec![Rect::default(); weights.len()];
    }
    let cells = f64::from(area.width) * f64::from(area.height);
    let floor = (MIN_CELLS / cells).min(1.0 / weights.len() as f64);
    // Square units: one cell is 1 wide and CELL_ASPECT tall.
    let (w, h) = (f64::from(area.width), f64::from(area.height) * CELL_ASPECT);
    let areas: Vec<f64> = shares(weights, floor).iter().map(|s| s * w * h).collect();
    squarify(&areas, 0.0, 0.0, w, h)
        .iter()
        .map(|&[x, y, bw, bh]| {
            // Edges round once, so neighbours meet with no gap and no overlap.
            let (x0, x1) = (x.round(), (x + bw).round());
            let (y0, y1) = ((y / CELL_ASPECT).round(), ((y + bh) / CELL_ASPECT).round());
            Rect::new(
                area.x + x0 as u16,
                area.y + y0 as u16,
                (x1 - x0).max(0.0) as u16,
                (y1 - y0).max(0.0) as u16,
            )
        })
        .collect()
}

/// A box's cells inside its separators: the right column and bottom row are the gap to the next
/// box, unless the box reaches the edge of `outer`.
fn trim(b: Rect, outer: Rect) -> Rect {
    let right = u16::from(b.right() < outer.right());
    let bottom = u16::from(b.bottom() < outer.bottom());
    Rect::new(
        b.x,
        b.y,
        b.width.saturating_sub(right),
        b.height.saturating_sub(bottom),
    )
}

/// Weighted mean return of the tiles that have one.
fn wavg<'a>(tiles: impl Iterator<Item = &'a Tile>) -> Option<f64> {
    let (mut num, mut den) = (0.0, 0.0);
    for t in tiles {
        if let Some(r) = t.ret {
            num += t.weight * r;
            den += t.weight;
        }
    }
    (den > 0.0).then(|| num / den)
}

/// `s` as plain ASCII, cut to `max` columns; a cut ends in "..".
fn fit(s: &str, max: usize) -> String {
    let s: String = s
        .chars()
        .map(|c| if c.is_ascii() { c } else { '?' })
        .collect();
    if s.len() <= max {
        return s;
    }
    if max <= 2 {
        return s.chars().take(max).collect();
    }
    format!("{}..", &s[..max - 2])
}

impl Universe {
    fn apply_spec(&mut self, spec: &str) -> bool {
        match parse_range(spec, self.latest) {
            Some((from, to)) => {
                self.spec = spec.trim().to_lowercase();
                self.from = from;
                self.to = to;
                let held: Vec<String> = self
                    .holdings
                    .values()
                    .flatten()
                    .map(|m| m.ticker.clone())
                    .collect();
                match load_returns(&self.db_path, from, to, &held) {
                    Ok(r) => {
                        self.returns = r;
                        self.flash.clear();
                    }
                    Err(e) => self.flash = e,
                }
                true
            }
            None => {
                self.flash = format!("bad range {spec:?}: try 30d, 6m, ytd, 2026-01-01 or a..b");
                false
            }
        }
    }

    /// One name's return over the range. Funds come from their own daily
    /// series, so the Yahoo fallback counts; everything else from the bars pull.
    fn ret_of(&self, ticker: &str) -> Option<f64> {
        match self.fund_series.get(ticker) {
            Some(s) => span_return(s, self.from, self.to).map(|(r, _)| r),
            None => self.returns.get(ticker).copied(),
        }
    }

    /// A member's share in a basket under the current weighting. A name with
    /// no market cap counts for nothing under cap weighting rather than a guess.
    fn weight_of(&self, m: &Member) -> f64 {
        match self.weighting {
            Weighting::Cap => self.caps.get(&m.ticker).copied().unwrap_or(0.0),
            Weighting::Equal => 1.0,
            Weighting::Exposure => m.weight,
        }
    }

    /// A basket's share of the view. Equal weighting counts every basket as one tile, so the
    /// tiles split the map evenly; otherwise it is the priced members' weights.
    fn group_weight(&self, g: &Group) -> f64 {
        match self.weighting {
            Weighting::Equal => 1.0,
            _ => g
                .members
                .iter()
                .filter(|m| self.ret_of(&m.ticker).is_some())
                .map(|m| self.weight_of(m))
                .sum(),
        }
    }

    fn member_tile(&self, m: &Member) -> Tile {
        Tile {
            title: m.ticker.clone(),
            sub: m.name.clone(),
            order: 0,
            ret: self.ret_of(&m.ticker),
            value: m.ticker.clone(),
            weight: self.weight_of(m),
            parent: None,
        }
    }

    /// A holding's tile: its weight in the fund sits in the subline. The
    /// map uses the fund's own weights (already real) unless equal-weighted.
    fn holding_tile(&self, m: &Member) -> Tile {
        Tile {
            sub: format!("{:.1}% {}", m.weight * 100.0, m.name),
            weight: if self.weighting == Weighting::Equal {
                1.0
            } else {
                m.weight
            },
            ..self.member_tile(m)
        }
    }

    fn open_fund(&mut self, ticker: String) {
        self.view = View::Fund(ticker);
        self.sel = 0;
        self.rebuild();
    }

    /// Basket return: equal-weight mean, or category-weight weighted, over
    /// members that have prices. (return, members priced)
    fn basket(&self, g: &Group) -> (Option<f64>, usize) {
        let (mut num, mut den, mut n) = (0.0, 0.0, 0);
        for m in &g.members {
            if let Some(r) = self.ret_of(&m.ticker) {
                let w = self.weight_of(m);
                num += w * r;
                den += w;
                n += 1;
            }
        }
        ((den > 0.0).then(|| num / den), n)
    }

    /// Sub-sectors are drawn nested under their primary (the Sub-sector level, at the top).
    fn nested(&self) -> bool {
        matches!(self.view, View::Groups) && LEVELS[self.level].0 == "sub"
    }

    fn rebuild(&mut self) {
        let level = LEVELS[self.level].0;
        let mut tiles: Vec<Tile> = match self.view {
            View::Fund(ref ticker) => self
                .holdings
                .get(ticker)
                .map(|ms| ms.iter().map(|m| self.holding_tile(m)).collect())
                .unwrap_or_default(),
            // Funds have no basket: each fund is its own tile. Favorites are single names,
            // so they show the same way: one tile per ticker.
            View::Groups if level == "fund" || level == "favorites" => self
                .groups
                .iter()
                .filter(|g| g.level == level)
                .flat_map(|g| &g.members)
                .map(|m| self.member_tile(m))
                .collect(),
            View::Groups => self
                .groups
                .iter()
                .enumerate()
                .filter(|(_, g)| g.level == level)
                .map(|(i, g)| {
                    let (ret, n) = self.basket(g);
                    let sub = match &g.parent {
                        Some(p) => format!("{p} - {n}"),
                        None => format!("{n}/{} priced", g.members.len()),
                    };
                    Tile {
                        title: g.label.clone(),
                        order: g.order,
                        sub,
                        ret,
                        value: i.to_string(),
                        weight: self.group_weight(g),
                        parent: g.parent.clone(),
                    }
                })
                .collect(),
            View::Members(i) => self.groups[i]
                .members
                .iter()
                .map(|m| self.member_tile(m))
                .collect(),
        };
        if self.nested() {
            // Primaries in taxonomy order; each one's sub-sectors stay together, heaviest first.
            let mut first: HashMap<String, i32> = HashMap::new();
            for t in &tiles {
                let e = first
                    .entry(t.parent.clone().unwrap_or_default())
                    .or_insert(i32::MAX);
                *e = (*e).min(t.order);
            }
            let key = |t: &Tile| t.parent.clone().unwrap_or_default();
            tiles.sort_by(|a, b| {
                first[&key(a)]
                    .cmp(&first[&key(b)])
                    .then_with(|| key(a).cmp(&key(b)))
                    .then_with(|| b.weight.total_cmp(&a.weight))
                    .then_with(|| a.title.cmp(&b.title))
            });
        } else {
            tiles.sort_by(|a, b| {
                b.weight
                    .total_cmp(&a.weight)
                    .then_with(|| a.title.cmp(&b.title))
            });
        }
        self.tiles = tiles;
        self.sel = self.sel.min(self.tiles.len().saturating_sub(1));
    }

    /// A tile's background: heat colour by return. The selected tile keeps full colour; the rest
    /// fade toward the background.
    fn tile_bg(&self, ret: Option<f64>, scale: f64, selected: bool) -> Color {
        let t = self.theme;
        let base = t.bg.unwrap_or(Color::Rgb(0x1e, 0x1e, 0x2e));
        let bg = match ret {
            None => mix(base, t.dim, 0.15),
            Some(r) => {
                let k = (r.abs() / scale).clamp(0.0, 1.0);
                mix(base, if r >= 0.0 { t.up } else { t.down }, 0.10 + 0.30 * k)
            }
        };
        if selected { bg } else { mix(base, bg, DIM) }
    }

    /// Colour scale: 90th percentile of |return| so one outlier doesn't wash out the rest.
    fn colour_scale(&self) -> f64 {
        let mut mags: Vec<f64> = self
            .tiles
            .iter()
            .filter_map(|x| x.ret)
            .map(f64::abs)
            .collect();
        mags.sort_by(f64::total_cmp);
        mags.get(mags.len().saturating_sub(1) * 9 / 10)
            .copied()
            .unwrap_or(1.0)
            .max(1.0)
    }

    /// Where every tile and label sits in `body`. Flat views tile the body with the tiles. The
    /// nested sub-sector view tiles it with the primaries; each primary's box has a label row,
    /// and its sub-sectors tile the rest.
    fn plates(&self, body: Rect) -> Vec<Plate> {
        let mut out = Vec::new();
        if self.nested() {
            let mut parents: Vec<(String, Vec<usize>)> = Vec::new();
            for (i, t) in self.tiles.iter().enumerate() {
                let p = t.parent.clone().unwrap_or_default();
                match parents.last_mut() {
                    Some((name, kids)) if *name == p => kids.push(i),
                    _ => parents.push((p, vec![i])),
                }
            }
            let weights: Vec<f64> = parents
                .iter()
                .map(|(_, kids)| kids.iter().map(|&i| self.tiles[i].weight).sum())
                .collect();
            for ((name, kids), b) in parents.iter().zip(treemap(body, &weights)) {
                let b = trim(b, body);
                if b.width == 0 || b.height == 0 {
                    continue;
                }
                let inner = if b.height >= 3 {
                    let ret = wavg(kids.iter().map(|&i| &self.tiles[i]));
                    out.push(Plate::Label(
                        Rect::new(b.x, b.y, b.width, 1),
                        name.clone(),
                        ret,
                    ));
                    Rect::new(b.x, b.y + 1, b.width, b.height - 1)
                } else {
                    b
                };
                let weights: Vec<f64> = kids.iter().map(|&i| self.tiles[i].weight).collect();
                for (&i, cb) in kids.iter().zip(treemap(inner, &weights)) {
                    let c = trim(cb, inner);
                    if c.width > 0 && c.height > 0 {
                        out.push(Plate::Tile(c, i));
                    }
                }
            }
        } else {
            let weights: Vec<f64> = self.tiles.iter().map(|t| t.weight).collect();
            for (i, b) in treemap(body, &weights).into_iter().enumerate() {
                let c = trim(b, body);
                if c.width > 0 && c.height > 0 {
                    out.push(Plate::Tile(c, i));
                }
            }
        }
        out
    }

    /// The fund page: name, last close, and the return over each range.
    fn draw_fund(&self, frame: &mut Frame, area: Rect, ticker: &str) {
        let t = self.theme;
        let name = self
            .groups
            .iter()
            .flat_map(|g| &g.members)
            .find(|m| m.ticker == ticker)
            .map_or("", |m| m.name.as_str());
        let Some(series) = self.fund_series.get(ticker).filter(|s| !s.is_empty()) else {
            let msg = format!("no daily prices for {ticker} (no bars, no Yahoo history cached)");
            frame.render_widget(Paragraph::new(msg).style(t.dim()), area);
            return;
        };
        let (last_day, last) = series[series.len() - 1];
        let mut lines = vec![
            Line::from(vec![
                Span::styled(format!(" {ticker}  "), t.title()),
                Span::styled(name.to_string(), t.base()),
            ]),
            Line::styled(
                format!(
                    " last ${last:.2} on {last_day} | {} daily closes since {}",
                    series.len(),
                    series[0].0
                ),
                t.dim(),
            ),
            Line::default(),
        ];
        for spec in PRESETS {
            let label = Span::styled(format!(" {spec:<5}"), t.dim());
            let window = parse_range(spec, self.latest);
            let ret = window.and_then(|(f, to)| span_return(series, f, to).map(|x| (x, f)));
            lines.push(match ret {
                Some(((r, base), from)) => {
                    // The history starts after the window: say so, or "1y" reads as the full year.
                    let note = if base > from {
                        format!("   from {base} (history starts there)")
                    } else {
                        format!("   from {base}")
                    };
                    Line::from(vec![
                        label,
                        Span::styled(format!("{r:>+8.1}%"), t.signed(r)),
                        Span::styled(note, t.dim()),
                    ])
                }
                None => Line::from(vec![label, Span::styled("     n/a", t.dim())]),
            });
        }
        frame.render_widget(Paragraph::new(lines), area);
    }

    fn header(&self) -> Vec<Span<'static>> {
        let t = self.theme;
        let mut spans = vec![
            Span::styled(" AI universe ", t.title()),
            Span::styled(
                format!("{} -> {}  ({}) ", self.from, self.to, self.spec),
                t.accent(),
            ),
            Span::styled(self.weighting.label(), t.dim()),
        ];
        match &self.view {
            View::Groups => {
                for (i, (_, label)) in LEVELS.iter().enumerate() {
                    let st = if i == self.level {
                        t.selected()
                    } else {
                        t.dim()
                    };
                    spans.push(Span::styled(format!(" {label} "), st));
                }
            }
            View::Members(i) => {
                let g = &self.groups[*i];
                let (ret, n) = self.basket(g);
                spans.push(Span::styled(format!("> {} ", g.label), t.title()));
                if let Some(r) = ret {
                    spans.push(Span::styled(format!("{r:+.1}% "), t.signed(r)));
                }
                spans.push(Span::styled(format!("{n} priced"), t.dim()));
            }
            View::Fund(ticker) => {
                spans.push(Span::styled(format!("> Funds > {ticker} "), t.title()));
                let held: &[Member] = self.holdings.get(ticker).map_or(&[], Vec::as_slice);
                spans.push(Span::styled(
                    format!(
                        "{} holdings, {:.0}% of fund",
                        held.len(),
                        covered(held) * 100.0
                    ),
                    t.dim(),
                ));
            }
        }
        spans
    }

    /// One tile's text, centred in its box both ways: the ticker, the return, then the sub-label
    /// wrapped below, as one block.
    fn write_tile(&self, buf: &mut Buffer, r: Rect, tile: &Tile, fill: Color) {
        let t = self.theme;
        let inner = usize::from(r.width).saturating_sub(2);
        if inner == 0 || r.height == 0 {
            return;
        }
        // Text stays the foreground colour on every fill, so it reads at any heat.
        let title = Style::new().fg(t.fg).bg(fill).add_modifier(Modifier::BOLD);
        let plain = Style::new().fg(t.fg).bg(fill);
        let ret_s = tile.ret.map_or("n/a".to_string(), |v| format!("{v:+.1}%"));
        let mut lines: Vec<(String, Style)> = Vec::new();
        if r.height == 1 {
            lines.push((fit(&format!("{} {ret_s}", tile.title), inner), title));
        } else {
            lines.push((fit(&tile.title, inner), title));
            lines.push((fit(&ret_s, inner), plain));
            let mut rest = short_name(&tile.sub);
            for _ in 0..usize::from(r.height) - 2 {
                if rest.is_empty() {
                    break;
                }
                let (head, tail) = split_words(&rest, inner);
                if head.is_empty() {
                    // One word wider than the box: cut it to fit and stop.
                    lines.push((fit(&rest, inner), plain));
                    break;
                }
                lines.push((head, plain));
                rest = tail;
            }
        }
        let top = (usize::from(r.height) - lines.len()) / 2;
        for (i, (text, st)) in lines.iter().enumerate() {
            let pad = inner.saturating_sub(text::width(text)) / 2;
            buf.set_stringn(
                r.x + 1 + pad as u16,
                r.y + (top + i) as u16,
                text,
                inner - pad,
                *st,
            );
        }
    }

    /// The map: the body in the background colour, then each box filled with its heat colour. The
    /// gutter between boxes stays background, so the boundaries are clean blocks, not line art.
    fn draw_map(&self, frame: &mut Frame, body: Rect, plates: &[Plate]) {
        let t = self.theme;
        let base = t.bg.unwrap_or(Color::Rgb(0x1e, 0x1e, 0x2e));
        let scale = self.colour_scale();
        // The gutters are the terminal's own background (Reset) unless --bg set one, so the map
        // sits flush with the terminal instead of on a colour of its own.
        let buf = frame.buffer_mut();
        buf.set_style(body, Style::new().bg(t.bg.unwrap_or(Color::Reset)));
        for p in plates {
            match p {
                Plate::Tile(r, i) => {
                    let tile = &self.tiles[*i];
                    let selected = *i == self.sel;
                    let fill = self.tile_bg(tile.ret, scale, selected);
                    let mut st = Style::new().fg(t.fg).bg(fill);
                    if selected {
                        st = st.add_modifier(Modifier::BOLD);
                    }
                    buf.set_style(*r, st);
                    self.write_tile(buf, *r, tile, fill);
                }
                Plate::Label(r, name, ret) => {
                    let fill = mix(base, t.dim, 0.45);
                    buf.set_style(*r, Style::new().bg(fill));
                    let ret_s = ret.map_or("n/a".to_string(), |v| format!("{v:+.1}%"));
                    let st = Style::new().fg(t.fg).bg(fill).add_modifier(Modifier::BOLD);
                    let inner = usize::from(r.width).saturating_sub(2);
                    let head = fit(&format!("{name}  {ret_s}"), inner);
                    let pad = inner.saturating_sub(text::width(&head)) / 2;
                    buf.set_stringn(r.x + 1 + pad as u16, r.y, &head, inner - pad, st);
                }
            }
        }
    }

    /// The map of the current view, filling `body`.
    fn draw_body(&mut self, frame: &mut Frame, body: Rect) {
        self.body = body;
        let plates = self.plates(body);
        self.draw_map(frame, body, &plates);
    }

    /// Moves the cursor to the box that lies that way (dx, dy) from the current one: the nearest,
    /// with a penalty for drifting off the line. Stays put when nothing lies that way.
    fn step(&mut self, dx: i32, dy: i32) {
        let plates = self.plates(self.body);
        // Centres in square units, so distances are the same both ways.
        let centre = |r: Rect| {
            (
                f64::from(r.x) + f64::from(r.width) / 2.0,
                (f64::from(r.y) + f64::from(r.height) / 2.0) * CELL_ASPECT,
            )
        };
        let cur = plates.iter().find_map(|p| match p {
            Plate::Tile(r, i) if *i == self.sel => Some(*r),
            _ => None,
        });
        let Some(cur) = cur else { return };
        let (cx, cy) = centre(cur);
        let (dx, dy) = (f64::from(dx), f64::from(dy));
        let mut best: Option<(f64, usize)> = None;
        for p in &plates {
            let Plate::Tile(r, i) = p else { continue };
            if *i == self.sel {
                continue;
            }
            let (x, y) = centre(*r);
            let (vx, vy) = (x - cx, y - cy);
            let along = vx * dx + vy * dy;
            if along <= 0.0 {
                continue;
            }
            let score = along + 2.0 * (vx * dy - vy * dx).abs();
            if best.is_none_or(|(s, _)| score < s) {
                best = Some((score, *i));
            }
        }
        if let Some((_, i)) = best {
            self.sel = i;
        }
    }
}

impl Screen for Universe {
    fn leader_ok(&self) -> bool {
        self.editing.is_none()
    }

    fn needs_redraw(&self) -> bool {
        false
    }

    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [head, body, foot] = Layout::vertical([
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(Line::from(self.header())), head);

        let footer = match &self.editing {
            Some(buf) => Line::from(vec![
                Span::styled(" range > ", t.accent()),
                Span::styled(buf.clone(), t.base()),
                Span::styled("_  enter apply | esc cancel", t.dim()),
            ]),
            None if !self.flash.is_empty() => Line::styled(format!(" {}", self.flash), t.dim()),
            None if matches!(self.view, View::Fund(_)) => {
                Line::styled(" hjkl move | enter dossier | esc back", t.dim())
            }
            None => Line::styled(
                " hjkl move | enter open | [ ] range | r edit | w weighting | H/L level | esc back",
                t.dim(),
            ),
        };
        frame.render_widget(Paragraph::new(footer), foot);

        if let View::Fund(ticker) = &self.view {
            let ticker = ticker.clone();
            let [summary, holdings] =
                Layout::vertical([Constraint::Length(FUND_SUMMARY_H), Constraint::Min(1)])
                    .areas(body);
            self.draw_fund(frame, summary, &ticker);
            if self.tiles.is_empty() {
                let msg = if self.holdings.is_empty() {
                    NO_HOLDINGS.to_string()
                } else {
                    format!("no holdings for {ticker}")
                };
                frame.render_widget(Paragraph::new(msg).style(t.dim()), holdings);
            } else {
                self.draw_body(frame, holdings);
            }
            return;
        }
        if self.tiles.is_empty() {
            frame.render_widget(Paragraph::new(NOT_LOADED).style(t.dim()), body);
            return;
        }
        self.draw_body(frame, body);
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if let Some(buf) = self.editing.as_mut() {
            match key.code {
                KeyCode::Esc => self.editing = None,
                KeyCode::Enter => {
                    let spec = std::mem::take(buf);
                    self.editing = None;
                    if self.apply_spec(&spec) {
                        self.rebuild();
                    }
                }
                KeyCode::Backspace => {
                    buf.pop();
                }
                KeyCode::Char(c) if !key.modifiers.contains(KeyModifiers::CONTROL) => buf.push(c),
                _ => {}
            }
            return Action::None;
        }

        let n = self.tiles.len();
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => match self.view {
                View::Groups => return Action::Quit,
                View::Members(_) | View::Fund(_) => {
                    self.view = View::Groups;
                    self.sel = 0;
                    self.rebuild();
                }
            },
            KeyCode::Char('l') | KeyCode::Right => self.step(1, 0),
            KeyCode::Char('h') | KeyCode::Left => self.step(-1, 0),
            KeyCode::Char('j') | KeyCode::Down => self.step(0, 1),
            KeyCode::Char('k') | KeyCode::Up => self.step(0, -1),
            KeyCode::Char('g') => self.sel = 0,
            KeyCode::Char('G') => self.sel = n.saturating_sub(1),
            KeyCode::Char('H' | 'L') if self.view == View::Groups => {
                let d = if key.code == KeyCode::Char('L') {
                    1
                } else {
                    LEVELS.len() - 1
                };
                self.level = (self.level + d) % LEVELS.len();
                self.sel = 0;
                self.rebuild();
            }
            KeyCode::Char('r') => self.editing = Some(String::new()),
            KeyCode::Char('w') => {
                self.weighting = self.weighting.next();
                self.rebuild();
            }
            KeyCode::Char(c @ ('[' | ']')) => {
                let cur = PRESETS.iter().position(|p| *p == self.spec);
                let next = match (cur, c) {
                    (Some(i), ']') => (i + 1).min(PRESETS.len() - 1),
                    (Some(i), _) => i.saturating_sub(1),
                    (None, _) => 2,
                };
                if self.apply_spec(PRESETS[next]) {
                    self.rebuild();
                }
            }
            KeyCode::Enter => {
                let Some(tile) = self.tiles.get(self.sel) else {
                    return Action::None;
                };
                let value = tile.value.clone();
                match self.view {
                    View::Groups if LEVELS[self.level].0 == "fund" => self.open_fund(value),
                    View::Groups if LEVELS[self.level].0 == "favorites" => {
                        return Action::Route(Route::Screen {
                            screen: "dossier".into(),
                            arg: Some(value),
                        });
                    }
                    View::Groups => {
                        if let Ok(i) = value.parse::<usize>() {
                            self.view = View::Members(i);
                            self.sel = 0;
                            self.rebuild();
                        }
                    }
                    View::Members(i) if self.groups[i].level == "fund" => self.open_fund(value),
                    View::Members(_) | View::Fund(_) => {
                        return Action::Route(Route::Screen {
                            screen: "dossier".into(),
                            arg: Some(value),
                        });
                    }
                }
            }
            _ => {}
        }
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(y: i32, m: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(y, m, day).unwrap()
    }

    #[test]
    #[ignore = "needs the real local DuckDB + bars"]
    fn real_data_smoke() {
        let ctx = Ctx {
            db_path: crate::db_path(),
            theme: Theme::default(),
        };
        let u = open(&ctx, None).unwrap();
        eprintln!(
            "{} groups, {} returns, latest {}",
            u.groups.len(),
            u.returns.len(),
            u.latest
        );
        for t in u.tiles.iter().take(5) {
            eprintln!("{} {:?} {}", t.title, t.ret, t.sub);
        }
        assert!(!u.returns.is_empty(), "{}", u.flash);
    }

    /// Prints the real map at a laptop-ish size: `cargo test print_real_map -- --ignored --nocapture`.
    #[test]
    #[ignore = "needs the real local DuckDB + bars"]
    fn print_real_map() {
        let ctx = Ctx {
            db_path: crate::db_path(),
            theme: Theme::default(),
        };
        let mut u = open(&ctx, None).unwrap();
        eprintln!("{}", render(&mut u, 160, 48));
        let key = |c| KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE);
        u.on_key(key('L'));
        eprintln!("{}", render(&mut u, 160, 48));
        u.on_key(key('w'));
        eprintln!("{}", render(&mut u, 160, 48));
    }

    #[test]
    fn parses_relative_and_absolute_ranges() {
        let latest = d(2026, 10, 8);
        assert_eq!(parse_range("30d", latest), Some((d(2026, 9, 8), latest)));
        assert_eq!(parse_range("6m", latest), Some((d(2026, 4, 8), latest)));
        assert_eq!(parse_range("ytd", latest), Some((d(2025, 12, 31), latest)));
        assert_eq!(
            parse_range("2026-01-01", latest),
            Some((d(2026, 1, 1), latest))
        );
        assert_eq!(
            parse_range("2026-01-01..2026-03-01", latest),
            Some((d(2026, 1, 1), d(2026, 3, 1)))
        );
        assert_eq!(parse_range("nonsense", latest), None);
        assert_eq!(parse_range("0d", latest), None);
    }

    #[test]
    fn covered_sums_the_loaded_weights() {
        let m = |t: &str, w: f64| Member {
            ticker: t.into(),
            name: t.into(),
            weight: w,
        };
        assert!((covered(&[m("NVDA", 0.08), m("AMD", 0.06)]) - 0.14).abs() < 1e-9);
        assert_eq!(covered(&[]), 0.0);
    }

    #[test]
    fn span_return_measures_from_the_close_before_the_start() {
        let s = [
            (d(2026, 9, 30), 100.0),
            (d(2026, 10, 2), 110.0),
            (d(2026, 10, 9), 121.0),
        ];
        // base is the 9-30 close (on or before 10-01), end is the 10-09 close
        let (r, base) = span_return(&s, d(2026, 10, 1), d(2026, 10, 9)).unwrap();
        assert!((r - 21.0).abs() < 1e-9);
        assert_eq!(base, d(2026, 9, 30));
        // a window starting before the series: base is the first close after the start
        let (r, base) = span_return(&s, d(2026, 9, 1), d(2026, 10, 2)).unwrap();
        assert!((r - 10.0).abs() < 1e-9);
        assert_eq!(base, d(2026, 9, 30));
        // nothing on or before the end: no return
        assert_eq!(span_return(&s, d(2026, 1, 1), d(2026, 1, 2)), None);
    }

    #[test]
    fn fit_cuts_to_plain_ascii_with_dots() {
        assert_eq!(fit("NVIDIA", 6), "NVIDIA");
        assert_eq!(fit("NVIDIA", 4), "NV..");
        assert_eq!(fit("AB", 1), "A");
        assert_eq!(fit("Caf\u{e9}", 10), "Caf?");
    }

    /// The boxes cover `area` cell by cell: none outside it, none overlapping, none missing.
    fn assert_tiles(area: Rect, boxes: &[Rect]) {
        let mut hits = vec![0u8; usize::from(area.width) * usize::from(area.height)];
        for r in boxes {
            for y in r.y..r.bottom() {
                for x in r.x..r.right() {
                    assert!(
                        x >= area.x && x < area.right() && y >= area.y && y < area.bottom(),
                        "{r:?} leaves {area:?}"
                    );
                    let i =
                        usize::from(y - area.y) * usize::from(area.width) + usize::from(x - area.x);
                    hits[i] += 1;
                }
            }
        }
        assert!(
            hits.iter().all(|&n| n == 1),
            "boxes must cover every cell once: {boxes:?}"
        );
    }

    #[test]
    fn equal_weights_give_each_box_the_same_share() {
        let area = Rect::new(0, 0, 40, 12);
        let boxes = treemap(area, &[1.0; 5]);
        assert_tiles(area, &boxes);
        // 480 cells / 5 = 96 each; rounding the edges to cells moves each by a row or column.
        for r in &boxes {
            let cells = f64::from(r.width) * f64::from(r.height);
            assert!((cells - 96.0).abs() <= 15.0, "{r:?} has {cells} cells");
        }
    }

    #[test]
    fn the_map_always_fills_the_body() {
        for (w, h) in [(7, 3), (60, 20), (200, 50), (9, 40)] {
            let area = Rect::new(3, 2, w, h);
            assert_tiles(area, &treemap(area, &[1.0; 143]));
            assert_tiles(
                area,
                &treemap(area, &[5e12, 3e12, 0.0, 1e6, 0.0, 2.0, f64::NAN]),
            );
        }
    }

    #[test]
    fn a_tiny_weight_still_gets_a_readable_box() {
        let area = Rect::new(0, 0, 60, 20);
        let boxes = treemap(area, &[1e12, 1.0, 0.0]);
        assert_tiles(area, &boxes);
        for r in &boxes {
            let cells = u32::from(r.width) * u32::from(r.height);
            assert!(cells >= 8, "{r:?} is too small to label");
        }
    }

    #[test]
    fn sub_sectors_nest_under_their_primary() {
        let mut u = bare(vec![
            sub("Chips", "Compute", 2.0),
            sub("Memory", "Compute", 1.0),
            sub("Power", "Energy", 1.0),
        ]);
        u.level = 1;
        let plates = u.plates(Rect::new(0, 0, 80, 24));
        let labels: Vec<&str> = plates
            .iter()
            .filter_map(|p| match p {
                Plate::Label(_, name, _) => Some(name.as_str()),
                Plate::Tile(..) => None,
            })
            .collect();
        assert_eq!(labels, ["Compute", "Energy"]);
        let tiles = plates
            .iter()
            .filter(|p| matches!(p, Plate::Tile(..)))
            .count();
        assert_eq!(tiles, 3);
    }

    #[test]
    fn arrows_move_to_a_box_that_lies_that_way() {
        let mut u = bare(vec![
            tile("A", 4.0, Some(1.0)),
            tile("B", 2.0, Some(1.0)),
            tile("C", 1.0, Some(1.0)),
            tile("D", 1.0, Some(1.0)),
        ]);
        u.body = Rect::new(0, 0, 60, 16);
        let key = |c| KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE);
        let centre = |u: &Universe, i: usize| {
            let r = u
                .plates(u.body)
                .iter()
                .find_map(|p| match p {
                    Plate::Tile(r, j) if *j == i => Some(*r),
                    _ => None,
                })
                .unwrap();
            (
                f64::from(r.x) + f64::from(r.width) / 2.0,
                (f64::from(r.y) + f64::from(r.height) / 2.0) * CELL_ASPECT,
            )
        };
        for start in 0..u.tiles.len() {
            for (c, dx, dy) in [
                ('l', 1.0, 0.0),
                ('h', -1.0, 0.0),
                ('j', 0.0, 1.0),
                ('k', 0.0, -1.0),
            ] {
                u.sel = start;
                u.on_key(key(c));
                if u.sel != start {
                    let (a, b) = (centre(&u, start), centre(&u, u.sel));
                    assert!(
                        (b.0 - a.0) * dx + (b.1 - a.1) * dy > 0.0,
                        "{c} from {start} went to {}",
                        u.sel
                    );
                }
            }
        }
    }

    #[test]
    fn equal_weighting_counts_each_basket_as_one_tile() {
        let member = |t: &str, w: f64| Member {
            ticker: t.into(),
            name: t.into(),
            weight: w,
        };
        let g = Group {
            level: "primary".into(),
            name: "x".into(),
            label: "X".into(),
            order: 0,
            parent: None,
            members: vec![member("A", 0.5), member("B", 0.5), member("C", 0.5)],
        };
        let mut u = bare(vec![]);
        u.returns = HashMap::from([("A".to_string(), 1.0), ("B".to_string(), 2.0)]);
        u.caps = HashMap::from([("A".to_string(), 1e12), ("B".to_string(), 1e12)]);
        u.weighting = Weighting::Equal;
        assert_eq!(u.group_weight(&g), 1.0);
        u.weighting = Weighting::Cap;
        assert_eq!(
            u.group_weight(&g),
            2e12,
            "C is unpriced, so it adds nothing"
        );
    }

    #[test]
    fn weighting_uses_market_cap_and_cycles_with_w() {
        let mut u = bare(vec![]);
        u.caps = HashMap::from([("NVDA".to_string(), 3e12), ("AMD".to_string(), 1e12)]);
        let m = |t: &str| Member {
            ticker: t.into(),
            name: t.into(),
            weight: 0.5,
        };
        u.weighting = Weighting::Cap;
        assert_eq!(u.weight_of(&m("NVDA")), 3e12);
        // No market cap: counts for nothing, not a guessed size.
        assert_eq!(u.weight_of(&m("XYZ")), 0.0);
        u.weighting = Weighting::Exposure;
        assert_eq!(u.weight_of(&m("NVDA")), 0.5);
        u.weighting = Weighting::Equal;
        assert_eq!(u.weight_of(&m("XYZ")), 1.0);
        assert_eq!(Weighting::Cap.next(), Weighting::Equal);
        assert_eq!(Weighting::Equal.next(), Weighting::Exposure);
        assert_eq!(Weighting::Exposure.next(), Weighting::Cap);
    }

    fn bare(tiles: Vec<Tile>) -> Universe {
        Universe {
            theme: Theme::default(),
            groups: Vec::new(),
            returns: HashMap::new(),
            fund_series: HashMap::new(),
            holdings: HashMap::new(),
            db_path: std::path::PathBuf::new(),
            spec: "1m".into(),
            from: NaiveDate::MIN,
            to: NaiveDate::MIN,
            latest: NaiveDate::MIN,
            weighting: Weighting::Exposure,
            caps: HashMap::new(),
            level: 0,
            view: View::Groups,
            tiles,
            sel: 0,
            editing: None,
            flash: String::new(),
            body: Rect::default(),
        }
    }

    fn tile(title: &str, weight: f64, ret: Option<f64>) -> Tile {
        Tile {
            title: title.into(),
            sub: String::new(),
            order: 0,
            ret,
            value: title.into(),
            weight,
            parent: None,
        }
    }

    fn sub(title: &str, parent: &str, weight: f64) -> Tile {
        Tile {
            parent: Some(parent.into()),
            ..tile(title, weight, Some(1.0))
        }
    }

    fn render(u: &mut Universe, w: u16, h: u16) -> String {
        let mut term = ratatui::Terminal::new(ratatui::backend::TestBackend::new(w, h)).unwrap();
        term.draw(|f| u.draw(f)).unwrap();
        term.backend().to_string()
    }

    #[test]
    fn the_map_is_plain_ascii_and_labels_every_box() {
        let mut u = bare(vec![
            tile("NVDA", 3.0, Some(12.0)),
            tile("AMD", 1.0, Some(-4.0)),
            tile("XYZ", 2.0, None),
        ]);
        let out = render(&mut u, 80, 20);
        assert!(out.is_ascii(), "non-ASCII on screen:\n{out}");
        assert!(
            out.contains("NVDA") && out.contains("+12.0%") && out.contains("n/a"),
            "{out}"
        );
        // Rows 2..19 are the map (header is 2 rows, footer 1). No line art left in it.
        let map: String = out.lines().skip(2).take(17).collect::<Vec<_>>().join("\n");
        assert!(!map.contains(['|', '#']), "line art left in the map:\n{map}");
    }
}
