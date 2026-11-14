// CHIP tab, GATE-ALL-AROUND: the overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on this part (tools/pbr3d/blender/chip_gaa.py). Zoom-ins a-e and
// sections 1-10 are Blender scenes from the same script, in the picture-and-panel template.
// Sources are section 10 of CHIP_GAA.txt.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the whole chip: a gate-all-around transistor", BEAT_MS)
        .note(
            "The same chip as the hero, with the NMOS replaced by a gate-all-around (GAA) transistor. Silicon, contacts, wiring and bumps are unchanged.",
            "The highlighted block at the NMOS spot, between the silicon and the contacts.",
        )
        .detail("GAA is the transistor of the 3 nm class and below.", &["Samsung 3GAA, 2022; TSMC N2, 4Q25"]),
    Beat::new("in on the stack of nanosheets", BEAT_MS)
        .note(
            "The camera moves in. Thin silicon sheets are stacked one above another between two raised source and drain blocks.",
            "Three pale sheets, each running source to drain, with grey gate metal in the gaps between them.",
        )
        .detail("3-4 Si/SiGe pairs in the stack, about 1 nm thickness control.", &["SUPERLATTICE (textbook)"]),
    Beat::new("the gate wraps every side of each sheet", BEAT_MS)
        .note(
            "High-k dielectric and work-function metal, put down by ALD, wrap the top, bottom and both faces of each sheet. The gate turns on.",
            "Amber gate metal and a translucent shell round each sheet.",
        )
        .detail("The gaps are about 10 nm and the whole stack must fit in them.", &["HK/METAL GATE (textbook)"]),
    Beat::new("current through every sheet", BEAT_MS)
        .note(
            "With the gate on, every sheet conducts. Carriers stream from source to drain through all the sheets at once.",
            "Glowing sheets, with dots moving from the left block through each sheet to the right block.",
        )
        .detail("TSMC N2 vs N3E: +10-15% speed or -25-30% power.", &["TSMC N2, IEEE Spectrum 2024"]),
    Beat::new("a wide sheet: more drive current", BEAT_MS)
        .note(
            "Sheet width is a drawn dimension. A wider sheet has more channel area under the gate, so more current: faster, but larger.",
            "The view turns to the side; the shell along the sheet depth is wide.",
        )
        .detail("Effective width is about N sheets x (W + 2T).", &["SHEET WIDTH (textbook)"]),
    Beat::new("a narrow sheet: less leakage, less area", BEAT_MS)
        .note(
            "A narrow sheet gives less drive current but takes less area and leaks less. Designers choose the width per cell.",
            "The same view, with a thinner shell along the sheet depth.",
        )
        .detail("TSMC says N2 allows cells with different sheet widths on one chip.", &["TSMC N2, IEEE Spectrum 2024"]),
    Beat::new("back out to the whole chip", BEAT_MS)
        .note(
            "The GAA transistor is one device among many. The wiring and bumps around it are the same as in the hero.",
            "The whole chip again, with the GAA transistor highlighted.",
        )
        .detail("Backside power: Intel PowerVia on 18A; TSMC Super Power Rail on A16.", &["Intel 18A; TSMC A16"]),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

// ---- zoom-ins a-e: the process flow, release, sheet width, backside power, roadmap ----

