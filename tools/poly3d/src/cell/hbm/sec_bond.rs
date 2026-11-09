//! Section 6: bonding. The stack opened to show microbumps between the dies; closed
//! again on its bumps; then hybrid bonding, copper to copper, which removes the bump
//! gaps and makes the stack shorter. It returns to bumps for the loop.

use super::super::stage::{self, text, Clock, Shot, GLASS, TEXT};
use super::rig::{self, Rig, FOCUS};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let f = |y: f64| [FOCUS[0], y, FOCUS[1]];
    let keys = [
        Shot { target: f(170.0), dist: 800.0, yaw: 0.70, pitch: 0.20 },
        Shot { target: f(100.0), dist: 650.0, yaw: 0.40, pitch: 0.15 },
        Shot { target: f(90.0), dist: 650.0, yaw: 0.30, pitch: 0.15 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.explode = c.ramp(0, 0.1, 0.5) * (1.0 - c.ramp(1, 0.0, 0.4));
    r.hybrid = c.ramp(2, 0.1, 0.5) * (1.0 - c.ramp(2, 0.86, 0.99));
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let (title, sub) = match c.beat {
        0 => ("microbumps between every pair of dies", "pitch about 40 um, shrinking toward 10 um"),
        1 => ("bonded on its bumps: a small gap per die", "HBM4 keeps microbumps"),
        _ => ("hybrid bonding: copper to copper, no gap", "the next step beyond 16-high"),
    };
    let k = c.during(c.beat, 0.0, 1.0);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, TEXT, k);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, sub, GLASS, k);
}
