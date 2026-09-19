// CANSLIM scorecard screen — reads the JSON blob `services/canslim.py`
// wrote into canslim_cache directly out of DuckDB (same no-IPC pattern as
// the portfolio history screen) and renders one bordered gauge panel per
// letter, wide enough to show the raw numbers a score came from.

use std::io;
use std::path::Path;
use std::time::Duration;

use crossterm::event::{self, Event, KeyCode};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style, Stylize};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Bar, BarChart, BarGroup, Block, Borders, Clear, Gauge, Paragraph};
use ratatui::Terminal;
use serde_json::Value;

/// Per-letter drill-down content for the Enter-expanded popup. Each variant
/// is a small reusable chart/list shape — new letters add a variant here
/// instead of inventing a one-off widget layout each time.
enum Detail {
    Bars(Vec<BarPoint>),
}

struct BarPoint {
    label: String,
    actual: f64,
    estimate: f64,
}

fn f(v: &Value, path: &[&str]) -> Option<f64> {
    let mut cur = v;
    for key in path {
        cur = cur.get(key)?;
    }
    cur.as_f64()
}

fn s(v: &Value, path: &[&str]) -> Option<String> {
    let mut cur = v;
    for key in path {
        cur = cur.get(key)?;
    }
    cur.as_str().map(|s| s.to_string())
}

/// Rough 0-100 normalization per letter, for the gauge fill only — the raw
/// numbers underneath (rendered alongside) are the actual data; this is
/// just "how good does this look" at a glance, not a stored score.
fn clamp_pct(v: f64, lo: f64, hi: f64) -> u16 {
    (((v - lo) / (hi - lo)).clamp(0.0, 1.0) * 100.0).round() as u16
}

struct Letter {
    key: char,
    title: &'static str,
    score: u16,
    lines: Vec<String>,
    detail: Option<Detail>,
}

