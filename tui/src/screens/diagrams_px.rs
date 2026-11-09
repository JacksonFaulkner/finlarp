// Pixel drawing for the diagram scenes. A scene draws in a fixed design space
// (1000 x 600 units). `Px` fits that space into the image, centred, keeping its
// aspect ratio, and paints plain shapes with anti-aliased edges. There is no
// font: labels stay in the terminal text beside the picture.

// The CELL and LITHO scenes moved to 3D; only BG is still used, so most of the kit is idle.
#![allow(dead_code)]

use image::{Rgba, RgbaImage};

pub type Rgb = [u8; 3];

pub const DESIGN_W: f32 = 1000.0;
pub const DESIGN_H: f32 = 600.0;

// Dracula, the same palette as the bell jar (`FULL_BG` in diagrams.rs).
pub const BG: Rgb = [0x28, 0x2a, 0x36];
pub const FG: Rgb = [0xf8, 0xf8, 0xf2];
pub const DIM: Rgb = [0x62, 0x72, 0xa4];
pub const CYAN: Rgb = [0x8b, 0xe9, 0xfd];
pub const GREEN: Rgb = [0x50, 0xfa, 0x7b];
pub const ORANGE: Rgb = [0xff, 0xb8, 0x6c];
pub const PURPLE: Rgb = [0xbd, 0x93, 0xf9];
pub const YELLOW: Rgb = [0xf1, 0xfa, 0x8c];

/// Blend `a` of `c` over `d` per channel.
pub fn mix(c: Rgb, d: Rgb, a: f32) -> Rgb {
    let a = a.clamp(0.0, 1.0);
    let f = |i: usize| (c[i] as f32 * a + d[i] as f32 * (1.0 - a)).round() as u8;
    [f(0), f(1), f(2)]
}

pub struct Px {
    img: RgbaImage,
    scale: f32,
    ox: f32,
    oy: f32,
}

impl Px {
    /// A `w` x `h` image filled with `bg`.
    pub fn new(w: u32, h: u32, bg: Rgb) -> Self {
        let (w, h) = (w.max(1), h.max(1));
        let scale = (w as f32 / DESIGN_W).min(h as f32 / DESIGN_H);
        let ox = (w as f32 - DESIGN_W * scale) / 2.0;
        let oy = (h as f32 - DESIGN_H * scale) / 2.0;
        let img = RgbaImage::from_pixel(w, h, Rgba([bg[0], bg[1], bg[2], 255]));
        Self { img, scale, ox, oy }
    }

    pub fn into_image(self) -> RgbaImage {
        self.img
    }

    fn to_px(&self, x: f32, y: f32) -> (f32, f32) {
        (self.ox + x * self.scale, self.oy + y * self.scale)
    }

    fn blend(&mut self, x: i64, y: i64, c: Rgb, a: f32) {
        if x < 0 || y < 0 || x >= i64::from(self.img.width()) || y >= i64::from(self.img.height()) {
            return;
        }
        let p = self.img.get_pixel_mut(x as u32, y as u32);
        for (k, v) in c.iter().enumerate() {
            let old = f32::from(p.0[k]);
            p.0[k] = (f32::from(*v) * a + old * (1.0 - a)).round() as u8;
        }
    }

    /// Paint every pixel in the design-space box whose coverage `cov` (in pixel
    /// coordinates, 0..1) is above zero.
    fn paint(
        &mut self,
        bx: (f32, f32, f32, f32),
        c: Rgb,
        a: f32,
        cov: impl Fn(f32, f32) -> f32,
    ) {
        let (x0, y0) = self.to_px(bx.0, bx.1);
        let (x1, y1) = self.to_px(bx.2, bx.3);
        for py in (y0.floor() as i64)..=(y1.ceil() as i64) {
            for px in (x0.floor() as i64)..=(x1.ceil() as i64) {
                let k = cov(px as f32 + 0.5, py as f32 + 0.5);
                if k > 0.0 {
                    self.blend(px, py, c, a * k);
                }
            }
        }
    }

    /// Filled rectangle between two corners (design units).
    pub fn rect(&mut self, x0: f32, y0: f32, x1: f32, y1: f32, c: Rgb, a: f32) {
        let (x0, x1) = (x0.min(x1), x0.max(x1));
        let (y0, y1) = (y0.min(y1), y0.max(y1));
        let (ax, ay) = self.to_px(x0, y0);
        let (bx, by) = self.to_px(x1, y1);
        self.paint((x0, y0, x1, y1), c, a, move |x, y| {
            if x >= ax && x <= bx && y >= ay && y <= by {
                1.0
            } else {
                0.0
            }
        });
    }

    /// Rectangle outline, `w` units thick, drawn inside the corners.
    #[allow(clippy::too_many_arguments)]
    pub fn frame(&mut self, x0: f32, y0: f32, x1: f32, y1: f32, w: f32, c: Rgb, a: f32) {
        self.rect(x0, y0, x1, y0 + w, c, a);
        self.rect(x0, y1 - w, x1, y1, c, a);
        self.rect(x0, y0, x0 + w, y1, c, a);
        self.rect(x1 - w, y0, x1, y1, c, a);
    }

