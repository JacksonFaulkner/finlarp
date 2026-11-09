//! Section 1: a bit is charge on a capacitor. One cell, full (a 1). The transistor opens
//! and it empties (a 0). The camera pulls back and the same cell sits in a field of
//! cells, each holding its own 1 or 0.

use super::push_sphere;
use super::stage::{self, disc_lattice, label, slot_fill, text, Clock, Shot, CYAN, GLASS, METAL, NO_GLOW, ORANGE, PINK, PLATE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const COLS: i32 = 7;
const ROWS: i32 = 5;
const PITCH: f64 = 230.0;
/// the field's stored bits, row by row; the centre cell is the one we watched empty
const BITS: [&str; 5] = ["1011001", "0110110", "1100101", "1001011", "0111010"];

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 40.0, 0.0], dist: 640.0, yaw: 0.45, pitch: 0.30 },
    Shot { target: [0.0, 40.0, 0.0], dist: 640.0, yaw: 0.20, pitch: 0.30 },
    Shot { target: [0.0, 0.0, 30.0], dist: 2450.0, yaw: 0.22, pitch: 0.82 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// The watched cell's charge: refilled at the loop start, emptied through beat 1.
fn charge(c: &Clock) -> f64 {
    if c.beat == 0 {
        c.ramp(0, 0.0, 0.35)
    } else {
        1.0 - c.ramp(1, 0.12, 0.88)
    }
}

/// The word line opens the transistor to write: at the loop start and through beat 1.
fn open(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.35, 0.55)
    } else {
        c.ramp(1, 0.0, 0.12) * (1.0 - c.ramp(1, 0.88, 1.0))
    }
}

/// How far the field of other cells has appeared.
fn field(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.0, 0.3)
    } else {
        c.ramp(2, 0.0, 0.4)
    }
}