fn build_letters(card: &Value) -> Vec<Letter> {
    let c = &card["c"];
    let a = &card["a"];
    let n = &card["n"];
    let sup = &card["s"];
    let l = &card["l"];
    let i = &card["i"];
    let m = &card["m"];

    let fwd_growth = f(c, &["forward_qtr_eps_growth_pct"]);
    let earnings_yoy = f(a, &["trailing_yoy_earnings_growth_pct"]);
    let pct_off_high = f(n, &["pct_off_high"]);
    let vol_surge = f(sup, &["volume_surge_ratio"]);
    let rs = f(l, &["relative_strength_score"]);
    let held_inst = f(i, &["held_pct_institutions"]);
    let trend = s(m, &["trend"]);

    let earnings_bars: Vec<BarPoint> = c
        .get("history")
        .and_then(|v| v.as_array())
        .map(|history| {
            history
                .iter()
                .filter_map(|q| {
                    let label = q.get("quarter_end")?.as_str()?.to_string();
                    let actual = q.get("eps_actual")?.as_f64()?;
                    let estimate = q.get("eps_estimate")?.as_f64()?;
                    Some(BarPoint { label, actual, estimate })
                })
                .collect()
        })
        .unwrap_or_default();

    // IBD's actual C rule wants revenue confirming earnings growth, not
    // just EPS estimate drift — filed revenue YoY (real 10-Q data, not an
    // analyst guess) from the latest quarter in revenue_history.
    let latest_rev_yoy = c
        .get("revenue_history")
        .and_then(|v| v.as_array())
        .and_then(|a| a.last())
        .and_then(|q| q.get("yoy_growth_pct"))
        .and_then(|v| v.as_f64());
    let c_score = match (fwd_growth, latest_rev_yoy) {
        (Some(eps), Some(rev)) => (clamp_pct(eps, 0.0, 25.0) + clamp_pct(rev, 0.0, 25.0)) / 2,
        (Some(eps), None) => clamp_pct(eps, 0.0, 25.0),
        (None, Some(rev)) => clamp_pct(rev, 0.0, 25.0),
        (None, None) => 0,
    };

    vec![
        Letter {
            key: 'C',
            title: "Current Earnings",
            score: c_score,
            lines: vec![
                format!(
                    "eps est: {}  (7d: {}  30d: {}  90d: {})   fwd qoq: {}",
                    fmt_opt(f(c, &["eps_estimate_current"]), ""),
                    fmt_opt(f(c, &["eps_estimate_7d_ago"]), ""),
                    fmt_opt(f(c, &["eps_estimate_30d_ago"]), ""),
                    fmt_opt(f(c, &["eps_estimate_90d_ago"]), ""),
                    fmt_opt(fwd_growth, "%"),
                ),
                format!("filed revenue YoY (SEC): {}", fmt_opt(latest_rev_yoy, "%")),
            ],
            detail: if earnings_bars.is_empty() { None } else { Some(Detail::Bars(earnings_bars)) },
        },
        Letter {
            key: 'A',
            title: "Annual Growth",
            score: earnings_yoy.map(|v| clamp_pct(v, 0.0, 40.0)).unwrap_or(0),
            lines: vec![
                format!(
                    "earnings YoY: {}   revenue YoY: {}   ROE: {}",
                    fmt_opt(earnings_yoy, "%"),
                    fmt_opt(f(a, &["trailing_yoy_revenue_growth_pct"]), "%"),
                    fmt_opt(f(a, &["return_on_equity_pct"]).map(|v| v * 100.0), "%"),
                ),
                fmt_annual_history(a.get("history")),
            ],
            detail: None,
        },
        Letter {
            key: 'N',
            title: "New High",
            score: pct_off_high.map(|v| clamp_pct(30.0 - v, 0.0, 30.0)).unwrap_or(0),
            lines: vec![format!(
                "price: {}   52w hi: {}   52w lo: {}   off high: {}",
                fmt_opt(f(n, &["price_current"]), ""),
                fmt_opt(f(n, &["fifty_two_week_high"]), ""),
                fmt_opt(f(n, &["fifty_two_week_low"]), ""),
                fmt_opt(pct_off_high.map(|v| -v), "%"),
            )],
            detail: None,
        },
        Letter {
            key: 'S',
            title: "Supply/Demand",
            score: vol_surge.map(|v| clamp_pct(v, 0.5, 2.0)).unwrap_or(0),
            lines: vec![format!(
                "shares out: {}   short %float: {}   vol surge (10d/3mo): {}x",
                fmt_shares(f(sup, &["shares_outstanding"])),
                fmt_opt(f(sup, &["short_pct_of_float"]).map(|v| v * 100.0), "%"),
                fmt_opt(vol_surge, ""),
            )],
            detail: None,
        },
        Letter {
            key: 'L',
            title: "Leader/Laggard",
            score: rs.map(|v| clamp_pct(v, -20.0, 20.0)).unwrap_or(0),
            lines: vec![format!(
                "symbol 3mo: {}   SPY 3mo: {}   relative strength: {}",
                fmt_opt(f(l, &["symbol_return_pct"]), "%"),
                fmt_opt(f(l, &["benchmark_return_pct"]), "%"),
                fmt_opt(rs, ""),
            )],
            detail: None,
        },
        Letter {
            key: 'I',
            title: "Institutional",
            score: held_inst.map(|v| clamp_pct(v * 100.0, 0.0, 100.0)).unwrap_or(0),
            detail: None,
            lines: {
                let mut ls = vec![format!(
                    "held by inst: {}   analyst: {}   tgt: {}",
                    fmt_opt(held_inst.map(|v| v * 100.0), "%"),
                    s(i, &["recommendation_key"]).unwrap_or_else(|| "-".into()),
                    fmt_opt(f(i, &["target_mean_price"]), ""),
                )];
                if let Some(holders) = i.get("top_holders").and_then(|v| v.as_array()) {
                    let top3: Vec<String> = holders
                        .iter()
                        .take(3)
                        .filter_map(|h| {
                            let org = h.get("organization")?.as_str()?;
                            let pct = h.get("pct_held")?.as_f64()?;
                            Some(format!("{} {:.1}%", org, pct * 100.0))
                        })
                        .collect();
                    if !top3.is_empty() {
                        ls.push(format!("top: {}", top3.join(", ")));
                    }
                }
                ls
            },
        },
        Letter {
            key: 'M',
            title: "Market Direction",
            score: match trend.as_deref() {
                Some("uptrend") => 100,
                Some("correction") => 50,
                Some("downtrend") => 0,
                _ => 0,
            },
            lines: vec![format!(
                "SPY vs MA50: {}   SPY vs MA200: {}   trend: {}",
                fmt_opt(f(m, &["price_vs_ma50"]), ""),
                fmt_opt(f(m, &["price_vs_ma200"]), ""),
                trend.unwrap_or_else(|| "-".into()),
            )],
            detail: None,
        },
    ]
}

