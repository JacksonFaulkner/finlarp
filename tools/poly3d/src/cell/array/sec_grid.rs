//! Section 1: what happens. A grid of cells in rows and columns: the array is read a
//! whole row at a time into the sense amps, then columns are picked from there.

use super::super::stage::{self, Clock, Shot};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

const ROW: usize = 4;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 30.0, 0.0], dist: 1500.0, yaw: -0.30, pitch: 0.80 },
    Shot { target: [0.0, 40.0, 100.0], dist: 1600.0, yaw: 0.20, pitch: 0.55 },
    Shot { target: [120.0, 30.0, 240.0], dist: 1500.0, yaw: 0.55, pitch: 0.60 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let close = c.ramp(2, 0.75, 0.97);
    r.addr = c.during(0, 0.4, 1.0);
    r.wl[ROW] = c.ramp(1, 0.05, 0.3) * (1.0 - close);
    r.share = c.ramp(1, 0.3, 0.6) * (1.0 - close);
    r.sense = c.ramp(1, 0.5, 0.9) * (1.0 - close);
    for col in 4..8 {
        r.read[col] = c.during(2, 0.1, 0.75);
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
}
