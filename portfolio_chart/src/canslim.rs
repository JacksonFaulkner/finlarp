// CANSLIM scorecard screen — reads the JSON blob `services/canslim.py`
// wrote into canslim_cache directly out of DuckDB (same no-IPC pattern as
// the portfolio history screen) and renders a master/detail view: one
// compact row per letter on the left, the selected letter's raw numbers
// on the right.

use std::io;
use std::path::Path;
use std::time::Duration;

use crossterm::event::{self, Event, KeyCode};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style, Stylize};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use ratatui::Terminal;
use serde_json::Value;

/// Per-letter drill-down content rendered inline under the letter's numbers. Each variant
/// is a small reusable chart/list shape — new letters add a variant here
/// instead of inventing a one-off widget layout each time.
enum Detail {
    Earnings(EarningsDetail),
}

struct BarPoint {
    label: String,
    actual: f64,
    estimate: f64,
}

/// C's full drill-down: paired EPS actual-vs-estimate bars (existing),
/// filed quarterly revenue as its own bar series (the "sales confirms
/// earnings" half of IBD's rule), and the estimate-revision trend
/// (90d/30d/7d/current) as a sparkline — is Wall St. raising or cutting
/// numbers lately.
struct EarningsDetail {
    eps_bars: Vec<BarPoint>,
    revenue_bars: Vec<RevenueBar>,
    eps_revision_trend: Vec<f64>,
    as_of: String,
}

struct RevenueBar {
    label: String,
    revenue: f64,
    qoq_growth_pct: Option<f64>,
    yoy_growth_pct: Option<f64>,
    net_margin_pct: Option<f64>,
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
    let as_of = card.get("as_of").and_then(|v| v.as_str()).unwrap_or("-").to_string();

    // Growth off a negative or zero base is not meaningful (-650% "growth"
    // for a name going from -0.01 to -0.06) — drop it from both the line
    // and the score rather than let one garbage ratio dominate.
    let eps_current = f(c, &["eps_estimate_current"]);
    let eps_negative_base = eps_current.map(|v| v <= 0.0).unwrap_or(false);
    let fwd_growth = if eps_negative_base { None } else { f(c, &["forward_qtr_eps_growth_pct"]) };
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
    let revenue_bars: Vec<RevenueBar> = c
        .get("revenue_history")
        .and_then(|v| v.as_array())
        .map(|history| {
            history
                .iter()
                .filter_map(|q| {
                    let label = q.get("quarter_end")?.as_str()?.to_string();
                    let revenue = q.get("revenue")?.as_f64()?;
                    let qoq_growth_pct = q.get("qoq_growth_pct").and_then(|v| v.as_f64());
                    let yoy_growth_pct = q.get("yoy_growth_pct").and_then(|v| v.as_f64());
                    let net_margin_pct = q.get("net_margin_pct").and_then(|v| v.as_f64());
                    Some(RevenueBar { label, revenue, qoq_growth_pct, yoy_growth_pct, net_margin_pct })
                })
                .collect()
        })
        .unwrap_or_default();
    let latest_rev_yoy = revenue_bars.last().and_then(|r| r.yoy_growth_pct);
    let eps_revision_trend: Vec<f64> = [
        f(c, &["eps_estimate_90d_ago"]),
        f(c, &["eps_estimate_30d_ago"]),
        f(c, &["eps_estimate_7d_ago"]),
        f(c, &["eps_estimate_current"]),
    ]
    .into_iter()
    .flatten()
    .collect();
    // Bounds calibrated against real filed/estimate data across a spread
    // of symbols (MU, NVDA, GOOGL, WEN, GME) after fixing a unit bug where
    // these came out of Yahoo/EDGAR ~10x too small (see services/canslim.py
    // _raw_pct). IBD's floor is 25% for both; 100%+ EPS growth is common
    // for names with real operating leverage, 50%+ revenue growth is rarer
    // so gets a tighter ceiling.
    let c_score = match (fwd_growth, latest_rev_yoy) {
        (Some(eps), Some(rev)) => (clamp_pct(eps, 0.0, 100.0) + clamp_pct(rev, 0.0, 50.0)) / 2,
        (Some(eps), None) => clamp_pct(eps, 0.0, 100.0),
        (None, Some(rev)) => clamp_pct(rev, 0.0, 50.0),
        (None, None) => 0,
    };

