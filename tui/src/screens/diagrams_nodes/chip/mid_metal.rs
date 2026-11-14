// CHIP tab, MID METAL: the overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py) with
// the camera zooming in on the middle wiring tier, M5-M9 (tools/pbr3d/blender/chip_mid_metal.py).
// Six beats. Zoom-ins a-e and sections 1-10 are Blender scenes from the same script, each a
// picture-and-panel page (docs/diagram-pages.md): zooms are 3 beats, sections 3 or 4.
//
// Sources: tui/src/screens/diagrams_pages/CHIP_MID_METAL.txt and .details.txt (IBM copper history
// and resistivity study; Intel 4 and TSMC N5 and N3E node notes; low-k modulus, patent text; Intel
// IEDM 2024; Lienig EM slides; Applied and Lam filings; textbook RC).

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("the middle tier: M5-M9 route block to block", BEAT_MS)
        .note(
            "The whole chip, cut open. Above the thin wires, five levels of copper, M5-M9, carry signals from one block to the next. The middle tier is lit.",
            "the lit band of copper between the thin wires below and the thick top wires above, with the vias that join the levels",
        )
        .detail(
            "Medium copper is the tier that routes block-to-block signals, between thin M1-M4 and thick M10-M14.",
            &[
                "M5-M9: five dual-damascene passes (CHIP_MID_METAL.txt, section 1)",
                "Medium levels balance R and C (CHIP_MID_METAL.txt, section 3)",
            ],
        ),
    Beat::new("in on the mid wires", BEAT_MS)
        .note(
            "The camera glides in on the middle tier. Each wire is a copper line in low-k dielectric, and a signal crosses to the next block only along these wires and the vias between them.",
            "the lit copper runs left and right at several heights, joined by vertical vias, with the block beneath",
        )
        .detail(
            "Block-to-block wires are wider and taller than the thin level, so they carry signals further.",
            &[
                "Dual damascene: one copper fill and one CMP per level (CHIP_MID_METAL.txt, section 2)",
                "Cu resistivity: about 2.0 uOhm-cm in wide lines, over 3.0 below about 60 nm (IBM study)",
            ],
        ),
    Beat::new("a short hop: one block over is quick", BEAT_MS)
        .note(
            "A signal leaves a via and runs along one middle wire to the next block. The wire is short, so its resistance and capacitance are small and the signal arrives fast.",
            "a train of cyan dots running from the via along one short run, reaching its end before the longer run below does",
        )
        .detail(
            "Wire delay is set by R times C, so a short wire is fast.",
            &[
                "Wire delay ~ R x C = rho k eps0 L^2 / (W S) (CHIP_MID_METAL.txt, section 3; textbook)",
                "Cu resistivity: about 2.0 uOhm-cm in wide lines (IBM study)",
            ],
        ),
    Beat::new("a longer run takes longer", BEAT_MS)
        .note(
            "The same signal on a longer run. Both the resistance and the capacitance to the neighbouring wires grow with length, so the delay grows faster than the length.",
            "the cyan dots on the long run to the left, slower to arrive than the short hop before, with the via at their start",
        )
        .detail(
            "Both R and C grow with length, so the RC product grows with length squared.",
            &[
                "R x C scales with L^2 (CHIP_MID_METAL.txt, section 3; textbook)",
                "Long nets get repeaters, or move to upper levels (CHIP_MID_METAL.txt, section 3)",
            ],
        ),
    Beat::new("why: resistance times capacitance", BEAT_MS)
        .note(
            "Up close, one wire has resistance from its narrow copper, and capacitance to the wire beside it through the dielectric between them. The delay is their product.",
            "the copper line with the via rising from it; the tag R marks the narrow copper, the tag C marks the gap of dielectric between it and the next wire",
        )
        .detail(
            "Narrower lines raise R and closer neighbours raise C. Low-k cuts C, but soft low-k is weak.",
            &[
                "SiO2 k 4.0 at about 72 GPa; carbon-doped oxide k 2.7 at 7-10 GPa (patent text, section 5)",
                "Air gaps cut line-to-line capacitance by up to 25% (Intel IEDM 2024)",
            ],
        ),
    Beat::new("the longest runs climb to the thick top", BEAT_MS)
        .note(
            "Back on the whole chip. The longest signals leave the middle tier and climb to the thick top wires, which have the lowest resistance. Critical nets move up, and repeaters cover the rest.",
            "the top tier lit in gold, the middle tier below it, and the long runs rising through the vias",
        )
        .detail(
            "Wider, thicker copper has lower resistance, so the longest runs move up.",
            &[
                "Thick M10-M14 carry power, clock and global wires (CHIP_MID_METAL.txt, section 3)",
                "Designers insert repeaters and move critical nets to upper levels (CHIP_MID_METAL.txt, section 3)",
            ],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

// ---- zoom-ins a-e -----------------------------------------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("trench and via, cut through one mask", BEAT_MS)
        .note(
            "The level about to form: a trench and the via below it are etched into the low-k film through one hard mask.",
            "the lilac dielectric band over the lower wire run, with the via column dropping to the level below; the tag marks the trench and via",
        )
        .detail(
            "Both the trench and the via are patterned, then filled together, so one pass makes both.",
            &[
                "PATTERN+ETCH: trench and via through a hard mask (CHIP_MID_METAL.details.txt)",
                "Each pass is 4-6 tool visits (CHIP_MID_METAL.txt, section 1)",
            ],
        ),
    Beat::new("copper plates both at once", BEAT_MS)
        .note(
            "A barrier and seed line the walls, then copper plates bottom-up, filling the via and the trench in one step.",
            "a translucent copper glow over the lower wire run, with cyan dots flowing out of the via along it",
        )
        .detail(
            "One copper fill and one polish per level keeps the process to two steps.",
            &[
                "Trench and via are filled with copper in one plating step (CHIP_MID_METAL.txt, section 2)",
                "PLATE Cu: bottom-up electroplating (CHIP_MID_METAL.details.txt)",
            ],
        ),
    Beat::new("CMP levels it, a SiCN cap seals it", BEAT_MS)
        .note(
            "Polish removes the excess copper and stops on the dielectric. A SiCN or SiN cap then seals the level so the next one can form.",
            "a gold cap glow over the same wire run, the tag marking CMP and the cap",
        )
        .detail(
            "The cap has a higher k than the dielectric, so thinner caps and metal caps are used to cut capacitance.",
            &[
                "CMP strips the excess, stops on the dielectric (CHIP_MID_METAL.txt, section 1)",
                "SiCN or SiN cap, higher k (CHIP_MID_METAL.txt, section 2)",
            ],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("R: the narrow copper", BEAT_MS)
        .note(
            "Resistance is set by the copper's length, width and height: R = rho L / (W H). A narrow wire resists more.",
            "the lilac-lit lower wire running left, with the tag R = rho L / (W H) under it",
        )
        .detail(
            "Narrow lines raise R, and the copper's resistivity rises below about 60 nm.",
            &[
                "R = rho L / (W H) (CHIP_MID_METAL.details.txt, RC DELAY)",
                "Cu about 2.0 uOhm-cm in wide lines, over 3.0 below about 60 nm (IBM study)",
            ],
        ),
    Beat::new("C: wire to wire through low-k", BEAT_MS)
        .note(
            "Capacitance is mostly between neighbouring lines, through the dielectric between them. It grows with k and with height over spacing.",
            "two lilac-lit wires, one above the other, with the dielectric gap between them and the tag on that gap",
        )
        .detail(
            "Low-k cuts C, but the softer the film, the weaker it is.",
            &[
                "C grows with k and H/S (CHIP_MID_METAL.txt, section 3)",
                "Low-k trades k against stiffness (CHIP_MID_METAL.txt, section 5)",
            ],
        ),
    Beat::new("long run: delay ~ L^2", BEAT_MS)
        .note(
            "Delay is R times C, and both grow with length. A run twice as long is about four times slower to arrive.",
            "the lilac-lit lower wire with the cyan dots crossing slowly from the left, the tag long run",
        )
        .detail(
            "Long block-to-block runs belong on wider, thicker levels.",
            &[
                "Wire delay ~ R x C = rho k eps0 L^2 / (W S) (CHIP_MID_METAL.txt, section 3; textbook)",
                "Long nets move to upper levels (CHIP_MID_METAL.txt, section 3)",
            ],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("low-k: a soft, porous film", BEAT_MS)
        .note(
            "A lower-k dielectric cuts capacitance, but the film gets softer as k drops. Silicon dioxide is stiff; carbon-doped oxide is not.",
            "the lilac dielectric band across the middle tier with its wires; the tag gives k 2.7 CDO at 7-10 GPa",
        )
        .detail(
            "Each step down in k costs stiffness, and porous films crack in CMP and packaging.",
            &[
                "SiO2 k 4.0 at about 72 GPa; carbon-doped oxide k 2.7 at 7-10 GPa (CHIP_MID_METAL.txt, section 5)",
                "Weak ILD cracks in CMP, wire bonding and packaging (CHIP_MID_METAL.details.txt, DEPOSIT ILD)",
            ],
        ),
    Beat::new("air gap: no dielectric between lines", BEAT_MS)
        .note(
            "Removing the dielectric between the tightest lines leaves a gap of air, which cuts line-to-line capacitance.",
            "a pale glowing box in the dielectric between two wires, where no solid film sits; the tag air gap -25% C",
        )
        .detail(
            "Air has k near 1, so a gap is the lowest-k dielectric there is. Voids are weak and trap heat.",
            &[
                "Intel IEDM 2024: up to 25% lower line-to-line capacitance at pitches <=25 nm (CHIP_MID_METAL.details.txt, AIR GAP)",
                "Voids are mechanically weak and trap heat (CHIP_MID_METAL.details.txt, AIR GAP)",
            ],
        ),
    Beat::new("ruthenium: etched lines, no barrier", BEAT_MS)
        .note(
            "Below about 20 nm pitch, etched ruthenium without a barrier replaces damascene copper. Ru needs no liner and can be etched.",
            "two middle wires recoloured as blue-grey ruthenium, the tag Ru: etched, no barrier",
        )
        .detail(
            "Copper's resistance wall at tight pitch is why the subtractive flow is coming.",
            &[
                "RU / SUBTRACTIVE: below about 20-25 nm pitch (CHIP_MID_METAL.txt, section 7)",
                "Intel IEDM 2024: <=25 nm subtractive Ru (CHIP_MID_METAL.details.txt, RU / SUBTRACTIVE)",
            ],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("current pushes copper atoms", BEAT_MS)
        .note(
            "Electrons drag copper atoms along the copper and cap interface, the weakest path in the line.",
            "a train of cyan dots drifting along the middle wire, with the tag electrons push Cu atoms",
        )
        .detail(
            "The drift is the electron wind; the atoms move opposite to the current.",
            &[
                "ELECTROMIGRATION: atoms drift along the Cu/cap interface (CHIP_MID_METAL.txt, section 6)",
                "Voids upstream, hillocks downstream (CHIP_MID_METAL.txt, section 6)",
            ],
        ),
    Beat::new("heat and a void: MTTF falls", BEAT_MS)
        .note(
            "Black's equation: lifetime falls with current density and with temperature. A void opens upstream, where atoms have left.",
            "the middle wire glowing orange, with a dark void on it and the tag void upstream, heat: MTTF falls",
        )
        .detail(
            "Hotter and denser currents fail sooner; the exponent on J is about 2.",
            &[
                "MTTF = A x J^-n x exp(Ea/kT), n often about 2 (CHIP_MID_METAL.txt, section 6)",
                "Cu Ea about 0.7-1.1 eV against Al 0.5-0.7 eV (CHIP_MID_METAL.txt, section 6)",
            ],
        ),
    Beat::new("CoWP or Co cap slows drift", BEAT_MS)
        .note(
            "A metal cap on the copper, and a liner under it, hold the atoms at the interface and slow the drift.",
            "the middle wire under a gold cap glow, the void still dark, the tag CoWP or Co cap slows drift",
        )
        .detail(
            "A better cap raises lifetime, but a metal cap costs selectivity and carries leakage risk.",
            &[
                "Fixes: CoWP, Co or Ru caps, Mn or Co liners, copper reflow (CHIP_MID_METAL.txt, section 6)",
                "Metal caps reduce EM at the cost of selectivity and leakage (CHIP_MID_METAL.details.txt, CAP+REPEAT)",
            ],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("via: lands on target", BEAT_MS)
        .note(
            "A via landed where it was drawn has low resistance and joins one level to the next cleanly.",
            "a lilac-lit via column between the lower and upper middle wires, the tag via: lands on target, low R",
        )
        .detail(
            "A via is a copper plug between levels, and at the tightest levels its resistance can dominate.",
            &[
                "VIA / EPE: a via landed where planned has low resistance (CHIP_MID_METAL.txt, section 7)",
                "Via resistance is the main RC problem at the tightest levels (CHIP_MID_METAL.details.txt, VIA / EPE)",
            ],
        ),
    Beat::new("misaligned: narrow bottom", BEAT_MS)
        .note(
            "A misaligned via narrows at the bottom. Its resistance rises, and a short or electromigration becomes more likely.",
            "a thin orange via beside the lit one, narrower at its foot; the tag misaligned: narrow, R up",
        )
        .detail(
            "The overlay budget is about a quarter of the pitch at 70 nm and below.",
            &[
                "Overlay about a quarter of the pitch at 70 nm and below (CHIP_MID_METAL.txt, section 7)",
                "EPE: litho overlay plus CD error (CHIP_MID_METAL.details.txt, VIA / EPE)",
            ],
        ),
    Beat::new("StarRC, Quantus: R and C per wire", BEAT_MS)
        .note(
            "The stack pulled back. Extraction tools turn every wire into R and C values, so timing signoff sees the real delay.",
            "cyan dots along the lower and middle runs of the stack, with the tag StarRC, Quantus: R and C per wire",
        )
        .detail(
            "Designers see the back end as resistance and capacitance tables for each layer.",
            &[
                "Synopsys StarRC (SNPS) and Cadence Quantus (CDNS) (CHIP_MID_METAL.txt, section 8)",
                "StarRC product page (CHIP_MID_METAL.txt, section 10, source 12)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "one dual-damascene pass",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "RC delay",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "low-k, air gaps and ruthenium",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "electromigration",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "vias, edge placement and RC extraction",
        build: zoom_e,
    },
];

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_d.glb"),
        ZD_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_mid_metal_zoom_e.glb"),
        ZE_BEATS,
    )
}

// ---- sections 1-10 ---------------------------------------------------------------------------

const SEC1_BEATS: &[Beat] = &[
    Beat::new("five passes build M5 to M9", BEAT_MS)
        .note(
            "The middle tier is five metal levels, each made by the same dual-damascene pass, one on top of the other.",
            "the middle tier lit lilac, the tag M5-M9: five passes",
        )
        .detail(
            "Each pass makes one metal level plus the vias below it.",
            &["M5-M9 is five dual-damascene passes, about 4-6 tool visits each (CHIP_MID_METAL.txt, section 1)"],
        ),
    Beat::new("M5: the first pass", BEAT_MS)
        .note(
            "The first level goes down: ILD, pattern and etch, barrier and seed, copper, CMP, then the cap.",
            "the lowest middle level glowing copper, the tag M5: one pass",
        )
        .detail(
            "Every level goes through the same sequence of tool steps.",
            &[
                "DEPOSIT ILD, PATTERN+ETCH, BARRIER+SEED, PLATE Cu, CMP, CAP+REPEAT (CHIP_MID_METAL.txt, section 1)",
                "Each pass makes one metal level plus the vias below it (CHIP_MID_METAL.txt, section 1)",
            ],
        ),
    Beat::new("M6 on top of M5", BEAT_MS)
        .note(
            "The next level is built the same way, its vias landing on the level below.",
            "the second middle level lit copper, the tag M6: the next pass",
        )
        .detail(
            "The cap makes the level below ready to take the next one.",
            &[
                "CAP+REPEAT forms the next level (CHIP_MID_METAL.txt, section 1)",
                "Vias join each level to the one below (CHIP_MID_METAL.details.txt, CAP+REPEAT)",
            ],
        ),
    Beat::new("M7 to M9 complete the tier", BEAT_MS)
        .note(
            "Three more levels finish the tier. Each repeats the same sequence, one fill and one polish per level.",
            "the three upper middle levels lit copper, the tag M7 to M9: three more",
        )
        .detail(
            "M5 to M9 is five passes, each also forming the vias down to the previous level.",
            &[
                "Five passes for M5-M9 (CHIP_MID_METAL.details.txt, CMP)",
                "Dual damascene: one copper fill and one CMP per level (CHIP_MID_METAL.txt, section 2)",
            ],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("trench: the wire that runs across", BEAT_MS)
        .note(
            "The trench is the horizontal part of the level: the wire that routes the signal across the block.",
            "the lower wire lit lilac, the tag trench: the lateral wire",
        )
        .detail(
            "The trench and the via below it are patterned into the same dielectric, then filled at once.",
            &["Trench and via patterned into the same ILD, then filled at once (CHIP_MID_METAL.details.txt, PATTERN+ETCH)"],
        ),
    Beat::new("via: the plug down", BEAT_MS)
        .note(
            "The via is the vertical plug that joins one level to the next.",
            "the via column lit lilac between the levels, the tag via: the plug down",
        )
        .detail(
            "A via is a copper plug between levels; its resistance counts in a short net.",
            &["A via is a Cu plug between levels (CHIP_MID_METAL.details.txt, VIA / EPE)"],
        ),
    Beat::new("one fill: copper runs into both", BEAT_MS)
        .note(
            "Copper plates down the via and out along the trench in one step, so each level has one fill and one polish.",
            "cyan dots flowing from the upper level down the via and out along the lower wire, the tag one fill for both",
        )
        .detail(
            "One plating step fills both, so there is only one copper fill and one CMP per level.",
            &[
                "Trench and via are filled with copper in one plating step (CHIP_MID_METAL.txt, section 2)",
                "PLATE Cu: bottom-up electrofill (CHIP_MID_METAL.details.txt, PLATE Cu)",
            ],
        ),
    Beat::new("barrier stops short of the via foot", BEAT_MS)
        .note(
            "The barrier coats the walls but not the bottom of the via, so the via copper touches the line copper directly.",
            "the via lit at its junction with the wire, the tag barrier stops at via foot",
        )
        .detail(
            "Leaving the barrier off the via bottom keeps the via resistance low.",
            &[
                "The barrier coats the walls but not the via bottom (CHIP_MID_METAL.txt, section 2)",
                "No barrier at the via bottom (CHIP_MID_METAL.details.txt, overview notes)",
            ],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("thin: high R", BEAT_MS)
        .note(
            "The thin levels M1-M4 are the finest wires, with the most resistance per micron.",
            "the bottom tier lit cyan, the tag thin: high R",
        )
        .detail(
            "Thin lines have the highest resistance per micron, the size effect.",
            &["Thin M1-M4 have the highest resistance per micron, the size effect (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("medium: R and C balanced", BEAT_MS)
        .note(
            "The medium levels M5-M9 are wider and taller than the thin ones, which balances resistance against capacitance.",
            "the middle tier lit lilac, the tag medium: R and C balanced",
        )
        .detail(
            "Medium levels are where R and C are traded off against each other.",
            &["Medium M5-M9 balance R and C (CHIP_MID_METAL.txt, section 3)"],
        ),
    Beat::new("thick: lowest R", BEAT_MS)
        .note(
            "The thick top levels carry power, clock and global wires, at the lowest resistance.",
            "the top tier lit gold, the tag thick: lowest R, and the formula in the corner",
        )
        .detail(
            "Wide copper has the lowest resistance; the resistivity rises as lines narrow.",
            &[
                "Thick M10-M14 carry power, clock and global wires (CHIP_MID_METAL.txt, section 3)",
                "Cu about 2.0 uOhm-cm in wide lines, over 3.0 below about 60 nm (IBM study)",
            ],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("Intel 7 and Intel 4 at 44-52 nm", BEAT_MS)
        .note(
            "Published points for the middle levels: Intel 7 M2 and M4 at 44 and 52 nm, Intel 4 at 45 nm with some EUV.",
            "the middle tier lit, the tags Intel 7 M2/M4: 44-52 nm and Intel 4: 45 nm, some EUV",
        )
        .detail(
            "EUV or multipatterning is chosen per level.",
            &[
                "Intel 7 M2 / M4 44 / 52 nm, DUV multipatterning (CHIP_MID_METAL.txt, section 4)",
                "Intel 4 M2 / M4 45 nm, EUV for some metal and vias (CHIP_MID_METAL.txt, section 4)",
            ],
        ),
    Beat::new("TSMC: 23 nm and 30% tighter", BEAT_MS)
        .note(
            "TSMC N5 Mx scaled about 30% tighter than N7 with EUV. N3E reached 23 nm with a single EUV exposure.",
            "the thin tier lit cyan, the tags TSMC N3E: 23 nm, EUV single and TSMC N5 Mx ~30% tighter",
        )
        .detail(
            "Tight pitches now need EUV; the cost of each step is what sets the choice.",
            &[
                "TSMC N5 Mx about 30% tighter than N7, EUV (CHIP_MID_METAL.txt, section 4)",
                "TSMC N3E M0 23 nm, EUV single pattern (CHIP_MID_METAL.txt, section 4)",
            ],
        ),
    Beat::new("no full per-level tables", BEAT_MS)
        .note(
            "Foundries do not publish a pitch for every level. M5-M9 is a class label, and EUV or multipatterning is a per-level choice.",
            "the whole chip with the middle tier lit, the tag no full per-level tables",
        )
        .detail(
            "Only the disclosed examples are given here.",
            &["EUV VS MULTI is a per-level choice; foundries don't publish full per-level pitch tables (CHIP_MID_METAL.txt, section 4)"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("SiO2: stiff, k 4.0", BEAT_MS)
        .note(
            "Plain silicon dioxide has k about 4.0 and is stiff, about 72 GPa.",
            "the middle tier's dielectric band lit lilac, the tag SiO2 k 4.0: 72 GPa",
        )
        .detail(
            "This is the reference point: every lower-k film trades stiffness for k.",
            &["SiO2 (k about 4.0) 72 GPa (CHIP_MID_METAL.txt, section 5)"],
        ),
    Beat::new("k 2.7 CDO: softer", BEAT_MS)
        .note(
            "Carbon-doped oxide at k 2.7 is about ten times softer than silicon dioxide.",
            "the same band, the tag k 2.7 CDO: 7-10 GPa",
        )
        .detail(
            "Modulus falls an order of magnitude as k drops by a third.",
            &[
                "Carbon-doped oxide (k about 2.7) 7-10 GPa (CHIP_MID_METAL.txt, section 5)",
                "Modulus falls an order of magnitude as k drops by a third (CHIP_MID_METAL.txt, section 5)",
            ],
        ),
    Beat::new("58% porous CDO: 3 GPa", BEAT_MS)
        .note(
            "Pores lower k further, but a porous film is much weaker, about 3 GPa. The white pores are the air in it.",
            "white pores scattered through the dielectric band, the tag 58% porous CDO: 3 GPa",
        )
        .detail(
            "Films below k 2 are at least half porous, which is why they crack under CMP and packaging.",
            &[
                "58% porous CDO 3 GPa (CHIP_MID_METAL.txt, section 5)",
                "Films below k 2.0 are at least 50% porous (CHIP_MID_METAL.details.txt, LOW-K / ULK)",
            ],
        ),
    Beat::new("air gap: no dielectric at all", BEAT_MS)
        .note(
            "Removing the dielectric between lines leaves a gap of air, which cuts capacitance by 25% or more.",
            "a pale gap glow between two middle wires where no film sits; the tag air gap: -25% C",
        )
        .detail(
            "The gap is the lowest-k dielectric there is, at the cost of mechanical strength.",
            &[
                "AIR GAP cuts capacitance 25% or more (CHIP_MID_METAL.txt, section 5)",
                "Intel IEDM 2024: up to 25% lower line-to-line capacitance (CHIP_MID_METAL.details.txt, AIR GAP)",
            ],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("electrons push copper atoms", BEAT_MS)
        .note(
            "The electron wind pushes copper atoms along the weakest path, the copper and cap interface.",
            "cyan dots drifting along the middle wire, with the tag electrons push Cu atoms",
        )
        .detail(
            "Atoms leave voids upstream and pile up as hillocks downstream.",
            &["ELECTROMIGRATION: voids upstream, hillocks downstream (CHIP_MID_METAL.txt, section 6)"],
        ),
    Beat::new("heat makes it worse", BEAT_MS)
        .note(
            "Black's equation: lifetime falls with current density and with temperature, so a hot level fails sooner.",
            "the middle wire glowing orange, the tag MTTF = A J^-n exp(Ea/kT)",
        )
        .detail(
            "The exponent on current density is often about 2.",
            &[
                "Black's equation, n often about 2 (CHIP_MID_METAL.txt, section 6)",
                "Cu Ea about 0.7-1.1 eV against Al 0.5-0.7 eV (CHIP_MID_METAL.txt, section 6)",
            ],
        ),
    Beat::new("caps and liners slow it", BEAT_MS)
        .note(
            "Metal caps and liners hold the atoms at the interface, so the drift is slower.",
            "the wire under a gold cap glow, the tag caps and liners slow it",
        )
        .detail(
            "Metal caps cut EM, but cost selectivity and carry leakage risk.",
            &[
                "Fixes: CoWP, Co or Ru caps, Mn or Co liners, copper reflow (CHIP_MID_METAL.txt, section 6)",
                "Metal caps reduce EM at the cost of selectivity and leakage (CHIP_MID_METAL.details.txt, CAP+REPEAT)",
            ],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("via: lands on target", BEAT_MS)
        .note(
            "A via landed where it was drawn has low resistance and a clean join between levels.",
            "two via columns lit lilac between the middle levels, the tag via: lands on target",
        )
        .detail(
            "A landed via is a low-resistance join; a missed one is a problem.",
            &["VIA / EPE: a via landed where planned has low resistance (CHIP_MID_METAL.txt, section 7)"],
        ),
    Beat::new("misaligned: narrow bottom", BEAT_MS)
        .note(
            "A misaligned via narrows at the bottom. Its resistance rises, and a short or electromigration becomes more likely.",
            "an orange via, thinner at its foot, the tag misaligned: narrow bottom",
        )
        .detail(
            "Self-aligned vias set the via edge by the line grating, which cuts placement error.",
            &[
                "Overlay about a quarter of the pitch at 70 nm and below (CHIP_MID_METAL.txt, section 7)",
                "Self-aligned vias cut EPE (CHIP_MID_METAL.details.txt, VIA / EPE)",
            ],
        ),
    Beat::new("StarRC, Quantus: R and C", BEAT_MS)
        .note(
            "Extraction tools turn every wire into R and C values, so timing signoff sees the real delay.",
            "cyan dots along the lower and middle runs, the tag StarRC, Quantus: R and C",
        )
        .detail(
            "Millions of parasitics per net make extraction hard, and the foundry tech file decides adoption.",
            &[
                "Synopsys StarRC (SNPS), Cadence Quantus (CDNS) (CHIP_MID_METAL.txt, section 8)",
                "StarRC product page (CHIP_MID_METAL.txt, section 10, source 12)",
            ],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("tool makers", BEAT_MS)
        .note(
            "Applied Materials supplies the barrier, seed and low-k tools; Lam Research supplies the copper plating.",
            "the middle tier lit lilac, the tags Applied: Endura CuBS, Black Diamond and Lam: SABRE copper plating",
        )
        .detail(
            "The tool makers sell the deposition, etch, CMP and plating steps.",
            &[
                "Applied: Endura CuBS barrier/seed with Ru CVD, Black Diamond low-k (CHIP_MID_METAL.txt, section 8)",
                "Lam: SABRE copper plating (CHIP_MID_METAL.txt, section 8)",
            ],
        ),
    Beat::new("fabs and designers", BEAT_MS)
        .note(
            "TSMC, Intel and Samsung build the chips. Arm, NVIDIA and AMD design to the rules those fabs publish.",
            "the silicon tagged with the fabs, the top tier tagged with the designers",
        )
        .detail(
            "The fabs own the process; the designers see it as timing tables.",
            &[
                "Fabs: TSMC (TSM), Intel (INTC), Samsung (005930.KS) (CHIP_MID_METAL.txt, section 8)",
                "Designers working to the fabs' rules (textbook)",
            ],
        ),
    Beat::new("China: 30% of Applied sales", BEAT_MS)
        .note(
            "China was 30% of Applied's FY2025 revenue: $8,529M of $28,368M.",
            "the middle tier lit, the tags China: 30% of Applied sales and the FY2025 figures",
        )
        .detail(
            "Export controls make this revenue share a risk to watch.",
            &["Applied FY2025 revenue $28,368M, $8,529M from China (CHIP_MID_METAL.txt, section 8; AMAT FY2025 ARS)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("copper's resistance wall", BEAT_MS)
        .note(
            "Below about 20 nm pitch copper's resistance is a wall: narrow copper resists more than ruthenium does.",
            "the thin tier lit cyan, the tag Cu wall below ~20 nm pitch",
        )
        .detail(
            "This is the switch to ruthenium at the tightest levels.",
            &["A copper resistance wall below about 20 nm pitch, the switch to Ru (CHIP_MID_METAL.txt, section 9)"],
        ),
    Beat::new("porous ULK and EM", BEAT_MS)
        .note(
            "Porous low-k films damage easily, and higher current speeds electromigration. One wire glows hot.",
            "the middle tier lit, one wire orange; the tags porous ULK damages easily and EM: more current, faster",
        )
        .detail(
            "Two reliability risks rise together as the film gets softer and the current gets higher.",
            &[
                "Damage to porous ultra-low-k films (CHIP_MID_METAL.txt, section 9)",
                "Electromigration at higher current (CHIP_MID_METAL.txt, section 9)",
            ],
        ),
    Beat::new("tools shift, China at 30%", BEAT_MS)
        .note(
            "Subtractive ruthenium changes which companies sell the tools, and China is 30% of Applied's sales.",
            "the top tier lit gold; the tags tools shift to Ru and China: 30% of Applied",
        )
        .detail(
            "The tool market shifts with the process, so the sellers and their exposure shift too.",
            &["China at 30% of Applied's sales, and the move to subtractive Ru (CHIP_MID_METAL.txt, section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources: copper and resistivity", BEAT_MS)
        .note(
            "The whole chip, pulled back slowly. The first sources cover the copper history and the resistivity study.",
            "the whole chip, slowly pulled back, with no tags",
        )
        .detail(
            "Sources 1, 2 and 6, as listed on the page.",
            &[
                "[1] IBM Cu history: ibm.com/history/copper-interconnects ; en.wikipedia.org/wiki/Copper_interconnects",
                "[2] Barrier scaling: semiengineering.com/how-far-will-copper-interconnects-scale",
                "[6] IBM Cu resistivity study: research.ibm.com/publications/the-effect-of-microstructure-on-resistivity-and-reliability-in-copper-interconnects",
            ],
        ),
    Beat::new("sources: nodes and fabs", BEAT_MS)
        .note(
            "The whole chip, pulled back further. These sources cover the node pitches and the IEDM papers.",
            "the whole chip, pulled back, with no tags",
        )
        .detail(
            "Sources 3 to 5, as listed on the page.",
            &[
                "[3] Intel 4: anandtech.com/show/17448 ; fuse.wikichip.org/news/6720/a-look-at-intel-4-process-technology/3 ; realworldtech.com/intel-4/5",
                "[4] N5: semiwiki.com TSMC IEDM2019 5nm article ; N3E: semianalysis.com/p/iedm2022p1",
                "[5] fuse.wikichip.org/?p=7375 (TSMC N3)",
            ],
        ),
    Beat::new("sources: dielectric, EM and vias", BEAT_MS)
        .note(
            "The whole chip at its widest. These sources cover the low-k modulus, the electromigration and the via placement.",
            "the whole chip at its widest, with no tags",
        )
        .detail(
            "Sources 7 to 10, as listed on the page.",
            &[
                "[7] Intel IEDM 2024: newsroom.intel.com/intel-foundry/intel-foundry-unveils-technology-advancements-iedm-2024",
                "[8] Low-k modulus: patents.justia.com/patent/9766170 ; image-ppubs.uspto.gov 6964919",
                "[9] EM: ifte.de/mitarbeiter/lienig/vlsi05.pdf ; halbleiter.org/en/reliability/electromigration-tddb-nbti/",
                "[10] Via EPE: image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11916010",
            ],
        ),
    Beat::new("sources: tools and EDA", BEAT_MS)
        .note(
            "The whole chip, held at its widest. The last sources cover the tool makers and the extraction tools.",
            "the whole chip, held wide, with no tags",
        )
        .detail(
            "Sources 11 and 12, as listed on the page.",
            &[
                "[11] AMAT FY2025 ARS: sec.gov/Archives/edgar/data/6951/000119312526027318/d54380dars.pdf",
                "[12] StarRC: synopsys.com/implementation-and-signoff/signoff/starrc.html",
            ],
        ),
];

static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_mid_metal_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` heading of CHIP_MID_METAL.txt, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, SEC3_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, SEC5_BEATS),
    section!(6, SEC6_BEATS),
    section!(7, SEC7_BEATS),
    section!(8, SEC8_BEATS),
    section!(9, SEC9_BEATS),
    section!(10, SEC10_BEATS),
];

pub const NODE: Node = Node {
    page: "MID METAL",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};
    use super::*;

    #[test]
    fn overview_zooms_are_keyed_abcde() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        assert_eq!(s.beats().len(), 6);
        explained(s.as_ref(), "MID METAL overview");
    }

    #[test]
    fn zooms_have_three_explained_beats_and_draw() {
        let counts: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3]);
        for z in ZOOMS {
            let s = (z.build)();
            explained(s.as_ref(), &format!("MID METAL zoom {}", z.key));
            draws_every_beat(s.as_ref(), &format!("MID METAL zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [4, 4, 3, 3, 4, 3, 3, 3, 3, 4]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            explained(s.as_ref(), &format!("MID METAL section {}", i + 1));
            draws_every_beat(s.as_ref(), &format!("MID METAL section {}", i + 1));
        }
    }
}
