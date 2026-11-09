//! The subarray every ARRAY scene shares: a grid of 1T1C cells, a word line per row,
//! a bit line per column, the row decoder on the left, the sense amp stripe (the row
//! buffer) at the front, the column decoder past it and the I/O on the right.
//!
//! Geometry, schematic units, Y up: rows run along x (index along z), columns along z
//! (index along x). Cells stand on the substrate at y = 0..40, word lines at y = 50,
//! bit lines at y = 62.

use super::super::push_box;
use super::super::stage::{self, label, particles, Rect, CYAN, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri, V3};

pub(super) const NR: usize = 8;
pub(super) const NC: usize = 12;
pub(super) const PITCH: f64 = 60.0;
pub(super) const WL_Y: f64 = 50.0;
pub(super) const BL_Y: f64 = 62.0;
const CELL_R: f64 = 13.0;
const CELL_H: f64 = 40.0;
/// sense amp stripe, column decoder, decoder and I/O positions
pub(super) const SA_Z: f64 = 300.0;
pub(super) const CD_Z: f64 = 380.0;
pub(super) const DEC_X: f64 = -420.0;
pub(super) const IO: V3 = [470.0, 30.0, 440.0];

pub(super) fn col_x(c: usize) -> f64 {
    (c as f64 - (NC as f64 - 1.0) / 2.0) * PITCH
}

pub(super) fn row_z(r: usize) -> f64 {
    (r as f64 - (NR as f64 - 1.0) / 2.0) * PITCH
}

/// The stored data: a fixed scatter of ones and zeros.
pub(super) fn bit(r: usize, c: usize) -> bool {
    (r * 7 + c * 5 + (r * c) % 3) % 3 != 0
}

/// The parts a spotlight or a note can pick out.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum Part {
    Cells,
    Decoder,
    BitLine,
    SenseAmps,
    ColDecoder,
    Io,
    OpenRow,
}

#[derive(Clone, Copy, Debug)]
pub(super) struct Rig {
    /// word line level per row, 0..1
    pub wl: [f64; NR],
    /// charge sharing onto the bit lines, 0..1 (a small nudge)
    pub share: f64,
    /// sense amps latched, 0..1 (bit lines driven to full rails, row buffer full)
    pub sense: f64,
    /// read strength per column: data leaving the row buffer for the I/O
    pub read: [f64; NC],
    /// an address arriving at the row decoder, 0..1
    pub addr: f64,
    /// colour kept per part (cells, decoder+word lines, bit lines, sense amps,
    /// column decoder, I/O), 1 = full, 0 = grey
    pub colour: [f64; 6],
    /// a row is marked bad (redundancy scenes) and how strongly
    pub bad: Option<(usize, f64)>,
    pub u: f64,
}

impl Default for Rig {
    fn default() -> Self {
        Rig { wl: [0.0; NR], share: 0.0, sense: 0.0, read: [0.0; NC], addr: 0.0, colour: [1.0; 6], bad: None, u: 0.0 }
    }
}

impl Rig {
    /// The row the sense amps hold: the one whose word line is highest.
    pub fn open_row(&self) -> usize {
        let mut best = 0;
        for r in 1..NR {
            if self.wl[r] > self.wl[best] {
                best = r;
            }
        }
        best
    }

    /// Bit line level of column `c`: 0.5 is VDD/2, 0 GND, 1 VDD.
    pub fn bl(&self, c: usize) -> f64 {
        let dev = 0.14 * self.share + 0.86 * self.sense;
        let up = bit(self.open_row(), c);
        0.5 + if up { 0.5 } else { -0.5 } * dev.min(1.0)
    }
}

fn tint(r: &Rig, i: usize, col: Col) -> Col {
    stage::mix(QUIET, col, r.colour[i])
}

const ZERO: Col = [0.18, 0.19, 0.24];

