// POWER tab, UPS: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_UPS.txt, from the
// Blender scenes in tools/pbr3d/blender/power_ups_sections.py (GLBs in tools/pbr3d/assets/power_ups_section_<n>.glb).
// Three beats each. The Sources heading (10) is text only. The close-ups stand on a bench beside the cut-open site.

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

/// 1 what happens: batteries bridge the gap until generators run.
const S1_B: &[Beat] = &[
    Beat::new("the utility feeds the UPS", BEAT_MS)
        .note(
            "Utility power comes down the pole and through the transfer switch into the UPS. Inside, the rectifier turns it to DC, and the inverter turns that back into clean AC for the racks.",
            "Yellow beads run from the utility line through the transfer switch into the grey UPS lineup, then out to the racks at the far end of the bench.",
        )
        .detail(
            "Rectifier in, inverter out.",
            &["RECTIFIER: AC to DC", "INVERTER: clean AC"],
        ),
    Beat::new("the utility fails, the batteries carry", BEAT_MS)
        .note(
            "When the utility drops, the batteries feed the DC link and the inverter keeps running. The racks see no break at all, because the load was never on the utility directly.",
            "The utility line turns red; orange battery power flows into the DC link and out through the inverter, which stays lit.",
        )
        .detail(
            "No break at the racks.",
            &["Batteries feed the DC link", "Inverter keeps running"],
        ),
    Beat::new("the generator takes over", BEAT_MS)
        .note(
            "The generator starts on its signal and comes up to voltage and frequency. The transfer switch then moves the UPS input over to it, and the batteries begin to recharge.",
            "The engine and alternator spin up at the left; the transfer switch's blade swings across, and green generator power runs into the UPS input.",
        )
        .detail(
            "Generator power replaces the batteries as the source.",
            &["GENERATOR starts", "TRANSFER SWITCH moves"],
        ),
];

/// 2 the parts: the lineup, the battery cabinets, the generator and the transfer switch.
const S2_B: &[Beat] = &[
    Beat::new("the UPS lineup", BEAT_MS)
        .note(
            "The UPS lineup is a row of grey cabinets: the rectifier, the DC link and the inverter. Power passes from one to the next, and each cabinet is cut open at the front so its boards and bridges show.",
            "The cabinets cut open at the front: the rectifier at the left with its bridge on a heatsink, the DC link's capacitors in the middle, and the inverter at the right.",
        )
        .detail(
            "Double conversion: AC to DC to AC.",
            &["RECTIFIER, DC LINK, INVERTER", "The load runs from the inverter"],
        ),
    Beat::new("the lithium-ion cabinets", BEAT_MS)
        .note(
            "Beside the lineup stand rows of lithium-ion battery cabinets, each a stack of modules with its own LED. The DC link keeps them charged, and they hold the energy that carries the load between an outage and generator start.",
            "Tall blue cabinets stacked with modules, their green LEDs lit, with cyan dots running from the DC link into their tops.",
        )
        .detail(
            "Runtime is minutes, not hours.",
            &["LITHIUM-ION cabinets", "RUNTIME: minutes"],
        ),
    Beat::new("the generator and the switch", BEAT_MS)
        .note(
            "The diesel generator sits outside on its pad, a diesel engine driving an alternator. The transfer switch between it and the UPS moves the input from the utility to the generator.",
            "A grey genset at the right with its copper alternator and exhaust stack, and the transfer switch's blade at the top of the site, pointing at the UPS.",
        )
        .detail(
            "About 2-3 MW per unit.",
            &["DIESEL: engine + alternator", "TRANSFER SWITCH (ATS)"],
        ),
];

/// 3 a power cut, in order: the utility drops, the inverter runs on battery, the generator starts, the switch moves.
const S3_B: &[Beat] = &[
    Beat::new("1-2: the feed drops; the inverter runs on battery", BEAT_MS)
        .note(
            "Step 1: the utility feed drops, and its line at the pole goes red. Step 2: the inverter keeps running on battery DC, so the output to the racks never breaks.",
            "The utility cable at the top of the pole is red; orange dots run from the battery cabinet to the inverter, which stays lit and feeds the racks.",
        )
        .detail(
            "Interruption at the racks: none.",
            &["1: utility feed drops", "2: inverter on battery DC"],
        ),
    Beat::new("3-4: start signal, at speed in about ten seconds", BEAT_MS)
        .note(
            "Step 3: the controller sends the generator its start signal. Step 4: within about ten seconds the engine fires and the alternator reaches voltage and frequency.",
            "A small signal bead runs to the generator, which fires: its pistons move and the alternator at the right spins up.",
        )
        .detail(
            "Standby within 10 seconds, NFPA 110 Type 10.",
            &["3: start signal", "4: at voltage and speed, ~10 s"],
        ),
    Beat::new("5-6: the switch moves; the batteries recharge", BEAT_MS)
        .note(
            "Step 5: the transfer switch moves the UPS input to the generators. Step 6: the batteries recharge; when the utility returns, the load moves back the same way.",
            "The transfer switch's blade swings to the generator; green power runs in, and cyan dots flow back into the battery cabinets to refill them.",
        )
        .detail(
            "The load moves back once the utility returns.",
            &["5: TRANSFER SWITCH to generators", "6: batteries recharge"],
        ),
];

