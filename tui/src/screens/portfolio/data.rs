// Data + metrics for the portfolio screen. Everything here is read-only
// DuckDB (portfolio_history, positions_cache, history_cache) plus the AI
// universe JSON for industry labels; the metrics are pure functions over
// those rows so they can be unit-tested without a database.
//
// Returns are time-weighted: the equity index chains each day's
// `day_change_pct` (which py/sources/etrade.py computes net of same-day
// transfers), so deposits and withdrawals never show up as performance.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use chrono::{DateTime, NaiveDate};

#[derive(Debug, Clone, PartialEq)]
pub struct Snapshot {
    pub date: NaiveDate,
    pub value: f64,
    /// Time-weighted % change for the day (0 for the first row).
    pub day_pct: f64,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Position {
    pub symbol: String,
    pub qty: f64,
    pub price: f64,
    pub price_paid: f64,
    pub total_gain: f64,
    pub value: f64,
    pub day_gain: f64,
    pub day_pct: f64,
    /// Dominant niche from ai_stocks.json ("memory storage"), "Other" if unknown.
    pub industry: String,
}

impl Position {
    pub fn cost(&self) -> f64 {
        self.price_paid * self.qty
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Range {
    OneM,
    ThreeM,
    SixM,
    OneY,
    All,
}

impl Range {
    pub const ALL: [Range; 5] = [
        Range::OneM,
        Range::ThreeM,
        Range::SixM,
        Range::OneY,
        Range::All,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Range::OneM => "1M",
            Range::ThreeM => "3M",
            Range::SixM => "6M",
            Range::OneY => "1Y",
            Range::All => "ALL",
        }
    }

    pub fn days(self) -> Option<i64> {
        match self {
            Range::OneM => Some(30),
            Range::ThreeM => Some(90),
            Range::SixM => Some(182),
            Range::OneY => Some(365),
            Range::All => None,
        }
    }

    pub fn next(self) -> Range {
        let i = Self::ALL.iter().position(|r| *r == self).unwrap_or(0);
        Self::ALL[(i + 1) % Self::ALL.len()]
    }

    pub fn index(self) -> usize {
        Self::ALL.iter().position(|r| *r == self).unwrap_or(0)
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Bench {
    Spy,
    Qqq,
    Soxx,
}

impl Bench {
    pub const ALL: [Bench; 3] = [Bench::Spy, Bench::Qqq, Bench::Soxx];

    pub fn symbol(self) -> &'static str {
        match self {
            Bench::Spy => "SPY",
            Bench::Qqq => "QQQ",
            Bench::Soxx => "SOXX",
        }
    }
    pub fn next(self) -> Bench {
        match self {
            Bench::Spy => Bench::Qqq,
            Bench::Qqq => Bench::Soxx,
            Bench::Soxx => Bench::Spy,
        }
    }
}

#[derive(Debug, Default)]
pub struct Data {
    pub history: Vec<Snapshot>,
    pub positions: Vec<Position>,
    /// Unix seconds the positions were last pulled from E*TRADE.
    pub positions_at: Option<f64>,
    pub bench: HashMap<&'static str, Vec<(NaiveDate, f64)>>,
    /// Daily closes per held symbol (longest cached range), oldest first.
    pub closes: HashMap<String, Vec<(NaiveDate, f64)>>,
    /// Cached E*TRADE transactions (all accounts), oldest first.
    pub txns: Vec<Txn>,
}

/// One cached E*TRADE transaction. `amount` is the cash effect (buys
/// negative, sells and income positive); `qty` is signed shares.
#[derive(Debug, Clone, PartialEq)]
pub struct Txn {
    pub date: NaiveDate,
    pub kind: String,
    pub symbol: String,
    pub qty: f64,
    pub price: f64,
    pub amount: f64,
}

/// `transactions_cache` rows: `[{"date": epoch_ms, "type", "symbol",
/// "quantity", "price", "amount"}, ...]`. Rows without a symbol or date
/// (transfers) are dropped.
pub fn parse_txns(json: &str) -> Vec<Txn> {
    let Ok(serde_json::Value::Array(items)) = serde_json::from_str::<serde_json::Value>(json)
    else {
        return Vec::new();
    };
    items
        .iter()
        .filter_map(|t| {
            let ms = t.get("date")?.as_i64()?;
            Some(Txn {
                date: DateTime::from_timestamp_millis(ms)?.date_naive(),
                kind: t.get("type")?.as_str()?.to_string(),
                symbol: t.get("symbol")?.as_str()?.to_string(),
                qty: num(t, "quantity"),
                price: num(t, "price"),
                amount: num(t, "amount"),
            })
        })
        .collect()
}

/// Whole-history roll-up for one symbol from the transaction cache.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct SymbolHistory {
    /// Gross cash spent on buys (positive).
    pub bought: f64,
    pub sold: f64,
    /// Dividends and interest.
    pub income: f64,
    pub trades: usize,
    pub first: Option<NaiveDate>,
    /// Shares implied by the transactions (buys, sells, splits).
    pub net_shares: f64,
    /// Buys and sells, newest first.
    pub recent: Vec<Txn>,
}

pub fn symbol_history(txns: &[Txn], symbol: &str) -> SymbolHistory {
    let mut h = SymbolHistory::default();
    for t in txns.iter().filter(|t| t.symbol == symbol) {
        h.first = Some(h.first.map_or(t.date, |f| f.min(t.date)));
        match t.kind.as_str() {
            "Bought" => {
                h.bought -= t.amount;
                h.net_shares += t.qty;
                h.trades += 1;
                h.recent.push(t.clone());
            }
            "Sold" => {
                h.sold += t.amount;
                h.net_shares += t.qty;
                h.trades += 1;
                h.recent.push(t.clone());
            }
            "Stock Split" => h.net_shares += t.qty,
            "Dividend" | "Qualified Dividend" | "Interest Income" => h.income += t.amount,
            _ => {}
        }
    }
    h.recent.sort_by(|a, b| b.date.cmp(&a.date));
    h
}

impl SymbolHistory {
    /// All-time P&L: what you hold now plus everything that came back
    /// (sales, dividends) minus everything put in.
    pub fn all_time_pnl(&self, value: f64) -> f64 {
        value + self.sold + self.income - self.bought
    }