    vec![
        Letter {
            key: 'C',
            title: "Current Earnings",
            score: c_score,
            lines: vec![
                format!(
                    "eps est: {}  (7d: {}  30d: {}  90d: {})",
                    fmt_eps(eps_current),
                    fmt_eps(f(c, &["eps_estimate_7d_ago"])),
                    fmt_eps(f(c, &["eps_estimate_30d_ago"])),
                    fmt_eps(f(c, &["eps_estimate_90d_ago"])),
                ),
                format!(
                    "fwd qoq: {}{}",
                    if eps_negative_base { "n/m (negative EPS)".to_string() } else { fmt_opt(fwd_growth, "%") },
                    // Thin analyst coverage (small/recent names especially)
                    // means a dramatic-looking % is one guess, not a
                    // consensus — shown inline instead of a bare number
                    // that reads as more authoritative than it is.
                    match c.get("num_analysts").and_then(|v| v.as_i64()) {
                        Some(n) if n <= 3 => format!("  ({n} analysts — thin coverage)"),
                        Some(n) => format!("  ({n} analysts)"),
                        None => String::new(),
                    },
                ),
                format!("filed revenue YoY (SEC): {}", fmt_opt(latest_rev_yoy, "%")),
            ],
            detail: if earnings_bars.is_empty() && revenue_bars.is_empty() {
                None
            } else {
                Some(Detail::Earnings(EarningsDetail {
                    eps_bars: earnings_bars,
                    revenue_bars,
                    eps_revision_trend,
                    as_of: as_of.clone(),
                }))
            },
        },
        Letter {
            key: 'A',
            title: "Annual Growth",
            // IBD floor is 25% annual growth; 50%+ is a strong CANSLIM
            // candidate, so that's the ceiling for a full-green gauge.
            score: earnings_yoy.map(|v| clamp_pct(v, 0.0, 50.0)).unwrap_or(0),
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

/// EPS-scale numbers are cents, not percents — one decimal turns -0.04 into
/// a misleading "-0.0".
fn fmt_eps(v: Option<f64>) -> String {
    match v {
        Some(v) => format!("{:.2}", v),
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
                Span::styled(format!(" {symbol} "), bg_style.fg(Color::Gray).bold()),
                Span::styled("CANSLIM Scorecard  ", bg_style.fg(Color::Gray)),
                Span::styled(fmt_opt(price, " "), bg_style.fg(Color::Gray)),
                Span::styled(format!("  as of {as_of}"), bg_style.fg(Color::Gray)),
                Span::styled(
                    if just_refreshed { "  refreshed" } else { "  r refresh" },
                    bg_style.fg(if just_refreshed { Color::Rgb(0x4d, 0x93, 0x75) } else { Color::Gray }),
                ),
            ]);

            let chunks = Layout::vertical([
                Constraint::Length(1),
                Constraint::Length(1),
                Constraint::Min(0),
                Constraint::Length(1),
            ])
            .split(area);

            frame.render_widget(Paragraph::new(header).style(bg_style), chunks[0]);

            // Top band: compact list of all seven letters (one row each,
            // mini bar + score + title) with the selected letter's raw
            // numbers beside it. Below a full-width rule, the selected
            // letter's charts get the whole remaining width. Replaces the
            // old stack of seven bordered gauge panels.
            let list_h = letters.len() as u16;
            let bands = Layout::vertical([Constraint::Length(list_h), Constraint::Length(1), Constraint::Min(0)])
                .split(chunks[2]);
            let top = Layout::horizontal([Constraint::Length(40), Constraint::Min(0)]).split(bands[0]);
            render_letter_list(frame, top[0], &letters, selected, bg_style);
            render_letter_lines(frame, top[1], &letters[selected], bg_style);
            frame.render_widget(
                Block::default().borders(Borders::TOP).style(bg_style.fg(Color::Gray)),
                bands[1],
            );
            render_letter_detail(frame, bands[2], &letters[selected], bg_style);

            let footer_text = " ↑↓ select   s search   q quit ";
            let footer = Line::from(vec![Span::styled(footer_text, bg_style.fg(Color::Gray))]);
            frame.render_widget(Paragraph::new(footer).style(bg_style), chunks[3]);
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
                    KeyCode::Char('s') => return Ok(true),
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(false),
                    KeyCode::Char('c')
                        if key.modifiers.contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        return Ok(false);
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        selected = selected.saturating_sub(1);
                    }
                    KeyCode::Down | KeyCode::Char('j') => {
                        selected = (selected + 1).min(6);
                    }
                    KeyCode::Char('r') => {
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

/// One row per letter: key, ten-cell mini bar, score, title. The selected
/// row is bold with a marker.
fn render_letter_list(frame: &mut ratatui::Frame, area: Rect, letters: &[Letter], selected: usize, bg_style: Style) {
    let mut lines = Vec::with_capacity(letters.len());
    for (idx, letter) in letters.iter().enumerate() {
        let focused = idx == selected;
        let color = gauge_color(letter.score);
        let filled = ((letter.score as usize) * 10 / 100).min(10);
        let bar = format!("{}{}", "▰".repeat(filled), "▱".repeat(10 - filled));
        let text_style = if focused { bg_style.fg(Color::Gray).bold() } else { bg_style.fg(Color::Gray) };
        lines.push(Line::from(vec![
            Span::styled(if focused { "▶ " } else { "  " }, text_style),
            Span::styled(format!("{} ", letter.key), text_style),
            Span::styled(bar, bg_style.fg(color)),
            Span::styled(format!(" {:>3}%  ", letter.score), bg_style.fg(color)),
            Span::styled(letter.title, text_style),
        ]));
    }
    frame.render_widget(Paragraph::new(lines).style(bg_style), area);
}

/// The selected letter's raw numbers, wrapped, beside the list.
fn render_letter_lines(frame: &mut ratatui::Frame, area: Rect, letter: &Letter, bg_style: Style) {
    let mut lines = vec![Line::from(Span::styled(
        format!("{} — {}", letter.key, letter.title),
        bg_style.fg(Color::Gray).bold(),
    ))];
    for l in &letter.lines {
        lines.push(Line::from(Span::styled(l.as_str(), bg_style.fg(Color::Gray))));
    }
    let text_area = Rect { x: area.x + 2, width: area.width.saturating_sub(3), ..area };
    frame.render_widget(Paragraph::new(lines).style(bg_style).wrap(Wrap { trim: false }), text_area);
}

/// The selected letter's drill-down charts, or a placeholder for letters
/// that have none yet.
fn render_letter_detail(frame: &mut ratatui::Frame, area: Rect, letter: &Letter, bg_style: Style) {
    let inner = Rect { y: area.y + 1, height: area.height.saturating_sub(1), ..area };
    match &letter.detail {
        Some(Detail::Earnings(d)) => render_earnings_detail(frame, inner, d, bg_style),
        None => {
            let msg = Paragraph::new(format!("no drill-down for {} yet", letter.key))
                .style(bg_style.fg(Color::DarkGray))
                .centered();
            frame.render_widget(msg, centered(inner, 1));
        }
    }
}

fn render_earnings_detail(frame: &mut ratatui::Frame, area: Rect, d: &EarningsDetail, bg_style: Style) {
    let up = Color::Rgb(0x4d, 0x93, 0x75);
    let down = Color::Rgb(0xc2, 0x5c, 0x5c);

    let gold = Color::Rgb(0xd9, 0xa5, 0x2c);

    // Two columns. Left: EPS estimate revision on top, EPS actual-vs-
    // estimate by quarter under it, each with its own legend. Right: the
    // filed revenue table gets the full height (it has the most rows).
    let cols = Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)]).split(area);
    let trend_h = 2 + 4; // border + four checkpoints
    let eps_h = 2 + (d.eps_bars.len() as u16) * 3;
    let left = Layout::vertical([
        Constraint::Length(trend_h), // estimate-revision bars
        Constraint::Length(1),       // revision legend
        Constraint::Length(1),       // spacer
        Constraint::Length(eps_h),   // EPS actual vs estimate bars
        Constraint::Length(1),       // EPS legend + date
        Constraint::Min(0),
    ])
    .split(Rect { width: cols[0].width.saturating_sub(1), ..cols[0] });
    let trend_area = left[0];
    let trend_legend_area = left[1];
    let eps_area = left[3];
    let eps_legend_area = left[4];
    let right = Layout::vertical([Constraint::Min(0), Constraint::Length(1)]).split(cols[1]);
    let revenue_area = right[0];
    let revenue_legend_area = right[1];


