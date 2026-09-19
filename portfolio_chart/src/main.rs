// Renders the daily portfolio % change as a line chart in the terminal.
// Reads `portfolio_history` straight out of the same DuckDB file
// db.py/etrade_client.py write to — no IPC, no JSON handoff, this binary
// just queries the on-disk db directly. Launched by nvim inside a floating
// `:terminal`, so it's a real ratatui TUI nested inside the editor.

mod canslim;

use std::env;
use std::io;
use std::path::PathBuf;
use std::time::{Duration, Instant};

use chrono::NaiveDate;
use crossterm::event::{self, Event, KeyCode};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen};
use crossterm::{execute, ExecutableCommand};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style, Stylize};
use ratatui::symbols;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Axis, Block, Borders, Chart, Dataset, GraphType, Paragraph};
use ratatui::Terminal;

struct Point {
    date: String,
    total_value: f64,
}

#[derive(Clone, Copy, PartialEq)]
enum Range {
    OneM,
    ThreeM,
    SixM,
    OneY,
    All,
}

impl Range {
    /// Calendar days back from the latest data point, or None for "All".
    fn days(self) -> Option<i64> {
        match self {
            Range::OneM => Some(30),
            Range::ThreeM => Some(90),
            Range::SixM => Some(182),
            Range::OneY => Some(365),
            Range::All => None,
        }
    }

    fn label(self) -> &'static str {
        match self {
            Range::OneM => "1M",
            Range::ThreeM => "3M",
            Range::SixM => "6M",
            Range::OneY => "1Y",
            Range::All => "ALL",
        }
    }
}

/// Slices `history` down to the trailing window `range` covers, anchored
/// to the most recent data point (not "today" — the history can lag by a
/// weekend/holiday). Recomputes day_change_pct relative to the first bar
/// kept, so a zoomed-in range reads as "% change since the start of this
/// window" instead of carrying the full-history first-day baseline.
fn windowed<'a>(history: &'a [Point], range: Range) -> Vec<(&'a Point, f64)> {
    if history.is_empty() {
        return Vec::new();
    }
    let slice: &[Point] = match range.days() {
        None => history,
        Some(days) => {
            let latest = NaiveDate::parse_from_str(&history[history.len() - 1].date, "%Y-%m-%d").ok();
            match latest {
                None => history,
                Some(latest) => {
                    let cutoff = latest - chrono::Duration::days(days);
                    let start = history
                        .iter()
                        .position(|p| {
                            NaiveDate::parse_from_str(&p.date, "%Y-%m-%d")
                                .map(|d| d >= cutoff)
                                .unwrap_or(false)
                        })
                        .unwrap_or(0);
                    &history[start..]
                }
            }
        }
    };

    let base_value = slice[0].total_value;
    slice
        .iter()
        .map(|p| {
            let pct_since_start = if base_value != 0.0 {
                (p.total_value - base_value) / base_value * 100.0
            } else {
                0.0
            };
            (p, pct_since_start)
        })
        .collect()
}

fn db_path() -> PathBuf {
    if let Ok(p) = env::var("SECURITY_SPREAD_DB") {
        return PathBuf::from(p);
    }
    let home = env::var("HOME").expect("HOME not set");
    PathBuf::from(home).join(".local/share/nvim/security_spread.duckdb")
}

/// #rrggbb -> ratatui Color. Falls back to the terminal's default (no
/// explicit background) on anything unparseable, so a bad arg degrades
/// gracefully instead of crashing.
fn parse_hex_color(s: &str) -> Option<Color> {
    let s = s.trim_start_matches('#');
    if s.len() != 6 {
        return None;
    }
    let r = u8::from_str_radix(&s[0..2], 16).ok()?;
    let g = u8::from_str_radix(&s[2..4], 16).ok()?;
    let b = u8::from_str_radix(&s[4..6], 16).ok()?;
    Some(Color::Rgb(r, g, b))
}

