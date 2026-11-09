//! The optical link every Fiber-tab scene shares, laid out as five stations the camera
//! flies between. Each station is gated by its own level so only what a beat needs is
//! drawn, and every quantity is a float so scenes blend without cuts.
//!
//! - LINK  (z = 0): host chip, copper traces, a pluggable transceiver in its cage,
//!   the fiber cable, and a mirrored receiving module and host. Cable length `span`.
//! - GLASS (z = -5000): one fiber, magnified 4 units per micron: core, cladding (glass)
//!   and coating, stepped like a stripped fiber, with light travelling in the core.
//! - LASER (z = 5000): an EML chip (x = -1300), a silicon-photonics modulator (x = 0)
//!   and a VCSEL (x = 1300).
//! - PD    (z = 8000): a photodiode with a fiber above it and its TIA beside it.
//! - CPO   (z = 11000): a switch package, with pluggables at the front panel or
//!   optical engines on the package.
//!
//! Schematic units, Y up; board tops at y = 0.

use super::super::stage::{self, label, ring, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, TEXT, YELLOW};
use super::super::{push_box, push_sphere};
use crate::{Cam, Canvas, Col, Tri, V3};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LinkPart {
    Asic,
    Board,
    Trace,
    Panel,
    Module,
    Dsp,
    Driver,
    Laser,
    Lens,
    Connector,
    Cable,
    RxModule,
    Pd,
    Tia,
    Eye,
    Symbols,
    Core,
    Cladding,
    Coating,
    Eml,
    Eam,
    Siph,
    Mzm,
    Vcsel,
    Absorber,
    Amp,
    Switch,
    Plug,
    Engine,
    Els,
    Ring,
}

pub const LINK_PARTS: usize = 31;

/// Station centres (the camera targets them; the TUI keeps copies).
pub const GLASS_Z: f64 = -5000.0;
pub const LASER_Z: f64 = 5000.0;
pub const PD_Z: f64 = 8000.0;
pub const CPO_Z: f64 = 11000.0;
const EML_X: f64 = -1700.0;
const VCSEL_X: f64 = 1500.0;
/// Glass station: fiber axis height, and units per micron.
const AXIS_Y: f64 = 300.0;
const UM: f64 = 4.0;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct LinkState {
    /// stations drawn, 0..1
    pub link: f64,
    pub glass: f64,
    pub laser: f64,
    pub pd: f64,
    pub cpo: f64,
    /// LINK: module lid closed (1) or slid open (0)
    pub shell: f64,
    /// optical lanes each way, 1..8
    pub lanes: f64,
    /// a DSP in the module (0 = linear drive, LPO)
    pub dsp: f64,
    /// copper cable instead of optics (DAC), 0..1
    pub copper: f64,
    /// multimode: VCSEL lasers, aqua cable, 50 um core, 0..1
    pub mm: f64,
    /// cable length factor
    pub span: f64,
    /// electrical data, light in fiber, 0..1
    pub elec: f64,
    pub light: f64,
    /// signal levels: 0 NRZ (2 levels), 1 PAM4 (4 levels)
    pub pam4: f64,
    /// symbol strip over the cable, 0..1
    pub bars: f64,
    /// eye diagram over the DSP, 0..1, and how open it is (0 = closed by noise)
    pub eye: f64,
    pub eq: f64,
    /// GLASS: coating stripped back, 0..1; rays bouncing off the cladding, 0..1;
    /// light lost along the length, 0..1
    pub strip: f64,
    pub tir: f64,
    pub loss: f64,
    /// PD: carriers in the absorber, 0..1
    pub carriers: f64,
    /// CPO: optical engines on the package (1) or pluggables at the panel (0)
    pub engines: f64,
    /// heat off modules and engines, 0..1
    pub heat: f64,
    pub dim: f64,
    pub hi: [f64; LINK_PARTS],
}

impl LinkState {
    /// A working single-mode link: closed module, eight lanes, PAM4, light on.
    pub const BASE: LinkState = LinkState {
        link: 1.0,
        glass: 0.0,
        laser: 0.0,
        pd: 0.0,
        cpo: 0.0,
        shell: 1.0,
        lanes: 8.0,
        dsp: 1.0,
        copper: 0.0,
        mm: 0.0,
        span: 1.0,
        elec: 0.0,
        light: 1.0,
        pam4: 1.0,
        bars: 0.0,
        eye: 0.0,
        eq: 1.0,
        strip: 1.0,
        tir: 0.0,
        loss: 0.0,
        carriers: 1.0,
        engines: 0.0,
        heat: 0.0,
        dim: 0.0,
        hi: [0.0; LINK_PARTS],
    };

    pub const fn spot(mut self, p: LinkPart) -> LinkState {
        self.dim = 0.85;
        self.hi[p as usize] = 1.0;
        self
    }

    pub(super) fn lerp(a: &LinkState, b: &LinkState, k: f64) -> LinkState {
        let l = |x: f64, y: f64| x + (y - x) * k;
        let mut hi = [0.0; LINK_PARTS];
        for i in 0..LINK_PARTS {
            hi[i] = l(a.hi[i], b.hi[i]);
        }
        LinkState {
            link: l(a.link, b.link),
            glass: l(a.glass, b.glass),
            laser: l(a.laser, b.laser),
            pd: l(a.pd, b.pd),
            cpo: l(a.cpo, b.cpo),
            shell: l(a.shell, b.shell),
            lanes: l(a.lanes, b.lanes),
            dsp: l(a.dsp, b.dsp),
            copper: l(a.copper, b.copper),
            mm: l(a.mm, b.mm),
            span: l(a.span, b.span),
            elec: l(a.elec, b.elec),
            light: l(a.light, b.light),
            pam4: l(a.pam4, b.pam4),
            bars: l(a.bars, b.bars),
            eye: l(a.eye, b.eye),
            eq: l(a.eq, b.eq),
            strip: l(a.strip, b.strip),
            tir: l(a.tir, b.tir),
            loss: l(a.loss, b.loss),
            carriers: l(a.carriers, b.carriers),
            engines: l(a.engines, b.engines),
            heat: l(a.heat, b.heat),
            dim: l(a.dim, b.dim),
            hi,
        }
    }
}

