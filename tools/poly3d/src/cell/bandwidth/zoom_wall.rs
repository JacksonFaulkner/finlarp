//! Zoom e: the memory wall. Eleven two-year steps over twenty years, on a log scale:
//! peak server compute growing 3.0x every two years, DRAM bandwidth 1.6x, interconnect
//! 1.4x (Gholami et al., AI and Memory Wall). The gap between them is the wall.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, PINK, PURPLE, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

const STEPS: usize = 11;
const SERIES: [(&str, f64, Col); 3] = [("compute 3.0x / 2 yrs", 3.0, PINK), ("DRAM bandwidth 1.6x / 2 yrs", 1.6, CYAN), ("interconnect 1.4x / 2 yrs", 1.4, PURPLE)];
/// world units per decade
const DEC: f64 = 70.0;

fn sx(i: usize) -> f64 {
    -400.0 + 80.0 * i as f64
}

fn sz(s: usize) -> f64 {
    (s as f64 - 1.0) * 70.0
}

/// How much of series `s` has grown in: compute in beat 0, the other two in beat 1.
fn grown(c: &Clock, s: usize) -> f64 {
    let beat = if s == 0 { 0 } else { 1 };
    c.ramp(beat, 0.1, 0.85) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 120.0, 0.0], dist: 1300.0, yaw: 0.35, pitch: 0.30 },
        Shot { target: [0.0, 100.0, 0.0], dist: 1300.0, yaw: 0.50, pitch: 0.28 },
        Shot { target: [100.0, 120.0, 0.0], dist: 1250.0, yaw: 0.25, pitch: 0.25 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-460.0, -20.0, -140.0], [460.0, 0.0, 140.0], STEEL, NO_GLOW);
    for (s, (_, f, col)) in SERIES.iter().enumerate() {
        let g = grown(c, s);
        for i in 0..STEPS {
            let t = (g * STEPS as f64 - i as f64).clamp(0.0, 1.0);
            if t < 0.01 {
                continue;
            }
            let hgt = (DEC * (i as f64 * f.log10())).max(4.0) * t;
            push_box(m, [sx(i) - 14.0, 0.0, sz(s) - 20.0], [sx(i) + 14.0, hgt + 4.0, sz(s) + 20.0], *col, stage::scaled(*col, 0.12));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    for (s, (name, f, col)) in SERIES.iter().enumerate() {
        let g = grown(c, s);
        let top = DEC * (10.0 * f.log10()) + 4.0;
        label(cv, cam, [sx(STEPS - 1) + 14.0, top * g.min(1.0), sz(s)], (0.03, -0.03), name, *col, g);
    }
    let gap = c.during(2, 0.05, 0.85);
    let (hc, hb) = (DEC * 10.0 * 3.0f64.log10(), DEC * 10.0 * 1.6f64.log10());
    cv.overlay(cam, [sx(STEPS - 1) + 30.0, hb, 0.0], [sx(STEPS - 1) + 30.0, hc, -70.0], TEXT, (0.9 * gap) as f32);
    label(cv, cam, [sx(STEPS - 1) + 30.0, (hb + hc) / 2.0, -30.0], (0.04, 0.0), "the wall: 60,000x vs 100x", TEXT, gap);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "20 years, log scale (Gholami et al.)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "one bar per 2 years", GLASS, 0.8);
}
