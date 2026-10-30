// Portfolio activity (tab 5): one stock at a time. The row selected in the
// bottom ledger picks the stock. The top is its price with your fills on it:
// a line from each entry to each exit, so a round trip reads as one vertical
// move. A one-line summary sits under the chart. The ledger is every cached
// transaction, newest first. Everything is computed from the cache in data.rs;
// nothing is fetched.

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Paragraph, Row, Table, TableState};

use super::data::{self, Data, Txn};
use super::holding;
use super::overview::{money, signed_money};
use crate::ui::theme::Theme;

const HEADER: [&str; 7] = ["Date", "Type", "Sym", "Qty", "Price", "Shares", "Realized"];
const WIDTHS: [Constraint; 7] = [
    Constraint::Length(10),
    Constraint::Length(13),
    Constraint::Length(7),
    Constraint::Length(8),
    Constraint::Length(10),
    Constraint::Length(9),
    Constraint::Fill(1),
];

/// Running state of one ledger row, after that row's transaction.
#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct Ledger {
    /// Shares held in the row's symbol after the row.
    pub shares: f64,
    /// Average cost per share of what is still held (0 when flat).
    pub avg_cost: f64,
    /// Gain or loss the row locks in: sales only.
    pub realized: Option<f64>,
}

/// Running position per row. `txns` is in cache order, oldest first, and the
/// result lines up with it. Sales are charged at the average cost held just
/// before the sale.
pub fn ledger(txns: &[Txn]) -> Vec<Ledger> {
    let mut book: HashMap<&str, (f64, f64)> = HashMap::new(); // symbol -> (shares, cost basis)
    txns.iter()
        .map(|t| {
            let (shares, cost) = book.entry(t.symbol.as_str()).or_insert((0.0, 0.0));
            let mut realized = None;
            match t.kind.as_str() {
                "Bought" => {
                    *shares += t.qty;
                    *cost += -t.amount;
                }
                "Sold" => {
                    let avg = if *shares > 0.0 { *cost / *shares } else { 0.0 };
                    let sold = -t.qty; // sales carry negative quantities
                    realized = Some(t.amount - avg * sold);
                    *cost -= avg * sold;
                    *shares += t.qty;
                }
                "Stock Split" => *shares += t.qty,
                _ => {}
            }
            Ledger {
                shares: *shares,
                avg_cost: if *shares > 0.0 { *cost / *shares } else { 0.0 },
                realized,
            }
        })
        .collect()
}

/// Context on each side of the trades, in twelfths of the chart width. The
/// default, 2, is a sixth: the trades fill the middle two-thirds.
pub const MARGIN_DEFAULT: u8 = 2;
pub const MARGIN_MIN: u8 = 1;
pub const MARGIN_MAX: u8 = 4;

pub fn draw(
    frame: &mut Frame,
    area: Rect,
    t: &Theme,
    d: &Data,
    sel: usize,
    now: DateTime<Utc>,
    margin: u8,
) {
    if d.txns.is_empty() {
        frame.render_widget(
            Paragraph::new("no transactions cached yet")
                .style(t.dim())
                .centered(),
            area,
        );
        return;
    }
    let n = d.txns.len();
    let sel = sel.min(n - 1);
    let book = ledger(&d.txns);
    // The ledger is newest first, so row `sel` is transaction `n - 1 - sel`.
    let symbol = d.txns[n - 1 - sel].symbol.as_str();

    let [chart, summary, bottom] = Layout::vertical([
        Constraint::Fill(2),
        Constraint::Length(1),
        Constraint::Fill(1),
    ])
    .areas(area);
    draw_chart(frame, chart, t, d, symbol, now, margin);
    frame.render_widget(Paragraph::new(summary_line(t, d, &book, symbol)), summary);
    draw_ledger(frame, bottom, t, &d.txns, &book, sel);
}

fn panel<'a>(t: &Theme, title: String) -> Block<'a> {
    Block::bordered()
        .border_style(t.border())
        .title_top(Line::from(Span::styled(format!(" {title} "), t.title())))
        .style(t.base())
}

