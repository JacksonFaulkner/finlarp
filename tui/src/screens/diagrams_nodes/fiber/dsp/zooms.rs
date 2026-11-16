// PAM4 DSP: lettered zoom-ins a-e. Each is one frozen picture of the overview's Blender scene
// (tools/pbr3d/blender/fiber_dsp_zooms.py, GLBs tools/pbr3d/assets/fiber_dsp_zoom_<letter>.glb),
// with the camera held on one subject and one tag, shown for its three beats.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

const BEAT_MS: u64 = 8000;

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_zoom_e.glb"),
        E_B,
    )
}

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "lid and fins",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "the die",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "PAM4 ladder",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "electrical data in",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "heat off the fins",
        build: zoom_e,
    },
];

/// Zoom a: the lid and fins: on, lifting, up.
const A_B: &[Beat] = &[
    Beat::new("PAM4 DSP: the lid", BEAT_MS)
        .note(
            "The lid is a hat-shaped metal cover: a plate over the die and a skirt glued to the substrate's edge on a sealant bead. Fins stand on its plate. It protects the die and is the first step of the heat path.",
            "The package cut open: the grey lid plate across the top, its skirt walls at the edges on the black bead, and the row of fins on top.",
        )
        .detail(
            "The lid carries the die's heat to the fins.",
            &["Hat lid: plate + skirt", "Glued on a sealant bead", "Fins on the plate"],
        ),
    Beat::new("PAM4 DSP: the lid lifts", BEAT_MS)
        .note(
            "Lifting the lid shows what joined it to the die: a thin layer of thermal paste on the die's back, filling the gap so heat can cross into the lid.",
            "The lid and fins rise off the package; the pale paste stays on the dark die, and the black bead marks where the skirt stood.",
        )
        .detail(
            "The paste is the weakest thermal link, so it is kept thin.",
            &["Thermal paste on the die's back", "Fills the gap to the lid", "Sealant bead holds the skirt"],
        ),
    Beat::new("PAM4 DSP: lid up, fins on top", BEAT_MS)
        .note(
            "Up close, the fins are thin plates standing on the lid's plate, with gaps between them for air. The plate spreads the die's heat sideways, and the fins hand it to the air.",
            "The raised lid seen from the side: grey fins in a row on the plate, pale air beads running through the gaps.",
        )
        .detail(
            "More plates, more surface to cool.",
            &["Fins: thin plates, air gaps", "Plate spreads the heat", "Air takes it away"],
        ),
];

/// Zoom b: the die: face down in the package, its floor plan, on its bumps.
const B_B: &[Beat] = &[
    Beat::new("PAM4 DSP: the die", BEAT_MS)
        .note(
            "With the lid raised, the die shows: a slab of silicon sitting face down, its circuits in the metal stack on its underside, against the substrate.",
            "The cut-open package with the lid above: the dark die, its metal stack glowing blue along the bottom of both cut faces.",
        )
        .detail(
            "The die is where all the signal processing happens.",
            &["Die face down (flip-chip)", "Circuits on its underside", "Made at TSMC, 5 nm and 3 nm"],
        ),
    Beat::new("PAM4 DSP: the die's logic", BEAT_MS)
        .note(
            "Face up, the die's floor plan shows: SerDes lanes down both edges, eight to the host and eight to the optics, with the transmit blocks (FEC and PAM4 encoders) and the receive blocks (equaliser and FEC decoder) between them.",
            "A die face up on a grey tray: gold lane tiles down both edges, the back half glowing orange with cyan beads crossing it, the front half glowing blue with orange beads crossing back.",
        )
        .detail(
            "Two directions, each with its own encode or clean-up path.",
            &["8 host + 8 line lanes", "Transmit: PAM4 + FEC encode", "Receive: equaliser + FEC decode"],
        ),
    Beat::new("PAM4 DSP: the die on its substrate", BEAT_MS)
        .note(
            "The die connects to the substrate through C4 bumps: copper pillars with solder caps, set in underfill epoxy. The substrate's copper layers and vias carry each connection down to a ball on the board.",
            "A close-up of the seam: copper pillars with silver caps under the dark die, olive underfill round them, cyan beads climbing the bumps, the brown substrate with its copper vias, silver balls below.",
        )
        .detail(
            "Every signal, and the power, crosses these bumps.",
            &["C4 bumps: pillar + solder cap", "Underfill holds them", "Substrate fans out to the board"],
        ),
];