const BOARD: Col = [0.16, 0.34, 0.22];
const PCB: Col = [0.18, 0.42, 0.28];
const ASIC: Col = [0.52, 0.44, 0.78];
const SUBSTRATE: Col = [0.42, 0.36, 0.22];
const DSP: Col = [0.28, 0.60, 0.64];
const CHIP: Col = [0.30, 0.32, 0.38];
const COPPER: Col = [0.95, 0.62, 0.30];
const GOLD: Col = [0.95, 0.80, 0.35];
const SHELL: Col = [0.62, 0.64, 0.68];
const SMF: Col = [0.95, 0.85, 0.30];
const OM4: Col = [0.45, 0.85, 0.85];
const DAC: Col = [0.16, 0.16, 0.18];
const INP: Col = [0.45, 0.42, 0.52];
const SILICON: Col = [0.50, 0.55, 0.64];
const COATING: Col = [0.90, 0.90, 0.92];
const ABSORB: Col = [0.25, 0.22, 0.32];
const MPO: Col = [0.25, 0.60, 0.40];
/// the light (infrared, drawn red-pink)
pub(super) const LIGHT: Col = [1.0, 0.35, 0.45];

fn col(s: &LinkState, p: LinkPart, c: Col) -> Col {
    stage::mix(QUIET, c, (1.0 - s.dim).max(s.hi[p as usize]))
}

fn glow(s: &LinkState, p: LinkPart, c: Col) -> Col {
    stage::scaled(c, 0.3 * s.hi[p as usize] * s.dim)
}

// ---------------------------------------------------------------- LINK station

/// Where the cable starts and the mirror plane between the two ends.
fn cable_x(s: &LinkState) -> (f64, f64, f64) {
    let x0 = 300.0;
    let x1 = x0 + 2200.0 * s.span.max(0.2);
    (x0, x1, (x0 + x1) / 2.0)
}

/// A box, mirrored across the plane x = mx when `mx` is given.
fn bx(m: &mut Vec<Tri>, mx: Option<f64>, lo: V3, hi: V3, c: Col, e: Col) {
    match mx {
        Some(x) => push_box(m, [2.0 * x - hi[0], lo[1], lo[2]], [2.0 * x - lo[0], hi[1], hi[2]], c, e),
        None => push_box(m, lo, hi, c, e),
    }
}

fn mp(mx: Option<f64>, p: V3) -> V3 {
    match mx {
        Some(x) => [2.0 * x - p[0], p[1], p[2]],
        None => p,
    }
}

/// Lane z positions for the side `sign` (+1 front, -1 back) of a module.
fn lane_z(s: &LinkState, sign: f64) -> Vec<f64> {
    let n = s.lanes.round().clamp(1.0, 8.0) as usize;
    (0..n).map(|i| sign * (10.0 + (i as f64 + 0.5) * 46.0 / n as f64)).collect()
}

/// One host (board, chip, traces, cage) and its module. `mx` mirrors it to the far
/// end; `tx` puts lasers at the front (+z) and photodiodes behind, `!tx` the reverse.
fn host(s: &LinkState, m: &mut Vec<Tri>, mx: Option<f64>, tx: bool) {
    let k = s.link;
    let opt = 1.0 - s.copper;
    bx(m, mx, [-1100.0, -24.0, -360.0], [0.0, 0.0, 360.0], col(s, LinkPart::Board, BOARD), NO_GLOW);
    bx(m, mx, [-950.0, 0.0, -200.0], [-550.0, 10.0, 200.0], col(s, LinkPart::Asic, SUBSTRATE), NO_GLOW);
    bx(m, mx, [-900.0, 10.0, -150.0], [-600.0, 10.0 + 30.0 * k, 150.0], col(s, LinkPart::Asic, ASIC), glow(s, LinkPart::Asic, ASIC));
    // copper traces to the cage, one per electrical lane
    for i in 0..8 {
        let z = -56.0 + i as f64 * 16.0;
        bx(m, mx, [-550.0, 0.0, z - 3.0], [-300.0, 1.5, z + 3.0], col(s, LinkPart::Trace, COPPER), glow(s, LinkPart::Trace, COPPER));
    }
    // front panel
    // front panel, cut away in front of the module so its inside shows
    bx(m, mx, [0.0, 0.0, -360.0], [14.0, 170.0 * k, -70.0], col(s, LinkPart::Panel, METAL), NO_GLOW);
    bx(m, mx, [0.0, 110.0, -70.0], [14.0, 110.0 + 60.0 * k, 70.0], col(s, LinkPart::Panel, METAL), NO_GLOW);
    // the module: tray, PCB, chips, optics, connector; a lid that slides shut
    let part = if mx.is_some() { LinkPart::RxModule } else { LinkPart::Module };
    let sc = col(s, part, SHELL);
    bx(m, mx, [-300.0, 6.0, -65.0], [300.0, 10.0, 65.0], sc, NO_GLOW);
    bx(m, mx, [-300.0, 6.0, -65.0], [300.0, 40.0, -61.0], sc, NO_GLOW);
    bx(m, mx, [290.0, 6.0, -65.0], [300.0, 86.0, 65.0], sc, NO_GLOW);
    if s.shell > 0.01 {
        let zc = -65.0 + 130.0 * s.shell;
        bx(m, mx, [-300.0, 82.0, -65.0], [300.0, 86.0, zc], sc, glow(s, part, SHELL));
        bx(m, mx, [-300.0, 6.0, zc - 4.0], [300.0, 86.0, zc], sc, NO_GLOW);
        // fins on the lid
        for i in 0..7 {
            let x = -240.0 + i as f64 * 80.0;
            bx(m, mx, [x, 86.0, -60.0], [x + 14.0, 104.0, (zc - 5.0).max(-60.0)], sc, NO_GLOW);
        }
    }
    bx(m, mx, [-295.0, 10.0, -58.0], [240.0, 14.0, 58.0], col(s, part, PCB), NO_GLOW);
    for i in 0..6 {
        let z = -45.0 + i as f64 * 18.0;
        bx(m, mx, [-300.0, 9.0, z - 5.0], [-272.0, 15.0, z + 5.0], col(s, part, GOLD), NO_GLOW);
    }
    let d = s.dsp * opt;
    if d > 0.01 {
        let dc = col(s, LinkPart::Dsp, DSP);
        let hot = stage::scaled([1.0, 0.4, 0.2], 0.3 * s.heat);
        bx(m, mx, [-155.0 - 45.0 * d, 14.0, -45.0 * d], [-155.0 + 45.0 * d, 14.0 + 12.0 * d, 45.0 * d], dc, [hot[0] + glow(s, LinkPart::Dsp, DSP)[0], hot[1] + glow(s, LinkPart::Dsp, DSP)[1], hot[2]]);
    }
    let (fz, bz): (f64, f64) = if tx { (1.0, -1.0) } else { (-1.0, 1.0) };
    if opt > 0.01 {
        // driver beside the lasers, TIA beside the photodiodes
        bx(m, mx, [-40.0, 14.0, (10.0 * fz).min(50.0 * fz)], [0.0, 14.0 + 8.0 * opt, (10.0 * fz).max(50.0 * fz)], col(s, LinkPart::Driver, CHIP), glow(s, LinkPart::Driver, CHIP));
        bx(m, mx, [-40.0, 14.0, (10.0 * bz).min(50.0 * bz)], [0.0, 14.0 + 8.0 * opt, (10.0 * bz).max(50.0 * bz)], col(s, LinkPart::Tia, CHIP), glow(s, LinkPart::Tia, CHIP));
        let lc = stage::mix([0.85, 0.40, 0.30], [0.40, 0.75, 0.80], s.mm);
        let n = lane_z(s, fz).len() as f64;
        let hw = (20.0 / n).min(5.0);
        for z in lane_z(s, fz) {
            bx(m, mx, [80.0, 14.0, z - hw], [110.0, 14.0 + 10.0 * opt, z + hw], col(s, LinkPart::Laser, lc), stage::scaled(LIGHT, 0.4 * s.light * opt));
            push_sphere(m, mp(mx, [140.0, 22.0, z]), 5.0 * opt, 6, col(s, LinkPart::Lens, GLASS), NO_GLOW);
        }
        for z in lane_z(s, bz) {
            bx(m, mx, [80.0, 14.0, z - hw], [110.0, 14.0 + 6.0 * opt, z + hw], col(s, LinkPart::Pd, [0.20, 0.25, 0.50]), glow(s, LinkPart::Pd, CYAN));
            push_sphere(m, mp(mx, [140.0, 20.0, z]), 5.0 * opt, 6, col(s, LinkPart::Lens, GLASS), NO_GLOW);
        }
        // fibre ribbon from the lenses to the connector
        let fc = stage::mix(SMF, OM4, s.mm);
        bx(m, mx, [150.0, 20.0, -56.0], [250.0, 24.0, 56.0], col(s, LinkPart::Connector, fc), NO_GLOW);
        bx(m, mx, [250.0, 26.0, -40.0], [290.0, 66.0, 40.0], col(s, LinkPart::Connector, MPO), glow(s, LinkPart::Connector, MPO));
    }
}

