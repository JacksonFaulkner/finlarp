//! The power path every Power-tab scene shares, laid out as five stations the camera
//! flies between, each gated by its own level so only what a beat needs is drawn.
//!
//! - CAMPUS (z = 0): transmission towers, the substation yard, the switchgear house,
//!   a row of generators and the data hall.
//! - XFMR   (z = -6000): one power transformer, its tank cut open to show the core,
//!   the low- and high-voltage windings, bushings and radiators.
//! - BACKUP (z = 6000): utility feed, transfer switch, generator, UPS and batteries
//!   feeding a short row of racks; `outage` and `genset` play a power cut.
//! - RACK   (z = 10000): an NVL72-style rack, power shelves and DC busbar, with an
//!   optional 800 V sidecar; `count` racks in a row.
//! - BOARD  (z = 14000): a GPU board, its 54 V-to-12 V converter and the VRM phases
//!   around the GPU, which `vertical` moves underneath it.
//!
//! Schematic units, Y up; floors at y = 0. Not to scale between stations.

use super::super::stage::{self, label, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PURPLE, QUIET, STEEL, TEXT, YELLOW};
use super::super::{push_box, push_sphere};
use crate::{Cam, Canvas, Col, Tri, V3};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PwrPart {
    Pylon,
    Wire,
    Yard,
    Xfmr,
    Switchgear,
    Hall,
    Gen,
    Tank,
    Core,
    Lv,
    Hv,
    Bushing,
    Radiator,
    Utility,
    Ats,
    Ups,
    Battery,
    Load,
    Rack,
    Shelf,
    Busbar,
    Tray,
    Sidecar,
    Board,
    Gpu,
    Ibc,
    Phase,
}

pub const PWR_PARTS: usize = 27;

pub const XFMR_Z: f64 = -6000.0;
pub const BACKUP_Z: f64 = 6000.0;
pub const RACK_Z: f64 = 10000.0;
pub const BOARD_Z: f64 = 14000.0;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct PwrState {
    /// stations drawn, 0..1
    pub campus: f64,
    pub xfmr: f64,
    pub backup: f64,
    pub rack: f64,
    pub board: f64,
    /// power flowing, 0..1
    pub flow: f64,
    /// the utility feed lost, 0..1; generators running, 0..1
    pub outage: f64,
    pub genset: f64,
    /// XFMR: tank front cut away, 0..1
    pub cut: f64,
    /// heat off losses, 0..1
    pub heat: f64,
    /// RACK: 800 V DC sidecar instead of AC power shelves, 0..1; racks in a row, 1..6
    pub hvdc: f64,
    pub count: f64,
    /// BOARD: VRM phases moved under the GPU, 0..1
    pub vertical: f64,
    pub dim: f64,
    pub hi: [f64; PWR_PARTS],
}

impl PwrState {
    /// Everything at rest: the campus shown, power flowing, no outage.
    pub const BASE: PwrState = PwrState {
        campus: 1.0,
        xfmr: 0.0,
        backup: 0.0,
        rack: 0.0,
        board: 0.0,
        flow: 1.0,
        outage: 0.0,
        genset: 0.0,
        cut: 0.0,
        heat: 0.0,
        hvdc: 0.0,
        count: 1.0,
        vertical: 0.0,
        dim: 0.0,
        hi: [0.0; PWR_PARTS],
    };

    pub const fn spot(mut self, p: PwrPart) -> PwrState {
        self.dim = 0.85;
        self.hi[p as usize] = 1.0;
        self
    }

    pub(super) fn lerp(a: &PwrState, b: &PwrState, k: f64) -> PwrState {
        let l = |x: f64, y: f64| x + (y - x) * k;
        let mut hi = [0.0; PWR_PARTS];
        for i in 0..PWR_PARTS {
            hi[i] = l(a.hi[i], b.hi[i]);
        }
        PwrState {
            campus: l(a.campus, b.campus),
            xfmr: l(a.xfmr, b.xfmr),
            backup: l(a.backup, b.backup),
            rack: l(a.rack, b.rack),
            board: l(a.board, b.board),
            flow: l(a.flow, b.flow),
            outage: l(a.outage, b.outage),
            genset: l(a.genset, b.genset),
            cut: l(a.cut, b.cut),
            heat: l(a.heat, b.heat),
            hvdc: l(a.hvdc, b.hvdc),
            count: l(a.count, b.count),
            vertical: l(a.vertical, b.vertical),
            dim: l(a.dim, b.dim),
            hi,
        }
    }
}

const GROUND: Col = [0.20, 0.25, 0.22];
const GRAVEL: Col = [0.42, 0.42, 0.40];
const TANK: Col = [0.44, 0.48, 0.44];
const CONCRETE: Col = [0.70, 0.70, 0.68];
const HALL: Col = [0.80, 0.81, 0.80];
const GENSET: Col = [0.62, 0.58, 0.30];
const CABINET: Col = [0.42, 0.46, 0.54];
const BATTERY: Col = [0.30, 0.55, 0.45];
const COPPER: Col = [0.95, 0.62, 0.30];
const IRON: Col = [0.40, 0.42, 0.46];
const PORCELAIN: Col = [0.82, 0.74, 0.62];
const RACKC: Col = [0.18, 0.19, 0.22];
const PCB: Col = [0.16, 0.38, 0.24];
const ASIC: Col = [0.52, 0.44, 0.78];
const SUBSTRATE: Col = [0.42, 0.36, 0.22];
const INDUCTOR: Col = [0.55, 0.56, 0.60];
const STAGEC: Col = [0.14, 0.14, 0.16];
/// power in flight
pub(super) const AMPS: Col = YELLOW;
const DCOL: Col = ORANGE;
const HOT: Col = [1.0, 0.45, 0.25];

