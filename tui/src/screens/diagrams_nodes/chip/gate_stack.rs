// CHIP tab, GATE STACK: the node's pictures in the picture-and-panel template, from the Blender
// scenes in tools/pbr3d/blender/chip_gate_stack.py. The overview is the whole-chip scene with the
// camera gliding into the NMOS, drawn as the detailed replacement-gate rig of
// chip_gate_stack_detail.py. Zoom-ins a-e (the layers, the gate-last flow, EOT, the work-function
// metals, the nanosheet gap) and sections 1-10 are close-up rigs of their own; section 10 lists
// the sources.

use super::super::Node;
use super::super::blender::{BEAT_MS, Cell, Page, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("NMOS gate: a stack of thin films", BEAT_MS)
        .note(
            "This is the whole chip in cross-section: transistors in the silicon at the bottom, copper wiring above, solder bumps on top. The highlighted NMOS transistor's gate, the switch that turns it on and off, is not one block but a stack of films a few atoms thick, each grown by atomic layer deposition (ALD).",
            "The whole chip, with the NMOS at lower left boxed in cyan. Tan silicon at the bottom, brown copper layers above, silver bumps on top.",
        )
        .detail(
            "Built with gate-last high-k metal gate (HKMG), first put into production by Intel at 45 nm.",
            &["Intel 45 nm HKMG, 2007 (Penryn)", "Films a few atoms thick"],
        ),
    Beat::new("In on the gate: four films", BEAT_MS)
        .note(
            "Close up, the gate sits in a trench between nitride spacers. On the silicon floor is a ~0.5 nm SiOx interlayer (IL), then ~1.8 nm of hafnium oxide (HfO2), then the TiAlC(N) work-function metal that sets the threshold, and a tungsten fill that carries the signal. The films are drawn far thicker than life.",
            "Nested U-shapes in the trench: a thin grey IL on the floor, the yellow HfO2, gold and blue metal bands, and the big grey tungsten block in the middle. Green spacers either side, pale oxide beyond, blue source and drain below.",
        )
        .detail(
            "Every gate on the chip is built from the same films.",
            &["IL ~0.5 nm, HfO2 ~1.8 nm", "TiAlC(N) for NMOS, TiN for PMOS", "W fill sets gate resistance"],
        ),
    Beat::new("Gate up: the field runs down", BEAT_MS)
        .note(
            "The gate goes positive. Its electric field reaches down through the HfO2 and the interlayer into the silicon. No current crosses the insulator: the field alone does the work, like the plates of a capacitor.",
            "The gate glows amber and gold arrows run down from the fill through the films into the silicon. The grey pillars above are the tungsten contacts that bring the signal in.",
        )
        .detail(
            "The thinner the insulator looks electrically, the stronger the gate's grip.",
            &["Gate and channel form a capacitor", "No current through the HfO2"],
        ),
    Beat::new("The field inverts the channel", BEAT_MS)
        .note(
            "The field pulls electrons up out of the p-type silicon to the surface under the gate. They pile up into a thin inversion layer that links source to drain, and the transistor is on.",
            "Cyan electrons ride thin tracks up from deep in the silicon, then a bright cyan band lights at the surface under the gate.",
        )
        .detail(
            "The work-function metal sets how much gate voltage this takes (the threshold voltage, Vt).",
            &["Inversion layer a few nm deep", "Vt set by the work-function metal"],
        ),
    Beat::new("Thick in fact, thin in effect", BEAT_MS)
        .note(
            "HfO2's dielectric constant is ~20-25, against 3.9 for SiO2. So the 2.3 nm of IL plus HfO2 grips the channel like ~0.85 nm of SiO2: its equivalent oxide thickness (EOT). Being physically thicker, it leaks far less by tunnelling.",
            "Close on the trench floor: a tall cyan bar beside it marks the physical thickness, a short pink bar the EOT.",
        )
        .detail(
            "EOT = t_IL + t_HfO2 x 3.9/k.",
            &["HfO2 k ~20-25 vs SiO2 3.9", "~2.3 nm physical, ~0.85 nm EOT", "Intel 45 nm: ~1.0 nm EOT"],
        ),
    Beat::new("Field off: back to the whole chip", BEAT_MS)
        .note(
            "The gate returns to zero, the field drops and the channel empties. This one gate is repeated billions of times across the die, every one built from the same few films.",
            "Back out to the whole chip, the NMOS boxed in cyan again.",
        )
        .detail(
            "Gate-last HKMG is the industry standard flow.",
            &["Gate-last: Intel 45 nm, TSMC 28 nm"],
        ),
];

