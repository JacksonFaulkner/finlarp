//! The transistor every Chip-tab scene shares, from substrate to top metal.
//!
//! One model morphs between the three generations: planar (a channel on the surface),
//! FinFET (the channel rises into fins the gate drapes over) and gate-all-around
//! (each fin splits into stacked sheets the gate fills between). NMOS and PMOS differ
//! in colour and carrier. Above sit contacts, then the metal stack: two thin layers,
//! two intermediate, two thick top layers. Every quantity is a float, so a scene can
//! blend between any two states without a cut.
//!
//! Geometry, schematic units (not to scale), Y up: silicon surface at y = 0, source at
//! -x, drain at +x, channel width along z.

use super::super::push_box;
use super::super::push_sphere;
use super::super::stage::{self, label, particles, Rect, CYAN, GLASS, GREEN, METAL, NO_GLOW, ORANGE, PINK, PURPLE, QUIET, STEEL, TEXT, YELLOW};
use crate::{Cam, Canvas, Col, Tri, V3};

/// The parts a label, a highlight or a note can point at.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ChipPart {
    Substrate,
    Well,
    Sti,
    Source,
    Drain,
    Channel,
    Gate,
    Oxide,
    Spacer,
    Silicide,
    Contact,
    ThinMetal,
    MidMetal,
    TopMetal,
    Via,
    Depletion,
    Inversion,
    Fin,
    Sheet,
    Dopants,
    Halo,
    Drift,
}

pub const PARTS: usize = 22;

impl ChipPart {
    fn idx(self) -> usize {
        self as usize
    }
}

/// The transistor and its stack at one instant. All fields blend linearly.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct ChipState {
    /// 0 planar, 1 FinFET, 2 gate-all-around
    pub arch: f64,
    /// 0 NMOS (n+ source/drain, electrons), 1 PMOS (p+, holes)
    pub pmos: f64,
    /// gate voltage, 0 off .. 1 on
    pub vg: f64,
    /// drain voltage, 0 .. 1
    pub vd: f64,
    /// depletion region under the gate, 0..1
    pub depletion: f64,
    /// inversion layer (the channel), 0..1
    pub inversion: f64,
    /// pinch-off at the drain end (saturation), 0..1
    pub pinch: f64,
    /// carriers flowing source to drain, 0..1
    pub flow: f64,
    /// leakage: carriers sneaking under the channel and through the oxide, 0..1
    pub leak: f64,
    /// gate length factor, 1 = drawn length, smaller = shrunk
    pub gate_len: f64,
    /// high-k dielectric shown thick and bright, 0 thin SiO2 .. 1 high-k
    pub hik: f64,
    /// metal gate (1) vs polysilicon (0)
    pub metal_gate: f64,
    /// strain arrows along the channel, 0..1
    pub strain: f64,
    /// contact plugs, 0 none .. 1 full height
    pub contacts: f64,
    /// silicide on the source/drain tops, 0..1
    pub silicide: f64,
    /// metal layers shown, 0..6 (2 thin, 2 intermediate, 2 top)
    pub metal: f64,
    /// signal pulses up the contacts and along the metal, 0..1
    pub signal: f64,
    /// layers pulled apart vertically, 0..1
    pub explode: f64,
    /// transistors in a row, 1..5
    pub cells: f64,
    /// front half of the gate and source/drain cut away, 0..1
    pub cut: f64,
    /// dopant atoms in the source/drain, 0..1
    pub dopants: f64,
    /// halo pockets beside the channel, 0..1
    pub halo: f64,
    /// heat in the top metal (current crowding), 0..1
    pub heat: f64,
    /// CMOS pair: odd cells take the opposite polarity, with their own flow, 0/1
    pub pair: f64,
    /// flow and inversion in the odd (paired) cells
    pub flow2: f64,
    pub inv2: f64,
    /// FD-SOI: a buried oxide under a thin silicon film, 0..1
    pub soi: f64,
    /// fins per transistor, 1..3 (rounded)
    pub fins: f64,
    /// GAA before release: the gaps between sheets are still sacrificial SiGe, 0..1
    pub sige: f64,
    /// backside power rails under a thinned substrate, 0..1
    pub backside: f64,
    /// how much everything not highlighted greys out, 0..1
    pub dim: f64,
    /// highlight per part (ChipPart order), 0..1
    pub hi: [f64; PARTS],
}

