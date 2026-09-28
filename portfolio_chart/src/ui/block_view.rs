// Renders a list of model::Block stacked vertically in one scrollable pane,
// with a cursor over selectable items (table rows, kv rows, series points,
// bars). The cursor's Source is what the source bar shows, so this is the
// component that makes every number auditable.
//
// Rendering per block type (each a small private fn below):
//   Table  -> ratatui Table, content-sized columns (long text truncated with
//             …; the cursor row wraps to show everything), h/l cell cursor
//   Kv     -> two-column Table, values right-aligned
//   Series -> x / value table with SparkBars beside it (None = gap), or a
//             SparkBars row over the table when the width is too narrow
//   Bars   -> horizontal bars: label, bar, value; `compare` as a dim second
//             bar; negative values grow left from a shared zero column
//   Text   -> wrapped paragraph (the whole text is one item)
//
// How scrolling works: every block is measured at the pane width (a `Geom`:
// height + each item's line span), giving one tall virtual page. Blocks that
// intersect the viewport are rendered into their own Buffer and the visible
// rows copied into the frame, so partially visible tables still use the real
// widgets. `scroll` follows the cursor.
//
// Gutter (2 cols left of every item): col 0 = ● for `new`; col 1 in audit
// mode = ƒ (derived, formula) or ✗ (no source). Audit mode also adds a dim
// source-label column (tables / kv / series / bars) or line (text).

use std::borrow::Cow;

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{
    Cell, HighlightSpacing, Paragraph, Row as TRow, Scrollbar, ScrollbarOrientation,
    ScrollbarState, StatefulWidget, Table, TableState, Widget,
};

use crate::model::{BarItem, Block, KvRow, Point, Row, Source};
use crate::ui::charts::SparkBars;
use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Default, Clone, Copy, PartialEq, Eq)]
pub struct Cursor {
    pub block: usize,
    pub item: usize,
}

#[derive(Debug, Default)]
pub struct BlockView {
    pub cursor: Cursor,
    /// Vertical scroll in lines.
    pub scroll: u16,
    /// Audit overlay: tint derived values and show per-item source labels inline.
    pub audit: bool,
    /// Selected column within the current Table row (h/l); None = whole row.
    pub col: Option<usize>,
    /// Pane height at the last render (drives ^d/^u); 0 before the first render.
    pub viewport: u16,
}

impl BlockView {
    pub fn new() -> Self {
        Self::default()
    }

    /// Reset when the underlying blocks change (e.g. new section selected).
    pub fn reset(&mut self) {
        *self = Self {
            audit: self.audit,
            ..Self::default()
        };
    }

    pub fn selected_source<'a>(&self, blocks: &'a [Block]) -> Option<&'a Source> {
        blocks.get(self.cursor.block)?.source(self.cursor.item)
    }

    /// Full text of the selected table cell (with h/l), else None.
    pub fn selected_cell<'a>(&self, blocks: &'a [Block]) -> Option<&'a str> {
        match blocks.get(self.cursor.block)? {
            Block::Table { rows, .. } => rows
                .get(self.cursor.item)?
                .cells
                .get(self.col?)
                .map(String::as_str),
            _ => None,
        }
    }

    /// Move to the next selectable item, crossing (and skipping empty) blocks.
    pub fn next(&mut self, blocks: &[Block]) {
        self.clamp(blocks);
        let Some(b) = blocks.get(self.cursor.block) else {
            return;
        };
        if self.cursor.item + 1 < b.len() {
            self.cursor.item += 1;
        } else if let Some(nb) =
            (self.cursor.block + 1..blocks.len()).find(|&i| !blocks[i].is_empty())
        {
            self.cursor = Cursor { block: nb, item: 0 };
            self.col = None;
        }
    }

    pub fn previous(&mut self, blocks: &[Block]) {
        self.clamp(blocks);
        if self.cursor.item > 0 {
            self.cursor.item -= 1;
        } else if let Some(pb) = (0..self.cursor.block)
            .rev()
            .find(|&i| !blocks[i].is_empty())
        {
            self.cursor = Cursor {
                block: pb,
                item: blocks[pb].len() - 1,
            };
            self.col = None;
        }
    }

    pub fn first(&mut self, blocks: &[Block]) {
        self.cursor = Cursor {
            block: blocks.iter().position(|b| !b.is_empty()).unwrap_or(0),
            item: 0,
        };
        self.col = None;
    }

    pub fn last(&mut self, blocks: &[Block]) {
        if let Some(i) = blocks.iter().rposition(|b| !b.is_empty()) {
            self.cursor = Cursor {
                block: i,
                item: blocks[i].len() - 1,
            };
            self.col = None;
        }
    }

    /// First item of the next non-empty block (tab).
    pub fn next_block(&mut self, blocks: &[Block]) {
        if let Some(nb) = (self.cursor.block + 1..blocks.len()).find(|&i| !blocks[i].is_empty()) {
            self.cursor = Cursor { block: nb, item: 0 };
            self.col = None;
        }
    }

    /// First item of this block, or of the previous one if already there (shift-tab).
    pub fn previous_block(&mut self, blocks: &[Block]) {
        if self.cursor.item > 0 {
            self.cursor.item = 0;
        } else if let Some(pb) = (0..self.cursor.block)
            .rev()
            .find(|&i| !blocks[i].is_empty())
        {
            self.cursor = Cursor { block: pb, item: 0 };
        }
        self.col = None;
    }

    /// Move `n` items down / up (half-page keys).
    pub fn move_by(&mut self, blocks: &[Block], n: isize) {
        for _ in 0..n.unsigned_abs() {
            if n > 0 {
                self.next(blocks)
            } else {
                self.previous(blocks)
            }
        }
    }

    /// Keep the cursor on a real item after the blocks changed.
    fn clamp(&mut self, blocks: &[Block]) {
        if blocks.get(self.cursor.block).is_none_or(|b| b.is_empty()) {
            self.first(blocks);
        }
        if let Some(b) = blocks.get(self.cursor.block) {
            self.cursor.item = self.cursor.item.min(b.len().saturating_sub(1));
            let ncols = match b {
                Block::Table { cols, .. } => cols.len(),
                _ => 0,
            };
            self.col = self.col.filter(|&c| c < ncols);
        }
    }

    /// Navigation keys: j/k ↓/↑, g/G, ^d/^u (half page), PgDn/PgUp,
    /// tab/shift-tab (block), h/l (table column). Returns true if handled;
    /// h with no column selected is left to the screen (e.g. focus nav).
    pub fn on_key(&mut self, key: KeyEvent, blocks: &[Block]) -> bool {
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        let half = (self.viewport / 2).max(1) as isize;
        match key.code {
            KeyCode::Char('d') if ctrl => self.move_by(blocks, half),
            KeyCode::Char('u') if ctrl => self.move_by(blocks, -half),
            KeyCode::PageDown => self.move_by(blocks, half * 2),
            KeyCode::PageUp => self.move_by(blocks, -half * 2),
            _ if ctrl => return false,
            KeyCode::Char('j') | KeyCode::Down => self.next(blocks),
            KeyCode::Char('k') | KeyCode::Up => self.previous(blocks),
            KeyCode::Char('g') | KeyCode::Home => self.first(blocks),
            KeyCode::Char('G') | KeyCode::End => self.last(blocks),
            KeyCode::Tab => self.next_block(blocks),
            KeyCode::BackTab => self.previous_block(blocks),
            KeyCode::Char('l') | KeyCode::Right => {
                let Some(Block::Table { cols, .. }) = blocks.get(self.cursor.block) else {
                    return false;
                };
                let last = cols.len().saturating_sub(1);
                self.col = Some(self.col.map_or(0, |c| (c + 1).min(last)));
            }
            KeyCode::Char('h') | KeyCode::Left => match self.col {
                Some(0) => self.col = None,
                Some(c) => self.col = Some(c - 1),
                None => return false,
            },
            KeyCode::Esc if self.col.is_some() => self.col = None,
            _ => return false,
        }
        true
    }

    pub fn render(&mut self, frame: &mut Frame, area: Rect, blocks: &[Block], theme: &Theme) {
        frame.render_stateful_widget(BlockList { blocks, theme }, area, self);
    }
}

