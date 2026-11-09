//! Section 3: one access, in order. Five beats on the subarray: precharged and idle,
//! ACTIVATE, sense, READ, PRECHARGE. The step names run along the bottom.

use super::super::stage::{self, text, Clock, Shot, GLASS, ORANGE};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

pub(super) const BEATS: usize = 5;
const ROW: usize = 5;

const SHOTS: [Shot; BEATS] = [
    Shot { target: [0.0, 40.0, 60.0], dist: 1700.0, yaw: 0.10, pitch: 0.70 },
    Shot { target: [-120.0, 40.0, 60.0], dist: 1600.0, yaw: -0.40, pitch: 0.55 },
    Shot { target: [0.0, 40.0, 220.0], dist: 1300.0, yaw: 0.20, pitch: 0.50 },
    Shot { target: [140.0, 30.0, 300.0], dist: 1400.0, yaw: 0.55, pitch: 0.55 },
    Shot { target: [0.0, 40.0, 100.0], dist: 1700.0, yaw: 0.20, pitch: 0.70 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let close = c.ramp(4, 0.1, 0.5);
    r.addr = c.during(0, 0.4, 1.0);
    r.wl[ROW] = c.ramp(1, 0.05, 0.35) * (1.0 - close);
    r.share = c.ramp(1, 0.35, 0.9) * (1.0 - c.ramp(4, 0.3, 0.8));
    r.sense = c.ramp(2, 0.05, 0.6) * (1.0 - c.ramp(4, 0.3, 0.8));
    for col in 6..10 {
        r.read[col] = c.during(3, 0.1, 0.95);
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
    const STEPS: [&str; BEATS] = ["1 idle", "2 ACT", "3 sense", "4 READ", "5 PRE"];
    let (w, h) = (cv.w as f64, cv.h as f64);
    let sc = stage::text_scale(cv);
    let mut x = (w * 0.04) as i64;
    for (i, st) in STEPS.iter().enumerate() {
        let k = stage::spotlight(c, i, BEATS);
        text(cv, x, (h * 0.92) as i64, st, stage::mix(GLASS, ORANGE, k), 0.45 + 0.55 * k);
        x += stage::text_w(st, sc) + 10 * sc;
    }
}
