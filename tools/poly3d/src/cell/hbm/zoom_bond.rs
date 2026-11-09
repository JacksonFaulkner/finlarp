//! Zoom d: microbumps vs hybrid bonding. Two 16-high stacks side by side. On the left
//! each die sits on microbumps with a gap; on the right hybrid bonding joins copper to
//! copper with no bump, so the same dies make a shorter stack. A plane marks the height
//! limit, raised from 720 to 775 um, which let 16-high HBM4 keep microbumps.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, GLASS, NO_GLOW, PINK, STEEL, TEXT, YELLOW};
use super::rig::{DRAM, LOGIC};
use crate::{Cam, Canvas, Tri};

const DIES: usize = 16;
const T: f64 = 14.0;
const GAP: f64 = 6.0;
const LX: f64 = -170.0;
const RX: f64 = 170.0;
/// world units per um for the limit plane (base die excluded)
const UM: f64 = (DIES as f64 * (T + GAP)) / 760.0;

fn hybrid(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.6) * (1.0 - c.ramp(2, 0.88, 0.99))
}

fn limit(c: &Clock) -> f64 {
    720.0 + 55.0 * c.ramp(2, 0.1, 0.5) * (1.0 - c.ramp(2, 0.88, 0.99))
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [LX, 170.0, 0.0], dist: 950.0, yaw: 0.30, pitch: 0.15 },
        Shot { target: [0.0, 170.0, 0.0], dist: 1050.0, yaw: 0.20, pitch: 0.12 },
        Shot { target: [0.0, 200.0, 0.0], dist: 1100.0, yaw: 0.35, pitch: 0.15 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn stack(m: &mut Vec<Tri>, x: f64, gap: f64) {
    push_box(m, [x - 90.0, 0.0, -70.0], [x + 90.0, 20.0, 70.0], LOGIC, NO_GLOW);
    for d in 0..DIES {
        let y = 20.0 + gap + d as f64 * (T + gap);
        if gap > 0.5 {
            for bx in [-60.0, 0.0, 60.0] {
                push_box(m, [x + bx - 6.0, y - gap, -6.0], [x + bx + 6.0, y, 6.0], YELLOW, NO_GLOW);
            }
        }
        push_box(m, [x - 86.0, y, -66.0], [x + 86.0, y + T, 66.0], DRAM, NO_GLOW);
    }
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-360.0, -20.0, -140.0], [360.0, 0.0, 140.0], STEEL, NO_GLOW);
    stack(m, LX, GAP);
    let hb = hybrid(c);
    stack(m, RX, GAP * (1.0 - hb));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let y = 20.0 + limit(c) * UM;
    let a = (0.4 + 0.5 * c.during(2, 0.05, 1.0)) as f32;
    stage::glass_box(cv, cam, [-330.0, y, -110.0], [330.0, y, 110.0], PINK, a);
    label(cv, cam, [330.0, y, 110.0], (0.03, -0.04), &format!("height limit {:.0} um", limit(c)), PINK, 0.9);
    label(cv, cam, [LX + 90.0, 20.0 + 3.0 * (T + GAP), 70.0], (0.04, 0.06), "microbumps: a gap per die", YELLOW, 0.9);
    label(cv, cam, [RX + 90.0, 20.0 + DIES as f64 * T, 70.0], (0.04, -0.06), "hybrid bonding: copper to copper", TEXT, hybrid(c));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "16-high stacks (not to scale)", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, "HBM4 kept microbumps once the limit rose", GLASS, c.during(2, 0.3, 1.0));
}
