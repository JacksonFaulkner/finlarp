// PACKAGING tab, BOARD: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PKG_BOARD.txt,
// from the Blender scenes in tools/pbr3d/blender/pkg_board_sections.py (GLBs
// tools/pbr3d/assets/pkg_board_section_<n>.glb). Three beats each. The Sources heading (10) is text only.

use super::super::super::blender::{page, Cell, BEAT_MS};
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

/// 1 what happens: the module; power climbs; heat leaves into the coolant
const S1_B: &[Beat] = &[
    Beat::new("the module", BEAT_MS)
        .note(
            "A module board carries the GPU package under its cold plate, the regulator phases beside it and connectors at the edge.",
            "The whole module cut open: green board, dark phases, grey cold plate with hoses, black connector.",
        )
        .detail(
            "Package, power, cooling and links on one board.",
            &["MODULE", "BGA BALLS join package to board"],
        ),
    Beat::new("power climbs", BEAT_MS)
        .note(
            "Hundreds of amps leave the regulators, cross the board and climb through the balls and substrate into the die.",
            "Red beads run from the inductors into the board and up through a see-through substrate.",
        )
        .detail(
            "Power comes up from below.",
            &["POWER DELIVERY", "VRM beside the package"],
        ),
    Beat::new("heat leaves", BEAT_MS)
        .note(
            "Every watt becomes heat, which leaves upward through the lid into the cold plate's coolant.",
            "The dies glow; orange beads rise through the lid; blue beads run between the fins.",
        )
        .detail(
            "Heat goes out the top.",
            &["COLD PLATE", "LIQUID COOLING"],
        ),
];

/// 2 the parts: the column cut open
const S2_B: &[Beat] = &[
    Beat::new("the board half", BEAT_MS)
        .note(
            "One column drawn four times larger. At the bottom: the board's copper planes, a plated via, the pads and the BGA ball.",
            "A big cross-section: striped tan and copper board layers, a copper via, gold pads and a silver half ball.",
        )
        .detail(
            "The board's job is planes and vias.",
            &["BGA BALLS", "Plated via + power plane"],
        ),
    Beat::new("the package half", BEAT_MS)
        .note(
            "Above the ball: ABF build-up layers with stacked microvias, a glass-fibre core with a plated through-hole, C4 bumps, the silicon interposer with TSVs, the RDL, microbumps and the die.",
            "The column's middle: dark green build-up layers, a pale core with a copper barrel, small silver bumps, grey silicon with copper pillars, a thin wiring layer, tiny bumps and the purple die.",
        )
        .detail(
            "Each level shrinks the pitch.",
            &["Substrate: build-up + core", "Interposer: TSV + RDL"],
        ),
    Beat::new("the thermal half", BEAT_MS)
        .note(
            "Above the die: TIM1, the lid, TIM2, the cold plate base and its fins.",
            "The column's top: thin grey layer, thick silver lid, a pale pad, copper base, a comb of fins.",
        )
        .detail(
            "Five layers between die and water.",
            &["TIM1 + LID + TIM2", "COLD PLATE fins"],
        ),
];

/// 3 in order: VRM to plane; up the column; die to coolant
const S3_B: &[Beat] = &[
    Beat::new("1 the VRM", BEAT_MS)
        .note(
            "The regulator steps board power down to under a volt and drives it into the power plane.",
            "Red beads leave the left inductors and drop into the board's copper plane.",
        )
        .detail(
            "Step 1: step it down.",
            &["VRM: to under 1 V", "Power plane"],
        ),
    Beat::new("2-3 up into the die", BEAT_MS)
        .note(
            "The current climbs the ball, the through-hole, the C4s and the TSVs, and the die turns it into compute and heat.",
            "The 4x column: red beads climb from the plane through every layer into the purple die.",
        )
        .detail(
            "Steps 2 and 3: climb and compute.",
            &["BGA > PTH > C4 > TSV", "The die"],
        ),
    Beat::new("4-5 heat out", BEAT_MS)
        .note(
            "The heat crosses the lid into the cold plate, and coolant carries it away to the facility.",
            "The dies glow; orange beads rise into the plate; blue beads run between the fins.",
        )
        .detail(
            "Steps 4 and 5: out and away.",
            &["Lid > cold plate", "Coolant to the facility"],
        ),
];

