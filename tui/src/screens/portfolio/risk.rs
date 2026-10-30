// Portfolio risk (tab 4): volatility, beta and drawdown over the chosen range,
// plus position concentration. Everything is computed from the cached
// portfolio history and benchmark closes in data.rs.

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use super::data::{self, Bench, Data, Range, Snapshot};
use crate::ui::theme::Theme;

/// Fewest daily returns that make a beta worth showing.
const MIN_BETA_DAYS: usize = 20;

pub fn draw(frame: &mut Frame, area: Rect, t: &Theme, d: &Data, range: Range, bench: Bench) {
    let win = data::window(&d.history, range);
    if win.len() < 2 {
        frame.render_widget(
            Paragraph::new("not enough history for this range")
                .style(t.dim())
                .centered(),
            area,
        );
        return;
    }
    let twr = data::twr_pct(win);
    let dd = data::drawdown(&twr);
    let bench_cum = d
        .bench
        .get(bench.symbol())
        .and_then(|c| data::bench_pct(win, c));
    let st = data::stats(win, &twr, bench_cum.as_deref());
    let beta = bench_cum.as_deref().and_then(|b| beta(win, b));
    let tot = data::totals(&d.history, &d.positions);
    let conc = data::concentration(&d.positions, &tot);

    let [left, right] =
        Layout::horizontal([Constraint::Percentage(60), Constraint::Percentage(40)]).areas(area);
    let risk = vec![
        kv(
            t,
            &format!("Return, {}", range.label()),
            pct(st.ret),
            Some(st.ret),
        ),
        kv(
            t,
            &format!("Benchmark {}", bench.symbol()),
            st.bench_ret.map_or("n/a".into(), pct),
            st.bench_ret,
        ),
        kv(
            t,
            "Volatility (annualised)",
            format!("{:.1}%", st.vol),
            None,
        ),
        kv(
            t,
            "Return / volatility",
            if st.vol > 0.0 {
                format!("{:.2}  (no risk-free rate)", st.ret / st.vol)
            } else {
                "n/a".into()
            },
            None,
        ),
        kv(
            t,
            &format!("Beta vs {}", bench.symbol()),
            beta.map_or("n/a".into(), |b| format!("{b:.2}")),
            None,
        ),
        kv(t, "Max drawdown", pct(st.max_dd), Some(st.max_dd)),
        kv(
            t,
            "Current drawdown",
            pct(dd.last().copied().unwrap_or(0.0)),
            Some(dd.last().copied().unwrap_or(0.0)),
        ),
        kv(t, "Best day", day(st.best_day), Some(st.best_day.0)),
        kv(t, "Worst day", day(st.worst_day), Some(st.worst_day.0)),
        kv(t, "Up days", format!("{:.0}%", st.up_days), None),
    ];
    frame.render_widget(lines_block(t, "Risk", risk), left);

    let concentration = vec![
        kv(t, "Top 3", format!("{:.0}%", conc.top3), None),
        kv(t, "Top 5", format!("{:.0}%", conc.top5), None),
        kv(t, "HHI", format!("{:.2}", conc.hhi), None),
        kv(t, "Positions", conc.count.to_string(), None),
    ];
    frame.render_widget(lines_block(t, "Concentration", concentration), right);
}

/// Beta of the portfolio's daily returns against the benchmark's, over the
/// window. `bench_cum` is the benchmark's cumulative % path aligned to `win`.
fn beta(win: &[Snapshot], bench_cum: &[f64]) -> Option<f64> {
    let (mut xs, mut ys) = (Vec::new(), Vec::new());
    for i in 1..win.len().min(bench_cum.len()) {
        let (b0, b1) = (1.0 + bench_cum[i - 1] / 100.0, 1.0 + bench_cum[i] / 100.0);
        xs.push(b1 / b0 - 1.0);
        ys.push(win[i].day_pct / 100.0);
    }
    if xs.len() < MIN_BETA_DAYS {
        return None;
    }
    let mean = |v: &[f64]| v.iter().sum::<f64>() / v.len() as f64;
    let (mx, my) = (mean(&xs), mean(&ys));
    let cov: f64 = xs.iter().zip(&ys).map(|(x, y)| (x - mx) * (y - my)).sum();
    let var: f64 = xs.iter().map(|x| (x - mx).powi(2)).sum();
    (var > 0.0).then(|| cov / var)
}

fn pct(v: f64) -> String {
    format!("{v:+.2}%")
}

fn day((pct, date): (f64, Option<NaiveDate>)) -> String {
    match date {
        Some(d) => format!("{pct:+.2}%  {d}"),
        None => "n/a".into(),
    }
}

fn kv<'a>(t: &Theme, label: &str, value: String, signed: Option<f64>) -> Line<'a> {
    let style = match signed {
        Some(v) => t.signed(v),
        None => t.base(),
    };
    Line::from(vec![
        Span::styled(format!(" {label:<26}"), t.dim()),
        Span::styled(value, style),
    ])
}

fn lines_block<'a>(t: &Theme, title: &str, lines: Vec<Line<'a>>) -> Paragraph<'a> {
    Paragraph::new(lines).style(t.base()).block(
        Block::bordered()
            .border_style(t.border())
            .title_top(Line::from(Span::styled(format!(" {title} "), t.title())))
            .style(t.base()),
    )
}
