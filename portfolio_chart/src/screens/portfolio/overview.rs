// Tab 1: Overview. KPI strip, equity-vs-benchmark chart (time-weighted %
// since the window start), drawdown chart under it sharing the cursor, and
// a bottom row of top movers / allocation / alerts. All real data.

use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::symbols::Marker;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Axis, Block, Chart, Dataset, GraphType, Paragraph};

use super::data::{self, Bench, Data, Level, Range};
use crate::ui::text;
use crate::ui::theme::Theme;

pub struct View<'a> {
    pub theme: &'a Theme,
    pub data: &'a Data,
    pub range: Range,
    pub bench: Bench,
    pub marker: Marker,
    /// Index into the current window; None = latest.
    pub cursor: Option<usize>,
    /// Unix seconds, for staleness alerts.
    pub now: f64,
}

/// $12,345
pub fn money(v: f64) -> String {
    let s = format!("{:.0}", v.abs());
    let mut out = String::new();
    for (i, c) in s.chars().enumerate() {
        if i > 0 && (s.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    format!("{}${out}", if v < 0.0 { "-" } else { "" })
}

pub fn signed_money(v: f64) -> String {
    format!("{}{}", if v < 0.0 { "" } else { "+" }, money(v))
}

pub fn signed_pct(v: f64) -> String {
    format!("{v:+.1}%")
}

fn panel<'a>(theme: &Theme, title: impl Into<Line<'a>>) -> Block<'a> {
    Block::bordered()
        .border_style(theme.border())
        .title_top(title.into())
        .style(theme.base())
}

/// Number of window points to clamp the cursor to.
pub fn window_len(data: &Data, range: Range) -> usize {
    data::window(&data.history, range).len()
}

pub fn draw(frame: &mut Frame, area: Rect, v: &View) {
    let t = v.theme;
    let win = data::window(&v.data.history, v.range);
    if win.len() < 2 {
        let msg = "no history yet: open the $ dashboard at least once a day to start tracking";
        let r = area.centered_vertically(Constraint::Length(1));
        frame.render_widget(Paragraph::new(msg).style(t.dim()).centered(), r);
        return;
    }
    let twr = data::twr_pct(win);
    let bench = v
        .data
        .bench
        .get(v.bench.symbol())
        .and_then(|c| data::bench_pct(win, c));
    let dd = data::drawdown(&twr);
    let st = data::stats(win, &twr, bench.as_deref());
    let tot = data::totals(&v.data.history, &v.data.positions);
    let sel = v.cursor.unwrap_or(win.len() - 1).min(win.len() - 1);

    let [kpi, equity, under, bottom] = area.layout(&Layout::vertical([
        Constraint::Length(4),
        Constraint::Fill(3),
        Constraint::Fill(1),
        Constraint::Length(9),
    ]));
    draw_kpis(frame, kpi, v, &tot, &st);
    draw_equity(frame, equity, v, win, &twr, bench.as_deref(), sel);
    draw_drawdown(frame, under, v, &dd, &st, sel);
    draw_bottom(frame, bottom, v, &tot, &st);
}

