// CHIP tab, PLANAR: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera gliding into the planar NMOS, drawn as the detailed device of
// chip_planar_detail.py (tools/pbr3d/blender/chip_planar.py). The gate
// lies flat on the channel and controls it from one side only; as the channel shortens, the drain
// pulls on it and current leaks under the gate in the off state.
//
// Zoom-ins a-e and sections 1-10 are Blender scenes from the same script; each is its own detailed
// close-up of one planar transistor (chip_planar_detail.py).
//
// Sources: CHIP_PLANAR.details.txt (Counterpoint mature-node share, Intel 22 nm FinFET, textbook
// subthreshold and DIBL figures, allaboutcircuits nanoscale SCE article).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("a flat channel under a flat gate", BEAT_MS)
        .note(
            "This is the whole chip in cross-section: transistors in the silicon at the bottom, copper wiring above, solder bumps on top. The highlighted NMOS is a planar transistor, the kind every chip used until about 2011: a flat channel at the silicon surface under a flat gate.",
            "The whole chip, the NMOS at lower left boxed in cyan. Tan silicon, brown copper layers, silver bumps on top.",
        )
        .detail(
            "Planar still makes most wafers at 28 nm and above.",
            &["Leading edge until ~22 nm", "Mature nodes: still planar"],
        ),
    Beat::new("the gate lies flat on the channel, on one side only", BEAT_MS)
        .note(
            "Close up: n+ source and drain sit either side of a polysilicon gate on a thin SiON oxide, all in p-type silicon, with isolation oxide (STI) walling off the neighbours. The gate touches the channel from the top only. The grey pillars are the chip's tungsten contacts landing on source, drain and gate.",
            "A cut-away transistor: brown gate between green spacers on a thin pale oxide, blue source and drain, tan body, grey STI at the ends, dark silicide pads under the pillars.",
        )
        .detail(
            "One-sided control is the planar transistor's limit.",
            &["Gate on one side of the channel", "SiON, later HfO2, dielectric"],
        ),
    Beat::new("gate high: the channel forms and carries current", BEAT_MS)
        .note(
            "Raise the gate and its field reaches down through the oxide and pulls electrons to the silicon surface. They form a thin inversion layer that bridges source and drain, and current flows.",
            "Gold arrows run down from the gate to the surface; a cyan band lights under the gate and cyan electrons ride a track from source to drain.",
        )
        .detail(
            "Only the top few nanometres of silicon conduct.",
            &["Inversion layer at the surface"],
        ),
    Beat::new("the channel shortens: the drain pulls on the barrier", BEAT_MS)
        .note(
            "Each new node shortened the gate. With a short gate, the depletion regions round source and drain grow until they meet underneath, and the drain's voltage starts lowering the energy barrier at the source (DIBL). The gate is losing control.",
            "A narrow gate. Peach depletion bands spread from the blue junctions and merge under it; a pink arrow runs from the drain toward the source below the surface.",
        )
        .detail(
            "Vt falls as the drain voltage rises.",
            &["DIBL: drain-induced barrier lowering", "Vt roll-off with gate length"],
        ),
    Beat::new("gate low: off, yet current leaks under the gate", BEAT_MS)
        .note(
            "Switch the gate off and current should stop. In a short planar device it doesn't: electrons still drift along the surface (subthreshold leakage) and punch through deeper in the body, where the gate's field never reached. The gate sits only on top.",
            "The gate dark. Pink electrons ride a track along the surface and another arching under the gate, from drain to source.",
        )
        .detail(
            "Off-state power grew with every shrink.",
            &["Subthreshold leakage", "Punch-through under short gates"],
        ),
    Beat::new("back out: the planar limit", BEAT_MS)
        .note(
            "Strain, high-k metal gates and FD-SOI held this off until about 22 nm. Then the leading edge moved to fins, which wrap the gate round three sides of the channel. Planar lives on at mature nodes.",
            "Back out to the whole chip, the NMOS boxed in cyan again.",
        )
        .detail(
            "Intel announced the first FinFET node, 22 nm, in 2011.",
            &["Intel 22 nm FinFET (2011)", "Mature nodes still planar"],
        ),
];

