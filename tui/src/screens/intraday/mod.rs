// Intraday screen: a 2x2 grid of horizontal candle tapes (one row per bar,
// newest at the bottom) fed live by py/sources/intraday_stream.py.
//
//   fl intraday MKSI,WDC,WULF,APLD     (missing slots fall back to SPY QQQ NVDA AAPL)
//
// The feed delivers 1-minute bars; 5m / 15m are aggregated here, so the
// interval key never touches the network. Each tile shows VWAP (accent line),
// the previous close (dotted line), session volume, and dims pre/post-market.

mod data;
mod picture;
mod stream;

use std::hash::{Hash, Hasher};
use std::io;
use std::rc::Rc;
use std::time::{Duration, Instant};

use image::{DynamicImage, RgbaImage};
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Style;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui_image::picker::cap_parser::QueryStdioOptions;
use ratatui_image::picker::{Capability, Picker, ProtocolType};
use ratatui_image::protocol::kitty::StatefulKitty;
use ratatui_image::protocol::{StatefulProtocol, StatefulProtocolType};
use ratatui_image::{Resize, StatefulImage};

use crate::app::{Action, Ctx, Screen};
use crate::ui::hcandles::{HBar, HCandles};
use crate::ui::help::{self, Key, key};
use crate::ui::pixels::Palette;
use crate::ui::text;
use crate::ui::theme::Theme;

use data::{STEPS, Series};
use stream::{Event, Stream};

const TILES: usize = 4;
const DEFAULTS: [&str; TILES] = ["SPY", "QQQ", "NVDA", "AAPL"];

const KEYS: &[Key] = &[
    key("hjkl", "move between tiles"),
    key("H/L", "cursor back / forward"),
    key("J/K", "cursor down / up (tapes)"),
    key("tab/1-4", "focus tile"),
    key("G", "follow latest"),
    key("i", "interval 1m/5m/15m"),
    key("e", "pre/post-market"),
    key("g", "pictures / ascii tapes"),
    key("↵/z", "full screen tile"),
    key("esc", "back to grid"),
    key("s", "set ticker"),
    key("r", "resync"),
    key("?", "help"),
    key("q", "close"),
];

/// A tile's picture as last sent. Resending one costs ~1.5 MB of escapes through tmux, so
/// the cursor is drawn as a text row under it (never in it) and live ticks resend at most
/// once per `LIVE_REFRESH`; a change of shape (size, window, interval) resends at once.
/// `key` is the raster's identity (see `raster_key`): same key, same pixels, same protocol.
struct PicSlot {
    key: u64,
    shape: u64,
    sent: Instant,
    proto: StatefulProtocol,
}

const LIVE_REFRESH: Duration = Duration::from_secs(1);

struct Tile {
    sym: String,
    series: Series,
    /// The last picture sent to the terminal.
    pic: Option<PicSlot>,
    /// Index into the aggregated bars; None follows the latest bar.
    cursor: Option<usize>,
    /// Bars hidden past the newest edge of the window (0 = pinned to latest).
    end_off: usize,
    /// Rows the last draw could show, so cursor moves know the window size.
    rows: usize,
    err: Option<String>,
    /// The buffer pictures are rendered into; reused across redraws of this tile.
    scratch: RgbaImage,
}

