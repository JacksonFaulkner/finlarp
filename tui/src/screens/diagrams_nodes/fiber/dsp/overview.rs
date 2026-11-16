// PAM4 DSP: the page's overview, a Blender scene (tools/pbr3d/blender/fiber_dsp_overview.py, GLB
// tools/pbr3d/assets/fiber_dsp_overview.glb). The whole link with the DSP lit, then the DSP's package
// and behaviour, then the signal going on to the laser. Seven beats, one 8 s beat each.

use super::super::super::blender::Cell;
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(super::super::super::blender::Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step of the DSP's story (match fiber_dsp_overview.py's beats).
const BEATS: &[Beat] = &[
    Beat::new("PAM4 DSP: the link's first station", BEAT_MS)
        .note(
            "This is an optical module with its shell cut away. Data from the host chip (a GPU or switch) comes in through the gold edge connector and meets the PAM4 DSP first. The DSP cleans every bit going in and out of the module; after it come the laser, the fibre and, on the way back, the photodiode.",
            "The cut-away module on the bench: the gold frame on the board marks the finned DSP package. The driver, laser and photodiode cans sit to its right, the fibres run out to the receptacle, and a scope stands at the left.",
        )
        .detail(
            "Every bit in and out of the module passes through this chip.",
            &["8 SerDes lanes from the host", "100G lane: 53.125 GBd PAM4", "Next stations: laser, fibre, photodiode"],
        ),
    Beat::new("PAM4 DSP: electrical data in", BEAT_MS)
        .note(
            "The host sends data to the module over copper, eight SerDes lanes side by side. Each lane carries PAM4 symbols, and by the time they reach the module the trace and connector have blurred them.",
            "Orange beads ride all eight copper lanes from the gold fingers to the package, over a faint orange glow.",
        )
        .detail(
            "The DSP's first job is to undo that blur.",
            &["8 lanes x 100G = 800G", "200G lanes: 106.25 GBd", "Blurred by the trace and connector"],
        ),
    Beat::new("PAM4 DSP: inside the package", BEAT_MS)
        .note(
            "The finned lid lifts off. Underneath, the die sits face down on C4 solder bumps (flip-chip), with thermal paste on its back to carry heat into the lid. The die holds the SerDes, the equaliser and the FEC logic.",
            "The grey lid and fins rise; on the cut faces the dark die with its purple metal stack underneath, the pale paste on top, and the bumps and brown substrate below.",
        )
        .detail(
            "Flip-chip gives every pad a short path straight down.",
            &["Die face down on C4 bumps", "Paste carries heat to the lid", "Made at TSMC, 5 nm and 3 nm"],
        ),
    Beat::new("PAM4: two bits, four levels", BEAT_MS)
        .note(
            "A scope probing a host lane shows what PAM4 is: four voltage levels, two bits per symbol, doubling the data over NRZ at the same baud rate. The cost: the gap between levels is a third of NRZ's, so noise matters more.",
            "The scope at the left: a cyan trace steps between four silver levels one symbol at a time, a gold dot riding it. Cyan beads run up the arched probe lead from the lane.",
        )
        .detail(
            "Two bits a symbol is why the DSP is needed at all.",
            &["PAM4: 4 levels, 2 bits per symbol", "Gap: 1/3 of NRZ's", "~9.5 dB of SNR penalty"],
        ),
    Beat::new("PAM4 DSP: clean symbols", BEAT_MS)
        .note(
            "The lid drops back. Blurred symbols come in, the DSP samples them, equalization separates the levels again, and FEC checks the data. Clean symbols leave down a bump, a via and a ball, then along the board to the laser driver.",
            "Orange beads on the host lanes; the die's metal stack glows cyan; cyan beads run down the package's cut face and along the board to the driver's bond wires.",
        )
        .detail(
            "Equalize, check FEC, resend clean: a retimer.",
            &["Equalization undoes the blur", "KP4 FEC: RS(544,514), ~5% overhead", "Raw ~2 errors in 10,000 fixed"],
        ),
    Beat::new("PAM4 DSP: heat off the fins", BEAT_MS)
        .note(
            "All that processing costs power, and nearly all of it leaves as heat. The DSP is most of a module's power: a 1.6T module with a 3 nm DSP is listed at up to about 25 W.",
            "The cut die and paste glow orange, and orange puffs rise off the lid's fins.",
        )
        .detail(
            "This heat is why LPO (no DSP) is attractive.",
            &["1.6T, 3 nm DSP: up to ~25 W", "DSP module: ~16-19 pJ/bit (OCP)", "LPO: ~6.25 pJ/bit"],
        ),
    Beat::new("PAM4 DSP: next, the laser", BEAT_MS)
        .note(
            "The clean symbols run to the laser driver, which turns each into a current for the laser. They cross the driver's die over its gold bond wires, then up the laser's pin and over its bond wire onto the laser chip, which turns them into light in the fibre.",
            "Cyan beads ride the arched gold bond wires in the cut-open black driver, then along the board, up the laser's pin and over its wire; the laser chip lights orange and pulses slide down the fibre.",
        )
        .detail(
            "From the laser on, the signal is light.",
            &["Driver: symbol to laser current", "Then the laser, then the fibre", "Far end: a DSP in reverse"],
        ),
];