fn link(s: &LinkState, m: &mut Vec<Tri>) {
    let (x0, x1, mx) = cable_x(s);
    host(s, m, None, true);
    host(s, m, Some(mx), false);
    let c = stage::mix(stage::mix(SMF, OM4, s.mm), DAC, s.copper);
    crate::push_tube(m, [x0, 46.0, 0.0], [x1, 46.0, 0.0], 14.0 * s.link, 14, col(s, LinkPart::Cable, c), glow(s, LinkPart::Cable, c), true);
}

/// A PAM4 (or NRZ) level for symbol `i`, 0..3.
fn level(s: &LinkState, i: usize) -> f64 {
    const PAT: [f64; 16] = [3.0, 0.0, 2.0, 1.0, 3.0, 1.0, 0.0, 2.0, 2.0, 3.0, 0.0, 1.0, 3.0, 2.0, 0.0, 1.0];
    let p = PAT[i % 16];
    let nrz = if p >= 2.0 { 3.0 } else { 0.0 };
    nrz + (p - nrz) * s.pam4
}

fn link_overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    let (x0, x1, mx) = cable_x(s);
    let k = s.link;
    let opt = 1.0 - s.copper;
    let ec = s.elec * k;
    // electrical: host chip to the module, through the DSP, to the driver
    for (i, z) in [-40.0, -8.0, 24.0, 56.0].iter().enumerate() {
        let dz = 30.0 + i as f64 * 6.0;
        let path = [[-600.0, 25.0, *z], [-300.0, 8.0, *z], [-155.0, 28.0, z * 0.5], [-20.0, 24.0, dz], [95.0, 26.0, dz]];
        stage::particles(cv, cam, &path, 5, u * 2.0 + i as f64 * 0.21, 6.0, CYAN, ec);
        let back: Vec<V3> = path.iter().rev().map(|p| [2.0 * mx - p[0], p[1], -p[2]]).collect();
        stage::particles(cv, cam, &back, 5, u * 2.0 + i as f64 * 0.21 + 0.5, 6.0, CYAN, ec);
    }
    // copper cable: the electrical signal runs the whole way
    if s.copper > 0.01 {
        stage::particles(cv, cam, &[[290.0, 46.0, 0.0], [x1 + 10.0, 46.0, 0.0]], 12, u * 2.0, 9.0, CYAN, s.elec.max(0.6) * s.copper * k);
    }
    // light: lasers, lenses, connector, the cable, then the far photodiodes
    let la = s.light * opt * k;
    if la > 0.01 {
        for (i, z) in lane_z(s, 1.0).iter().enumerate().step_by(2) {
            let path = [[110.0, 20.0, *z], [140.0, 22.0, *z], [260.0, 46.0, z * 0.3], [x0, 46.0, 0.0]];
            stage::particles(cv, cam, &path, 3, u * 2.0 + i as f64 * 0.1, 5.0, LIGHT, la);
        }
        let n = 14;
        for i in 0..n {
            let t = (u * 2.0 + i as f64 / n as f64).rem_euclid(1.0);
            let x = x0 + (x1 - x0) * t;
            let lv = level(s, i);
            let fade = (std::f64::consts::PI * t).sin().sqrt();
            stage::dot(cv, cam, [x, 46.0, 15.0], 7.0 + 3.0 * lv, LIGHT, la * fade * (0.25 + 0.25 * lv));
        }
        for (i, z) in lane_z(s, 1.0).iter().enumerate().step_by(2) {
            let path = [[x1, 46.0, 0.0], [2.0 * mx - 260.0, 46.0, z * 0.3], [2.0 * mx - 140.0, 22.0, *z], [2.0 * mx - 95.0, 20.0, *z]];
            stage::particles(cv, cam, &path, 3, u * 2.0 + i as f64 * 0.1, 5.0, LIGHT, la);
        }
    }
    // symbol strip: each symbol a bar whose height is its level
    if s.bars > 0.01 {
        let n = 16;
        let (a, b) = (x0 + 200.0, x0 + 200.0 + (x1 - x0 - 400.0).min(1400.0));
        let c = stage::mix(CYAN, LIGHT, opt);
        for i in 0..n {
            let t = (i as f64 / n as f64 + u * 0.5).rem_euclid(1.0);
            let x = a + (b - a) * t;
            let fade = ((std::f64::consts::PI * t).sin()).sqrt() * s.bars * k;
            let h = 20.0 + 30.0 * level(s, i);
            cv.line(cam, [x, 140.0, 0.0], [x, 140.0 + h, 0.0], c, (0.9 * fade) as f32);
            cv.line(cam, [x + 6.0, 140.0, 0.0], [x + 6.0, 140.0 + h, 0.0], c, (0.9 * fade) as f32);
            stage::dot(cv, cam, [x + 3.0, 140.0 + h, 0.0], 6.0, c, fade);
        }
        for lv in 0..4 {
            let y = 160.0 + 30.0 * lv as f64;
            let show = if lv == 1 || lv == 2 { s.pam4 } else { 1.0 };
            cv.line(cam, [a, y, 0.0], [b, y, 0.0], GLASS, (0.25 * s.bars * k * show) as f32);
        }
    }
    // eye diagram over the DSP: many symbol transitions laid on top of each other
    if s.eye > 0.01 {
        let (cx, cy, w, hgt) = (-155.0, 240.0, 260.0, 150.0);
        let a = (s.eye * k) as f32;
        stage::glass_box(cv, cam, [cx - w / 2.0, cy - hgt / 2.0, 0.0], [cx + w / 2.0, cy + hgt / 2.0, 0.0], GLASS, a * 0.5);
        let lvy = |l: f64| cy - hgt * 0.4 + hgt * 0.8 * l / 3.0;
        for j in 0..28usize {
            let h1 = ((j * 7919 + 13) % 97) as f64 / 97.0;
            let h2 = ((j * 104729 + 7) % 89) as f64 / 89.0;
            let la = level(s, j);
            let lb = level(s, j * 5 + 3);
            let noise = (1.0 - s.eq) * 0.9 * (h1 - 0.5) + (1.0 - s.eq) * 0.4 * ((u * 3.0 + h2 * 6.0).sin());
            let mut prev: Option<V3> = None;
            for i in 0..=24 {
                let t = i as f64 / 24.0;
                let e = stage::smooth_step(0.3, 0.7, t);
                let l = la + (lb - la) * e + noise * (1.0 - (2.0 * e - 1.0).powi(2) * 0.3);
                let p = [cx - w / 2.0 + w * t, lvy(l), 0.0];
                if let Some(q) = prev {
                    cv.line(cam, q, p, CYAN, a * 0.55);
                }
                prev = Some(p);
            }
        }
    }
}