    /// False when the cache (a 2-year pull) misses older lots, i.e. the
    /// transactions don't add up to the shares E*TRADE says you hold.
    pub fn complete(&self, qty: f64) -> bool {
        self.trades > 0 && (self.net_shares - qty).abs() < 0.01
    }
}

pub fn load(db_path: &Path) -> Result<Data, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let e = |e: duckdb::Error| e.to_string();

    let mut history = Vec::new();
    {
        let mut stmt = conn
            .prepare(
                "SELECT CAST(date AS VARCHAR), total_value, day_change_pct \
                 FROM portfolio_history ORDER BY date",
            )
            .map_err(e)?;
        let rows = stmt
            .query_map([], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, Option<f64>>(1)?,
                    r.get::<_, Option<f64>>(2)?,
                ))
            })
            .map_err(e)?;
        for row in rows {
            let (date, value, pct) = row.map_err(e)?;
            // a NULL total_value is a missing snapshot: skip, never plot as 0
            if let (Ok(date), Some(value)) = (NaiveDate::parse_from_str(&date, "%Y-%m-%d"), value) {
                history.push(Snapshot {
                    date,
                    value,
                    day_pct: pct.unwrap_or(0.0),
                });
            }
        }
    }

    let industries = load_industries();
    let mut positions = Vec::new();
    let mut positions_at = None;
    {
        let mut stmt = conn
            .prepare("SELECT positions_json, fetched_at FROM positions_cache WHERE id = 0")
            .map_err(e)?;
        let row = stmt
            .query_row([], |r| {
                Ok((r.get::<_, String>(0)?, r.get::<_, Option<f64>>(1)?))
            })
            .ok();
        if let Some((json, at)) = row {
            positions_at = at;
            positions = parse_positions(&json, &industries);
        }
    }

    // Longest cached daily range per symbol; the cache holds 1y and 2y.
    let mut closes = HashMap::new();
    {
        let mut stmt = conn
            .prepare(
                "SELECT symbol, points_json FROM history_cache WHERE interval = '1d' \
                 QUALIFY row_number() OVER (PARTITION BY symbol ORDER BY length(points_json) DESC) = 1",
            )
            .map_err(e)?;
        let rows = stmt
            .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))
            .map_err(e)?;
        for (sym, json) in rows.flatten() {
            let held = positions.iter().any(|p| p.symbol == sym);
            if held || Bench::ALL.iter().any(|b| b.symbol() == sym) {
                closes.insert(sym, parse_closes(&json));
            }
        }
    }
    let bench = Bench::ALL
        .iter()
        .filter_map(|b| Some((b.symbol(), closes.get(b.symbol())?.clone())))
        .collect();
    let mut txns = Vec::new();
    {
        let mut stmt = conn
            .prepare("SELECT transactions_json FROM transactions_cache")
            .map_err(e)?;
        let rows = stmt.query_map([], |r| r.get::<_, String>(0)).map_err(e)?;
        for json in rows.flatten() {
            txns.extend(parse_txns(&json));
        }
        txns.sort_by_key(|t| t.date);
    }
    Ok(Data {
        history,
        positions,
        positions_at,
        bench,
        closes,
        txns,
    })
}

