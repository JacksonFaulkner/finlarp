// PHOTODIODE: lettered zoom-ins a-e. Each is one frozen state of the overview scene
// (tools/pbr3d/blender/fiber_photodiode_zooms.py), with the camera held on one subject and one tag,
// shown for its three beats. a window, b chip, c pins, d current path, e module cage.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_photodiode_zoom_e.glb"),
        E_B,
    )
}

/// a window: the ball lens in the can's cap, light from the fibre; a bright burst; two pulses.
const A_B: &[Beat] = &[
    Beat::new("WINDOW: the ball lens", BEAT_MS)
        .note(
            "The TO-can's only opening is a small glass ball lens in its cap, facing the fibre's end across an air gap. Light leaving the fibre spreads as a cone; the lens catches it and bends it back toward the chip.",
            "The gold ferrule at left, orange photons crossing the gap, the clear ball lens set in the steel cap.",
        )
        .detail(
            "Everything the photodiode sees comes through here.",
            &["Ball lens: glass or sapphire, ~1-2 mm (typical)", "Light spreads from the fibre as a cone"],
        ),
    Beat::new("WINDOW: a bright burst", BEAT_MS)
        .note(
            "A bright burst sends many photons through the lens at once. The lens folds the whole cone down to a small spot on the chip's window, so a brighter burst means more photons in that spot.",
            "The can cut open: a dense stream of photons through the orange cone, which narrows from the lens onto the chip at right.",
        )
        .detail(
            "More light in, more current out.",
            &["Responsivity close to 1 A/W (InGaAs)"],
        ),
    Beat::new("WINDOW: pulse, gap, pulse", BEAT_MS)
        .note(
            "Data arrives as pulses of light, one per symbol. Between pulses the cone goes nearly dark; each pulse crosses the lens and lands on the chip a moment later.",
            "Two short groups of photons cross the gap and the lens, with a quiet spell between them.",
        )
        .detail(
            "The light's timing is the data's timing.",
            &["PAM4: 4 light levels, 2 bits per symbol"],
        ),
];

/// b chip: the PIN chip in the open can; pairs freed in the InGaAs; current leaving up the bond wire.
const B_B: &[Beat] = &[
    Beat::new("CHIP: a PIN layer stack", BEAT_MS)
        .note(
            "The chip is a PIN photodiode: p-type InP on top, an undoped (intrinsic) InGaAs absorber in the middle, n-type InP below, on an InP substrate and a white ceramic submount. A gold ring on top is the p contact; the light enters through its middle.",
            "The cut face: pink p-InP, yellow InGaAs, blue n-InP, grey substrate; the gold ring at left with the orange cone ending in it.",
        )
        .detail(
            "Real layers are only microns thick.",
            &["InGaAs absorbs 1310 and 1550 nm", "Grown on an InP chip"],
        ),
    Beat::new("CHIP: one photon, one pair", BEAT_MS)
        .note(
            "Each absorbed photon frees one electron and one hole in the InGaAs. The reverse bias sweeps them apart: electrons to the n side, holes to the p side. That flow is the photocurrent.",
            "White flashes in the yellow layer; violet holes drift left to the pink layer, cyan electrons right into the blue layer and down to the gold n pad.",
        )
        .detail(
            "Silicon can't do this at 1310 nm: it is transparent past ~1.1 um.",
            &["One photon -> one electron-hole pair", "Reverse bias sweeps them apart"],
        ),
    Beat::new("CHIP: the current leaves", BEAT_MS)
        .note(
            "The current leaves the chip through its contacts and runs up a hair-thin gold bond wire into the TIA beside it.",
            "Cyan beads run up the arched gold bond wire from the chip's ring to the dark TIA above; amber beads leave on the TIA's second wire.",
        )
        .detail(
            "Short wires keep the signal fast and quiet.",
            &["Photocurrent: microamps", "TIA: current in, voltage out"],
        ),
];

