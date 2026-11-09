//! Zoom d: redundancy. Test walks the rows and finds a bad cell. A laser blows a fuse
//! in the fuse bank, which stores the bad row's address. From then on the decoder
//! sends that address to a spare row at the edge of the array. The next die comes in
//! with the fuses whole, closing the loop.

use super::super::push_box;
use super::super::stage::{self, label, particles, text, Clock, Shot, GREEN, METAL, NO_GLOW, ORANGE, PINK, QUIET, STEEL, TEXT, YELLOW};
use crate::{Cam, Canvas, Tri};

const ROWS: usize = 8;
const SPARES: usize = 2;
const BAD: usize = 3;
const BAD_COL: usize = 6;
const COLS: usize = 12;
const P: f64 = 50.0;
const FUSE_X: f64 = -420.0;
const DEC_X: f64 = -330.0;

fn rz(r: usize) -> f64 {
    (r as f64 - (ROWS + SPARES) as f64 / 2.0) * P
}

fn cx(c: usize) -> f64 {
    (c as f64 - (COLS as f64 - 1.0) / 2.0) * P
}

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 20.0, 0.0], dist: 1200.0, yaw: 0.30, pitch: 0.70 },
    Shot { target: [-330.0, 20.0, 0.0], dist: 950.0, yaw: -0.40, pitch: 0.55 },
    Shot { target: [-100.0, 20.0, 60.0], dist: 1250.0, yaw: -0.15, pitch: 0.70 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// Fault found (beat 0), fuse blown (beat 1); both reset at the loop's end.
fn found(c: &Clock) -> f64 {
    c.ramp(0, 0.45, 0.6) * (1.0 - c.ramp(2, 0.85, 0.99))
}

fn blown(c: &Clock) -> f64 {
    c.ramp(1, 0.4, 0.65) * (1.0 - c.ramp(2, 0.85, 0.99))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [FUSE_X - 60.0, -20.0, rz(0) - 60.0], [cx(COLS - 1) + 60.0, 0.0, rz(ROWS + SPARES - 1) + 60.0], STEEL, NO_GLOW);
    let f = found(c);
    let b = blown(c);
    let remap = c.during(2, 0.05, 0.85);
    for r in 0..ROWS + SPARES {
        let spare = r >= ROWS;
        let z = rz(r);
        for col in 0..COLS {
            let mut colr = if spare { stage::mix(QUIET, GREEN, 0.25 + 0.6 * b) } else { stage::mix(QUIET, ORANGE, 0.6) };
            let mut glow = [0.0f32; 3];
            if r == BAD {
                colr = stage::mix(colr, QUIET, 0.6 * b);
            }
            if r == BAD && col == BAD_COL {
                colr = stage::mix(colr, PINK, f);
                glow = stage::scaled(PINK, 0.5 * f);
            }
            if spare && r == ROWS {
                glow = stage::scaled(GREEN, 0.3 * remap);
            }
            crate::push_tube(m, [cx(col), 0.0, z], [cx(col), 26.0, z], 10.0, 10, colr, glow, true);
        }
        push_box(m, [DEC_X - 24.0, 0.0, z - 16.0], [DEC_X + 24.0, 24.0, z + 16.0], METAL, NO_GLOW);
    }
    // fuse bank: a link per address bit; one gap where the laser cut
    for k in 0..6 {
        let z = rz(1) + k as f64 * 60.0;
        let cut = if k == 2 { b } else { 0.0 };
        let col = stage::mix(stage::mix(METAL, YELLOW, 0.3), [0.1, 0.1, 0.12], cut);
        push_box(m, [FUSE_X - 30.0, 0.0, z - 8.0], [FUSE_X - 30.0 + 60.0 * (1.0 - 0.6 * cut), 12.0, z + 8.0], col, NO_GLOW);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let u = c.u();
    // test: a probe walks the rows
    let probe = c.during(0, 0.0, 0.7);
    let s = c.local.min(0.6) / 0.6;
    let at = (s * BAD as f64).min(BAD as f64);
    let z = rz(0) + at * P;
    if probe > 0.01 {
        cv.line(cam, [cx(0) - 30.0, 30.0, z], [cx(COLS - 1) + 30.0, 30.0, z], YELLOW, (0.8 * probe) as f32);
    }
    let f = found(c);
    label(cv, cam, [cx(BAD_COL), 26.0, rz(BAD)], (0.06, -0.10), "test finds a bad cell", PINK, f * (1.0 - c.during(2, 0.0, 1.0)));
    // laser onto the fuse
    let laser = c.during(1, 0.2, 0.7);
    let fz = rz(1) + 2.0 * 60.0;
    if laser > 0.01 {
        cv.overlay(cam, [FUSE_X, 500.0, fz], [FUSE_X, 12.0, fz], PINK, (0.9 * laser) as f32);
    }
    label(cv, cam, [FUSE_X, 12.0, rz(1)], (-0.14, -0.06), "fuse bank", YELLOW, 0.8);
    label(cv, cam, [FUSE_X, 12.0, fz], (-0.16, 0.08), "laser blows a fuse", PINK, laser);
    label(cv, cam, [cx(COLS - 1), 26.0, rz(ROWS)], (0.04, 0.06), "spare rows", GREEN, 0.75);
    // remap: the bad row's address now lands on the spare
    let remap = c.during(2, 0.05, 0.85);
    let path = [[DEC_X - 120.0, 30.0, rz(BAD)], [DEC_X, 30.0, rz(BAD)], [DEC_X + 40.0, 30.0, rz(ROWS)], [cx(COLS - 1), 30.0, rz(ROWS)]];
    particles(cv, cam, &path, 7, u * 1.4, 7.0, GREEN, remap);
    label(cv, cam, [DEC_X, 24.0, rz(BAD)], (-0.10, 0.12), "address of the bad row", TEXT, remap);
    label(cv, cam, [cx(COLS / 2), 30.0, rz(ROWS)], (0.0, 0.10), "now served by the spare", GREEN, remap);
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "spare rows and columns repair defects", TEXT, 0.9);
}
