//! Zoom b: row hit, row miss, row conflict. Three lanes of timeline, built up one per
//! beat, each segment as long as its DDR4-3200 time: a hit needs only the column read
//! (tCL), a miss on a closed bank adds the activate (tRCD), and a conflict also has to
//! close the old row first (tRP). The bars clear at the end of the loop.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PINK, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

/// DDR4-3200 22-22-22: tRP = tRCD = tCL = 13.75 ns
const T: f64 = 13.75;
/// world units per ns
const NS: f64 = 14.0;
const X0: f64 = -300.0;
const LANE: f64 = 160.0;

/// Segments per lane: label, colour.
fn lanes() -> [(&'static str, Vec<(&'static str, Col)>); 3] {
    [
        ("row hit", vec![("RD tCL", GREEN)]),
        ("row miss", vec![("ACT tRCD", ORANGE), ("RD tCL", GREEN)]),
        ("row conflict", vec![("PRE tRP", PINK), ("ACT tRCD", ORANGE), ("RD tCL", GREEN)]),
    ]
}

fn lane_z(i: usize) -> f64 {
    (i as f64 - 1.0) * LANE
}

const SHOTS: [Shot; 3] = [
    Shot { target: [-120.0, 30.0, -100.0], dist: 1300.0, yaw: 0.20, pitch: 0.55 },
    Shot { target: [-40.0, 30.0, -20.0], dist: 1400.0, yaw: 0.25, pitch: 0.60 },
    Shot { target: [20.0, 30.0, 40.0], dist: 1500.0, yaw: 0.30, pitch: 0.65 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// How far lane `i` has grown, 0..1 of its length; all clear at the loop's end.
fn grown(c: &Clock, i: usize) -> f64 {
    c.ramp(i, 0.1, 0.75) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [X0 - 40.0, -20.0, -LANE * 1.6], [X0 + 3.0 * T * NS + 60.0, 0.0, LANE * 1.6], STEEL, NO_GLOW);
    for (i, (_, segs)) in lanes().iter().enumerate() {
        let z = lane_z(i);
        let total = segs.len() as f64 * T * NS;
        let reach = X0 + total * grown(c, i);
        let mut x = X0;
        for (_, col) in segs {
            let end = (x + T * NS).min(reach);
            if end > x + 0.5 {
                push_box(m, [x + 2.0, 0.0, z - 40.0], [end - 2.0, 36.0, z + 40.0], *col, stage::scaled(*col, 0.15));
            }
            x += T * NS;
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    // a tick every 13.75 ns
    for k in 0..=3 {
        let x = X0 + k as f64 * T * NS;
        cv.line(cam, [x, 1.0, -LANE * 1.5], [x, 1.0, LANE * 1.5], stage::GLASS, 0.35);
    }
    for (i, (name, segs)) in lanes().iter().enumerate() {
        let z = lane_z(i);
        let g = grown(c, i);
        label(cv, cam, [X0, 36.0, z], (-0.16, -0.04), name, TEXT, 0.5 + 0.5 * g.min(1.0));
        let ns = segs.len() as f64 * T;
        label(cv, cam, [X0 + ns * NS, 36.0, z + 40.0], (0.03, 0.04), &format!("{ns:.2} ns"), CYAN, g);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "DDR4-3200 22-22-22: 13.75 ns each", TEXT, 0.9);
    let sc = stage::text_scale(cv);
    let mut x = (w * 0.04) as i64;
    for (seg, col) in [("PRE tRP", PINK), ("ACT tRCD", ORANGE), ("RD tCL", GREEN)] {
        text(cv, x, (h * 0.10) as i64, seg, col, 0.9);
        x += stage::text_w(seg, sc) + 10 * sc;
    }
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "an open row is a cache: hit it and skip ACT", GREEN, c.during(2, 0.3, 1.0));
}
