// Data + metrics for the portfolio screen. Everything here is read-only
// DuckDB (portfolio_history, positions_cache, history_cache) plus the AI
// universe JSON for industry labels; the metrics are pure functions over
// those rows so they can be unit-tested without a database.
//
// Returns are time-weighted: the equity index chains each day's
// `day_change_pct` (which py/sources/etrade.py computes net of same-day
// transfers), so deposits and withdrawals never show up as performance.

use std::collections::{HashMap, HashSet};
use std::path::Path;

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
    /// Dominant niche from the universe tables ("memory storage"), "Other" if unknown.
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
    /// Daily closes per held or traded symbol (longest cached range), oldest first.
    pub closes: HashMap<String, Vec<(NaiveDate, f64)>>,
    /// Cached E*TRADE transactions (all accounts), oldest first.
    pub txns: Vec<Txn>,
    /// Derived from the rows above; filled in by `load`.
    pub exposure: Exposure,
}

/// One cached E*TRADE transaction. `amount` is the cash effect (buys
/// negative, sells and income positive); `qty` is signed shares.
#[derive(Debug, Clone, PartialEq)]
pub struct Txn {
    /// E*TRADE `transaction_id`. The cache can hold the same record twice.
    pub id: String,
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
                id: t
                    .get("transaction_id")
                    .and_then(|v| v.as_str())
                    .unwrap_or_default()
                    .to_string(),
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

/// Drops repeat records of the same E*TRADE transaction, keeping the first.
/// Rows without an id are never treated as duplicates.
pub fn dedupe_txns(txns: &mut Vec<Txn>) {
    let mut seen = HashSet::new();
    txns.retain(|t| t.id.is_empty() || seen.insert(t.id.clone()));
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

    let industries = load_industries(&conn);
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
        dedupe_txns(&mut txns);
    }

    // Longest cached daily range per symbol; the cache holds 1y and 2y.
    // Traded symbols too, so the drift replay can price names sold off.
    let traded: HashSet<&str> = txns.iter().map(|t| t.symbol.as_str()).collect();
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
            let bench = Bench::ALL.iter().any(|b| b.symbol() == sym);
            if held || bench || traded.contains(sym.as_str()) {
                closes.insert(sym, parse_closes(&json));
            }
        }
    }
    let bench = Bench::ALL
        .iter()
        .filter_map(|b| Some((b.symbol(), closes.get(b.symbol())?.clone())))
        .collect();
    let exposure = build_exposure(&history, &positions, &txns, &closes, &industries);
    Ok(Data {
        history,
        positions,
        positions_at,
        bench,
        closes,
        txns,
        exposure,
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

/// ticker -> dominant niche ("memory storage") from the universe tables.
/// A missing table or ticker just means "Other".
fn load_industries(conn: &duckdb::Connection) -> HashMap<String, String> {
    let sql = "SELECT ticker, arg_max(category, weight) FROM ai_universe_category \
               WHERE level = 'sub' GROUP BY ticker";
    let Ok(mut stmt) = conn.prepare(sql) else {
        return HashMap::new();
    };
    let Ok(rows) = stmt.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))
    else {
        return HashMap::new();
    };
    rows.flatten()
        .map(|(t, c)| (t, c.replace('_', " ")))
        .collect()
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

/// Pairs at or above this daily-return correlation are linked into a cluster.
const CLUSTER_RHO: f64 = 0.7;
/// Fewest shared return days before a pair's correlation is trusted.
const CLUSTER_MIN_DAYS: usize = 30;

/// Derived inputs for the Exposure tab, built once per load.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Exposure {
    /// Snapshot dates the drift series are sampled on, oldest first.
    pub dates: Vec<NaiveDate>,
    /// Industry -> weight % of invested at each date, largest latest weight first.
    pub drift: Vec<(String, Vec<f64>)>,
    /// Held names that move together, largest share of the book first.
    pub clusters: Vec<Cluster>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Cluster {
    pub symbols: Vec<String>,
    /// Mean correlation over the linked pairs in this cluster.
    pub avg_rho: f64,
    /// Share of account value held in the cluster, %.
    pub weight_pct: f64,
}

/// Concentration of the book. `top*` are % of account value (cash counted
/// in the denominator); `hhi` is over invested weights, 0..1, where an even
/// split across n names gives 1/n.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Concentration {
    pub top1: f64,
    pub top3: f64,
    pub top5: f64,
    pub hhi: f64,
    pub count: usize,
}