/// c pins: the header's four pins; the voltage out; a bright burst; on to the board.
const C_B: &[Beat] = &[
    Beat::new("PINS: voltage out", BEAT_MS)
        .note(
            "Four gold pins pass through the can's header in glass seals: power for the TIA, bias for the photodiode, ground and the output. The TIA's voltage leaves on the OUT pin.",
            "The header from the side, the four gold pins running to the orange flex; amber beads run out along the top pin.",
        )
        .detail(
            "The pins are the can's only electrical path.",
            &["PIN-TIA can: 4-5 pins (typical)", "Glass seals keep the can airtight"],
        ),
    Beat::new("PINS: a bright burst", BEAT_MS)
        .note(
            "A bright burst of light gives a big current and so a big voltage on the OUT pin; a dim burst after it gives a small one.",
            "Big amber beads run out along the OUT pin and down the flex, then small ones.",
        )
        .detail(
            "Output level follows light level.",
            &["~1 A/W: 1 mW -> ~1 mA"],
        ),
    Beat::new("PINS: on to the board", BEAT_MS)
        .note(
            "The pins solder into a flex circuit that carries the signal down to the board, where a copper trace leads to the transceiver.",
            "The sealed can from behind; amber beads leave the OUT pin, drop down the flex and run along the board.",
        )
        .detail(
            "Flex absorbs the mechanical tolerance.",
            &["Flex: polyimide with copper traces"],
        ),
];

/// d current path: OUT pin, flex, board trace toward the transceiver's cage.
const D_B: &[Beat] = &[
    Beat::new("CURRENT PATH: a bright burst", BEAT_MS)
        .note(
            "The signal runs out of the OUT pin, down the flex and along a copper trace on the board. A bright burst shows up as a big signal along the whole path.",
            "Big amber beads leave the can's top pin, drop down the orange flex and run along the copper trace toward the cage at right.",
        )
        .detail(
            "A short, controlled-impedance path.",
            &["Trace: ~100 Ohm differential (typical)"],
        ),
    Beat::new("CURRENT PATH: bright, then dim", BEAT_MS)
        .note(
            "Every burst takes this same path; a dim burst follows the bright one as a smaller signal.",
            "Big beads, then small beads, along the same pin, flex and trace.",
        )
        .detail(
            "The path doesn't change; the level does.",
            &["Level carries the PAM4 symbol"],
        ),
    Beat::new("CURRENT PATH: into the cage", BEAT_MS)
        .note(
            "The trace runs under the transceiver's cage, where the DSP equalizes the signal and decides each PAM4 level.",
            "A steady stream of amber beads along the trace into the cage at right.",
        )
        .detail(
            "Next: the DSP decides the levels.",
            &["DSP decides each PAM4 level"],
        ),
];

/// e module cage: the transceiver in its cage at the board edge, the trace running in.
const E_B: &[Beat] = &[
    Beat::new("TRANSCEIVER: the cage", BEAT_MS)
        .note(
            "The signal from the photodiode runs along the board into a metal cage at the board's edge, which holds a pluggable transceiver module.",
            "The grey cage on the green board; the photodiode can, flex and trace at left, amber beads running in.",
        )
        .detail(
            "The cage is the socket for a pluggable.",
            &["Pluggables: QSFP-DD, OSFP"],
        ),
    Beat::new("TRANSCEIVER: the module in its cage", BEAT_MS)
        .note(
            "A finned module slides into the cage; the fins carry its heat away. Inside it sit the optics and the DSP; its gold card edge plugs into the switch.",
            "The finned housing on top of the cage, the trace running in under it.",
        )
        .detail(
            "Optics, DSP and card edge in one box.",
            &["800G module: 8 lanes x 100G"],
        ),
    Beat::new("TRANSCEIVER: most of the volume", BEAT_MS)
        .note(
            "Pluggable modules are the usual way to put optics on a switch, so module makers ship most of the volume.",
            "The same cage and module, the signal still flowing in.",
        )
        .detail(
            "Module makers ship most of the volume.",
            &["Innolight, Eoptolink, Coherent"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "window",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "chip",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "pins",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "current path",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "module cage",
        build: zoom_e,
    },
];