const ZA_BEATS: &[Beat] = &[
    Beat::new("superlattice: Si and SiGe layers in the fin", BEAT_MS)
        .note(
            "Alternating silicon and SiGe layers are grown; the SiGe is sacrificial and is removed later.",
            "a block of purple SiGe bands between grey silicon sheets, at the transistor spot",
        )
        .detail("3-4 Si/SiGe pairs with about 1 nm thickness control.", &["SUPERLATTICE (page text, section 4)"]),
    Beat::new("dummy gate, inner spacer and S/D epi", BEAT_MS)
        .note(
            "A placeholder gate goes on, the SiGe ends are recessed and filled with nitride, and the source and drain grow from the sheet edges.",
            "a translucent dummy gate over the stack, the SiGe pulled back to the middle, pale spacers at its ends and blue epi blocks either side",
        )
        .detail(
            "Spacers isolate the gate from the source and drain at every level.",
            &["INNER SPACER, S/D EPI (page text, section 2)"],
        ),
    Beat::new("release and the real gate: HK/metal fills the gaps", BEAT_MS)
        .note(
            "The dummy gate and the SiGe come out; high-k and metal fill every gap and wrap each sheet.",
            "grey gate metal in the gaps between the three sheets, with the high-k skin and pale spacers at the ends",
        )
        .detail(
            "The gaps are about 10 nm and the whole stack must fit in them.",
            &["RELEASE, HK/METAL GATE (page text, section 4)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("before release: sheets with SiGe between", BEAT_MS)
        .note(
            "Silicon sheets stacked with the sacrificial SiGe between them; the source and drain are already grown.",
            "purple SiGe layers between grey silicon sheets, with blue epi blocks either side",
        )
        .detail(
            "SiGe sets the gap height: silicon, SiGe, silicon, SiGe, silicon, SiGe.",
            &["Before release (page text, section 3)"],
        ),
    Beat::new("SiGe etched sideways", BEAT_MS)
        .note(
            "A selective etch removes the SiGe from its sides and must leave the silicon alone.",
            "the SiGe layers pulled in from both ends, shrinking to short purple pieces in the middle while the sheets stand clear",
        )
        .detail(
            "Any silicon lost thins the sheet and shifts the threshold voltage.",
            &["Release: Si:SiGe selectivity (page text, section 3)"],
        ),
    Beat::new("gate metal takes its place", BEAT_MS)
        .note(
            "The SiGe is gone; high-k and metal fill the gaps, wrapping each sheet on all four sides.",
            "grey gate metal in each gap between the sheets, with no purple left",
        )
        .detail("ALD into gaps of about 10 nm (page text, section 4).", &["HK/METAL GATE"]),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("FinFET: width in whole fins", BEAT_MS)
        .note(
            "A FinFET can only add whole fins, so its width steps one fin at a time.",
            "three narrow fins side by side under one gate, seen from the side",
        )
        .detail("Discrete steps (page text, section 5).", &["FINFET"]),
    Beat::new("wide sheet: drive and speed", BEAT_MS)
        .note(
            "A sheet can be drawn any width. A wide one has more channel under the gate: more drive current, faster, but larger.",
            "three wide sheets with the gate behind each, turned to show the width in depth",
        )
        .detail("Effective width is about N sheets x (W + 2T).", &["SHEET WIDTH (page text, section 5)"]),
    Beat::new("narrow sheet: less leakage, less area", BEAT_MS)
        .note(
            "A narrow sheet gives less drive but takes less area and leaks less. Cells on one chip can mix widths.",
            "three thin sheets in the same stack, with a shorter gate shell along the depth",
        )
        .detail("TSMC says N2 allows cells with different sheet widths on one chip.", &["TSMC N2 (source 3)"]),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("front-side power: shared, crowded metal", BEAT_MS)
        .note(
            "Power and signals share the front metal: the power path climbs from the bumps through the stacked wiring, long and thin.",
            "dots running down from the VDD bump through the thin, mid and top wiring to the transistor",
        )
        .detail(
            "Conventional chips route power and signals through the same front-side metal.",
            &["Frontside power (page text, section 6)"],
        ),
    Beat::new("rails move under the substrate", BEAT_MS)
        .note(
            "The wafer is thinned and power rails are built beneath it, reached through nano-TSVs.",
            "a copper VDD rail and a grey VSS rail under the silicon, with dots rising up the TSVs to the transistor",
        )
        .detail(
            "Backside power shortens the power path.",
            &["Intel PowerVia on 18A; TSMC Super Power Rail on A16 (sources 2 and 4)"],
        ),
    Beat::new("the front metal is all signals", BEAT_MS)
        .note(
            "Signals get the front metal to themselves; the power has moved below.",
            "signal dots running along the thin wiring, with the rails still under the silicon",
        )
        .detail(
            "Less congestion on the front metal.",
            &["PowerVia (18A), Super Power Rail (A16) (sources 2 and 4)"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("FinFET: three gated sides", BEAT_MS)
        .note(
            "A FinFET gate wraps three sides of each fin; the bottom stays ungated.",
            "one fin under a gate, with metal on the top and both sides",
        )
        .detail("Fins run out of room below 3 nm (page text, section 8).", &["FINFET to about 3 nm class"]),
    Beat::new("nanosheet: gate on four sides", BEAT_MS)
        .note(
            "The sheets are stacked and the gate wraps all four sides of each one, as in N2, 18A and SF2.",
            "three sheets with a translucent gate shell round each and gate metal in the gaps",
        )
        .detail("Nanosheets are the current node class (page text, section 8).", &["NANOSHEET at N2, 18A, SF2"]),
    Beat::new("forksheet: a wall between n and p", BEAT_MS)
        .note(
            "A forksheet puts a dielectric wall between the NMOS and PMOS sheets so they can sit closer.",
            "two devices with a grey wall between them, the wall as tall as the gates",
        )
        .detail("imec extends nanosheets to A10 with the forksheet (page text, section 8).", &["FORKSHEET (source 5)"]),
    Beat::new("CFET: NMOS over PMOS", BEAT_MS)
        .note(
            "A CFET stacks an NMOS sheet stack over a PMOS one on the same footprint; imec puts monolithic CFET at A7, after 2030.",
            "two devices stacked: the NMOS below, the PMOS above it, each with blue epi either side",
        )
        .detail("The CFET is on the imec roadmap beyond 2030 (page text, section 8).", &["CFET (source 5)"]),
];

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_a.glb"),
        ZA_BEATS,
    )
}
fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_b.glb"),
        ZB_BEATS,
    )
}
fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_c.glb"),
        ZC_BEATS,
    )
}
fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_d.glb"),
        ZD_BEATS,
    )
}
fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gaa_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the process flow: superlattice to gate",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "release: etching out the SiGe",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "sheet width: a new design knob",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "backside power",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "roadmap: nanosheet, forksheet, CFET",
        build: zoom_e,
    },
];

