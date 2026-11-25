// NETWORK+COOL tab, COLD PLATE: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_COLD_PLATE.txt, from
// the Blender scenes in tools/pbr3d/blender/net_cold_plate_sections.py (GLBs in tools/pbr3d/assets/net_cold_plate_section_<n>.glb).
// Three beats each. The Sources heading (10) is text only.

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

/// 1 what happens.
const S1_B: &[Beat] = &[
    Beat::new("cool in", BEAT_MS)
        .note(
            "Cool coolant comes in from the manifold and hose onto the plate.",
            "Blue beads along the hose into the plate's riser.",
        )
        .detail("Supply.", &["MANIFOLD", "QUICK DISCONNECT"]),
    Beat::new("heat into the fins", BEAT_MS)
        .note(
            "The GPU's heat crosses the TIM and base into the fins.",
            "Glowing dies and orange dots rising into the fins.",
        )
        .detail("Through the copper.", &["TIM", "MICROCHANNEL"]),
    Beat::new("warm out", BEAT_MS)
        .note(
            "Warm water at 45-60 C leaves for the return manifold.",
            "Orange beads leave the plate and climb the red pipe.",
        )
        .detail("Return.", &["WARM WATER", "MANIFOLD"]),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("package and TIM", BEAT_MS)
        .note(
            "The dies and HBM sit on the substrate; TIM covers them.",
            "A close cut-away of dies, HBM and a silver TIM strip.",
        )
        .detail("The heat source.", &["TIM"]),
    Beat::new("plate", BEAT_MS)
        .note(
            "The copper base, microchannel fins and cover with its inlet.",
            "The plate's copper base and fins under the grey cover.",
        )
        .detail("The cold plate.", &["COLD PLATE", "BASE", "MICROCHANNEL"]),
    Beat::new("tray plumbing", BEAT_MS)
        .note(
            "Hoses, quick disconnects and the rack manifolds.",
            "Black hoses to couplings and the blue and red pipes.",
        )
        .detail("The loop.", &["QUICK DISCONNECT", "MANIFOLD"]),
];

/// 3 in order.
const S3_B: &[Beat] = &[
    Beat::new("manifold to hose", BEAT_MS)
        .note(
            "Supply manifold, quick disconnect, hose.",
            "Blue beads up the pipe, through the coupling and down the hose.",
        )
        .detail("Steps 1-3.", &["MANIFOLD", "QUICK DISCONNECT"]),
    Beat::new("through the plate", BEAT_MS)
        .note(
            "Inlet over the dies, along the microchannels, into the outlet plenum.",
            "Beads drop into the fins, run them blue then orange.",
        )
        .detail("Steps 4-5.", &["MICROCHANNEL"]),
    Beat::new("back out", BEAT_MS)
        .note(
            "Hose, quick disconnect, return manifold.",
            "Orange beads out the hose and up the red pipe.",
        )
        .detail("Step 6.", &["WARM WATER", "CDU"]),
];

/// 4 why liquid.
const S4_B: &[Beat] = &[
    Beat::new("a kilowatt on a chip", BEAT_MS)
        .note(
            "A GPU's 1,000-1,400 W on a few square centimetres is too much for fins and fans.",
            "Glowing dies with heat billowing above the plate.",
        )
        .detail("Heat flux is the problem.", &["~1,000-1,400 W"]),
    Beat::new("water carries it", BEAT_MS)
        .note(
            "Per litre, water holds about 3,500 times the heat air does.",
            "Water running through the fins, glowing orange.",
        )
        .detail(
            "A small flow does a lot.",
            &["~3,500x air per litre", "~1-1.5 L/min per kW"],
        ),
    Beat::new("racks of 120 kW", BEAT_MS)
        .note(
            "An NVL72 rack runs about 120-130 kW; air tops out near 40-50 kW.",
            "The rack pulled back: stacked trays and both manifolds flowing.",
        )
        .detail(
            "Density forces liquid.",
            &["NVL72: ~120-130 kW", "Air: ~40-50 kW"],
        ),
];

