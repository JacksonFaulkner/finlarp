//! Section 9: chokepoints and risks, one per beat: the memory wall (compute outruns
//! bandwidth), pins (every extra pin costs package area and power), and HBM's
//! packaging (it needs an interposer beside the processor; see HBM STACK).

use super::super::push_box;
use super::super::stage::{self, label, particles, spotlight, text, Clock, Shot, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1100.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i), 60.0, 0.0], dist: 1150.0, yaw: 0.25, pitch: 0.45 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    // 0: a wide processor fed through a narrow pipe
    push_box(m, [x(0) - 320.0, -16.0, -200.0], [x(0) + 320.0, 0.0, 200.0], STEEL, NO_GLOW);
    push_box(m, [x(0) - 280.0, 0.0, -150.0], [x(0) - 60.0, 160.0, 150.0], stage::mix(QUIET, PINK, 0.3 + 0.6 * k[0]), NO_GLOW);
    crate::push_tube(m, [x(0) - 60.0, 60.0, 0.0], [x(0) + 200.0, 60.0, 0.0], 14.0, 14, stage::mix(QUIET, CYAN, 0.3 + 0.6 * k[0]), NO_GLOW, false);
    push_box(m, [x(0) + 200.0, 0.0, -80.0], [x(0) + 280.0, 120.0, 80.0], stage::mix(QUIET, GREEN, 0.3 + 0.6 * k[0]), NO_GLOW);
    // 1: a package edge crowded with pins
    push_box(m, [x(1) - 320.0, -16.0, -200.0], [x(1) + 320.0, 0.0, 200.0], STEEL, NO_GLOW);
    push_box(m, [x(1) - 160.0, 0.0, -160.0], [x(1) + 160.0, 40.0, 160.0], stage::mix(QUIET, PURPLE, 0.3 + 0.6 * k[1]), NO_GLOW);
    for i in 0..14 {
        for j in 0..14 {
            let (px, pz) = (x(1) - 145.0 + i as f64 * 22.3, -145.0 + j as f64 * 22.3);
            push_box(m, [px - 5.0, 40.0, pz - 5.0], [px + 5.0, 48.0, pz + 5.0], stage::mix(QUIET, ORANGE, 0.3 + 0.6 * k[1]), NO_GLOW);
        }
    }
    // 2: an HBM stack on an interposer beside the processor
    push_box(m, [x(2) - 320.0, -16.0, -200.0], [x(2) + 320.0, 0.0, 200.0], STEEL, NO_GLOW);
    push_box(m, [x(2) - 250.0, 0.0, -130.0], [x(2) + 250.0, 10.0, 130.0], stage::mix(QUIET, METAL, 0.3 + 0.6 * k[2]), NO_GLOW);
    push_box(m, [x(2) - 220.0, 10.0, -100.0], [x(2) + 20.0, 50.0, 100.0], stage::mix(QUIET, PURPLE, 0.3 + 0.6 * k[2]), NO_GLOW);
    for d in 0..8 {
        let y = 12.0 + 12.0 * d as f64;
        push_box(m, [x(2) + 60.0, y, -70.0], [x(2) + 200.0, y + 9.0, 70.0], stage::mix(QUIET, ORANGE, 0.3 + 0.6 * k[2]), NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    particles(cv, cam, &[[x(0) + 200.0, 60.0, 0.0], [x(0) - 60.0, 60.0, 0.0]], 5, c.u() * 0.8, 9.0, CYAN, k[0]);
    label(cv, cam, [x(0) - 60.0, 160.0, 150.0], (0.02, -0.06), "compute outruns memory", PINK, 0.4 + 0.6 * k[0]);
    label(cv, cam, [x(1) + 160.0, 0.0, 160.0], (0.02, 0.06), "every pin costs area and power", ORANGE, 0.4 + 0.6 * k[1]);
    label(cv, cam, [x(2) + 200.0, 108.0, 70.0], (0.02, -0.05), "HBM needs an interposer (HBM STACK)", ORANGE, 0.4 + 0.6 * k[2]);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "chokepoints and risks", TEXT, 0.95);
}