fn col(s: &PwrState, p: PwrPart, c: Col) -> Col {
    stage::mix(QUIET, c, (1.0 - s.dim).max(s.hi[p as usize]))
}

fn glow(s: &PwrState, p: PwrPart, c: Col) -> Col {
    stage::scaled(c, 0.3 * s.hi[p as usize] * s.dim)
}

fn tube(m: &mut Vec<Tri>, a: V3, b: V3, r: f64, seg: usize, c: Col, e: Col) {
    crate::push_tube(m, a, b, r, seg, c, e, true);
}

/// The utility feed strength: power from the grid, gone during an outage.
fn grid_on(s: &PwrState) -> f64 {
    s.flow * (1.0 - s.outage)
}

// ---------------------------------------------------------------- CAMPUS

const PYLONS: [f64; 3] = [-2900.0, -2350.0, -1800.0];
const PYLON_Z: f64 = -600.0;
const ARM_Y: [f64; 2] = [440.0, 540.0];
const XF: [(f64, f64); 2] = [(-1250.0, -650.0), (-900.0, -650.0)];
const GEN_Z: f64 = -560.0;

fn gen_x(i: usize) -> f64 {
    450.0 + i as f64 * 260.0
}

fn campus(s: &PwrState, m: &mut Vec<Tri>) {
    let k = s.campus;
    push_box(m, [-3200.0, -10.0, -1300.0], [2900.0, 0.0, 1300.0], col(s, PwrPart::Hall, GROUND), NO_GLOW);
    // transmission towers
    for x in PYLONS {
        let c = col(s, PwrPart::Pylon, METAL);
        push_box(m, [x - 22.0, 0.0, PYLON_Z - 22.0], [x + 22.0, 580.0 * k, PYLON_Z + 22.0], c, glow(s, PwrPart::Pylon, METAL));
        for (i, y) in ARM_Y.iter().enumerate() {
            let w = 150.0 - 40.0 * i as f64;
            push_box(m, [x - 8.0, y - 8.0, PYLON_Z - w], [x + 8.0, y + 8.0, PYLON_Z + w], c, NO_GLOW);
        }
    }
    // substation yard: gravel pad, gantry, two transformers
    push_box(m, [-1550.0, 0.0, -950.0], [-600.0, 6.0, -250.0], col(s, PwrPart::Yard, GRAVEL), NO_GLOW);
    let gc = col(s, PwrPart::Yard, METAL);
    for z in [-760.0, -440.0] {
        push_box(m, [-1520.0, 0.0, z - 10.0], [-1500.0, 420.0 * k, z + 10.0], gc, NO_GLOW);
    }
    push_box(m, [-1520.0, 410.0, -770.0], [-1500.0, 430.0, -430.0], gc, NO_GLOW);
    for (x, z) in XF {
        let tc = col(s, PwrPart::Xfmr, TANK);
        let e = glow(s, PwrPart::Xfmr, TANK);
        push_box(m, [x - 90.0, 6.0, z - 80.0], [x + 90.0, 6.0 + 150.0 * k, z + 80.0], tc, e);
        for j in 0..6 {
            let fz = z - 70.0 + j as f64 * 28.0;
            push_box(m, [x + 90.0, 20.0, fz], [x + 130.0, 140.0 * k, fz + 8.0], tc, NO_GLOW);
        }
        for j in 0..3 {
            let bz = z - 50.0 + j as f64 * 50.0;
            tube(m, [x - 40.0, 156.0, bz], [x - 40.0, 156.0 + 110.0 * k, bz], 8.0, 8, col(s, PwrPart::Xfmr, PORCELAIN), NO_GLOW);
        }
    }
    // switchgear house
    push_box(m, [-450.0, 0.0, -420.0], [-50.0, 130.0 * k, -120.0], col(s, PwrPart::Switchgear, CONCRETE), glow(s, PwrPart::Switchgear, CONCRETE));
    // generators along the hall
    for i in 0..8 {
        let x = gen_x(i);
        let gc = stage::mix(col(s, PwrPart::Gen, GENSET), [1.0, 0.85, 0.4], 0.25 * s.genset);
        push_box(m, [x - 90.0, 0.0, GEN_Z - 60.0], [x + 90.0, 90.0 * k, GEN_Z + 60.0], gc, glow(s, PwrPart::Gen, GENSET));
        tube(m, [x + 60.0, 90.0, GEN_Z], [x + 60.0, 90.0 + 60.0 * k, GEN_Z], 9.0, 8, col(s, PwrPart::Gen, STEEL), NO_GLOW);
    }
    // the data hall, with cooling units on its roof
    push_box(m, [200.0, 0.0, -350.0], [2600.0, 190.0 * k, 1000.0], col(s, PwrPart::Hall, HALL), glow(s, PwrPart::Hall, HALL));
    for i in 0..10 {
        let x = 330.0 + i as f64 * 230.0;
        push_box(m, [x - 70.0, 190.0, 0.0], [x + 70.0, 190.0 + 40.0 * k, 260.0], col(s, PwrPart::Hall, METAL), NO_GLOW);
    }
}

fn sag(a: V3, b: V3, d: f64) -> Vec<V3> {
    (0..=8)
        .map(|i| {
            let t = i as f64 / 8.0;
            [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - d * 4.0 * t * (1.0 - t), a[2] + (b[2] - a[2]) * t]
        })
        .collect()
}