impl ChipState {
    /// A planar NMOS, off, no stack: the starting point every scene edits.
    pub const BASE: ChipState = ChipState {
        arch: 0.0,
        pmos: 0.0,
        vg: 0.0,
        vd: 0.0,
        depletion: 0.0,
        inversion: 0.0,
        pinch: 0.0,
        flow: 0.0,
        leak: 0.0,
        gate_len: 1.0,
        hik: 0.5,
        metal_gate: 1.0,
        strain: 0.0,
        contacts: 0.0,
        silicide: 0.0,
        metal: 0.0,
        signal: 0.0,
        explode: 0.0,
        cells: 1.0,
        cut: 0.0,
        dopants: 0.0,
        halo: 0.0,
        heat: 0.0,
        pair: 0.0,
        flow2: 0.0,
        inv2: 0.0,
        soi: 0.0,
        fins: 2.0,
        sige: 0.0,
        backside: 0.0,
        dim: 0.0,
        hi: [0.0; PARTS],
    };

    /// The same state with one part highlighted and the rest greyed.
    pub const fn spot(mut self, p: ChipPart) -> ChipState {
        self.dim = 0.85;
        self.hi[p as usize] = 1.0;
        self
    }

    pub(super) fn lerp(a: &ChipState, b: &ChipState, k: f64) -> ChipState {
        let l = |x: f64, y: f64| x + (y - x) * k;
        let mut hi = [0.0; PARTS];
        for i in 0..PARTS {
            hi[i] = l(a.hi[i], b.hi[i]);
        }
        ChipState {
            arch: l(a.arch, b.arch),
            pmos: l(a.pmos, b.pmos),
            vg: l(a.vg, b.vg),
            vd: l(a.vd, b.vd),
            depletion: l(a.depletion, b.depletion),
            inversion: l(a.inversion, b.inversion),
            pinch: l(a.pinch, b.pinch),
            flow: l(a.flow, b.flow),
            leak: l(a.leak, b.leak),
            gate_len: l(a.gate_len, b.gate_len),
            hik: l(a.hik, b.hik),
            metal_gate: l(a.metal_gate, b.metal_gate),
            strain: l(a.strain, b.strain),
            contacts: l(a.contacts, b.contacts),
            silicide: l(a.silicide, b.silicide),
            metal: l(a.metal, b.metal),
            signal: l(a.signal, b.signal),
            explode: l(a.explode, b.explode),
            cells: l(a.cells, b.cells),
            cut: l(a.cut, b.cut),
            dopants: l(a.dopants, b.dopants),
            halo: l(a.halo, b.halo),
            heat: l(a.heat, b.heat),
            pair: l(a.pair, b.pair),
            flow2: l(a.flow2, b.flow2),
            inv2: l(a.inv2, b.inv2),
            soi: l(a.soi, b.soi),
            fins: l(a.fins, b.fins),
            sige: l(a.sige, b.sige),
            backside: l(a.backside, b.backside),
            dim: l(a.dim, b.dim),
            hi,
        }
    }
}

// ---- geometry -------------------------------------------------------------------

const N_PLUS: Col = [0.36, 0.55, 0.95];
const P_PLUS: Col = [0.95, 0.45, 0.62];
const SUB_P: Col = [0.34, 0.30, 0.42];
const SUB_N: Col = [0.28, 0.34, 0.46];
const SILICON: Col = [0.62, 0.84, 0.70];
const GATE_METAL: Col = [0.52, 0.56, 0.66];
const POLY: Col = [0.72, 0.60, 0.42];
const HIK: Col = [0.95, 0.85, 0.35];
const SPACER: Col = [0.48, 0.50, 0.56];
const SILICIDE: Col = [0.45, 0.42, 0.55];
const TUNGSTEN: Col = [0.70, 0.72, 0.78];
const COPPER: Col = [0.95, 0.62, 0.30];
const ELECTRON: Col = CYAN;
const HOLE: Col = ORANGE;

pub(super) const CELL_DX: f64 = 620.0;
const FIN_H: f64 = 60.0;
const GATE_H: f64 = 50.0;
const SD_X0: f64 = 70.0;
const SD_X1: f64 = 240.0;
const CONTACT_H: f64 = 110.0;
/// metal layers: (thickness, wire width, gap above the previous)
const LAYERS: [(f64, f64, f64); 6] = [(10.0, 14.0, 40.0), (10.0, 14.0, 30.0), (18.0, 26.0, 40.0), (18.0, 26.0, 36.0), (34.0, 50.0, 50.0), (34.0, 50.0, 46.0)];

fn colour(s: &ChipState, p: ChipPart, c: Col) -> Col {
    let keep = (1.0 - s.dim).max(s.hi[p.idx()]);
    stage::mix(QUIET, c, keep)
}

fn glow(s: &ChipState, p: ChipPart) -> f64 {
    s.hi[p.idx()] * s.dim
}