fn draw_chart(
    frame: &mut Frame,
    area: Rect,
    t: &Theme,
    d: &Data,
    symbol: &str,
    now: DateTime<Utc>,
    margin: u8,
) {
    let block = panel(t, format!("{symbol} · price and your trades"));
    let inner = block.inner(area);
    frame.render_widget(block, area);
    let h = data::symbol_history(&d.txns, symbol);
    let (from, to) = trade_window(&h, now, margin);
    let held = d.positions.iter().find(|p| p.symbol == symbol);
    // Minute closes when this stock traded recently; daily closes otherwise.
    let mut prices: Vec<(DateTime<Utc>, f64)> = match d.minutes.get(symbol) {
        Some(m) if !m.is_empty() => m.clone(),
        _ => d
            .closes
            .get(symbol)
            .map(|c| {
                c.iter()
                    .map(|(day, p)| (holding::close_utc(*day), *p))
                    .collect()
            })
            .unwrap_or_default(),
    };
    if let Some(p) = held.filter(|p| p.price > 0.0)
        && prices.last().is_none_or(|(at, _)| *at < now)
    {
        prices.push((now, p.price));
    }
    let avg = held.map_or(0.0, |p| p.price_paid);
    holding::price_chart(frame, inner, t, t.accent, avg, &h, &prices, (from, to));
}

/// Chart window for one stock. Its fills span the middle of the chart, with
/// `margin` twelfths of the width of context on each side. Context is at
/// least 30 minutes, the end is clipped to now, and six weeks is the most
/// the chart shows.
fn trade_window(
    h: &data::SymbolHistory,
    now: DateTime<Utc>,
    margin: u8,
) -> (DateTime<Utc>, DateTime<Utc>) {
    const MIN_PAD_SECS: f64 = 30.0 * 60.0;
    const MAX_DAYS: i64 = 42;
    let margin = f64::from(margin.clamp(MARGIN_MIN, MARGIN_MAX));
    // h.recent is newest first: its ends are the last and first trades
    let (Some(first), Some(last)) = (
        h.recent.last().map(|t| t.at),
        h.recent.first().map(|t| t.at),
    ) else {
        return (now - chrono::Duration::days(MAX_DAYS), now);
    };
    // With the trades spanning `span`, the chart is span / (1 - 2 * margin / 12) wide,
    // so each side gets span * margin / (12 - 2 * margin).
    let span = (last - first).num_milliseconds() as f64 / 1000.0;
    let pad = chrono::Duration::milliseconds(
        (span * margin / (12.0 - 2.0 * margin) * 1000.0).max(MIN_PAD_SECS * 1000.0) as i64,
    );
    let to = (last + pad).min(now);
    let from = (first - pad).max(to - chrono::Duration::days(MAX_DAYS));
    (from, to)
}

/// Where the position stands and what it has made, in one line.
fn summary_line(t: &Theme, d: &Data, book: &[Ledger], symbol: &str) -> Line<'static> {
    let h = data::symbol_history(&d.txns, symbol);
    let held = d.positions.iter().find(|p| p.symbol == symbol);
    let (shares, avg, realized) = d
        .txns
        .iter()
        .zip(book.iter())
        .filter(|(x, _)| x.symbol == symbol)
        .fold((0.0, 0.0, 0.0), |(_, _, r), (_, l)| {
            (l.shares, l.avg_cost, r + l.realized.unwrap_or(0.0))
        });
    let position = if shares > 0.0 {
        format!("{shares:.2} sh at avg {}", money(avg))
    } else {
        "sold out".into()
    };
    let all_time = if h.complete(shares) {
        let v = h.all_time_pnl(held.map_or(0.0, |p| p.value));
        Span::styled(format!("all-time {}", signed_money(v)), t.signed(v))
    } else {
        Span::styled("incomplete history", t.dim())
    };
    let sep = Span::styled("  ·  ", t.dim());
    let mut spans = vec![
        Span::styled(format!(" {position}"), t.base()),
        sep.clone(),
        Span::styled(
            format!("realized {}", signed_money(realized)),
            t.signed(realized),
        ),
        sep.clone(),
        all_time,
    ];
    if let Some(first) = h.first {
        spans.push(sep);
        spans.push(Span::styled(
            format!("{} trades since {first}", h.trades),
            t.dim(),
        ));
    }
    Line::from(spans)
}

