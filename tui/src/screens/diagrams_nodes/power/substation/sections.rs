// SUBSTATION: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_SUB.txt, from the Blender
// scenes in tools/pbr3d/blender/power_substation_sections.py (GLBs in tools/pbr3d/assets/power_substation_section_<n>.glb).
// Three beats each. Heading 10 (Sources) is text only.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1 what happens: a transformer steps the voltage down.
const S1_B: &[Beat] = &[
    Beat::new("the line lands on the gantry", BEAT_MS)
        .note(
            "Transmission lines land on a steel gantry in the yard and connect to the tall bushings on a power transformer.",
            "The transformer cut open at the front, the lines landing on the gantry at the left, and bushings rising from the tank lid.",
        )
        .detail(
            "The line connects straight to the transformer.",
            &["230 kV line in (example)", "BUSHING: brings each conductor through the lid"],
        ),
    Beat::new("the core's field links the windings", BEAT_MS)
        .note(
            "Alternating current in the high-voltage windings drives a changing magnetic field round the laminated steel core. That field induces a lower voltage in the low-voltage winding.",
            "The core in the tank with cyan flux beads looping round it, and the windings glowing at its limbs.",
        )
        .detail(
            "A changing field induces voltage.",
            &["Core: laminated electrical steel", "Windings: copper coils"],
        ),
    Beat::new("about 34.5 kV leaves for the campus", BEAT_MS)
        .note(
            "A 230 kV line comes out at about 34.5 kV for the campus. Current rises as voltage falls, so the low side carries more amps through thicker copper.",
            "The low-voltage bushings on the far side of the tank, with a few beads leaving through them toward the site.",
        )
        .detail(
            "Step-down to the campus.",
            &["230 kV in, about 34.5 kV out (example)", "Power stays about the same"],
        ),
];

/// 2 the parts: the unit whole, cut open, and a bushing in section.
const S2_B: &[Beat] = &[
    Beat::new("the unit whole", BEAT_MS)
        .note(
            "A power transformer is a core and windings in an oil-filled tank, rated tens to hundreds of MVA. Its bushings, radiators and conservator sit outside the tank.",
            "The whole transformer in grey: tall bushings on top, radiator panels on the sides, and a round conservator over the tank.",
        )
        .detail(
            "Tens to hundreds of MVA, oil-filled.",
            &["POWER TRANSFORMER: tens to hundreds of MVA", "RADIATOR: cools the oil"],
        ),
    Beat::new("cut open: core, windings, oil", BEAT_MS)
        .note(
            "Cut open, the tank shows the core of three limbs and two yokes, with the copper windings wound round each limb.",
            "The tank front lifted away: the dark core with pale steel limbs, copper coils inside, and the oil-filled tank around them.",
        )
        .detail(
            "The core carries the field; the windings carry the current.",
            &["CORE: stacked electrical-steel sheets", "WINDINGS: copper coils, many turns on the HV side"],
        ),
    Beat::new("a bushing in section", BEAT_MS)
        .note(
            "A bushing carries each conductor through the grounded tank lid without arcing to it. The high-voltage ones are tall because the insulation path must be long.",
            "A bushing cut in section: a tall porcelain or polymer insulator with its conductor down the middle.",
        )
        .detail(
            "Bushings are a common failure point.",
            &["BUSHING: long insulation path", "A long-lead spare"],
        ),
];

/// 3 in order: the bushing and HV winding, the core's flux, the LV out and the oil to the radiators.
const S3_B: &[Beat] = &[
    Beat::new("into the bushing and HV winding", BEAT_MS)
        .note(
            "Step 1: high-voltage current enters through the tall bushings. Step 2: it flows through the many-turn high-voltage winding.",
            "A bushing lit at its top, with beads running down the lead into the outer winding's stacked coils.",
        )
        .detail(
            "High voltage, low current in.",
            &["HV: many turns"],
        ),
    Beat::new("the core's flux, then the LV out", BEAT_MS)
        .note(
            "Step 3: the core carries the alternating field to the other winding. Step 4: the few-turn low-voltage winding gives a lower voltage at higher current.",
            "Cyan flux looping round the core, and the inner low-voltage coil with its bushings glowing on the far side.",
        )
        .detail(
            "Low voltage, high current out.",
            &["LV: few heavy turns", "Power stays about the same"],
        ),
    Beat::new("oil carries the heat", BEAT_MS)
        .note(
            "Step 5: the oil carries the heat from the core and windings to the radiators, where fins and fans cool it.",
            "Orange heat rising from the tank into the radiator panels on its side, with fans below.",
        )
        .detail(
            "Heat needs a path out.",
            &["RADIATOR: cools the oil", "Mineral oil fills the tank"],
        ),
];