fn campus_overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    let k = s.campus;
    let g = grid_on(s);
    let wc = stage::mix(col(s, PwrPart::Wire, GLASS), [1.0, 0.35, 0.3], 0.6 * s.outage);
    // conductors: three phases on two arms, tower to tower, then down to the gantry
    let mut spans: Vec<Vec<V3>> = Vec::new();
    for (i, y) in ARM_Y.iter().enumerate() {
        let w = 150.0 - 40.0 * i as f64;
        for zz in [-w + 10.0, w - 10.0] {
            let mut pts: Vec<V3> = vec![[-3300.0, *y - 40.0, PYLON_Z + zz]];
            for x in PYLONS {
                pts.push([x, *y, PYLON_Z + zz]);
            }
            pts.push([-1510.0, 420.0, PYLON_Z + zz * 0.6 - 0.0]);
            let mut line = Vec::new();
            for w2 in pts.windows(2) {
                line.extend(sag(w2[0], w2[1], 26.0));
            }
            spans.push(line);
        }
    }
    for line in &spans {
        for w2 in line.windows(2) {
            cv.line(cam, w2[0], w2[1], wc, (0.8 * k) as f32);
        }
    }
    for (i, line) in spans.iter().enumerate().step_by(2) {
        stage::particles(cv, cam, line, 6, u * 1.0 + i as f64 * 0.13, 10.0, AMPS, g * k);
    }
    // yard: gantry to transformers, transformers to switchgear, switchgear to hall
    for (i, (x, z)) in XF.iter().enumerate() {
        let p = [[-1510.0, 420.0, -600.0], [x - 40.0, 270.0, *z], [*x, 60.0, *z], [-250.0, 60.0, -270.0]];
        stage::particles(cv, cam, &p, 5, u * 1.0 + i as f64 * 0.4, 9.0, AMPS, g * k);
    }
    let feed = [[-250.0, 60.0, -270.0], [200.0, 60.0, -200.0], [900.0, 60.0, 300.0]];
    stage::particles(cv, cam, &feed, 6, u * 1.0, 9.0, AMPS, s.flow.max(s.genset) * k);
    // generators: exhaust when running, power into the hall
    if s.genset > 0.01 {
        for i in 0..8 {
            let x = gen_x(i) + 60.0;
            stage::particles(cv, cam, &[[x, 150.0, GEN_Z], [x + 30.0, 420.0, GEN_Z - 40.0]], 3, u * 1.0 + i as f64 * 0.19, 14.0, [0.55, 0.55, 0.58], s.genset * k);
            stage::particles(cv, cam, &[[x - 60.0, 50.0, GEN_Z + 60.0], [x - 60.0, 50.0, -350.0]], 2, u * 2.0 + i as f64 * 0.19, 8.0, AMPS, s.genset * k);
        }
    }
    if s.heat > 0.01 {
        for i in 0..10 {
            let x = 330.0 + i as f64 * 230.0;
            stage::particles(cv, cam, &[[x, 240.0, 130.0], [x, 520.0, 130.0]], 3, u * 1.0 + i as f64 * 0.21, 12.0, HOT, s.heat * k);
        }
    }
}

// ---------------------------------------------------------------- XFMR

/// The three core limbs' x positions.
const LIMBS: [f64; 3] = [-170.0, 0.0, 170.0];

fn xfmr(s: &PwrState, m: &mut Vec<Tri>) {
    let k = s.xfmr;
    let z = XFMR_Z;
    let zc = |z1: f64| if s.cut > 0.01 { z1 * (1.0 - s.cut) } else { z1 };
    push_box(m, [-500.0, -10.0, z - 400.0], [500.0, 0.0, z + 400.0], col(s, PwrPart::Tank, CONCRETE), NO_GLOW);
    // tank: back, sides, floor and lid; the front comes off with `cut`
    let tc = col(s, PwrPart::Tank, TANK);
    push_box(m, [-300.0, 0.0, z - 200.0], [300.0, 440.0 * k, z - 190.0], tc, NO_GLOW);
    push_box(m, [-300.0, 0.0, z - 200.0], [-290.0, 440.0 * k, z + zc(200.0)], tc, NO_GLOW);
    push_box(m, [290.0, 0.0, z - 200.0], [300.0, 440.0 * k, z + zc(200.0)], tc, NO_GLOW);
    push_box(m, [-300.0, 430.0, z - 200.0], [300.0, 440.0 * k, z + zc(200.0)], tc, glow(s, PwrPart::Tank, TANK));
    if s.cut < 0.99 {
        let y1 = 440.0 * (1.0 - s.cut);
        push_box(m, [-300.0, 0.0, z + 190.0], [300.0, y1 * k, z + 200.0], tc, glow(s, PwrPart::Tank, TANK));
    }
    // radiators on both ends
    for sx in [-1.0, 1.0] {
        for j in 0..8 {
            let fz = z - 170.0 + j as f64 * 44.0;
            if fz > z + zc(200.0) {
                continue;
            }
            let (x0, x1) = if sx < 0.0 { (-370.0, -300.0) } else { (300.0, 370.0) };
            push_box(m, [x0, 40.0, fz], [x1, 400.0 * k, fz + 10.0], col(s, PwrPart::Radiator, TANK), glow(s, PwrPart::Radiator, TANK));
        }
    }
    // core: three limbs and two yokes of laminated steel
    let ic = col(s, PwrPart::Core, IRON);
    let ie = glow(s, PwrPart::Core, IRON);
    push_box(m, [-230.0, 30.0, z - 40.0], [230.0, 80.0 * k, z + 40.0], ic, ie);
    push_box(m, [-230.0, 350.0, z - 40.0], [230.0, 400.0 * k, z + 40.0], ic, ie);
    for x in LIMBS {
        push_box(m, [x - 30.0, 80.0, z - 30.0], [x + 30.0, 350.0 * k, z + 30.0], ic, ie);
    }
    // windings on each limb: low voltage inside (few turns), high voltage outside (many)
    for x in LIMBS {
        tube(m, [x, 95.0, z], [x, 95.0 + 240.0 * k, z], 48.0, 20, col(s, PwrPart::Lv, COPPER), glow(s, PwrPart::Lv, COPPER));
        let hc = col(s, PwrPart::Hv, [0.78, 0.48, 0.24]);
        let he = glow(s, PwrPart::Hv, COPPER);
        // the HV coil as discs, so its many turns show
        for d in 0..12 {
            let y = 100.0 + d as f64 * 20.0;
            tube(m, [x, y, z], [x, y + 14.0 * k, z], 74.0, 20, hc, he);
        }
    }
    // bushings: tall high-voltage ones, short low-voltage ones; a conservator tank
    for x in LIMBS.iter() {
        tube(m, [*x, 440.0, z + 60.0], [*x, 440.0 + 300.0 * k, z + 60.0], 16.0, 10, col(s, PwrPart::Bushing, PORCELAIN), glow(s, PwrPart::Bushing, PORCELAIN));
        tube(m, [*x + 50.0, 440.0, z - 100.0], [*x + 50.0, 440.0 + 120.0 * k, z - 100.0], 12.0, 10, col(s, PwrPart::Bushing, PORCELAIN), NO_GLOW);
    }
    tube(m, [-220.0, 520.0, z - 150.0], [220.0, 520.0, z - 150.0], 40.0 * k, 14, tc, NO_GLOW);
}