fn draw_ledger(
    frame: &mut Frame,
    area: Rect,
    t: &Theme,
    txns: &[Txn],
    book: &[Ledger],
    sel: usize,
) {
    let rows: Vec<Row> = txns
        .iter()
        .zip(book.iter())
        .rev()
        .map(|(x, l)| {
            let realized = match l.realized {
                Some(r) => Cell::from(format!("{r:+.0}")).style(t.signed(r)),
                None => Cell::from(""),
            };
            Row::new(vec![
                Cell::from(x.date.to_string()).style(t.dim()),
                Cell::from(x.kind.clone()),
                Cell::from(x.symbol.clone()),
                Cell::from(if x.qty != 0.0 {
                    format!("{:+.0}", x.qty)
                } else {
                    String::new()
                }),
                Cell::from(if x.price != 0.0 {
                    format!("${:.2}", x.price)
                } else {
                    String::new()
                }),
                Cell::from(format!("{:.0}", l.shares)),
                realized,
            ])
        })
        .collect();
    let n = rows.len();
    let mut state = TableState::default().with_selected(Some(sel.min(n - 1)));
    let title = format!(" Ledger · {n} newest first ");
    let table = Table::new(rows, WIDTHS.to_vec())
        .header(Row::new(HEADER.iter().map(|h| Cell::from(*h))).style(t.dim()))
        .row_highlight_style(t.selected())
        .block(panel(t, title.trim().to_string()))
        .style(t.base());
    frame.render_stateful_widget(table, area, &mut state);
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    fn tx(date: &str, kind: &str, qty: f64, amount: f64) -> Txn {
        let date = NaiveDate::parse_from_str(date, "%Y-%m-%d").unwrap();
        Txn {
            id: format!("{date}{kind}"),
            date,
            at: date.and_hms_opt(16, 0, 0).unwrap().and_utc(),
            kind: kind.into(),
            symbol: "X".into(),
            qty,
            price: if qty != 0.0 {
                (amount / qty).abs()
            } else {
                0.0
            },
            amount,
        }
    }

    #[test]
    fn ledger_tracks_shares_average_cost_and_realized_gain() {
        let txns = [
            tx("2026-01-02", "Bought", 10.0, -1000.0),
            tx("2026-02-02", "Bought", 10.0, -2000.0),
            tx("2026-03-02", "Sold", -5.0, 1500.0),
        ];
        let l = ledger(&txns);
        assert_eq!(l[1].shares, 20.0);
        assert_eq!(l[1].avg_cost, 150.0);
        assert_eq!(l[1].realized, None);
        // sold 5 at 300 against an average cost of 150: realized 750
        assert_eq!(l[2].shares, 15.0);
        assert_eq!(l[2].avg_cost, 150.0, "selling does not move the average");
        assert_eq!(l[2].realized, Some(750.0));
    }

    #[test]
    fn splits_change_shares_not_cost() {
        let txns = [
            tx("2026-01-02", "Bought", 10.0, -1000.0),
            tx("2026-02-02", "Stock Split", 10.0, 0.0),
        ];
        let l = ledger(&txns);
        assert_eq!(l[1].shares, 20.0);
        assert_eq!(l[1].avg_cost, 50.0);
    }

    fn at(s: &str) -> DateTime<Utc> {
        DateTime::parse_from_rfc3339(s).unwrap().with_timezone(&Utc)
    }

    /// A fill at `when` (RFC 3339), date taken from the same instant.
    fn fill(when: &str, kind: &str, qty: f64, amount: f64) -> Txn {
        let when = at(when);
        Txn {
            at: when,
            date: when.date_naive(),
            ..tx("2026-01-01", kind, qty, amount)
        }
    }

    #[test]
    fn trades_fill_the_middle_two_thirds_of_the_window() {
        // SOXS on 10/29: bought 9:32 ET, sold 14:26 ET (13:32 and 18:26 UTC)
        let h = data::SymbolHistory {
            recent: vec![
                fill("2026-10-29T18:26:57Z", "Sold", -1150.0, 48000.0),
                fill("2026-10-29T13:32:31Z", "Bought", 1000.0, -42270.0),
            ],
            ..Default::default()
        };
        let now = at("2026-10-30T13:00:00Z");
        let (from, to) = trade_window(&h, now, MARGIN_DEFAULT);
        let (first, last) = (at("2026-10-29T13:32:31Z"), at("2026-10-29T18:26:57Z"));
        let total = (to - from).num_seconds() as f64;
        let entry = (first - from).num_seconds() as f64 / total;
        let exit = (last - from).num_seconds() as f64 / total;
        assert!((entry - 1.0 / 6.0).abs() < 1e-3, "entry at {entry}");
        assert!((exit - 5.0 / 6.0).abs() < 1e-3, "exit at {exit}");
    }

    #[test]
    fn widening_the_margin_keeps_the_trades_centred() {
        let h = data::SymbolHistory {
            recent: vec![
                fill("2026-10-29T18:00:00Z", "Sold", -1.0, 1.0),
                fill("2026-10-29T14:00:00Z", "Bought", 1.0, -1.0),
            ],
            ..Default::default()
        };
        let now = at("2026-10-30T13:00:00Z");
        let (a, b) = trade_window(&h, now, MARGIN_DEFAULT);
        let (c, e) = trade_window(&h, now, 3);
        // the window grows on both sides, and the trades stay in the middle
        assert!(c < a && e > b);
        let mid = |x: DateTime<Utc>, y: DateTime<Utc>| x + (y - x) / 2;
        assert!((mid(a, b) - mid(c, e)).num_seconds().abs() < 1);
    }

    #[test]
    fn trade_window_has_minimum_context_and_a_six_week_cap() {
        let now = at("2026-10-30T13:00:00Z");
        // a same-minute round trip still gets 30 minutes either side
        let same_minute = data::SymbolHistory {
            recent: vec![
                fill("2026-10-29T14:00:00Z", "Sold", -1.0, 1.0),
                fill("2026-10-29T14:00:00Z", "Bought", 1.0, -1.0),
            ],
            ..Default::default()
        };
        let (from, to) = trade_window(&same_minute, now, MARGIN_DEFAULT);
        assert_eq!(to - from, chrono::Duration::hours(1));
        // a long run: six weeks at most
        let long = data::SymbolHistory {
            recent: vec![
                fill("2026-09-01T14:00:00Z", "Sold", -1.0, 1.0),
                fill("2026-05-01T14:00:00Z", "Bought", 1.0, -1.0),
            ],
            ..Default::default()
        };
        let (from, to) = trade_window(&long, now, MARGIN_DEFAULT);
        assert_eq!((to - from).num_days(), 42);
        // the end is clipped to now
        let open = data::SymbolHistory {
            recent: vec![fill("2026-10-30T12:50:00Z", "Bought", 1.0, -1.0)],
            ..Default::default()
        };
        assert!(trade_window(&open, now, MARGIN_DEFAULT).1 <= now);
    }

    #[test]
    fn dividends_leave_the_position_alone() {
        let txns = [
            tx("2026-01-02", "Bought", 10.0, -1000.0),
            tx("2026-02-02", "Dividend", 0.0, 12.0),
        ];
        let l = ledger(&txns);
        assert_eq!(l[1].shares, 10.0);
        assert_eq!(l[1].realized, None);
    }
}