fn num(v: &serde_json::Value, k: &str) -> f64 {
    v.get(k).and_then(|x| x.as_f64()).unwrap_or(0.0)
}

pub fn parse_positions(json: &str, industries: &HashMap<String, String>) -> Vec<Position> {
    let Ok(serde_json::Value::Array(items)) = serde_json::from_str::<serde_json::Value>(json)
    else {
        return Vec::new();
    };
    let mut out: Vec<Position> = items
        .iter()
        .filter_map(|p| {
            let symbol = p.get("symbol")?.as_str()?.to_string();
            let industry = industries
                .get(&symbol)
                .cloned()
                .unwrap_or_else(|| "Other".into());
            Some(Position {
                qty: num(p, "quantity"),
                price: num(p, "last_price"),
                price_paid: num(p, "price_paid"),
                total_gain: num(p, "total_gain"),
                value: num(p, "market_value"),
                day_gain: num(p, "change_close"),
                day_pct: num(p, "change_close_pct"),
                symbol,
                industry,
            })
        })
        .collect();
    out.sort_by(|a, b| b.value.total_cmp(&a.value));
    out
}

/// `[{"t": unix_seconds, "close": f64}, ...]` -> (UTC date, close).
pub fn parse_closes(json: &str) -> Vec<(NaiveDate, f64)> {
    let Ok(serde_json::Value::Array(items)) = serde_json::from_str::<serde_json::Value>(json)
    else {
        return Vec::new();
    };
    items
        .iter()
        .filter_map(|p| {
            let t = p.get("t")?.as_i64()?;
            let c = p.get("close")?.as_f64()?;
            Some((DateTime::from_timestamp(t, 0)?.date_naive(), c))
        })
        .collect()
}

/// ticker -> dominant niche, from data/ai_stocks.json next to the crate.
/// Missing file or ticker just means "Other"; FINLARP_UNIVERSE
/// overrides the path.
fn load_industries() -> HashMap<String, String> {
    let path = std::env::var_os("FINLARP_UNIVERSE")
        .map(PathBuf::from)
        .or_else(|| {
            // target/release/finlarp -> crate -> plugin dir
            let exe = std::env::current_exe().ok()?;
            let plugin = exe.ancestors().nth(4)?;
            Some(plugin.join("data/ai_stocks.json"))
        });
    let Some(text) = path.and_then(|p| std::fs::read_to_string(p).ok()) else {
        return HashMap::new();
    };
    parse_industries(&text)
}

