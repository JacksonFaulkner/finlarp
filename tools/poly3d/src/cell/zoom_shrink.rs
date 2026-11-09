//! Zoom d: shrinking the cell. One capacitor morphs: wide and flat, then narrow and
//! flat, then narrow and tall. Charge is a fixed lattice that the capacitor's volume
//! reveals, so the amount of charge visibly follows the shape. A glass outline keeps
//! the old size in view, and the gauge shows how much charge fits.

use super::push_sphere;
use super::stage::{self, label, Clock, Shot};
use super::{lerp, smooth};
use crate::{Cam, Canvas, Col, Tri, V3};

const WIDE_R: f64 = 240.0;
const NARROW_R: f64 = 100.0;
const FLAT_H: f64 = 66.0;
/// tall enough to get the wide capacitor's volume back: R^2 H is the same
const TALL_H: f64 = FLAT_H * (WIDE_R * WIDE_R) / (NARROW_R * NARROW_R);
const PITCH: f64 = 34.0;
const FLOOR: f64 = -240.0;
const GAUGE_X: f64 = 420.0;
const GAUGE_H: f64 = 380.0;

const PLATE: Col = [0.86, 0.87, 0.84];
const CHARGE: Col = [1.0, 0.72, 0.42];
const GLASS: Col = [0.62, 0.80, 0.92];
const TEXT: Col = [0.97, 0.97, 0.95];
const PURPLE: Col = [0.74, 0.58, 0.98];

const SHOTS: [Shot; 3] = [
    Shot { target: [70.0, -30.0, 0.0], dist: 1200.0, yaw: 0.34, pitch: 0.36 },
    Shot { target: [70.0, -30.0, 0.0], dist: 1200.0, yaw: 0.42, pitch: 0.36 },
    Shot { target: [70.0, 40.0, 0.0], dist: 1440.0, yaw: 0.34, pitch: 0.18 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Capacitor radius and height: narrows in beat 1, grows in beat 2, and the loop
/// returns to the wide cell at the start of beat 0.
fn shape(c: &Clock) -> (f64, f64) {
    let back = 1.0 - c.ramp(0, 0.0, 0.35);
    let narrow = (c.ramp(1, 0.08, 0.9) + if c.beat == 0 { back } else { 0.0 }).min(1.0);
    let tall = if c.beat == 0 { back } else { c.ramp(2, 0.08, 0.9) };
    (lerp(WIDE_R, NARROW_R, narrow), lerp(FLAT_H, TALL_H, tall))
}

/// Charge the shape holds, against the wide cell: its volume, R^2 H.
fn held(r: f64, h: f64) -> f64 {
    (r * r * h / (WIDE_R * WIDE_R * FLAT_H)).clamp(0.0, 1.0)
}

/// The fixed charge lattice. Odd layers are offset for a tidier look at an angle.
fn lattice() -> Vec<V3> {
    let mut v = Vec::new();
    let rows = ((TALL_H / 2.0 + PITCH) / PITCH).ceil() as i32;
    let n = (WIDE_R / PITCH).ceil() as i32;
    for ly in -rows..rows {
        let y = (ly as f64 + 0.5) * PITCH;
        for i in -n..=n {
            for j in -n..=n {
                v.push([i as f64 * PITCH, y, j as f64 * PITCH]);
            }
        }
    }
    v
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let zero = [0.0f32; 3];
    let (r, h) = shape(c);
    for y in [h / 2.0 + 6.0, -h / 2.0 - 6.0] {
        crate::push_tube(m, [0.0, y - 6.0, 0.0], [0.0, y + 6.0, 0.0], r, 56, PLATE, zero, true);
    }
    let lead_top = (h / 2.0 + 12.0).max(200.0);
    crate::push_tube(m, [0.0, h / 2.0 + 12.0, 0.0], [0.0, lead_top + 90.0, 0.0], 9.0, 12, [0.55, 0.56, 0.60], zero, true);
    crate::push_tube(m, [0.0, -h / 2.0 - 12.0, 0.0], [0.0, FLOOR, 0.0], 9.0, 12, [0.55, 0.56, 0.60], zero, true);

    // a sphere exists only inside the capacitor, and shrinks away at the boundary
    let glow = stage::scaled(CHARGE, 0.5);
    for p in lattice() {
        let rad = (p[0] * p[0] + p[2] * p[2]).sqrt();
        let inside = smooth(0.0, PITCH * 0.6, r - 14.0 - rad) * smooth(0.0, PITCH * 0.6, h / 2.0 + 12.0 - p[1].abs());
        if inside > 0.02 {
            push_sphere(m, p, 11.0 * inside, 8, CHARGE, glow);
        }
    }

    let fill = held(r, h) * GAUGE_H;
    let base = FLOOR;
    crate::push_tube(m, [GAUGE_X, base, 0.0], [GAUGE_X, base + fill, 0.0], 22.0, 24, CHARGE, stage::scaled(CHARGE, 0.35), true);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let (r, h) = shape(c);
    // footprint on the floor: this is what scaling takes away
    let side = r + 24.0;
    stage::glass_box(cv, cam, [-side, FLOOR, -side], [side, FLOOR, side], PURPLE, 0.85);
    // the old size, once the shape has left it
    let ghost = smooth(0.02, 0.2, (WIDE_R - r) / (WIDE_R - NARROW_R));
    if ghost > 0.0 {
        let a = 0.45 * ghost as f32;
        stage::glass_cyl(cv, cam, [0.0, -FLAT_H / 2.0 - 12.0, 0.0], WIDE_R, FLAT_H + 24.0, GLASS, a);
        let old = WIDE_R + 24.0;
        stage::glass_box(cv, cam, [-old, FLOOR, -old], [old, FLOOR, old], GLASS, a);
    }
    stage::glass_cyl(cv, cam, [GAUGE_X, FLOOR, 0.0], 32.0, GAUGE_H, GLASS, 0.3);

    label(cv, cam, [GAUGE_X, FLOOR + GAUGE_H, 0.0], (-0.06, -0.07), "charge it holds", CHARGE, 0.95);
    label(cv, cam, [side, FLOOR, side], (-0.26, 0.05), "cell area: scales with F^2", PURPLE, 0.95);
    label(cv, cam, [-WIDE_R * 0.8, FLAT_H / 2.0 + 12.0, -WIDE_R * 0.5], (-0.14, -0.13), "old size", GLASS, ghost * c.ramp(1, 0.0, 0.12) * (1.0 - c.ramp(2, 0.05, 0.3)));
    let tall = (h - FLAT_H) / (TALL_H - FLAT_H);
    label(cv, cam, [-r, h / 4.0, 0.0], (-0.34, -0.12), "taller: charge back", TEXT, smooth(0.25, 0.7, tall));
}