// ---- zoom a: the layers, from interlayer to fill -----------------------------------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("IL and HfO2: the first two films", BEAT_MS)
        .note(
            "The gate is cut back in steps here so every film shows. On the silicon floor sits the interlayer (IL), a chemical SiOx about 0.5 nm thick that gives the high-k a clean surface. On it, ~1.8 nm of HfO2 is the real gate insulator.",
            "Looking into the trench floor: the pale grey IL band at the front, the yellow HfO2 step just behind it, tan silicon below.",
        )
        .detail(
            "HfO2's k is ~20-25, about six times SiO2's.",
            &["IL ~0.5 nm", "HfO2 ~1.8 nm, k ~20-25"],
        ),
    Beat::new("TiAlC(N): the work-function metal", BEAT_MS)
        .note(
            "A thin TiN cap protects the HfO2. On it sits the work-function metal, an Al-rich TiAlC(N) for NMOS. Its work function, the energy to pull an electron out of it, sets where the threshold voltage lands.",
            "Up the left wall: the gold TiN cap and, inside it, the blue TiAlC(N) U.",
        )
        .detail(
            "PMOS uses TiN instead (zoom d).",
            &["NMOS WFM: TiAlC(N), Al-rich", "TiN cap protects the high-k"],
        ),
    Beat::new("W fill: the gate metal", BEAT_MS)
        .note(
            "A TiN barrier keeps tungsten from diffusing into the metals below. Tungsten then fills the rest of the trench. It has the lowest resistance of the stack, so it carries the gate signal along the gate line.",
            "The thin gold barrier U, and the large grey tungsten block filling the middle.",
        )
        .detail(
            "Narrower gates leave less room for the fill (section 9).",
            &["TiN barrier blocks W", "W fill: low resistance"],
        ),
    Beat::new("The whole gate: four films", BEAT_MS)
        .note(
            "Pulled back, the films read as nested U-shapes lining the trench floor and walls, with the fill in the middle, between nitride spacers. The channel is the silicon just under the floor.",
            "The whole transistor in its stepped cut-away: yellow, gold and blue U-shapes round grey fill, green spacers, pale oxide, blue source and drain.",
        )
        .detail(
            "IL, high-k, work-function metal, fill.",
            &["Gate-last HKMG"],
        ),
];

// ---- zoom b: gate-last, dummy poly to stack ----------------------------------------------------

const ZB_BEATS: &[Beat] = &[
    Beat::new("dummy poly: a placeholder gate", BEAT_MS)
        .note(
            "Gate-last starts with a fake gate: a polysilicon block on a thin SiO2 film, with nitride spacers on its sides. It marks where the real gate will go and takes the heat of the steps that follow.",
            "A brown polysilicon block between two green spacers on tan silicon, a thin pale SiO2 line under it.",
        )
        .detail(
            "High-k and metal are not there yet.",
            &["DUMMY POLY on thin SiO2"],
        ),
    Beat::new("S/D anneal, then the ILD fill", BEAT_MS)
        .note(
            "The source and drain are grown and doped beside the dummy gate and annealed at about 1000 C, hot enough to shift a high-k gate's threshold. Then oxide (ILD0) is filled over everything and polished down to the top of the poly.",
            "Blue source and drain blocks appear and glow orange in the anneal; then pale see-through oxide fills in either side, level with the poly.",
        )
        .detail(
            "This is the hottest step in the front end.",
            &["Anneal ~1000 C", "ILD0 oxide, CMP to the poly top"],
        ),
    Beat::new("poly pull leaves a trench", BEAT_MS)
        .note(
            "The poly is etched out and the etch products are pumped away, leaving a trench lined by the spacers with the channel silicon at its floor. That trench is the mould for the real gate.",
            "The brown poly flashes cyan and vanishes while pale beads ride up out of it; an empty trench is left between the green spacers.",
        )
        .detail(
            "The trench width is the gate length.",
            &["POLY PULL: etch out the dummy"],
        ),
    Beat::new("the stack goes into the trench", BEAT_MS)
        .note(
            "Now the IL, HfO2, TiN, work-function metal and TiN barrier are grown into the trench one after another, and tungsten fills the middle, polished flat. None of them ever saw the anneal.",
            "Nested U-shapes appear in turn: grey IL, yellow HfO2, gold and blue metals, then the grey fill level with the top.",
        )
        .detail(
            "Intel used this at 45 nm (2007), TSMC at 28 nm.",
            &["RMG: replacement metal gate", "Intel 45 nm, TSMC 28 nm"],
        ),
];

// ---- zoom c: EOT ------------------------------------------------------------------------------