fn fmt_opt(v: Option<f64>, suffix: &str) -> String {
    match v {
        Some(v) => format!("{:.1}{}", v, suffix),
        None => "-".to_string(),
    }
}

fn fmt_shares(v: Option<f64>) -> String {
    match v {
        Some(v) if v >= 1e9 => format!("{:.2}B", v / 1e9),
        Some(v) if v >= 1e6 => format!("{:.1}M", v / 1e6),
        Some(v) => format!("{:.0}", v),
        None => "-".to_string(),
    }
}

/// "FY22 $7.75 | FY23 -$5.34 | FY24 $0.70 | FY25 $7.59" — filed annual EPS
/// (SEC 10-K), a real multi-year trend instead of Yahoo's single trailing
/// YoY figure.
fn fmt_annual_history(history: Option<&Value>) -> String {
    let Some(years) = history.and_then(|v| v.as_array()) else {
        return "SEC filed history: -".to_string();
    };
    if years.is_empty() {
        return "SEC filed history: -".to_string();
    }
    let parts: Vec<String> = years
        .iter()
        .filter_map(|y| {
            let end = y.get("fiscal_year_end")?.as_str()?;
            let fy = end.get(2..4).unwrap_or("??");
            let eps = y.get("eps").and_then(|v| v.as_f64());
            let eps_str = match eps {
                Some(v) => format!("${:.2}", v),
                None => "-".to_string(),
            };
            Some(format!("FY{fy} {eps_str}"))
        })
        .collect();
    format!("SEC filed EPS: {}", parts.join(" | "))
}

fn gauge_color(score: u16) -> Color {
    if score >= 70 {
        Color::Rgb(0x4d, 0x93, 0x75)
    } else if score >= 40 {
        Color::Rgb(0xd9, 0xa5, 0x2c)
    } else {
        Color::Rgb(0xc2, 0x5c, 0x5c)
    }
}

fn load_scorecard(db_path: &Path, symbol: &str) -> Result<Option<Value>, duckdb::Error> {
    let conn = duckdb::Connection::open(db_path)?;
    let mut stmt = conn.prepare("SELECT scorecard_json FROM canslim_cache WHERE symbol = ?")?;
    let mut rows = stmt.query([symbol])?;
    if let Some(row) = rows.next()? {
        let json: String = row.get(0)?;
        Ok(serde_json::from_str(&json).ok())
    } else {
        Ok(None)
    }
}

