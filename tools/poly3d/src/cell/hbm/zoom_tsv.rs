//! Zoom a: a TSV and its microbumps, cut open. Two thinned DRAM dies over the base die:
//! copper through-silicon vias run straight through each die, and microbumps join the
//! via of one die to the next. A signal runs down the column. Then the dies thin, as
//! they must for tall stacks, and return for the loop.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, NO_GLOW, QUIET, TEXT, YELLOW};
use super::rig::{COPPER, DRAM, LOGIC};
use crate::{Cam, Canvas, Tri};

const XS: [f64; 3] = [-110.0, 0.0, 110.0];
const HZ: f64 = 45.0;
const BASE_T: f64 = 50.0;
const BUMP: f64 = 16.0;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 100.0, 0.0], dist: 900.0, yaw: 0.30, pitch: 0.15 },
        Shot { target: [0.0, 100.0, 0.0], dist: 850.0, yaw: 0.10, pitch: 0.12 },
        Shot { target: [0.0, 90.0, 0.0], dist: 850.0, yaw: 0.45, pitch: 0.18 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// Die thickness: 70 units, thinned to 40 in beat 2, back at the end.
fn die_t(c: &Clock) -> f64 {
    70.0 - 30.0 * c.ramp(2, 0.1, 0.5) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let t = die_t(c);
    // cut open at z = 0: the slab behind, the vias half exposed on the cut face
    push_box(m, [-220.0, 0.0, -HZ], [220.0, BASE_T, 0.0], LOGIC, NO_GLOW);
    let mut y = BASE_T;
    for _ in 0..2 {
        // bumps, then the die
        for x in XS {
            push_box(m, [x - 13.0, y, -13.0], [x + 13.0, y + BUMP, 13.0], stage::mix(QUIET, YELLOW, 0.6), NO_GLOW);
        }
        y += BUMP;
        push_box(m, [-220.0, y, -HZ], [220.0, y + t, 0.0], stage::scaled(DRAM, 0.9), NO_GLOW);
        for x in XS {
            crate::push_tube(m, [x, y - 1.0, 0.0], [x, y + t + 1.0, 0.0], 9.0, 12, COPPER, stage::scaled(COPPER, 0.25), true);
        }
        y += t;
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let t = die_t(c);
    let top = BASE_T + 2.0 * (BUMP + t);
    let sig = c.during(1, 0.05, 0.95);
    for (i, x) in XS.iter().enumerate() {
        particles(cv, cam, &[[*x, top, 0.0], [*x, BASE_T, 0.0]], 5, c.u() * 2.0 + i as f64 * 0.2, 7.0, YELLOW, sig);
    }
    stage::glass_box(cv, cam, [-220.0, 0.0, -HZ], [220.0, top, HZ], GLASS, 0.15);
    label(cv, cam, [XS[2], top, 0.0], (0.05, -0.06), "TSV: copper through the silicon", COPPER, 0.9);
    label(cv, cam, [XS[2] + 13.0, BASE_T + BUMP / 2.0, 13.0], (0.06, 0.06), "microbumps join die to die", YELLOW, 0.9);
    label(cv, cam, [220.0, BASE_T / 2.0, HZ], (0.03, 0.06), "base logic die", CYAN, 0.8);
    label(cv, cam, [-220.0, BASE_T + BUMP + t / 2.0, HZ], (-0.14, 0.03), "DRAM die", TEXT, 0.8);
    let thin = c.during(2, 0.1, 0.95);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "a cut through two DRAM dies (not to scale)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "dies thinned to 30-50 um; bump pitch about 40 um, heading to 10", GLASS, thin);
}
