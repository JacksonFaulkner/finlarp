// Positions tab, left side: the spotlight card for the selected holding
// (P&L lines plus a price chart with your trades and average cost on it)
// and the holdings table under it. Columns drop lowest-priority first
// when the panel is narrow.

use std::collections::HashMap;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::symbols::Marker;
use ratatui::text::{Line, Span};
use ratatui::widgets::{
    Axis, Block, Cell, Chart, Dataset, GraphType, Padding, Paragraph, Row, Table, TableState,
};

use super::data::{self, SymbolHistory, Totals, Txn};
use super::overview::{money, signed_money, signed_pct};
use super::pie::Entry;
use crate::ui::theme::Theme;

pub type Closes = HashMap<String, Vec<(NaiveDate, f64)>>;

/// Days of price history in the card chart (stretched back to the first
/// buy when that is within a year).
const CHART_DAYS: i64 = 182;
/// Card text width when the chart sits beside it rather than below.
const TEXT_W: u16 = 46;
/// Days of closes in the table's sparkline.
const SPARK_DAYS: i64 = 30;

/// Closes for `sym` with today's quote appended when it is newer than the
/// last cached close.
fn series(closes: &Closes, sym: &str, price: f64, today: NaiveDate) -> Vec<(NaiveDate, f64)> {
    let mut s = closes.get(sym).cloned().unwrap_or_default();
    if price > 0.0 && s.last().is_none_or(|(d, _)| *d < today) {
        s.push((today, price));
    }
    s
}

fn since(s: &[(NaiveDate, f64)], from: NaiveDate) -> &[(NaiveDate, f64)] {
    &s[s.partition_point(|(d, _)| *d < from)..]
}

/// Block-character sparkline of `vals`, resampled to `width` cells.
pub fn spark(vals: &[f64], width: usize) -> String {
    const BARS: [char; 8] = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
    if vals.len() < 2 || width == 0 {
        return String::new();
    }
    let (lo, hi) = vals
        .iter()
        .fold((f64::MAX, f64::MIN), |(l, h), v| (l.min(*v), h.max(*v)));
    let n = width.min(vals.len());
    (0..n)
        .map(|i| {
            let v = vals[(i + 1) * vals.len() / n - 1];
            let f = if hi > lo { (v - lo) / (hi - lo) } else { 0.5 };
            BARS[((f * 7.0).round() as usize).min(7)]
        })
        .collect()
}

/// Weight bar in eighth blocks, full width = `max`.
fn bar(v: f64, max: f64, width: usize) -> String {
    const EIGHTHS: [char; 8] = ['▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'];
    if max <= 0.0 || v <= 0.0 {
        return String::new();
    }
    let eighths = ((v / max) * (width * 8) as f64).round().max(1.0) as usize;
    let mut s = "█".repeat(eighths / 8);
    if !eighths.is_multiple_of(8) {
        s.push(EIGHTHS[eighths % 8 - 1]);
    }
    s
}

/// "12d", "8mo", "2.1y".
fn held(first: NaiveDate, today: NaiveDate) -> String {
    let d = (today - first).num_days().max(0);
    match d {
        0..60 => format!("{d}d"),
        60..730 => format!("{}mo", d / 30),
        _ => format!("{:.1}y", d as f64 / 365.0),
    }
}

struct Col {
    title: &'static str,
    width: u16,
    /// Lower keeps the column longer as the panel narrows.
    keep: u8,
    right: bool,
}

const COLS: [Col; 10] = [
    Col {
        title: "",
        width: 7,
        keep: 0,
        right: false,
    },
    Col {
        title: "Wt",
        width: 5,
        keep: 0,
        right: true,
    },
    Col {
        title: "",
        width: 6,
        keep: 5,
        right: false,
    },
    Col {
        title: "Value",
        width: 8,
        keep: 1,
        right: true,
    },
    Col {
        title: "Day",
        width: 6,
        keep: 2,
        right: true,
    },
    Col {
        title: "Today",
        width: 7,
        keep: 4,
        right: true,
    },
    Col {
        title: "Gain",
        width: 7,
        keep: 3,
        right: true,
    },
    Col {
        title: "1M",
        width: 10,
        keep: 6,
        right: false,
    },
    Col {
        title: "Off hi",
        width: 6,
        keep: 7,
        right: true,
    },
    Col {
        title: "Held",
        width: 5,
        keep: 8,
        right: true,
    },
];