fn draw_kpis(frame: &mut Frame, area: Rect, v: &View, tot: &data::Totals, st: &data::Stats) {
    let t = v.theme;
    let cols = Layout::horizontal([Constraint::Fill(1); 5]).split(area);
    let cash_pct = if tot.value > 0.0 {
        tot.cash / tot.value * 100.0
    } else {
        0.0
    };
    let bench_line = match st.bench_ret {
        Some(b) => (
            format!("vs {} {}", v.bench.symbol(), signed_pct(b)),
            t.signed(st.ret - b),
            format!("{:+.1} pts", st.ret - b),
        ),
        None => (
            format!("no {} history cached", v.bench.symbol()),
            t.dim(),
            String::new(),
        ),
    };
    let cells: [(String, Line, Line); 5] = [
        (
            " Account ".into(),
            Line::styled(money(tot.value), t.title()),
            Line::styled(
                format!("cash {} ({cash_pct:.0}%)", money(tot.cash)),
                t.dim(),
            ),
        ),
        (
            " Today ".into(),
            Line::from(vec![
                Span::styled(signed_money(tot.day_gain), t.signed(tot.day_gain).bold()),
                Span::styled(
                    format!("  {}", signed_pct(tot.day_pct)),
                    t.signed(tot.day_pct),
                ),
            ]),
            Line::styled(format!("{} positions", v.data.positions.len()), t.dim()),
        ),
        (
            " Total P&L ".into(),
            Line::from(vec![
                Span::styled(
                    signed_money(tot.total_gain),
                    t.signed(tot.total_gain).bold(),
                ),
                Span::styled(
                    format!("  {}", signed_pct(tot.total_pct)),
                    t.signed(tot.total_pct),
                ),
            ]),
            Line::styled(
                format!("on cost {}", money(tot.invested - tot.total_gain)),
                t.dim(),
            ),
        ),
        (
            format!(" {} return (TWR) ", v.range.label()),
            Line::styled(signed_pct(st.ret), t.signed(st.ret).bold()),
            Line::from(vec![
                Span::styled(bench_line.0, t.dim()),
                Span::styled(format!("  {}", bench_line.2), bench_line.1),
            ]),
        ),
        (
            " Risk ".into(),
            Line::from(vec![
                Span::styled(format!("max DD {:.1}%", st.max_dd), t.down().bold()),
                Span::styled(format!("  now {:.1}%", st.cur_dd), t.dim()),
            ]),
            Line::styled(
                format!("vol {:.0}%  up days {:.0}%", st.vol, st.up_days),
                t.dim(),
            ),
        ),
    ];
    for (col, (title, main, sub)) in cols.iter().zip(cells) {
        let block = panel(t, Line::styled(title, t.dim()));
        let inner = block.inner(*col);
        frame.render_widget(block, *col);
        frame.render_widget(Paragraph::new(vec![main, sub]).style(t.base()), inner);
    }
}

fn bounds(series: &[&[f64]], include_zero: bool) -> [f64; 2] {
    let (mut lo, mut hi) = if include_zero {
        (0.0_f64, 0.0_f64)
    } else {
        (f64::MAX, f64::MIN)
    };
    for s in series {
        for &y in *s {
            lo = lo.min(y);
            hi = hi.max(y);
        }
    }
    if lo > hi {
        return [-1.0, 1.0];
    }
    if (hi - lo).abs() < 1e-9 {
        return [lo - 1.0, hi + 1.0];
    }
    let pad = (hi - lo) * 0.06;
    [lo - pad, hi + pad]
}

fn xy(ys: &[f64]) -> Vec<(f64, f64)> {
    ys.iter().enumerate().map(|(i, &y)| (i as f64, y)).collect()
}

/// "Sep 30", or "Sep 2025" when the window is long enough that the year matters.
fn date_label(d: chrono::NaiveDate, long: bool) -> Line<'static> {
    Line::from(d.format(if long { "%b %Y" } else { "%b %d" }).to_string())
}

