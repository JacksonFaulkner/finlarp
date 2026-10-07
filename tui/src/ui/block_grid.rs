// Blocks laid out as a grid of bordered containers, 1-3 per row by screen
// width, with spatial hjkl navigation. BlockView (one tall column) stays the
// choice for long, list-like sections; BlockGrid is for dashboards like
// CANSLIM's letters, where several small blocks read best side by side.
//
// Packing (reading order is kept):
//   - columns per row: Compact 1, Normal 2, Roomy 3 (theme.spacing), and never
//     narrower than MIN_CELL_W columns per container
//   - wide blocks (Text, Tables with >= 5 columns) take a full row
//   - a row's height is its tallest container, capped so the grid stays
//     scannable; taller content scrolls inside its container
//   - neighbouring containers share border lines (merged ┬ ┼ ┤)
//
// Navigation is by geometry, not by index, so any packing works:
//   j/k   next / previous item; past the last item, the container below / above
//   h/l   container to the left / right (item kept at the same screen row)
//   tab / shift-tab  next / previous container in reading order
//   g/G   first / last container, ^d/^u five items
//
// Items are drawn by block_view's per-type renderers (`body_geom` /
// `draw_body`), so tables, bars, series, kv and text look identical in both.

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::symbols::merge::MergeStrategy;
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block as Frame_, StatefulWidget, Widget};

use crate::model::{Block, Source};
use crate::ui::block_view::{Cursor, body_geom, draw_body};
use crate::ui::theme::Theme;

/// Narrowest container before the grid drops a column.
const MIN_CELL_W: u16 = 44;
/// Items moved by ^d / ^u.
const JUMP: usize = 5;

#[derive(Debug, Default)]
pub struct BlockGrid {
    pub cursor: Cursor,
    /// Audit overlay, passed through to the block renderers.
    pub audit: bool,
    /// Vertical scroll of the whole grid, in lines.
    pub scroll: u16,
    /// Last layout: each block's container rect on the virtual page (y from 0),
    /// None for empty / unplaced blocks. Drives spatial navigation.
    cells: Vec<Option<Rect>>,
    /// Inner scroll of the focused container.
    inner_scroll: u16,
}

impl BlockGrid {
    pub fn new() -> Self {
        Self::default()
    }

    /// Reset when the blocks change (e.g. another section selected).
    pub fn reset(&mut self) {
        *self = Self {
            audit: self.audit,
            ..Self::default()
        };
    }

