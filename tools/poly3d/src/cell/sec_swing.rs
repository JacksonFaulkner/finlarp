//! Section 7: less area means less signal. Cc is the cell tank and Cb the bit line tank.
//! The bar is the swing the sense amp gets, worked out from the page's formula and drawn
//! enlarged. Narrow the cell and the bar drops; make it taller and the bar comes back.

use super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, PURPLE, STEEL, TEXT};
use super::{lerp, smooth};
use crate::{Cam, Canvas, Tri};

const CELL_X: f64 = -470.0;
const LINE_X: f64 = -60.0;
const BAR_X: f64 = 390.0;
const WIDE_R: f64 = 95.0;
const NARROW_R: f64 = 48.0;
const FLAT_H: f64 = 120.0;
/// tall enough to reach the wide cell's volume again
const TALL_H: f64 = FLAT_H * (WIDE_R * WIDE_R) / (NARROW_R * NARROW_R);
const LINE_R: f64 = 170.0;
const LINE_H: f64 = 300.0;
/// Cb against the wide cell's Cc; schematic, chosen to match the read scene
const CB: f64 = 6.0;
/// the bar's enlargement of the swing
const BAR_SCALE: f64 = 5200.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [-30.0, 170.0, 0.0], dist: 1460.0, yaw: 0.10, pitch: 0.22 },
    Shot { target: [-30.0, 170.0, 0.0], dist: 1460.0, yaw: 0.02, pitch: 0.22 },
    Shot { target: [-30.0, 240.0, 0.0], dist: 1560.0, yaw: 0.10, pitch: 0.16 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Cell radius and height: narrows in beat 1, grows in beat 2, resets at the loop start.
fn shape(c: &Clock) -> (f64, f64) {
    let back = if c.beat == 0 { 1.0 - c.ramp(0, 0.0, 0.3) } else { 0.0 };
    let narrow = (c.ramp(1, 0.08, 0.85) + back).min(1.0);
    let tall = if c.beat == 0 { back } else { c.ramp(2, 0.08, 0.85) };
    (lerp(WIDE_R, NARROW_R, narrow), lerp(FLAT_H, TALL_H, tall))
}

/// The page's formula at Vcell = VDD: dV = (VDD - VDD/2) x Cc / (Cc + Cb), VDD = 1.
fn swing(r: f64, h: f64) -> f64 {
    let cc = r * r * h / (WIDE_R * WIDE_R * FLAT_H);
    0.5 * cc / (cc + CB)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let (r, h) = shape(c);
    crate::push_tube(m, [CELL_X, -10.0, 0.0], [CELL_X, 0.0, 0.0], WIDE_R + 14.0, 40, STEEL, NO_GLOW, true);
    crate::push_tube(m, [CELL_X, 0.0, 0.0], [CELL_X, h, 0.0], r, 32, ORANGE, stage::scaled(ORANGE, 0.3), true);
    crate::push_tube(m, [LINE_X, -10.0, 0.0], [LINE_X, 0.0, 0.0], LINE_R + 12.0, 48, STEEL, NO_GLOW, true);
    crate::push_tube(m, [LINE_X, 0.0, 0.0], [LINE_X, LINE_H, 0.0], LINE_R, 48, CYAN, stage::scaled(CYAN, 0.16), true);
    crate::push_tube(m, [CELL_X + r, 26.0, 0.0], [LINE_X - LINE_R, 26.0, 0.0], 10.0, 10, stage::METAL, NO_GLOW, false);
    // the swing bar
    let bar = swing(r, h) * BAR_SCALE;
    crate::push_tube(m, [BAR_X, -10.0, 0.0], [BAR_X, 0.0, 0.0], 88.0, 32, STEEL, NO_GLOW, true);
    crate::push_tube(m, [BAR_X, 0.0, 0.0], [BAR_X, bar, 0.0], 70.0, 28, PURPLE, stage::scaled(PURPLE, 0.3), true);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let (r, h) = shape(c);
    let full = swing(WIDE_R, FLAT_H) * BAR_SCALE;
    stage::ring(cv, cam, [BAR_X, full, 0.0], 88.0, TEXT, 0.8);
    stage::glass_cyl(cv, cam, [BAR_X, 0.0, 0.0], 72.0, full, GLASS, 0.15);
    let ghost = smooth(0.02, 0.2, (WIDE_R - r) / (WIDE_R - NARROW_R));
    stage::glass_cyl(cv, cam, [CELL_X, 0.0, 0.0], WIDE_R, FLAT_H, GLASS, 0.4 * ghost as f32);

    label(cv, cam, [CELL_X, h, 0.0], (-0.05, -0.08), "Cc: the cell", ORANGE, 0.95);
    label(cv, cam, [LINE_X, LINE_H, 0.0], (-0.08, -0.08), "Cb: the bit line", CYAN, 0.95);
    label(cv, cam, [BAR_X, 0.0, 88.0], (-0.12, 0.08), "swing (enlarged)", PURPLE, 0.95);
    label(cv, cam, [BAR_X, full, 0.0], (-0.12, -0.08), "starting swing", TEXT, ghost * 0.9);
    let (w, h_px) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h_px * 0.04) as i64, "swing = (Vcell - VDD/2) x Cc / (Cc + Cb)", TEXT, 0.95);
    text(cv, (w * 0.04) as i64, (h_px * 0.93) as i64, "smaller Cc: the sense amp has less to work with", PURPLE, c.during(1, 0.3, 1.0));
    text(cv, (w * 0.04) as i64, (h_px * 0.93) as i64, "taller capacitor: Cc back, swing back", ORANGE, c.during(2, 0.3, 0.98));
}