fn draw_equity(
    frame: &mut Frame,
    area: Rect,
    v: &View,
    win: &[data::Snapshot],
    twr: &[f64],
    bench: Option<&[f64]>,
    sel: usize,
) {
    let t = v.theme;
    let mut series: Vec<&[f64]> = vec![twr];
    if let Some(b) = bench {
        series.push(b);
    }
    let [lo, hi] = bounds(&series, true);
    let mine = xy(twr);
    let theirs = bench.map(xy).unwrap_or_default();
    let guide = vec![(sel as f64, lo), (sel as f64, hi)];
    let dot = vec![(sel as f64, twr[sel])];
    let end_style = t.signed(*twr.last().unwrap_or(&0.0));

    let mut datasets = vec![
        Dataset::default()
            .marker(Marker::Braille)
            .graph_type(GraphType::Line)
            .style(t.border())
            .data(&guide),
    ];
    if bench.is_some() {
        datasets.push(
            Dataset::default()
                .name(v.bench.symbol())
                .marker(v.marker)
                .graph_type(GraphType::Line)
                .style(t.dim())
                .data(&theirs),
        );
    }
    datasets.push(
        Dataset::default()
            .name("you")
            .marker(v.marker)
            .graph_type(GraphType::Line)
            .style(end_style)
            .data(&mine),
    );
    datasets.push(
        Dataset::default()
            .marker(Marker::Dot)
            .graph_type(GraphType::Scatter)
            .style(t.accent())
            .data(&dot),
    );

    let readout = {
        let mut spans = vec![
            Span::styled(format!("{} ", win[sel].date.format("%b %d")), t.dim()),
            Span::styled(format!("you {}", signed_pct(twr[sel])), t.signed(twr[sel])),
        ];
        if let Some(b) = bench {
            spans.push(Span::styled(
                format!("  {} {}", v.bench.symbol(), signed_pct(b[sel])),
                t.dim(),
            ));
            spans.push(Span::styled(
                format!("  {:+.1} pts ", twr[sel] - b[sel]),
                t.signed(twr[sel] - b[sel]),
            ));
        }
        Line::from(spans).right_aligned()
    };
    let block = panel(
        t,
        Line::styled(
            format!(
                " Equity vs {} · time-weighted % since {} ",
                v.bench.symbol(),
                win[0].date.format("%b %d, %Y")
            ),
            t.title(),
        ),
    )
    .title_top(readout);
    let last = win.len() - 1;
    let long = (win[last].date - win[0].date).num_days() > 200;
    let x_labels = vec![
        date_label(win[0].date, long),
        date_label(win[last / 2].date, long),
        date_label(win[last].date, long),
    ];
    let lbl = |y: f64| Line::from(signed_pct(y));
    let chart = Chart::new(datasets)
        .block(block)
        .style(t.base())
        .x_axis(
            Axis::default()
                .bounds([0.0, last.max(1) as f64])
                .labels(x_labels)
                .style(t.dim()),
        )
        .y_axis(
            Axis::default()
                .bounds([lo, hi])
                .labels(vec![lbl(lo), lbl(0.0), lbl(hi)])
                .style(t.dim()),
        )
        .legend_position(None);
    frame.render_widget(chart, area);
}

fn draw_drawdown(
    frame: &mut Frame,
    area: Rect,
    v: &View,
    dd: &[f64],
    st: &data::Stats,
    sel: usize,
) {
    let t = v.theme;
    let lo = (dd.iter().copied().fold(0.0, f64::min) * 1.15).min(-1.0);
    let line = xy(dd);
    let guide = vec![(sel as f64, lo), (sel as f64, 0.0)];
    let dot = vec![(sel as f64, dd[sel])];
    let datasets = vec![
        Dataset::default()
            .marker(Marker::Braille)
            .graph_type(GraphType::Line)
            .style(t.border())
            .data(&guide),
        Dataset::default()
            .marker(v.marker)
            .graph_type(GraphType::Line)
            .style(t.down())
            .data(&line),
        Dataset::default()
            .marker(Marker::Dot)
            .graph_type(GraphType::Scatter)
            .style(t.accent())
            .data(&dot),
    ];
    let block = panel(t, Line::styled(" Drawdown ", t.title())).title_top(
        Line::from(vec![
            Span::styled(format!("at cursor {:.1}%  ", dd[sel]), t.dim()),
            Span::styled(format!("max {:.1}% ", st.max_dd), t.down()),
        ])
        .right_aligned(),
    );
    let chart = Chart::new(datasets)
        .block(block)
        .style(t.base())
        .x_axis(Axis::default().bounds([0.0, (dd.len() - 1).max(1) as f64]))
        .y_axis(
            Axis::default()
                .bounds([lo, 0.0])
                .labels(vec![Line::from(format!("{lo:.0}%")), Line::from("0%")])
                .style(t.dim()),
        )
        .legend_position(None);
    frame.render_widget(chart, area);
}

