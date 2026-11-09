//! Zoom b: DDR5's two subchannels. A DDR4 DIMM is one 64-bit channel: all eight chips
//! work in lockstep and a 64-byte line takes 8 transfers of 8 bytes. A DDR5 DIMM is
//! two independent 32-bit subchannels (40 with ECC): each half serves its own request,
//! a 64-byte line in 16 transfers of 4 bytes, so two requests run at once.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const CHIPS: usize = 8;
const DX: f64 = 300.0;
const CX: f64 = -380.0;

/// Chip positions: two halves with a small gap (the board is the same in every beat;
/// the split shows in colour and flow).
fn chip_z(k: usize) -> f64 {
    (k as f64 - 3.5) * 60.0 + if k >= 4 { 20.0 } else { -20.0 }
}

fn split(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.45) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 20.0, 0.0], dist: 1150.0, yaw: 0.35, pitch: 0.65 },
        Shot { target: [0.0, 20.0, 0.0], dist: 1150.0, yaw: 0.55, pitch: 0.60 },
        Shot { target: [0.0, 20.0, 0.0], dist: 1100.0, yaw: 0.20, pitch: 0.70 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [CX - 80.0, -20.0, -320.0], [DX + 80.0, 0.0, 320.0], STEEL, NO_GLOW);
    push_box(m, [DX, 0.0, -260.0], [DX + 30.0, 100.0, 260.0], [0.20, 0.42, 0.30], NO_GLOW);
    let s = split(c);
    for k in 0..CHIPS {
        let col = if k < 4 { stage::mix(GREEN, ORANGE, s) } else { stage::mix(GREEN, CYAN, s) };
        push_box(m, [DX - 10.0, 20.0, chip_z(k) - 22.0], [DX, 80.0, chip_z(k) + 22.0], stage::mix(QUIET, col, 0.7), NO_GLOW);
        crate::push_tube(m, [CX + 40.0, 10.0, chip_z(k)], [DX - 10.0, 10.0, chip_z(k)], 3.0, 6, METAL, NO_GLOW, false);
    }
    // the controller, one port, or two as the DIMM splits
    push_box(m, [CX - 60.0, 0.0, -260.0], [CX + 40.0, 60.0, 260.0], stage::mix(METAL, PURPLE, 0.35), NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let s = split(c);
    let two = c.during(2, 0.05, 0.85);
    for k in 0..CHIPS {
        let z = chip_z(k);
        let col = if k < 4 { stage::mix(GREEN, ORANGE, s) } else { stage::mix(GREEN, CYAN, s) };
        // in lockstep every wire pulses together; split, each half runs its own stream
        let ph = if k < 4 { 0.0 } else { 0.37 * s };
        let n = if s > 0.5 { 16 } else { 8 };
        particles(cv, cam, &[[DX - 12.0, 12.0, z], [CX + 44.0, 12.0, z]], n, c.u() * 1.4 + ph, 5.0, col, 1.0);
    }
    label(cv, cam, [DX + 30.0, 100.0, -260.0], (0.03, -0.06), "one DIMM, 8 chips", TEXT, 0.85);
    label(cv, cam, [CX - 60.0, 60.0, -260.0], (-0.06, -0.07), "memory controller", PURPLE, 0.85);
    label(cv, cam, [DX, 80.0, chip_z(1)], (0.05, -0.06), "subchannel A: 32 bits", ORANGE, s);
    label(cv, cam, [DX, 80.0, chip_z(6)], (0.05, 0.06), "subchannel B: 32 bits", CYAN, s);
    label(cv, cam, [0.0, 12.0, 0.0], (0.0, 0.10), "two requests at once", TEXT, two);
    let (title, sub) = if c.beat == 0 {
        ("DDR4: one 64-bit channel, chips in lockstep", "64-byte line = 8 transfers x 8 bytes")
    } else {
        ("DDR5: two independent 32-bit subchannels", "64-byte line = 16 transfers x 4 bytes (BL16)")
    };
    let k = if c.beat == 0 { c.during(0, 0.0, 1.0) } else { c.during(1, 0.0, 1.0) + c.during(2, 0.0, 1.0) };
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, TEXT, k.min(1.0));
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, sub, CYAN, k.min(1.0));
}
