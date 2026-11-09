//! The chip every BANK scene shares: 16 banks in 4 bank groups (DDR4 x8), a command
//! bus running in from the controller, a data bus along the spine to the I/O. Each
//! bank is a small array with its own row buffer stripe, so each can hold its own
//! open row. A `Rig` is the state at one instant.
//!
//! Geometry, schematic units, Y up: groups sit in the four quadrants, banks 2 x 2 in
//! each. The data bus runs along x at z = 0, the command bus along z at x = 0, the
//! controller pad at the back (z < 0), the I/O pads at the front.

use super::super::push_box;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri, V3};

pub(super) const N: usize = 16;
const BW: f64 = 70.0;
const BD: f64 = 55.0;
const H: f64 = 24.0;
pub(super) const CTRL: V3 = [0.0, 20.0, -470.0];
pub(super) const IO: V3 = [0.0, 20.0, 470.0];

/// Centre of bank `i` (group i / 4, bank i % 4).
pub(super) fn centre(i: usize) -> V3 {
    let (g, b) = (i / 4, i % 4);
    let gx = if g % 2 == 0 { -270.0 } else { 270.0 };
    let gz = if g < 2 { -200.0 } else { 200.0 };
    let bx = if b % 2 == 0 { -88.0 } else { 88.0 };
    let bz = if b < 2 { -72.0 } else { 72.0 };
    [gx + bx, 0.0, gz + bz]
}

/// The side of bank `i` that faces the data bus (row buffer side), as a z sign.
fn spine_side(i: usize) -> f64 {
    if centre(i)[2] < 0.0 { 1.0 } else { -1.0 }
}

