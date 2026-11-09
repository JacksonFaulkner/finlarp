//! Section 2: the parts. The chip, one part in the spotlight per beat: banks, bank
//! groups, command bus, data bus, I/O, and the controller's commands coming in.

use super::super::stage::{self, spotlight, text, Clock, Shot, GREEN, ORANGE, TEXT};
use super::rig::{self, centre, Rig, CTRL, IO, N};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;

pub(super) fn shot(c: &Clock) -> Shot {
    let b = centre(5);
    let keys = [
        Shot { target: [b[0], 0.0, b[2]], dist: 1000.0, yaw: 0.30, pitch: 0.70 },
        Shot { target: [0.0, 0.0, 0.0], dist: 1800.0, yaw: 0.20, pitch: 0.90 },
        Shot { target: [0.0, 0.0, -250.0], dist: 1400.0, yaw: -0.40, pitch: 0.60 },
        Shot { target: [150.0, 0.0, 0.0], dist: 1400.0, yaw: 0.70, pitch: 0.55 },
        Shot { target: [IO[0], 0.0, IO[2] - 100.0], dist: 1100.0, yaw: 0.30, pitch: 0.55 },
        Shot { target: [CTRL[0], 0.0, CTRL[2] + 100.0], dist: 1100.0, yaw: 2.9, pitch: 0.55 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let s = |i: usize| spotlight(c, i, BEATS);
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    for i in 0..BEATS {
        r.colour[i] = 0.15 + 0.85 * s(i);
    }
    r.open[5] = s(0);
    for i in [0, 4, 8, 12] {
        r.open[i] = s(1);
    }
    r.cmd[6] = s(2) + s(5);
    r.open[6] = s(3) + s(4);
    r.read[6] = s(3) + s(4);
    for i in 0..N {
        r.open[i] = r.open[i].min(1.0);
        r.cmd[i] = r.cmd[i].min(1.0);
        r.read[i] = r.read[i].min(1.0);
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
    rig::bank_label(cv, cam, 5, "bank: an array with its own row buffer", ORANGE, spotlight(c, 0, BEATS));
    let jobs: [(&str, Col); BEATS] = [
        ("bank: holds its own open row", ORANGE),
        ("bank group: 4 banks sharing some circuits", TEXT),
        ("command bus: one command at a time", TEXT),
        ("data bus: shared by every bank", GREEN),
        ("I/O: the chip's data pins", GREEN),
        ("controller: decides the order of commands", TEXT),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, (job, col)) in jobs.iter().enumerate() {
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, *col, spotlight(c, i, BEATS));
    }
}
