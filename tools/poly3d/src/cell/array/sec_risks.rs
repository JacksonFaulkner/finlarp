//! Section 9: chokepoints and risks, one per beat, the camera visiting each: row
//! conflicts cost three times a hit, RowHammer (hammering one row drains its
//! neighbours), and the periphery (decoders and sense amps) taking area from cells.

use super::super::push_box;
use super::super::stage::{self, label, spotlight, text, Clock, Shot, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 1150.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i) * 0.8, 60.0, 0.0], dist: 1300.0, yaw: 0.25, pitch: 0.50 });
    stage::shot_at(&keys, c.beat, c.local)
}

const ROWS: usize = 5;
const AGG: usize = 2;

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    // 0: hit vs conflict bars, 10 units per ns
    let k0 = spotlight(c, 0, 3);
    push_box(m, [x(0) - 200.0, -16.0, -150.0], [x(0) + 200.0, 0.0, 150.0], STEEL, NO_GLOW);
    for (dx, ns, col) in [(-70.0, 13.75, GREEN), (70.0, 41.25, PINK)] {
        push_box(m, [x(0) + dx - 40.0, 0.0, -40.0], [x(0) + dx + 40.0, ns * 10.0, 40.0], stage::mix(QUIET, col, 0.3 + 0.7 * k0), stage::scaled(col, 0.15 * k0));
    }
    // 1: RowHammer: the aggressor row flickers, its neighbours lose charge
    let k1 = spotlight(c, 1, 3);
    let p1 = x(1);
    push_box(m, [p1 - 260.0, -16.0, -200.0], [p1 + 260.0, 0.0, 200.0], STEEL, NO_GLOW);
    let flick = 0.5 + 0.5 * (c.u() * 40.0).sin();
    let drain = c.during(1, 0.1, 1.0);
    for r in 0..ROWS {
        let z = (r as f64 - 2.0) * 70.0;
        let agg = r == AGG;
        let near = r + 1 == AGG || r == AGG + 1;
        let w = if agg { k1 * flick } else { 0.0 };
        crate::push_tube(m, [p1 - 240.0, 50.0, z - 18.0], [p1 + 240.0, 50.0, z - 18.0], 5.0 + 4.0 * w, 10, stage::mix(METAL, ORANGE, w), stage::scaled(ORANGE, 0.4 * w), false);
        for i in 0..8 {
            let cx = p1 + (i as f64 - 3.5) * 60.0;
            let mut col = ORANGE;
            if near {
                col = stage::mix(ORANGE, QUIET, 0.7 * drain);
                if i == 5 {
                    col = stage::mix(col, PINK, drain);
                }
            }
            crate::push_tube(m, [cx, 0.0, z], [cx, 40.0, z], 12.0, 10, stage::mix(QUIET, col, 0.3 + 0.7 * k1), NO_GLOW, true);
        }
    }
    // 2: a mat with its periphery: cells in the middle, stripes and drivers around
    let k2 = spotlight(c, 2, 3);
    let p2 = x(2);
    push_box(m, [p2 - 260.0, -16.0, -220.0], [p2 + 260.0, 0.0, 220.0], STEEL, NO_GLOW);
    push_box(m, [p2 - 150.0, 0.0, -130.0], [p2 + 190.0, 26.0, 150.0], stage::mix(QUIET, ORANGE, 0.3 + 0.6 * k2), NO_GLOW);
    for dz in [-170.0, 190.0] {
        push_box(m, [p2 - 150.0, 0.0, dz - 30.0], [p2 + 190.0, 22.0, dz + 10.0], stage::mix(QUIET, PURPLE, 0.3 + 0.6 * k2), NO_GLOW);
    }
    push_box(m, [p2 - 220.0, 0.0, -130.0], [p2 - 170.0, 22.0, 150.0], stage::mix(QUIET, CYAN, 0.3 + 0.6 * k2), NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k0 = spotlight(c, 0, 3);
    label(cv, cam, [x(0) - 70.0, 137.5, 40.0], (-0.10, -0.05), "hit 13.75 ns", GREEN, 0.4 + 0.6 * k0);
    label(cv, cam, [x(0) + 70.0, 412.5, 40.0], (0.04, -0.03), "conflict 41.25 ns", PINK, 0.4 + 0.6 * k0);
    let k1 = spotlight(c, 1, 3);
    label(cv, cam, [x(1) + 240.0, 50.0, -18.0], (0.03, -0.06), "aggressor row, opened again and again", ORANGE, k1);
    label(cv, cam, [x(1) + (5.0 - 3.5) * 60.0, 40.0, 70.0], (0.03, 0.08), "neighbour loses charge: a bit flips", PINK, k1 * c.during(1, 0.3, 1.0));
    let k2 = spotlight(c, 2, 3);
    label(cv, cam, [x(2) + 190.0, 26.0, 0.0], (0.03, -0.05), "cells", ORANGE, 0.4 + 0.6 * k2);
    label(cv, cam, [x(2) + 190.0, 22.0, 190.0], (0.03, 0.06), "sense amp stripes", PURPLE, 0.4 + 0.6 * k2);
    label(cv, cam, [x(2) - 220.0, 22.0, -130.0], (-0.12, -0.06), "decoders", CYAN, 0.4 + 0.6 * k2);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "chokepoints and risks", TEXT, 0.95);
}
