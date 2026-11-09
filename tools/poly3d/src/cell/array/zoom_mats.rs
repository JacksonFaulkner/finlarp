//! Zoom c: mats, subarrays, the bank. One mat: a small grid of cells with its local
//! word line drivers on one side and sense amp stripes on two. Mats tile in a line
//! into a subarray, under a global word line. Subarrays stack into a bank, joined by
//! global bit lines to the bank's I/O; only one subarray's row is open at a time.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const N: usize = 4;
const SP: f64 = 260.0;
const HALF: f64 = 95.0;
const FIRST: (usize, usize) = (1, 1);
const ACTIVE: usize = 1;

const fn mx(i: usize) -> f64 {
    (i as f64 - 1.5) * SP
}

const fn mz(j: usize) -> f64 {
    (j as f64 - 1.5) * SP
}

/// How present mat (i, j) is: the first always, its row in beat 1, the rest in beat 2.
fn present(c: &Clock, i: usize, j: usize) -> f64 {
    let p = if (i, j) == FIRST {
        return 1.0;
    } else if j == FIRST.1 {
        c.ramp(1, 0.1, 0.5)
    } else {
        c.ramp(2, 0.05, 0.45)
    };
    p * (1.0 - c.ramp(2, 0.85, 0.99))
}

const SHOTS: [Shot; 3] = [
    Shot { target: [mx(1), 20.0, mz(1)], dist: 800.0, yaw: 0.40, pitch: 0.55 },
    Shot { target: [0.0, 20.0, mz(1)], dist: 1400.0, yaw: 0.30, pitch: 0.55 },
    Shot { target: [0.0, 20.0, 0.0], dist: 1900.0, yaw: 0.25, pitch: 0.75 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-2.4 * SP, -24.0, -2.4 * SP], [2.4 * SP, 0.0, 2.4 * SP], STEEL, NO_GLOW);
    let bank = c.during(2, 0.3, 1.0);
    for j in 0..N {
        for i in 0..N {
            let p = present(c, i, j);
            if p < 0.01 {
                continue;
            }
            let (x, z) = (mx(i), mz(j));
            let on = if j == ACTIVE { 1.0 } else { 1.0 - bank };
            let cells = stage::mix(QUIET, ORANGE, 0.35 + 0.5 * on);
            push_box(m, [x - HALF, 0.0, z - HALF], [x + HALF, 30.0 * p, z + HALF], cells, stage::scaled(ORANGE, 0.08 * on));
            // sense amp stripes front and back, word line drivers on the left
            for dz in [-HALF - 14.0, HALF + 14.0] {
                push_box(m, [x - HALF, 0.0, z + dz - 10.0], [x + HALF, 22.0 * p, z + dz + 10.0], stage::mix(QUIET, PURPLE, 0.4 + 0.5 * on), NO_GLOW);
            }
            push_box(m, [x - HALF - 26.0, 0.0, z - HALF], [x - HALF - 8.0, 26.0 * p, z + HALF], METAL, NO_GLOW);
        }
    }
    // global word line over the subarray, global bit lines across the bank
    let gwl = c.ramp(1, 0.4, 0.8) * (1.0 - c.ramp(2, 0.85, 0.99));
    if gwl > 0.01 {
        crate::push_tube(m, [mx(0) - HALF, 60.0, mz(ACTIVE)], [mx(0) - HALF + (4.0 * SP) * gwl, 60.0, mz(ACTIVE)], 6.0, 10, ORANGE, stage::scaled(ORANGE, 0.3), false);
    }
    let gbl = c.ramp(2, 0.3, 0.7) * (1.0 - c.ramp(2, 0.85, 0.99));
    if gbl > 0.01 {
        for i in 0..N {
            let x = mx(i) + 40.0;
            crate::push_tube(m, [x, 74.0, mz(0) - HALF], [x, 74.0, mz(0) - HALF + 4.0 * SP * gbl], 5.0, 10, CYAN, stage::scaled(CYAN, 0.25), false);
        }
        push_box(m, [mx(0) - HALF, 0.0, mz(N - 1) + HALF + 50.0], [mx(N - 1) + HALF, 30.0 * gbl, mz(N - 1) + HALF + 90.0], stage::mix(METAL, CYAN, 0.4), NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    // the mat's own cell grid
    let (x, z) = (mx(FIRST.0), mz(FIRST.1));
    for k in 0..=6 {
        let t = -HALF + k as f64 * HALF / 3.0;
        cv.line(cam, [x + t, 31.0, z - HALF], [x + t, 31.0, z + HALF], GLASS, 0.3);
        cv.line(cam, [x - HALF, 31.0, z + t], [x + HALF, 31.0, z + t], GLASS, 0.3);
    }
    let one = 1.0 - c.during(2, 0.0, 1.0) * 0.6;
    label(cv, cam, [x + HALF, 30.0, z - HALF], (0.04, -0.10), "one mat: a small grid of cells", ORANGE, one);
    label(cv, cam, [x, 22.0, z + HALF + 14.0], (-0.12, 0.09), "sense amp stripes", PURPLE, c.during(0, 0.1, 1.0));
    label(cv, cam, [x - HALF - 17.0, 26.0, z - HALF], (-0.22, 0.10), "local word line drivers", TEXT, c.during(0, 0.1, 1.0));
    let gwl = c.during(1, 0.4, 1.0);
    label(cv, cam, [mx(N - 1) + HALF, 60.0, mz(ACTIVE)], (0.03, -0.07), "subarray: mats in a row, one global word line", ORANGE, gwl);
    let bank = c.during(2, 0.3, 1.0);
    label(cv, cam, [mx(N - 1) + HALF, 30.0, mz(N - 1) + HALF + 70.0], (0.03, 0.06), "bank: subarrays share global bit lines", CYAN, bank);
    label(cv, cam, [mx(0) - HALF, 30.0, mz(ACTIVE)], (-0.14, 0.05), "only this subarray is open", ORANGE, bank);
    // data from the open subarray down the global bit lines
    for i in 0..N {
        let px = mx(i) + 40.0;
        particles(cv, cam, &[[px, 76.0, mz(ACTIVE)], [px, 76.0, mz(N - 1) + HALF + 60.0]], 4, c.u() * 1.6 + i as f64 * 0.2, 7.0, CYAN, bank);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "a bank is many subarrays, each with its own sense amps", TEXT, 0.9);
}
