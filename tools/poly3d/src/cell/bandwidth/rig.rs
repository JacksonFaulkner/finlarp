//! The memory system every BANDWIDTH scene shares: the processor with its memory
//! controller on the left, up to four DDR channels running right to their DIMMs,
//! and an HBM stack close beside the processor at the front. Bits travel the wires
//! as dots; a gauge on the left shows the peak bandwidth on a log scale.
//!
//! Geometry, schematic units, Y up: the processor at x = -470, DIMMs at x = 430,
//! channel c a ribbon of 8 wires (one per 8 data pins) at z = -270 + 160 c. The HBM
//! stack sits at x = -170, z = 470, joined to the processor by a wide short ribbon.

use super::super::push_box;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT};
use crate::{Cam, Canvas, Col, Tri, V3};

pub(super) const CH: usize = 4;
pub(super) const WIRES: usize = 8;
pub(super) const CPU_X: f64 = -470.0;
pub(super) const DIMM_X: f64 = 430.0;
const HBM_X: f64 = -170.0;
const HBM_Z: f64 = 470.0;
const HBM_WIRES: usize = 28;
const GAUGE: V3 = [-640.0, 0.0, -330.0];

pub(super) fn ch_z(c: usize) -> f64 {
    -270.0 + 160.0 * c as f64
}

