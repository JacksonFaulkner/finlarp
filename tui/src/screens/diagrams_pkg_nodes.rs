// Packaging tab pages (LOGIC DIE, MICROBUMP, INTERPOSER, SUBSTRATE, ASSEMBLY, BOARD): the beat
// text for their overviews, zoom-ins and sections. The pictures are Blender scenes
// (tools/pbr3d/blender/*_overview.py and pkg_zooms.py), wired in diagrams_nodes/packaging/.
// Each overview is seven beats; each zoom and section is three.

use crate::ui::anim::Beat;

const BEAT_MS: u64 = 8000;
const OVERVIEW_MS: u64 = 8000;

pub(crate) const L_B: &[Beat] = &[
    Beat::new("the logic die: the GPU itself", OVERVIEW_MS)
        .note(
            "This purple slab is the logic die: the piece of silicon that does the computing. The GPU's cores, caches and memory controllers are all etched into it, on TSMC's N4-class processes (4N for Hopper, 4NP for Blackwell). Everything else in the package exists to feed it data and power and to carry its heat away.",
            "One large purple die on its own. It is drawn thick so it reads in 3D; the real die is under 1 mm thick and about 26 x 33 mm across.",
        )
        .detail("Everything else in the package serves it.", &["H100: ~80B transistors on ~814 mm2", "B200: ~104B transistors per die, 2 dies", "TSMC 4N / 4NP (N4-class)"]),
    Beat::new("as big as one exposure allows", OVERVIEW_MS)
        .note(
            "Chips are printed by a scanner that exposes one rectangle of the wafer at a time, at most 26 x 33 mm (858 mm2). One die can't be bigger than that field, so the largest AI dies are designed right up to it: H100 is about 814 mm2, ~95% of the field.",
            "The pink outline is the reticle field, the most one exposure can print. The die almost fills it.",
        )
        .detail("High-NA halves the field in one direction.", &["Reticle field 26 x 33 mm = 858 mm2", "H100 ~814 mm2 (~95% of it)", "High-NA EUV halves it to 26 x 16.5 mm"]),
    Beat::new("big dies yield worse", OVERVIEW_MS)
        .note(
            "Every wafer has a few random defects: a particle, a flaw in the pattern. One defect anywhere on a die usually scraps the whole die, so the bigger the die, the more likely it catches one. At ~800 mm2, estimates put only about half the dies fully good, and each good die carries the cost of the failed ones.",
            "The die glows white under test. The red bumps are defects; any one of them can kill it.",
        )
        .detail("Smaller dies waste less per defect.", &["~45-47% good at 800-814 mm2 (estimates)", "~90% at 100 mm2 with the same defect rate", "Defects ~0.1 per cm2 (rough)"]),
    Beat::new("HBM along its edges", OVERVIEW_MS)
        .note(
            "The layered blocks are HBM: 8-12 memory dies stacked on a base die and wired top to bottom by TSVs (the copper columns in the cut face). Each stack talks to the GPU over ~1024 wires that must stay a few millimetres long, so it has to sit right against the die's edge. Edge length, the 'shoreline', caps how many stacks fit.",
            "Four HBM stacks beside the die's long edges, on the interposer (the grey slab underneath).",
        )
        .detail("More memory needs more shoreline.", &["1024-bit bus per stack", "H100: 6 HBM sites (5 active)", "~10 mm of die edge per stack"]),
    Beat::new("chiplets: two dies, one GPU", OVERVIEW_MS)
        .note(
            "To get past the reticle limit, Blackwell splits the GPU into two near-reticle dies side by side. A silicon bridge under the seam joins them at about 10 TB/s, fast enough that software sees one GPU. Two dies also double the shoreline, so eight HBM stacks fit around them.",
            "The die splits in two. The cyan strip under the seam is the bridge; more stacks line both sides.",
        )
        .detail("Blackwell: two dies on CoWoS-L.", &["Die-to-die ~10 TB/s (NV-HBI)", "8 HBM3E stacks: ~8 TB/s, 192 GB", "Packaged on TSMC CoWoS-L"]),
    Beat::new("data and power at once", OVERVIEW_MS)
        .note(
            "Running, the die pulls data from every HBM stack at once while hundreds of amps climb up from the board below through thousands of tiny bumps. Both have to arrive together: the memory feeds the cores, the current runs them.",
            "Cyan blobs are data arriving from the stacks; the yellow column is power rising from the board.",
        )
        .detail("The die is where it all meets.", &["~8 TB/s of memory traffic (B200)", "~1,000 W at under 1 V = 1,000+ A", "Thousands of bumps share the current"]),
    Beat::new("and heat to remove", OVERVIEW_MS)
        .note(
            "Nearly all that power ends up as heat inside the die. A B200 turns about 1,000 W into heat in an area smaller than a playing card, and it has to leave through the top: a thin thermal layer, the lid, then a cold plate. If it can't get out fast enough, the chip slows itself down.",
            "The dies glow hot and heat rises out through the top.",
        )
        .detail("See BOARD for cooling.", &["~700 W (H100 SXM), ~1,000 W (B200)", "Out through the lid and cold plate", "See BOARD for the cooling"]),
];

