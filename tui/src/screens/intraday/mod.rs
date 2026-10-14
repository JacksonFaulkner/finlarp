// Intraday screen: a 2x2 grid of horizontal candle tapes (one row per bar,
// newest at the bottom) fed live by py/sources/intraday_stream.py.
//
//   fl intraday MKSI,WDC,WULF,APLD     (missing slots fall back to SPY QQQ NVDA AAPL)
//
// The feed delivers 1-minute bars; 5m / 15m are aggregated here, so the
// interval key never touches the network. Each tile shows VWAP (accent line),
// the previous close (dotted line), session volume, and dims pre/post-market.

mod data;
mod stream;

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph};

use crate::app::{Action, Ctx, Screen};
use crate::ui::hcandles::{HBar, HCandles};
use crate::ui::help::{self, Key, key};
use crate::ui::text;
use crate::ui::theme::Theme;

use data::{STEPS, Series};
use stream::{Event, Stream};

const TILES: usize = 4;
const DEFAULTS: [&str; TILES] = ["SPY", "QQQ", "NVDA", "AAPL"];

const KEYS: &[Key] = &[
    key("hjkl", "move between tiles"),
    key("J/K", "move cursor down / up"),
    key("tab/1-4", "focus tile"),
    key("G", "follow latest"),
    key("i", "interval 1m/5m/15m"),
    key("e", "pre/post-market"),
    key("↵/z", "full screen tile"),
    key("esc", "back to grid"),
    key("s", "set ticker"),
    key("r", "resync"),
    key("?", "help"),
    key("q", "close"),
];

struct Tile {
    sym: String,
    series: Series,
    /// Index into the aggregated bars; None follows the latest bar.
    cursor: Option<usize>,
    /// Bars hidden past the newest edge of the window (0 = pinned to latest).
    end_off: usize,
    /// Rows the last draw could show, so cursor moves know the window size.
    rows: usize,
    err: Option<String>,
}

impl Tile {
    fn new(sym: String) -> Self {
        Self {
            sym,
            series: Series::default(),
            cursor: None,
            end_off: 0,
            rows: 20,
            err: None,
        }
    }
}

pub struct Intraday {
    theme: Theme,
    stream: Stream,
    tiles: Vec<Tile>,
    focus: usize,
    step: usize,
    ext: bool,
    zoom: bool,
    live: bool,
    status: String,
    help: bool,
    /// Ticker being typed for the focused tile.
    prompt: Option<String>,
    flash: Option<String>,
}

/// `A,B C` -> four uppercase symbols, deduped, padded from DEFAULTS.
fn parse_symbols(arg: Option<&str>) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    let given = arg
        .unwrap_or("")
        .split([',', ' '])
        .map(|s| s.trim().to_uppercase());
    for s in given.chain(DEFAULTS.iter().map(|s| s.to_string())) {
        if !s.is_empty() && !out.contains(&s) {
            out.push(s);
        }
    }
    out.truncate(TILES);
    out
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Intraday> {
    Ok(Intraday::new(
        ctx.theme,
        parse_symbols(arg.as_deref()),
        Stream::spawn(),
    ))
}

impl Intraday {
    fn new(theme: Theme, symbols: Vec<String>, mut stream: Stream) -> Self {
        stream.set_symbols(&symbols);
        Self {
            theme,
            stream,
            tiles: symbols.into_iter().map(Tile::new).collect(),
            focus: 0,
            step: 1,
            ext: false,
            zoom: false,
            live: false,
            status: "connecting…".into(),
            help: false,
            prompt: None,
            flash: None,
        }
    }

    fn symbols(&self) -> Vec<String> {
        self.tiles.iter().map(|t| t.sym.clone()).collect()
    }

    fn handle(&mut self, ev: Event) {
        match ev {
            Event::Seed {
                sym,
                prev_close,
                reg,
                bars,
            } => {
                for t in self.tiles.iter_mut().filter(|t| t.sym == sym) {
                    t.series.seed(prev_close, reg, &bars);
                    t.err = None;
                }
            }
            Event::Bar { sym, bar } => {
                for t in self.tiles.iter_mut().filter(|t| t.sym == sym) {
                    t.series.apply(bar);
                }
            }
            Event::Status { live, msg } => {
                self.live = live;
                self.status = msg;
            }
            Event::Error { sym, msg } => {
                for t in self.tiles.iter_mut().filter(|t| t.sym == sym) {
                    t.err = Some(msg.clone());
                }
            }
        }
    }

    fn bars(&self, tile: &Tile) -> Vec<HBar> {
        tile.series.aggregate(STEPS[self.step], self.ext)
    }

    /// (start, end) of the visible window over `len` aggregated bars.
    fn window(tile: &Tile, len: usize, rows: usize) -> (usize, usize) {
        let end = len - tile.end_off.min(len.saturating_sub(rows.min(len)));
        (end.saturating_sub(rows), end)
    }

