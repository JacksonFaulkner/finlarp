//! Zoom b: the base logic die. Under the DRAM dies (drawn as glass here) sits a logic
//! die: the TSV field in the middle where the stack's vias land, the PHY along the edge
//! that drives the wide bus across the interposer, and test and repair logic. For
//! HBM4 the base die moves to a foundry logic process.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, GREEN, NO_GLOW, PURPLE, STEEL, TEXT, YELLOW};
use super::rig::{COPPER, LOGIC};
use crate::{Cam, Canvas, Tri};

const HX: f64 = 220.0;
const HZ: f64 = 170.0;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 60.0, 0.0], dist: 1100.0, yaw: 0.40, pitch: 0.50 },
        Shot { target: [160.0, 30.0, 0.0], dist: 1000.0, yaw: 0.80, pitch: 0.45 },
        Shot { target: [0.0, 30.0, 0.0], dist: 1000.0, yaw: 0.25, pitch: 0.75 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let lift = c.ramp(0, 0.2, 0.7) * (1.0 - c.ramp(2, 0.85, 0.99));
    push_box(m, [-HX - 200.0, -20.0, -HZ - 60.0], [HX + 380.0, 0.0, HZ + 60.0], STEEL, NO_GLOW);
    push_box(m, [-HX, 0.0, -HZ], [HX, 24.0, HZ], stage::scaled(LOGIC, 0.7), NO_GLOW);
    // TSV landing field
    for i in 0..8 {
        for j in 0..6 {
            let (x, z) = (-105.0 + i as f64 * 30.0, -75.0 + j as f64 * 30.0);
            push_box(m, [x - 5.0, 24.0, z - 5.0], [x + 5.0, 28.0 + 6.0 * lift, z + 5.0], COPPER, stage::scaled(COPPER, 0.15));
        }
    }
    // PHY along the edge facing the GPU, test logic on the far side
    push_box(m, [HX - 50.0, 24.0, -HZ + 20.0], [HX - 10.0, 34.0, HZ - 20.0], CYAN, stage::scaled(CYAN, 0.15));
    push_box(m, [-HX + 10.0, 24.0, -HZ + 20.0], [-HX + 60.0, 32.0, -20.0], GREEN, stage::scaled(GREEN, 0.1));
    // the GPU beyond the interposer gap
    push_box(m, [HX + 140.0, 0.0, -HZ], [HX + 360.0, 50.0, HZ], stage::mix(STEEL, PURPLE, 0.5), NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let lift = c.ramp(0, 0.2, 0.7) * (1.0 - c.ramp(2, 0.85, 0.99));
    // the DRAM dies above, as glass, lifted to show the base die
    for d in 0..8 {
        let y = 30.0 + 60.0 * lift + d as f64 * 14.0;
        stage::glass_box(cv, cam, [-HX, y, -HZ], [HX, y + 10.0, HZ], GLASS, 0.25);
    }
    let phy = c.during(1, 0.05, 1.0) + c.during(2, 0.0, 0.95);
    for k in 0..10 {
        let z = -HZ + 30.0 + k as f64 * 30.0;
        particles(cv, cam, &[[HX - 10.0, 20.0, z], [HX + 140.0, 20.0, z * 0.9]], 4, c.u() * 2.0 + k as f64 * 0.1, 5.0, CYAN, phy.min(1.0));
    }
    label(cv, cam, [105.0, 28.0, 75.0], (0.04, 0.08), "TSV landing field", YELLOW, 0.85);
    label(cv, cam, [HX - 10.0, 34.0, -HZ + 20.0], (0.04, -0.07), "PHY: drives the bus to the GPU", CYAN, 0.85);
    label(cv, cam, [-HX + 60.0, 32.0, -HZ + 20.0], (-0.12, -0.07), "test and repair logic", GREEN, 0.8);
    label(cv, cam, [HX + 360.0, 50.0, -HZ], (0.02, -0.06), "GPU", PURPLE, 0.8);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "the base die: logic under the DRAM", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "HBM4: base die on a foundry logic process", GLASS, c.during(2, 0.1, 0.95));
}
