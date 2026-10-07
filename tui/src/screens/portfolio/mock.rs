// Tabs 2-6 as skeletons: real layout and key handling, hard-coded mock rows.
// Every panel title says "mock" so nothing here is mistaken for real data.
// Replace each `MOCK_*` const with a loader in data.rs as the tab gets built.

use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Paragraph, Row, Table, TableState};

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
                Span::styled(format!("{name:<14}"), t.base()),
                Span::styled("█".repeat(n), t.accent()),
                Span::styled(format!(" {pct:.0}%"), t.dim()),
            ])
        })
        .collect()
}

pub fn exposure(frame: &mut Frame, area: Rect, t: &Theme) {
    let [left, right] = area.layout(&Layout::horizontal([
        Constraint::Percentage(55),
        Constraint::Fill(1),
    ]));
    let [sector, cluster] = left.layout(&Layout::vertical([
        Constraint::Percentage(55),
        Constraint::Fill(1),
    ]));

    let block = panel(t, "By industry");
    let inner = block.inner(sector);
    frame.render_widget(block, sector);
    let rows = [
        ("Semis", 38.0),
        ("Equipment", 15.0),
        ("Memory", 10.0),
        ("Software", 19.0),
        ("Power", 6.0),
        ("Cash", 6.0),
    ];
    frame.render_widget(
        Paragraph::new(bars(t, &rows, inner.width as usize)).style(t.base()),
        inner,
    );

    let block = panel(t, "Correlation clusters");
    let inner = block.inner(cluster);
    frame.render_widget(block, cluster);
    frame.render_widget(
        Paragraph::new(vec![
            Line::styled("NVDA AMD AVGO MRVL   ρ > 0.8   58% of book", t.base()),
            Line::styled("VRT ETN               ρ > 0.7   11% of book", t.base()),
            Line::styled("AI-exposed share of book: 71%", t.dim()),
        ])
        .style(t.base()),
        inner,
    );

    let block = panel(t, "Concentration");
    let inner = block.inner(right);
    frame.render_widget(block, right);
    let kv = |k: &str, v: &str, warn: bool| {
        Line::from(vec![
            Span::styled(format!("{k:<12}"), t.dim()),
            Span::styled(v.to_string(), if warn { t.accent() } else { t.base() }),
        ])
    };
    frame.render_widget(
        Paragraph::new(vec![
            kv("Top 1", "22%  ⚠ over 20%", true),
            kv("Top 3", "45%", false),
            kv("Top 5", "61%", false),
            kv("HHI", "0.14", false),
            kv("Positions", "12", false),
            kv("Countries", "US 88%  TW 8%  KR 4%", false),
        ])
        .style(t.base()),
        inner,
    );
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
