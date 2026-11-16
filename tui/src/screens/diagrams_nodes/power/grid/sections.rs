// GRID: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_GRID.txt, from the Blender
// scenes in tools/pbr3d/blender/power_grid_sections.py (GLBs in tools/pbr3d/assets/power_grid_section_<n>.glb).
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

/// 1 what happens: the plant feeds the grid, the lines carry it, the substation steps it down.
const S1_B: &[Beat] = &[
    Beat::new("the plant feeds the grid", BEAT_MS)
        .note(
            "A power plant generates at about 10 to 25 kV, and a step-up transformer raises it to transmission voltage. Everything after this depends on that one connection.",
            "The plant at the left, with its stack and the step-up transformer; yellow beads leave it toward the lines.",
        )
        .detail(
            "The utility's connection sets how big a campus can be.",
            &["Plant: ~10-25 kV", "Transmission: 115-345 kV"],
        ),
    Beat::new("lines on towers at 115-345 kV", BEAT_MS)
        .note(
            "Transmission lines carry the power across the country on steel towers at 115 to 345 kV and higher. Each circuit is three conductors, the grid's standard three-phase power.",
            "Grey lattice towers march away from the plant, with silver conductors hanging on teal insulator strings and yellow beads riding them.",
        )
        .detail(
            "High voltage keeps the current, and the loss, small.",
            &["115-345 kV and up", "Three conductors per circuit"],
        ),
    Beat::new("the substation steps it down", BEAT_MS)
        .note(
            "At the campus edge the line lands on a substation gantry, and a transformer steps the voltage down for the site. Past the utility's meter, cables run to the data hall.",
            "The steel gantry where the conductors land, the step-down transformer with brown bushings, and the grey meter cabinet beside it.",
        )
        .detail(
            "The utility's equipment ends at the meter.",
            &["Step-down at the campus substation", "Utility meter: where the campus begins"],
        ),
];

/// 2 the parts: TRANSMISSION, THREE-PHASE; UTILITY, QUEUE, LOAD; PUE, BEHIND THE METER, GAS TURBINE.
const S2_B: &[Beat] = &[
    Beat::new("transmission and three-phase", BEAT_MS)
        .note(
            "Transmission lines carry power across the country at 115 to 345 kV and up, on steel towers. Each circuit is three conductors of three-phase AC, whose voltages peak one third of a cycle apart.",
            "A lattice tower with six silver conductors in two sets of three, and teal insulator strings at each arm.",
        )
        .detail(
            "Three-phase power moves more per conductor.",
            &["115-345 kV and up", "Three conductors per circuit"],
        ),
    Beat::new("utility, queue and load", BEAT_MS)
        .note(
            "The utility owns the wires to the site and sells the power under rates set by regulators. The interconnection queue is the line of projects waiting for permission to connect.",
            "Projects lined up along the road: solar arrays, battery containers and a gas plant, with a cyan ring round the one under study.",
        )
        .detail(
            "The utility and the queue decide when a campus can open.",
            &["~1,400 GW generation + 890 GW storage queued", "176 TWh in 2023 (4.4%)"],
        ),
    Beat::new("PUE and power on site", BEAT_MS)
        .note(
            "PUE is total site power over IT power. Where the grid is too slow, a campus can run a gas turbine behind the meter, a plant on its own site.",
            "A grey gas-turbine package with its stack and a blue generator, next to the data hall's cooling units on the roof.",
        )
        .detail(
            "PUE 1.2 means 20% overhead.",
            &["Efficient sites ~1.1-1.2", "Gas turbine: tens to hundreds of MW"],
        ),
];

/// 3 in order: the generator, the step-up, the three-phase lines, the gantry, the step-down.
const S3_B: &[Beat] = &[
    Beat::new("from the generator", BEAT_MS)
        .note(
            "The generator makes power at about 10 to 25 kV, and the step-up transformer raises it to transmission voltage. Only then does the power leave the plant.",
            "The turbine hall with its stack, the blue generator, and the transformer with brown bushings; yellow beads leave it toward the line.",
        )
        .detail(
            "The step-up comes before the lines.",
            &["Generator: ~10-25 kV", "Transmission: 115-345 kV"],
        ),
    Beat::new("along the three-phase lines", BEAT_MS)
        .note(
            "Three-phase lines carry the power tower to tower, the conductors sagging between towers. Each circuit carries three phases.",
            "Grey lattice towers in a row, silver conductors sagging between them, and yellow beads moving along all of them.",
        )
        .detail(
            "THREE-PHASE: three conductors, voltages peaking in turn.",
            &["Three phases per circuit"],
        ),
    Beat::new("the gantry and the step-down", BEAT_MS)
        .note(
            "The line reaches the campus substation's gantry, and the step-down transformer lowers the voltage for the site. The step-down is the last high-voltage stage before the load.",
            "The steel gantry where the conductors land and drop to the bus, the transformer with its cooling fins, and beads running down the leads into it.",
        )
        .detail(
            "The step-down is the last high-voltage stage.",
            &["Step-down for the site", "Utility meter: where the campus begins"],
        ),
];

