// NETWORK+COOL tab, COLD PLATE: lettered zoom-ins a-e. Each is the overview's tray with the camera held on one subject
// (tools/pbr3d/blender/net_cold_plate_zooms.py, GLBs in tools/pbr3d/assets/net_cold_plate_zoom_<letter>.glb):
// a the plate cut open, b TIM and heat, c microchannels, d quick disconnects, e rack manifolds.

use super::super::super::blender::{page, Cell};
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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the stack", BEAT_MS)
        .note(
            "Cut through the middle: the package, a thin TIM, then the copper base of the plate.",
            "Purple dies on a brown substrate, a silver strip on top, then a thick copper slab.",
        )
        .detail(
            "Every layer is a step in temperature.",
            &["TIM", "BASE"],
        ),
    Beat::new("fins and cover", BEAT_MS)
        .note(
            "Above the base stand skived copper fins under a nickel-plated cover, held down by spring screws.",
            "Copper fins in a row under a grey lid; springs coiled round screws at the corners.",
        )
        .detail(
            "The cover makes the channels.",
            &["MICROCHANNEL", "Spring screws: even pressure"],
        ),
    Beat::new("inlet and outlet", BEAT_MS)
        .note(
            "Water enters through a slot right over the dies and leaves from a plenum at the back.",
            "Blue beads drop through the top slot and spread along the fins toward the back riser.",
        )
        .detail(
            "Coolest water on the hottest spot.",
            &["Inlet over the dies", "Outlet plenum"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("the dies heat up", BEAT_MS)
        .note(
            "Two GPU dies and their HBM stacks run at full power, around a kilowatt or more.",
            "The purple dies glow amber under the plate.",
        )
        .detail(
            "Heat starts in the transistors.",
            &["~1,000-1,400 W", "HBM beside the dies"],
        ),
    Beat::new("across the TIM", BEAT_MS)
        .note(
            "Heat crosses the TIM, which fills the tiny gaps between die and copper.",
            "Orange dots climb from the dies through a thin silver layer into the copper.",
        )
        .detail("No air in the path.", &["TIM", "BASE"]),
    Beat::new("into the water", BEAT_MS)
        .note(
            "The heat reaches the fins and the water carries it away.",
            "Orange dots reach the fins, which glow orange as beads stream through.",
        )
        .detail(
            "The water is the heat's ride out.",
            &["MICROCHANNEL", "Warm water out"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("in over the dies", BEAT_MS)
        .note(
            "Cool water drops through the cover's slot onto the hottest part of the die.",
            "Blue beads fall from the inlet riser through the slot into the fins.",
        )
        .detail(
            "Split flow: in at the middle.",
            &["Inlet slot", "Hot spot first"],
        ),
    Beat::new("along the channels", BEAT_MS)
        .note(
            "It runs the slots between fins only a fraction of a millimetre wide, touching a large surface.",
            "End-on copper fins glowing blue with beads running between them.",
        )
        .detail(
            "Narrow channels, big surface.",
            &["MICROCHANNEL: ~0.1-0.3 mm", "Skived copper"],
        ),
    Beat::new("out to the plenum", BEAT_MS)
        .note(
            "Now warm, the water gathers in the outlet plenum and leaves by the back riser.",
            "Orange beads leave the fins into the back of the plate and up the riser.",
        )
        .detail(
            "Warmed by the chip.",
            &["Outlet plenum", "WARM WATER"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("mated", BEAT_MS)
        .note(
            "The tray's halves are pushed into the manifold's halves, supply and return.",
            "Blue and red collared couplings joined between the tray's rear plate and the vertical pipes.",
        )
        .detail(
            "Two per tray.",
            &["QUICK DISCONNECT", "Supply + return"],
        ),
    Beat::new("the tray slides out", BEAT_MS)
        .note(
            "Pulling the tray parts the couplings; spring valves close both sides first.",
            "The tray moves toward the viewer; the couplings separate, leaving stubs on the pipes.",
        )
        .detail(
            "Dripless.",
            &["Poppet valves shut", "No tools"],
        ),
    Beat::new("back in", BEAT_MS)
        .note(
            "Pushed home, the tray blind-mates again and flow restarts.",
            "The tray slides back and the couplings rejoin; a green LED blinks.",
        )
        .detail(
            "Blind-mate.",
            &["Blind-mate", "OCP UQD"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("supply and return", BEAT_MS)
        .note(
            "Two vertical pipes run the height of the rack from the CDU: supply and return.",
            "A blue pipe and a red pipe rising behind a stack of trays, a dark CDU box at the bottom.",
        )
        .detail(
            "The rack's spine for water.",
            &["MANIFOLD", "CDU"],
        ),
    Beat::new("one tap per tray", BEAT_MS)
        .note(
            "Each tray has a supply and return tap with a quick disconnect.",
            "Blue beads branch off the blue pipe into each tray's coupling.",
        )
        .detail(
            "Every tray in parallel.",
            &["QUICK DISCONNECT", "Parallel flow"],
        ),
    Beat::new("back to the CDU", BEAT_MS)
        .note(
            "Warm water from every tray rises up the return to the CDU.",
            "Orange beads climb the red pipe from each tray.",
        )
        .detail(
            "~120-130 kW per rack.",
            &["WARM WATER: ~45-60 C", "Back to the CDU"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the plate cut open",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "TIM and heat",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "microchannels",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "quick disconnects",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "rack manifolds",
        build: zoom_e,
    },
];
