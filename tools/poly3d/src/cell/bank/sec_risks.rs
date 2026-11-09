//! Section 9: chokepoints and risks, one per beat: interference (two cores' requests
//! colliding in one bank), the tFAW cap on activations (power), and refresh growing
//! with density (more rows to refresh per window).

use super::super::push_box;
use super::super::stage::{self, label, particles, spotlight, text, Clock, Shot, CYAN, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1100.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i), 40.0, 0.0], dist: 1200.0, yaw: 0.25, pitch: 0.55 });
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    // 0: one bank, two cores
    push_box(m, [x(0) - 300.0, -16.0, -250.0], [x(0) + 300.0, 0.0, 250.0], STEEL, NO_GLOW);
    push_box(m, [x(0) - 80.0, 0.0, -60.0], [x(0) + 80.0, 30.0, 60.0], stage::mix(QUIET, PINK, 0.3 + 0.6 * k[0]), NO_GLOW);
    for (dx, col) in [(-250.0, ORANGE), (250.0, CYAN)] {
        push_box(m, [x(0) + dx - 40.0, 0.0, -200.0], [x(0) + dx + 40.0, 50.0, -120.0], stage::mix(QUIET, col, 0.3 + 0.6 * k[0]), NO_GLOW);
    }
    // 1: activates against the window: four bars and a lid
    push_box(m, [x(1) - 300.0, -16.0, -200.0], [x(1) + 300.0, 0.0, 200.0], STEEL, NO_GLOW);
    for t in 0..6 {
        let bx = x(1) - 250.0 + t as f64 * 90.0;
        let col = if t < 4 { ORANGE } else { QUIET };
        push_box(m, [bx, 0.0, -30.0], [bx + 50.0, 120.0, 30.0], stage::mix(QUIET, col, 0.3 + 0.6 * k[1]), NO_GLOW);
    }
    push_box(m, [x(1) - 260.0, 140.0, -40.0], [x(1) + 100.0, 150.0, 40.0], stage::mix(QUIET, PINK, 0.3 + 0.7 * k[1]), NO_GLOW);
    // 2: rows to refresh grow with density: three stacks
    push_box(m, [x(2) - 300.0, -16.0, -200.0], [x(2) + 300.0, 0.0, 200.0], STEEL, NO_GLOW);
    for (j, hgt) in [60.0, 120.0, 240.0].iter().enumerate() {
        let bx = x(2) - 180.0 + j as f64 * 150.0;
        push_box(m, [bx - 50.0, 0.0, -50.0], [bx + 50.0, *hgt, 50.0], stage::mix(QUIET, CYAN, 0.3 + 0.6 * k[2]), stage::scaled(CYAN, 0.1 * k[2]));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k: [f64; 3] = std::array::from_fn(|i| spotlight(c, i, 3));
    for (dx, col, ph) in [(-250.0, ORANGE, 0.0), (250.0, CYAN, 0.5)] {
        particles(cv, cam, &[[x(0) + dx, 50.0, -160.0], [x(0), 30.0, 0.0]], 6, c.u() * 1.4 + ph, 9.0, col, k[0]);
    }
    label(cv, cam, [x(0) + 80.0, 30.0, 60.0], (0.03, 0.06), "two cores, one bank: rows fight", PINK, 0.4 + 0.6 * k[0]);
    label(cv, cam, [x(1) + 100.0, 150.0, 40.0], (0.03, -0.06), "tFAW: 4 ACTs, then wait", PINK, 0.4 + 0.6 * k[1]);
    label(cv, cam, [x(2) + 170.0, 240.0, 50.0], (0.03, -0.05), "denser chips: more rows to refresh", CYAN, 0.4 + 0.6 * k[2]);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "chokepoints and risks", TEXT, 0.95);
}
