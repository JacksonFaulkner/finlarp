// AI-universe heatmap (ai_universe / ai_universe_category, loaded from
// data/ai_stocks_reviewed.json by db.load_universe). Every bucket is treated
// like an ETF: a basket whose return over an editable date range is the
// top-level number, shown as a heatmap tile. Enter drills into the basket's
// members (same heatmap, one tile per ticker); Enter on a ticker opens its
// dossier. Funds (kind = etf) sit outside the sector tree: the Funds level
// tiles each fund, and Enter on a fund opens its page: the returns summary on
// top, a heatmap of its top holdings (fund_holdings) below. Enter on a holding
// opens its dossier. Prices are the Databento daily bars (parquet beside the
// DuckDB), with Yahoo history as the fallback for funds the bars don't cover.
//
//   H / L      primary / sub / region / funds      [ ]  step range preset
//   hjkl       move                         r    edit range (30d, 6m, ytd, 2026-01-01[..2026-03-01])
//   w          equal / category weight      ↵    drill in / open dossier or fund   esc  back

use std::collections::HashMap;
use std::io;
use std::path::Path;

use chrono::{Datelike, Months, NaiveDate};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, NvimAction, Screen};
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
    FROM ai_universe WHERE kind = 'etf' AND eligible IS DISTINCT FROM false";

const NOT_LOADED: &str = "The AI universe isn't loaded into DuckDB yet.\n\n  \
    python -c 'from core import db; db.load_universe()'   (from the repo root)";

const PRESETS: [&str; 8] = ["1d", "1w", "1m", "3m", "6m", "ytd", "1y", "max"];
const LEVELS: [(&str, &str); 4] = [
    ("primary", "Primary"),
    ("sub", "Sub-sector"),
    ("region", "Region"),
    ("fund", "Funds"),
];
const TILE_W: u16 = 20;
const TILE_H: u16 = 5;
/// The fund page's returns summary: name, last close, blank, then one line per preset.
const FUND_SUMMARY_H: u16 = 3 + PRESETS.len() as u16;
const NO_HOLDINGS: &str = "No fund holdings loaded yet.\n\n  \
    uv run sources/yahoo.py universe holdings   (from py/)";
/// How much of an unselected tile's colour survives (the pie dims the same way).
const DIM: f64 = 0.55;

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
    /// Stack order from the taxonomy; ties between equal returns break on it.
    order: i32,
    parent: Option<String>,
    members: Vec<Member>,
}