/// 4 double conversion: dirty in, clean out, 3-5% lost as heat, eco mode through the static bypass.
const S4_B: &[Beat] = &[
    Beat::new("dirty in, clean out", BEAT_MS)
        .note(
            "Sags, spikes and the outage itself all arrive at the UPS's input. Every watt is rectified to DC and inverted back into clean AC, so the racks are fed from the inverter and never see those disturbances.",
            "Jagged yellow beads, sags and spikes, enter the cabinet at the left; clean AC beads leave the inverter at the right.",
        )
        .detail(
            "Double conversion hides the grid's disturbances.",
            &["Every watt rectified", "Clean AC from the inverter"],
        ),
    Beat::new("two conversions lose 3-5%", BEAT_MS)
        .note(
            "The losses in the rectifier and inverter bridges turn into heat, which rises off their heatsinks. This page's example puts the total at 3-5%, and that heat must also be cooled.",
            "Close in on the two bridges: heat shimmer rises off the heatsinks of the rectifier and the inverter, and the cooling fins glow faintly warm.",
        )
        .detail(
            "Two conversions cost a few percent.",
            &["3-5% lost as heat (this page's example)", "~3-5 MW of heat on a 100 MW site"],
        ),
    Beat::new("eco mode: the static bypass", BEAT_MS)
        .note(
            "In eco mode the static bypass closes and the utility goes around the conversion straight to the racks. The rectifier and inverter sit idle, which saves the losses at the cost of the protection.",
            "The static bypass switch closes; a yellow line runs from the utility straight to the racks, and the rectifier and inverter go dim.",
        )
        .detail(
            "Eco modes skip the conversion when the utility is clean.",
            &["Static bypass: utility straight through", "Rectifier and inverter idle"],
        ),
];

/// 5 batteries: a lithium-ion cell cut open; Li-ion against lead-acid; runtime measured in minutes.
const S5_B: &[Beat] = &[
    Beat::new("a lithium-ion cell, cut open", BEAT_MS)
        .note(
            "A lithium-ion cell cut open on the bench: a graphite anode and an oxide cathode on aluminium foil, with a thin separator between them. Its energy is stored in the chemistry between those layers.",
            "The cell's wall is cut away; the layers show as bands: dark graphite anode, a pale separator, and the cathode foil, with a cyan dot of charge at each side.",
        )
        .detail(
            "Lithium-ion is the chemistry replacing lead-acid.",
            &["Graphite anode", "Oxide cathode on Al foil"],
        ),
    Beat::new("Li-ion against lead-acid", BEAT_MS)
        .note(
            "Beside the lithium-ion cell stands a lead-acid (VRLA) block for the same energy. The lithium-ion version is smaller and lighter and lasts longer, which matters as UPS rooms grow.",
            "The two cells side by side on the bench: a small blue lithium-ion block and a larger grey lead-acid block with its lead plates visible.",
        )
        .detail(
            "Smaller, lighter, and longer-lived.",
            &["Li-ion: smaller, lighter", "Lead-acid (VRLA): lead plates"],
        ),
    Beat::new("runtime: minutes, not hours", BEAT_MS)
        .note(
            "Runtime is how long the batteries carry full load: here, minutes, enough to cover the generator's start. Carrying the load for hours would need far more cabinets than a site can hold.",
            "The battery cabinet at the right of the racks, its modules draining, with a label marking the runtime in minutes.",
        )
        .detail(
            "Runtime is sized for minutes.",
            &["RUNTIME: minutes", "Hours would need far more cabinets"],
        ),
];

/// 6 generators: the genset cut open; start within 10 s; a row of sets with fuel on site.
const S6_B: &[Beat] = &[
    Beat::new("the diesel genset, cut open", BEAT_MS)
        .note(
            "A standby genset is a diesel engine driving an alternator. Cut open here, its six cylinders, the alternator's stator and rotor, and the radiator and fan at the end are all visible.",
            "The genset cut open: the grey engine with six cylinders at the left, the copper alternator at the right, and the radiator and fan above the set.",
        )
        .detail(
            "Engine and alternator in one set.",
            &["Diesel engine: six cylinders", "Alternator: stator + rotor"],
        ),
    Beat::new("firing, then within 10 seconds", BEAT_MS)
        .note(
            "On its start signal the pistons fire and the alternator turns, reaching voltage and speed within about ten seconds. Power then runs out to the transfer switch.",
            "The pistons in the engine fire in sequence; the alternator spins; a bead of power runs out along the cable toward the switch.",
        )
        .detail(
            "NFPA 110 Type 10 requires standby within 10 seconds.",
            &["Within 10 s", "Power out to the switch"],
        ),
    Beat::new("a row of gensets, fuel on site", BEAT_MS)
        .note(
            "A site has a row of these sets outside the hall, each about 2-3 MW, with fuel stored on site. The fuel is what sets how long a site can run on generators in a long outage.",
            "A row of gensets on their concrete pads outside, each with its exhaust stack, and a fuel tank at the end of the row.",
        )
        .detail(
            "About 2-3 MW each; fuel for a day or more.",
            &["About 2-3 MW each", "Fuel on site: a day or more"],
        ),
];