fn load_history() -> Result<Vec<Point>, duckdb::Error> {
    let conn = duckdb::Connection::open(db_path())?;
    let mut stmt = conn.prepare(
        "SELECT CAST(date AS VARCHAR), total_value FROM portfolio_history ORDER BY date",
    )?;
    let rows = stmt.query_map([], |row| {
        Ok(Point {
            date: row.get(0)?,
            total_value: row.get(1)?,
        })
    })?;
    rows.collect()
}

fn main() -> io::Result<()> {
    let args: Vec<String> = env::args().collect();
    let bg = args.get(1).and_then(|s| parse_hex_color(s));
    let fg_up = args.get(2).and_then(|s| parse_hex_color(s)).unwrap_or(Color::Rgb(0x4d, 0x93, 0x75));
    let fg_down = args.get(3).and_then(|s| parse_hex_color(s)).unwrap_or(Color::Rgb(0xc2, 0x5c, 0x5c));
    let bg_style = bg.map(|c| Style::default().bg(c)).unwrap_or_default();

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // `portfolio_chart <bg> <fg_up> <fg_down> canslim <SYMBOL>` switches to
    // the per-security scorecard screen instead of the portfolio history
    // chart — same binary, same DB, no separate crate needed.
    let is_canslim = args.get(4).map(String::as_str) == Some("canslim");
    let (result, back_to_picker) = if is_canslim {
        let symbol = args.get(5).cloned().unwrap_or_else(|| "MU".to_string());
        match canslim::run(&mut terminal, &db_path(), &symbol, bg_style) {
            Ok(back) => (Ok(()), back),
            Err(e) => (Err(e), false),
        }
    } else {
        (run(&mut terminal, bg, fg_up, fg_down), false)
    };

    disable_raw_mode()?;
    io::stdout().execute(LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    result?;

    // Exit code 90 is a sentinel the tmux-popup shell wrapper (see
    // ui/portfolio_chart.lua) watches for, to reopen the fzf-lua symbol
    // picker back in nvim after this process exits — this binary runs in
    // its own tmux pane, so it can't call back into nvim directly.
    if back_to_picker {
        std::process::exit(90);
    }
    Ok(())
}

fn run(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    bg: Option<Color>,
    fg_up: Color,
    fg_down: Color,
) -> io::Result<()> {
    let bg_style = bg.map(|c| Style::default().bg(c)).unwrap_or_default();
    let mut range = Range::ThreeM;
    let mut history = load_history().unwrap_or_default();
    let mut refreshed_at: Option<Instant> = None;

    loop {
        terminal.draw(|frame| {
            let area = frame.area();
            frame.render_widget(Paragraph::new("").style(bg_style), area);

            if history.is_empty() {
                let msg = Paragraph::new(
                    "no history yet — open the $ dashboard at least once today to start tracking",
                )
                .style(bg_style.fg(Color::Gray));
                frame.render_widget(msg, centered(area, 3));
                return;
            }

            let windowed_points = windowed(&history, range);
            let latest_point = &windowed_points[windowed_points.len() - 1];
            let latest = latest_point.0;
            let window_pct = latest_point.1;

            let chunks = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).split(area);

            let latest_color = if window_pct >= 0.0 { fg_up } else { fg_down };
            let range_labels = [Range::OneM, Range::ThreeM, Range::SixM, Range::OneY, Range::All];
            let mut header_spans = vec![
                Span::styled(" Portfolio  ", bg_style.fg(Color::White)),
                Span::styled(format!("${:.2}", latest.total_value), bg_style.fg(Color::White)),
                Span::raw("  "),
                Span::styled(
                    format!("{}{:.2}%", if window_pct >= 0.0 { "+" } else { "" }, window_pct),
                    bg_style.fg(latest_color),
                ),
                Span::raw("   "),
            ];
            for (i, r) in range_labels.iter().enumerate() {
                let style = if *r == range {
                    bg_style.fg(Color::White).bold()
                } else {
                    bg_style.fg(Color::DarkGray)
                };
                header_spans.push(Span::styled(format!("[{}]{}", i + 1, r.label()), style));
                header_spans.push(Span::raw(" "));
            }
            let just_refreshed = refreshed_at.map(|t| t.elapsed() < Duration::from_millis(1200)).unwrap_or(false);
            header_spans.push(Span::styled(
                if just_refreshed { "  refreshed" } else { "  r refresh" },
                bg_style.fg(if just_refreshed { fg_up } else { Color::DarkGray }),
            ));
            header_spans.push(Span::styled("   q to close", bg_style.fg(Color::DarkGray)));
            frame.render_widget(Paragraph::new(Line::from(header_spans)).style(bg_style), chunks[0]);

            let points: Vec<(f64, f64)> = windowed_points
                .iter()
                .enumerate()
                .map(|(i, (_, pct))| (i as f64, *pct))
                .collect();

            let up: Vec<(f64, f64)> = points.iter().copied().filter(|(_, y)| *y >= 0.0).collect();
            let down: Vec<(f64, f64)> = points.iter().copied().filter(|(_, y)| *y < 0.0).collect();

            let min_y = points.iter().map(|(_, y)| *y).fold(0.0_f64, f64::min);
            let max_y = points.iter().map(|(_, y)| *y).fold(0.0_f64, f64::max);
            let pad = ((max_y - min_y).abs() * 0.15).max(0.5);
            let y_bounds = [min_y - pad, max_y + pad];
            let x_bounds = [0.0, (points.len().saturating_sub(1)) as f64];

            let mut datasets = vec![Dataset::default()
                .name("+")
                .marker(symbols::Marker::Braille)
                .graph_type(GraphType::Line)
                .style(Style::default().fg(fg_up))
                .data(&up)];
            if !down.is_empty() {
                datasets.push(
                    Dataset::default()
                        .name("-")
                        .marker(symbols::Marker::Braille)
                        .graph_type(GraphType::Line)
                        .style(Style::default().fg(fg_down))
                        .data(&down),
                );
            }

            let first = windowed_points[0].0;
            let x_labels = if windowed_points.len() <= 1 {
                vec![Line::from(first.date.clone())]
            } else {
                vec![Line::from(first.date.clone()), Line::from(latest.date.clone())]
            };

            let chart = Chart::new(datasets)
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .title(format!(" % change since {} ", first.date))
                        .style(bg_style.fg(Color::DarkGray)),
                )
                .x_axis(
                    Axis::default()
                        .style(bg_style.fg(Color::DarkGray))
                        .bounds(x_bounds)
                        .labels(x_labels),
                )
                .y_axis(
                    Axis::default()
                        .style(bg_style.fg(Color::DarkGray))
                        .bounds(y_bounds)
                        .labels(vec![
                            Line::from(format!("{:.1}%", y_bounds[0])),
                            Line::from("0%"),
                            Line::from(format!("{:.1}%", y_bounds[1])),
                        ]),
                )
                .style(bg_style);
            frame.render_widget(chart, chunks[1]);
        })?;

        if event::poll(Duration::from_millis(200))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(()),
                    KeyCode::Char('c')
                        if key.modifiers.contains(crossterm::event::KeyModifiers::CONTROL) =>
                    {
                        return Ok(());
                    }
                    KeyCode::Char('1') => range = Range::OneM,
                    KeyCode::Char('2') => range = Range::ThreeM,
                    KeyCode::Char('3') => range = Range::SixM,
                    KeyCode::Char('4') => range = Range::OneY,
                    KeyCode::Char('5') => range = Range::All,
                    KeyCode::Char('r') => {
                        // Re-reads DuckDB — cheap local read, so this
                        // picks up whatever the latest `$` refresh or
                        // backfill run wrote without relaunching the TUI.
                        history = load_history().unwrap_or_default();
                        refreshed_at = Some(Instant::now());
                    }
                    _ => {}
                }
            }
        }
    }
}

/// Roughly centers a small fixed-height message box inside `area`.
fn centered(area: Rect, height: u16) -> Rect {
    let y = area.y + area.height.saturating_sub(height) / 2;
    Rect { x: area.x, y, width: area.width, height: height.min(area.height) }
}
