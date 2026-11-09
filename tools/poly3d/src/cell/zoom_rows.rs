//! Zoom c: refresh across the rows. Each row is a bar whose height is its charge.
//! Every bar sags until the pointer reaches it, flashes yellow while it is read,
//! and jumps back to full when rewritten. The time is periodic, so the loop is seamless.

use super::push_box;
use super::stage::{self, label, Clock, Shot};
use super::smooth;
use crate::{Cam, Canvas, Col, Tri};

const ROWS: usize = 16;
const PITCH: f64 = 50.0;
const WIDE: f64 = 32.0;
const LEN: f64 = 250.0;
const TALL: f64 = 250.0;
/// the pointer spends beats 0 and 1 walking the rows, then parks
const WALK: f64 = 2.0;
/// how long, in beats, a row stays read (yellow) and then rewriting
const READ_FOR: f64 = 0.10;
const WRITE_FOR: f64 = 0.10;
const SAG: f64 = 0.55;

const STALE: Col = [1.0, 0.66, 0.34];
const READ: Col = [0.95, 0.98, 0.40];
const DONE: Col = [0.31, 0.92, 0.50];
const POINTER: Col = [0.97, 0.97, 0.95];
const WINDOW: Col = [1.0, 0.72, 0.42];
const GLASS: Col = [0.62, 0.80, 0.92];
const TEXT: Col = [0.97, 0.97, 0.95];

fn row_z(r: f64) -> f64 {
    (r - (ROWS as f64 - 1.0) / 2.0) * PITCH
}

/// Where the pointer is, in rows: walks down, parks at the end, glides home late in beat 2.
fn pointer(c: &Clock) -> f64 {
    let last = ROWS as f64 - 1.0;
    let walk = (c.u() / WALK).clamp(0.0, 1.0) * last;
    walk * (1.0 - c.ramp(2, 0.72, 1.0))
}

/// The row at the pointer, for the shot that follows it in beat 1.
fn follow_z(c: &Clock) -> f64 {
    row_z(pointer(c))
}

pub(super) fn shot(c: &Clock) -> Shot {
    let keys = [
        Shot { target: [0.0, 70.0, 20.0], dist: 1500.0, yaw: 0.72, pitch: 0.40 },
        Shot { target: [-80.0, 90.0, follow_z(c)], dist: 1320.0, yaw: 0.90, pitch: 0.34 },
        Shot { target: [0.0, 70.0, 20.0], dist: 1500.0, yaw: 0.72, pitch: 0.40 },
    ];
    stage::shot_at(&keys, c.beat, c.local)
}

/// Beats since row `r` was last rewritten, wrapping once around the 3-beat loop.
fn age(r: usize, u: f64) -> f64 {
    let at = WALK * r as f64 / (ROWS - 1) as f64;
    (u - at).rem_euclid(3.0)
}

/// A row's charge and colour at `u`: sagging while stale, topped up after its turn.
fn row_state(r: usize, c: &Clock) -> (f64, Col, f64) {
    let u = c.u();
    let a = age(r, u);
    // read, then rewrite: charge climbs through the rewrite
    let write = smooth(READ_FOR, READ_FOR + WRITE_FOR, a);
    let since = (a - READ_FOR - WRITE_FOR).max(0.0) / (3.0 - READ_FOR - WRITE_FOR);
    let stale = 1.0 - SAG;
    let charge = stale + (1.0 - stale) * write * (1.0 - since);

    // the row turns green once rewritten this window; all go back to stale as the next begins
    let at = WALK * r as f64 / (ROWS - 1) as f64;
    let done = smooth(at + READ_FOR, at + READ_FOR + WRITE_FOR, u);
    let fresh = done * (1.0 - c.ramp(2, 0.80, 1.0));
    let mut col = stage::mix(STALE, DONE, fresh);
    // yellow flash while the row is being read
    let flash = smooth(0.0, 0.03, a) * (1.0 - smooth(READ_FOR, READ_FOR + WRITE_FOR, a));
    col = stage::mix(col, READ, flash);
    (charge, col, flash)
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let zero = [0.0f32; 3];
    let half = ROWS as f64 * PITCH / 2.0 + 16.0;
    push_box(m, [-LEN - 26.0, -14.0, -half], [LEN + 26.0, 0.0, half], [0.20, 0.21, 0.24], zero);
    for r in 0..ROWS {
        let (charge, col, flash) = row_state(r, c);
        let z = row_z(r as f64);
        let top = charge * TALL;
        // a sagging row also dims, so stale rows read at a glance
        let lit = 0.42 + 0.58 * ((charge - (1.0 - SAG)) / SAG).clamp(0.0, 1.0);
        let col = stage::scaled(col, lit + (1.0 - lit) * flash);
        let glow = stage::scaled(col, 0.22 + 0.4 * flash);
        push_box(m, [-LEN, 0.0, z - WIDE / 2.0], [LEN, top, z + WIDE / 2.0], col, glow);
    }

    // pointer: a block riding the near end of the rows, facing the camera
    let z = row_z(pointer(c));
    let x = LEN + 26.0;
    push_box(m, [x + 12.0, 0.0, z - 17.0], [x + 90.0, 44.0, z + 17.0], POINTER, stage::scaled(POINTER, 0.35));

    // refresh window: a bar along the front that fills across the loop
    let z = half + 44.0;
    let fill = (c.u() / 2.75).clamp(0.0, 1.0) * (1.0 - c.ramp(2, 0.80, 1.0));
    push_box(m, [-LEN - 26.0, 0.0, z], [LEN + 26.0, 8.0, z + 26.0], [0.26, 0.27, 0.32], zero);
    if fill > 0.001 {
        let x1 = -LEN - 26.0 + 2.0 * (LEN + 26.0) * fill;
        push_box(m, [-LEN - 26.0, 8.0, z + 2.0], [x1, 26.0, z + 24.0], WINDOW, stage::scaled(WINDOW, 0.4));
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let half = ROWS as f64 * PITCH / 2.0 + 16.0;
    stage::glass_box(cv, cam, [-LEN, 0.0, -half], [LEN, TALL, half], GLASS, 0.16);

    let p = pointer(c);
    let z = row_z(p);
    let walking = c.ramp(0, 0.0, 0.12) * (1.0 - c.ramp(2, 0.0, 0.2));
    label(cv, cam, [LEN + 90.0, 44.0, z], (0.03, -0.08), "refresh pointer", POINTER, 0.95 * walking);
    label(cv, cam, [-LEN, 8.0, half + 70.0], (-0.06, 0.07), "64 ms window", WINDOW, 0.95);
    label(cv, cam, [-LEN, TALL, -half], (-0.10, -0.07), "bar height = charge", TEXT, 0.9 * c.ramp(0, 0.0, 0.12) * (1.0 - c.ramp(1, 0.0, 0.2)));

    // in beat 1 the camera is close enough to name the two steps on the row itself
    let r = p.round() as usize;
    let a = age(r.min(ROWS - 1), c.u());
    let close = c.during(1, 0.05, 0.95);
    let row_top = [0.0, TALL, row_z(r as f64)];
    let reading = 1.0 - smooth(READ_FOR * 0.6, READ_FOR, a);
    label(cv, cam, row_top, (-0.20, -0.22), "read", READ, close * reading);
    label(cv, cam, row_top, (-0.20, -0.22), "rewrite", DONE, close * (1.0 - reading));
    label(cv, cam, [0.0, TALL, -half], (-0.10, -0.12), "all rows done in time", DONE, c.during(2, 0.1, 0.8));
}