pub(super) fn half_len(s: &ChipState) -> f64 {
    60.0 * s.gate_len
}

pub(super) fn fin_h(s: &ChipState) -> f64 {
    FIN_H * s.arch.clamp(0.0, 1.0)
}

/// The fins (or the planar slab they merge into): centre z and half width.
fn fins(s: &ChipState) -> Vec<(f64, f64)> {
    let f = s.arch.clamp(0.0, 1.0);
    let g = (s.arch - 1.0).clamp(0.0, 1.0);
    let n = s.fins.round().clamp(1.0, 3.0) as usize;
    // planar: one wide slab whatever the fin count
    let n = if f < 0.05 { 1 } else { n };
    let hw_fin = 12.0 + (30.0 - 12.0) * g;
    let hw = 120.0 + (hw_fin - 120.0) * f;
    let pitch = 124.0 * f;
    (0..n).map(|i| ((i as f64 - (n as f64 - 1.0) / 2.0) * pitch, if n == 1 { hw.max(hw_fin) } else { hw_fin.max(hw.min(55.0)) })).collect()
}

/// Sheets per fin: (bottom, top) heights. One block for planar/FinFET, three for GAA.
fn sheets(s: &ChipState) -> Vec<(f64, f64)> {
    let h = fin_h(s);
    let g = (s.arch - 1.0).clamp(0.0, 1.0);
    if g < 0.01 {
        return vec![(0.0, h)];
    }
    let gap = 12.0 * g;
    let t = (h - 3.0 * gap) / 3.0;
    (0..3).map(|i| (gap + i as f64 * (t + gap), gap + i as f64 * (t + gap) + t)).collect()
}

/// Vertical lift of each layer group when the stack is exploded.
fn lift(s: &ChipState, level: usize) -> f64 {
    s.explode * 55.0 * level as f64
}

/// Bottom of the contact level and of each metal layer.
pub(super) fn contact_base(s: &ChipState) -> f64 {
    fin_h(s) + GATE_H + lift(s, 1)
}

pub(super) fn layer_y(s: &ChipState, i: usize) -> f64 {
    let mut y = fin_h(s) + GATE_H + CONTACT_H;
    for j in 0..=i {
        y += LAYERS[j].2;
        if j < i {
            y += LAYERS[j].0;
        }
    }
    y + lift(s, i + 2)
}

fn cell_xs(s: &ChipState) -> Vec<(f64, f64)> {
    let n = s.cells.max(1.0);
    let whole = n.ceil() as usize;
    (0..whole)
        .map(|i| {
            let presence = (n - i as f64).clamp(0.0, 1.0);
            let x = (i as f64 - (n - 1.0) / 2.0) * CELL_DX;
            (x, presence)
        })
        .collect()
}

/// The state as cell `i` sees it: in a CMOS pair, odd cells are the other polarity
/// and carry their own channel.
fn cell_state(s: &ChipState, i: usize) -> ChipState {
    if s.pair > 0.5 && i % 2 == 1 {
        ChipState { pmos: 1.0 - s.pmos, flow: s.flow2, inversion: s.inv2, vg: 1.0 - s.vg, ..*s }
    } else {
        *s
    }
}

