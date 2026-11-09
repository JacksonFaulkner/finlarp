//! Section 7: multi-patterning. The target is lines at a pitch one exposure cannot
//! print: tried at once, they blur into each other. Split over two masks, A prints
//! every other line and B fills the gaps. Any overlay error between the two passes
//! shows up as uneven spacing.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, NO_GLOW, ORANGE, PINK, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const N: i32 = 8;
const PITCH: f64 = 60.0;
const W: f64 = 24.0;
const HZ: f64 = 180.0;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 0.0, 0.0], dist: 950.0, yaw: 0.30, pitch: 0.65 },
    Shot { target: [0.0, 0.0, 0.0], dist: 950.0, yaw: 0.50, pitch: 0.55 },
    Shot { target: [0.0, 0.0, 0.0], dist: 800.0, yaw: 0.15, pitch: 0.80 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn lx(i: i32) -> f64 {
    (i as f64 - (N as f64 - 1.0) / 2.0) * PITCH
}

/// One exposure's blur, fading as the split takes over in beat 1.
fn blur(c: &Clock) -> f64 {
    c.ramp(0, 0.1, 0.5) * (1.0 - c.ramp(1, 0.0, 0.25))
}

fn pass_a(c: &Clock) -> f64 {
    c.ramp(1, 0.2, 0.5) * (1.0 - c.ramp(2, 0.85, 0.99))
}

fn pass_b(c: &Clock) -> f64 {
    c.ramp(1, 0.55, 0.85) * (1.0 - c.ramp(2, 0.85, 0.99))
}

/// B's shift from overlay error, in beat 2.
fn shift(c: &Clock) -> f64 {
    14.0 * c.during(2, 0.1, 0.8)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-300.0, -30.0, -220.0], [300.0, 0.0, 220.0], STEEL, NO_GLOW);
    let bl = blur(c);
    if bl > 0.01 {
        // all at once: the lines swell into one smeared band
        let wide = W + (PITCH - W) * bl;
        for i in 0..N {
            push_box(m, [lx(i) - wide / 2.0, 0.0, -HZ], [lx(i) + wide / 2.0, 4.0 * bl, HZ], stage::mix(STEEL, ORANGE, 0.6 * bl), NO_GLOW);
        }
    }
    let (a, b, s) = (pass_a(c), pass_b(c), shift(c));
    for i in 0..N {
        let (k, col, dx) = if i % 2 == 0 { (a, PINK, 0.0) } else { (b, CYAN, s) };
        if k > 0.01 {
            let x = lx(i) + dx;
            push_box(m, [x - W / 2.0, 0.0, -HZ], [x + W / 2.0, 14.0 * k, HZ], col, stage::scaled(col, 0.15 * k));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let bl = blur(c);
    let (a, b) = (pass_a(c), pass_b(c));
    label(cv, cam, [lx(N - 1), 4.0, HZ], (0.03, 0.06), "one exposure: lines merge", ORANGE, bl);
    label(cv, cam, [lx(0), 14.0, -HZ], (-0.08, -0.08), "mask A", PINK, a);
    label(cv, cam, [lx(1) + shift(c), 14.0, HZ], (0.02, 0.09), "mask B", CYAN, b);
    let s = c.during(2, 0.1, 0.8);
    label(cv, cam, [lx(1) + shift(c), 14.0, 0.0], (0.08, -0.12), "B off by overlay error", TEXT, s);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "k1 below 0.25: split the pattern", TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "each pass: another mask, more time, more error", GLASS, 0.5 + 0.5 * s);
}
