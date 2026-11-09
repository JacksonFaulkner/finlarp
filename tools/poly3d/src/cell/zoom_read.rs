//! Zoom b: a read, as two tanks joined by the access transistor. The cell is a small
//! tank and the bit line a wide one, so when the switch opens the levels meet close
//! to where the bit line already was. That small bump is the signal, and the trace
//! under the tanks draws it. The sense amp then drives both to the full rail.

use super::push_box;
use super::stage::{self, label, particles, screen_line, text, Clock, Shot};
use crate::{Cam, Canvas, Col, Tri};

const H: f64 = 360.0;
const CELL_X: f64 = -430.0;
const CELL_R: f64 = 62.0;
const BL_X: f64 = 170.0;
const BL_R: f64 = 170.0;
const PIPE_Y: f64 = 30.0;
const GATE_X: f64 = -130.0;
const SA_X: f64 = 500.0;

const CELL: Col = [1.0, 0.72, 0.42];
const LINE: Col = [0.55, 0.91, 0.99];
const OFF: Col = [0.34, 0.35, 0.40];
const PINK: Col = [1.0, 0.47, 0.78];
const AMP_IDLE: Col = [0.35, 0.36, 0.42];
const AMP_ON: Col = [0.74, 0.58, 0.98];
const GLASS: Col = [0.62, 0.80, 0.92];
const TEXT: Col = [0.97, 0.97, 0.95];
const DIM: Col = [0.45, 0.50, 0.66];

