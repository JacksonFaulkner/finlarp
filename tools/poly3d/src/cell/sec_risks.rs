//! Section 9: three risks on one bank of rows. Refresh costs time and power, a meter
//! climbing as the rows are rewritten. Refresh blocks access, requests queueing at a
//! closed gate. RowHammer: one row activated over and over leaks charge into its neighbours.

use super::push_box;
use super::stage::{self, label, text, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PINK, STEEL, TEXT, YELLOW};
use super::smooth;
use crate::{Cam, Canvas, Col, Tri};

const ROWS: usize = 9;
const PITCH: f64 = 62.0;
const WIDE: f64 = 44.0;
const LEN: f64 = 300.0;
const TALL: f64 = 220.0;
const MID: usize = ROWS / 2;
const GATE_X: f64 = LEN + 70.0;
const QUEUE_END: f64 = 960.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 70.0, 20.0], dist: 1320.0, yaw: 0.55, pitch: 0.40 },
    Shot { target: [290.0, 70.0, 0.0], dist: 1640.0, yaw: 0.20, pitch: 0.34 },
    Shot { target: [0.0, 90.0, 0.0], dist: 1120.0, yaw: 1.42, pitch: 0.20 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn z(r: usize) -> f64 {
    (r as f64 - (ROWS as f64 - 1.0) / 2.0) * PITCH
}

/// A refresh sweep over the rows during beat 0 and beat 1: the flash at row `r`.
fn sweep_flash(c: &Clock, r: usize) -> f64 {
    let mut f = 0.0f64;
    for (b, a, d) in [(0.0, 0.1, 0.8), (1.0, 0.05, 0.75)] {
        let at = b + a + d * r as f64 / (ROWS - 1) as f64;
        let u = c.u();
        f = f.max(smooth(at - 0.05, at, u) * (1.0 - smooth(at + 0.05, at + 0.13, u)));
    }
    f
}

/// Hammering: strength of the attack, rising through beat 2 and healing at the loop start.
fn hammer(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.0, 0.25)
    } else {
        c.ramp(2, 0.05, 0.9)
    }
}

/// The aggressor row toggles on and off rapidly while the attack runs.
fn pulse(c: &Clock) -> f64 {
    let wave = (c.u() * 24.0 * std::f64::consts::TAU).sin() * 0.5 + 0.5;
    wave * c.during(2, 0.05, 0.95)
}

/// The access gate shuts while the refresh runs in beat 1.
fn gate(c: &Clock) -> f64 {
    c.during(1, 0.02, 0.82)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let half = ROWS as f64 * PITCH / 2.0 + 14.0;
    push_box(m, [-LEN - 24.0, -14.0, -half], [LEN + 24.0, 0.0, half], STEEL, NO_GLOW);
    let h = hammer(c);
    for r in 0..ROWS {
        let flash = sweep_flash(c, r);
        let side = r.abs_diff(MID) == 1;
        let mut lv = 1.0;
        let mut col: Col = stage::scaled(ORANGE, 0.8);
        if side {
            lv = 1.0 - 0.62 * h;
            col = stage::mix(col, PINK, h);
        }
        if r == MID {
            col = stage::mix(col, YELLOW, pulse(c));
        }
        col = stage::mix(col, GREEN, flash);
        let glow = stage::scaled(col, 0.2 + 0.3 * flash);
        push_box(m, [-LEN, 0.0, z(r) - WIDE / 2.0], [LEN, lv * TALL, z(r) + WIDE / 2.0], col, glow);
    }

    // the time-and-power meter: climbs with the refreshes in beat 0, drains after
    let fill = c.ramp(0, 0.1, 0.9) * (1.0 - c.ramp(1, 0.8, 1.0));
    let (x, zz) = (-LEN - 90.0, half - 40.0);
    crate::push_tube(m, [x, 0.0, zz], [x, 12.0, zz], 42.0, 20, STEEL, NO_GLOW, true);
    if fill > 0.005 {
        crate::push_tube(m, [x, 12.0, zz], [x, 12.0 + 260.0 * fill, zz], 28.0, 20, GREEN, stage::scaled(GREEN, 0.3), true);
    }

    // the gate rises out of the floor to block the way in
    let g = gate(c);
    if g > 0.01 {
        push_box(m, [GATE_X - 14.0, 0.0, -66.0], [GATE_X + 14.0, 150.0 * g, 66.0], PINK, stage::scaled(PINK, 0.3));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let half = ROWS as f64 * PITCH / 2.0 + 14.0;
    let u = c.u();
    let g = gate(c);
    let reqs = c.during(1, 0.0, 1.0);

    // requests: run freely when open, bunch up behind the gate when shut
    const N: usize = 8;
    for i in 0..N {
        let s = (u * 1.5 + i as f64 / N as f64).rem_euclid(1.0);
        let free = QUEUE_END - s * (QUEUE_END - LEN + 30.0);
        let held = GATE_X + 40.0 + (N - 1 - i) as f64 * 40.0;
        let x = free + (free.max(held) - free) * g;
        stage::dot(cv, cam, [x, 40.0, 0.0], 15.0, CYAN, reqs);
    }

    let (w, h) = (cv.w as f64, cv.h as f64);
    let (x, zz) = (-LEN - 90.0, half - 40.0);
    label(cv, cam, [x, 12.0, zz], (-0.08, 0.08), "refresh time + power", GREEN, c.during(0, 0.05, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "covering weak cells costs time and power", TEXT, c.during(0, 0.05, 1.0));

    label(cv, cam, [GATE_X, 150.0, 66.0], (-0.05, -0.09), "bank busy: refresh", PINK, g);
    label(cv, cam, [QUEUE_END - 120.0, 40.0, 0.0], (-0.08, 0.10), "requests wait", CYAN, reqs);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "refresh blocks access while it runs", TEXT, reqs);

    let hm = c.during(2, 0.0, 1.0);
    label(cv, cam, [LEN, TALL, z(MID)], (-0.20, -0.09), "activated again and again", YELLOW, hm);
    label(cv, cam, [LEN, hammer(c).mul_add(-0.62, 1.0) * TALL, z(MID + 1)], (-0.10, 0.22), "neighbours lose charge", PINK, hm);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "RowHammer: a reliability and security risk", TEXT, hm);
}