/// Widget over a block list; state is the `BlockView` cursor/scroll.
pub struct BlockList<'a> {
    pub blocks: &'a [Block],
    pub theme: &'a Theme,
}

impl StatefulWidget for BlockList<'_> {
    type State = BlockView;

    fn render(self, area: Rect, buf: &mut Buffer, st: &mut BlockView) {
        let th = self.theme;
        buf.set_style(area, th.base());
        st.viewport = area.height;
        if area.is_empty() {
            return;
        }
        if self.blocks.iter().all(Block::is_empty) {
            Line::styled("no data", th.dim()).render(area, buf);
            return;
        }
        st.clamp(self.blocks);

        // measure at full width; if it overflows, re-measure leaving a scrollbar column
        let mut width = area.width;
        let mut page = measure(self.blocks, st, width, th);
        if page.total > area.height && width > 1 {
            width -= 1;
            page = measure(self.blocks, st, width, th);
        }
        follow_cursor(st, &page, area.height);

        let top = st.scroll;
        let bottom = top.saturating_add(area.height);
        for (bi, (y, g)) in page.blocks.iter().enumerate() {
            let (y, h) = (*y, g.height);
            if y >= bottom || y.saturating_add(h) <= top || h == 0 {
                continue;
            }
            let mut tmp = Buffer::empty(Rect::new(0, 0, width, h));
            tmp.set_style(tmp.area, th.base());
            draw_block(&self.blocks[bi], &cx(st, bi, width, th), &mut tmp);
            // copy the visible rows into the frame
            for ry in top.saturating_sub(y)..h.min(bottom - y) {
                let dy = area.y + (y + ry - top);
                for x in 0..width {
                    buf[(area.x + x, dy)] = tmp[(x, ry)].clone();
                }
            }
        }

        if page.total > area.height {
            let mut sb = ScrollbarState::new(page.total.saturating_sub(area.height) as usize)
                .position(st.scroll as usize)
                .viewport_content_length(area.height as usize);
            Scrollbar::new(ScrollbarOrientation::VerticalRight)
                .begin_symbol(None)
                .end_symbol(None)
                .track_symbol(Some("│"))
                .track_style(th.border())
                .thumb_style(th.dim())
                .render(area, buf, &mut sb);
        }
    }
}

/// Adjust `scroll` so the cursor item is visible (the block title too when
/// the cursor is on the first item), then clamp to the page.
fn follow_cursor(st: &mut BlockView, page: &Page, height: u16) {
    if let Some((y, g)) = page.blocks.get(st.cursor.block)
        && let Some(&(off, h)) = g.items.get(st.cursor.item)
    {
        let start = if st.cursor.item == 0 { *y } else { y + off };
        let end = y + off + h;
        if start < st.scroll {
            st.scroll = start;
        } else if end > st.scroll.saturating_add(height) {
            // tall item: show its top
            st.scroll = end.saturating_sub(height).min(y + off);
        }
    }
    st.scroll = st.scroll.min(page.total.saturating_sub(height));
}

// ---------------------------------------------------------------- geometry

/// A block's height and each item's (line offset, height) within it.
#[derive(Debug, Default)]
struct Geom {
    height: u16,
    items: Vec<(u16, u16)>,
}

/// Every block's (top line, Geom) on the virtual page.
struct Page {
    blocks: Vec<(u16, Geom)>,
    total: u16,
}

/// Per-block render context.
struct Cx<'a> {
    th: &'a Theme,
    audit: bool,
    width: u16,
    /// Cursor item if the cursor is in this block.
    sel: Option<usize>,
    col: Option<usize>,
}

fn cx<'a>(st: &BlockView, bi: usize, width: u16, th: &'a Theme) -> Cx<'a> {
    let here = st.cursor.block == bi;
    Cx {
        th,
        audit: st.audit,
        width,
        sel: here.then_some(st.cursor.item),
        col: if here { st.col } else { None },
    }
}