/// 4 high voltage: the same power at two voltages, and the loss at each.
const S4_B: &[Beat] = &[
    Beat::new("same power, two ways", BEAT_MS)
        .note(
            "Power is voltage times current. For the same power, a high-voltage line carries far less current, so its wires run cool and lose little.",
            "Two cut-away wires side by side: a thin high-voltage line with few beads, and a thick low-voltage line with many beads running hot.",
        )
        .detail(
            "Voltage times current is the power.",
            &["Power = voltage x current", "Transmission: 115-345 kV"],
        ),
    Beat::new("ten times the volts", BEAT_MS)
        .note(
            "Wire loss goes with the current squared. Ten times the voltage means a tenth of the current and a hundredth of the loss.",
            "A pair of conductors with the loss shown as a faint orange glow; the high-voltage one stays cool.",
        )
        .detail(
            "Loss goes with current squared (I squared R).",
            &["10x the voltage = 1/100 the loss"],
        ),
    Beat::new("why it steps down near the load", BEAT_MS)
        .note(
            "The lines run at hundreds of kilovolts across the country, and the voltage steps down only near the load. Stepping down earlier would waste the saving.",
            "A tall tower carrying the conductors across the distance, then the gantry and the transformer at the far end, where the voltage drops.",
        )
        .detail(
            "Transmission steps down only near the load.",
            &["Transmission: 115-345 kV and up", "Step-down at the campus"],
        ),
];

/// 5 AI's power: the data hall's share of US electricity, and one rack's draw.
const S5_B: &[Beat] = &[
    Beat::new("58 to 176 TWh", BEAT_MS)
        .note(
            "US data centers used about 58 TWh in 2014 and about 176 TWh in 2023, when they were 4.4% of US electricity.",
            "The data hall cut open: rows of black racks with green lights, the gold busway over each row, cooling units on the roof.",
        )
        .detail(
            "LBNL, December 2024.",
            &["58 TWh (2014)", "176 TWh (2023), 4.4%"],
        ),
    Beat::new("325-580 TWh by 2028", BEAT_MS)
        .note(
            "Berkeley Lab projects 325-580 TWh by 2028, 6.7% to 12% of US electricity, driven mostly by AI servers. The projection is the reason the grid is being asked for more.",
            "A tall dark cabinet standing beside the hall, and the rows of racks running on along the gold busway.",
        )
        .detail(
            "A projection, not a measurement.",
            &["325-580 TWh projected for 2028", "6.7-12% of US electricity"],
        ),
    Beat::new("one rack: about 120 kW", BEAT_MS)
        .note(
            "One GB200 NVL72 rack draws about 120 kW, so racks add up to a large load quickly. A large campus is hundreds of megawatts to over a gigawatt.",
            "A single rack with its green status lights lit, its busway tap running down to it from the gold bus.",
        )
        .detail(
            "Density is what makes the campus large.",
            &["~120 kW per NVL72 rack", "Campus: hundreds of MW to over 1 GW"],
        ),
];

/// 6 the queue: studied at the gate, 1,400 GW waiting, 55 months from request to operation.
const S6_B: &[Beat] = &[
    Beat::new("studied at the gate", BEAT_MS)
        .note(
            "Every new plant or large load is studied before it connects, and the grid operator does the study. Until it is approved, nothing is built.",
            "Projects lined up along the road to the substation gate; a cyan ring round the one at the gate, under study.",
        )
        .detail(
            "The grid operators do the study.",
            &["Interconnection queue"],
        ),
    Beat::new("1,400 GW and 890 GW waiting", BEAT_MS)
        .note(
            "About 1,400 GW of generation and 890 GW of storage were waiting in US queues at the end of 2024.",
            "The board beside the gate, its gold tiles lit as the months pass.",
        )
        .detail(
            "Queued projects wait years for a connection.",
            &["~1,400 GW generation queued", "890 GW storage queued (end of 2024)"],
        ),
    Beat::new("55 months from request", BEAT_MS)
        .note(
            "Projects built in 2024 took 55 months on average from request to operation, so the queue often sets when a campus can open.",
            "The campus at the far edge, with the board's tiles counting the months.",
        )
        .detail(
            "The queue, not the chips, often sets the date.",
            &["55 months, request to operation (2024)", "LBNL Queued Up 2025"],
        ),
];