/// 4 turns ratio: a teaching core, one field, one turn lit in each coil.
const S4_B: &[Beat] = &[
    Beat::new("the same field, two coils", BEAT_MS)
        .note(
            "A small teaching core: two coils wound on one steel loop share a single changing field. Each turn in either coil gets the same volts.",
            "The teaching core: a steel loop with a coil of many turns on one side and a coil of few turns on the other, both lit.",
        )
        .detail(
            "Same field, same volts per turn.",
            &["Volts per turn equal in both", "TURNS RATIO: turns in / turns out = voltage in / voltage out"],
        ),
    Beat::new("ten times the turns", BEAT_MS)
        .note(
            "With ten times more turns on one side, that side has ten times the voltage. The other side has ten times the current, with the same power.",
            "A single turn lit in each coil, with beads moving through both.",
        )
        .detail(
            "Turns ratio = voltage ratio.",
            &["10x the turns = 10x the volts", "Current goes the other way"],
        ),
    Beat::new("230 kV to 34.5 kV", BEAT_MS)
        .note(
            "A 230 kV to 34.5 kV transformer needs about 6.7 times more turns on the high side. Current goes the other way, through thicker low-side copper.",
            "The transformer's two windings in cutaway: the high-voltage coil's many discs, and the low-voltage coil's fewer, heavier turns.",
        )
        .detail(
            "An example ratio.",
            &["About 6.7 times more turns on the high side"],
        ),
];

/// 5 losses: the core glows, then the windings; the oil carries the heat to the radiators and fans.
const S5_B: &[Beat] = &[
    Beat::new("the core glows", BEAT_MS)
        .note(
            "The core loses power to magnetic losses in its steel, which run even at no load. Thin insulated sheets keep the eddy currents down.",
            "The core's limbs glowing warm orange from within, the rest of the tank dark.",
        )
        .detail(
            "Core loss is always on.",
            &["Core loss: always on, even at no load"],
        ),
    Beat::new("then the windings", BEAT_MS)
        .note(
            "The windings lose power to resistance, which rises with load. Losses go with current squared, so the copper glows brighter at full load.",
            "The copper coils glowing pale yellow, the glow growing as the load rises.",
        )
        .detail(
            "I squared R.",
            &["Copper loss rises with load"],
        ),
    Beat::new("oil and fans carry it away", BEAT_MS)
        .note(
            "The oil carries the heat to the radiators, where it cools and sinks back, sometimes helped by fans and pumps.",
            "Orange heat rising off the top, the radiators on the sides and fans below them.",
        )
        .detail(
            "Cooling sets how much load it can carry.",
            &["Over 99% efficient", "Overheating ages the insulation"],
        ),
];

/// 6 lead time: about 50 weeks in 2021, 120 in 2024, 128 and 144 in 2025.
const S6_B: &[Beat] = &[
    Beat::new("about 50 weeks in 2021", BEAT_MS)
        .note(
            "The average transformer lead time was about 50 weeks in 2021, from order to delivery.",
            "Rows of pale bars in front of the transformer, with one short bar for 2021.",
        )
        .detail(
            "Lead time is order to delivery.",
            &["About 50 weeks in 2021"],
        ),
    Beat::new("about 120 weeks in 2024", BEAT_MS)
        .note(
            "Lead times rose to about 120 weeks by 2024, more than double the 2021 figure.",
            "A longer row of bars stacked beside the 2021 one.",
        )
        .detail(
            "More than doubled since 2021.",
            &["About 120 weeks in 2024"],
        ),
    Beat::new("about 128 weeks in 2025", BEAT_MS)
        .note(
            "In Q2 2025 large power transformers averaged about 128 weeks, and generator step-up units about 144. Each is custom-built to its site's voltages.",
            "The longest bars, pale orange, stacked under the transformer, with the step-up row the longest.",
        )
        .detail(
            "The longest-lead item on the grid side.",
            &["About 128 weeks, large units (Q2 2025)", "About 144 weeks, GSU"],
        ),
];

