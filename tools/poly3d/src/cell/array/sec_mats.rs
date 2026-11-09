//! Section 5: why the array is cut into mats. One bit line with its cells and a sense
//! amp at the end. Every cell adds capacitance to the bit line (Cb), so a longer line
//! means a smaller swing, Cc / (Cc + Cb), for the sense amp to read. Doubling the line
//! halves the signal; cutting it in two with a sense amp stripe in the middle brings
//! it back, at the cost of more stripes. The bar on the right is the swing.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, METAL, NO_GLOW, ORANGE, PURPLE, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const N: usize = 16;
const P: f64 = 34.0;
const Z0: f64 = -540.0;
/// bit line capacitance per cell, as a fraction of one cell's (illustrative)
const CB_PER_CELL: f64 = 0.02;
/// each drawn cell stands for 32 real ones: 16 drawn = 512
const SCALE: f64 = 32.0;

fn cz(i: usize) -> f64 {
    Z0 + i as f64 * P
}

/// How much of the second half of the line is there (beat 1 on), gone at the end.
fn long(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.55) * (1.0 - c.ramp(2, 0.85, 0.99))
}

/// The middle sense amp stripe (beat 2), gone at the end.
fn split(c: &Clock) -> f64 {
    c.ramp(2, 0.1, 0.45) * (1.0 - c.ramp(2, 0.85, 0.99))
}

/// Cells on the bit line the sense amp sees (drawn cells).
fn cells_seen(c: &Clock) -> f64 {
    N as f64 * (1.0 + long(c) * (1.0 - split(c)))
}

fn swing(c: &Clock) -> f64 {
    1.0 / (1.0 + cells_seen(c) * SCALE * CB_PER_CELL)
}

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 40.0, -280.0], dist: 1300.0, yaw: 1.05, pitch: 0.35 },
    Shot { target: [0.0, 40.0, 0.0], dist: 1700.0, yaw: 1.10, pitch: 0.40 },
    Shot { target: [0.0, 40.0, 0.0], dist: 1650.0, yaw: 0.95, pitch: 0.45 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-120.0, -20.0, Z0 - 160.0], [260.0, 0.0, cz(2 * N) + 120.0], STEEL, NO_GLOW);
    let l = long(c);
    let s = split(c);
    for i in 0..2 * N {
        let k = if i < N { 1.0 } else { l };
        if k < 0.01 {
            continue;
        }
        crate::push_tube(m, [0.0, 0.0, cz(i)], [0.0, 40.0 * k, cz(i)], 11.0, 10, ORANGE, stage::scaled(ORANGE, 0.12), true);
    }
    let end = cz(N - 1) + (cz(2 * N - 1) - cz(N - 1)) * l;
    crate::push_tube(m, [18.0, 62.0, Z0 - 30.0], [18.0, 62.0, end + 20.0], 5.0, 10, CYAN, stage::scaled(CYAN, 0.15), false);
    // the end sense amp, and the middle one when the line is cut
    push_box(m, [-40.0, 0.0, Z0 - 110.0], [70.0, 50.0, Z0 - 40.0], PURPLE, stage::scaled(PURPLE, 0.15));
    if s > 0.01 {
        let z = cz(N) - P / 2.0;
        push_box(m, [-40.0, 0.0, z - 30.0 * s], [70.0, 50.0 * s, z + 30.0 * s], PURPLE, stage::scaled(PURPLE, 0.25 * s));
    }
    // the swing bar
    let hgt = swing(c) * 3000.0;
    push_box(m, [180.0, 0.0, -40.0], [240.0, hgt, 20.0], stage::mix(METAL, CYAN, 0.7), stage::scaled(CYAN, 0.2));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let hgt = swing(c) * 3000.0;
    stage::glass_box(cv, cam, [180.0, 0.0, -40.0], [240.0, 300.0, 20.0], GLASS, 0.25);
    let real = (cells_seen(c) * SCALE).round();
    label(cv, cam, [240.0, hgt, 20.0], (0.04, -0.05), &format!("swing, {real:.0} cells on the line"), CYAN, 0.95);
    label(cv, cam, [70.0, 50.0, Z0 - 75.0], (0.04, 0.08), "sense amp", PURPLE, 0.85);
    label(cv, cam, [0.0, 40.0, cz(2 * N - 1)], (0.04, -0.08), "twice the cells: twice Cb", ORANGE, c.during(1, 0.3, 1.0));
    label(cv, cam, [70.0, 50.0, cz(N) - P / 2.0], (0.04, 0.06), "a stripe in the middle: two short lines", PURPLE, split(c));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "swing = Cc / (Cc + Cb)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "illustrative Cb per cell", GLASS, 0.8);
}
