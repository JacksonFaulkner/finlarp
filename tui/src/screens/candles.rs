// Candlestick screen (leader-vb): OHLC candles + volume for one ticker.
// Bars are mock (src/mock.rs) until this reads bars_1d. h/l move a cursor,
// the header shows the selected bar's O/H/L/C, change and volume.

use std::io;

use chrono::Local;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph, Tabs};

use crate::app::{Action, Ctx, Screen};
use crate::mock;
use crate::model::Candle;
use crate::ui::candles::{CandleChart, fit};
use crate::ui::help::{self, Key, key};
use crate::ui::theme::Theme;

const DEFAULT_TICKER: &str = "SPRB";
const DAILY_VOL: f64 = 0.045;
/// Trading days per range tab: 1M 3M 6M 1Y.
const RANGES: [(&str, usize); 4] = [("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252)];

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
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<CandlesScreen> {
    let ticker = arg
        .map(|a| a.trim().to_uppercase())
        .filter(|a| !a.is_empty())
        .unwrap_or_else(|| DEFAULT_TICKER.into());
    Ok(CandlesScreen::new(ctx.theme, ticker))
}

impl CandlesScreen {
    pub fn new(theme: Theme, ticker: String) -> Self {
        let seed = mock::seed_for(&ticker);
        // Mock end price in 10..210, stable per ticker.
        let end_price = 10.0 + (seed % 200_000) as f64 / 1000.0;
        let n = RANGES[RANGES.len() - 1].1;
        let all = mock::candles(seed, n, end_price, DAILY_VOL, Local::now().date_naive());
        Self {
            theme,
            ticker,
            all,
            range: 1,
            cursor: None,
            help: false,
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
            Span::styled("  (mock)", Style::new().fg(t.dim)),
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
        frame.render_widget(CandleChart::new(&bars, &t).selected(sel), chart);
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
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    fn screen() -> CandlesScreen {
        CandlesScreen::new(Theme::default(), "SPRB".into())
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
        assert!(out.contains("SPRB") && out.contains("(mock)"));
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
    fn tiny_terminal_does_not_panic() {
        render(&mut screen(), 12, 4);
        render(&mut screen(), 3, 2);
    }
}
