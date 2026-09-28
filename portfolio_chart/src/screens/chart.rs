// Portfolio history: total account value over time as a % change line
// chart. Reads `portfolio_history` (one E*TRADE account snapshot per day,
// upserted by sources/etrade.py on every live `$` refresh) straight out of
// DuckDB, read-only.
//
// Every number on screen is a point's value or its % change since the
// window start; the cursor (h/l) selects a point and the source bar shows
// that point's Source: the snapshot it came from, and for the % change the
// formula with both snapshot values as inputs (`i` to inspect, `y` copy).

use std::io;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::symbols::Marker;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Tabs};

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::model::{Point, Source};
use crate::ui::charts::LineChart;
use crate::ui::command_palette::{self, Command, Entry, Palette};
use crate::ui::help::{self, Key, key};
use crate::ui::layout::{self, FrameTitles, PaneOpts};
use crate::ui::source_bar::{self, SourceInspector};
use crate::ui::theme::Theme;

const KEYS: &[Key] = &[
    key("^p", "command palette"),
    key("1-5", "range 1M/3M/6M/1Y/ALL"),
    key("h/l", "move cursor"),
    key("H/L", "first / last point"),
    key("i", "inspect formula + inputs"),
    key("y", "copy formula"),
    key("m", "marker braille/octant"),
    key("r", "reload from DuckDB"),
    key("?", "help"),
    key("q", "close"),
];

const FLASH_FOR: Duration = Duration::from_millis(1500);

/// One row of `portfolio_history`.
#[derive(Debug, Clone, PartialEq)]
pub struct Snapshot {
    pub date: String,
    pub total_value: f64,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Range {
    OneM,
    ThreeM,
    SixM,
    OneY,
    All,
}

impl Range {
    const ALL: [Range; 5] = [
        Range::OneM,
        Range::ThreeM,
        Range::SixM,
        Range::OneY,
        Range::All,
    ];

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

    fn index(self) -> usize {
        Self::ALL.iter().position(|r| *r == self).unwrap_or(0)
    }

    fn parse(s: &str) -> Option<Range> {
        Self::ALL
            .into_iter()
            .find(|r| r.label().eq_ignore_ascii_case(s))
    }
}

/// Slices `history` down to the trailing window `range` covers, anchored
/// to the most recent data point (not "today" — the history can lag by a
/// weekend/holiday).
fn window(history: &[Snapshot], range: Range) -> &[Snapshot] {
    let (Some(days), Some(last)) = (range.days(), history.last()) else {
        return history;
    };
    let Ok(latest) = NaiveDate::parse_from_str(&last.date, "%Y-%m-%d") else {
        return history;
    };
    let cutoff = latest - chrono::Duration::days(days);
    let start = history
        .iter()
        .position(|p| NaiveDate::parse_from_str(&p.date, "%Y-%m-%d").is_ok_and(|d| d >= cutoff))
        .unwrap_or(0);
    &history[start..]
}

/// Window as model Points: y = % change since the first snapshot kept, so
/// a zoomed-in range reads as "% change since the start of this window".
/// Each point carries the formula and both snapshot values as its Source.
fn to_points(win: &[Snapshot]) -> Vec<Point> {
    let Some(base) = win.first() else {
        return Vec::new();
    };
    win.iter()
        .map(|p| {
            let pct =
                (base.total_value != 0.0).then(|| (p.total_value / base.total_value - 1.0) * 100.0);
            let formula = match pct {
                Some(pct) => format!(
                    "({} / {} - 1) × 100 = {:+.2}%",
                    money(p.total_value),
                    money(base.total_value),
                    pct
                ),
                None => format!(
                    "start value {} is zero: % change undefined",
                    money(base.total_value)
                ),
            };
            let src = Source::derived(
                format!("E*TRADE account snapshot {}", p.date),
                formula,
                vec![snapshot_source(p), snapshot_source(base)],
            );
            Point {
                x: p.date.clone(),
                y: pct,
                src: Some(src),
            }
        })
        .collect()
}

fn snapshot_source(s: &Snapshot) -> Source {
    Source {
        label: format!(
            "E*TRADE account snapshot {}: total_value {} (DuckDB portfolio_history)",
            s.date,
            money(s.total_value)
        ),
        ..Default::default()
    }
}

/// $12,345.67
fn money(v: f64) -> String {
    let s = format!("{:.2}", v.abs());
    let (int, frac) = s.split_once('.').unwrap_or((&s, "00"));
    let mut out = String::new();
    for (i, c) in int.chars().enumerate() {
        if i > 0 && (int.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    format!("{}${out}.{frac}", if v < 0.0 { "-" } else { "" })
}

fn load_history(path: &Path) -> Result<Vec<Snapshot>, String> {
    let cfg = duckdb::Config::default()
        .access_mode(duckdb::AccessMode::ReadOnly)
        .map_err(|e| e.to_string())?;
    let conn = duckdb::Connection::open_with_flags(path, cfg)
        .map_err(|e| format!("{}: {e}", path.display()))?;
    let mut stmt = conn
        .prepare("SELECT CAST(date AS VARCHAR), total_value FROM portfolio_history ORDER BY date")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, Option<f64>>(1)?))
        })
        .map_err(|e| e.to_string())?;
    let mut out = Vec::new();
    for r in rows {
        // A NULL total_value is a missing snapshot: skip it, never plot as 0.
        if let (date, Some(total_value)) = r.map_err(|e| e.to_string())? {
            out.push(Snapshot { date, total_value });
        }
    }
    Ok(out)
}

