// Portfolio suite: one screen, seven tabs (1-7).
//
//   1 Overview   real: KPIs, equity vs benchmark, drawdown, movers, allocation, alerts
//   2 Positions  real: weights pie + holdings table, linked by selection
//   3 Exposure   real: industry drift, concentration, correlation clusters
//   4 Risk       real: volatility, beta, drawdown, concentration
//   5 Activity   real: every cached transaction, newest first
//   6 Signals    real: calendar of every cached trade (buys green, sells red)
//   7 History    real: daily % change of the account, cursor and source bar (screens/chart.rs)
//
// Reads DuckDB only (see data.rs); the E*TRADE pull that fills it is the
// `$` refresh in py/sources/etrade.py, so a stale cache is shown, not fetched.

mod activity;
pub(crate) mod data;
mod holding;
mod mock;
mod overview;
mod pie;
mod risk;

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
use crate::screens::chart::ChartScreen;
use crate::ui::calendar::{Calendar, Event, Tone};
use crate::ui::help::{self, Key, key};
use crate::ui::layout::{self, PaneOpts};
use crate::ui::spin::{self, Spin};
use crate::ui::theme::Theme;
use data::{Bench, Data, Range};

const KEYS: &[Key] = &[
    key("1-7", "tab"),
    key("?", "help"),
    key("h/l", "cursor (overview, history) / holding (positions)"),
    key("j/k", "row (other tabs)"),
    key("r", "range (overview, history)"),
    key("b", "benchmark"),
    key("[ ]", "activity: context either side of the trades"),
    key("m", "marker braille/octant"),
    key("R", "reload from DuckDB"),
    key("q", "close"),
];

const TABS: [&str; 7] = [
    "1 Overview",
    "2 Positions",
    "3 Exposure",
    "4 Risk",
    "5 Activity",
    "6 Signals",
    "7 History",
];

const FLASH_FOR: Duration = Duration::from_millis(1500);
/// Env var naming the JSON file the background refresh reports through.
const STATUS_FILE_ENV: &str = "FINLARP_STATUS_FILE";
/// Positions older than this get a stale warning in the header.
const STALE_AFTER_S: f64 = 10.0 * 60.0;

/// Where the background refresh has got to.
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
    /// Activity chart context per side, in twelfths of the width (see activity::MARGIN_DEFAULT).
    margin: u8,
    /// Overview cursor: index into the range window; None = latest.
    cursor: Option<usize>,
    /// Row cursor for the table tabs.
    row: usize,
    help: bool,
    flash: Option<(String, Instant)>,
    /// Positions pie rotation.
    spin: Spin,
    /// Status file written by the background refresh, its last raw contents, and what
    /// it said. The TUI only reads DuckDB, so this is how it learns to reload.
    status_file: Option<PathBuf>,
    status_seen: String,
    sync: Sync,
    redraw: bool,
    /// Signals tab: the calendar of every cached trade.
    signals: Calendar,
    /// History tab: the daily % change chart. Owns its own range and cursor.
    history: ChartScreen,
}