/// 7 AI loads: GPU racks swing; the swings travel upstream; in-rack batteries or capacitors smooth them.
const S7_B: &[Beat] = &[
    Beat::new("GPUs: full power, then idle", BEAT_MS)
        .note(
            "A GPU rack swings between full power and idle in milliseconds, as training steps sync up across thousands of chips. The swings are sudden and in step with one another.",
            "The rack's LEDs flash together, full and then idle; a row of purple compute trays pulses in step as the GPUs swing.",
        )
        .detail(
            "The swings come in milliseconds.",
            &["Full power to idle in ms", "Training steps sync up"],
        ),
    Beat::new("the swings reach the UPS", BEAT_MS)
        .note(
            "The swings travel upstream: the inverter sees the spiky draw, and the generators and the grid feel it too. The UPS was not designed for loads that swing this fast.",
            "Bursts of orange dots run from the rack back along the cable to the inverter; a red warning light flashes at its top.",
        )
        .detail(
            "Rapid swings stress UPS, generators and the grid.",
            &["Spiky draw at the inverter", "Not what UPS systems were built for"],
        ),
    Beat::new("in-rack batteries smooth them", BEAT_MS)
        .note(
            "Newer designs add batteries or capacitors inside the rack. They supply the swing locally, so the upstream draw settles into a steady line.",
            "A small battery or capacitor block inside the rack glows at its base; the swings smooth into a steady beam of dots running upstream.",
        )
        .detail(
            "Storage in the rack smooths the swings.",
            &["Batteries or capacitors in the rack", "Steady draw upstream"],
        ),
];

/// 8 who makes it: UPS makers, generator makers, battery makers.
const S8_B: &[Beat] = &[
    Beat::new("UPS makers", BEAT_MS)
        .note(
            "The UPS lineup is made by a few large power-equipment firms. Vertiv (VRT), Schneider Electric, Eaton (ETN) and ABB build the rectifier, inverter and DC-link cabinets in rows like these.",
            "The UPS cabinets with name tags on each: Vertiv at the rectifier, Schneider at the DC link, Eaton at the inverter.",
        )
        .detail(
            "Four large makers in this market.",
            &["Vertiv (VRT)", "Schneider Electric; Eaton (ETN); ABB"],
        ),
    Beat::new("generator makers", BEAT_MS)
        .note(
            "Standby gensets come from engine makers: Caterpillar (CAT), Cummins (CMI), Rolls-Royce (mtu) and Kohler. Each row of sets on the bench is one of these firms' products.",
            "A row of gensets on the bench, each tagged with its maker: Caterpillar at the top, Cummins and Rolls-Royce next to it.",
        )
        .detail(
            "The engines are standard industrial diesels.",
            &["Caterpillar (CAT); Cummins (CMI)", "Rolls-Royce (mtu); Kohler"],
        ),
    Beat::new("battery makers", BEAT_MS)
        .note(
            "Lithium-ion cells for UPS cabinets come from Asian battery makers: Samsung SDI, LG, CATL and others. The cells in each module come from the same supply chains.",
            "Four cells stand in a row on the bench, each tagged: Samsung SDI, LG, CATL, and a space for the others.",
        )
        .detail(
            "Cells come from a few Asian makers.",
            &["Samsung SDI; LG; CATL", "and others"],
        ),
];

/// 9 chokepoints: generator lead times and air permits; losses scale with every MW; spiky loads.
const S9_B: &[Beat] = &[
    Beat::new("generator lead times", BEAT_MS)
        .note(
            "The generators are the slow part. Each set needs a pad, a permit for its diesel exhaust, and a truck to bring it, so the pads wait for the next genset to arrive.",
            "Concrete pads stand empty on the bench; one genset arrives on a truck, and a stack of diesel exhaust rises from a set already in place.",
        )
        .detail(
            "Gensets and air permits take time.",
            &["Generator lead times", "Diesel exhaust: air permits"],
        ),
    Beat::new("losses scale with every MW", BEAT_MS)
        .note(
            "Each megawatt that passes through a UPS loses a few percent as heat, so more MW means more converters, each shedding heat. The losses rise in step with the load.",
            "A row of conversion cabinets in a hall, each with heat rising from its top, and the row grows longer across the frame.",
        )
        .detail(
            "Losses rise with every megawatt.",
            &["3-5% as heat", "More MW, more converters"],
        ),
    Beat::new("spiky loads were not planned for", BEAT_MS)
        .note(
            "GPU racks with sudden swings are the new stress. UPS systems were designed for steadier loads, so the swings land on the inverter with nothing to smooth them.",
            "Spiky orange bursts run from the racks toward the inverter, and a red warning light flashes above it.",
        )
        .detail(
            "Spiky AI loads, UPS not designed for them.",
            &["Spiky AI loads", "UPS not designed for this"],
        ),
];


fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