const SHOTS: [Shot; 3] = [
    Shot { target: [-10.0, 20.0, 0.0], dist: 1500.0, yaw: 0.10, pitch: 0.20 },
    Shot { target: [30.0, 20.0, 0.0], dist: 1500.0, yaw: -0.08, pitch: 0.20 },
    Shot { target: [10.0, 20.0, 0.0], dist: 1500.0, yaw: 0.02, pitch: 0.22 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// The access transistor: opens at the start of the read, closes at the start of precharge.
fn switch(c: &Clock) -> f64 {
    c.ramp(0, 0.0, 0.14) * (1.0 - c.ramp(2, 0.0, 0.3))
}

/// Bit line level: VDD/2, a small bump from sharing, driven to VDD, precharged back.
fn line_level(c: &Clock) -> f64 {
    0.5 + 0.07 * c.ramp(0, 0.14, 0.85) + 0.43 * c.ramp(1, 0.08, 0.8) - 0.5 * c.ramp(2, 0.32, 0.92)
}

/// Cell level: full, falls to meet the bit line, restored with it, then stays full.
fn cell_level(c: &Clock) -> f64 {
    1.0 - 0.43 * c.ramp(0, 0.14, 0.85) + 0.43 * c.ramp(1, 0.08, 0.8)
}

/// Bit line level at loop position `u`, for drawing the trace behind the current time.
fn line_at(u: f64) -> f64 {
    let beat = (u.floor() as usize).min(2);
    line_level(&Clock { beat, local: u - beat as f64 })
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let zero = [0.0f32; 3];
    let sw = switch(c);
    let amp = c.during(1, 0.0, 1.0);

    // tank floors and the levels inside them
    let steel = [0.22, 0.23, 0.27];
    for (x, r) in [(CELL_X, CELL_R), (BL_X, BL_R)] {
        crate::push_tube(m, [x, -10.0, 0.0], [x, 0.0, 0.0], r + 8.0, 48, steel, zero, true);
    }
    let cell = cell_level(c) * H;
    crate::push_tube(m, [CELL_X, 0.0, 0.0], [CELL_X, cell, 0.0], CELL_R, 32, CELL, stage::scaled(CELL, 0.3), true);
    let line = line_level(c) * H;
    crate::push_tube(m, [BL_X, 0.0, 0.0], [BL_X, line, 0.0], BL_R, 48, LINE, stage::scaled(LINE, 0.18), true);

    // the pipe between them, and the transistor gate on it
    let pipe = stage::mix(OFF, PINK, sw);
    let glow = stage::scaled(PINK, 0.45 * sw);
    crate::push_tube(m, [CELL_X + CELL_R, PIPE_Y, 0.0], [BL_X - BL_R, PIPE_Y, 0.0], 11.0 + 5.0 * sw, 12, pipe, glow, false);
    // the gate is a valve on the pipe: down blocks it, the word line lifts it clear
    let lift = 66.0 * sw;
    crate::push_tube(m, [GATE_X, PIPE_Y + lift, 0.0], [GATE_X, PIPE_Y + 210.0, 0.0], 6.0, 8, OFF, zero, false);
    push_box(
        m,
        [GATE_X - 26.0, PIPE_Y - 24.0 + lift, -30.0],
        [GATE_X + 26.0, PIPE_Y + 34.0 + lift, 30.0],
        stage::mix(OFF, [1.0, 0.72, 0.42], sw),
        stage::scaled([1.0, 0.72, 0.42], 0.3 * sw),
    );

    // sense amp on the far side of the bit line
    let amp_col = stage::mix(AMP_IDLE, AMP_ON, amp);
    crate::push_tube(m, [BL_X + BL_R, PIPE_Y, 0.0], [SA_X - 70.0, PIPE_Y, 0.0], 11.0, 12, OFF, zero, false);
    push_box(m, [SA_X - 70.0, 0.0, -60.0], [SA_X + 70.0, 110.0, 60.0], amp_col, stage::scaled(AMP_ON, 0.3 * amp));

    // VDD/2 mark around the bit line tank
    let y = 0.5 * H;
    crate::push_tube(m, [BL_X, y - 2.0, 0.0], [BL_X, y + 2.0, 0.0], BL_R + 12.0, 48, [0.85, 0.86, 0.84], zero, false);
}

/// The voltage trace along the foot of the frame, drawn up to the current time.
fn trace(cv: &mut Canvas, c: &Clock) {
    let (w, h) = (cv.w as f64, cv.h as f64);
    let fade = 1.0 - c.ramp(2, 0.86, 1.0);
    let (x0, x1) = (w * 0.17, w * 0.94);
    let (top, bot) = (h * 0.76, h * 0.96);
    let y_of = |v: f64| bot + (top - bot) * v;
    for (v, name) in [(1.0, "VDD"), (0.5, "VDD/2")] {
        screen_line(cv, (x0, y_of(v)), (x1, y_of(v)), DIM, 0.5, 1);
        text(cv, (w * 0.03) as i64, y_of(v) as i64 - 6, name, DIM, 0.95);
    }
    let weight = ((h / 300.0).round() as i64).max(1);
    let u = c.u();
    let n = 180;
    let at = |k: usize| {
        let s = 3.0 * k as f64 / n as f64;
        (x0 + (x1 - x0) * s / 3.0, y_of(line_at(s)))
    };
    for k in 0..n {
        if 3.0 * (k as f64 + 1.0) / n as f64 > u {
            break;
        }
        screen_line(cv, at(k), at(k + 1), LINE, fade, weight);
    }
    text(cv, (x0 + 6.0) as i64, (top - h * 0.045) as i64, "bit line voltage", LINE, 0.95);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    stage::glass_cyl(cv, cam, [CELL_X, 0.0, 0.0], CELL_R, H, GLASS, 0.30);
    stage::glass_cyl(cv, cam, [BL_X, 0.0, 0.0], BL_R, H, GLASS, 0.26);

    let u = c.u();
    let (a, b) = ([CELL_X + CELL_R, PIPE_Y, 0.0], [BL_X - BL_R, PIPE_Y, 0.0]);
    particles(cv, cam, &[a, b], 7, u * 1.6, 12.0, CELL, c.during(0, 0.12, 0.9));
    particles(cv, cam, &[b, a], 7, u * 1.6, 12.0, LINE, c.during(1, 0.08, 0.85));
    let amp_in = [[SA_X - 70.0, PIPE_Y, 0.0], [BL_X + BL_R, PIPE_Y, 0.0]];
    particles(cv, cam, &amp_in, 5, u * 1.6, 12.0, [0.74, 0.58, 0.98], c.during(1, 0.08, 0.85));

    label(cv, cam, [CELL_X, H, 0.0], (-0.06, -0.08), "cell: small", CELL, 0.95);
    label(cv, cam, [BL_X, H, 0.0], (-0.12, -0.08), "bit line: much bigger", LINE, 0.95);
    let sw = switch(c);
    label(cv, cam, [GATE_X, PIPE_Y - 24.0, 30.0], (-0.12, 0.09), "transistor off", TEXT, 0.9 * (1.0 - sw));
    label(cv, cam, [GATE_X, PIPE_Y - 8.0, 16.0], (-0.30, 0.09), "word line high: open", PINK, sw);
    label(cv, cam, [BL_X + BL_R + 12.0, 0.5 * H, 0.0], (0.03, -0.03), "VDD/2", TEXT, 0.9);
    let amp = c.during(1, 0.0, 1.0);
    label(cv, cam, [SA_X, 0.0, 60.0], (-0.10, 0.07), "sense amp", TEXT, 0.9 - 0.9 * amp);
    label(cv, cam, [SA_X, 0.0, 60.0], (-0.16, 0.07), "driving to VDD", AMP_ON, amp);
    trace(cv, c);
}