/// Every cached trade as a calendar event: buys green, sells red, the rest plain.
fn trade_events(txns: &[data::Txn]) -> Vec<Event> {
    txns.iter()
        .map(|x| {
            let tone = match x.kind.as_str() {
                "Bought" => Tone::Up,
                "Sold" => Tone::Down,
                _ => Tone::Plain,
            };
            Event {
                date: x.date,
                time: None,
                label: format!("{} {} {:.0}", x.kind, x.symbol, x.qty),
                detail: Some(format!(
                    "{:.0} @ ${:.2}  cash {:+.0}",
                    x.qty, x.price, x.amount
                )),
                tone,
                link: None,
            }
        })
        .collect()
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
        let history = ChartScreen::new(theme, db_path.clone(), Vec::new());
        Self {
            history,
            db_path,
            theme,
            data,
            load_err: None,
            tab: 0,
            range: Range::ThreeM,
            bench: Bench::Spy,
            marker: Marker::Braille,
            margin: activity::MARGIN_DEFAULT,
            cursor: None,
            row: 0,
            help: false,
            flash: None,
            spin: Spin::default(),
            status_file: None,
            status_seen: String::new(),
            sync: Sync::Idle,
            redraw: false,
            signals: Calendar::new(chrono::Local::now().date_naive(), Vec::new(), theme),
        }
    }

    /// Re-reads DuckDB, leaving the cursor where it is.
    fn refresh_data(&mut self) {
        self.history.reload();
        match data::load(&self.db_path) {
            Ok(d) => {
                self.signals.set_events(trade_events(&d.txns));
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

    /// Applies a new status message from the background refresh.
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
            4 => self.data.txns.len(),
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
                        rot: self.spin.angle,
                        today: chrono::Local::now().date_naive(),
                    };
                    pie::draw(frame, p.detail, &view);
                }
                2 => {
                    let tot = data::totals(&self.data.history, &self.data.positions);
                    let view = mock::ExposureView {
                        theme: &t,
                        positions: &self.data.positions,
                        tot: &tot,
                        exp: &self.data.exposure,
                    };
                    mock::exposure(frame, p.detail, &view);
                }
                3 => risk::draw(frame, p.detail, &t, &self.data, self.range, self.bench),
                4 => activity::draw(
                    frame,
                    p.detail,
                    &t,
                    &self.data,
                    self.row,
                    chrono::Utc::now(),
                    self.margin,
                ),
                5 => self.signals.draw(frame, p.detail),
                _ => self.history.draw_body(frame, p.detail),
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
        // The Signals tab is a calendar: it takes its own keys, except the ones that leave the screen or switch tabs.
        let tab_key = matches!(
            key.code,
            KeyCode::Char('q' | '?' | '1'..='7') | KeyCode::Tab | KeyCode::BackTab | KeyCode::Esc
        );
        if self.tab == 5 && !tab_key && self.signals.on_key(key) {
            return Action::None;
        }
        // The History tab's source inspector takes every key until it closes.
        if self.tab == 6 && self.history.inspecting() {
            return self.history.on_key(key);
        }
        // `r` is the range here, as on the overview; `R` still reloads everything.
        if self.tab == 6 && !tab_key && key.code != KeyCode::Char('R') {
            if key.code == KeyCode::Char('r') {
                self.history.cycle_range();
                return Action::None;
            }
            return self.history.on_key(key);
        }
        let switch = |s: &mut Self, tab: usize| {
            s.tab = tab;
            s.row = 0;
        };
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char(c @ '1'..='7') => switch(self, (c as u8 - b'1') as usize),
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
            KeyCode::Char(']') if self.tab == 4 => {
                self.margin = (self.margin + 1).min(activity::MARGIN_MAX)
            }
            KeyCode::Char('[') if self.tab == 4 => {
                self.margin = self.margin.saturating_sub(1).max(activity::MARGIN_MIN)
            }
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
        self.flash.is_some() || self.spin.turning || self.redraw
    }

    fn poll_interval(&self) -> Duration {
        if self.spin.turning {
            spin::FRAME
        } else {
            Duration::from_millis(100)
        }
    }

    fn tick(&mut self) -> Action {
        self.poll_status();
        let cash = data::totals(&self.data.history, &self.data.positions).cash;
        let target = pie::facing_left(&self.data.positions, cash, self.row);
        self.spin.tick(target, self.tab == 1, Instant::now());
        Action::None
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::chart;
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
            for tab in 0..7 {
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
    fn risk_activity_and_signals_render_real_data() {
        let mut d = sample();
        d.txns = vec![data::Txn {
            id: "1".into(),
            date: NaiveDate::from_ymd_opt(2026, 9, 12).unwrap(),
            at: NaiveDate::from_ymd_opt(2026, 9, 12)
                .unwrap()
                .and_hms_opt(16, 0, 0)
                .unwrap()
                .and_utc(),
            kind: "Sold".into(),
            symbol: "AMD".into(),
            qty: -50.0,
            price: 162.0,
            amount: 8100.0,
        }];
        let mut s = screen(d);
        s.tab = 3;
        let out = render(&mut s, 120, 30);
        assert!(
            out.contains("Volatility") && out.contains("Concentration"),
            "{out}"
        );
        s.tab = 4;
        let out = render(&mut s, 120, 30);
        assert!(out.contains("Ledger") && out.contains("AMD"), "{out}");
        s.tab = 5;
        assert!(!render(&mut s, 120, 30).contains("mock"));
        let events = trade_events(&s.data.txns);
        assert_eq!(events.len(), 1);
        assert_eq!(events[0].tone, Tone::Down, "sells are red");
        assert_eq!(events[0].label, "Sold AMD -50");
    }

    #[test]
    fn exposure_drift_renders_industry_rows() {
        let mut d = sample();
        let start = NaiveDate::from_ymd_opt(2026, 1, 1).unwrap();
        d.txns = vec![data::Txn {
            id: "1".into(),
            date: start,
            at: start.and_hms_opt(16, 0, 0).unwrap().and_utc(),
            kind: "trade".into(),
            symbol: "NVDA".into(),
            qty: 10.0,
            price: 100.0,
            amount: -1000.0,
        }];
        d.closes.insert(
            "NVDA".into(),
            (0..120)
                .map(|i| (start + chrono::Duration::days(i), 100.0 + i as f64))
                .collect(),
        );
        let industries =
            std::collections::HashMap::from([("NVDA".to_string(), "gpu accelerators".to_string())]);
        d.exposure =
            data::build_exposure(&d.history, &d.positions, &d.txns, &d.closes, &industries);
        let mut s = screen(d);
        s.tab = 2;
        let out = render(&mut s, 160, 50);
        assert!(out.contains("gpu accel"), "{out}");
        assert!(
            out.contains("100.0%"),
            "latest drift weight missing:\n{out}"
        );
    }

    #[test]
    fn exposure_tab_shows_real_panels() {
        let mut s = screen(sample());
        s.tab = 2;
        let out = render(&mut s, 160, 50);
        assert!(out.contains("By industry"), "{out}");
        assert!(out.contains("Industry drift"));
        assert!(out.contains("Concentration"));
        assert!(out.contains("Top 1"));
        assert!(
            !out.contains("· mock"),
            "exposure panels are live, not mock:\n{out}"
        );
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
        assert_eq!(s.tab, 6); // wraps
    }

    #[test]
    fn history_tab_draws_the_chart_and_takes_its_keys() {
        let start = NaiveDate::from_ymd_opt(2026, 1, 1).unwrap();
        let history = (0..60)
            .map(|i| chart::Snapshot {
                date: (start + chrono::Duration::days(i)).to_string(),
                total_value: 10_000.0 + i as f64 * 10.0,
            })
            .collect();
        let mut s = screen(sample());
        s.history = ChartScreen::new(Theme::default(), PathBuf::new(), history);
        s.on_key(k('7'));
        let out = render(&mut s, 120, 30);
        assert!(!out.contains("no history yet"), "{out}");
        assert!(out.contains("ALL"), "range tabs missing:\n{out}");
        s.on_key(k('r'));
        assert_eq!(s.history.range, chart::Range::SixM);
        assert_eq!(s.range, Range::ThreeM, "overview range must not move");
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
        assert!(s.spin.turning, "should be turning after a selection change");
        for _ in 0..2000 {
            std::thread::sleep(Duration::from_millis(1));
            s.tick();
            if !s.spin.turning {
                break;
            }
        }
        assert!(!s.spin.turning);
        let cash = data::totals(&s.data.history, &s.data.positions).cash;
        assert!((s.spin.angle - pie::facing_left(&s.data.positions, cash, s.row)).abs() < 1e-6);
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