pub(super) fn solids(r: &Rig, m: &mut Vec<Tri>) {
    let hx = col_x(NC - 1) + 60.0;
    let hz = row_z(NR - 1) + 60.0;
    push_box(m, [DEC_X - 60.0, -24.0, -hz - 20.0], [IO[0] + 60.0, 0.0, CD_Z + 90.0], STEEL, NO_GLOW);

    let open = r.open_row();
    for row in 0..NR {
        let z = row_z(row);
        let w = r.wl[row];
        let bad = r.bad.filter(|b| b.0 == row).map_or(0.0, |b| b.1);
        // cells: full charge orange, empty dark
        for c in 0..NC {
            let x = col_x(c);
            let on = bit(row, c);
            let mut col = tint(r, 0, if on { ORANGE } else { ZERO });
            let mut glow = stage::scaled(ORANGE, if on { 0.18 * r.colour[0] } else { 0.0 });
            if row == open && w > 0.01 {
                glow = stage::scaled(if on { ORANGE } else { CYAN }, 0.25 * w * r.colour[0]);
            }
            if bad > 0.0 && c == 5 {
                col = stage::mix(col, PINK, bad);
                glow = stage::scaled(PINK, 0.5 * bad);
            }
            crate::push_tube(m, [x, 0.0, z], [x, CELL_H, z], CELL_R, 14, col, glow, true);
        }
        // word line: thickens and turns orange when high
        let col = tint(r, 1, stage::mix(METAL, ORANGE, w));
        crate::push_tube(m, [DEC_X + 30.0, WL_Y, z - 18.0], [hx, WL_Y, z - 18.0], 5.0 + 4.0 * w, 10, col, stage::scaled(ORANGE, 0.4 * w * r.colour[1]), false);
        // its driver in the row decoder
        push_box(m, [DEC_X - 30.0, 0.0, z - 22.0], [DEC_X + 30.0, 30.0 + 30.0 * w, z + 8.0], col, stage::scaled(ORANGE, 0.3 * w * r.colour[1]));
    }
    push_box(m, [DEC_X - 40.0, 0.0, -hz], [DEC_X + 40.0, 16.0, hz], tint(r, 1, METAL), NO_GLOW);

    // bit lines, sense amps, column decoder
    for c in 0..NC {
        let x = col_x(c) + 18.0;
        let v = r.bl(c);
        let hi = (v - 0.5).max(0.0) * 2.0;
        let lo = (0.5 - v).max(0.0) * 2.0;
        let col = stage::mix(stage::mix(METAL, CYAN, hi), ZERO, lo);
        crate::push_tube(m, [x, BL_Y, -hz], [x, BL_Y, SA_Z - 30.0], 5.0, 10, tint(r, 2, col), stage::scaled(CYAN, 0.3 * hi * r.colour[2]), false);
        let held = r.sense;
        let sa = stage::mix(PURPLE, if bit(r.open_row(), c) { ORANGE } else { ZERO }, held);
        push_box(m, [x - 22.0, 0.0, SA_Z - 30.0], [x + 22.0, 40.0 + 14.0 * held, SA_Z + 30.0], tint(r, 3, sa), stage::scaled(PURPLE, 0.15 * r.colour[3]));
        let sel = r.read[c];
        let cd = stage::mix(METAL, GREEN, sel);
        push_box(m, [x - 22.0, 0.0, CD_Z - 18.0], [x + 22.0, 22.0 + 10.0 * sel, CD_Z + 18.0], tint(r, 4, cd), stage::scaled(GREEN, 0.3 * sel * r.colour[4]));
    }
    // I/O pad
    let any = r.read.iter().cloned().fold(0.0, f64::max);
    push_box(m, [IO[0] - 40.0, 0.0, IO[2] - 40.0], [IO[0] + 40.0, 30.0 + 20.0 * any, IO[2] + 40.0], tint(r, 5, stage::mix(METAL, GREEN, 0.3 + 0.6 * any)), stage::scaled(GREEN, 0.3 * any * r.colour[5]));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, r: &Rig) {
    let u = r.u;
    let open = r.open_row();
    let z = row_z(open);
    // charge sharing: a little charge from each cell of the open row onto its bit line
    let flow = r.share * (1.0 - r.sense);
    for c in 0..NC {
        let x = col_x(c);
        let path = [[x, CELL_H, z], [x + 18.0, BL_Y, z], [x + 18.0, BL_Y, SA_Z - 30.0]];
        particles(cv, cam, &path, 3, u * 1.2 + c as f64 * 0.07, 5.0, if bit(open, c) { ORANGE } else { CYAN }, flow);
    }
    // reads: data from the chosen sense amps to the column decoder and on to the I/O
    for c in 0..NC {
        if r.read[c] <= 0.01 {
            continue;
        }
        let x = col_x(c) + 18.0;
        let path = [[x, 50.0, SA_Z], [x, 30.0, CD_Z], [x, 30.0, IO[2]], [IO[0], 40.0, IO[2]]];
        particles(cv, cam, &path, 5, u * 1.6 + c as f64 * 0.05, 6.0, GREEN, r.read[c]);
    }
    // the address into the row decoder
    let path = [[DEC_X - 80.0, 30.0, row_z(NR - 1) + 140.0], [DEC_X, 30.0, row_z(NR - 1) + 60.0], [DEC_X, 40.0, z]];
    particles(cv, cam, &path, 6, u * 1.6, 7.0, TEXT, r.addr);
}

