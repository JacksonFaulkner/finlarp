//! Zoom e: open vs folded bit lines. A sense amp compares two lines. In the open
//! layout the reference line lies in the next array. It then lifts over the sense amp
//! and settles beside the signal line: folded. A noise pulse crosses the array and
//! bumps both lines alike, so the difference the amp sees stays flat.

use super::push_box;
use super::stage::{self, label, particles, Clock, Shot};
use super::{lerp, smooth};
use crate::{Cam, Canvas, Col, Tri, V3};

const LEFT: (f64, f64) = (-620.0, -80.0);
const RIGHT: (f64, f64) = (80.0, 620.0);
const DEPTH: f64 = 210.0;
const LINE_Y: f64 = 16.0;
const FOLD_Z: f64 = 56.0;
const SEGS: usize = 44;

const SIGNAL: Col = [0.55, 0.91, 0.99];
const REFERENCE: Col = [1.0, 0.72, 0.42];
const AMP: Col = [0.74, 0.58, 0.98];
const NOISE: Col = [1.0, 0.47, 0.78];
const DIFF: Col = [0.31, 0.92, 0.50];
const QUIET: Col = [0.33, 0.35, 0.44];
const GLASS: Col = [0.62, 0.80, 0.92];
const TEXT: Col = [0.97, 0.97, 0.95];

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 10.0, 0.0], dist: 1760.0, yaw: 0.06, pitch: 0.72 },
    Shot { target: [-190.0, 40.0, 0.0], dist: 1400.0, yaw: 0.24, pitch: 0.60 },
    Shot { target: [-300.0, 40.0, 30.0], dist: 1100.0, yaw: 0.44, pitch: 0.34 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// 0 open .. 1 folded: folds during beat 1, opens again at the start of the loop.
fn folded(c: &Clock) -> f64 {
    if c.beat == 0 {
        1.0 - c.ramp(0, 0.0, 0.35)
    } else {
        c.ramp(1, 0.08, 0.7)
    }
}

/// The noise pulse's x position and height, crossing the array during beat 2.
fn noise(c: &Clock) -> (f64, f64) {
    let k = ((c.u() - 2.12) / 0.70).clamp(0.0, 1.0);
    let x = lerp(LEFT.0 - 60.0, LEFT.1 - 110.0, k);
    (x, 86.0 * c.during(2, 0.08, 0.90))
}

fn bump(x: f64, c: &Clock) -> f64 {
    let (nx, amp) = noise(c);
    // both lines are held at the sense amp, so the bump dies out before reaching it
    amp * (-((x - nx) / 70.0).powi(2)).exp() * smooth(0.0, 90.0, LEFT.1 - x)
}

/// A bit line as tube pieces, so it can carry the noise bump.
fn push_line(m: &mut Vec<Tri>, pts: &[V3], r: f64, col: Col, glow: Col) {
    for w in pts.windows(2) {
        crate::push_tube(m, w[0], w[1], r, 8, col, glow, false);
    }
}

/// Points of the signal line: left array, into the sense amp.
fn signal_pts(c: &Clock) -> Vec<V3> {
    (0..=SEGS)
        .map(|i| {
            let x = lerp(LEFT.0, LEFT.1, i as f64 / SEGS as f64);
            [x, LINE_Y + bump(x, c), 0.0]
        })
        .collect()
}

/// Points of the reference line: right array when open, beside the signal when folded.
/// It lifts in an arc over the sense amp on the way.
fn reference_pts(c: &Clock) -> Vec<V3> {
    let f = folded(c);
    let shift = LEFT.0 - RIGHT.0;
    let lift = 110.0 * (std::f64::consts::PI * f).sin();
    (0..=SEGS)
        .map(|i| {
            let x = lerp(RIGHT.0, RIGHT.1, i as f64 / SEGS as f64) + shift * f;
            [x, LINE_Y + lift + bump(x, c) * f, FOLD_Z * f]
        })
        .collect()
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let zero = [0.0f32; 3];
    let f = folded(c);
    // the board under the arrays
    push_box(m, [LEFT.0 - 30.0, -12.0, -DEPTH], [LEFT.1, 0.0, DEPTH], [0.20, 0.21, 0.24], zero);
    if f < 0.98 {
        let k = 1.0 - f;
        let col = stage::mix([0.157, 0.165, 0.212], [0.20, 0.21, 0.24], k);
        push_box(m, [RIGHT.0, -12.0, -DEPTH], [RIGHT.1 + 30.0, 0.0, DEPTH], col, zero);
    }

    // the other lines of the array, dim: the pair being compared is the subject
    for z in [-150.0, -90.0, 130.0, 180.0] {
        crate::push_tube(m, [LEFT.0, 8.0, z], [LEFT.1, 8.0, z], 5.0, 6, QUIET, zero, false);
        if f < 0.7 {
            let col = stage::mix(QUIET, [0.157, 0.165, 0.212], f / 0.7);
            crate::push_tube(m, [RIGHT.0, 8.0, z], [RIGHT.1, 8.0, z], 5.0, 6, col, zero, false);
        }
    }

    push_line(m, &signal_pts(c), 11.0, SIGNAL, stage::scaled(SIGNAL, 0.3));
    push_line(m, &reference_pts(c), 11.0, REFERENCE, stage::scaled(REFERENCE, 0.3));

    // sense amp between the arrays, where both lines end
    push_box(m, [-72.0, 0.0, -66.0], [72.0, 74.0, 66.0 + FOLD_Z * f], AMP, stage::scaled(AMP, 0.2));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let f = folded(c);
    let u = c.u();
    stage::glass_box(cv, cam, [LEFT.0 - 30.0, 0.0, -DEPTH], [LEFT.1, 90.0, DEPTH], GLASS, 0.20);
    stage::glass_box(cv, cam, [RIGHT.0, 0.0, -DEPTH], [RIGHT.1 + 30.0, 90.0, DEPTH], GLASS, 0.20 * (1.0 - f) as f32);

    // signal and reference travel to the amp while no noise is running
    let quiet = 1.0 - c.ramp(2, 0.0, 0.12) + c.ramp(2, 0.88, 1.0);
    let sig = signal_pts(c);
    let refs = reference_pts(c);
    // particles ride on top of the lines, not inside them
    let above = |pts: &[V3]| -> Vec<V3> { pts.iter().map(|p| [p[0], p[1] + 18.0, p[2]]).collect() };
    particles(cv, cam, &above(&sig), 6, u * 1.5, 15.0, TEXT, 0.95 * quiet);
    let settled = if c.beat == 1 { c.ramp(1, 0.70, 0.85) } else { 1.0 };
    // open: the reference runs in from the far end of the other array, toward the amp
    let mut toward_amp = above(&refs);
    if f < 0.5 {
        toward_amp.reverse();
    }
    let travelling = if (0.02..0.98).contains(&f) { 0.0 } else { settled };
    particles(cv, cam, &toward_amp, 6, u * 1.5, 15.0, TEXT, 0.95 * quiet * travelling);

    // the noise pulse: a pink band moving across both lines
    let (nx, amp) = noise(c);
    let k = (amp / 86.0).clamp(0.0, 1.0);
    if k > 0.01 {
        let lo = [nx - 6.0, 2.0, -DEPTH];
        let hi = [nx - 6.0, 2.0, DEPTH];
        cv.overlay(cam, lo, hi, NOISE, 0.8 * k as f32);
        cv.overlay(cam, [nx + 6.0, 2.0, -DEPTH], [nx + 6.0, 2.0, DEPTH], NOISE, 0.5 * k as f32);
    }

    // the difference the amp sees: flat, on the floor in front of the pair
    let diff = c.during(2, 0.10, 0.96);
    let z = DEPTH + 60.0;
    let x0 = LEFT.0 - 30.0;
    for dz in [0.0, 3.0, 6.0] {
        cv.overlay(cam, [x0, 2.0, z + dz], [LEFT.1, 2.0, z + dz], DIFF, diff as f32);
    }

    // names
    label(cv, cam, sig[8], (-0.08, -0.16), "signal line", SIGNAL, 0.95);
    let at = if f < 0.5 { SEGS - 8 } else { 10 };
    label(cv, cam, refs[at], (-0.04, 0.09), "reference line", REFERENCE, 0.95);
    label(cv, cam, [0.0, 74.0, 0.0], (-0.05, -0.15), "sense amp compares them", AMP, 0.95 * (1.0 - c.ramp(2, 0.05, 0.2)) + 0.95 * c.ramp(2, 0.95, 1.0));
    label(cv, cam, [(LEFT.0 + LEFT.1) / 2.0, 0.0, DEPTH], (-0.04, 0.17), "array 1", GLASS, 0.9 * (1.0 - f));
    label(cv, cam, [(RIGHT.0 + RIGHT.1) / 2.0, 0.0, DEPTH], (-0.04, 0.17), "array 2", GLASS, 0.9 * (1.0 - f));
    label(cv, cam, [(LEFT.0 + LEFT.1) / 2.0, 0.0, -DEPTH], (-0.08, -0.14), "same array, side by side", GLASS, 0.95 * f * c.ramp(1, 0.0, 0.3) * (1.0 - c.ramp(2, 0.0, 0.2)));
    label(cv, cam, [nx, 2.0, -DEPTH], (-0.05, -0.08), "noise hits both", NOISE, k);
    label(cv, cam, [x0 + 40.0, 2.0, z], (-0.02, 0.06), "difference: stays flat", DIFF, diff);
}