const ZC_BEATS: &[Beat] = &[
    Beat::new("a thin SiO2 film leaks", BEAT_MS)
        .note(
            "A gate insulator of SiO2 about 1.2 nm thick, only ~5 atomic layers, was the limit by the 90 nm node. At that thickness electrons tunnel straight through it, a quantum effect, so the gate leaks all the time.",
            "Brown metal gate, a thin pale SiO2 band, tan silicon. Cyan electrons ride straight tracks up through the SiO2 into the gate.",
        )
        .detail(
            "Tunnel current rises roughly tenfold for every ~0.2 nm thinner (rule of thumb).",
            &["SiO2 ~1.2 nm at 90 nm", "~5 atomic layers"],
        ),
    Beat::new("HfO2: thick, with the same EOT", BEAT_MS)
        .note(
            "Swap in 0.5 nm of IL plus 1.8 nm of HfO2. It is about twice as thick, yet because HfO2's k is ~20-25 it couples the gate to the channel like ~0.85 nm of SiO2: its equivalent oxide thickness (EOT).",
            "The two stacks side by side, a cyan ruler (physical thickness) and a pink ruler (EOT) beside each. On the SiO2 they match; on the HfO2 stack the pink one is far shorter.",
        )
        .detail(
            "Thick in fact, thin in effect.",
            &["2.3 nm physical", "~0.85 nm EOT (example)"],
        ),
    Beat::new("Intel 45 nm: over 10x less leakage", BEAT_MS)
        .note(
            "Intel's 45 nm process in 2007 was the first to ship this. It claimed over 10x lower gate leakage and about 20% more drive current, at an EOT of about 1.0 nm.",
            "Left, three tracks of electrons still crossing the SiO2; right, a single electron crossing the HfO2 stack.",
        )
        .detail(
            "The gains are Intel's own claims.",
            &[">10x lower gate leakage (Intel)", "~20% more drive (Intel)", "EOT ~1.0 nm"],
        ),
    Beat::new("EOT: the thickness that counts", BEAT_MS)
        .note(
            "EOT = t_IL + t_HfO2 x 3.9/k. The IL has a low k, so it counts almost in full: in the example 0.5 nm of IL is more than half the EOT, while 1.8 nm of HfO2 adds only ~0.35 nm. Scaling further means thinning the IL.",
            "Close on the HfO2 stack: the IL band glows cyan, the HfO2 band glows amber, each tagged with its term of the formula.",
        )
        .detail(
            "3.9 is SiO2's dielectric constant.",
            &["EOT = t_IL + t_hk x 3.9/k", "IL ~0.5 of ~0.85 nm"],
        ),
];

// ---- zoom d: work-function metals and dipoles ----------------------------------------------------

const ZD_BEATS: &[Beat] = &[
    Beat::new("TiAlC(N): the NMOS metal", BEAT_MS)
        .note(
            "An NMOS needs a gate metal whose work function sits near silicon's conduction band, so it turns on at a low positive voltage. The industry answer is an Al-rich TiAlC(N) layer inside the TiN cap.",
            "The NMOS gate trench: the blue TiAlC(N) U inside gold TiN, yellow HfO2 outside it, blue n+ source to the left.",
        )
        .detail(
            "Al lowers the effective work function.",
            &["NMOS WFM: Al-rich TiAlC(N)"],
        ),
    Beat::new("TiN: the PMOS metal", BEAT_MS)
        .note(
            "A PMOS needs the opposite: a work function near the valence band. Its gate uses a thicker TiN stack instead of the aluminium-rich metal, so the two transistors get different metals in the same kind of trench.",
            "The PMOS gate trench: one thick gold TiN U inside the yellow HfO2, pink p+ source to the left.",
        )
        .detail(
            "N and P metals are patterned separately.",
            &["PMOS WFM: TiN"],
        ),
    Beat::new("La dipole: a cap shifts the threshold", BEAT_MS)
        .note(
            "A very thin lanthanum oxide cap, driven down to the HfO2/IL interface, forms an electric dipole that lowers the nFET threshold further. It adds almost no thickness, which matters in tight gaps.",
            "Close on the NMOS wall: a thin pink line between the yellow HfO2 and the gold TiN.",
        )
        .detail(
            "Recipes vary by foundry (general literature).",
            &["La dipole lowers nFET Vt"],
        ),
    Beat::new("two gates, two thresholds", BEAT_MS)
        .note(
            "Side by side, the NMOS and PMOS have the same high-k but different metals and caps, each tuned to its own threshold. Varying metal thickness and dipoles gives a chip several threshold flavours, from fast and leaky to slow and frugal.",
            "Both transistors in one view: NMOS left with blue metal and n+ source/drain, PMOS right with gold TiN and p+ source/drain.",
        )
        .detail(
            "Each extra flavour adds masks and steps.",
            &["One high-k, two metal stacks", "Several Vt flavours per chip"],
        ),
];

// ---- zoom e: the stack in a nanosheet gap ---------------------------------------------------------

const ZE_BEATS: &[Beat] = &[
    Beat::new("sheets, gate on four sides", BEAT_MS)
        .note(
            "In a gate-all-around transistor the channel is a stack of thin silicon sheets, and the gate wraps all four sides of each one. This view cuts across the sheets: each is ringed by the gate films and set in tungsten fill.",
            "Three tan silicon sheets, each in a grey IL, yellow HfO2 and blue metal ring, in grey tungsten on a tan base.",
        )
        .detail(
            "Four-sided control is what fins and sheets add over planar.",
            &["GAA: gate on all four sides", "Sheets ~5 nm thick"],
        ),
    Beat::new("IL, HfO2 and metal fit the gap", BEAT_MS)
        .note(
            "Between two sheets there are only a few nanometres to spare, and both sheets' IL, HfO2 and work-function metal must fit, with tungsten in what is left. Every film is grown by ALD to reach into that gap evenly.",
            "Close on one sheet: the thin grey IL ring, the yellow HfO2 ring and the blue metal ring, each tagged.",
        )
        .detail(
            "Gaps of a few nm to ~10 nm.",
            &["IL ~0.5 nm, HfO2 ~1.8 nm", "ALD reaches into the gaps"],
        ),
    Beat::new("tight gaps: Vt varies", BEAT_MS)
        .note(
            "Because the gaps are so tight, a small difference in metal thickness from one sheet to the next shifts that sheet's threshold. Sheets that should match end up different, costing speed and margin.",
            "The same stack, but the middle sheet's blue metal ring is visibly thinner than the others.",
        )
        .detail(
            "Threshold variability is the main GAA gate risk.",
            &["Vt variation in tiny gaps"],
        ),
    Beat::new("the channel carries current", BEAT_MS)
        .note(
            "Cut the other way, along the channel, each sheet runs from the n+ source to the n+ drain, with the gate in the gaps between sheets and nitride inner spacers at its ends. With the gate on, electrons flow along every sheet at once.",
            "A side cut: blue source and drain blocks at the ends, tan sheets running between them, blue-and-yellow gate segments between the sheets. Cyan electrons ride a track along each sheet.",
        )
        .detail(
            "More sheets, more drive from the same footprint.",
            &["Stacked sheets under one gate", "Inner spacers isolate gate from S/D"],
        ),
];

