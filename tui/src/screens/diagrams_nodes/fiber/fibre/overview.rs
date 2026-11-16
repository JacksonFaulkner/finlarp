// OPTICAL FIBER: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_fibre_overview.py, GLB
// tools/pbr3d/assets/fiber_fibre_overview.glb). Beat 0 is the whole link on its board; beats 1-5 move along it
// (laser end, a magnified slice of the glass, the whole run, the far end); beat 6 is the photodiode, next.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match fiber_fibre_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("OPTICAL FIBER: glass from laser to photodiode", BEAT_MS)
        .note(
            "The optical fibre carries the light from the laser to the photodiode. On a real link it can run for kilometres; here the run is drawn short. Each end of the glass is held in a ceramic ferrule, so it can be lined up with a lens and plugged in.",
            "Left to right on the green board: the steel laser can, a glass lens, the white ferrule assembly with its spring, the blue coated fibre on its clamps, the second ferrule, a lens and the photodiode can. The fibre's core glows end to end; the box above is a magnified slice of the glass.",
        )
        .detail(
            "Light stays trapped in the glass core for kilometres.",
            &["Core ~8.2 µm, cladding 125 µm", "Coating 242 µm", "Single-mode: buildings and beyond"],
        ),
    Beat::new("FERRULE: light enters the core", BEAT_MS)
        .note(
            "A lens focuses the laser's light onto the end of the core, held in the tip of the ferrule. Only light that arrives within the fibre's acceptance angle stays in; the rest is lost, so the laser, lens and core must be lined up precisely.",
            "The laser can on its block, its pale orange beam spreading to the lens on its post, then narrowing to a point on the white ferrule's tip, where the glowing core starts.",
        )
        .detail(
            "Focusing onto an ~8 µm core needs precise alignment.",
            &["Single-mode core ~8.2 µm", "Light must arrive within the acceptance angle"],
        ),
    Beat::new("CORE: total internal reflection", BEAT_MS)
        .note(
            "The cladding round the core has a slightly lower refractive index, so light meeting the boundary at a shallow angle reflects back in completely: total internal reflection. The magnified slice above the run shows it with the core drawn wide so the ray can be seen.",
            "In the magnified slice: the orange ray zig-zags down the pale-blue core, turning back each time it reaches the grey cladding. The white guide lines lead back to the ring on the fibre run.",
        )
        .detail(
            "The index step is only about a third of a percent.",
            &["Core index ~1/3 % above the cladding", "Shallow rays reflect completely"],
        ),
    Beat::new("LOSS: a little per kilometre", BEAT_MS)
        .note(
            "A little light is scattered and absorbed in every kilometre of glass. On Corning's SMF-28 Ultra it is at most 0.32 dB per km at 1310 nm, about 7% of the light, and 0.18 dB at 1550 nm.",
            "In the magnified slice: glowing packets shrink as they run down the core, and small bright sparks fly out of it through the cladding.",
        )
        .detail(
            "Attenuation comes from scattering in the glass itself and residual absorption.",
            &["≤0.32 dB/km at 1310 nm", "≤0.18 dB/km at 1550 nm", "0.32 dB ≈ 7% of the light"],
        ),
    Beat::new("REACH: kilometres, drawn short", BEAT_MS)
        .note(
            "Light runs the whole length, laser to photodiode. A 2 km data-center link loses under 1 dB in the glass, less than its connectors, and light covers about 1 km every 5 microseconds. The run here is drawn short.",
            "The whole link from above: packets of light running the full length of the glowing core, from the left ferrule to the right one.",
        )
        .detail(
            "Inside a building the glass barely matters; the joints do.",
            &["2 km: under 1 dB in the glass", "~5 µs per km"],
        ),
    Beat::new("FERRULE: holds the far end", BEAT_MS)
        .note(
            "At the far end a second ferrule holds the glass end steady. The light leaves the core as a widening cone, and a lens collects it onto the photodiode's window.",
            "The white ferrule's chamfered tip on the left, the pale cone of light leaving the core, the glass lens on its post, and the steel photodiode can on the right.",
        )
        .detail(
            "Any offset at either end loses light.",
            &["Light leaves the far end into the receiver's lens"],
        ),
    Beat::new("PHOTODIODE: light back to current", BEAT_MS)
        .note(
            "Next, the photodiode turns the light back into an electrical current, which runs to an amplifier chip (a TIA) that turns it into a voltage for the DSP.",
            "Light enters the photodiode can; glowing cyan beads ride the arched copper wire from the can to the dark amplifier chip on the board.",
        )
        .detail(
            "Next station: the PHOTODIODE page.",
            &["Light in, current out"],
        ),
];