pub fn concentration(positions: &[Position], tot: &Totals) -> Concentration {
    let mut vals: Vec<f64> = positions
        .iter()
        .map(|p| p.value)
        .filter(|v| *v > 0.0)
        .collect();
    vals.sort_by(|a, b| b.total_cmp(a));
    let invested: f64 = vals.iter().sum();
    let top = |n: usize| {
        if tot.value > 0.0 {
            vals.iter().take(n).sum::<f64>() / tot.value * 100.0
        } else {
            0.0
        }
    };
    let hhi = if invested > 0.0 {
        vals.iter().map(|v| (v / invested).powi(2)).sum::<f64>()
    } else {
        0.0
    };
    Concentration {
        top1: top(1),
        top3: top(3),
        top5: top(5),
        hhi,
        count: vals.len(),
    }
}

/// Exposure inputs derived from the loaded rows. Weights for clusters are
/// % of account value, same basis as the allocation rows.
pub fn build_exposure(
    history: &[Snapshot],
    positions: &[Position],
    txns: &[Txn],
    closes: &HashMap<String, Vec<(NaiveDate, f64)>>,
    industries: &HashMap<String, String>,
) -> Exposure {
    let dates: Vec<NaiveDate> = history.iter().map(|s| s.date).collect();
    let tot = totals(history, positions);
    let weights: HashMap<&str, f64> = positions
        .iter()
        .map(|p| {
            let w = if tot.value > 0.0 {
                p.value / tot.value * 100.0
            } else {
                0.0
            };
            (p.symbol.as_str(), w)
        })
        .collect();
    Exposure {
        drift: industry_drift(&dates, txns, closes, industries),
        clusters: correlation_clusters(closes, &weights, CLUSTER_RHO, CLUSTER_MIN_DAYS),
        dates,
    }
}

/// Industry weight (% of invested) on each date, rebuilt from the trade log:
/// shares held that day × the symbol's last close on or before it. A
/// symbol with no close yet on a date contributes nothing. Transfers are not
/// in `txns`, and lots bought before the cache starts are missing too, so
/// the replay can under-count holdings that were not bought inside the window.
pub fn industry_drift(
    dates: &[NaiveDate],
    txns: &[Txn],
    closes: &HashMap<String, Vec<(NaiveDate, f64)>>,
    industries: &HashMap<String, String>,
) -> Vec<(String, Vec<f64>)> {
    let mut shares: HashMap<&str, f64> = HashMap::new();
    // symbol -> (next close index, last close seen); dates only move forward.
    let mut cursor: HashMap<&str, (usize, f64)> = HashMap::new();
    let mut next = 0;
    let mut per_date: Vec<HashMap<String, f64>> = Vec::with_capacity(dates.len());
    for &d in dates {
        while next < txns.len() && txns[next].date <= d {
            let held = shares.entry(txns[next].symbol.as_str()).or_default();
            // A sale larger than the lots we can see means the opening lot
            // predates the cache, so the replay floors the balance at zero.
            *held = (*held + txns[next].qty).max(0.0);
            next += 1;
        }
        let mut vals: HashMap<String, f64> = HashMap::new();
        for (&sym, &n) in &shares {
            if n.abs() < 1e-9 {
                continue;
            }
            let Some(series) = closes.get(sym) else {
                continue;
            };
            let (idx, last) = cursor.entry(sym).or_insert((0, 0.0));
            while *idx < series.len() && series[*idx].0 <= d {
                *last = series[*idx].1;
                *idx += 1;
            }
            if *last <= 0.0 {
                continue;
            }
            let ind = industries.get(sym).map_or("Other", String::as_str);
            *vals.entry(ind.to_string()).or_default() += n * *last;
        }
        let total: f64 = vals.values().sum();
        per_date.push(
            vals.into_iter()
                .map(|(k, v)| (k, if total > 0.0 { v / total * 100.0 } else { 0.0 }))
                .collect(),
        );
    }

    let mut names: Vec<String> = per_date
        .iter()
        .flat_map(|m| m.keys().cloned())
        .collect::<HashSet<_>>()
        .into_iter()
        .collect();
    let latest = per_date.last();
    let w = |m: Option<&HashMap<String, f64>>, k: &str| {
        m.and_then(|m| m.get(k)).copied().unwrap_or(0.0)
    };
    names.sort_by(|a, b| w(latest, b).total_cmp(&w(latest, a)).then_with(|| a.cmp(b)));
    names
        .into_iter()
        .map(|name| {
            let series = per_date.iter().map(|m| w(Some(m), &name)).collect();
            (name, series)
        })
        .collect()
}