/// Returns `Ok(true)` if the user pressed `s` on the main screen (not the
/// popup) — a request to jump back to the fzf-lua symbol picker, which
/// `main.rs` turns into a process exit code the tmux-popup shell wrapper
/// watches for. `Ok(false)` is a plain quit (`q`/Esc/Ctrl-C).
pub fn run(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    db_path: &Path,
    symbol: &str,
    bg_style: Style,
) -> io::Result<bool> {
    let mut card = load_scorecard(db_path, symbol).unwrap_or(None);
    let mut selected: usize = 0;
    let mut refreshed_at: Option<std::time::Instant> = None;
    let mut popup_open = false;

    loop {
        terminal.draw(|frame| {
            let area = frame.area();
            frame.render_widget(Paragraph::new("").style(bg_style), area);

            let Some(card) = &card else {
                let msg = Paragraph::new(format!(
                    "no CANSLIM data cached for {symbol} — run `uv run services/canslim.py {symbol}` first"
                ))
                .style(bg_style.fg(Color::Gray));
                frame.render_widget(msg, centered(area, 3));
                return;
            };

            let letters = build_letters(card);
            let price = f(card, &["n", "price_current"]);
            let as_of = card.get("as_of").and_then(|v| v.as_str()).unwrap_or("-");

            let just_refreshed = refreshed_at
                .map(|t| t.elapsed() < Duration::from_millis(1200))
                .unwrap_or(false);
            let header = Line::from(vec![
                Span::styled(format!(" {symbol} "), bg_style.fg(Color::White).bold()),
                Span::styled("CANSLIM Scorecard  ", bg_style.fg(Color::DarkGray)),
                Span::styled(fmt_opt(price, " "), bg_style.fg(Color::White)),
                Span::styled(format!("  as of {as_of}"), bg_style.fg(Color::DarkGray)),
                Span::styled(
                    if just_refreshed { "  refreshed" } else { "  r refresh" },
                    bg_style.fg(if just_refreshed { Color::Rgb(0x4d, 0x93, 0x75) } else { Color::DarkGray }),
                ),
            ]);

            let mut constraints = vec![Constraint::Length(1)];
            constraints.extend(letters.iter().map(|l| Constraint::Length(3 + l.lines.len() as u16)));
            constraints.push(Constraint::Length(1));
            let chunks = Layout::vertical(constraints).split(area);

            frame.render_widget(Paragraph::new(header).style(bg_style), chunks[0]);

            for (idx, letter) in letters.iter().enumerate() {
                let focused = idx == selected;
                let border_color = if focused { Color::White } else { Color::DarkGray };
                let block = Block::default()
                    .borders(Borders::ALL)
                    .title(format!(" {} — {} ", letter.key, letter.title))
                    .title_style(bg_style.fg(Color::White).bold())
                    .style(bg_style.fg(border_color));

                let inner = block.inner(chunks[idx + 1]);
                frame.render_widget(block, chunks[idx + 1]);

                let rows = Layout::vertical(
                    std::iter::once(Constraint::Length(1))
                        .chain(letter.lines.iter().map(|_| Constraint::Length(1)))
                        .collect::<Vec<_>>(),
                )
                .split(inner);

                let gauge = Gauge::default()
                    .gauge_style(Style::default().fg(gauge_color(letter.score)).bg(bg_style.bg.unwrap_or(Color::Reset)))
                    .percent(letter.score)
                    .label(format!("{}%", letter.score));
                frame.render_widget(gauge, rows[0]);

                for (li, line) in letter.lines.iter().enumerate() {
                    frame.render_widget(
                        Paragraph::new(line.as_str()).style(bg_style.fg(Color::Gray)),
                        rows[li + 1],
                    );
                }
            }

            let footer_text = if popup_open {
                " s close "
            } else if letters[selected].detail.is_some() {
                " ↑↓ select   a expand   s search   q quit "
            } else {
                " ↑↓ select   s search   q quit "
            };
            let footer = Line::from(vec![Span::styled(footer_text, bg_style.fg(Color::DarkGray))]);
            frame.render_widget(Paragraph::new(footer).style(bg_style), chunks[chunks.len() - 1]);

            if popup_open {
                if let Some(detail) = &letters[selected].detail {
                    render_detail_popup(frame, area, &letters[selected], detail, bg_style);
                }
            }
        })?;

        if event::poll(Duration::from_millis(200))? {
            if let Event::Key(key) = event::read()? {
                // Some terminals (kitty-protocol-aware ones especially)
                // report both a Press and a Release event per keypress —
                // without this filter a single Enter toggles the popup
                // open then immediately closed again, looking like a dead
                // key. Everything else here is naturally idempotent-ish
                // (j/k clamp, q/esc just return) so it went unnoticed.
                if key.kind != event::KeyEventKind::Press {
                    continue;
                }
                match key.code {
                    KeyCode::Char('s') if popup_open => {
                        popup_open = false;
                    }
                    KeyCode::Char('s') => return Ok(true),
                    KeyCode::Char('q') | KeyCode::Esc if popup_open => {
                        popup_open = false;
                    }
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(false),
                    KeyCode::Char('c')
                        if key.modifiers.contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        return Ok(false);
                    }
                    KeyCode::Char('a') if !popup_open => {
                        let has_detail = card
                            .as_ref()
                            .map(|c| build_letters(c)[selected].detail.is_some())
                            .unwrap_or(false);
                        if has_detail {
                            popup_open = true;
                        }
                    }
                    KeyCode::Up | KeyCode::Char('k') if !popup_open => {
                        selected = selected.saturating_sub(1);
                    }
                    KeyCode::Down | KeyCode::Char('j') if !popup_open => {
                        selected = (selected + 1).min(6);
                    }
                    KeyCode::Char('r') if !popup_open => {
                        // Cheap local DB re-read — picks up whatever a
                        // background `services/canslim.py` refresh wrote,
                        // without blocking the TUI on the network fetch
                        // itself (nvim kicks that off separately).
                        card = load_scorecard(db_path, symbol).unwrap_or(None);
                        refreshed_at = Some(std::time::Instant::now());
                    }
                    _ => {}
                }
            }
        }
    }
}