pub(crate) const LA_B: &[Beat] = &[
    Beat::new("one field: 26 x 33 mm", BEAT_MS)
        .note(
            "A lithography scanner prints the chip pattern one rectangular field at a time. The field is at most 26 x 33 mm, set by the scanner's optics and the size of the mask (the reticle).",
            "The pink outline is one exposure field.",
        )
        .detail("858 mm2.", &["26 x 33 mm = 858 mm2", "The same limit on today's EUV and DUV scanners"]),
    Beat::new("H100: ~814 mm2", BEAT_MS)
        .note(
            "Big AI dies are designed right up to that edge: H100's ~814 mm2 fills about 95% of the field. Anything bigger would not fit in one exposure. Stitching patterns across fields is used for interposers, not for leading-edge logic.",
            "The die nearly fills the outline.",
        )
        .detail("Secondary sources.", &["H100 ~814 mm2", "~95% of the reticle"]),
    Beat::new("no room left", BEAT_MS)
        .note(
            "Once a die fills the reticle, more compute can't come from a bigger die. It has to come from more dies working together inside one package: chiplets.",
            "The die splits in two.",
        )
        .detail("CHIPLETS.", &["Next: chiplets (zoom c)", "High-NA EUV: the field halves to 26 x 16.5 mm"]),
];

pub(crate) const LB_B: &[Beat] = &[
    Beat::new("a defect on a big die", BEAT_MS)
        .note(
            "Defects land at random across the wafer. On an ~800 mm2 die a single one scraps the whole thing, so roughly half of these dies fail (industry estimates).",
            "One big die with defects on it (the red bumps).",
        )
        .detail("Yield ~45-47% (estimates).", &["~45-47% good at ~800 mm2 (estimates)"]),
    Beat::new("split in two: each half yields better", BEAT_MS)
        .note(
            "Build the same silicon as two half-size dies and a defect only scraps the half it lands on. More of the wafer ends up in working parts, so each good GPU wastes less silicon.",
            "Two dies, one bridge between them.",
        )
        .detail("More good silicon per wafer.", &["A defect scraps half as much", "More good silicon per wafer"]),
    Beat::new("KNOWN GOOD DIE", BEAT_MS)
        .note(
            "Each die is fully tested before packaging, and only the ones that pass ('known-good dies') are used. One bad die would otherwise scrap the whole package, including the expensive HBM bonded next to it.",
            "The die glows while it is tested.",
        )
        .detail("Protects the HBM.", &["KGD: tested before assembly", "A bad die would scrap the HBM too"]),
];

pub(crate) const LC_B: &[Beat] = &[
    Beat::new("two dies side by side", BEAT_MS)
        .note(
            "Blackwell (B200) is two compute dies, each near the reticle limit, side by side on one interposer and run as a single GPU.",
            "Two dies on an interposer.",
        )
        .detail("One GPU to software.", &["2 dies, ~104B transistors each", "One GPU to software"]),
    Beat::new("a bridge under the seam", BEAT_MS)
        .note(
            "A small piece of silicon, a bridge, sits under the joint between the dies. Silicon carries far finer wires than the organic interposer around it, so the bridge takes the thousands of die-to-die connections.",
            "The cyan bridge under the seam.",
        )
        .detail("CoWoS-L.", &["CoWoS-L: local silicon bridges (LSI)", "Fine wiring only where it is needed"]),
    Beat::new("~10 TB/s between them", BEAT_MS)
        .note(
            "The link across the bridge runs at about 10 TB/s, more than the memory bandwidth, so the two halves can share work and memory as if they were one die.",
            "The bridge spans the seam.",
        )
        .detail("Tom's Hardware.", &["Die-to-die ~10 TB/s (NV-HBI)", "Memory ~8 TB/s, for comparison"]),
];

pub(crate) const LD_B: &[Beat] = &[
    Beat::new("four stacks on the edges", BEAT_MS)
        .note(
            "Each HBM stack talks to the GPU over ~1024 wires that must stay very short, so every stack sits right against the die's edge and claims about 10 mm of it.",
            "Four stacks along the die's edges.",
        )
        .detail("SHORELINE.", &["~10 mm of die edge per stack", "1024-bit bus per stack"]),
    Beat::new("eight stacks need more edge", BEAT_MS)
        .note(
            "More memory means more stacks, and more stacks need more edge. One die only has so much, so the die grows (up to the reticle) or the design splits into chiplets, which adds edge.",
            "Eight stacks around two dies.",
        )
        .detail("Blackwell.", &["B200: 8 stacks around 2 dies"]),
    Beat::new("data along every edge", BEAT_MS)
        .note(
            "Each stack sends its data through the interposer straight into the die beside it. With all eight streaming at once, the GPU gets about 8 TB/s of memory bandwidth.",
            "Data flows in from every stack.",
        )
        .detail("~8 TB/s memory bandwidth.", &["~1 TB/s per HBM3E stack", "~8 TB/s in total (B200)"]),
];

