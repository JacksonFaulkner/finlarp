//! Zoom e: a burst. The open row sits in the row buffer as a strip of latches. A READ
//! with a column address picks 64 of them; they go out over 8 data pins as 8
//! transfers (burst length 8 on a x8 DDR4 chip). The next READ to the same open row
//! picks another 64 with no activate: that is a row hit.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const LATCHES: usize = 32;
const LP: f64 = 22.0;
const PINS: usize = 8;
const PIN_X: f64 = 520.0;

fn lx(i: usize) -> f64 {
    (i as f64 - (LATCHES as f64 - 1.0) / 2.0) * LP
}

fn pin_z(p: usize) -> f64 {
    (p as f64 - (PINS as f64 - 1.0) / 2.0) * 40.0
}

fn bit(i: usize, row: usize) -> bool {
    (i * 5 + row * 3 + i / 4) % 3 != 0
}

const ROWS: usize = 6;

fn rz(r: usize) -> f64 {
    (r as f64 - (ROWS as f64 - 1.0) / 2.0) * 34.0
}

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 20.0, 0.0], dist: 1150.0, yaw: 0.20, pitch: 0.75 },
    Shot { target: [220.0, 20.0, 0.0], dist: 1100.0, yaw: 0.45, pitch: 0.55 },
    Shot { target: [80.0, 20.0, 0.0], dist: 1200.0, yaw: 0.25, pitch: 0.70 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Selection strength of strip row `r`: the first READ picks rows 1-2, the second
/// (beat 2) rows 4-5. Each pair is 2 x 32 = 64 bits.
fn picked(c: &Clock, r: usize) -> f64 {
    let first = c.ramp(0, 0.2, 0.45) * (1.0 - c.ramp(1, 0.85, 1.0));
    let second = c.ramp(2, 0.1, 0.3) * (1.0 - c.ramp(2, 0.85, 0.99));
    match r {
        1 | 2 => first,
        4 | 5 => second,
        _ => 0.0,
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [lx(0) - 50.0, -20.0, rz(0) - 60.0], [PIN_X + 80.0, 0.0, rz(ROWS - 1) + 60.0], STEEL, NO_GLOW);
    for r in 0..ROWS {
        let k = picked(c, r);
        for i in 0..LATCHES {
            let on = bit(i, r);
            let base = stage::mix(PURPLE, if on { ORANGE } else { [0.18, 0.19, 0.24] }, 0.7);
            let col = stage::mix(stage::mix(QUIET, base, 0.6), stage::mix(base, GREEN, 0.4), k);
            push_box(m, [lx(i) - 8.0, 0.0, rz(r) - 12.0], [lx(i) + 8.0, 16.0 + 12.0 * k, rz(r) + 12.0], col, stage::scaled(GREEN, 0.2 * k));
        }
    }
    for p in 0..PINS {
        push_box(m, [PIN_X - 16.0, 0.0, pin_z(p) - 10.0], [PIN_X + 40.0, 20.0, pin_z(p) + 10.0], stage::mix(METAL, GREEN, 0.3), NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let send = c.during(1, 0.05, 0.85) + c.during(2, 0.3, 0.85);
    // eight transfers: a wave of dots down the eight pins per transfer
    for p in 0..PINS {
        let path = [[lx(LATCHES - 1) + 20.0, 20.0, pin_z(p) * 0.6], [PIN_X - 16.0, 20.0, pin_z(p)], [PIN_X + 120.0, 20.0, pin_z(p)]];
        particles(cv, cam, &path, 8, c.u() * 2.0, 7.0, GREEN, send);
    }
    let first = c.during(0, 0.2, 1.0) + c.during(1, 0.0, 0.85);
    label(cv, cam, [lx(0), 28.0, rz(1)], (-0.18, -0.08), "column address picks 64 bits", GREEN, first.min(1.0));
    label(cv, cam, [PIN_X + 40.0, 20.0, pin_z(0)], (0.03, -0.07), "8 data pins x 8 transfers", GREEN, 0.8);
    label(cv, cam, [lx(0), 16.0, rz(ROWS - 1)], (-0.10, 0.08), "row buffer (open row)", PURPLE, 0.85);
    label(cv, cam, [lx(LATCHES / 2), 28.0, rz(4)], (0.05, 0.08), "next READ: same row, no ACT", CYAN, c.during(2, 0.1, 0.9));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "burst length 8 on a x8 DDR4 chip", TEXT, 0.9);
}
