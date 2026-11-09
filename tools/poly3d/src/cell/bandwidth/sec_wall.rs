//! Section 7: the memory wall, as bytes available per operation. Compute grew
//! 60,000x in twenty years and DRAM bandwidth 100x (Gholami et al.), so each unit of
//! compute has 600x less bandwidth behind it. A bar shrinks step by step, log scale.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, PINK, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const STEPS: usize = 11;

fn sx(i: usize) -> f64 {
    -400.0 + 80.0 * i as f64
}

/// Bandwidth per compute after `i` two-year steps: (1.6 / 3.0)^i, log scale,
/// 90 units a decade above a floor at 10^-3.
fn hgt(i: usize) -> f64 {
    let r = (1.6f64 / 3.0).powi(i as i32);
    90.0 * (r.log10() + 3.0)
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-200.0, 140.0, 0.0], dist: 1200.0, yaw: 0.30, pitch: 0.25 },
        Shot { target: [0.0, 120.0, 0.0], dist: 1250.0, yaw: 0.45, pitch: 0.25 },
        Shot { target: [200.0, 80.0, 0.0], dist: 1150.0, yaw: 0.20, pitch: 0.25 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// How many bars are in: they come in through beats 0 and 1, and clear at the end.
fn shown(c: &Clock) -> f64 {
    let g = (c.ramp(0, 0.1, 0.95) * 0.5 + c.ramp(1, 0.0, 0.9) * 0.5) * (1.0 - c.ramp(2, 0.85, 0.99));
    g * STEPS as f64
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-460.0, -20.0, -120.0], [460.0, 0.0, 120.0], STEEL, NO_GLOW);
    let n = shown(c);
    for i in 0..STEPS {
        let t = (n - i as f64).clamp(0.0, 1.0);
        if t < 0.01 {
            continue;
        }
        let col = stage::mix(CYAN, PINK, i as f64 / (STEPS - 1) as f64);
        push_box(m, [sx(i) - 26.0, 0.0, -40.0], [sx(i) + 26.0, hgt(i) * t + 3.0, 40.0], col, stage::scaled(col, 0.12));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let n = shown(c);
    label(cv, cam, [sx(0), hgt(0), 40.0], (-0.06, -0.07), "bandwidth per unit of compute, year 0", CYAN, n.min(1.0));
    label(cv, cam, [sx(STEPS - 1), hgt(STEPS - 1), 40.0], (-0.10, -0.10), "20 years on: about 1/600", PINK, (n - 10.0).clamp(0.0, 1.0));
    label(cv, cam, [sx(STEPS - 1), 0.0, 40.0], (0.0, 0.08), "large models wait on memory", TEXT, c.during(2, 0.1, 0.85));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "1.6x / 3.0x every 2 years (Gholami et al.)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "log scale", GLASS, 0.8);
}