    pub fn selected_source<'a>(&self, blocks: &'a [Block]) -> Option<&'a Source> {
        blocks.get(self.cursor.block)?.source(self.cursor.item)
    }

    pub fn render(&mut self, frame: &mut Frame, area: Rect, blocks: &[Block], theme: &Theme) {
        frame.render_stateful_widget(GridView { blocks, theme }, area, self);
    }

    /// Render over a bordered pane's *inner* area so the outer containers
    /// replace the pane's border instead of nesting inside it (no `││`).
    /// The pane's title is covered by the containers' titles. Box-drawing
    /// glyphs on the pane's border are merged with the containers' edges, so
    /// the pane's junctions with its neighbours (┬ ┴ ├ ┤) survive.
    pub fn render_in_frame(
        &mut self,
        frame: &mut Frame,
        inner: Rect,
        blocks: &[Block],
        theme: &Theme,
    ) {
        let outer = Rect {
            x: inner.x.saturating_sub(1),
            y: inner.y.saturating_sub(1),
            width: inner.width + 2,
            height: inner.height + 2,
        }
        .intersection(frame.area());
        if outer.is_empty() {
            return;
        }
        let (l, r, t, b) = (outer.x, outer.right() - 1, outer.y, outer.bottom() - 1);
        let edge: Vec<(u16, u16)> = (l..=r)
            .flat_map(|x| [(x, t), (x, b)])
            .chain((t..=b).flat_map(|y| [(l, y), (r, y)]))
            .collect();
        let before: Vec<String> = {
            let buf = frame.buffer_mut();
            edge.iter().map(|&p| buf[p].symbol().to_string()).collect()
        };
        self.render(frame, outer, blocks, theme);
        let buf = frame.buffer_mut();
        for (&p, old) in edge.iter().zip(&before) {
            let new = buf[p].symbol().to_string();
            if is_box(old) && is_box(&new) && *old != new {
                buf[p]
                    .set_symbol(old)
                    .merge_symbol(&new, MergeStrategy::Exact);
            }
        }
    }

    fn clamp(&mut self, blocks: &[Block]) {
        if blocks.get(self.cursor.block).is_none_or(Block::is_empty) {
            self.cursor = Cursor {
                block: blocks.iter().position(|b| !b.is_empty()).unwrap_or(0),
                item: 0,
            };
        }
        if let Some(b) = blocks.get(self.cursor.block) {
            self.cursor.item = self.cursor.item.min(b.len().saturating_sub(1));
        }
    }

    fn focus(&mut self, block: usize, item: usize) {
        if block != self.cursor.block {
            self.inner_scroll = 0;
        }
        self.cursor = Cursor { block, item };
    }

    /// Nearest container from the current one in direction (dx, dy): must lie
    /// fully on that side; ranked by distance along the axis, then by how far
    /// its centre is off the current one across it.
    fn neighbour(&self, dx: i32, dy: i32) -> Option<usize> {
        let cur = self.cells.get(self.cursor.block).copied().flatten()?;
        let (cx, cy) = centre(cur);
        self.cells
            .iter()
            .enumerate()
            .filter_map(|(i, r)| Some((i, (*r)?)))
            .filter(|&(i, r)| {
                i != self.cursor.block
                    && match (dx, dy) {
                        (1, _) => r.x >= cur.right().saturating_sub(1),
                        (-1, _) => r.right() <= cur.x + 1,
                        (_, 1) => r.y >= cur.bottom().saturating_sub(1),
                        _ => r.bottom() <= cur.y + 1,
                    }
            })
            .min_by_key(|&(_, r)| {
                let (x, y) = centre(r);
                if dx != 0 {
                    ((x - cx).abs(), (y - cy).abs())
                } else {
                    ((y - cy).abs(), (x - cx).abs())
                }
            })
            .map(|(i, _)| i)
    }

    /// Item of `block` closest to the cursor's current screen row (for h/l).
    fn item_at_row(&self, blocks: &[Block], block: usize, theme: &Theme) -> usize {
        let (Some(cur), Some(dst)) = (
            self.cells.get(self.cursor.block).copied().flatten(),
            self.cells.get(block).copied().flatten(),
        ) else {
            return 0;
        };
        let inner_w = dst.width.saturating_sub(2);
        let (_, items) = body_geom(
            &blocks[self.cursor.block],
            cur.width.saturating_sub(2),
            None,
            self.audit,
            theme,
        );
        let row = cur.y
            + 1
            + items
                .get(self.cursor.item)
                .map_or(0, |i| i.0)
                .saturating_sub(self.inner_scroll);
        let (_, dst_items) = body_geom(&blocks[block], inner_w, None, self.audit, theme);
        dst_items
            .iter()
            .enumerate()
            .min_by_key(|(_, (off, _))| (dst.y + 1 + off).abs_diff(row))
            .map_or(0, |(i, _)| i)
    }

    /// Reading-order step to the next / previous non-empty container.
    fn step_block(&mut self, blocks: &[Block], forward: bool) {
        let n = blocks.len();
        let next = if forward {
            (self.cursor.block + 1..n).find(|&i| !blocks[i].is_empty())
        } else {
            (0..self.cursor.block)
                .rev()
                .find(|&i| !blocks[i].is_empty())
        };
        if let Some(b) = next {
            self.focus(b, 0);
        }
    }

    /// Navigation keys (see module header). Returns true if handled.
    /// `theme` is needed to measure item rows for h/l.
    pub fn on_key(&mut self, key: KeyEvent, blocks: &[Block], theme: &Theme) -> bool {
        self.clamp(blocks);
        let Some(len) = blocks.get(self.cursor.block).map(Block::len) else {
            return false;
        };
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        match key.code {
            KeyCode::Char('d') if ctrl => {
                self.cursor.item = (self.cursor.item + JUMP).min(len.saturating_sub(1))
            }
            KeyCode::Char('u') if ctrl => self.cursor.item = self.cursor.item.saturating_sub(JUMP),
            _ if ctrl => return false,
            KeyCode::Char('j') | KeyCode::Down => {
                if self.cursor.item + 1 < len {
                    self.cursor.item += 1;
                } else if let Some(b) = self.neighbour(0, 1) {
                    self.focus(b, 0);
                }
            }
            KeyCode::Char('k') | KeyCode::Up => {
                if self.cursor.item > 0 {
                    self.cursor.item -= 1;
                } else if let Some(b) = self.neighbour(0, -1) {
                    self.focus(b, blocks[b].len().saturating_sub(1));
                }
            }
            KeyCode::Char('l') | KeyCode::Right => {
                if let Some(b) = self.neighbour(1, 0) {
                    let item = self.item_at_row(blocks, b, theme);
                    self.focus(b, item);
                }
            }
            KeyCode::Char('h') | KeyCode::Left => {
                if let Some(b) = self.neighbour(-1, 0) {
                    let item = self.item_at_row(blocks, b, theme);
                    self.focus(b, item);
                }
            }
            KeyCode::Tab => self.step_block(blocks, true),
            KeyCode::BackTab => self.step_block(blocks, false),
            KeyCode::Char('g') | KeyCode::Home => {
                let b = blocks.iter().position(|b| !b.is_empty()).unwrap_or(0);
                self.focus(b, 0);
            }
            KeyCode::Char('G') | KeyCode::End => {
                if let Some(b) = blocks.iter().rposition(|b| !b.is_empty()) {
                    self.focus(b, blocks[b].len() - 1);
                }
            }
            _ => return false,
        }
        true
    }
}

