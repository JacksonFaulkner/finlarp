// CHIP tab, NMOS: the node's overview is the whole-chip scene (tools/pbr3d/blender/chip_kit.py)
// with the camera zooming in on this part (tools/pbr3d/blender/chip_nmos.py). Six beats: the
// whole chip, in on the NMOS with the gate low, the gate rising and the channel forming, the
// electrons flowing source to drain, the gate falling, and back out. Zoom-ins a-e and sections
// 1-10 are their own Blender scenes in the same template.
//
// Sources: CHIP_NMOS.txt section 10 (anandtech.com/show/21310; Banerjee, UCSB ECE225 Lecture 5;
// semiengineering.com 18A coverage); textbook figures are marked as such.

use super::super::Node;
use super::super::blender::{BEAT_MS, Cell, Page, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("whole chip: one NMOS, the pull-down switch", BEAT_MS)
        .note(
            "The whole chip in cut-away: silicon at the bottom, layers of copper wiring above it, package bumps on top. Down in the silicon sit the transistors. The one outlined in yellow is an NMOS, the switch that pulls a signal down to 0 V.",
            "The chip as a slab: tan silicon at the bottom with two transistors (blue NMOS on the left, pink PMOS on the right), grey and copper wiring tiers above, silver bumps on top. A yellow box marks the NMOS.",
        )
        .detail(
            "Every switch in a chip is an NMOS or a PMOS.",
            &["NVIDIA B200: 208 billion transistors (CHIP_NMOS.txt, section 7)", "AMD MI300X: 153 billion (CHIP_NMOS.txt, section 7)"],
        ),
    Beat::new("off: gate at 0 V, nothing joins source and drain", BEAT_MS)
        .note(
            "Up close the NMOS is two n+ islands, the source (tied to ground) and the drain (the output), in a p-type well full of holes. With the gate at 0 V both islands meet the well in reverse-biased junctions, so no current can cross.",
            "Blue n+ source and drain under light-blue raised epitaxy, grey contact pillars up to the first copper wire, the green-capped gate between them, gold dots (holes) through the tan well, and thin violet depletion bands round the junctions.",
        )
        .detail(
            "Off, the switch passes only leakage.",
            &["Gate 0 V: junctions block current (CHIP_NMOS.txt, section 3)", "n+ ~1e20-1e21 /cm3 (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("gate up: the field pulls a channel of electrons", BEAT_MS)
        .note(
            "The gate rises to the supply, about 0.75 V. Its field reaches through the thin high-k dielectric, pushes the holes away and draws electrons into a sheet a few nanometres thick under the gate. That sheet, the channel, joins source and drain.",
            "The gate's fill metal glows amber, pink arrows point down through the teal high-k, the gold holes under the gate disappear, and a bright cyan strip appears on the surface.",
        )
        .detail(
            "Only the gate's field reaches the silicon; no current enters the gate.",
            &["Vt ~0.2-0.4 V at leading nodes (typical)", "Supply ~0.7-0.8 V (typical)"],
        ),
    Beat::new("flow: electrons ride from ground, through the channel, to the drain", BEAT_MS)
        .note(
            "With the channel open, electrons come in from ground through the source contact, cross under the gate and leave up the drain contact. That current pulls the output node down to 0 V.",
            "Cyan beads ride down the left contact pillar, along the cyan channel under the amber gate, and up the right pillar toward the copper wire.",
        )
        .detail(
            "Electrons are the fast carrier, which is why the NMOS is the stronger switch.",
            &["Electron mobility ~2-3x hole mobility in bulk Si (textbook)"],
        ),
    Beat::new("gate down: the channel empties and the flow stops", BEAT_MS)
        .note(
            "The gate falls back to 0 V. The amber glow and the channel fade, the holes return under the gate, and the switch is off again. A trickle of leakage still crosses below the surface.",
            "The gate goes dark grey, the cyan strip fades out, gold holes reappear under the gate, and a few violet dots drift from source to drain.",
        )
        .detail(
            "No switch turns off perfectly; leakage across billions of them adds up.",
            &["Swing >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("whole chip again: one switch of billions", BEAT_MS)
        .note(
            "Back out to the whole chip. This NMOS is one of billions, joined to its PMOS partner and its neighbours by tungsten contacts and copper wiring.",
            "The whole chip in cut-away again, the yellow box back round the NMOS.",
        )
        .detail(
            "Every switch on the chip is built this same way.",
            &["NVIDIA H100/H200: 80 billion (CHIP_NMOS.txt, section 7)", "Apple M4: 28 billion (CHIP_NMOS.txt, section 7)"],
        ),
];

// ---- zoom-ins a-e: the gate stack, threshold, saturation, DIBL, dopants -----------------------

const ZA_BEATS: &[Beat] = &[
    Beat::new("the gate stack, cut open: metal on high-k over the silicon", BEAT_MS)
        .note(
            "The gate is a stack of layers. A thin SiO2 interlayer sits on the silicon, a hafnium-oxide high-k layer lines a U-shaped trench, a work-function metal inside it sets the threshold voltage, and a fill metal carries the signal. Nitride spacers flank it.",
            "Close on the gate: a white line at the bottom (SiO2), a teal U (high-k), a brass U inside it (work-function metal), the grey fill in the middle, green nitride all round; gold holes in the tan silicon below.",
        )
        .detail(
            "The high-k metal gate has been standard since the 45 nm node.",
            &["Metal + high-k (HfO2) + thin SiO2 (CHIP_NMOS.txt, section 2)", "EOT ~1 nm class (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("gate voltage on: the field reaches through the oxide", BEAT_MS)
        .note(
            "Raise the gate to ~0.75 V and an electric field crosses the dielectric into the silicon. The dielectric is an insulator, so no current flows into the gate: it works like one plate of a capacitor.",
            "The fill metal glowing amber and three pink arrows running down through the high-k into the silicon.",
        )
        .detail(
            "Capacitive control is why a gate draws power only when it switches.",
            &["Gate draws no DC current (CHIP_NMOS.txt, section 1)"],
        ),
    Beat::new("the channel: electrons gather at the surface", BEAT_MS)
        .note(
            "The field pushes the holes down into the well and pulls electrons up to the surface. Above the threshold they form a thin inversion layer: the channel.",
            "A bright cyan strip under the gate, the gold holes gone from just beneath it, the pink field arrows still lit.",
        )
        .detail(
            "Inversion turns the p-type surface n-type, joining source and drain.",
            &["Inversion above Vt (CHIP_NMOS.txt, section 3)", "Vt ~0.2-0.4 V (typical)"],
        ),
    Beat::new("high-k: thick but electrically thin", BEAT_MS)
        .note(
            "Plain SiO2 thin enough for today's transistors would be only a few atoms thick and leak badly by tunnelling. Hafnium oxide has a dielectric constant several times higher, so a physically thicker layer gives the same pull on the channel with far less leakage.",
            "Yellow outlines on the teal high-k layer: along the bottom of the gate and up its side.",
        )
        .detail(
            "High-k is what let gate scaling continue past ~1 nm of SiO2.",
            &["HfO2 k ~20-25 vs SiO2 3.9 (textbook)", "EOT ~1 nm class (CHIP_NMOS.txt, section 2)"],
        ),
];

const ZB_BEATS: &[Beat] = &[
    Beat::new("below threshold: leakage only", BEAT_MS)
        .note(
            "Below the threshold the surface is depleted but not inverted, and electrons from the source face an energy barrier. Only the few with enough thermal energy get over it. This subthreshold current is the off-state leakage.",
            "The gate faintly amber, a violet depletion block under it, a few violet dots crossing just under the surface, and the gauge at the right showing a short bar.",
        )
        .detail(
            "The current rises about 10x for every 60-90 mV of gate voltage here.",
            &["Swing >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)", "Real swing ~70-90 mV/decade (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("threshold: inversion starts and the channel forms", BEAT_MS)
        .note(
            "At the threshold voltage the surface inverts and a thin electron layer forms. The current has climbed several decades from leakage and keeps climbing steeply.",
            "A faint cyan strip under the dim amber gate, a sparse line of cyan electrons, and the gauge bar halfway up.",
        )
        .detail(
            "Lower Vt is faster but leaks more, so chips offer several Vt choices.",
            &["Vt ~0.2-0.4 V at leading nodes (typical)", "~10x leakage per 60-100 mV lower Vt (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("above threshold: full current", BEAT_MS)
        .note(
            "At the full supply the channel is strong and the current is limited mostly by how fast the electrons can move. On-current is roughly five to six decades above the leakage, which is what makes this a good switch.",
            "The gate bright amber, a solid cyan channel, a dense stream of electrons, and the gauge bar near the top.",
        )
        .detail(
            "Ion/Ioff is the figure of merit for a logic transistor.",
            &["Ion/Ioff ~1e5-1e6 (typical, estimate)", "Supply ~0.7-0.8 V (typical)"],
        ),
];

const ZC_BEATS: &[Beat] = &[
    Beat::new("low drain voltage: an even channel", BEAT_MS)
        .note(
            "With the gate on and only a small drain voltage, the channel is the same thickness from source to drain. It behaves like a resistor: double the drain voltage and the current roughly doubles (the linear region).",
            "The amber gate over an even cyan strip, with cyan electrons moving steadily along it.",
        )
        .detail(
            "The linear region is where a switch sits once it has nearly finished pulling its output down.",
            &["Linear region at small drain voltage (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("the drain end thins: the drain weakens the gate's pull", BEAT_MS)
        .note(
            "As the drain voltage rises, the voltage between gate and channel shrinks toward the drain end, so fewer electrons gather there. The channel tapers, and the current grows more slowly.",
            "The cyan channel in steps: thick at the source end, thinner toward the drain; electrons still flowing.",
        )
        .detail(
            "Current stops rising in proportion to the drain voltage.",
            &["Channel charge falls toward the drain (textbook)"],
        ),
    Beat::new("pinch-off at the drain: current levels out", BEAT_MS)
        .note(
            "Once the drain voltage exceeds gate voltage minus threshold, the channel pinches off short of the drain. Electrons cross the last gap pulled by the drain's field, and the current hardly rises any more: saturation. The transistor now acts like a current source set by the gate.",
            "The cyan channel stopping short of the drain, a violet depletion region reaching out from the drain, and electrons still crossing to it.",
        )
        .detail(
            "Logic gates switch most of their charge in saturation.",
            &["Saturation when VD > VG - Vt (CHIP_NMOS.txt, section 3)"],
        ),
];

const ZD_BEATS: &[Beat] = &[
    Beat::new("a long gate: the gate owns the barrier", BEAT_MS)
        .note(
            "In a long transistor the depletion under the gate is far from the drain. The gate alone sets the barrier that keeps electrons in the source, so the threshold does not depend on the drain voltage.",
            "A wide gate over a violet depletion block, with the drain's own depletion bands staying near the drain.",
        )
        .detail(
            "Long-channel behaviour is what the textbook equations assume.",
            &["Long channel: Vt independent of drain voltage (textbook)"],
        ),
    Beat::new("the drain field reaches the source: DIBL", BEAT_MS)
        .note(
            "Shrink the gate and the drain's depletion region reaches across under it. The drain now helps lower the source barrier (drain-induced barrier lowering), so the threshold falls and some electrons leak across while the gate is off.",
            "A narrow gate, violet depletion stretching from the drain toward the source, a pink arrow pointing from the drain side to the source side, and violet leakage dots crossing.",
        )
        .detail(
            "DIBL and Vt roll-off are the classic short-channel effects.",
            &["DIBL: the drain lowers the source barrier (CHIP_NMOS.txt, section 5)", "Vt roll-off as the channel shrinks (textbook)"],
        ),
    Beat::new("higher drain voltage: more leakage", BEAT_MS)
        .note(
            "Raise the drain voltage and the effect grows: the depletion reaches further, the barrier drops more and leakage climbs steeply. Wrapping the gate round the channel (FinFET, gate-all-around) is the cure.",
            "Wider violet depletion from the drain, two pink arrows reaching past the gate, and a denser stream of violet leakage dots.",
        )
        .detail(
            "This is why planar transistors gave way to fins at 22/16 nm.",
            &["FinFET and GAA gates surround the channel (CHIP_NMOS.txt, section 5)"],
        ),
];

// The same picture as section 6, so the same beats.
const ZE_BEATS: &[Beat] = SEC6;

// ---- sections 1-10 ----------------------------------------------------------------------------
// Each section is a close-up of one detailed NMOS in cut-away (chip_mos_detail.py): blue n+
// source and drain under light-blue Si:P epitaxy, dark silicide and grey tungsten contacts, the
// gate stack (white SiO2, teal high-k, brass work-function metal, grey fill, green nitride cap and
// spacers), orange-brown halo pockets, the tan p-well over a darker p substrate, white STI walls.

const SEC1: &[Beat] = &[
    Beat::new("off: gate at 0 V, nothing joins source and drain", BEAT_MS)
        .note(
            "An NMOS is a switch made of doped silicon. Two blue n+ islands, the source and the drain, sit in a tan p-type well full of holes. With the gate at 0 V each island meets the p-well in a reverse-biased junction, so almost no current can cross from one to the other.",
            "The cut face of one transistor: the two blue n+ blocks under their light-blue raised epitaxy and grey contact pillars, the green-capped gate between them, the white STI walls at both ends, and gold dots (holes) spread through the tan p-well.",
        )
        .detail(
            "Off means only leakage flows, which is what lets billions of these sit idle on one chip.",
            &["Gate 0 V: junctions reverse-biased, only leakage (CHIP_NMOS.txt, section 3)", "Supply at leading nodes ~0.7-0.8 V (typical)"],
        ),
    Beat::new("gate high: its field pulls an electron channel", BEAT_MS)
        .note(
            "Raising the gate to the supply (~0.75 V) puts an electric field across the thin dielectric. The field pushes the holes away from the surface and draws electrons into a sheet a few nanometres thick right under the gate: the channel. No current flows into the gate; only its field reaches the silicon.",
            "The camera closes on the gate. The gate's fill metal glows amber, three pink arrows (the field) point down through the teal high-k, and a thin bright cyan strip (the channel) appears on the silicon surface between the extensions.",
        )
        .detail(
            "Field control with no gate current is why CMOS logic burns so little power at rest.",
            &["Threshold voltage ~0.2-0.4 V at leading nodes (typical)", "Gate draws no DC current (CHIP_NMOS.txt, section 1)"],
        ),
    Beat::new("on: electrons run from source to drain", BEAT_MS)
        .note(
            "With the drain at the supply, electrons leave the grounded source, cross the channel and leave through the drain. This is the switch conducting: in an inverter it pulls the output down to 0 V. Electrons move about two to three times faster than holes, so an NMOS of a given size is the stronger switch.",
            "Cyan dots (electrons) come down the left contact pillar, run along the bright channel under the amber gate, and climb the right contact. The gold holes stay deeper in the tan well.",
        )
        .detail(
            "NMOS pulls outputs low; its PMOS partner pulls them high.",
            &["Electron mobility ~2-3x hole mobility in bulk Si (textbook)", "Bulk Si: electrons ~1400, holes ~450 cm2/Vs (textbook)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("N+ SOURCE: where the electrons come from", BEAT_MS)
        .note(
            "The source is silicon doped so heavily with arsenic or phosphorus that it is full of free electrons. On top sits a raised layer of phosphorus-doped silicon grown in place (Si:P epitaxy), then a thin metal silicide that lets the tungsten contact connect with low resistance. The source is usually tied to ground.",
            "A yellow outline round the left side: the blue n+ block, the light-blue raised epitaxy on it, the dark silicide strip, and the grey tungsten contact pillar rising from it.",
        )
        .detail(
            "Every ohm in the source path subtracts from drive current.",
            &["n+ doping ~1e20-1e21 /cm3 (CHIP_NMOS.txt, section 2)", "Si:P epitaxy ~1.2e21 /cm3 (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("GATE STACK: metal on high-k on a thin oxide", BEAT_MS)
        .note(
            "The gate is a sandwich. A thin SiO2 interlayer sits on the silicon, then a hafnium-oxide high-k layer, then a work-function metal that sets the threshold voltage, then a fill metal, capped with silicon nitride. High-k lets the dielectric stay physically thicker (less tunnelling) while acting electrically like ~1 nm of SiO2.",
            "Close on the gate: the white interlayer at the bottom, the teal high-k lining a U-shaped trench, the brass work-function metal inside it, the grey fill metal in the middle and the green nitride cap and spacers round it.",
        )
        .detail(
            "The high-k metal gate (HKMG) has been standard since 45 nm.",
            &["EOT ~1 nm class (CHIP_NMOS.txt, section 2)", "HfO2 k ~20-25 vs SiO2 3.9 (textbook)", "Work-function metal sets Vt (textbook)"],
        ),
    Beat::new("N+ DRAIN: the output", BEAT_MS)
        .note(
            "The drain is built the same way as the source, but it is the output: it connects to the node the switch pulls down. The two ends are physically symmetric; which one is the drain depends on which is at the higher voltage.",
            "A yellow outline round the right side: blue n+ block, light-blue epitaxy, dark silicide and the grey contact pillar that carries the output.",
        )
        .detail(
            "The drain junction also adds capacitance the circuit must charge every cycle.",
            &["Drain: the output node (CHIP_NMOS.txt, section 2)", "Same n+ doping as the source (textbook)"],
        ),
    Beat::new("P-WELL: the body, full of holes", BEAT_MS)
        .note(
            "The transistor sits in a p-type well doped with boron, on a lightly doped p-type wafer. In p-type silicon the free carriers are holes. The well's doping helps set the threshold and keeps neighbouring devices from talking to each other through the silicon.",
            "A yellow outline round the tan p-well below the device, with the gold dots (holes) through it; the darker tan band underneath is the p substrate.",
        )
        .detail(
            "The well is a fourth terminal: biasing it shifts the threshold (section 5).",
            &["P-well boron ~1e15-1e18 /cm3 (CHIP_NMOS.txt, section 2)", "Holes: the majority carrier (CHIP_NMOS.txt, section 2)"],
        ),
    Beat::new("halo pockets, spacers, STI", BEAT_MS)
        .note(
            "Small parts with a big effect. Shallow extensions carry current under the gate edge. Halo pockets, extra boron just below the extension tips, stop the source and drain depletion regions from merging (punch-through). Nitride spacers set how far the deep source and drain sit from the gate. STI oxide walls isolate neighbours.",
            "Yellow outlines on the two orange-brown halo pockets under the extension tips; tags on the green spacer beside the gate, the thin blue extension, and the white STI wall at the right.",
        )
        .detail(
            "Halos trade a little speed for much less short-channel leakage.",
            &["Halos stop punch-through (CHIP_NMOS.txt, section 2)", "Spacers set extension spacing; STI isolates (CHIP_NMOS.txt, section 2)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. OFF STATE: gate at 0 V", BEAT_MS)
        .note(
            "At rest the gate is at 0 V. The source and drain junctions with the p-well are reverse-biased, so each is wrapped in a thin depletion layer with no free carriers, and no channel joins them.",
            "Violet bands under and beside the blue source and drain (the junction depletion), the gate dark, and gold holes everywhere in the well including right under the gate.",
        )
        .detail(
            "The off state still leaks a little; section 4 shows why.",
            &["VG = 0: junctions block current (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("2. DEPLETION: holes pushed away", BEAT_MS)
        .note(
            "A small positive gate voltage repels the holes from the surface under the gate. That leaves a depletion region: fixed, ionised boron atoms but no free carriers. Nothing conducts yet.",
            "Close on the gate: the fill metal faintly amber, a violet block under the gate where the gold holes have gone, and holes still in the rest of the well.",
        )
        .detail(
            "Depletion charge has to be built before any channel can form.",
            &["0 < VG < Vt: holes pushed away (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("3. INVERSION: an electron channel", BEAT_MS)
        .note(
            "Above the threshold voltage the surface inverts: electrons from the source and drain gather in a thin sheet under the gate, so the p-type surface now behaves like n-type. That sheet is the channel.",
            "The gate glowing amber, pink field arrows down through the high-k, and a bright cyan strip on the surface above the violet depletion region.",
        )
        .detail(
            "Inversion is what 'on' means in a MOSFET.",
            &["VG > Vt (CHIP_NMOS.txt, section 3)", "Vt ~0.2-0.4 V at leading nodes (typical)"],
        ),
    Beat::new("4. LINEAR, then SATURATION", BEAT_MS)
        .note(
            "With a small drain voltage the channel is even from end to end and acts like a resistor (linear region). Raising the drain voltage thins the channel at the drain end until it pinches off; the current then levels out and depends mostly on the gate (saturation).",
            "Cyan electrons run source to drain. First half of the beat: an even cyan strip. Second half: the strip stepping thinner toward the drain and stopping short of it.",
        )
        .detail(
            "Logic gates switch through both regions on every transition.",
            &["Saturation when VD > VG - Vt (CHIP_NMOS.txt, section 3)"],
        ),
    Beat::new("5. TURN-OFF: the channel empties", BEAT_MS)
        .note(
            "The gate drops back to 0 V. The channel's electrons drain back into the source and drain almost at once, and the holes return under the gate. A trickle of leakage remains.",
            "The amber glow and cyan strip fade, the gold holes reappear under the gate, and a few violet dots (leakage) still drift under the surface from source to drain.",
        )
        .detail(
            "A switch cannot turn fully off; the swing limit sets how close it gets.",
            &["VG -> 0 (CHIP_NMOS.txt, section 3)", "Swing >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("below threshold: a barrier, and a leak", BEAT_MS)
        .note(
            "Below the threshold the surface is depleted but not inverted. Electrons from the source face an energy barrier; only the few with enough thermal energy hop over it. That subthreshold current rises about 10x for every 60-90 mV of gate voltage, and at 0 V it is the off-state leakage.",
            "The gate faintly amber, a violet depletion block under it, and a few violet dots crossing just under the surface from source to drain.",
        )
        .detail(
            "Leakage times billions of transistors is a large share of chip power.",
            &["Swing >= 60 mV/decade at 300 K (CHIP_NMOS.txt, section 4)", "Real swing ~70-90 mV/decade (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("at threshold: the channel just forms", BEAT_MS)
        .note(
            "At the threshold voltage the surface inverts and a thin electron layer appears. Current climbs steeply from here. Designers pick Vt as a trade: lower Vt is faster but leaks more.",
            "A faint, half-transparent cyan strip under the dim amber gate, and a sparse line of cyan electrons moving source to drain.",
        )
        .detail(
            "Chips offer several Vt flavours so designers can mix fast and low-leakage cells.",
            &["Vt ~0.2-0.4 V at leading nodes (typical)", "Each 60-100 mV lower Vt: ~10x more leakage (CHIP_NMOS.txt, section 4)"],
        ),
    Beat::new("above threshold: fully on", BEAT_MS)
        .note(
            "At the full supply the channel is strong and the current is limited mainly by how fast electrons can move (their velocity saturates near ~1e7 cm/s). The ratio of on-current to off-current, roughly a million to one or more, is what makes a good switch.",
            "The gate bright amber, a solid cyan channel, and a dense stream of cyan electrons from the left contact to the right.",
        )
        .detail(
            "Ion/Ioff is the figure of merit for a logic transistor.",
            &["Supply ~0.7-0.8 V (typical)", "Ion/Ioff ~1e5-1e6 or more (typical, estimate)"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("DIBL: the drain lowers the source barrier", BEAT_MS)
        .note(
            "In a short channel the drain is close enough that its field reaches under the gate and lowers the barrier at the source (drain-induced barrier lowering). The threshold falls as drain voltage rises, and leakage climbs.",
            "Pink arrows pointing from the drain side toward the source under the dark gate, a violet depletion region stretching out from the drain, and violet leakage dots crossing below the surface.",
        )
        .detail(
            "DIBL and Vt roll-off are why planar transistors stopped scaling below ~20 nm.",
            &["DIBL: drain-induced barrier lowering (CHIP_NMOS.txt, section 5)", "Planar bulk gave way to FinFET at 22/16 nm (textbook)"],
        ),
    Beat::new("body bias: the well is a fourth terminal", BEAT_MS)
        .note(
            "A p+ tap past the STI wall connects the p-well to a voltage. Driving the well negative (reverse body bias) widens the depletion under the gate and raises the threshold, cutting leakage; forward bias lowers it for speed. The shift follows a square-root law.",
            "A yellow outline on the p+ tap and its contact at the right, a pink arrow from the tap into the well, and a deeper violet depletion block under the gate.",
        )
        .detail(
            "Body bias works best on planar and FD-SOI; fins weaken it.",
            &["Body bias: square-root law (CHIP_NMOS.txt, section 5)", "Speed vs leakage knob (CHIP_NMOS.txt, section 5)"],
        ),
    Beat::new("wrap the gate round the channel: FinFET", BEAT_MS)
        .note(
            "The fix for short channels is geometry. Here the device is cut across the gate: the silicon is a thin vertical fin, and the gate wraps its top and both sides, so the gate, not the drain, controls the barrier. The channel forms on all three faces.",
            "Three-quarter view of two grey silicon fins in cross-section, each lined with teal high-k and brass work-function metal inside the grey gate, with bright cyan channels on three faces; blue n+ epitaxy past the green spacer.",
        )
        .detail(
            "FinFETs carried the industry from 22 nm to 3 nm; gate-all-around sheets come next.",
            &["FinFET and nanosheet gates surround the channel (CHIP_NMOS.txt, section 5)", "Fin width ~5-7 nm at N5/N3 class (estimate)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("dopants: arsenic shallow, phosphorus deep", BEAT_MS)
        .note(
            "The n+ regions are made by adding donor atoms. Arsenic diffuses slowly, so it makes the shallow, abrupt extensions under the gate edge. Phosphorus activates more fully but spreads faster, so it goes in the deep source and drain.",
            "White dots (dopant atoms) through the blue source, drain and their raised epitaxy; yellow outlines on the two thin extensions at the gate edges.",
        )
        .detail(
            "Abrupt junctions keep the channel short without leaking.",
            &["n+ ~1e20-1e21 /cm3 (CHIP_NMOS.txt, section 2)", "As shallow and abrupt; P deeper (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("Si:P epitaxy and halo pockets", BEAT_MS)
        .note(
            "Modern NMOS source and drain are not implanted but grown: silicon with phosphorus built in (Si:P), which reaches very high active doping and low resistance. Below the extension tips, boron halo pockets hold the barrier against punch-through.",
            "Yellow outlines on the light-blue raised epitaxy on both sides and on the two orange-brown halo pockets beneath the extension tips; the dopant dots stay lit.",
        )
        .detail(
            "Grown-in doping beats implants at these sizes.",
            &["Si:P ~1.2e21 /cm3, ~0.3 mOhm.cm (CHIP_NMOS.txt, section 6)", "Contact resistivity to 1.5e-9 Ohm.cm2 reported (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("tensile strain: faster electrons", BEAT_MS)
        .note(
            "Phosphorus and carbon atoms are smaller than silicon, so Si:P source and drain pull the channel lattice apart (tensile strain). Stretched silicon lets electrons move faster, raising drive current without shrinking anything.",
            "Pale yellow arrows pointing outward from the channel centre toward the source and drain, the gate amber, the cyan channel lit, and a quick stream of cyan electrons.",
        )
        .detail(
            "Strain has been a free speed-up since the 90 nm node.",
            &["Si:P stretches the channel, speeding electrons (CHIP_NMOS.txt, section 6)", "Intel 90 nm strain: NMOS ~+10% drive (CHIP_PMOS.txt, section 6)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("one NMOS: one switch", BEAT_MS)
        .note(
            "Everything so far is one transistor, switched on with electrons flowing. At a leading node a transistor like this is roughly a tenth of a micron across. Every logic gate on a chip is built from NMOS and PMOS pairs like it.",
            "The whole cut-away device, gate amber, cyan channel lit and cyan electrons running from the left contact to the right.",
        )
        .detail(
            "Transistor count is the simplest measure of how much a chip can do.",
            &["Contacted gate pitch ~50 nm at N3 class (estimate)", "Every transistor is an NMOS or a PMOS (CHIP_NMOS.txt, section 7)"],
        ),
    Beat::new("billions of them, in rows", BEAT_MS)
        .note(
            "Seen from above, transistors are laid out in rows: strips of active silicon crossed by gate lines, each crossing a transistor. Blue NMOS rows alternate with pink PMOS rows. A big AI GPU holds hundreds of billions.",
            "A top-down tile: blue and pink active strips across the picture, crossed by many grey vertical gate lines, on tan and slate wells.",
        )
        .detail(
            "Counts grow with die area, density and the number of dies in a package.",
            &["NVIDIA B200: 208 billion (CHIP_NMOS.txt, section 7)", "AMD MI300X: 153 billion; H100: 80 billion (CHIP_NMOS.txt, section 7)"],
        ),
    Beat::new("wired into a chip", BEAT_MS)
        .note(
            "Contacts drop onto every source, drain and gate, and copper wires above them connect the transistors into gates, cells and whole processors. Wiring now limits density as much as the transistors do.",
            "Copper-coloured horizontal and vertical straps laid over the rows of transistors.",
        )
        .detail(
            "Billions of switches only become a chip once they are wired.",
            &["Apple M4: 28 billion; Apple M1: 16 billion (CHIP_NMOS.txt, section 7)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("TSMC: FinFET at N3", BEAT_MS)
        .note(
            "TSMC (TSM) builds the transistors for NVIDIA, AMD and Apple. Its N3 family still uses fins: the gate wraps three sides of each thin silicon fin. Its N2 node moves to nanosheets.",
            "Two grey fins cut across the gate, wrapped in teal high-k and brass metal inside the grey gate, cyan channels glowing on three faces.",
        )
        .detail(
            "Most leading-edge NMOS in AI chips come out of TSMC fabs.",
            &["TSMC 2025: 3 nm 24%, 7 nm and below 74% of wafer revenue (CHIP_NMOS.txt, section 8)", "2025 revenue NT$3,809B (~US$122B) (CHIP_NMOS.txt, section 8)"],
        ),
    Beat::new("Intel 18A: RibbonFET, stacked sheets", BEAT_MS)
        .note(
            "Intel (INTC) makes gate-all-around transistors on 18A: the channel is a stack of thin silicon ribbons, and the gate surrounds every one on all four sides, for even tighter control than a fin.",
            "Three grey silicon sheets stacked in the cut face, each ringed by teal high-k and brass metal with a cyan channel on all four sides, inside the grey gate.",
        )
        .detail(
            "Gate-all-around is the next step after FinFET for every leading foundry.",
            &["18A: 4 NMOS Vt options over 180 mV (CHIP_NMOS.txt, section 8)", "18A-P: ~+5% NMOS drive (CHIP_NMOS.txt, section 8)"],
        ),
    Beat::new("Synopsys, Cadence: simulating the device", BEAT_MS)
        .note(
            "Before anything is built, process and device simulators (TCAD) split the transistor into a mesh and solve for the potential and current in each cell. Circuit simulators then use compact models fitted to the results. Synopsys (SNPS) and Cadence (CDNS) sell these tools.",
            "A glowing blue grid laid over the cut-away device, and a violet block under the amber gate showing the solved potential region.",
        )
        .detail(
            "No chip is taped out without simulating its transistors first.",
            &["FY25 revenue: Synopsys $7.054B, Cadence $5.297B (CHIP_NMOS.txt, section 8)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("leakage and Vt variability", BEAT_MS)
        .note(
            "Small transistors leak in more ways: under the gate (subthreshold), through the thin gate dielectric (tunnelling), and at the junctions. And with only a few dopant atoms in the channel, exactly where they land shifts each device's threshold.",
            "Violet leakage dots crossing under the gate and rising through the gate dielectric, and a few bright yellow dopant atoms scattered in the channel region.",
        )
        .detail(
            "Variability forces designers to add margin, which costs speed or power.",
            &["Leakage and Vt variability grow at 2 nm-class nodes (CHIP_NMOS.txt, section 9)"],
        ),
    Beat::new("contact resistance limits drive", BEAT_MS)
        .note(
            "As everything shrinks, the contacts get smaller but the current through them does not, so the resistance at the metal-to-silicon interface becomes a large part of the total. Better silicide and higher doping help, but it remains a limit.",
            "The two contact pillars tinted red, a red-hot line where each meets the silicide, and cyan electrons crawling through.",
        )
        .detail(
            "Contact resistance is one of the main brakes on drive current today.",
            &["Strain and contact resistance limit drive (CHIP_NMOS.txt, section 9)", "1.5e-9 Ohm.cm2 reported on Si:P (CHIP_NMOS.txt, section 6)"],
        ),
    Beat::new("very few fabs can make them", BEAT_MS)
        .note(
            "Only three companies make leading-edge logic transistors: TSMC, Intel and Samsung. TSMC makes most of the AI chips, so a disruption at its fabs would hit almost every AI accelerator at once.",
            "Three transistor cross-sections side by side, cut across the gate: a FinFET (two fins) and two gate-all-around stacks, each tagged with its maker.",
        )
        .detail(
            "Concentration in a few fabs is a supply risk for the whole AI stack.",
            &["Leading-edge makers: TSMC, Intel, Samsung (CHIP_NMOS.txt, section 9)", "TSMC 7 nm and below: 74% of its 2025 wafer revenue (CHIP_NMOS.txt, section 8)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("transistor counts: NVIDIA, AMD, Apple", BEAT_MS)
        .note(
            "The transistor counts come from launch coverage and company statements; they are company or press figures, not independent counts.",
            "The top-down rows of transistors, tagged with the source numbers.",
        )
        .detail(
            "Counts come from launch coverage and company statements.",
            &[
                "[1] anandtech.com/show/21310; tomshardware.com Blackwell B200 launch",
                "[3] tweaktown.com/news/94342; digitimes.com/news/a20230614VL200.html",
                "[11] en.wikipedia.org/wiki/Apple_M4; heise.de/en/news (M4 iPad Pro)",
            ],
        ),
    Beat::new("dopants and Si:P: patents and an ECS paper", BEAT_MS)
        .note(
            "The arsenic and phosphorus trade-off and the Si:P doping, resistivity and contact figures come from these patents and conference paper.",
            "The cut-away device with yellow outlines on the source and drain and white dopant atoms through them.",
        )
        .detail(
            "The dopant and Si:P figures are taken from these.",
            &[
                "[4] patents.google.com/patent/US4851360; patents.google.com/patent/US8039375",
                "[5] image-ppubs.uspto.gov 7960236; ecs.confex.com/ecs/242/webprogram/Paper166416.html",
            ],
        ),
    Beat::new("swing and DIBL: UCSB lecture and arXiv", BEAT_MS)
        .note(
            "The swing equation and the DIBL description come from a UCSB device lecture and an arXiv paper.",
            "Close on the gate: a yellow outline on the gate stack, its fill faintly amber, and violet depletion reaching out from the drain.",
        )
        .detail(
            "The swing and DIBL equations are from these sources.",
            &["[6] courses.ece.ucsb.edu ECE225 Lecture_05; arxiv.org/pdf/1212.2684"],
        ),
    Beat::new("makers and simulators: TSMC, Intel, Synopsys, Cadence", BEAT_MS)
        .note(
            "The 18A options, TSMC's revenue mix, NVIDIA's results and the Synopsys and Cadence revenue come from these filings and articles.",
            "The three transistor cross-sections side by side, each tagged with its source numbers.",
        )
        .detail(
            "Company filings and press coverage for the makers and simulators.",
            &[
                "[7] semiengineering.com/extending-18a-with-significant-power-and-performance-gains",
                "[8] sec.gov/Archives/edgar/data/1046179 (6-K); telecomlead.com TSMC 2025 results",
                "[9] sec.gov/Archives/edgar/data/1045810/000104581026000019/q4fy26pr.htm",
                "[10] cimdata.com Synopsys FY2025; seekingalpha.com/pr/20402555 Cadence FY2025",
            ],
        ),
];

// ---- the cells and builders -------------------------------------------------------------------

static OVERVIEW: Cell = std::sync::OnceLock::new();
static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();
static SEC: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_a.glb"),
        ZA_BEATS,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_b.glb"),
        ZB_BEATS,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_c.glb"),
        ZC_BEATS,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_d.glb"),
        ZD_BEATS,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos_zoom_e.glb"),
        ZE_BEATS,
    )
}

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the gate stack: metal on high-k",
        build: || -> Box<dyn Scene> { zoom_a() },
    },
    Zoom {
        key: 'b',
        label: "subthreshold, threshold, on",
        build: || -> Box<dyn Scene> { zoom_b() },
    },
    Zoom {
        key: 'c',
        label: "saturation: pinch-off at the drain",
        build: || -> Box<dyn Scene> { zoom_c() },
    },
    Zoom {
        key: 'd',
        label: "short channels: DIBL",
        build: || -> Box<dyn Scene> { zoom_d() },
    },
    Zoom {
        key: 'e',
        label: "dopants and strain",
        build: || -> Box<dyn Scene> { zoom_e() },
    },
];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &SEC[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/chip_nmos_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of CHIP_NMOS.txt, in order.
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

fn overview() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/chip_nmos.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

pub const NODE: Node = Node {
    page: "NMOS",
    overview: Some(overview),
    sections: &SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = overview();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "NMOS overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        super::super::super::blender::draws_every_beat(s.as_ref(), "NMOS overview");
    }

    #[test]
    fn zooms_have_their_beats_explained_and_draw() {
        for (name, build, n) in [
            ("zoom a", zoom_a as fn() -> Box<dyn Scene>, 4),
            ("zoom b", zoom_b, 3),
            ("zoom c", zoom_c, 3),
            ("zoom d", zoom_d, 3),
            ("zoom e", zoom_e, 3),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), n, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 5, 5, 3, 3, 3, 3, 3, 3, 4]);
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
