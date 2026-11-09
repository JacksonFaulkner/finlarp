//! Substrate slab, capacitor plates, storage node and ground pillar.

use super::{push_box, CellAnim, CellParams};
use crate::Tri;

const SUBSTRATE: [f32; 3] = [0.20, 0.21, 0.24];
const STEEL: [f32; 3] = [0.20, 0.21, 0.24];
const PLATE: [f32; 3] = [0.82, 0.83, 0.80];
const PLATE_EDGE: [f32; 3] = [0.62, 0.63, 0.62];
const METAL: [f32; 3] = [0.55, 0.56, 0.60];
const NO_EMIT: [f32; 3] = [0.0, 0.0, 0.0];

/// Segments around each cylinder.
const SEG_PLATE: usize = 40;
const SEG_POST: usize = 20;

pub(super) fn build(p: &CellParams, _a: &CellAnim, m: &mut Vec<Tri>) {
    let h = p.substrate_half;
    let cx = p.cap_x;

    // substrate slab, top face at y = 0
    push_box(m, [-h, -p.substrate_thick, -h], [h, 0.0, h], SUBSTRATE, NO_EMIT);

    // ground pillar from the substrate up to the bottom plate
    push_post(m, [cx, 0.0, 0.0], [cx, p.bot_plate_y, 0.0], 12.0, SEG_POST, STEEL);

    // bottom plate, centred on bot_plate_y
    push_plate(m, cx, p.bot_plate_y, p);

    // top plate, centred on top_plate_y
    push_plate(m, cx, p.top_plate_y, p);

    // storage node from the top plate up to the channel
    push_post(m, [cx, p.top_plate_y, 0.0], [cx, p.ch_y, 0.0], 8.0, SEG_POST, METAL);
}

/// Plain round post, flat ends.
fn push_post(m: &mut Vec<Tri>, a: [f64; 3], b: [f64; 3], r: f64, seg: usize, col: [f32; 3]) {
    crate::push_tube(m, a, b, r, seg, col, NO_EMIT, true);
}

/// Capacitor plate: a light disc with a slightly darker, wider rim so its edge reads
/// as a plate of finite thickness from the orbit camera.
fn push_plate(m: &mut Vec<Tri>, cx: f64, y: f64, p: &CellParams) {
    let t = p.plate_t;
    let half = t * 0.5;
    // main disc
    crate::push_tube(
        m,
        [cx, y - half, 0.0],
        [cx, y + half, 0.0],
        p.plate_r,
        SEG_PLATE,
        PLATE,
        NO_EMIT,
        true,
    );
    // rim band around the outer edge, a touch wider and darker
    crate::push_tube(
        m,
        [cx, y - half, 0.0],
        [cx, y + half, 0.0],
        p.plate_r * 1.03,
        SEG_PLATE,
        PLATE_EDGE,
        NO_EMIT,
        false,
    );
}
