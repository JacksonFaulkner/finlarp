//! Section 1: what happens. DRAM dies stacked on a base die, right beside the GPU on
//! a silicon interposer: the package, the stack opened up, and a read crossing to the GPU.

use super::super::stage::{self, Clock, Shot};
use super::rig::{self, Rig, FOCUS};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 40.0, 0.0], dist: 1700.0, yaw: 0.35, pitch: 0.65 },
        Shot { target: [FOCUS[0], 150.0, FOCUS[1]], dist: 850.0, yaw: 0.60, pitch: 0.25 },
        Shot { target: [180.0, 60.0, 60.0], dist: 1100.0, yaw: 0.40, pitch: 0.50 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.explode = c.ramp(1, 0.1, 0.5) * (1.0 - c.ramp(2, 0.0, 0.3));
    r.tsv = c.during(2, 0.1, 0.9);
    r.link = c.during(2, 0.2, 0.95);
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