pub struct ChartScreen {
    db_path: PathBuf,
    theme: Theme,
    history: Vec<Snapshot>,
    load_err: Option<String>,
    range: Range,
    /// Index into the current window; None = follow the latest point.
    cursor: Option<usize>,
    marker: Marker,
    help: bool,
    palette: Palette,
    inspector: SourceInspector,
    flash: Option<(String, Instant)>,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<ChartScreen> {
    let mut s = ChartScreen::new(ctx.theme, ctx.db_path.clone(), Vec::new());
    s.range = arg
        .as_deref()
        .and_then(Range::parse)
        .unwrap_or(Range::ThreeM);
    s.reload();
    Ok(s)
}

impl ChartScreen {
    pub fn new(theme: Theme, db_path: PathBuf, history: Vec<Snapshot>) -> Self {
        Self {
            db_path,
            theme,
            history,
            load_err: None,
            range: Range::ThreeM,
            cursor: None,
            marker: Marker::Braille,
            help: false,
            palette: Palette::default(),
            inspector: SourceInspector::default(),
            flash: None,
        }
    }

    fn reload(&mut self) {
        match load_history(&self.db_path) {
            Ok(h) => {
                self.history = h;
                self.load_err = None;
            }
            Err(e) => self.load_err = Some(e),
        }
    }

    fn points(&self) -> Vec<Point> {
        to_points(window(&self.history, self.range))
    }

    fn selected(&self, len: usize) -> Option<usize> {
        if len == 0 {
            return None;
        }
        Some(self.cursor.unwrap_or(len - 1).min(len - 1))
    }

    fn move_cursor(&mut self, delta: isize) {
        let len = window(&self.history, self.range).len();
        let Some(cur) = self.selected(len) else {
            return;
        };
        let next = cur.saturating_add_signed(delta).min(len - 1);
        self.cursor = if next == len - 1 { None } else { Some(next) };
    }

    fn selected_source(&self) -> Option<Source> {
        let pts = self.points();
        let i = self.selected(pts.len())?;
        pts.into_iter().nth(i)?.src
    }

    fn render_header(&self, frame: &mut Frame, area: Rect, points: &[Point], sel: usize) {
        let t = &self.theme;
        let p = &points[sel];
        let snap = &window(&self.history, self.range)[sel];
        let pct = p.y.unwrap_or(0.0);
        let left = Line::from(vec![
            Span::styled(" Portfolio  ", t.title()),
            Span::styled(money(snap.total_value), t.base()),
            Span::styled("  ", t.base()),
            Span::styled(
                p.y.map_or("n/a".into(), |v| format!("{v:+.2}%")),
                t.signed(pct),
            ),
            Span::styled(format!("  {}", p.x), t.dim()),
        ]);
        let [l, r] = Layout::horizontal([Constraint::Min(0), Constraint::Length(26)]).areas(area);
        frame.render_widget(Paragraph::new(left).style(t.base()), l);
        let tabs = Tabs::new(Range::ALL.iter().map(|r| r.label()))
            .select(self.range.index())
            .style(t.dim())
            .highlight_style(t.title())
            .divider(" ")
            .padding("", "");
        frame.render_widget(tabs, r);
    }

    fn render_chart(&self, frame: &mut Frame, area: Rect, points: &[Point], sel: usize) {
        let chart = LineChart::new(points, &self.theme)
            .selected(Some(sel))
            .signed(true)
            .marker(self.marker)
            .unit("%")
            .cursor_line(true);
        frame.render_widget(chart, area);
    }

