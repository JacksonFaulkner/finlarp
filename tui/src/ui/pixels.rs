// Pixel drawing for pictures sent through the terminal's graphics protocol
// (see screens/intraday/picture.rs and screens/portfolio/chart_pic.rs). Plain
// RGBA buffer code, no terminal in it: lines, rectangles, and a 5x7 bitmap
// font, so labels can sit in the picture next to the lines that point to them.

use image::{Rgba, RgbaImage};
use ratatui::style::Color;

use crate::ui::theme::Theme;

/// One pixel colour, RGBA.
pub type Px = [u8; 4];

/// Colors as RGBA, resolved from the theme. Named or indexed theme colors
/// fall back to the Tokyo Night values the rest of the TUI uses.
#[derive(Clone, Copy, Debug, PartialEq, Hash)]
pub struct Palette {
    pub bg: [u8; 4],
    pub up: [u8; 4],
    pub down: [u8; 4],
    pub fg: [u8; 4],
    pub dim: [u8; 4],
    pub accent: [u8; 4],
}

impl Palette {
    pub fn from_theme(t: &Theme) -> Self {
        Self {
            bg: rgba(
                t.bg.unwrap_or(Color::Rgb(0x1a, 0x1b, 0x26)),
                [0x1a, 0x1b, 0x26],
            ),
            up: rgba(t.up, [0x4d, 0x93, 0x75]),
            down: rgba(t.down, [0xc2, 0x5c, 0x5c]),
            fg: rgba(t.fg, [0xc0, 0xca, 0xf5]),
            dim: rgba(t.dim, [0x56, 0x5f, 0x89]),
            accent: rgba(t.accent, [0xd7, 0xa6, 0x5f]),
        }
    }
}

fn rgba(c: Color, fallback: [u8; 3]) -> [u8; 4] {
    match c {
        Color::Rgb(r, g, b) => [r, g, b, 255],
        _ => [fallback[0], fallback[1], fallback[2], 255],
    }
}

/// `keep` of `a` over `b`.
pub fn blend(a: Px, b: Px, keep: f64) -> Px {
    let mix = |x: u8, y: u8| (x as f64 * keep + y as f64 * (1.0 - keep)).round() as u8;
    [mix(a[0], b[0]), mix(a[1], b[1]), mix(a[2], b[2]), 255]
}

pub fn put(img: &mut RgbaImage, x: i64, y: i64, c: Px) {
    if x >= 0 && y >= 0 && (x as u32) < img.width() && (y as u32) < img.height() {
        img.put_pixel(x as u32, y as u32, Rgba(c));
    }
}

/// Filled rectangle, both corners inclusive.
pub fn fill(img: &mut RgbaImage, x0: u32, y0: u32, x1: u32, y1: u32, c: Px) {
    for y in y0..=y1 {
        for x in x0..=x1 {
            put(img, x as i64, y as i64, c);
        }
    }
}

/// Horizontal run from `x0` up to, not including, `x1`.
pub fn hline(img: &mut RgbaImage, y: u32, x0: u32, x1: u32, c: Px) {
    fill(img, x0, y, x1.saturating_sub(1), y, c);
}

/// Vertical run, `y0` and `y1` in either order, both inclusive.
pub fn vline(img: &mut RgbaImage, x: u32, y0: u32, y1: u32, c: Px) {
    fill(img, x, y0.min(y1), x, y0.max(y1), c);
}

/// Bresenham line between two points (may leave the picture; clipped).
pub fn line(img: &mut RgbaImage, (x0, y0): (i64, i64), (x1, y1): (i64, i64), c: Px) {
    let (dx, dy) = ((x1 - x0).abs(), -(y1 - y0).abs());
    let (sx, sy) = (if x0 < x1 { 1 } else { -1 }, if y0 < y1 { 1 } else { -1 });
    let (mut x, mut y, mut err) = (x0, y0, dx + dy);
    loop {
        put(img, x, y, c);
        if x == x1 && y == y1 {
            break;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x += sx;
        }
        if e2 <= dx {
            err += dx;
            y += sy;
        }
    }
}

/// 5x7 glyphs, one byte per row, the low five bits used (bit 4 is the left column).
fn glyph(ch: char) -> Option<[u8; 7]> {
    Some(match ch {
        '0' => [0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E],
        '1' => [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E],
        '2' => [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F],
        '3' => [0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E],
        '4' => [0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02],
        '5' => [0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E],
        '6' => [0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E],
        '7' => [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08],
        '8' => [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E],
        '9' => [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C],
        '.' => [0, 0, 0, 0, 0, 0x0C, 0x0C],
        '$' => [0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04],
        '+' => [0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0],
        '-' => [0, 0, 0, 0x1F, 0, 0, 0],
        '/' => [0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10],
        'B' => [0x1E, 0x09, 0x09, 0x1E, 0x09, 0x09, 0x1E],
        'S' => [0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E],
        _ => return None,
    })
}

/// Width in pixels of `s` at `scale` (one glyph is 5 columns, plus one column of space).
pub fn text_width(s: &str, scale: u32) -> u32 {
    s.chars().count() as u32 * 6 * scale
}

/// Height in pixels of one text row at `scale`.
pub fn text_height(scale: u32) -> u32 {
    7 * scale
}

/// Draws `s` with its top-left corner at (x, y). Characters without a glyph are blank.
pub fn text(img: &mut RgbaImage, x: i64, y: i64, s: &str, scale: u32, c: Px) {
    for (i, ch) in s.chars().enumerate() {
        let Some(rows) = glyph(ch) else { continue };
        let gx = x + i as i64 * 6 * scale as i64;
        for (ry, bits) in rows.iter().enumerate() {
            for col in 0..5 {
                if bits >> (4 - col) & 1 == 1 {
                    for dy in 0..scale {
                        for dx in 0..scale {
                            let px = gx + col as i64 * scale as i64 + dx as i64;
                            let py = y + ry as i64 * scale as i64 + dy as i64;
                            put(img, px, py, c);
                        }
                    }
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn text_draws_its_glyph_pixels() {
        let mut img = RgbaImage::from_pixel(20, 10, Rgba([0, 0, 0, 255]));
        text(&mut img, 0, 0, "1", 1, [255, 255, 255, 255]);
        // the "1" glyph's top row is 0x04: only the third column is lit
        assert_eq!(img.get_pixel(2, 0).0, [255, 255, 255, 255]);
        assert_eq!(img.get_pixel(0, 0).0, [0, 0, 0, 255]);
        assert_eq!(text_width("$1.5", 2), 4 * 6 * 2);
    }

    #[test]
    fn line_hits_both_ends_and_clips() {
        let mut img = RgbaImage::from_pixel(10, 10, Rgba([0, 0, 0, 255]));
        line(&mut img, (-5, -5), (9, 9), [1, 2, 3, 255]);
        assert_eq!(img.get_pixel(9, 9).0, [1, 2, 3, 255]);
        assert_eq!(img.get_pixel(4, 4).0, [1, 2, 3, 255]);
    }
}
