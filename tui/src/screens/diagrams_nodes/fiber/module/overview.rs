// TRANSCEIVER: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_module_overview.py, GLB
// tools/pbr3d/assets/fiber_module_overview.glb). The link with the module highlighted, then the module in close-up.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match fiber_module_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("TRANSCEIVER: the module in the link", BEAT_MS)
        .note(
            "The transceiver is where a switch's copper turns into light. The switch chip sends eight electrical lanes over the board to a pluggable module at the front panel; the module sends them out as light on fibre to the next switch, and turns the light coming back into lanes.",
            "A switch board: the ASIC under its finned heat sink at right, cyan pulses on the copper traces to the cage, the grey finned module in the cage, and the yellow fibre leaving its front.",
        )
        .detail(
            "Every switch-to-switch link has a module at each end.",
            &["800G: 8 lanes x 100G PAM4", "Board copper, then fibre"],
        ),
    Beat::new("plug in: the module seats", BEAT_MS)
        .note(
            "The module is hot-pluggable: it slides into the cage while the switch runs. The gold fingers on the end of its circuit board lead the way into the connector at the back of the cage, which is its only electrical link to the host.",
            "The finned module sliding in from the left, its blue pull tab trailing, into the cage with the vented far wall.",
        )
        .detail(
            "OSFP: 8 lanes, room for about 25 W, finned shell.",
            &["OSFP connector: 60 contacts", "QSFP-DD: smaller, cooler shell"],
        ),
    Beat::new("TRANSCEIVER: lid off, the optics", BEAT_MS)
        .note(
            "Lift the finned lid and the whole conversion sits on one small board. At the front are the TOSA (transmit optics, eight lasers) and the ROSA (receive optics, eight photodiodes); behind them the laser driver and the TIA; in the middle the PAM4 DSP.",
            "The lid lifts out of view. Two open gold packages at the front (TOSA far, ROSA near), two dark chips behind them, and the tan DSP package mid-board.",
        )
        .detail(
            "Electrical to light and back, on one board.",
            &["TOSA: 8 lasers (DR8)", "ROSA: 8 photodiodes", "DSP retimes the lanes"],
        ),
    Beat::new("light at the front", BEAT_MS)
        .note(
            "The lasers glow and their light runs along eight fibres to the MPO connector at the front, then out along the cable. Light from the far end comes back in on eight more fibres through the same connector to the photodiodes.",
            "Orange light on the yellow cable in both directions, the eight lasers glowing in the far package and the photodiodes lighting in the near one; the black MPO plug in the module's nose.",
        )
        .detail(
            "DR8: one fibre per lane, 16 in one MPO.",
            &["DR8: ~500 m on single-mode", "MPO: 12 or 16 fibres in one plug"],
        ),
    Beat::new("electrical in, electrical out", BEAT_MS)
        .note(
            "The host's lanes enter at the card edge and run to the DSP, which retimes them and passes them to the laser driver; arched gold bond wires carry each lane's drive to its laser. Received lanes come back over bond wires from the photodiodes to the TIA, through the DSP and out of the card edge.",
            "Cyan beads riding the copper traces from the card edge into the DSP, along to the glowing driver and over the arched bond wires to the lasers; others ride back from the photodiodes to the glowing TIA and out.",
        )
        .detail(
            "Both directions run at once, eight lanes each.",
            &["Driver: lanes to laser drive", "TIA: photocurrent to voltage"],
        ),
    Beat::new("fins shed the heat", BEAT_MS)
        .note(
            "The lid comes back down. It is the module's heat sink: the DSP and optics dump their heat into it, and its fins hand it to the air the switch's fans push along the front panel. Listings put 1.6T DSP modules at up to about 25-26 W each.",
            "The finned lid dropping back onto the module, orange heat rising off the fins and pale air running along them.",
        )
        .detail(
            "A 64-port switch's optics can draw over a kilowatt.",
            &["1.6T DSP modules: up to ~25-26 W", "LPO cuts that roughly in half or more"],
        ),
    Beat::new("next: the CPO", BEAT_MS)
        .note(
            "Module power at cluster scale pushes the optics toward the chip. Co-packaged optics (CPO) put optical engines on the switch chip's package itself, so the long copper run and the pluggable module are no longer needed.",
            "The ASIC becomes a CPO package: blue optical engines around the heat-sunk ASIC on a tan substrate, yellow fibre stubs leaving them, while the pluggable still sits at the front.",
        )
        .detail(
            "The next station: optics on the package.",
            &["CPO: optics on the package", "No module, no module DSP"],
        ),
];