// ---------------------------------------------------------------- GLASS station

/// A glass tube along x: rings in the y-z plane and lines down its length.
fn glass_tube_x(cv: &mut Canvas, cam: &Cam, y: f64, z: f64, xa: f64, xb: f64, r: f64, c: Col, a: f32) {
    const SEG: usize = 40;
    let at = |x: f64, i: usize| {
        let th = std::f64::consts::TAU * i as f64 / SEG as f64;
        [x, y + r * th.cos(), z + r * th.sin()]
    };
    let rings = (((xb - xa) / 250.0).round() as usize).max(1);
    for k in 0..=rings {
        let x = xa + (xb - xa) * k as f64 / rings as f64;
        for i in 0..SEG {
            cv.line(cam, at(x, i), at(x, i + 1), c, a);
        }
    }
    for i in (0..SEG).step_by(4) {
        cv.line(cam, at(xa, i), at(xb, i), c, a * 0.7);
    }
}

fn core_r(s: &LinkState) -> f64 {
    (4.1 + (25.0 - 4.1) * s.mm) * UM
}

fn glass(s: &LinkState, m: &mut Vec<Tri>) {
    let k = s.glass;
    let z = GLASS_Z;
    let xc = -1000.0 + 650.0 * s.strip;
    crate::push_tube(m, [-1000.0, AXIS_Y, z], [xc.max(-990.0), AXIS_Y, z], 121.0 * UM * k, 40, col(s, LinkPart::Coating, COATING), glow(s, LinkPart::Coating, COATING), true);
}

fn glass_overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    let k = s.glass;
    let z = GLASS_Z;
    let rc = core_r(s);
    let a = k as f32;
    let cl = col(s, LinkPart::Cladding, GLASS);
    let cc = col(s, LinkPart::Core, PINK);
    glass_tube_x(cv, cam, AXIS_Y, z, -1000.0, 1000.0, 62.5 * UM, cl, a * 0.55);
    glass_tube_x(cv, cam, AXIS_Y, z, -1000.0, 1000.0, rc, cc, a * 0.9);
    // light: straight down the axis in single-mode; bouncing between the walls in
    // multimode (total internal reflection at the core edge)
    let amp = rc * 0.8 * s.tir;
    let n = 18;
    for i in 0..n {
        let t = (u * 1.0 + i as f64 / n as f64).rem_euclid(1.0);
        let x = -1000.0 + 2000.0 * t;
        let ph = (x + 1000.0) / 260.0;
        let tri = 2.0 * (ph - (ph + 0.5).floor()).abs() * 2.0 - 1.0;
        let y = AXIS_Y + amp * tri;
        let fade = (std::f64::consts::PI * t).sin().sqrt();
        let lost = 1.0 - 0.85 * s.loss * t;
        let lv = level(s, i);
        stage::dot(cv, cam, [x, y, z], 7.0 + 2.0 * lv, LIGHT, s.light * k * fade * lost * (0.35 + 0.2 * lv));
    }
    if s.tir > 0.01 {
        let mut prev: Option<V3> = None;
        for i in 0..=80 {
            let x = -1000.0 + 25.0 * i as f64;
            let ph = (x + 1000.0) / 260.0;
            let tri = 2.0 * (ph - (ph + 0.5).floor()).abs() * 2.0 - 1.0;
            let p = [x, AXIS_Y + amp * tri, z];
            if let Some(q) = prev {
                cv.line(cam, q, p, LIGHT, (0.35 * s.tir * k) as f32);
            }
            prev = Some(p);
        }
    }
}

