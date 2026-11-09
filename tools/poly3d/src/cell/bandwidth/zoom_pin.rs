//! Zoom a: one pin. A clock runs above the wire. Sending one bit per clock gives one
//! transfer per cycle; DDR sends one on each edge, two per cycle (DDR4-3200 is 3200
//! million transfers a second from a 1600 MHz clock); PAM4 uses four voltage levels,
//! two bits per symbol (GDDR6X). The pin then returns to one bit per clock.

use super::super::push_box;
use super::super::stage::{self, label, text, Clock, Shot, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, STEEL, TEXT};
use crate::{Cam, Canvas, Tri};

const L: f64 = 420.0;
const P: f64 = 120.0;
const CLK_Y: f64 = 150.0;

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 70.0, 0.0], dist: 1050.0, yaw: 0.05, pitch: 0.25 },
        Shot { target: [0.0, 70.0, 0.0], dist: 1000.0, yaw: 0.20, pitch: 0.28 },
        Shot { target: [0.0, 70.0, 0.0], dist: 1050.0, yaw: -0.10, pitch: 0.30 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

fn ddr(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.4) * (1.0 - c.ramp(2, 0.85, 0.99))
}

fn pam(c: &Clock) -> f64 {
    c.ramp(2, 0.1, 0.4) * (1.0 - c.ramp(2, 0.85, 0.99))
}

/// Where the wave has moved to, within one period, and how many whole periods.
fn shift(c: &Clock) -> f64 {
    (c.u() * P).rem_euclid(P)
}

fn periods(c: &Clock) -> i64 {
    c.u().floor() as i64
}

/// A symbol's level, 0..1: binary (0 or 1) blended to four levels with PAM4. The
/// pattern repeats every 6 symbols, the shift over one loop, so the loop is seamless.
fn level(n: i64, pam: f64) -> f64 {
    const PATTERN: [usize; 6] = [3, 0, 2, 1, 3, 2];
    let h = PATTERN[n.rem_euclid(6) as usize];
    let bin = (h % 2) as f64;
    let four = (h % 4) as f64 / 3.0;
    bin + (four - bin) * pam
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-L - 40.0, -20.0, -80.0], [L + 40.0, 0.0, 80.0], STEEL, NO_GLOW);
    crate::push_tube(m, [-L, 10.0, 0.0], [L, 10.0, 0.0], 4.0, 8, METAL, NO_GLOW, false);
    let (d, p, sh, base) = (ddr(c), pam(c), shift(c), periods(c));
    // symbols ride the wire: one per rising edge, and one per falling edge as DDR comes in
    let n0 = (-L / P).floor() as i64 - 1;
    for n in n0..=((L / P).ceil() as i64 + 1) {
        for half in [0.0, 0.5] {
            let scale = if half == 0.0 { 1.0 } else { d };
            if scale < 0.01 {
                continue;
            }
            let x = n as f64 * P + half * P + sh;
            if x.abs() > L - 20.0 {
                continue;
            }
            let edge = ((L - x.abs()) / 60.0).clamp(0.0, 1.0);
            // each symbol keeps its value as it moves along
            let k = (n - base) * 2 + (half * 2.0) as i64;
            let lv = level(k, p);
            let hgt = (14.0 + 70.0 * lv) * scale * edge;
            let col = stage::mix(stage::mix(ORANGE, GREEN, lv), CYAN, p * 0.5);
            push_box(m, [x - 18.0 * scale, 14.0, -18.0], [x + 18.0 * scale, 14.0 + hgt, 18.0], col, stage::scaled(col, 0.15));
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    // the clock: a square wave moving with the symbols
    let sh = shift(c);
    let mut x = -L - P + sh;
    while x < L {
        let (a, b) = (x.max(-L), (x + P / 2.0).min(L));
        if b > a {
            cv.line(cam, [a, CLK_Y + 40.0, 0.0], [b, CLK_Y + 40.0, 0.0], TEXT, 0.7);
        }
        let (a2, b2) = ((x + P / 2.0).max(-L), (x + P).min(L));
        if b2 > a2 {
            cv.line(cam, [a2, CLK_Y, 0.0], [b2, CLK_Y, 0.0], TEXT, 0.7);
        }
        for e in [x, x + P / 2.0] {
            if e.abs() < L {
                cv.line(cam, [e, CLK_Y, 0.0], [e, CLK_Y + 40.0, 0.0], TEXT, 0.7);
            }
        }
        x += P;
    }
    label(cv, cam, [L, CLK_Y + 40.0, 0.0], (0.03, -0.04), "clock", TEXT, 0.8);
    label(cv, cam, [L, 10.0, 0.0], (0.03, 0.05), "one data pin", GLASS, 0.8);
    let (title, sub) = match c.beat {
        0 => ("one transfer per clock", "the bit changes once a cycle"),
        1 => ("DDR: a transfer on each edge", "DDR4-3200: 3200 MT/s from a 1600 MHz clock"),
        _ => ("PAM4: four levels, two bits per symbol", "GDDR6X (Micron)"),
    };
    let k = c.during(c.beat, 0.0, 1.0);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, title, TEXT, k);
    text(cv, (w * 0.04) as i64, (h * 0.10) as i64, sub, CYAN, k);
}
