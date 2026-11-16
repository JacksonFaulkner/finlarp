// LASER: lettered zoom-ins a-e. Each is the overview's scene with the camera held on one subject
// (tools/pbr3d/blender/fiber_laser_zooms.py, GLBs in tools/pbr3d/assets/fiber_laser_zoom_<letter>.glb):
// a the TO-can, b the chip and facet, c the monitor photodiode, d the window and pigtail, e the fibre core.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_laser_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the can and its parts", BEAT_MS)
        .note(
            "The TO-can is the laser's package: a gold-plated header with pins sealed through it in glass, a heat-sink post carrying the chip, and a steel cap welded on with a glass window. The weld keeps the chip in dry gas, away from moisture.",
            "The can cut open: the gold header at the left with glass rings round the pins, the bronze heat-sink post, the small chip on top, and the grey cap arching over to the window.",
        )
        .detail(
            "The can holds the chip in line with the lens and fibre.",
            &["TO-can: welded, hermetic", "Pins sealed in glass"],
        ),
    Beat::new("the facet glows at the chip", BEAT_MS)
        .note(
            "Inside, gold bond wires run from the pin tips to the chip's pads. With the driver's bias and data flowing, the chip's stripe lases and the light at its front facet steps through four brightness levels.",
            "Closer in: the arched gold wires from the pins, the cut-open chip on its white submount with its stripe lit, and the glow at its right end.",
        )
        .detail(
            "PAM4 carries two bits per symbol.",
            &["Four light levels: two bits per symbol"],
        ),
    Beat::new("the beam leaves through the window", BEAT_MS)
        .note(
            "The beam spreads as it leaves the chip, crosses the can's glass window and heads for the lens outside.",
            "An orange cone widens from the chip's front end through the window in the cap, toward the lens on its post.",
        )
        .detail(
            "The beam is drawn orange; datacom lasers emit infrared.",
            &["Drawn orange; real light is 1310 nm infrared"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("the chip sits on its submount", BEAT_MS)
        .note(
            "The laser chip is a sliver of indium phosphide on a white AlN ceramic submount, cut open here to show its layers. It is an EML: a DFB laser section and a modulator section side by side, each with its own gold pad.",
            "The cut chip: dark InP bulk, the thin pink light layer with cyan grating teeth above it, the green modulator band at the right, two gold pads on top, and the white submount below.",
        )
        .detail(
            "The facet is where the light leaves the chip.",
            &["InP EML: DFB laser + modulator", "AlN submount carries heat away"],
        ),
    Beat::new("the top level: the facet glows widest", BEAT_MS)
        .note(
            "The DFB section runs steadily. When the symbol calls for the top PAM4 level, the modulator lets almost all of the light through and the front facet glows at its brightest.",
            "The stripe lit along the chip and the largest glow at its right end.",
        )
        .detail(
            "PAM4 carries two bits per symbol.",
            &["Top level: modulator nearly clear"],
        ),
    Beat::new("the bottom level: the facet glows smallest", BEAT_MS)
        .note(
            "For the bottom level the modulator section absorbs most of the light, so the glow at the facet shrinks to its smallest. The laser itself stays on throughout; only the modulator changes.",
            "The same chip with the smallest glow at its right end, under the modulator's gold pad.",
        )
        .detail(
            "Switching outside the laser keeps the light clean.",
            &["Bottom level: modulator absorbs most", "The DFB stays on"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("the monitor photodiode behind the chip", BEAT_MS)
        .note(
            "A monitor photodiode stands on the submount right behind the laser chip, its blue active face turned toward the chip's back facet.",
            "The dark upright block at the chip's left end, with its blue face toward the chip and a gold wire leaving its top.",
        )
        .detail(
            "The monitor reads the light that leaves the back facet.",
            &["Monitor photodiode on the back facet"],
        ),
    Beat::new("it reads back light", BEAT_MS)
        .note(
            "The back facet's mirror lets a little light through. It lands on the monitor, which turns it into a small current that tracks the laser's output; the current climbs the bond wire to the monitor's own pin.",
            "A small orange cone from the chip's back end lights the blue face; blue dots climb the gold wire to the top pin.",
        )
        .detail(
            "The back light tracks the front light.",
            &["Monitor current tracks output power"],
        ),
    Beat::new("the driver holds the power", BEAT_MS)
        .note(
            "The monitor's current runs back to the driver IC, which raises or lowers the bias current to hold the laser's power steady as it warms and ages.",
            "Wider view: blue dots run along the top pin into the black driver IC, and bias dots run back along the pin below it toward the chip.",
        )
        .detail(
            "Feedback keeps the power steady as the chip warms and cools.",
            &["Closed loop: automatic power control"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("the glass window", BEAT_MS)
        .note(
            "The window is the only opening in the sealed can: a disc of glass in the cap's front, with the lens waiting outside.",
            "The cut-open cap with the window in its right end, the chip inside, and the clear lens on its post beyond.",
        )
        .detail(
            "The window seals the can and passes the beam.",
            &["Sealed, welded can", "Glass window"],
        ),
    Beat::new("the beam crosses the window", BEAT_MS)
        .note(
            "The spreading beam crosses the window and fills the lens, which bends it back into a cone that narrows onto the fibre's end in the ferrule.",
            "The orange cone widens through the window into the lens, then narrows into the white ferrule at the right.",
        )
        .detail(
            "The beam is drawn orange; datacom lasers emit infrared.",
            &["Lens focuses onto the fibre end"],
        ),
    Beat::new("the pigtail takes the light away", BEAT_MS)
        .note(
            "The fibre's end sits in a ceramic ferrule held in a gold sleeve. From there the light runs down the fibre's core, the pigtail that leaves the package.",
            "The gold sleeve and white ferrule, with the fibre running off to the right and its core glowing.",
        )
        .detail(
            "From here on, the light is in glass.",
            &["Ceramic ferrule in a gold sleeve", "Lit core runs out to the link"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("a lit single-mode core", BEAT_MS)
        .note(
            "The lens's rays converge on the fibre's end in the ferrule. They have to meet on a single-mode core about 9 um across, so everything must line up to around a micrometre.",
            "Bright rays from the lens meet at one point on the end of the fibre, in the white ferrule.",
        )
        .detail(
            "A single-mode core is the narrow path the light takes.",
            &["Single-mode core: about 9 um"],
        ),
    Beat::new("the light enters the core", BEAT_MS)
        .note(
            "The focused light enters the core. The glass cladding round it has a slightly lower refractive index, which keeps the light guided inside.",
            "The lit core starting at the ferrule's face, inside the pale glass cladding.",
        )
        .detail(
            "Cladding keeps the light in the core.",
            &["Core inside 125 um cladding"],
        ),
    Beat::new("the light runs down the core", BEAT_MS)
        .note(
            "The light runs on down the core toward the photodiode at the far end. Single-mode glass loses little over a datacenter link; the joints along the way cost more.",
            "The glowing core running away to the right inside the fibre's beige coating, with a dot of light travelling along it.",
        )
        .detail(
            "Glass carries the light; loss sets the reach.",
            &["~0.3 dB/km at 1310 nm", "Next stop: the PHOTODIODE"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "TO-can",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "chip and facet",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "monitor photodiode",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "window and pigtail",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "fibre core",
        build: zoom_e,
    },
];