fn centre(r: Rect) -> (i32, i32) {
    (
        r.x as i32 + r.width as i32 / 2,
        r.y as i32 + r.height as i32 / 2,
    )
}

/// A single box-drawing glyph (U+2500..U+257F), i.e. a border cell.
fn is_box(s: &str) -> bool {
    let mut c = s.chars();
    matches!((c.next(), c.next()), (Some(ch), None) if ('\u{2500}'..='\u{257f}').contains(&ch))
}

fn is_wide(b: &Block) -> bool {
    match b {
        Block::Text { .. } => true,
        Block::Table { cols, .. } => cols.len() >= 5,
        _ => false,
    }
}

/// Rows of block indices, in reading order.
fn pack(blocks: &[Block], cols: usize) -> Vec<Vec<usize>> {
    let mut rows: Vec<Vec<usize>> = Vec::new();
    let mut cur: Vec<usize> = Vec::new();
    for (i, b) in blocks.iter().enumerate() {
        if b.is_empty() && !matches!(b, Block::Text { .. }) {
            continue;
        }
        if is_wide(b) || cols == 1 {
            if !cur.is_empty() {
                rows.push(std::mem::take(&mut cur));
            }
            rows.push(vec![i]);
            continue;
        }
        cur.push(i);
        if cur.len() == cols {
            rows.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        rows.push(cur);
    }
    rows
}

/// Stateless grid widget; state is the `BlockGrid` cursor / scroll / layout.
pub struct GridView<'a> {
    pub blocks: &'a [Block],
    pub theme: &'a Theme,
}