fn transistor(s: &ChipState, m: &mut Vec<Tri>, ox: f64, k: f64) {
    let pm = s.pmos;
    let sd = stage::mix(N_PLUS, P_PLUS, pm);
    let hl = half_len(s);
    let fh = fin_h(s);
    // cut: the drain half is removed, leaving a face across the gate at x = ox
    let zc = 0.0;
    let keep = 1.0 - s.cut;
    // well under the transistor (n-well for PMOS)
    push_box(m, [ox - 280.0, -120.0 * k, -150.0], [ox + 280.0 * keep, -2.0, 150.0], colour(s, ChipPart::Well, stage::mix(SUB_P, SUB_N, pm)), NO_GLOW);
    // backside power: rails under the substrate, reached through nano-TSVs
    if s.backside > 0.01 {
        for z in [-90.0, 90.0] {
            push_box(m, [ox - 280.0, -150.0 - 30.0 * s.backside, z - 30.0], [ox + 280.0, -150.0, z + 30.0], colour(s, ChipPart::TopMetal, COPPER), stage::scaled(COPPER, 0.2 * s.backside));
        }
        for x in [ox - 160.0, ox + 160.0] {
            crate::push_tube(m, [x, -150.0, -90.0], [x, -40.0, -90.0], 7.0 * s.backside, 8, colour(s, ChipPart::Via, TUNGSTEN), NO_GLOW, false);
        }
    }
    // FD-SOI: buried oxide under a thin film
    if s.soi > 0.01 {
        push_box(m, [ox - 280.0, -40.0 * k, -150.0], [ox + 280.0, -18.0 * k, 150.0], colour(s, ChipPart::Well, [0.55, 0.75, 0.90]), stage::scaled([0.55, 0.75, 0.90], 0.15 * s.soi));
    }
    // STI at the sides
    for sx in [-1.0, 1.0] {
        if sx > 0.0 && s.cut > 0.5 {
            continue;
        }
        push_box(m, [ox + sx * 250.0 - 30.0, -80.0 * k, -150.0], [ox + sx * 250.0 + 30.0, 0.0, 150.0], colour(s, ChipPart::Sti, [0.55, 0.60, 0.68]), NO_GLOW);
    }
    // source and drain: implanted wells in planar, raised epitaxy on fins
    for (p, sx) in [(ChipPart::Source, -1.0), (ChipPart::Drain, 1.0)] {
        let (x0, x1) = if sx < 0.0 { (ox - SD_X1, ox - SD_X0.max(hl + 20.0)) } else { (ox + SD_X0.max(hl + 20.0), ox + SD_X1) };
        // the drain goes with the cut
        let x1 = if sx > 0.0 { x0 + (x1 - x0) * keep } else { x1 };
        if x1 < x0 + 1.0 {
            continue;
        }
        let top = (fh + 6.0 * s.arch.min(1.0)) * k;
        let c = colour(s, p, sd);
        push_box(m, [x0, -50.0 * k, -140.0], [x1, top.max(0.5), 140.0 - zc * 0.9], c, stage::scaled(sd, 0.3 * glow(s, p)));
        if s.silicide > 0.01 {
            push_box(m, [x0 + 8.0, top, -130.0], [x1 - 8.0, top + 6.0 * s.silicide, 130.0 - zc * 0.9], colour(s, ChipPart::Silicide, SILICIDE), NO_GLOW);
        }
    }
    // channel: fins / sheets of silicon under the gate (planar: a thin surface slab)
    let chan = colour(s, ChipPart::Channel, SILICON);
    for (z, hw) in fins(s) {
        for (b, t) in sheets(s) {
            let tt = if fh < 1.0 { 4.0 } else { t };
            push_box(m, [ox - hl - 10.0, b * k, z - hw], [ox + (hl + 10.0) * keep, tt * k, z + hw], chan, stage::scaled(SILICON, 0.2 * glow(s, ChipPart::Channel)));
        }
    }
    // high-k dielectric: a thin shell over the channel
    let hk = colour(s, ChipPart::Oxide, stage::mix([0.80, 0.80, 0.85], HIK, s.hik));
    let ot = 2.0 + 4.0 * s.hik;
    let gx = ox + hl * keep;
    push_box(m, [ox - hl, fh * k, -148.0], [gx, (fh + ot) * k, 148.0 - zc], hk, stage::scaled(HIK, 0.3 * glow(s, ChipPart::Oxide)));
    // gate: fills down between fins (and between sheets for GAA), cut at the front when asked
    let gc = colour(s, ChipPart::Gate, stage::mix(POLY, GATE_METAL, s.metal_gate));
    let gg = stage::scaled(YELLOW, 0.25 * s.vg + 0.3 * glow(s, ChipPart::Gate));
    push_box(m, [ox - hl, (fh + ot) * k, -150.0], [gx, (fh + ot + GATE_H) * k, 150.0 - zc], gc, gg);
    if fh > 1.0 {
        // gate between and outside the fins, down to the STI
        let fz = fins(s);
        let mut spans = vec![(-150.0, fz[0].0 - fz[0].1 - ot)];
        for w in fz.windows(2) {
            spans.push((w[0].0 + w[0].1 + ot, w[1].0 - w[1].1 - ot));
        }
        let last = fz[fz.len() - 1];
        spans.push((last.0 + last.1 + ot, 150.0 - zc));
        for (z0, z1) in spans {
            let z1 = z1.min(150.0 - zc);
            if z1 > z0 + 1.0 {
                push_box(m, [ox - hl, 0.0, z0], [gx, (fh + ot) * k, z1], gc, gg);
            }
        }
        // GAA: gate (or, before release, sacrificial SiGe) fills the gaps between sheets
        let sh = sheets(s);
        if sh.len() > 1 {
            let fill = stage::mix(gc, colour(s, ChipPart::Sheet, [0.80, 0.55, 0.85]), s.sige);
            let mut gaps: Vec<(f64, f64)> = sh.windows(2).map(|w| (w[0].1, w[1].0)).collect();
            gaps.insert(0, (0.0, sh[0].0));
            for (y0, y1) in gaps {
                for &(z, hw) in &fz {
                    if z + hw < 150.0 - zc && y1 > y0 + 1.0 {
                        push_box(m, [ox - hl - 10.0 * s.sige, y0 * k + 1.0, z - hw], [(ox + hl + 10.0 * s.sige) * keep + gx * s.cut, y1 * k - 1.0, z + hw], fill, if s.sige > 0.5 { NO_GLOW } else { gg });
                    }
                }
            }
        }
    }
    // spacers
    for sx in [-1.0, 1.0] {
        if sx > 0.0 && s.cut > 0.5 {
            continue;
        }
        let x0 = ox + sx * hl;
        let x1 = ox + sx * (hl + 16.0);
        push_box(m, [x0.min(x1), fh * k, -150.0], [x0.max(x1), (fh + ot + GATE_H) * k, 150.0 - zc], colour(s, ChipPart::Spacer, SPACER), NO_GLOW);
    }
    // dopant atoms and halo pockets
    if s.dopants > 0.01 {
        for i in 0..18 {
            let side = if i % 2 == 0 { -1.0 } else { 1.0 };
            let x = ox + side * (110.0 + ((i * 37) % 100) as f64);
            let y = -40.0 + ((i * 17) % 40) as f64 + fh * 0.6;
            let z = -110.0 + ((i * 53) % 220) as f64;
            push_sphere(m, [x, y, z], 7.0 * s.dopants, 6, colour(s, ChipPart::Dopants, sd), stage::scaled(sd, 0.4 * s.dopants));
        }
    }
    if s.halo > 0.01 {
        for sx in [-1.0, 1.0] {
            let x = ox + sx * (hl + 4.0);
            push_box(m, [x - 14.0, -38.0 * s.halo, -120.0], [x + 14.0, -6.0, 120.0], colour(s, ChipPart::Halo, stage::mix(P_PLUS, N_PLUS, pm)), NO_GLOW);
        }
    }
}