// ---------------------------------------------------------------- LASER station

fn tube(m: &mut Vec<Tri>, a: V3, b: V3, r: f64, c: Col, e: Col) {
    crate::push_tube(m, a, b, r, 12, c, e, true);
}

fn laser(s: &LinkState, m: &mut Vec<Tri>) {
    let k = s.laser;
    let z = LASER_Z;
    // EML: one InP chip, a DFB laser section and an electro-absorption modulator
    let x = EML_X;
    push_box(m, [x - 250.0, 0.0, z - 90.0], [x + 150.0, 80.0 * k, z + 90.0], col(s, LinkPart::Eml, INP), glow(s, LinkPart::Eml, INP));
    push_box(m, [x - 250.0, 80.0, z - 10.0], [x - 10.0, 80.0 + 12.0 * k, z + 10.0], col(s, LinkPart::Eml, [0.85, 0.45, 0.35]), stage::scaled(LIGHT, 0.5 * s.light * k));
    push_box(m, [x + 10.0, 80.0, z - 10.0], [x + 150.0, 80.0 + 12.0 * k, z + 10.0], col(s, LinkPart::Eam, PURPLE), glow(s, LinkPart::Eam, PURPLE));
    push_box(m, [x - 200.0, 80.0, z + 18.0], [x - 60.0, 80.0 + 4.0 * k, z + 70.0], col(s, LinkPart::Eml, GOLD), NO_GLOW);
    push_box(m, [x + 40.0, 80.0, z + 18.0], [x + 130.0, 80.0 + 4.0 * k, z + 70.0], col(s, LinkPart::Eam, GOLD), NO_GLOW);
    push_sphere(m, [x + 300.0, 86.0, z], 40.0 * k, 16, col(s, LinkPart::Lens, GLASS), NO_GLOW);
    tube(m, [x + 420.0, 86.0, z], [x + 900.0, 86.0, z], 30.0 * k, col(s, LinkPart::Cable, COATING), NO_GLOW);
    // silicon photonics: a CW laser die feeding a Mach-Zehnder modulator
    let x = 0.0;
    let wg = col(s, LinkPart::Siph, [0.80, 0.85, 0.95]);
    push_box(m, [x - 400.0, 0.0, z - 200.0], [x + 400.0, 40.0 * k, z + 200.0], col(s, LinkPart::Siph, SILICON), glow(s, LinkPart::Siph, SILICON));
    push_box(m, [x - 520.0, 10.0, z - 40.0], [x - 410.0, 10.0 + 40.0 * k, z + 40.0], col(s, LinkPart::Laser, INP), stage::scaled(LIGHT, 0.4 * s.light * k));
    let r = 4.0 * k;
    let y = 42.0;
    tube(m, [x - 410.0, y, z], [x - 250.0, y, z], r, wg, NO_GLOW);
    for sz in [-1.0, 1.0] {
        tube(m, [x - 250.0, y, z], [x - 160.0, y, z + 60.0 * sz], r, wg, NO_GLOW);
        tube(m, [x - 160.0, y, z + 60.0 * sz], [x + 160.0, y, z + 60.0 * sz], r, col(s, LinkPart::Mzm, [0.80, 0.85, 0.95]), glow(s, LinkPart::Mzm, CYAN));
        tube(m, [x + 160.0, y, z + 60.0 * sz], [x + 250.0, y, z], r, wg, NO_GLOW);
        push_box(m, [x - 130.0, 40.0, z + 60.0 * sz + 10.0 * sz - 8.0], [x + 130.0, 40.0 + 6.0 * k, z + 60.0 * sz + 10.0 * sz + 8.0], col(s, LinkPart::Mzm, GOLD), NO_GLOW);
    }
    tube(m, [x + 250.0, y, z], [x + 330.0, y, z], r, wg, NO_GLOW);
    for i in 0..6 {
        let gx = x + 335.0 + i as f64 * 9.0;
        push_box(m, [gx, 40.0, z - 20.0], [gx + 4.0, 40.0 + 4.0 * k, z + 20.0], wg, NO_GLOW);
    }
    tube(m, [x + 360.0, 60.0, z], [x + 440.0, 560.0, z], 20.0 * k, col(s, LinkPart::Cable, COATING), NO_GLOW);
    // VCSEL: light leaves the top of a mirror-stack mesa, straight into multimode fiber
    let x = VCSEL_X;
    push_box(m, [x - 250.0, 0.0, z - 250.0], [x + 250.0, 40.0 * k, z + 250.0], col(s, LinkPart::Vcsel, [0.40, 0.42, 0.48]), NO_GLOW);
    for i in 0..10 {
        let y0 = 40.0 + i as f64 * 5.0;
        let c = if i % 2 == 0 { [0.70, 0.66, 0.60] } else { [0.45, 0.45, 0.55] };
        crate::push_tube(m, [x, y0, z], [x, y0 + 5.0 * k, z], 50.0, 24, col(s, LinkPart::Vcsel, c), NO_GLOW, true);
    }
    crate::push_tube(m, [x, 90.0, z], [x, 90.0 + 6.0 * k, z], 50.0, 24, col(s, LinkPart::Vcsel, [0.9, 0.4, 0.4]), stage::scaled(LIGHT, 0.6 * s.light * k), true);
    for i in 0..8 {
        let y0 = 96.0 + i as f64 * 5.0;
        let c = if i % 2 == 0 { [0.70, 0.66, 0.60] } else { [0.45, 0.45, 0.55] };
        crate::push_tube(m, [x, y0, z], [x, y0 + 5.0 * k, z], 50.0, 24, col(s, LinkPart::Vcsel, c), NO_GLOW, true);
    }
    tube(m, [x, 520.0, z], [x, 1000.0, z], 60.0 * k, col(s, LinkPart::Cable, OM4), NO_GLOW);
}