fn draw_bottom(frame: &mut Frame, area: Rect, v: &View, tot: &data::Totals, st: &data::Stats) {
    let t = v.theme;
    let [movers, alloc, alerts] = area.layout(&Layout::horizontal([
        Constraint::Fill(1),
        Constraint::Fill(1),
        Constraint::Fill(1),
    ]));

    // top movers by absolute dollar change today
    let mut ps: Vec<&data::Position> = v.data.positions.iter().collect();
    ps.sort_by(|a, b| b.day_gain.abs().total_cmp(&a.day_gain.abs()));
    let block = panel(t, Line::styled(" Top movers (day) ", t.title()));
    let inner = block.inner(movers);
    frame.render_widget(block, movers);
    let lines: Vec<Line> = if ps.is_empty() {
        vec![Line::styled("no positions cached", t.dim())]
    } else {
        ps.iter()
            .take(inner.height as usize)
            .map(|p| {
                Line::from(vec![
                    Span::styled(format!("{:<6}", text::truncate(&p.symbol, 6)), t.base()),
                    Span::styled(
                        format!("{:>7}", signed_pct(p.day_pct)),
                        t.signed(p.day_gain),
                    ),
                    Span::styled(
                        format!("{:>10}", signed_money(p.day_gain)),
                        t.signed(p.day_gain),
                    ),
                ])
            })
            .collect()
    };
    frame.render_widget(Paragraph::new(lines).style(t.base()), inner);

    // allocation by industry
    let block = panel(t, Line::styled(" Allocation ", t.title()));
    let inner = block.inner(alloc);
    frame.render_widget(block, alloc);
    let rows = data::allocation(&v.data.positions, tot, inner.height.max(2) as usize);
    let label_w = ((inner.width as usize) / 3).clamp(10, 22);
    let bar_w = (inner.width as usize).saturating_sub(label_w + 7).max(1);
    let max = rows.iter().map(|r| r.1).fold(1.0, f64::max);
    let lines: Vec<Line> = rows
        .iter()
        .map(|(name, pct)| {
            let n = ((pct / max) * bar_w as f64).round() as usize;
            let style = if name == "Cash" { t.dim() } else { t.accent() };
            Line::from(vec![
                Span::styled(
                    format!("{:<label_w$}", text::truncate(name, label_w - 1)),
                    t.base(),
                ),
                Span::styled("█".repeat(n), style),
                Span::styled(format!(" {pct:.0}%"), t.dim()),
            ])
        })
        .collect();
    frame.render_widget(Paragraph::new(lines).style(t.base()), inner);

    // alerts
    let block = panel(t, Line::styled(" Alerts ", t.title()));
    let inner = block.inner(alerts);
    frame.render_widget(block, alerts);
    let al = data::alerts(&v.data.positions, tot, st, v.data.positions_at, v.now);
    let lines: Vec<Line> = if al.is_empty() {
        vec![Line::styled("nothing to flag", t.dim())]
    } else {
        al.iter()
            .take(inner.height as usize)
            .map(|(lvl, msg)| {
                let (mark, style) = match lvl {
                    Level::Warn => ("⚠ ", t.accent()),
                    Level::Info => ("● ", t.dim()),
                };
                Line::from(vec![
                    Span::styled(mark, style),
                    Span::styled(
                        text::truncate(msg, (inner.width as usize).saturating_sub(2)),
                        t.base(),
                    ),
                ])
            })
            .collect()
    };
    frame.render_widget(Paragraph::new(lines).style(t.base()), inner);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn money_groups_and_signs() {
        assert_eq!(money(1234567.4), "$1,234,567");
        assert_eq!(money(-950.0), "-$950");
        assert_eq!(signed_money(12.0), "+$12");
        assert_eq!(signed_money(-12.0), "-$12");
        assert_eq!(signed_pct(-1.234), "-1.2%");
    }

    #[test]
    fn bounds_include_zero_and_pad() {
        let b = bounds(&[&[2.0, 4.0]], true);
        assert!(b[0] < 0.0 && b[1] > 4.0);
        assert_eq!(bounds(&[&[]], false), [-1.0, 1.0]);
        let flat = bounds(&[&[3.0, 3.0]], false);
        assert!(flat[0] < 3.0 && flat[1] > 3.0);
    }
}