fn xfmr_overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    let k = s.xfmr;
    let z = XFMR_Z;
    let f = s.flow * k;
    // high voltage in at low current: few particles; low voltage out at high current: many
    for (i, x) in LIMBS.iter().enumerate() {
        stage::particles(cv, cam, &[[*x, 900.0, z + 60.0], [*x, 440.0, z + 60.0], [*x + 70.0, 300.0, z + 30.0]], 2, u * 1.0 + i as f64 * 0.3, 9.0, AMPS, f);
        stage::particles(cv, cam, &[[*x + 50.0, 300.0, z - 50.0], [*x + 50.0, 440.0, z - 100.0], [*x + 50.0, 700.0, z - 100.0], [*x + 50.0, 760.0, z - 400.0]], 7, u * 2.0 + i as f64 * 0.3, 7.0, DCOL, f);
    }
    // magnetic flux circulating in the core (cut open only)
    if s.cut > 0.3 {
        let a = s.cut * k;
        for (i, x) in LIMBS.iter().enumerate() {
            let loop_pts = [[*x, 60.0, z + 41.0], [*x, 375.0, z + 41.0], [x + 85.0 * if i == 2 { -1.0 } else { 1.0 }, 375.0, z + 41.0], [x + 85.0 * if i == 2 { -1.0 } else { 1.0 }, 60.0, z + 41.0], [*x, 60.0, z + 41.0]];
            stage::particles(cv, cam, &loop_pts, 6, u * 1.0 + i as f64 * 0.33, 6.0, CYAN, a * 0.8);
        }
    }
    if s.heat > 0.01 {
        for sx in [-1.0, 1.0] {
            for j in 0..3 {
                let fz = z - 120.0 + j as f64 * 120.0;
                stage::particles(cv, cam, &[[sx * 335.0, 380.0, fz], [sx * 380.0, 700.0, fz]], 3, u * 1.0 + j as f64 * 0.2 + sx * 0.1, 10.0, HOT, s.heat * k);
            }
        }
    }
}

// ---------------------------------------------------------------- BACKUP

const ATS_X: f64 = -1000.0;
const UPS_X: f64 = -600.0;
const LOAD_X: f64 = 300.0;

fn backup(s: &PwrState, m: &mut Vec<Tri>) {
    let k = s.backup;
    let z = BACKUP_Z;
    push_box(m, [-1700.0, -10.0, z - 800.0], [900.0, 0.0, z + 500.0], col(s, PwrPart::Load, CONCRETE), NO_GLOW);
    // utility entrance: a pole-mounted feed coming in from the left
    push_box(m, [-1560.0, 0.0, z - 20.0], [-1520.0, 360.0 * k, z + 20.0], col(s, PwrPart::Utility, METAL), glow(s, PwrPart::Utility, METAL));
    // transfer switch
    push_box(m, [ATS_X - 70.0, 0.0, z - 50.0], [ATS_X + 70.0, 220.0 * k, z + 50.0], col(s, PwrPart::Ats, CABINET), glow(s, PwrPart::Ats, CABINET));
    // the generator behind it, with its exhaust stack
    let gx = ATS_X - 200.0;
    let gz = z - 520.0;
    let gc = stage::mix(col(s, PwrPart::Gen, GENSET), [1.0, 0.85, 0.4], 0.25 * s.genset);
    push_box(m, [gx - 260.0, 0.0, gz - 110.0], [gx + 260.0, 220.0 * k, gz + 110.0], gc, glow(s, PwrPart::Gen, GENSET));
    for j in 0..8 {
        let fx = gx + 200.0 + j as f64 * 6.0;
        push_box(m, [fx, 30.0, gz + 110.0], [fx + 3.0, 190.0 * k, gz + 114.0], col(s, PwrPart::Gen, STEEL), NO_GLOW);
    }
    tube(m, [gx - 150.0, 220.0, gz], [gx - 150.0, 220.0 + 200.0 * k, gz], 18.0, 10, col(s, PwrPart::Gen, STEEL), NO_GLOW);
    // UPS: rectifier, DC link, inverter cabinets
    for j in 0..3 {
        let x = UPS_X - 120.0 + j as f64 * 120.0;
        push_box(m, [x - 55.0, 0.0, z - 60.0], [x + 55.0, 220.0 * k, z + 60.0], col(s, PwrPart::Ups, CABINET), glow(s, PwrPart::Ups, CABINET));
        push_box(m, [x - 40.0, 160.0, z + 60.0], [x + 40.0, 200.0 * k, z + 63.0], col(s, PwrPart::Ups, [0.25, 0.30, 0.40]), stage::scaled(CYAN, 0.15 * k));
    }
    // battery cabinets: open fronts, rows of modules
    for j in 0..4 {
        let x = UPS_X - 180.0 + j as f64 * 120.0;
        let bz = z - 300.0;
        push_box(m, [x - 55.0, 0.0, bz - 60.0], [x + 55.0, 220.0 * k, bz - 50.0], col(s, PwrPart::Battery, CABINET), NO_GLOW);
        for r in 0..6 {
            let y = 15.0 + r as f64 * 34.0;
            let lvl = 1.0 - 0.6 * s.outage * (1.0 - s.genset);
            let bc = stage::mix(col(s, PwrPart::Battery, [0.25, 0.30, 0.28]), col(s, PwrPart::Battery, BATTERY), lvl);
            push_box(m, [x - 48.0, y, bz - 50.0], [x + 48.0, y + 26.0 * k, bz + 40.0], bc, glow(s, PwrPart::Battery, BATTERY));
        }
    }
    // the load: a short row of racks
    for j in 0..4 {
        let x = LOAD_X + j as f64 * 110.0;
        push_box(m, [x - 50.0, 0.0, z - 80.0], [x + 50.0, 240.0 * k, z + 80.0], col(s, PwrPart::Load, RACKC), glow(s, PwrPart::Load, RACKC));
        for r in 0..8 {
            let y = 20.0 + r as f64 * 26.0;
            push_box(m, [x - 44.0, y, z + 80.0], [x + 44.0, y + 4.0, z + 82.0], col(s, PwrPart::Load, GREEN), stage::scaled(GREEN, 0.4 * s.flow.max(s.outage) * k));
        }
    }
}