pub(crate) const LE_B: &[Beat] = &[
    Beat::new("data in, power up", BEAT_MS)
        .note(
            "The die needs hundreds of amps at under a volt. That current climbs from the board through the substrate, the interposer and thousands of tiny bumps under the die, while data arrives from the HBM at its sides.",
            "Cyan data blobs fly in from the stacks.",
        )
        .detail("Power enters from below.", &["1,000+ A at under 1 V", "Thousands of power bumps"]),
    Beat::new("heat out", BEAT_MS)
        .note(
            "Nearly every watt that goes in comes out as heat, concentrated in the die. It has to leave through the top, into the lid and the cold plate above it.",
            "The die glows.",
        )
        .detail("HEAT.", &["~1,000 W of heat (B200)"]),
    Beat::new("the split dies run hot", BEAT_MS)
        .note(
            "Two dies make twice the heat in one package. Getting it out is now one of the hardest limits on how much power a GPU can use, which is why AI racks are moving to liquid cooling.",
            "Both dies glow hot.",
        )
        .detail("See BOARD.", &["See BOARD for cooling", "Liquid cooling for ~1 kW GPUs"]),
];

pub(crate) const U_B: &[Beat] = &[
    Beat::new("a finished package", OVERVIEW_MS).note("From outside, the package is a die on an interposer on a substrate.", "The package on its board.").detail("Bumps join every level.", &["3 levels of joints"]),
    Beat::new("pulled apart: bumps at every level", OVERVIEW_MS).note("Separated, each level shows its bumps: C4 under the interposer, microbumps under the die.", "The levels lift apart, bumps showing.").detail("Plus BGA balls below.", &["C4 ~150 um", "Microbump ~40 um"]),
    Beat::new("microbumps under the die", OVERVIEW_MS).note("A dense grid of copper pillars with solder caps joins the die to the interposer at ~40 um pitch.", "The die drops onto the dense bump grid.").detail("20-25 um bumps, 15 um spacing.", &["MICROBUMP ~40 um"]),
    Beat::new("C4 bumps under the interposer", OVERVIEW_MS).note("Coarser solder balls at ~150 um join the interposer to the substrate.", "The substrate closes onto the C4 row.").detail("About 4x the microbump pitch.", &["C4 ~150 um"]),
    Beat::new("power climbs through the bumps", OVERVIEW_MS).note("Every amp for the die passes through these joints.", "Yellow power climbs level by level.").detail("Shrinking bumps raise current density.", &["ELECTROMIGRATION"]),
    Beat::new("underfill shares the stress", OVERVIEW_MS).note("Epoxy flows between the levels so stress spreads across the area.", "Dark underfill fills the gaps.").detail(">10x thermal-cycle life for C4.", &["UNDERFILL"]),
    Beat::new("hybrid bonds: no bumps at all", OVERVIEW_MS).note("Below ~10 um pitch, copper bonds directly to copper and the gap disappears.", "The bumps vanish and the die sits flat on the interposer.").detail("TSMC SoIC.", &["HYBRID BOND <=10 um"]),
];

pub(crate) const UA_B: &[Beat] = &[
    Beat::new("C4 BUMP: ~150 um", BEAT_MS)
        .note("Solder balls to the substrate.", "The C4 row.")
        .detail("Coarsest.", &["C4"]),
    Beat::new("MICROBUMP: ~40 um", BEAT_MS)
        .note(
            "Copper pillars under the dies.",
            "The dense microbump grid.",
        )
        .detail("~16x the density of C4.", &["Microbump"]),
    Beat::new("HYBRID BOND: <=10 um", BEAT_MS)
        .note("Direct copper-to-copper.", "Dies flat on the interposer.")
        .detail("No solder.", &["Hybrid"]),
];

pub(crate) const UB_B: &[Beat] = &[
    Beat::new("copper pillars plated", BEAT_MS)
        .note(
            "Pillars plated on the die, solder caps on top.",
            "The die lifted above its bumps.",
        )
        .detail("CU PILLAR.", &["Plating"]),
    Beat::new("placed and reflowed", BEAT_MS)
        .note(
            "Face down on the interposer, heated until the solder joins.",
            "The die settles onto its bumps.",
        )
        .detail("REFLOW.", &["Reflow"]),
    Beat::new("underfilled", BEAT_MS)
        .note("Epoxy wicks under and cures.", "Underfill fills the gap.")
        .detail("UNDERFILL.", &["Underfill"]),
];

