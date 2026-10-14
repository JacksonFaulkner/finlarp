// Candlestick chart: OHLC candles on a price axis with a volume strip.
// Missing data is never drawn; the caller passes real bars.
//
// Two widths, picked from how many bars fit:
//   wide    3 cols per bar (body 5 subpixels, wick on the centre subpixel)
//   narrow  2 cols per bar (body 3 subpixels, wick on the centre subpixel)
// Bars that fit narrow are all kept (wide if they also fit wide); otherwise
// they are merged (`fit`): open of the first, close of the
// last, extremes of the group, volume summed.
//
// Candles are drawn as a bitmap of subpixels, 2 across by 3 down per cell, and
// each cell becomes the matching sextant glyph (U+1FB00..), so the body and a
// centred one-pixel wick always join. A 14-row pane resolves 42 price levels.

use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::Style;
use ratatui::widgets::Widget;

use crate::model::Candle;
use crate::ui::theme::Theme;

/// Columns reserved on the left for price labels.
pub const AXIS_W: u16 = 8;
/// Rows used by the volume strip when the area is tall enough.
const VOL_ROWS: u16 = 2;
const MIN_H_FOR_VOLUME: u16 = 12;

/// Merge `bars` so they fit an area `width` columns wide. Returns the bars
/// the widget will draw (pass these, not the originals, to `CandleChart`).
pub fn fit(bars: &[Candle], width: u16) -> Vec<Candle> {
    let plot_w = width.saturating_sub(AXIS_W) as usize;
    let (narrow, wide) = (plot_w / 2, plot_w / 3);
    if bars.is_empty() || narrow == 0 {
        return Vec::new();
    }
    // Keep every bar if they fit narrow; else prefer wide candles when
    // merging pairs gets there; else merge into narrow slots.
    let group = if bars.len() <= narrow {
        1
    } else if wide > 0 && bars.len().div_ceil(wide) <= 2 {
        bars.len().div_ceil(wide)
    } else {
        bars.len().div_ceil(narrow)
    };
    if group == 1 {
        return bars.to_vec();
    }
    bars.chunks(group).map(merge).collect()
}

fn merge(g: &[Candle]) -> Candle {
    let (first, last) = (&g[0], &g[g.len() - 1]);
    Candle {
        date: last.date.clone(),
        open: first.open,
        high: g.iter().map(|c| c.high).fold(f64::MIN, f64::max),
        low: g.iter().map(|c| c.low).fold(f64::MAX, f64::min),
        close: last.close,
        volume: g.iter().map(|c| c.volume).sum(),
    }
}

pub struct CandleChart<'a> {
    bars: &'a [Candle],
    theme: &'a Theme,
    selected: Option<usize>,
}

impl<'a> CandleChart<'a> {
    pub fn new(bars: &'a [Candle], theme: &'a Theme) -> Self {
        Self {
            bars,
            theme,
            selected: None,
        }
    }

    pub fn selected(mut self, selected: Option<usize>) -> Self {
        self.selected = selected;
        self
    }
}

/// Subpixels per cell: 2 across, 3 down.
const SUB_X: usize = 2;
const SUB_Y: usize = 3;

/// Glyph for a 6-bit sextant mask: bit0 top-left, bit1 top-right, bit2
/// mid-left, bit3 mid-right, bit4 bottom-left, bit5 bottom-right.
pub fn sextant(mask: u8) -> char {
    match mask & 0x3f {
        0 => ' ',
        0x15 => '▌',
        0x2a => '▐',
        0x3f => '█',
        m => {
            // Unicode skips the empty, left-half, right-half and full cells.
            let idx = m as u32 - 1 - (m > 0x15) as u32 - (m > 0x2a) as u32;
            char::from_u32(0x1FB00 + idx).unwrap_or(' ')
        }
    }
}

/// Subpixel columns of a bar: (body width, wick column, cell columns).
fn bar_cols(wide: bool) -> (usize, usize) {
    // Odd body widths leave a single centre column for the wick.
    if wide { (5, 2) } else { (3, 1) }
}

const EIGHTHS: [char; 9] = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];

