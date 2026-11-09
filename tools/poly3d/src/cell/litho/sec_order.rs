//! Section 3: one exposure, in order. A small column over a cut through the wafer:
//! the reticle, a lens, and the film stack from zoom c. Five beats: flash, project,
//! expose, develop, etch. A fresh film and resist come back at the end of the loop.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, NO_GLOW, STEEL, TEXT};
use super::rig::{CHROME, LIGHT, QUARTZ};
use super::zoom_resist::{self, Stack, GAPS, GAP_W, RESIST_TOP};
use crate::{Cam, Canvas, Tri};

pub(super) const BEATS: usize = 5;
const MASK_Y: f64 = 760.0;
const LENS_Y: f64 = 470.0;
const SOURCE_Y: f64 = 920.0;

const SHOTS: [Shot; BEATS] = [
    Shot { target: [0.0, 640.0, 0.0], dist: 1600.0, yaw: 0.45, pitch: 0.20 },
    Shot { target: [0.0, 420.0, 0.0], dist: 1900.0, yaw: 0.60, pitch: 0.15 },
    Shot { target: [0.0, 40.0, 0.0], dist: 1000.0, yaw: 0.40, pitch: 0.36 },
    Shot { target: [0.0, 30.0, 0.0], dist: 950.0, yaw: 0.55, pitch: 0.48 },
    Shot { target: [0.0, 20.0, 0.0], dist: 950.0, yaw: 0.25, pitch: 0.42 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn state(c: &Clock) -> Stack {
    let reset = 1.0 - c.ramp(4, 0.72, 0.97);
    Stack {
        expose: c.ramp(2, 0.05, 0.7) * reset,
        develop: c.ramp(3, 0.1, 0.8) * reset,
        etch: c.ramp(4, 0.05, 0.55) * reset,
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    zoom_resist::stack(&state(c), m);
    // reticle: openings twice as far apart as the gaps they print (shrunk by the lens)
    let lit = c.ramp(0, 0.1, 0.35) * (1.0 - c.ramp(2, 0.7, 0.95));
    push_box(m, [-420.0, MASK_Y - 5.0, -150.0], [420.0, MASK_Y + 5.0, 150.0], QUARTZ, NO_GLOW);
    let mut x0 = -420.0;
    for g in GAPS {
        let o = 2.0 * g;
        push_box(m, [x0, MASK_Y + 5.0, -150.0], [o - GAP_W, MASK_Y + 10.0, 150.0], CHROME, NO_GLOW);
        x0 = o + GAP_W;
    }
    push_box(m, [x0, MASK_Y + 5.0, -150.0], [420.0, MASK_Y + 10.0, 150.0], CHROME, NO_GLOW);
    crate::push_tube(m, [0.0, LENS_Y - 12.0, 0.0], [0.0, LENS_Y + 12.0, 0.0], 330.0, 64, stage::mix(STEEL, CYAN, 0.55), stage::scaled(CYAN, 0.1 * lit), true);
    push_box(m, [-90.0, SOURCE_Y, -60.0], [90.0, SOURCE_Y + 60.0, 60.0], stage::mix(STEEL, LIGHT, 0.3 + 0.6 * lit), stage::scaled(LIGHT, 0.35 * lit));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let s = state(c);
    let u = c.u();
    let flash = c.ramp(0, 0.1, 0.35) * (1.0 - c.ramp(2, 0.7, 0.95));
    let reach = c.ramp(1, 0.05, 0.4) * (1.0 - c.ramp(2, 0.7, 0.95));
    for (i, g) in GAPS.iter().enumerate() {
        let o = 2.0 * g;
        let down = [[o * 0.3, SOURCE_Y, 0.0], [o, MASK_Y + 12.0, 0.0]];
        particles(cv, cam, &down, 4, u * 1.4 + i as f64 * 0.2, 8.0, LIGHT, flash);
        let on = [[o, MASK_Y - 6.0, 0.0], [o * 0.8, LENS_Y, 0.0], [*g, RESIST_TOP + 2.0, 0.0]];
        particles(cv, cam, &on, 6, u * 1.4 + i as f64 * 0.2, 8.0, LIGHT, flash * reach);
    }
    let ions = c.during(4, 0.0, 0.6);
    for (i, g) in GAPS.iter().enumerate() {
        particles(cv, cam, &[[*g, 300.0, 0.0], [*g, 4.0, 0.0]], 5, u * 2.0 + i as f64 * 0.3, 7.0, CYAN, ions);
    }
    zoom_resist::names(cv, cam, &s);
    label(cv, cam, [420.0, MASK_Y + 10.0, 150.0], (0.04, -0.06), "reticle", TEXT, 0.8);
    label(cv, cam, [330.0, LENS_Y, 0.0], (0.05, 0.0), "lens: 2x here, 4x in a scanner", CYAN, 0.8);
    const STEPS: [&str; BEATS] = ["1 flash", "2 project", "3 expose", "4 develop", "5 etch"];
    let (w, h) = (cv.w as f64, cv.h as f64);
    let sc = stage::text_scale(cv);
    let mut x = (w * 0.04) as i64;
    for (i, st) in STEPS.iter().enumerate() {
        let k = stage::spotlight(c, i, BEATS);
        text(cv, x, (h * 0.92) as i64, st, stage::mix(GLASS, stage::ORANGE, k), 0.45 + 0.55 * k);
        x += stage::text_w(st, sc) + 10 * sc;
    }
}