pub(crate) const UC_B: &[Beat] = &[
    Beat::new("halve the pitch, 4x the joints", BEAT_MS)
        .note(
            "Density goes with one over pitch squared.",
            "Dense microbumps.",
        )
        .detail("BUMP PITCH.", &["1 / pitch^2"]),
    Beat::new("solder bridges near 10 um", BEAT_MS)
        .note(
            "Below ~10 um, molten solder can bridge neighbours.",
            "Close on the bumps.",
        )
        .detail("Microbumps hit a wall.", &["~10 um wall"]),
    Beat::new("hybrid bonding past the wall", BEAT_MS)
        .note(
            "Copper-to-copper bonds need near-perfect flatness but go to a few um.",
            "Dies bonded flat.",
        )
        .detail("TSMC SoIC.", &["SoIC"]),
];

pub(crate) const UD_B: &[Beat] = &[
    Beat::new("different expansion rates", BEAT_MS)
        .note(
            "Die, interposer and substrate expand differently when hot.",
            "The package stacked on its bumps.",
        )
        .detail(
            "Stress concentrates in the outer joints.",
            &["CTE mismatch"],
        ),
    Beat::new("stress gathers at the joints", BEAT_MS)
        .note("The big organic substrate carries every level.", "The package on its bumps.")
        .detail("Bumps take the strain.", &["WARPAGE"]),
    Beat::new("underfill spreads the load", BEAT_MS)
        .note(
            "Epoxy shares the stress over the whole area: >10x C4 life.",
            "Underfill between levels.",
        )
        .detail("UCLA (Totta).", &["UNDERFILL"]),
];

pub(crate) const UE_B: &[Beat] = &[
    Beat::new("thousands of bumps carry power", BEAT_MS)
        .note(
            "Power for the die enters through thousands of joints.",
            "Power climbs through the bumps.",
        )
        .detail("Each shares the current.", &["Power bumps"]),
    Beat::new("smaller bumps, more current each", BEAT_MS)
        .note("Shrinking raises current density per joint.", "Hot bumps.")
        .detail("ELECTROMIGRATION.", &["Current density"]),
    Beat::new("more bumps share the load", BEAT_MS)
        .note(
            "Finer pitch also means more bumps to share current.",
            "A dense grid carrying power.",
        )
        .detail("A design trade.", &["Trade"]),
];

pub(crate) const I_B: &[Beat] = &[
    Beat::new("the interposer: wiring under the dies", OVERVIEW_MS).note("A slab of fine wiring carries thousands of connections between the GPU and its HBM.", "Copper traces on the interposer, under the logic die and four stacks.").detail("TSMC calls the package CoWoS.", &["CoWoS"]),
    Beat::new("data runs across it", OVERVIEW_MS).note("Each stack's 1024-bit bus crosses the interposer to the GPU.", "Cyan data flows from each stack, through the interposer, into the die.").detail("Silicon wiring is fine enough.", &["1024 bits per HBM3 stack"]),
    Beat::new("power climbs up through TSVs", OVERVIEW_MS).note("TSVs carry power up from below the interposer into the die.", "Seen through the interposer: power climbing the TSVs.").detail("Every amp passes through.", &["TSV"]),
    Beat::new("CoWoS-S: one silicon slab, up to ~3.3x reticle", OVERVIEW_MS).note("A full silicon interposer handles up to about 3.3x reticle size, ~2,700 mm2.", "The full package with a silicon interposer.").detail("TSMC's page.", &["COWOS-S ~3.3x reticle"]),
    Beat::new("CoWoS-L: silicon bridges in an organic interposer", OVERVIEW_MS).note("Beyond that, small silicon bridges sit only under the joints, inside an organic interposer.", "Two dies, eight stacks, cyan bridges under the seams.").detail("Blackwell uses CoWoS-L.", &["COWOS-L", "~10 TB/s die-to-die"]),
    Beat::new("growing past the reticle", OVERVIEW_MS).note("TSMC plans 9.5-reticle interposers with 12 HBM stacks in 2027.", "The organic interposer grows to about 9.5 reticles.").detail("Tom's Hardware.", &["9.5x (2027)", ">14x (2029)"]),
    Beat::new("the whole package on its board", OVERVIEW_MS).note("The finished package sits on its board, on a grid of BGA balls.", "The package, the substrate and the board under it.").detail("Almost every top AI accelerator uses CoWoS, so its capacity limits shipments.", &["CoWoS capacity"]),
];

pub(crate) const IA_B: &[Beat] = &[
    Beat::new("CoWoS-S: one silicon slab", BEAT_MS)
        .note(
            "A full silicon interposer: fine wiring and TSVs in one piece.",
            "A silicon slab under the die and four stacks.",
        )
        .detail("Up to ~3.3x reticle.", &["COWOS-S"]),
    Beat::new("the slab is wider than the die", BEAT_MS)
        .note(
            "It carries the die and four HBM stacks, with room to spare.",
            "The slab reaches past the die on every side.",
        )
        .detail("Up to ~2,700 mm2.", &["2,700 mm2"]),
    Beat::new("CoWoS-L: silicon bridges", BEAT_MS)
        .note(
            "Small bridges sit under the seams, in an organic slab.",
            "Two dies, eight stacks, cyan bridges at the seam.",
        )
        .detail("Blackwell uses CoWoS-L.", &["COWOS-L"]),
];