    fn move_cursor(&mut self, delta: isize) {
        let step = self.step;
        let ext = self.ext;
        let tile = &mut self.tiles[self.focus];
        let len = tile.series.aggregate(STEPS[step], ext).len();
        if len == 0 {
            return;
        }
        let cur = tile.cursor.unwrap_or(len - 1).min(len - 1);
        let new = cur.saturating_add_signed(delta).min(len - 1);
        let (start, end) = Self::window(tile, len, tile.rows);
        if new < start {
            tile.end_off += start - new;
        } else if new >= end {
            tile.end_off = tile.end_off.saturating_sub(new + 1 - end);
        }
        if new == len - 1 {
            tile.cursor = None;
            tile.end_off = 0;
        } else {
            tile.cursor = Some(new);
        }
    }

    /// Move tile focus on the 2x2 grid (row-major); stops at the edges.
    fn move_focus(&mut self, drow: isize, dcol: isize) {
        let (r, c) = (self.focus / 2, self.focus % 2);
        let r = r.saturating_add_signed(drow).min(1);
        let c = c.saturating_add_signed(dcol).min(1);
        self.focus = (r * 2 + c).min(self.tiles.len() - 1);
    }

    fn follow_latest(&mut self) {
        let t = &mut self.tiles[self.focus];
        t.cursor = None;
        t.end_off = 0;
    }

    fn set_ticker(&mut self, sym: String) {
        let t = &mut self.tiles[self.focus];
        t.sym = sym;
        t.series.clear();
        t.cursor = None;
        t.end_off = 0;
        t.err = None;
        let syms = self.symbols();
        self.stream.set_symbols(&syms);
    }

    fn readout(&self, bars: &[HBar], sel: Option<usize>, prev_close: Option<f64>) -> Line<'static> {
        let t = &self.theme;
        let dim = Style::new().fg(t.dim);
        let i = sel.unwrap_or(bars.len().saturating_sub(1));
        let Some(b) = bars.get(i) else {
            return Line::default();
        };
        let base = if i > 0 {
            Some(bars[i - 1].close)
        } else {
            prev_close
        };
        let chg = base.map(|p| (b.close / p - 1.0) * 100.0);
        let color = if b.is_up() { t.up } else { t.down };
        let mut spans = vec![
            Span::styled(format!("{} ", b.label), Style::new().fg(t.accent)),
            Span::raw(format!(
                "O {:.2} H {:.2} L {:.2} C {:.2} ",
                b.open, b.high, b.low, b.close
            )),
        ];
        if let Some(c) = chg {
            spans.push(Span::styled(format!("{c:+.2}% "), Style::new().fg(color)));
        }
        spans.push(Span::styled(
            format!("v {}", text::fmt_num(b.volume as f64)),
            dim,
        ));
        Line::from(spans)
    }

    fn draw_tile(&mut self, frame: &mut Frame, area: Rect, idx: usize) {
        let t = self.theme;
        let focused = idx == self.focus;
        let bars = self.bars(&self.tiles[idx]);
        let tile = &self.tiles[idx];
        let last = bars
            .last()
            .map(|b| b.close)
            .or_else(|| tile.series.last_close());
        let pct = last
            .zip(tile.series.prev_close)
            .map(|(l, p)| (l / p - 1.0) * 100.0);
        let mut title = vec![Span::styled(
            format!(" {} ", tile.sym),
            Style::new().fg(t.accent).bold(),
        )];
        if let Some(l) = last {
            title.push(Span::raw(format!("{l:.2} ")));
        }
        if let Some(p) = pct {
            title.push(Span::styled(
                format!("{p:+.2}% "),
                Style::new().fg(if p >= 0.0 { t.up } else { t.down }),
            ));
        }
        title.push(Span::styled(
            format!("{}m ", STEPS[self.step]),
            Style::new().fg(t.dim),
        ));
        let border = if focused { t.accent() } else { t.border() };
        let block = Block::default()
            .borders(Borders::ALL)
            .border_style(border)
            .title(Line::from(title));
        let inner = block.inner(area);
        frame.render_widget(block, area);
        if inner.height < 3 {
            return;
        }
        let [head, chart] =
            Layout::vertical([Constraint::Length(1), Constraint::Min(2)]).areas(inner);

        if bars.is_empty() {
            let msg = match &tile.err {
                Some(e) => Line::styled(
                    text::truncate(e, inner.width as usize),
                    Style::new().fg(t.down),
                ),
                None => Line::styled("loading…", Style::new().fg(t.dim)),
            };
            frame.render_widget(Paragraph::new(msg), head);
            return;
        }

        let rows = HCandles::capacity(chart.height);
        let (start, end) = Self::window(tile, bars.len(), rows);
        let visible = &bars[start..end];
        let sel_abs = tile.cursor.map(|c| c.min(bars.len() - 1));
        let sel = sel_abs
            .filter(|c| (start..end).contains(c))
            .map(|c| c - start);
        frame.render_widget(
            Paragraph::new(self.readout(&bars, sel_abs, tile.series.prev_close)),
            head,
        );
        frame.render_widget(
            HCandles::new(visible, &t)
                .vwap(tile.series.vwap())
                .prev_close(tile.series.prev_close)
                .selected(sel),
            chart,
        );
        self.tiles[idx].rows = rows;
    }

    fn header(&self) -> Line<'static> {
        let t = &self.theme;
        let dim = Style::new().fg(t.dim);
        let dot = if self.live {
            Span::styled("● live", Style::new().fg(t.up))
        } else {
            Span::styled("○ offline", Style::new().fg(t.down))
        };
        Line::from(vec![
            Span::styled(" INTRADAY ", Style::new().fg(t.accent).bold()),
            Span::styled(
                format!(
                    " {}m · {} ",
                    STEPS[self.step],
                    if self.ext {
                        "pre/post on"
                    } else {
                        "regular hours"
                    }
                ),
                dim,
            ),
            dot,
            Span::styled(format!("  {}", self.status), dim),
        ])
    }

    fn prompt_key(&mut self, key: KeyEvent) -> Action {
        let Some(buf) = self.prompt.as_mut() else {
            return Action::None;
        };
        match key.code {
            KeyCode::Esc => self.prompt = None,
            KeyCode::Enter => {
                let sym = buf.trim().to_uppercase();
                self.prompt = None;
                if !sym.is_empty() {
                    self.set_ticker(sym);
                }
            }
            KeyCode::Backspace => {
                buf.pop();
            }
            KeyCode::Char(c) if !key.modifiers.contains(KeyModifiers::CONTROL) => {
                if buf.len() < 12 {
                    buf.push(c);
                }
            }
            _ => {}
        }
        Action::None
    }
}

