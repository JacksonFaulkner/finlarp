//! Zoom d: address mapping. The controller splits each address into fields: row,
//! bank, bank group, column. With the column bits at the bottom, consecutive
//! addresses stay in one open row of one bank (row hits). A stride that flips the
//! bank bits spreads the requests over many banks, so they can work in parallel.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PURPLE, QUIET, TEXT};
use super::rig::{self, centre, Rig, N};
use crate::{Cam, Canvas, Col, Tri};

const BITS: usize = 16;
const BZ: f64 = -660.0;
/// Field per bit, high bit first: 6 row, 2 bank, 2 bank group, 6 column.
fn field(i: usize) -> (usize, Col) {
    match i {
        0..=5 => (0, ORANGE),
        6 | 7 => (1, PURPLE),
        8 | 9 => (2, CYAN),
        _ => (3, GREEN),
    }
}

fn bx(i: usize) -> f64 {
    (i as f64 - (BITS as f64 - 1.0) / 2.0) * 50.0
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 20.0, -560.0], dist: 1100.0, yaw: 0.05, pitch: 0.55 },
        Shot { target: [0.0, 10.0, -280.0], dist: 1700.0, yaw: 0.10, pitch: 0.75 },
        Shot { target: [0.0, 10.0, -200.0], dist: 1850.0, yaw: -0.10, pitch: 0.80 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// The bank each request goes to: one bank in beat 1, a new bank each step in beat 2.
fn target(c: &Clock) -> usize {
    if c.beat == 2 {
        ((c.local * 8.0) as usize * 5) % N
    } else {
        0
    }
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    let seq = c.during(1, 0.1, 0.95);
    r.open[0] = seq;
    r.read[0] = seq;
    for k in 0..8 {
        let i = (k * 5) % N;
        let t = 0.1 + 0.85 * k as f64 / 8.0;
        let w = c.ramp(2, t, t + 0.05) * (1.0 - c.ramp(2, 0.85, 0.97));
        r.open[i] = r.open[i].max(w);
        r.row[i] = 0.3 + 0.05 * k as f64;
    }
    r
}

/// Bit `i` lit: fields glow in beat 0; low (column) bits count in beat 1; bank bits in beat 2.
fn bit_on(c: &Clock, i: usize) -> f64 {
    let (f, _) = field(i);
    let step = (c.local * 8.0) as usize;
    let on = match (c.beat, f) {
        (1, 3) => ((step >> (BITS - 1 - i)) & 1) as f64,
        (2, 1) | (2, 2) => ((target(c) >> (9 - i)) & 1) as f64,
        _ => 0.0,
    };
    on * c.during(c.beat, 0.03, 0.9)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
    for i in 0..BITS {
        let (_, col) = field(i);
        let show = c.during(0, 0.1, 1.0);
        let lit = bit_on(c, i);
        let base = stage::mix(QUIET, col, 0.45 + 0.4 * show);
        push_box(m, [bx(i) - 20.0, 0.0, BZ - 20.0], [bx(i) + 20.0, 30.0 + 20.0 * lit, BZ + 20.0], stage::mix(base, col, lit), stage::scaled(col, 0.4 * lit));
    }
    push_box(m, [bx(0) - 40.0, -24.0, BZ - 50.0], [bx(BITS - 1) + 40.0, 0.0, BZ + 50.0], [0.2, 0.21, 0.24], NO_GLOW);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    let show = 0.6 + 0.4 * c.during(0, 0.1, 1.0);
    for (f, name, col) in [(0usize, "row", ORANGE), (1, "bank", PURPLE), (2, "bank group", CYAN), (3, "column", GREEN)] {
        let idx: Vec<usize> = (0..BITS).filter(|&i| field(i).0 == f).collect();
        let mid = (bx(idx[0]) + bx(*idx.last().unwrap())) / 2.0;
        label(cv, cam, [mid, 30.0, BZ - 20.0], (-0.03, -0.08), name, col, show);
    }
    let seq = c.during(1, 0.1, 0.95);
    let b = centre(0);
    particles(cv, cam, &[[bx(13), 30.0, BZ], [b[0], 30.0, b[2]]], 6, c.u() * 1.6, 8.0, GREEN, seq);
    label(cv, cam, rig::at(rig::Part::Bank(0)), (0.03, -0.07), "same bank, same row: hits", GREEN, seq);
    let spread = c.during(2, 0.1, 0.95);
    let t = centre(target(c));
    particles(cv, cam, &[[bx(7), 30.0, BZ], [t[0], 30.0, t[2]]], 6, c.u() * 1.6, 8.0, PURPLE, spread);
    label(cv, cam, [t[0], 30.0, t[2]], (0.04, -0.06), "stride: a new bank each time", PURPLE, spread);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "the controller picks which address bits choose the bank", TEXT, 0.9);
}
