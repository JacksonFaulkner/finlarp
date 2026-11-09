//! Section 2: the parts, one in the spotlight per beat: DRAM dies, base logic die,
//! TSVs, microbumps, the silicon interposer and the GPU.

use super::super::stage::{self, spotlight, text, Clock, Shot, CYAN, ORANGE, PURPLE, TEXT, YELLOW};
use super::rig::{self, Rig, COPPER, FOCUS};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;

pub(super) fn shot(c: &Clock) -> Shot {
    let f = |y: f64| [FOCUS[0], y, FOCUS[1]];
    let keys = [
        Shot { target: f(110.0), dist: 800.0, yaw: 0.55, pitch: 0.35 },
        Shot { target: f(60.0), dist: 700.0, yaw: 0.40, pitch: 0.20 },
        Shot { target: f(170.0), dist: 850.0, yaw: 0.30, pitch: 0.20 },
        Shot { target: f(170.0), dist: 800.0, yaw: 0.70, pitch: 0.20 },
        Shot { target: [200.0, 40.0, 100.0], dist: 1300.0, yaw: 0.50, pitch: 0.55 },
        Shot { target: [0.0, 60.0, 0.0], dist: 1100.0, yaw: 0.20, pitch: 0.60 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let s = |i: usize| spotlight(c, i, BEATS);
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    for i in 0..BEATS {
        r.colour[i] = 0.15 + 0.85 * s(i);
    }
    r.explode = (s(2) + s(3)).min(1.0);
    r.tsv = s(2);
    r.link = (s(4) + s(5)).min(1.0);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let jobs: [(&str, Col); BEATS] = [
        ("DRAM dies: the memory, stacked", ORANGE),
        ("base logic die: PHY, test, TSV landing", CYAN),
        ("TSVs: vertical wires through every die", COPPER),
        ("microbumps: the joints between dies", YELLOW),
        ("interposer: thousands of short wires", TEXT),
        ("GPU: the stack's customer, millimetres away", PURPLE),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, (job, col)) in jobs.iter().enumerate() {
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, *col, spotlight(c, i, BEATS));
    }
}
