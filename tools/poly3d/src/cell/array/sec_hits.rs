//! Section 4: row hits and misses on the subarray. Row A is open. A hit reads it
//! again straight away. A conflict closes A and opens row B first. Then the bank sits
//! closed, and a miss only has to open A again, which brings the loop back to start.
//! A clock in the corner adds up each access's DDR4-3200 time.

use super::super::stage::{self, text, Clock, Shot, CYAN, GREEN, ORANGE, PINK, TEXT};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

const A: usize = 2;
const B: usize = 6;
const T: f64 = 13.75;

const SHOTS: [Shot; 3] = [
    Shot { target: [100.0, 30.0, 200.0], dist: 1500.0, yaw: 0.45, pitch: 0.60 },
    Shot { target: [-60.0, 40.0, 60.0], dist: 1750.0, yaw: -0.25, pitch: 0.65 },
    Shot { target: [0.0, 40.0, 60.0], dist: 1700.0, yaw: 0.15, pitch: 0.70 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Rows and sense: A open at the start; beat 1 closes A and opens B; beat 2 closes B,
/// then opens A again.
fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let a_close = c.ramp(1, 0.05, 0.25);
    let a_open = c.ramp(2, 0.45, 0.6);
    r.wl[A] = (1.0 - a_close) + a_open;
    r.wl[B] = c.ramp(1, 0.3, 0.45) * (1.0 - c.ramp(2, 0.05, 0.25));
    // sensed rows: down while the rows switch, up once the new row is open
    let off1 = c.ramp(1, 0.0, 0.2) * (1.0 - c.ramp(1, 0.45, 0.6));
    let off2 = c.ramp(2, 0.0, 0.2) * (1.0 - c.ramp(2, 0.6, 0.75));
    let held = 1.0 - off1 - off2;
    r.share = held;
    r.sense = held;
    for col in 0..4 {
        r.read[col] = c.during(0, 0.2, 0.9) + c.during(1, 0.7, 1.0) + c.during(2, 0.75, 1.0);
    }
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let (name, ns, col) = match c.beat {
        0 => ("row hit: RD only", T, GREEN),
        1 => ("row conflict: PRE + ACT + RD", 3.0 * T, PINK),
        _ => ("row miss (bank closed): ACT + RD", 2.0 * T, ORANGE),
    };
    let k = c.during(c.beat, 0.0, 1.0);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, name, col, k);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, &format!("{ns:.2} ns at DDR4-3200"), CYAN, k);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "tRP = tRCD = tCL = 13.75 ns", TEXT, 0.8);
}
