// Intraday screen: a 2x2 grid of horizontal candle tapes (one row per bar,
// newest at the bottom) fed live by py/sources/intraday_stream.py.
//
//   fl intraday MKSI,WDC,WULF,APLD     (missing slots fall back to SPY QQQ NVDA AAPL)
//
// The feed delivers 1-minute bars; 5m / 15m are aggregated here, so the
// interval key never touches the network. Each tile shows VWAP (accent line),
// the previous close (dotted line), session volume, and dims pre/post-market.

pub mod breadth;
pub(crate) mod data;
pub(crate) mod grid;
mod layouts;
pub(crate) mod picture;
mod stops;
pub(crate) mod stream;

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
use ratatui_image::{Resize, ResizeEncodeRender, StatefulImage};

use crate::app::{Action, Ctx, Screen};
use crate::ui::hcandles::{HBar, HCandles};
use crate::ui::help::{Help, Key, key};
use crate::ui::pixels::Palette;
use crate::ui::text;
use crate::ui::theme::Theme;

use data::{STEPS, Series};
use grid::{Cell, Change, Dir, Grid};
use stream::{Event, Stream};

const TILES: usize = 4;
const DEFAULTS: [&str; TILES] = ["SPY", "QQQ", "NVDA", "AAPL"];

const KEYS: &[Key] = &[
    key("hjkl", "move between tiles"),
    key("space w h/l", "new column left / right of the tile (same ticker; s changes it)"),
    key("space w k/j", "new row above / below the tile"),
    key("space w c", "close the tile (a side that lines up takes its place)"),
    key("f", "saved layouts: j/k pick, ↵ load, D D delete, esc close"),
    key("D", "in the layouts menu: press twice to delete"),
    key("m", "eat mode: hjkl grow the tile over its neighbours, ↵ take, esc cancel"),
    key("H/L", "cursor back / forward"),
    key("J/K", "cursor down / up (tapes)"),
    key("tab", "focus next tile (shift-tab: previous)"),
    key(
        "5L 50H 3J",
        "a count repeats a motion (digits, then the key)",
    ),
    key(
        "{ }",
        "previous / next volume spike or swing high / low (3} = third)",
    ),
    key(
        "gg/G",
        "first bar / latest bar (follow live); 50G or 50gg: bar 50",
    ),
    key("i", "interval 1m/5m/15m; in visual: zoom to the selection"),
    key("V", "visual: select bars from the cursor (H/L extend)"),
    key("e", "pre/post-market"),
    key("↵/z", "full screen tile"),
    key("esc", "leave visual / zoom out / back to grid"),
    key("s", "set ticker"),
    key("r", "resync"),
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
/// Largest count a motion takes (`99999L`): plenty for a day of 1m bars.
const MAX_COUNT: usize = 99_999;

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
    /// Visual mode: the bar `v` was pressed on (an index into the aggregated bars).
    anchor: Option<usize>,
    /// Zoomed in on bars [start, end) (`i` in visual mode); None shows the usual window.
    span: Option<(usize, usize)>,
    err: Option<String>,
    /// The buffer pictures are rendered into; reused across redraws of this tile.
    scratch: RgbaImage,
    /// Which of the tile's two image ids the next send uses (see `tile_image_id`).
    which: u8,
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
            anchor: None,
            span: None,
            err: None,
            scratch: RgbaImage::new(1, 1),
            which: 0,
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
    /// A `g` was pressed: a second one makes `gg`.
    pending_g: bool,
    /// The terminal's background colour, when it reported one: the charts' background.
    term_bg: Option<[u8; 4]>,
    /// A count being typed (`50` of `50L`), shown in the header until a key uses it.
    count: Option<usize>,
    /// Pictures the tiles laid out this frame, built together by `flush_pictures`.
    jobs: Vec<PicJob>,
    /// Where each tile sits (tiles[i] is grid.cells[i]).
    grid: Grid,
    /// Eat mode (`m`): the cells the focused tile will take on ↵.
    eat: Option<Cell>,
    /// The saved layout this screen edits (None until the first edit).
    layout_id: Option<u64>,
    /// `f`: the saved layouts, the row under the cursor, and whether `D` was pressed once.
    menu: Option<(Vec<layouts::Layout>, usize, bool)>,
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
        // the terminal's own background (OSC 11), so the charts sit on it seamlessly
        terminal_background_color_osc: true,
        ..Default::default()
    };
    let picker = Picker::from_query_stdio_with_options(options)
        .ok()
        .filter(|p| p.protocol_type() != ProtocolType::Halfblocks);
    let mut screen = Intraday::new(ctx.theme, parse_symbols(arg.as_deref()), Stream::spawn());
    screen.pictures = picker.is_some();
    // FL_CHART_BG=theme keeps the theme's chart background instead of the terminal's
    if std::env::var("FL_CHART_BG").as_deref() != Ok("theme") {
        screen.term_bg = picker.as_ref().and_then(|p| {
            p.capabilities().iter().find_map(|c| match c {
                Capability::Background(r, g, b) => Some([*r, *g, *b, 255]),
                _ => None,
            })
        });
    }
    screen.picker = picker;
    // no tickers asked for: the layout edited last comes back
    if arg.as_deref().is_none_or(|a| a.trim().is_empty()) {
        if let Some(l) = layouts::load().first() {
            screen.load_layout(l);
        }
    }
    Ok(screen)
}