// ---- zoom-ins a-e ---------------------------------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("subthreshold: drain to source below Vt", BEAT_MS)
        .note(
            "With the gate off, a small current still diffuses from drain to source along the surface. It falls by at most 10x for every ~60 mV below threshold, so a low threshold means a large off current.",
            "A planar transistor with its gate off; pink electrons ride a shallow arched track along the surface from drain to source.",
        )
        .detail(
            "The main leak in modern logic.",
            &["~60 mV per decade at 300 K"],
        ),
    Beat::new("gate tunnelling through thin oxide", BEAT_MS)
        .note(
            "The SiON gate oxide is only ~1.2 nm, a few atoms. Electrons tunnel straight through it into the gate, a quantum effect that grows about tenfold for every 0.2 nm the oxide thins.",
            "Close on the gate: three pink tracks cross the thin pale oxide, electrons riding up them into the brown gate.",
        )
        .detail(
            "High-k dielectrics fixed this path (zoom c).",
            &["SiON ~1.2 nm", "~10x per 0.2 nm thinner (rule of thumb)"],
        ),
    Beat::new("punch-through and junction leakage", BEAT_MS)
        .note(
            "Deeper down, the drain's field reaches under a short gate to the source and current punches through the body. At the drain edge, the strong field under the gate also pulls electrons into the body: junction leakage and gate-induced drain leakage (GIDL).",
            "Magenta electrons ride an arch deep under the gate from drain to source; yellow ones ride a curved track from the drain edge down into the body.",
        )
        .detail(
            "Halo implants, then fins, fought these paths.",
            &["Punch-through under short gates", "Junction / GIDL at the drain"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("SHORT CHANNEL: the drain reaches the source", BEAT_MS)
        .note(
            "Each junction has a depletion region, a zone emptied of free carriers. Shorten the gate and the regions from source and drain grow toward each other until they meet under the channel. The gate no longer sets the barrier alone.",
            "A short gate; peach depletion bands round the blue source and drain, small at first, then spreading until they merge under the gate.",
        )
        .detail(
            "Vt roll-off: shorter gates, lower thresholds.",
            &["Short-channel effects (allaboutcircuits)"],
        ),
    Beat::new("DIBL: Vt falls with drain voltage", BEAT_MS)
        .note(
            "With the regions merged, a higher drain voltage lowers the source barrier too: drain-induced barrier lowering (DIBL). The threshold now depends on the drain voltage, and current punches through below the surface.",
            "A pink arrow from drain toward source under the gate, and magenta electrons riding an arch beneath the channel.",
        )
        .detail(
            "Off current rises with the supply a circuit runs at.",
            &["DIBL: Vt falls as Vd rises"],
        ),
    Beat::new("the swing floor", BEAT_MS)
        .note(
            "Below threshold, current falls by at most 10x per ~60 mV at room temperature, set by kT/q. So every 60 mV taken off Vt to gain speed costs ten times more off current, and planar's weak gate makes its swing worse than that floor.",
            "Pink electrons leak along the surface; beside the device three glowing bars on a dark board, each ten times the last on a log scale.",
        )
        .detail(
            "Lowering Vt for speed costs standby power exponentially.",
            &["~60 mV/decade at 300 K", "60 mV less Vt = ~10x Ioff"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("polysilicon on SiON", BEAT_MS)
        .note(
            "For decades the gate was doped polysilicon on a thin silicon oxynitride (SiON). By the 90-65 nm nodes the SiON was ~1.2 nm, a few atoms, and electrons tunnelled straight through it.",
            "Close on the gate: a brown poly block on a thin pale SiON line, pink electrons riding tracks up through it.",
        )
        .detail(
            "Thinning it further was no longer possible.",
            &["SiON ~1.2 nm at 90-65 nm"],
        ),
    Beat::new("HfO2: thicker but electrically thinner", BEAT_MS)
        .note(
            "Hafnium oxide's dielectric constant is ~20-25, against 3.9 for SiO2. A film several times thicker gives the gate the same grip on the channel, and tunnelling, which falls off steeply with thickness, nearly stops.",
            "The same gate on a yellow HfO2 film over a thin grey interlayer; only one electron crosses.",
        )
        .detail(
            "Thick in fact, thin in effect (EOT).",
            &["HfO2 k ~20-25 vs SiO2 3.9"],
        ),
    Beat::new("a metal gate sets Vt", BEAT_MS)
        .note(
            "Polysilicon doesn't sit well on HfO2, so the gate became metal too. Its work function sets the threshold voltage. Intel shipped high-k metal gate at 45 nm in 2007, with a gate-last flow; others followed at 32-28 nm.",
            "A grey metal gate on the yellow HfO2; cyan electrons ride a track from source to drain under it.",
        )
        .detail(
            "This stack carried on into FinFET and GAA gates.",
            &["Intel 45 nm HKMG, 2007", "Work function sets Vt"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("bulk: depletion reaches deep", BEAT_MS)
        .note(
            "In bulk silicon the depletion regions and leak paths spread deep into the body, out of the gate's reach. The body has to be doped to fight that, and the random spread of a few dopant atoms under each gate varies Vt from device to device.",
            "A bulk transistor with wide peach depletion bands and magenta electrons riding an arch deep under the gate.",
        )
        .detail(
            "Random dopant variation is what a thin film removes.",
            &["Deep leak paths in bulk", "Random-dopant Vt spread"],
        ),
    Beat::new("FD-SOI: a thin film on buried oxide", BEAT_MS)
        .note(
            "FD-SOI builds the transistor in an undoped silicon film a few nanometres thick, on a buried oxide (BOX). The film is too thin to hold a depletion region, no doping is needed, and the BOX blocks the path under the channel.",
            "A thin cream film on a pale BOX layer over the tan base wafer, raised blue source and drain, cyan electrons riding through the film.",
        )
        .detail(
            "Soitec makes the wafers (Smart Cut).",
            &["Film a few nm, undoped", "BOX blocks the path below"],
        ),
    Beat::new("body bias under the BOX", BEAT_MS)
        .note(
            "A voltage on the silicon under the BOX acts like a weak second gate from below. Forward bias lowers Vt for speed; reverse bias raises it to cut leakage when idle, and it can change while the chip runs.",
            "The base wafer under the BOX glows violet, with arrows rising toward the channel.",
        )
        .detail(
            "GlobalFoundries ships FD-SOI as 22FDX.",
            &["Forward: lower Vt", "Reverse: less leakage", "GF 22FDX"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("one node: shrink everything by 1/k", BEAT_MS)
        .note(
            "Dennard's recipe: scale the gate length, width, oxide thickness and supply voltage all by 1/k, with k about 1.4 per node. Fields inside stay the same, so the transistor works the same, only smaller and faster.",
            "A long-gate transistor, cyan electrons riding source to drain.",
        )
        .detail(
            "Gate delay falls by 1/k.",
            &["k ~1.4 (x0.7) per node"],
        ),
    Beat::new("twice the transistors, same power", BEAT_MS)
        .note(
            "Capacitance and voltage both fall by 1/k, so power per gate falls by ~1/k^2 even at a higher clock. Gates per area rise by k^2, so power per area stays flat: about twice the transistors for the same watts.",
            "The whole device shrinks to 0.7x, then electrons ride the smaller channel.",
        )
        .detail(
            "Power density x 1.",
            &["Power/gate x 1/k^2", "Gates/area x k^2"],
        ),
    Beat::new("until Vt stopped scaling", BEAT_MS)
        .note(
            "Off current grows ~10x for every 60 mV the threshold drops, and the oxide could thin no further, so Vt and the supply stopped falling in the mid-2000s, stalling near 1 V. More transistors then meant more power: multicore and dark silicon.",
            "The shrunken device switched off; pink electrons still ride along the surface and up through the oxide.",
        )
        .detail(
            "Breakdown dated to about 2005.",
            &["Vdd stalled near 1 V", "~10x Ioff per 60 mV of Vt"],
        ),
];

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

pub fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_planar_zoom_a.glb"),
        ZA_BEATS,
    )
}

pub fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_planar_zoom_b.glb"),
        ZB_BEATS,
    )
}

pub fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_planar_zoom_c.glb"),
        ZC_BEATS,
    )
}

pub fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_planar_zoom_d.glb"),
        ZD_BEATS,
    )
}