fn contacts(s: &ChipState, m: &mut Vec<Tri>, ox: f64, k: f64) {
    let h = CONTACT_H * s.contacts * k;
    if h < 1.0 {
        return;
    }
    let base = contact_base(s);
    let fh = fin_h(s);
    let c = colour(s, ChipPart::Contact, TUNGSTEN);
    let g = stage::scaled(TUNGSTEN, 0.25 * glow(s, ChipPart::Contact));
    for x in [ox - 160.0, ox + 160.0] {
        crate::push_tube(m, [x, fh + 6.0, 0.0], [x, base + h, 0.0], 16.0, 14, c, g, true);
    }
    crate::push_tube(m, [ox, fh + GATE_H + 6.0, 70.0], [ox, base + h, 70.0], 14.0, 14, c, g, true);
}

fn metal(s: &ChipState, m: &mut Vec<Tri>, span: f64) {
    for (i, (t, w, _)) in LAYERS.iter().enumerate() {
        let p = (s.metal - i as f64).clamp(0.0, 1.0);
        if p < 0.01 {
            continue;
        }
        let part = match i {
            0 | 1 => ChipPart::ThinMetal,
            2 | 3 => ChipPart::MidMetal,
            _ => ChipPart::TopMetal,
        };
        let hot = if i >= 4 { s.heat } else { 0.0 };
        let c = stage::mix(colour(s, part, COPPER), [1.0, 0.35, 0.2], 0.6 * hot);
        let gl = stage::scaled(COPPER, 0.25 * glow(s, part) + 0.3 * hot);
        let y = layer_y(s, i);
        let pitch = w * 3.2;
        if i % 2 == 0 {
            // wires along x
            let n = (300.0 / pitch).floor() as i32;
            for j in -n..=n {
                let z = j as f64 * pitch;
                push_box(m, [-span, y, z - w / 2.0], [span, y + t * p, z + w / 2.0], c, gl);
            }
        } else {
            let n = (span / pitch).floor() as i32;
            for j in -n..=n {
                let x = j as f64 * pitch;
                push_box(m, [x - w / 2.0, y, -150.0], [x + w / 2.0, y + t * p, 150.0], c, gl);
            }
        }
        // vias down to the layer below
        if i > 0 {
            let below = layer_y(s, i - 1) + LAYERS[i - 1].0;
            let vc = colour(s, ChipPart::Via, TUNGSTEN);
            for vx in [-span * 0.5, 0.0, span * 0.5] {
                push_box(m, [vx - w * 0.3, below, -w * 0.3], [vx + w * 0.3, y, w * 0.3], vc, stage::scaled(TUNGSTEN, 0.2 * glow(s, ChipPart::Via)));
            }
        }
    }
}