/// Indices of the columns that fit `width`, in display order.
fn fit_cols(width: u16) -> Vec<usize> {
    let mut order: Vec<usize> = (0..COLS.len()).collect();
    order.sort_by_key(|&i| COLS[i].keep);
    let mut used = 0u16;
    let mut keep: Vec<usize> = Vec::new();
    for i in order {
        let w = COLS[i].width + u16::from(!keep.is_empty());
        if used + w > width {
            break;
        }
        used += w;
        keep.push(i);
    }
    keep.sort_unstable();
    keep
}

pub struct TableView<'a> {
    pub theme: &'a Theme,
    pub rows: &'a [Entry<'a>],
    pub tot: &'a Totals,
    pub txns: &'a [Txn],
    pub closes: &'a Closes,
    pub sel: usize,
    pub today: NaiveDate,
}

pub fn table(frame: &mut Frame, area: Rect, v: &TableView) {
    let t = v.theme;
    let area = area.inner(ratatui::layout::Margin::new(1, 0));
    let cols = fit_cols(area.width);
    let max_w = v.rows.iter().map(|e| e.value).fold(0.0, f64::max);
    let cell = |i: usize, s: Span<'static>| {
        if COLS[i].right {
            Cell::from(Line::from(s).right_aligned())
        } else {
            Cell::from(Line::from(s))
        }
    };
    let rows: Vec<Row> = v
        .rows
        .iter()
        .map(|e| {
            let p = e.pos;
            let s = p.map(|p| series(v.closes, &p.symbol, p.price, v.today));
            let h = p.map(|p| data::symbol_history(v.txns, &p.symbol));
            let cells = cols.iter().map(|&i| {
                let span = match (i, p) {
                    (0, _) => {
                        return Cell::from(Line::from(vec![
                            Span::styled("● ", Style::new().fg(e.color)),
                            Span::raw(e.label.to_string()),
                        ]));
                    }
                    (1, _) => {
                        Span::styled(format!("{:.1}%", e.value / v.tot.value * 100.0), t.dim())
                    }
                    (2, _) => Span::styled(
                        bar(e.value, max_w, COLS[2].width as usize),
                        Style::new().fg(e.color),
                    ),
                    (3, _) => Span::raw(money(e.value)),
                    (4, Some(p)) => Span::styled(signed_pct(p.day_pct), t.signed(p.day_pct)),
                    (5, Some(p)) => Span::styled(signed_money(p.day_gain), t.signed(p.day_gain)),
                    (6, Some(p)) => {
                        let g = if p.cost() > 0.0 {
                            p.total_gain / p.cost() * 100.0
                        } else {
                            0.0
                        };
                        Span::styled(format!("{g:+.0}%"), t.signed(g))
                    }
                    (7, Some(_)) => {
                        let s = s.as_deref().unwrap_or_default();
                        let from = s.last().map_or(v.today, |(d, _)| *d)
                            - chrono::Duration::days(SPARK_DAYS);
                        let vals: Vec<f64> = since(s, from).iter().map(|(_, c)| *c).collect();
                        let chg = match (vals.first(), vals.last()) {
                            (Some(a), Some(b)) => b - a,
                            _ => 0.0,
                        };
                        Span::styled(spark(&vals, COLS[7].width as usize), t.signed(chg))
                    }
                    (8, Some(p)) => {
                        let s = s.as_deref().unwrap_or_default();
                        let from = v.today - chrono::Duration::days(365);
                        let hi = since(s, from)
                            .iter()
                            .map(|(_, c)| *c)
                            .fold(p.price, f64::max);
                        if hi > 0.0 && !s.is_empty() {
                            let off = (p.price / hi - 1.0) * 100.0;
                            Span::styled(
                                format!("{off:.0}%"),
                                if off > -5.0 { t.up() } else { t.dim() },
                            )
                        } else {
                            Span::raw("")
                        }
                    }
                    (9, Some(p)) => match &h {
                        Some(h) if h.first.is_some() => {
                            let mark = if h.complete(p.qty) { "" } else { ">" };
                            Span::styled(
                                format!("{mark}{}", held(h.first.unwrap(), v.today)),
                                t.dim(),
                            )
                        }
                        _ => Span::raw(""),
                    },
                    _ => Span::raw(""),
                };
                cell(i, span)
            });
            Row::new(cells.collect::<Vec<_>>())
        })
        .collect();
    let header = Row::new(cols.iter().map(|&i| cell(i, Span::raw(COLS[i].title)))).style(t.dim());
    let widths: Vec<Constraint> = cols
        .iter()
        .map(|&i| Constraint::Length(COLS[i].width))
        .collect();
    let table = Table::new(rows, widths)
        .header(header)
        .column_spacing(1)
        .row_highlight_style(t.selected())
        .style(t.base());
    let mut state = TableState::default().with_selected(Some(v.sel));
    frame.render_stateful_widget(table, area, &mut state);
}