// ---- sections 1-10, one picture per `# ` heading of CHIP_GAA.txt ----

const SEC1: &[Beat] = &[
    Beat::new("stack the sheets: Si and SiGe", BEAT_MS)
        .note(
            "Si and SiGe layers are grown in each fin: silicon sheets with purple SiGe between.",
            "the stack of grey silicon bands alternating with purple SiGe, blue epi either side",
        )
        .detail(
            "3-4 Si/SiGe pairs in the stack, about 1 nm thickness control.",
            &["SUPERLATTICE (textbook)"],
        ),
    Beat::new("release them: SiGe out", BEAT_MS)
        .note(
            "The SiGe is etched sideways out of the gaps, leaving the silicon sheets suspended between the source and drain.",
            "the purple SiGe pulled in to short pieces, the three sheets bridging the blue epi blocks",
        )
        .detail(
            "The etch needs high Si:SiGe selectivity; any lost silicon thins the sheet.",
            &["RELEASE (page text, section 4)"],
        ),
    Beat::new("wrap the gate", BEAT_MS)
        .note(
            "High-k and metal wrap every side of each sheet. The gate turns on.",
            "amber gate metal and a translucent shell round each sheet",
        )
        .detail(
            "The gaps are about 10 nm; the whole stack must fit in them.",
            &["HK/METAL GATE (page text, section 4)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("source and drain epi", BEAT_MS)
        .note(
            "Raised n+ blocks at either end, grown from the sheet edges for strain and low contact resistance.",
            "the two blue epi blocks either side of the stack, the sheets between them dim",
        )
        .detail(
            "SiP for NMOS, grown from the sheet edges.",
            &["S/D EPI (page text, section 2)"],
        ),
    Beat::new("carriers through every sheet", BEAT_MS)
        .note(
            "With the gate on, current flows from source to drain through each silicon sheet.",
            "the three sheets glow cyan and dots run from the left block through each one to the right",
        )
        .detail(
            "Current flows through each sheet to the drain epi.",
            &["Along the channel (page text, section 2)"],
        ),
    Beat::new("gate and inner spacers", BEAT_MS)
        .note(
            "High-k and metal wrap each sheet; inner spacers isolate the gate from the source and drain.",
            "the gate lit amber around the sheets, pale spacers between the gate and the epi",
        )
        .detail(
            "SiN or SiOCN spacers isolate the gate from the S/D at every level.",
            &["INNER SPACER (page text, section 2)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("before release", BEAT_MS)
        .note(
            "Silicon sheets with sacrificial SiGe between, the source and drain already grown.",
            "purple SiGe layers between grey sheets, blue epi either side",
        )
        .detail(
            "SiGe sets the gap height.",
            &["Before release (page text, section 3)"],
        ),
    Beat::new("SiGe recessed, nitride in", BEAT_MS)
        .note(
            "The SiGe ends are recessed and filled with nitride: the inner spacers.",
            "the SiGe pulled back to the middle, pale spacers at both ends",
        )
        .detail(
            "Recess, fill, etch back: a source of variation in the process.",
            &["INNER SPACER (page text, section 4)"],
        ),
    Beat::new("after release: gate metal", BEAT_MS)
        .note(
            "The SiGe is gone; gate metal fills every gap and wraps each sheet.",
            "grey gate metal in each gap, no purple left",
        )
        .detail(
            "Any silicon lost to the etch shifts the threshold voltage.",
            &["Selectivity (page text, section 3)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("SUPERLATTICE: Si and SiGe pairs", BEAT_MS)
        .note(
            "Alternating silicon and SiGe layers are grown in the fin; the SiGe is sacrificial.",
            "purple SiGe bands between grey silicon sheets, a block at the transistor spot",
        )
        .detail("3-4 pairs, about 1 nm thickness control.", &["SUPERLATTICE (page text, section 4)"]),
    Beat::new("INNER SPACER: SiGe recessed, nitride in", BEAT_MS)
        .note(
            "The SiGe ends are recessed, then filled with nitride so the gate and the epi cannot touch.",
            "the purple SiGe shortened to the middle, pale spacers at both ends",
        )
        .detail("Spacers isolate the gate from S/D at every level.", &["INNER SPACER (page text, section 4)"]),
    Beat::new("S/D EPI: grown from the sheet edges", BEAT_MS)
        .note(
            "The source and drain grow from the sheet edges, after the spacers.",
            "blue epi blocks rise either side, past the top sheet",
        )
        .detail("Strain and low contact resistance (page text, section 2).", &["S/D EPI"]),
    Beat::new("RELEASE: SiGe out", BEAT_MS)
        .note(
            "The SiGe is etched away sideways; the sheets are left standing between the epi.",
            "the sheets bridging the epi with no SiGe between them",
        )
        .detail("Needs high Si:SiGe etch selectivity (page text, section 3).", &["RELEASE"]),
    Beat::new("HK/METAL GATE: wrap every sheet", BEAT_MS)
        .note(
            "High-k and metal go into the gaps by ALD and wrap every sheet on four sides.",
            "amber gate on the metal and the translucent shell round each sheet",
        )
        .detail("Gaps of about 10 nm must fit the whole stack.", &["HK/METAL GATE"]),
];

const SEC7: &[Beat] = &[
    Beat::new("Samsung SF3E: first GAA (2022)", BEAT_MS)
        .note(
            "vs 5 nm: -45% power, +23% performance, -16% area (vendor claim).",
            "the nanosheet stack with the gate on and the sheets lit",
        )
        .detail("Vendor claims under different conditions.", &["Samsung 3GAA (source 1)"]),
    Beat::new("TSMC N2 and Intel 18A (2025)", BEAT_MS)
        .note(
            "N2 vs N3E: +10-15% speed or -25-30% power. 18A vs Intel 3: about 25% frequency or -36% power at 1.1 V.",
            "the same stack with the sheets conducting, dots moving through every sheet",
        )
        .detail("Vendor claims, not equal conditions.", &["TSMC N2 (source 3); Intel 18A (source 2)"]),
    Beat::new("TSMC A16 (2026+): backside power", BEAT_MS)
        .note(
            "Adds backside power: +8-10% speed and -15-20% power vs N2P, up to 8-10% density (vendor claim).",
            "the stack with copper and grey rails under the silicon, dots rising through the TSVs",
        )
        .detail("Super Power Rail contacts the source and drain directly.", &["TSMC A16 (source 4)"]),
];

const SEC8: &[Beat] = &[
    Beat::new("NODES: SF3, N2, 18A, A16", BEAT_MS)
        .note(
            "Samsung, TSMC and Intel all ship nanosheets, under different names.",
            "the gate-on stack with the sheets conducting and the node names in the tags",
        )
        .detail("Different names, same idea (page text, section 8).", &["NODES"]),
    Beat::new("TOOLS: epi, ALD, selective etch", BEAT_MS)
        .note(
            "GAA raises tool spend: about $7B per 100K wafer starts a month vs $6B for FinFET (Applied).",
            "the epi blocks, the gate shell and the stack; the tags name the process steps",
        )
        .detail(
            "Applied, Lam, TEL and ASML sell the tools.",
            &["Applied Materials Q2 FY2024 call (source 7); Lam Akara (source 8)"],
        ),
    Beat::new("forksheet, then CFET", BEAT_MS)
        .note(
            "Forksheet puts a wall between n and p sheets (to A10); CFET stacks NMOS over PMOS (A7, after 2030).",
            "the NMOS below and the PMOS above, on one footprint",
        )
        .detail("imec roadmap (page text, section 8).", &["imec (source 5)"]),
];

const SEC9: &[Beat] = &[
    Beat::new("Samsung SF3E: yield 50-60%", BEAT_MS)
        .note(
            "Reported SF3E yields: 50-60% (2024), SF3 about 20%, SF2 test about 30% (Feb 2025).",
            "the gate-on stack with the sheets lit and a short gate",
        )
        .detail(
            "Secondary reports, not audited.",
            &["Samsung yields (reports, source 6)"],
        ),
    Beat::new("N3E FinFET: about 82-86%", BEAT_MS)
        .note(
            "The FinFET it replaces yields far better (N3E about 82-86%, report).",
            "a single FinFET block with its three fins",
        )
        .detail(
            "GAA resets the learning curve.",
            &["N3E 82-86% (report, source 6)"],
        ),
    Beat::new("wafer price: over $30,000 (reported)", BEAT_MS)
        .note(
            "N2 wafers are reported above $30,000 vs about $18,000 for N3 (unconfirmed).",
            "a wafer under the chip, with the wiring above it",
        )
        .detail(
            "Cost per good die rises when yield is low.",
            &["N2 wafer price (report, source 6)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("Samsung 3GAA and Intel 18A", BEAT_MS)
        .note(
            "Samsung's first GAA production and Intel's 18A PowerVia and performance figures.",
            "the first card lit on the plinth",
        )
        .detail("Vendor announcements.", &["Samsung news; Intel newsroom and Tom's Hardware (sources 1, 2)"]),
    Beat::new("TSMC N2 and A16", BEAT_MS)
        .note(
            "TSMC's N2 volume production and the A16 backside power plan.",
            "the second card lit",
        )
        .detail("TSMC research pages and press (sources 3, 4).", &["IEEE Spectrum; AnandTech (sources 3, 4)"]),
    Beat::new("imec and press reports", BEAT_MS)
        .note(
            "imec's forksheet and CFET roadmap; press reports on yields and wafer prices.",
            "the third card lit",
        )
        .detail("Roadmap and reports (sources 5, 6).", &["imec articles; TechSpot, NotebookCheck (sources 5, 6)"]),
    Beat::new("Applied, Lam and IBM", BEAT_MS)
        .note(
            "Applied Materials' GAA tool spend, Lam's Akara etch tool, and IBM's dry selective SiGe etch paper.",
            "the fourth card lit",
        )
        .detail("Tool makers and research (sources 7, 8, 9).", &["Applied call; Lam Akara; PMC and IBM research (sources 7, 8, 9)"]),
];

static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_gaa_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` heading of the page, in order. Sections 5 and 6 reuse the zoom-in
/// beats of c and d, as the scenes do.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, ZC_BEATS),
    section!(6, ZD_BEATS),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

pub const NODE: Node = Node {
    page: "GATE-ALL-AROUND",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_and_sections_match_the_blender_beats_and_draw() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        let zoom_beats: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(zoom_beats, [3, 3, 3, 3, 4]);
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 5, 3, 3, 3, 3, 3, 4]);
        for z in ZOOMS {
            let s = (z.build)();
            super::super::super::blender::explained(s.as_ref(), &format!("zoom {}", z.key));
            super::super::super::blender::draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
