//! Zoom c: GDDR next to HBM. A GPU with GDDR6 chips on the board around it: each chip
//! has 32 data pins at up to 16 Gb/s, 64 GB/s. An HBM3 stack sits right beside the
//! GPU on an interposer: 1024 data pins at 6.4 Gb/s, 819 GB/s. Short, dense wiring is
//! what lets HBM use so many pins at a lower rate per pin.

use super::super::push_box;
use super::super::stage::{self, label, particles, spotlight, text, Clock, Shot, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const GDDR: [[f64; 2]; 4] = [[-420.0, -260.0], [-420.0, 260.0], [420.0, -260.0], [420.0, 260.0]];
const HBM: [f64; 2] = [0.0, 230.0];

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [-200.0, 10.0, -60.0], dist: 1400.0, yaw: 0.25, pitch: 0.70 },
        Shot { target: [0.0, 30.0, 150.0], dist: 1000.0, yaw: 0.40, pitch: 0.50 },
        Shot { target: [0.0, 20.0, 60.0], dist: 1500.0, yaw: 0.15, pitch: 0.80 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let g = 1.0 - spotlight(c, 1, 3) * 0.7;
    let hb = 1.0 - spotlight(c, 0, 3) * 0.7;
    push_box(m, [-560.0, -24.0, -400.0], [560.0, 0.0, 400.0], [0.14, 0.26, 0.18], NO_GLOW);
    // interposer under GPU and HBM
    push_box(m, [-200.0, 0.0, -150.0], [200.0, 8.0, HBM[1] + 90.0], stage::mix(STEEL, METAL, 0.5), NO_GLOW);
    push_box(m, [-150.0, 8.0, -130.0], [150.0, 50.0, 130.0], stage::mix(METAL, PURPLE, 0.4), NO_GLOW);
    for d in 0..8 {
        let y = 10.0 + d as f64 * 12.0;
        push_box(m, [HBM[0] - 70.0, y, HBM[1] - 50.0], [HBM[0] + 70.0, y + 9.0, HBM[1] + 50.0], stage::mix(QUIET, ORANGE, 0.3 + 0.6 * hb), NO_GLOW);
    }
    for [x, z] in GDDR {
        push_box(m, [x - 60.0, 0.0, z - 50.0], [x + 60.0, 26.0, z + 50.0], stage::mix(QUIET, GREEN, 0.3 + 0.6 * g), NO_GLOW);
        for k in 0..4 {
            let dz = -30.0 + 20.0 * k as f64;
            let gx = if x < 0.0 { -150.0 } else { 150.0 };
            crate::push_tube(m, [x + if x < 0.0 { 60.0 } else { -60.0 }, 4.0, z + dz], [gx, 4.0, z * 0.3 + dz], 2.5, 6, METAL, NO_GLOW, false);
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let g = spotlight(c, 0, 3) + spotlight(c, 2, 3);
    let hb = spotlight(c, 1, 3) + spotlight(c, 2, 3);
    for [x, z] in GDDR {
        for k in 0..4 {
            let dz = -30.0 + 20.0 * k as f64;
            let gx = if x < 0.0 { -150.0 } else { 150.0 };
            particles(cv, cam, &[[x + if x < 0.0 { 60.0 } else { -60.0 }, 6.0, z + dz], [gx, 6.0, z * 0.3 + dz]], 6, c.u() * 2.2 + k as f64 * 0.1, 4.5, GREEN, g.min(1.0));
        }
    }
    for k in 0..32 {
        let x = -66.0 + 4.2 * k as f64;
        particles(cv, cam, &[[x, 12.0, HBM[1] - 50.0], [x, 12.0, 130.0]], 3, c.u() * 1.2 + k as f64 * 0.03, 2.5, CYAN, hb.min(1.0));
    }
    label(cv, cam, [GDDR[0][0] + 60.0, 26.0, GDDR[0][1] - 50.0], (0.0, -0.08), "GDDR6: 32 pins x 16 Gbit/s = 64 GB/s", GREEN, 0.4 + 0.6 * g.min(1.0));
    label(cv, cam, [HBM[0] + 70.0, 106.0, HBM[1] + 50.0], (0.04, 0.02), "HBM3: 1024 pins x 6.4 Gbit/s = 819 GB/s", ORANGE, 0.4 + 0.6 * hb.min(1.0));
    label(cv, cam, [150.0, 50.0, -130.0], (0.04, -0.06), "GPU", PURPLE, 0.8);
    label(cv, cam, [200.0, 8.0, HBM[1] + 90.0], (0.04, 0.06), "interposer: short, dense wires", TEXT, c.during(2, 0.1, 1.0));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "GB/s = pins x Gbit/s per pin / 8", TEXT, 0.9);
}