    // EPS actual vs estimate — horizontal ▰▱ bars, two per quarter (est
    // in gray, actual in green/red), same glyph bars as the letter list
    // so the whole screen reads as one style. Lengths are scaled to the
    // widest value; negative values are shifted up by the set's floor so
    // a loss-making name still gets visible, correctly-ordered bars while
    // the number label carries the true signed value.
    let eps_block = Block::default()
        .borders(Borders::ALL)
        .border_style(bg_style.fg(Color::Gray))
        .title(" EPS: estimate (gray) vs actual (green/red) — by quarter ")
        .title_style(bg_style.fg(Color::Gray).bold());
    let eps_inner = eps_block.inner(eps_area);
    frame.render_widget(eps_block, eps_area);

    let eps_floor = d
        .eps_bars
        .iter()
        .flat_map(|p| [p.actual, p.estimate])
        .fold(0.0_f64, f64::min);
    let eps_ceil = d
        .eps_bars
        .iter()
        .flat_map(|p| [p.actual, p.estimate])
        .fold(f64::MIN, f64::max)
        .max(eps_floor + f64::EPSILON);
    // "2025-09-30  est  " prefix (17) + "  -12.34" suffix (8)
    let bar_w = eps_inner.width.saturating_sub(17 + 8).max(1) as usize;
    let glyph_bar = |v: f64| {
        let filled = (((v - eps_floor) / (eps_ceil - eps_floor)) * bar_w as f64).round() as usize;
        let filled = filled.min(bar_w);
        format!("{}{}", "▰".repeat(filled), "▱".repeat(bar_w - filled))
    };
    let mut eps_lines = Vec::with_capacity(d.eps_bars.len() * 3);
    for p in &d.eps_bars {
        let beat = p.actual >= p.estimate;
        let act_color = if beat { up } else { down };
        eps_lines.push(Line::from(vec![
            Span::styled(format!("{:<12}est  ", p.label), bg_style.fg(Color::Gray)),
            Span::styled(glyph_bar(p.estimate), bg_style.fg(Color::Gray)),
            Span::styled(format!("  {:>6.2}", p.estimate), bg_style.fg(Color::Gray)),
        ]));
        eps_lines.push(Line::from(vec![
            Span::styled(format!("{:<12}act  ", ""), bg_style.fg(Color::Gray)),
            Span::styled(glyph_bar(p.actual), bg_style.fg(act_color)),
            Span::styled(format!("  {:>6.2}", p.actual), bg_style.fg(act_color).bold()),
        ]));
        eps_lines.push(Line::from(""));
    }
    frame.render_widget(Paragraph::new(eps_lines).style(bg_style), eps_inner);
    let eps_latest_date = d.eps_bars.last().map(|p| p.label.as_str()).unwrap_or("-");
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("green", bg_style.fg(up)),
            Span::styled("=beat  ", bg_style.fg(Color::Gray)),
            Span::styled("red", bg_style.fg(down)),
            Span::styled("=missed", bg_style.fg(Color::Gray)),
            Span::styled(format!("    latest quarter: {eps_latest_date}"), bg_style.fg(Color::Gray)),
        ])),
        eps_legend_area,
    );

    // Filed quarterly revenue (SEC) — a table, one row per quarter: date,
    // revenue as a glyph bar scaled to the biggest quarter, then QoQ / YoY
    // / net margin as aligned columns. Row colored by YoY sign — the
    // "sales confirms earnings" half of IBD's C rule.
    let rev_block = Block::default()
        .borders(Borders::ALL)
        .border_style(bg_style.fg(Color::Gray))
        .title(" Revenue (SEC filed) — by quarter ")
        .title_style(bg_style.fg(Color::Gray).bold());
    let rev_inner = rev_block.inner(revenue_area);
    frame.render_widget(rev_block, revenue_area);

    let fmt_pct = |v: Option<f64>| v.map(|v| format!("{v:+.1}%")).unwrap_or_else(|| "-".to_string());
    let rev_max = d.revenue_bars.iter().map(|r| r.revenue).fold(0.0_f64, f64::max).max(f64::EPSILON);
    // "2025-09-30  " (12) + bar + "  1.87B" (7) + three 9-wide columns
    let rev_bar_w = rev_inner.width.saturating_sub(12 + 7 + 27).max(1) as usize;
    let rev_bar = |v: f64| {
        let filled = ((v / rev_max) * rev_bar_w as f64).round().max(0.0) as usize;
        let filled = filled.min(rev_bar_w);
        format!("{}{}", "▰".repeat(filled), "▱".repeat(rev_bar_w - filled))
    };
    let mut rev_lines = vec![Line::from(Span::styled(
        format!("{:<12}{:<w$}{:>7}{:>9}{:>9}{:>9}", "quarter", "revenue", "", "QoQ", "YoY", "margin", w = rev_bar_w),
        bg_style.fg(Color::DarkGray),
    ))];
    for r in &d.revenue_bars {
        let growing = r.yoy_growth_pct.map(|g| g >= 0.0).unwrap_or(true);
        let color = if growing { up } else { down };
        rev_lines.push(Line::from(vec![
            Span::styled(format!("{:<12}", r.label), bg_style.fg(Color::Gray)),
            Span::styled(rev_bar(r.revenue), bg_style.fg(color)),
            Span::styled(format!("{:>7}", fmt_shares(Some(r.revenue))), bg_style.fg(color).bold()),
            Span::styled(format!("{:>9}", fmt_pct(r.qoq_growth_pct)), bg_style.fg(Color::Gray)),
            Span::styled(format!("{:>9}", fmt_pct(r.yoy_growth_pct)), bg_style.fg(color)),
            Span::styled(format!("{:>9}", fmt_pct(r.net_margin_pct)), bg_style.fg(Color::Gray)),
        ]));
    }
    frame.render_widget(Paragraph::new(rev_lines).style(bg_style), rev_inner);
    let revenue_latest_date = d.revenue_bars.last().map(|r| r.label.as_str()).unwrap_or("-");
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("green", bg_style.fg(up)),
            Span::styled("=YoY growing  ", bg_style.fg(Color::Gray)),
            Span::styled("red", bg_style.fg(down)),
            Span::styled("=YoY shrinking", bg_style.fg(Color::Gray)),
            Span::styled(format!("    latest filed quarter: {revenue_latest_date}"), bg_style.fg(Color::Gray)),
        ])),
        revenue_legend_area,
    );

    // Estimate-revision trend (90d -> current): is Wall St. raising or
    // cutting numbers lately. Same glyph bars as everything else, one row
    // per checkpoint, with the delta vs the prior checkpoint colored by
    // direction.
    let trend_block = Block::default()
        .borders(Borders::ALL)
        .border_style(bg_style.fg(Color::Gray))
        .title(" EPS estimate revision — next quarter consensus ")
        .title_style(bg_style.fg(Color::Gray).bold());
    let trend_inner = trend_block.inner(trend_area);
    frame.render_widget(trend_block, trend_area);

    let trend_labels = ["90d ago", "30d ago", "7d ago", "now"];
    let t_floor = d.eps_revision_trend.iter().copied().fold(0.0_f64, f64::min);
    let t_ceil = d
        .eps_revision_trend
        .iter()
        .copied()
        .fold(f64::MIN, f64::max)
        .max(t_floor + f64::EPSILON);
    // "90d ago  " (9) + bar + "  -0.01" (7) + "  +0.10 ▲" (10)
    let t_bar_w = trend_inner.width.saturating_sub(9 + 7 + 10).max(1) as usize;
    let t_bar = |v: f64| {
        let filled = (((v - t_floor) / (t_ceil - t_floor)) * t_bar_w as f64).round() as usize;
        let filled = filled.min(t_bar_w);
        format!("{}{}", "▰".repeat(filled), "▱".repeat(t_bar_w - filled))
    };
    let mut trend_lines = Vec::with_capacity(4);
    let mut prev: Option<f64> = None;
    for (i, label) in trend_labels.iter().enumerate() {
        let v = d.eps_revision_trend.get(i).copied();
        let (delta_text, delta_color) = match (prev, v) {
            (Some(a), Some(b)) if b > a + 1e-9 => (format!("  {:+.2} ▲", b - a), up),
            (Some(a), Some(b)) if b < a - 1e-9 => (format!("  {:+.2} ▼", b - a), down),
            (Some(a), Some(b)) => (format!("  {:+.2}  ", b - a), Color::Gray),
            _ => (String::new(), Color::Gray),
        };
        trend_lines.push(Line::from(vec![
            Span::styled(format!("{:<9}", label), bg_style.fg(Color::Gray)),
            Span::styled(v.map(&t_bar).unwrap_or_else(|| "▱".repeat(t_bar_w)), bg_style.fg(gold)),
            Span::styled(
                format!("  {:>5}", v.map(|v| format!("{v:.2}")).unwrap_or_else(|| "-".to_string())),
                bg_style.fg(gold).bold(),
            ),
            Span::styled(delta_text, bg_style.fg(delta_color)),
        ]));
        prev = v;
    }
    frame.render_widget(Paragraph::new(trend_lines).style(bg_style), trend_inner);
    frame.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("gold", bg_style.fg(gold)),
            Span::styled(" = consensus EPS estimate   ", bg_style.fg(Color::Gray)),
            Span::styled("▲", bg_style.fg(up)),
            Span::styled("/", bg_style.fg(Color::Gray)),
            Span::styled("▼", bg_style.fg(down)),
            Span::styled(format!(" = raised/cut vs prior    as of: {}", d.as_of), bg_style.fg(Color::Gray)),
        ])),
        trend_legend_area,
    );
}


fn centered(area: Rect, height: u16) -> Rect {
    let y = area.y + area.height.saturating_sub(height) / 2;
    Rect { x: area.x, y, width: area.width, height: height.min(area.height) }
}
