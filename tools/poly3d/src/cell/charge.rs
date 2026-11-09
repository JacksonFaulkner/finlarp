//! Charge spheres in the capacitor gap (solid), leak and read/restore streams (overlays).

use super::stage::{disc_lattice, mix, particles, scaled, slot_fill};
use super::{push_sphere, CellAnim, CellParams};
use crate::{Cam, Canvas, Tri};

/// lit charge
const ORANGE: [f32; 3] = [1.0, 0.72, 0.42];
/// empty slot
const UNLIT: [f32; 3] = [0.30, 0.31, 0.35];
/// read stream: cell up to the bit line
const READ: [f32; 3] = [0.55, 0.91, 0.99];
/// restore stream: bit line back into the cell (violet, so it never reads as charge)
const RESTORE: [f32; 3] = [0.80, 0.60, 1.00];
/// leakage: deeper orange than the charge so it reads as a stream, not as stored charge
const LEAK: [f32; 3] = [1.00, 0.52, 0.22];

const SPHERE_SEG: usize = 8;

pub(super) fn build(p: &CellParams, a: &CellAnim, m: &mut Vec<Tri>) {
    let y = 0.5 * (p.bot_plate_y + p.top_plate_y);
    let pts = disc_lattice(p.plate_r - 18.0, 30.0, &[-15.0, 15.0]);
    let n = pts.len();
    let level = a.cap.clamp(0.0, 1.0);
    for (rank, q) in pts.iter().enumerate() {
        // slots light and dim gradually, so charge never pops
        let f = slot_fill(rank, n, level);
        let col = mix(UNLIT, ORANGE, f);
        let c = [p.cap_x + q[0], y + q[1], q[2]];
        push_sphere(m, c, 5.0 + 5.0 * f, SPHERE_SEG, col, scaled(ORANGE, 0.5 * f));
    }
}

pub(super) fn flows(cv: &mut Canvas, cam: &Cam, p: &CellParams, a: &CellAnim) {
    // read: storage node up to the channel height, across to the bit line, down to the sense amp
    let path = [
        [p.cap_x, p.top_plate_y, 0.0],
        [p.cap_x, p.ch_y, 0.0],
        [p.bl_x, p.ch_y, 0.0],
        [p.bl_x, p.sa_h, 0.0],
    ];
    particles(cv, cam, &path, 12, a.phase, 9.0, READ, a.read);

    // restore: the same path walked backwards, from the bit line into the cell
    let mut back = path;
    back.reverse();
    particles(cv, cam, &back, 12, a.phase, 9.0, RESTORE, a.restore);

    // leakage: out of both plate edges, sideways and a little down, fading as it goes
    for side in [-1.0, 1.0] {
        for (y, zdir) in [(p.bot_plate_y, 1.0), (p.top_plate_y, -1.0)] {
            let x0 = p.cap_x + side * p.plate_r;
            let start = [x0, y, 0.0];
            let end = [x0 + side * 150.0, y - 50.0, zdir * 120.0];
            let offset = 0.25 * (side + zdir);
            particles(cv, cam, &[start, end], 4, a.phase + offset, 8.0, LEAK, a.leak);
        }
    }
}