pub(super) fn solids(s: &ChipState, m: &mut Vec<Tri>) {
    let cells = cell_xs(s);
    let span = (s.cells.max(1.0) - 1.0) * CELL_DX / 2.0 + 300.0;
    let sub_x1 = (span + 40.0) * (1.0 - s.cut) + (cell_xs(s).last().map_or(0.0, |c| c.0)) * s.cut;
    push_box(m, [-span - 40.0, -220.0, -170.0], [sub_x1, -120.0, 170.0], colour(s, ChipPart::Substrate, stage::mix(SUB_P, SUB_N, 0.3)), NO_GLOW);
    for (i, (x, k)) in cells.into_iter().enumerate() {
        if k < 0.01 {
            continue;
        }
        let cs = cell_state(s, i);
        transistor(&cs, m, x, k);
        contacts(&cs, m, x, k);
    }
    metal(s, m, span);
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, s: &ChipState, u: f64) {
    let hl = half_len(s);
    let fh = fin_h(s);
    for (ci, (ox, k)) in cell_xs(s).into_iter().enumerate() {
        if k < 0.5 {
            continue;
        }
        let cs = cell_state(s, ci);
        let s = &cs;
        let carrier = if s.pmos > 0.5 { HOLE } else { ELECTRON };
        // the front face works as a cross-section drawing: depletion, channel, carriers
        let zf = FACE;
        // depletion region under the gate: hatched on the face
        if s.depletion > 0.01 {
            let d = 70.0 * s.depletion;
            let a = (0.55 * s.depletion) as f32;
            for i in 0..=8 {
                let y = -d * i as f64 / 8.0;
                cv.overlay(cam, [ox - hl, y, zf], [ox + hl, y, zf], PURPLE, a);
            }
            for x in [ox - hl, ox + hl] {
                cv.overlay(cam, [x, 0.0, zf], [x, -d, zf], PURPLE, a);
            }
        }
        // inversion layer: a bright band at the surface, tapering at the drain when pinched
        if s.inversion > 0.01 {
            let x1 = ox + hl * (1.0 - 1.2 * s.pinch);
            let a = (0.9 * s.inversion) as f32;
            if fh < 1.0 {
                for dy in [-1.0, -3.0, -5.0] {
                    let taper = if dy < -2.0 { 1.0 - 0.6 * s.pinch } else { 1.0 };
                    cv.overlay(cam, [ox - hl - 10.0, dy, zf], [ox - hl + (x1 - ox + hl) * taper, dy, zf], carrier, a);
                }
            } else {
                for (z, hw) in fins(s) {
                    for dz in [-hw * 0.6, 0.0, hw * 0.6] {
                        cv.line(cam, [ox - hl - 10.0, fh * 0.5, z + dz], [x1, fh * 0.5, z + dz], carrier, a);
                    }
                }
            }
        }
        // dopant atoms and halo pockets, drawn on the face
        if s.dopants > 0.01 {
            let sd = stage::mix(N_PLUS, P_PLUS, s.pmos);
            for i in 0..20 {
                let side = if i % 2 == 0 { -1.0 } else { 1.0 };
                let x = ox + side * (hl + 30.0 + ((i * 37) % 120) as f64);
                let y = -6.0 - ((i * 17) % 40) as f64;
                particles_front(cv, cam, &[[x, y, zf], [x, y, zf]], 1, 0.5, 6.0, stage::mix(sd, TEXT, 0.4), s.dopants);
            }
        }
        if s.halo > 0.01 {
            let hc = stage::mix(P_PLUS, N_PLUS, s.pmos);
            for sx in [-1.0, 1.0] {
                let x = ox + sx * (hl + 4.0);
                for i in 0..=5 {
                    let y = -6.0 - 32.0 * s.halo * i as f64 / 5.0;
                    cv.overlay(cam, [x - 14.0, y, zf], [x + 14.0, y, zf], hc, (0.8 * s.halo) as f32);
                }
            }
        }
        // carriers on the face (planar), and through each fin/sheet
        if fh < 1.0 {
            let x1 = ox + hl * (1.0 - 1.2 * s.pinch);
            let path = [[ox - 200.0, -4.0, zf], [ox - hl, -4.0, zf], [x1, -4.0, zf], [ox + hl, -10.0, zf], [ox + 200.0, -6.0, zf]];
            particles_front(cv, cam, &path, 8, u * 1.6, 6.0, carrier, s.flow);
        }
        for (j, (z, hw)) in fins(s).iter().enumerate() {
            for (b, t) in sheets(s) {
                let y = if fh > 1.0 { (b + t) / 2.0 } else { 3.0 };
                let path = [[ox - 200.0, y, *z], [ox - hl, y, *z], [ox + hl, y, *z], [ox + 200.0, y, *z]];
                particles(cv, cam, &path, 6, u * 1.6 + j as f64 * 0.21 + b * 0.01, 5.0, carrier, s.flow);
                let _ = hw;
            }
        }
        // leakage: faint carriers under the channel and up through the oxide
        if s.leak > 0.01 {
            let path = [[ox - 200.0, -30.0, zf], [ox, -45.0, zf], [ox + 200.0, -30.0, zf]];
            particles_front(cv, cam, &path, 5, u * 1.1, 4.5, carrier, 0.8 * s.leak);
            let path = [[ox - 200.0, -30.0, 0.0], [ox, -45.0, 0.0], [ox + 200.0, -30.0, 0.0]];
            particles(cv, cam, &path, 5, u * 1.1, 4.0, carrier, 0.7 * s.leak);
            particles(cv, cam, &[[ox, fh + 1.0, -40.0], [ox, fh + GATE_H + 10.0, -40.0]], 3, u * 0.9, 4.0, PINK, 0.6 * s.leak);
        }
        // gate field: lines from the gate down into the channel
        if s.vg > 0.01 {
            for dx in [-hl * 0.6, 0.0, hl * 0.6] {
                cv.line(cam, [ox + dx, fh + 20.0, 145.0], [ox + dx, fh - 20.0, 145.0], YELLOW, (0.6 * s.vg) as f32);
            }
        }
        // strain: arrows pushing along the channel
        if s.strain > 0.01 {
            for sx in [-1.0, 1.0] {
                let a = [ox + sx * (hl + 120.0), fh + 20.0, 150.0];
                let b = [ox + sx * (hl + 30.0), fh + 20.0, 150.0];
                cv.overlay(cam, a, b, GREEN, (0.9 * s.strain) as f32);
            }
        }
        // signal: up the contacts and along M1
        if s.signal > 0.01 && s.contacts > 0.5 {
            let top = contact_base(s) + CONTACT_H * s.contacts;
            particles(cv, cam, &[[ox + 160.0, fh + 6.0, 0.0], [ox + 160.0, top, 0.0], [ox + 160.0, layer_y(s, 0) + 5.0, 0.0]], 4, u * 1.8, 6.0, YELLOW, s.signal);
            if s.metal > 0.5 {
                let y = layer_y(s, 0) + 5.0;
                particles(cv, cam, &[[ox + 160.0, y, 0.0], [ox + 160.0 + CELL_DX * 0.8, y, 0.0]], 5, u * 1.8 + 0.3, 6.0, YELLOW, s.signal);
            }
        }
    }
    // signal climbing the stack through the vias
    if s.signal > 0.01 && s.metal > 1.5 {
        let n = s.metal.floor() as usize;
        let mut pts = vec![];
        for i in 0..n.min(6) {
            pts.push([0.0, layer_y(s, i) + LAYERS[i].0 / 2.0, 0.0]);
        }
        if pts.len() > 1 {
            particles(cv, cam, &pts, 5, u * 1.4, 7.0, YELLOW, s.signal);
        }
    }
    let _ = (GLASS, METAL, STEEL, TEXT);
}