// ---- sections ------------------------------------------------------------------------------------
// Each section is its own close-up rig (tools/pbr3d/blender/chip_gate_stack_detail.py): one
// replacement-metal-gate transistor, two dielectric stacks side by side, or a nanosheet stack.

// 1 what happens: the empty trench, ALD grows the dielectric, then the metals and the fill.
const S1_BEATS: &[Beat] = &[
    Beat::new("the gate trench, waiting for its films", BEAT_MS)
        .note(
            "This is one transistor in a gate-last flow, just after the placeholder gate was etched out. What is left is a trench between two nitride spacers, with the bare silicon channel at its floor. Every film of the real gate is grown into this trench, so its width is the gate length.",
            "The tan block is the silicon. The blue blocks either side are the raised n+ source and drain. The green walls are the nitride spacers and the pale see-through blocks are the ILD0 oxide. The gap between the green walls is the empty trench.",
        )
        .detail(
            "Gate-last high-k metal gate (HKMG) has been the mainstream since Intel's 45 nm node.",
            &["Intel 45 nm HKMG, 2007 (Penryn)", "Films drawn far thicker than life"],
        ),
    Beat::new("ALD grows the IL, then the HfO2", BEAT_MS)
        .note(
            "Atomic layer deposition (ALD) grows a film one atomic layer per cycle, from alternating gas pulses, so it coats the floor and walls evenly. First a chemical SiOx interlayer (IL) forms on the silicon floor only. Then hafnium oxide (HfO2) lines the floor and both walls.",
            "Pale dots raining into the trench are the precursor pulses. The thin grey band on the floor is the IL; the yellow U is the HfO2 on the floor and up the walls.",
        )
        .detail(
            "The film thickness is set by counting cycles.",
            &["IL ~0.5 nm", "HfO2 ~1.5-2 nm", "~0.1 nm per ALD cycle"],
        ),
    Beat::new("metals, fill, then polish flat", BEAT_MS)
        .note(
            "A TiN cap, the work-function metal and a TiN barrier go in next, each another U inside the last. Tungsten then overfills the trench, and chemical-mechanical polishing (CMP) grinds it back to the top of the oxide, leaving metal only in the gate.",
            "Gold TiN, blue TiAlC and gold TiN U-shapes nest inside the yellow HfO2. The grey tungsten slab spills over the top, the pale CMP layer sweeps it off, and the grey fill is left level with the oxide.",
        )
        .detail(
            "The work-function metal sets the threshold voltage (Vt); the fill sets the gate resistance.",
            &["W (or Co) fill, then CMP", "Work-function metal sets Vt"],
        ),
];

// 2 the replacement-metal-gate flow.
const S2_BEATS: &[Beat] = &[
    Beat::new("DUMMY POLY: a placeholder gate", BEAT_MS)
        .note(
            "Gate-last starts with a fake gate: a block of polysilicon on a thin SiO2 film, patterned where the real gate will go. Nitride spacers are built on its sides. It only marks the spot and takes the heat that follows.",
            "The brown block is the dummy polysilicon gate, with green nitride spacers either side and a thin pale SiO2 line under it, on the tan silicon.",
        )
        .detail(
            "The real high-k and metal never exist during the hot steps.",
            &["DUMMY POLY on thin SiO2", "Spacers set the gate edge"],
        ),
    Beat::new("SPACER + S/D: implant, epi, anneal", BEAT_MS)
        .note(
            "The source and drain are grown and doped on both sides of the dummy gate, then annealed at about 1000 C to activate the dopants. High-k films and metals would shift their threshold at that temperature, which is why they are not there yet.",
            "Blue n+ source and drain blocks appear either side of the brown gate, then glow orange during the anneal.",
        )
        .detail(
            "This is the hottest step in the front end.",
            &["Anneal ~1000 C", "Raised n+ epi source/drain"],
        ),
    Beat::new("ILD + CMP, then POLY PULL", BEAT_MS)
        .note(
            "Oxide (ILD0) is filled over everything and polished down until the top of the poly shows. Then the poly is etched out, leaving a trench lined by the spacers, with the channel silicon exposed at its floor.",
            "Pale see-through oxide blocks fill in beside the spacers and a polish layer skims the top. The brown poly then vanishes, a cyan flash marks the opening, and an empty trench is left.",
        )
        .detail(
            "The trench is a mould for the real gate.",
            &["ILD0 oxide, CMP to the poly top", "POLY PULL: etch out the dummy"],
        ),
    Beat::new("RMG STACK: the real gate goes in", BEAT_MS)
        .note(
            "The IL, HfO2, TiN, work-function metal and TiN barrier are grown into the trench one after another, then tungsten fills the middle and is polished flat. The source and drain heat is long over, so the films keep their properties.",
            "The films appear as nested U-shapes in turn: grey IL on the floor, yellow HfO2, gold and blue metals, then the grey tungsten fill flush with the top.",
        )
        .detail(
            "Intel used this at 45 nm in 2007; TSMC used gate-last at 28 nm.",
            &["Intel 45 nm (2007)", "TSMC 28 nm gate-last"],
        ),
];

