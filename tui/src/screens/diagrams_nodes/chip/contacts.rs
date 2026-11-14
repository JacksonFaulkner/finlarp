// CHIP tab, CONTACTS: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on the contact layer (tools/pbr3d/blender/chip_contacts.py): the
// tungsten plugs from source, drain and gate up to thin metal, the silicide under them, and the
// current squeezing down a narrow plug. Zoom-ins a-e and sections 1-10 are Blender scenes from the
// same script, one per beat group.

use super::super::blender::{page, Cell, Page, BEAT_MS};
use super::super::Node;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("Contacts: the plugs from each transistor up to the first metal", BEAT_MS)
        .note(
            "The whole chip, with the contact layer lit: tungsten plugs stand over each transistor's source, drain and gate, rising to the thin metal.",
            "A cyan glow over the two transistor bases, with the plug columns rising to the thin wire above.",
        )
        .detail(
            "Contacts are the middle of line, between the silicon and the wiring; their resistance sits in series with every transistor.",
            &["W mean free path 19.1 nm"],
        ),
    Beat::new("Three plugs per transistor: source, gate and drain", BEAT_MS)
        .note(
            "In close, each transistor has three plugs, one on the source, one on the gate and one on the drain. Each runs from the silicon up to M1, the first metal, which wires them into the circuit.",
            "Three columns per transistor, each with a grey liner ring around a see-through tungsten core, and M1 across the top.",
        )
        .detail(
            "The plug-to-wire interface adds resistance on top of the plug body, so every plug counts.",
            &["Contact + via0 + M1 RC dominate local delay (textbook)"],
        ),
    Beat::new("Silicide: the metal-silicon bridge under each source and drain plug", BEAT_MS)
        .note(
            "A thin silicide layer, NiSi in modern processes (TiSi2 in older work), sits between each source and drain plug and the doped silicon.",
            "The silver caps on the source and drain blocks, under their plugs, lit in this beat.",
        )
        .detail(
            "Its barrier height to silicon sets how easily current crosses into the plug; NiSi went in around 65 nm because it stays low-resistance at small widths.",
            &["NiSi Schottky barrier 0.65-0.7 eV (patent)", "TiSi2 barrier 0.58 eV (patent)"],
        ),
    Beat::new("Current squeezes down a small plug", BEAT_MS)
        .note(
            "Current from the thin metal runs down the drain plug. The plug is only about 15-20 nm wide, so all of the flow goes through a narrow column into the silicide.",
            "Small cyan dots dropping down the narrow column from M1 to the drain silicide.",
        )
        .detail(
            "The liner takes a few nm of each side, and tungsten's 19.1 nm electron mean free path means the thin core scatters electrons at its surfaces.",
            &["W mean free path 19.1 nm", "liner takes a few nm per side (textbook)"],
        ),
    Beat::new("Silicide lowers the contact resistance", BEAT_MS)
        .note(
            "The silicide lowers the barrier, so current crosses from the silicon into the plug more easily. With the barrier lower, the contact resistance falls.",
            "The silicide lights on the source as dots cross it from the source plug; the tag names the lower barrier.",
        )
        .detail(
            "Contact resistance is roughly rho_c over contact area; a lower barrier cuts rho_c. One patent reports dopant segregation cutting the n-type barrier from 0.7 to 0.34 eV.",
            &["N2+ pre-silicide implant 0.7 -> 0.34 eV (patent summary)", "contact rho_c pFET ~3e-9, nFET ~1e-8 ohm-cm2 (patent background)"],
        ),
    Beat::new("Back out to the whole chip", BEAT_MS)
        .note(
            "Out to the whole chip: a set of contacts in every transistor. Their resistance adds up, and it erodes each node's gains as the plugs shrink.",
            "The contact layer lit again over the two transistors, as in the first beat, with the chip's wiring around it.",
        )
        .detail(
            "Contact area falls with the square of pitch, so the resistance per plug rises fast as the chip shrinks.",
            &["Applied Volta W up to 90% lower contact R (vendor claim)"],
        ),
];

// ---- zoom-ins a-e: three beats each, the scenes chip_contacts.py builds as zoom_a..zoom_e ----

