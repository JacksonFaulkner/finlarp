//! Section 4: generations, three stops: interface width, rate per pin and bandwidth per
//! stack, HBM3 against HBM4 (JEDEC): 1024 vs 2048 bits, 6.4 vs 8 Gbit/s, 819 vs 2048 GB/s.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const STOPS: [(&str, f64, f64, &str); 3] = [
    ("data pins per stack", 1024.0, 2048.0, ""),
    ("Gbit/s per pin", 6.4, 8.0, ""),
    ("GB/s per stack", 819.2, 2048.0, ""),
];
const SPACE: f64 = 900.0;

fn sx(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [sx(i), 140.0, 0.0], dist: 1000.0, yaw: 0.20, pitch: 0.25 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    for (i, (_, a, b, _)) in STOPS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        push_box(m, [sx(i) - 260.0, -20.0, -120.0], [sx(i) + 260.0, 0.0, 120.0], STEEL, NO_GLOW);
        let top = a.max(*b);
        for (j, v, col) in [(0, *a, CYAN), (1, *b, ORANGE)] {
            let bx = sx(i) + if j == 0 { -90.0 } else { 90.0 };
            let hgt = 300.0 * v / top;
            push_box(m, [bx - 55.0, 0.0, -55.0], [bx + 55.0, hgt, 55.0], stage::mix(QUIET, col, 0.3 + 0.7 * k), stage::scaled(col, 0.12 * k));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for (i, (title, a, b, _)) in STOPS.iter().enumerate() {
        let k = spotlight(c, i, 3);
        let top = a.max(*b);
        for (j, v, col, name) in [(0, *a, CYAN, "HBM3"), (1, *b, ORANGE, "HBM4")] {
            let bx = sx(i) + if j == 0 { -90.0 } else { 90.0 };
            label(cv, cam, [bx, 300.0 * v / top, 55.0], (-0.03, -0.06), &format!("{v}"), col, 0.3 + 0.7 * k);
            label(cv, cam, [bx, 0.0, 55.0], (-0.03, 0.06), name, TEXT, 0.3 + 0.7 * k);
        }
        let (w, h) = (cv.w as f64, cv.h as f64);
        text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, TEXT, k);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "HBM4: up to 16-high, 64 GB per stack (JEDEC JESD270-4)", GLASS, 0.85);
}