fn laser_overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    let k = s.laser;
    let z = LASER_Z;
    let la = s.light * k;
    // EML: steady light in the laser section, pulses after the modulator
    let x = EML_X;
    stage::particles(cv, cam, &[[x - 240.0, 92.0, z], [x - 10.0, 92.0, z]], 6, u * 2.0, 6.0, LIGHT, la);
    pulses(cv, cam, s, &[[x + 10.0, 92.0, z], [x + 150.0, 90.0, z], [x + 300.0, 86.0, z], [x + 900.0, 86.0, z]], u, la);
    for sz in [-1.0, 1.0] {
        cv.line(cam, [x + 150.0, 86.0, z], [x + 260.0, 86.0 + 36.0 * sz, z], LIGHT, (0.35 * la) as f32);
        cv.line(cam, [x + 150.0, 86.0, z], [x + 260.0, 86.0, z + 36.0 * sz], LIGHT, (0.35 * la) as f32);
    }
    // SiPh: light splits into both arms and recombines; the arms' phase sets the output
    let x = 0.0;
    stage::particles(cv, cam, &[[x - 410.0, 46.0, z], [x - 250.0, 46.0, z]], 4, u * 2.0, 6.0, LIGHT, la);
    for sz in [-1.0, 1.0] {
        stage::particles(cv, cam, &[[x - 250.0, 46.0, z], [x - 160.0, 46.0, z + 60.0 * sz], [x + 160.0, 46.0, z + 60.0 * sz], [x + 250.0, 46.0, z]], 7, u * 2.0 + 0.3, 6.0, LIGHT, la * 0.8);
    }
    pulses(cv, cam, s, &[[x + 250.0, 46.0, z], [x + 360.0, 50.0, z], [x + 440.0, 560.0, z]], u, la);
    // VCSEL: straight up
    let x = VCSEL_X;
    pulses(cv, cam, s, &[[x, 140.0, z], [x, 1000.0, z]], u, la);
    for (dx, dz) in [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)] {
        cv.line(cam, [x + 40.0 * dx, 136.0, z + 40.0 * dz], [x + 60.0 * dx, 520.0, z + 60.0 * dz], LIGHT, (0.3 * la) as f32);
    }
    ring(cv, cam, [x, 137.0, z], 46.0, GOLD, (0.9 * k) as f32);
}

/// Light pulses along `pts` whose brightness follows the symbol levels.
fn pulses(cv: &mut Canvas, cam: &Cam, s: &LinkState, pts: &[V3], u: f64, a: f64) {
    if a <= 0.004 {
        return;
    }
    let n = 10;
    for i in 0..n {
        let t = (u * 2.0 + i as f64 / n as f64).rem_euclid(1.0);
        let lv = level(s, i);
        let fade = (std::f64::consts::PI * t).sin().sqrt();
        stage::dot(cv, cam, stage::along(pts, t), 6.0 + 2.5 * lv, LIGHT, a * fade * (0.15 + 0.28 * lv));
    }
}

// ---------------------------------------------------------------- PD station

fn pd(s: &LinkState, m: &mut Vec<Tri>) {
    let k = s.pd;
    let z = PD_Z;
    push_box(m, [-220.0, 0.0, z - 220.0], [220.0, 50.0 * k, z + 220.0], col(s, LinkPart::Absorber, INP), NO_GLOW);
    push_box(m, [-150.0, 50.0, z - 150.0], [150.0, 50.0 + 10.0 * k, z + 150.0], col(s, LinkPart::Absorber, [0.50, 0.48, 0.60]), NO_GLOW);
    push_box(m, [-110.0, 60.0, z - 110.0], [110.0, 60.0 + 50.0 * k, z + 110.0], col(s, LinkPart::Absorber, ABSORB), glow(s, LinkPart::Absorber, PURPLE));
    push_box(m, [-100.0, 110.0, z - 100.0], [100.0, 110.0 + 10.0 * k, z + 100.0], col(s, LinkPart::Absorber, [0.55, 0.50, 0.62]), NO_GLOW);
    let gc = col(s, LinkPart::Absorber, GOLD);
    for (lo, hi) in [
        ([-100.0, -100.0], [100.0, -80.0]),
        ([-100.0, 80.0], [100.0, 100.0]),
        ([-100.0, -80.0], [-80.0, 80.0]),
        ([80.0, -80.0], [100.0, 80.0]),
    ] {
        push_box(m, [lo[0], 120.0, z + lo[1]], [hi[0], 120.0 + 8.0 * k, z + hi[1]], gc, NO_GLOW);
    }
    push_box(m, [130.0, 60.0, z - 60.0], [200.0, 60.0 + 6.0 * k, z + 60.0], gc, NO_GLOW);
    tube(m, [0.0, 350.0, z], [0.0, 900.0, z], 60.0 * k, col(s, LinkPart::Cable, COATING), NO_GLOW);
    // wire to the TIA and the TIA chip
    tube(m, [90.0, 128.0, z], [450.0, 60.0, z], 4.0 * k, gc, NO_GLOW);
    push_box(m, [450.0, 0.0, z - 80.0], [650.0, 40.0 * k, z + 80.0], col(s, LinkPart::Amp, DSP), glow(s, LinkPart::Amp, DSP));
}

fn pd_overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    let k = s.pd;
    let z = PD_Z;
    pulses(cv, cam, s, &[[0.0, 900.0, z], [0.0, 90.0, z]], u, s.light * k);
    for sz in [-1.0, 1.0] {
        cv.line(cam, [50.0 * sz, 350.0, z], [80.0 * sz, 120.0, z], LIGHT, (0.3 * s.light * k) as f32);
    }
    // each absorbed photon frees an electron (to the n side) and a hole (to the ring)
    let c = s.carriers * s.light * k;
    for j in 0..6 {
        let xz = ((j * 37) % 7) as f64 * 30.0 - 90.0;
        let zz = ((j * 53) % 5) as f64 * 40.0 - 80.0;
        stage::particles(cv, cam, &[[xz, 85.0, z + zz], [xz * 1.2, 52.0, z + zz], [165.0, 62.0, z]], 2, u * 2.0 + j as f64 * 0.17, 6.0, CYAN, c);
        stage::particles(cv, cam, &[[xz, 85.0, z + zz], [xz, 118.0, z + zz], [90.0, 124.0, z + 90.0]], 2, u * 2.0 + j as f64 * 0.17 + 0.5, 6.0, ORANGE, c);
    }
    stage::particles(cv, cam, &[[90.0, 128.0, z], [450.0, 60.0, z]], 4, u * 2.0, 6.0, YELLOW, c);
    stage::particles(cv, cam, &[[650.0, 30.0, z], [1050.0, 30.0, z]], 6, u * 2.0, 7.0, CYAN, s.light * k);
}