pub fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_planar_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the four leakage paths",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "short channels and DIBL",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "high-k metal gate",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "FD-SOI and body bias",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "Dennard scaling and its end",
        build: zoom_e,
    },
];

// ---- sections 1-10 --------------------------------------------------------------------------
// Each section is its own close-up of one planar transistor (or a wafer), from
// tools/pbr3d/blender/chip_planar_detail.py.

const SEC1: &[Beat] = &[
    Beat::new("DENNARD SCALING: shrinking was free", BEAT_MS)
        .note(
            "A planar transistor is a flat channel under a flat gate. For decades each new node shrank every dimension and the supply voltage by about 0.7x together, so transistors got faster and cheaper while the power per area stayed flat. That free ride was Dennard scaling.",
            "A cut-away NMOS: brown polysilicon gate between green spacers, blue n+ source and drain, tan silicon, grey isolation oxide at the ends and tungsten contacts. Cyan electrons cross under the gate, then the whole device shrinks to 0.7x.",
        )
        .detail(
            "Power density stayed constant as long as the voltage scaled with the size.",
            &["~0.7x per node (k ~1.4)", "Power density ~flat"],
        ),
    Beat::new("the LEAKAGE WALL, ~2005", BEAT_MS)
        .note(
            "Around 2005 the threshold voltage could no longer fall without off-state leakage exploding, and the oxide was too thin to thin further. Supply voltage stalled near 1 V, so each shrink stopped saving power. Even switched off, the short transistor leaks.",
            "A short-gate device with the gate off. Red dots still drift under the gate from drain to source, and pink dots tunnel up through the thin oxide.",
        )
        .detail(
            "Clock speeds stalled and chips went multicore.",
            &["Vdd stalled near 1 V", "Breakdown ~2005 (semiengineering)"],
        ),
    Beat::new("patched, then replaced at ~22 nm", BEAT_MS)
        .note(
            "Planar was patched for several nodes: strained silicon from 90 nm, high-k metal gate from 45 nm, FD-SOI at 28/22 nm. But the gate still touches the channel only from the top, and below about 22 nm it could not hold the leakage, so the leading edge moved to fins. Intel announced the first FinFET node, 22 nm, in 2011.",
            "The same device with its patches: a green tensile liner over it, a grey metal gate on a yellow HfO2 film. The gate still sits on top of a flat channel.",
        )
        .detail(
            "Planar still makes most wafers at mature nodes, 28 nm and above.",
            &["Strain 90 nm, HKMG 45 nm", "Intel 22 nm FinFET, 2011"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("the cross-section, switched on", BEAT_MS)
        .note(
            "An NMOS has n+ source and drain either side of a gate on a thin dielectric, all on p-type silicon shared by every transistor on the die. With the gate high, its field pulls electrons into a thin inversion layer at the surface, and current flows from source to drain.",
            "Brown poly gate on a thin pale SiON film, blue n+ source and drain, tan p-type body. Gold arrows run from the gate down to the surface, a cyan band lights under the gate and cyan electrons cross it.",
        )
        .detail(
            "Only the top few nanometres of silicon conduct.",
            &["Planar bulk CMOS to 28/22 nm", "SiON, later HfO2, dielectric"],
        ),
    Beat::new("the gate sees only the top", BEAT_MS)
        .note(
            "The gate controls the channel from one side, the top. Deeper in the body its field fades, while the drain's field reaches across underneath toward the source. As the gate shortens, the drain gets more say over the current than the gate does.",
            "Gold arrows stop at the surface. A red see-through block below the channel marks silicon the gate cannot reach, and a pink arrow runs through it from drain to source.",
        )
        .detail(
            "This one-sided control is why planar ended.",
            &["Gate field: surface only", "Drain field reaches the source"],
        ),
    Beat::new("four leak paths when off", BEAT_MS)
        .note(
            "Switched off, the transistor still leaks four ways: subthreshold current along the surface, tunnelling through the thin gate oxide, junction and gate-induced drain leakage (GIDL) from the drain into the body, and punch-through deep under a short gate.",
            "Coloured dots, numbered: red along the surface, pink up through the oxide, yellow down from the drain into the body, magenta in an arc under the gate.",
        )
        .detail(
            "Each path needs its own fix.",
            &["Subthreshold, tunnelling", "Junction/GIDL, punch-through"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("long gate: the barrier holds", BEAT_MS)
        .note(
            "Each source and drain junction has a depletion region round it, a zone emptied of free carriers. With a long gate those zones stay far apart, and the gate alone sets the energy barrier that keeps electrons in the source.",
            "A wide brown gate. Peach bands hug the blue source and drain, with plain tan silicon between them under the gate.",
        )
        .detail(
            "The gate, not the drain, sets the threshold.",
            &["Long channel: Vt set by the gate"],
        ),
    Beat::new("short gate: DIBL", BEAT_MS)
        .note(
            "Shrink the gate and the two depletion regions meet under it. The drain's voltage now lowers the source barrier too (drain-induced barrier lowering, DIBL), so the threshold falls as the drain voltage rises, and current punches through below the surface.",
            "A narrow gate. The peach depletion bands run together under it, and pink dots slip from drain to source below the channel.",
        )
        .detail(
            "Vt roll-off: shorter gates have lower, less predictable thresholds.",
            &["DIBL: Vt falls as Vd rises", "Punch-through under short gates"],
        ),
    Beat::new("the swing floor: 60 mV per decade", BEAT_MS)
        .note(
            "Below threshold, current falls by at most 10x for every ~60 mV the gate drops at room temperature (S = (kT/q) ln10 (1 + Cdep/Cox)). So each 60 mV taken off Vt to gain speed costs ten times the off-state leakage. Planar's weak gate control makes its swing worse than that floor.",
            "The short device with red dots leaking along the surface, and beside it three glowing bars on a dark board, each ten times the last on a log scale.",
        )
        .detail(
            "Lowering Vt for speed costs standby power exponentially.",
            &["~60 mV/decade at 300 K", "60 mV less Vt = ~10x Ioff"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("STRAINED SI: SiGe squeezes the PMOS", BEAT_MS)
        .note(
            "In the PMOS, the source and drain are etched out and regrown as silicon-germanium (SiGe). SiGe has a larger lattice, so it squeezes the channel between them, and holes move faster. Intel brought strain in at 90 nm.",
            "A PMOS on a grey-green n-well: orange SiGe source and drain raised above the surface, with glowing arrows pressing in from both sides toward the channel.",
        )
        .detail(
            "Strain buys mobility without shrinking anything.",
            &["Intel 90 nm: ~+25% PMOS drive (secondary)"],
        ),
    Beat::new("a nitride liner stretches the NMOS", BEAT_MS)
        .note(
            "For the NMOS a tensile silicon-nitride film is laid over the gate and source/drain. It pulls on the silicon and stretches the channel along its length, which speeds up electrons.",
            "An NMOS under a translucent green liner draped over the gate and the source and drain, with green arrows pulling outward from the channel.",
        )
        .detail(
            "Electrons gain less from strain than holes do.",
            &["Intel 90 nm: ~+10% NMOS drive (secondary)"],
        ),
    Beat::new("HIGH-K METAL GATE replaces poly/SiON", BEAT_MS)
        .note(
            "The thin SiON oxide under a poly gate leaked by tunnelling. High-k metal gate swapped it for hafnium oxide, physically thicker for the same gate strength, and replaced poly with a metal whose work function sets Vt. Intel shipped it at 45 nm in 2007.",
            "First a brown poly gate on thin pale SiON, with pink dots tunnelling up; then a grey metal gate on a yellow HfO2 film, and no dots.",
        )
        .detail(
            "This stack is the direct ancestor of FinFET and GAA gates.",
            &["HfO2 k ~20-25 vs SiO2 3.9", "Intel 45 nm HKMG, 2007"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("MATURE NODES: 36% of foundry revenue", BEAT_MS)
        .note(
            "Planar transistors still make most of the world's chips by volume, at 28 nm and above. Those nodes were 36% of pure-play foundry revenue in 2025, down from 54% in 2021, because leading-edge wafers sell for much more.",
            "A bulk planar NMOS with a metal gate on HfO2, cyan electrons crossing under it.",
        )
        .detail(
            "Mature wafers are cheaper, so their share of wafers is higher than their share of revenue.",
            &["28 nm+: 36% of revenue, 2025", "54% in 2021 (Counterpoint)"],
        ),
    Beat::new("UMC and GLOBALFOUNDRIES", BEAT_MS)
        .note(
            "UMC (UMC) put 22/28 nm at about 35-40% of its revenue through 2025; 2025 revenue was NT$237.5B, up 2.3%. GlobalFoundries (GFS) ships FD-SOI as 22FDX, plus RF and automotive parts, on FY25 revenue of about $6.79B.",
            "The FD-SOI version: the same gate, on a thin silicon film over a pale buried-oxide layer.",
        )
        .detail(
            "GF's FY25 figure is from a secondary report.",
            &["UMC 2025: NT$237.5B, +2.3%", "GF FY25 ~$6.79B; 22FDX"],
        ),
    Beat::new("SMIC", BEAT_MS)
        .note(
            "SMIC (0981.HK) makes mostly 28 nm and above, for mature and domestic Chinese demand: microcontrollers, power management, display drivers and RF.",
            "A bulk planar NMOS with a brown poly gate, cyan electrons crossing under it.",
        )
        .detail(
            "SMIC reports in Hong Kong and China, not to the SEC.",
            &["SMIC: mostly 28 nm+ (secondary)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("one node: every size x 1/k", BEAT_MS)
        .note(
            "Dennard's recipe: scale the gate length L, width W, oxide thickness t_ox and the supply voltage Vdd all by 1/k, with k about 1.4 per node. Fields inside the device stay the same, so it keeps working, only smaller and faster.",
            "A long-gate NMOS, the gate and the thin oxide tagged, cyan electrons crossing under it.",
        )
        .detail(
            "Gate delay also falls by 1/k.",
            &["k ~1.4 (x0.7) per node", "Delay x 1/k"],
        ),
    Beat::new("power per gate x 1/k^2", BEAT_MS)
        .note(
            "Capacitance falls by 1/k and voltage by 1/k, so switching power per gate falls by about 1/k^2 even at the higher clock. Gates per area rise by k^2, so power per area stays flat: twice the transistors for the same watts.",
            "The device shrinks to 0.7x in every direction, then electrons cross the smaller channel.",
        )
        .detail(
            "Power density x 1.",
            &["Power/gate x 1/k^2", "Gates/area x k^2"],
        ),
    Beat::new("until Vt stopped scaling", BEAT_MS)
        .note(
            "Off-current grows ~10x for every 60 mV the threshold drops, and the oxide could not thin further, so Vt and Vdd stopped falling in the mid-2000s. Supply stalled near 1 V; more transistors at the same voltage meant more power, so chips added cores and left parts idle (dark silicon).",
            "The shrunken device switched off, red dots leaking along the surface and pink dots tunnelling through the oxide.",
        )
        .detail(
            "Breakdown dated to about 2005.",
            &["Vdd stalled near 1 V", "~10x Ioff per 60 mV of Vt"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("bulk: depletion reaches deep", BEAT_MS)
        .note(
            "In bulk silicon the depletion regions and leak paths spread deep into the body, out of the gate's reach. The body must be doped to fight that, and the random spread of a few dopant atoms under each gate varies the threshold from transistor to transistor.",
            "A bulk NMOS with broad peach depletion bands reaching under the gate, and magenta dots arcing deep below the channel.",
        )
        .detail(
            "Random dopant variation is what the thin film removes.",
            &["Deep leak paths in bulk", "Random-dopant Vt spread"],
        ),
    Beat::new("FD-SOI: a thin film on buried oxide", BEAT_MS)
        .note(
            "FD-SOI builds the transistor in an undoped silicon film only a few nanometres thick, on a buried oxide (BOX). The film is too thin to hold a depletion region, so no dopants are needed, junction capacitance is low, and the BOX cuts the leak path under the channel.",
            "A thin cream silicon film on a pale BOX layer over the tan base wafer, with raised blue source and drain and a metal gate on top.",
        )
        .detail(
            "Soitec makes the wafers with its Smart Cut process.",
            &["Film a few nm, undoped", "BOX blocks the path below"],
        ),
    Beat::new("BODY BIAS under the BOX", BEAT_MS)
        .note(
            "A voltage on the silicon under the BOX acts like a second, weaker gate from below. Forward bias lowers Vt for speed; reverse bias raises it to cut leakage when idle, and it can be changed while the chip runs.",
            "The base wafer under the BOX glows violet, with arrows rising toward the channel.",
        )
        .detail(
            "GlobalFoundries ships FD-SOI as 22FDX.",
            &["Forward bias: lower Vt", "Reverse bias: lower leakage", "GF 22FDX"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("TSMC: 28 nm, still a big line", BEAT_MS)
        .note(
            "TSMC (TSM) still runs a large 28 nm planar line years after moving its leading edge to fins. 28 nm was the last node where planar was the main option for most designs, and it remains a long-lived workhorse.",
            "A bulk planar transistor with a grey metal gate on yellow HfO2, cyan electrons crossing under it.",
        )
        .detail(
            "28 nm planar was offered with poly/SiON and with HKMG.",
            &["TSMC 28 nm planar line"],
        ),
    Beat::new("Intel: FinFET at 22 nm", BEAT_MS)
        .note(
            "Intel (INTC) was the first to drop planar at the leading edge, announcing its 22 nm 'tri-gate' FinFET in 2011. A fin lets the gate wrap the channel on three sides instead of one.",
            "The same planar device: its gate glows cyan, and the red block below the channel marks what a gate on top cannot control.",
        )
        .detail(
            "Everyone else followed at 16/14 nm.",
            &["Intel 22 nm FinFET, 2011", "Gate on 3 sides vs 1"],
        ),
    Beat::new("Soitec: the SOI wafers", BEAT_MS)
        .note(
            "Soitec (SOI.PA) makes most of the SOI wafers that FD-SOI is built on. Its Smart Cut process splits a thin layer of silicon off a donor wafer and bonds it over an oxide on a handle wafer.",
            "A wafer cut in half: the cream top silicon film, the pale buried oxide and the grey handle wafer, layers drawn thick.",
        )
        .detail(
            "UMC, GlobalFoundries and SMIC also ship planar (sections 5 and 9).",
            &["Soitec Smart Cut", "Top Si / BOX / handle"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("mature-node overcapacity", BEAT_MS)
        .note(
            "New mature-node fabs, many in China, are adding capacity faster than demand. UMC shipped 12.3% more wafers in 2025 but its revenue rose only 2.3%, a sign of falling price per wafer.",
            "Grey wafers stack up one by one into a tall pile.",
        )
        .detail(
            "Volume up, price down.",
            &["UMC 2025: wafers +12.3%", "UMC 2025: revenue +2.3%"],
        ),
    Beat::new("FD-SOI stays a niche", BEAT_MS)
        .note(
            "FD-SOI serves IoT, RF and automotive chips where low leakage and body bias matter. The mass market moved to FinFET at 16/14 nm and below, so FD-SOI's ecosystem stays small.",
            "The FD-SOI device: thin film on the pale buried oxide, cyan electrons crossing under the gate.",
        )
        .detail(
            "Fewer customers means fewer tools and IP built for it.",
            &["FD-SOI: IoT, RF, automotive", "FinFET at 16/14 nm and below"],
        ),
    Beat::new("node names are not gate lengths", BEAT_MS)
        .note(
            "The '28 nm' or '22 nm' in a node name no longer matches any physical gate length, and each vendor's numbers differ. Compare nodes by transistor density, contacted gate pitch and SRAM cell size instead.",
            "A planar device with a glowing cyan bar on top of the gate showing its actual length.",
        )
        .detail(
            "Gate lengths of 'N nm' nodes vary by vendor.",
            &["Node name = label, not a ruler", "Compare density and pitches"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("[1] Dennard's end and short channels", BEAT_MS)
        .note(
            "Source 1 covers the end of Dennard scaling and the short-channel effects: semiconductor engineering's Dennard piece and an allaboutcircuits article on nanoscale electrostatics.",
            "A short-gate device with its depletion regions meeting and magenta dots punching through, tagged [1].",
        )
        .detail(
            "Backs sections 1, 3 and 6.",
            &[
                "semiengineering.com/dennards-law-and-the-finfet",
                "allaboutcircuits.com nanoscale SCE article",
            ],
        ),
    Beat::new("[2] FD-SOI", BEAT_MS)
        .note(
            "Source 2 is a Soitec press release on the FD-SOI ecosystem and a Compound Semiconductor article.",
            "The FD-SOI device, its buried oxide tagged [2].",
        )
        .detail(
            "Backs section 7.",
            &["soitec.com press release, 2015/07/14", "compoundsemiconductor.net/article/97528"],
        ),
    Beat::new("[3] strain", BEAT_MS)
        .note(
            "Source 3 is Intel's strained-silicon pages and an EDN summary; the drive-current gains are secondary summaries of Intel's 2003-04 disclosures.",
            "The PMOS with orange SiGe source and drain and arrows pressing in, tagged [3].",
        )
        .detail(
            "Backs section 4.",
            &["intel.com strain pressroom kit", "edn.com/?p=4046419"],
        ),
    Beat::new("[4-6] mature share, UMC, node naming", BEAT_MS)
        .note(
            "Source 4 is Counterpoint's pure-play foundry revenue split and a Tom's Hardware trailing-edge roadmap; source 5 is UMC's 2025 results filed with the SEC; source 6 is the node-naming articles.",
            "A stack of wafers building up, tagged with sources 4 to 6.",
        )
        .detail(
            "Backs sections 5, 8 and 9.",
            &[
                "counterpointresearch.com pure-play foundry 2025",
                "sec.gov UMC EX-99.1 (2025 results)",
                "pcgamer.com LMC paper; eejournal.com no-more-nanometers",
            ],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_planar_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` heading of CHIP_PLANAR.txt, in order (section 10 is the sources).
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_planar.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "PLANAR",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};
    use super::*;

    #[test]
    fn zoom_keys_and_beats() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let scene = (z.build)();
            assert_eq!(scene.beats().len(), 3, "zoom {}", z.key);
            explained(scene.as_ref(), &format!("zoom {}", z.key));
            draws_every_beat(scene.as_ref(), &format!("zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3, 3, 3, 3, 3, 4]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            explained(s.as_ref(), &format!("section {}", i + 1));
            draws_every_beat(s.as_ref(), &format!("section {}", i + 1));
        }
    }
}