impl Screen for Intraday {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        let [header, grid, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(4),
            Constraint::Length(1),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(self.header()), header);

        if self.zoom {
            self.draw_tile(frame, grid, self.focus);
        } else {
            let rows = Layout::vertical([Constraint::Percentage(50), Constraint::Percentage(50)])
                .split(grid);
            for (r, row) in rows.iter().enumerate() {
                let cols =
                    Layout::horizontal([Constraint::Percentage(50), Constraint::Percentage(50)])
                        .split(*row);
                for (c, cell) in cols.iter().enumerate() {
                    let idx = r * 2 + c;
                    if idx < self.tiles.len() {
                        self.draw_tile(frame, *cell, idx);
                    }
                }
            }
        }

        if let Some(buf) = &self.prompt {
            let line = Line::from(vec![
                Span::styled(" ticker for tile ", Style::new().fg(t.dim)),
                Span::styled(format!("{}", self.focus + 1), Style::new().fg(t.accent)),
                Span::raw(format!(": {buf}▏")),
            ]);
            frame.render_widget(Paragraph::new(line), footer);
        } else {
            help::render_footer(frame, footer, KEYS, self.flash.as_deref(), &t);
        }
        if self.help {
            help::render_overlay(frame, area, "intraday", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.prompt.is_some() {
            return self.prompt_key(key);
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        self.flash = None;
        let n = self.tiles.len();
        match key.code {
            KeyCode::Char('q') => return Action::Quit,
            KeyCode::Esc if self.zoom => self.zoom = false,
            KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Tab => self.focus = (self.focus + 1) % n,
            KeyCode::BackTab => self.focus = (self.focus + n - 1) % n,
            KeyCode::Char(c @ '1'..='4') => self.focus = (c as usize - '1' as usize).min(n - 1),
            KeyCode::Char('h') | KeyCode::Left => self.move_focus(0, -1),
            KeyCode::Char('l') | KeyCode::Right => self.move_focus(0, 1),
            KeyCode::Char('k') => self.move_focus(-1, 0),
            KeyCode::Char('j') => self.move_focus(1, 0),
            KeyCode::Char('J') | KeyCode::Down => self.move_cursor(1),
            KeyCode::Char('K') | KeyCode::Up => self.move_cursor(-1),
            KeyCode::Char('d') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                let half = (self.tiles[self.focus].rows / 2).max(1) as isize;
                self.move_cursor(half);
            }
            KeyCode::Char('u') if key.modifiers.contains(KeyModifiers::CONTROL) => {
                let half = (self.tiles[self.focus].rows / 2).max(1) as isize;
                self.move_cursor(-half);
            }
            KeyCode::Char('G') => self.follow_latest(),
            KeyCode::Char('i') => self.step = (self.step + 1) % STEPS.len(),
            KeyCode::Char('e') => self.ext = !self.ext,
            KeyCode::Enter => self.zoom = true,
            KeyCode::Char('z') => self.zoom = !self.zoom,
            KeyCode::Char('s') => self.prompt = Some(String::new()),
            KeyCode::Char('r') => {
                let syms = self.symbols();
                self.stream.resync(&syms);
                self.flash = Some("resyncing…".into());
            }
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
        self.flash = Some(msg);
    }

    fn leader_ok(&self) -> bool {
        self.prompt.is_none()
    }
}

#[cfg(test)]
mod tests;