/// The front face of the well, where cross-section drawings go.
const FACE: f64 = 151.0;

/// Particles drawn over everything (on the cross-section face).
fn particles_front(cv: &mut Canvas, cam: &Cam, pts: &[V3], n: usize, clock: f64, r: f64, col: Col, strength: f64) {
    if strength <= 0.004 {
        return;
    }
    for i in 0..n {
        let s = (clock + i as f64 / n as f64).rem_euclid(1.0);
        let fade = (std::f64::consts::PI * s).sin().sqrt();
        let p = stage::along(pts, s);
        if let Some((x, y, inv)) = cam.project(p) {
            let pr = (r * cam.focal * inv).max(1.5);
            let a = (strength * fade) as f32;
            for py in (y - pr).floor() as i64..=(y + pr).ceil() as i64 {
                for px in (x - pr).floor() as i64..=(x + pr).ceil() as i64 {
                    if px < 0 || py < 0 || px >= cv.w as i64 || py >= cv.h as i64 {
                        continue;
                    }
                    let d = ((px as f64 + 0.5 - x).powi(2) + (py as f64 + 0.5 - y).powi(2)).sqrt();
                    let cover = ((pr + 0.5 - d).clamp(0.0, 1.0)) as f32 * a;
                    if cover > 0.0 {
                        let c = &mut cv.rgb[py as usize * cv.w + px as usize];
                        for k in 0..3 {
                            c[k] = c[k] * (1.0 - cover) + col[k] * cover;
                        }
                    }
                }
            }
        }
    }
}

