//! Section 6: why it matters for memory. A patch of die ruled in squares of F, the
//! feature size lithography sets. One 1T1C cell covers 3F x 2F = 6F^2. Shrink F by
//! 0.7 and the cell's area halves, so the same patch holds about twice the cells.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const HX: f64 = 330.0;
const HZ: f64 = 220.0;
const F0: f64 = 60.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 0.0, 0.0], dist: 900.0, yaw: 0.30, pitch: 0.85 },
    Shot { target: [0.0, 0.0, 0.0], dist: 950.0, yaw: 0.45, pitch: 0.95 },
    Shot { target: [0.0, 0.0, 0.0], dist: 1150.0, yaw: 0.20, pitch: 0.75 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// F: shrinks by 0.7 in beat 1, back at the end of beat 2.
fn f(c: &Clock) -> f64 {
    F0 * (1.0 - 0.3 * c.ramp(1, 0.1, 0.7) + 0.3 * c.ramp(2, 0.82, 0.98))
}

/// Cells that fit: whole 3F x 2F cells across the patch.
fn cells(f: f64) -> (i32, i32) {
    ((2.0 * HX / (3.0 * f)).floor() as i32, (2.0 * HZ / (2.0 * f)).floor() as i32)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-HX - 20.0, -30.0, -HZ - 20.0], [HX + 20.0, 0.0, HZ + 20.0], STEEL, NO_GLOW);
    let f = f(c);
    let (nx, nz) = cells(f);
    let all = c.during(2, 0.05, 0.85);
    let (x0, z0) = (-(nx as f64) * 1.5 * f, -(nz as f64) * f);
    for i in 0..nx {
        for j in 0..nz {
            let centre = i == nx / 2 && j == nz / 2;
            let k = if centre { 1.0 } else { all };
            let col = stage::mix(QUIET, ORANGE, 0.25 + 0.75 * k);
            let (a, b) = (x0 + i as f64 * 3.0 * f, z0 + j as f64 * 2.0 * f);
            push_box(m, [a + 3.0, 0.0, b + 3.0], [a + 3.0 * f - 3.0, 10.0 + 8.0 * k, b + 2.0 * f - 3.0], col, stage::scaled(ORANGE, 0.15 * k));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let f = f(c);
    let (nx, nz) = cells(f);
    // the F grid
    let y = 20.0;
    let mut x = 0.0;
    while x <= HX {
        for s in [x, -x] {
            cv.line(cam, [s, y, -HZ], [s, y, HZ], GLASS, 0.25);
        }
        x += f;
    }
    let mut z = 0.0;
    while z <= HZ {
        for s in [z, -z] {
            cv.line(cam, [-HX, y, s], [HX, y, s], GLASS, 0.25);
        }
        z += f;
    }
    let (a, b) = (-(nx as f64) * 1.5 * f + (nx / 2) as f64 * 3.0 * f, -(nz as f64) * f + (nz / 2) as f64 * 2.0 * f);
    label(cv, cam, [a + 3.0 * f, 18.0, b], (0.05, -0.10), "one cell: 3F x 2F = 6F^2", ORANGE, 0.95);
    let all = c.during(2, 0.05, 0.85);
    label(cv, cam, [HX, 0.0, HZ], (0.02, 0.08), &format!("{} cells in this patch", nx * nz), TEXT, 0.5 + 0.5 * all);
    let shrink = c.during(1, 0.1, 1.0);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, &format!("F = {:.2} x", f / F0), CYAN, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "F x 0.7 -> cell area x 0.49", TEXT, shrink);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "F is set by the smallest line litho prints", CYAN, 0.8);
}
