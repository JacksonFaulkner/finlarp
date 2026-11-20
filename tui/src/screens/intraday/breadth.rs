// Breadth board: the few names the day's trade is read off, one row each, and a gate line
// that says how many are above their previous close. When every name is up at once the
// gate reads ALL UP with the ET time it was first seen, and it drops the moment one slips
// back below its close.
//
//   fl breadth                         (SOXX QQQ SPY DRAM NVDA)
//   fl breadth SOXX,QQQ,SPY,DRAM,AMD
//
// Same feed as `fl intraday` (stream.rs): one websocket, 1-minute bars folded per symbol.
// Up = latest print above the previous close. VWAP is shown per row, not gated on.
// ↵ opens the intraday tapes with the selected name first.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Paragraph};

use crate::app::{Action, Ctx, Route, Screen};
use crate::ui::help::{self, Key, key};
use crate::ui::theme::Theme;

use super::data::Series;
use super::stream::{Event, Stream};

/// The basket when no tickers are given: the two index ETFs, the memory ETF, and the AI name in the news.
pub const DEFAULT_BASKET: [&str; 5] = ["SOXX", "QQQ", "SPY", "DRAM", "NVDA"];

const KEYS: &[Key] = &[
    key("j/k", "move cursor"),
    key("↵", "intraday tapes for the selected name"),
    key("r", "resync from REST"),
    key("?", "help"),
    key("q/esc", "close"),
];

/// `A,B C` -> uppercase symbols, deduped, in the order given; the default basket when empty.
pub fn parse_basket(arg: Option<&str>) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for s in arg
        .unwrap_or("")
        .split([',', ' '])
        .map(|s| s.trim().to_uppercase())
    {
        if !s.is_empty() && !out.contains(&s) {
            out.push(s);
        }
    }
    if out.is_empty() {
        out = DEFAULT_BASKET.iter().map(|s| s.to_string()).collect();
    }
    out
}

/// One name's state as the gate sees it. `None` means no data yet.
#[derive(Debug, Clone, PartialEq)]
pub struct Row {
    pub sym: String,
    pub last: Option<f64>,
    pub prev: Option<f64>,
    pub vwap: Option<f64>,
    /// Epoch seconds of the latest bar.
    pub t: Option<i64>,
}

impl Row {
    /// Percent change from the previous close.
    pub fn pct(&self) -> Option<f64> {
        match (self.last, self.prev) {
            (Some(l), Some(p)) if p > 0.0 => Some((l / p - 1.0) * 100.0),
            _ => None,
        }
    }

    /// Some(true) above the previous close, Some(false) at or below, None without data.
    pub fn up(&self) -> Option<bool> {
        self.pct().map(|p| p > 0.0)
    }
}

/// Every name has data and is above its previous close. One missing name blocks the gate.
pub fn all_up(rows: &[Row]) -> bool {
    !rows.is_empty() && rows.iter().all(|r| r.up() == Some(true))
}

fn row_of(sym: &str, s: Option<&Series>) -> Row {
    Row {
        sym: sym.to_string(),
        last: s.and_then(Series::last_close),
        prev: s.and_then(|s| s.prev_close),
        vwap: s.and_then(Series::vwap),
        t: s.and_then(Series::last_time),
    }
}

pub struct Breadth {
    theme: Theme,
    stream: Stream,
    /// One entry per basket name, in basket order.
    names: Vec<(String, Series)>,
    cursor: usize,
    live: bool,
    status: String,
    /// Epoch seconds of the bar at which the gate was first seen open this run.
    gate_at: Option<i64>,
    help: bool,
    flash: Option<String>,
    changed: bool,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Breadth> {
    let basket = parse_basket(arg.as_deref());
    Ok(Breadth::new(ctx.theme, basket, Stream::spawn()))
}

impl Breadth {
    fn new(theme: Theme, basket: Vec<String>, mut stream: Stream) -> Self {
        stream.set_symbols(&basket);
        Self {
            theme,
            stream,
            names: basket.into_iter().map(|s| (s, Series::default())).collect(),
            cursor: 0,
            live: false,
            status: "connecting…".into(),
            gate_at: None,
            help: false,
            flash: None,
            changed: true,
        }
    }

    fn rows(&self) -> Vec<Row> {
        self.names
            .iter()
            .map(|(sym, s)| row_of(sym, (!s.is_empty()).then_some(s)))
            .collect()
    }

    fn handle(&mut self, ev: Event) {
        self.changed = true;
        match ev {
            Event::Seed {
                sym,
                prev_close,
                reg,
                bars,
            } => {
                for (_, s) in self.names.iter_mut().filter(|(n, _)| *n == sym) {
                    s.seed(prev_close, reg, &bars);
                }
            }
            Event::Bar { sym, bar } => {
                for (_, s) in self.names.iter_mut().filter(|(n, _)| *n == sym) {
                    s.apply(bar);
                }
            }
            Event::Status { live, msg } => {
                self.live = live;
                self.status = msg;
            }
            Event::Error { sym, msg } => {
                self.status = format!("{sym}: {msg}");
            }
        }
        self.update_gate();
    }

