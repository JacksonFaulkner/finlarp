//! Zoom c: channels. The stack's 1024-bit HBM3 interface is not one bus: it is 16
//! independent channels, each with its own commands and data, so many requests run at
//! once. HBM4 doubles it: 32 channels over 2048 bits.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, PURPLE, STEEL, TEXT};
use super::rig::{DRAM, LOGIC};
use crate::{Cam, Canvas, Col, Tri};

const SX: f64 = 280.0;
const GX: f64 = -200.0;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [40.0, 40.0, 0.0], dist: 1200.0, yaw: 0.30, pitch: 0.55 },
        Shot { target: [40.0, 40.0, 0.0], dist: 1150.0, yaw: 0.45, pitch: 0.60 },
        Shot { target: [40.0, 40.0, 0.0], dist: 1200.0, yaw: 0.20, pitch: 0.70 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// Bundles drawn: 1 bus in beat 0, 16 in beat 1, 32 in beat 2, back to 1 at the end.
fn split(c: &Clock) -> f64 {
    c.ramp(1, 0.05, 0.3) * (1.0 - c.ramp(2, 0.88, 0.99))
}

fn doubled(c: &Clock) -> f64 {
    c.ramp(2, 0.1, 0.35) * (1.0 - c.ramp(2, 0.88, 0.99))
}

fn chan_col(i: usize, n: usize) -> Col {
    stage::mix(CYAN, ORANGE, i as f64 / (n.max(2) - 1) as f64)
}

pub(super) fn solids(_c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [GX - 200.0, -20.0, -260.0], [SX + 160.0, 0.0, 260.0], STEEL, NO_GLOW);
    push_box(m, [GX - 180.0, 0.0, -220.0], [GX, 50.0, 220.0], stage::mix(STEEL, PURPLE, 0.5), NO_GLOW);
    push_box(m, [SX - 80.0, 0.0, -110.0], [SX + 80.0, 14.0, 110.0], LOGIC, NO_GLOW);
    for d in 0..8 {
        let y = 16.0 + d as f64 * 12.0;
        push_box(m, [SX - 76.0, y, -106.0], [SX + 76.0, y + 9.0, 106.0], DRAM, NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let s = split(c);
    let d = doubled(c);
    let n = if d > 0.5 { 32 } else { 16 };
    for i in 0..n {
        let z = -200.0 + 400.0 * (i as f64 + 0.5) / n as f64;
        let col = stage::mix(CYAN, chan_col(i, n), s);
        let a = [SX - 80.0, 8.0, z * 0.5];
        let b = [GX, 8.0, z];
        cv.line(cam, a, b, GLASS, 0.25);
        // each channel runs its own traffic: its own phase and on/off rhythm
        let on = if s > 0.01 { (0.5 + 0.5 * ((c.u() * 3.0 + i as f64 * 1.7).sin())).max(1.0 - s) } else { 1.0 };
        let phase = i as f64 * 0.37 * s;
        particles(cv, cam, &[a, b], 3, c.u() * 1.8 + phase, 4.0, col, on);
    }
    let label_n = c.during(0, 0.1, 1.0);
    label(cv, cam, [(SX + GX) / 2.0, 8.0, 0.0], (0.0, -0.10), "1024 bits wide (HBM3)", CYAN, label_n);
    label(cv, cam, [(SX + GX) / 2.0, 8.0, 200.0], (0.0, 0.08), "16 independent channels", ORANGE, s * (1.0 - d));
    label(cv, cam, [(SX + GX) / 2.0, 8.0, 200.0], (0.0, 0.08), "HBM4: 32 channels, 2048 bits", ORANGE, d);
    label(cv, cam, [SX + 80.0, 110.0, 110.0], (0.03, -0.05), "HBM stack", TEXT, 0.8);
    label(cv, cam, [GX - 180.0, 50.0, -220.0], (-0.04, -0.06), "GPU", PURPLE, 0.8);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "one stack, many channels (JEDEC)", TEXT, 0.9);
}
