// The AI universe as a fake oil.nvim buffer. The bottom quarter lists a directory of the
// universe tree (the same layout as data/universe, see universe_fs): the primaries, then
// their sub-sectors, then the names, plus funds/, regions/ and ~grids/. j/k move, enter goes
// into a directory (on a fund: its holdings), - goes back up with the cursor on where you
// came from, _ jumps to the top. The top three quarters preview what the cursor is on:
//
//   a directory  its contents as a heatmap (colour = return over the range, size = its share
//                under the weighting: cap / equal / exposure, `w`)
//   a ticker     the expanded view (universe_monitor): price line, chart, peers
//
// Tickers in the buffer carry live quotes (the intraday feed, subscribed to the listing on
// screen); { } step to the previous / next sibling directory; s sorts the names, t switches
// the chart between the range and today, [ ] / r set the range.
//
// Real nvim is kept as a side door: E opens the user's own nvim + oil on the same tree
// beside the screen (universe_nvim), and the buffer follows oil's cursor (ctrl-p: off).
// ~grids is plain directories, so grids made in oil show up here.
//
// Prices are the Databento daily bars (parquet beside the DuckDB), with Yahoo history as the
// fallback for funds the bars don't cover.

#[path = "universe_monitor.rs"]
mod monitor;
#[path = "universe_nvim.rs"]
mod nvim;
#[path = "universe_fs.rs"]
mod tree_fs;

use std::collections::HashMap;
use std::io;
use std::path::{Path, PathBuf};
use std::time::{Instant, SystemTime};

use self::monitor::{Basket, Chart, Monitor, Row, Sort};
use crate::ui::pic_chart::PicChart;
use self::nvim::NvimPane;
use self::tree_fs::{Spot, Tree};

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
use crate::ui::help::{Help, Key, key};
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

const PRESETS: [&str; 9] = ["live", "1d", "1w", "1m", "3m", "6m", "ytd", "1y", "max"];
/// The `live` range: the last close before today to the latest print (pre/post included).
const LIVE: &str = "live";
/// How often the live range asks Yahoo again.
const LIVE_EVERY: std::time::Duration = std::time::Duration::from_secs(60);

/// The `live` range's moves, from `yahoo.py since-close` (one batched v7 quote call).
#[derive(Default)]
struct Live {
    /// Percent move per ticker since the last close before today.
    rets: HashMap<String, f64>,
    /// When the moves were priced (unix seconds), per Yahoo's reply.
    asof: Option<i64>,
    /// The pull in flight.
    rx: Option<std::sync::mpsc::Receiver<Result<String, String>>>,
    /// When the last pull started.
    asked: Option<Instant>,
}

/// `yahoo.py since-close` JSON -> (moves, asof).
fn parse_live(json: &str) -> Result<(HashMap<String, f64>, Option<i64>), String> {
    let v: serde_json::Value = serde_json::from_str(json).map_err(|e| format!("live: {e}"))?;
    let rets = v["moves"]
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|m| Some((m["symbol"].as_str()?.to_string(), m["pct"].as_f64()?)))
        .collect();
    Ok((rets, v["asof"].as_i64()))
}
/// How often the open pane re-reads ~grids for edits made in oil.
const GRIDS_EVERY: std::time::Duration = std::time::Duration::from_secs(1);
const NO_HOLDINGS: &str = "No fund holdings loaded yet.\n\n  \
    uv run sources/yahoo.py universe holdings   (from py/)";
/// `sel` when the preview heatmap has no cursor: every box at full colour.
const NO_SEL: usize = usize::MAX;
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
    ret: Option<f64>,
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
}

/// A directory of the fake oil buffer. Paths match the tree on disk (universe_fs).
#[derive(Clone, PartialEq, Eq, Hash, Debug)]
enum Dir {
    Root,
    /// A primary: its sub-sectors.
    Primary(usize),
    /// A basket's names: a sub-sector, the fund list, a region or a grid.
    Basket(usize),
    Regions,
    Grids,
    /// A fund's top holdings.
    Holdings(String),
}