    fn render_empty(&self, frame: &mut Frame, area: Rect) {
        let t = &self.theme;
        let msg = match &self.load_err {
            Some(e) => format!("could not read portfolio_history: {e}"),
            None => {
                "no history yet — open the $ dashboard at least once today to start tracking".into()
            }
        };
        let r = area.centered_vertically(Constraint::Length(1));
        frame.render_widget(Paragraph::new(msg).style(t.dim()).centered(), r);
    }
}

impl Screen for ChartScreen {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        if self
            .flash
            .as_ref()
            .is_some_and(|(_, at)| at.elapsed() > FLASH_FOR)
        {
            self.flash = None;
        }
        let points = self.points();
        let titles = FrameTitles {
            detail: Line::from(match points.first() {
                Some(p) => format!(" % change since {} ", p.x),
                None => " portfolio history ".into(),
            }),
            detail_right: Line::from(format!(
                " {} ",
                if self.marker == Marker::Braille {
                    "braille"
                } else {
                    "octant"
                }
            )),
            source: Line::from(" source "),
            ..Default::default()
        };
        let p = layout::render_frame(
            frame,
            area,
            PaneOpts {
                nav_width: 0,
                ..Default::default()
            },
            &titles,
            &t,
        );
        let flash = self.flash.as_ref().map(|(m, _)| m.as_str());
        help::render_footer(frame, p.footer, KEYS, flash, &t);

        let Some(sel) = self.selected(points.len()) else {
            self.render_empty(frame, p.detail);
            return;
        };
        self.render_header(frame, p.header, &points, sel);
        self.render_chart(frame, p.detail, &points, sel);
        source_bar::render_source_bar(frame, p.source, points[sel].src.as_ref(), &t);

