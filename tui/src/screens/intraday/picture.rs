// Intraday tiles as pictures. A tile's bars are drawn into an RGBA buffer
// (candles with wicks, volume strip, session VWAP, previous close, the
// cursor) and sent through the terminal's graphics protocol, the same way
// `fl video` draws frames. Pure pixel code with no terminal in it, so the
// tests can check the image itself.

use image::{DynamicImage, Rgba, RgbaImage};

use crate::ui::hcandles::HBar;
use crate::ui::pixels::{Palette, blend};

/// Share of the picture height given to the volume strip at the bottom.
const VOLUME_SHARE: f64 = 0.2;
/// Narrowest a bar slot may get; below this the candles stop being readable.
const SLOT_PX: u32 = 3;

/// What one tile shows. `bars` is the visible window, oldest first.
pub struct Pic<'a> {
    pub bars: &'a [HBar],
    pub vwap: Option<f64>,
    pub prev_close: Option<f64>,
    /// Index into `bars` of the cursor bar, if any.
    pub sel: Option<usize>,
}

/// Bars that fit `px_w` pixels at the narrowest readable slot.
pub fn capacity(px_w: u32) -> usize {
    (px_w / SLOT_PX).max(1) as usize
}

/// Draws the picture at `w` x `h` pixels. Only the last `capacity(w)` bars are drawn.
pub fn render(pic: &Pic, w: u32, h: u32, pal: &Palette) -> DynamicImage {
    let mut img = RgbaImage::new(w.max(1), h.max(1));
    render_into(&mut img, pic, pal);
    DynamicImage::ImageRgba8(img)
}

/// `render` into a buffer the caller keeps (its size is the picture's size). Every
/// pixel is overwritten, so a buffer from an earlier draw can be reused as it is.
pub fn render_into(img: &mut RgbaImage, pic: &Pic, pal: &Palette) {
    let (w, h) = img.dimensions();
    let stride = w as usize * 4;
    let raw: &mut [u8] = img;
    // Clear: one background row, then copy it down.
    for px in raw[..stride].chunks_exact_mut(4) {
        px.copy_from_slice(&pal.bg);
    }
    for y in 1..h as usize {
        raw.copy_within(0..stride, y * stride);
    }
    let n = pic.bars.len().min(capacity(w));
    if n == 0 {
        return;
    }
    let bars = &pic.bars[pic.bars.len() - n..];
    let price_h = ((h as f64) * (1.0 - VOLUME_SHARE)).floor().max(1.0) as u32;
    let vol_top = (price_h + 2).min(h - 1);

    // Price range over the drawn bars, plus the reference lines, padded 5%.
    let mut lo = bars.iter().map(|b| b.low).fold(f64::MAX, f64::min);
    let mut hi = bars.iter().map(|b| b.high).fold(f64::MIN, f64::max);
    for extra in [pic.vwap, pic.prev_close].into_iter().flatten() {
        lo = lo.min(extra);
        hi = hi.max(extra);
    }
    let pad = ((hi - lo) * 0.05).max(0.01);
    let (lo, hi) = (lo - pad, hi + pad);
    // Price -> row. The constants are hoisted out of the per-bar loop; the arithmetic is the
    // same as the reference renderer's, so every row rounds the same way.
    let span = hi - lo;
    let top = (price_h - 1) as f64;
    let y = |p: f64| -> u32 { (((hi - p) / span) * top).round().clamp(0.0, top) as u32 };

    // Four faint price gridlines.
    let grid = blend(pal.dim, pal.bg, 0.5);
    for k in 1..4 {
        let p = lo + span * k as f64 / 4.0;
        fill_rect(raw, w, h, 0, y(p), w - 1, y(p), grid);
    }

    let slot = w as f64 / n as f64;
    let body = (slot * 0.6).max(1.0);
    let half = (body / 2.0).floor() as u32;
    let vmax = bars.iter().map(|b| b.volume).max().unwrap_or(0).max(1) as f64;
    let vol_h = (h - vol_top) as f64;
    for (i, b) in bars.iter().enumerate() {
        let cx = ((i as f64 + 0.5) * slot) as u32;
        let base = if b.ext {
            blend(if b.is_up() { pal.up } else { pal.down }, pal.bg, 0.5)
        } else if b.is_up() {
            pal.up
        } else {
            pal.down
        };
        // wick, then body (at least one pixel tall, so a flat bar still shows)
        let (wick_hi, wick_lo) = (y(b.high), y(b.low));
        fill_rect(raw, w, h, cx, wick_hi.min(wick_lo), cx, wick_hi.max(wick_lo), base);
        let (top, bot) = (y(b.open.max(b.close)), y(b.open.min(b.close)));
        fill_rect(
            raw,
            w,
            h,
            cx.saturating_sub(half),
            top,
            cx + half,
            bot.max(top),
            base,
        );
        // volume, from the bottom of the picture up
        let vh = ((b.volume as f64 / vmax) * vol_h).round() as u32;
        if vh > 0 {
            fill_rect(
                raw,
                w,
                h,
                cx.saturating_sub(half),
                h - vh,
                cx + half,
                h - 1,
                blend(base, pal.bg, 0.6),
            );
        }
    }

    // Session VWAP across the picture, previous close dotted.
    if let Some(v) = pic.vwap {
        fill_rect(raw, w, h, 0, y(v), w - 1, y(v), pal.accent);
    }
    if let Some(p) = pic.prev_close {
        let row = y(p);
        for x in (0..w).step_by(6) {
            fill_rect(raw, w, h, x, row, (x + 3).min(w - 1), row, pal.fg);
        }
    }
    // Cursor: a full-height line through the selected bar.
    if let Some(sel) = pic.sel.filter(|s| *s < n) {
        let cx = ((sel as f64 + 0.5) * slot) as u32;
        fill_rect(raw, w, h, cx, 0, cx, h - 1, blend(pal.fg, pal.bg, 0.4));
    }
}