pub fn parse_industries(text: &str) -> HashMap<String, String> {
    let Ok(v) = serde_json::from_str::<serde_json::Value>(text) else {
        return HashMap::new();
    };
    let mut out = HashMap::new();
    for s in v
        .get("stocks")
        .and_then(|s| s.as_array())
        .into_iter()
        .flatten()
    {
        let (Some(t), Some(subs)) = (
            s.get("ticker").and_then(|t| t.as_str()),
            s.get("subs").and_then(|s| s.as_object()),
        ) else {
            continue;
        };
        // dominant niche = highest weight
        if let Some((k, _)) = subs.iter().max_by(|a, b| {
            a.1.as_f64()
                .unwrap_or(0.0)
                .total_cmp(&b.1.as_f64().unwrap_or(0.0))
        }) {
            out.insert(t.to_string(), k.replace('_', " "));
        }
    }
    out
}

/// Trailing window of `range`, anchored to the last snapshot.
pub fn window(history: &[Snapshot], range: Range) -> &[Snapshot] {
    let (Some(days), Some(last)) = (range.days(), history.last()) else {
        return history;
    };
    let cutoff = last.date - chrono::Duration::days(days);
    let start = history.iter().position(|s| s.date >= cutoff).unwrap_or(0);
    &history[start..]
}

/// Time-weighted % change since the window start, one entry per snapshot
/// (first entry is 0). Chains `day_pct`, so transfers are excluded.
pub fn twr_pct(win: &[Snapshot]) -> Vec<f64> {
    let mut idx = 1.0;
    win.iter()
        .enumerate()
        .map(|(i, s)| {
            if i > 0 {
                idx *= 1.0 + s.day_pct / 100.0;
            }
            (idx - 1.0) * 100.0
        })
        .collect()
}

/// Benchmark % change since the first window date, forward-filled onto
/// the window's dates. None if the benchmark has no close on/before the start.
pub fn bench_pct(win: &[Snapshot], closes: &[(NaiveDate, f64)]) -> Option<Vec<f64>> {
    let first = win.first()?;
    let at = |d: NaiveDate| {
        closes
            .iter()
            .rev()
            .find(|(cd, _)| *cd <= d)
            .map(|(_, c)| *c)
    };
    let base = at(first.date)?;
    win.iter()
        .map(|s| at(s.date).map(|c| (c / base - 1.0) * 100.0))
        .collect()
}

