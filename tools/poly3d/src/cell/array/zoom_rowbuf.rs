//! Zoom a: the row buffer. Close on the sense amp stripe: a row opens, every cell in
//! it nudges its bit line, and the sense amps latch the whole row at once. Reads then
//! come straight from the latches, and precharge empties them.

use super::super::stage::{self, label, text, Clock, Shot, CYAN, ORANGE, PURPLE};
use super::rig::{self, Part, Rig, NC};
use crate::{Cam, Canvas, Tri};

const ROW: usize = 5;

const SHOTS: [Shot; 3] = [
    Shot { target: [0.0, 40.0, 220.0], dist: 1150.0, yaw: -0.25, pitch: 0.45 },
    Shot { target: [60.0, 40.0, 290.0], dist: 1050.0, yaw: 0.35, pitch: 0.55 },
    Shot { target: [0.0, 40.0, 160.0], dist: 1300.0, yaw: 0.10, pitch: 0.62 },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

fn rig_at(c: &Clock) -> Rig {
    let mut r = Rig { u: c.u() * 1.6, ..Rig::default() };
    r.wl[ROW] = c.ramp(0, 0.05, 0.3) * (1.0 - c.ramp(2, 0.55, 0.8));
    r.share = c.ramp(0, 0.3, 0.7) * (1.0 - c.ramp(2, 0.7, 0.95));
    r.sense = c.ramp(0, 0.55, 0.95) * (1.0 - c.ramp(2, 0.7, 0.95));
    for col in 3..8 {
        r.read[col] = c.during(1, 0.2, 0.9);
    }
    r
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    rig::solids(&rig_at(c), m);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let r = rig_at(c);
    rig::overlay(cv, cam, &r);
    label(cv, cam, rig::at(Part::SenseAmps, &r), (0.05, -0.05), "sense amps: one latch per bit line", PURPLE, 0.9);
    label(cv, cam, rig::at(Part::OpenRow, &r), (0.05, -0.08), "open row", ORANGE, r.wl[ROW]);
    label(cv, cam, [rig::col_x(NC / 2), 40.0, rig::SA_Z + 30.0], (-0.20, 0.10), "the whole row, latched", ORANGE, c.during(1, 0.0, 0.9));
    label(cv, cam, rig::at(Part::ColDecoder, &r), (-0.10, 0.10), "reads come from the latches", stage::GREEN, c.during(1, 0.2, 0.9));
    label(cv, cam, [rig::col_x(0), rig::BL_Y, rig::row_z(ROW)], (-0.16, -0.08), "cells restored", CYAN, c.during(2, 0.0, 0.6));
    let (w, h) = (cv.w as f64, cv.h as f64);
    text(cv, (w * 0.04) as i64, (h * 0.04) as i64, "row buffer: 1 KB per x8 DDR4 chip", stage::TEXT, 0.9);
    text(cv, (w * 0.04) as i64, (h * 0.92) as i64, "precharge empties it for the next row", CYAN, c.during(2, 0.5, 1.0));
}