// 3 one replacement gate in section, as a stepped cut-away.
const S3_BEATS: &[Beat] = &[
    Beat::new("the floor: IL, HfO2, dipole cap", BEAT_MS)
        .note(
            "Each film here is cut back a step behind the one under it, so all of them show. At the bottom sits the IL, a chemical SiOx about 0.5 nm thick, then the HfO2 high-k, then a very thin dipole cap (lanthanum oxide here) that nudges the threshold.",
            "Looking into the trench floor: the pale grey IL band at the front, the yellow HfO2 step behind it, and the pink dipole line just behind that, running up the left wall too.",
        )
        .detail(
            "HfO2's dielectric constant is ~20-25, against 3.9 for SiO2.",
            &["IL ~0.5 nm", "HfO2 k ~20-25 (SiO2 3.9)", "EOT ~1 nm class"],
        ),
    Beat::new("the work-function metals", BEAT_MS)
        .note(
            "A thin TiN cap protects the high-k. On it sits the work-function metal, which sets where the threshold lands. NMOS uses an Al-rich TiAlC(N) near silicon's conduction band; PMOS uses TiN near the valence band.",
            "Up the left wall: the gold TiN cap U, then the blue TiAlC(N) U inside it.",
        )
        .detail(
            "Thickness and composition of these metals give the chip several threshold flavours.",
            &["NMOS WFM: TiAlC(N)", "PMOS WFM: TiN"],
        ),
    Beat::new("barrier and fill", BEAT_MS)
        .note(
            "A last TiN layer keeps the tungsten from diffusing into the metals below. Tungsten fills the rest, and because it is the lowest-resistance part, it carries the gate signal along the gate line.",
            "The thin gold TiN barrier U inside the blue metal, and the large grey tungsten block in the middle.",
        )
        .detail(
            "Less room for the fill means more gate resistance.",
            &["TiN barrier blocks W diffusion", "W fill sets gate resistance"],
        ),
    Beat::new("the whole gate in section", BEAT_MS)
        .note(
            "Pulled back, the films read as nested U-shapes lining the floor and walls of the trench, with the fill in the middle. Nitride spacers and ILD0 oxide sit either side, and the channel is the silicon just under the floor.",
            "The trench between two green spacers, its yellow, gold and blue U-shapes round the grey fill, pale oxide blocks beside it and blue source and drain below.",
        )
        .detail(
            "Every gate on a modern logic die is built this way.",
            &["U-shaped films, W in the middle", "Spacers + ILD0 either side"],
        ),
];

// 4 gate-first versus gate-last.
const S4_BEATS: &[Beat] = &[
    Beat::new("two ways to build the same gate", BEAT_MS)
        .note(
            "Gate-first lays the high-k and metal flat, caps them with poly and patterns the gate, like the old poly gate. Gate-last puts a dummy poly gate in first and builds the real stack later. Both transistors here are at the same step, before the source/drain anneal.",
            "Top: gate-first, with thin yellow and blue films under a brown poly cap. Bottom: gate-last, with only a brown dummy poly gate on thin SiO2.",
        )
        .detail(
            "Gate-first is denser and simpler to integrate.",
            &["Gate-first: IBM Common Platform, 32/28 nm", "Gate-last: Intel 45 nm, TSMC 28 nm"],
        ),
    Beat::new("the anneal: ~1000 C", BEAT_MS)
        .note(
            "Both go through the source/drain anneal at about 1000 C. In gate-first the high-k and metal are already in place and take the heat, which shifts the threshold voltage. In gate-last only the throwaway poly is there.",
            "The blue source and drain glow orange in both. In the top transistor the gate films turn red-hot; in the bottom one the brown dummy poly sits in their place.",
        )
        .detail(
            "Threshold control got harder for gate-first as nodes shrank.",
            &["Anneal ~1000 C", "Vt shifts with the thermal budget"],
        ),
    Beat::new("gate-last: the stack goes in after", BEAT_MS)
        .note(
            "After the hot steps, gate-last pulls the dummy poly and grows the real films into the trench. They never see the anneal, so their threshold stays where it was designed. Gate-last won as nodes shrank.",
            "The bottom transistor's brown poly disappears and nested yellow, gold and blue U-shapes grow round a grey fill. The top one keeps its heated film.",
        )
        .detail(
            "Gate-last is the industry's standard flow today.",
            &["Gate-last at Intel 45 nm and TSMC 28 nm", "Industry standard since"],
        ),
];

