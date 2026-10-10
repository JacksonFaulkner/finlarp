// Tab 3 (exposure) runs on real data from data.rs. Tabs 4-6 are still
// skeletons: real layout and key handling, hard-coded mock rows, and every
// panel title says "mock" so nothing there is mistaken for real data.
// Replace each `MOCK_*` const with a loader in data.rs as the tab gets built.

use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Paragraph, Row, Sparkline, Table, TableState};

use super::data::{self, Cluster, Concentration, Exposure, Position, Totals};
use crate::ui::theme::Theme;

/// (title, header labels, column widths)
type TableSpec<'a> = (&'a str, &'a [&'a str], &'a [Constraint]);

const TAG: &str = " · mock";

fn panel<'a>(t: &Theme, title: &str) -> Block<'a> {
    Block::bordered()
        .border_style(t.border())
        .title_top(Line::from(vec![
            Span::styled(format!(" {title}"), t.title()),
            Span::styled(format!("{TAG} "), t.dim()),
        ]))
        .style(t.base())
}

/// Same frame as `panel`, for panels showing real data.
fn live_panel<'a>(t: &Theme, title: &str) -> Block<'a> {
    Block::bordered()
        .border_style(t.border())
        .title_top(Line::from(Span::styled(format!(" {title} "), t.title())))
        .style(t.base())
}

fn signed_cell<'a>(t: &Theme, text: String, v: f64) -> Cell<'a> {
    Cell::from(text).style(t.signed(v))
}

/// Bordered table with a highlighted row; `sel` is clamped to the rows.
fn table(
    frame: &mut Frame,
    area: Rect,
    t: &Theme,
    (title, header, widths): TableSpec,
    rows: Vec<Row>,
    sel: Option<usize>,
) {
    let n = rows.len();
    let mut state = TableState::default().with_selected(sel.map(|s| s.min(n.saturating_sub(1))));
    let table = Table::new(rows, widths.to_vec())
        .header(Row::new(header.iter().map(|h| Cell::from(*h))).style(t.dim()))
        .row_highlight_style(t.selected())
        .block(panel(t, title))
        .style(t.base());
    frame.render_stateful_widget(table, area, &mut state);
}

fn bars<'a>(t: &Theme, rows: &[(&str, f64)], width: usize) -> Vec<Line<'a>> {
    let max = rows.iter().map(|r| r.1).fold(1.0, f64::max);
    let bar_w = width.saturating_sub(24).max(1);
    rows.iter()
        .map(|(name, pct)| {
            let n = (pct / max * bar_w as f64).round() as usize;
            Line::from(vec![
                Span::styled(format!("{name:<18.18}"), t.base()),
                Span::styled("█".repeat(n), t.accent()),
                Span::styled(format!(" {pct:.0}%"), t.dim()),
            ])
        })
        .collect()
}

/// Real-data inputs for the exposure tab. `positions` and `tot` drive the
/// industry and concentration panels; `exp` holds the drift and clusters
/// that `data::load` derived from the history and trade log.
pub struct ExposureView<'a> {
    pub theme: &'a Theme,
    pub positions: &'a [Position],
    pub tot: &'a Totals,
    pub exp: &'a Exposure,
}

/// Drift rows shown at once; the rest are folded into "Other" at draw time.
const DRIFT_ROWS: usize = 5;
/// Sparkline values are weight % × 10, so 1000 is 100%.
const SPARK_MAX: u64 = 1000;