const GUTTER: u16 = 2;
/// Blank lines between blocks.
const GAP: u16 = 1;

fn measure(blocks: &[Block], st: &BlockView, width: u16, th: &Theme) -> Page {
    let mut y: u16 = 0;
    let mut out = Vec::with_capacity(blocks.len());
    for (i, b) in blocks.iter().enumerate() {
        if i > 0 {
            y = y.saturating_add(GAP);
        }
        let g = geom(b, &cx(st, i, width, th));
        out.push((y, g));
        y = y.saturating_add(out[i].1.height);
    }
    Page {
        blocks: out,
        total: y,
    }
}

fn has_header(b: &Block) -> bool {
    !b.title().is_empty()
        || matches!(b, Block::Series { unit, .. } | Block::Bars { unit, .. } if !unit.is_empty())
}

/// Geometry without drawing (a dry run of `body`).
fn geom(b: &Block, cx: &Cx) -> Geom {
    let hdr = u16::from(has_header(b));
    let mut g = body(b, cx, None, hdr);
    g.height += hdr;
    g
}

/// Header line + body into `buf` (whose area is exactly the block's Geom height).
fn draw_block(b: &Block, cx: &Cx, buf: &mut Buffer) {
    let hdr = u16::from(has_header(b));
    if hdr == 1 {
        header(b, cx).render(
            Rect {
                height: 1,
                ..buf.area
            },
            buf,
        );
    }
    let area = Rect {
        y: buf.area.y + hdr,
        height: buf.area.height.saturating_sub(hdr),
        ..buf.area
    };
    body(b, cx, Some((buf, area)), hdr);
}

/// "Title  $M" in bold (accent while the cursor is in this block).
fn header<'a>(b: &'a Block, cx: &Cx) -> Line<'a> {
    let th = cx.th;
    let style = if cx.sel.is_some() {
        th.title().fg(th.accent)
    } else {
        th.title()
    };
    let mut spans = vec![Span::styled(b.title(), style)];
    if let Block::Series { unit, .. } | Block::Bars { unit, .. } = b
        && !unit.is_empty()
    {
        spans.push(Span::styled(format!("  {unit}"), th.dim()));
    }
    Line::from(spans)
}

/// Dispatch to the per-type renderer. With `out = None` only geometry is
/// computed; item offsets are shifted by `hdr` to be block-relative.
fn body(b: &Block, cx: &Cx, out: Option<(&mut Buffer, Rect)>, hdr: u16) -> Geom {
    let mut g = match b {
        Block::Table { cols, rows, .. } => table(cols, rows, cx, out),
        Block::Kv { rows, .. } => kv(rows, cx, out),
        Block::Series { points, .. } => series(points, cx, out),
        Block::Bars { items, .. } => bars(items, cx, out),
        Block::Text { text, src, .. } => text_block(text, src.as_ref(), cx, out),
    };
    for it in &mut g.items {
        it.0 += hdr;
    }
    g
}

/// For other layouts (ui::block_grid): one block's body (no title line) at
/// `width`: its height and each item's (line offset, height).
pub(crate) fn body_geom(
    b: &Block,
    width: u16,
    sel: Option<usize>,
    audit: bool,
    th: &Theme,
) -> (u16, Vec<(u16, u16)>) {
    let g = body(
        b,
        &Cx {
            th,
            audit,
            width,
            sel,
            col: None,
        },
        None,
        0,
    );
    (g.height, g.items)
}

/// Draw one block's body (no title line) into the whole of `buf`.
pub(crate) fn draw_body(b: &Block, buf: &mut Buffer, sel: Option<usize>, audit: bool, th: &Theme) {
    let area = buf.area;
    body(
        b,
        &Cx {
            th,
            audit,
            width: area.width,
            sel,
            col: None,
        },
        Some((buf, area)),
        0,
    );
}

// ---------------------------------------------------------------- grid (table / kv / series rows)

/// One row of a grid: display cells + the provenance bits the gutter needs.
struct GridRow<'a> {
    cells: Vec<Cow<'a, str>>,
    new: bool,
    src: Option<&'a Source>,
}

/// Right-aligned columns, header labels (None = no header row).
struct GridSpec<'a> {
    header: Option<&'a [String]>,
    right: Vec<bool>,
    /// Style for a cell's text by (row, col) before selection is applied.
    cell_style: &'a dyn Fn(usize, usize) -> Style,
}

/// Width of the audit source-label column.
fn src_col_width(cx: &Cx) -> u16 {
    if cx.audit {
        (cx.width / 4).clamp(8, 40)
    } else {
        0
    }
}

/// Column widths fitting `avail`: each column gets its natural width unless
/// that doesn't fit, in which case the widest are capped equally
/// ("water-filling"), so short columns (dates, numbers) are never cut.
fn fit_widths(natural: &[u16], avail: u16) -> Vec<u16> {
    let mut sorted: Vec<u16> = natural.to_vec();
    sorted.sort_unstable();
    let mut remaining = avail;
    let mut cap = u16::MAX;
    for (k, &w) in sorted.iter().enumerate() {
        let share = remaining / (sorted.len() - k) as u16;
        if w <= share {
            remaining -= w;
        } else {
            cap = share;
            break;
        }
    }
    natural.iter().map(|&w| w.min(cap)).collect()
}

/// Gutter cell: ● new, then the audit marker.
fn gutter<'a>(new: bool, src: Option<&Source>, cx: &Cx) -> Line<'a> {
    let th = cx.th;
    let a = if new {
        Span::styled("●", th.new_marker())
    } else {
        Span::raw(" ")
    };
    let b = match (cx.audit, src) {
        (false, _) => Span::raw(" "),
        (true, None) => Span::styled("✗", th.down()),
        (true, Some(s)) if s.is_derived() => Span::styled("ƒ", th.derived()),
        (true, Some(_)) => Span::raw(" "),
    };
    Line::from(vec![a, b])
}