// ---------------------------------------------------------------- CPO station

/// Optical engine centres (x, z) around the switch chip.
fn engines_xz() -> [(f64, f64); 8] {
    [(-170.0, 380.0), (170.0, 380.0), (380.0, -170.0), (380.0, 170.0), (-170.0, -380.0), (170.0, -380.0), (-380.0, -170.0), (-380.0, 170.0)]
}

/// The panel slot for engine `i`, ordered by where the engine sits so nothing crosses.
fn plug_z(i: usize) -> f64 {
    let (ex, ez) = engines_xz()[i];
    (ez * 1.35 + ex * 0.25).clamp(-640.0, 640.0)
}

/// A fibre from engine `i` up over the package and across to its panel slot.
fn fibre_path(i: usize, z: f64) -> [V3; 3] {
    let (ex, ez) = engines_xz()[i];
    [[ex, 56.0, z + ez], [ex + 40.0, 95.0, z + ez], [1750.0, 95.0, z + plug_z(i)]]
}

fn cpo(s: &LinkState, m: &mut Vec<Tri>) {
    let k = s.cpo;
    let z = CPO_Z;
    let e = s.engines;
    push_box(m, [-900.0, -30.0, z - 900.0], [1900.0, -2.0 + 2.0 * k, z + 900.0], col(s, LinkPart::Board, BOARD), NO_GLOW);
    push_box(m, [-520.0, 0.0, z - 520.0], [520.0, 30.0 * k, z + 520.0], col(s, LinkPart::Switch, SUBSTRATE), NO_GLOW);
    push_box(m, [-230.0, 30.0, z - 230.0], [230.0, 30.0 + 40.0 * k, z + 230.0], col(s, LinkPart::Switch, ASIC), glow(s, LinkPart::Switch, ASIC));
    push_box(m, [1750.0, 0.0, z - 800.0], [1770.0, 200.0 * k, z + 800.0], col(s, LinkPart::Panel, METAL), NO_GLOW);
    let hot = stage::scaled([1.0, 0.4, 0.2], 0.3 * s.heat);
    // traces from the chip to each optic: to the panel, or a short hop to an engine
    for (i, (ex, ez)) in engines_xz().iter().enumerate() {
        let start = [ex.clamp(-230.0, 230.0), 31.0, z + ez.clamp(-230.0, 230.0)];
        let plug = [1450.0, 2.0, z + plug_z(i)];
        let eng = [*ex, 31.0, z + ez];
        let end = [plug[0] + (eng[0] - plug[0]) * e, plug[1] + (eng[1] - plug[1]) * e, plug[2] + (eng[2] - plug[2]) * e];
        let st = [start[0], 2.0 + 29.0 * e, start[2]];
        tube(m, st, end, 3.0 * k, col(s, LinkPart::Trace, COPPER), glow(s, LinkPart::Trace, COPPER));
        // engine: photonic chip with its electronic chip on top, fibres out to the panel
        if e > 0.01 {
            let h = 55.0 * e;
            push_box(m, [ex - h, 30.0, z + ez - h], [ex + h, 30.0 + 14.0 * e, z + ez + h], col(s, LinkPart::Engine, SILICON), glow(s, LinkPart::Engine, SILICON));
            push_box(m, [ex - h * 0.6, 44.0, z + ez - h * 0.6], [ex + h * 0.6, 44.0 + 10.0 * e, z + ez + h * 0.6], col(s, LinkPart::Engine, DSP), hot);
            let f = fibre_path(i, z);
            tube(m, f[0], f[1], 4.0 * e, col(s, LinkPart::Cable, SMF), NO_GLOW);
            tube(m, f[1], f[2], 4.0 * e, col(s, LinkPart::Cable, SMF), NO_GLOW);
        }
        // pluggable at the panel
        let p = 1.0 - e;
        if p > 0.01 {
            let pz = plug_z(i);
            push_box(m, [1450.0, 0.0, z + pz - 36.0], [1450.0 + 300.0 * p, 60.0 * p, z + pz + 36.0], col(s, LinkPart::Plug, SHELL), hot);
        }
    }
    // external laser sources at the panel feed the engines
    if e > 0.01 {
        for sz in [-1.0, 1.0] {
            push_box(m, [1500.0, 0.0, z + 720.0 * sz - 50.0], [1500.0 + 240.0 * e, 60.0 * e, z + 720.0 * sz + 50.0], col(s, LinkPart::Els, [0.85, 0.50, 0.35]), stage::scaled(LIGHT, 0.3 * e * s.light));
        }
    }
}

fn cpo_overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    let k = s.cpo;
    let z = CPO_Z;
    let e = s.engines;
    for (i, (ex, ez)) in engines_xz().iter().enumerate() {
        let plug = [1450.0, 30.0, z + plug_z(i)];
        let eng = [*ex, 50.0, z + ez];
        let end = [plug[0] + (eng[0] - plug[0]) * e, plug[1] + (eng[1] - plug[1]) * e, plug[2] + (eng[2] - plug[2]) * e];
        stage::particles(cv, cam, &[[ex * 0.3, 72.0, z + ez * 0.3], end], 4, u * 2.0 + i as f64 * 0.11, 7.0, CYAN, s.elec * k);
        if e > 0.5 {
            stage::particles(cv, cam, &fibre_path(i, z), 5, u * 2.0 + i as f64 * 0.11, 6.0, LIGHT, s.light * k * (e - 0.5) * 2.0);
        } else {
            stage::particles(cv, cam, &[[1770.0, 30.0, z + plug_z(i)], [2100.0, 30.0, z + plug_z(i)]], 3, u * 2.0 + i as f64 * 0.11, 6.0, LIGHT, s.light * k * (1.0 - 2.0 * e));
        }
    }
    // the micro-ring modulator on one engine
    let (ex, ez) = engines_xz()[3];
    let a = (s.hi[LinkPart::Ring as usize].max(0.3) * e * k) as f32;
    ring(cv, cam, [ex + 20.0, 45.0, z + ez + 20.0], 24.0, CYAN, a);
    cv.line(cam, [ex - 40.0, 45.0, z + ez + 40.0], [ex + 50.0, 45.0, z + ez + 40.0], GLASS, a);
    // heat
    if s.heat > 0.01 {
        for j in 0..8 {
            let (x, zz, y0) = if e < 0.5 { (1600.0, plug_z(j), 60.0) } else { (engines_xz()[j].0, engines_xz()[j].1, 55.0) };
            let st = s.heat * k * (1.0 - (2.0 * e - 1.0).abs() * 0.0);
            stage::particles(cv, cam, &[[x, y0, z + zz], [x, y0 + 260.0, z + zz]], 3, u * 1.0 + j as f64 * 0.17, 9.0, [1.0, 0.45, 0.25], st);
        }
    }
}

