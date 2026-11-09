//! Section 3: one interleaved access, in order. ACT bank A, ACT bank B (another
//! group), READ A, READ B, PRECHARGE both. The step names run along the bottom.

use super::super::stage::{self, text, Clock, Shot, GLASS, ORANGE};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

pub(super) const BEATS: usize = 5;
const A: usize = 0;
const B: usize = 4;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-250.0, 0.0, -150.0], dist: 1300.0, yaw: 0.10, pitch: 0.70 },
        Shot { target: [0.0, 0.0, -150.0], dist: 1400.0, yaw: 0.20, pitch: 0.70 },
        Shot { target: [-100.0, 0.0, 50.0], dist: 1600.0, yaw: 0.35, pitch: 0.65 },
        Shot { target: [100.0, 0.0, 50.0], dist: 1600.0, yaw: 0.45, pitch: 0.65 },
        Shot { target: [0.0, 0.0, -100.0], dist: 1600.0, yaw: 0.20, pitch: 0.80 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let close = c.ramp(4, 0.2, 0.7);
    r.cmd[A] = c.during(0, 0.0, 0.4) + c.during(2, 0.0, 0.3) + c.during(4, 0.0, 0.3);
    r.cmd[B] = c.during(1, 0.0, 0.4) + c.during(3, 0.0, 0.3) + c.during(4, 0.1, 0.4);
    r.open[A] = c.ramp(0, 0.3, 0.7) * (1.0 - close);
    r.open[B] = c.ramp(1, 0.3, 0.7) * (1.0 - close);
    r.row[A] = 0.3;
    r.row[B] = 0.65;
    r.read[A] = c.during(2, 0.2, 0.95);
    r.read[B] = c.during(3, 0.2, 0.95);
    r.pre[A] = c.during(4, 0.1, 0.8);
    r.pre[B] = c.during(4, 0.15, 0.85);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    rig::bank_label(cv, cam, A, "bank A", ORANGE, r.open[A]);
    rig::bank_label(cv, cam, B, "bank B", ORANGE, r.open[B]);
    const STEPS: [&str; BEATS] = ["1 ACT A", "2 ACT B", "3 RD A", "4 RD B", "5 PRE"];
    let (w, h) = (cv.w as f64, cv.h as f64);
    let sc = stage::text_scale(cv);
    let mut x = (w * 0.04) as i64;
    for (i, st) in STEPS.iter().enumerate() {
        let k = stage::spotlight(c, i, BEATS);
        text(cv, x, (h * 0.92) as i64, st, stage::mix(GLASS, ORANGE, k), 0.45 + 0.55 * k);
        x += stage::text_w(st, sc) + 10 * sc;
    }
}