impl Intraday {
    fn new(theme: Theme, symbols: Vec<String>, mut stream: Stream) -> Self {
        stream.set_symbols(&symbols);
        let grid = Grid::auto(symbols.len());
        Self {
            grid,
            eat: None,
            layout_id: None,
            menu: None,
            theme,
            stream,
            tiles: symbols.into_iter().map(Tile::new).collect(),
            focus: 0,
            step: 1,
            ext: false,
            zoom: false,
            live: false,
            status: "connecting…".into(),
            prompt: None,
            flash: None,
            picker: None,
            pictures: false,
            changed: true,
            deferred: false,
            jobs: Vec::new(),
            pending_g: false,
            term_bg: None,
            count: None,
            pending_cursor: 0,
        }
    }

    /// The tickers on screen, once each (two tiles can show the same one).
    fn symbols(&self) -> Vec<String> {
        let mut out: Vec<String> = Vec::new();
        for t in &self.tiles {
            if !out.contains(&t.sym) {
                out.push(t.sym.clone());
            }
        }
        out
    }

    /// Mirrors what a grid operation did on the tile list, then resubscribes.
    fn apply_changes(&mut self, changes: Vec<Change>) {
        for c in changes {
            match c {
                Change::Added { from } => {
                    let mut t = Tile::new(self.tiles[from].sym.clone());
                    t.series = self.tiles[from].series.clone();
                    self.tiles.push(t);
                }
                Change::Removed(i) => {
                    self.tiles.remove(i);
                    if self.focus > i {
                        self.focus -= 1;
                    }
                }
            }
        }
        self.focus = self.focus.min(self.tiles.len().saturating_sub(1));
        // every tile's picture is re-laid out; drop the old ones so none lingers
        for t in self.tiles.iter_mut() {
            t.pic = None;
        }
        let syms = self.symbols();
        self.stream.set_symbols(&syms);
        self.save_layout();
    }

    /// Saves the layout on screen (its grid and tickers) under this screen's id.
    fn save_layout(&mut self) {
        let id = *self.layout_id.get_or_insert_with(layouts::new_id);
        let syms = self.tiles.iter().map(|t| t.sym.clone()).collect();
        layouts::save(layouts::Layout::from_grid(id, &self.grid, syms));
    }

    /// Puts a saved layout on screen; later edits save back into it.
    fn load_layout(&mut self, l: &layouts::Layout) {
        if !l.valid() {
            return;
        }
        self.grid = l.grid();
        self.tiles = l.symbols.iter().cloned().map(Tile::new).collect();
        self.focus = 0;
        self.zoom = false;
        self.eat = None;
        self.layout_id = Some(l.id);
        let syms = self.symbols();
        self.stream.set_symbols(&syms);
    }