/// 7 PUE, on site: site power over IT power, the cooling overhead, and a campus's own plant.
const S7_B: &[Beat] = &[
    Beat::new("site power over IT power", BEAT_MS)
        .note(
            "PUE is total site power divided by the power that reaches the IT equipment. Efficient hyperscale sites run near 1.1 to 1.2.",
            "The data hall with its racks and the cooling units on its roof, with beads running along the busways into the racks.",
        )
        .detail(
            "PUE = site power / IT power.",
            &["Efficient sites ~1.1-1.2"],
        ),
    Beat::new("the rest is cooling and losses", BEAT_MS)
        .note(
            "The rest goes to cooling and conversion losses. At PUE 1.2, 100 MW of IT needs 120 MW from the grid.",
            "Orange heat rising off the roof's cooling units, and orange beads climbing a riser up to them.",
        )
        .detail(
            "20% overhead at PUE 1.2.",
            &["At PUE 1.2, 100 MW of IT = 120 MW from the grid"],
        ),
    Beat::new("behind the meter", BEAT_MS)
        .note(
            "Where the grid cannot connect fast enough, a campus can make power on site with gas turbines, or deal with nearby nuclear plants.",
            "A gas-turbine enclosure beside the hall, with a stack and a yellow fuel line running in.",
        )
        .detail(
            "Behind the meter: power made on site.",
            &["Gas turbine on site", "Own plant and fuel supply"],
        ),
];

/// 8 who makes it: the producers and utilities, the turbine and grid-equipment makers, the transmission builders.
const S8_B: &[Beat] = &[
    Beat::new("utilities and producers", BEAT_MS)
        .note(
            "The utilities and power producers include NextEra (NEE), Vistra (VST), Constellation (CEG), Dominion (D) and Southern (SO).",
            "A power plant with cooling towers and a transmission tower, the labels pinned on the parts they stand for.",
        )
        .detail(
            "Producers and utilities own the supply.",
            &["NextEra (NEE), Vistra (VST), Constellation (CEG)"],
        ),
    Beat::new("turbines and grid equipment", BEAT_MS)
        .note(
            "Turbine and grid-equipment makers include GE Vernova (GEV), Siemens Energy and Mitsubishi Heavy. Each sells a few large machines to a few buyers.",
            "The turbine hall with its stack, a gas-turbine enclosure, and grid towers with silver conductors.",
        )
        .detail(
            "Few makers, long order books.",
            &["GE Vernova (GEV), Siemens Energy", "Mitsubishi Heavy"],
        ),
    Beat::new("who builds the lines", BEAT_MS)
        .note(
            "Transmission is built by utilities and contractors such as Quanta (PWR). The companies here are the ones behind the grid a campus connects to.",
            "A lattice tower under construction at the edge of the scene, with conductors being strung between towers.",
        )
        .detail(
            "Transmission is built by utilities and contractors.",
            &["Quanta (PWR)"],
        ),
];

/// 9 chokepoints: queues take years, new lines take a decade, large loads raise prices.
const S9_B: &[Beat] = &[
    Beat::new("queues take years", BEAT_MS)
        .note(
            "Interconnection queues take years, and the study comes before any build. A project built in 2024 took 55 months on average.",
            "The queue at the gate: projects waiting, with a cyan ring on the one under study.",
        )
        .detail(
            "The queue is the first bottleneck.",
            &["Queues: years", "55 months (2024)"],
        ),
    Beat::new("new lines take a decade", BEAT_MS)
        .note(
            "New transmission lines take a decade to permit and build, so a campus cannot count on a new line for its opening date.",
            "A lattice tower and its conductors, with more towers running on into the distance.",
        )
        .detail(
            "Lines are slow to permit and build.",
            &["New transmission lines: about a decade"],
        ),
    Beat::new("large loads raise prices", BEAT_MS)
        .note(
            "Large loads raise prices for other customers, which draws regulators in. The utility sells its power under rates that regulators set.",
            "The utility meter and cabinet at the edge of the campus, with the hall behind it and beads running through the meter.",
        )
        .detail(
            "Rates are set by regulators.",
            &["Utility sells power under regulated rates"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