fn backup_overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    let k = s.backup;
    let z = BACKUP_Z;
    let g = grid_on(s) * k;
    let bat = s.outage * (1.0 - s.genset) * k;
    let gen = s.genset * s.outage.max(0.0) * k;
    let wc = stage::mix(GLASS, [1.0, 0.35, 0.3], s.outage);
    cv.line(cam, [-1900.0, 350.0, z], [-1540.0, 350.0, z], wc, (0.8 * k) as f32);
    stage::particles(cv, cam, &[[-1900.0, 350.0, z], [-1540.0, 350.0, z], [-1540.0, 120.0, z + 30.0], [ATS_X, 120.0, z + 52.0]], 6, u * 2.0, 9.0, AMPS, g);
    // generator to the transfer switch
    stage::particles(cv, cam, &[[ATS_X - 200.0, 120.0, z - 410.0], [ATS_X, 120.0, z - 50.0]], 5, u * 2.0, 9.0, AMPS, gen);
    // through the UPS: rectifier to DC to inverter, then to the racks
    let feed = (g + gen).min(1.0);
    stage::particles(cv, cam, &[[ATS_X, 120.0, z + 52.0], [UPS_X - 120.0, 120.0, z + 62.0], [UPS_X, 120.0, z + 62.0]], 5, u * 2.0, 9.0, AMPS, feed);
    let out = (g + gen + bat).min(1.0) * s.flow.max(s.outage);
    stage::particles(cv, cam, &[[UPS_X, 120.0, z + 62.0], [UPS_X + 120.0, 120.0, z + 62.0], [LOAD_X - 60.0, 120.0, z + 85.0], [LOAD_X + 330.0, 120.0, z + 85.0]], 8, u * 2.0, 9.0, AMPS, out);
    // batteries: charging gently, or carrying the whole load in an outage
    stage::particles(cv, cam, &[[UPS_X - 60.0, 120.0, z - 240.0], [UPS_X, 120.0, z - 60.0]], 5, u * 2.0, 9.0, DCOL, bat);
    stage::particles(cv, cam, &[[UPS_X, 100.0, z - 60.0], [UPS_X - 60.0, 100.0, z - 240.0]], 2, u * 1.0, 6.0, DCOL, g * 0.5);
    // exhaust
    if gen > 0.01 {
        stage::particles(cv, cam, &[[ATS_X - 350.0, 420.0, z - 520.0], [ATS_X - 300.0, 760.0, z - 600.0]], 5, u * 1.0, 18.0, [0.55, 0.55, 0.58], gen);
    }
    // the transfer switch's position: utility or generator
    let ang = s.genset * s.outage;
    let pivot = [ATS_X, 150.0, z + 52.0];
    let tip = [ATS_X - 40.0, 150.0 + 40.0 * (1.0 - 2.0 * ang), z + 52.0];
    cv.line(cam, pivot, tip, YELLOW, (0.9 * k) as f32);
}

// ---------------------------------------------------------------- RACK

/// Tray heights (y0, kind): 0 power shelf, 1 compute tray, 2 switch tray.
fn trays() -> Vec<(f64, u8)> {
    let mut v = Vec::new();
    let mut y = 40.0;
    for (n, kind) in [(3, 0u8), (8, 1), (9, 2), (10, 1), (3, 0)] {
        for _ in 0..n {
            v.push((y, kind));
            y += 30.0;
        }
        y += 14.0;
    }
    v
}

const RACK_DX: f64 = 380.0;

fn rack_xs(s: &PwrState) -> Vec<(f64, f64)> {
    let n = s.count.max(1.0);
    (0..n.ceil() as usize).map(|i| ((i as f64 - (n - 1.0) / 2.0) * RACK_DX, (n - i as f64).clamp(0.0, 1.0))).collect()
}