/// 5 microchannels.
const S5_B: &[Beat] = &[
    Beat::new("fins and channels", BEAT_MS)
        .note(
            "A slice of base and fins, five times larger: copper fins with channels between.",
            "Big copper fins standing on a copper base over a purple die.",
        )
        .detail("The surface the water touches.", &["MICROCHANNEL", "BASE"]),
    Beat::new("water warms", BEAT_MS)
        .note(
            "Heat climbs the fins; the water warms from blue to orange as it passes.",
            "Orange dots climb the fins; beads change from blue to orange.",
        )
        .detail("Heat into the flow.", &["Fins ~0.1-0.2 mm"]),
    Beat::new("jet impingement", BEAT_MS)
        .note(
            "Many plates drop the water straight onto the hot spot and split it both ways.",
            "A nozzle block on top with blue beads falling into the fins.",
        )
        .detail("Hot spot first.", &["Split flow", "Skived copper"]),
];

/// 6 TIM.
const S6_B: &[Beat] = &[
    Beat::new("air in the gaps", BEAT_MS)
        .note(
            "Die and copper touch only at high points; the gaps hold air, an insulator.",
            "Rough purple and copper surfaces with black voids between.",
        )
        .detail("Air blocks heat.", &["TIM: needed"]),
    Beat::new("TIM fills them", BEAT_MS)
        .note(
            "The TIM fills every gap: grease, pad, liquid metal or indium.",
            "A silver layer fills the gap between die and copper.",
        )
        .detail("No air left.", &["TIM"]),
    Beat::new("heat crosses", BEAT_MS)
        .note(
            "Heat crosses the TIM into the copper; thinner layers resist less.",
            "Orange dots climb from the die through the silver layer into the copper.",
        )
        .detail("Thin is good.", &["TIM: biggest single drop"]),
];

/// 7 quick disconnects.
const S7_B: &[Beat] = &[
    Beat::new("mated and flowing", BEAT_MS)
        .note(
            "One coupling cut open: poppets pushed back, water flowing through.",
            "Two steel halves joined, springs compressed, blue beads crossing.",
        )
        .detail("Open when joined.", &["QUICK DISCONNECT"]),
    Beat::new("parted and sealed", BEAT_MS)
        .note(
            "As the halves part, springs shut both poppets; the flat faces barely wet.",
            "The halves separate; the poppets snap to the faces.",
        )
        .detail("Dripless.", &["Poppet valves", "Flat faces"]),
    Beat::new("blind-mate", BEAT_MS)
        .note(
            "Pushed together, they reopen: the tray needs no tools.",
            "The halves rejoin and water flows again.",
        )
        .detail("Push to connect.", &["OCP UQD", "O-ring seals"]),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("cold plates", BEAT_MS)
        .note(
            "CoolIT, Boyd, Cooler Master, AVC, Auras, Delta and JetCool (Flex) make plates.",
            "The plate cut-away with maker tags.",
        )
        .detail(
            "Many plate makers.",
            &["AVC 3017.TW", "Auras 3324.TW", "FLEX"],
        ),
    Beat::new("couplings", BEAT_MS)
        .note(
            "Staubli, CPC, Parker and Danfoss make quick disconnects.",
            "The couplings at the tray's rear.",
        )
        .detail("A tight supply.", &["PH"]),
    Beat::new("manifolds and CDUs", BEAT_MS)
        .note(
            "Vertiv, nVent, Schneider, Supermicro, Delta and Modine make manifolds and CDUs.",
            "The rack pulled back with both manifolds.",
        )
        .detail("Rack-level gear.", &["VRT", "NVT", "SMCI", "MOD"]),
];

/// 9 chokepoints.
const S9_B: &[Beat] = &[
    Beat::new("a leak", BEAT_MS)
        .note(
            "A weeping coupling drips into the tray; sensors must catch it.",
            "Blue drops falling from a coupling, a red alarm blinking.",
        )
        .detail("Leaks are the fear.", &["Leak detection"]),
    Beat::new("warm water", BEAT_MS)
        .note(
            "45-60 C return water can skip chillers and even heat buildings.",
            "Orange beads leaving up the red pipe.",
        )
        .detail("Only if the site is built for it.", &["WARM WATER"]),
    Beat::new("more watts", BEAT_MS)
        .note(
            "Each GPU generation adds watts; plates and couplings ran short in the NVL72 ramp.",
            "The full rack with every flow lit.",
        )
        .detail("Supply and scale.", &["Plate + QD supply"]),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
