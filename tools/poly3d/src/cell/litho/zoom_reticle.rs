//! Zoom a: the reticle. A quartz plate with chrome lines on it: light passes the clear
//! openings and stops on the chrome. Below it, three dies printed from it. A speck of
//! dirt in one opening shows up on every die, until the mask is cleaned.

use super::super::push_box;
use super::super::stage::{self, label, particles, Clock, Shot, CYAN, NO_GLOW, PINK, STEEL, TEXT};
use super::rig::{CHROME, LIGHT, QUARTZ};
use crate::{Cam, Canvas, Tri};

const HX: f64 = 300.0;
const HZ: f64 = 200.0;
const OPEN: [f64; 4] = [-180.0, -60.0, 60.0, 180.0];
const OPEN_W: f64 = 60.0;
const DIE_Y: f64 = -380.0;
const DIES: [f64; 3] = [-330.0, 0.0, 330.0];
const DEFECT: (f64, f64) = (60.0, 40.0);

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 0.0, 0.0], dist: 1150.0, yaw: 0.50, pitch: 0.60 },
    Shot { target: [0.0, -90.0, 0.0], dist: 1500.0, yaw: 0.35, pitch: 0.25 },
    Shot { target: [0.0, -200.0, 0.0], dist: 1650.0, yaw: 0.30, pitch: 0.40 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn light(c: &Clock) -> f64 {
    c.ramp(1, 0.05, 0.3) * (1.0 - c.ramp(2, 0.85, 1.0))
}

/// The dirt in the opening: comes in early in beat 2, cleaned off at its end.
fn defect(c: &Clock) -> f64 {
    c.ramp(2, 0.05, 0.3) * (1.0 - c.ramp(2, 0.80, 0.97))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-HX, -8.0, -HZ], [HX, 8.0, HZ], QUARTZ, NO_GLOW);
    let mut x0 = -HX;
    for ox in OPEN {
        push_box(m, [x0, 8.0, -HZ], [ox - OPEN_W / 2.0, 16.0, HZ], CHROME, NO_GLOW);
        x0 = ox + OPEN_W / 2.0;
    }
    push_box(m, [x0, 8.0, -HZ], [HX, 16.0, HZ], CHROME, NO_GLOW);
    let d = defect(c);
    if d > 0.01 {
        let s = 16.0 * d;
        push_box(m, [DEFECT.0 - s, 8.0, DEFECT.1 - s], [DEFECT.0 + s, 8.0 + 14.0 * d, DEFECT.1 + s], PINK, stage::scaled(PINK, 0.3 * d));
    }
    // three dies printed from this mask, the lines 4x smaller than the openings
    for dx in DIES {
        push_box(m, [dx - 120.0, DIE_Y - 10.0, -100.0], [dx + 120.0, DIE_Y, 100.0], STEEL, NO_GLOW);
        for ox in OPEN {
            let x = dx + ox / 2.0;
            let hw = OPEN_W / 4.0 / 2.0 + 2.0;
            push_box(m, [x - hw, DIE_Y, -80.0], [x + hw, DIE_Y + 4.0, 80.0], stage::mix(STEEL, CYAN, 0.75), stage::scaled(CYAN, 0.08));
        }
        if d > 0.01 {
            let (x, z) = (dx + DEFECT.0 / 2.0, DEFECT.1 / 2.0);
            let s = 10.0 * d;
            push_box(m, [x - s, DIE_Y + 4.0, z - s], [x + s, DIE_Y + 7.0, z + s], PINK, stage::scaled(PINK, 0.4 * d));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let u = c.u();
    let l = light(c);
    let d = defect(c);
    // light falling on the whole plate: through the openings it goes on, on the chrome it stops
    for i in 0..9 {
        let x = -HX + 30.0 + i as f64 * 67.5;
        let open = OPEN.iter().any(|o| (x - o).abs() < OPEN_W / 2.0);
        let z = ((i * 37) % 7) as f64 * 40.0 - 120.0;
        if open {
            let path = [[x, 380.0, z], [x, -8.0, z], [x * 0.5, DIE_Y + 6.0, z * 0.5]];
            particles(cv, cam, &path, 6, u * 1.3 + i as f64 * 0.11, 9.0, LIGHT, l);
        } else {
            let path = [[x, 380.0, z], [x, 18.0, z]];
            particles(cv, cam, &path, 3, u * 1.3 + i as f64 * 0.11, 9.0, stage::scaled(LIGHT, 0.7), l);
        }
    }
    label(cv, cam, [HX, 16.0, -HZ * 0.6], (0.05, -0.08), "chrome: blocks light", TEXT, 0.9);
    label(cv, cam, [OPEN[0], 8.0, HZ], (-0.10, 0.10), "clear quartz opening", CYAN, 0.9);
    label(cv, cam, [DIES[2] + 120.0, DIE_Y, 100.0], (0.03, 0.07), "printed dies", CYAN, 0.6 + 0.4 * l);
    label(cv, cam, [DEFECT.0, 20.0, DEFECT.1], (-0.30, -0.10), "a speck on the mask", PINK, d);
    label(cv, cam, [DIES[0] + DEFECT.0 / 2.0, DIE_Y + 6.0, DEFECT.1 / 2.0], (-0.12, 0.10), "copied onto every die", PINK, d);
}
