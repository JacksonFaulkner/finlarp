// SUBSTATION: lettered zoom-ins a-e. Each replays the overview's scene with its own camera and tags
// (tools/pbr3d/blender/power_substation_zooms.py, GLBs in tools/pbr3d/assets/power_substation_zoom_<letter>.glb):
// a core and windings, b how the turns ratio works, c losses and cooling, d lead times, e electrical steel.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_zoom_e.glb"),
        E_B,
    )
}

/// a core and windings: the steel core, then the LV and HV windings round it.
const A_B: &[Beat] = &[
    Beat::new("the core", BEAT_MS)
        .note(
            "The core is a stack of thin grain-oriented electrical-steel sheets, forming three limbs and two yokes that close the magnetic loop.",
            "A cut-open tank: the dark steel core fills the frame, its three limbs visible with the coil shapes inside them, and the laminations stacked at the edges.",
        )
        .detail(
            "Thin, insulated sheets cut the eddy-current heating.",
            &["Three limbs, two yokes", "Laminated electrical steel"],
        ),
    Beat::new("the low-voltage winding", BEAT_MS)
        .note(
            "The low-voltage winding sits closest to the core: few turns of heavy copper, so it carries the high current on the low side.",
            "The inner coils, tan pressboard barriers between them, and the steel limb running through their centres.",
        )
        .detail(
            "High current, few turns.",
            &["LV: few turns of heavy copper", "HV: many turns, outside it"],
        ),
    Beat::new("the high-voltage winding", BEAT_MS)
        .note(
            "The high-voltage winding wraps the outside, with many turns of thinner wire in stacked disc coils. Its lead runs up to the bushing on the lid.",
            "Stacked disc coils of copper, brown in colour, with the lead from the HV bushing at the top.",
        )
        .detail(
            "Many turns: high voltage on the outside.",
            &["HV: many turns", "Bushing: long insulation path"],
        ),
];

/// b how the turns ratio works: one field, the same volts per turn in each winding.
const B_B: &[Beat] = &[
    Beat::new("the field in the core", BEAT_MS)
        .note(
            "Alternating current in the coils makes a changing magnetic field in the core, which both windings share.",
            "Cyan flux beads loop round the core, with the coils either side.",
        )
        .detail(
            "A changing field induces voltage (Faraday).",
            &["Same field in both windings"],
        ),
    Beat::new("same volts per turn", BEAT_MS)
        .note(
            "Each turn of either winding gets the same volts, so more turns means more voltage. The ratio of turns sets the ratio of voltages.",
            "The two windings side by side: the high-voltage one with many discs, the low-voltage one with fewer, heavier turns, and beads on each lead.",
        )
        .detail(
            "Turns ratio = voltage ratio.",
            &["Volts per turn equal in both windings", "Power stays about the same"],
        ),
    Beat::new("230 kV to 34.5 kV", BEAT_MS)
        .note(
            "A 230 kV to 34.5 kV step needs about 6.7 times more turns on the high side. Current goes the other way, through thicker copper on the low side.",
            "The transformer's two windings in cutaway: the high-voltage coil wound with many turns, the low-voltage coil with fewer, heavier ones.",
        )
        .detail(
            "An example ratio.",
            &["About 6.7 times more turns on the high side", "Current runs the other way"],
        ),
];

/// c losses and cooling: the steel's losses, the copper's, and the oil and radiators that carry the heat.
const C_B: &[Beat] = &[
    Beat::new("losses in the steel", BEAT_MS)
        .note(
            "The core loses power all day, even at no load, to magnetic losses in its steel. Thin insulated sheets keep these small.",
            "The core glowing warm orange from within, the rest of the tank dark.",
        )
        .detail(
            "Core loss runs even at no load.",
            &["Core loss: always on", "Magnetic losses in the steel"],
        ),
    Beat::new("losses in the copper", BEAT_MS)
        .note(
            "The windings lose power to resistance, which rises with load. Losses go with current squared, so the copper glows brighter at full load.",
            "The copper coils lit pale yellow, the glow growing as the load rises.",
        )
        .detail(
            "I squared R.",
            &["Copper loss rises with load", "Losses go with current squared"],
        ),
    Beat::new("oil to the radiators", BEAT_MS)
        .note(
            "The oil carries the heat to the radiators, where it cools and sinks back, sometimes helped by fans and pumps.",
            "Orange heat rising off the top of the tank, the radiator fins on its sides, and fans below them.",
        )
        .detail(
            "Over 99% of power passes through.",
            &["Over 99% efficient", "Cooling sets how much load it carries"],
        ),
];

/// d lead times: about 50 weeks in 2021, 120 in 2024, 128 for large units in 2025, 144 for GSUs.
const D_B: &[Beat] = &[
    Beat::new("2021: about 50 weeks", BEAT_MS)
        .note(
            "The average transformer lead time was about 50 weeks in 2021, from order to delivery.",
            "The transformer at the back, with a row of bars in front of it; one short pale bar stands for 2021.",
        )
        .detail(
            "Lead time is order to delivery.",
            &["About 50 weeks in 2021"],
        ),
    Beat::new("2024: about 120 weeks", BEAT_MS)
        .note(
            "Lead times rose to about 120 weeks by 2024, more than double the 2021 figure.",
            "A longer row of bars stacked beside the 2021 one.",
        )
        .detail(
            "More than doubled since 2021.",
            &["About 120 weeks in 2024"],
        ),
    Beat::new("2025: about 128 weeks", BEAT_MS)
        .note(
            "In Q2 2025 large power transformers averaged about 128 weeks, and generator step-up units about 144. Each is custom-built to its site's voltages.",
            "The longest rows, pale orange, stacked under the transformer, with the step-up row the longest of all.",
        )
        .detail(
            "The longest-lead item on the grid side.",
            &["About 128 weeks, large units (Q2 2025)", "About 144 weeks, GSU"],
        ),
];

/// e electrical steel: the grain-oriented strip, the stacked core, and the few mills that make it.
const E_B: &[Beat] = &[
    Beat::new("grain-oriented steel", BEAT_MS)
        .note(
            "Grain-oriented electrical steel is rolled so its crystals line up with the magnetic field, which cuts core losses.",
            "A thin strip of steel in the foreground, coiled, with the sheets of the core stacked behind it.",
        )
        .detail(
            "Lower losses in the core.",
            &["Grain-oriented silicon steel"],
        ),
    Beat::new("few mills make it", BEAT_MS)
        .note(
            "Few mills make grain-oriented steel. In the US one company, Cleveland-Cliffs, is the domestic producer, which ties transformer output to one supplier.",
            "Sheets stacked into packets along the core's limbs, with a steel frame at the back.",
        )
        .detail(
            "One domestic producer.",
            &["Cleveland-Cliffs: US domestic producer"],
        ),
    Beat::new("custom, imported, scarce", BEAT_MS)
        .note(
            "Most large units for the US are imported, and each is built to its site's voltages, with little spare stock on hand.",
            "Three custom transformers on a pad, with an empty plinth beside them where the spare would stand.",
        )
        .detail(
            "Tariffs could lengthen lead times.",
            &["Most large US units imported", "Tariffs on imports"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "core and windings",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "how the turns ratio works",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "losses and cooling",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "lead times",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "electrical steel",
        build: zoom_e,
    },
];
