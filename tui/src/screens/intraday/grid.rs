// The intraday layout: a grid of `cols` x `rows` cells, each tile covering a rectangle of
// them, tiles never overlapping and together covering the whole grid. Pure layout, no
// terminal, so the tests can check every operation.
//
//   split   `<space>w h/j/k/l`: a new column left / right of the focused tile, or a row
//           above / below it. The new tile takes the focused tile's span; tiles beside the
//           new line grow across it, so the grid stays covered.
//   eat     `m`, then hjkl: the focused tile grows over the cells around it. Tiles it
//           covers whole go; tiles it covers part of keep what is left (cut into rectangles).
//   close   `<space>w c`: the focused tile goes and the tiles along one side of it grow
//           into its place (refused when no side lines up with it exactly).
//
// After eat and close, grid lines no tile starts on are dropped (`compact`), so a 3x2
// grid where one tile now spans a whole column becomes the 2x2 it looks like.

use ratatui::layout::Rect;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Cell {
    pub col: u16,
    pub row: u16,
    pub w: u16,
    pub h: u16,
}

impl Cell {
    pub fn new(col: u16, row: u16, w: u16, h: u16) -> Self {
        Self { col, row, w, h }
    }
    fn right(self) -> u16 {
        self.col + self.w
    }
    fn bottom(self) -> u16 {
        self.row + self.h
    }
    fn t(self) -> Self {
        Self::new(self.row, self.col, self.h, self.w)
    }
    fn overlaps(self, o: Cell) -> bool {
        self.col < o.right() && o.col < self.right() && self.row < o.bottom() && o.row < self.bottom()
    }
    pub fn contains(self, o: Cell) -> bool {
        o.col >= self.col && o.row >= self.row && o.right() <= self.right() && o.bottom() <= self.bottom()
    }
    /// What is left of `self` once `cut` is taken out: up to four rectangles (the band
    /// above, below, then left and right of `cut`).
    fn minus(self, cut: Cell) -> Vec<Cell> {
        if !self.overlaps(cut) {
            return vec![self];
        }
        let mut out = Vec::new();
        if cut.row > self.row {
            out.push(Cell::new(self.col, self.row, self.w, cut.row - self.row));
        }
        if cut.bottom() < self.bottom() {
            out.push(Cell::new(self.col, cut.bottom(), self.w, self.bottom() - cut.bottom()));
        }
        let top = self.row.max(cut.row);
        let h = self.bottom().min(cut.bottom()) - top;
        if cut.col > self.col {
            out.push(Cell::new(self.col, top, cut.col - self.col, h));
        }
        if cut.right() < self.right() {
            out.push(Cell::new(cut.right(), top, self.right() - cut.right(), h));
        }
        out
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Dir {
    Left,
    Right,
    Up,
    Down,
}

impl Dir {
    pub fn from_key(c: char) -> Option<Dir> {
        match c {
            'h' => Some(Dir::Left),
            'l' => Some(Dir::Right),
            'k' => Some(Dir::Up),
            'j' => Some(Dir::Down),
            _ => None,
        }
    }
    fn vertical(self) -> bool {
        matches!(self, Dir::Up | Dir::Down)
    }
    /// The same direction with rows and columns swapped.
    fn t(self) -> Dir {
        match self {
            Dir::Left => Dir::Up,
            Dir::Right => Dir::Down,
            Dir::Up => Dir::Left,
            Dir::Down => Dir::Right,
        }
    }
}

/// What an operation did to the tile list, for the screen to mirror on its tiles.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Change {
    /// A tile was added at the end of the list, copying tile `from`'s ticker.
    Added { from: usize },
    /// Tile `i` was removed (list indices after it moved down one).
    Removed(usize),
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Grid {
    pub cols: u16,
    pub rows: u16,
    pub cells: Vec<Cell>,
}

/// Most tiles a grid holds (each one is a live feed and a picture).
pub const MAX_TILES: usize = 12;

impl Grid {
    /// `n` tiles in a near-square grid, row by row (4 -> 2x2).
    pub fn auto(n: usize) -> Self {
        let n = n.max(1);
        let cols = (n as f64).sqrt().ceil() as u16;
        let rows = (n as u16).div_ceil(cols);
        let mut cells: Vec<Cell> = (0..n as u16)
            .map(|i| Cell::new(i % cols, i / cols, 1, 1))
            .collect();
        // the last row's last tile stretches over any empty cells after it
        if let Some(last) = cells.last_mut() {
            last.w = cols - last.col;
        }
        Self { cols, rows, cells }
    }

    fn t(&self) -> Self {
        Self {
            cols: self.rows,
            rows: self.cols,
            cells: self.cells.iter().map(|c| c.t()).collect(),
        }
    }

    /// Screen rectangles for every tile in `area`; grid lines fall on whole cells.
    pub fn rects(&self, area: Rect) -> Vec<Rect> {
        let xs = edges(area.x, area.width, self.cols);
        let ys = edges(area.y, area.height, self.rows);
        self.cells
            .iter()
            .map(|c| {
                let x = xs[c.col as usize];
                let y = ys[c.row as usize];
                Rect::new(x, y, xs[c.right() as usize] - x, ys[c.bottom() as usize] - y)
            })
            .collect()
    }

    /// A new tile beside tile `f`, in direction `d`. Returns its index (the last).
    pub fn split(&mut self, f: usize, d: Dir) -> Option<usize> {
        if f >= self.cells.len() || self.cells.len() >= MAX_TILES {
            return None;
        }
        if d.vertical() {
            let mut g = self.t();
            let i = g.split(f, d.t())?;
            *self = g.t();
            return Some(i);
        }
        let fc = self.cells[f];
        let k = if d == Dir::Right { fc.right() } else { fc.col };
        for (i, c) in self.cells.iter_mut().enumerate() {
            if i == f {
                if d == Dir::Left {
                    c.col += 1;
                }
                continue;
            }
            match d {
                Dir::Right if c.col >= k => c.col += 1,
                Dir::Right if c.right() >= k => c.w += 1,
                Dir::Left if c.col > k => c.col += 1,
                Dir::Left if c.col == k || c.right() > k => c.w += 1,
                _ => {}
            }
        }
        self.cols += 1;
        self.cells.push(Cell::new(k, fc.row, 1, fc.h));
        Some(self.cells.len() - 1)
    }

    /// The tile next to `f` in direction `d`: touching its edge, nearest its middle.
    pub fn neighbor(&self, f: usize, d: Dir) -> Option<usize> {
        let fc = *self.cells.get(f)?;
        let mid = |c: Cell| (2 * c.col + c.w, 2 * c.row + c.h);
        let (fx, fy) = mid(fc);
        self.cells
            .iter()
            .enumerate()
            .filter(|&(i, c)| {
                i != f
                    && match d {
                        Dir::Right => c.col == fc.right() && c.row < fc.bottom() && fc.row < c.bottom(),
                        Dir::Left => c.right() == fc.col && c.row < fc.bottom() && fc.row < c.bottom(),
                        Dir::Down => c.row == fc.bottom() && c.col < fc.right() && fc.col < c.right(),
                        Dir::Up => c.bottom() == fc.row && c.col < fc.right() && fc.col < c.right(),
                    }
            })
            .min_by_key(|(_, c)| {
                let (x, y) = mid(**c);
                if d.vertical() { x.abs_diff(fx) } else { y.abs_diff(fy) }
            })
            .map(|(i, _)| i)
    }

    /// `target` grown one cell from `t` in direction `d` (kept inside the grid).
    pub fn grow(&self, t: Cell, d: Dir) -> Cell {
        let mut t = t;
        match d {
            Dir::Left if t.col > 0 => {
                t.col -= 1;
                t.w += 1;
            }
            Dir::Right if t.right() < self.cols => t.w += 1,
            Dir::Up if t.row > 0 => {
                t.row -= 1;
                t.h += 1;
            }
            Dir::Down if t.bottom() < self.rows => t.h += 1,
            _ => {}
        }
        t
    }

    /// Tile `f` takes `target` (which must contain it). Tiles inside it go; tiles partly
    /// inside keep the rest, cut into rectangles (extra pieces are new tiles).
    pub fn eat(&mut self, f: usize, target: Cell) -> Vec<Change> {
        let mut changes = Vec::new();
        if f >= self.cells.len() || !target.contains(self.cells[f]) {
            return changes;
        }
        self.cells[f] = target;
        let mut i = 0;
        let mut owner = f;
        while i < self.cells.len() {
            if i == owner || !self.cells[i].overlaps(target) {
                i += 1;
                continue;
            }
            let rest = self.cells[i].minus(target);
            if rest.is_empty() {
                self.cells.remove(i);
                changes.push(Change::Removed(i));
                if owner > i {
                    owner -= 1;
                }
                continue;
            }
            self.cells[i] = rest[0];
            for piece in &rest[1..] {
                self.cells.push(*piece);
                changes.push(Change::Added { from: i });
            }
            i += 1;
        }
        changes.extend(self.compact_changes());
        changes
    }

    /// Removes tile `f`, growing the tiles along one of its sides into the space. None when
    /// no side's tiles line up with it exactly (or it is the last tile).
    pub fn close(&mut self, f: usize) -> Option<Vec<Change>> {
        if self.cells.len() < 2 || f >= self.cells.len() {
            return None;
        }
        let fc = self.cells[f];
        // left and up first: a tile split off to the right or below gives its space back
        // to the tile it came from
        for d in [Dir::Left, Dir::Up, Dir::Right, Dir::Down] {
            let side: Vec<usize> = (0..self.cells.len())
                .filter(|&i| {
                    let c = self.cells[i];
                    i != f
                        && match d {
                            Dir::Right => c.col == fc.right() && c.row < fc.bottom() && fc.row < c.bottom(),
                            Dir::Left => c.right() == fc.col && c.row < fc.bottom() && fc.row < c.bottom(),
                            Dir::Down => c.row == fc.bottom() && c.col < fc.right() && fc.col < c.right(),
                            Dir::Up => c.bottom() == fc.row && c.col < fc.right() && fc.col < c.right(),
                        }
                })
                .collect();
            let fits = !side.is_empty()
                && side.iter().all(|&i| {
                    let c = self.cells[i];
                    if d.vertical() {
                        c.col >= fc.col && c.right() <= fc.right()
                    } else {
                        c.row >= fc.row && c.bottom() <= fc.bottom()
                    }
                });
            if !fits {
                continue;
            }
            for &i in &side {
                let c = &mut self.cells[i];
                match d {
                    Dir::Right => {
                        c.col = fc.col;
                        c.w += fc.w;
                    }
                    Dir::Left => c.w += fc.w,
                    Dir::Down => {
                        c.row = fc.row;
                        c.h += fc.h;
                    }
                    Dir::Up => c.h += fc.h,
                }
            }
            self.cells.remove(f);
            let mut changes = vec![Change::Removed(f)];
            changes.extend(self.compact_changes());
            return Some(changes);
        }
        None
    }

    /// Drops grid lines no tile starts on (no change to the tile list).
    fn compact_changes(&mut self) -> Vec<Change> {
        self.compact_cols();
        let mut g = self.t();
        g.compact_cols();
        *self = g.t();
        Vec::new()
    }

    fn compact_cols(&mut self) {
        let mut x = 1;
        while x < self.cols {
            if self.cells.iter().any(|c| c.col == x) {
                x += 1;
                continue;
            }
            for c in self.cells.iter_mut() {
                if c.col > x {
                    c.col -= 1;
                } else if c.right() > x {
                    c.w -= 1;
                }
            }
            self.cols -= 1;
        }
    }

    /// Every cell of the grid is covered by exactly one tile.
    #[cfg(test)]
    fn valid(&self) -> bool {
        let mut seen = vec![0u8; self.cols as usize * self.rows as usize];
        for c in &self.cells {
            if c.w == 0 || c.h == 0 || c.right() > self.cols || c.bottom() > self.rows {
                return false;
            }
            for y in c.row..c.bottom() {
                for x in c.col..c.right() {
                    seen[y as usize * self.cols as usize + x as usize] += 1;
                }
            }
        }
        seen.iter().all(|&n| n == 1)
    }
}

/// `n + 1` boundaries splitting `len` cells from `start` into `n` near-equal parts.
fn edges(start: u16, len: u16, n: u16) -> Vec<u16> {
    let n = n.max(1) as u32;
    (0..=n)
        .map(|i| start + (len as u32 * i / n) as u16)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn auto_lays_out_near_square_grids() {
        let g = Grid::auto(4);
        assert_eq!((g.cols, g.rows), (2, 2));
        assert!(g.valid());
        let g = Grid::auto(3);
        assert_eq!((g.cols, g.rows), (2, 2));
        assert_eq!(g.cells[2], Cell::new(0, 1, 2, 1));
        assert!(g.valid());
    }

    #[test]
    fn split_adds_a_column_or_row_beside_the_focus() {
        for d in [Dir::Left, Dir::Right, Dir::Up, Dir::Down] {
            let mut g = Grid::auto(4);
            let new = g.split(0, d).unwrap();
            assert_eq!(new, 4);
            assert!(g.valid(), "{d:?}: {g:?}");
            let side = g.neighbor(0, d).unwrap();
            assert_eq!(side, new, "{d:?}: the new tile sits on that side of the focus");
        }
        let mut g = Grid::auto(4);
        g.split(0, Dir::Right);
        // tile 1 (top right) grew across the new column; bottom row too
        assert_eq!((g.cols, g.rows), (3, 2));
        assert_eq!(g.cells[0], Cell::new(0, 0, 1, 1));
        assert_eq!(g.cells[4], Cell::new(1, 0, 1, 1));
        assert_eq!(g.cells[2], Cell::new(0, 1, 2, 1));
    }

    #[test]
    fn eat_takes_neighbours_and_keeps_what_is_left() {
        // 2x2: tile 0 eats down then right -> whole grid
        let mut g = Grid::auto(4);
        let t = g.grow(g.cells[0], Dir::Down);
        let t = g.grow(t, Dir::Right);
        let ch = g.eat(0, t);
        assert_eq!(ch.iter().filter(|c| matches!(c, Change::Removed(_))).count(), 3);
        assert_eq!(g.cells.len(), 1);
        assert_eq!((g.cols, g.rows), (1, 1));
        assert!(g.valid());

        // 3x3, centre eats right: the right column's middle goes, nothing else changes
        let mut g = Grid::auto(9);
        let t = g.grow(g.cells[4], Dir::Right);
        g.eat(4, t);
        assert!(g.valid());
        assert_eq!(g.cells.len(), 8);

        // a tall tile partly eaten keeps the rest
        let mut g = Grid {
            cols: 2,
            rows: 2,
            cells: vec![Cell::new(0, 0, 1, 1), Cell::new(1, 0, 1, 2), Cell::new(0, 1, 1, 1)],
        };
        let t = g.grow(g.cells[0], Dir::Right);
        let ch = g.eat(0, t);
        assert!(ch.is_empty());
        assert!(g.valid());
        assert_eq!(g.cells[1], Cell::new(1, 1, 1, 1));
    }

    #[test]
    fn eat_through_the_middle_cuts_the_rest_into_new_tiles() {
        // a wide bottom tile, eaten in its middle column from above
        let mut g = Grid {
            cols: 3,
            rows: 2,
            cells: vec![
                Cell::new(0, 0, 1, 1),
                Cell::new(1, 0, 1, 1),
                Cell::new(2, 0, 1, 1),
                Cell::new(0, 1, 3, 1),
            ],
        };
        let t = g.grow(g.cells[1], Dir::Down);
        let ch = g.eat(1, t);
        assert_eq!(ch, vec![Change::Added { from: 3 }]);
        assert!(g.valid());
        assert_eq!(g.cells.len(), 5);
    }

    #[test]
    fn close_gives_the_space_to_a_side_that_lines_up() {
        let mut g = Grid::auto(4);
        let ch = g.close(0).unwrap();
        assert_eq!(ch, vec![Change::Removed(0)]);
        assert!(g.valid());
        assert_eq!(g.cells.len(), 3);
        // the old tile 1 (top right) took the whole top row
        assert_eq!(g.cells[0], Cell::new(0, 0, 2, 1));
        let mut one = Grid::auto(1);
        assert!(one.close(0).is_none());
        // split then close is back where it started
        let mut g = Grid::auto(4);
        let n = g.split(1, Dir::Down).unwrap();
        g.close(n).unwrap();
        assert_eq!(g, Grid::auto(4));
    }

    #[test]
    fn rects_tile_the_area_without_gaps() {
        let mut g = Grid::auto(4);
        g.split(3, Dir::Right);
        let r = g.rects(Rect::new(0, 0, 100, 40));
        let area: u32 = r.iter().map(|r| r.width as u32 * r.height as u32).sum();
        assert_eq!(area, 4000);
    }

    #[test]
    fn neighbors_follow_the_layout() {
        let g = Grid::auto(4);
        assert_eq!(g.neighbor(0, Dir::Right), Some(1));
        assert_eq!(g.neighbor(0, Dir::Down), Some(2));
        assert_eq!(g.neighbor(0, Dir::Left), None);
        assert_eq!(g.neighbor(3, Dir::Up), Some(1));
    }
}
