// Candlestick screen (leader-vb): OHLC candles + volume for one ticker, from
// the local bars_1d pull (see universe::bars_glob). h/l move a cursor, the
// header shows the selected bar's O/H/L/C, change and volume.

use std::io;
use std::path::Path;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Tabs};

use crate::app::{Action, Ctx, Screen};
use crate::model::Candle;
use crate::ui::candles::{CandleChart, fit};
use crate::ui::help::{self, Key, key};
use crate::ui::theme::Theme;

const DEFAULT_TICKER: &str = "MRVL";
/// Trading days per range tab: 1M 3M 6M 1Y.
const RANGES: [(&str, usize); 4] = [("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252)];
/// Daily bars loaded per ticker: the longest range.
const LOAD: usize = 252;

const KEYS: &[Key] = &[
    key("1-4", "range 1M/3M/6M/1Y"),
    key("h/l", "move cursor"),
    key("H/L", "first / last bar"),
    key("?", "help"),
    key("q", "close"),
];

pub struct CandlesScreen {
    theme: Theme,
    ticker: String,
    all: Vec<Candle>,
    range: usize,
    /// Index into the drawn (merged) bars; None = follow the latest.
    cursor: Option<usize>,
    help: bool,
    /// Why there are no bars (no pull yet, unknown ticker); drawn instead of the chart.
    error: Option<String>,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<CandlesScreen> {
    let ticker = arg
        .map(|a| a.trim().to_uppercase())
        .filter(|a| !a.is_empty())
        .unwrap_or_else(|| DEFAULT_TICKER.into());
    let (all, error) = match load_bars(&ctx.db_path, &ticker) {
        Ok(bars) if bars.is_empty() => (bars, Some(format!("no daily bars for {ticker}"))),
        Ok(bars) => (bars, None),
        Err(e) => (Vec::new(), Some(e)),
    };
    Ok(CandlesScreen::new(ctx.theme, ticker, all, error))
}

/// The last LOAD daily bars for `ticker`, oldest first. Dates are New York
/// session dates (the bars are stamped 20:00 ET).
pub fn load_bars(db_path: &Path, ticker: &str) -> Result<Vec<Candle>, String> {
    if !ticker
        .chars()
        .all(|c| c.is_ascii_alphanumeric() || c == '.' || c == '-')
    {
        return Err(format!("bad ticker {ticker:?}"));
    }
    let conn = crate::db::open_read_only(db_path)?;
    let sql = format!(
        "SELECT CAST((ts_event AT TIME ZONE 'America/New_York')::DATE AS VARCHAR), open, high, low, close, volume \
         FROM bars_1d_adj WHERE symbol = '{ticker}' \
         ORDER BY ts_event DESC LIMIT {LOAD}"
    );
    let mut stmt = conn
        .prepare(&sql)
        .map_err(|e| format!("no daily bars ({e}). Run the databento bars_1d pull."))?;
    let mut bars: Vec<Candle> = stmt
        .query_map([], |r| {
            Ok(Candle {
                date: r.get(0)?,
                open: r.get(1)?,
                high: r.get(2)?,
                low: r.get(3)?,
                close: r.get(4)?,
                volume: r.get(5)?,
            })
        })
        .and_then(|rows| rows.collect())
        .map_err(|e| e.to_string())?;
    bars.reverse();
    Ok(bars)
}

impl CandlesScreen {
    pub fn new(theme: Theme, ticker: String, all: Vec<Candle>, error: Option<String>) -> Self {
        Self {
            theme,
            ticker,
            all,
            range: 1,
            cursor: None,
            help: false,
            error,
        }
    }

    fn window(&self) -> &[Candle] {
        let n = RANGES[self.range].1.min(self.all.len());
        &self.all[self.all.len() - n..]
    }

    fn selected(&self, len: usize) -> Option<usize> {
        (len > 0).then(|| self.cursor.unwrap_or(len - 1).min(len - 1))
    }

    fn move_cursor(&mut self, delta: isize, len: usize) {
        if let Some(cur) = self.selected(len) {
            self.cursor = Some(cur.saturating_add_signed(delta).min(len - 1));
        }
    }

    fn readout(&self, bars: &[Candle], sel: usize) -> Line<'static> {
        let t = &self.theme;
        let c = &bars[sel];
        let prev = if sel > 0 { bars[sel - 1].close } else { c.open };
        let chg = (c.close / prev - 1.0) * 100.0;
        let color = if c.is_up() { t.up } else { t.down };
        Line::from(vec![
            Span::styled(format!(" {} ", self.ticker), Style::new().fg(t.accent)),
            Span::styled(format!("{}  ", c.date), Style::new().fg(t.dim)),
            Span::raw(format!(
                "O {:.2}  H {:.2}  L {:.2}  C {:.2}  ",
                c.open, c.high, c.low, c.close
            )),
            Span::styled(format!("{chg:+.2}%  "), Style::new().fg(color)),
            Span::styled(format!("vol {}", c.volume), Style::new().fg(t.dim)),
            Span::styled("  bars_1d", Style::new().fg(t.dim)),
        ])
    }
}

impl Screen for CandlesScreen {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        let [tabs, header, chart, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(1),
        ])
        .areas(area);

        frame.render_widget(
            Tabs::new(RANGES.iter().map(|(l, _)| *l))
                .select(self.range)
                .style(Style::new().fg(t.dim))
                .highlight_style(Style::new().fg(t.accent)),
            tabs,
        );

        let bars = fit(self.window(), chart.width);
        let sel = self.selected(bars.len());
        if let Some(sel) = sel {
            frame.render_widget(Paragraph::new(self.readout(&bars, sel)), header);
        }
        match &self.error {
            Some(msg) => frame.render_widget(
                Paragraph::new(msg.as_str()).style(Style::new().fg(t.dim)),
                chart,
            ),
            None => frame.render_widget(CandleChart::new(&bars, &t).selected(sel), chart),
        }
        help::render_footer(frame, footer, KEYS, None, &t);
        if self.help {
            help::render_overlay(frame, area, "candles", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        // Cursor moves act on the drawn bars; width is unknown here, so the
        // clamp happens in `selected` on the next draw.
        let len = self.window().len();
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char(c @ '1'..='4') => {
                self.range = (c as usize) - ('1' as usize);
                self.cursor = None;
            }
            KeyCode::Char('h') | KeyCode::Left => self.move_cursor(-1, len),
            KeyCode::Char('l') | KeyCode::Right => self.move_cursor(1, len),
            KeyCode::Char('H') => self.cursor = Some(0),
            KeyCode::Char('L') => self.cursor = None,
            _ => {}
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, NaiveDate};
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    /// Deterministic bars, oldest first, one per calendar day from 2025-01-01.
    fn bars(n: usize) -> Vec<Candle> {
        let start = NaiveDate::from_ymd_opt(2025, 1, 1).unwrap();
        let mut prev = 50.0;
        (0..n)
            .map(|i| {
                let close = 50.0 + (i as f64 * 0.7).sin() * 5.0;
                let c = Candle {
                    date: (start + Duration::days(i as i64)).to_string(),
                    open: prev,
                    high: prev.max(close) + 1.0,
                    low: prev.min(close) - 1.0,
                    close,
                    volume: 1000 + i as u64,
                };
                prev = close;
                c
            })
            .collect()
    }

    fn screen() -> CandlesScreen {
        CandlesScreen::new(Theme::default(), "TEST".into(), bars(300), None)
    }

    fn render(s: &mut CandlesScreen, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| s.draw(f)).unwrap();
        let b = t.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn press(s: &mut CandlesScreen, c: KeyCode) -> Action {
        s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
    }

    #[test]
    fn renders_tabs_readout_and_chart() {
        let out = render(&mut screen(), 100, 24);
        assert!(out.contains("1M") && out.contains("1Y"));
        assert!(out.contains("TEST") && out.contains("bars_1d"));
        assert!(!out.contains("mock"));
        assert!(out.lines().any(|l| l.contains('█') || l.contains('▀')));
    }

    #[test]
    fn keys_change_range_and_cursor() {
        let mut s = screen();
        assert_eq!(s.window().len(), 63);
        press(&mut s, KeyCode::Char('1'));
        assert_eq!(s.window().len(), 21);
        press(&mut s, KeyCode::Char('4'));
        assert_eq!(s.window().len(), 252);
        press(&mut s, KeyCode::Char('h'));
        assert_eq!(s.cursor, Some(250));
        press(&mut s, KeyCode::Char('H'));
        assert_eq!(s.cursor, Some(0));
        press(&mut s, KeyCode::Char('h'));
        assert_eq!(s.cursor, Some(0));
        press(&mut s, KeyCode::Char('L'));
        assert_eq!(s.cursor, None);
        assert!(matches!(press(&mut s, KeyCode::Char('q')), Action::Quit));
    }

    #[test]
    fn readout_follows_cursor() {
        let mut s = screen();
        press(&mut s, KeyCode::Char('H'));
        let first = s.window()[0].date.clone();
        // 3M at width 100 is merged, so the first drawn bar ends its group.
        assert!(render(&mut s, 100, 24).contains(&first[..4]));
    }

    #[test]
    fn missing_bars_show_the_reason() {
        let mut s = CandlesScreen::new(
            Theme::default(),
            "XYZ".into(),
            Vec::new(),
            Some("no daily bars for XYZ".into()),
        );
        assert!(render(&mut s, 100, 24).contains("no daily bars for XYZ"));
    }

    #[test]
    fn tiny_terminal_does_not_panic() {
        render(&mut screen(), 12, 4);
        render(&mut screen(), 3, 2);
    }
}