/// Card for the highlighted entry. Headline is all-time P&L from the whole
/// transaction history (open gain + realized sales + dividends); the chart
/// shows the price with buys/sells marked and the average cost line.
pub fn spotlight(frame: &mut Frame, area: Rect, v: &TableView) {
    let (t, e, tot) = (v.theme, &v.rows[v.sel], v.tot);
    let card = Block::bordered()
        .border_style(Style::new().fg(e.color))
        .title_top(Line::from(vec![
            Span::styled(" ● ", Style::new().fg(e.color)),
            Span::styled(format!("{} ", e.label), t.title()),
        ]))
        .padding(Padding::horizontal(1))
        .style(t.base());
    let inner = card.inner(area);
    frame.render_widget(card, area);
    let label = |k: &str, v: String| {
        Line::from(vec![
            Span::styled(format!("{k:<9}"), t.dim()),
            Span::styled(v, t.base()),
        ])
    };
    let weight = format!(
        "{}  ({:.1}% of account)",
        money(e.value),
        e.value / tot.value * 100.0
    );
    let Some(p) = e.pos else {
        let lines = vec![label("Value", weight), Line::styled("uninvested", t.dim())];
        frame.render_widget(Paragraph::new(lines), inner);
        return;
    };
    let h = data::symbol_history(v.txns, &p.symbol);
    let lines = text_lines(t, p, &h, weight);

    // Beside the text only when stacking would leave the chart too short.
    let side_by_side = inner.width >= TEXT_W + 30 && inner.height < TEXT_ROWS + 10;
    let (text, chart) = if side_by_side {
        let [a, _, b] = inner.layout(&Layout::horizontal([
            Constraint::Length(TEXT_W),
            Constraint::Length(2),
            Constraint::Fill(1),
        ]));
        (a, b)
    } else {
        let [a, b] = inner.layout(&Layout::vertical([
            Constraint::Length(lines.len() as u16),
            Constraint::Fill(1),
        ]));
        (a, b)
    };
    frame.render_widget(Paragraph::new(lines), text);
    if chart.height >= 4 && chart.width >= 20 {
        let s = series(v.closes, &p.symbol, p.price, v.today);
        price_chart(frame, chart, t, e.color, p.price_paid, &h, &s, v.today);
    }
}

/// Rows the card text needs (for sizing the card).
pub const TEXT_ROWS: u16 = 7;

fn text_lines<'a>(
    t: &Theme,
    p: &data::Position,
    h: &SymbolHistory,
    weight: String,
) -> Vec<Line<'a>> {
    let label = |k: &str, v: String| {
        Line::from(vec![
            Span::styled(format!("{k:<9}"), t.dim()),
            Span::styled(v, t.base()),
        ])
    };
    let complete = h.complete(p.qty);
    // Without a full history the cash-flow number is wrong, so fall back
    // to E*TRADE's open gain on cost and say so.
    let (pnl, base) = if complete {
        (h.all_time_pnl(p.value), h.bought)
    } else {
        (p.total_gain, p.price_paid * p.qty)
    };
    let pct = if base > 0.0 { pnl / base * 100.0 } else { 0.0 };
    let mut lines = vec![Line::from(vec![
        Span::styled(format!("{:<9}", "P&L"), t.dim()),
        Span::styled(signed_money(pnl), t.signed(pnl).bold()),
        Span::styled(format!("  {}", signed_pct(pct)), t.signed(pct)),
        Span::styled(if complete { "  all-time" } else { "  open" }, t.dim()),
    ])];
    if complete {
        let open = p.total_gain;
        let realized = pnl - open;
        lines.push(Line::from(vec![
            Span::styled(format!("{:<9}", "Open"), t.dim()),
            Span::styled(signed_money(open), t.signed(open)),
            Span::styled("  realized+div ", t.dim()),
            Span::styled(signed_money(realized), t.signed(realized)),
        ]));
    } else {
        let note = h.first.map_or_else(
            || "no trades cached".to_string(),
            |d| format!("trade history from {} only", d.format("%b %Y")),
        );
        lines.push(Line::from(vec![
            Span::styled(format!("{:<9}", ""), t.dim()),
            Span::styled(note, t.accent()),
        ]));
    }
    lines.extend([
        Line::from(vec![
            Span::styled(format!("{:<9}", "Today"), t.dim()),
            Span::styled(signed_money(p.day_gain), t.signed(p.day_gain)),
            Span::styled(format!("  {}", signed_pct(p.day_pct)), t.signed(p.day_pct)),
        ]),
        label("Value", weight),
        label(
            "Shares",
            format!(
                "{:.0} @ ${:.2} avg, now ${:.2}",
                p.qty, p.price_paid, p.price
            ),
        ),
        label(
            "Flow",
            format!(
                "in {} · out {} · div {}",
                money(h.bought),
                money(h.sold),
                money(h.income)
            ),
        ),
    ]);
    if let Some(tx) = h.recent.first() {
        let (verb, style) = if tx.qty >= 0.0 {
            ("bought", t.up())
        } else {
            ("sold", t.down())
        };
        lines.push(Line::from(vec![
            Span::styled(format!("{:<9}", "Last"), t.dim()),
            Span::styled(format!("{} ", tx.date.format("%b %d")), t.base()),
            Span::styled(verb, style),
            Span::styled(format!(" {:.0} @ ${:.2}", tx.qty.abs(), tx.price), t.base()),
            Span::styled(format!(" · {} trades", h.trades), t.dim()),
        ]));
    }
    lines
}