pub fn exposure(frame: &mut Frame, area: Rect, v: &ExposureView) {
    let t = v.theme;
    let [left, right] = area.layout(&Layout::horizontal([
        Constraint::Percentage(55),
        Constraint::Fill(1),
    ]));
    let [sector, cluster] = left.layout(&Layout::vertical([
        Constraint::Percentage(55),
        Constraint::Fill(1),
    ]));
    let [drift, conc] = right.layout(&Layout::vertical([
        Constraint::Percentage(55),
        Constraint::Fill(1),
    ]));

    let block = live_panel(t, "By industry");
    let inner = block.inner(sector);
    frame.render_widget(block, sector);
    let alloc = data::allocation(v.positions, v.tot, inner.height.max(2) as usize);
    let rows: Vec<(&str, f64)> = alloc.iter().map(|(k, p)| (k.as_str(), *p)).collect();
    frame.render_widget(
        Paragraph::new(bars(t, &rows, inner.width as usize)).style(t.base()),
        inner,
    );

    let block = live_panel(t, "Correlation clusters");
    let inner = block.inner(cluster);
    frame.render_widget(block, cluster);
    frame.render_widget(
        Paragraph::new(cluster_lines(t, &v.exp.clusters, inner.height as usize)).style(t.base()),
        inner,
    );

    let block = live_panel(t, "Industry drift");
    let inner = block.inner(drift);
    frame.render_widget(block, drift);
    draw_drift(frame, inner, t, v.exp);

    let block = live_panel(t, "Concentration");
    let inner = block.inner(conc);
    frame.render_widget(block, conc);
    let c = data::concentration(v.positions, v.tot);
    frame.render_widget(
        Paragraph::new(concentration_lines(t, &c)).style(t.base()),
        inner,
    );
}

fn cluster_lines<'a>(t: &Theme, clusters: &[Cluster], height: usize) -> Vec<Line<'a>> {
    if clusters.is_empty() {
        return vec![Line::styled(
            "no pairs at ρ ≥ 0.70 over 30+ shared days",
            t.dim(),
        )];
    }
    let mut lines: Vec<Line> = clusters
        .iter()
        .take(height.saturating_sub(1).max(1))
        .map(|c| {
            Line::from(vec![
                Span::styled(format!("{:<22}", c.symbols.join(" ")), t.base()),
                Span::styled(format!("ρ {:.2}  ", c.avg_rho), t.dim()),
                Span::styled(format!("{:>4.0}% of book", c.weight_pct), t.base()),
            ])
        })
        .collect();
    let in_clusters: f64 = clusters.iter().map(|c| c.weight_pct).sum();
    lines.push(Line::styled(
        format!("{in_clusters:.0}% of account value sits in a cluster"),
        t.dim(),
    ));
    lines
}

/// One sparkline per industry, newest on the right, with the latest weight.
/// Dates are sampled evenly down to the panel width.
fn draw_drift(frame: &mut Frame, area: Rect, t: &Theme, exp: &Exposure) {
    if exp.drift.is_empty() || exp.dates.is_empty() {
        frame.render_widget(
            Paragraph::new(Line::styled("no trades in the cached history", t.dim())),
            area,
        );
        return;
    }
    let n = exp.dates.len();
    let sample = |series: &[f64], width: usize| -> Vec<u64> {
        (0..width)
            .map(|i| {
                let idx = if width == 1 {
                    n - 1
                } else {
                    i * (n - 1) / (width - 1)
                };
                (series[idx] * 10.0).round().clamp(0.0, SPARK_MAX as f64) as u64
            })
            .collect()
    };

    let mut shown: Vec<(String, Vec<f64>)> = exp.drift.iter().take(DRIFT_ROWS).cloned().collect();
    if exp.drift.len() > DRIFT_ROWS {
        let rest: Vec<f64> = (0..n)
            .map(|i| exp.drift[DRIFT_ROWS..].iter().map(|(_, s)| s[i]).sum())
            .collect();
        shown.push(("Other".into(), rest));
    }

    let rows = Layout::vertical(vec![
        Constraint::Length(1);
        shown.len().min(area.height as usize)
    ])
    .split(area);
    for (row, (name, series)) in rows.iter().zip(&shown) {
        let [label, spark, pct] = row.layout(&Layout::horizontal([
            Constraint::Length(18),
            Constraint::Fill(1),
            Constraint::Length(9),
        ]));
        let latest = series.last().copied().unwrap_or(0.0);
        frame.render_widget(Paragraph::new(name.as_str()).style(t.base()), label);
        frame.render_widget(
            Sparkline::default()
                .data(sample(series, spark.width.max(1) as usize))
                .max(SPARK_MAX)
                .style(t.accent()),
            spark,
        );
        frame.render_widget(
            Paragraph::new(format!("{latest:>5.1}%")).style(t.dim()),
            pct,
        );
    }
}

