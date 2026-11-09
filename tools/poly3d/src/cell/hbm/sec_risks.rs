//! Section 9: chokepoints and risks, one per beat: packaging capacity (finished GPUs
//! queue for interposers), stack yield (one bad die spoils the stack, so yield falls
//! with height: illustrative 99% per die), and heat in tall stacks.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use super::rig::DRAM;
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1000.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i), 80.0, 0.0], dist: 1100.0, yaw: 0.25, pitch: 0.40 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    // 0: a queue of GPU dies waiting at one packaging line
    push_box(m, [x(0) - 340.0, -16.0, -200.0], [x(0) + 340.0, 0.0, 200.0], STEEL, NO_GLOW);
    push_box(m, [x(0) + 150.0, 0.0, -90.0], [x(0) + 300.0, 120.0, 90.0], stage::mix(QUIET, CYAN, 0.3 + 0.6 * k[0]), NO_GLOW);
    for i in 0..6 {
        let gx = x(0) + 90.0 - i as f64 * 75.0;
        push_box(m, [gx - 28.0, 0.0, -28.0], [gx + 28.0, 22.0, 28.0], stage::mix(QUIET, PURPLE, 0.3 + 0.6 * k[0]), NO_GLOW);
    }
    // 1: yield bars for 8, 12 and 16 dies at 99% per die
    push_box(m, [x(1) - 300.0, -16.0, -160.0], [x(1) + 300.0, 0.0, 160.0], STEEL, NO_GLOW);
    for (j, n) in [8, 12, 16].iter().enumerate() {
        let y = 0.99f64.powi(*n);
        let bx = x(1) - 150.0 + j as f64 * 150.0;
        push_box(m, [bx - 45.0, 0.0, -45.0], [bx + 45.0, 260.0 * y, 45.0], stage::mix(QUIET, ORANGE, 0.3 + 0.6 * k[1]), NO_GLOW);
    }
    // 2: a tall stack glowing hot at the bottom
    push_box(m, [x(2) - 300.0, -16.0, -160.0], [x(2) + 300.0, 0.0, 160.0], STEEL, NO_GLOW);
    for d in 0..16 {
        let y = 10.0 + d as f64 * 13.0;
        let hot = (1.0 - d as f64 / 16.0) * k[2];
        push_box(m, [x(2) - 80.0, y, -60.0], [x(2) + 80.0, y + 10.0, 60.0], stage::mix(stage::mix(QUIET, DRAM, 0.4 + 0.5 * k[2]), [1.0, 0.35, 0.2], 0.7 * hot), stage::scaled([1.0, 0.35, 0.2], 0.3 * hot));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    label(cv, cam, [x(0) + 300.0, 120.0, 90.0], (0.02, -0.06), "packaging capacity: GPUs wait", CYAN, 0.4 + 0.6 * k[0]);
    for (j, n) in [8, 12, 16].iter().enumerate() {
        let y = 0.99f64.powi(*n);
        let bx = x(1) - 150.0 + j as f64 * 150.0;
        label(cv, cam, [bx, 260.0 * y, 45.0], (-0.04, -0.06), &format!("{n}-high {:.0}%", 100.0 * y), ORANGE, 0.4 + 0.6 * k[1]);
    }
    label(cv, cam, [x(1) + 195.0, 0.0, 45.0], (0.02, 0.07), "one bad die spoils the stack (99%/die, illustrative)", TEXT, k[1]);
    label(cv, cam, [x(2) + 80.0, 30.0, 60.0], (0.03, 0.05), "heat trapped low in tall stacks", PINK, 0.4 + 0.6 * k[2]);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "chokepoints and risks", TEXT, 0.95);
}
