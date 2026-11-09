//! Section 6: by the numbers, three stops: rate per pin, pins per device, and
//! the product, for DDR4-3200 (channel), DDR5-4800 (DIMM), GDDR6 (chip) and HBM3
//! (stack). Bars are on log scales so all four fit.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

/// name, Gb/s per pin, data pins, GB/s
const PARTS: [(&str, f64, f64, f64, Col); 4] = [
    ("DDR4-3200", 3.2, 64.0, 25.6, GREEN),
    ("DDR5-4800", 4.8, 64.0, 38.4, PURPLE),
    ("GDDR6", 16.0, 32.0, 64.0, CYAN),
    ("HBM3", 6.4, 1024.0, 819.2, ORANGE),
];
const SPACE: f64 = 1400.0;
const TITLES: [&str; 3] = ["Gbit/s per pin", "data pins", "GB/s per device"];

fn sx(stop: usize) -> f64 {
    (stop as f64 - 1.0) * SPACE
}

fn value(stop: usize, p: usize) -> f64 {
    let (_, r, n, g, _) = PARTS[p];
    [r, n, g][stop]
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [sx(i), 130.0, 0.0], dist: 1150.0, yaw: 0.20, pitch: 0.25 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    for stop in 0..3 {
        let k = spotlight(c, stop, 3);
        push_box(m, [sx(stop) - 420.0, -20.0, -130.0], [sx(stop) + 420.0, 0.0, 130.0], STEEL, NO_GLOW);
        for p in 0..4 {
            let bx = sx(stop) + (p as f64 - 1.5) * 190.0;
            let v = value(stop, p);
            let hgt = 100.0 * (v.log10() + 0.3).max(0.1);
            let col = PARTS[p].4;
            push_box(m, [bx - 45.0, 0.0, -45.0], [bx + 45.0, hgt, 45.0], stage::mix(QUIET, col, 0.3 + 0.7 * k), stage::scaled(col, 0.12 * k));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for stop in 0..3 {
        let k = spotlight(c, stop, 3);
        for p in 0..4 {
            let bx = sx(stop) + (p as f64 - 1.5) * 190.0;
            let v = value(stop, p);
            let hgt = 100.0 * (v.log10() + 0.3).max(0.1);
            label(cv, cam, [bx, hgt, 45.0], (-0.03, -0.06), &format!("{v}"), PARTS[p].4, 0.3 + 0.7 * k);
            label(cv, cam, [bx, 0.0, 45.0], (-0.04, 0.06), PARTS[p].0, TEXT, 0.3 + 0.7 * k);
        }
        let (w, h) = (cv.w as f64, cv.h as f64);
        text(cv, (w * 0.04) as i64, (h * 0.04) as i64, TITLES[stop], TEXT, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "log scales; DDR5 as two 32-bit subchannels", stage::GLASS, 0.8);
}