/// Drawdown in % (<= 0) from the running peak of the TWR index.
pub fn drawdown(twr: &[f64]) -> Vec<f64> {
    let mut peak = f64::MIN;
    twr.iter()
        .map(|&p| {
            let idx = 1.0 + p / 100.0;
            peak = peak.max(idx);
            (idx / peak - 1.0) * 100.0
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct Stats {
    pub ret: f64,
    pub bench_ret: Option<f64>,
    pub max_dd: f64,
    pub cur_dd: f64,
    /// Annualised stdev of daily returns, %.
    pub vol: f64,
    pub best_day: (f64, Option<NaiveDate>),
    pub worst_day: (f64, Option<NaiveDate>),
    pub up_days: f64,
}

pub fn stats(win: &[Snapshot], twr: &[f64], bench: Option<&[f64]>) -> Stats {
    let dd = drawdown(twr);
    let days: Vec<&Snapshot> = win.iter().skip(1).collect();
    let n = days.len() as f64;
    let mean = if n > 0.0 {
        days.iter().map(|s| s.day_pct).sum::<f64>() / n
    } else {
        0.0
    };
    let var = if n > 1.0 {
        days.iter().map(|s| (s.day_pct - mean).powi(2)).sum::<f64>() / (n - 1.0)
    } else {
        0.0
    };
    let pick = |best: bool| {
        days.iter()
            .copied()
            .max_by(|a, b| {
                let o = a.day_pct.total_cmp(&b.day_pct);
                if best { o } else { o.reverse() }
            })
            .map_or((0.0, None), |s| (s.day_pct, Some(s.date)))
    };
    Stats {
        ret: twr.last().copied().unwrap_or(0.0),
        bench_ret: bench.and_then(|b| b.last().copied()),
        max_dd: dd.iter().copied().fold(0.0, f64::min),
        cur_dd: dd.last().copied().unwrap_or(0.0),
        vol: var.sqrt() * 252f64.sqrt(),
        best_day: pick(true),
        worst_day: pick(false),
        up_days: if n > 0.0 {
            days.iter().filter(|s| s.day_pct > 0.0).count() as f64 / n * 100.0
        } else {
            0.0
        },
    }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub struct Totals {
    pub value: f64,
    pub invested: f64,
    pub cash: f64,
    pub day_gain: f64,
    pub day_pct: f64,
    pub total_gain: f64,
    pub total_pct: f64,
}

/// Account value comes from the latest snapshot (cash + positions); cash is
/// what's left after positions, clamped at 0 since the snapshot and
/// positions are pulled at slightly different moments.
pub fn totals(history: &[Snapshot], positions: &[Position]) -> Totals {
    let invested: f64 = positions.iter().map(|p| p.value).sum();
    let value = history.last().map_or(invested, |s| s.value.max(invested));
    let day_gain: f64 = positions.iter().map(|p| p.day_gain).sum();
    let cost: f64 = positions.iter().map(Position::cost).sum();
    let total_gain: f64 = positions.iter().map(|p| p.total_gain).sum();
    let prev = invested - day_gain;
    Totals {
        value,
        invested,
        cash: (value - invested).max(0.0),
        day_gain,
        day_pct: if prev > 0.0 {
            day_gain / prev * 100.0
        } else {
            0.0
        },
        total_gain,
        total_pct: if cost > 0.0 {
            total_gain / cost * 100.0
        } else {
            0.0
        },
    }
}

/// Allocation rows (label, weight % of account value), largest first, with
/// a trailing Cash row. Small industries fold into "Other" past `max` rows.
pub fn allocation(positions: &[Position], t: &Totals, max: usize) -> Vec<(String, f64)> {
    if t.value <= 0.0 {
        return Vec::new();
    }
    let mut by: HashMap<&str, f64> = HashMap::new();
    for p in positions {
        *by.entry(p.industry.as_str()).or_default() += p.value;
    }
    let mut rows: Vec<(String, f64)> = by
        .into_iter()
        .map(|(k, v)| (k.to_string(), v / t.value * 100.0))
        .collect();
    rows.sort_by(|a, b| b.1.total_cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    if rows.len() > max.saturating_sub(1) {
        let rest: f64 = rows
            .split_off(max.saturating_sub(2))
            .iter()
            .map(|r| r.1)
            .sum();
        if let Some(o) = rows.iter_mut().find(|r| r.0 == "Other") {
            o.1 += rest;
        } else {
            rows.push(("Other".into(), rest));
        }
    }
    rows.push(("Cash".into(), t.cash / t.value * 100.0));
    rows
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Level {
    Warn,
    Info,
}

/// Rule-based alerts over data we actually have. `now` is unix seconds.
pub fn alerts(
    positions: &[Position],
    t: &Totals,
    st: &Stats,
    positions_at: Option<f64>,
    now: f64,
) -> Vec<(Level, String)> {
    let mut out = Vec::new();
    if let Some(at) = positions_at
        && now - at > 24.0 * 3600.0
    {
        out.push((
            Level::Warn,
            format!(
                "positions {}h old: refresh with $",
                ((now - at) / 3600.0) as i64
            ),
        ));
    }
    if t.value > 0.0 {
        for p in positions.iter().take(3) {
            let w = p.value / t.value * 100.0;
            if w >= 20.0 {
                out.push((
                    Level::Warn,
                    format!("{} is {w:.0}% of the account", p.symbol),
                ));
            }
        }
        let top3: f64 = positions.iter().take(3).map(|p| p.value).sum::<f64>() / t.value * 100.0;
        if top3 >= 50.0 {
            out.push((
                Level::Info,
                format!("top 3 names are {top3:.0}% of the account"),
            ));
        }
        let cash = t.cash / t.value * 100.0;
        if cash >= 15.0 {
            out.push((Level::Info, format!("cash is {cash:.0}% of the account")));
        }
    }
    for p in positions {
        if p.day_pct.abs() >= 5.0 {
            out.push((
                Level::Info,
                format!("{} {:+.1}% today", p.symbol, p.day_pct),
            ));
        }
    }
    if st.cur_dd <= -10.0 {
        out.push((Level::Warn, format!("in a {:.1}% drawdown", st.cur_dd)));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(s: &str) -> NaiveDate {
        NaiveDate::parse_from_str(s, "%Y-%m-%d").unwrap()
    }

    fn snaps(pcts: &[f64]) -> Vec<Snapshot> {
        pcts.iter()
            .enumerate()
            .map(|(i, &p)| Snapshot {
                date: d("2026-01-01") + chrono::Duration::days(i as i64),
                value: 1000.0,
                day_pct: p,
            })
            .collect()
    }

    #[test]
    fn twr_chains_daily_returns_and_ignores_first_day_pct() {
        let s = snaps(&[9.0, 10.0, -10.0]);
        let t = twr_pct(&s);
        assert_eq!(t[0], 0.0);
        assert!((t[1] - 10.0).abs() < 1e-9);
        assert!((t[2] - (1.1 * 0.9 - 1.0) * 100.0).abs() < 1e-9);
    }

    #[test]
    fn drawdown_tracks_peak() {
        let dd = drawdown(&[0.0, 10.0, 0.0]);
        assert_eq!(dd[0], 0.0);
        assert_eq!(dd[1], 0.0);
        assert!((dd[2] - (1.0 / 1.1 - 1.0) * 100.0).abs() < 1e-9);
    }

    #[test]
    fn bench_forward_fills_weekends() {
        let s = snaps(&[0.0, 0.0, 0.0]);
        let closes = vec![(d("2026-01-01"), 100.0), (d("2026-01-03"), 110.0)];
        let b = bench_pct(&s, &closes).unwrap();
        assert_eq!(b.len(), 3);
        assert_eq!(b[1], 0.0); // 01-02 carries the 01-01 close
        assert!((b[2] - 10.0).abs() < 1e-9);
    }

    #[test]
    fn bench_none_without_a_start_close() {
        let s = snaps(&[0.0]);
        assert!(bench_pct(&s, &[(d("2026-02-01"), 1.0)]).is_none());
    }

    #[test]
    fn window_anchors_to_latest_snapshot() {
        let s = snaps(&vec![0.0; 100]);
        let w = window(&s, Range::OneM);
        assert_eq!(w.last(), s.last());
        assert_eq!(w.len(), 31);
        assert_eq!(window(&s, Range::All).len(), 100);
    }

    #[test]
    fn stats_best_worst_and_up_days() {
        let s = snaps(&[0.0, 2.0, -3.0, 1.0]);
        let t = twr_pct(&s);
        let st = stats(&s, &t, None);
        assert_eq!(st.best_day.0, 2.0);
        assert_eq!(st.worst_day.0, -3.0);
        assert!((st.up_days - 200.0 / 3.0).abs() < 1e-9);
        assert!(st.max_dd < 0.0);
    }

    fn pos(sym: &str, value: f64, day_gain: f64, industry: &str) -> Position {
        Position {
            symbol: sym.into(),
            qty: 1.0,
            price: value,
            price_paid: value * 0.8,
            total_gain: value * 0.2,
            value,
            day_gain,
            day_pct: day_gain / value * 100.0,
            industry: industry.into(),
        }
    }

    #[test]
    fn totals_cash_is_remainder_and_clamped() {
        let ps = vec![pos("A", 600.0, 6.0, "x"), pos("B", 300.0, -3.0, "y")];
        let t = totals(&snaps(&[0.0]), &ps); // snapshot value 1000
        assert_eq!(t.invested, 900.0);
        assert_eq!(t.cash, 100.0);
        assert_eq!(t.day_gain, 3.0);
        // positions worth more than the (stale) snapshot: cash clamps to 0
        let big = vec![pos("A", 2000.0, 0.0, "x")];
        assert_eq!(totals(&snaps(&[0.0]), &big).cash, 0.0);
    }

    #[test]
    fn allocation_sums_to_100_with_cash_last() {
        let ps = vec![
            pos("A", 400.0, 0.0, "semis"),
            pos("B", 300.0, 0.0, "semis"),
            pos("C", 200.0, 0.0, "power"),
        ];
        let t = totals(&snaps(&[0.0]), &ps);
        let a = allocation(&ps, &t, 6);
        assert_eq!(a[0].0, "semis");
        assert_eq!(a.last().unwrap().0, "Cash");
        let sum: f64 = a.iter().map(|r| r.1).sum();
        assert!((sum - 100.0).abs() < 1e-9);
    }

    #[test]
    fn allocation_folds_the_tail_into_other() {
        let ps: Vec<Position> = (0..8)
            .map(|i| pos(&format!("S{i}"), 100.0 - i as f64, 0.0, &format!("ind{i}")))
            .collect();
        let t = totals(&snaps(&[0.0]), &ps);
        let a = allocation(&ps, &t, 4);
        assert_eq!(a.len(), 4); // 2 named + Other + Cash
        assert!(a.iter().any(|r| r.0 == "Other"));
        let sum: f64 = a.iter().map(|r| r.1).sum();
        assert!((sum - 100.0).abs() < 1e-9);
    }

    #[test]
    fn alerts_flag_concentration_and_stale_positions() {
        let ps = vec![pos("BIG", 900.0, 0.0, "x"), pos("S", 50.0, 0.0, "x")];
        let t = totals(&snaps(&[0.0]), &ps);
        let st = Stats::default();
        let a = alerts(&ps, &t, &st, Some(0.0), 3.0 * 24.0 * 3600.0);
        assert!(a.iter().any(|(_, m)| m.contains("BIG is 90%")));
        assert!(a.iter().any(|(_, m)| m.contains("72h old")));
    }

    #[test]
    fn parses_positions_and_industries() {
        let ind = parse_industries(
            r#"{"stocks":[{"ticker":"MU","subs":{"memory_storage":0.9,"x":0.1}}]}"#,
        );
        assert_eq!(ind["MU"], "memory storage");
        let ps = parse_positions(
            r#"[{"symbol":"MU","quantity":2,"last_price":10,"price_paid":5,
                 "total_gain":10,"market_value":20,"change_close":1,"change_close_pct":5.0},
                {"symbol":"ZZZ","market_value":50}]"#,
            &ind,
        );
        assert_eq!(ps[0].symbol, "ZZZ"); // sorted by value
        assert_eq!(ps[0].industry, "Other");
        assert_eq!(ps[1].industry, "memory storage");
        assert_eq!(ps[1].cost(), 10.0);
    }

    #[test]
    fn parses_closes_to_utc_dates() {
        let c = parse_closes(r#"[{"t":1786541400,"close":302.25},{"bad":1}]"#);
        assert_eq!(c.len(), 1);
        assert_eq!(c[0].1, 302.25);
    }

    #[test]
    fn symbol_history_rolls_up_cash_flow_and_flags_gaps() {
        let json = r#"[
            {"date":1735689600000,"type":"Bought","symbol":"X","quantity":10,"price":10,"amount":-100},
            {"date":1738368000000,"type":"Sold","symbol":"X","quantity":-4,"price":15,"amount":60},
            {"date":1740787200000,"type":"Dividend","symbol":"X","quantity":0,"price":0,"amount":2},
            {"date":1740787200000,"type":"Bought","symbol":"Y","quantity":1,"price":5,"amount":-5},
            {"date":1740787200000,"type":"Online Transfer","symbol":null,"quantity":0,"price":0,"amount":500}
        ]"#;
        let txns = parse_txns(json);
        assert_eq!(txns.len(), 4);
        let h = symbol_history(&txns, "X");
        assert_eq!(
            (h.bought, h.sold, h.income, h.trades),
            (100.0, 60.0, 2.0, 2)
        );
        assert_eq!(h.recent[0].kind, "Sold");
        // 6 shares left worth 120: 120 + 60 + 2 - 100
        assert_eq!(h.all_time_pnl(120.0), 82.0);
        assert!(h.complete(6.0));
        assert!(!h.complete(9.0));
    }
}