const ZA_BEATS: &[Beat] = &[
    Beat::new("PRE-CLEAN and SILICIDE on the source and drain", BEAT_MS)
        .note(
            "The native oxide is etched off, then a few nm of NiSi forms on the source and drain, under their plugs.",
            "the two silicide caps lit cyan on the source and drain, under the plug columns",
        )
        .detail(
            "The silicide's barrier height to silicon sets how easily current crosses into the plug.",
            &["NiSi Schottky barrier 0.65-0.7 eV (patent)", "PRE-CLEAN, then Ni anneal into NiSi (page text, section 1)"],
        ),
    Beat::new("LINER/BARRIER and W FILL", BEAT_MS)
        .note(
            "A few nm of Ti/TiN liner, by ALD or CVD, lines each hole. Tungsten from WF6 and H2 then fills it, on the source, drain and gate.",
            "the three plugs of the transistor lit, each with its liner ring around the tungsten core",
        )
        .detail(
            "The liner takes width that carries no current, so less of the 15-20 nm hole is conductor.",
            &["Liner and TiN take a few nm per side of a 15 nm hole (page text, section 4)", "W fill from WF6 and H2 (page text, section 1)"],
        ),
    Beat::new("CMP and VIA0 / M1: the first metal lands", BEAT_MS)
        .note(
            "Chemical-mechanical polish stops on the dielectric, leaving flat plugs. The first via and the M1 metal land on them.",
            "the thin metal M1 band lit cyan across the tops of the plugs",
        )
        .detail(
            "M1 wires at a 30-40 nm pitch, and via0 lands on a plug.",
            &["M1 wires at 30-40 nm pitch (page text, section 2)", "CMP stops on the ILD (page text, section 1)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("TRENCH CONTACT (TS): one bar straps source and drain", BEAT_MS)
        .note(
            "A long bar runs across the source and drain of the transistor, so the epi is contacted along its length instead of at single holes.",
            "the tungsten bar lit across the tops of the source and drain silicide, with the plugs rising from it",
        )
        .detail(
            "Trench contacts replaced one hole per plug, which older nodes etched.",
            &["TS: a long bar strapping the source/drain epi (page text, section 3)", "older nodes etched one hole per plug (page text, section 3)"],
        ),
    Beat::new("GATE CONTACT: a plug on the gate metal", BEAT_MS)
        .note(
            "The gate plug stands on the gate metal, which used to sit off the active area.",
            "the gate plug lit cyan, rising from the gate block to M1",
        )
        .detail(
            "Moving the gate contact over the active area is the COAG step in zoom c.",
            &["GATE CONTACT: a plug on the gate metal (page text, section 3)"],
        ),
    Beat::new("SELECTIVE W: bottom-up fill, no seam", BEAT_MS)
        .note(
            "Tungsten grows from the bottom of the hole up, so it fills without a seam and with less barrier metal.",
            "dots rising up the drain plug from the silicide to M1, the plug filling as they go",
        )
        .detail(
            "Vendor claim: Applied's selective W cuts contact resistance by more than 40% against conventional W.",
            &["Applied selective W: over 40% contact-resistance drop vs conventional W (vendor)", "Co, Ru, Mo are the tungsten alternatives (page text, section 5)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("SAC CAP: a cap that forgives misalignment", BEAT_MS)
        .note(
            "A SiN cap sits on the gate, so a source or drain contact can land close to it without shorting.",
            "the pale SiN cap on top of the gate block",
        )
        .detail(
            "The cap is what lets the contact land by the gate without a short.",
            &["SAC CAP: a SiN cap on the gate that tolerates misalignment (page text, section 3)"],
        ),
    Beat::new("COAG: contact over active gate", BEAT_MS)
        .note(
            "The gate contact lands right over the channel instead of beside it, so the gate plug sits over the active area.",
            "the gate block and the channel under it lit, with the gate plug lit above them",
        )
        .detail(
            "Intel moved to COAG at 10 nm, which shrinks the standard cell.",
            &["COAG: contact over active gate, Intel 10 nm (page text, section 3)", "COAG: en.wikichip.org/wiki/COAG (source [7])"],
        ),
    Beat::new("a smaller standard cell", BEAT_MS)
        .note(
            "With the gate contact over the channel, the standard cell can be shorter: Intel reported about 10% less cell height.",
            "the whole chip pulled back, with the contact layer lit under both transistors",
        )
        .detail(
            "Intel's claim, and a secondary one: an area win, not measured here.",
            &["COAG cut standard-cell height by about 10% (Intel claim, secondary; source [7])"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("CONTACT RESISTANCE: rho_c / A", BEAT_MS)
        .note(
            "Current crosses from the silicide into the plug through a contact resistance rho_c over area A. Area falls with pitch squared, so rho_c / A climbs fast.",
            "the silicide under the source plug lit, with its plug above",
        )
        .detail(
            "Contact area falls with the square of pitch, so the resistance per plug rises fast as the chip shrinks.",
            &["Contact R = rho_c / A plus plug body plus liner (page text, section 4)", "pFET rho_c ~3e-9, nFET ~1e-8 ohm-cm2 (older patent background)"],
        ),
    Beat::new("LINER SQUEEZE", BEAT_MS)
        .note(
            "The liner does not shrink with the plug, so in a 15 nm hole much of the width is liner, not conductor.",
            "the drain plug with its liner ring lit and its tungsten core, with dots passing down the core",
        )
        .detail(
            "Plug body resistance rises as the liner takes more of the hole.",
            &["Liner and TiN take a few nm per side of a 15 nm hole (page text, section 4)"],
        ),
    Beat::new("BARRIER TUNING: dopant segregation", BEAT_MS)
        .note(
            "A pre-silicide N2+ implant segregates dopant to the interface and lowers the Schottky barrier from 0.7 to 0.34 eV.",
            "the drain silicide lit, with dots crossing it from the plug",
        )
        .detail(
            "A lower barrier cuts rho_c, so the contact conducts more easily.",
            &["N2+ pre-silicide implant 0.7 -> 0.34 eV (patent summary)", "Silicide/SBH patents: uspto 10546856 (source [4])"],
        ),
];

const ZE_BEATS: &[Beat] = &[
    Beat::new("tungsten: the old standard", BEAT_MS)
        .note(
            "Tungsten fills the plugs. Its bulk resistivity is low, but its 19.1 nm electron mean free path is longer than the plug, so the surfaces scatter the electrons.",
            "the tungsten cores in the three plugs lit",
        )
        .detail(
            "The plug is narrower than tungsten's mean free path, so surface scattering dominates.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])", "W bulk resistivity ~5.6 uOhm-cm (approximate)"],
        ),
    Beat::new("cobalt: Intel 10 nm (2017)", BEAT_MS)
        .note(
            "Intel moved local interconnect to cobalt at 10 nm in 2017.",
            "the M1 wires lit cyan, with the plugs below them",
        )
        .detail(
            "Intel reports 2x via resistance and 5-10x electromigration. These are claims, not like-for-like tests.",
            &["Intel 10 nm cobalt: 2x via resistance, 5-10x electromigration (source [6])"],
        ),
    Beat::new("Co, Ru, Mo: the next fills", BEAT_MS)
        .note(
            "Ruthenium and molybdenum are the other candidates. Their bulk resistivities are close to tungsten's, and they need thinner or no barrier.",
            "the row of wires lit with the plugs and M1 above the transistors",
        )
        .detail(
            "They need new tools and qualification before a fab can use them.",
            &["Bulk: Ru ~7.1, Mo ~5.3 uOhm-cm (approximate)", "New metals need new tools and qualification (page text, section 9)"],
        ),
];

// ---- sections 1-10, in the page's order: 3 beats each except sections 4 and 5 ----

const SEC1_BEATS: &[Beat] = &[
    Beat::new("the contact layer: silicide and plugs under the transistors", BEAT_MS)
        .note(
            "Contacts are the plugs from the silicon up to the first metal, the middle of line. Silicide sits under each source and drain plug.",
            "the contact layer lit over both transistors, with the whole chip around it",
        )
        .detail(
            "Contacts are the middle of line between transistor and wiring, and their resistance is in series with every device.",
            &["PRE-CLEAN, SILICIDE, LINER, W FILL, CMP, VIA0/M1 (page text, section 1)"],
        ),
    Beat::new("W plugs over the source, drain and gate", BEAT_MS)
        .note(
            "Tungsten plugs with liners stand over the source, drain and gate of the NMOS. M1 is the next layer up.",
            "the three NMOS plugs lit, each with its liner ring and tungsten core",
        )
        .detail(
            "The plugs are about 15-20 nm wide here.",
            &["Plugs are about 15-20 nm wide (page text, section 4)"],
        ),
    Beat::new("M1 lands on the plugs", BEAT_MS)
        .note(
            "CMP polishes the plugs flat, and the first via and M1 metal land on them.",
            "the thin metal M1 band lit cyan across the plug tops",
        )
        .detail(
            "M1 wires at a 30-40 nm pitch.",
            &["M1 at 30-40 nm pitch (page text, section 2)", "CMP stops on the ILD (page text, section 1)"],
        ),
];

const SEC2_BEATS: &[Beat] = &[
    Beat::new("M1 and via0: the first wiring", BEAT_MS)
        .note(
            "M1 wires run at a 30-40 nm pitch, and via0 drops from them onto a plug.",
            "the M1 band lit, with its via column down to a plug",
        )
        .detail(
            "This is the first layer of wiring over the transistors.",
            &["M1 wires at 30-40 nm pitch; via0 lands on a plug (page text, section 2)"],
        ),
    Beat::new("plugs and the SiN gate cap", BEAT_MS)
        .note(
            "Tungsten plugs with liners sit in the dielectric. A SiN cap on the gate is self-aligned, so contacts can land beside it.",
            "the SiN cap lit on the gate, and the plugs lit beside it",
        )
        .detail(
            "A self-aligned cap lets the contact land close without shorting.",
            &["SiN cap on the gate, self-aligned (page text, section 2)"],
        ),
    Beat::new("silicide between the plug and the epi", BEAT_MS)
        .note(
            "NiSi or TiSi, a few nm thick, sits between each plug and the doped epi, where dopant is above 1e20 per cm3.",
            "the silicide caps on the source and drain lit under their plugs",
        )
        .detail(
            "Its barrier height to silicon sets the contact resistance.",
            &["Silicide a few nm, dopant above 1e20 /cm3 (page text, section 2)", "NiSi 0.65-0.7 eV; TiSi2 0.58 eV (patents, source [4])"],
        ),
];

const SEC3_BEATS: &[Beat] = &[
    Beat::new("trench and gate contacts", BEAT_MS)
        .note(
            "A trench contact is a long bar strapping the source and drain epi. A gate contact is a plug on the gate metal.",
            "the tungsten bar lit across the source and drain, and the gate plug lit above the gate",
        )
        .detail(
            "Trench contacts use self-aligned etch stops.",
            &["TS: a long bar strapping the source/drain epi; GATE CONTACT: a plug on the gate metal (page text, section 3)"],
        ),
    Beat::new("COAG and the SAC cap", BEAT_MS)
        .note(
            "The SAC cap lets source and drain contacts land near the gate. COAG lets the gate contact land over the channel.",
            "the SiN cap on the gate, and the gate plug and channel lit together",
        )
        .detail(
            "Intel first used COAG at 10 nm.",
            &["COAG and SAC cap (page text, section 3)", "Intel 10 nm COAG (wikichip, source [7])"],
        ),
    Beat::new("selective W and the new metals", BEAT_MS)
        .note(
            "Tungsten grown bottom-up has no seam and needs less barrier. Cobalt, ruthenium and molybdenum are the other fills.",
            "dots rising up the drain plug as it fills, the plug lit",
        )
        .detail(
            "Applied's selective W is a vendor claim of more than 40% lower contact R.",
            &["Applied selective W: over 40% contact-resistance drop (vendor claim, source [5])"],
        ),
];

const SEC4_BEATS: &[Beat] = &[
    Beat::new("the path: contact R sits in series", BEAT_MS)
        .note(
            "Total resistance is the channel, the source and drain epi, the contact and the local wire, all in series. The contact is one of them.",
            "the whole chip, with dots running from M1 down the drain plug to the silicide",
        )
        .detail(
            "Contact resistance adds to every device, and it grows as the plugs shrink.",
            &["Total resistance = channel + S/D epi + contact + local wire (page text, section 4)"],
        ),
    Beat::new("the plug is 15-20 nm wide", BEAT_MS)
        .note(
            "The plug is about 15-20 nm wide, and current has to squeeze down it.",
            "dots passing down the narrow drain plug from M1 toward the silicide",
        )
        .detail(
            "Tungsten's 19.1 nm electron mean free path is longer than the plug, so the surfaces scatter the electrons.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])", "Plugs about 15-20 nm wide (page text, section 4)"],
        ),
    Beat::new("the liner takes a few nm a side", BEAT_MS)
        .note(
            "The liner and TiN take a few nm from each side of the hole, so much of the width is not conductor.",
            "the liner ring lit around the drain plug, the tungsten core inside",
        )
        .detail(
            "That is why the plug body's resistance rises as the holes shrink.",
            &["Liner and TiN take a few nm per side of a 15 nm hole (page text, section 4)"],
        ),
    Beat::new("the barrier: 0.7 to 0.34 eV", BEAT_MS)
        .note(
            "Dopant segregation from an N2+ implant before silicidation lowers the Schottky barrier from 0.7 to 0.34 eV, so current crosses more easily.",
            "the silicide lit on both source and drain, with dots crossing from the plug",
        )
        .detail(
            "A lower barrier cuts rho_c, the contact resistance per area.",
            &["N2+ pre-silicide implant 0.7 -> 0.34 eV (patent summary, source [4])"],
        ),
];

const SEC5_BEATS: &[Beat] = &[
    Beat::new("W mean free path: 19.1 nm", BEAT_MS)
        .note(
            "Tungsten's electron mean free path is 19.1 nm at room temperature, wider than a 15-20 nm plug.",
            "dots down the plug core, with the plug lit",
        )
        .detail(
            "Surface scattering in a narrow plug is what makes this number matter.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])"],
        ),
    Beat::new("Schottky barriers: NiSi and TiSi2", BEAT_MS)
        .note(
            "The silicide-to-silicon barrier is 0.65-0.7 eV for NiSi and 0.58 eV for TiSi2.",
            "the silicide lit on both the source and drain",
        )
        .detail(
            "A lower barrier means a lower contact resistance.",
            &["NiSi 0.65-0.7 eV; TiSi2 0.58 eV (patents, source [4])"],
        ),
    Beat::new("contact rho_c and bulk resistivity", BEAT_MS)
        .note(
            "Contact rho_c is about 3e-9 ohm-cm2 for pFET and 1e-8 for nFET, from older patent background. Bulk: W ~5.6, Co ~6.2, Ru ~7.1, Mo ~5.3 uOhm-cm, approximate.",
            "the NMOS plugs lit",
        )
        .detail(
            "Contact values come from older patent background; the bulk values are approximate.",
            &["contact rho_c pFET ~3e-9, nFET ~1e-8 ohm-cm2 (older patent background)", "bulk resistivity W ~5.6, Co ~6.2, Ru ~7.1, Mo ~5.3 uOhm-cm (approximate)"],
        ),
    Beat::new("vendor and fab claims", BEAT_MS)
        .note(
            "Applied's Volta W claims up to 90% lower contact resistance. Intel's cobalt claims 5-10x electromigration. TSMC N2 reports up to a 20% middle-of-line R+C cut.",
            "the whole chip, with the contact layer lit under both transistors",
        )
        .detail(
            "These are claims, not equal test conditions.",
            &["Applied Volta W up to 90% lower contact R, CD dependent (vendor claim, source [5])", "Intel 10 nm cobalt, 5-10x electromigration (source [6])", "TSMC N2 up to 20% R+C cut (reported, source [9])"],
        ),
];

const SEC6_BEATS: &[Beat] = &[
    Beat::new("Applied: $28.37B in FY2025", BEAT_MS)
        .note(
            "Applied Materials' FY2025 revenue was $28.37B, and it sells the contact-metal tools.",
            "the M1 wires lit over the transistor",
        )
        .detail(
            "Revenue from the company's FY2025 10-K.",
            &["AMAT FY2025 10-K (source [1])"],
        ),
    Beat::new("Semiconductor Systems: $20.80B", BEAT_MS)
        .note(
            "Semiconductor Systems was $20.80B: 67% foundry, logic and other, 26% DRAM, 7% NAND.",
            "the whole chip, with the M1 wires lit",
        )
        .detail(
            "The segment split shows where the contact tools sell.",
            &["AMAT FY2025 10-K segment split (source [1])"],
        ),
    Beat::new("contact metals: Endura and selective W", BEAT_MS)
        .note(
            "Endura PVD, CVD and ALD tools deposit the liners and the tungsten. Selective W and cobalt are on the list too.",
            "the plugs lit, with their liners and cores",
        )
        .detail(
            "These are Applied's own claims for its tools.",
            &["Endura PVD/CVD/ALD, cobalt, selective W (source [1], [5])"],
        ),
];

const SEC7_BEATS: &[Beat] = &[
    Beat::new("tungsten: the old standard", BEAT_MS)
        .note(
            "Tungsten fills the plugs. Its 19.1 nm mean free path is longer than the plug, so the surfaces scatter the electrons.",
            "the tungsten cores in the three plugs lit",
        )
        .detail(
            "Surface scattering in a 15-20 nm plug is what pushes the industry to new fills.",
            &["W mean free path 19.1 nm at 293 K (PRB 2012, DFT; source [3])"],
        ),
    Beat::new("cobalt: Intel 10 nm", BEAT_MS)
        .note(
            "Intel moved local interconnect to cobalt at 10 nm in 2017.",
            "the M1 wires lit, with the plugs below them",
        )
        .detail(
            "Intel's claims for cobalt are 2x via resistance and 5-10x electromigration.",
            &["Intel 10 nm cobalt (source [6])"],
        ),
    Beat::new("Ru, Mo: less barrier", BEAT_MS)
        .note(
            "Molybdenum and ruthenium can run with thinner or no barrier, which saves width.",
            "the row of wires lit with the plugs",
        )
        .detail(
            "Less barrier raises adhesion and diffusion risk.",
            &["Bulk: Mo ~5.3, Ru ~7.1 uOhm-cm (approximate)", "Barrierless fill raises adhesion and diffusion risk (page text, section 9)"],
        ),
];

const SEC8_BEATS: &[Beat] = &[
    Beat::new("Applied Materials and Lam Research", BEAT_MS)
        .note(
            "Applied makes the Endura PVD, CVD and ALD tools. Lam makes ALTUS CVD and ALD tungsten and molybdenum.",
            "the M1 wires lit over the transistor",
        )
        .detail(
            "Tool suppliers for the contact step.",
            &["AMAT Endura; Lam ALTUS (page text, section 8)", "Lam FY2025 $18.44B (source [2])"],
        ),
    Beat::new("TSMC and Intel design the contact scheme", BEAT_MS)
        .note(
            "TSMC and Intel design the contact schemes. Intel was first with cobalt and COAG at 10 nm.",
            "the contact layer lit under both transistors",
        )
        .detail(
            "Foundry design choices set what the tools have to deposit.",
            &["TSMC (TSM) and Intel (INTC) (page text, section 8)"],
        ),
    Beat::new("memory makers, TEL and EDA", BEAT_MS)
        .note(
            "Samsung, SK hynix and Micron buy the tools. Tokyo Electron sells CVD and ALD. Synopsys and Cadence extract contact RC.",
            "the whole chip pulled back, with the plug and wire labels",
        )
        .detail(
            "Buyers, tool sellers and the software that extracts the resistance.",
            &["Samsung, SK hynix, Micron; TEL 8035.T; Synopsys, Cadence (page text, section 8)"],
        ),
];

const SEC9_BEATS: &[Beat] = &[
    Beat::new("new metals need new tools", BEAT_MS)
        .note(
            "Molybdenum and ruthenium need new tools and qualification before a fab can run them.",
            "the plugs lit with M1 above",
        )
        .detail(
            "Adoption risk.",
            &["New metals (Mo, Ru) need new tools and qualification (page text, section 9)"],
        ),
    Beat::new("barrierless fill: adhesion and diffusion risk", BEAT_MS)
        .note(
            "Dropping the barrier saves width but raises adhesion and diffusion risk.",
            "the drain plug lit, with its liner",
        )
        .detail(
            "A reliability risk.",
            &["Barrierless fill raises adhesion and diffusion risk (page text, section 9)"],
        ),
    Beat::new("contact RC erodes the node gains", BEAT_MS)
        .note(
            "Contact RC erodes node-to-node performance gains, so the middle of line matters more each node.",
            "the whole chip with the contact layer lit under both transistors",
        )
        .detail(
            "Contacts limit every device on the chip.",
            &["Contact RC erodes node-to-node gains (page text, section 9)"],
        ),
];

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1-3: the 10-Ks and the mean free path", BEAT_MS)
        .note(
            "The Applied and Lam 10-K filings, and the paper that gives tungsten's mean free path.",
            "the whole chip, pulling back slowly",
        )
        .detail(
            "Each number on this page traces to one of these.",
            &[
                "[1] AMAT FY2025 10-K: sec.gov/Archives/edgar/data/6951/000162828025056742/amat-20251026.htm",
                "[2] Lam FY2025 10-K: sec.gov/Archives/edgar/data/707549/000070754925000075/lrcx-20250629.htm",
                "[3] W mean free path: doi.org/10.1103/PHYSREVB.86.045432",
            ],
        ),
    Beat::new("sources 4-6: patents, Applied Volta W, Intel cobalt", BEAT_MS)
        .note(
            "The silicide patent, the Applied Volta W page, and Intel's cobalt interconnect article.",
            "the whole chip, pulling back slowly",
        )
        .detail(
            "Patent figures and vendor claims are marked as such on the page.",
            &[
                "[4] Silicide/SBH patents: image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10546856",
                "[5] Applied Volta W: appliedmaterials.com/jp/ja/semiconductor/products/processes/cvd/endura-volta-w-cvd.html",
                "[6] Intel 10nm Co: fuse.wikichip.org/news/525/iedm-2017-isscc-2018-intels-10nm-switching-to-cobalt-interconnects/",
            ],
        ),
    Beat::new("sources 7-9: COAG, Applied blog, TSMC N2", BEAT_MS)
        .note(
            "The COAG pages, Applied's contact-scaling blog, and TSMC's N2 paper summary.",
            "the whole chip, pulling back slowly",
        )
        .detail(
            "Intel's COAG figure is a secondary source.",
            &[
                "[7] COAG: en.wikichip.org/wiki/COAG ; community.cadence.com/cadence_blogs_8/b/breakfast-bytes/posts/intel-10nm",
                "[8] Applied blog: appliedmaterials.com/us/en/newsroom/blogs/powering-the-next-era-of-contact-scaling-with-ald-molybdenum.html",
                "[9] TSMC N2 IEDM 2024: semiconductor-digest.com/?p=30341",
            ],
        ),
];

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_a.glb"),
        ZA_BEATS,
    )
}
fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_b.glb"),
        ZB_BEATS,
    )
}
fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_c.glb"),
        ZC_BEATS,
    )
}
fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_d.glb"),
        ZD_BEATS,
    )
}
fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_contacts_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the contact module: silicide to M1",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "contact types: trench, gate, selective W",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "SAC cap and COAG",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "contact resistance",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "new metals: cobalt, ruthenium, molybdenum",
        build: zoom_e,
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_contacts_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
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
    page: "CONTACTS",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_keys_and_beat_counts_match_the_blender_scenes() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        let counts: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 3, 3]);
        for z in ZOOMS {
            let s = (z.build)();
            super::super::super::blender::explained(s.as_ref(), &format!("zoom {}", z.key));
            super::super::super::blender::draws_every_beat(s.as_ref(), &format!("zoom {}", z.key));
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 3, 3, 4, 4, 3, 3, 3, 3, 3]);
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