impl Tile {
    fn new(sym: String) -> Self {
        Self {
            sym,
            series: Series::default(),
            pic: None,
            cursor: None,
            end_off: 0,
            rows: 20,
            err: None,
            scratch: RgbaImage::new(1, 1),
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
    /// The terminal's graphics protocol, when it has one (None: ASCII tapes only).
    picker: Option<Picker>,
    /// Draw tiles as pictures (only ever true with a picker). `g` flips it.
    pictures: bool,
    /// Something changed since the last draw (feed event, key, flash): see `needs_redraw`.
    changed: bool,
    /// A picture changed but is waiting out its `LIVE_REFRESH`, so it needs another draw.
    deferred: bool,
    /// Cursor steps from keys since the last draw; applied once, in `draw`.
    pending_cursor: isize,
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
    // Must run before the event loop reads stdin: the terminal answers the query on stdin.
    // Halfblocks is no graphics protocol at all, so the ASCII tapes stay.
    // A picture re-sent through tmux is ~1.5 MB of raw RGBA as base64, but these flat-colour
    // charts deflate ~50x, so zlib is the default (ratatui-image deflates at level 1). Shared
    // memory sends only a name. The picker uses whichever the terminal answers OK to.
    // FL_KITTY=raw|shm opts out (raw: no compression, shm: shared memory).
    let mode = std::env::var("FL_KITTY").unwrap_or_default();
    let options = QueryStdioOptions {
        kitty_compression: !matches!(mode.as_str(), "raw" | "shm"),
        kitty_shared_memory_object: (mode == "shm")
            .then(QueryStdioOptions::probe_kitty_smo)
            .flatten(),
        ..Default::default()
    };
    let picker = Picker::from_query_stdio_with_options(options)
        .ok()
        .filter(|p| p.protocol_type() != ProtocolType::Halfblocks);
    let mut screen = Intraday::new(ctx.theme, parse_symbols(arg.as_deref()), Stream::spawn());
    screen.pictures = picker.is_some();
    screen.picker = picker;
    Ok(screen)
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
            picker: None,
            pictures: false,
            changed: true,
            deferred: false,
            pending_cursor: 0,
        }
    }

