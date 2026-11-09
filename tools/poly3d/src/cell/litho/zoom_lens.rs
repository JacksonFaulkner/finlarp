//! Zoom b: the lens and its numerical aperture. Light converges from the last lens
//! element to a focus on the wafer. NA is the sine of the cone's half-angle: at NA
//! 0.33 the lines printed below are wide, at 0.55 they are finer. The wider cone
//! costs depth: the zone that stays sharp shrinks with NA squared.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, NO_GLOW, PINK, PURPLE, STEEL, TEXT};
use super::rig::{FILM, LIGHT, RESIST};
use crate::{Cam, Canvas, Tri};

const LENS_Y: f64 = 330.0;
const WAVELENGTH: f64 = 13.5;
const K1: f64 = 0.4;
/// world units per nm, for the printed lines and the focus zone
const NM: f64 = 5.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 150.0, 0.0], dist: 1350.0, yaw: 0.45, pitch: 0.18 },
    Shot { target: [0.0, 140.0, 0.0], dist: 1350.0, yaw: 0.65, pitch: 0.24 },
    Shot { target: [0.0, 60.0, 0.0], dist: 1000.0, yaw: 0.35, pitch: 0.10 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// NA: 0.33, opened to 0.55 in beat 1, back to 0.33 by the end of beat 2.
fn na(c: &Clock) -> f64 {
    0.33 + 0.22 * c.ramp(1, 0.1, 0.6) - 0.22 * c.ramp(2, 0.62, 0.95)
}

fn cd(c: &Clock) -> f64 {
    K1 * WAVELENGTH / na(c)
}

fn lens_r(c: &Clock) -> f64 {
    let th = na(c).asin();
    LENS_Y * th.tan()
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let r = lens_r(c);
    crate::push_tube(m, [0.0, LENS_Y, 0.0], [0.0, LENS_Y + 26.0, 0.0], r, 64, stage::mix(STEEL, CYAN, 0.55), stage::scaled(CYAN, 0.1), true);
    // wafer: film and resist, with lines at the width this NA can print
    push_box(m, [-340.0, -30.0, -220.0], [340.0, -10.0, 220.0], STEEL, NO_GLOW);
    push_box(m, [-340.0, -10.0, -220.0], [340.0, -2.0, 220.0], stage::scaled(RESIST, 0.8), NO_GLOW);
    let w = cd(c) * NM;
    let n = (300.0 / (2.0 * w)).floor() as i32;
    for i in -n..=n {
        let x = i as f64 * 2.0 * w;
        push_box(m, [x - w / 2.0, -2.0, -200.0], [x + w / 2.0, 2.0, 200.0], stage::mix(FILM, PINK, 0.35), stage::scaled(PINK, 0.12));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = lens_r(c);
    let u = c.u();
    for k in 0..16 {
        let th = std::f64::consts::TAU * k as f64 / 16.0;
        let rim = [r * th.cos(), LENS_Y, r * th.sin()];
        cv.line(cam, rim, [0.0, 2.0, 0.0], LIGHT, 0.35);
        if k % 2 == 0 {
            particles(cv, cam, &[rim, [0.0, 2.0, 0.0]], 4, u * 1.5 + k as f64 * 0.07, 6.0, LIGHT, 0.9);
        }
    }
    cv.line(cam, [0.0, LENS_Y, 0.0], [0.0, 0.0, 0.0], TEXT, 0.25);
    // the depth that stays sharp: DOF ~ wavelength / NA^2, drawn about the focus
    let depth = c.during(2, 0.05, 1.0);
    if depth > 0.01 {
        let half = WAVELENGTH / (na(c) * na(c)) * NM * 0.25;
        stage::glass_cyl(cv, cam, [0.0, -half, 0.0], 60.0, 2.0 * half, PURPLE, (0.7 * depth) as f32);
        label(cv, cam, [60.0, half, 0.0], (0.06, -0.05), "in focus", PURPLE, depth);
    }
    label(cv, cam, [r, LENS_Y + 26.0, 0.0], (0.05, -0.06), "last lens element", CYAN, 0.9);
    label(cv, cam, [r * 0.5, LENS_Y * 0.5, 0.0], (0.10, 0.0), &format!("NA {:.2}", na(c)), LIGHT, 1.0);
    label(cv, cam, [300.0, 0.0, 200.0], (0.02, 0.08), &format!("line {:.0} nm", cd(c)), PINK, 0.95);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "CD = k1 x wavelength / NA", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "EUV 13.5 nm, k1 0.4", GLASS, 0.8);
}