/// A plain cell: plates, a transistor on top, and a glowing slab for its charge.
fn small_cell(m: &mut Vec<Tri>, x: f64, z: f64, s: f64, on: bool) {
    let (a, b) = ([x, 0.0, z], s * 70.0);
    for y in [-26.0, 26.0] {
        let y = y * s;
        crate::push_tube(m, [a[0], y - 4.0 * s, z], [a[0], y + 4.0 * s, z], b, 20, PLATE, NO_GLOW, true);
    }
    if on {
        crate::push_tube(m, [x, -16.0 * s, z], [x, 16.0 * s, z], b * 0.82, 16, ORANGE, stage::scaled(ORANGE, 0.5), false);
    }
    super::push_box(m, [x - 20.0 * s, 44.0 * s, z - 14.0 * s], [x + 20.0 * s, 74.0 * s, z + 14.0 * s], QUIET, NO_GLOW);
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let lv = charge(c);
    let op = open(c);
    // the watched cell: big alone, the same size as the others once it joins the field
    let s = 1.0 - 0.53 * field(c);
    for y in [-52.0, 52.0] {
        let y = y * s;
        crate::push_tube(m, [0.0, y - 7.0 * s, 0.0], [0.0, y + 7.0 * s, 0.0], 150.0 * s, 56, PLATE, NO_GLOW, true);
    }
    let pts = disc_lattice(122.0, 34.0, &[-17.0, 17.0]);
    let n = pts.len();
    for (rank, p) in pts.iter().enumerate() {
        let f = slot_fill(rank, n, lv);
        let at = [p[0] * s, p[1] * s, p[2] * s];
        push_sphere(m, at, (5.0 + 8.0 * f) * s, 8, stage::mix(QUIET, ORANGE, f), stage::scaled(ORANGE, 0.5 * f));
    }
    // the wiring belongs to the close-up, and withdraws as the field appears
    let w = (1.0 - field(c) * 2.0).max(0.0);
    if w > 0.01 {
        let y = 150.0;
        crate::push_tube(m, [0.0, 59.0, 0.0], [0.0, y, 0.0], 9.0 * w, 12, METAL, NO_GLOW, false);
        let ch = stage::mix(QUIET, PINK, op);
        crate::push_tube(m, [0.0, y, 0.0], [-210.0, y, 0.0], 10.0 * w, 12, ch, stage::scaled(PINK, 0.45 * op), false);
        crate::push_tube(m, [-210.0, -120.0, 0.0], [-210.0, 250.0, 0.0], 10.0 * w, 12, CYAN, stage::scaled(CYAN, 0.2), true);
        super::push_box(m, [-126.0, y - 20.0 * w, -36.0 * w], [-84.0, y + (34.0 + 22.0 * op) * w, 36.0 * w], STEEL, NO_GLOW);
    } else {
        super::push_box(m, [-20.0 * s, 110.0 * s, -14.0 * s], [20.0 * s, 150.0 * s, 14.0 * s], QUIET, NO_GLOW);
    }

    let k = field(c);
    if k > 0.01 {
        for r in 0..ROWS {
            for q in 0..COLS {
                if r == ROWS / 2 && q == COLS / 2 {
                    continue;
                }
                let (x, z) = ((q - COLS / 2) as f64 * PITCH, (r - ROWS / 2) as f64 * PITCH);
                let on = BITS[r as usize].as_bytes()[q as usize] == b'1';
                small_cell(m, x, z, k, on);
            }
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let lv = charge(c);
    let k = field(c);
    let close = 1.0 - k;
    let u = c.u();
    stage::glass_cyl(cv, cam, [0.0, -45.0, 0.0], 150.0, 90.0, GLASS, 0.18 * close as f32);
    stage::particles(cv, cam, &[[0.0, 40.0, 0.0], [0.0, 150.0, 0.0], [-210.0, 150.0, 0.0], [-210.0, -120.0, 0.0]], 8, u * 1.6, 8.0, ORANGE, c.during(1, 0.1, 0.9));
    stage::particles(cv, cam, &[[-210.0, 250.0, 0.0], [-210.0, 150.0, 0.0], [0.0, 150.0, 0.0], [0.0, 40.0, 0.0]], 8, u * 1.6, 8.0, CYAN, c.during(0, 0.0, 0.38));

    label(cv, cam, [150.0, 52.0, 0.0], (0.02, -0.10), "capacitor", TEXT, 0.9 * close);
    label(cv, cam, [-105.0, 190.0, 0.0], (-0.05, -0.09), "transistor", TEXT, 0.9 * close);
    label(cv, cam, [-210.0, 0.0, 0.0], (-0.20, 0.03), "bit line", CYAN, 0.9 * close);
    // the verdict, big and central: 1 while full, 0 once empty
    let (w, h) = (cv.w as f64, cv.h as f64);
    let (x, y) = ((w * 0.60) as i64, (h * 0.84) as i64);
    text(cv, x, y, "full charge = 1", ORANGE, close * stage::scaled([1.0; 3], (lv * 2.0 - 1.0).clamp(0.0, 1.0))[0] as f64);
    text(cv, x, y, "empty = 0", TEXT, close * ((1.0 - lv) * 2.0 - 1.0).clamp(0.0, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "1 transistor + 1 capacitor = 1T1C", TEXT, close);

    // each cell in the field shows its bit
    if k > 0.3 {
        let a = (k - 0.3) / 0.7;
        for r in 0..ROWS {
            for q in 0..COLS {
                let (x, z) = ((q - COLS / 2) as f64 * PITCH, (r - ROWS / 2) as f64 * PITCH);
                let mid = r == ROWS / 2 && q == COLS / 2;
                let on = !mid && BITS[r as usize].as_bytes()[q as usize] == b'1';
                let Some((px, py, _)) = cam.project([x, 90.0, z]) else { continue };
                text(cv, px as i64 - 4, py as i64 - 18, if on { "1" } else { "0" }, if on { ORANGE } else { TEXT }, a);
            }
        }
        text(cv, (cv.w as f64 * 0.04) as i64, (cv.h as f64 * 0.04) as i64, "every cell holds its own bit", TEXT, a);
    }
}