/// A part's point, for labels, notes and leaders.
pub(super) fn at(p: Part, r: &Rig) -> V3 {
    let hz = row_z(NR - 1);
    match p {
        Part::Cells => [col_x(NC - 3), CELL_H, row_z(0)],
        Part::Decoder => [DEC_X, 40.0, -hz],
        Part::BitLine => [col_x(NC - 1) + 18.0, BL_Y, row_z(NR - 1) + 30.0],
        Part::SenseAmps => [col_x(NC - 1) + 40.0, 40.0, SA_Z],
        Part::ColDecoder => [col_x(0) - 4.0, 22.0, CD_Z + 18.0],
        Part::Io => [IO[0] + 40.0, 40.0, IO[2]],
        Part::OpenRow => [col_x(NC - 1) + 60.0, WL_Y, row_z(r.open_row()) - 18.0],
    }
}

pub(super) fn names(cv: &mut Canvas, cam: &Cam, r: &Rig) -> Vec<Rect> {
    let k = |i: usize| r.colour[i];
    let w = r.wl.iter().cloned().fold(0.0, f64::max);
    let any = r.read.iter().cloned().fold(0.0, f64::max);
    let lit = |x: f64| 0.62 + 0.38 * x.clamp(0.0, 1.0);
    let mut out = Vec::new();
    out.extend(label(cv, cam, at(Part::Cells, r), (0.03, -0.13), "cells (1T1C)", ORANGE, 0.85 * k(0)));
    out.extend(label(cv, cam, at(Part::Decoder, r), (-0.10, -0.08), "row decoder", TEXT, lit(r.addr + w) * k(1)));
    out.extend(label(cv, cam, at(Part::BitLine, r), (0.05, -0.08), "bit lines (columns)", CYAN, lit(r.share + r.sense) * k(2)));
    out.extend(label(cv, cam, at(Part::SenseAmps, r), (0.05, -0.03), "sense amps = row buffer", PURPLE, lit(r.sense) * k(3)));
    out.extend(label(cv, cam, at(Part::ColDecoder, r), (-0.14, 0.07), "column decoder", GREEN, lit(any) * k(4)));
    out.extend(label(cv, cam, at(Part::Io, r), (0.06, 0.03), "I/O", GREEN, lit(any) * k(5)));
    out.extend(label(cv, cam, at(Part::OpenRow, r), (0.05, -0.07), "open row (word line high)", ORANGE, w * k(1)));
    out
}