// 5 EOT and leakage.
const S5_BEATS: &[Beat] = &[
    Beat::new("SiO2 at 1.2 nm: electrons tunnel", BEAT_MS)
        .note(
            "By the 90 nm node the SiO2 gate oxide was about 1.2 nm, only ~5 atomic layers. At that thickness electrons cross it by quantum tunnelling, so the gate leaks current all the time. Thinning it more to strengthen the gate would have made that much worse.",
            "Brown metal gate on top, the thin pale SiO2 band, tan silicon below. Cyan dots climb from the silicon straight through the SiO2 into the gate.",
        )
        .detail(
            "Tunnel current rises roughly tenfold for every ~0.2 nm the oxide thins (rule of thumb).",
            &["SiO2 ~1.2 nm at 90 nm", "~5 atomic layers"],
        ),
    Beat::new("HfO2: thicker, yet a stronger gate", BEAT_MS)
        .note(
            "Hafnium oxide has a dielectric constant of ~20-25, about six times SiO2's 3.9. So a film twice as thick still couples the gate to the channel more strongly, while tunnelling, which falls off sharply with thickness, nearly stops.",
            "Right: a thin grey IL and a thick yellow HfO2 band under the gate, with almost no dots crossing. Left: the SiO2 stack still leaking.",
        )
        .detail(
            "Intel claimed over 10x lower gate leakage at 45 nm.",
            &["HfO2 k ~20-25 vs SiO2 3.9", "IL 0.5 + HfO2 1.8 = 2.3 nm"],
        ),
    Beat::new("EOT: the thickness that counts", BEAT_MS)
        .note(
            "Equivalent oxide thickness (EOT) is the SiO2 thickness that would give the same capacitance: EOT = t_IL + t_HfO2 x 3.9/k. For 0.5 nm of IL and 1.8 nm of HfO2 at k ~20 that is ~0.85 nm, thinner in effect than the old 1.2 nm SiO2, though physically about twice as thick.",
            "Beside each stack, a cyan bar shows the physical thickness and a pink bar the EOT. On the left they are equal; on the right the cyan bar is tall and the pink one short.",
        )
        .detail(
            "Thick in fact, thin in effect.",
            &["EOT = t_IL + t_hk x 3.9/k", "Example: ~0.85 nm EOT", "Intel 45 nm: ~1.0 nm EOT"],
        ),
    Beat::new("now the IL eats the budget", BEAT_MS)
        .note(
            "The IL has a low k, so it counts almost one-for-one in the EOT. In the example, 0.5 nm of IL is more than half of the ~0.85 nm, while 1.8 nm of HfO2 adds only ~0.35 nm. Scaling EOT further now means thinning the interlayer.",
            "Close on the right stack: the thin IL band glows cyan under the much thicker yellow HfO2, with the two rulers beside it.",
        )
        .detail(
            "Every 0.1 nm of IL is ~0.1 nm of EOT.",
            &["IL ~0.5 of ~0.85 nm EOT", "HfO2 1.8 nm adds ~0.35 nm"],
        ),
];

// 6 threshold tuning in a nanosheet gate.
const S6_BEATS: &[Beat] = &[
    Beat::new("the gate wraps every sheet", BEAT_MS)
        .note(
            "In a gate-all-around transistor the channel is a stack of thin silicon sheets, and the gate surrounds each one. The IL, HfO2 and work-function metal must all fit in the few-nanometre gaps between sheets, with tungsten in what is left.",
            "A cut across three tan silicon sheets: each is ringed by a thin grey IL, a yellow HfO2 ring and a blue metal ring, set in the grey tungsten fill on a tan silicon base.",
        )
        .detail(
            "The gaps leave room for only a few nanometres of film.",
            &["Sheets ~5 nm thick", "Gaps of a few nm to ~10 nm"],
        ),
    Beat::new("La dipole: lower nFET Vt", BEAT_MS)
        .note(
            "A very thin lanthanum oxide film, driven to the IL/HfO2 interface, forms an electric dipole that lowers the nFET threshold. Changing the threshold this way adds almost no thickness, which matters in tight gaps.",
            "A pink ring appears round each sheet of the nFET stack, between the IL and the HfO2.",
        )
        .detail(
            "Recipes vary by foundry (general literature).",
            &["La-based dipole lowers nFET Vt", "Adds ~no thickness"],
        ),
    Beat::new("Al dipole on the pFET, several Vt", BEAT_MS)
        .note(
            "An aluminium oxide dipole shifts the threshold the opposite way, which helps the pFET. Mixing dipoles with work-function metal thickness and type gives one chip several threshold flavours, from fast and leaky to slow and frugal.",
            "Both stacks side by side: the nFET with blue TiAlC rings and pink dipoles, the pFET with gold TiN rings and green dipoles.",
        )
        .detail(
            "Each extra threshold flavour adds masks and process steps.",
            &["Al-based dipole: opposite shift", "nFET TiAlC, pFET TiN"],
        ),
];

