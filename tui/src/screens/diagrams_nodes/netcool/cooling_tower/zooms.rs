// NETWORK+COOL tab, COOLING TOWERS: lettered zoom-ins a-e (tools/pbr3d/blender/net_cooling_tower_zooms.py, GLBs in
// tools/pbr3d/assets/net_cooling_tower_zoom_<letter>.glb): a fill, b evaporation, c drift, d water use, e heat out.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("corrugated sheets", BEAT_MS)
        .note(
            "Fill is stacks of thin corrugated PVC sheets. Warm water from the nozzles lands on top.",
            "Four zig-zag grey sheets drawn large; amber beads start at the top.",
        )
        .detail(
            "Surface area is everything.",
            &["FILL: PVC sheets", "Warm water on top"],
        ),
    Beat::new("films and air", BEAT_MS)
        .note(
            "The water spreads into thin films along the corrugations while air rises in the gaps between the sheets.",
            "Blue film lines on the sheets; pale air beads rise between them.",
        )
        .detail(
            "Water down, air up.",
            &["Thin films", "Counterflow air"],
        ),
    Beat::new("vapour leaves", BEAT_MS)
        .note(
            "Vapour leaves the film surfaces into the air, and the cooled water drips out the bottom.",
            "White vapour beads rising off the films; blue beads leaving the bottom.",
        )
        .detail(
            "Evaporation at the surface.",
            &["Vapour off", "Cooled water out"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("one drop", BEAT_MS)
        .note(
            "Follow one warm drop falling through the tower: vapour leaves its surface as it falls.",
            "A large amber ball falling with white vapour beads leaving its skin.",
        )
        .detail(
            "Each drop loses a little water.",
            &["Warm drop", "Vapour off"],
        ),
    Beat::new("latent heat", BEAT_MS)
        .note(
            "Evaporating a kilogram of water takes about 2,400 kJ, while cooling a kilogram by 6 C releases only about 25 kJ.",
            "Two bars: a tall red one for evaporation and a short amber one for 6 C of cooling.",
        )
        .detail(
            "Evaporation carries a lot of heat.",
            &["~2,400 kJ/kg", "~25 kJ for 6 C"],
        ),
    Beat::new("the wet-bulb limit", BEAT_MS)
        .note(
            "So about 1% evaporating cools the rest by roughly 6 C. The water can approach, but never reach, the air's wet-bulb temperature.",
            "The drop, now blue, falling away below.",
        )
        .detail(
            "1% for 6 C.",
            &["~1% per 6 C", "WET-BULB limit"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("chevron blades", BEAT_MS)
        .note(
            "Drift eliminators are rows of chevron blades above the spray. The air leaving the tower carries fine droplets with it.",
            "Zig-zag blades in a row with amber droplets and white vapour rising toward them.",
        )
        .detail(
            "Air carries droplets.",
            &["DRIFT ELIMINATORS", "Chevron blades"],
        ),
    Beat::new("caught", BEAT_MS)
        .note(
            "The air turns sharply through the blades. Droplets are too heavy to follow, hit the blades and drain back down.",
            "Close up: amber drops hit the bends and fall; white beads weave through.",
        )
        .detail(
            "Inertia catches them.",
            &["Droplets caught", "Vapour passes"],
        ),
    Beat::new("tiny losses", BEAT_MS)
        .note(
            "Good eliminators hold drift to about 0.001% of the circulating flow or less, which saves water and limits aerosols.",
            "The blade row from the other side.",
        )
        .detail(
            "Almost nothing escapes.",
            &["~0.001% drift", "Fewer aerosols"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("make-up", BEAT_MS)
        .note(
            "A make-up line with a meter replaces the water that evaporates.",
            "The brass meter by the tower with its needle spinning and green beads flowing in.",
        )
        .detail(
            "Refill what is lost.",
            &["MAKE-UP METER", "Replaces evaporation"],
        ),
    Beat::new("blowdown", BEAT_MS)
        .note(
            "Evaporation leaves minerals behind, so some basin water is drained as blowdown; towers typically run at 3-6 cycles of concentration.",
            "Blue beads draining from the basin corner.",
        )
        .detail(
            "Shed the minerals.",
            &["BLOWDOWN", "3-6 cycles"],
        ),
    Beat::new("litres per day", BEAT_MS)
        .note(
            "Rejecting 100 MW of heat by evaporation uses roughly 3.6 million litres a day: about 1.5 litres evaporated per kWh, plus blowdown.",
            "Three glowing bars rising: blue, amber and a tall red one.",
        )
        .detail(
            "Scale matters.",
            &["~3.6M L/day per 100 MW", "~1.5 L/kWh"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("wet: vapour", BEAT_MS)
        .note(
            "A wet tower sends the heat into the air mostly as water vapour, and can cool water close to the wet-bulb temperature.",
            "The tower with a tall white plume.",
        )
        .detail(
            "Latent heat out.",
            &["WET: vapour", "Near wet-bulb"],
        ),
    Beat::new("into the outdoor air", BEAT_MS)
        .note(
            "Whichever way it goes, every watt the servers use ends up in the outdoor air. A dry cooler does it as warm air, with no water.",
            "A wider view of the plume; a dry cooler with fans and rising heat.",
        )
        .detail(
            "The last step.",
            &["HEAT OUT", "DRY: warm air"],
        ),
    Beat::new("dry trade-off", BEAT_MS)
        .note(
            "Dry coolers use no water but leave the water warmer and need more fan power, so they fit warm-water liquid cooling best.",
            "The dry cooler close up with fans spinning.",
        )
        .detail(
            "Water vs power.",
            &["Zero evaporation", "More fan power"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "fill",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "evaporation",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "drift",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "water use",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "heat out",
        build: zoom_e,
    },
];
