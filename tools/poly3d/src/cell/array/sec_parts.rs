//! Section 2: the parts. The subarray, one part in the spotlight per beat: it keeps
//! its colour and acts, the rest go grey, and the camera moves to it.

use super::super::stage::{self, spotlight, text, Clock, Shot, CYAN, GREEN, ORANGE, PURPLE, TEXT};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;
const ROW: usize = 3;

const SHOTS: [Shot; BEATS] = [
    Shot { target: [0.0, 30.0, 0.0], dist: 1200.0, yaw: 0.30, pitch: 0.65 },
    Shot { target: [-250.0, 40.0, 0.0], dist: 1300.0, yaw: -0.60, pitch: 0.50 },
    Shot { target: [100.0, 50.0, 80.0], dist: 1300.0, yaw: 0.10, pitch: 0.45 },
    Shot { target: [0.0, 40.0, 280.0], dist: 1100.0, yaw: 0.20, pitch: 0.50 },
    Shot { target: [100.0, 30.0, 360.0], dist: 1100.0, yaw: 0.45, pitch: 0.55 },
    Shot { target: [300.0, 30.0, 380.0], dist: 1100.0, yaw: 0.70, pitch: 0.50 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let s = |i: usize| spotlight(c, i, BEATS);
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    for i in 0..BEATS {
        r.colour[i] = 0.15 + 0.85 * s(i);
    }
    // word line beat: the row opens; bit line and sense amp beats: it is sensed; reads
    // in the column decoder and I/O beats
    r.addr = s(1);
    r.wl[ROW] = (s(1) + s(2) + s(3) + s(4) + s(5)).min(1.0);
    r.share = (s(2) + s(3) + s(4) + s(5)).min(1.0);
    r.sense = (s(3) + s(4) + s(5)).min(1.0);
    for col in 2..6 {
        r.read[col] = (s(4) + s(5)).min(1.0);
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
    let jobs: [(&str, Col); BEATS] = [
        ("cells: one bit each, in rows and columns", ORANGE),
        ("row decoder: raises one word line, opening a row", TEXT),
        ("bit lines: one per column, carry each cell's charge", CYAN),
        ("sense amps: latch the whole row (the row buffer)", PURPLE),
        ("column decoder: picks which latches to read", GREEN),
        ("I/O: sends the chosen bits off the chip", GREEN),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, (job, col)) in jobs.iter().enumerate() {
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, *col, spotlight(c, i, BEATS));
    }
}
