//! Section 6: by the numbers, three stops the camera visits: a 512 x 512 array, one
//! DDR4 row spread across sixteen of them (1 KB on a x8 chip), and the DDR4-3200
//! timings as bars.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GLASS, GREEN, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1500.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [x(0), 0.0, 0.0], dist: 1050.0, yaw: 0.25, pitch: 0.85 },
        Shot { target: [x(1), 0.0, 0.0], dist: 1300.0, yaw: 0.20, pitch: 0.75 },
        Shot { target: [x(2), 120.0, 0.0], dist: 1100.0, yaw: 0.30, pitch: 0.30 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// DDR4-3200 22-22-22 timings in ns: name, value.
const TIMES: [(&str, f64); 4] = [("tRCD", 13.75), ("tCL", 13.75), ("tRP", 13.75), ("tRAS", 32.5)];

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    // 1: one array, 512 units square
    let k0 = spotlight(c, 0, 3);
    push_box(m, [x(0) - 270.0, -16.0, -270.0], [x(0) + 270.0, 0.0, 270.0], stage::mix(QUIET, ORANGE, 0.25 + 0.5 * k0), NO_GLOW);
    // 2: sixteen arrays in a line, one row lit across them all
    let k1 = spotlight(c, 1, 3);
    for i in 0..16 {
        let ax = x(1) + (i as f64 - 7.5) * 48.0;
        push_box(m, [ax - 22.0, 0.0, -160.0], [ax + 22.0, 10.0, 160.0], stage::mix(QUIET, ORANGE, 0.3 + 0.3 * k1), NO_GLOW);
    }
    push_box(m, [x(1) - 400.0, 10.0, 20.0], [x(1) + 400.0, 16.0, 30.0], stage::mix(QUIET, ORANGE, k1), stage::scaled(ORANGE, 0.4 * k1));
    push_box(m, [x(1) - 420.0, -16.0, -200.0], [x(1) + 420.0, 0.0, 200.0], STEEL, NO_GLOW);
    // 3: timing bars, 12 units per ns
    let k2 = spotlight(c, 2, 3);
    push_box(m, [x(2) - 260.0, -16.0, -120.0], [x(2) + 260.0, 0.0, 120.0], STEEL, NO_GLOW);
    for (i, (_, ns)) in TIMES.iter().enumerate() {
        let bx = x(2) + (i as f64 - 1.5) * 120.0;
        let col = if i == 3 { PINK } else { GREEN };
        push_box(m, [bx - 35.0, 0.0, -35.0], [bx + 35.0, ns * 12.0, 35.0], stage::mix(QUIET, col, 0.3 + 0.7 * k2), stage::scaled(col, 0.15 * k2));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k0 = spotlight(c, 0, 3);
    for k in 0..=64 {
        let t = -256.0 + k as f64 * 8.0;
        let a = (0.12 + 0.2 * k0) as f32;
        cv.line(cam, [x(0) + t, 1.0, -256.0], [x(0) + t, 1.0, 256.0], GLASS, a);
        cv.line(cam, [x(0) - 256.0, 1.0, t], [x(0) + 256.0, 1.0, t], GLASS, a);
    }
    label(cv, cam, [x(0) + 270.0, 0.0, 270.0], (0.02, 0.06), "512 x 512 = 262,144 cells", ORANGE, 0.4 + 0.6 * k0);
    let k1 = spotlight(c, 1, 3);
    label(cv, cam, [x(1) + 400.0, 16.0, 30.0], (0.03, -0.07), "one row: 8 Kb = 1 KB (x8 DDR4)", ORANGE, 0.4 + 0.6 * k1);
    label(cv, cam, [x(1) + 380.0, 10.0, 160.0], (0.02, 0.07), "spread over 16 arrays of 512", TEXT, k1);
    let k2 = spotlight(c, 2, 3);
    for (i, (name, ns)) in TIMES.iter().enumerate() {
        let bx = x(2) + (i as f64 - 1.5) * 120.0;
        label(cv, cam, [bx, ns * 12.0, 35.0], (-0.04, -0.06), &format!("{name} {ns} ns"), CYAN, 0.3 + 0.7 * k2);
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "DDR4-3200 22-22-22 (JEDEC grade)", TEXT, k2);
}
