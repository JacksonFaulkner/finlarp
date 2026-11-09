//! Section 2: the parts. The scanner, one part in the spotlight per beat: it keeps
//! its colour and acts, the rest go grey, and the camera moves to it.

use super::super::stage::{self, spotlight, text, Clock, Shot, CYAN, GREEN, PURPLE, TEXT, YELLOW};
use super::rig::{self, Rig};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;

const SHOTS: [Shot; BEATS] = [
    Shot { target: [0.0, 800.0, 0.0], dist: 1300.0, yaw: 0.50, pitch: 0.20 },
    Shot { target: [0.0, 640.0, 0.0], dist: 1200.0, yaw: 0.35, pitch: 0.45 },
    Shot { target: [0.0, 360.0, 0.0], dist: 1400.0, yaw: 0.60, pitch: 0.12 },
    Shot { target: [60.0, 66.0, 200.0], dist: 1250.0, yaw: 0.30, pitch: 0.62 },
    Shot { target: [0.0, 30.0, 0.0], dist: 1700.0, yaw: 0.70, pitch: 0.35 },
    Shot { target: [140.0, 200.0, 0.0], dist: 1200.0, yaw: 0.40, pitch: 0.30 },
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
    r.light = (s(0) + s(1) + s(2)).min(1.0);
    r.project = s(2);
    let fill = s(3);
    for e in r.exposed.iter_mut() {
        e.0 = fill;
    }
    // the stage shows it moves: a slow figure across its travel
    let k = s(4);
    let th = c.local * std::f64::consts::TAU;
    r.wafer = [90.0 * th.sin() * k, 70.0 * (2.0 * th).sin() * k];
    r.align = s(5);
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
        ("wavelength: DUV 193 nm, EUV 13.5 nm", YELLOW),
        ("reticle: the pattern, one mask per layer", TEXT),
        ("lens: sets NA, prints the image 4x smaller", CYAN),
        ("photoresist: exposed part develops away", PURPLE),
        ("wafer stage: field by field across the wafer", TEXT),
        ("overlay: this layer lined up on the last", GREEN),
    ];
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, (job, col)) in jobs.iter().enumerate() {
        text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, *col, spotlight(c, i, BEATS));
    }
}
