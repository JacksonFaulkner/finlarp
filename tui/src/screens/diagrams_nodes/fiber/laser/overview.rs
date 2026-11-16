// LASER: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_laser_overview.py, GLB
// tools/pbr3d/assets/fiber_laser_overview.glb). Beat 0 is the whole link with the laser highlighted;
// beats 1 to 5 are a detailed cut-away of the TO-can, driver, lens and ferrule; beat 6 follows the light down the fibre.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match fiber_laser_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("LASER: bits to light", BEAT_MS)
        .note(
            "The laser is where the link's signal stops being electrical and becomes light. It sits between the PAM4 DSP, which makes the symbols, and the optical fiber, which carries them away. In a single-mode module the light source is usually an EML: a DFB laser plus a modulator on one indium phosphide (InP) chip.",
            "The green board with the finned PAM4 DSP at the left, the small silver laser can next to it (highlighted), and the glass fibre running on to the right. Blue dots run along the copper trace from the DSP.",
        )
        .detail(
            "From the laser on, the signal is light.",
            &["EML: DFB laser + modulator, one InP chip", "1310 nm (O-band) for single-mode", "EMLs: Lumentum (LITE), Coherent (COHR), others"],
        ),
    Beat::new("LASER: a TO-can package", BEAT_MS)
        .note(
            "Inside, the laser chip sits on a ceramic submount on a heat-sink post, sealed in a metal can with a glass window at the front. Gold pins pass through glass seals in the gold header and run back to the laser driver IC; hair-thin bond wires join them to the chip. A monitor photodiode stands behind the chip.",
            "The can cut open: the gold header at the left with pins through it, the bronze post and white submount, the small layered chip with its glowing stripe and gold pads, the dark monitor photodiode behind it, the grey cap arching over, and the window in the cap's right end. The black driver IC stands at the far left.",
        )
        .detail(
            "Every part inside carries current in, light out, or heat away.",
            &["Chip on AlN submount, on a post", "Glass-sealed pins to the driver", "Sealed can, glass window"],
        ),
    Beat::new("LASER: bits to light", BEAT_MS)
        .note(
            "The driver receives the DSP's PAM4 symbols. It feeds the DFB section a steady bias current and puts the data on the modulator section as a voltage; the modulator absorbs part of the light, so what leaves the chip steps through four brightness levels, one per symbol.",
            "Blue dots (bias) run from the driver along the upper pin and over a bond wire into the chip's left pad; pink dots (data) run along the lower pin and the long wire to the right pad. The glow at the chip's front end grows and shrinks through four sizes.",
        )
        .detail(
            "PAM4 carries two bits per symbol.",
            &["Bias: steady, into the DFB", "Data: a voltage on the modulator", "Four light levels: two bits per symbol"],
        ),
    Beat::new("LASER: the beam leaves the window", BEAT_MS)
        .note(
            "The beam leaves the chip spreading out, crosses the can's window, and fills a lens. The lens focuses it back down onto the end of the fibre, held in a ceramic ferrule inside a gold sleeve.",
            "An orange cone widens from the chip through the window into the clear lens on its post, then narrows into the white ferrule at the right; a dot of light runs all the way along it and the fibre's core lights up.",
        )
        .detail(
            "The beam is drawn orange; datacom lasers emit infrared.",
            &["Lens focuses the beam onto the fibre", "Drawn orange; real light is infrared (1310 nm)"],
        ),
    Beat::new("LASER: power held steady", BEAT_MS)
        .note(
            "A little light leaks from the chip's back facet onto the monitor photodiode, which turns it into a current. That current runs back up its own pin to the driver, and the driver adjusts the bias to keep the laser's power steady as it warms and ages.",
            "A small orange cone from the chip's back end lights the blue face of the monitor photodiode; blue dots climb its bond wire and run back along the top pin to the driver, while bias dots keep flowing in.",
        )
        .detail(
            "Feedback keeps the power steady as the chip warms and cools.",
            &["Monitor photodiode on the back facet", "Closed loop: automatic power control"],
        ),
    Beat::new("LASER: coupling into the fibre", BEAT_MS)
        .note(
            "The beam has to land in a single-mode core only about 9 um across, so the lens, ferrule and laser must line up to around a micrometre. Light that misses the core is lost.",
            "Close in at the ferrule: the lens's cone and four bright rays converge on the end of the fibre in the white ferrule, and light runs on down the lit core.",
        )
        .detail(
            "Alignment is what makes this hard to build.",
            &["Single-mode core: about 9 um", "Aligned to ~1 um (estimate)"],
        ),
    Beat::new("LASER: out along the fibre", BEAT_MS)
        .note(
            "Back on the board, the light now runs down the glass fibre from the laser to the photodiode, which turns it back into current at the far end.",
            "The fibre's core glows from the laser can to the photodiode can, with a dot of light travelling along it.",
        )
        .detail(
            "Glass carries the light; loss sets the reach.",
            &["Single-mode fibre: ~0.3 dB/km at 1310 nm", "Next: OPTICAL FIBER, then PHOTODIODE"],
        ),
];