    /// Latch the gate on the first all-up observation; clear it as soon as a name drops back.
    fn update_gate(&mut self) {
        let rows = self.rows();
        match (all_up(&rows), self.gate_at) {
            (true, None) => self.gate_at = rows.iter().filter_map(|r| r.t).max(),
            (false, Some(_)) => self.gate_at = None,
            _ => {}
        }
    }

    fn gate_line(&self) -> Line<'static> {
        let t = &self.theme;
        let rows = self.rows();
        let total = rows.len();
        let up = rows.iter().filter(|r| r.up() == Some(true)).count();
        if let Some(at) = self.gate_at {
            let clock = self.names[0].1.label(at);
            Line::from(vec![
                Span::styled(
                    format!(" ALL UP {up}/{total} "),
                    Style::new().fg(t.up).bold(),
                ),
                Span::styled(format!("as of {clock} ET"), Style::new().fg(t.fg)),
            ])
        } else {
            let waiting = rows.iter().filter(|r| r.up().is_none()).count();
            let note = if waiting > 0 {
                format!("  ({waiting} waiting for data)")
            } else {
                String::new()
            };
            Line::from(vec![
                Span::styled(format!(" {up}/{total} up "), Style::new().fg(t.fg).bold()),
                Span::styled(format!("gate not yet{note}"), Style::new().fg(t.dim)),
            ])
        }
    }

    fn table(&self) -> Vec<Line<'static>> {
        let t = &self.theme;
        let mut out = vec![Line::from(Span::styled(
            format!("  {:<7}{:>11}{:>10}   {}", "SYM", "LAST", "CHG", "VWAP"),
            Style::new().fg(t.dim),
        ))];
        for (i, r) in self.rows().iter().enumerate() {
            let color = match r.up() {
                Some(true) => t.up,
                Some(false) => t.down,
                None => t.dim,
            };
            let marker = if i == self.cursor { "▸ " } else { "  " };
            let last = r.last.map_or("—".to_string(), |v| format!("{v:.2}"));
            let pct = r.pct().map_or("—".to_string(), |p| format!("{p:+.2}%"));
            let vwap = match (r.last, r.vwap) {
                (Some(l), Some(v)) if l > v => format!("above {v:.2}"),
                (Some(_), Some(v)) => format!("below {v:.2}"),
                _ => "—".to_string(),
            };
            let mut style = Style::new().fg(color);
            if i == self.cursor {
                style = style.bold();
            }
            out.push(Line::from(Span::styled(
                format!("{marker}{:<7}{:>11}{:>10}   {vwap}", r.sym, last, pct),
                style,
            )));
        }
        out
    }

    fn selected_sym(&self) -> Option<String> {
        self.names.get(self.cursor).map(|(s, _)| s.clone())
    }

    fn move_cursor(&mut self, delta: isize) {
        let len = self.names.len() as isize;
        if len > 0 {
            self.cursor = (self.cursor as isize + delta).rem_euclid(len) as usize;
        }
    }
}

impl Screen for Breadth {
    fn draw(&mut self, frame: &mut Frame) {
        self.changed = false;
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        let [header, gate, body, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(1),
            Constraint::Min(3),
            Constraint::Length(1),
        ])
        .areas(area);

        let dot = if self.live {
            Span::styled("● live", Style::new().fg(t.up))
        } else {
            Span::styled("○ offline", Style::new().fg(t.down))
        };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" BREADTH ", Style::new().fg(t.accent).bold()),
                dot,
                Span::styled(format!("  {}", self.status), Style::new().fg(t.dim)),
            ])),
            header,
        );
        frame.render_widget(Paragraph::new(self.gate_line()), gate);
        frame.render_widget(Paragraph::new(self.table()), body);
        if self.help {
            help::render_overlay(frame, area, "breadth", KEYS, &t);
        } else {
            help::render_footer(frame, footer, KEYS, self.flash.as_deref(), &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            self.changed = true;
            return Action::None;
        }
        self.changed = true;
        self.flash = None;
        match key.code {
            KeyCode::Char('j') | KeyCode::Down => self.move_cursor(1),
            KeyCode::Char('k') | KeyCode::Up => self.move_cursor(-1),
            KeyCode::Char('n') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.move_cursor(1)
            }
            KeyCode::Char('p') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                self.move_cursor(-1)
            }
            KeyCode::Char('r') => {
                let syms: Vec<String> = self.names.iter().map(|(s, _)| s.clone()).collect();
                self.stream.resync(&syms);
                self.flash = Some("resync sent".into());
            }
            KeyCode::Char('?') => self.help = true,
            KeyCode::Enter => {
                if let Some(sym) = self.selected_sym() {
                    // Intraday pads its tiles from its own defaults, so the chosen name comes first.
                    let basket: Vec<String> = std::iter::once(sym.clone())
                        .chain(
                            self.names
                                .iter()
                                .map(|(s, _)| s.clone())
                                .filter(|s| *s != sym),
                        )
                        .collect();
                    return Action::Route(Route::Screen {
                        screen: "intraday".into(),
                        arg: Some(basket.join(",")),
                    });
                }
            }
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            _ => {}
        }
        Action::None
    }

    fn tick(&mut self) -> Action {
        let events: Vec<Event> = self.stream.rx.try_iter().collect();
        for ev in events {
            self.handle(ev);
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.changed = true;
        self.flash = Some(msg);
    }

    fn needs_redraw(&self) -> bool {
        self.changed
    }
}