/// Audit column text for a source.
fn src_label<'a>(src: Option<&Source>, w: usize, th: &Theme) -> Line<'a> {
    match src {
        None => Line::styled(text::truncate("no source", w), th.down()),
        Some(s) if s.is_derived() => Line::styled(
            text::truncate(&format!("ƒ {}", s.label), w),
            th.dim().add_modifier(Modifier::ITALIC),
        ),
        Some(s) => Line::styled(text::truncate(&s.label, w), th.dim()),
    }
}

/// Max lines the cursor row may wrap to.
const MAX_ROW_LINES: usize = 6;

fn grid(spec: &GridSpec, rows: &[GridRow], cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let th = cx.th;
    if rows.is_empty() {
        if let Some((buf, area)) = out {
            Line::styled("  (none)", th.dim()).render(area, buf);
        }
        return Geom {
            height: 1,
            items: vec![],
        };
    }
    let ncols = spec.right.len();
    let srcw = src_col_width(cx);
    // Available content width before table column separators.
    let avail = cx.width.saturating_sub(GUTTER + srcw);
    // With a table cell selected, preserve readable column widths and reveal
    // the selected column plus following columns in a horizontal window.
    // Without cell selection, keep the compact all-columns overview.
    let display_cols: Vec<usize> = if let Some(selected) = cx.col.filter(|_| spec.header.is_some())
    {
        let mut used = 0u16;
        let mut cols = Vec::new();
        for c in selected.min(ncols.saturating_sub(1))..ncols {
            let w = spec
                .header
                .and_then(|h| h.get(c))
                .map_or(0, |s| text::width(s))
                .max(
                    rows.iter()
                        .map(|r| r.cells.get(c).map_or(0, |s| text::width(s)))
                        .max()
                        .unwrap_or(0),
                )
                .clamp(1, 28) as u16;
            let next = used
                .saturating_add(w)
                .saturating_add(u16::from(!cols.is_empty()));
            if !cols.is_empty() && next > avail {
                break;
            }
            cols.push(c);
            used = next;
        }
        cols
    } else {
        (0..ncols).collect()
    };
    let natural: Vec<u16> = display_cols
        .iter()
        .copied()
        .map(|c| {
            let h = spec
                .header
                .and_then(|h| h.get(c))
                .map_or(0, |s| text::width(s));
            let body = rows
                .iter()
                .map(|r| r.cells.get(c).map_or(0, |s| text::width(s)))
                .max()
                .unwrap_or(0);
            h.max(body).min(u16::MAX as usize) as u16
        })
        .collect();
    let spacing = display_cols.len() as u16 + u16::from(srcw > 0);
    let avail = cx.width.saturating_sub(GUTTER + srcw + spacing);
    let widths = fit_widths(&natural, avail);

    // cursor row wraps when something in it was truncated
    let sel_lines: Vec<Vec<String>> = match cx.sel.and_then(|i| rows.get(i)) {
        Some(r) => display_cols
            .iter()
            .enumerate()
            .map(|(visible, &c)| {
                let s = r.cells.get(c).map_or("", |s| s.as_ref());
                if text::width(s) > widths[visible] as usize && widths[visible] > 0 {
                    text::wrap(s, widths[visible] as usize)
                        .into_iter()
                        .take(MAX_ROW_LINES)
                        .collect()
                } else {
                    vec![s.to_string()]
                }
            })
            .collect(),
        None => vec![],
    };
    let sel_h = sel_lines.iter().map(Vec::len).max().unwrap_or(1).max(1) as u16;
    let hdr = u16::from(spec.header.is_some());
    let mut items = Vec::with_capacity(rows.len());
    let mut y = hdr;
    for i in 0..rows.len() {
        let h = if cx.sel == Some(i) { sel_h } else { 1 };
        items.push((y, h));
        y += h;
    }
    let geom = Geom { height: y, items };
    let Some((buf, area)) = out else { return geom };

    let align = |line: Line<'static>, c: usize| {
        if spec.right[display_cols[c]] {
            line.right_aligned()
        } else {
            line
        }
    };
    let trows: Vec<TRow> = rows
        .iter()
        .enumerate()
        .map(|(i, r)| {
            let mut cells = vec![Cell::from(gutter(r.new, r.src, cx))];
            for (visible, &c) in display_cols.iter().enumerate() {
                let style = (spec.cell_style)(i, c);
                let text: Text = if cx.sel == Some(i) {
                    let lines = sel_lines.get(visible).cloned().unwrap_or_default();
                    Text::from(
                        lines
                            .into_iter()
                            .map(|l| align(Line::styled(l, style), visible))
                            .collect::<Vec<_>>(),
                    )
                } else {
                    let s = r.cells.get(c).map_or("", |s| s.as_ref());
                    Text::from(align(
                        Line::styled(text::truncate(s, widths[visible] as usize), style),
                        visible,
                    ))
                };
                cells.push(Cell::from(text));
            }
            if srcw > 0 {
                cells.push(Cell::from(src_label(r.src, srcw as usize, th)));
            }
            let row = TRow::new(cells).height(items_h(&geom, i));
            if cx.audit && r.src.is_some_and(Source::is_derived) {
                row.style(th.derived())
            } else {
                row
            }
        })
        .collect();

    let mut constraints = vec![Constraint::Length(GUTTER)];
    constraints.extend(widths.iter().map(|&w| Constraint::Length(w)));
    if srcw > 0 {
        constraints.push(Constraint::Length(srcw));
    }
    let mut table = Table::new(trows, constraints)
        .column_spacing(1)
        .style(th.base())
        .row_highlight_style(th.selected())
        .cell_highlight_style(
            th.on_cursor(th.accent())
                .add_modifier(Modifier::BOLD | Modifier::UNDERLINED),
        )
        .highlight_spacing(HighlightSpacing::Never);
    if let Some(h) = spec.header {
        let cells = display_cols.iter().enumerate().map(|(visible, &c)| {
            let s = h.get(c).map_or("", String::as_str);
            Cell::from(align(
                Line::styled(
                    text::truncate(s, widths[visible] as usize),
                    th.dim().add_modifier(Modifier::BOLD),
                ),
                visible,
            ))
        });
        let mut hc = vec![Cell::from("")];
        hc.extend(cells);
        if srcw > 0 {
            hc.push(Cell::from(Line::styled(
                "source",
                th.dim().add_modifier(Modifier::BOLD),
            )));
        }
        table = table.header(TRow::new(hc));
    }
    // column index in the widget includes the gutter column
    let mut state = TableState::default()
        .with_selected(cx.sel)
        .with_selected_column(cx.col.map(|_| 1));
    StatefulWidget::render(table, area, buf, &mut state);
    geom
}

