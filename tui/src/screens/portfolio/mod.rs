// Portfolio suite: one screen, six tabs (1-6).
//
//   1 Overview   real: KPIs, equity vs benchmark, drawdown, movers, allocation, alerts
//   2 Positions  real: weights pie + holdings table, linked by selection
//   3 Exposure   mock skeleton
//   4 Risk       mock skeleton
//   5 Activity   mock skeleton
//   6 Signals    mock skeleton
//
// Reads DuckDB only (see data.rs); the E*TRADE pull that fills it is the
// `$` refresh in py/sources/etrade.py, so a stale cache is shown, not fetched.

mod data;
mod holding;
mod mock;
mod overview;
mod pie;

use std::io;
use std::path::PathBuf;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::symbols::Marker;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Tabs};

use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{self, Key, key};
use crate::ui::layout::{self, PaneOpts};
use crate::ui::theme::Theme;
use data::{Bench, Data, Range};

const KEYS: &[Key] = &[
    key("1-6", "tab"),
    key("?", "help"),
    key("h/l", "cursor (overview) / holding (positions)"),
    key("j/k", "row (other tabs)"),
    key("r", "range"),
    key("b", "benchmark"),
    key("m", "marker braille/octant"),
    key("R", "reload from DuckDB"),
    key("q", "close"),
];

const TABS: [&str; 6] = [
    "1 Overview",
    "2 Positions",
    "3 Exposure",
    "4 Risk",
    "5 Activity",
    "6 Signals",
];

const FLASH_FOR: Duration = Duration::from_millis(1500);
/// Redraw interval while the pie spins, and its ease-out time constant (s).
const FRAME: Duration = Duration::from_millis(16);
const SPIN_TAU: f64 = 0.09;
/// Env var naming the JSON file nvim's background refresh reports through.
const STATUS_FILE_ENV: &str = "FINLARP_STATUS_FILE";
/// Positions older than this get a stale warning in the header.
const STALE_AFTER_S: f64 = 10.0 * 60.0;

/// Where nvim's background refresh (init.lua refresh_portfolio) has got to.
#[derive(Debug, Default, PartialEq)]
enum Sync {
    #[default]
    Idle,
    Refreshing(String),
    Failed(String),
}

#[derive(serde::Deserialize)]
struct StatusMsg {
    state: String,
    #[serde(default)]
    msg: String,
    #[serde(default)]
    pulled: bool,
}

pub struct PortfolioScreen {
    db_path: PathBuf,
    theme: Theme,
    data: Data,
    load_err: Option<String>,
    tab: usize,
    range: Range,
    bench: Bench,
    marker: Marker,
    /// Overview cursor: index into the range window; None = latest.
    cursor: Option<usize>,
    /// Row cursor for the table tabs.
    row: usize,
    help: bool,
    flash: Option<(String, Instant)>,
    /// Positions pie rotation (degrees) and whether it is still turning.
    spin: f64,
    spinning: bool,
    spin_at: Instant,
    /// Status file written by nvim's refresh, its last raw contents, and what
    /// it said. The TUI only reads DuckDB, so this is how it learns to reload.
    status_file: Option<PathBuf>,
    status_seen: String,
    sync: Sync,
    redraw: bool,
}

/// `arg`: optional starting range ("1M".."ALL").
pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<PortfolioScreen> {
    let mut s = PortfolioScreen::new(ctx.theme, ctx.db_path.clone(), Data::default());
    if let Some(r) = arg.as_deref().and_then(|a| {
        Range::ALL
            .into_iter()
            .find(|r| r.label().eq_ignore_ascii_case(a))
    }) {
        s.range = r;
    }
    s.status_file = std::env::var_os(STATUS_FILE_ENV).map(PathBuf::from);
    s.reload();
    Ok(s)
}

impl PortfolioScreen {
    pub fn new(theme: Theme, db_path: PathBuf, data: Data) -> Self {
        Self {
            db_path,
            theme,
            data,
            load_err: None,
            tab: 0,
            range: Range::ThreeM,
            bench: Bench::Spy,
            marker: Marker::Braille,
            cursor: None,
            row: 0,
            help: false,
            flash: None,
            spin: 0.0,
            spinning: false,
            spin_at: Instant::now(),
            status_file: None,
            status_seen: String::new(),
            sync: Sync::Idle,
            redraw: false,
        }
    }

