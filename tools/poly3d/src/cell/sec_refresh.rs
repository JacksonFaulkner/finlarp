//! Section 4: refresh on a timer. A ring is the 64 ms window and its ticks are REF
//! commands. Each one the hand reaches rewrites the next slice of rows in the stack at
//! the centre, so by the time the ring closes every row has had its turn.

use super::push_box;
use super::stage::{self, label, text, Clock, Shot, GREEN, NO_GLOW, ORANGE, QUIET, STEEL, TEXT, YELLOW};
use super::smooth;
use crate::{Cam, Canvas, Tri, V3};

const RING_R: f64 = 470.0;
const TICKS: usize = 64;
const SLICES: usize = 16;
const SLICE_H: f64 = 22.0;
const SLICE_GAP: f64 = 6.0;
const HALF: f64 = 190.0;
/// the hand finishes the ring here, leaving the end of the loop to fade out
const SWEEP: f64 = 2.72;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 60.0, 80.0], dist: 1560.0, yaw: 0.40, pitch: 0.62 },
    Shot { target: [0.0, 190.0, 0.0], dist: 1040.0, yaw: 0.65, pitch: 0.30 },
    Shot { target: [0.0, 90.0, 40.0], dist: 1560.0, yaw: 0.40, pitch: 0.72 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// How far round the window: 0..1.
fn sweep(c: &Clock) -> f64 {
    (c.u() / SWEEP).clamp(0.0, 1.0)
}

/// Everything lit returns to dark as the next window starts.
fn reset(c: &Clock) -> f64 {
    1.0 - c.ramp(2, 0.82, 1.0)
}

fn on_ring(s: f64, r: f64, y: f64) -> V3 {
    // starts at the front and runs clockwise seen from above
    let th = std::f64::consts::TAU * s + std::f64::consts::FRAC_PI_2;
    [r * th.cos(), y, r * th.sin()]
}

fn slice_y(i: usize) -> f64 {
    20.0 + i as f64 * (SLICE_H + SLICE_GAP)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let s = sweep(c);
    let back = reset(c);
    crate::push_tube(m, [0.0, -14.0, 0.0], [0.0, 0.0, 0.0], RING_R + 40.0, 72, STEEL, NO_GLOW, true);
    for i in 0..TICKS {
        let at = i as f64 / TICKS as f64;
        let done = smooth(at, at + 0.012, s) * back;
        let p = on_ring(at, RING_R, 0.0);
        let col = stage::mix(QUIET, ORANGE, done);
        let h = 16.0 + 14.0 * done;
        push_box(m, [p[0] - 7.0, 0.0, p[2] - 7.0], [p[0] + 7.0, h, p[2] + 7.0], col, stage::scaled(ORANGE, 0.35 * done));
    }
    // the hand: from the centre stack out to the current tick
    let tip = on_ring(s, RING_R - 16.0, 18.0);
    crate::push_tube(m, on_ring(s, HALF + 30.0, 18.0), tip, 6.0, 8, TEXT, stage::scaled(TEXT, 0.3), true);

    // the array as slices of rows; each REF rewrites one
    for i in 0..SLICES {
        let at = i as f64 / SLICES as f64;
        let hit = at + 0.02;
        let done = smooth(hit, hit + 0.03, s) * back;
        let flash = smooth(hit - 0.02, hit, s) * (1.0 - smooth(hit + 0.02, hit + 0.05, s)) * back;
        let col = stage::mix(stage::mix(QUIET, GREEN, done), YELLOW, flash);
        let y = slice_y(i);
        push_box(m, [-HALF, y, -HALF], [HALF, y + SLICE_H, HALF], col, stage::scaled(col, 0.15 + 0.35 * flash));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let s = sweep(c);
    let live = c.ramp(0, 0.0, 0.1) * reset(c);
    let tip = on_ring(s, RING_R, 34.0);
    stage::dot(cv, cam, tip, 20.0, TEXT, live);
    let i = ((s * SLICES as f64) as usize).min(SLICES - 1);
    let top = [HALF, slice_y(i) + SLICE_H / 2.0, HALF];

    label(cv, cam, tip, (0.03, -0.08), "REF", TEXT, live * (1.0 - c.during(1, 0.0, 1.0)) * (1.0 - c.ramp(2, 0.4, 0.6)));
    label(cv, cam, on_ring(0.62, RING_R, 0.0), (-0.12, -0.10), "one REF every 7800 ns", ORANGE, c.during(0, 0.1, 1.0));
    label(cv, cam, top, (0.10, -0.06), "a slice of rows", YELLOW, c.during(1, 0.05, 0.98));
    let (w, h) = (cv.w as f64, cv.h as f64);
    let done = c.during(2, 0.15, 0.92);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "8192 REF in 64 ms: every row got its turn", GREEN, done);
    text(cv, (w * 0.04) as i64, (h * 0.93) as i64, "ring = 64 ms window. 64 ticks drawn, 8192 real", TEXT, 0.8 * c.ramp(0, 0.0, 0.1) * (1.0 - c.ramp(2, 0.0, 0.15)));
}