        if self.inspector.is_open() {
            self.inspector.render(frame, area, &t);
        }
        if self.help {
            help::render_overlay(frame, area, "portfolio history", KEYS, &t);
        }
        if self.palette.open {
            self.palette.render(frame, area, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.palette.open
            && let Some(command) = self.palette.handle(key) {
                return match command {
                    Some(Command::Screen(screen)) => Action::Nvim(NvimAction::Screen {
                        screen: screen.into(),
                        arg: None,
                    }),
                    Some(Command::Picker(screen)) => Action::Nvim(NvimAction::Picker {
                        screen: screen.into(),
                    }),
                    Some(Command::Range(i)) => {
                        self.range = Range::ALL[(i as usize).min(Range::ALL.len() - 1)];
                        self.cursor = None;
                        Action::None
                    }
                    _ => Action::None,
                };
            }
        if key.code == KeyCode::Char('p') && key.modifiers.contains(KeyModifiers::CONTROL) {
            let mut entries = command_palette::destinations("", "chart");
            entries.extend(Range::ALL.iter().enumerate().map(|(i, r)| {
                Entry::new(
                    format!("Show {} history", r.label()),
                    "chart range",
                    Command::Range(i as u8),
                )
            }));
            self.palette.show(entries);
            return Action::None;
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        if self.inspector.is_open() {
            return self.inspector.on_key(key);
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char(c @ '1'..='5') => {
                self.range = Range::ALL[(c as u8 - b'1') as usize];
                self.cursor = None;
            }
            KeyCode::Char('h') | KeyCode::Left => self.move_cursor(-1),
            KeyCode::Char('l') | KeyCode::Right => self.move_cursor(1),
            KeyCode::Char('H') | KeyCode::Home => self.cursor = Some(0),
            KeyCode::Char('L') | KeyCode::End => self.cursor = None,
            KeyCode::Char('m') => {
                self.marker = if self.marker == Marker::Braille {
                    Marker::Octant
                } else {
                    Marker::Braille
                };
            }
            KeyCode::Char('r') => {
                // Cheap local read: picks up whatever the latest `$` refresh
                // or backfill wrote without relaunching the TUI.
                self.reload();
                let msg = match &self.load_err {
                    Some(e) => format!("reload failed: {e}"),
                    None => format!("reloaded {} snapshots", self.history.len()),
                };
                self.set_flash(msg);
            }
            KeyCode::Char('i') => {
                if let Some(src) = self.selected_source().filter(Source::is_derived) {
                    self.inspector.open(&src);
                }
            }
            _ => {
                return source_bar::source_action(key, self.selected_source().as_ref())
                    .unwrap_or(Action::None);
            }
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
    }

    /// Key-driven screen: only redraw while a flash is waiting to expire.
    fn needs_redraw(&self) -> bool {
        self.flash.is_some()
    }
}

#[cfg(test)]
mod tests {
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    use super::*;

    /// 120 daily snapshots from 2026-01-01: dips below the start then
    /// recovers above it, so both colours and a zero crossing appear.
    fn history() -> Vec<Snapshot> {
        let start = NaiveDate::from_ymd_opt(2026, 1, 1).expect("date");
        (0..120)
            .map(|i| {
                let v =
                    10_000.0 + (i as f64 - 40.0) * (i as f64 - 40.0) - 1_600.0 + i as f64 * 10.0;
                Snapshot {
                    date: (start + chrono::Duration::days(i)).to_string(),
                    total_value: v,
                }
            })
            .collect()
    }

    fn screen() -> ChartScreen {
        ChartScreen::new(Theme::default(), PathBuf::from("/nonexistent"), history())
    }

    fn render(s: &mut ChartScreen) -> String {
        let mut term = Terminal::new(TestBackend::new(100, 24)).expect("terminal");
        term.draw(|f| s.draw(f)).expect("draw");
        let buf = term.backend().buffer();
        (0..buf.area.height)
            .map(|y| {
                (0..buf.area.width)
                    .map(|x| buf[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn press(s: &mut ChartScreen, c: KeyCode) -> Action {
        s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
    }

    #[test]
    fn window_anchors_on_latest_point() {
        let h = history();
        assert_eq!(
            window(&h, Range::OneM).first().map(|s| s.date.as_str()),
            Some("2026-03-31")
        );
        assert_eq!(window(&h, Range::All).len(), 120);
        assert!(window(&[], Range::OneM).is_empty());
    }

    #[test]
    fn points_carry_formula_and_both_snapshots() {
        let pts = to_points(&[
            Snapshot {
                date: "2026-01-01".into(),
                total_value: 2_000.0,
            },
            Snapshot {
                date: "2026-01-02".into(),
                total_value: 2_500.0,
            },
        ]);
        assert_eq!(pts[1].y, Some(25.0));
        let src = pts[1].src.as_ref().expect("src");
        assert_eq!(src.label, "E*TRADE account snapshot 2026-01-02");
        assert_eq!(
            src.formula.as_deref(),
            Some("($2,500.00 / $2,000.00 - 1) × 100 = +25.00%")
        );
        assert_eq!(src.inputs.len(), 2);
        assert!(
            src.inputs[0]
                .label
                .contains("2026-01-02: total_value $2,500.00")
        );
        assert!(
            src.inputs[1]
                .label
                .contains("2026-01-01: total_value $2,000.00")
        );
    }

    #[test]
    fn zero_start_value_is_a_gap_not_zero() {
        let pts = to_points(&[
            Snapshot {
                date: "d0".into(),
                total_value: 0.0,
            },
            Snapshot {
                date: "d1".into(),
                total_value: 5.0,
            },
        ]);
        assert_eq!(pts[1].y, None);
    }

    #[test]
    fn money_formats_thousands() {
        assert_eq!(money(1_234_567.891), "$1,234,567.89");
        assert_eq!(money(12.0), "$12.00");
        assert_eq!(money(-1_000.0), "-$1,000.00");
    }

    #[test]
    fn header_tabs_and_cursor_source() {
        let mut s = screen();
        let out = render(&mut s);
        let last = history().pop().expect("last");
        assert!(out.contains("Portfolio"), "{out}");
        assert!(out.contains(&money(last.total_value)), "{out}");
        assert!(out.contains("1M 3M 6M 1Y ALL"), "{out}");
        assert!(
            out.contains(&format!("E*TRADE account snapshot {}", last.date)),
            "{out}"
        );

        press(&mut s, KeyCode::Char('h'));
        let out = render(&mut s);
        assert!(out.contains("E*TRADE account snapshot 2026-04-29"), "{out}");

        press(&mut s, KeyCode::Char('5'));
        press(&mut s, KeyCode::Char('H'));
        let out = render(&mut s);
        assert!(out.contains("E*TRADE account snapshot 2026-01-01"), "{out}");
        assert!(out.contains("+0.00%"), "{out}");
    }

    #[test]
    fn keys() {
        let mut s = screen();
        assert_eq!(press(&mut s, KeyCode::Char('q')), Action::Quit);
        // y copies the formula (no document URL for an account snapshot).
        match press(&mut s, KeyCode::Char('y')) {
            Action::Copy(f) => assert!(f.contains("× 100 ="), "{f}"),
            a => panic!("expected copy, got {a:?}"),
        }
        press(&mut s, KeyCode::Char('i'));
        assert!(s.inspector.is_open());
        press(&mut s, KeyCode::Esc);
        assert!(!s.inspector.is_open());
        // Cursor clamps at both ends.
        for _ in 0..500 {
            press(&mut s, KeyCode::Char('h'));
        }
        assert_eq!(s.selected(window(&s.history, s.range).len()), Some(0));
        for _ in 0..500 {
            press(&mut s, KeyCode::Char('l'));
        }
        assert_eq!(s.cursor, None);
    }

    #[test]
    fn empty_and_unreadable_db_render_a_message() {
        let mut s = ChartScreen::new(
            Theme::default(),
            PathBuf::from("/nonexistent/x.duckdb"),
            Vec::new(),
        );
        assert!(render(&mut s).contains("no history yet"));
        s.reload();
        assert!(render(&mut s).contains("could not read portfolio_history"));
    }

    #[test]
    fn range_arg_parses() {
        assert_eq!(Range::parse("1y"), Some(Range::OneY));
        assert_eq!(Range::parse("ALL"), Some(Range::All));
        assert_eq!(Range::parse("x"), None);
    }
}
