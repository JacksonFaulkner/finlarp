//! Section 5: depth of focus. A cone of light converging on the wafer, and the band
//! around the focus that stays sharp (DOF ~ wavelength / NA^2). A wider cone (higher
//! NA) makes the band shorter, and a wafer that is not flat drifts out of it.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, NO_GLOW, ORANGE, PINK, PURPLE, STEEL, TEXT};
use super::rig::{LIGHT, RESIST};
use crate::{Cam, Canvas, Tri};

const LENS_Y: f64 = 420.0;
const WL: f64 = 13.5;
/// world units per nm of depth
const NM: f64 = 1.1;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 160.0, 0.0], dist: 1400.0, yaw: 0.40, pitch: 0.12 },
    Shot { target: [0.0, 140.0, 0.0], dist: 1300.0, yaw: 0.60, pitch: 0.14 },
    Shot { target: [0.0, 40.0, 0.0], dist: 1050.0, yaw: 0.25, pitch: 0.22 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn na(c: &Clock) -> f64 {
    0.33 + 0.22 * c.ramp(1, 0.1, 0.6) - 0.22 * c.ramp(2, 0.85, 0.99)
}

/// Half the sharp band, in world units.
fn half_dof(c: &Clock) -> f64 {
    WL / (na(c) * na(c)) * NM * 0.5
}

/// The wafer's bumps: there in beat 2.
fn bumps(c: &Clock) -> f64 {
    c.during(2, 0.05, 0.95)
}

fn surface(x: f64, b: f64) -> f64 {
    b * 55.0 * (x / 90.0).sin()
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let b = bumps(c);
    let r = LENS_Y * na(c).asin().tan();
    crate::push_tube(m, [0.0, LENS_Y, 0.0], [0.0, LENS_Y + 24.0, 0.0], r, 64, stage::mix(STEEL, CYAN, 0.55), stage::scaled(CYAN, 0.1), true);
    // the wafer surface in slices, raised and lowered by its bumps
    let n = 24;
    for i in 0..n {
        let x0 = -360.0 + 720.0 * i as f64 / n as f64;
        let x1 = x0 + 720.0 / n as f64;
        let y = surface((x0 + x1) / 2.0, b);
        let sharp = (y.abs() <= half_dof(c)) as i32 as f64;
        let col = stage::mix(stage::mix(RESIST, PINK, 0.4), stage::mix(RESIST, ORANGE, 0.7), (1.0 - sharp) * b);
        push_box(m, [x0, -80.0, -200.0], [x1, y, 200.0], col, NO_GLOW);
    }
    push_box(m, [-380.0, -110.0, -220.0], [380.0, -80.0, 220.0], STEEL, NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = LENS_Y * na(c).asin().tan();
    for k in 0..16 {
        let th = std::f64::consts::TAU * k as f64 / 16.0;
        let rim = [r * th.cos(), LENS_Y, r * th.sin()];
        cv.line(cam, rim, [0.0, 0.0, 0.0], LIGHT, 0.3);
        if k % 2 == 0 {
            particles(cv, cam, &[rim, [0.0, 0.0, 0.0]], 4, c.u() * 1.5 + k as f64 * 0.07, 6.0, LIGHT, 0.85);
        }
    }
    let half = half_dof(c);
    // the sharp band: a slab across the whole wafer, so the bumps can be seen leaving it
    for y in [-half, half] {
        stage::glass_box(cv, cam, [-360.0, y, -200.0], [360.0, y, 200.0], PURPLE, 0.75);
    }
    stage::glass_cyl(cv, cam, [0.0, -half, 0.0], 50.0, 2.0 * half, PURPLE, 0.6);
    label(cv, cam, [360.0, half, 200.0], (0.03, -0.06), &format!("in focus: {:.0} nm band", 0.5 * WL / (na(c) * na(c))), PURPLE, 0.95);
    label(cv, cam, [r * 0.5, LENS_Y * 0.5, 0.0], (0.10, 0.0), &format!("NA {:.2}", na(c)), LIGHT, 1.0);
    let b = bumps(c);
    label(cv, cam, [141.0, surface(141.0, b), 200.0], (-0.10, 0.10), "bump leaves the band: blurred", ORANGE, b);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "DOF = k2 x wavelength / NA^2", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "illustrative: k2 = 0.5, EUV 13.5 nm", CYAN, 0.8);
}