fn rack(s: &PwrState, m: &mut Vec<Tri>) {
    let k = s.rack;
    let z = RACK_Z;
    let span = (s.count.max(1.0) - 1.0) * RACK_DX / 2.0 + 900.0;
    push_box(m, [-span, -10.0, z - 600.0], [span, 0.0, z + 600.0], col(s, PwrPart::Rack, [0.30, 0.31, 0.34]), NO_GLOW);
    for (ox, p) in rack_xs(s) {
        if p < 0.01 {
            continue;
        }
        let kk = k * p;
        let rc = col(s, PwrPart::Rack, RACKC);
        for (dx, dz) in [(-150.0, -267.0), (140.0, -267.0), (-150.0, 257.0), (140.0, 257.0)] {
            push_box(m, [ox + dx, 0.0, z + dz], [ox + dx + 10.0, 1120.0 * kk, z + dz + 10.0], rc, NO_GLOW);
        }
        push_box(m, [ox - 150.0, 1110.0, z - 267.0], [ox + 150.0, 1120.0 * kk, z + 267.0], rc, NO_GLOW);
        push_box(m, [ox - 150.0, 0.0, z - 267.0], [ox + 150.0, 20.0 * kk, z + 267.0], rc, NO_GLOW);
        for (y, kind) in trays() {
            let ac = 1.0 - s.hvdc;
            let (c, e, part) = match kind {
                0 => (stage::mix(METAL, QUIET, s.hvdc * 0.6), stage::scaled(YELLOW, 0.12 * ac * s.flow), PwrPart::Shelf),
                1 => (stage::mix(RACKC, ASIC, 0.35), stage::scaled(ASIC, 0.15 * s.flow), PwrPart::Tray),
                _ => ([0.22, 0.42, 0.44], NO_GLOW, PwrPart::Tray),
            };
            let h = if kind == 0 { 26.0 * (1.0 - 0.7 * s.hvdc) } else { 24.0 };
            let hot = if kind == 1 { stage::scaled(HOT, 0.2 * s.heat) } else { NO_GLOW };
            push_box(m, [ox - 138.0, y, z - 255.0], [ox + 138.0, y + h * kk, z + 255.0], col(s, part, c), [e[0] + hot[0] + glow(s, part, c)[0], e[1] + hot[1], e[2] + hot[2]]);
        }
        // DC busbar down the back
        let bw = 18.0 * (1.0 - 0.6 * s.hvdc);
        push_box(m, [ox - bw, 40.0, z - 285.0], [ox + bw, 40.0 + 960.0 * kk, z - 270.0], col(s, PwrPart::Busbar, COPPER), glow(s, PwrPart::Busbar, COPPER));
        // 800 V sidecar: a power rack beside the compute rack
        if s.hvdc > 0.01 && ox + RACK_DX / 2.0 > span - 900.0 - 1.0 {
            let x0 = ox + 180.0;
            push_box(m, [x0, 0.0, z - 267.0], [x0 + 300.0 * s.hvdc, 1120.0 * kk, z + 267.0], col(s, PwrPart::Sidecar, [0.30, 0.33, 0.40]), glow(s, PwrPart::Sidecar, CABINET));
            for r in 0..10 {
                let y = 60.0 + r as f64 * 100.0;
                push_box(m, [x0 + 15.0, y, z + 267.0], [x0 + (15.0 + 270.0) * s.hvdc, y + 70.0 * kk, z + 270.0], col(s, PwrPart::Sidecar, METAL), stage::scaled(YELLOW, 0.12 * s.hvdc));
            }
        }
    }
}

fn rack_overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    let k = s.rack;
    let z = RACK_Z;
    let f = s.flow * k;
    let ac = 1.0 - s.hvdc;
    for (ri, (ox, p)) in rack_xs(s).iter().enumerate() {
        if *p < 0.5 {
            continue;
        }
        // AC whips into the top shelves, DC down the busbar, into each tray
        for (j, dx) in [-90.0, 0.0, 90.0].iter().enumerate() {
            stage::particles(cv, cam, &[[ox + dx, 1500.0, z - 200.0], [ox + dx, 1120.0, z - 200.0], [ox + dx, 980.0, z - 200.0]], 3, u * 2.0 + j as f64 * 0.3 + ri as f64 * 0.1, 9.0, AMPS, f * ac);
        }
        stage::particles(cv, cam, &[[*ox, 1000.0, z - 290.0], [*ox, 50.0, z - 290.0]], 10, u * 2.0 + ri as f64 * 0.1, 10.0, DCOL, f);
        for (i, (y, kind)) in trays().iter().enumerate().step_by(3) {
            if *kind == 0 {
                continue;
            }
            stage::particles(cv, cam, &[[*ox, y + 12.0, z - 285.0], [*ox, y + 12.0, z + 100.0]], 2, u * 2.0 + i as f64 * 0.07, 7.0, DCOL, f * 0.8);
        }
        // the sidecar: 800 V across to the rack
        if s.hvdc > 0.01 {
            for j in 0..4 {
                let y = 200.0 + j as f64 * 220.0;
                stage::particles(cv, cam, &[[ox + 330.0, y, z - 290.0], [*ox, y, z - 290.0]], 3, u * 2.0 + j as f64 * 0.25, 9.0, AMPS, f * s.hvdc);
            }
        }
        if s.heat > 0.01 {
            for j in 0..5 {
                let y = 300.0 + j as f64 * 150.0;
                stage::particles(cv, cam, &[[ox + 0.0, y, z + 260.0], [ox + 40.0, y + 120.0, z + 520.0]], 3, u * 1.0 + j as f64 * 0.21, 10.0, HOT, s.heat * k);
            }
        }
    }
}