    pub fn disc(&mut self, x: f32, y: f32, r: f32, c: Rgb, a: f32) {
        let (cx, cy) = self.to_px(x, y);
        let pr = r * self.scale;
        self.paint((x - r, y - r, x + r, y + r), c, a, move |px, py| {
            let d = ((px - cx).powi(2) + (py - cy).powi(2)).sqrt();
            (pr + 0.5 - d).clamp(0.0, 1.0)
        });
    }

    /// Straight line segment, `width` units thick, round ends.
    #[allow(clippy::too_many_arguments)]
    pub fn line(&mut self, x0: f32, y0: f32, x1: f32, y1: f32, width: f32, c: Rgb, a: f32) {
        let (ax, ay) = self.to_px(x0, y0);
        let (bx, by) = self.to_px(x1, y1);
        let hw = width * self.scale / 2.0;
        let bbox = (
            x0.min(x1) - width,
            y0.min(y1) - width,
            x0.max(x1) + width,
            y0.max(y1) + width,
        );
        let (dx, dy) = (bx - ax, by - ay);
        let len2 = (dx * dx + dy * dy).max(1e-6);
        self.paint(bbox, c, a, move |px, py| {
            let t = (((px - ax) * dx + (py - ay) * dy) / len2).clamp(0.0, 1.0);
            let (qx, qy) = (ax + dx * t, ay + dy * t);
            let d = ((px - qx).powi(2) + (py - qy).powi(2)).sqrt();
            (hw + 0.5 - d).clamp(0.0, 1.0)
        });
    }

    /// Connected segments through `pts`.
    pub fn path(&mut self, pts: &[(f32, f32)], width: f32, c: Rgb, a: f32) {
        for w in pts.windows(2) {
            self.line(w[0].0, w[0].1, w[1].0, w[1].1, width, c, a);
        }
    }

    /// A line with an arrowhead at (x1, y1).
    #[allow(clippy::too_many_arguments)]
    pub fn arrow(&mut self, x0: f32, y0: f32, x1: f32, y1: f32, width: f32, c: Rgb, a: f32) {
        self.line(x0, y0, x1, y1, width, c, a);
        let ang = (y1 - y0).atan2(x1 - x0);
        let head = 9.0 + width;
        for side in [2.6_f32, -2.6] {
            let (hx, hy) = (x1 - head * (ang + side).cos(), y1 - head * (ang + side).sin());
            self.line(x1, y1, hx, hy, width, c, a);
        }
    }
}

/// The point a fraction `s` (0..1, wrapping) of the way along the polyline `pts`,
/// by arc length.
pub fn along(pts: &[(f32, f32)], s: f32) -> (f32, f32) {
    let total: f32 = pts.windows(2).map(|w| seg_len(w[0], w[1])).sum();
    if total <= 0.0 || pts.len() < 2 {
        return pts.first().copied().unwrap_or((0.0, 0.0));
    }
    let mut want = s.rem_euclid(1.0) * total;
    for w in pts.windows(2) {
        let l = seg_len(w[0], w[1]);
        if want <= l {
            let t = if l > 0.0 { want / l } else { 0.0 };
            return (w[0].0 + (w[1].0 - w[0].0) * t, w[0].1 + (w[1].1 - w[0].1) * t);
        }
        want -= l;
    }
    *pts.last().unwrap_or(&(0.0, 0.0))
}

fn seg_len(a: (f32, f32), b: (f32, f32)) -> f32 {
    ((b.0 - a.0).powi(2) + (b.1 - a.1).powi(2)).sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fits_design_space_centred() {
        let p = Px::new(2000, 600, BG);
        // scale is 1 (height bound), so the design is 1000 px wide, centred.
        assert_eq!(p.to_px(0.0, 0.0), (500.0, 0.0));
        assert_eq!(p.to_px(1000.0, 600.0), (1500.0, 600.0));
    }

    #[test]
    fn paints_shapes_and_leaves_background() {
        let mut p = Px::new(200, 120, BG);
        p.rect(0.0, 0.0, 500.0, 300.0, GREEN, 1.0);
        let img = p.into_image();
        assert_eq!(img.get_pixel(10, 10).0[..3], GREEN);
        assert_eq!(img.get_pixel(199, 119).0[..3], BG);
    }

    #[test]
    fn along_walks_the_polyline() {
        let pts = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)];
        assert_eq!(along(&pts, 0.0), (0.0, 0.0));
        assert_eq!(along(&pts, 0.5), (10.0, 0.0));
        assert_eq!(along(&pts, 0.75), (10.0, 5.0));
        // the end wraps to the start, so a looping animation never stops at a gap
        assert_eq!(along(&pts, 1.0), (0.0, 0.0));
        assert_eq!(along(&pts, 0.999).0.round(), 10.0);
    }
}
