//! Voltage gauge tube (fill solid + glass wireframe) and cell footprint wireframe.

use super::{CellAnim, CellParams};
use crate::{Cam, Canvas, Col, Tri, V3};

const STEEL: Col = [0.20, 0.21, 0.24];
const CYAN: Col = [0.55, 0.91, 0.99];
const TICK: Col = [0.82, 0.83, 0.80];
const NO_EMIT: Col = [0.0, 0.0, 0.0];

const GLASS: Col = [0.62, 0.80, 0.92];
const GLASS_ALPHA: f32 = 0.28;
const GRID_ALPHA: f32 = 0.14;

/// Segments around each gauge ring.
const RING_SEG: usize = 64;
/// Meridians around the gauge.
const MERIDIANS: usize = 12;
/// Steel posts holding the glass.
const POSTS: usize = 6;

pub(super) fn build(p: &CellParams, a: &CellAnim, m: &mut Vec<Tri>) {
    let (gx, gz, gr, gh) = (p.gauge_x, p.gauge_z, p.gauge_r, p.gauge_h);

    // The glass is wireframe, so the steel is a cage: a base plate, six posts and
    // a top rim. A closed wall would hide the fill column inside it.
    let rim = (gr * 0.15).max(2.0);
    crate::push_tube(m, [gx, 0.0, gz], [gx, rim, gz], gr, 48, STEEL, NO_EMIT, true);
    crate::push_tube(m, [gx, gh - rim, gz], [gx, gh, gz], gr, 48, STEEL, NO_EMIT, false);
    let post = gr * 0.07;
    for k in 0..POSTS {
        let th = std::f64::consts::TAU * k as f64 / POSTS as f64;
        let (px, pz) = (gx + gr * th.cos(), gz + gr * th.sin());
        super::push_box(m, [px - post, 0.0, pz - post], [px + post, gh, pz + post], STEEL, NO_EMIT);
    }

    // fill column: the bit line voltage, from the base up
    let fill_h = a.bl.clamp(0.0, 1.0) * gh;
    if fill_h > 0.5 {
        let emit = [CYAN[0] * 0.3, CYAN[1] * 0.3, CYAN[2] * 0.3];
        crate::push_tube(m, [gx, 0.0, gz], [gx, fill_h, gz], gr * 0.7, 32, CYAN, emit, true);
    }

    // VDD/2 tick: a thin disc across the tube at half height
    let y = 0.5 * gh;
    crate::push_tube(
        m,
        [gx, y - 2.0, gz],
        [gx, y + 2.0, gz],
        gr * 1.12,
        RING_SEG / 2,
        TICK,
        NO_EMIT,
        true,
    );
}

pub(super) fn frame(cv: &mut Canvas, cam: &Cam, p: &CellParams, _a: &CellAnim) {
    gauge_glass(cv, cam, p);
    footprint(cv, cam, p);
}

/// Horizontal circle of radius `r` centred on `c`.
fn circle(cv: &mut Canvas, cam: &Cam, c: V3, r: f64, seg: usize, alpha: f32) {
    let mut prev: Option<V3> = None;
    for i in 0..=seg {
        let th = std::f64::consts::TAU * i as f64 / seg as f64;
        let pt = [c[0] + r * th.cos(), c[1], c[2] + r * th.sin()];
        if let Some(q) = prev {
            cv.line(cam, q, pt, GLASS, alpha);
        }
        prev = Some(pt);
    }
}

/// Glass tube around the voltage gauge: rings along the height, meridians up it,
/// and a cap with two diameters on top.
fn gauge_glass(cv: &mut Canvas, cam: &Cam, p: &CellParams) {
    let (gx, gz, gr, gh) = (p.gauge_x, p.gauge_z, p.gauge_r, p.gauge_h);
    const RINGS: usize = 5;
    for k in 0..=RINGS {
        let y = gh * k as f64 / RINGS as f64;
        circle(cv, cam, [gx, y, gz], gr, RING_SEG, GLASS_ALPHA);
    }
    for k in 0..MERIDIANS {
        let th = std::f64::consts::TAU * k as f64 / MERIDIANS as f64;
        let (c, s) = (th.cos(), th.sin());
        cv.line(
            cam,
            [gx + gr * c, 0.0, gz + gr * s],
            [gx + gr * c, gh, gz + gr * s],
            GLASS,
            GLASS_ALPHA,
        );
    }
    // top cap: two diameters across the circle
    cv.line(cam, [gx - gr, gh, gz], [gx + gr, gh, gz], GLASS, GLASS_ALPHA);
    cv.line(cam, [gx, gh, gz - gr], [gx, gh, gz + gr], GLASS, GLASS_ALPHA);
}

/// A light grid on the floor. It grounds the scene without boxing it in.
fn footprint(cv: &mut Canvas, cam: &Cam, p: &CellParams) {
    let s = p.substrate_half;
    let floor = 2.0;
    const DIV: usize = 4;
    for y in [floor] {
        for k in 1..DIV {
            let t = -s + 2.0 * s * k as f64 / DIV as f64;
            cv.line(cam, [-s, y, t], [s, y, t], GLASS, GRID_ALPHA);
            cv.line(cam, [t, y, -s], [t, y, s], GLASS, GRID_ALPHA);
        }
    }
}