/// Daily simple returns keyed by the date they land on.
fn daily_returns(series: &[(NaiveDate, f64)]) -> HashMap<NaiveDate, f64> {
    series
        .windows(2)
        .filter(|w| w[0].1 > 0.0)
        .map(|w| (w[1].0, w[1].1 / w[0].1 - 1.0))
        .collect()
}

/// Pearson correlation over the return dates both series share.
fn pearson(
    a: &HashMap<NaiveDate, f64>,
    b: &HashMap<NaiveDate, f64>,
    min_days: usize,
) -> Option<f64> {
    let pairs: Vec<(f64, f64)> = a
        .iter()
        .filter_map(|(d, x)| b.get(d).map(|y| (*x, *y)))
        .collect();
    if pairs.len() < min_days {
        return None;
    }
    let n = pairs.len() as f64;
    let mx = pairs.iter().map(|p| p.0).sum::<f64>() / n;
    let my = pairs.iter().map(|p| p.1).sum::<f64>() / n;
    let (mut sxy, mut sxx, mut syy) = (0.0, 0.0, 0.0);
    for (x, y) in &pairs {
        let (dx, dy) = (x - mx, y - my);
        sxy += dx * dy;
        sxx += dx * dx;
        syy += dy * dy;
    }
    if sxx <= 0.0 || syy <= 0.0 {
        return None;
    }
    Some(sxy / (sxx * syy).sqrt())
}

fn find(parent: &mut [usize], i: usize) -> usize {
    if parent[i] != i {
        parent[i] = find(parent, parent[i]);
    }
    parent[i]
}