pub(crate) const IB_B: &[Beat] = &[
    Beat::new("out of the HBM base die", BEAT_MS)
        .note(
            "Data leaves the stack through microbumps.",
            "Data from a stack.",
        )
        .detail("1024 bits.", &["Out"]),
    Beat::new("across the fine wiring", BEAT_MS)
        .note(
            "It crosses millimetres of silicon wiring.",
            "Data across the interposer.",
        )
        .detail("WIRING DENSITY.", &["Across"]),
    Beat::new("up into the GPU", BEAT_MS)
        .note("And rises into the logic die.", "Data into the die.")
        .detail("Thousands in parallel.", &["In"]),
];

pub(crate) const IC_B: &[Beat] = &[
    Beat::new("9.5x reticle by 2027", BEAT_MS)
        .note(
            "TSMC's roadmap: an interposer about 9.5 reticles across.",
            "The organic slab, wide, under two dies.",
        )
        .detail("Roadmap.", &["9.5x"]),
    Beat::new("12 HBM stacks on the 2027 plan", BEAT_MS)
        .note(
            "The 2027 plan puts 12 stacks on it; eight are drawn.",
            "Eight stacks drawn, with room for more.",
        )
        .detail("Tom's Hardware.", &["12 stacks"]),
    Beat::new("CoWoS-L bridges still link the dies", BEAT_MS)
        .note(
            "Silicon bridges under the die seam carry the links.",
            "Cyan bridges at the seam between the dies.",
        )
        .detail("Blackwell.", &["Bridges"]),
];

pub(crate) const ID_B: &[Beat] = &[
    Beat::new("TSV: copper through the silicon", BEAT_MS)
        .note(
            "Copper columns run through the slab, carrying power and signals.",
            "The slab cut open: a row of copper TSVs.",
        )
        .detail("TSV.", &["TSV"]),
    Beat::new("power climbs up", BEAT_MS)
        .note(
            "Every amp comes up through the TSV array.",
            "Yellow power climbing through the columns.",
        )
        .detail("Many TSVs share it.", &["Power"]),
    Beat::new("to the C4 bumps below", BEAT_MS)
        .note(
            "The TSVs land on the C4 bumps to the substrate.",
            "The C4 row under the slab.",
        )
        .detail("~150 um pitch.", &["C4"]),
];

pub(crate) const IE_B: &[Beat] = &[
    Beat::new("interposers are cut from a wafer", BEAT_MS)
        .note(
            "Each interposer is cut from a wafer; a bigger one leaves fewer per wafer.",
            "A wafer of interposer squares, beside the package.",
        )
        .detail("Tom's Hardware.", &["Per wafer"]),
    Beat::new("each one is bonded into a package", BEAT_MS)
        .note(
            "Each square is bonded into a package and set on its board.",
            "The package on its board.",
        )
        .detail("Packaging.", &["Package"]),
    Beat::new("capacity limits AI output", BEAT_MS)
        .note(
            "CoWoS capacity, not wafers, has capped high-end accelerator shipments.",
            "The package on its board.",
        )
        .detail("Reports.", &["Capacity"]),
];

pub(crate) const S_B: &[Beat] = &[
    Beat::new("the substrate under the interposer", OVERVIEW_MS).note("A laminate of copper and insulating film sits under the interposer and carries its bumps.", "The brown substrate under the interposer.").detail("Wider than the interposer on top.", &["Organic substrate"]),
    Beat::new("C4 bumps on top", OVERVIEW_MS).note("The interposer lands on it through C4 bumps at ~150 um.", "Lifted: the C4 row between interposer and substrate.").detail("Patent example.", &["C4 ~150 um"]),
    Beat::new("build-up layers of ABF and copper", OVERVIEW_MS).note("Layer after layer of ABF film and copper wiring, laminated onto a core.", "Cut face: a core, with copper wiring and vias around it.").detail("Ajinomoto ~95% of ABF; 12-20 layers (estimates).", &["ABF FILM", "BUILD-UP LAYERS"]),
    Beat::new("BGA balls below", OVERVIEW_MS).note("Its underside carries BGA balls at ~1 mm that solder to the board.", "Low view: the ball grid under the substrate.").detail("FAN-OUT from 150 um to ~1 mm.", &["BGA"]),
    Beat::new("power fans in from the board", OVERVIEW_MS).note("Power routes from the board up through the layers.", "Power climbs from the board through the substrate.").detail("Power planes.", &["Fan-out"]),
    Beat::new("warpage: the big laminate bends", OVERVIEW_MS).note("A large, thin organic laminate bows as it heats and cools.", "The substrate bends.").detail("Curl drawn far larger than real warpage.", &["WARPAGE", "GLASS CORE"]),
    Beat::new("bigger packages, bigger substrates", OVERVIEW_MS).note("Multi-die layouts roughly double substrate area per package.", "A large two-die package.").detail("Few makers yield 14+ layers: Ibiden, Shinko, Unimicron, AT&S, Nan Ya.", &["SUBSTRATE MAKERS"]),
];