/// One line of the buffer.
#[derive(Clone, PartialEq, Debug)]
enum Entry {
    Dir(Dir),
    Ticker(String),
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
    /// The directory the buffer lists, its lines, and the cursor.
    dir: Dir,
    entries: Vec<Entry>,
    cur: usize,
    /// Where the cursor was in each directory left, so coming back lands there.
    marks: HashMap<Dir, usize>,
    /// The preview heatmap: its boxes, its selected box (NO_SEL: none), and whether
    /// sub-sectors nest under their primary.
    tiles: Vec<Tile>,
    sel: usize,
    nest: bool,
    editing: Option<String>,
    flash: String,
    /// The map's body as last drawn; cursor moves read its geometry.
    body: Rect,
    /// The baskets as directories (universe_fs), for nvim.
    tree: Tree,
    /// Index of the first `grid` group: grids sit last so reloading them keeps the rest.
    grids_from: usize,
    grids_read: Instant,
    /// The nvim pane, once `-` first opened it.
    nvim: Option<NvimPane>,
    pane_open: bool,
    /// Keys go to nvim (otherwise to the map).
    nvim_focus: bool,
    /// The map follows oil's cursor.
    follow: bool,
    /// `.cursor`'s mtime and text when last read.
    cursor_seen: Option<SystemTime>,
    cursor_rel: String,
    /// A reveal waiting for nvim's socket (the pane was just started).
    pending_reveal: Option<(String, Option<String>)>,
    /// nvim's screen, the followed map or a quote changed since the last draw.
    dirty: bool,
    /// The basket view's quotes, closes and settings.
    monitor: Monitor,
    /// The `live` range's moves.
    live: Live,
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
        dir: Dir::Root,
        entries: Vec::new(),
        cur: 0,
        marks: HashMap::new(),
        tiles: Vec::new(),
        sel: NO_SEL,
        nest: false,
        editing: None,
        flash: String::new(),
        body: Rect::default(),
        tree: Tree::default(),
        grids_from: 0,
        grids_read: Instant::now(),
        nvim: None,
        pane_open: false,
        nvim_focus: false,
        follow: true,
        cursor_seen: None,
        cursor_rel: String::new(),
        pending_reveal: None,
        dirty: false,
        monitor: Monitor::default(),
        live: Live::default(),
    };
    match load_groups(ctx) {
        Ok(g) => u.groups = g,
        Err(e) => u.flash = e,
    }
    u.write_tree();
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
        Ok(d) => u.latest = d,
        Err(e) => u.flash = e,
    }
    // Opens on the move since the last close: the bars lag, Yahoo is today.
    u.apply_spec(LIVE);
    match load_caps(&u.db_path) {
        Ok(c) => u.caps = c,
        Err(e) => {
            // No sizes yet: fall back to equal weights rather than a map of slivers.
            u.weighting = Weighting::Equal;
            u.flash = e;
        }
    }
    u.cd(Dir::Root);
    // "level|category" opens that basket directly.
    if let Some((level, cat)) = arg.as_deref().and_then(|a| a.split_once('|')) {
        if let Some(i) = u
            .groups
            .iter()
            .position(|g| g.level == level && g.name == cat)
        {
            u.cd(if level == "primary" {
                Dir::Primary(i)
            } else {
                Dir::Basket(i)
            });
        }
    }
    // the expanded chart draws candles as a picture where the terminal can
    u.monitor.pic = Some(PicChart::probe(&ctx.theme, 1));
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
        if spec.trim().eq_ignore_ascii_case(LIVE) {
            self.spec = LIVE.into();
            let today = chrono::Local::now().date_naive();
            (self.from, self.to) = (today, today);
            self.monitor.chart = Chart::Today;
            self.ask_live();
            return true;
        }
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
        if self.spec == LIVE {
            return self.live.rets.get(ticker).copied();
        }
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
            ret: self.ret_of(&m.ticker),
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

    /// Sub-sectors are drawn nested under their primary.
    fn nested(&self) -> bool {
        self.nest
    }

    /// A basket's box: its return, its share under the weighting, `value` = group index.
    fn group_tile(&self, i: usize) -> Tile {
        let g = &self.groups[i];
        let (ret, n) = self.basket(g);
        let sub = match &g.parent {
            Some(p) => format!("{p} - {n}"),
            None => format!("{n}/{} priced", g.members.len()),
        };
        Tile {
            title: g.label.clone(),
            sub,
            ret,
            weight: self.group_weight(g),
            parent: g.parent.clone(),
        }
    }

    /// The heatmap that previews directory `d`: a box per thing inside it, heaviest first.
    fn preview_tiles(&self, d: &Dir) -> Vec<Tile> {
        let mut tiles: Vec<Tile> = match d {
            Dir::Holdings(t) => self
                .holdings
                .get(t)
                .map(|ms| ms.iter().map(|m| self.holding_tile(m)).collect())
                .unwrap_or_default(),
            Dir::Basket(i) => self.groups[*i]
                .members
                .iter()
                .map(|m| self.member_tile(m))
                .collect(),
            _ => self
                .entries_of(d)
                .iter()
                .filter_map(|e| match e {
                    Entry::Dir(Dir::Primary(i) | Dir::Basket(i)) => Some(self.group_tile(*i)),
                    _ => None,
                })
                .collect(),
        };
        tiles.sort_by(|a, b| {
            b.weight
                .total_cmp(&a.weight)
                .then_with(|| a.title.cmp(&b.title))
        });
        tiles
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

    /// Every name the screen can show: basket members, funds and fund holdings.
    fn all_tickers(&self) -> Vec<String> {
        let mut out: Vec<String> = self
            .groups
            .iter()
            .flat_map(|g| &g.members)
            .chain(self.holdings.values().flatten())
            .map(|m| m.ticker.clone())
            .chain(self.holdings.keys().cloned())
            .collect();
        out.sort();
        out.dedup();
        out
    }

    /// Starts a `since-close` pull for every name unless one is in flight.
    fn ask_live(&mut self) {
        if self.live.rx.is_some() || cfg!(test) {
            return;
        }
        let syms = self.all_tickers().join(",");
        if syms.is_empty() {
            return;
        }
        self.live.asked = Some(Instant::now());
        self.live.rx = Some(crate::pyrun::spawn_script(
            "py/sources/yahoo.py",
            &["since-close", &syms],
        ));
    }

    /// Takes in a finished live pull and starts the next one when due. True when the map moved.
    fn poll_live(&mut self) -> bool {
        if self.spec != LIVE {
            return false;
        }
        let mut changed = false;
        if let Some(rx) = &self.live.rx {
            match rx.try_recv() {
                Ok(res) => {
                    self.live.rx = None;
                    match res.and_then(|s| parse_live(&s)) {
                        Ok((rets, asof)) => {
                            self.live.rets = rets;
                            self.live.asof = asof;
                        }
                        Err(e) => self.flash = e,
                    }
                    self.refresh();
                    changed = true;
                }
                Err(std::sync::mpsc::TryRecvError::Disconnected) => self.live.rx = None,
                Err(std::sync::mpsc::TryRecvError::Empty) => {}
            }
        }
        if self.live.asked.is_none_or(|t| t.elapsed() >= LIVE_EVERY) {
            self.ask_live();
        }
        changed
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
                    let selected = *i == self.sel || self.sel == NO_SEL;
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
}

/// The tree on disk and the nvim pane beside the map.
impl Universe {
    /// data/universe, beside the DuckDB file.
    fn tree_root(&self) -> PathBuf {
        self.db_path
            .parent()
            .unwrap_or(Path::new("."))
            .join("universe")
    }

    /// Writes the baskets as directories (universe_fs), then reads ~grids in as groups.
    fn write_tree(&mut self) {
        let root = self.tree_root();
        let nodes: Vec<tree_fs::Node> = self
            .groups
            .iter()
            .map(|g| tree_fs::Node {
                level: &g.level,
                label: &g.label,
                parent: g.parent.as_deref(),
                members: g
                    .members
                    .iter()
                    .map(|m| (m.ticker.as_str(), m.name.as_str()))
                    .collect(),
            })
            .collect();
        let favorites: Vec<&str> = self
            .groups
            .iter()
            .filter(|g| g.level == "favorites")
            .flat_map(|g| g.members.iter().map(|m| m.ticker.as_str()))
            .collect();
        match Tree::write(&root, &nodes, &favorites) {
            Ok(t) => self.tree = t,
            Err(e) => self.flash = format!("universe tree in {}: {e}", root.display()),
        }
        self.grids_from = self.groups.len();
        self.reload_grids();
    }

    /// Re-reads ~grids into the `grid` groups (kept last). Rebuilds the map only on a change.
    fn reload_grids(&mut self) {
        self.grids_read = Instant::now();
        let grids = Tree::grids(&self.tree_root());
        let current: Vec<(String, Vec<String>)> = self.groups[self.grids_from..]
            .iter()
            .map(|g| {
                (
                    g.name.clone(),
                    g.members.iter().map(|m| m.ticker.clone()).collect(),
                )
            })
            .collect();
        if current == grids {
            return;
        }
        let names: HashMap<String, String> = self.groups[..self.grids_from]
            .iter()
            .flat_map(|g| &g.members)
            .map(|m| (m.ticker.clone(), m.name.clone()))
            .collect();
        self.groups.truncate(self.grids_from);
        self.tree.clear_grids();
        for (k, (name, tickers)) in grids.into_iter().enumerate() {
            self.tree.add_grid(&name, self.grids_from + k);
            self.groups.push(Group {
                level: "grid".into(),
                label: name.clone(),
                order: k as i32,
                parent: None,
                members: tickers
                    .into_iter()
                    .map(|t| Member {
                        name: names.get(&t).cloned().unwrap_or_default(),
                        ticker: t,
                        weight: 1.0,
                    })
                    .collect(),
                name,
            });
        }
        if matches!(self.dir, Dir::Basket(i) if i >= self.groups.len()) {
            self.cur = 0;
        }
        self.refresh();
    }

    /// Where `E` opens oil: the buffer's directory with the cursor on the same entry.
    /// (directory relative to the root, entry)
    fn selection_path(&self) -> (String, Option<String>) {
        let last = |rel: &str| rel.rsplit('/').next().unwrap_or(rel).to_string();
        let entry = self.hovered().and_then(|e| match e {
            Entry::Ticker(t) => Some(t.clone()),
            Entry::Dir(Dir::Primary(i) | Dir::Basket(i)) => self.tree.path_of(*i).map(last),
            Entry::Dir(Dir::Grids) => Some(tree_fs::GRIDS.to_string()),
            Entry::Dir(_) => None,
        });
        match &self.dir {
            // holdings aren't on disk: open the fund list on the fund
            Dir::Holdings(t) => (tree_fs::FUNDS.into(), Some(t.clone())),
            d => (self.rel_of(d), entry),
        }
    }

    /// Keys go to nvim right now.
    fn nvim_keys(&self) -> bool {
        self.pane_open && self.nvim_focus
    }

    /// `-`: opens the nvim pane with focus, oil on the selected box.
    fn open_pane(&mut self) {
        if self.nvim.is_none() {
            self.nvim = Some(NvimPane::new(&self.tree_root()));
        }
        self.pane_open = true;
        self.nvim_focus = true;
        self.pending_reveal = Some(self.selection_path());
    }

    /// Follows oil: when `.cursor` changed, moves the map to the place it names. True when
    /// the map moved.
    fn follow_cursor(&mut self) -> bool {
        let path = self.tree_root().join(tree_fs::CURSOR);
        let Ok(mtime) = std::fs::metadata(&path).and_then(|m| m.modified()) else {
            return false;
        };
        if self.cursor_seen == Some(mtime) {
            return false;
        }
        self.cursor_seen = Some(mtime);
        let Ok(text) = std::fs::read_to_string(&path) else {
            return false;
        };
        let rel = text.trim().to_string();
        if rel == self.cursor_rel {
            return false;
        }
        if rel.starts_with(tree_fs::GRIDS) {
            self.reload_grids();
        }
        let groups = &self.groups;
        let spot = self.tree.locate(&rel, |i| {
            groups.get(i).map(|g| g.level.clone()).unwrap_or_default()
        });
        self.cursor_rel = rel;
        match spot {
            Some(spot) => {
                self.go_to(spot);
                true
            }
            None => false,
        }
    }

    /// Puts the buffer where oil's cursor is: `spot`'s directory, cursor on its entry.
    fn go_to(&mut self, spot: Spot) {
        let level_of = |u: &Self, i: usize| u.groups.get(i).map(|g| g.level.clone());
        let (dir, on): (Dir, Option<Entry>) = match spot {
            Spot::Groups { level, pick } => {
                let picked = pick.as_deref().and_then(|p| p.parse::<usize>().ok());
                match (level.as_str(), picked) {
                    ("fund", _) => match self.funds_group() {
                        Some(f) => (Dir::Basket(f), pick.map(Entry::Ticker)),
                        None => (Dir::Root, None),
                    },
                    ("grid", Some(i)) => (Dir::Grids, Some(Entry::Dir(Dir::Basket(i)))),
                    ("grid", None) => (Dir::Root, Some(Entry::Dir(Dir::Grids))),
                    ("primary", Some(i)) => (Dir::Root, Some(Entry::Dir(Dir::Primary(i)))),
                    ("sub", Some(i)) => {
                        let up = self.parent(&Dir::Basket(i)).unwrap_or(Dir::Root);
                        (up, Some(Entry::Dir(Dir::Basket(i))))
                    }
                    _ => (Dir::Root, None),
                }
            }
            Spot::Members { group, pick } => {
                if level_of(self, group).is_none() {
                    return;
                }
                (Dir::Basket(group), pick.map(Entry::Ticker))
            }
        };
        if dir != self.dir {
            self.cd(dir);
        }
        if let Some(e) = on {
            self.select(&e);
        }
    }
}

/// The fake oil buffer: directories, the cursor, and what the panes show for them.
impl Universe {
    /// Groups at `level` in taxonomy order (sub-sectors grouped under their primary).
    fn groups_at(&self, level: &str) -> Vec<usize> {
        let primary_order: HashMap<&str, i32> = self
            .groups
            .iter()
            .filter(|g| g.level == "primary")
            .map(|g| (g.label.as_str(), g.order))
            .collect();
        let mut out: Vec<usize> = (0..self.groups.len())
            .filter(|&i| self.groups[i].level == level)
            .collect();
        out.sort_by_key(|&i| {
            let g = &self.groups[i];
            let p = g
                .parent
                .as_deref()
                .and_then(|p| primary_order.get(p))
                .copied()
                .unwrap_or(i32::MAX);
            (p, g.order, g.label.clone())
        });
        out
    }

    fn funds_group(&self) -> Option<usize> {
        self.groups.iter().position(|g| g.level == "fund")
    }

    /// The lines of directory `d`.
    fn entries_of(&self, d: &Dir) -> Vec<Entry> {
        let dirs = |v: Vec<usize>| -> Vec<Entry> {
            v.into_iter().map(|i| Entry::Dir(Dir::Basket(i))).collect()
        };
        match d {
            Dir::Root => {
                let mut v: Vec<Entry> = self
                    .groups_at("primary")
                    .into_iter()
                    .map(|i| Entry::Dir(Dir::Primary(i)))
                    .collect();
                if let Some(f) = self.funds_group() {
                    v.push(Entry::Dir(Dir::Basket(f)));
                }
                if self.groups.iter().any(|g| g.level == "region") {
                    v.push(Entry::Dir(Dir::Regions));
                }
                v.push(Entry::Dir(Dir::Grids));
                v
            }
            Dir::Primary(i) => {
                let label = self.groups[*i].label.as_str();
                dirs(
                    self.groups_at("sub")
                        .into_iter()
                        .filter(|&j| self.groups[j].parent.as_deref() == Some(label))
                        .collect(),
                )
            }
            Dir::Regions => {
                let mut v = self.groups_at("region");
                v.sort_by_key(|&i| std::cmp::Reverse(self.groups[i].members.len()));
                dirs(v)
            }
            Dir::Grids => dirs(self.groups_at("grid")),
            Dir::Basket(i) => self.tickers(&self.groups[*i].members, false),
            Dir::Holdings(t) => self.tickers(self.holdings.get(t).map_or(&[], Vec::as_slice), true),
        }
    }

    /// Ticker lines in the monitor's order. `held`: fund holdings, whose weight is the fund's.
    fn tickers(&self, members: &[Member], held: bool) -> Vec<Entry> {
        let mut ms: Vec<&Member> = members.iter().collect();
        let key = |v: Option<f64>| v.unwrap_or(f64::NEG_INFINITY);
        let m = &self.monitor;
        match m.sort {
            Sort::Weight if held => ms.sort_by(|a, b| b.weight.total_cmp(&a.weight)),
            Sort::Weight => ms.sort_by(|a, b| {
                self.weight_of(b)
                    .total_cmp(&self.weight_of(a))
                    .then_with(|| a.ticker.cmp(&b.ticker))
            }),
            Sort::Chg => ms.sort_by(|a, b| key(m.chg(&b.ticker)).total_cmp(&key(m.chg(&a.ticker)))),
            Sort::Range => ms.sort_by(|a, b| {
                key(self.ret_of(&b.ticker)).total_cmp(&key(self.ret_of(&a.ticker)))
            }),
            Sort::Ticker => ms.sort_by(|a, b| a.ticker.cmp(&b.ticker)),
        }
        ms.dedup_by(|a, b| a.ticker == b.ticker);
        ms.into_iter()
            .map(|m| Entry::Ticker(m.ticker.clone()))
            .collect()
    }

    /// The directory above `d`.
    fn parent(&self, d: &Dir) -> Option<Dir> {
        Some(match d {
            Dir::Root => return None,
            Dir::Primary(_) | Dir::Regions | Dir::Grids => Dir::Root,
            Dir::Holdings(_) => self.funds_group().map_or(Dir::Root, Dir::Basket),
            Dir::Basket(i) => {
                let g = &self.groups[*i];
                match g.level.as_str() {
                    "sub" => g
                        .parent
                        .as_deref()
                        .and_then(|p| {
                            self.groups
                                .iter()
                                .position(|x| x.level == "primary" && x.label == p)
                        })
                        .map_or(Dir::Root, Dir::Primary),
                    "region" => Dir::Regions,
                    "grid" => Dir::Grids,
                    _ => Dir::Root,
                }
            }
        })
    }

    /// `d`'s path in the tree, relative to the root (empty for the root and regions).
    fn rel_of(&self, d: &Dir) -> String {
        match d {
            Dir::Primary(i) | Dir::Basket(i) => self.tree.path_of(*i).unwrap_or_default().into(),
            Dir::Grids => tree_fs::GRIDS.into(),
            Dir::Holdings(t) => format!("{}/{t}", tree_fs::FUNDS),
            Dir::Regions => "regions".into(),
            Dir::Root => String::new(),
        }
    }

    /// An entry's name in the buffer: `memory_storage/`, `funds/`, `MU`.
    fn entry_name(&self, e: &Entry) -> String {
        match e {
            Entry::Ticker(t) => t.clone(),
            Entry::Dir(Dir::Regions) => "regions/".into(),
            Entry::Dir(Dir::Grids) => format!("{}/", tree_fs::GRIDS),
            Entry::Dir(Dir::Root) => "/".into(),
            Entry::Dir(Dir::Holdings(t)) => format!("{t}/"),
            Entry::Dir(Dir::Primary(i) | Dir::Basket(i)) => {
                let g = &self.groups[*i];
                match g.level.as_str() {
                    "fund" => format!("{}/", tree_fs::FUNDS),
                    "grid" => format!("{}/", g.name),
                    _ => format!("{}/", tree_fs::slug(&g.label)),
                }
            }
        }
    }

    /// A directory's title, return over the range, and how many names it holds.
    fn dir_info(&self, d: &Dir) -> (String, Option<f64>, usize) {
        match d {
            Dir::Primary(i) | Dir::Basket(i) => {
                let g = &self.groups[*i];
                (g.label.clone(), self.basket(g).0, g.members.len())
            }
            Dir::Regions => ("Regions".into(), None, self.groups_at("region").len()),
            Dir::Grids => ("Grids".into(), None, self.groups_at("grid").len()),
            Dir::Holdings(t) => {
                let held = self.holdings.get(t).map_or(&[][..], Vec::as_slice);
                let (mut num, mut den) = (0.0, 0.0);
                for m in held {
                    if let Some(r) = self.ret_of(&m.ticker) {
                        num += m.weight * r;
                        den += m.weight;
                    }
                }
                (
                    format!("{t} holdings, {:.0}% of fund", covered(held) * 100.0),
                    (den > 0.0).then(|| num / den),
                    held.len(),
                )
            }
            Dir::Root => ("AI universe".into(), None, self.groups_at("primary").len()),
        }
    }

    fn hovered(&self) -> Option<&Entry> {
        self.entries.get(self.cur)
    }

    /// Lists `d` with the cursor where it was last time there.
    fn cd(&mut self, d: Dir) {
        self.marks.insert(self.dir.clone(), self.cur);
        self.entries = self.entries_of(&d);
        self.cur = self
            .marks
            .get(&d)
            .copied()
            .unwrap_or(0)
            .min(self.entries.len().saturating_sub(1));
        self.dir = d;
        self.load_listing();
        self.on_move();
    }

    /// `-`: the directory above, with the cursor on the one just left.
    fn up(&mut self) {
        let Some(p) = self.parent(&self.dir) else {
            return;
        };
        let from = match &self.dir {
            Dir::Holdings(t) => Entry::Ticker(t.clone()),
            d => Entry::Dir(d.clone()),
        };
        self.cd(p);
        self.select(&from);
    }

    /// Puts the cursor on `e` if it is in the listing.
    fn select(&mut self, e: &Entry) {
        if let Some(i) = self.entries.iter().position(|x| x == e) {
            self.cur = i;
            self.on_move();
        }
    }

    /// `{ }`: the sibling directory `step` away (the next sub-sector in this primary, the next
    /// grid...), wrapping around.
    fn sibling(&mut self, step: isize) {
        let Some(p) = self.parent(&self.dir) else {
            return;
        };
        let dirs: Vec<Dir> = self
            .entries_of(&p)
            .into_iter()
            .filter_map(|e| match e {
                Entry::Dir(d) => Some(d),
                Entry::Ticker(_) => None,
            })
            .collect();
        let Some(at) = dirs.iter().position(|d| *d == self.dir) else {
            return;
        };
        let n = dirs.len() as isize;
        let next = dirs[((at as isize + step).rem_euclid(n)) as usize].clone();
        self.cd(next);
    }

    /// Re-lists the directory (after a sort, range or weighting change), cursor kept on its entry.
    fn refresh(&mut self) {
        let on = self.hovered().cloned();
        self.entries = self.entries_of(&self.dir);
        self.cur = self.cur.min(self.entries.len().saturating_sub(1));
        if let Some(e) = on {
            self.select(&e);
        }
        self.on_move();
    }

    fn move_cursor(&mut self, to: usize) {
        self.cur = to.min(self.entries.len().saturating_sub(1));
        self.on_move();
    }

    /// The cursor moved: rebuild the preview when it is on a directory.
    fn on_move(&mut self) {
        self.dirty = true;
        if let Some(Entry::Dir(d)) = self.hovered().cloned() {
            self.tiles = self.preview_tiles(&d);
            self.sel = NO_SEL;
            self.nest = false;
        }
    }

    /// Feeds the listing's tickers to the monitor: their daily closes (once per ticker) and
    /// the live quotes.
    fn load_listing(&mut self) {
        let tickers: Vec<String> = self
            .entries
            .iter()
            .filter_map(|e| match e {
                Entry::Ticker(t) => Some(t.clone()),
                Entry::Dir(_) => None,
            })
            .collect();
        let missing: Vec<String> = tickers
            .iter()
            .filter(|t| !self.monitor.closes.contains_key(*t))
            .cloned()
            .collect();
        if !missing.is_empty() && !cfg!(test) {
            match load_fund_series(&self.db_path, &missing) {
                Ok(mut got) => {
                    for t in missing {
                        // an empty entry marks "asked, none on file" so it isn't asked again
                        let v = got.remove(&t).unwrap_or_default();
                        self.monitor.closes.insert(t, v);
                    }
                }
                Err(e) => self.flash = e,
            }
        }
        self.monitor.watch(&tickers);
    }

    /// The listing as monitor rows.
    fn rows(&self) -> Vec<Row> {
        let name_of: HashMap<&str, &str> = self
            .groups
            .iter()
            .flat_map(|g| &g.members)
            .chain(self.holdings.values().flatten())
            .map(|m| (m.ticker.as_str(), m.name.as_str()))
            .collect();
        self.entries
            .iter()
            .map(|e| match e {
                Entry::Ticker(t) => Row {
                    ticker: t.clone(),
                    name: name_of.get(t.as_str()).copied().unwrap_or("").to_string(),
                    ret: self.ret_of(t),
                    cap: self.caps.get(t).copied(),
                    names: None,
                },
                Entry::Dir(d) => {
                    let (label, ret, n) = self.dir_info(d);
                    Row {
                        ticker: self.entry_name(e),
                        name: label,
                        ret,
                        cap: None,
                        names: Some(n),
                    }
                }
            })
            .collect()
    }

    /// The listing's place among its siblings, 1-based (0 of 0 at the top).
    fn sibling_pos(&self) -> (usize, usize) {
        let Some(p) = self.parent(&self.dir) else {
            return (0, 0);
        };
        let dirs: Vec<Entry> = self
            .entries_of(&p)
            .into_iter()
            .filter(|e| matches!(e, Entry::Dir(_)))
            .collect();
        let at = dirs.iter().position(|e| *e == Entry::Dir(self.dir.clone()));
        at.map_or((0, 0), |i| (i + 1, dirs.len()))
    }

    /// Both panes: the preview over the top, the buffer under it.
    fn draw_oil(&mut self, frame: &mut Frame, body: Rect) {
        let t = self.theme;
        // the listing at the bottom gets 3 rows more than its share
        let list_h = (body.height as u32 * monitor::MONITOR_PCT as u32 / 100) as u16 + 3;
        let [top, bottom] = Layout::vertical([
            Constraint::Min(1),
            Constraint::Length(list_h.min(body.height.saturating_sub(4))),
        ])
        .areas(body);
        let rows = self.rows();
        let (label, ret, _) = self.dir_info(&self.dir);
        let parent_label = self
            .parent(&self.dir)
            .filter(|p| *p != Dir::Root)
            .map(|p| self.dir_info(&p).0);
        let basket = Basket {
            label: &label,
            parent: parent_label.as_deref(),
            ret,
            pos: self.sibling_pos(),
            spec: &self.spec,
            from: self.from,
            to: self.to,
        };
        match self.hovered().cloned() {
            Some(Entry::Ticker(_)) => {
                let ticker_rows: Vec<Row> = rows
                    .iter()
                    .filter(|r| r.names.is_none())
                    .map(|r| Row {
                        ticker: r.ticker.clone(),
                        name: r.name.clone(),
                        ret: r.ret,
                        cap: r.cap,
                        names: None,
                    })
                    .collect();
                if let Some(row) = rows.get(self.cur) {
                    self.monitor
                        .draw_expanded(frame, top, row, &ticker_rows, &basket, &t);
                }
            }
            Some(Entry::Dir(d)) => {
                let (dl, dr, n) = self.dir_info(&d);
                let mut title = vec![
                    Span::styled(
                        format!(" {} ", self.entry_name(&Entry::Dir(d.clone()))),
                        t.title(),
                    ),
                    Span::styled(format!("{dl}  "), t.base()),
                ];
                if let Some(r) = dr {
                    title.push(Span::styled(format!("{r:+.1}%  "), t.signed(r)));
                }
                title.push(Span::styled(format!("{n} names "), t.dim()));
                let block = Block::new()
                    .borders(ratatui::widgets::Borders::ALL)
                    .border_style(t.border())
                    .title(Line::from(title));
                let inner = block.inner(top);
                frame.render_widget(block, top);
                if self.tiles.is_empty() {
                    frame.render_widget(Paragraph::new("empty").style(t.dim()), inner);
                } else {
                    let plates = self.plates(inner);
                    self.draw_map(frame, inner, &plates);
                }
            }
            None => {
                frame.render_widget(Paragraph::new("empty directory").style(t.dim()), top);
            }
        }
        self.monitor
            .draw_table(frame, bottom, &rows, self.cur, &basket, &t);
    }
}

const KEYS: &[Key] = &[
    key("j/k", "move in the buffer"),
    key("g/G", "first / last line"),
    key(
        "↵",
        "into a directory (a fund: its holdings); on a name: its dossier",
    ),
    key("-", "up a directory, cursor on where you were"),
    key("_", "the top of the tree"),
    key("{ }", "previous / next sibling directory"),
    key("D", "dossier for the name under the cursor"),
    key("s", "sort names: weight, today, range, ticker"),
    key("t", "chart: range / today"),
    key("[ ]", "range (live: last close -> now, incl. pre/post)"),
    key("r", "edit the range"),
    key("w", "weighting"),
    key("E", "the same tree in your nvim (oil), beside the screen"),
    key("ctrl-/ ctrl-7", "keys to nvim / back to the buffer"),
    key("ctrl-p", "buffer follows oil's cursor: on / off"),
    key("q", "quit (closes nvim first)"),
    key("esc", "up a directory; at the top, quit"),
];

impl Screen for Universe {
    fn leader_ok(&self) -> bool {
        self.editing.is_none() && !self.nvim_keys()
    }

    /// Quotes and nvim change on their own: redraw when either did.
    fn needs_redraw(&self) -> bool {
        self.dirty
    }

    fn tick(&mut self) -> Action {
        if self.monitor.poll() {
            self.dirty = true;
        }
        if self.poll_live() {
            self.dirty = true;
        }
        if !self.pane_open {
            return Action::None;
        }
        if let Some(nv) = self.nvim.as_mut() {
            if nv.ready() {
                if let Some((rel, name)) = self.pending_reveal.take() {
                    nv.reveal(&rel, name.as_deref());
                }
            }
            if nv.refresh() {
                self.dirty = true;
            }
        }
        if self.follow && self.follow_cursor() {
            self.dirty = true;
        }
        if self.grids_read.elapsed() >= GRIDS_EVERY {
            self.reload_grids();
        }
        Action::None
    }

    /// Frame rate right after a key to nvim, so its echo shows at once; the usual pace else.
    fn poll_interval(&self) -> std::time::Duration {
        let hot = self.pane_open && self.nvim.as_ref().is_some_and(NvimPane::hot);
        std::time::Duration::from_millis(if hot { 12 } else { 100 })
    }

    fn draw(&mut self, frame: &mut Frame) {
        self.dirty = false;
        let t = self.theme;
        let full = frame.area();
        frame.render_widget(Block::new().style(t.base()), full);
        let area = if self.pane_open {
            let w = (full.width * 2 / 5)
                .max(34)
                .min(full.width.saturating_sub(20));
            let [map, pane] =
                Layout::horizontal([Constraint::Min(1), Constraint::Length(w)]).areas(full);
            let focus = self.nvim_focus;
            if let Some(nv) = self.nvim.as_mut() {
                nv.draw(frame, pane, focus, &t);
            }
            map
        } else {
            full
        };
        // The bottom row exists only while the range prompt is open.
        // no title row: the map starts at the top
        let [body, foot] = Layout::vertical([
            Constraint::Min(1),
            Constraint::Length(u16::from(self.editing.is_some())),
        ])
        .areas(area);

        if let Some(buf) = &self.editing {
            let line = Line::from(vec![
                Span::styled(" range > ", t.accent()),
                Span::styled(buf.clone(), t.base()),
                Span::styled("_  enter apply | esc cancel", t.dim()),
            ]);
            frame.render_widget(Paragraph::new(line), foot);
        }

        if !self.entries.is_empty() {
            self.draw_oil(frame, body);
            return;
        }
        // No tree (the universe isn't loaded): the map of whatever tiles there are.
        if self.tiles.is_empty() {
            frame.render_widget(Paragraph::new(NOT_LOADED).style(t.dim()), body);
            return;
        }
        self.draw_body(frame, body);
    }

    fn takes_text(&self) -> bool {
        self.editing.is_some() || self.nvim_keys()
    }

    fn flash_text(&self) -> Option<&str> {
        Some(self.flash.as_str()).filter(|s| !s.is_empty())
    }

    fn help(&self) -> Help {
        Help::new("universe", KEYS)
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if let Some(buf) = self.editing.as_mut() {
            match key.code {
                KeyCode::Esc => self.editing = None,
                KeyCode::Enter => {
                    let spec = std::mem::take(buf);
                    self.editing = None;
                    if self.apply_spec(&spec) {
                        self.refresh();
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

        // ctrl-/ is byte 0x1f, which crossterm reports as `7` with ctrl
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let ctrl_slash = key.code == KeyCode::Char('7') && ctrl;
        if self.nvim_keys() {
            if ctrl_slash {
                self.nvim_focus = false;
            } else if let Some(nv) = self.nvim.as_mut() {
                nv.send_key(key);
            }
            return Action::None;
        }
        if ctrl_slash {
            if self.pane_open {
                self.nvim_focus = true;
            }
            return Action::None;
        }
        if key.code == KeyCode::Char('p') && ctrl {
            self.follow = !self.follow;
            self.flash = if self.follow {
                "buffer follows oil's cursor".into()
            } else {
                "buffer stays put".into()
            };
            return Action::None;
        }
        if self.pane_open && matches!(key.code, KeyCode::Esc | KeyCode::Char('q')) {
            self.pane_open = false;
            return Action::None;
        }

        let n = self.entries.len();
        match key.code {
            KeyCode::Char('q') => return Action::Quit,
            KeyCode::Esc if self.dir == Dir::Root => return Action::Quit,
            KeyCode::Esc | KeyCode::Char('-') => self.up(),
            KeyCode::Char('_') => self.cd(Dir::Root),
            KeyCode::Char('j') | KeyCode::Down => self.move_cursor(self.cur + 1),
            KeyCode::Char('k') | KeyCode::Up => self.move_cursor(self.cur.saturating_sub(1)),
            KeyCode::Char('g') => self.move_cursor(0),
            KeyCode::Char('G') => self.move_cursor(n.saturating_sub(1)),
            KeyCode::Char('}') => self.sibling(1),
            KeyCode::Char('{') => self.sibling(-1),
            KeyCode::Char('E') => self.open_pane(),
            KeyCode::Char('s') => {
                self.monitor.sort = self.monitor.sort.next();
                self.refresh();
            }
            KeyCode::Char('t') => {
                self.monitor.chart = match self.monitor.chart {
                    Chart::Range => Chart::Today,
                    Chart::Today => Chart::Range,
                };
            }
            KeyCode::Char('r') => self.editing = Some(String::new()),
            KeyCode::Char('w') => {
                self.weighting = self.weighting.next();
                self.refresh();
            }
            KeyCode::Char(c @ ('[' | ']')) => {
                let cur = PRESETS.iter().position(|p| *p == self.spec);
                let next = match (cur, c) {
                    (Some(i), ']') => (i + 1).min(PRESETS.len() - 1),
                    (Some(i), _) => i.saturating_sub(1),
                    (None, _) => 3,
                };
                if self.apply_spec(PRESETS[next]) {
                    self.refresh();
                }
            }
            KeyCode::Char('D') => {
                if let Some(Entry::Ticker(t)) = self.hovered() {
                    return Action::Route(Route::Screen {
                        screen: "dossier".into(),
                        arg: Some(t.clone()),
                    });
                }
            }
            KeyCode::Enter => match self.hovered().cloned() {
                Some(Entry::Dir(d)) => self.cd(d),
                Some(Entry::Ticker(t)) => {
                    let in_funds =
                        matches!(self.dir, Dir::Basket(i) if Some(i) == self.funds_group());
                    if in_funds && self.holdings.get(&t).is_some_and(|h| !h.is_empty()) {
                        self.cd(Dir::Holdings(t));
                    } else {
                        return Action::Route(Route::Screen {
                            screen: "dossier".into(),
                            arg: Some(t),
                        });
                    }
                }
                None => {}
            },
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
        u.on_key(KeyEvent::new(KeyCode::Enter, KeyModifiers::NONE));
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
        u.nest = true;
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

    /// Two primaries, three sub-sectors, a fund list with holdings.
    fn tree() -> Universe {
        let m = |t: &str| Member {
            ticker: t.into(),
            name: format!("{t} Inc"),
            weight: 0.5,
        };
        let g = |level: &str, label: &str, order: i32, parent: Option<&str>, ms: &[&str]| Group {
            level: level.into(),
            name: label.to_lowercase(),
            label: label.into(),
            order,
            parent: parent.map(String::from),
            members: ms.iter().map(|t| m(t)).collect(),
        };
        let mut u = bare(vec![]);
        u.groups = vec![
            g("primary", "Compute & Semis", 1, None, &["MU", "NVDA"]),
            g("primary", "Power & Energy", 2, None, &["VST"]),
            g(
                "sub",
                "Memory & Storage",
                2,
                Some("Compute & Semis"),
                &["MU", "SNDK"],
            ),
            g("sub", "Processors", 1, Some("Compute & Semis"), &["NVDA"]),
            g("sub", "Utilities", 1, Some("Power & Energy"), &["VST"]),
            g("fund", "Funds", 0, None, &["DRAM", "QQQ"]),
        ];
        u.holdings = HashMap::from([("DRAM".to_string(), vec![m("MU"), m("SNDK")])]);
        u.caps = HashMap::from([("MU".to_string(), 1e11), ("SNDK".to_string(), 2e11)]);
        u.weighting = Weighting::Cap;
        u.cd(Dir::Root);
        u
    }

    fn press(u: &mut Universe, code: KeyCode) {
        u.on_key(KeyEvent::new(code, KeyModifiers::NONE));
    }

    fn names(u: &Universe) -> Vec<String> {
        u.entries.iter().map(|e| u.entry_name(e)).collect()
    }

    #[test]
    fn the_buffer_walks_the_tree_like_oil() {
        let mut u = tree();
        assert_eq!(
            names(&u),
            ["compute_semis/", "power_energy/", "funds/", "~grids/"]
        );
        press(&mut u, KeyCode::Enter);
        assert_eq!(u.dir, Dir::Primary(0));
        // sub-sectors in taxonomy order
        assert_eq!(names(&u), ["processors/", "memory_storage/"]);
        press(&mut u, KeyCode::Char('j'));
        press(&mut u, KeyCode::Enter);
        assert_eq!(u.dir, Dir::Basket(2));
        // names by market cap under cap weighting
        assert_eq!(names(&u), ["SNDK", "MU"]);
        // - goes up with the cursor on the directory just left
        press(&mut u, KeyCode::Char('-'));
        assert_eq!(u.dir, Dir::Primary(0));
        assert_eq!(u.hovered(), Some(&Entry::Dir(Dir::Basket(2))));
        press(&mut u, KeyCode::Char('-'));
        assert_eq!(u.hovered(), Some(&Entry::Dir(Dir::Primary(0))));
        // esc at the top quits
        assert!(matches!(
            u.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE)),
            Action::Quit
        ));
    }

    #[test]
    fn a_directory_under_the_cursor_previews_as_a_heatmap() {
        let mut u = tree();
        // on compute_semis/: one box per sub-sector inside it
        let titles: Vec<&str> = u.tiles.iter().map(|t| t.title.as_str()).collect();
        assert_eq!(titles.len(), 2);
        assert!(titles.contains(&"Memory & Storage") && titles.contains(&"Processors"));
        press(&mut u, KeyCode::Char('j'));
        let titles: Vec<&str> = u.tiles.iter().map(|t| t.title.as_str()).collect();
        assert_eq!(titles, ["Utilities"]);
    }

    #[test]
    fn braces_step_to_the_next_sibling_and_wrap() {
        let mut u = tree();
        u.cd(Dir::Basket(3)); // processors
        press(&mut u, KeyCode::Char('}'));
        assert_eq!(u.dir, Dir::Basket(2));
        press(&mut u, KeyCode::Char('}'));
        assert_eq!(u.dir, Dir::Basket(3), "wraps within the primary");
        press(&mut u, KeyCode::Char('{'));
        assert_eq!(u.dir, Dir::Basket(2));
    }

    #[test]
    fn enter_on_a_fund_lists_its_holdings_and_minus_comes_back_to_it() {
        let mut u = tree();
        u.cd(Dir::Basket(5));
        assert_eq!(u.hovered(), Some(&Entry::Ticker("DRAM".into())));
        press(&mut u, KeyCode::Enter);
        assert_eq!(u.dir, Dir::Holdings("DRAM".into()));
        assert_eq!(
            names(&u),
            ["MU", "SNDK"],
            "the fund's own weights order them"
        );
        press(&mut u, KeyCode::Char('-'));
        assert_eq!(u.dir, Dir::Basket(5));
        assert_eq!(u.hovered(), Some(&Entry::Ticker("DRAM".into())));
        // enter on a plain name opens its dossier
        u.move_cursor(1);
        assert!(matches!(
            u.on_key(KeyEvent::new(KeyCode::Enter, KeyModifiers::NONE)),
            Action::Route(_)
        ));
    }

    #[test]
    fn oil_cursor_lands_the_buffer_on_the_same_entry() {
        let mut u = tree();
        u.go_to(Spot::Groups {
            level: "sub".into(),
            pick: Some("2".into()),
        });
        assert_eq!(u.dir, Dir::Primary(0));
        assert_eq!(u.hovered(), Some(&Entry::Dir(Dir::Basket(2))));
        u.go_to(Spot::Members {
            group: 2,
            pick: Some("MU".into()),
        });
        assert_eq!(u.dir, Dir::Basket(2));
        assert_eq!(u.hovered(), Some(&Entry::Ticker("MU".into())));
    }

    #[test]
    fn live_range_reads_since_close_moves() {
        let (rets, asof) = parse_live(
            r#"{"asof": 1795443889, "moves": [{"symbol": "NVDA", "pct": 31.4}, {"symbol": "X"}]}"#,
        )
        .unwrap();
        assert_eq!(asof, Some(1795443889));
        assert_eq!(rets.len(), 1);
        let mut u = tree();
        u.live.rets = rets;
        assert!(u.apply_spec("live"));
        assert_eq!(u.ret_of("NVDA"), Some(31.4));
        assert_eq!(u.ret_of("MU"), None);
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
            dir: Dir::Root,
            entries: Vec::new(),
            cur: 0,
            marks: HashMap::new(),
            tiles,
            sel: 0,
            nest: false,
            editing: None,
            flash: String::new(),
            body: Rect::default(),
            tree: Tree::default(),
            grids_from: 0,
            grids_read: Instant::now(),
            nvim: None,
            pane_open: false,
            nvim_focus: false,
            follow: true,
            cursor_seen: None,
            cursor_rel: String::new(),
            pending_reveal: None,
            dirty: false,
            monitor: Monitor::default(),
            live: Live::default(),
        }
    }

    fn tile(title: &str, weight: f64, ret: Option<f64>) -> Tile {
        Tile {
            title: title.into(),
            sub: String::new(),
            ret,
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
        // Rows 2..19 are the map (header is 2 rows). No line art left in it.
        let map: String = out.lines().skip(2).take(17).collect::<Vec<_>>().join("\n");
        assert!(
            !map.contains(['|', '#']),
            "line art left in the map:\n{map}"
        );
    }
}