/// Renders whichever `Detail` variant a letter carries, centered over the
/// whole screen. New variants (a price line chart for N, a holder list for
/// I, ...) add a match arm here — the popup shell (Clear + Block + sizing)
/// stays the same for all of them.
fn render_detail_popup(
    frame: &mut ratatui::Frame,
    area: Rect,
    letter: &Letter,
    detail: &Detail,
    bg_style: Style,
) {
    let popup_area = centered_pct(area, 70, 60);
    frame.render_widget(Clear, popup_area);

    let block = Block::default()
        .borders(Borders::ALL)
        .title(format!(" {} — {} detail ", letter.key, letter.title))
        .title_style(bg_style.fg(Color::White).bold())
        .style(bg_style.fg(Color::White));
    let inner = block.inner(popup_area);
    frame.render_widget(block, popup_area);

    match detail {
        Detail::Bars(points) => {
            let up = Color::Rgb(0x4d, 0x93, 0x75);
            let down = Color::Rgb(0xc2, 0x5c, 0x5c);
            let bars: Vec<Bar> = points
                .iter()
                .flat_map(|p| {
                    let beat = p.actual >= p.estimate;
                    vec![
                        Bar::default()
                            .value((p.estimate.max(0.0) * 100.0) as u64)
                            .text_value(format!("{:.2}", p.estimate))
                            .label(Line::from(format!("{} est", p.label)))
                            .style(Style::default().fg(Color::DarkGray)),
                        Bar::default()
                            .value((p.actual.max(0.0) * 100.0) as u64)
                            .text_value(format!("{:.2}", p.actual))
                            .label(Line::from("actual"))
                            .style(Style::default().fg(if beat { up } else { down })),
                    ]
                })
                .collect();

            let chart = BarChart::default()
                .data(BarGroup::default().bars(&bars))
                .bar_width(9)
                .bar_gap(1)
                .style(bg_style);
            frame.render_widget(chart, Rect { height: inner.height.saturating_sub(2), ..inner });

            let legend = Line::from(vec![
                Span::styled("actual EPS ", bg_style.fg(Color::Gray)),
                Span::styled("green = beat estimate  ", bg_style.fg(up)),
                Span::styled("red = missed", bg_style.fg(down)),
            ]);
            frame.render_widget(
                Paragraph::new(legend),
                Rect { y: inner.y + inner.height.saturating_sub(1), height: 1, ..inner },
            );
        }
    }
}

/// Centers a `Rect` covering `pct_w`%/`pct_h`% of `area`.
fn centered_pct(area: Rect, pct_w: u16, pct_h: u16) -> Rect {
    let w = area.width * pct_w / 100;
    let h = area.height * pct_h / 100;
    Rect {
        x: area.x + (area.width.saturating_sub(w)) / 2,
        y: area.y + (area.height.saturating_sub(h)) / 2,
        width: w,
        height: h,
    }
}

fn centered(area: Rect, height: u16) -> Rect {
    let y = area.y + area.height.saturating_sub(height) / 2;
    Rect { x: area.x, y, width: area.width, height: height.min(area.height) }
}
