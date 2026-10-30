// Exposure tab (3) layout helpers. Its numbers come from data.rs; nothing here is mock data.

use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Sparkline};

use super::data::{self, Cluster, Concentration, Exposure, Position, Totals};
use crate::ui::theme::Theme;

/// Same frame as `panel`, for panels showing real data.
fn live_panel<'a>(t: &Theme, title: &str) -> Block<'a> {
    Block::bordered()
        .border_style(t.border())
        .title_top(Line::from(Span::styled(format!(" {title} "), t.title())))
        .style(t.base())
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
