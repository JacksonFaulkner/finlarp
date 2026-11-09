//! Section 3: building a stack, in order. DRAM dies arrive one by one; they are thinned
//! and given TSVs and bumps (shown pulled apart); bonded down onto the base die; tested
//! with a read down the TSVs; and the stack is mounted beside the GPU and linked across
//! the interposer. Then the stack is taken away for the next build.

use super::super::stage::{self, text, Clock, Shot, GLASS, ORANGE};
use super::rig::{self, Rig, FOCUS};
use crate::{Cam, Canvas, Tri};

pub(super) const BEATS: usize = 5;

pub(super) fn shot(c: &Clock) -> Shot {
    let f = |y: f64| [FOCUS[0], y, FOCUS[1]];
    let keys = [
        Shot { target: f(100.0), dist: 850.0, yaw: 0.50, pitch: 0.30 },
        Shot { target: f(170.0), dist: 850.0, yaw: 0.70, pitch: 0.22 },
        Shot { target: f(110.0), dist: 800.0, yaw: 0.40, pitch: 0.25 },
        Shot { target: f(110.0), dist: 800.0, yaw: 0.25, pitch: 0.25 },
        Shot { target: [180.0, 60.0, 60.0], dist: 1200.0, yaw: 0.40, pitch: 0.55 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.dies = 8.0 * c.ramp(0, 0.05, 0.9) * (1.0 - c.ramp(4, 0.85, 0.99));
    r.explode = c.ramp(1, 0.1, 0.5) * (1.0 - c.ramp(2, 0.1, 0.6));
    r.tsv = c.during(3, 0.1, 0.9);
    r.link = c.during(4, 0.1, 0.85);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    const STEPS: [&str; BEATS] = ["1 dies", "2 thin + TSV", "3 bond", "4 test", "5 mount"];
    let (w, h) = (cv.w as f64, cv.h as f64);
    let sc = stage::text_scale(cv);
    let mut x = (w * 0.04) as i64;
    for (i, st) in STEPS.iter().enumerate() {
        let k = stage::spotlight(c, i, BEATS);
        text(cv, x, (h * 0.92) as i64, st, stage::mix(GLASS, ORANGE, k), 0.45 + 0.55 * k);
        x += stage::text_w(st, sc) + 10 * sc;
    }
}