/// Groups held names whose daily-return correlation is at least `min_rho`
/// (single linkage). Singletons are dropped. `weights` is % of account value
/// per symbol; names without a close series are skipped.
pub fn correlation_clusters(
    closes: &HashMap<String, Vec<(NaiveDate, f64)>>,
    weights: &HashMap<&str, f64>,
    min_rho: f64,
    min_days: usize,
) -> Vec<Cluster> {
    let mut syms: Vec<&str> = weights
        .keys()
        .copied()
        .filter(|s| closes.contains_key(*s))
        .collect();
    syms.sort();
    let rets: Vec<HashMap<NaiveDate, f64>> =
        syms.iter().map(|s| daily_returns(&closes[*s])).collect();

    let mut parent: Vec<usize> = (0..syms.len()).collect();
    let mut links: Vec<(usize, usize, f64)> = Vec::new();
    for i in 0..syms.len() {
        for j in i + 1..syms.len() {
            if let Some(r) = pearson(&rets[i], &rets[j], min_days).filter(|r| *r >= min_rho) {
                links.push((i, j, r));
                let (ri, rj) = (find(&mut parent, i), find(&mut parent, j));
                parent[ri] = rj;
            }
        }
    }

    let mut groups: HashMap<usize, (Vec<usize>, f64, usize)> = HashMap::new();
    for i in 0..syms.len() {
        let root = find(&mut parent, i);
        groups
            .entry(root)
            .or_insert_with(|| (Vec::new(), 0.0, 0))
            .0
            .push(i);
    }
    for (i, _, r) in &links {
        let root = find(&mut parent, *i);
        let g = groups.get_mut(&root).expect("linked pair has a group");
        g.1 += r;
        g.2 += 1;
    }

    let mut out: Vec<Cluster> = groups
        .into_values()
        .filter(|(members, _, _)| members.len() >= 2)
        .map(|(members, rho_sum, links_n)| Cluster {
            symbols: members.iter().map(|&i| syms[i].to_string()).collect(),
            avg_rho: rho_sum / links_n as f64,
            weight_pct: members.iter().map(|&i| weights[syms[i]]).sum(),
        })
        .collect();
    out.sort_by(|a, b| {
        b.weight_pct
            .total_cmp(&a.weight_pct)
            .then_with(|| a.symbols.cmp(&b.symbols))
    });
    out
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
        let ind = HashMap::from([("MU".to_string(), "memory storage".to_string())]);
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

    fn flat(prices: &[f64]) -> Vec<(NaiveDate, f64)> {
        let start = d("2026-01-01");
        prices
            .iter()
            .enumerate()
            .map(|(i, p)| (start + chrono::Duration::days(i as i64), *p))
            .collect()
    }

    fn txn(date: &str, sym: &str, qty: f64) -> Txn {
        Txn {
            id: String::new(),
            date: d(date),
            kind: "trade".into(),
            symbol: sym.into(),
            qty,
            price: 10.0,
            amount: -qty * 10.0,
        }
    }

    #[test]
    fn drift_follows_trades_and_prices() {
        let dates: Vec<NaiveDate> = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
            .iter()
            .map(|s| d(s))
            .collect();
        let closes = HashMap::from([
            ("AAA".to_string(), flat(&[10.0; 4])),
            ("BBB".to_string(), flat(&[10.0; 4])),
        ]);
        let industries = HashMap::from([
            ("AAA".to_string(), "semis".to_string()),
            ("BBB".to_string(), "software".to_string()),
        ]);
        let txns = vec![
            txn("2026-01-01", "AAA", 10.0),
            txn("2026-01-02", "BBB", 10.0),
            txn("2026-01-03", "AAA", -10.0),
        ];
        let drift = industry_drift(&dates, &txns, &closes, &industries);
        // latest weight decides order: software ends at 100%, semis at 0%
        assert_eq!(drift[0].0, "software");
        assert_eq!(drift[0].1, vec![0.0, 50.0, 100.0, 100.0]);
        assert_eq!(drift[1].0, "semis");
        assert_eq!(drift[1].1, vec![100.0, 50.0, 0.0, 0.0]);
    }

    #[test]
    fn drift_weights_by_value_not_shares() {
        let dates = vec![d("2026-01-01")];
        let closes = HashMap::from([
            ("AAA".to_string(), flat(&[10.0])),
            ("BBB".to_string(), flat(&[30.0])),
        ]);
        let industries = HashMap::from([
            ("AAA".to_string(), "semis".to_string()),
            ("BBB".to_string(), "software".to_string()),
        ]);
        let txns = vec![
            txn("2026-01-01", "AAA", 10.0),
            txn("2026-01-01", "BBB", 10.0),
        ];
        let drift = industry_drift(&dates, &txns, &closes, &industries);
        // 10 × $10 vs 10 × $30 is a 25/75 split
        assert_eq!(drift[0], ("software".to_string(), vec![75.0]));
        assert_eq!(drift[1], ("semis".to_string(), vec![25.0]));
    }

    #[test]
    fn drift_floors_sales_without_a_known_lot() {
        let dates = vec![d("2026-01-02")];
        let closes = HashMap::from([("AAA".to_string(), flat(&[10.0]))]);
        let industries = HashMap::from([("AAA".to_string(), "semis".to_string())]);
        let txns = vec![
            txn("2026-01-01", "AAA", -8.0),
            txn("2026-01-02", "AAA", 5.0),
        ];
        let drift = industry_drift(&dates, &txns, &closes, &industries);
        // the sale of 8 floors the balance at 0, so the later buy of 5 is the whole book
        assert_eq!(drift[0], ("semis".to_string(), vec![100.0]));
    }

    #[test]
    fn dedupe_keeps_first_record_per_transaction_id() {
        let mut t = vec![
            Txn {
                id: "7".into(),
                ..txn("2026-06-05", "GOOGL", 7.0)
            },
            Txn {
                id: "7".into(),
                ..txn("2026-06-05", "GOOGL", 7.0)
            },
            Txn {
                id: "8".into(),
                ..txn("2026-06-12", "GOOGL", 10.0)
            },
            // rows without an id are never collapsed together
            txn("2026-06-12", "GOOGL", 10.0),
            txn("2026-06-12", "GOOGL", 10.0),
        ];
        dedupe_txns(&mut t);
        assert_eq!(t.len(), 4);
        assert_eq!(t[0].id, "7");
    }

    #[test]
    fn concentration_counts_cash_in_account_value() {
        let positions = vec![
            pos("AAA", 500.0, 0.0, "semis"),
            pos("BBB", 300.0, 0.0, "software"),
            pos("CCC", 200.0, 0.0, "power"),
        ];
        let tot = Totals {
            value: 1000.0,
            ..Default::default()
        };
        let c = concentration(&positions, &tot);
        assert_eq!(c.top1, 50.0);
        assert_eq!(c.top3, 100.0);
        assert_eq!(c.top5, 100.0);
        assert!((c.hhi - 0.38).abs() < 1e-9);
        assert_eq!(c.count, 3);
    }

    /// Prices from a return pattern, starting at 100.
    fn priced(returns: impl Iterator<Item = f64>) -> Vec<(NaiveDate, f64)> {
        let mut p = 100.0;
        let mut out = vec![100.0];
        for r in returns {
            p *= 1.0 + r;
            out.push(p);
        }
        flat(&out)
    }

    #[test]
    fn clusters_link_co_moving_names_only() {
        let n = 60;
        // alternating returns: A and B move together, C is orthogonal to them
        let alt = |i: usize, s: f64| if i % 2 == 0 { s } else { -s };
        let period4 = |i: usize| [0.01, 0.01, -0.01, -0.01][i % 4];
        let closes = HashMap::from([
            ("AAA".to_string(), priced((1..n).map(|i| alt(i, 0.01)))),
            ("BBB".to_string(), priced((1..n).map(|i| alt(i, 0.02)))),
            ("CCC".to_string(), priced((1..n).map(period4))),
        ]);
        let weights = HashMap::from([("AAA", 40.0), ("BBB", 20.0), ("CCC", 30.0)]);
        let clusters = correlation_clusters(&closes, &weights, 0.7, 30);
        assert_eq!(clusters.len(), 1);
        assert_eq!(clusters[0].symbols, vec!["AAA", "BBB"]);
        assert!((clusters[0].avg_rho - 1.0).abs() < 1e-6);
        assert!((clusters[0].weight_pct - 60.0).abs() < 1e-9);
    }

    #[test]
    fn clusters_need_enough_shared_days() {
        let closes = HashMap::from([
            (
                "AAA".to_string(),
                priced((1..10).map(|i| if i % 2 == 0 { 0.01 } else { -0.01 })),
            ),
            (
                "BBB".to_string(),
                priced((1..10).map(|i| if i % 2 == 0 { 0.02 } else { -0.02 })),
            ),
        ]);
        let weights = HashMap::from([("AAA", 50.0), ("BBB", 50.0)]);
        assert!(correlation_clusters(&closes, &weights, 0.7, 30).is_empty());
    }
}
