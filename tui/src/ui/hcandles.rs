// Horizontal candlesticks for the intraday tape: time runs down (one terminal
// row per bar, newest last), price runs left to right.
//
//   ▸09:35 ▏ ──▐███▌──          ▏▎  vol
//   time    price plot           volume
//
// Like ui::candles, bars are drawn as a subpixel bitmap (2 across x 3 down per
// cell) and each cell becomes a sextant glyph. Three rows per bar is odd, so
// the wick sits exactly on the middle row and the body fills all three: the
// wick and body can never miss each other. Price resolution is two subpixels
// per column, so a 60-column plot resolves 120 price levels.
//
// Overlays are single-subpixel-wide vertical lines drawn only where no bar is:
//   VWAP         accent colour
//   prev close   dim dotted
// Rows outside the regular session (`ext`) are drawn dimmed.

use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Modifier, Style};
use ratatui::widgets::Widget;

use crate::ui::candles::sextant;
use crate::ui::theme::Theme;

/// Columns left of the plot: cursor marker + "HH:MM" + gap.
pub const TIME_W: u16 = 7;
const SUB_X: usize = 2;
const SUB_Y: usize = 3;
const EIGHTHS: [char; 9] = [' ', '▏', '▎', '▍', '▌', '▋', '▊', '▉', '█'];

/// One drawn bar (already aggregated to the chosen interval).
#[derive(Debug, Clone, PartialEq)]
pub struct HBar {
    pub label: String,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: u64,
    /// Pre- or post-market.
    pub ext: bool,
}

impl HBar {
    pub fn is_up(&self) -> bool {
        self.close >= self.open
    }
}

pub struct HCandles<'a> {
    bars: &'a [HBar],
    theme: &'a Theme,
    vwap: Option<f64>,
    prev_close: Option<f64>,
    selected: Option<usize>,
}

impl<'a> HCandles<'a> {
    pub fn new(bars: &'a [HBar], theme: &'a Theme) -> Self {
        Self {
            bars,
            theme,
            vwap: None,
            prev_close: None,
            selected: None,
        }
    }

    pub fn vwap(mut self, v: Option<f64>) -> Self {
        self.vwap = v;
        self
    }

    pub fn prev_close(mut self, v: Option<f64>) -> Self {
        self.prev_close = v;
        self
    }

    pub fn selected(mut self, s: Option<usize>) -> Self {
        self.selected = s;
        self
    }

    /// Bars that fit in a chart `height` rows tall (one row is the price axis).
    pub fn capacity(height: u16) -> usize {
        height.saturating_sub(1) as usize
    }
}

/// Volume column width for a chart `width` columns wide.
fn vol_w(width: u16) -> u16 {
    if width >= 56 {
        8
    } else if width >= 36 {
        5
    } else {
        0
    }
}