fn items_h(g: &Geom, i: usize) -> u16 {
    g.items.get(i).map_or(1, |&(_, h)| h)
}

/// Looks like a number / amount / percentage (right-align it); dates don't count.
fn is_numeric(s: &str) -> bool {
    let s = s.trim();
    let b = s.as_bytes();
    let is_date =
        b.len() >= 10 && b[4] == b'-' && b[7] == b'-' && b[..4].iter().all(u8::is_ascii_digit);
    !s.is_empty()
        && !is_date
        && s.chars().any(|c| c.is_ascii_digit())
        && s.chars()
            .all(|c| c.is_ascii_digit() || ",.$%+-−()KMBkx× ".contains(c))
}

fn table(cols: &[String], rows: &[Row], cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let right: Vec<bool> = (0..cols.len())
        .map(|c| {
            // mostly numeric ("new", "n/a" placeholders don't flip the column)
            let vals: Vec<&String> = rows
                .iter()
                .filter_map(|r| r.cells.get(c))
                .filter(|s| !s.trim().is_empty())
                .collect();
            let num = vals.iter().filter(|s| is_numeric(s)).count();
            num > 0 && num * 4 >= vals.len() * 3
        })
        .collect();
    let grows: Vec<GridRow> = rows
        .iter()
        .map(|r| GridRow {
            cells: r.cells.iter().map(|s| Cow::Borrowed(s.as_str())).collect(),
            new: r.new,
            src: r.src.as_ref(),
        })
        .collect();
    let th = cx.th;
    // signed columns (Δ, +x / -x) get up/down colour
    let style = |i: usize, c: usize| {
        let s = rows
            .get(i)
            .and_then(|r| r.cells.get(c))
            .map_or("", String::as_str)
            .trim();
        match s.chars().next() {
            Some('+') if right[c] => th.up(),
            Some('-' | '−') if right[c] => th.down(),
            _ => th.base(),
        }
    };
    grid(
        &GridSpec {
            header: Some(cols),
            right: right.clone(),
            cell_style: &style,
        },
        &grows,
        cx,
        out,
    )
}

fn kv(rows: &[KvRow], cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let grows: Vec<GridRow> = rows
        .iter()
        .map(|r| GridRow {
            cells: vec![
                Cow::Borrowed(r.label.as_str()),
                Cow::Borrowed(r.value.as_str()),
            ],
            new: r.new,
            src: r.src.as_ref(),
        })
        .collect();
    let th = cx.th;
    let style = |_: usize, c: usize| if c == 0 { th.dim() } else { th.base() };
    grid(
        &GridSpec {
            header: None,
            right: vec![false, true],
            cell_style: &style,
        },
        &grows,
        cx,
        out,
    )
}

/// Rows the sparkline takes above the series table.
const SPARK_H: u16 = 2;
/// Side-by-side series: columns between the rows and the chart, and the
/// narrowest chart worth drawing beside them.
const SIDE_GAP: u16 = 3;
const SIDE_MIN_CHART: u16 = 12;

fn series(points: &[Point], cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let th = cx.th;
    let spark = if points.iter().any(|p| p.y.is_some()) {
        SPARK_H
    } else {
        0
    };
    let ys: Vec<f64> = points.iter().filter_map(|p| p.y).collect();
    let mut fmt = text::fmt_nums(&ys).into_iter();
    let grows: Vec<GridRow> = points
        .iter()
        .map(|p| GridRow {
            cells: vec![
                Cow::Borrowed(p.x.as_str()),
                Cow::Owned(p.y.and_then(|_| fmt.next()).unwrap_or_else(|| "–".into())),
            ],
            new: false,
            src: p.src.as_ref(),
        })
        .collect();
    let style = |i: usize, c: usize| match (c, points.get(i).and_then(|p| p.y)) {
        (0, _) => th.dim(),
        (_, None) => th.dim(),
        _ => th.base(),
    };
    let spec = GridSpec {
        header: None,
        right: vec![false, true],
        cell_style: &style,
    };

    // Side by side when there's room: x / value rows on the left, a chart as
    // tall as the rows on the right. Otherwise the sparkline sits on top.
    let col_w = |c: usize| {
        grows
            .iter()
            .map(|r| text::width(&r.cells[c]) as u16)
            .max()
            .unwrap_or(0)
    };
    let table_w = GUTTER + 2 + col_w(0) + col_w(1);
    let chart_room = cx.width.saturating_sub(table_w + SIDE_GAP);
    if spark > 0 && !cx.audit && chart_room >= SIDE_MIN_CHART {
        let tcx = Cx {
            th,
            audit: false,
            width: table_w,
            sel: cx.sel,
            col: None,
        };
        let Some((buf, area)) = out else {
            return grid(&spec, &grows, &tcx, None);
        };
        let g = grid(&spec, &grows, &tcx, Some((buf, Rect { width: table_w.min(area.width), ..area })));
        let bars = SparkBars {
            points,
            selected: cx.sel,
            theme: th,
        };
        let (per, _) = bars.geometry(chart_room);
        let chart_w = (per * points.len() as u16).clamp(1, chart_room);
        let chart = Rect {
            x: area.x + table_w + SIDE_GAP,
            width: chart_w,
            height: g.height.min(area.height),
            ..area
        };
        bars.render(chart.intersection(area), buf);
        return g;
    }

    let mut g = match out {
        None => grid(&spec, &grows, cx, None),
        Some((buf, area)) => {
            let spark_r = Rect {
                x: area.x + GUTTER,
                width: area.width.saturating_sub(GUTTER),
                height: spark.min(area.height),
                ..area
            };
            SparkBars {
                points,
                selected: cx.sel,
                theme: th,
            }
            .render(spark_r, buf);
            let rest = Rect {
                y: area.y + spark,
                height: area.height.saturating_sub(spark),
                ..area
            };
            grid(&spec, &grows, cx, Some((buf, rest)))
        }
    };
    g.height += spark;
    for it in &mut g.items {
        it.0 += spark;
    }
    g
}