/// Price since CHART_DAYS ago (or the first buy, if earlier and within a
/// year) with the average cost as a flat line and ▲/▼ at each trade.
#[allow(clippy::too_many_arguments)]
fn price_chart(
    frame: &mut Frame,
    area: Rect,
    t: &Theme,
    color: Color,
    avg: f64,
    h: &SymbolHistory,
    s: &[(NaiveDate, f64)],
    today: NaiveDate,
) {
    let mut from = today - chrono::Duration::days(CHART_DAYS);
    if let Some(f) = h
        .first
        .filter(|f| *f >= today - chrono::Duration::days(365))
    {
        from = from.min(f - chrono::Duration::days(7));
    }
    let s = since(s, from);
    if s.len() < 2 {
        let msg = Paragraph::new("no price history cached").style(t.dim());
        frame.render_widget(msg, area.centered_vertically(Constraint::Length(1)));
        return;
    }
    let x0 = s[0].0;
    let x = |d: NaiveDate| (d - x0).num_days() as f64;
    let xmax = x(s[s.len() - 1].0).max(1.0);
    let trades: Vec<&Txn> = h.recent.iter().filter(|tx| tx.date >= x0).collect();
    let (mut lo, mut hi) = s
        .iter()
        .map(|(_, c)| *c)
        .chain(trades.iter().map(|tx| tx.price))
        .chain((avg > 0.0).then_some(avg))
        .fold((f64::MAX, f64::MIN), |(l, h), v| (l.min(v), h.max(v)));
    let pad = ((hi - lo) * 0.06).max(hi * 0.005);
    lo -= pad;
    hi += pad;

    let fmt = |v: f64| {
        if v >= 100.0 {
            format!("${v:.0}")
        } else {
            format!("${v:.2}")
        }
    };
    let lab_w = fmt(hi).len().max(fmt(lo).len()) as u16 + 1;
    let [ylab, plot] = area.layout(&Layout::horizontal([
        Constraint::Length(lab_w),
        Constraint::Fill(1),
    ]));
    let [plot, xlab] = plot.layout(&Layout::vertical([
        Constraint::Fill(1),
        Constraint::Length(1),
    ]));

    let line: Vec<(f64, f64)> = s.iter().map(|(d, c)| (x(*d), *c)).collect();
    let cost = vec![(0.0, avg), (xmax, avg)];
    let mut datasets = Vec::new();
    if avg > 0.0 {
        datasets.push(
            Dataset::default()
                .marker(Marker::Braille)
                .graph_type(GraphType::Line)
                .style(t.dim())
                .data(&cost),
        );
    }
    datasets.push(
        Dataset::default()
            .marker(Marker::Braille)
            .graph_type(GraphType::Line)
            .style(Style::new().fg(color))
            .data(&line),
    );
    let chart = Chart::new(datasets)
        .style(t.base())
        .x_axis(Axis::default().bounds([0.0, xmax]))
        .y_axis(Axis::default().bounds([lo, hi]))
        .legend_position(None);
    frame.render_widget(chart, plot);

    // Trade markers drawn over the braille line, one cell each.
    let buf = frame.buffer_mut();
    let to_cell = |xv: f64, yv: f64| {
        let cx = plot.x + ((xv / xmax) * f64::from(plot.width - 1)).round() as u16;
        let cy = plot.y + (((hi - yv) / (hi - lo)) * f64::from(plot.height - 1)).round() as u16;
        (cx.min(plot.right() - 1), cy.min(plot.bottom() - 1))
    };
    // Trades landing in the same cell merge; glyph size is the cell's
    // dollar amount relative to the biggest one on the chart.
    let mut cells: Vec<((u16, u16, bool), f64)> = Vec::new();
    for tx in &trades {
        let (cx, cy) = to_cell(x(tx.date), tx.price);
        let key = (cx, cy, tx.qty >= 0.0);
        let amt = (tx.qty * tx.price).abs();
        match cells.iter_mut().find(|(k, _)| *k == key) {
            Some((_, sum)) => *sum += amt,
            None => cells.push((key, amt)),
        }
    }
    let biggest = cells.iter().map(|(_, a)| *a).fold(0.0, f64::max);
    for ((cx, cy, buy), amt) in cells {
        let frac = if biggest > 0.0 { amt / biggest } else { 1.0 };
        let style = if buy { t.up() } else { t.down() };
        buf[(cx, cy)]
            .set_symbol(trade_glyph(buy, frac))
            .set_style(style.bold());
    }
    if avg > 0.0 {
        let (_, cy) = to_cell(0.0, avg);
        let tag = format!("avg {}", fmt(avg));
        if plot.width as usize > tag.len() + 2 {
            let cx = plot.x + 1;
            buf.set_string(cx, cy, &tag, t.dim());
        }
    }

    buf.set_string(ylab.x, plot.y, fmt(hi), t.dim());
    if plot.height > 1 {
        buf.set_string(ylab.x, plot.bottom() - 1, fmt(lo), t.dim());
    }
    let first = s[0].0.format("%b %d").to_string();
    let last = s[s.len() - 1].0.format("%b %d").to_string();
    frame.render_widget(Paragraph::new(first).style(t.dim()), xlab);
    frame.render_widget(Paragraph::new(last).style(t.dim()).right_aligned(), xlab);
}

