//! Timelines in 3D: lanes of command blocks laid along a time axis, each block a box
//! that grows in as the scene's clock passes its start. Used by the timing scenes.

use super::super::push_box;
use super::super::stage::{self, label, Clock, Shot, GLASS, NO_GLOW, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

/// world units per ns
pub(in crate::cell) const NS: f64 = 32.0;
pub(in crate::cell) const X0: f64 = -380.0;
const LANE: f64 = 150.0;

/// The camera for a timeline: looking down over the middle of the span, easing a
/// little between beats so the picture still moves.
pub(in crate::cell) fn shot(c: &Clock, span: f64, lanes: usize) -> Shot {
    let cx = X0 + span * NS * 0.45;
    let d = 760.0 + 120.0 * lanes as f64 + 12.0 * span;
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot {
        target: [cx - 30.0 + 30.0 * i as f64, 10.0, 30.0],
        dist: d,
        yaw: 0.10 + 0.06 * i as f64,
        pitch: 1.05 - 0.04 * i as f64,
    });
    stage::shot_at(&keys, c.beat, c.local)
}

/// One block: lane, start (ns), length (ns), colour, label, and the beat it belongs to.
#[derive(Clone, Copy)]
pub(in crate::cell) struct Block {
    pub lane: usize,
    pub t0: f64,
    pub len: f64,
    pub col: Col,
    pub name: &'static str,
    pub beat: usize,
}

pub(in crate::cell) fn lane_z(lane: usize, lanes: usize) -> f64 {
    (lane as f64 - (lanes as f64 - 1.0) / 2.0) * LANE
}

/// How far block `b` has grown: it comes in over its beat in time order, and every
/// block clears at the end of the loop (`last` is the final beat).
pub(in crate::cell) fn grown(c: &Clock, b: &Block, span: f64, last: usize) -> f64 {
    let a = 0.05 + 0.75 * (b.t0 / span).clamp(0.0, 1.0);
    c.ramp(b.beat, a, (a + 0.15).min(0.98)) * (1.0 - c.ramp(last, 0.88, 0.99))
}

pub(in crate::cell) fn solids(c: &Clock, blocks: &[Block], lanes: usize, span: f64, last: usize, m: &mut Vec<Tri>) {
    push_box(m, [X0 - 60.0, -20.0, lane_z(0, lanes) - 80.0], [X0 + span * NS + 80.0, 0.0, lane_z(lanes - 1, lanes) + 80.0], STEEL, NO_GLOW);
    for b in blocks {
        let g = grown(c, b, span, last);
        if g < 0.01 {
            continue;
        }
        let z = lane_z(b.lane, lanes);
        let x0 = X0 + b.t0 * NS;
        let x1 = x0 + b.len * NS * g;
        push_box(m, [x0 + 1.5, 0.0, z - 34.0], [x1.max(x0 + 2.0) - 1.5, 30.0, z + 34.0], b.col, stage::scaled(b.col, 0.15));
    }
}

/// Ticks every `step` ns, lane names, and each block's name once it is in.
pub(in crate::cell) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock, blocks: &[Block], lanes: &[&str], span: f64, step: f64, last: usize) {
    let n = lanes.len();
    let mut t = 0.0;
    while t <= span + 1e-6 {
        let x = X0 + t * NS;
        cv.line(cam, [x, 1.0, lane_z(0, n) - 60.0], [x, 1.0, lane_z(n - 1, n) + 60.0], GLASS, 0.3);
        t += step;
    }
    for (i, name) in lanes.iter().enumerate() {
        label(cv, cam, [X0 - 30.0, 30.0, lane_z(i, n)], (-0.22, -0.01), name, TEXT, 0.85);
    }
    for b in blocks.iter().filter(|b| !b.name.is_empty()) {
        let g = grown(c, b, span, last);
        label(cv, cam, [X0 + (b.t0 + b.len * 0.5) * NS, 30.0, lane_z(b.lane, n) - 34.0], (-0.02, -0.06), b.name, b.col, g);
    }
}
