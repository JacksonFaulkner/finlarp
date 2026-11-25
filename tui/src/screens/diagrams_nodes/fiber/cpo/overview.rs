// CPO: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_cpo_overview.py, GLB
// tools/pbr3d/assets/fiber_cpo_overview.glb). The CPO switch package: the switch chip and eight optical
// engines on one substrate, fibre out through passive connectors to the front panel, and the external
// laser at the panel. Beat 0 shows the whole link for context.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_cpo_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match fiber_cpo_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("CPO: optics on the chip package", BEAT_MS)
        .note(
            "This is the whole link from the earlier pages, left to right: the PAM4 DSP, the laser, the fibre, the photodiode and a pluggable transceiver. Co-packaged optics (CPO) is the last station, and it changes where the optics live: instead of a module at the front panel, optical engines sit on the switch chip's own package.",
            "The five earlier stations along the green board at the left; the CPO package at the right, outlined in cyan, with its eight engines and pale fibre ribbons.",
        )
        .detail(
            "It removes the long copper run to the panel.",
            &["Engines on the switch package", "Light leaves the package in fibre"],
        ),
    Beat::new("the package: switch chip and engines on one substrate", BEAT_MS)
        .note(
            "The switch chip sits in the middle of the package. Around it are optical engines, each a silicon-photonics chip with its driver chip on top, millimetres from the switch chip. Fibre runs from each engine to a connector on the board.",
            "The grey-blue tiled switch chip in the centre of the brown-grey substrate; eight lavender engines around it, two per side; pale fibre ribbons out to aqua connectors.",
        )
        .detail(
            "Millimetres from the chip, not tens of centimetres.",
            &["Engine = photonic chip + electronic chip", "Eight engines drawn around one chip"],
        ),
    Beat::new("ELECTRICAL HOP: a few millimetres", BEAT_MS)
        .note(
            "The switch chip's SerDes drives only a few millimetres of package wiring to reach the engine's electronic chip. In a pluggable switch the same signal would cross tens of centimetres of board, which at 200G per lane needs a DSP in every module to recover it.",
            "From above: cyan beads ride the copper traces between the chip's gold SerDes edge and the dark electronic chip, outward on some lanes and back on others.",
        )
        .detail(
            "Short copper is the point of CPO.",
            &["A few mm of package wiring", "Pluggable: tens of cm and a DSP"],
        ),
    Beat::new("OPTICAL ENGINE: bits to light", BEAT_MS)
        .note(
            "Steady light arrives from the external laser on fibre. The electronic chip drives micro-ring modulators, rings a few microns across that pass light only at their resonant wavelength; the drive voltage shifts that resonance and imprints the data on the light. NVIDIA's engines use 200 Gb/s rings on TSMC's COUPE process. Receive runs the other way: light from the far switch lands on germanium photodiodes, and the electronic chip amplifies the photocurrent back into electrical lanes.",
            "Red-pink beads ride in on the arched laser fibres and glow along the bus on the lavender photonic chip. The gold rings flash, and orange-white beads leave them into the fibre array; on the receive lanes, beads arrive from the fibres, stop at the gold photodiode pads and turn into cyan electrons heading to the dark electronic chip.",
        )
        .detail(
            "Rings are tiny and efficient but need heater control.",
            &["200 Gb/s micro-ring modulators", "TSMC COUPE: EIC stacked on PIC"],
        ),
    Beat::new("PASSIVE CONNECTOR: fibre leaves the edge", BEAT_MS)
        .note(
            "The light runs along the fibre ribbon to a connector on the board, then on a cable to the front panel. The connector is only glass and alignment, with no electronics, so the light passes straight through.",
            "Orange-white beads run along the pale ribbon, through the aqua connector and the black cable connector, and along the aqua cable to the adapter in the steel panel.",
        )
        .detail(
            "Fibre attach at scale is one of CPO's new manufacturing steps.",
            &["Connector: glass and alignment only", "Cable to the front panel"],
        ),
    Beat::new("SHARED HEAT: optics beside the chip", BEAT_MS)
        .note(
            "The engines sit right beside the hottest chip in the switch. Rings drift with temperature, so each needs heater control. The lasers, which fail more often than silicon and run best cool, stay out at the panel. A failed engine, though, means replacing the whole switch board.",
            "A red-orange glow pulses on the switch chip's lid; orange heat beads spread outward through the substrate on all four sides, and the electronic chips of all eight engines warm.",
        )
        .detail(
            "Serviceability is the main trade-off.",
            &["Rings need heater control", "Failed engine = whole switch board"],
        ),
    Beat::new("NEXT: light leaves on fibre", BEAT_MS)
        .note(
            "The light leaves the front panel on a fibre cable toward the next switch, where photodiodes turn it back into current. NVIDIA says its photonics switches cut power 3.5x versus pluggable transceivers.",
            "Bright beads ride the aqua cable out of the steel panel and off to the right; the external laser module sits in the panel beside it.",
        )
        .detail(
            "Power per port is the reason for CPO.",
            &["NVIDIA: 3.5x lower power (claimed)", "1.6T port: ~9 W vs ~25 W (one report)"],
        ),
];