    /// Keys while the layouts menu (`f`) is open.
    fn menu_key(&mut self, key: KeyEvent) -> Action {
        let Some((list, sel, arm)) = self.menu.as_mut() else {
            return Action::None;
        };
        let last = list.len().saturating_sub(1);
        let armed = std::mem::take(arm);
        match key.code {
            KeyCode::Esc | KeyCode::Char('f') | KeyCode::Char('q') => self.menu = None,
            KeyCode::Char('j') | KeyCode::Down => *sel = (*sel + 1).min(last),
            KeyCode::Char('k') | KeyCode::Up => *sel = sel.saturating_sub(1),
            KeyCode::Char('g') => *sel = 0,
            KeyCode::Char('G') => *sel = last,
            KeyCode::Char('D') => {
                if armed {
                    if let Some(l) = list.get(*sel) {
                        layouts::delete(l.id);
                        if self.layout_id == Some(l.id) {
                            self.layout_id = None;
                        }
                        list.remove(*sel);
                        *sel = (*sel).min(list.len().saturating_sub(1));
                    }
                } else {
                    *arm = true;
                    self.flash = Some("D again deletes this layout".into());
                }
            }
            KeyCode::Enter => {
                if let Some(l) = list.get(*sel).cloned() {
                    self.menu = None;
                    self.load_layout(&l);
                }
            }
            _ => {}
        }
        Action::None
    }

    /// The `f` menu: saved layouts, newest edit first; the one on screen is marked.
    fn draw_menu(&self, frame: &mut Frame, area: Rect) {
        let Some((list, sel, _)) = &self.menu else { return };
        let t = &self.theme;
        let w = 70.min(area.width.saturating_sub(4));
        let h = (list.len() as u16 + 2).clamp(3, area.height.saturating_sub(2).max(3));
        let r = Rect::new(
            area.x + area.width.saturating_sub(w) / 2,
            area.y + area.height.saturating_sub(h) / 3,
            w,
            h,
        );
        frame.render_widget(ratatui::widgets::Clear, r);
        let lines: Vec<Line> = if list.is_empty() {
            vec![Line::styled(
                "no saved layouts yet: space w h/j/k/l, m or s save one",
                Style::new().fg(t.dim),
            )]
        } else {
            list.iter()
                .enumerate()
                .map(|(i, l)| {
                    let on = self.layout_id == Some(l.id);
                    let mark = if on { "● " } else { "  " };
                    let style = if i == *sel {
                        t.selected()
                    } else if on {
                        Style::new().fg(t.accent)
                    } else {
                        t.base()
                    };
                    Line::styled(
                        text::truncate(&format!("{mark}{}", l.label()), w as usize - 2),
                        style,
                    )
                })
                .collect()
        };
        let top = sel.saturating_sub(h.saturating_sub(3) as usize);
        frame.render_widget(
            Paragraph::new(lines.into_iter().skip(top).collect::<Vec<_>>()).block(
                Block::default()
                    .borders(Borders::ALL)
                    .border_style(Style::new().fg(t.accent))
                    .title(" layouts · ↵ load · D D delete · esc "),
            ),
            r,
        );
    }

    /// `<space>w h/j/k/l`: a new tile beside the focused one, showing the same ticker
    /// (`s` sets another).
    fn split(&mut self, d: Dir) {
        match self.grid.split(self.focus, d) {
            Some(new) => {
                self.apply_changes(vec![Change::Added { from: self.focus }]);
                self.focus = new;
            }
            None => self.flash = Some(format!("at most {} tiles", grid::MAX_TILES)),
        }
    }

    /// `<space>w c`: closes the focused tile.
    fn close_tile(&mut self) {
        match self.grid.close(self.focus) {
            Some(ch) => self.apply_changes(ch),
            None if self.tiles.len() < 2 => self.flash = Some("the last tile stays".into()),
            None => self.flash = Some("no side lines up with this tile; eat it instead (m)".into()),
        }
    }