pub(crate) const SA_B: &[Beat] = &[
    Beat::new("a CORE: the stiff start", BEAT_MS)
        .note(
            "Start from a stiff core with plated through-holes.",
            "The core, a thin band in the middle of the cut face.",
        )
        .detail("Fights warpage.", &["CORE"]),
    Beat::new("ABF FILM and copper layers", BEAT_MS)
        .note(
            "Each layer is insulating ABF film, with copper wiring on it.",
            "ABF and copper layers stacked on each side of the core.",
        )
        .detail("Ajinomoto.", &["ABF"]),
    Beat::new("BUILD-UP LAYERS: 12-20", BEAT_MS)
        .note(
            "Drill, plate, laminate, repeat: 12-20 layers.",
            "Twelve copper layers in the cut face.",
        )
        .detail("Estimates.", &["12-20 layers"]),
];

pub(crate) const SB_B: &[Beat] = &[
    Beat::new("150 um bumps on top", BEAT_MS)
        .note("C4 bumps from the interposer.", "The C4 row under the lifted package.")
        .detail("Fine pitch.", &["C4"]),
    Beat::new("wires fan out through the layers", BEAT_MS)
        .note("Wires spread out layer by layer.", "The layers in the cut face.")
        .detail("FAN-OUT.", &["Fan-out"]),
    Beat::new("~1 mm balls below", BEAT_MS)
        .note("BGA balls at board pitch.", "The ball grid under the substrate.")
        .detail("BGA.", &["BGA"]),
];

pub(crate) const SC_B: &[Beat] = &[
    Beat::new("flat when cool", BEAT_MS)
        .note(
            "At room temperature the substrate is flat.",
            "A flat substrate, with its ball grid below.",
        )
        .detail("Mostly.", &["Flat"]),
    Beat::new("bends when hot", BEAT_MS)
        .note(
            "During reflow it bends, stressing every joint.",
            "The substrate bows: ends up, middle down, C4 row with it.",
        )
        .detail("WARPAGE.", &["Warp"]),
    Beat::new("the joints take the strain", BEAT_MS)
        .note(
            "Every C4 joint carries the stress as the laminate bends.",
            "The C4 row on the bent laminate.",
        )
        .detail("Glass cores: not yet in volume.", &["Glass"]),
];

pub(crate) const SD_B: &[Beat] = &[
    Beat::new("Ajinomoto: the film", BEAT_MS)
        .note(
            "~95% of CPU/GPU-grade ABF (analyst estimate).",
            "The film layers in the cut face.",
        )
        .detail("Single supplier.", &["ABF FILM"]),
    Beat::new("SUBSTRATE MAKERS", BEAT_MS)
        .note(
            "Ibiden, Shinko, Unimicron, AT&S, Nan Ya; shares are estimates that disagree.",
            "A large substrate under a two-die package.",
        )
        .detail("Ibiden ~JPY 500B for two fabs.", &["Makers"]),
    Beat::new("14+ layers are hard", BEAT_MS)
        .note(
            "Few makers yield GPU-class 14+ layer substrates at volume (estimate).",
            "Twelve copper layers drawn; 14+ is the hard part.",
        )
        .detail("Capacity risk.", &["Layers"]),
];

pub(crate) const SE_B: &[Beat] = &[
    Beat::new("power fans in from the board", BEAT_MS)
        .note(
            "Power climbs from the board and spreads out through the substrate.",
            "Yellow power fanning in from the board's edge.",
        )
        .detail("Power planes.", &["Power"]),
    Beat::new("wide planes spread it", BEAT_MS)
        .note(
            "Wide copper planes carry hundreds of amps across the laminate.",
            "Yellow power spreading in the cut layers.",
        )
        .detail("Low resistance.", &["Planes"]),
    Beat::new("all through one laminate", BEAT_MS)
        .note(
            "Every connection to the outside world crosses the substrate.",
            "The cut layers, with power planes through them.",
        )
        .detail("FAN-OUT.", &["One path"]),
];

