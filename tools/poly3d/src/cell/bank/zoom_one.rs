//! Zoom a: one bank. Close on a single bank: it is a whole array with its own row
//! buffer, so it keeps its own open row and walks its own states: idle, ACTIVATE (a
//! row opens), READs from its row buffer, PRECHARGE back to idle.

use super::super::stage::{self, label, text, Clock, Shot, GREEN, ORANGE, PINK, PURPLE, TEXT};
use super::rig::{self, centre, Part, Rig};
use crate::{Cam, Canvas, Tri};

const K: usize = 0;

pub(super) fn shot(c: &Clock) -> Shot {
    let p = centre(K);
    let keys = [
        Shot { target: [p[0], 10.0, p[2]], dist: 950.0, yaw: 0.35, pitch: 0.60 },
        Shot { target: [p[0] * 0.6, 10.0, p[2] * 0.5], dist: 1000.0, yaw: 0.50, pitch: 0.55 },
        Shot { target: [p[0], 10.0, p[2]], dist: 950.0, yaw: 0.15, pitch: 0.65 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    r.cmd[K] = c.during(0, 0.0, 0.4) + c.during(1, 0.0, 0.25) + c.during(2, 0.0, 0.3);
    r.open[K] = c.ramp(0, 0.3, 0.7) * (1.0 - c.ramp(2, 0.2, 0.55));
    r.row[K] = 0.4;
    r.read[K] = c.during(1, 0.2, 0.95);
    r.pre[K] = c.during(2, 0.15, 0.8);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    let p = centre(K);
    label(cv, cam, rig::at(Part::Bank(K)), (0.03, -0.07), "one bank: a whole array", TEXT, 0.9);
    label(cv, cam, [p[0], 20.0, p[2] + 63.0], (-0.12, 0.10), "its own row buffer", PURPLE, 0.9);
    label(cv, cam, [p[0] - 64.0, 27.0, p[2] - 10.0], (-0.16, -0.08), "its own open row", ORANGE, r.open[K]);
    label(cv, cam, rig::at(Part::DataBus), (0.03, -0.05), "READ: data to the shared bus", GREEN, r.read[K]);
    label(cv, cam, [p[0] + 70.0, 24.0, p[2]], (0.04, 0.05), "PRECHARGE: back to idle", PINK, r.pre[K]);
    let state = match c.beat {
        0 => "idle -> ACTIVATE",
        1 => "active: READs",
        _ => "PRECHARGE -> idle",
    };
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, state, ORANGE, c.during(c.beat, 0.0, 1.0));
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "each bank keeps its own state", TEXT, 0.85);
}