/// One heatmap tile: a basket or a ticker, with its return over the range.
struct Tile {
    title: String,
    sub: String,
    order: i32,
    ret: Option<f64>,
    value: String,
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
    bars: String,
    db_path: std::path::PathBuf,
    spec: String,
    from: NaiveDate,
    to: NaiveDate,
    latest: NaiveDate,
    equal_weight: bool,
    level: usize,
    view: View,
    tiles: Vec<Tile>,
    sel: usize,
    cols: usize,
    editing: Option<String>,
    flash: String,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Universe> {
    let mut u = Universe {
        theme: ctx.theme,
        groups: Vec::new(),
        returns: HashMap::new(),
        fund_series: HashMap::new(),
        holdings: HashMap::new(),
        bars: bars_glob(&ctx.db_path),
        db_path: ctx.db_path.clone(),
        spec: "1m".into(),
        from: NaiveDate::MIN,
        to: NaiveDate::MIN,
        latest: NaiveDate::MIN,
        equal_weight: true,
        level: 0,
        view: View::Groups,
        tiles: Vec::new(),
        sel: 0,
        cols: 1,
        editing: None,
        flash: String::new(),
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
    match load_fund_series(&u.db_path, &u.bars, &funds) {
        Ok(s) => u.fund_series = s,
        Err(e) => u.flash = e,
    }
    match load_holdings(&u.db_path) {
        Ok(h) => u.holdings = h,
        Err(e) => u.flash = e,
    }
    match latest_bar(&u.db_path, &u.bars) {
        Ok(d) => u.latest = d,
        Err(e) => u.flash = e,
    }
    u.apply_spec("1m");
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
    u.rebuild();
    Ok(u)
}

pub fn bars_glob(db_path: &Path) -> String {
    bars_glob_for(db_path, "bars_1d")
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

fn latest_bar(db_path: &Path, glob: &str) -> Result<NaiveDate, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let sql = format!(
        "SELECT CAST(max((ts_event AT TIME ZONE 'UTC')::DATE) AS VARCHAR) \
         FROM read_parquet('{}', union_by_name=true)",
        glob.replace('\'', "''")
    );
    let s: Option<String> = conn
        .query_row(&sql, [], |r| r.get(0))
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
    glob: &str,
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
            FROM read_parquet('{}', union_by_name=true)
            WHERE close > 0 AND (symbol IN (SELECT ticker FROM ai_universe){extra})
         )
         SELECT symbol,
                arg_max(close, d) FILTER (WHERE d <= CAST(? AS DATE)) AS last,
                coalesce(arg_max(close, d) FILTER (WHERE d <= CAST(? AS DATE)),
                         arg_min(close, d) FILTER (WHERE d > CAST(? AS DATE))) AS base
         FROM b GROUP BY symbol",
        glob.replace('\'', "''")
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
    glob: &str,
    tickers: &[String],
) -> Result<HashMap<String, Vec<(NaiveDate, f64)>>, String> {
    let mut out: HashMap<String, Vec<(NaiveDate, f64)>> = HashMap::new();
    if tickers.is_empty() {
        return Ok(out);
    }
    let conn = crate::db::open_read_only(db_path)?;
    let sql = format!(
        "SELECT symbol, CAST((ts_event AT TIME ZONE 'UTC')::DATE AS VARCHAR), close \
         FROM read_parquet('{}', union_by_name=true) \
         WHERE close > 0 AND symbol IN ({}) ORDER BY symbol, ts_event",
        glob.replace('\'', "''"),
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
                match load_returns(&self.db_path, &self.bars, from, to, &held) {
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

    fn member_tile(&self, m: &Member) -> Tile {
        Tile {
            title: m.ticker.clone(),
            sub: m.name.clone(),
            order: 0,
            ret: self.ret_of(&m.ticker),
            value: m.ticker.clone(),
        }
    }

    /// A holding's tile: its weight in the fund sits in the subline.
    fn holding_tile(&self, m: &Member) -> Tile {
        Tile {
            sub: format!("{:.1}% {}", m.weight * 100.0, m.name),
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
                let w = if self.equal_weight { 1.0 } else { m.weight };
                num += w * r;
                den += w;
                n += 1;
            }
        }
        ((den > 0.0).then(|| num / den), n)
    }

    fn rebuild(&mut self) {
        let level = LEVELS[self.level].0;
        let mut tiles: Vec<Tile> = match self.view {
            View::Fund(ref ticker) => self
                .holdings
                .get(ticker)
                .map(|ms| ms.iter().map(|m| self.holding_tile(m)).collect())
                .unwrap_or_default(),
            // Funds have no basket: each fund is its own tile.
            View::Groups if level == "fund" => self
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
                        Some(p) => format!("{p} · {n}"),
                        None => format!("{n}/{} priced", g.members.len()),
                    };
                    Tile {
                        title: g.label.clone(),
                        order: g.order,
                        sub,
                        ret,
                        value: i.to_string(),
                    }
                })
                .collect(),
            View::Members(i) => self.groups[i]
                .members
                .iter()
                .map(|m| self.member_tile(m))
                .collect(),
        };
        tiles.sort_by(|a, b| {
            b.ret
                .unwrap_or(f64::NEG_INFINITY)
                .total_cmp(&a.ret.unwrap_or(f64::NEG_INFINITY))
                .then_with(|| a.order.cmp(&b.order))
                .then_with(|| a.title.cmp(&b.title))
        });
        self.tiles = tiles;
        self.sel = self.sel.min(self.tiles.len().saturating_sub(1));
    }

    /// Selected tile keeps full colour; the rest fade toward the background.
    fn tile_style(&self, ret: Option<f64>, scale: f64, selected: bool) -> Style {
        let t = self.theme;
        let base = t.bg.unwrap_or(Color::Rgb(0x1e, 0x1e, 0x2e));
        let bg = match ret {
            None => mix(base, t.dim, 0.15),
            Some(r) => {
                let k = (r.abs() / scale).clamp(0.0, 1.0);
                mix(base, if r >= 0.0 { t.up } else { t.down }, 0.18 + 0.62 * k)
            }
        };
        let bg = if selected { bg } else { mix(base, bg, DIM) };
        let mut s = Style::new().fg(t.fg).bg(bg);
        if selected {
            s = s.add_modifier(Modifier::BOLD);
        }
        s
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
                    " last ${last:.2} on {last_day} · {} daily closes since {}",
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
                format!("{} → {}  ({}) ", self.from, self.to, self.spec),
                t.accent(),
            ),
            Span::styled(
                if self.equal_weight {
                    "equal-wt "
                } else {
                    "cat-wt "
                },
                t.dim(),
            ),
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
                spans.push(Span::styled(format!("› {} ", g.label), t.title()));
                if let Some(r) = ret {
                    spans.push(Span::styled(format!("{r:+.1}% "), t.signed(r)));
                }
                spans.push(Span::styled(format!("{n} priced"), t.dim()));
            }
            View::Fund(ticker) => {
                spans.push(Span::styled(format!("› Funds › {ticker} "), t.title()));
                let held: &[Member] = self.holdings.get(ticker).map_or(&[], Vec::as_slice);
                spans.push(Span::styled(
                    format!(
                        "{} holdings · {:.0}% of fund",
                        held.len(),
                        covered(held) * 100.0
                    ),
                    t.dim(),
                ));
            }
        }
        spans
    }

    /// The heatmap: one tile per ticker or basket, filled left to right, top to bottom.
    fn draw_tiles(&mut self, frame: &mut Frame, body: Rect) {
        let t = self.theme;
        // Colour scale: 90th percentile of |return| so one outlier doesn't wash out the rest.
        let mut mags: Vec<f64> = self
            .tiles
            .iter()
            .filter_map(|x| x.ret)
            .map(f64::abs)
            .collect();
        mags.sort_by(f64::total_cmp);
        let scale = mags
            .get(mags.len().saturating_sub(1) * 9 / 10)
            .copied()
            .unwrap_or(1.0)
            .max(1.0);

        let cols = ((body.width / TILE_W).max(1)) as usize;
        self.cols = cols;
        let tile_w = body.width / cols as u16;
        let rows_visible = (body.height / TILE_H).max(1) as usize;
        let sel_row = self.sel / cols;
        let first_row = sel_row.saturating_sub(rows_visible - 1);

        for (i, tile) in self.tiles.iter().enumerate() {
            let (row, col) = (i / cols, i % cols);
            if row < first_row || row >= first_row + rows_visible {
                continue;
            }
            let r = Rect::new(
                body.x + col as u16 * tile_w,
                body.y + (row - first_row) as u16 * TILE_H,
                tile_w.saturating_sub(1),
                TILE_H - 1,
            );
            let selected = i == self.sel;
            let st = self.tile_style(tile.ret, scale, selected);
            let w = r.width as usize;
            let ret = match tile.ret {
                Some(v) => format!("{v:+.1}%"),
                None => "n/a".into(),
            };
            // Border row top and bottom is always reserved; only the selected
            // tile draws it (like the pie's outlined slice).
            let block = if selected {
                Block::bordered().border_style(st.fg(t.fg))
            } else {
                Block::new()
            };
            let inner = Rect::new(r.x, r.y + 1, r.width, r.height - 2);
            frame.render_widget(Block::new().style(st), r);
            frame.render_widget(block.style(st), r);
            // Title, then as many words of the sub-label as fit beside it; the
            // rest wraps onto the return line.
            let title = text::truncate(&tile.title, w.saturating_sub(3));
            let room = w.saturating_sub(text::width(&title) + 4);
            let (head, rest) = split_words(&short_name(&tile.sub), room);
            let rest = text::truncate(&rest, w.saturating_sub(text::width(&ret) + 5));
            let plain = st.remove_modifier(Modifier::BOLD);
            let lines = vec![
                Line::from(vec![
                    Span::styled(format!(" {title}"), st.add_modifier(Modifier::BOLD)),
                    Span::styled(format!("  {head}"), plain),
                ]),
                Line::from(vec![
                    Span::styled(format!(" {ret}"), st.add_modifier(Modifier::BOLD)),
                    Span::styled(format!("  {rest}"), plain),
                ]),
            ];
            frame.render_widget(Paragraph::new(lines).style(st), inner);
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
                Span::styled(" range › ", t.accent()),
                Span::styled(buf.clone(), t.base()),
                Span::styled("█  ↵ apply · esc cancel", t.dim()),
            ]),
            None if !self.flash.is_empty() => Line::styled(format!(" {}", self.flash), t.dim()),
            None if matches!(self.view, View::Fund(_)) => {
                Line::styled(" hjkl move · ↵ dossier · esc back", t.dim())
            }
            None => Line::styled(
                " hjkl move · ↵ open · [ ] range · r edit · w weighting · H/L level · esc back",
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
                self.draw_tiles(frame, holdings);
            }
            return;
        }
        if self.tiles.is_empty() {
            frame.render_widget(Paragraph::new(NOT_LOADED).style(t.dim()), body);
            return;
        }
        self.draw_tiles(frame, body);
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
        let cols = self.cols.max(1);
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') => match self.view {
                View::Groups => return Action::Quit,
                View::Members(_) | View::Fund(_) => {
                    self.view = View::Groups;
                    self.sel = 0;
                    self.rebuild();
                }
            },
            KeyCode::Char('l') | KeyCode::Right => {
                self.sel = (self.sel + 1).min(n.saturating_sub(1))
            }
            KeyCode::Char('h') | KeyCode::Left => self.sel = self.sel.saturating_sub(1),
            KeyCode::Char('j') | KeyCode::Down => {
                self.sel = (self.sel + cols).min(n.saturating_sub(1))
            }
            KeyCode::Char('k') | KeyCode::Up => self.sel = self.sel.saturating_sub(cols),
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
                self.equal_weight = !self.equal_weight;
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
                    View::Groups => {
                        if let Ok(i) = value.parse::<usize>() {
                            self.view = View::Members(i);
                            self.sel = 0;
                            self.rebuild();
                        }
                    }
                    View::Members(i) if self.groups[i].level == "fund" => self.open_fund(value),
                    View::Members(_) | View::Fund(_) => {
                        return Action::Nvim(NvimAction::Screen {
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
}
