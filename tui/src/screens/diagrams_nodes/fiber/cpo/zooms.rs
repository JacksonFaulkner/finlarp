// CPO: lettered zoom-ins a-e. Each is one frozen state of the overview scene (tools/pbr3d/blender/fiber_cpo_zooms.py,
// GLB tools/pbr3d/assets/fiber_cpo_zoom_<letter>.glb), the camera held on one subject of the CPO package for three beats.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

/// a: the ASIC (the switch chip on the substrate).
const A_B: &[Beat] = &[
    Beat::new("ASIC: the switch chip", BEAT_MS)
        .note(
            "The ASIC is the switch chip itself: it moves packets between ports and makes no light. Its bandwidth leaves through SerDes, the high-speed circuits along its edges. With CPO those edges face optical engines a few millimetres away.",
            "The grey-blue die with its tiled top; the gold band around its edge is the SerDes; the dark rim at its foot is underfill hiding the solder bumps.",
        )
        .detail(
            "Electrical only; the engines make the light.",
            &["SerDes along every edge", "Engines a few mm away"],
        ),
    Beat::new("ELECTRICAL HOP: out of the ASIC", BEAT_MS)
        .note(
            "Data leaves the SerDes edge on a few millimetres of package wiring to the engine's electronic chip. At 200G per lane, a long board trace to a front-panel module would need a DSP to recover the signal; this short hop does not.",
            "Cyan beads ride the copper traces from the gold SerDes edge across the gap to the dark electronic chip.",
        )
        .detail(
            "No DSP between chip and optics.",
            &["A few mm of package wiring", "200G per lane"],
        ),
    Beat::new("SHARED HEAT: the ASIC's heat", BEAT_MS)
        .note(
            "The switch chip is the package's main heat source, and the engines sit right beside it. Their micro-rings drift with temperature, so each needs heater control to stay on the laser's wavelength.",
            "A red-orange glow pulses over the chip; a lighter orange covers the engines around it.",
        )
        .detail(
            "The optics live in the chip's heat.",
            &["Rings drift with temperature", "Heater control per ring"],
        ),
];

/// b: the optical engine (electrical in, light out).
const B_B: &[Beat] = &[
    Beat::new("OPTICAL ENGINE: electrical in, light out", BEAT_MS)
        .note(
            "An optical engine is a photonic chip (waveguides, modulators, photodiodes) with an electronic chip stacked on it that drives the modulators and amplifies what the photodiodes receive. NVIDIA's are made on TSMC's COUPE process, which does that stacking.",
            "The lavender photonic chip with white waveguides, gold rings and small gold photodiode pads; the dark electronic chip on its inner end; the grey V-groove fibre array at its outer edge.",
        )
        .detail(
            "Two chips, one engine.",
            &["PIC + EIC", "TSMC COUPE stacks them"],
        ),
    Beat::new("BEAMS: light into the fibres", BEAT_MS)
        .note(
            "Laser light comes in on two lanes and runs along a bus past the rings. Each ring, a few microns across, is driven with the data and imprints it on the light, which then leaves through the fibre array, one fibre per lane.",
            "The red-pink bus glows along the edge of the chip; the gold rings flash; orange-white beads leave each ring along a waveguide into the fibres.",
        )
        .detail(
            "200 Gb/s per ring on NVIDIA's engines.",
            &["Micro-ring modulators", "One fibre per lane"],
        ),
    Beat::new("ELECTRICAL DATA: in from the ASIC", BEAT_MS)
        .note(
            "The engine's data arrives from the switch chip over a few millimetres of package wiring, into the electronic chip that drives the rings.",
            "Cyan beads ride the copper traces from the chip's gold SerDes edge into the dark electronic chip.",
        )
        .detail(
            "The driver sits right over the optics.",
            &["A few mm of wiring", "Electronic chip drives the rings"],
        ),
];