/// Buy/sell marker in three sizes; `frac` is the trade's dollar amount
/// over the largest on the chart.
fn trade_glyph(buy: bool, frac: f64) -> &'static str {
    let tier = usize::from(frac > 1.0 / 3.0) + usize::from(frac > 2.0 / 3.0);
    if buy {
        ["▵", "▴", "▲"][tier]
    } else {
        ["▿", "▾", "▼"][tier]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn trade_glyph_grows_with_size() {
        assert_eq!(trade_glyph(true, 0.1), "▵");
        assert_eq!(trade_glyph(true, 0.5), "▴");
        assert_eq!(trade_glyph(true, 1.0), "▲");
        assert_eq!(trade_glyph(false, 1.0), "▼");
    }

    #[test]
    fn spark_spans_low_to_high() {
        assert_eq!(spark(&[1.0, 2.0, 3.0], 3), "▁▅█");
        assert_eq!(spark(&[1.0], 5), "");
        // resampled down to the width, keeping the last value
        assert_eq!(spark(&[1.0, 9.0, 2.0, 3.0], 2).chars().count(), 2);
    }

    #[test]
    fn bar_scales_to_max() {
        assert_eq!(bar(10.0, 10.0, 3), "███");
        assert_eq!(bar(5.0, 10.0, 2), "█");
        assert_eq!(bar(0.0, 10.0, 3), "");
    }

    #[test]
    fn columns_drop_by_priority() {
        assert_eq!(fit_cols(500).len(), COLS.len());
        let narrow = fit_cols(30);
        assert!(narrow.contains(&0) && narrow.contains(&1) && narrow.contains(&3));
        assert!(!narrow.contains(&9));
        assert!(narrow.windows(2).all(|w| w[0] < w[1]));
    }

    #[test]
    fn held_units() {
        let d = |y, m, dd| NaiveDate::from_ymd_opt(y, m, dd).unwrap();
        assert_eq!(held(d(2026, 9, 1), d(2026, 9, 13)), "12d");
        assert_eq!(held(d(2026, 1, 1), d(2026, 9, 1)), "8mo");
        assert_eq!(held(d(2023, 1, 1), d(2026, 1, 1)), "3.0y");
    }
}