    /// Re-reads DuckDB, leaving the cursor where it is.
    fn refresh_data(&mut self) {
        match data::load(&self.db_path) {
            Ok(d) => {
                self.data = d;
                self.load_err = None;
            }
            Err(e) => self.load_err = Some(e),
        }
    }

    fn reload(&mut self) {
        self.refresh_data();
        self.cursor = None;
    }

    /// Applies a new status message from nvim's background refresh.
    fn poll_status(&mut self) {
        let Some(path) = &self.status_file else {
            return;
        };
        let Ok(raw) = std::fs::read_to_string(path) else {
            return;
        };
        if raw == self.status_seen {
            return;
        }
        let msg = serde_json::from_str::<StatusMsg>(&raw).ok();
        self.status_seen = raw;
        let Some(m) = msg else {
            return;
        };
        self.redraw = true;
        match m.state.as_str() {
            "refreshing" => self.sync = Sync::Refreshing(m.msg),
            "error" => {
                self.refresh_data(); // whatever did land
                self.sync = Sync::Failed(m.msg);
            }
            _ => {
                self.refresh_data();
                self.sync = Sync::Idle;
                if m.pulled {
                    self.set_flash(m.msg);
                }
            }
        }
    }

    fn rows_in_tab(&self) -> usize {
        match self.tab {
            1 => {
                let cash = data::totals(&self.data.history, &self.data.positions).cash;
                pie::len(&self.data.positions, cash)
            }
            3 => mock::RISK_LEN,
            4 => mock::ACTIVITY_LEN,
            5 => mock::SIGNALS_LEN,
            _ => 0,
        }
    }

    fn move_cursor(&mut self, delta: isize) {
        let len = overview::window_len(&self.data, self.range);
        if len == 0 {
            return;
        }
        let cur = self.cursor.unwrap_or(len - 1).min(len - 1);
        let next = cur.saturating_add_signed(delta).min(len - 1);
        self.cursor = if next == len - 1 { None } else { Some(next) };
    }

    fn move_row(&mut self, delta: isize) {
        let len = self.rows_in_tab();
        if len > 0 {
            self.row = self.row.saturating_add_signed(delta).min(len - 1);
        }
    }

    fn header(&self) -> Line<'static> {
        let t = &self.theme;
        let age = self.data.positions_at.map(|at| {
            let h = (now() - at) / 3600.0;
            if h < 1.0 {
                format!("{:.0}m ago", (h * 60.0).max(0.0))
            } else {
                format!("{h:.0}h ago")
            }
        });
        let stale = self
            .data
            .positions_at
            .is_some_and(|at| now() - at > STALE_AFTER_S);
        let mut spans = vec![
            Span::styled(" Portfolio ", t.title()),
            Span::styled(" E*TRADE", t.dim()),
        ];
        if let Some(a) = age {
            let style = if stale && self.sync == Sync::Idle {
                t.accent()
            } else {
                t.dim()
            };
            let tag = if stale { " (stale)" } else { "" };
            spans.push(Span::styled(format!(" · positions {a}{tag}"), style));
        }
        match &self.sync {
            Sync::Idle => {}
            Sync::Refreshing(m) => spans.push(Span::styled(format!(" · ↻ {m}"), t.accent())),
            Sync::Failed(m) => spans.push(Span::styled(format!(" · ✗ {m}"), t.down())),
        }
        if self.tab > 1 {
            spans.push(Span::styled(" · tabs 3-6 are mock data", t.accent()));
        }
        Line::from(spans)
    }
}

fn now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0.0, |d| d.as_secs_f64())
}

impl Screen for PortfolioScreen {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        self.redraw = false;
        frame.render_widget(Block::new().style(t.base()), area);
        if self
            .flash
            .as_ref()
            .is_some_and(|(_, at)| at.elapsed() > FLASH_FOR)
        {
            self.flash = None;
        }
        let p = layout::panes(
            area,
            PaneOpts {
                nav_width: 0,
                source_height: 0,
                tabs_height: 1,
                ..Default::default()
            },
        );

        let [left, right] = p.header.layout(&Layout::horizontal([
            Constraint::Min(0),
            Constraint::Length(26),
        ]));
        frame.render_widget(Paragraph::new(self.header()).style(t.base()), left);
        if self.tab == 0 {
            let ranges = Tabs::new(Range::ALL.iter().map(|r| r.label()))
                .select(self.range.index())
                .style(t.dim())
                .highlight_style(t.title())
                .divider(" ")
                .padding("", "");
            frame.render_widget(ranges, right);
        }