pub(crate) const A_B: &[Beat] = &[
    Beat::new("known-good dies arrive", OVERVIEW_MS).note("Tested logic dies and HBM stacks wait to be assembled.", "Bare dies and HBM stacks on a tray.").detail("Only known-good ones.", &["KNOWN GOOD DIE"]),
    Beat::new("CHIP ON WAFER: onto the interposer wafer", OVERVIEW_MS).note("Dies are bonded face down onto a whole, uncut interposer wafer.", "Several interposers in a row with dies landing.").detail("Bonding happens before the wafer is cut apart.", &["CoW"]),
    Beat::new("HBM stacks join", OVERVIEW_MS).note("The HBM stacks are bonded beside each logic die.", "Stacks appear on every interposer.").detail("HBM gives the logic die its memory bandwidth.", &["HBM"]),
    Beat::new("cut apart, then ON SUBSTRATE", OVERVIEW_MS).note("One interposer is cut free and bonded to a substrate by C4 reflow.", "The rest of the wafer goes; the cut-out interposer is lowered onto a substrate.").detail("CoWoS is chip on wafer on substrate.", &["CoWoS"]),
    Beat::new("UNDERFILL FLOW", OVERVIEW_MS).note("Epoxy wicks into the gap under the die and cures.", "Dark underfill flows in from the front and fills the gap.").detail(">10x joint life.", &["Underfill"]),
    Beat::new("LID goes on", OVERVIEW_MS).note("A steel lid is set over the die and HBM stacks.", "The lid drops onto the package.").detail("A late defect scraps everything, HBM included. YIELD STACKUP: 10 parts at 99% = ~90%.", &["Test"]),
    Beat::new("CAPACITY: the bottleneck", OVERVIEW_MS).note("CoWoS capacity limits how many AI accelerators ship; this row is the output.", "Finished packages in a row.").detail("NVIDIA reportedly took 40-50% in 2024. ASE and Amkor add capacity (OSAT).", &["Capacity"]),
];

pub(crate) const AA_B: &[Beat] = &[
    Beat::new("dies onto an uncut wafer", BEAT_MS)
        .note("Placed face down at wafer scale.", "Interposers in a row.")
        .detail("CHIP ON WAFER.", &["CoW"]),
    Beat::new("HBM beside every die", BEAT_MS)
        .note("Logic and HBM stacks sit on each interposer site.", "Stacks on every site.")
        .detail("Microbumps.", &["Placed"]),
    Beat::new("the wafer is not cut yet", BEAT_MS)
        .note(
            "The sites are still joined on one wafer.",
            "The uncut wafer.",
        )
        .detail("Dice next.", &["Thin"]),
];

pub(crate) const AB_B: &[Beat] = &[
    Beat::new("one interposer, cut out", BEAT_MS)
        .note("The wafer is diced; this interposer keeps its dies.", "One interposer.")
        .detail("Each with its dies.", &["Dice"]),
    Beat::new("C4 REFLOW onto the substrate", BEAT_MS)
        .note(
            "Bonded to an organic substrate by C4 solder balls.",
            "The interposer sits on the substrate.",
        )
        .detail("ON SUBSTRATE.", &["oS"]),
    Beat::new("underfill fills the gap", BEAT_MS)
        .note("Epoxy wicks under the die and cures.", "Dark underfill at the die edge.")
        .detail("UNDERFILL FLOW.", &["Underfill"]),
];

pub(crate) const AC_B: &[Beat] = &[
    Beat::new("one part at 99%", BEAT_MS)
        .note("One part passes with 99% yield.", "The die in the package.")
        .detail("Illustrative.", &["99%"]),
    Beat::new("ten parts multiply", BEAT_MS)
        .note(
            "Ten parts at 99% each: 0.99^10 is about 90%.",
            "The whole package.",
        )
        .detail("YIELD STACKUP.", &["~90%"]),
    Beat::new("why known-good dies matter", BEAT_MS)
        .note(
            "A late failure scraps the whole package.",
            "The package.",
        )
        .detail("KGD.", &["KGD"]),
];

pub(crate) const AD_B: &[Beat] = &[
    Beat::new("almost every AI accelerator uses CoWoS", BEAT_MS)
        .note("So its capacity limits shipments.", "A row of finished packages.")
        .detail("Reports.", &["CAPACITY"]),
    Beat::new("each package is one stack", BEAT_MS)
        .note(
            "Substrate, interposer, die, HBM and lid.",
            "One package in the row.",
        )
        .detail("Per package.", &["Per package"]),
    Beat::new("capacity sets the output", BEAT_MS)
        .note(
            "Each finished package uses CoWoS capacity.",
            "Packages come off the line.",
        )
        .detail("Output.", &["OSAT"]),
];

pub(crate) const AE_B: &[Beat] = &[
    Beat::new("the lid goes on", BEAT_MS)
        .note("A steel lid seals the die and its HBM.", "The lid over the die.")
        .detail("LID.", &["Sort"]),
    Beat::new("one stack, whole", BEAT_MS)
        .note("Substrate, C4, interposer, die and lid form one stack.", "The stack, whole.")
        .detail("Stacked.", &["Mid"]),
    Beat::new("the finished package", BEAT_MS)
        .note("Ready to mount on the board.", "The package on its substrate.")
        .detail("Next: the board.", &["Final"]),
];