impl StatefulWidget for GridView<'_> {
    type State = BlockGrid;

    fn render(self, area: Rect, buf: &mut Buffer, st: &mut BlockGrid) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if area.is_empty() {
            return;
        }
        if self.blocks.iter().all(Block::is_empty) {
            Line::styled("no data", th.dim()).render(area, buf);
            return;
        }
        st.clamp(self.blocks);

        let density_cols = if area.width < 100 {
            1
        } else if area.width < 170 {
            2
        } else {
            3
        };
        let cols = density_cols.min((area.width / MIN_CELL_W).max(1) as usize);
        let rows = pack(self.blocks, cols);
        // Tall enough to show a whole short block, short enough that a
        // screen holds more than one row of containers.
        let cap = (area.height * 3 / 5).max(8);

        // ---- layout on a virtual page: rows overlap by one line, cells by one column
        st.cells = vec![None; self.blocks.len()];
        let mut y: u16 = 0;
        for row in &rows {
            let widths = Layout::horizontal(vec![Constraint::Fill(1); row.len()])
                .spacing(-1)
                .split(Rect::new(0, 0, area.width, 1));
            let h = row
                .iter()
                .zip(widths.iter())
                .map(|(&bi, r)| {
                    let sel = (st.cursor.block == bi).then_some(st.cursor.item);
                    body_geom(
                        &self.blocks[bi],
                        r.width.saturating_sub(2),
                        sel,
                        st.audit,
                        th,
                    )
                    .0 + 2
                })
                .max()
                .unwrap_or(3)
                .clamp(3, cap);
            for (&bi, r) in row.iter().zip(widths.iter()) {
                st.cells[bi] = Some(Rect {
                    x: r.x,
                    y,
                    width: r.width,
                    height: h,
                });
            }
            y += h - 1;
        }
        let total = y + 1;

        // ---- follow the focused container: whole container in view if it fits
        if let Some(c) = st.cells.get(st.cursor.block).copied().flatten() {
            if c.y < st.scroll {
                st.scroll = c.y;
            } else if c.bottom() > st.scroll + area.height {
                st.scroll = c.bottom().saturating_sub(area.height).min(c.y);
            }
        }
        st.scroll = st.scroll.min(total.saturating_sub(area.height));

        // ---- draw every container onto a virtual page, then copy the visible slice
        let mut page = Buffer::empty(Rect::new(0, 0, area.width, total));
        page.set_style(page.area, th.base());
        for (bi, cell) in st.cells.clone().iter().enumerate() {
            let Some(r) = *cell else { continue };
            let focused = bi == st.cursor.block;
            draw_container(&self.blocks[bi], r, &mut page, st, focused, th);
        }
        for dy in 0..area.height.min(total.saturating_sub(st.scroll)) {
            for x in 0..area.width {
                buf[(area.x + x, area.y + dy)] = page[(x, st.scroll + dy)].clone();
            }
        }
    }
}