/// 7 steel: the grain-oriented strip, the stacked sheets of the core, and the one US mill.
const S7_B: &[Beat] = &[
    Beat::new("grain-oriented steel", BEAT_MS)
        .note(
            "The core is grain-oriented electrical steel, rolled so its crystals line up with the field. That cuts the core losses.",
            "A coil of steel strip in the foreground, its edges visible, with the core stacked behind it.",
        )
        .detail(
            "Lower losses in the core.",
            &["GRAIN-ORIENTED: crystals aligned with the field"],
        ),
    Beat::new("sheets stacked into a core", BEAT_MS)
        .note(
            "Thin insulated sheets are stacked into packets to make the core's closed loops, which keeps eddy-current heating down.",
            "Stacked sheets of pale steel forming the core's limbs, with the tank wall beside them.",
        )
        .detail(
            "Thin, insulated sheets.",
            &["CORE: stacked electrical-steel sheets"],
        ),
    Beat::new("one US mill feeds the line", BEAT_MS)
        .note(
            "Few mills make this steel, and in the US one company, Cleveland-Cliffs, is the domestic producer. Transformer output depends on that one supplier.",
            "The steel strip coming off a coil, and a transformer tank with a stacked core beside it.",
        )
        .detail(
            "Supply is one of the bottlenecks.",
            &["Few mills make it", "US domestic producer: Cleveland-Cliffs"],
        ),
];

/// 8 who makes it: the makers' names on a row of units, and a heavy-lift ship bringing one in.
const S8_B: &[Beat] = &[
    Beat::new("units from many makers", BEAT_MS)
        .note(
            "Large units are made by Hitachi Energy, Siemens Energy, GE Vernova (GEV, including Prolec GE), HD Hyundai Electric, Hyosung Heavy Industries and Eaton (ETN).",
            "A row of transformer tanks, each tagged with its maker's name.",
        )
        .detail(
            "Most large units for the US are imported.",
            &["Hitachi Energy, Siemens Energy", "GE Vernova (GEV), Eaton (ETN)"],
        ),
    Beat::new("a unit ships in", BEAT_MS)
        .note(
            "Most large units for the US come from overseas, carried by ship and built to order for one site.",
            "A heavy-lift ship at a dock with a transformer on its deck, a crane lifting it off.",
        )
        .detail(
            "Imports add lead time and tariff risk.",
            &["Most large US units imported"],
        ),
    Beat::new("the makers' limit", BEAT_MS)
        .note(
            "Each unit is custom-built to its site's voltages, and the makers cite labour shortages as the limit on their output.",
            "A tank on a pad with its maker's tag pinned on, next to an empty plinth.",
        )
        .detail(
            "Labour, not design, is the stated limit.",
            &["Makers cite labour shortages"],
        ),
];

/// 9 chokepoints: a two-to-three-year row, custom units with no spare, and a tariff gate at the dock.
const S9_B: &[Beat] = &[
    Beat::new("two to three years", BEAT_MS)
        .note(
            "Large units have a lead time of two to three years, and each order is custom-built, so spares are rare.",
            "A row of transformer tanks on a pad, each labelled with the long wait.",
        )
        .detail(
            "Two to three years for large units.",
            &["About 128 weeks (Q2 2025)", "Little spare stock"],
        ),
    Beat::new("custom units, no spare", BEAT_MS)
        .note(
            "Custom designs mean little interchangeability, so a failed unit cannot simply be swapped for another site's spare.",
            "Three custom transformers on a pad, with an empty plinth beside them where the spare would stand.",
        )
        .detail(
            "Little interchangeability.",
            &["Custom designs", "Little spare stock"],
        ),
    Beat::new("a tariff gate at the dock", BEAT_MS)
        .note(
            "Tariffs on imports sit between the ship and the site, and Wood Mackenzie expects them to worsen lead times.",
            "A ship at a dock, with a barrier gate across the quay.",
        )
        .detail(
            "Tariffs could lengthen lead times.",
            &["Tariffs on imports", "Wood Mackenzie expects worse lead times"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_substation_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
