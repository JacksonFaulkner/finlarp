//! Section 2: the parts. One assembled cell. Each beat puts one part in the spotlight:
//! it takes its colour and glows, the rest go grey, and the camera moves to it.

use super::push_box;
use super::stage::{self, label, particles, spotlight, Clock, Shot, CYAN, GREEN, NO_GLOW, ORANGE, PINK, PLATE, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri};

pub(super) const BEATS: usize = 6;
const WL: usize = 0;
const FET: usize = 1;
const CAP: usize = 2;
const BL: usize = 3;
const SA: usize = 4;
const PRE: usize = 5;

const BL_X: f64 = -210.0;
const GATE_X: f64 = -20.0;
const CAP_X: f64 = 190.0;
const CH_Y: f64 = 400.0;
const WL_Y: f64 = 500.0;
const TOP: f64 = 300.0;
const BOT: f64 = 220.0;
const R: f64 = 110.0;
const PRE_Y: f64 = 250.0;

const SHOTS: [Shot; BEATS] = [
    Shot { target: [GATE_X, WL_Y - 30.0, 0.0], dist: 900.0, yaw: 0.75, pitch: 0.30 },
    Shot { target: [GATE_X, CH_Y + 10.0, 0.0], dist: 760.0, yaw: 0.25, pitch: 0.22 },
    Shot { target: [CAP_X, 260.0, 0.0], dist: 760.0, yaw: 0.35, pitch: 0.30 },
    Shot { target: [BL_X, 260.0, 0.0], dist: 1040.0, yaw: -0.25, pitch: 0.18 },
    Shot { target: [BL_X, 90.0, 0.0], dist: 760.0, yaw: -0.10, pitch: 0.30 },
    Shot { target: [BL_X - 60.0, PRE_Y, 0.0], dist: 760.0, yaw: -0.45, pitch: 0.22 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn part(c: &Clock, i: usize, col: Col) -> (Col, Col) {
    let k = spotlight(c, i, BEATS);
    (stage::mix(QUIET, col, k), stage::scaled(col, 0.4 * k))
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    push_box(m, [-520.0, -24.0, -320.0], [420.0, 0.0, 320.0], STEEL, NO_GLOW);

    let (col, glow) = part(c, WL, ORANGE);
    crate::push_tube(m, [GATE_X, WL_Y, -280.0], [GATE_X, WL_Y, 280.0], 13.0, 16, col, glow, true);

    let (col, glow) = part(c, FET, PINK);
    crate::push_tube(m, [BL_X, CH_Y, 0.0], [CAP_X, CH_Y, 0.0], 11.0, 14, col, glow, false);
    push_box(m, [GATE_X - 26.0, CH_Y - 16.0, -46.0], [GATE_X + 26.0, WL_Y, 46.0], stage::mix(STEEL, col, 0.45), glow);

    let (col, glow) = part(c, CAP, PLATE);
    let k = spotlight(c, CAP, BEATS);
    for y in [TOP, BOT] {
        crate::push_tube(m, [CAP_X, y - 6.0, 0.0], [CAP_X, y + 6.0, 0.0], R, 48, col, stage::scaled(glow, 0.3), true);
    }
    crate::push_tube(m, [CAP_X, TOP, 0.0], [CAP_X, CH_Y, 0.0], 9.0, 12, col, NO_GLOW, false);
    crate::push_tube(m, [CAP_X, 0.0, 0.0], [CAP_X, BOT, 0.0], 9.0, 12, col, NO_GLOW, false);
    let charge = stage::mix(stage::mix(QUIET, ORANGE, 0.45), ORANGE, k);
    crate::push_tube(m, [CAP_X, BOT + 14.0, 0.0], [CAP_X, TOP - 14.0, 0.0], R * 0.8, 32, charge, stage::scaled(ORANGE, 0.1 + 0.4 * k), false);

    let (col, glow) = part(c, BL, CYAN);
    crate::push_tube(m, [BL_X, 110.0, 0.0], [BL_X, CH_Y + 60.0, 0.0], 11.0, 14, col, glow, true);

    let (col, glow) = part(c, SA, PURPLE);
    push_box(m, [BL_X - 90.0, 0.0, -70.0], [BL_X + 90.0, 110.0, 70.0], col, glow);

    let (col, glow) = part(c, PRE, GREEN);
    crate::push_tube(m, [BL_X - 90.0, PRE_Y, 0.0], [BL_X, PRE_Y, 0.0], 7.0, 10, col, glow, false);
    push_box(m, [BL_X - 170.0, PRE_Y - 34.0, -34.0], [BL_X - 90.0, PRE_Y + 34.0, 34.0], col, glow);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let u = c.u();
    // what each part does, shown in motion while it is in the spotlight
    let s = |i: usize| spotlight(c, i, BEATS);
    particles(cv, cam, &[[GATE_X, WL_Y + 20.0, -280.0], [GATE_X, WL_Y + 20.0, 280.0]], 7, u * 0.9, 10.0, ORANGE, s(WL));
    particles(cv, cam, &[[CAP_X, CH_Y + 18.0, 0.0], [BL_X, CH_Y + 18.0, 0.0]], 6, u * 1.2, 9.0, TEXT, s(FET));
    particles(cv, cam, &[[BL_X + 18.0, CH_Y + 60.0, 0.0], [BL_X + 18.0, 110.0, 0.0]], 6, u * 1.2, 9.0, TEXT, s(BL));
    particles(cv, cam, &[[BL_X - 170.0, PRE_Y + 16.0, 0.0], [BL_X, PRE_Y + 16.0, 0.0]], 5, u * 1.2, 9.0, GREEN, s(PRE));

    // the name always, the job in the spotlight
    let names: [(usize, [f64; 3], (f64, f64), &str, &str, Col); BEATS] = [
        (WL, [GATE_X, WL_Y, -280.0], (0.04, -0.09), "word line", "row select: high turns on its row", ORANGE),
        (FET, [(GATE_X + CAP_X) / 2.0, CH_Y, 0.0], (0.0, -0.16), "access transistor", "switch: bit line to storage node", PINK),
        (CAP, [CAP_X + R, TOP, 0.0], (-0.10, -0.12), "storage capacitor", "holds the bit as charge", TEXT),
        (BL, [BL_X, CH_Y + 60.0, 0.0], (-0.04, -0.08), "bit line", "column wire, at VDD/2 before a read", CYAN),
        (SA, [BL_X, 0.0, 70.0], (-0.10, 0.08), "sense amp", "latches to a full rail", PURPLE),
        (PRE, [BL_X - 130.0, PRE_Y - 34.0, 34.0], (-0.12, 0.09), "precharge", "holds the bit line at VDD/2", GREEN),
    ];
    for (i, at, off, name, _, col) in names {
        label(cv, cam, at, off, name, col, s(i));
    }
    let (w, h) = (cv.w as f64, cv.h as f64);
    for (i, _, _, _, job, col) in names {
        stage::text(cv, (w * 0.04) as i64, (h * 0.92) as i64, job, col, s(i));
    }
}