    fn symbols(&self) -> Vec<String> {
        self.tiles.iter().map(|t| t.sym.clone()).collect()
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

    fn bars(&self, tile: &Tile) -> Rc<Vec<HBar>> {
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
        // Crossing an edge jumps the view half a screen (or as far as the cursor needs), so
        // the cursor is not on the edge again after the next step.
        let page = (tile.rows / 2).max(1);
        let (start, end) = Self::window(tile, len, tile.rows);
        if new < start {
            tile.end_off += (start - new).max(page);
        } else if new >= end {
            tile.end_off = tile.end_off.saturating_sub((new + 1 - end).max(page));
        }
        // A jump bigger than a screen can still leave the cursor out of view: show it as the newest bar.
        let (start, end) = Self::window(tile, len, tile.rows);
        if !(start..end).contains(&new) {
            tile.end_off = len - (new + 1);
        }
        if new == len - 1 {
            tile.cursor = None;
            tile.end_off = 0;
        } else {
            tile.cursor = Some(new);
        }
    }

    /// Applies the cursor steps keys accumulated since the last draw, as one move.
    fn apply_pending_cursor(&mut self) {
        let d = std::mem::take(&mut self.pending_cursor);
        if d != 0 {
            self.move_cursor(d);
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
                // Data arrived but none of it is in the regular session yet (pre-market).
                None if !tile.series.is_empty() => Line::styled(
                    "no regular-session bars yet · e shows pre/post-market",
                    Style::new().fg(t.dim),
                ),
                None => Line::styled("loading…", Style::new().fg(t.dim)),
            };
            frame.render_widget(Paragraph::new(msg), head);
            return;
        }

        // Pictures fit as many bars as the chart's pixels allow; tapes one per row.
        let picker = if self.pictures {
            self.picker.as_ref()
        } else {
            None
        };
        let rows = match picker {
            Some(p) => picture::capacity(chart.width as u32 * u32::from(p.font_size().width)),
            None => HCandles::capacity(chart.height),
        };
        let (start, end) = Self::window(tile, bars.len(), rows);
        let visible = &bars[start..end];
        let sel_abs = tile.cursor.map(|c| c.min(bars.len() - 1));
        let sel = sel_abs
            .filter(|c| (start..end).contains(c))
            .map(|c| c - start);
        let (vwap, prev_close) = (tile.series.vwap(), tile.series.prev_close);
        let version = tile.series.version();
        frame.render_widget(
            Paragraph::new(self.readout(&bars, sel_abs, prev_close)),
            head,
        );
        match picker {
            Some(p) => {
                let font = p.font_size();
                let [img, marks] =
                    Layout::vertical([Constraint::Min(1), Constraint::Length(1)]).areas(chart);
                let px = (
                    img.width as u32 * u32::from(font.width),
                    img.height as u32 * u32::from(font.height),
                );
                let pic = picture::Pic {
                    bars: visible,
                    vwap,
                    prev_close,
                    sel: None,
                };
                let pal = Palette::from_theme(&self.theme);
                let key = raster_key(version, STEPS[self.step], self.ext, (start, end), px, &pal);
                let shape = shape_key(px, visible);
                let id = tile_image_id(idx);
                let deferred = draw_picture(
                    frame,
                    img,
                    &mut self.tiles[idx],
                    p,
                    id,
                    &pic,
                    &pal,
                    px,
                    key,
                    shape,
                );
                self.deferred |= deferred;
                if let Some(s) = sel {
                    frame.render_widget(
                        cursor_row(s, visible.len(), px.0, font.width, &t),
                        marks,
                    );
                }
            }
            None => frame.render_widget(
                HCandles::new(visible, &t)
                    .vwap(vwap)
                    .prev_close(prev_close)
                    .selected(sel),
                chart,
            ),
        }
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

/// What the picture is laid out over: its pixel size and which bars it spans. A change here
/// resends at once; a change in the bars' values alone (live ticks) waits for `LIVE_REFRESH`.
fn shape_key(px: (u32, u32), bars: &[HBar]) -> u64 {
    use std::hash::{Hash, Hasher};
    let mut h = std::collections::hash_map::DefaultHasher::new();
    px.hash(&mut h);
    bars.len().hash(&mut h);
    bars.first().map(|b| &b.label).hash(&mut h);
    bars.last().map(|b| &b.label).hash(&mut h);
    h.finish()
}

/// `▲` under the cursor bar, in the cell column its candle is drawn in.
fn cursor_row(sel: usize, n: usize, px_w: u32, font_w: u16, t: &Theme) -> Paragraph<'static> {
    let slot = px_w as f64 / n.max(1) as f64;
    let col = (((sel as f64 + 0.5) * slot) / f64::from(font_w.max(1))) as usize;
    Paragraph::new(Line::from(vec![
        Span::raw(" ".repeat(col)),
        Span::styled("▲", Style::new().fg(t.accent).bold()),
    ]))
}

/// Identity of one tile's raster: the data version, the bars it spans, its pixel size and
/// the palette. Equal keys mean equal pixels, so the picture already sent still stands; the
/// cursor is not in it (it is a text row), so cursor moves never change the key.
fn raster_key(
    version: u64,
    step: i64,
    ext: bool,
    span: (usize, usize),
    px: (u32, u32),
    pal: &Palette,
) -> u64 {
    let mut h = std::collections::hash_map::DefaultHasher::new();
    (version, step, ext, span, px, pal).hash(&mut h);
    h.finish()
}

/// Kitty image id for a tile. Stable, so re-sending a tile's picture replaces the image the
/// terminal holds for it instead of adding another one (ratatui-image's own protocols take a
/// random id per send, and expose no way to delete the old image).
fn tile_image_id(idx: usize) -> u32 {
    u32::from_be_bytes([0, 0xF1, 0xDA, idx as u8 + 1])
}

/// One protocol per picture. Kitty gets the tile's stable id; other protocols use ratatui-image's.
fn picture_protocol(picker: &Picker, img: DynamicImage, id: u32) -> StatefulProtocol {
    if picker.protocol_type() != ProtocolType::Kitty {
        return picker.new_resize_protocol(img);
    }
    let caps = picker.capabilities();
    StatefulProtocol::new(
        img,
        picker.font_size(),
        None,
        StatefulProtocolType::Kitty(StatefulKitty::new(
            id,
            picker.tmux_detected(),
            caps.contains(&Capability::KittyCompression),
            caps.contains(&Capability::KittySharedMemory),
        )),
    )
}

/// Draws one tile's picture. The protocol is rebuilt only when the raster key changes, and
/// then at most once per `LIVE_REFRESH` unless the shape changed (see `PicSlot`). Returns true
/// when a changed picture is waiting out that interval, so the screen must draw again.
#[allow(clippy::too_many_arguments)]
fn draw_picture(
    frame: &mut Frame,
    area: Rect,
    tile: &mut Tile,
    picker: &Picker,
    id: u32,
    pic: &picture::Pic,
    pal: &Palette,
    px: (u32, u32),
    key: u64,
    shape: u64,
) -> bool {
    let stale = tile.pic.as_ref().is_none_or(|s| s.key != key);
    let resend = stale
        && tile
            .pic
            .as_ref()
            .is_none_or(|s| s.shape != shape || s.sent.elapsed() >= LIVE_REFRESH);
    let deferred = stale && !resend;
    if resend {
        let (w, h) = (px.0.max(1), px.1.max(1));
        if tile.scratch.dimensions() != (w, h) {
            tile.scratch = RgbaImage::new(w, h);
        }
        picture::render_into(&mut tile.scratch, pic, pal);
        let img = DynamicImage::ImageRgba8(tile.scratch.clone());
        tile.pic = Some(PicSlot {
            key,
            shape,
            sent: Instant::now(),
            proto: picture_protocol(picker, img, id),
        });
    }
    if let Some(s) = tile.pic.as_mut() {
        frame.render_stateful_widget(
            StatefulImage::default().resize(Resize::Fit(None)),
            area,
            &mut s.proto,
        );
    }
    deferred
}

impl Screen for Intraday {
    fn draw(&mut self, frame: &mut Frame) {
        self.apply_pending_cursor();
        self.changed = false;
        self.deferred = false;
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
            self.changed = true;
            return Action::None;
        }
        self.changed = true;
        self.flash = None;
        // Cursor steps only accumulate here; `draw` applies them as one move. Held J/K
        // queue up while a frame draws, so a backlog costs one draw, not one per key.
        let half = (self.tiles[self.focus].rows / 2).max(1) as isize;
        let step = match key.code {
            KeyCode::Char('L') | KeyCode::Char('J') | KeyCode::Down => Some(1),
            KeyCode::Char('H') | KeyCode::Char('K') | KeyCode::Up => Some(-1),
            KeyCode::Char('d') if key.modifiers.contains(KeyModifiers::CONTROL) => Some(half),
            KeyCode::Char('u') if key.modifiers.contains(KeyModifiers::CONTROL) => Some(-half),
            _ => None,
        };
        if let Some(d) = step {
            self.pending_cursor += d;
            return Action::None;
        }
        // Any other key sees the cursor as the keys before it left it.
        self.apply_pending_cursor();
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
            KeyCode::Char('G') => self.follow_latest(),
            KeyCode::Char('i') => self.step = (self.step + 1) % STEPS.len(),
            KeyCode::Char('e') => self.ext = !self.ext,
            KeyCode::Char('g') => {
                if self.picker.is_some() {
                    self.pictures = !self.pictures;
                } else {
                    self.flash =
                        Some("this terminal has no graphics protocol: ASCII tapes only".into());
                }
            }
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
        self.changed = true;
        self.flash = Some(msg);
    }

    /// Redraws only after something changed: a feed event, a key, a flash, or a picture
    /// waiting out its live-refresh interval. (The tape still redraws every poll; see app.)
    fn needs_redraw(&self) -> bool {
        self.changed || self.deferred
    }

    fn leader_ok(&self) -> bool {
        self.prompt.is_none()
    }
}

#[cfg(test)]
mod tests;
