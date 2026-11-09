//! Section 6: by the numbers, three stops: DDR4's 16 banks in 4 groups, DDR5's 32
//! banks in 8 groups, and the burst: 8 transfers on DDR4, 16 on DDR5.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1300.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i), 0.0, 0.0], dist: 1250.0, yaw: 0.20, pitch: 0.75 });
    stage::shot_at(&keys, c.beat, c.local)
}

/// A grid of `groups` x 4 banks centred on `cx`.
fn banks(m: &mut Vec<Tri>, cx: f64, groups: usize, k: f64) {
    let cols = groups.min(4);
    let rows = groups.div_ceil(4);
    for g in 0..groups {
        let (gc, gr) = (g % cols, g / cols);
        let gx = cx + (gc as f64 - (cols as f64 - 1.0) / 2.0) * 220.0;
        let gz = (gr as f64 - (rows as f64 - 1.0) / 2.0) * 220.0;
        let col = if g % 2 == 0 { ORANGE } else { PURPLE };
        for b in 0..4 {
            let bx = gx + if b % 2 == 0 { -50.0 } else { 50.0 };
            let bz = gz + if b < 2 { -50.0 } else { 50.0 };
            push_box(m, [bx - 42.0, 0.0, bz - 42.0], [bx + 42.0, 20.0, bz + 42.0], stage::mix(QUIET, col, 0.3 + 0.6 * k), NO_GLOW);
        }
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    push_box(m, [x(0) - 300.0, -16.0, -300.0], [x(0) + 300.0, 0.0, 300.0], STEEL, NO_GLOW);
    banks(m, x(0), 4, k[0]);
    push_box(m, [x(1) - 500.0, -16.0, -300.0], [x(1) + 500.0, 0.0, 300.0], STEEL, NO_GLOW);
    banks(m, x(1), 8, k[1]);
    // bursts: two lanes of transfers
    push_box(m, [x(2) - 420.0, -16.0, -200.0], [x(2) + 420.0, 0.0, 200.0], STEEL, NO_GLOW);
    for (lane, n, col) in [(0, 8, GREEN), (1, 16, CYAN)] {
        let z = if lane == 0 { -70.0 } else { 70.0 };
        for t in 0..n {
            let bx = x(2) - 380.0 + t as f64 * 46.0;
            push_box(m, [bx, 0.0, z - 35.0], [bx + 40.0, 26.0, z + 35.0], stage::mix(QUIET, col, 0.3 + 0.7 * k[2]), stage::scaled(col, 0.1 * k[2]));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    label(cv, cam, [x(0) + 300.0, 0.0, 300.0], (0.02, 0.06), "DDR4: 16 banks, 4 groups", TEXT, 0.4 + 0.6 * k[0]);
    label(cv, cam, [x(1) + 500.0, 0.0, 300.0], (0.02, 0.06), "DDR5: 32 banks, 8 groups", TEXT, 0.4 + 0.6 * k[1]);
    label(cv, cam, [x(2) - 380.0, 26.0, -105.0], (-0.04, -0.07), "DDR4 burst: 8 transfers", GREEN, 0.4 + 0.6 * k[2]);
    label(cv, cam, [x(2) + 360.0, 26.0, 105.0], (0.02, 0.07), "DDR5 burst: 16 transfers", CYAN, 0.4 + 0.6 * k[2]);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "more banks: more rows open at once", TEXT, 0.85);
}