/// Writes `c` over the inclusive rectangle (x0,y0)-(x1,y1), clipped to a `w` x `h` buffer.
#[allow(clippy::too_many_arguments)]
fn fill_rect(raw: &mut [u8], w: u32, h: u32, x0: u32, y0: u32, x1: u32, y1: u32, c: [u8; 4]) {
    if x0 > x1 || y0 > y1 || x0 >= w || y0 >= h {
        return;
    }
    let (x1, y1) = (x1.min(w - 1), y1.min(h - 1));
    let stride = w as usize * 4;
    let span = (x0 as usize * 4)..((x1 as usize + 1) * 4);
    for y in y0..=y1 {
        let row = y as usize * stride;
        for px in raw[row + span.start..row + span.end].chunks_exact_mut(4) {
            px.copy_from_slice(&c);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::pixels::{fill, hline, vline};
    use crate::ui::theme::Theme;
    use ratatui::style::Color;

    fn bar(open: f64, high: f64, low: f64, close: f64, volume: u64) -> HBar {
        HBar {
            label: "09:30".into(),
            open,
            high,
            low,
            close,
            volume,
            ext: false,
        }
    }

    fn pal() -> Palette {
        Palette {
            bg: [0, 0, 0, 255],
            up: [0, 255, 0, 255],
            down: [255, 0, 0, 255],
            fg: [255, 255, 255, 255],
            dim: [90, 90, 90, 255],
            accent: [0, 0, 255, 255],
        }
    }

    fn px(img: &DynamicImage, x: u32, y: u32) -> [u8; 4] {
        img.to_rgba8().get_pixel(x, y).0
    }

    /// The renderer as it was before `render_into`: the oracle the optimised one must match.
    /// The original renderer, kept verbatim as the oracle for `render_into`.
    fn render_reference(pic: &Pic, w: u32, h: u32, pal: &Palette) -> DynamicImage {
        let (w, h) = (w.max(1), h.max(1));
        let mut img = RgbaImage::from_pixel(w, h, Rgba(pal.bg));
        let n = pic.bars.len().min(capacity(w));
        if n == 0 {
            return DynamicImage::ImageRgba8(img);
        }
        let bars = &pic.bars[pic.bars.len() - n..];
        let price_h = ((h as f64) * (1.0 - VOLUME_SHARE)).floor().max(1.0) as u32;
        let vol_top = (price_h + 2).min(h - 1);

        // Price range over the drawn bars, plus the reference lines, padded 5%.
        let mut lo = bars.iter().map(|b| b.low).fold(f64::MAX, f64::min);
        let mut hi = bars.iter().map(|b| b.high).fold(f64::MIN, f64::max);
        for extra in [pic.vwap, pic.prev_close].into_iter().flatten() {
            lo = lo.min(extra);
            hi = hi.max(extra);
        }
        let pad = ((hi - lo) * 0.05).max(0.01);
        let (lo, hi) = (lo - pad, hi + pad);
        let y = |p: f64| -> u32 {
            let f = (hi - p) / (hi - lo);
            (f * (price_h - 1) as f64)
                .round()
                .clamp(0.0, (price_h - 1) as f64) as u32
        };

        // Four faint price gridlines.
        let grid = blend(pal.dim, pal.bg, 0.5);
        for k in 1..4 {
            let p = lo + (hi - lo) * k as f64 / 4.0;
            hline(&mut img, y(p), 0, w, grid);
        }

        let slot = w as f64 / n as f64;
        let body = (slot * 0.6).max(1.0);
        let vmax = bars.iter().map(|b| b.volume).max().unwrap_or(0).max(1) as f64;
        let vol_h = (h - vol_top) as f64;
        for (i, b) in bars.iter().enumerate() {
            let cx = ((i as f64 + 0.5) * slot) as u32;
            let base = if b.ext {
                blend(if b.is_up() { pal.up } else { pal.down }, pal.bg, 0.5)
            } else if b.is_up() {
                pal.up
            } else {
                pal.down
            };
            // wick, then body (at least one pixel tall, so a flat bar still shows)
            vline(&mut img, cx, y(b.high), y(b.low), base);
            let (top, bot) = (y(b.open.max(b.close)), y(b.open.min(b.close)));
            let half = (body / 2.0).floor() as u32;
            fill(
                &mut img,
                cx.saturating_sub(half),
                top,
                cx + half,
                bot.max(top),
                base,
            );
            // volume, from the bottom of the picture up
            let vh = ((b.volume as f64 / vmax) * vol_h).round() as u32;
            if vh > 0 {
                fill(
                    &mut img,
                    cx.saturating_sub(half),
                    h - vh,
                    cx + half,
                    h - 1,
                    blend(base, pal.bg, 0.6),
                );
            }
        }

        // Session VWAP across the picture, previous close dotted.
        if let Some(v) = pic.vwap {
            hline(&mut img, y(v), 0, w, pal.accent);
        }
        if let Some(p) = pic.prev_close {
            let row = y(p);
            for x in (0..w).step_by(6) {
                fill(&mut img, x, row, (x + 3).min(w - 1), row, pal.fg);
            }
        }
        // Cursor: a full-height line through the selected bar.
        if let Some(sel) = pic.sel.filter(|s| *s < n) {
            let cx = ((sel as f64 + 0.5) * slot) as u32;
            vline(&mut img, cx, 0, h - 1, blend(pal.fg, pal.bg, 0.4));
        }
        DynamicImage::ImageRgba8(img)
    }

    fn varied_bars(n: usize, seed: u64) -> Vec<HBar> {
        let mut x = seed;
        let mut rnd = move || {
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            (x % 10_000) as f64 / 10_000.0
        };
        let mut c = 100.0;
        (0..n)
            .map(|i| {
                let o = c;
                c += (rnd() - 0.5) * 2.0;
                let mut b = bar(
                    o,
                    o.max(c) + rnd(),
                    o.min(c) - rnd(),
                    c,
                    if i % 17 == 0 { 0 } else { 1 + (rnd() * 5000.0) as u64 },
                );
                b.ext = i % 5 == 0;
                b
            })
            .collect()
    }

    #[test]
    fn render_into_matches_the_reference_byte_for_byte() {
        let p = pal();
        for (seed, n) in [(1u64, 0usize), (2, 1), (3, 7), (4, 90), (5, 400)] {
            let bars = varied_bars(n, seed * 977);
            for (w, h) in [(1u32, 1u32), (3, 2), (30, 30), (101, 37), (480, 260), (9, 200)] {
                for (vwap, prev_close, sel) in [
                    (None, None, None),
                    (Some(101.0), Some(99.0), Some(n / 2)),
                    (Some(90.0), None, Some(0)),
                    (None, Some(140.0), Some(usize::MAX)),
                ] {
                    let pic = Pic {
                        bars: &bars,
                        vwap,
                        prev_close,
                        sel: sel.filter(|s| *s < n.max(1)),
                    };
                    let want = render_reference(&pic, w, h, &p).to_rgba8();
                    let got = render(&pic, w, h, &p).to_rgba8();
                    assert_eq!(got.as_raw(), want.as_raw(), "n={n} {w}x{h} vwap={vwap:?}");
                    // a reused buffer, left over from a different picture, gives the same bytes
                    let mut buf = RgbaImage::from_pixel(w, h, Rgba([9, 9, 9, 9]));
                    render_into(&mut buf, &pic, &p);
                    assert_eq!(buf.as_raw(), want.as_raw(), "reused n={n} {w}x{h}");
                }
            }
        }
    }

    #[test]
    fn up_and_down_bars_take_their_colors() {
        let bars = [
            bar(10.0, 11.0, 9.5, 11.0, 100),
            bar(11.0, 11.2, 10.0, 10.2, 100),
        ];
        let img = render(
            &Pic {
                bars: &bars,
                vwap: None,
                prev_close: None,
                sel: None,
            },
            40,
            40,
            &pal(),
        );
        // slots are 20px wide: bar 0 centred on x=10, bar 1 on x=30; the body at mid-height
        assert_eq!(px(&img, 10, 12), [0, 255, 0, 255]);
        assert_eq!(px(&img, 30, 12), [255, 0, 0, 255]);
    }

    #[test]
    fn vwap_is_a_full_width_accent_line() {
        let bars = [
            bar(10.0, 12.0, 9.0, 11.0, 100),
            bar(11.0, 13.0, 10.0, 12.0, 100),
        ];
        let vwap = Some(11.0);
        let img = render(
            &Pic {
                bars: &bars,
                vwap,
                prev_close: None,
                sel: None,
            },
            40,
            40,
            &pal(),
        );
        let price_h = (40.0_f64 * 0.8).floor() as u32;
        let lo = 9.0 - 0.05 * 4.0;
        let hi = 13.0 + 0.05 * 4.0;
        let row = ((hi - 11.0) / (hi - lo) * (price_h - 1) as f64).round() as u32;
        assert_eq!(px(&img, 0, row), [0, 0, 255, 255]);
        assert_eq!(px(&img, 39, row), [0, 0, 255, 255]);
    }

    #[test]
    fn only_the_newest_bars_that_fit_are_drawn() {
        let bars: Vec<HBar> = (0..50)
            .map(|i| bar(10.0, 10.5, 9.5, 10.0 + i as f64 * 0.01, 1))
            .collect();
        assert_eq!(capacity(30), 10);
        let img = render(
            &Pic {
                bars: &bars,
                vwap: None,
                prev_close: None,
                sel: None,
            },
            30,
            30,
            &pal(),
        );
        assert_eq!((img.width(), img.height()), (30, 30));
    }

    #[test]
    fn no_bars_is_just_the_background() {
        let img = render(
            &Pic {
                bars: &[],
                vwap: None,
                prev_close: None,
                sel: None,
            },
            20,
            10,
            &pal(),
        );
        assert_eq!(px(&img, 5, 5), [0, 0, 0, 255]);
    }

    #[test]
    fn palette_falls_back_for_named_colors() {
        let mut t = Theme::default();
        t.up = Color::Green;
        let p = Palette::from_theme(&t);
        assert_eq!(p.up, [0x4d, 0x93, 0x75, 255]);
    }

    /// Writes a sample picture to $FL_PICTURE_DUMP (a PNG path) for a visual check. No-op otherwise.
    #[test]
    fn dump_sample_picture() {
        let Ok(path) = std::env::var("FL_PICTURE_DUMP") else {
            return;
        };
        let mut bars = Vec::new();
        let mut c = 100.0_f64;
        for i in 0..60 {
            let o = c;
            c += ((i as f64) * 0.7).sin() * 0.8 + 0.05;
            bars.push(bar(
                o,
                o.max(c) + 0.3,
                o.min(c) - 0.3,
                c,
                1000 + (i * 37 % 900) as u64,
            ));
        }
        let img = render(
            &Pic {
                bars: &bars,
                vwap: Some(100.6),
                prev_close: Some(99.5),
                sel: Some(40),
            },
            480,
            260,
            &Palette::from_theme(&Theme::default()),
        );
        img.save(path).unwrap();
    }
}