fn bars(items: &[BarItem], cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let th = cx.th;
    let per = if items.iter().any(|i| i.compare.is_some()) {
        2
    } else {
        1
    };
    let geom = Geom {
        height: (items.len() as u16 * per).max(1),
        items: (0..items.len() as u16).map(|i| (i * per, per)).collect(),
    };
    let Some((buf, area)) = out else { return geom };
    if items.is_empty() {
        Line::styled("  (none)", th.dim()).render(area, buf);
        return geom;
    }
    let srcw = src_col_width(cx);
    // values and compares share one decimal count so the column lines up
    let nums: Vec<f64> = items
        .iter()
        .map(|i| i.value)
        .chain(items.iter().filter_map(|i| i.compare))
        .collect();
    let mut fmt = text::fmt_nums(&nums).into_iter();
    let vals: Vec<String> = fmt.by_ref().take(items.len()).collect();
    let cmps: Vec<String> = items
        .iter()
        .map(|i| i.compare.and_then(|_| fmt.next()).unwrap_or_default())
        .collect();
    let vw = vals
        .iter()
        .chain(&cmps)
        .map(|s| text::width(s))
        .max()
        .unwrap_or(0) as u16;
    let lw = (items
        .iter()
        .map(|i| text::width(&i.label))
        .max()
        .unwrap_or(0) as u16)
        .min(28)
        .min(cx.width / 3);
    let fixed = GUTTER + lw + 1 + 1 + vw + if srcw > 0 { srcw + 1 } else { 0 };
    let bw = area.width.saturating_sub(fixed);
    // shared scale with a zero column so mixed signs line up
    let all = items
        .iter()
        .flat_map(|i| [Some(i.value), i.compare])
        .flatten();
    let (lo, hi) = all.fold((0.0_f64, 0.0_f64), |(l, h), v| (l.min(v), h.max(v)));
    let span = (hi - lo).max(f64::EPSILON);
    let zero = ((-lo / span) * bw as f64).round() as u16;

    for (i, it) in items.iter().enumerate() {
        let sel = cx.sel == Some(i);
        let y = area.y + i as u16 * per;
        if y >= area.bottom() {
            break;
        }
        let row = |dy: u16| Rect {
            x: area.x,
            y: y + dy,
            width: area.width,
            height: 1,
        };
        let x_label = area.x + GUTTER;
        let x_bar = x_label + lw + 1;
        let x_val = x_bar + bw + 1;
        if sel {
            // faint band across the whole item (both rows when there's a compare bar)
            buf.set_style(
                Rect {
                    height: per.min(area.bottom() - y),
                    ..row(0)
                },
                th.selected(),
            );
        }
        gutter(false, it.src.as_ref(), cx).render(row(0), buf);
        let lstyle = if sel { th.selected() } else { th.base() };
        let lstyle = if cx.audit && it.src.as_ref().is_some_and(Source::is_derived) {
            lstyle.patch(th.derived())
        } else {
            lstyle
        };
        buf.set_stringn(
            x_label,
            y,
            text::fit(&it.label, lw as usize, false),
            lw as usize,
            lstyle,
        );
        let bar_style = if sel {
            th.on_cursor(th.accent())
        } else {
            th.signed(it.value)
        };
        hbar(
            buf,
            Rect {
                x: x_bar,
                y,
                width: bw,
                height: 1,
            },
            zero,
            it.value / span * bw as f64,
            bar_style,
        );
        buf.set_stringn(
            x_val,
            y,
            text::fit(&vals[i], vw as usize, true),
            vw as usize,
            if sel {
                th.on_cursor(th.signed(it.value))
            } else {
                th.signed(it.value)
            },
        );
        if srcw > 0 {
            src_label(it.src.as_ref(), srcw as usize, th).render(
                Rect {
                    x: x_val + vw + 1,
                    y,
                    width: srcw,
                    height: 1,
                }
                .intersection(area),
                buf,
            );
        }
        if per == 2
            && y + 1 < area.bottom()
            && let Some(c) = it.compare
        {
            let dim = if sel {
                th.on_cursor(th.dim())
            } else {
                th.dim()
            };
            buf.set_stringn(
                x_label,
                y + 1,
                text::fit("vs", lw as usize, true),
                lw as usize,
                dim,
            );
            {
                hbar(
                    buf,
                    Rect {
                        x: x_bar,
                        y: y + 1,
                        width: bw,
                        height: 1,
                    },
                    zero,
                    c / span * bw as f64,
                    dim,
                );
                buf.set_stringn(
                    x_val,
                    y + 1,
                    text::fit(&cmps[i], vw as usize, true),
                    vw as usize,
                    dim,
                );
            }
        }
    }
    geom
}

/// Horizontal bar of `cells` (signed) starting at column `zero` of `r`:
/// right with 1/8 resolution, left with 1/2 (only a right-half block exists).
fn hbar(buf: &mut Buffer, r: Rect, zero: u16, cells: f64, style: Style) {
    const EIGHTHS: [&str; 8] = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"];
    if r.width == 0 || !cells.is_finite() {
        return;
    }
    let buf_area = buf.area;
    let mut put = |x: u16, s: &str| {
        if x >= r.x && x < r.right() && buf_area.contains((x, r.y).into()) {
            buf[(x, r.y)].set_symbol(s).set_style(style);
        }
    };
    if cells >= 0.0 {
        let eighths = (cells * 8.0).round() as u32;
        let full = (eighths / 8) as u16;
        for dx in 0..full {
            put(r.x + zero + dx, "█");
        }
        let rem = (eighths % 8) as usize;
        if rem > 0 {
            put(r.x + zero + full, EIGHTHS[rem]);
        }
    } else {
        let halves = (-cells * 2.0).round() as u32;
        let full = (halves / 2) as u16;
        for dx in 1..=full.min(zero) {
            put(r.x + zero - dx, "█");
        }
        if halves % 2 == 1 && zero > full {
            put(r.x + zero - full - 1, "▐");
        }
    }
}

