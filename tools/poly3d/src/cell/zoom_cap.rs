//! Zoom a: the storage capacitor and nothing else. Two plates, the charge between
//! them, and a level gauge. Charge leaves through the three named leak paths, and
//! a refresh brings it back down the top lead.

use super::push_sphere;
use super::stage::{self, disc_lattice, label, particles, slot_fill, Clock, Shot};
use crate::{Cam, Canvas, Col, Tri};

const PLATE_R: f64 = 300.0;
const GAP: f64 = 85.0;
const PLATE_T: f64 = 20.0;
const GAUGE_X: f64 = -470.0;
const GAUGE_H: f64 = 380.0;

const PLATE: Col = [0.86, 0.87, 0.84];
const LEAD: Col = [0.55, 0.56, 0.60];
const CHARGE: Col = [1.0, 0.72, 0.42];
const EMPTY: Col = [0.30, 0.31, 0.37];
const LEAK: Col = [1.0, 0.50, 0.25];
const REFILL: Col = [0.55, 0.91, 0.99];
const GLASS: Col = [0.62, 0.80, 0.92];
const TEXT: Col = [0.97, 0.97, 0.95];

const SHOTS: [Shot; 3] = [
    Shot { target: [-70.0, 10.0, 0.0], dist: 1180.0, yaw: 0.42, pitch: 0.34 },
    Shot { target: [20.0, 20.0, 0.0], dist: 1320.0, yaw: 0.62, pitch: 0.30 },
    Shot { target: [-60.0, 90.0, 0.0], dist: 1240.0, yaw: 0.34, pitch: 0.24 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Charge: full, drains through beat 1, refilled through beat 2. Back at full by the loop.
fn level(c: &Clock) -> f64 {
    1.0 - 0.5 * c.ramp(1, 0.05, 0.95) + 0.5 * c.ramp(2, 0.12, 0.88)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let zero = [0.0f32; 3];
    for y in [GAP, -GAP] {
        let (a, b) = (y - PLATE_T / 2.0, y + PLATE_T / 2.0);
        crate::push_tube(m, [0.0, a, 0.0], [0.0, b, 0.0], PLATE_R, 72, PLATE, zero, true);
    }
    crate::push_tube(m, [0.0, GAP, 0.0], [0.0, 340.0, 0.0], 15.0, 16, LEAD, zero, true);
    crate::push_tube(m, [0.0, -GAP, 0.0], [0.0, -300.0, 0.0], 15.0, 16, LEAD, zero, true);

    let lv = level(c);
    let pts = disc_lattice(PLATE_R - 40.0, 58.0, &[-28.0, 28.0]);
    let n = pts.len();
    for (rank, p) in pts.iter().enumerate() {
        let f = slot_fill(rank, n, lv);
        let col = stage::mix(EMPTY, CHARGE, f);
        let glow = stage::scaled(CHARGE, 0.5 * f);
        push_sphere(m, *p, 8.0 + 9.0 * f, 8, col, glow);
    }

    // level gauge: the fill is the charge in the cell
    let fill = lv * GAUGE_H;
    let base = -GAUGE_H / 2.0;
    crate::push_tube(
        m,
        [GAUGE_X, base, 0.0],
        [GAUGE_X, base + fill, 0.0],
        20.0,
        24,
        CHARGE,
        stage::scaled(CHARGE, 0.35),
        true,
    );
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    stage::glass_cyl(cv, cam, [0.0, -GAP + 10.0, 0.0], PLATE_R, 2.0 * GAP - 20.0, GLASS, 0.20);
    stage::glass_cyl(cv, cam, [GAUGE_X, -GAUGE_H / 2.0, 0.0], 30.0, GAUGE_H, GLASS, 0.30);

    let u = c.u();
    let leak = c.during(1, 0.0, 1.0);
    let refill = c.during(2, 0.05, 0.95);

    // the three leak paths the notes name
    let dielectric = [[PLATE_R - 20.0, 0.0, 30.0], [PLATE_R + 110.0, -6.0, 60.0], [PLATE_R + 300.0, -30.0, 90.0]];
    let junction = [[0.0, 210.0, 0.0], [130.0, 240.0, 70.0], [300.0, 300.0, 120.0]];
    let off_fet = [[0.0, 110.0, 0.0], [0.0, 340.0, 0.0], [0.0, 430.0, 0.0]];
    particles(cv, cam, &dielectric, 9, u * 1.5, 11.0, LEAK, leak);
    particles(cv, cam, &junction, 6, u * 1.5 + 0.3, 10.0, LEAK, leak);
    particles(cv, cam, &off_fet, 6, u * 1.5 + 0.6, 10.0, LEAK, leak);
    // refresh: charge comes back down the top lead and spreads over the plate
    let down = [[0.0, 430.0, 0.0], [0.0, GAP + 12.0, 0.0], [130.0, GAP - 22.0, 90.0]];
    let down2 = [[0.0, 430.0, 0.0], [0.0, GAP + 12.0, 0.0], [-130.0, GAP - 22.0, -60.0]];
    particles(cv, cam, &down, 8, u * 2.0, 12.0, REFILL, refill);
    particles(cv, cam, &down2, 8, u * 2.0 + 0.06, 12.0, REFILL, refill);

    // names: the parts always, each flow only while it runs
    label(cv, cam, [PLATE_R * 0.7, GAP + 10.0, -PLATE_R * 0.5], (0.05, -0.11), "top plate", TEXT, 0.9);
    label(cv, cam, [PLATE_R * 0.7, -GAP, PLATE_R * 0.6], (0.05, 0.09), "bottom plate", TEXT, 0.9);
    label(cv, cam, [0.0, 0.0, PLATE_R - 30.0], (-0.30, 0.20), "charge = the bit", CHARGE, 1.0 - 0.6 * leak);
    label(cv, cam, [GAUGE_X, GAUGE_H / 2.0, 0.0], (-0.03, -0.07), "charge level", CHARGE, 0.95);
    label(cv, cam, dielectric[2], (-0.20, -0.08), "through dielectric", LEAK, leak);
    label(cv, cam, junction[2], (0.02, -0.05), "node junction", LEAK, leak);
    label(cv, cam, off_fet[2], (-0.32, -0.02), "off transistor", LEAK, leak);
    label(cv, cam, down[0], (0.05, 0.03), "refresh: charge in", REFILL, refill);
}