        let strip = Tabs::new(TABS)
            .select(self.tab)
            .style(t.dim())
            .highlight_style(t.selected().bold())
            .divider("│")
            .padding(" ", " ");
        frame.render_widget(strip, p.tabs);

        let flash = self.flash.as_ref().map(|(m, _)| m.as_str());
        help::render_footer(frame, p.footer, KEYS, flash, &t);

        if let Some(e) = &self.load_err {
            let r = p.detail.centered_vertically(Constraint::Length(1));
            let msg = format!("could not read portfolio data: {e}");
            frame.render_widget(Paragraph::new(msg).style(t.dim()).centered(), r);
        } else {
            match self.tab {
                0 => overview::draw(
                    frame,
                    p.detail,
                    &overview::View {
                        theme: &t,
                        data: &self.data,
                        range: self.range,
                        bench: self.bench,
                        marker: self.marker,
                        cursor: self.cursor,
                        now: now(),
                    },
                ),
                1 => {
                    let tot = data::totals(&self.data.history, &self.data.positions);
                    let view = pie::View {
                        theme: &t,
                        positions: &self.data.positions,
                        tot: &tot,
                        txns: &self.data.txns,
                        closes: &self.data.closes,
                        sel: self.row,
                        rot: self.spin,
                        today: chrono::Local::now().date_naive(),
                    };
                    pie::draw(frame, p.detail, &view);
                }
                2 => mock::exposure(frame, p.detail, &t),
                3 => mock::risk(frame, p.detail, &t, self.row),
                4 => mock::activity(frame, p.detail, &t, self.row),
                _ => mock::signals(frame, p.detail, &t, self.row),
            }
        }
        if self.help {
            help::render_overlay(frame, area, "portfolio", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        let switch = |s: &mut Self, tab: usize| {
            s.tab = tab;
            s.row = 0;
        };
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char(c @ '1'..='6') => switch(self, (c as u8 - b'1') as usize),
            KeyCode::Tab => switch(self, (self.tab + 1) % TABS.len()),
            KeyCode::BackTab => switch(self, (self.tab + TABS.len() - 1) % TABS.len()),
            KeyCode::Char('h') | KeyCode::Left if self.tab == 0 => self.move_cursor(-1),
            KeyCode::Char('l') | KeyCode::Right if self.tab == 0 => self.move_cursor(1),
            KeyCode::Char('h') | KeyCode::Left if self.tab == 1 => self.move_row(-1),
            KeyCode::Char('l') | KeyCode::Right if self.tab == 1 => self.move_row(1),
            KeyCode::Char('H') | KeyCode::Home if self.tab == 0 => self.cursor = Some(0),
            KeyCode::Char('L') | KeyCode::End if self.tab == 0 => self.cursor = None,
            KeyCode::Char('j') | KeyCode::Down => self.move_row(1),
            KeyCode::Char('k') | KeyCode::Up => self.move_row(-1),
            KeyCode::Char('g') => self.row = 0,
            KeyCode::Char('G') => self.row = self.rows_in_tab().saturating_sub(1),
            KeyCode::Char('r') if self.tab == 0 => {
                self.range = self.range.next();
                self.cursor = None;
            }
            KeyCode::Char('b') if self.tab == 0 => self.bench = self.bench.next(),
            KeyCode::Char('m') => {
                self.marker = if self.marker == Marker::Braille {
                    Marker::Octant
                } else {
                    Marker::Braille
                };
            }
            KeyCode::Char('R') => {
                self.reload();
                let msg = match &self.load_err {
                    Some(e) => format!("reload failed: {e}"),
                    None => format!(
                        "reloaded {} snapshots, {} positions",
                        self.data.history.len(),
                        self.data.positions.len()
                    ),
                };
                self.set_flash(msg);
            }
            _ => {}
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some((msg, Instant::now()));
    }

    fn needs_redraw(&self) -> bool {
        self.flash.is_some() || self.spinning || self.redraw
    }

    fn poll_interval(&self) -> Duration {
        if self.spinning {
            FRAME
        } else {
            Duration::from_millis(100)
        }
    }

    fn tick(&mut self) -> Action {
        self.poll_status();
        let now = Instant::now();
        let dt = now.duration_since(self.spin_at).as_secs_f64().min(0.1);
        self.spin_at = now;
        let cash = data::totals(&self.data.history, &self.data.positions).cash;
        let target = pie::facing_left(&self.data.positions, cash, self.row);
        // Shortest way round, exponential ease-out.
        let delta = (target - self.spin + 540.0).rem_euclid(360.0) - 180.0;
        if self.tab != 1 || delta.abs() < 0.2 {
            self.spin = target;
            self.spinning = false;
        } else {
            self.spin += delta * (1.0 - (-dt / SPIN_TAU).exp());
            self.spinning = true;
        }
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;
    use data::{Position, Snapshot};
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    fn k(c: char) -> KeyEvent {
        KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)
    }

    fn sample() -> Data {
        let start = NaiveDate::from_ymd_opt(2026, 1, 1).unwrap();
        let history: Vec<Snapshot> = (0..120)
            .map(|i| Snapshot {
                date: start + chrono::Duration::days(i),
                value: 50_000.0 + i as f64 * 40.0,
                day_pct: if i % 7 == 0 { -1.4 } else { 0.6 },
            })
            .collect();
        let closes: Vec<(NaiveDate, f64)> = (0..120)
            .map(|i| (start + chrono::Duration::days(i), 500.0 + i as f64))
            .collect();
        let mut d = Data {
            history,
            ..Default::default()
        };
        d.bench.insert("SPY", closes);
        d.positions = vec![Position {
            symbol: "NVDA".into(),
            qty: 10.0,
            price: 100.0,
            price_paid: 80.0,
            total_gain: 200.0,
            value: 1000.0,
            day_gain: 20.0,
            day_pct: 2.0,
            industry: "gpu accelerators".into(),
        }];
        d
    }

    fn screen(data: Data) -> PortfolioScreen {
        PortfolioScreen::new(Theme::default(), PathBuf::new(), data)
    }

    fn render(s: &mut PortfolioScreen, w: u16, h: u16) -> String {
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| s.draw(f)).unwrap();
        term.backend().to_string()
    }