impl Widget for HCandles<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let vw = vol_w(area.width);
        if self.bars.is_empty() || area.height < 2 || area.width < TIME_W + vw + 6 {
            return;
        }
        let t = self.theme;
        let dim = Style::new().fg(t.dim);
        let plot_x = area.x + TIME_W;
        let plot_w = (area.width - TIME_W - vw) as usize;
        let sub_w = plot_w * SUB_X;
        let rows = Self::capacity(area.height).min(self.bars.len());

        let shown = &self.bars[self.bars.len() - rows..];
        let hi = shown.iter().map(|b| b.high).fold(f64::MIN, f64::max);
        let lo = shown.iter().map(|b| b.low).fold(f64::MAX, f64::min);
        let span = (hi - lo).max(f64::EPSILON * hi.abs().max(1.0));
        let col = |v: f64| (((v - lo) / span) * (sub_w - 1) as f64).round() as usize;
        let inside = |v: Option<f64>| v.filter(|v| (lo..=hi).contains(v)).map(col);
        let (vwap_x, prev_x) = (inside(self.vwap), inside(self.prev_close));

        // Price axis: low, middle, high along the top row.
        let label = |v: f64| format!("{v:.2}");
        let (l, m, h) = (label(lo), label((lo + hi) / 2.0), label(hi));
        buf.set_stringn(plot_x, area.y, &l, plot_w, dim);
        let mid_x = plot_x + (plot_w.saturating_sub(m.len()) / 2) as u16;
        if mid_x > plot_x + l.len() as u16 + 1
            && mid_x + (m.len() as u16) + 1 < plot_x + plot_w as u16
        {
            buf.set_stringn(mid_x, area.y, &m, plot_w, dim);
        }
        let hx = plot_x + plot_w.saturating_sub(h.len()) as u16;
        if hx > plot_x + l.len() as u16 + 1 {
            buf.set_stringn(hx, area.y, &h, plot_w, dim);
        }

        let max_vol = shown.iter().map(|b| b.volume).max().unwrap_or(1).max(1) as f64;
        let first_idx = self.bars.len() - rows;
        for (r, b) in shown.iter().enumerate() {
            let y = area.y + 1 + r as u16;
            let cursor = self.selected == Some(first_idx + r);
            let color = if b.is_up() { t.up } else { t.down };
            let mut style = Style::new().fg(color);
            if b.ext {
                style = style.add_modifier(Modifier::DIM);
            }
            let label_style = if cursor {
                Style::new().fg(t.accent)
            } else {
                dim
            };
            buf.set_string(area.x, y, if cursor { "▸" } else { " " }, label_style);
            buf.set_string(area.x + 1, y, &b.label, label_style);

            let (po, pc) = (col(b.open), col(b.close));
            let (body_l, body_r) = (po.min(pc), po.max(pc));
            let (wick_l, wick_r) = (col(b.low), col(b.high));
            let px = |sx: usize, sy: usize| {
                (sx >= body_l && sx <= body_r) || (sy == 1 && sx >= wick_l && sx <= wick_r)
            };
            for cx in 0..plot_w {
                let mut mask = 0u8;
                for sy in 0..SUB_Y {
                    for sx in 0..SUB_X {
                        if px(cx * SUB_X + sx, sy) {
                            mask |= 1 << (sy * SUB_X + sx);
                        }
                    }
                }
                let x = plot_x + cx as u16;
                if mask != 0 {
                    buf.set_string(x, y, sextant(mask).to_string(), style);
                } else if let Some(g) = overlay(cx, vwap_x, prev_x) {
                    let st = if g.vwap {
                        Style::new().fg(t.accent)
                    } else {
                        dim
                    };
                    buf.set_string(x, y, g.ch.to_string(), st);
                }
            }

            if vw > 0 {
                let levels =
                    ((b.volume as f64 / max_vol) * (vw as usize * 8) as f64).ceil() as usize;
                for c in 0..vw as usize {
                    let fill = levels.saturating_sub(c * 8).min(8);
                    if fill > 0 {
                        let x = plot_x + plot_w as u16 + c as u16;
                        buf.set_string(
                            x,
                            y,
                            EIGHTHS[fill].to_string(),
                            style.add_modifier(Modifier::DIM),
                        );
                    }
                }
            }
        }
    }
}

struct Overlay {
    ch: char,
    vwap: bool,
}

