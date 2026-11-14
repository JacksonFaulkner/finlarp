// CHIP tab, PLANAR: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on the planar NMOS (tools/pbr3d/blender/chip_planar.py). The gate
// lies flat on the channel and controls it from one side only; as the channel shortens, the drain
// pulls on it and current leaks under the gate in the off state.
//
// Zoom-ins a-e and sections 1-10 are Blender scenes from the same script: zoom b and section 3
// share a scene, as do zoom e and section 6, and zoom d and section 7.
//
// Sources: CHIP_PLANAR.details.txt (Counterpoint mature-node share, Intel 22 nm FinFET, textbook
// subthreshold and DIBL figures, allaboutcircuits nanoscale SCE article).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("a flat channel under a flat gate", BEAT_MS)
        .note(
            "The whole chip, with the planar NMOS lit: a gate lying flat on a channel at the silicon surface, the transistor that carried logic to 28 nm.",
            "the cyan block over the NMOS, its flat grey gate on top, the PMOS dim beside it",
        )
        .detail(
            "Every chip was built this way until the planar limit at 28 to 22 nm.",
            &["Planar bulk CMOS: to 28/22 nm (CHIP_PLANAR.txt, section 2)"],
        ),
    Beat::new("the gate lies flat on the channel, on one side only", BEAT_MS)
        .note(
            "Source and drain are n+ blocks either side of the gate, which sits on a thin oxide. The channel is the layer of silicon under the gate, and the gate touches it from the top only.",
            "the grey gate on its oxide, the blue n+ source and drain, the channel between them at the surface, the tan p-type body below",
        )
        .detail(
            "The gate can switch the channel from above only; everything below the surface is outside its reach.",
            &["Electrons flow in the inversion layer under the gate (textbook)"],
        ),
    Beat::new("gate high: the channel forms and carries current", BEAT_MS)
        .note(
            "With the gate high the channel inverts under it, and electrons run from source to drain along the surface.",
            "the amber gate lit, the cyan channel under it, the white dots running from source to drain",
        )
        .detail(
            "On state: a long planar channel conducts well, and the one-sided gate is enough to switch it.",
            &["Planar NMOS conducts with the gate high (textbook)"],
        ),
    Beat::new("the channel shortens: the drain pulls on the barrier", BEAT_MS)
        .note(
            "As the gate gets shorter, the depletion regions of the drain and the source reach toward each other under the channel. The gate, on one side, loses its grip on the barrier between them.",
            "two orange depletion bands growing out of the n+ junctions until they meet under the channel",
        )
        .detail(
            "Drain-induced barrier lowering: a higher drain voltage lowers the source barrier, so the threshold falls.",
            &[
                "DIBL: Vt falls as Vd rises (allaboutcircuits, nanoscale SCE article)",
                "Subthreshold swing floor about 60 mV per decade at 300 K (textbook)",
            ],
        ),
    Beat::new("gate low: off, yet current leaks under the gate", BEAT_MS)
        .note(
            "With the gate low the channel is gone, but charge still slips from the drain to the source through the body, under the gate.",
            "the gate dark and the channel gone, white dots arcing from the drain under the gate to the source through the orange depletion band",
        )
        .detail(
            "Each 60 mV of threshold given up multiplies the off-state current by ten, so leakage grows as the channel shortens.",
            &[
                "Each 60 mV of Vt lost = 10x off-state leakage (textbook)",
                "Leak paths: subthreshold and punch-through (textbook)",
            ],
        ),
    Beat::new("back out: the planar limit", BEAT_MS)
        .note(
            "The camera backs out to the whole chip. Planar stopped scaling here: a flat gate cannot cut off the path below the surface, so the channel was raised into fins.",
            "the whole chip again, the planar NMOS lit, the depletion bands gone",
        )
        .detail(
            "Mature nodes at 28 nm and above still make most wafers, so planar silicon is not gone.",
            &[
                "Mature nodes (28 nm and above): 36% of pure-play foundry revenue in 2025 (Counterpoint)",
                "Intel shipped the first 22 nm FinFET in 2011 (CHIP_PLANAR.details.txt)",
            ],
        ),
];