/// Where a part is, for labels, notes and leaders.
pub fn part_at(p: ChipPart, s: &ChipState) -> V3 {
    let hl = half_len(s);
    let fh = fin_h(s);
    let fz = fins(s);
    match p {
        ChipPart::Substrate => [260.0, -170.0, 170.0],
        ChipPart::Well => [260.0, -90.0, 150.0],
        ChipPart::Sti => [280.0, -20.0, 150.0],
        ChipPart::Source => [-200.0, fh, 140.0],
        ChipPart::Drain => [200.0, fh, 140.0],
        ChipPart::Channel => [(hl + 10.0) * (1.0 - s.cut), fh * 0.5, fz[fz.len() - 1].0 + fz[fz.len() - 1].1],
        ChipPart::Gate => [hl * (1.0 - s.cut), fh + GATE_H + 6.0, 150.0 - 60.0 * s.cut],
        ChipPart::Oxide => [hl * (1.0 - s.cut), fh + 3.0, 148.0 - 60.0 * s.cut],
        ChipPart::Spacer => [-hl - 16.0, fh + GATE_H * 0.6, 150.0],
        ChipPart::Silicide => [200.0, fh + 8.0, 130.0],
        ChipPart::Contact => [160.0, contact_base(s) + CONTACT_H * s.contacts * 0.6, 16.0],
        ChipPart::ThinMetal => [300.0, layer_y(s, 1) + 10.0, 150.0],
        ChipPart::MidMetal => [300.0, layer_y(s, 3) + 18.0, 150.0],
        ChipPart::TopMetal => [300.0, layer_y(s, 5) + 34.0, 150.0],
        ChipPart::Via => [150.0, layer_y(s, 2) - 10.0, 10.0],
        ChipPart::Depletion => [hl, -60.0 * s.depletion, FACE],
        ChipPart::Inversion => [hl * 0.6, if fh > 1.0 { fh * 0.5 } else { -3.0 }, FACE],
        ChipPart::Fin => [(hl + 10.0) * (1.0 - s.cut), fh, fz[fz.len() - 1].0 + fz[fz.len() - 1].1],
        ChipPart::Sheet => [(hl + 10.0) * (1.0 - s.cut), sheets(s).last().map_or(fh, |x| x.1), fz[fz.len() - 1].0 + fz[fz.len() - 1].1],
        ChipPart::Dopants => [-150.0, -20.0, FACE],
        ChipPart::Halo => [hl + 4.0, -30.0, FACE],
        ChipPart::Drift => [0.0, if fh > 1.0 { fh * 0.5 } else { -4.0 }, FACE],
    }
}

/// A part's label colour.
pub fn part_col(p: ChipPart, s: &ChipState) -> Col {
    let sd = stage::mix(N_PLUS, P_PLUS, s.pmos);
    match p {
        ChipPart::Source | ChipPart::Drain | ChipPart::Dopants => stage::mix(sd, TEXT, 0.3),
        ChipPart::Gate => [0.80, 0.85, 0.95],
        ChipPart::Oxide => HIK,
        ChipPart::Contact | ChipPart::Via => [0.85, 0.87, 0.92],
        ChipPart::ThinMetal | ChipPart::MidMetal | ChipPart::TopMetal => COPPER,
        ChipPart::Depletion => PURPLE,
        ChipPart::Inversion | ChipPart::Drift => if s.pmos > 0.5 { HOLE } else { ELECTRON },
        ChipPart::Halo => PINK,
        _ => TEXT,
    }
}

/// Draw the given labels at alpha `a`.
pub(super) fn labels(cv: &mut Canvas, cam: &Cam, s: &ChipState, list: &[(ChipPart, &str)], a: f64, out: &mut Vec<Rect>) {
    for (i, (p, t)) in list.iter().enumerate() {
        // push the name towards the side of the frame its part is on, alternating up/down
        let at = part_at(*p, s);
        let left = cam.project(at).is_some_and(|(x, _, _)| x < cv.w as f64 * 0.5);
        let w = stage::text_w(&t.to_ascii_uppercase(), stage::text_scale(cv)) as f64 / cv.h as f64;
        let dx = if left { -0.05 - w } else { 0.05 };
        let dy = if i % 2 == 0 { -0.07 } else { 0.06 };
        out.extend(label(cv, cam, at, (dx, dy), t, part_col(*p, s), a));
    }
}
