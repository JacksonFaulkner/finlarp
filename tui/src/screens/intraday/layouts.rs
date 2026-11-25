// Saved intraday layouts: the grid (which cells each tile covers) and each tile's ticker.
// Every edit (split, eat, close, a new ticker) saves the layout on screen, under its own id,
// to data/intraday_layouts.json; `f` lists them and loads one. `fl intraday` with no tickers
// opens the most recently edited one.

use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use super::grid::{Cell, Grid};

/// Overrides the file (tests).
pub const FILE_ENV: &str = "FL_LAYOUTS_FILE";
/// Oldest layouts drop off past this many.
const MAX: usize = 40;

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct Layout {
    pub id: u64,
    pub cols: u16,
    pub rows: u16,
    /// [col, row, w, h] per tile, in tile order.
    pub cells: Vec<[u16; 4]>,
    pub symbols: Vec<String>,
    /// Seconds since the epoch, last edit.
    pub updated: u64,
}

impl Layout {
    pub fn from_grid(id: u64, grid: &Grid, symbols: Vec<String>) -> Self {
        Self {
            id,
            cols: grid.cols,
            rows: grid.rows,
            cells: grid.cells.iter().map(|c| [c.col, c.row, c.w, c.h]).collect(),
            symbols,
            updated: now(),
        }
    }

    pub fn grid(&self) -> Grid {
        Grid {
            cols: self.cols,
            rows: self.rows,
            cells: self
                .cells
                .iter()
                .map(|c| Cell::new(c[0], c[1], c[2], c[3]))
                .collect(),
        }
    }

    /// Usable: one ticker per cell, cells inside the grid.
    pub fn valid(&self) -> bool {
        !self.cells.is_empty()
            && self.cells.len() == self.symbols.len()
            && self
                .cells
                .iter()
                .all(|c| c[2] > 0 && c[3] > 0 && c[0] + c[2] <= self.cols && c[1] + c[3] <= self.rows)
    }

    /// `3x2 · SPY QQQ NVDA AAPL MU`
    pub fn label(&self) -> String {
        format!("{}x{} · {}", self.cols, self.rows, self.symbols.join(" "))
    }
}

fn now() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

pub fn path() -> PathBuf {
    std::env::var_os(FILE_ENV)
        .map(PathBuf::from)
        .unwrap_or_else(|| crate::data_dir().join("intraday_layouts.json"))
}

/// Every saved layout, most recently edited first.
pub fn load() -> Vec<Layout> {
    let mut v: Vec<Layout> = std::fs::read_to_string(path())
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default();
    v.retain(Layout::valid);
    v.sort_by(|a, b| b.updated.cmp(&a.updated));
    v
}

fn store(v: &[Layout]) {
    // tests never touch the real file
    if cfg!(test) && std::env::var_os(FILE_ENV).is_none() {
        return;
    }
    let p = path();
    if let Some(d) = p.parent() {
        let _ = std::fs::create_dir_all(d);
    }
    let _ = std::fs::write(p, serde_json::to_string_pretty(v).unwrap_or_default());
}

/// Saves `l`, replacing the layout with its id.
pub fn save(l: Layout) {
    let mut v = load();
    v.retain(|x| x.id != l.id);
    v.insert(0, l);
    v.truncate(MAX);
    store(&v);
}

pub fn delete(id: u64) {
    let mut v = load();
    v.retain(|x| x.id != id);
    store(&v);
}

/// An id for a new layout.
pub fn new_id() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(1)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::intraday::grid::Dir;

    #[test]
    fn round_trips_a_grid() {
        let mut g = Grid::auto(4);
        g.split(0, Dir::Right);
        let syms: Vec<String> = ["A", "B", "C", "D", "E"].map(String::from).to_vec();
        let l = Layout::from_grid(7, &g, syms);
        assert!(l.valid());
        assert_eq!(l.grid(), g);
        assert_eq!(l.label(), "3x2 · A B C D E");
        let mut bad = l.clone();
        bad.symbols.pop();
        assert!(!bad.valid());
    }
}