/// 4 power delivery: phases, decaps, I x R
const S4_B: &[Beat] = &[
    Beat::new("phases and plane", BEAT_MS)
        .note(
            "Each phase's power stage switches 12 V and its inductor smooths it; the outputs join in a thick copper plane under the package.",
            "A close view of the left phases: dark stages, tall inductors, red beads dropping into the plane.",
        )
        .detail(
            "Many phases share the current.",
            &["VRM: multiphase", "Thick copper plane"],
        ),
    Beat::new("decoupling caps on the back", BEAT_MS)
        .note(
            "Under the package, on the board's back, rows of MLCCs hold charge for sudden load steps faster than the regulator can respond. A steel bolster frames them.",
            "A view from below: tan capacitors with silver ends in a grid under the package, a steel frame around them, amber beads rising into the board.",
        )
        .detail(
            "Caps cover the microseconds.",
            &["MLCC decaps", "Steel bolster plate"],
        ),
    Beat::new("I x R per level", BEAT_MS)
        .note(
            "Every level drops voltage by current times resistance. At a thousand amps, a tenth of a milliohm costs 0.1 V, an eighth of the supply.",
            "The 4x column with red beads climbing; tags at the plane, ball and bumps.",
        )
        .detail(
            "At these currents, milliohms matter.",
            &["Loss = I x R", "~0.8 V at the die"],
        ),
];

/// 5 cooling: up the column; the fins; the hoses
const S5_B: &[Beat] = &[
    Beat::new("heat up the column", BEAT_MS)
        .note(
            "Heat climbs from the die through TIM1, spreads in the lid, crosses TIM2 and enters the plate.",
            "The 4x column's top: orange beads rise through each thermal layer into the copper base.",
        )
        .detail(
            "Every layer is a resistance.",
            &["TIM1 > LID > TIM2", "Into the plate"],
        ),
    Beat::new("coolant in the fins", BEAT_MS)
        .note(
            "The fins give the water area; coolant runs between them and takes the heat.",
            "The plate's cover see-through: blue beads between copper fins.",
        )
        .detail(
            "Area and flow carry the heat.",
            &["COLD PLATE", "Skived copper fins"],
        ),
    Beat::new("hoses in and out", BEAT_MS)
        .note(
            "Cool water arrives through one hose and leaves warm through the other, to the rack's manifold.",
            "A higher view: blue beads ride down the blue hose into the plate, orange beads ride up the orange hose and away.",
        )
        .detail(
            "Each plate is one branch of a loop.",
            &["LIQUID COOLING", "To the rack manifold"],
        ),
];

/// 6 modules and links
const S6_B: &[Beat] = &[
    Beat::new("the module's parts", BEAT_MS)
        .note(
            "The module board carries the package, its power stages and its connectors.",
            "The whole module: phases, package, cold plate and connector.",
        )
        .detail(
            "A module is a GPU's board.",
            &["MODULE", "Power stages + connectors"],
        ),
    Beat::new("die to connector", BEAT_MS)
        .note(
            "NVLink lanes leave the die, run down through the package and along the board to a high-speed connector and twinax cables.",
            "Cyan beads leave the die and run through the package, along the board and into the teal cables.",
        )
        .detail(
            "Links leave by cable.",
            &["NVLINK lanes", "Connector + twinax"],
        ),
    Beat::new("a tray to its switch", BEAT_MS)
        .note(
            "Four modules per tray send cables to a switch tray, so every GPU reaches every other.",
            "A tray: four modules, teal cables rising to a switch tray, cyan beads riding them.",
        )
        .detail(
            "The switch joins the GPUs.",
            &["NVLINK SWITCH", "Many GPUs act as one"],
        ),
];