// ---------------------------------------------------------------- BOARD

/// VRM phase positions (x, z), beside the GPU or (vertical) under it.
fn phases(s: &PwrState) -> Vec<(f64, f64, f64)> {
    let v = s.vertical;
    let mut out = Vec::new();
    for side in [-1.0, 1.0] {
        for row in 0..2 {
            for j in 0..4 {
                let zz = -150.0 + j as f64 * 100.0;
                let bx = side * (270.0 + row as f64 * 70.0);
                let ux = side * (40.0 + row as f64 * 80.0);
                let uz = zz * 0.8;
                out.push((bx + (ux - bx) * v, zz + (uz - zz) * v, 8.0 + (-76.0 - 8.0) * v));
            }
        }
    }
    out
}

fn board(s: &PwrState, m: &mut Vec<Tri>) {
    let k = s.board;
    let z = BOARD_Z;
    push_box(m, [-650.0, -20.0, z - 420.0], [650.0, 0.0, z + 420.0], col(s, PwrPart::Board, PCB), glow(s, PwrPart::Board, PCB));
    // GPU package: substrate, die and four HBM stacks
    push_box(m, [-190.0, 0.0, z - 190.0], [190.0, 14.0 * k, z + 190.0], col(s, PwrPart::Gpu, SUBSTRATE), NO_GLOW);
    let hot = stage::scaled(HOT, 0.35 * s.heat);
    push_box(m, [-90.0, 14.0, z - 110.0], [90.0, 30.0 * k, z + 110.0], stage::mix(col(s, PwrPart::Gpu, ASIC), HOT, 0.3 * s.heat), [hot[0] + glow(s, PwrPart::Gpu, ASIC)[0], hot[1], hot[2]]);
    for (dx, dz) in [(-140.0, -80.0), (-140.0, 80.0), (140.0, -80.0), (140.0, 80.0)] {
        push_box(m, [dx - 35.0, 14.0, z + dz - 45.0], [dx + 35.0, 34.0 * k, z + dz + 45.0], col(s, PwrPart::Gpu, [0.78, 0.55, 0.36]), NO_GLOW);
    }
    // 54 V to 12 V converter brick near the board edge, and the input connector
    push_box(m, [-560.0, 0.0, z - 330.0], [-420.0, 50.0 * k, z - 220.0], col(s, PwrPart::Ibc, [0.22, 0.28, 0.48]), glow(s, PwrPart::Ibc, CABINET));
    push_box(m, [-650.0, 0.0, z - 310.0], [-610.0, 30.0 * k, z - 240.0], col(s, PwrPart::Ibc, COPPER), NO_GLOW);
    // VRM phases: power stage plus inductor each; under the board when vertical
    for (x, zz, y) in phases(s) {
        let yb = if y < 0.0 { y - 20.0 } else { y };
        push_box(m, [x - 14.0, yb - 8.0, z + zz - 16.0], [x + 14.0, yb + 8.0 * k - 8.0 + 8.0, z + zz - 2.0], col(s, PwrPart::Phase, STAGEC), NO_GLOW);
        let ic = stage::mix(col(s, PwrPart::Phase, INDUCTOR), HOT, 0.4 * s.heat);
        push_box(m, [x - 22.0, yb, z + zz + 2.0], [x + 22.0, yb + 30.0 * k, z + zz + 40.0], ic, glow(s, PwrPart::Phase, INDUCTOR));
    }
    // a row of capacitors along each side
    for side in [-1.0, 1.0] {
        for j in 0..8 {
            let cz = z - 175.0 + j as f64 * 50.0;
            push_sphere(m, [side * 215.0, 6.0, cz], 6.0 * k, 6, col(s, PwrPart::Phase, [0.65, 0.60, 0.50]), NO_GLOW);
        }
    }
}

fn board_overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    let k = s.board;
    let z = BOARD_Z;
    let f = s.flow * k;
    // 54 V in (few, slow), 12 V to the phases, then ~0.8 V at hundreds of amps into the GPU (many, fast)
    stage::particles(cv, cam, &[[-760.0, 15.0, z - 275.0], [-560.0, 25.0, z - 275.0]], 3, u * 1.0, 9.0, AMPS, f);
    for (i, (x, zz, y)) in phases(s).iter().enumerate() {
        let yy = if *y < 0.0 { y - 4.0 } else { 40.0 };
        stage::particles(cv, cam, &[[-420.0, 40.0, z - 275.0], [x * 0.9, yy.max(10.0), z + zz * 0.8 - 40.0], [*x, yy, z + zz]], 2, u * 2.0 + i as f64 * 0.11, 6.0, DCOL, f);
        let to = [x * 0.25, if *y < 0.0 { -2.0 } else { 32.0 }, z + zz * 0.4];
        stage::particles(cv, cam, &[[*x, yy, z + zz + 20.0], to], 4, u * 3.0 + i as f64 * 0.07, 7.0, HOT, f);
    }
    if s.heat > 0.01 {
        for (i, (x, zz, y)) in phases(s).iter().enumerate().step_by(2) {
            if *y < 0.0 {
                continue;
            }
            stage::particles(cv, cam, &[[*x, 50.0, z + zz + 20.0], [*x, 260.0, z + zz + 20.0]], 2, u * 1.0 + i as f64 * 0.13, 8.0, HOT, s.heat * k * 0.7);
        }
        stage::particles(cv, cam, &[[0.0, 40.0, z], [0.0, 330.0, z]], 4, u * 1.0, 10.0, HOT, s.heat * k);
    }
}

// ---------------------------------------------------------------- shared