    #[test]
    fn every_tab_renders_at_many_sizes_without_panicking() {
        for (w, h) in [(160, 50), (100, 30), (60, 20), (20, 6), (1, 1)] {
            for tab in 0..6 {
                let mut s = screen(sample());
                s.tab = tab;
                render(&mut s, w, h);
            }
        }
    }

    #[test]
    fn overview_shows_real_numbers() {
        let mut s = screen(sample());
        let out = render(&mut s, 160, 50);
        assert!(out.contains("Equity vs SPY"), "{out}");
        assert!(out.contains("Drawdown"));
        assert!(out.contains("NVDA"), "top mover missing");
        assert!(out.contains("gpu accel"), "allocation missing");
        assert!(out.contains("Cash"));
    }

    #[test]
    fn empty_data_shows_a_message_not_a_panic() {
        let mut s = screen(Data::default());
        let out = render(&mut s, 120, 40);
        assert!(out.contains("no history yet"), "{out}");
    }

    #[test]
    fn mock_tabs_are_labelled_mock() {
        let mut s = screen(sample());
        s.tab = 2;
        assert!(render(&mut s, 120, 30).contains("mock"));
    }

    #[test]
    fn number_keys_and_tab_switch_tabs() {
        let mut s = screen(sample());
        s.on_key(k('4'));
        assert_eq!(s.tab, 3);
        s.on_key(KeyEvent::new(KeyCode::Tab, KeyModifiers::NONE));
        assert_eq!(s.tab, 4);
        s.on_key(KeyEvent::new(KeyCode::BackTab, KeyModifiers::SHIFT));
        s.on_key(KeyEvent::new(KeyCode::BackTab, KeyModifiers::SHIFT));
        assert_eq!(s.tab, 2);
        s.on_key(k('1'));
        s.on_key(KeyEvent::new(KeyCode::BackTab, KeyModifiers::SHIFT));
        assert_eq!(s.tab, 5); // wraps
    }

    #[test]
    fn overview_cursor_follows_latest_and_clamps() {
        let mut s = screen(sample());
        s.on_key(k('h'));
        assert!(s.cursor.is_some());
        s.on_key(k('H'));
        assert_eq!(s.cursor, Some(0));
        s.on_key(k('h')); // clamps at the first point
        assert_eq!(s.cursor, Some(0));
        s.on_key(k('L'));
        assert_eq!(s.cursor, None);
        s.on_key(k('l')); // already at the end
        assert_eq!(s.cursor, None);
    }