#[cfg(test)]
mod tests {
    use super::super::data::Bar1;
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    // 2026-10-14 09:30 EDT
    const OPEN: i64 = 1_791_984_600;

    fn row(sym: &str, last: f64, prev: f64) -> Row {
        Row {
            sym: sym.into(),
            last: Some(last),
            prev: Some(prev),
            vwap: Some(prev),
            t: Some(OPEN),
        }
    }

    fn bar(t: i64, c: f64) -> Bar1 {
        Bar1 {
            t,
            o: c,
            h: c,
            l: c,
            c,
            v: 100,
        }
    }

    fn screen(basket: &[&str]) -> (Breadth, std::sync::mpsc::Sender<Event>) {
        let (stream, tx) = Stream::detached();
        let syms = basket.iter().map(|s| s.to_string()).collect();
        (Breadth::new(Theme::default(), syms, stream), tx)
    }

    fn render(s: &mut Breadth, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| s.draw(f)).unwrap();
        let b = t.backend().buffer();
        (0..b.area.height)
            .map(|y| {
                (0..b.area.width)
                    .map(|x| b[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn feed(tx: &std::sync::mpsc::Sender<Event>, sym: &str, prev: f64, last: f64, t: i64) {
        tx.send(Event::Seed {
            sym: sym.into(),
            prev_close: Some(prev),
            reg: None,
            bars: vec![bar(t, last)],
        })
        .unwrap();
    }

    #[test]
    fn basket_defaults_dedupes_and_keeps_order() {
        assert_eq!(parse_basket(None), ["SOXX", "QQQ", "SPY", "DRAM", "NVDA"]);
        assert_eq!(
            parse_basket(Some("amd, qqq ,AMD nvda")),
            ["AMD", "QQQ", "NVDA"]
        );
        assert_eq!(parse_basket(Some("  ")).len(), 5);
    }

    #[test]
    fn gate_needs_every_name_known_and_up() {
        assert!(all_up(&[row("A", 2.0, 1.0), row("B", 3.0, 2.0)]));
        // equal to prev close is not up
        assert!(!all_up(&[row("A", 2.0, 1.0), row("B", 2.0, 2.0)]));
        // one without data blocks the gate
        let missing = Row {
            sym: "C".into(),
            last: None,
            prev: None,
            vwap: None,
            t: None,
        };
        assert!(!all_up(&[row("A", 2.0, 1.0), missing]));
        assert!(!all_up(&[]));
    }

    #[test]
    fn gate_latches_on_all_up_and_clears_when_one_drops() {
        let (mut b, tx) = screen(&["SOXX", "QQQ", "NVDA"]);
        feed(&tx, "SOXX", 100.0, 101.0, OPEN);
        feed(&tx, "QQQ", 100.0, 101.0, OPEN);
        b.tick();
        assert_eq!(b.gate_at, None, "NVDA has no data yet");

        feed(&tx, "NVDA", 200.0, 205.0, OPEN + 120);
        b.tick();
        assert_eq!(b.gate_at, Some(OPEN + 120));

        // a later, higher print does not move the latched time
        tx.send(Event::Bar {
            sym: "QQQ".into(),
            bar: bar(OPEN + 300, 102.0),
        })
        .unwrap();
        b.tick();
        assert_eq!(b.gate_at, Some(OPEN + 120));

        // one name slips back below its close: gate off
        tx.send(Event::Bar {
            sym: "SOXX".into(),
            bar: bar(OPEN + 360, 99.0),
        })
        .unwrap();
        b.tick();
        assert_eq!(b.gate_at, None);
    }

    #[test]
    fn renders_rows_and_gate_count() {
        let (mut b, tx) = screen(&["SOXX", "QQQ", "NVDA"]);
        feed(&tx, "SOXX", 100.0, 101.5, OPEN);
        feed(&tx, "QQQ", 100.0, 99.0, OPEN);
        b.tick();
        let out = render(&mut b, 80, 12);
        assert!(out.contains("SOXX"), "{out}");
        assert!(out.contains("+1.50%"), "{out}");
        assert!(out.contains("-1.00%"), "{out}");
        assert!(out.contains("1/3 up"), "{out}");
        assert!(out.contains("waiting for data"), "{out}");
    }

    #[test]
    fn enter_opens_intraday_with_selected_name_first() {
        let (mut b, _tx) = screen(&["SOXX", "QQQ", "NVDA"]);
        b.move_cursor(2);
        let act = b.on_key(KeyEvent::new(KeyCode::Enter, KeyModifiers::NONE));
        assert_eq!(
            act,
            Action::Route(Route::Screen {
                screen: "intraday".into(),
                arg: Some("NVDA,SOXX,QQQ".into()),
            })
        );
    }
}