impl Widget for CandleChart<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if self.bars.is_empty() || area.width <= AXIS_W + 2 || area.height < 3 {
            return;
        }
        let t = self.theme;
        let vol_rows = if area.height >= MIN_H_FOR_VOLUME {
            VOL_ROWS
        } else {
            0
        };
        let price_h = area.height - vol_rows;
        let plot_x = area.x + AXIS_W;
        let plot_w = (area.width - AXIS_W) as usize;
        let wide = self.bars.len() * 3 <= plot_w;
        let cell_w: usize = if wide { 3 } else { 2 };

        let hi = self.bars.iter().map(|c| c.high).fold(f64::MIN, f64::max);
        let lo = self.bars.iter().map(|c| c.low).fold(f64::MAX, f64::min);
        let span = (hi - lo).max(f64::EPSILON * hi.abs().max(1.0));
        let sub_rows = price_h as usize * SUB_Y;
        let row = |v: f64| (((hi - v) / span) * (sub_rows - 1) as f64).round() as usize;

        // Price axis: top, middle, bottom.
        let dim = Style::new().fg(t.dim);
        for (y, v) in [(0, hi), (price_h / 2, (hi + lo) / 2.0), (price_h - 1, lo)] {
            buf.set_stringn(
                area.x,
                area.y + y,
                format!("{v:>7.2} "),
                AXIS_W as usize,
                dim,
            );
        }

        let max_vol = self.bars.iter().map(|c| c.volume).max().unwrap_or(1).max(1) as f64;
        for (i, c) in self.bars.iter().enumerate() {
            let x0 = plot_x + (i * cell_w) as u16;
            if x0 + cell_w as u16 > area.x + area.width + 1 {
                break;
            }
            let style = Style::new().fg(if c.is_up() { t.up } else { t.down });
            let (rh, rl) = (row(c.high), row(c.low));
            let (ro, rc) = (row(c.open), row(c.close));
            let (bt, bb) = (ro.min(rc), ro.max(rc));
            let (body_w, wick_x) = bar_cols(wide);
            let px = |sx: usize, sy: usize| {
                (sx < body_w && (bt..=bb).contains(&sy))
                    || (sx == wick_x && (rh..=rl).contains(&sy))
            };
            let cursor = self.selected == Some(i);
            for y in 0..price_h {
                let py = area.y + y;
                let mut any = false;
                for dx in 0..cell_w {
                    let mut mask = 0u8;
                    for sy in 0..SUB_Y {
                        for sx in 0..SUB_X {
                            if px(dx * SUB_X + sx, y as usize * SUB_Y + sy) {
                                mask |= 1 << (sy * SUB_X + sx);
                            }
                        }
                    }
                    if mask != 0 {
                        any = true;
                        buf.set_string(x0 + dx as u16, py, sextant(mask).to_string(), style);
                    }
                }
                if !any && cursor {
                    buf.set_string(x0, py, "┊", dim);
                }
            }
            if vol_rows > 0 {
                let levels = ((c.volume as f64 / max_vol) * (vol_rows * 8) as f64).ceil() as usize;
                for r in 0..vol_rows as usize {
                    // Row 0 is the top of the strip.
                    let below = (vol_rows as usize - 1 - r) * 8;
                    let fill = levels.saturating_sub(below).min(8);
                    let g = EIGHTHS[fill].to_string();
                    let py = area.y + price_h + r as u16;
                    for dx in 0..(cell_w as u16 - 1) {
                        buf.set_string(x0 + dx, py, &g, style);
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mock;
    use chrono::NaiveDate;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn bars(n: usize) -> Vec<Candle> {
        let end = NaiveDate::from_ymd_opt(2026, 10, 14).unwrap();
        mock::candles(mock::seed_for("SPRB"), n, 39.26, 0.045, end)
    }

    fn draw(w: u16, h: u16, b: &[Candle], sel: Option<usize>) -> String {
        let th = Theme::default();
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| f.render_widget(CandleChart::new(b, &th).selected(sel), f.area()))
            .unwrap();
        let buf = t.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| buf[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn fit_keeps_bars_that_fit_and_merges_the_rest() {
        let b = bars(120);
        assert_eq!(fit(&b, 8 + 240).len(), 120);
        let m = fit(&b, 8 + 100);
        assert!(m.len() <= 50 && m.len() >= 40);
        assert_eq!(m[0].open, b[0].open);
        assert_eq!(m.last().unwrap().close, b[119].close);
        assert_eq!(
            m.iter().map(|c| c.volume).sum::<u64>(),
            b.iter().map(|c| c.volume).sum::<u64>()
        );
        assert!(fit(&b, 5).is_empty() && fit(&[], 100).is_empty());
    }

    #[test]
    fn draws_axis_candles_and_volume() {
        let b = bars(20);
        let out = draw(80, 16, &b, None);
        let first = out.lines().next().unwrap();
        let hi = b.iter().map(|c| c.high).fold(f64::MIN, f64::max);
        assert!(first.starts_with(&format!("{hi:>7.2}")), "{first}");
        assert!(out.contains('█') || out.contains('▀') || out.contains('▄'));
        assert!(
            out.lines()
                .last()
                .unwrap()
                .chars()
                .any(|c| "▁▂▃▄▅▆▇█".contains(c))
        );
    }

    #[test]
    fn wide_vs_narrow_by_bar_count() {
        let glyph = |c: char| ('\u{1FB00}'..='\u{1FB3B}').contains(&c) || "▌▐█".contains(c);
        let few = draw(60, 16, &bars(10), None); // 10*3 <= 52: wide
        let many = draw(60, 16, &fit(&bars(120), 60), None); // narrow
        assert!(few.chars().any(glyph));
        assert!(many.chars().any(glyph));
        // Wide bars use 3 cells each, so the same bars span more columns.
        let used = |s: &str| {
            s.lines()
                .take(16)
                .map(|l| l.trim_end().chars().count())
                .max()
                .unwrap_or(0)
        };
        assert_eq!(used(&few), AXIS_W as usize + 9 * 3 + 3);
    }

    #[test]
    fn cursor_marks_blank_cells_of_selected_bar() {
        let out = draw(80, 16, &bars(20), Some(3));
        assert!(out.contains('┊'));
        assert!(!draw(80, 16, &bars(20), None).contains('┊'));
    }

    #[test]
    fn sextant_masks_map_to_glyphs() {
        assert_eq!(sextant(0), ' ');
        assert_eq!(sextant(0x3f), '█');
        assert_eq!(sextant(0x15), '▌');
        assert_eq!(sextant(0x2a), '▐');
        assert_eq!(sextant(0x01), '\u{1FB00}');
        assert_eq!(sextant(0x3e), '\u{1FB3B}');
    }

    #[test]
    fn wick_column_joins_body_without_gap() {
        // A tall wick over a body: every cell in the wick's column is filled.
        let mut b = bars(1);
        b[0].high = 120.0;
        b[0].low = 80.0;
        b[0].open = 99.0;
        b[0].close = 101.0;
        let out = draw(20, 8, &b, None);
        let col: Vec<char> = out
            .lines()
            .take(8)
            .map(|l| l.chars().nth(AXIS_W as usize + 1).unwrap_or(' '))
            .collect();
        assert!(col.iter().all(|c| *c != ' '), "gap in wick column: {col:?}");
    }

    #[test]
    fn flat_series_and_tiny_areas_do_not_panic() {
        let flat = vec![
            Candle {
                date: "d".into(),
                open: 5.0,
                high: 5.0,
                low: 5.0,
                close: 5.0,
                volume: 0
            };
            3
        ];
        draw(40, 10, &flat, Some(1));
        draw(10, 2, &bars(5), None);
        draw(40, 10, &[], None);
    }

    #[test]
    fn short_area_drops_volume_strip() {
        let tall = draw(60, 16, &bars(10), None);
        let short = draw(60, 10, &bars(10), None);
        let vol = |s: &str| {
            s.lines()
                .last()
                .unwrap()
                .chars()
                .any(|c| "▁▂▃▅▆▇".contains(c))
        };
        assert!(vol(&tall));
        assert!(!vol(&short));
    }
}