fn concentration_lines<'a>(t: &Theme, c: &Concentration) -> Vec<Line<'a>> {
    let kv = |k: &str, v: String, warn: bool| {
        Line::from(vec![
            Span::styled(format!("{k:<12}"), t.dim()),
            Span::styled(v, if warn { t.accent() } else { t.base() }),
        ])
    };
    vec![
        kv(
            "Top 1",
            format!(
                "{:.0}%{}",
                c.top1,
                if c.top1 > 20.0 { "  ⚠ over 20%" } else { "" }
            ),
            c.top1 > 20.0,
        ),
        kv("Top 3", format!("{:.0}%", c.top3), false),
        kv("Top 5", format!("{:.0}%", c.top5), false),
        kv("HHI", format!("{:.2}", c.hhi), false),
        kv("Positions", c.count.to_string(), false),
    ]
}

pub fn risk(frame: &mut Frame, area: Rect, t: &Theme, sel: usize) {
    let [kpi, body] = area.layout(&Layout::vertical([
        Constraint::Length(3),
        Constraint::Fill(1),
    ]));
    let block = panel(t, "Portfolio risk");
    let inner = block.inner(kpi);
    frame.render_widget(block, kpi);
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("beta 1.42   ", t.base()),
            Span::styled("vol(30d) 24%   ", t.base()),
            Span::styled("sharpe 1.1   ", t.base()),
            Span::styled("max DD -14.2%   ", t.down()),
            Span::styled("VaR95 -$3.1k", t.down()),
        ]))
        .style(t.base()),
        inner,
    );

    let [tbl, cal] = body.layout(&Layout::horizontal([
        Constraint::Fill(2),
        Constraint::Fill(1),
    ]));
    let data: &[(&str, f64, f64, f64, &str, f64)] = &[
        ("AEHR", 6.1, -8.0, 1.9, "8d", 11.0),
        ("NVDA", 3.4, -6.5, 1.7, "50d", 1.2),
        ("MRVL", 4.0, -7.0, 1.5, "64d", 3.4),
        ("MU", 3.8, -9.0, 1.4, "78d", 2.9),
        ("VRT", 3.1, -5.5, 1.3, "29d", 2.0),
    ];
    let rows = data
        .iter()
        .map(|r| {
            Row::new(vec![
                Cell::from(r.0),
                Cell::from(format!("{:.1}", r.1)),
                signed_cell(t, format!("{:.1}%", r.2), r.2),
                Cell::from(format!("{:.1}", r.3)),
                Cell::from(r.4).style(if r.4 == "8d" { t.accent() } else { t.dim() }),
                Cell::from(format!("{:.1}%", r.5)),
            ])
        })
        .collect();
    table(
        frame,
        tbl,
        t,
        (
            "Per position",
            &["Sym", "ATR%", "Stop", "Beta", "Earn in", "Short int"],
            &[
                Constraint::Length(7),
                Constraint::Length(6),
                Constraint::Length(8),
                Constraint::Length(6),
                Constraint::Length(9),
                Constraint::Fill(1),
            ],
        ),
        rows,
        Some(sel),
    );

    let block = panel(t, "Earnings calendar");
    let inner = block.inner(cal);
    frame.render_widget(block, cal);
    let ev = [
        ("Oct 07", "AEHR", true),
        ("Oct 29", "VRT", false),
        ("Nov 19", "NVDA", false),
        ("Dec 03", "MRVL", false),
    ];
    frame.render_widget(
        Paragraph::new(
            ev.iter()
                .map(|(d, s, soon)| {
                    Line::from(vec![
                        Span::styled(format!("{d}  "), t.dim()),
                        Span::styled(*s, if *soon { t.accent() } else { t.base() }),
                        Span::styled(if *soon { "  ⚠ within 7d" } else { "" }, t.accent()),
                    ])
                })
                .collect::<Vec<_>>(),
        )
        .style(t.base()),
        inner,
    );
}

