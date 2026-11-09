//! Section 1: what happens. The scanner, three beats: light passes the reticle, the
//! lens prints its image 4x smaller onto the resist, and develop leaves the pattern.

use super::super::stage::{self, Clock, Shot};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 640.0, 0.0], dist: 1600.0, yaw: 0.45, pitch: 0.22 },
    Shot { target: [0.0, 330.0, 0.0], dist: 2000.0, yaw: 0.65, pitch: 0.18 },
    Shot { target: [60.0, 66.0, 200.0], dist: 1250.0, yaw: 0.30, pitch: 0.62 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// The field under the lens when the stage is parked.
pub(super) fn centre_field() -> usize {
    rig::fields().iter().position(|f| f[0] == 0.0 && f[1] == 0.0).unwrap_or(0)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let off = 1.0 - c.ramp(2, 0.0, 0.2);
    r.light = c.ramp(0, 0.1, 0.4) * off;
    r.project = c.ramp(1, 0.05, 0.4) * off;
    let reset = 1.0 - c.ramp(2, 0.75, 0.97);
    r.exposed[centre_field()] = (c.ramp(1, 0.4, 0.95) * reset, 1.0);
    r.develop = c.ramp(2, 0.1, 0.5) * reset;
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