// 7 by the numbers.
const S7_BEATS: &[Beat] = &[
    Beat::new("SiO2 limit: ~1.2 nm at 90 nm", BEAT_MS)
        .note(
            "The SiO2 gate oxide stopped thinning at about 1.2 nm around the 90 nm node. Below that, direct tunnelling leakage grows roughly tenfold per 0.2 nm, and the gate's standby power became unacceptable.",
            "The SiO2 stack: brown gate, thin pale SiO2, tan silicon, with cyan dots tunnelling up through it.",
        )
        .detail(
            "The oxide could no longer follow the rest of the transistor down.",
            &["SiO2 ~1.2 nm at 90 nm", "~10x leak per 0.2 nm (rule of thumb)"],
        ),
    Beat::new("Intel 45 nm: HfO2, EOT ~1 nm", BEAT_MS)
        .note(
            "Intel's 45 nm process (2007) replaced SiO2 and poly with a hafnium-based high-k and metal gates. EOT was about 1.0 nm, and Intel claimed over 10x lower gate leakage and about 20% more drive current.",
            "Both stacks: the SiO2 one still leaking on the left, the thicker yellow HfO2 stack on the right with a single dot crossing.",
        )
        .detail(
            "Gains are Intel's own claims.",
            &[">10x lower gate leakage (Intel)", "~20% more drive (Intel)", "TiN (PMOS), TiAlN (NMOS)"],
        ),
    Beat::new("ALD: ~0.1 nm per cycle", BEAT_MS)
        .note(
            "The HfO2 is grown by ALD, about 0.1 nm per cycle, so ~18 cycles give ~1.8 nm. ASM puts the single-wafer ALD market at ~$3.0B in 2024 and forecasts $5.1-6.1B by 2030, driven by gate-all-around.",
            "Close on the right stack: a dark gap above the IL fills from the bottom with thin alternating yellow and cream layers, one per cycle.",
        )
        .detail(
            "ASM reported 2025 revenue of ~EUR 3.2B and a 51.8% gross margin.",
            &["Single-wafer ALD ~$3.0B (2024, ASM)", "$5.1-6.1B by 2030 (ASM forecast)", "ASM 2025: ~EUR 3.2B revenue"],
        ),
];

// 8 who makes it.
const S8_BEATS: &[Beat] = &[
    Beat::new("ASM International: the ALD films", BEAT_MS)
        .note(
            "ASM International (ASM.AS) leads in ALD tools and makes the reactors that grow the HfO2 high-k. It claims the leading share of single-wafer ALD. The IL under it is grown chemically on the silicon.",
            "Close on the stepped floor: the pale grey IL at the front and the yellow HfO2 step, each tagged.",
        )
        .detail(
            "The share figure is ASM's own claim.",
            &["ASM: high-k ALD reactors", "Claimed #1 in single-wafer ALD"],
        ),
    Beat::new("Applied and Lam: metals and fill", BEAT_MS)
        .note(
            "Applied Materials (AMAT) supplies the Centura dielectric tools and Endura PVD/ALD for the TiN and metal-gate layers. Lam Research (LRCX) supplies ALD tungsten (ALTUS) for the fill, and ALTUS Halo molybdenum aimed at GAA.",
            "Up the wall: the gold TiN U tagged for Applied, and the grey tungsten fill tagged for Lam.",
        )
        .detail(
            "Lam's FY2025 revenue was $18.44B (whole company).",
            &["Applied: Endura PVD/ALD, Centura", "Lam: ALTUS W, ALTUS Halo Mo"],
        ),
    Beat::new("TEL, and the foundries", BEAT_MS)
        .note(
            "Tokyo Electron (8035.T) makes furnace and ALD tools. The foundries choose and integrate the flow: Intel went gate-last at 45 nm in 2007, TSMC at 28 nm. Synopsys and Cadence model the threshold flavours for designers.",
            "The whole transistor in its stepped cut-away, with the oxide and spacers tagged for TEL and the gate for the foundries.",
        )
        .detail(
            "Tool makers sell the steps; foundries own the recipe.",
            &["TEL: furnace and ALD", "Intel 45 nm, TSMC 28 nm gate-last"],
        ),
];