    /// Keys in eat mode.
    fn eat_key(&mut self, key: KeyEvent) -> Action {
        let Some(t) = self.eat else {
            return Action::None;
        };
        match key.code {
            KeyCode::Esc | KeyCode::Char('m') => self.eat = None,
            KeyCode::Enter => {
                self.eat = None;
                let ch = self.grid.eat(self.focus, t);
                self.apply_changes(ch);
            }
            KeyCode::Char(c) => {
                if let Some(d) = Dir::from_key(c) {
                    self.eat = Some(self.grid.grow(t, d));
                }
            }
            KeyCode::Left => self.eat = Some(self.grid.grow(t, Dir::Left)),
            KeyCode::Right => self.eat = Some(self.grid.grow(t, Dir::Right)),
            KeyCode::Up => self.eat = Some(self.grid.grow(t, Dir::Up)),
            KeyCode::Down => self.eat = Some(self.grid.grow(t, Dir::Down)),
            _ => {}
        }
        Action::None
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
        if let Some((a, b)) = tile.span {
            let b = b.min(len);
            return (a.min(b.saturating_sub(1)), b);
        }
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
        // Zoomed: the cursor stays inside the zoomed bars and the window doesn't move.
        if tile.span.is_some() {
            let (a, b) = Self::window(tile, len, tile.rows);
            let new = new.clamp(a, b.saturating_sub(1).max(a));
            tile.cursor = if new == len - 1 { None } else { Some(new) };
            return;
        }
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

    /// Move tile focus to the neighbour in that direction; stops at the edges.
    fn move_focus(&mut self, drow: isize, dcol: isize) {
        let d = match (drow, dcol) {
            (_, c) if c < 0 => Dir::Left,
            (_, c) if c > 0 => Dir::Right,
            (r, _) if r < 0 => Dir::Up,
            _ => Dir::Down,
        };
        if let Some(i) = self.grid.neighbor(self.focus, d) {
            self.focus = i;
        }
    }

    fn follow_latest(&mut self) {
        let t = &mut self.tiles[self.focus];
        t.cursor = None;
        t.end_off = 0;
        t.anchor = None;
        t.span = None;
    }

    /// The picture palette: the theme's colours on the terminal's own background when it
    /// reported one, so a chart blends into the screen around it.
    fn palette(&self) -> Palette {
        let mut pal = Palette::from_theme(&self.theme);
        if let Some(bg) = self.term_bg {
            pal.bg = bg;
        }
        pal
    }

    /// `{` / `}`: the cursor on the previous / next stop (a volume spike or a swing high or
    /// low, see `stops`), `times` stops away.
    fn jump_stop(&mut self, forward: bool, times: usize) {
        let Some((cur, _)) = self.cursor_index() else {
            return;
        };
        let bars = self.bars(&self.tiles[self.focus]);
        if let Some(i) = stops::step(&stops::stops(&bars), cur, forward, times) {
            self.goto_bar(i);
        }
    }

    /// `50G` / `50gg`: the cursor on bar `i` (0-based) of the focused tile, clamped to it.
    fn goto_bar(&mut self, i: usize) {
        if let Some((cur, _)) = self.cursor_index() {
            self.move_cursor(i as isize - cur as isize);
        }
    }

    /// `gg`: the cursor on the first bar of the focused tile (the first zoomed bar when
    /// zoomed), the window scrolled back to it.
    fn first_bar(&mut self) {
        if let Some((cur, _)) = self.cursor_index() {
            self.move_cursor(-(cur as isize));
        }
    }

    /// The focused tile's cursor as an index into its aggregated bars (len: their count).
    fn cursor_index(&self) -> Option<(usize, usize)> {
        let tile = &self.tiles[self.focus];
        let len = self.bars(tile).len();
        (len > 0).then(|| (tile.cursor.unwrap_or(len - 1).min(len - 1), len))
    }

    /// Bar indices shift when the interval or the session filter changes: drop every
    /// selection and zoom that pointed at the old ones.
    fn forget_ranges(&mut self) {
        for t in &mut self.tiles {
            t.anchor = None;
            t.span = None;
            t.cursor = None;
            t.end_off = 0;
        }
    }

    /// `i` in visual mode: zoom the focused tile onto the selected bars.
    fn zoom_to_selection(&mut self) {
        let Some((cur, _)) = self.cursor_index() else {
            return;
        };
        let t = &mut self.tiles[self.focus];
        let Some(anchor) = t.anchor.take() else {
            return;
        };
        let (lo, hi) = (anchor.min(cur), anchor.max(cur));
        if hi > lo {
            t.span = Some((lo, hi + 1));
        } else {
            self.flash = Some("select at least two bars to zoom".into());
        }
    }

    /// The visual selection's readout: time span, move, high/low, volume.
    fn range_readout(&self, bars: &[HBar], lo: usize, hi: usize) -> Line<'static> {
        let t = &self.theme;
        let sel = &bars[lo..=hi.min(bars.len() - 1)];
        let (first, last) = (&sel[0], &sel[sel.len() - 1]);
        let pct = (last.close / first.open - 1.0) * 100.0;
        let high = sel.iter().map(|b| b.high).fold(f64::MIN, f64::max);
        let low = sel.iter().map(|b| b.low).fold(f64::MAX, f64::min);
        let vol: u64 = sel.iter().map(|b| b.volume).sum();
        let mins = sel.len() as i64 * STEPS[self.step];
        Line::from(vec![
            Span::styled("-- VISUAL -- ", Style::new().fg(t.accent).bold()),
            Span::styled(
                format!("{}→{} ", first.label, last.label),
                Style::new().fg(t.accent),
            ),
            Span::raw(format!(
                "{} bar{} {mins}m  ",
                sel.len(),
                if sel.len() == 1 { "" } else { "s" }
            )),
            Span::styled(
                format!("{pct:+.2}%  "),
                Style::new().fg(if pct >= 0.0 { t.up } else { t.down }),
            ),
            Span::raw(format!("H {high:.2} L {low:.2}  ")),
            Span::styled(
                format!("v {}", text::fmt_num(vol as f64)),
                Style::new().fg(t.dim),
            ),
        ])
    }