/// Zoom c: the PAM4 levels on a scope: top, bottom, a middle one.
const C_B: &[Beat] = &[
    Beat::new("PAM4: the top level, 10", BEAT_MS)
        .note(
            "PAM4 uses four voltage levels, each standing for two bits. Ethernet orders them in Gray code, 00, 01, 11, 10 from bottom to top, so a symbol misread as its neighbour costs only one bit. The top level is 10.",
            "A scope with four silver levels; the top one glows gold, with cyan dots running along it.",
        )
        .detail(
            "Gray code limits a near-miss to one wrong bit.",
            &["4 levels, 2 bits per symbol", "Gray order: 00, 01, 11, 10", "Top level: 10"],
        ),
    Beat::new("PAM4: the bottom level, 00", BEAT_MS)
        .note(
            "The bottom level, the lowest voltage, stands for 00. The three levels above it share the same total swing that NRZ uses for just two.",
            "The bottom silver level glows gold, cyan dots running along it.",
        )
        .detail(
            "Same swing as NRZ, split four ways.",
            &["Bottom level: 00", "Same swing as NRZ", "4 levels instead of 2"],
        ),
    Beat::new("PAM4: a middle level, 11", BEAT_MS)
        .note(
            "The middle levels sit between, and here the third one up is 11. Squeezing four levels into the swing leaves each gap a third of NRZ's, about 9.5 dB less signal-to-noise margin.",
            "The third silver level glows gold, cyan dots running along it, its neighbours close above and below.",
        )
        .detail(
            "Close levels are why PAM4 needs equalization and FEC.",
            &["Middle level: 11", "Gap: 1/3 of NRZ's", "~9.5 dB less margin"],
        ),
];

/// Zoom d: electrical data in: the differential pair, symbols riding it, into the die.
const D_B: &[Beat] = &[
    Beat::new("PAM4 DSP: electrical data in", BEAT_MS)
        .note(
            "Each host lane reaches the DSP as a differential pair: two copper traces side by side carrying equal and opposite signals, so noise that hits both cancels. The pair runs from the edge connector to a BGA ball under the package.",
            "Two thin copper traces on the green board, running from a pair of gold vias by the optics to the cut-open package's corner.",
        )
        .detail(
            "Differential pairs let copper run at these speeds.",
            &["One pair per lane", "8 host lanes in an 800G module", "Ends at a BGA ball"],
        ),
    Beat::new("PAM4 DSP: data on the way in", BEAT_MS)
        .note(
            "PAM4 symbols travel down the pair, about 53 billion a second on a 100G lane. The two traces carry mirror-image signals, and the trace and connector have already blurred them.",
            "Orange beads ride both traces side by side toward the package.",
        )
        .detail(
            "Blurred symbols are the DSP's raw material.",
            &["100G lane: 53.125 GBd", "200G lane: 106.25 GBd", "Blurred on the way"],
        ),
    Beat::new("PAM4 DSP: data reaches the package", BEAT_MS)
        .note(
            "At the package the signal climbs a ball and a plated via through the substrate, runs along a copper layer, and goes up a C4 bump into the die's receiver circuits, where it is sampled and equalized.",
            "On the cut face, the via and a substrate layer glow cyan, beads climb them into a bump, and the die's metal stack glows cyan.",
        )
        .detail(
            "Ball, via, layer, bump: a few millimetres from board to die.",
            &["Path: ball, via, bump, die", "Then: sample, equalize, FEC", "Flip-chip keeps it short"],
        ),
];

/// Zoom e: heat off the fins: hot die and lid, rising heat, air through the gaps.
const E_B: &[Beat] = &[
    Beat::new("PAM4 DSP: heat off the fins", BEAT_MS)
        .note(
            "The DSP turns its power into heat in the die. The heat crosses the paste into the lid, spreads through the plate and climbs into the fins, which start to shed it.",
            "The cut-open package glowing orange from the die up through the paste, the lid plate and every fin, with a few puffs above.",
        )
        .detail(
            "The DSP is most of a module's power.",
            &["1.6T, 3 nm DSP: up to ~25 W", "Heat made in the die", "Out through paste, lid, fins"],
        ),
    Beat::new("PAM4 DSP: heat rising", BEAT_MS)
        .note(
            "The fins give the heat a large surface to leave from, and it rises off them into the air.",
            "More orange puffs rising higher off the glowing fins.",
        )
        .detail(
            "More fin surface sheds more heat.",
            &["Fins: more surface", "Heat rises off the tips", "DSP module: ~16-19 pJ/bit (OCP)"],
        ),
    Beat::new("PAM4 DSP: heat into the air", BEAT_MS)
        .note(
            "Fans push air through the fin gaps and carry the heat away. Across tens of thousands of modules in a cluster this adds up, which is why LPO, with no DSP, is attractive at around 6.25 pJ/bit.",
            "Pale air beads run through the gaps between the fins while orange puffs rise high above.",
        )
        .detail(
            "Cutting the DSP cuts most of this heat.",
            &["LPO: ~6.25 pJ/bit (OCP)", "Tens of thousands per cluster", "Air carries the heat away"],
        ),
];
