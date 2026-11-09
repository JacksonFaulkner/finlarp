//! Zoom c: inside the resist. A cut through the wafer: substrate, the film to be
//! patterned, and the resist on top. Light through three openings exposes columns of
//! resist (acid forms there), develop dissolves them, and etch copies the gaps into
//! the film. Then the wafer gets a fresh film and resist, and the loop starts over.

use super::super::stage::{self, label, particles, Clock, Shot, NO_GLOW, PINK, STEEL, TEXT};
use super::super::{push_box, push_sphere};
use super::rig::{FILM, LIGHT, RESIST};
use crate::{Cam, Canvas, Tri};

pub(super) const GAPS: [f64; 3] = [-150.0, 0.0, 150.0];
pub(super) const GAP_W: f64 = 60.0;
const HX: f64 = 300.0;
const HZ: f64 = 150.0;
pub(super) const FILM_TOP: f64 = 40.0;
pub(super) const RESIST_TOP: f64 = 100.0;

/// The stack's state: exposed, developed, etched, each 0..1.
#[derive(Clone, Copy, Debug, Default)]
pub(super) struct Stack {
    pub expose: f64,
    pub develop: f64,
    pub etch: f64,
}

/// Spans of x between the gaps, from -HX to HX.
fn between() -> Vec<(f64, f64)> {
    let mut out = Vec::new();
    let mut x0 = -HX;
    for g in GAPS {
        out.push((x0, g - GAP_W / 2.0));
        x0 = g + GAP_W / 2.0;
    }
    out.push((x0, HX));
    out
}

pub(super) fn stack(s: &Stack, m: &mut Vec<Tri>) {
    push_box(m, [-HX, -70.0, -HZ], [HX, 0.0, HZ], STEEL, NO_GLOW);
    for (a, b) in between() {
        push_box(m, [a, 0.0, -HZ], [b, FILM_TOP, HZ], FILM, NO_GLOW);
        push_box(m, [a, FILM_TOP, -HZ], [b, RESIST_TOP, HZ], RESIST, NO_GLOW);
    }
    let latent = stage::mix(RESIST, PINK, s.expose);
    let glow = stage::scaled(PINK, 0.25 * s.expose);
    for g in GAPS {
        let (a, b) = (g - GAP_W / 2.0, g + GAP_W / 2.0);
        let film_top = FILM_TOP * (1.0 - s.etch);
        if film_top > 0.5 {
            push_box(m, [a, 0.0, -HZ], [b, film_top, HZ], FILM, NO_GLOW);
        }
        let top = RESIST_TOP - (RESIST_TOP - FILM_TOP) * s.develop;
        if top > FILM_TOP + 0.5 {
            push_box(m, [a, FILM_TOP, -HZ], [b, top, HZ], latent, glow);
            // acid in the exposed resist
            if s.expose > 0.05 {
                for k in 0..6 {
                    let y = FILM_TOP + 8.0 + (k % 3) as f64 * 18.0;
                    let z = -HZ + 30.0 + (k as f64) * 45.0;
                    if y < top - 6.0 {
                        push_sphere(m, [g + ((k * 7) % 5) as f64 * 5.0 - 10.0, y, z], 6.0 * s.expose, 6, PINK, stage::scaled(PINK, 0.5));
                    }
                }
            }
        }
    }
}

pub(super) fn names(cv: &mut Canvas, cam: &Cam, s: &Stack) {
    label(cv, cam, [HX, RESIST_TOP, HZ], (0.04, -0.06), "photoresist", stage::PURPLE, 0.9);
    label(cv, cam, [HX, FILM_TOP / 2.0, HZ], (0.05, 0.02), "film to pattern", stage::CYAN, 0.9);
    label(cv, cam, [HX, -35.0, HZ], (0.04, 0.08), "substrate", TEXT, 0.7);
    let k = s.expose * (1.0 - s.develop);
    label(cv, cam, [GAPS[0], RESIST_TOP, HZ], (-0.16, -0.10), "exposed: acid forms", PINK, k);
    label(cv, cam, [GAPS[1], FILM_TOP, HZ], (-0.04, -0.16), "developed away", TEXT, s.develop * (1.0 - s.etch));
    label(cv, cam, [GAPS[2], 0.0, HZ], (0.02, 0.10), "etched into the film", stage::CYAN, s.etch);
}

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 70.0, 0.0], dist: 1050.0, yaw: 0.35, pitch: 0.30 },
    Shot { target: [0.0, 60.0, 0.0], dist: 950.0, yaw: 0.55, pitch: 0.42 },
    Shot { target: [0.0, 30.0, 0.0], dist: 950.0, yaw: 0.25, pitch: 0.36 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn state(c: &Clock) -> Stack {
    let reset = 1.0 - c.ramp(2, 0.72, 0.97);
    Stack {
        expose: c.ramp(0, 0.1, 0.7) * reset,
        develop: c.ramp(1, 0.1, 0.8) * reset,
        etch: c.ramp(2, 0.05, 0.55) * reset,
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    stack(&state(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let s = state(c);
    let light = c.during(0, 0.0, 0.85);
    for (i, g) in GAPS.iter().enumerate() {
        for dz in [-80.0, 0.0, 80.0] {
            let path = [[*g, 420.0, dz], [*g, RESIST_TOP + 2.0, dz]];
            particles(cv, cam, &path, 4, c.u() * 1.5 + i as f64 * 0.2 + dz * 0.001, 8.0, LIGHT, light);
        }
    }
    // etch: ions come straight down into the gaps
    let ions = c.during(2, 0.0, 0.6);
    for (i, g) in GAPS.iter().enumerate() {
        let path = [[*g, 300.0, 0.0], [*g, FILM_TOP * (1.0 - s.etch) + 2.0, 0.0]];
        particles(cv, cam, &path, 5, c.u() * 2.0 + i as f64 * 0.3, 7.0, stage::CYAN, ions);
    }
    names(cv, cam, &s);
}