// ---- zoom-ins a-e ---------------------------------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("subthreshold: drain to source below Vt", BEAT_MS)
        .note(
            "With the gate low the channel is nearly off, but a weak current still crosses under it below threshold.",
            "faint dots crossing the channel at the surface, the planar NMOS tagged, the gate dark",
        )
        .detail(
            "Off-state current is set by the swing and the threshold voltage.",
            &["Subthreshold swing floor about 60 mV per decade at 300 K (textbook)"],
        ),
    Beat::new("gate tunnelling through thin oxide", BEAT_MS)
        .note(
            "Thin SiON lets carriers tunnel straight through the gate dielectric, even with the gate off.",
            "pink dots rising through the lit oxide layer under the gate, tagged gate tunnelling",
        )
        .detail(
            "High-k fixed this: a physically thicker film of HfO2 gives the same gate capacitance.",
            &[
                "SiON below about 1.2 nm leaks too much (textbook)",
                "HfO2 has a higher dielectric constant than SiON (textbook)",
            ],
        ),
    Beat::new("punch-through and junction leakage", BEAT_MS)
        .note(
            "In a short device the depletion regions meet deep in the body, and the drain junction leaks too (GIDL).",
            "pink dots arcing from the drain to the source under the channel, a tag on the drain junction",
        )
        .detail(
            "Halos and fins fight this path.",
            &["Four leak paths: subthreshold, tunnelling, junction/GIDL, punch-through (textbook)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("SHORT CHANNEL: the drain reaches the source", BEAT_MS)
        .note(
            "Shrink the gate and the depletion fields of the drain and the source reach toward each other under the channel.",
            "two orange depletion bands growing out of the n+ junctions until they nearly meet under a short gate",
        )
        .detail(
            "The gate loses its hold on the barrier between the two.",
            &["Short-channel effects: Vt roll-off, DIBL, punch-through (allaboutcircuits, nanoscale SCE article)"],
        ),
    Beat::new("DIBL: Vt falls with drain voltage", BEAT_MS)
        .note(
            "A higher drain voltage lowers the source barrier, so the threshold drops and leakage grows.",
            "the drain tagged, a strong leak arcing from the drain to the source under the bands",
        )
        .detail(
            "Off-current rises with the drain voltage a circuit runs at.",
            &["DIBL: Vt falls as Vd rises (allaboutcircuits, nanoscale SCE article)"],
        ),
    Beat::new("the swing floor", BEAT_MS)
        .note(
            "The subthreshold swing cannot fall below about 60 mV per decade at room temperature, so each 60 mV of Vt lost costs ten times the off-state current.",
            "a weak leak under the channel, the tag on the swing floor",
        )
        .detail(
            "Lowering Vt to gain speed costs standby power exponentially.",
            &[
                "Swing floor about 60 mV per decade at 300 K (textbook)",
                "Each 60 mV of Vt lost = 10x off-state leakage (textbook)",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("polysilicon on SiON", BEAT_MS)
        .note(
            "The old gate: doped polysilicon on a thin SiON oxide, which leaked by tunnelling as it thinned.",
            "a brown polysilicon gate on a thin pale oxide, the oxide tagged SiON",
        )
        .detail(
            "By the 90 to 65 nm nodes the SiON was only a few atomic layers thick.",
            &["SiON below about 1.2 nm leaks too much (textbook)"],
        ),
    Beat::new("HfO2: thicker but electrically thinner", BEAT_MS)
        .note(
            "Hafnium oxide's high dielectric constant gives the same gate capacitance from a physically thicker film, so tunnelling falls sharply.",
            "a pale HfO2 film under the poly gate, thicker than the SiON it replaces",
        )
        .detail(
            "The thicker film is what cuts the tunnelling.",
            &["HfO2 high-k: thicker film, same capacitance (textbook)"],
        ),
    Beat::new("a metal gate sets Vt", BEAT_MS)
        .note(
            "The metal gate replaces poly; its work function sets the threshold voltage, and gate-last flows arrived at 45 to 28 nm.",
            "the gate lit amber as metal, tagged metal gate sets Vt",
        )
        .detail(
            "This stack is the direct ancestor of the FinFET and GAA gate stacks.",
            &["Intel HKMG with gate-last at 45 nm, 2007 (textbook)"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("bulk: depletion reaches deep", BEAT_MS)
        .note(
            "In bulk silicon the depletion region and the leak paths reach deep into the body, where random dopants vary Vt.",
            "a deep translucent depletion region under the transistor, the leak arcing down through it",
        )
        .detail(
            "Random dopant variation is what the thin film removes.",
            &["Bulk: depletion and leak paths reach deep (textbook)"],
        ),
    Beat::new("FD-SOI: a thin film on buried oxide", BEAT_MS)
        .note(
            "A few-nanometre undoped film sits on a buried oxide (BOX), which holds no depletion charge and blocks the leakage path below.",
            "the pale BOX layer under the transistor, the thin silicon film above it, no leak below",
        )
        .detail(
            "Soitec's Smart Cut process makes the wafers.",
            &[
                "FD-SOI: thin film on BOX (soitec.com press release, 2015/07/14)",
                "Smart Cut substrate process (textbook)",
            ],
        ),
    Beat::new("body bias under the BOX", BEAT_MS)
        .note(
            "A voltage applied under the BOX tunes Vt after fabrication: faster when needed, low-leakage when idle.",
            "the substrate under the BOX lit violet, the tag on back bias",
        )
        .detail(
            "GlobalFoundries ships FD-SOI as 22FDX.",
            &[
                "Forward body bias lowers Vt, reverse raises it (textbook)",
                "GlobalFoundries 22FDX (2015 announcement, soitec.com)",
            ],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("one node: shrink everything by 1/k", BEAT_MS)
        .note(
            "Scale dimensions and voltage by 1/k, about 0.7 per node, and the transistor shrinks with them.",
            "one transistor with the on-current dots running across the channel, the tag x 1/k",
        )
        .detail(
            "Dennard's recipe: per-gate power falls as 1/k squared.",
            &["Dennard scaling, k about 1.4 per node (textbook; semiengineering.com/dennards-law-and-the-finfet)"],
        ),
    Beat::new("twice the transistors, same power", BEAT_MS)
        .note(
            "Gates per area rise as k squared while power per gate falls as 1/k squared, so power density stays flat.",
            "the transistor scaled down in the picture, the tag on the power arithmetic",
        )
        .detail(
            "The clock could rise about 1.4 times per node for free.",
            &["Power density x 1 (textbook)"],
        ),
    Beat::new("until Vt stopped scaling", BEAT_MS)
        .note(
            "Leakage grows exponentially as Vt falls, so the supply stalled near 1 V; more transistors at the same power meant dark silicon and multicore.",
            "the leak arcing under the shrunk transistor, the tag on the leakage wall",
        )
        .detail(
            "The breakdown is dated to about 2005.",
            &[
                "Vdd stalled near 1 V; clocks plateaued around 3-5 GHz (textbook)",
                "Breakdown dated to about 2005 (semiengineering.com/dennards-law-and-the-finfet)",
            ],
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

const SEC1: &[Beat] = &[
    Beat::new("DENNARD SCALING: shrinking was free", BEAT_MS)
        .note(
            "For decades shrinking the planar transistor was free: speed rose while power density stayed flat.",
            "the whole chip, the planar NMOS tagged free scaling",
        )
        .detail(
            "Each node cut dimensions and voltage together.",
            &["Dennard scaling (textbook; semiengineering.com/dennards-law-and-the-finfet)"],
        ),
    Beat::new("the LEAKAGE WALL", BEAT_MS)
        .note(
            "Around 2005 the threshold voltage could no longer fall without leakage exploding, and the supply stalled near 1 V.",
            "the planar NMOS close up, leak dots escaping from the drain and under the gate",
        )
        .detail(
            "Off-state leakage grows exponentially as Vt falls.",
            &[
                "Supply stalled near 1 V (textbook)",
                "Breakdown dated to about 2005 (semiengineering.com/dennards-law-and-the-finfet)",
            ],
        ),
    Beat::new("patched, then replaced", BEAT_MS)
        .note(
            "Strained silicon, high-k metal gate and FD-SOI patched planar from 90 nm to 22/28 nm before the industry moved to fins.",
            "the whole chip with the planar NMOS lit",
        )
        .detail(
            "Planar still makes most wafers at mature nodes, 28 nm and above.",
            &[
                "Mature nodes 28 nm and above: 36% of pure-play foundry revenue in 2025 (Counterpoint)",
                "Intel shipped the first 22 nm FinFET in 2011 (CHIP_PLANAR.details.txt)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("the cross-section", BEAT_MS)
        .note(
            "n+ source and drain either side of a gate on a thin dielectric, all on p-type bulk silicon shared by every transistor on the die.",
            "the NMOS conducting: gate lit, electrons running source to drain on the surface, the n+ blocks tagged",
        )
        .detail(
            "Electrons flow in the inversion layer under the gate.",
            &[
                "Planar bulk CMOS to 28/22 nm (CHIP_PLANAR.txt, section 2)",
                "Electrons in the inversion layer (textbook)",
            ],
        ),
    Beat::new("off, it should block", BEAT_MS)
        .note(
            "With the gate low the channel is gone, and the device should cut off the current.",
            "the gate dark, no channel, no dots, the tags on the source and the drain",
        )
        .detail(
            "The gate sees only the top of the channel.",
            &["The gate sees only the top; the drain field reaches through the body (CHIP_PLANAR.txt, section 2)"],
        ),
    Beat::new("four leak paths", BEAT_MS)
        .note(
            "Subthreshold, gate tunnelling, junction leakage and punch-through all leak while the device is off.",
            "dots leaking under the gate, through the oxide and through the body",
        )
        .detail(
            "Each path needs its own fix.",
            &["Four leak paths: subthreshold, tunnelling, junction/GIDL, punch-through (textbook)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("STRAINED SI", BEAT_MS)
        .note(
            "SiGe in the PMOS source and drain squeezes its channel, and a nitride cap stretches the NMOS.",
            "the PMOS source and drain lit as SiGe, the NMOS under a pale nitride cap",
        )
        .detail(
            "Strain buys carrier mobility.",
            &["Intel 90 nm: about +25% PMOS and +10% NMOS drive current (secondary summary of Intel disclosure)"],
        ),
    Beat::new("HIGH-K: HfO2 replaces SiON", BEAT_MS)
        .note(
            "A hafnium-based dielectric is physically thicker for the same capacitance, which cuts gate tunnelling.",
            "a pale HfO2 film under the gate, thicker than the SiON it replaces",
        )
        .detail(
            "The thicker film cuts the tunnelling without losing the gate's control.",
            &["Hafnium high-k: thicker film, same capacitance (textbook)"],
        ),
    Beat::new("HIGH-K METAL GATE: the metal", BEAT_MS)
        .note(
            "A metal gate replaces poly and its work function sets Vt; gate-last flows arrived at 45 to 28 nm.",
            "the gate lit amber as metal, tagged metal gate sets Vt",
        )
        .detail(
            "Gate-last lets the N and P work functions be tuned apart.",
            &["Intel HKMG with gate-last at 45 nm, 2007 (textbook)"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("MATURE NODES: 36% of foundry revenue", BEAT_MS)
        .note(
            "28 nm and above were 36% of pure-play foundry revenue in 2025, down from 54% in 2021.",
            "the whole chip with the planar NMOS lit, the tag on the share",
        )
        .detail(
            "Mature wafers sell for less, so their share of wafers is higher than their share of revenue.",
            &["Counterpoint: mature nodes 36% of pure-play revenue in 2025, 54% in 2021"],
        ),
    Beat::new("UMC and GLOBALFOUNDRIES", BEAT_MS)
        .note(
            "UMC put 22 and 28 nm at about 35 to 40% of its 2025 revenue; GlobalFoundries makes FD-SOI (22FDX), RF and automotive parts.",
            "the FD-SOI device with its buried oxide, the tag on UMC and GF",
        )
        .detail(
            "UMC 2025 revenue NT$237.5B; GlobalFoundries FY25 revenue about $6.79B.",
            &[
                "UMC 2025 results (sec.gov EX-99.1)",
                "GlobalFoundries FY25 revenue (secondary report, check the 20-F)",
            ],
        ),
    Beat::new("SMIC", BEAT_MS)
        .note(
            "SMIC builds mostly 28 nm and above, for mature and domestic demand.",
            "the whole chip with the planar NMOS lit, tagged SMIC",
        )
        .detail(
            "SMIC reports in China and Hong Kong filings, not with the SEC.",
            &["SMIC (0981.HK), mostly 28 nm and above (secondary report, methodology unverified)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("TSMC and Intel", BEAT_MS)
        .note(
            "TSMC still runs a large 28 nm line; Intel shipped the first 22 nm FinFET in 2011.",
            "the planar NMOS lit, the tag on the first FinFET",
        )
        .detail(
            "Leading-edge planar gave way to fins, and Intel went first.",
            &[
                "Intel 22 nm FinFET, 2011 (CHIP_PLANAR.details.txt)",
                "TSMC 28 nm planar line (textbook)",
            ],
        ),
    Beat::new("UMC, GlobalFoundries, SMIC", BEAT_MS)
        .note(
            "The mature-node foundries ship most of the planar wafers today.",
            "the whole chip with the planar NMOS lit, the tag on the foundries",
        )
        .detail(
            "Mature foundries serve power, display, MCU, automotive and RF.",
            &[
                "UMC 2025 results (sec.gov EX-99.1)",
                "SMIC (0981.HK), mostly 28 nm and above",
            ],
        ),
    Beat::new("Soitec", BEAT_MS)
        .note(
            "Soitec makes the SOI wafers that FD-SOI is built on, with a buried oxide under each device.",
            "the BOX layer lit under the device, the tag on Soitec",
        )
        .detail(
            "Smart Cut makes the thin film on the buried oxide.",
            &["Soitec press release, 2015/07/14 (FD-SOI ecosystem)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("overcapacity", BEAT_MS)
        .note(
            "Mature-node capacity added in China adds price pressure: UMC wafer shipments rose 12.3% in 2025, revenue 2.3%.",
            "the whole chip with the planar NMOS lit, tagged overcapacity",
        )
        .detail(
            "Volume up, price down.",
            &["UMC 2025: shipments +12.3%, revenue +2.3% (sec.gov EX-99.1)"],
        ),
    Beat::new("FD-SOI stays niche", BEAT_MS)
        .note(
            "FD-SOI serves IoT, RF and automotive; the mass market moved to FinFET at 16 and 14 nm and below.",
            "the BOX layer and thin film under the device, tagged FD-SOI",
        )
        .detail(
            "FinFET took the mass market at 16/14 nm and below.",
            &["FD-SOI as a niche (textbook; CHIP_PLANAR.details.txt)"],
        ),
    Beat::new("node names: not gate lengths", BEAT_MS)
        .note(
            "The 'N nm' label no longer matches any real gate length, so compare nodes by density instead.",
            "the depletion bands under a short gate, tagged node names",
        )
        .detail(
            "Density, pitches and SRAM cell size tell the real story.",
            &["Node naming: pcgamer.com LMC paper; eejournal.com, no more nanometers"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("the scaling story: Dennard and the short channel", BEAT_MS)
        .note(
            "Two articles cover the scaling story: a semiconductor engineering piece on Dennard scaling and the FinFET, and an allaboutcircuits piece on nanoscale short-channel effects.",
            "the whole chip pulling back slowly, the tag on the sources",
        )
        .detail(
            "These cards back sections 1, 3 and 6.",
            &[
                "semiengineering.com/dennards-law-and-the-finfet",
                "allaboutcircuits.com nanoscale SCE electrostatic challenges article",
            ],
        ),
    Beat::new("FD-SOI and strain", BEAT_MS)
        .note(
            "The FD-SOI cards are a Soitec press release and a compound semiconductor article; the strain cards are Intel's disclosure and a secondary summary.",
            "the pull-back continuing, the tag on the sources",
        )
        .detail(
            "Strain figures are secondary summaries of Intel disclosures.",
            &[
                "soitec.com press release, 2015/07/14",
                "intel.com strain pressroom; edn.com/?p=4046419",
            ],
        ),
    Beat::new("mature share and UMC", BEAT_MS)
        .note(
            "Counterpoint's pure-play foundry revenue and the UMC SEC exhibit give the mature-node share and the 2025 numbers.",
            "the whole chip with the tag on the sources",
        )
        .detail(
            "Revenue figures are from the 2025 reports.",
            &[
                "counterpointresearch.com pure-play foundry revenue 2025",
                "sec.gov EX-99.1, UMC 2025 results",
            ],
        ),
    Beat::new("node naming and the roadmap", BEAT_MS)
        .note(
            "Node naming (PC Gamer, EE Journal) and the Tom's Hardware trailing-edge roadmap close the page.",
            "the whole chip, the tag on the sources",
        )
        .detail(
            "Read node names as density, not nanometres.",
            &[
                "pcgamer.com LMC paper; eejournal.com no-more-nanometers",
                "tomshardware.com trailing-edge foundry roadmap",
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
    section!(3, ZB_BEATS),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, ZE_BEATS),
    section!(7, ZD_BEATS),
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
