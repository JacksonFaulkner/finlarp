//! Access transistor, gate, word line, bit line, sense amp block.
//!
//! Everything here is a solid: the bit line and channel are tubes, the sense
//! amp and gate are boxes, the word line is a tube along z over the gate.
//! The word line level `a.wl` drives the look: the word line thickens and
//! turns orange, and the channel lights up from dim grey to pink.

use super::{push_box, CellAnim, CellParams};
use crate::{lerp, push_tube, Tri};

const CYAN: [f32; 3] = [0.55, 0.91, 0.99];
const PINK: [f32; 3] = [1.0, 0.47, 0.78];
const ORANGE: [f32; 3] = [1.0, 0.72, 0.42];
const GREY_METAL: [f32; 3] = [0.55, 0.56, 0.60];
const DARK: [f32; 3] = [0.20, 0.21, 0.24];
const DIM: [f32; 3] = [0.35, 0.36, 0.40];

fn mix(a: [f32; 3], b: [f32; 3], t: f32) -> [f32; 3] {
    [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ]
}

fn scale(c: [f32; 3], s: f32) -> [f32; 3] {
    [c[0] * s, c[1] * s, c[2] * s]
}

pub(super) fn build(p: &CellParams, a: &CellAnim, m: &mut Vec<Tri>) {
    let wl = a.wl.clamp(0.0, 1.0) as f32;
    let no_emit = [0.0f32; 3];

    // sense amp block, sits on the ground at x = bl_x
    push_box(
        m,
        [p.bl_x - p.sa_half_w, 0.0, -p.sa_half_d],
        [p.bl_x + p.sa_half_w, p.sa_h, p.sa_half_d],
        a.sa_rgb,
        scale(a.sa_rgb, 0.25),
    );

    // bit line: vertical pillar from the top of the sense amp up to the channel
    let bl_r = 8.0;
    push_tube(
        m,
        [p.bl_x, p.sa_h - 4.0, 0.0],
        [p.bl_x, p.ch_y, 0.0],
        bl_r,
        20,
        CYAN,
        no_emit,
        true,
    );

    // access transistor channel: runs along x from the bit line to the storage node
    let ch_r = 8.0;
    let ch_base = mix(DIM, PINK, 0.45 + 0.55 * wl);
    let ch_emit = scale(PINK, 0.45 * wl);
    push_tube(
        m,
        [p.bl_x, p.ch_y, 0.0],
        [p.cap_x, p.ch_y, 0.0],
        ch_r,
        20,
        ch_base,
        ch_emit,
        true,
    );

    // gate: dark block over the channel, rising to the word line height
    let gate_bot = p.ch_y - ch_r;
    push_box(
        m,
        [p.gate_x - p.gate_half_w, gate_bot, -46.0],
        [p.gate_x + p.gate_half_w, p.wl_y, 46.0],
        DARK,
        no_emit,
    );

    // word line: rod along z over the gate, thicker and orange when high
    let wl_rad = lerp(p.wl_r * 0.6, p.wl_r * 1.4, wl as f64);
    push_tube(
        m,
        [p.gate_x, p.wl_y, -200.0],
        [p.gate_x, p.wl_y, 200.0],
        wl_rad,
        20,
        mix(GREY_METAL, ORANGE, wl),
        scale(ORANGE, wl * 0.4),
        true,
    );
}