    #[test]
    fn row_cursor_clamps_and_resets_on_tab_switch() {
        let mut s = screen(sample());
        s.on_key(k('2'));
        for _ in 0..50 {
            s.on_key(k('j'));
        }
        assert_eq!(s.row, s.rows_in_tab() - 1);
        s.on_key(k('k'));
        assert_eq!(s.row, s.rows_in_tab() - 2);
        s.on_key(k('3'));
        assert_eq!(s.row, 0);
    }

    #[test]
    fn hl_switch_holding_and_spotlight_shows_pnl() {
        let mut s = screen(sample());
        s.on_key(k('2'));
        s.on_key(k('l'));
        assert_eq!(s.row, 1);
        s.on_key(k('h'));
        assert_eq!(s.row, 0);
        let out = render(&mut s, 120, 40);
        assert!(out.contains("P&L"), "{out}");
    }

    #[test]
    fn pie_spins_toward_selection_then_settles() {
        let mut s = screen(sample());
        s.data.positions.push(Position {
            symbol: "AMD".into(),
            value: 3000.0,
            ..s.data.positions[0].clone()
        });
        s.on_key(k('2'));
        s.tick();
        s.on_key(k('j'));
        s.tick();
        assert!(s.spinning, "should be turning after a selection change");
        for _ in 0..2000 {
            std::thread::sleep(Duration::from_millis(1));
            s.tick();
            if !s.spinning {
                break;
            }
        }
        assert!(!s.spinning);
        let cash = data::totals(&s.data.history, &s.data.positions).cash;
        assert!((s.spin - pie::facing_left(&s.data.positions, cash, s.row)).abs() < 1e-6);
    }

    #[test]
    fn range_and_benchmark_cycle_only_on_overview() {
        let mut s = screen(sample());
        assert_eq!(s.range, Range::ThreeM);
        s.on_key(k('r'));
        assert_eq!(s.range, Range::SixM);
        s.on_key(k('b'));
        assert_eq!(s.bench, Bench::Qqq);
        s.on_key(k('b'));
        assert_eq!(s.bench, Bench::Soxx);
        s.on_key(k('b'));
        assert_eq!(s.bench, Bench::Spy);
        s.on_key(k('b'));
        s.on_key(k('2'));
        s.on_key(k('r'));
        assert_eq!(s.range, Range::SixM);
    }

    #[test]
    fn status_file_drives_header_and_reload() {
        let path = std::env::temp_dir().join(format!("pc_status_{}", std::process::id()));
        let mut s = screen(sample());
        s.status_file = Some(path.clone());
        let write = |j: &str| std::fs::write(&path, j).unwrap();

        write(r#"{"seq":1,"state":"refreshing","msg":"refreshing positions…","pulled":true}"#);
        s.poll_status();
        assert_eq!(s.sync, Sync::Refreshing("refreshing positions…".into()));
        assert!(render(&mut s, 120, 30).contains("refreshing positions"));

        write(r#"{"seq":2,"state":"error","msg":"positions: boom","pulled":true}"#);
        s.poll_status();
        assert_eq!(s.sync, Sync::Failed("positions: boom".into()));

        write(r#"{"seq":3,"state":"done","msg":"portfolio updated","pulled":true}"#);
        s.poll_status();
        assert_eq!(s.sync, Sync::Idle);
        assert!(s.flash.is_some());
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn quit_and_help() {
        let mut s = screen(sample());
        s.on_key(k('?'));
        assert!(s.help);
        assert_eq!(s.on_key(k('q')), Action::None); // closes help first
        assert!(!s.help);
        assert_eq!(s.on_key(k('q')), Action::Quit);
    }
}

/// Symbols that ever changed share count in the cached E*TRADE
/// transactions (buys, sells, splits), sorted. Empty when nothing is cached.
pub fn traded_symbols(db_path: &std::path::Path) -> Result<Vec<String>, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let Ok(mut stmt) = conn.prepare("SELECT transactions_json FROM transactions_cache") else {
        return Ok(Vec::new()); // table not created yet = nothing cached
    };
    let rows = stmt
        .query_map([], |r| r.get::<_, String>(0))
        .map_err(|e| e.to_string())?;
    let mut out = std::collections::BTreeSet::new();
    for json in rows.flatten() {
        for t in data::parse_txns(&json) {
            if matches!(t.kind.as_str(), "Bought" | "Sold" | "Stock Split") {
                out.insert(t.symbol);
            }
        }
    }
    Ok(out.into_iter().collect())
}