pub(crate) const B_B: &[Beat] = &[
    Beat::new("the package on its board", OVERVIEW_MS)
        .note(
            "The finished package solders to a module board through BGA balls.",
            "The package on a green board.",
        )
        .detail("~1 mm ball pitch.", &["BGA BALLS"]),
    Beat::new("BGA balls underneath", OVERVIEW_MS)
        .note(
            "A grid of solder balls joins substrate to board.",
            "Low view: the ball grid.",
        )
        .detail("All power and signals pass here.", &["BGA"]),
    Beat::new("power: hundreds of amps under a volt", OVERVIEW_MS)
        .note(
            "Regulators on the board feed current up through every level into the die.",
            "Regulators feed yellow power up through see-through layers.",
        )
        .detail("I x R drop at each stage.", &["POWER DELIVERY", "VRM"]),
    Beat::new("all of it becomes heat", OVERVIEW_MS)
        .note(
            "The die turns the power into heat that has to leave through the top.",
            "The die glows; heat rises.",
        )
        .detail("Packages heading to thousands of watts.", &["HEAT"]),
    Beat::new("lid and cold plate", OVERVIEW_MS)
        .note(
            "A lid spreads the heat into a copper cold plate.",
            "Lid and finned copper plate on top.",
        )
        .detail("COLD PLATE.", &["Cold plate"]),
    Beat::new("liquid cooling", OVERVIEW_MS)
        .note(
            "At AI densities, coolant runs through the plate itself.",
            "Coolant runs through the see-through plate base.",
        )
        .detail("LIQUID COOLING.", &["Liquid"]),
    Beat::new("modules linked by NVLink", OVERVIEW_MS)
        .note(
            "Modules on their own boards are tied together by GPU links; racks hold many of them.",
            "Three modules, each on its own board, linked.",
        )
        .detail("See Power and Network+Cool tabs.", &["NVLINK", "RACK"]),
];

pub(crate) const BA_B: &[Beat] = &[
    Beat::new("the package", BEAT_MS)
        .note("Ready to mount: die and HBM on top.", "The package.")
        .detail("BGA below.", &["Package"]),
    Beat::new("balls to the board", BEAT_MS)
        .note("Reflowed onto the board.", "The ball grid.")
        .detail("BGA BALLS.", &["BGA"]),
    Beat::new("the board under it", BEAT_MS)
        .note("A green board carries every ball.", "The board under the package.")
        .detail("BOARD.", &["Board"]),
];

pub(crate) const BB_B: &[Beat] = &[
    Beat::new("power starts at the board", BEAT_MS)
        .note(
            "Current rises from the board under the package.",
            "Yellow power at the board.",
        )
        .detail("Under a volt at the die.", &["Power"]),
    Beat::new("up through every level", BEAT_MS)
        .note(
            "From the board, through the BGA balls, up to the interposer.",
            "Power climbs.",
        )
        .detail("I x R each step.", &["Path"]),
    Beat::new("into the die", BEAT_MS)
        .note(
            "Hundreds of amps reach the die from below.",
            "Power into the die.",
        )
        .detail("See TOP METAL.", &["POWER DELIVERY"]),
];

pub(crate) const BC_B: &[Beat] = &[
    Beat::new("the lid and cold plate", BEAT_MS)
        .note("A lid spreads heat into a copper plate.", "Lid and finned plate.")
        .detail("COLD PLATE.", &["Heat"]),
    Beat::new("fins on the copper", BEAT_MS)
        .note("The fins give the plate a large surface.", "Rows of copper fins.")
        .detail("Spreads heat.", &["Cold plate"]),
    Beat::new("LIQUID COOLING", BEAT_MS)
        .note(
            "Coolant runs in one side of the plate and out the other.",
            "Blue tubes: coolant in and out.",
        )
        .detail("Thousands of watts ahead.", &["Liquid"]),
];

pub(crate) const BD_B: &[Beat] = &[
    Beat::new("one module", BEAT_MS)
        .note("One GPU package on its own board.", "One package.")
        .detail("MODULE.", &["Module"]),
    Beat::new("linked GPUs", BEAT_MS)
        .note(
            "Cyan NVLink bridges tie the modules together.",
            "Modules with links between.",
        )
        .detail("NVLINK.", &["Links"]),
    Beat::new("a row of modules", BEAT_MS)
        .note(
            "Several modules side by side, each on its own board.",
            "A row of modules.",
        )
        .detail("See Power and Network+Cool tabs.", &["Rack"]),
];

pub(crate) const BE_B: &[Beat] = &[
    Beat::new("bigger packages, bigger boards", BEAT_MS)
        .note(
            "Larger packages mean larger boards and more warpage at assembly.",
            "A big package on its board.",
        )
        .detail("Size limits the board.", &["Size"]),
    Beat::new("coolant through the plate", BEAT_MS)
        .note(
            "Coolant runs through the plate, not over fins in air.",
            "Tubes into the plate.",
        )
        .detail("Facilities.", &["Cooling"]),
    Beat::new("the whole stack", BEAT_MS)
        .note(
            "Lid, cold plate and BGA balls on one board.",
            "The package on its board.",
        )
        .detail("Power in, heat out.", &["Power"]),
];