pub(super) fn wire_z(c: usize, k: usize) -> f64 {
    ch_z(c) - 49.0 + 14.0 * k as f64
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum Part {
    Pin,
    Channel(usize),
    Dimm(usize),
    Cpu,
    Hbm,
    Gauge,
}

#[derive(Clone, Copy, Debug)]
pub(super) struct Rig {
    /// how present each channel is, 0..1
    pub chan: [f64; CH],
    /// in channel 0, how many of its wires carry data (0..1 of 8; 1/8 = one pin)
    pub width0: f64,
    /// data flowing on each channel, 0..1
    pub flow: [f64; CH],
    /// +1 reads (DIMM to processor), -1 writes; in between the bus turns around
    pub dir: f64,
    /// idle gaps in the stream, 0..1 (pink)
    pub gaps: f64,
    /// the HBM stack and its ribbon, 0..1
    pub hbm: f64,
    /// peak bandwidth shown on the gauge, GB/s
    pub gbps: f64,
    /// the memory-wall bars beside the gauge, 0..1
    pub wall: f64,
    /// colour kept per part: pins, channels, DIMMs, processor, HBM, gauge
    pub colour: [f64; 6],
    pub u: f64,
}

impl Default for Rig {
    fn default() -> Self {
        Rig { chan: [0.0; CH], width0: 1.0, flow: [0.0; CH], dir: 1.0, gaps: 0.0, hbm: 0.0, gbps: 0.0, wall: 0.0, colour: [1.0; 6], u: 0.0 }
    }
}

fn tint(r: &Rig, i: usize, col: Col) -> Col {
    stage::mix(QUIET, col, r.colour[i])
}

/// Gauge height for `gbps`, log scale: 0.1 GB/s at the floor, 80 units a decade.
pub(super) fn gauge_h(gbps: f64) -> f64 {
    (80.0 * (gbps.max(0.1) / 0.1).log10()).max(4.0)
}

pub(super) fn solids(r: &Rig, m: &mut Vec<Tri>) {
    push_box(m, [-720.0, -24.0, -400.0], [560.0, 0.0, 600.0], STEEL, NO_GLOW);
    // processor with the controller
    push_box(m, [CPU_X - 80.0, 0.0, -340.0], [CPU_X + 40.0, 60.0, 300.0], tint(r, 3, stage::mix(METAL, PURPLE, 0.35)), NO_GLOW);
    for c in 0..CH {
        let p = r.chan[c];
        if p < 0.01 {
            continue;
        }
        let z = ch_z(c);
        // DIMM: a board with eight chips
        push_box(m, [DIMM_X, 0.0, z - 62.0], [DIMM_X + 30.0, 90.0 * p, z + 62.0], tint(r, 2, [0.20, 0.42, 0.30]), NO_GLOW);
        for k in 0..8 {
            let cz = z - 52.0 + 14.8 * k as f64;
            push_box(m, [DIMM_X - 8.0, 20.0 * p, cz - 6.0], [DIMM_X, 60.0 * p, cz + 6.0], tint(r, 2, STEEL), NO_GLOW);
        }
        // the channel's wires
        for k in 0..WIRES {
            let lit = if c == 0 { ((r.width0 * WIRES as f64) - k as f64).clamp(0.0, 1.0) } else { 1.0 };
            let col = stage::mix(stage::scaled(METAL, 0.6), GREEN, 0.05 + 0.7 * lit * r.flow[c]);
            let wz = wire_z(c, k);
            let len = (DIMM_X - (CPU_X + 40.0)) * p;
            crate::push_tube(m, [CPU_X + 40.0, 12.0, wz], [CPU_X + 40.0 + len, 12.0, wz], 3.0, 6, tint(r, if c == 0 && k == 0 { 0 } else { 1 }, col), NO_GLOW, false);
        }
    }
    // HBM: a short stack of dies beside the processor, many wires
    if r.hbm > 0.01 {
        let h = r.hbm;
        for d in 0..8 {
            let y = 10.0 + d as f64 * 12.0 * h;
            push_box(m, [HBM_X - 60.0, y, HBM_Z - 60.0], [HBM_X + 60.0, y + 9.0 * h, HBM_Z + 60.0], tint(r, 4, stage::mix(STEEL, ORANGE, 0.5)), stage::scaled(ORANGE, 0.06 * h));
        }
        for k in 0..HBM_WIRES {
            let z = HBM_Z - 56.0 + 4.0 * k as f64;
            crate::push_tube(m, [CPU_X + 40.0, 6.0, z], [CPU_X + 40.0 + (HBM_X - 60.0 - CPU_X - 40.0) * h, 6.0, z], 1.5, 4, tint(r, 4, stage::mix(METAL, CYAN, 0.6)), NO_GLOW, false);
        }
        push_box(m, [CPU_X - 80.0, 0.0, 300.0], [CPU_X + 40.0, 60.0 * h, HBM_Z + 60.0], tint(r, 3, stage::mix(METAL, PURPLE, 0.35)), NO_GLOW);
    }
    // memory wall: 20 years of growth, log scale like the gauge (80 units a decade)
    if r.wall > 0.01 {
        for (dx, x, col) in [(150.0, 60000.0f64, PINK), (250.0, 100.0f64, CYAN)] {
            let hgt = 80.0 * x.log10() * r.wall;
            push_box(m, [GAUGE[0] + dx - 25.0, 0.0, GAUGE[2] - 25.0], [GAUGE[0] + dx + 25.0, hgt, GAUGE[2] + 25.0], col, stage::scaled(col, 0.15));
        }
    }
    // gauge
    let gh = gauge_h(r.gbps);
    push_box(m, [GAUGE[0] - 30.0, 0.0, GAUGE[2] - 30.0], [GAUGE[0] + 30.0, gh, GAUGE[2] + 30.0], tint(r, 5, CYAN), stage::scaled(CYAN, 0.2 * r.colour[5]));
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, r: &Rig) {
    let u = r.u;
    for c in 0..CH {
        let f = r.flow[c] * r.chan[c];
        if f < 0.01 {
            continue;
        }
        for k in 0..WIRES {
            let lit = if c == 0 { ((r.width0 * WIRES as f64) - k as f64).clamp(0.0, 1.0) } else { 1.0 };
            let wz = wire_z(c, k);
            let (a, b) = ([DIMM_X - 10.0, 16.0, wz], [CPU_X + 44.0, 16.0, wz]);
            // reads run left, writes right; the turnaround leaves the wire empty
            let dir = r.dir;
            let strength = f * lit * dir.abs();
            let path = if dir >= 0.0 { [a, b] } else { [b, a] };
            let col = if dir >= 0.0 { GREEN } else { ORANGE };
            particles(cv, cam, &path, 9, u * 2.2 + k as f64 * 0.05 + c as f64 * 0.11, 5.0, col, strength * (1.0 - r.gaps));
            if r.gaps > 0.01 {
                // gaps: pink markers where the stream has holes
                let s = (u * 0.7 + k as f64 * 0.13 + c as f64 * 0.31).rem_euclid(1.0);
                let p = stage::along(&path, s);
                stage::dot(cv, cam, p, 7.0, PINK, r.gaps * lit);
            }
        }
    }
    if r.hbm > 0.01 {
        for k in (0..HBM_WIRES).step_by(2) {
            let z = HBM_Z - 56.0 + 4.0 * k as f64;
            particles(cv, cam, &[[HBM_X - 64.0, 8.0, z], [CPU_X + 44.0, 8.0, z]], 4, u * 1.6 + k as f64 * 0.04, 3.5, CYAN, r.hbm);
        }
    }
    stage::glass_box(cv, cam, [GAUGE[0] - 30.0, 0.0, GAUGE[2] - 30.0], [GAUGE[0] + 30.0, gauge_h(1000.0), GAUGE[2] + 30.0], GLASS, 0.25);
}

pub(super) fn at(p: Part, r: &Rig) -> V3 {
    match p {
        Part::Pin => [0.0, 14.0, wire_z(0, 0)],
        Part::Channel(c) => [100.0, 14.0, wire_z(c, WIRES - 1)],
        Part::Dimm(c) => [DIMM_X + 30.0, 90.0, ch_z(c) + 62.0],
        Part::Cpu => [CPU_X + 40.0, 60.0, 300.0],
        Part::Hbm => [HBM_X + 60.0, 10.0 + 96.0 * r.hbm, HBM_Z + 60.0],
        Part::Gauge => [GAUGE[0] + 30.0, gauge_h(r.gbps), GAUGE[2]],
    }
}

/// The gauge value as text.
pub(super) fn gbps_text(v: f64) -> String {
    format!("{v:.1} GB/s peak")
}

pub(super) fn names(cv: &mut Canvas, cam: &Cam, r: &Rig) -> Vec<Rect> {
    let k = |i: usize| r.colour[i];
    let mut out = Vec::new();
    out.extend(label(cv, cam, at(Part::Cpu, r), (0.03, 0.05), "processor + memory controller", PURPLE, 0.85 * k(3)));
    out.extend(label(cv, cam, at(Part::Gauge, r), (-0.20, -0.05), &gbps_text(r.gbps), CYAN, 0.95 * k(5)));
    for c in 0..CH {
        if r.chan[c] > 0.5 {
            out.extend(label(cv, cam, at(Part::Dimm(c), r), (0.02, 0.0), &format!("DIMM {c}"), GREEN, 0.75 * k(2)));
        }
    }
    out.extend(label(cv, cam, at(Part::Channel(0), r), (0.0, 0.05), "channel: 64 data pins", GREEN, r.chan[0] * k(1) * (r.width0 * 1.15 - 0.15).clamp(0.0, 1.0)));
    out.extend(label(cv, cam, at(Part::Hbm, r), (0.03, -0.04), "HBM stack: 1024 pins", ORANGE, r.hbm * k(4)));
    out.extend(label(cv, cam, [GAUGE[0], 0.0, GAUGE[2] + 30.0], (-0.06, 0.06), "log scale", TEXT, 0.6 * k(5)));
    out.extend(label(cv, cam, [GAUGE[0] + 175.0, 80.0 * 60000f64.log10() * r.wall, GAUGE[2]], (0.03, -0.06), "compute x60,000", PINK, r.wall));
    out.extend(label(cv, cam, [GAUGE[0] + 275.0, 160.0 * r.wall, GAUGE[2]], (0.03, -0.02), "DRAM bandwidth x100", CYAN, r.wall));
    out
}