fn text_block(body: &str, src: Option<&Source>, cx: &Cx, out: Option<(&mut Buffer, Rect)>) -> Geom {
    let th = cx.th;
    let w = cx.width.saturating_sub(GUTTER) as usize;
    let lines = if w == 0 { vec![] } else { text::wrap(body, w) };
    let extra = u16::from(cx.audit);
    let n = (lines.len() as u16).max(1) + extra;
    let geom = Geom {
        height: n,
        items: vec![(0, n)],
    };
    let Some((buf, area)) = out else { return geom };
    let sel = cx.sel == Some(0);
    let style = if cx.audit && src.is_some_and(Source::is_derived) {
        th.derived()
    } else {
        th.base()
    };
    let mut out_lines: Vec<Line> = lines
        .into_iter()
        .map(|l| {
            let g = if sel {
                Span::styled("▌ ", th.accent())
            } else {
                Span::raw("  ")
            };
            Line::from(vec![g, Span::styled(l, style)])
        })
        .collect();
    if cx.audit {
        let mut l = src_label(src, w, th);
        l.spans.insert(
            0,
            gutter(false, src, cx)
                .spans
                .into_iter()
                .nth(1)
                .unwrap_or_default(),
        );
        l.spans.insert(0, Span::raw(" "));
        out_lines.push(l);
    }
    Paragraph::new(out_lines).render(area, buf);
    geom
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::Section;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn key(c: KeyCode) -> KeyEvent {
        KeyEvent::new(c, KeyModifiers::NONE)
    }

    fn sample() -> Vec<Block> {
        let doc = |l: &str| Some(Source::url(l, "https://www.sec.gov/Archives/x/doc.htm"));
        vec![
            Block::Kv {
                title: String::new(),
                rows: vec![
                    KvRow { label: "Revenue".into(), value: "$2.74B".into(), new: true, src: doc("10-Q Q2") },
                    KvRow {
                        label: "  YoY".into(),
                        value: "+36.5%".into(),
                        new: false,
                        src: Some(Source::derived("YoY growth", "2,739.3 / 2,006.1 − 1", vec![])),
                    },
                    KvRow { label: "Unsourced".into(), value: "42".into(), new: false, src: None },
                ],
            },
            Block::Table {
                title: "Biggest adds".into(),
                cols: vec!["manager".into(), "Δ shares".into()],
                rows: vec![
                    Row { cells: vec!["BlackRock, Inc.".into(), "+21.80M".into()], new: false, src: doc("13F BlackRock") },
                    Row {
                        cells: vec!["A very long manager name that will certainly not fit in a narrow pane at all".into(), "-3.1M".into()],
                        new: true,
                        src: doc("13F long"),
                    },
                ],
            },
            Block::Table { title: "Empty".into(), cols: vec!["x".into()], rows: vec![] },
            Block::Series {
                title: "Quarterly revenue".into(),
                unit: "$M".into(),
                points: vec![
                    Point { x: "Q1".into(), y: Some(1516.1), src: doc("10-Q Q1") },
                    Point { x: "Q2".into(), y: None, src: None },
                    Point { x: "Q3".into(), y: Some(2739.3), src: doc("10-Q Q3") },
                ],
            },
            Block::Bars {
                title: "Segments".into(),
                unit: "$M".into(),
                items: vec![
                    BarItem { label: "Data Center".into(), value: 6100.3, compare: Some(4000.0), src: doc("10-K DC") },
                    BarItem { label: "Other".into(), value: -500.0, compare: None, src: doc("10-K other") },
                ],
            },
            Block::Text { title: "About".into(), text: "Marvell provides data infrastructure semiconductor solutions.".into(), src: doc("Yahoo") },
        ]
    }

    fn draw(v: &mut BlockView, blocks: &[Block], w: u16, h: u16) -> (String, Buffer) {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| v.render(f, f.area(), blocks, &Theme::default()))
            .unwrap();
        let b = t.backend().buffer().clone();
        let s = (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n");
        (s, b)
    }

    fn line_of(s: &str, needle: &str) -> usize {
        s.lines()
            .position(|l| l.contains(needle))
            .unwrap_or_else(|| panic!("{needle:?} not in\n{s}"))
    }

    #[test]
    fn renders_every_block_type() {
        let blocks = sample();
        let mut v = BlockView::new();
        let (s, b) = draw(&mut v, &blocks, 70, 40);
        for needle in [
            "Revenue",
            "$2.74B",
            "Biggest adds",
            "manager",
            "BlackRock, Inc.",
            "Quarterly revenue  $M",
            "2,739.3",
            "Data Center",
            "6,100.3",
            "About",
            "Marvell provides",
        ] {
            assert!(s.contains(needle), "{needle:?} missing in\n{s}");
        }
        // new marker, truncation ellipsis, None as a dash
        assert!(s.lines().any(|l| l.starts_with("●  Revenue")), "{s}");
        assert!(s.contains('…'), "{s}");
        assert!(
            s.lines().any(|l| l.contains("Q2") && l.contains('–')),
            "{s}"
        );
        // cursor row (first kv row) is highlighted
        let y = line_of(&s, "$2.74B") as u16;
        assert!((b[(3, y)].bg == Theme::default().sel_bg()));
        let y2 = line_of(&s, "  YoY") as u16;
        assert!(!(b[(3, y2)].bg == Theme::default().sel_bg()));
        // values right-aligned: "+36.5%" ends where "$2.74B" ends
        let end = |n: &str| {
            s.lines()
                .nth(line_of(&s, n))
                .map(|l| text::width(&l[..l.find(n).unwrap()]) + n.len())
        };
        assert_eq!(end("$2.74B"), end("+36.5%"));
        // negative bar grows left of the positive one's start
        assert!(s.contains('█'));
    }

    #[test]
    fn cursor_crosses_blocks_and_skips_empty() {
        let blocks = sample();
        let mut v = BlockView::new();
        for _ in 0..3 {
            v.on_key(key(KeyCode::Char('j')), &blocks);
        }
        assert_eq!(v.cursor, Cursor { block: 1, item: 0 });
        v.on_key(key(KeyCode::Char('j')), &blocks);
        v.on_key(key(KeyCode::Char('j')), &blocks);
        assert_eq!(
            v.cursor,
            Cursor { block: 3, item: 0 },
            "empty table skipped"
        );
        v.on_key(key(KeyCode::Char('k')), &blocks);
        assert_eq!(v.cursor, Cursor { block: 1, item: 1 });
        v.on_key(key(KeyCode::Tab), &blocks);
        assert_eq!(v.cursor, Cursor { block: 3, item: 0 });
        v.on_key(key(KeyCode::BackTab), &blocks);
        assert_eq!(v.cursor, Cursor { block: 1, item: 0 });
        v.on_key(key(KeyCode::Char('G')), &blocks);
        assert_eq!(v.cursor, Cursor { block: 5, item: 0 });
        assert_eq!(v.selected_source(&blocks).unwrap().label, "Yahoo");
        v.on_key(key(KeyCode::Char('g')), &blocks);
        assert_eq!(v.cursor, Cursor::default());
        // h is left to the screen when no column is selected; l only in tables
        assert!(!v.on_key(key(KeyCode::Char('h')), &blocks));
        assert!(!v.on_key(key(KeyCode::Char('l')), &blocks));
        v.on_key(key(KeyCode::Tab), &blocks);
        assert!(v.on_key(key(KeyCode::Char('l')), &blocks));
        v.on_key(key(KeyCode::Char('l')), &blocks);
        v.on_key(key(KeyCode::Char('l')), &blocks);
        assert_eq!(v.col, Some(1));
        assert_eq!(v.selected_cell(&blocks), Some("+21.80M"));
        // half page
        v.viewport = 6;
        v.on_key(
            KeyEvent::new(KeyCode::Char('d'), KeyModifiers::CONTROL),
            &blocks,
        );
        assert_eq!(v.cursor, Cursor { block: 3, item: 1 });
        v.on_key(
            KeyEvent::new(KeyCode::Char('u'), KeyModifiers::CONTROL),
            &blocks,
        );
        assert_eq!(v.cursor, Cursor { block: 1, item: 0 });
    }

    #[test]
    fn scroll_follows_cursor() {
        let blocks = sample();
        let mut v = BlockView::new();
        v.last(&blocks);
        let (s, _) = draw(&mut v, &blocks, 60, 8);
        assert!(v.scroll > 0);
        assert!(s.contains("Marvell"), "{s}");
        assert!(s.contains("▌ "), "text cursor gutter\n{s}");
        v.first(&blocks);
        let (s, _) = draw(&mut v, &blocks, 60, 8);
        assert_eq!(v.scroll, 0);
        assert!(s.contains("$2.74B"));
    }

    #[test]
    fn cursor_row_wraps_long_cell() {
        let blocks = sample();
        let mut v = BlockView {
            cursor: Cursor { block: 1, item: 1 },
            ..Default::default()
        };
        let (s, _) = draw(&mut v, &blocks, 40, 30);
        assert!(s.contains("certainly"), "wrapped row shows full text\n{s}");
        assert!(s.contains("pane at all"), "{s}");
    }

    #[test]
    fn audit_marks_derived_and_missing() {
        let blocks = sample();
        let mut v = BlockView {
            audit: true,
            ..Default::default()
        };
        let (s, b) = draw(&mut v, &blocks, 90, 40);
        let yoy = line_of(&s, "YoY");
        assert!(s.lines().nth(yoy).unwrap().starts_with(" ƒ"), "{s}");
        assert!(s.lines().nth(yoy).unwrap().contains("ƒ YoY growth"), "{s}");
        let un = line_of(&s, "Unsourced");
        assert!(s.lines().nth(un).unwrap().starts_with(" ✗"), "{s}");
        assert!(s.lines().nth(un).unwrap().contains("no source"), "{s}");
        assert!(s.contains("10-Q Q2"), "source label inline\n{s}");
        assert!(b[(4, yoy as u16)].modifier.contains(Modifier::ITALIC));
    }

    #[test]
    fn tiny_and_empty() {
        let blocks = sample();
        for (w, h) in [(10, 3), (1, 1), (0, 0), (3, 20), (200, 2)] {
            let mut v = BlockView {
                audit: true,
                ..Default::default()
            };
            draw(&mut v, &blocks, w, h);
            v.last(&blocks);
            draw(&mut v, &blocks, w, h);
            draw(&mut v, &[], w, h);
        }
        let mut v = BlockView::new();
        v.next(&[]);
        v.previous(&[]);
        v.on_key(key(KeyCode::Char('G')), &[]);
        assert!(v.selected_source(&[]).is_none());
        // cursor left over from a bigger section is clamped
        let mut v = BlockView {
            cursor: Cursor { block: 9, item: 9 },
            ..Default::default()
        };
        draw(&mut v, &blocks, 40, 10);
        assert_eq!(v.cursor, Cursor::default());
    }

    #[test]
    fn real_dossier_parses_and_renders() {
        let raw = include_str!("../screens/fixtures/dossier_MRVL.json");
        #[derive(serde::Deserialize)]
        struct D {
            sections: Vec<Section>,
        }
        let d: D = serde_json::from_str(raw).expect("dossier JSON parses into Vec<Section>");
        assert_eq!(d.sections.len(), 8);
        for sec in &d.sections {
            let mut v = BlockView::new();
            for audit in [false, true] {
                v.audit = audit;
                let (s, _) = draw(&mut v, &sec.blocks, 100, 30);
                assert!(!s.trim().is_empty(), "{}", sec.id);
                for _ in 0..40 {
                    v.next(&sec.blocks);
                }
                draw(&mut v, &sec.blocks, 100, 30);
                draw(&mut v, &sec.blocks, 10, 3);
            }
        }
    }
}