    fn set_ticker(&mut self, sym: String) {
        let t = &mut self.tiles[self.focus];
        t.sym = sym;
        t.series.clear();
        t.cursor = None;
        t.end_off = 0;
        t.anchor = None;
        t.span = None;
        t.err = None;
        let syms = self.symbols();
        self.stream.set_symbols(&syms);
        self.save_layout();
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
        // on a `{ }` stop: why it is one
        if sel.is_some() {
            if let Some(stop) = stops::stops(bars).into_iter().find(|s| s.idx == i) {
                spans.push(Span::styled(
                    format!("  {}", stop.label()),
                    Style::new().fg(t.accent),
                ));
            }
        }
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
        if let Some((a, b)) = tile.span {
            let label = |i: usize| bars.get(i).map_or(String::new(), |x| x.label.clone());
            title.push(Span::styled(
                format!("zoom {}–{} ", label(a), label(b.saturating_sub(1))),
                Style::new().fg(t.accent),
            ));
        }
        let border = if focused { t.accent() } else { t.border() };
        let block = Block::default()
            .borders(Borders::ALL)
            .border_style(border)
            .title(Line::from(title));
        let inner = block.inner(area);
        frame.render_widget(block, area);
        if inner.height < 2 {
            return;
        }
        // small tiles (a crowded grid) give the readout row to the chart
        let compact = inner.height < 6 || inner.width < 28;
        let [head, chart] = if compact {
            [Rect::new(inner.x, inner.y, inner.width, 0), inner]
        } else {
            Layout::vertical([Constraint::Length(1), Constraint::Min(2)]).areas(inner)
        };

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
        let anchor = tile.anchor.map(|a| a.min(bars.len() - 1));
        let cur_abs = sel_abs.unwrap_or(bars.len() - 1);
        let picked = anchor.map(|a| (a.min(cur_abs), a.max(cur_abs)));
        let readout = match picked {
            Some((lo, hi)) => self.range_readout(&bars, lo, hi),
            None => self.readout(&bars, sel_abs, prev_close),
        };
        frame.render_widget(Paragraph::new(readout), head);
        // the selection relative to the window, clipped to it
        let range = picked
            .filter(|(lo, hi)| *hi >= start && *lo < end)
            .map(|(lo, hi)| (lo.max(start) - start, hi.min(end - 1) - start));
        match picker {
            Some(p) => {
                let font = p.font_size();
                let [img, marks] =
                    Layout::vertical([Constraint::Min(1), Constraint::Length(1)]).areas(chart);
                let px = (
                    img.width as u32 * u32::from(font.width),
                    img.height as u32 * u32::from(font.height),
                );
                let pal = self.palette();
                let key = raster_key(
                    version,
                    STEPS[self.step],
                    self.ext,
                    (start, end),
                    range,
                    px,
                    &pal,
                );
                let shape = shape_key(px, visible, range);
                self.jobs.push(PicJob {
                    idx,
                    area: img,
                    bars: visible.to_vec(),
                    vwap,
                    prev_close,
                    range,
                    px,
                    key,
                    shape,
                });
                if let Some(s) = sel {
                    frame.render_widget(cursor_row(s, visible.len(), px.0, font.width, &t), marks);
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
            // what's been typed toward a command, like vim's showcmd
            Span::styled(
                format!(
                    "  {}{}",
                    self.count.map_or(String::new(), |c| c.to_string()),
                    if self.pending_g { "g" } else { "" }
                ),
                Style::new().fg(t.accent).bold(),
            ),
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
fn shape_key(px: (u32, u32), bars: &[HBar], range: Option<(usize, usize)>) -> u64 {
    use std::hash::{Hash, Hasher};
    let mut h = std::collections::hash_map::DefaultHasher::new();
    px.hash(&mut h);
    // the visual selection follows the keys, so it never waits out LIVE_REFRESH
    range.hash(&mut h);
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
    range: Option<(usize, usize)>,
    px: (u32, u32),
    pal: &Palette,
) -> u64 {
    let mut h = std::collections::hash_map::DefaultHasher::new();
    (version, step, ext, span, range, px, pal).hash(&mut h);
    h.finish()
}

/// Kitty image id for a tile's picture: two per tile, used in turn (`which` 0 / 1). Re-sending
/// under the id on screen makes the terminal drop the old image the moment the new one starts
/// arriving, so the tile flashes blank until it is decoded; under the other id the old picture
/// stays up until the cells switch to the new one in the same write. Ids are fixed, so each
/// send replaces the image from two sends ago instead of piling up (ratatui-image's own
/// protocols take a random id per send, and expose no way to delete the old image).
fn tile_image_id(idx: usize, which: u8) -> u32 {
    u32::from_be_bytes([0, 0xF1, 0xDA, (idx as u8) * 2 + which + 1])
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

/// One tile's picture, laid out by `draw_tile` and built in `flush_pictures`.
struct PicJob {
    idx: usize,
    /// Where the picture goes on screen.
    area: Rect,
    /// The visible window, owned so the build can run on another thread.
    bars: Vec<HBar>,
    vwap: Option<f64>,
    prev_close: Option<f64>,
    range: Option<(usize, usize)>,
    px: (u32, u32),
    key: u64,
    shape: u64,
}

impl Intraday {
    /// Builds the pictures the tiles queued, all at once on their own threads, then places
    /// them. A tile's picture is rebuilt only when its raster key changed, and then at most
    /// once per `LIVE_REFRESH` unless its shape changed (see `PicSlot`); a change that has to
    /// wait marks the screen `deferred` so it draws again.
    ///
    /// Rasterising and encoding (zlib + base64, or the shared-memory write) is ~90% of a
    /// frame and every tile is independent, so they run in parallel: four tiles cost about
    /// what one does, and the last tile no longer waits behind the other three.
    fn flush_pictures(&mut self, frame: &mut Frame) {
        let jobs = std::mem::take(&mut self.jobs);
        let Some(picker) = self.picker.as_ref() else {
            return;
        };
        let pal = self.palette();
        let resize = Resize::Fit(None);
        // Which tiles rebuild now; the rest keep (or wait out) the picture they have.
        let mut build: Vec<bool> = Vec::with_capacity(jobs.len());
        for job in &jobs {
            let slot = self.tiles[job.idx].pic.as_ref();
            let stale = slot.is_none_or(|s| s.key != job.key);
            let resend = stale
                && slot.is_none_or(|s| s.shape != job.shape || s.sent.elapsed() >= LIVE_REFRESH);
            self.deferred |= stale && !resend;
            build.push(resend);
        }
        // Disjoint tiles: hand each building job its own tile's buffer and slot.
        let mut work: Vec<(&PicJob, u32, &mut RgbaImage, &mut Option<PicSlot>)> = Vec::new();
        let mut tiles: Vec<Option<&mut Tile>> = self.tiles.iter_mut().map(Some).collect();
        for (job, go) in jobs.iter().zip(&build) {
            if !go {
                continue;
            }
            if let Some(tile) = tiles.get_mut(job.idx).and_then(Option::take) {
                let id = tile_image_id(job.idx, tile.which);
                tile.which ^= 1;
                work.push((job, id, &mut tile.scratch, &mut tile.pic));
            }
        }
        std::thread::scope(|scope| {
            for (job, id, scratch, slot) in work {
                let resize = resize.clone();
                scope.spawn(move || {
                    let (w, h) = (job.px.0.max(1), job.px.1.max(1));
                    if scratch.dimensions() != (w, h) {
                        *scratch = RgbaImage::new(w, h);
                    }
                    let pic = picture::Pic {
                        bars: &job.bars,
                        vwap: job.vwap,
                        prev_close: job.prev_close,
                        sel: None,
                        range: job.range,
                    };
                    picture::render_into(scratch, &pic, &pal);
                    let img = DynamicImage::ImageRgba8(scratch.clone());
                    let mut proto = picture_protocol(picker, img, id);
                    // encode here, off the UI thread, so placing it below costs nothing
                    if let Some(size) = proto.needs_resize(&resize, job.area.into()) {
                        proto.resize_encode(&resize, size);
                    }
                    *slot = Some(PicSlot {
                        key: job.key,
                        shape: job.shape,
                        sent: Instant::now(),
                        proto,
                    });
                });
            }
        });
        for job in &jobs {
            if let Some(s) = self.tiles[job.idx].pic.as_mut() {
                frame.render_stateful_widget(
                    StatefulImage::default().resize(resize.clone()),
                    job.area,
                    &mut s.proto,
                );
            }
        }
    }
}

impl Screen for Intraday {
    fn draw(&mut self, frame: &mut Frame) {
        self.apply_pending_cursor();
        self.changed = false;
        self.deferred = false;
        let area = frame.area();
        let t = self.theme;
        frame.render_widget(Block::new().style(t.base()), area);
        // The bottom row exists only while the ticker prompt is open.
        let [header, grid, footer] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(4),
            Constraint::Length(u16::from(self.prompt.is_some())),
        ])
        .areas(area);
        frame.render_widget(Paragraph::new(self.header()), header);

        if self.zoom {
            self.draw_tile(frame, grid, self.focus);
            self.flush_pictures(frame);
        } else {
            let rects = self.grid.rects(grid);
            for (idx, r) in rects.iter().enumerate() {
                if idx < self.tiles.len() {
                    self.draw_tile(frame, *r, idx);
                }
            }
            self.flush_pictures(frame);
            if let Some(cell) = self.eat {
                // the cells the tile will take, outlined over the tiles it eats
                let g = Grid {
                    cols: self.grid.cols,
                    rows: self.grid.rows,
                    cells: vec![cell],
                };
                let r = g.rects(grid)[0];
                frame.render_widget(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_type(ratatui::widgets::BorderType::Double)
                        .border_style(Style::new().fg(t.accent).bold())
                        .title(" eat · hjkl grow · ↵ take · esc cancel "),
                    r,
                );
            }
        }

        self.draw_menu(frame, grid);
        if let Some(buf) = &self.prompt {
            let line = Line::from(vec![
                Span::styled(" ticker for tile ", Style::new().fg(t.dim)),
                Span::styled(format!("{}", self.focus + 1), Style::new().fg(t.accent)),
                Span::raw(format!(": {buf}▏")),
            ]);
            frame.render_widget(Paragraph::new(line), footer);
        }
    }

    fn help(&self) -> Help {
        Help::new("intraday", KEYS)
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.prompt.is_some() {
            return self.prompt_key(key);
        }
        if self.eat.is_some() {
            self.changed = true;
            return self.eat_key(key);
        }
        if self.menu.is_some() {
            self.changed = true;
            return self.menu_key(key);
        }
        self.changed = true;
        self.flash = None;
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        // A count, vim-style: digits build it (a leading 0 is not one), the next key uses it.
        if let KeyCode::Char(d) = key.code {
            if d.is_ascii_digit() && !ctrl && (d != '0' || self.count.is_some()) {
                let digit = d.to_digit(10).unwrap_or(0) as usize;
                self.count = Some((self.count.unwrap_or(0) * 10 + digit).min(MAX_COUNT));
                return Action::None;
            }
        }
        // `g` waits for a second `g` (gg: first bar); any other key drops it. The count
        // waits with it, so 50gg is bar 50.
        let after_g = std::mem::take(&mut self.pending_g);
        let first_g = key.code == KeyCode::Char('g') && !after_g;
        let count = if first_g {
            self.count
        } else {
            self.count.take()
        };
        let times = count.unwrap_or(1) as isize;
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
            self.pending_cursor += d * times;
            return Action::None;
        }
        // Any other key sees the cursor as the keys before it left it.
        self.apply_pending_cursor();
        let n = self.tiles.len();
        match key.code {
            KeyCode::Char('q') => return Action::Quit,
            KeyCode::Esc if count.is_some() => {}
            KeyCode::Esc if self.tiles[self.focus].anchor.is_some() => {
                self.tiles[self.focus].anchor = None;
            }
            KeyCode::Esc if self.tiles[self.focus].span.is_some() => {
                self.tiles[self.focus].span = None;
            }
            KeyCode::Esc if self.zoom => self.zoom = false,
            KeyCode::Esc => return Action::Quit,
            KeyCode::Char('V') => {
                let at = self.cursor_index().map(|(c, _)| c);
                let t = &mut self.tiles[self.focus];
                t.anchor = if t.anchor.is_some() { None } else { at };
            }
            KeyCode::Char('i') if self.tiles[self.focus].anchor.is_some() => {
                self.zoom_to_selection();
            }
            KeyCode::Tab => self.focus = (self.focus + 1) % n,
            KeyCode::BackTab => self.focus = (self.focus + n - 1) % n,
            KeyCode::Char('h') | KeyCode::Left => self.move_focus(0, -1),
            KeyCode::Char('l') | KeyCode::Right => self.move_focus(0, 1),
            KeyCode::Char('k') => self.move_focus(-1, 0),
            KeyCode::Char('j') => self.move_focus(1, 0),
            KeyCode::Char(c @ ('{' | '}')) => self.jump_stop(c == '}', times as usize),
            KeyCode::Char('G') => match count {
                Some(k) => self.goto_bar(k - 1),
                None => self.follow_latest(),
            },
            KeyCode::Char('i') => {
                self.step = (self.step + 1) % STEPS.len();
                self.forget_ranges();
            }
            KeyCode::Char('e') => {
                self.ext = !self.ext;
                self.forget_ranges();
            }
            KeyCode::Char('g') if after_g => match count {
                Some(k) => self.goto_bar(k - 1),
                None => self.first_bar(),
            },
            KeyCode::Char('g') => self.pending_g = true,
            KeyCode::Enter => self.zoom = true,
            KeyCode::Char('z') => self.zoom = !self.zoom,
            KeyCode::Char('s') => self.prompt = Some(String::new()),
            KeyCode::Char('f') => {
                let list = layouts::load();
                let sel = self
                    .layout_id
                    .and_then(|id| list.iter().position(|l| l.id == id))
                    .unwrap_or(0);
                self.menu = Some((list, sel, false));
            }
            KeyCode::Char('m') if !self.zoom => {
                self.eat = self.grid.cells.get(self.focus).copied();
            }
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

    fn takes_text(&self) -> bool {
        self.prompt.is_some()
    }

    fn flash_text(&self) -> Option<&str> {
        self.flash.as_deref()
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
        self.prompt.is_none() && self.eat.is_none() && self.menu.is_none()
    }

    fn leader_window(&mut self, key: KeyEvent) -> bool {
        let KeyCode::Char(c) = key.code else {
            return false;
        };
        self.changed = true;
        if c == 'c' {
            self.close_tile();
            return true;
        }
        match Dir::from_key(c) {
            Some(d) => {
                self.zoom = false;
                self.split(d);
                true
            }
            None => false,
        }
    }
}

#[cfg(test)]
mod tests;