pub(super) fn solids(s: &PwrState, m: &mut Vec<Tri>) {
    if s.campus > 0.01 {
        campus(s, m);
    }
    if s.xfmr > 0.01 {
        xfmr(s, m);
    }
    if s.backup > 0.01 {
        backup(s, m);
    }
    if s.rack > 0.01 {
        rack(s, m);
    }
    if s.board > 0.01 {
        board(s, m);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, s: &PwrState, u: f64) {
    if s.campus > 0.01 {
        campus_overlay(cv, cam, s, u);
    }
    if s.xfmr > 0.01 {
        xfmr_overlay(cv, cam, s, u);
    }
    if s.backup > 0.01 {
        backup_overlay(cv, cam, s, u);
    }
    if s.rack > 0.01 {
        rack_overlay(cv, cam, s, u);
    }
    if s.board > 0.01 {
        board_overlay(cv, cam, s, u);
    }
    let _ = (PURPLE, TEXT);
}

pub fn pwr_part_at(p: PwrPart, s: &PwrState) -> V3 {
    let span = (s.count.max(1.0) - 1.0) * RACK_DX / 2.0;
    let ph = phases(s);
    let ph = ph.last().copied().unwrap_or((340.0, 150.0, 8.0));
    match p {
        PwrPart::Pylon => [PYLONS[1], 580.0, PYLON_Z + 22.0],
        PwrPart::Wire => [PYLONS[2] + 140.0, ARM_Y[1] - 30.0, PYLON_Z + 140.0],
        PwrPart::Yard => [-600.0, 6.0, -250.0],
        PwrPart::Xfmr => [XF[1].0 + 90.0, 156.0, XF[1].1 + 80.0],
        PwrPart::Switchgear => [-50.0, 130.0, -120.0],
        PwrPart::Hall => [2600.0, 190.0, 1000.0],
        PwrPart::Gen if s.backup > s.campus => [ATS_X + 60.0, 220.0, BACKUP_Z - 410.0],
        PwrPart::Gen => [gen_x(7) + 90.0, 90.0, GEN_Z + 60.0],
        PwrPart::Tank => [300.0, 440.0, XFMR_Z + 200.0 * (1.0 - s.cut)],
        PwrPart::Core => [230.0, 380.0, XFMR_Z + 40.0],
        PwrPart::Lv => [LIMBS[0] + 48.0, 300.0, XFMR_Z + 30.0],
        PwrPart::Hv => [LIMBS[2] + 74.0, 200.0, XFMR_Z + 30.0],
        PwrPart::Bushing => [LIMBS[2] + 16.0, 700.0, XFMR_Z + 60.0],
        PwrPart::Radiator => [370.0, 300.0, XFMR_Z + 150.0 * (1.0 - s.cut)],
        PwrPart::Utility => [-1520.0, 360.0, BACKUP_Z + 20.0],
        PwrPart::Ats => [ATS_X + 70.0, 220.0, BACKUP_Z + 50.0],
        PwrPart::Ups => [UPS_X + 175.0, 220.0, BACKUP_Z + 60.0],
        PwrPart::Battery => [UPS_X + 235.0, 200.0, BACKUP_Z - 260.0],
        PwrPart::Load => [LOAD_X + 380.0, 240.0, BACKUP_Z + 80.0],
        PwrPart::Rack => [span + 150.0, 1120.0, RACK_Z + 267.0],
        PwrPart::Shelf => [span + 138.0, 1010.0, RACK_Z + 255.0],
        PwrPart::Busbar => [span + 18.0, 700.0, RACK_Z - 270.0],
        PwrPart::Tray => [span + 138.0, 560.0, RACK_Z + 255.0],
        PwrPart::Sidecar => [span + 480.0, 1120.0, RACK_Z + 267.0],
        PwrPart::Board => [650.0, 0.0, BOARD_Z + 420.0],
        PwrPart::Gpu => [90.0, 30.0, BOARD_Z + 110.0],
        PwrPart::Ibc => [-420.0, 50.0, BOARD_Z - 220.0],
        PwrPart::Phase => [ph.0 + 22.0, ph.2 + 30.0, BOARD_Z + ph.1 + 40.0],
    }
}

pub fn pwr_part_col(p: PwrPart) -> Col {
    match p {
        PwrPart::Wire | PwrPart::Pylon | PwrPart::Utility => GLASS,
        PwrPart::Xfmr | PwrPart::Tank | PwrPart::Radiator | PwrPart::Core => [0.75, 0.80, 0.72],
        PwrPart::Lv | PwrPart::Hv | PwrPart::Busbar => COPPER,
        PwrPart::Gen => [0.95, 0.85, 0.40],
        PwrPart::Battery => GREEN,
        PwrPart::Ups | PwrPart::Ats | PwrPart::Sidecar | PwrPart::Ibc => CYAN,
        PwrPart::Gpu | PwrPart::Tray => [0.78, 0.68, 0.98],
        PwrPart::Shelf => YELLOW,
        PwrPart::Phase => ORANGE,
        _ => TEXT,
    }
}

pub(super) fn labels(cv: &mut Canvas, cam: &Cam, s: &PwrState, list: &[(PwrPart, &str)], a: f64, out: &mut Vec<Rect>) {
    for (i, (p, t)) in list.iter().enumerate() {
        let at = pwr_part_at(*p, s);
        let left = cam.project(at).is_some_and(|(x, _, _)| x < cv.w as f64 * 0.5);
        let w = stage::text_w(&t.to_ascii_uppercase(), stage::text_scale(cv)) as f64 / cv.h as f64;
        let dx = if left { -0.05 - w } else { 0.05 };
        let dy = if i % 2 == 0 { -0.07 } else { 0.06 };
        out.extend(label(cv, cam, at, (dx, dy), t, pwr_part_col(*p), a));
    }
}