// 9 chokepoints and risks.
const S9_BEATS: &[Beat] = &[
    Beat::new("threshold spread in tiny gaps", BEAT_MS)
        .note(
            "In nanosheet gaps a few nanometres wide, a small change in work-function metal thickness moves that sheet's threshold. Sheets that should match end up different, which costs speed and margin across billions of transistors.",
            "Three wrapped tan sheets in grey fill; the middle sheet's blue metal ring is visibly thinner than the others.",
        )
        .detail(
            "Variability, not average thickness, is the hard part.",
            &["Vt variation in GAA gaps", "Gaps only a few nm"],
        ),
    Beat::new("IL thickness: every 0.1 nm counts", BEAT_MS)
        .note(
            "Because the IL counts almost one-for-one in EOT, 0.1 nm more IL is roughly 0.1 nm more EOT. ALD and IL growth must hold that thickness to fractions of an atom across a 300 mm wafer, wafer after wafer.",
            "Close on the trench floor: the thin IL band glows cyan under the yellow HfO2.",
        )
        .detail(
            "Uniformity control is a tool and process chokepoint.",
            &["+0.1 nm IL = ~+0.1 nm EOT", "Uniform across 300 mm"],
        ),
    Beat::new("fill voids as gates shrink", BEAT_MS)
        .note(
            "As the gate gets narrower the liners take up more of the trench, and the fill has less room. Tungsten growing in from both walls can close at the top and leave a seam or void, which raises gate resistance and can fail the part.",
            "A narrower trench: the same U-shaped films, a thin grey fill, and a dark slit down its middle.",
        )
        .detail(
            "Moving to molybdenum or other fill metals is one response.",
            &["Fill voids in narrow gates", "Lam ALTUS Halo: Mo fill"],
        ),
];

// 10 sources.
const S10_BEATS: &[Beat] = &[
    Beat::new("sources 1-2: Intel 45 nm", BEAT_MS)
        .note(
            "The finished replacement gate, as the sources describe it. Sources 1 and 2 cover Intel's 45 nm high-k metal gate: the first in production, in 2007.",
            "The whole transistor in its stepped cut-away, tagged at the gate.",
        )
        .detail(
            "Intel put HKMG into production at 45 nm (Penryn, 2007).",
            &[
                "[1] newelectronics.co.uk/content/news/intel-uses-high-k-and-metal-gates-in-45nm-process",
                "[2] EDN Intel 45 nm HKMG recipe: edn.com/?p=4005680",
            ],
        ),
    Beat::new("sources 3-4: HfO2, EOT, gate-last", BEAT_MS)
        .note(
            "Source 3 covers HfO2, the interlayer and EOT; source 4 compares gate-first and gate-last (IEDM 2010 coverage).",
            "Close on the floor films, the yellow HfO2 tagged [3] and the green spacer tagged [4].",
        )
        .detail(
            "Material facts from MRS and IEEE; flow comparison from IEDM coverage.",
            &[
                "[3] MRS 'Scalability of MOCVD-deposited hafnium oxide'; technav.ieee.org/topic/high-k-gate-dielectrics/",
                "[4] bit-tech.net/reviews/tech/global-foundries-gtc-2010/3/; realworldtech.com/iedm-2010/5",
            ],
        ),
    Beat::new("sources 5-8: ASM, Lam, Applied", BEAT_MS)
        .note(
            "Sources 5 to 8 are company results and product pages: ASM for ALD, Lam for tungsten and molybdenum fill, Applied for TiN.",
            "The floor and wall films tagged with the company that makes each one's tool.",
        )
        .detail(
            "Company figures are the companies' own reports; the market size is ASM's forecast.",
            &[
                "[5] ASM FY2025 results: investegate.co.uk (ASM International)",
                "[6] Lam FY2025 10-K: sec.gov/Archives/edgar/data/707549/000070754925000075/lrcx-20250629.htm",
                "[7] Applied: appliedmaterials.com/us/en/product-library/endura-ilb-pvd-ald.html",
                "[8] Lam Halo: siliconsemiconductor.net/article/121172/Lam_Research_ushers_in_new_era_of_semiconductor_metallisation_",
            ],
        ),
];

// ---- the pictures ----------------------------------------------------------------------------

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

pub fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_a.glb"),
        ZA_BEATS,
    )
}

pub fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_b.glb"),
        ZB_BEATS,
    )
}

pub fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_c.glb"),
        ZC_BEATS,
    )
}

pub fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_d.glb"),
        ZD_BEATS,
    )
}

pub fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the layers, from interlayer to fill",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "gate-last: dummy poly, pull, replace",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "EOT: why the oxide had to go",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "work-function metals and dipoles",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "the stack in a nanosheet gap",
        build: zoom_e,
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_gate_stack_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of CHIP_GATE_STACK.txt, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, S1_BEATS),
    section!(2, S2_BEATS),
    section!(3, S3_BEATS),
    section!(4, S4_BEATS),
    section!(5, S5_BEATS),
    section!(6, S6_BEATS),
    section!(7, S7_BEATS),
    section!(8, S8_BEATS),
    section!(9, S9_BEATS),
    section!(10, S10_BEATS),
];

fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_gate_stack.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "GATE STACK",
    overview: Some(build),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_keys_are_abcde() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
    }

    #[test]
    fn beat_counts_match_the_scripts() {
        let zooms: Vec<usize> = ZOOMS.iter().map(|z| (z.build)().beats().len()).collect();
        assert_eq!(zooms, [4, 4, 4, 4, 4]);
        let secs: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(secs, [3, 4, 4, 3, 4, 3, 3, 3, 3, 3]);
        assert_eq!(build().beats().len(), BEATS.len());
    }

    #[test]
    fn every_scene_is_explained_and_draws() {
        super::super::super::blender::explained(build().as_ref(), "overview");
        super::super::super::blender::draws_every_beat(build().as_ref(), "overview");
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