// ---------------------------------------------------------------- shared

pub(super) fn solids(s: &LinkState, m: &mut Vec<Tri>) {
    if s.link > 0.01 {
        link(s, m);
    }
    if s.glass > 0.01 {
        glass(s, m);
    }
    if s.laser > 0.01 {
        laser(s, m);
    }
    if s.pd > 0.01 {
        pd(s, m);
    }
    if s.cpo > 0.01 {
        cpo(s, m);
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, s: &LinkState, u: f64) {
    if s.link > 0.01 {
        link_overlay(cv, cam, s, u);
    }
    if s.glass > 0.01 {
        glass_overlay(cv, cam, s, u);
    }
    if s.laser > 0.01 {
        laser_overlay(cv, cam, s, u);
    }
    if s.pd > 0.01 {
        pd_overlay(cv, cam, s, u);
    }
    if s.cpo > 0.01 {
        cpo_overlay(cv, cam, s, u);
    }
    let _ = (GREEN, TEXT);
}

pub fn link_part_at(p: LinkPart, s: &LinkState) -> V3 {
    let (x0, x1, mx) = cable_x(s);
    let rc = core_r(s);
    let (ex, ez) = engines_xz()[1];
    match p {
        LinkPart::Asic => [-700.0, 40.0, 150.0],
        LinkPart::Board => [-950.0, 0.0, 360.0],
        LinkPart::Trace => [-420.0, 2.0, 60.0],
        LinkPart::Panel => [7.0, 170.0, -70.0],
        LinkPart::Module => [180.0, 104.0, 65.0],
        LinkPart::Dsp => [-155.0 + 45.0 * s.dsp, 26.0, 45.0 * s.dsp],
        LinkPart::Driver => [-20.0, 22.0, 50.0],
        LinkPart::Laser => [100.0, 24.0, 56.0],
        LinkPart::Lens => [140.0, 28.0, 56.0],
        LinkPart::Connector => [280.0, 66.0, 40.0],
        LinkPart::Cable => [x0 + (x1 - x0) * 0.5, 60.0, 14.0],
        LinkPart::RxModule => [2.0 * mx - 180.0, 104.0, 65.0],
        LinkPart::Pd => [2.0 * mx - 100.0, 20.0, 56.0],
        LinkPart::Tia => [2.0 * mx + 20.0, 22.0, 50.0],
        LinkPart::Eye => [-25.0, 315.0, 0.0],
        LinkPart::Symbols => [x0 + 200.0 + (x1 - x0 - 400.0).min(1400.0), 240.0, 0.0],
        LinkPart::Core => [1000.0, AXIS_Y + rc, GLASS_Z],
        LinkPart::Cladding => [500.0, AXIS_Y, GLASS_Z + 62.5 * UM],
        LinkPart::Coating => [-1000.0 + 650.0 * s.strip, AXIS_Y + 121.0 * UM * 0.7, GLASS_Z + 121.0 * UM * 0.7],
        LinkPart::Eml => [EML_X - 150.0, 80.0, LASER_Z + 90.0],
        LinkPart::Eam => [EML_X + 100.0, 92.0, LASER_Z + 10.0],
        LinkPart::Siph => [300.0, 40.0, LASER_Z + 200.0],
        LinkPart::Mzm => [0.0, 46.0, LASER_Z + 70.0],
        LinkPart::Vcsel => [VCSEL_X + 50.0, 120.0, LASER_Z + 50.0],
        LinkPart::Absorber => [110.0, 90.0, PD_Z + 110.0],
        LinkPart::Amp => [600.0, 40.0, PD_Z + 80.0],
        LinkPart::Switch => [200.0, 70.0, CPO_Z + 230.0],
        LinkPart::Plug => [1700.0, 60.0 * (1.0 - s.engines), CPO_Z + plug_z(7) + 60.0],
        LinkPart::Engine => [ex + 55.0, 54.0, CPO_Z + ez + 55.0],
        LinkPart::Els => [1740.0, 60.0, CPO_Z + 770.0],
        LinkPart::Ring => {
            let (rx, rz) = engines_xz()[3];
            [rx + 36.0, 45.0, CPO_Z + rz + 20.0]
        }
    }
}

pub fn link_part_col(p: LinkPart) -> Col {
    match p {
        LinkPart::Asic | LinkPart::Switch => [0.78, 0.68, 0.98],
        LinkPart::Dsp | LinkPart::Amp | LinkPart::Tia | LinkPart::Engine => CYAN,
        LinkPart::Laser | LinkPart::Eml | LinkPart::Vcsel | LinkPart::Els => [1.0, 0.55, 0.55],
        LinkPart::Core => PINK,
        LinkPart::Cladding | LinkPart::Lens => GLASS,
        LinkPart::Cable | LinkPart::Connector => SMF,
        LinkPart::Trace => COPPER,
        LinkPart::Board => GREEN,
        LinkPart::Eam | LinkPart::Mzm | LinkPart::Absorber => PURPLE,
        LinkPart::Ring | LinkPart::Eye | LinkPart::Pd => CYAN,
        LinkPart::Symbols => LIGHT,
        _ => TEXT,
    }
}

pub(super) fn labels(cv: &mut Canvas, cam: &Cam, s: &LinkState, list: &[(LinkPart, &str)], a: f64, out: &mut Vec<Rect>) {
    for (i, (p, t)) in list.iter().enumerate() {
        let at = link_part_at(*p, s);
        let left = cam.project(at).is_some_and(|(x, _, _)| x < cv.w as f64 * 0.5);
        let w = stage::text_w(&t.to_ascii_uppercase(), stage::text_scale(cv)) as f64 / cv.h as f64;
        let dx = if left { -0.05 - w } else { 0.05 };
        let dy = if i % 2 == 0 { -0.07 } else { 0.06 };
        out.extend(label(cv, cam, at, (dx, dy), t, link_part_col(*p), a));
    }
}
