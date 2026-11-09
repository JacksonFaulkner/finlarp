//! Section 9: chokepoints and risks, one per beat, the camera visiting each:
//! a single EUV maker with no second source, random (stochastic) defects in fine
//! lines as photon counts fall, and export controls fencing off advanced scanners.

use super::super::push_box;
use super::super::stage::{self, glass_box, label, particles, spotlight, text, Clock, Shot, GLASS, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT, YELLOW};
use super::rig::FILM;
use crate::{Cam, Canvas, Tri};

const SPACE: f64 = 620.0;

fn x(i: usize) -> f64 {
    (i as f64 - 1.0) * SPACE
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys: [Shot; 3] = std::array::from_fn(|i| Shot { target: [x(i) * 0.8, 120.0, 0.0], dist: 1250.0, yaw: 0.25, pitch: 0.45 });
    stage::shot_at(&keys, c.beat, c.local)
}

/// Spots on the line grid that fail: (line, z) pairs.
const DEFECTS: [(i32, f64); 7] = [(-3, -90.0), (-1, 60.0), (0, -140.0), (1, 20.0), (2, 120.0), (3, -40.0), (-2, 150.0)];

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    // 0: one maker, empty plinths beside it
    let k0 = spotlight(c, 0, 3);
    let p0 = x(0);
    push_box(m, [p0 - 260.0, -20.0, -150.0], [p0 + 260.0, 0.0, 150.0], STEEL, NO_GLOW);
    push_box(m, [p0 - 60.0, 0.0, -60.0], [p0 + 60.0, 300.0, 60.0], stage::mix(QUIET, YELLOW, 0.3 + 0.6 * k0), stage::scaled(YELLOW, 0.25 * k0));

    // 1: fine lines with random failures
    let k1 = spotlight(c, 1, 3);
    let p1 = x(1);
    push_box(m, [p1 - 240.0, -20.0, -200.0], [p1 + 240.0, 0.0, 200.0], STEEL, NO_GLOW);
    for i in -4..=4 {
        let lx = p1 + i as f64 * 52.0;
        push_box(m, [lx - 12.0, 0.0, -180.0], [lx + 12.0, 10.0, 180.0], stage::mix(QUIET, FILM, 0.4 + 0.6 * k1), NO_GLOW);
    }
    let show = c.during(1, 0.25, 1.0);
    for (n, (i, z)) in DEFECTS.iter().enumerate() {
        let k = show * stage::smooth_step(n as f64 / 7.0 * 0.5, n as f64 / 7.0 * 0.5 + 0.1, c.local);
        if k > 0.01 {
            let lx = p1 + *i as f64 * 52.0 + if n % 2 == 0 { 0.0 } else { 26.0 };
            push_box(m, [lx - 14.0 * k, 10.0, z - 14.0 * k], [lx + 14.0 * k, 16.0, z + 14.0 * k], PINK, stage::scaled(PINK, 0.4 * k));
        }
    }

    // 2: a scanner behind a fence
    let k2 = spotlight(c, 2, 3);
    let p2 = x(2);
    push_box(m, [p2 - 260.0, -20.0, -200.0], [p2 + 260.0, 0.0, 200.0], STEEL, NO_GLOW);
    push_box(m, [p2 - 60.0, 0.0, -110.0], [p2 + 100.0, 220.0, 10.0], stage::mix(QUIET, [0.8, 0.82, 0.88], 0.3 + 0.6 * k2), NO_GLOW);
    let fence = stage::mix(QUIET, ORANGE, 0.3 + 0.7 * k2);
    for j in 0..9 {
        let fz = -180.0 + j as f64 * 45.0;
        push_box(m, [p2 - 160.0, 0.0, fz - 5.0], [p2 - 150.0, 180.0, fz + 5.0], fence, stage::scaled(ORANGE, 0.15 * k2));
    }
    push_box(m, [p2 - 162.0, 160.0, -185.0], [p2 - 148.0, 172.0, 185.0], fence, NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let k0 = spotlight(c, 0, 3);
    let p0 = x(0);
    for dx in [-180.0, 180.0] {
        glass_box(cv, cam, [p0 + dx - 60.0, 0.0, -60.0], [p0 + dx + 60.0, 300.0, 60.0], GLASS, (0.15 + 0.3 * k0) as f32);
    }
    label(cv, cam, [p0 + 60.0, 300.0, 60.0], (0.03, -0.06), "one EUV scanner maker", YELLOW, 0.4 + 0.6 * k0);
    label(cv, cam, [p0 + 240.0, 150.0, 60.0], (0.03, 0.05), "no second source", GLASS, k0);

    let k1 = spotlight(c, 1, 3);
    let p1 = x(1);
    // sparse photons: at low dose few arrive, and where few land the line can fail
    for i in 0..7 {
        let lx = p1 + (i as f64 - 3.0) * 60.0 + 13.0;
        let path = [[lx, 380.0, ((i * 53) % 9) as f64 * 30.0 - 120.0], [lx, 12.0, ((i * 53) % 9) as f64 * 30.0 - 120.0]];
        particles(cv, cam, &path, 2, c.u() * 1.1 + i as f64 * 0.13, 7.0, YELLOW, k1);
    }
    label(cv, cam, [p1 + 240.0, 10.0, 200.0], (0.02, 0.07), "random breaks and bridges", PINK, 0.4 + 0.6 * k1);

    let k2 = spotlight(c, 2, 3);
    let p2 = x(2);
    label(cv, cam, [p2 - 155.0, 180.0, 185.0], (-0.12, -0.06), "export controls", ORANGE, 0.4 + 0.6 * k2);
    label(cv, cam, [p2 + 100.0, 220.0, 10.0], (0.04, -0.05), "advanced scanner", TEXT, k2);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "chokepoints and risks", TEXT, 0.95);
}
