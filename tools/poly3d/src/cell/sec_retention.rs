//! Section 5: why the window is what it is. A field of cells, each a column of charge.
//! They leak at different rates. The weakest heads for the level where it can no longer
//! be read, and the refresh has to arrive before it gets there.

use super::push_box;
use super::stage::{self, label, text, Clock, Shot, GREEN, NO_GLOW, ORANGE, PINK, STEEL, TEXT};
use super::{lerp, smooth};
use crate::{Cam, Canvas, Tri};

const N: usize = 7;
const PITCH: f64 = 118.0;
const R: f64 = 30.0;
const TALL: f64 = 250.0;
/// below this a cell can no longer be read; the height is schematic
const FLOOR_LEVEL: f64 = 0.24;
/// the weakest cell only just stays above the line
const WEAK: (usize, usize) = (5, 6);
const WEAK_RATE: f64 = 0.74;
/// leaking runs to here, then the refresh wave sweeps across
const LEAK_END: f64 = 2.45;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 60.0, 30.0], dist: 1420.0, yaw: 0.50, pitch: 0.66 },
    Shot { target: [170.0, 80.0, 200.0], dist: 1020.0, yaw: 0.62, pitch: 0.46 },
    Shot { target: [0.0, 60.0, 30.0], dist: 1420.0, yaw: 0.50, pitch: 0.66 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// A cell's leak rate, fixed per cell and varied: retention differs cell to cell.
fn rate(x: usize, z: usize) -> f64 {
    if (x, z) == WEAK {
        return WEAK_RATE;
    }
    let h = ((x * 7 + z * 13 + x * z * 5) % 17) as f64 / 16.0;
    0.14 + 0.44 * h
}

fn pos(i: usize) -> f64 {
    (i as f64 - (N as f64 - 1.0) / 2.0) * PITCH
}

/// A cell's charge at `u`: leaks steadily, then the refresh wave restores it.
fn level(x: usize, z: usize, c: &Clock) -> f64 {
    let u = c.u();
    let t = (u / LEAK_END).min(1.0);
    let at = LEAK_END + 0.34 * (x + z) as f64 / (2.0 * (N as f64 - 1.0));
    lerp(1.0 - rate(x, z) * t, 1.0, smooth(at, at + 0.14, u))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let half = N as f64 * PITCH / 2.0 + 16.0;
    push_box(m, [-half, -14.0, -half], [half, 0.0, half], STEEL, NO_GLOW);
    for x in 0..N {
        for z in 0..N {
            let lv = level(x, z, c);
            let weak = (x, z) == WEAK;
            let base = if weak { PINK } else { ORANGE };
            let k = 0.4 + 0.6 * lv;
            let (a, b) = (pos(x), pos(z));
            crate::push_tube(m, [a, 0.0, b], [a, lv * TALL, b], R, 14, stage::scaled(base, k), stage::scaled(base, 0.32 * k), true);
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let half = N as f64 * PITCH / 2.0 + 16.0;
    let y = FLOOR_LEVEL * TALL;
    // the unreadable level: a glass plane across the field
    let corners = [[-half, y, -half], [half, y, -half], [half, y, half], [-half, y, half]];
    for i in 0..4 {
        cv.line(cam, corners[i], corners[(i + 1) % 4], PINK, 0.85);
    }
    for k in 1..7 {
        let t = -half + 2.0 * half * k as f64 / 7.0;
        cv.line(cam, [-half, y, t], [half, y, t], PINK, 0.20);
        cv.line(cam, [t, y, -half], [t, y, half], PINK, 0.20);
    }
    let weak = [pos(WEAK.0), level(WEAK.0, WEAK.1, c) * TALL, pos(WEAK.1)];
    label(cv, cam, corners[0], (-0.12, -0.08), "too low to read", PINK, 0.95);
    label(cv, cam, weak, (0.06, 0.12), "weakest cell", PINK, c.during(1, 0.0, 1.0));
    label(cv, cam, weak, (0.06, 0.12), "weakest: just in time", PINK, c.during(2, 0.0, 0.6));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "each cell leaks at its own rate", TEXT, c.during(0, 0.08, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "the weakest cells set the refresh window", TEXT, c.during(1, 0.2, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "refresh: all back to full, for all cells", GREEN, c.during(2, 0.45, 0.98));
}