/// date, type, symbol, qty, price, realized, term, flags
type MockTxn = (
    &'static str,
    &'static str,
    &'static str,
    f64,
    f64,
    f64,
    &'static str,
    &'static str,
);

pub fn activity(frame: &mut Frame, area: Rect, t: &Theme, sel: usize) {
    let [strip, body] = area.layout(&Layout::vertical([
        Constraint::Length(1),
        Constraint::Fill(1),
    ]));
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled(" Orders ", t.dim()),
            Span::styled(" Transactions ", t.selected()),
            Span::styled(" Dividends ", t.dim()),
            Span::styled(" Lots ", t.dim()),
        ]))
        .style(t.base()),
        strip,
    );
    let data: &[MockTxn] = &[
        ("09-12", "SELL", "AMD", 50.0, 162.0, 610.0, "LT", ""),
        (
            "09-02",
            "SELL",
            "INTC",
            100.0,
            22.0,
            -340.0,
            "ST",
            "wash-sale window",
        ),
        ("08-21", "BUY", "AEHR", 200.0, 14.2, 0.0, "", ""),
        ("08-14", "DIV", "AVGO", 0.0, 0.0, 34.5, "", ""),
        ("08-02", "SELL", "MU", 40.0, 101.0, 220.0, "ST", ""),
    ];
    let rows = data
        .iter()
        .map(|r| {
            Row::new(vec![
                Cell::from(r.0).style(t.dim()),
                Cell::from(r.1),
                Cell::from(r.2),
                Cell::from(if r.3 > 0.0 {
                    format!("{:.0}", r.3)
                } else {
                    "".into()
                }),
                Cell::from(if r.4 > 0.0 {
                    format!("${:.2}", r.4)
                } else {
                    "".into()
                }),
                if r.5 == 0.0 {
                    Cell::from("")
                } else {
                    signed_cell(t, format!("{:+.0}", r.5), r.5)
                },
                Cell::from(r.6),
                Cell::from(r.7).style(t.accent()),
            ])
        })
        .collect();
    table(
        frame,
        body,
        t,
        (
            "Transactions",
            &[
                "Date", "Type", "Sym", "Qty", "Price", "Realized", "Term", "Flags",
            ],
            &[
                Constraint::Length(7),
                Constraint::Length(6),
                Constraint::Length(7),
                Constraint::Length(6),
                Constraint::Length(10),
                Constraint::Length(10),
                Constraint::Length(6),
                Constraint::Fill(1),
            ],
        ),
        rows,
        Some(sel),
    );
}

pub fn signals(frame: &mut Frame, area: Rect, t: &Theme, sel: usize) {
    let data: &[(&str, &str, &str, &str)] = &[
        ("09-28", "8-K", "MRVL", "Item 2.02 results"),
        ("09-27", "Form 4", "AEHR", "CEO sold 10k @ $18.40"),
        ("09-25", "13F", "NVDA", "Vanguard +2.1% QoQ"),
        ("09-24", "Risk", "AVGO", "NEW: export license language"),
        ("09-22", "Guide", "VRT", "Raised FY revenue outlook"),
    ];
    let rows = data
        .iter()
        .map(|r| {
            Row::new(vec![
                Cell::from(r.0).style(t.dim()),
                Cell::from(r.1).style(t.accent()),
                Cell::from(r.2),
                Cell::from(r.3),
            ])
        })
        .collect();
    table(
        frame,
        area,
        t,
        (
            "Signals on held names",
            &["Date", "Kind", "Sym", "Summary"],
            &[
                Constraint::Length(7),
                Constraint::Length(8),
                Constraint::Length(7),
                Constraint::Fill(1),
            ],
        ),
        rows,
        Some(sel),
    );
}

/// Row counts for the tabs whose cursor moves, so j/k can clamp.
pub const RISK_LEN: usize = 5;
pub const ACTIVITY_LEN: usize = 5;
pub const SIGNALS_LEN: usize = 5;
