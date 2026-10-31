//! Pie chart: a filled circle of half-block cells, one slice per value. The
//! selected slice is outlined and sticks out a little; the others dim. `rot`
//! turns the whole pie so a chosen slice can face a side panel. No screen
//! knowledge: callers pass values and colours.

use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::{Color, Style};
use ratatui::widgets::Widget;

/// Subpixels the selected slice sticks out past the others.
const GROW: f64 = 2.0;

#[derive(Clone, Copy)]
pub struct Slice {
    pub value: f64,
    pub color: Color,
}

/// Filled circle made of half-block cells (two square subpixels per cell),
/// sized to the whole area. Slices run clockwise from 12 o'clock.
pub struct Pie<'a> {
    pub slices: &'a [Slice],
    pub sel: usize,
    pub bg: Color,
    /// How much of an unselected slice's colour survives (1.0 = full).
    pub dim: f64,
    /// Degrees the whole pie is turned clockwise.
    pub rot: f64,
}

impl Widget for Pie<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let total: f64 = self.slices.iter().map(|e| e.value).sum();
        if total <= 0.0 || area.width < 2 || area.height < 2 {
            return;
        }
        let (w, h) = (f64::from(area.width), f64::from(area.height) * 2.0);
        // The selected slice grows GROW subpixels past the base radius; the
        // base is shrunk so the grown edge still fits the area.
        let r_full = w.min(h) / 2.0;
        let r = (r_full - GROW).max(1.0);
        let r_sel = r + GROW.min(r_full - r);
        let (cx, cy) = (w / 2.0, h / 2.0);
        let sole = self.slices.len() == 1;
        // Cumulative slice ends in degrees.
        let mut acc = 0.0;
        let ends: Vec<f64> = self
            .slices
            .iter()
            .map(|e| {
                acc += e.value / total * 360.0;
                acc
            })
            .collect();
        let at = |px: f64, py: f64| -> Option<Color> {
            let (dx, dy) = (px + 0.5 - cx, py + 0.5 - cy);
            let d = (dx * dx + dy * dy).sqrt();
            if d > r_sel {
                return None;
            }
            let ang = (dx.atan2(-dy).to_degrees() - self.rot).rem_euclid(360.0);
            let i = ends.iter().position(|e| ang < *e).unwrap_or(ends.len() - 1);
            let e = &self.slices[i];
            if i != self.sel {
                return (d <= r).then(|| fade(e.color, self.bg, self.dim));
            }
            // Outline: outer rim plus the two radial edges, ~1 subpixel wide.
            let start = if i == 0 { 0.0 } else { ends[i - 1] };
            let edge = (ang - start).min(ends[i] - ang).to_radians() * d;
            let rim = d > r_sel - 1.0;
            Some(if rim || (!sole && edge < 1.0) {
                fade(e.color, Color::Rgb(255, 255, 255), 0.55)
            } else {
                e.color
            })
        };
        for row in 0..area.height {
            for col in 0..area.width {
                let (x, y) = (f64::from(col), f64::from(row) * 2.0);
                let (top, bot) = (at(x, y), at(x, y + 1.0));
                let (sym, style) = match (top, bot) {
                    (None, None) => continue,
                    (Some(t), Some(b)) => ("▀", Style::new().fg(t).bg(b)),
                    (Some(t), None) => ("▀", Style::new().fg(t)),
                    (None, Some(b)) => ("▄", Style::new().fg(b)),
                };
                buf[(area.x + col, area.y + row)]
                    .set_symbol(sym)
                    .set_style(style);
            }
        }
    }
}

/// Cell just outside the circle's 9 o'clock point, where the selected
/// slice's centre sits once the pie has turned.
pub fn left_edge(area: Rect) -> (u16, u16) {
    let (w, h) = (f64::from(area.width), f64::from(area.height) * 2.0);
    let r = w.min(h) / 2.0;
    let col = (w / 2.0 - r - 0.5).ceil().max(0.0) as u16;
    (area.x + col, area.y + area.height / 2)
}