/// Glyph for the VWAP / previous-close lines in an otherwise empty cell.
fn overlay(cx: usize, vwap_x: Option<usize>, prev_x: Option<usize>) -> Option<Overlay> {
    let hit = |x: Option<usize>| x.filter(|x| x / SUB_X == cx);
    if let Some(x) = hit(vwap_x) {
        // one subpixel column: left or right half of the cell, full height
        let mask = if x % SUB_X == 0 { 0x15 } else { 0x2a };
        return Some(Overlay {
            ch: sextant(mask),
            vwap: true,
        });
    }
    hit(prev_x).map(|_| Overlay {
        ch: '┆',
        vwap: false,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn bar(label: &str, o: f64, h: f64, l: f64, c: f64, v: u64) -> HBar {
        HBar {
            label: label.into(),
            open: o,
            high: h,
            low: l,
            close: c,
            volume: v,
            ext: false,
        }
    }

    fn draw(w: u16, h: u16, bars: &[HBar], sel: Option<usize>) -> String {
        let theme = Theme::default();
        let mut term = Terminal::new(TestBackend::new(w, h)).unwrap();
        term.draw(|f| {
            f.render_widget(
                HCandles::new(bars, &theme)
                    .vwap(Some(100.0))
                    .prev_close(Some(99.0))
                    .selected(sel),
                f.area(),
            )
        })
        .unwrap();
        let b = term.backend().buffer();
        (0..b.area.height)
            .map(|y| {
                (0..b.area.width)
                    .map(|x| b[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn bars() -> Vec<HBar> {
        vec![
            bar("09:30", 99.0, 101.0, 98.0, 100.0, 500),
            bar("09:31", 100.0, 103.0, 99.5, 102.0, 900),
            bar("09:32", 102.0, 102.5, 100.0, 101.0, 300),
        ]
    }

    #[test]
    fn draws_axis_labels_bars_and_volume() {
        let out = draw(70, 6, &bars(), None);
        let first = out.lines().next().unwrap();
        assert!(
            first.contains("98.00") && first.contains("103.00"),
            "{first}"
        );
        assert!(out.contains("09:31"));
        assert!(
            out.chars()
                .any(|c| ('\u{1FB00}'..='\u{1FB3B}').contains(&c) || "▌▐█".contains(c))
        );
        assert!(out.contains('▏') || out.contains('█'), "volume bars: {out}");
    }

    #[test]
    fn wick_runs_the_full_high_low_range_on_the_middle_row() {
        // open == close: the body is one subpixel column, the wick spans
        // low..high and must leave no empty cell between them.
        let b = vec![
            bar("09:30", 100.0, 110.0, 90.0, 100.0, 1),
            bar("09:31", 95.0, 105.0, 95.0, 95.0, 1),
        ];
        let out = draw(70, 3, &b, None);
        let row = out.lines().nth(1).unwrap();
        let plot_w = 70 - TIME_W as usize - vol_w(70) as usize;
        let plot: Vec<char> = row.chars().skip(TIME_W as usize).take(plot_w).collect();
        // bar 0 spans the whole range, so every plot cell holds part of its wick
        assert!(plot.iter().all(|c| *c != ' '), "wick has gaps: {row}");
    }

    #[test]
    fn cursor_marks_the_selected_row() {
        let out = draw(70, 6, &bars(), Some(1));
        assert_eq!(out.lines().filter(|l| l.starts_with('▸')).count(), 1);
        assert!(out.lines().nth(2).unwrap().starts_with('▸'));
    }

    #[test]
    fn extended_hours_rows_are_dimmed() {
        let theme = Theme::default();
        let mut b = bars();
        b[0].ext = true;
        let mut term = Terminal::new(TestBackend::new(70, 6)).unwrap();
        term.draw(|f| f.render_widget(HCandles::new(&b, &theme), f.area()))
            .unwrap();
        let buf = term.backend().buffer();
        let dimmed = |y: u16| {
            (0..70).any(|x| {
                buf[(x, y)].modifier.contains(Modifier::DIM) && buf[(x, y)].symbol() != " "
            })
        };
        assert!(dimmed(1) && dimmed(2), "ext row and its volume are dim");
    }

    #[test]
    fn tiny_areas_and_flat_series_do_not_panic() {
        draw(10, 2, &bars(), None);
        draw(70, 1, &bars(), None);
        draw(70, 5, &[bar("09:30", 5.0, 5.0, 5.0, 5.0, 0)], None);
        draw(70, 5, &[], None);
    }
}
