//! Section 7: packaging. The GPU and its stacks on one silicon interposer (CoWoS): the
//! interposer carries thousands of short wires; the whole assembly sits on a package
//! substrate; and packaging capacity, not wafers, has been the limit on output.

use super::super::stage::{self, text, Clock, Shot, CYAN, GLASS, TEXT};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Tri};

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [180.0, 50.0, 60.0], dist: 1000.0, yaw: 0.45, pitch: 0.45 },
        Shot { target: [0.0, 20.0, 0.0], dist: 1700.0, yaw: 0.20, pitch: 0.25 },
        Shot { target: [0.0, 40.0, 0.0], dist: 1900.0, yaw: 0.55, pitch: 0.75 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.4, ..Rig::default() };
    r.link = c.during(0, 0.1, 1.0) + c.during(1, 0.0, 1.0) + c.during(2, 0.0, 0.9);
    r.link = r.link.min(1.0);
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    rig::names(cv, cam, &r);
    let (title, col) = match c.beat {
        0 => ("the interposer: short, dense wiring", CYAN),
        1 => ("on a package substrate, then onto the board", TEXT),
        _ => ("CoWoS capacity has limited AI accelerator output", TEXT),
    };
    let k = c.during(c.beat, 0.0, 1.0);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, col, k);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "Chip-on-Wafer-on-Substrate (TSMC)", GLASS, 0.8);
}