/// Group centre.
pub(super) fn group_centre(g: usize) -> V3 {
    let c = centre(g * 4);
    let d = centre(g * 4 + 3);
    [(c[0] + d[0]) / 2.0, 0.0, (c[2] + d[2]) / 2.0]
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum Part {
    Bank(usize),
    Group(usize),
    CmdBus,
    DataBus,
    Io,
    Ctrl,
}

#[derive(Clone, Copy, Debug)]
pub(super) struct Rig {
    /// row open in each bank, 0..1
    pub open: [f64; N],
    /// where the open row sits across the bank, 0..1
    pub row: [f64; N],
    /// data leaving each bank for the I/O
    pub read: [f64; N],
    /// precharging, 0..1 (pink)
    pub pre: [f64; N],
    /// refreshing, 0..1 (cyan)
    pub refresh: [f64; N],
    /// a command travelling to each bank
    pub cmd: [f64; N],
    /// a bank blocked (waiting on a rule), 0..1 (red frame)
    pub wait: [f64; N],
    /// colour kept per part: banks, groups, command bus, data bus, I/O, controller
    pub colour: [f64; 6],
    pub u: f64,
}

impl Default for Rig {
    fn default() -> Self {
        Rig {
            open: [0.0; N],
            row: [0.5; N],
            read: [0.0; N],
            pre: [0.0; N],
            refresh: [0.0; N],
            cmd: [0.0; N],
            wait: [0.0; N],
            colour: [1.0; 6],
            u: 0.0,
        }
    }
}

fn tint(r: &Rig, i: usize, col: Col) -> Col {
    stage::mix(QUIET, col, r.colour[i])
}

pub(super) fn solids(r: &Rig, m: &mut Vec<Tri>) {
    push_box(m, [-470.0, -24.0, -520.0], [470.0, 0.0, 520.0], STEEL, NO_GLOW);
    for i in 0..N {
        let [x, _, z] = centre(i);
        let o = r.open[i];
        let mut body = stage::mix(stage::mix(QUIET, ORANGE, 0.35), ORANGE, 0.5 * o);
        body = stage::mix(body, PINK, r.pre[i]);
        body = stage::mix(body, CYAN, r.refresh[i]);
        let glow = stage::scaled(body, 0.12 * (o + r.pre[i] + r.refresh[i]).min(1.0) * r.colour[0]);
        push_box(m, [x - BW, 0.0, z - BD], [x + BW, H, z + BD], tint(r, 0, body), glow);
        // row buffer stripe on the spine side
        let s = spine_side(i);
        let zs = z + s * (BD + 8.0);
        let rb = stage::mix(PURPLE, ORANGE, 0.6 * o);
        push_box(m, [x - BW, 0.0, zs - 7.0], [x + BW, H * 0.7 + 8.0 * o, zs + 7.0], tint(r, 0, rb), stage::scaled(PURPLE, 0.25 * o * r.colour[0]));
        // the open row: a bright line across the bank
        if o > 0.01 {
            let rz = z - BD + 10.0 + (2.0 * BD - 20.0) * r.row[i];
            crate::push_tube(m, [x - BW + 6.0, H + 3.0, rz], [x + BW - 6.0, H + 3.0, rz], 3.0 + 3.0 * o, 8, ORANGE, stage::scaled(ORANGE, 0.5 * o), false);
        }
    }
    // buses: data along the spine, command in from the controller
    let data: f64 = r.read.iter().cloned().fold(0.0, f64::max);
    push_box(m, [-460.0, 0.0, -10.0], [460.0, 6.0, 10.0], tint(r, 3, stage::mix(METAL, GREEN, 0.25 + 0.6 * data)), stage::scaled(GREEN, 0.2 * data * r.colour[3]));
    push_box(m, [-10.0, 0.0, -460.0], [10.0, 8.0, 460.0], tint(r, 2, stage::mix(METAL, TEXT, 0.3)), NO_GLOW);
    push_box(m, [CTRL[0] - 60.0, 0.0, CTRL[2] - 30.0], [CTRL[0] + 60.0, 40.0, CTRL[2] + 30.0], tint(r, 5, stage::mix(METAL, TEXT, 0.4)), NO_GLOW);
    push_box(m, [IO[0] - 90.0, 0.0, IO[2] - 30.0], [IO[0] + 90.0, 30.0 + 14.0 * data, IO[2] + 30.0], tint(r, 4, stage::mix(METAL, GREEN, 0.3 + 0.6 * data)), stage::scaled(GREEN, 0.3 * data * r.colour[4]));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, r: &Rig) {
    // group frames
    for g in 0..4 {
        let c = group_centre(g);
        let a = (0.15 + 0.35 * r.colour[1]) as f32;
        stage::glass_box(cv, cam, [c[0] - 175.0, 0.0, c[2] - 150.0], [c[0] + 175.0, H + 12.0, c[2] + 150.0], GLASS, a);
    }
    for i in 0..N {
        let [x, _, z] = centre(i);
        let s = spine_side(i);
        // a command: from the controller up the command bus, out to the bank
        let path = [CTRL, [0.0, 14.0, z], [x, H + 4.0, z]];
        particles(cv, cam, &path, 5, r.u * 1.6 + i as f64 * 0.11, 7.0, TEXT, r.cmd[i]);
        // data: from the row buffer to the data bus, along it to the I/O
        let zs = z + s * (BD + 8.0);
        let path = [[x, H, zs], [x, 10.0, 0.0], [0.0, 10.0, 0.0], [IO[0], 20.0, IO[2]]];
        particles(cv, cam, &path, 6, r.u * 1.8 + i as f64 * 0.07, 6.5, GREEN, r.read[i]);
        if r.wait[i] > 0.01 {
            stage::glass_box(cv, cam, [x - BW - 6.0, 0.0, z - BD - 6.0], [x + BW + 6.0, H + 8.0, z + BD + 6.0], PINK, (0.9 * r.wait[i]) as f32);
        }
    }
}

pub(super) fn at(p: Part) -> V3 {
    match p {
        Part::Bank(i) => {
            let c = centre(i);
            [c[0] + BW, H, c[2] - BD]
        }
        Part::Group(g) => {
            // the group's outer corner, away from the buses
            let c = group_centre(g);
            [c[0] + c[0].signum() * 175.0, H + 12.0, c[2] + c[2].signum() * 150.0]
        }
        Part::CmdBus => [0.0, 8.0, 330.0],
        Part::DataBus => [440.0, 6.0, 0.0],
        Part::Io => [IO[0] + 90.0, 30.0, IO[2]],
        Part::Ctrl => [CTRL[0] + 60.0, 40.0, CTRL[2]],
    }
}

pub(super) fn names(cv: &mut Canvas, cam: &Cam, r: &Rig) -> Vec<Rect> {
    let k = |i: usize| r.colour[i];
    let mut out = Vec::new();
    for g in 0..4 {
        let c = group_centre(g);
        let off = (if c[0] < 0.0 { -0.12 } else { 0.02 }, if c[2] < 0.0 { -0.05 } else { 0.04 });
        out.extend(label(cv, cam, at(Part::Group(g)), off, &format!("bank group {g}"), TEXT, 0.75 * k(1)));
    }
    out.extend(label(cv, cam, at(Part::Ctrl), (0.04, -0.05), "commands in", TEXT, 0.8 * k(5)));
    out.extend(label(cv, cam, at(Part::CmdBus), (-0.15, 0.02), "command bus", TEXT, 0.7 * k(2)));
    out.extend(label(cv, cam, at(Part::DataBus), (0.03, -0.05), "shared data bus", GREEN, 0.8 * k(3)));
    out.extend(label(cv, cam, at(Part::Io), (0.04, 0.04), "I/O", GREEN, 0.8 * k(4)));
    out
}

/// A name for one bank, offset from its corner.
pub(super) fn bank_label(cv: &mut Canvas, cam: &Cam, i: usize, s: &str, col: Col, a: f64) -> Option<Rect> {
    let off = if i % 2 == 0 { (-0.10, -0.09) } else { (0.03, -0.05) };
    label(cv, cam, at(Part::Bank(i)), off, s, col, a)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn banks_do_not_overlap() {
        for i in 0..N {
            for j in i + 1..N {
                let (a, b) = (centre(i), centre(j));
                let apart = (a[0] - b[0]).abs() >= 2.0 * BW || (a[2] - b[2]).abs() >= 2.0 * BD + 16.0;
                assert!(apart, "banks {i} and {j} overlap");
            }
        }
    }
}