/// 7 racks
const S7_B: &[Beat] = &[
    Beat::new("the rack", BEAT_MS)
        .note(
            "Compute trays and switch trays stack in one cabinet.",
            "A rack frame: green trays above and below grey switch trays, pipes at the back.",
        )
        .detail(
            "A rack is the unit that ships.",
            &["RACK", "Compute + switch trays"],
        ),
    Beat::new("its coolant loop", BEAT_MS)
        .note(
            "Cool water rises through a supply manifold, crosses every tray and returns warm, out to a coolant distribution unit.",
            "From the back: blue beads up the left pipe and across each tray; orange beads down the right.",
        )
        .detail(
            "The loop ends at a CDU.",
            &["Supply + return manifolds", "CDU (Network+Cool tab)"],
        ),
    Beat::new("switch trays and cables", BEAT_MS)
        .note(
            "NVLink cables tie each compute tray to the switch trays in the middle.",
            "A tray with teal cables up to the switch tray, cyan beads riding.",
        )
        .detail(
            "Cables run inside the rack.",
            &["NVLINK cables", "Switch trays mid-rack"],
        ),
];

/// 8 who makes it
const S8_B: &[Beat] = &[
    Beat::new("chips and package", BEAT_MS)
        .note(
            "NVIDIA and AMD design the GPUs; TSMC makes the dies and the CoWoS interposer; SK hynix, Samsung and Micron make HBM; Ibiden and Unimicron make substrates.",
            "The cut face with tags on die, interposer, HBM and substrate.",
        )
        .detail(
            "The package has many makers.",
            &["NVDA, AMD", "TSMC, Ibiden"],
        ),
    Beat::new("board and power", BEAT_MS)
        .note(
            "ODMs such as Foxconn, Quanta and Wistron build the boards and trays; Infineon, MPS and Renesas supply regulators; Murata and Samsung Electro-Mechanics make the MLCCs.",
            "The module from above with tags on the board, phases and back-side caps.",
        )
        .detail(
            "The board is an ODM's work.",
            &["Foxconn, Quanta, Wistron", "Infineon, MPS"],
        ),
    Beat::new("cooling and links", BEAT_MS)
        .note(
            "Cold plates come from makers such as Cooler Master, AVC and Boyd; Amphenol supplies high-speed connectors and cables; Vertiv supplies CDUs.",
            "The plate see-through with tags on fins, connector and hoses.",
        )
        .detail(
            "Cooling and cabling are their own trades.",
            &["Cooler Master, AVC, Boyd", "Amphenol, Vertiv"],
        ),
];

/// 9 chokepoints and risks
const S9_B: &[Beat] = &[
    Beat::new("rising power", BEAT_MS)
        .note(
            "Power per package keeps rising, and delivery losses rise with the square of the current.",
            "Red beads crowd the board's plane and climb into glowing dies.",
        )
        .detail(
            "More watts, more amps, more loss.",
            &["Power per package rising", "I x R loss rising"],
        ),
    Beat::new("air runs out", BEAT_MS)
        .note(
            "Air can't move this heat; liquid cooling needs pumps, manifolds and CDUs in the data centre.",
            "Coolant beads stream between the fins under a clear cover.",
        )
        .detail(
            "Liquid needs new infrastructure.",
            &["Air cooling runs out", "Liquid: new plumbing"],
        ),
    Beat::new("warpage", BEAT_MS)
        .note(
            "Larger packages and boards bend more as they heat and cool; corner balls take the strain.",
            "The outermost balls at each end of the cut face glow red.",
        )
        .detail(
            "Bigger means harder to assemble.",
            &["Warpage grows with size", "Corner joints first"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_board_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