/// c: the fibre ports at the engine edge, and the light going into and out of them.
const C_B: &[Beat] = &[
    Beat::new("FIBRE PORTS: the fibre array", BEAT_MS)
        .note(
            "Light gets on and off the photonic chip through a fibre array: fibres laid in V-shaped grooves in a block, clamped by a glass lid and fixed to the chip's edge. Attaching fibres like this to a package at scale, with low loss, is a new manufacturing step for switch makers.",
            "The grey block with its row of V-grooves, a clear glass lid over it, and one glass fibre in each groove, butted against the lavender chip.",
        )
        .detail(
            "A known CPO chokepoint.",
            &["Fibre attach at scale", "Low loss required"],
        ),
    Beat::new("BITS TO LIGHT: into the fibres", BEAT_MS)
        .note(
            "Modulated light leaves the rings and enters the fibres, one lane per fibre. The two outer fibres run the other way: they bring steady light in from the external laser.",
            "Orange-white beads run from the chip into the middle fibres; the two outer fibres glow steady red-pink.",
        )
        .detail(
            "Laser in, data out, on the same array.",
            &["Data lanes out", "Laser lanes in"],
        ),
    Beat::new("LIGHT RUNS OUT ALONG THE RIBBON", BEAT_MS)
        .note(
            "The light runs on along the fibre ribbon, over the substrate edge, toward the connector on the board. It is light in glass from here to the next switch.",
            "Orange-white beads ride along the pale ribbon toward the aqua connector.",
        )
        .detail(
            "No electronics in the path.",
            &["Glass only from here", "Ribbon to the connector"],
        ),
];

/// d: the passive connector at the end of the ribbon.
const D_B: &[Beat] = &[
    Beat::new("PASSIVE CONNECTOR: no electronics in the plug", BEAT_MS)
        .note(
            "The ribbon ends in a connector on the board, and a cable connector clips onto it. It is glass and alignment only: no laser, no DSP, no power. In a pluggable switch, this is where a powered module would sit.",
            "The aqua connector on the green board with the black cable connector clipped on, and the aqua cable leaving it.",
        )
        .detail(
            "The optics stay on the package.",
            &["No electronics in the plug", "Cable clips on"],
        ),
    Beat::new("LIGHT LEAVES THE CONNECTOR", BEAT_MS)
        .note(
            "The light passes straight through the connector into the cable, with no conversion, and runs on to the front panel.",
            "Orange-white beads run along the ribbon, through the connectors and along the top of the aqua cable.",
        )
        .detail(
            "Nothing in the plug converts the light.",
            &["Straight through", "On to the front panel"],
        ),
    Beat::new("NEXT: the cable carries on", BEAT_MS)
        .note(
            "At the front panel the light leaves on a fibre cable toward the next switch. The panel also holds the external laser that feeds the engines.",
            "Bright beads ride the aqua cable out of the steel panel to the right; the finned laser module sits in the panel beside it.",
        )
        .detail(
            "The link goes on as light.",
            &["Out of the front panel", "External laser beside it"],
        ),
];

/// e: the substrate, the base the chip and engines sit on.
const E_B: &[Beat] = &[
    Beat::new("SUBSTRATE: one base for the chip and engines", BEAT_MS)
        .note(
            "Everything sits on one organic package substrate: a stiff core with thin layers of insulator and copper on both sides, joined by plated vias, and solder balls underneath that connect it to the board.",
            "A corner of the substrate: the striped edge of tan insulator and copper planes around a greenish core, brown via barrels, and silver balls on the green board.",
        )
        .detail(
            "The chip and its optics share this base.",
            &["Copper layers + core", "Solder balls to the board"],
        ),
    Beat::new("SHARED HEAT: the substrate carries it", BEAT_MS)
        .note(
            "The switch chip's heat spreads through the substrate into the engines beside it. That is why the rings need heater control, and why the lasers are kept out at the panel.",
            "A red-orange glow pulses over the chip; a lighter orange covers the eight engines on the substrate.",
        )
        .detail(
            "One package, one heat problem.",
            &["Rings need heater control", "Lasers kept at the panel"],
        ),
    Beat::new("ELECTRICAL HOP: across the substrate", BEAT_MS)
        .note(
            "The substrate also carries the hop: a few millimetres of copper from the chip's SerDes edge to each engine.",
            "Cyan beads ride the copper traces on the substrate between the gold SerDes edge and the dark electronic chip.",
        )
        .detail(
            "Short copper, no DSP.",
            &["A few mm of wiring", "No DSP in the path"],
        ),
];

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_zoom_e.glb"),
        E_B,
    )
}

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the ASIC",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "the optical engine",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "the fibre ports",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "the passive connector",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "the substrate",
        build: zoom_e,
    },
];