fn draw_container(
    b: &Block,
    r: Rect,
    page: &mut Buffer,
    st: &mut BlockGrid,
    focused: bool,
    th: &Theme,
) {
    let edge = if focused { th.accent() } else { th.border() };
    // untitled blocks (a section's headline kv) get a bare top edge
    let mut title: Vec<Span> = (!b.title().is_empty())
        .then(|| {
            Span::styled(
                format!(" {} ", b.title()),
                if focused {
                    th.title().fg(th.accent)
                } else {
                    th.title()
                },
            )
        })
        .into_iter()
        .collect();
    if let Block::Series { unit, .. } | Block::Bars { unit, .. } = b
        && !unit.is_empty()
    {
        title.push(Span::styled(format!("{unit} "), th.dim()));
    }
    let frame = Frame_::bordered()
        .merge_borders(MergeStrategy::Exact)
        .border_style(edge)
        .style(th.base())
        .title_top(Line::from(title));
    let inner = frame.inner(r);
    frame.render(r, page);
    if inner.is_empty() {
        return;
    }

    // Body at full height, then the window of it that fits (focused container
    // scrolls to keep its cursor item visible).
    let sel = focused.then_some(st.cursor.item);
    let (h, items) = body_geom(b, inner.width, sel, st.audit, th);
    let h = h.max(1);
    let mut scroll = 0;
    if focused {
        if let Some(&(off, ih)) = items.get(st.cursor.item) {
            if off < st.inner_scroll {
                st.inner_scroll = off;
            } else if off + ih > st.inner_scroll + inner.height {
                st.inner_scroll = (off + ih).saturating_sub(inner.height);
            }
        }
        st.inner_scroll = st.inner_scroll.min(h.saturating_sub(inner.height));
        scroll = st.inner_scroll;
    }
    let mut tmp = Buffer::empty(Rect::new(0, 0, inner.width, h));
    tmp.set_style(tmp.area, th.base());
    draw_body(b, &mut tmp, sel, st.audit, th);
    for dy in 0..inner.height.min(h.saturating_sub(scroll)) {
        for x in 0..inner.width {
            page[(inner.x + x, inner.y + dy)] = tmp[(x, scroll + dy)].clone();
        }
    }
    // more below / above markers on the border
    if scroll > 0 {
        page.set_string(r.right().saturating_sub(3), r.y, "▲", th.dim());
    }
    if h > scroll + inner.height {
        page.set_string(r.right().saturating_sub(3), r.bottom() - 1, "▼", th.dim());
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::model::{BarItem, KvRow, Row};
    use crate::ui::spacing::{Density, Spacing};
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn kv(title: &str, n: usize) -> Block {
        Block::Kv {
            title: title.into(),
            rows: (0..n)
                .map(|i| KvRow {
                    label: format!("{title}{i}"),
                    value: format!("{i}"),
                    ..Default::default()
                })
                .collect(),
        }
    }
    fn blocks() -> Vec<Block> {
        vec![
            kv("A", 3),
            kv("B", 2),
            Block::Bars {
                title: "C".into(),
                unit: "$".into(),
                items: (0..3)
                    .map(|i| BarItem {
                        label: format!("q{i}"),
                        value: i as f64,
                        compare: Some(1.0),
                        ..Default::default()
                    })
                    .collect(),
            },
            kv("D", 4),
            Block::Table {
                title: "E".into(),
                cols: (0..5).map(|c| format!("c{c}")).collect(),
                rows: vec![Row {
                    cells: (0..5).map(|c| c.to_string()).collect(),
                    ..Default::default()
                }],
            },
            Block::Text {
                title: "F".into(),
                text: "rule text".into(),
                src: None,
            },
        ]
    }
    fn theme(d: Density) -> Theme {
        let mut t = Theme::default();
        t.spacing = Spacing::of(d);
        t
    }
    fn draw(g: &mut BlockGrid, b: &[Block], th: &Theme, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| g.render(f, f.area(), b, th)).unwrap();
        let buf = t.backend().buffer().clone();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| buf[(x, y)].symbol().to_string())
                    .collect::<String>()
                    + "\n"
            })
            .collect()
    }
    fn press(g: &mut BlockGrid, b: &[Block], th: &Theme, c: char) {
        g.on_key(KeyEvent::from(KeyCode::Char(c)), b, th);
    }

    #[test]
    fn packs_two_per_row_and_wide_blocks_alone() {
        assert_eq!(
            pack(&blocks(), 2),
            vec![vec![0, 1], vec![2, 3], vec![4], vec![5]]
        );
        assert_eq!(
            pack(&blocks(), 3),
            vec![vec![0, 1, 2], vec![3], vec![4], vec![5]]
        );
        assert_eq!(pack(&blocks(), 1).len(), 6);
    }

    #[test]
    fn hjkl_moves_spatially() {
        let b = blocks();
        let th = theme(Density::Normal);
        let mut g = BlockGrid::new();
        let out = draw(&mut g, &b, &th, 120, 40);
        assert!(out.contains(" A ") && out.contains(" B "), "{out}");
        press(&mut g, &b, &th, 'l');
        assert_eq!(g.cursor.block, 1, "l: A -> B");
        press(&mut g, &b, &th, 'h');
        assert_eq!(g.cursor.block, 0, "h: B -> A");
        for _ in 0..3 {
            press(&mut g, &b, &th, 'j');
        }
        assert_eq!(g.cursor.block, 2, "j past A's last item -> C below");
        press(&mut g, &b, &th, 'l');
        assert_eq!(g.cursor.block, 3, "l: C -> D");
        press(&mut g, &b, &th, 'G');
        assert_eq!(g.cursor.block, 5);
        press(&mut g, &b, &th, 'k');
        assert_eq!(g.cursor.block, 4, "k from F -> E above");
    }

    #[test]
    fn selected_source_follows_cursor_and_tiny_sizes_are_safe() {
        let b = blocks();
        let th = theme(Density::Compact);
        let mut g = BlockGrid::new();
        for (w, h) in [(0, 0), (1, 1), (10, 3), (40, 10), (200, 60)] {
            draw(&mut g, &b, &th, w, h);
        }
        g.cursor = Cursor { block: 3, item: 2 };
        assert!(g.selected_source(&b).is_none(), "fixture rows have no src");
        draw(&mut g, &[], &th, 40, 10);
    }
}
