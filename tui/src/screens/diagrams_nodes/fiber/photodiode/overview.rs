// PHOTODIODE: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_photodiode_overview.py, GLB
// tools/pbr3d/assets/fiber_photodiode_overview.glb). A close-up of the photodiode station: the whole link with
// the station lit, then the can (sealed, then cut open), the light in, the current out, and the pull-back.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match fiber_photodiode_overview.py's beats).
const BEATS: &[Beat] = &[
    Beat::new("PHOTODIODE: light back into current", BEAT_MS)
        .note(
            "The photodiode sits at the receive end of the fibre and turns light back into electricity. Light from the laser crosses the fibre, lands on the photodiode, and becomes a current that rises and falls with the light's PAM4 levels. A TIA beside it turns that current into a voltage for the DSP.",
            "The whole link on its green board: PAM4 DSP, laser can, the fibre with light running down it, the photodiode's can in a glowing outline, the finned transceiver, the CPO package.",
        )
        .detail(
            "The receive end of every optical link.",
            &["Light -> current -> voltage", "PIN photodiode, InGaAs absorber"],
        ),
    Beat::new("PHOTODIODE: light lands at the lens", BEAT_MS)
        .note(
            "Light leaves the fibre's end as a widening cone and crosses a small air gap to the TO-can. The only way in is a glass ball lens in the can's cap, which catches the cone and focuses it onto the chip inside.",
            "The gold ferrule on its mount, orange photons crossing the gap, the clear ball lens in the face of the steel can.",
        )
        .detail(
            "The chip is tiny; the lens is what lets the light hit it.",
            &["TO-can: steel cap, ball lens, header", "Drawn about 16x life size"],
        ),
    Beat::new("PHOTODIODE: the chip absorbs", BEAT_MS)
        .note(
            "Cut open, the can shows the chip: a PIN stack of p-type InP, an undoped InGaAs absorber and n-type InP. Photons are absorbed in the InGaAs; each frees an electron and a hole, and the reverse bias sweeps them to opposite contacts.",
            "The focused orange cone on the chip; white flashes in the yellow InGaAs; violet holes drift to the pink p side, cyan electrons to the blue n side.",
        )
        .detail(
            "InGaAs absorbs 1310 and 1550 nm, which silicon can't.",
            &["p / intrinsic InGaAs / n", "One photon -> one electron-hole pair"],
        ),
    Beat::new("PHOTODIODE: current out, voltage on", BEAT_MS)
        .note(
            "The current leaves the chip's gold contact ring up a hair-thin gold bond wire into the TIA right beside it. The TIA turns it into a voltage, which runs down a second bond wire to a pin post and out the OUT pin.",
            "Cyan beads run up the arched gold bond wire into the dark TIA; amber beads leave it on the second wire and run out along the gold OUT pin.",
        )
        .detail(
            "The shortest wire sits at the most sensitive point.",
            &["Photocurrent: microamps", "TIA: current in, voltage out"],
        ),
    Beat::new("PHOTODIODE: more light, more current", BEAT_MS)
        .note(
            "A bright burst of light frees many pairs and gives a big current; a dim burst gives a small one. Responsivity close to 1 A/W means a milliwatt of light gives about a milliamp, so the current is a copy of the light's power.",
            "A dense burst of photons into the can, then a sparse one; big amber beads run out the OUT pin and down the board trace, then small ones.",
        )
        .detail(
            "The light's level is the signal.",
            &["~1 A/W: 1 mW -> ~1 mA (InGaAs)", "Current tracks light power"],
        ),
    Beat::new("PHOTODIODE: the pulse follows", BEAT_MS)
        .note(
            "A short light pulse makes a short current pulse right after it. To follow 106 GBd symbols the photodiode must be tiny, so its capacitance is small, and the TIA must be just as fast.",
            "Two short bursts of photons into the can; a train of amber beads leaves the OUT pin after each.",
        )
        .detail(
            "Same timing in, same timing out.",
            &["106 GBd symbols", "Smaller diode = faster, harder to hit"],
        ),
    Beat::new("PHOTODIODE: on to the transceiver", BEAT_MS)
        .note(
            "The voltage leaves the pins through a flex circuit, runs along a copper trace on the board and into the transceiver's cage, where the DSP equalizes it and decides each PAM4 level.",
            "Pulled back: the sealed can on its mount, the orange flex behind its pins, amber beads running along the copper trace into the finned transceiver in its cage.",
        )
        .detail(
            "Next stop: the DSP, then the switch.",
            &["Next node: the TRANSCEIVER", "DSP decides each PAM4 level"],
        ),
];