/// Rotation (degrees clockwise) that puts slice `sel`'s centre at 9 o'clock,
/// facing a side panel on the left.
pub fn facing_left(values: &[f64], sel: usize) -> f64 {
    let total: f64 = values.iter().sum();
    if total <= 0.0 || values.is_empty() {
        return 0.0;
    }
    let sel = sel.min(values.len() - 1);
    let before: f64 = values[..sel].iter().sum();
    let centre = (before + values[sel] / 2.0) / total * 360.0;
    270.0 - centre
}

/// Golden-angle hue steps keep neighbouring slices far apart on the wheel;
/// alternating lightness separates the ones that still land close.
pub fn slice_color(i: usize) -> Color {
    let h = (i as f64 * 137.508) % 360.0;
    let (s, l) = if i % 2 == 0 {
        (0.65, 0.55)
    } else {
        (0.75, 0.68)
    };
    hsl(h, s, l)
}

/// Elbow connector from `from` to `to`, ending in an arrowhead that points
/// at the slice.
pub fn arrow(buf: &mut Buffer, from: (u16, u16), to: (u16, u16), color: Color) {
    let ((x0, y0), (x1, y1)) = (from, to);
    if x1 < x0 + 3 || y0 >= buf.area.bottom() || y1 >= buf.area.bottom() || x1 >= buf.area.right() {
        return;
    }
    let style = Style::new().fg(color);
    let mut put = |x: u16, y: u16, s: &str| {
        buf[(x, y)].set_symbol(s).set_style(style);
    };
    let xm = x0 + (x1 - x0) / 2;
    for x in x0..xm {
        put(x, y0, "─");
    }
    for x in xm + 1..x1 - 1 {
        put(x, y1, "─");
    }
    if y0 == y1 {
        put(xm, y0, "─");
    } else {
        let down = y1 > y0;
        put(xm, y0, if down { "╮" } else { "╯" });
        put(xm, y1, if down { "╰" } else { "╭" });
        for y in y0.min(y1) + 1..y0.max(y1) {
            put(xm, y, "│");
        }
    }
    put(x1 - 1, y1, "▶");
}

fn hsl(h: f64, s: f64, l: f64) -> Color {
    let c = (1.0 - (2.0 * l - 1.0).abs()) * s;
    let x = c * (1.0 - ((h / 60.0) % 2.0 - 1.0).abs());
    let m = l - c / 2.0;
    let (r, g, b) = match h as u32 / 60 {
        0 => (c, x, 0.0),
        1 => (x, c, 0.0),
        2 => (0.0, c, x),
        3 => (0.0, x, c),
        4 => (x, 0.0, c),
        _ => (c, 0.0, x),
    };
    let ch = |v: f64| ((v + m) * 255.0).round() as u8;
    Color::Rgb(ch(r), ch(g), ch(b))
}

/// Blend `c` toward `bg` by `keep` (1.0 = unchanged).
fn fade(c: Color, bg: Color, keep: f64) -> Color {
    match (c, bg) {
        (Color::Rgb(r, g, b), Color::Rgb(br, bgc, bb)) => {
            let mix =
                |a: u8, b: u8| (f64::from(a) * keep + f64::from(b) * (1.0 - keep)).round() as u8;
            Color::Rgb(mix(r, br), mix(g, bgc), mix(b, bb))
        }
        _ => c,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn selected_slice_centre_faces_left() {
        // A spans 0..180, centre 90: turn +180 to reach 9 o'clock.
        assert!((facing_left(&[50.0, 25.0, 25.0], 0) - 180.0).abs() < 1e-9);
        // B spans 180..270, centre 225: turn +45.
        assert!((facing_left(&[50.0, 25.0, 25.0], 1) - 45.0).abs() < 1e-9);
        assert_eq!(facing_left(&[], 0), 0.0);
    }

    #[test]
    fn colors_are_distinct() {
        let cs: Vec<Color> = (0..15).map(slice_color).collect();
        for (i, a) in cs.iter().enumerate() {
            assert!(!cs[i + 1..].contains(a));
        }
    }
}
