// NETWORK+COOL tab, CDU: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_CDU.txt, from
// the Blender scenes in tools/pbr3d/blender/net_cdu_sections.py (GLBs in tools/pbr3d/assets/net_cdu_section_<n>.glb).
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
    Beat::new("GPUs heat the cold plates", BEAT_MS)
        .note(
            "Each GPU draws around a kilowatt, and nearly all of it becomes heat in a copper cold plate pressed on top.",
            "The rack's trays: purple GPUs glowing under copper cold plates, with orange heat rising; cyan beads flow in, orange beads out.",
        )
        .detail(
            "The heat starts in the silicon.",
            &["COLD PLATE"],
        ),
    Beat::new("the secondary loop carries it", BEAT_MS)
        .note(
            "The secondary loop carries the heat out of the rack to the CDU, where pump A drives it round.",
            "The whole rack and CDU: orange beads up the return manifold and over to the cabinet, through the spinning pump.",
        )
        .detail(
            "Water carries far more heat than air.",
            &["SECONDARY LOOP"],
        ),
    Beat::new("facility water takes it away", BEAT_MS)
        .note(
            "In the plate heat exchanger the heat crosses into facility water, which leaves the room toward the chiller or cooling tower.",
            "The CDU cabinet: blue beads up into the plate stack and down out of it, sparks across the plates.",
        )
        .detail(
            "The CDU is the hand-off point.",
            &["PLATE HEAT EXCHANGER", "FACILITY LOOP"],
        ),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("the exchanger", BEAT_MS)
        .note(
            "The plate heat exchanger, with facility ports on one side and secondary ports on the other.",
            "Close on the blue-framed plate stack; steel ports at its corners, sparks hopping across.",
        )
        .detail(
            "The heart of the CDU.",
            &["PLATE HEAT EXCHANGER"],
        ),
    Beat::new("pumps, filter, reservoir", BEAT_MS)
        .note(
            "Two pumps, a canister filter and a reservoir move and condition the secondary coolant.",
            "The lower cabinet: two blue pumps, one cut open with a spinning impeller; the grey filter; copper pipes.",
        )
        .detail(
            "Move it, clean it, keep it topped up.",
            &["PUMP", "FILTER", "RESERVOIR"],
        ),
    Beat::new("controls and manifolds", BEAT_MS)
        .note(
            "A controller reads sensors on every pipe; in the rack, manifolds with quick disconnects feed every tray.",
            "The top of the cabinet with the white controller and blinking sensor LEDs, and the rack's back manifolds with gold couplings.",
        )
        .detail(
            "Measure, decide, distribute.",
            &["CONTROLLER (PLC)", "QUICK DISCONNECT"],
        ),
];

/// 3 in order.
const S3_B: &[Beat] = &[
    Beat::new("return, reservoir, pump", BEAT_MS)
        .note(
            "Warm coolant returns from the rack into the reservoir, then down to the running pump.",
            "Orange beads cross over the cabinet into the tank, then drop to the spinning pump.",
        )
        .detail(
            "Steps 1 to 3.",
            &["RESERVOIR", "PUMP"],
        ),
    Beat::new("filter, exchanger", BEAT_MS)
        .note(
            "The pump pushes it through the filter and up through the plate heat exchanger, where it gives up its heat.",
            "Orange beads rise through the filter canister and turn cyan as they zig-zag up the plate stack.",
        )
        .detail(
            "Steps 4 and 5.",
            &["FILTER", "PLATE HEAT EXCHANGER"],
        ),
    Beat::new("supply, cold plates, back", BEAT_MS)
        .note(
            "Cool supply goes out to the rack's supply manifold, through every cold plate and back up the return.",
            "Cyan beads leave the cabinet top, drop down the rack's supply manifold into the trays and leave orange.",
        )
        .detail(
            "Steps 6 to 8, then round again.",
            &["SECONDARY LOOP", "COLD PLATE"],
        ),
];

/// 4 why two loops.
const S4_B: &[Beat] = &[
    Beat::new("facility water stays out", BEAT_MS)
        .note(
            "Facility water is a large shared system that can carry scale, debris and pressure swings. It stops at the exchanger and never enters a server.",
            "Blue beads rise into the plate stack and return to the floor; the rack beyond stays dry of them.",
        )
        .detail(
            "Protect the servers from building water.",
            &["FACILITY LOOP"],
        ),
    Beat::new("a small, clean loop", BEAT_MS)
        .note(
            "The secondary loop holds only tens to hundreds of litres of treated coolant, such as water with 25% propylene glycol, filtered fine.",
            "Wide view: orange and cyan beads circling between the cabinet and the rack.",
        )
        .detail(
            "Small volume limits what a leak can spill.",
            &["SECONDARY LOOP", "PG25"],
        ),
    Beat::new("held above dew point", BEAT_MS)
        .note(
            "The CDU holds supply temperature, flow and pressure where the servers need them, and above the room's dew point so nothing condenses.",
            "The top of the cabinet: sensor stubs on the supply pipe and the controller box.",
        )
        .detail(
            "The CDU sets the conditions at the chip.",
            &["DEW POINT", "CONTROLLER (PLC)"],
        ),
];

/// 5 the plate heat exchanger.
const S5_B: &[Beat] = &[
    Beat::new("the stack", BEAT_MS)
        .note(
            "A real CDU exchanger holds roughly a hundred to a few hundred thin pressed plates, gasketed and bolted in a frame.",
            "The blue frame and grey plate stack, cyan beads zig-zagging across.",
        )
        .detail(
            "Area is what moves heat.",
            &["PLATE HEAT EXCHANGER"],
        ),
    Beat::new("counterflow", BEAT_MS)
        .note(
            "Two fluids run through alternate gaps in opposite directions.",
            "Blue beads zig-zag down the stack while cyan beads climb it.",
        )
        .detail(
            "Opposite directions keep a gap all the way.",
            &["Counterflow"],
        ),
    Beat::new("approach", BEAT_MS)
        .note(
            "The supply leaves within about 2 to 4 C of the incoming facility water. Adding plates adds capacity.",
            "Sparks hopping between plates while both bead streams run.",
        )
        .detail(
            "Smaller approach, warmer facility water allowed.",
            &["APPROACH: ~2-4 C"],
        ),
];

/// 6 pumps, filters, controls.
const S6_B: &[Beat] = &[
    Beat::new("N+1 pumps", BEAT_MS)
        .note(
            "Two variable-speed pumps, one running and one on standby.",
            "The two blue pumps; the first spinning, the second's amber LED blinking.",
        )
        .detail(
            "Never one pump between the GPUs and overheating.",
            &["N+1 pumps"],
        ),
    Beat::new("the filter", BEAT_MS)
        .note(
            "A canister filter on the discharge strains the coolant.",
            "The cut-open grey canister with its cream pleated element, beads passing up through.",
        )
        .detail("Protect the micro-channels.", &["FILTER"]),
    Beat::new("the controller", BEAT_MS)
        .note(
            "The PLC reads temperature, pressure and flow and moves the facility valve.",
            "Sensor LEDs blink and yellow beads run to the controller; the valve flag turns.",
        )
        .detail(
            "A control loop around the heat.",
            &["CONTROLLER (PLC)", "Control valve"],
        ),
];

/// 7 in-rack vs in-row.
const S7_B: &[Beat] = &[
    Beat::new("in-rack", BEAT_MS)
        .note(
            "A 4U in-rack CDU sits in the bottom of one rack with its own small exchanger and pumps.",
            "The grey box under the rack's lowest tray, lid off, beads flowing through it.",
        )
        .detail(
            "Self-contained per rack.",
            &["IN-RACK CDU"],
        ),
    Beat::new("one rack", BEAT_MS)
        .note(
            "It serves only that rack, about 100 to 250 kW. Supermicro's in-rack unit is rated 250 kW.",
            "The whole rack with the unit at its base.",
        )
        .detail(
            "Simple, but sized to one rack.",
            &["~100-250 kW"],
        ),
    Beat::new("in-row", BEAT_MS)
        .note(
            "An in-row CDU feeds a row of racks through a header. Vertiv's CoolChip range runs from in-rack units up to row units over 2 MW.",
            "The CDU and four racks, headers lit across the top.",
        )
        .detail(
            "Fewer, bigger units; shared redundancy.",
            &["IN-ROW CDU", "~1-2 MW+"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("row CDU makers", BEAT_MS)
        .note(
            "Vertiv, Schneider Electric (with Motivair), nVent and Modine build row-scale CDUs.",
            "The CDU cabinet with maker tags.",
        )
        .detail(
            "Power-and-cooling vendors lead here.",
            &["VRT", "NVT", "MOD"],
        ),
    Beat::new("in-rack and server makers", BEAT_MS)
        .note(
            "Supermicro builds in-rack CDUs as part of its rack-scale liquid cooling; CoolIT and Boyd supply rack CDUs and cold plates.",
            "The in-rack unit at the base of the rack, tagged.",
        )
        .detail(
            "Server makers sell the whole rack.",
            &["SMCI"],
        ),
    Beat::new("components", BEAT_MS)
        .note(
            "Delta, Nidec and LiquidStack build CDUs too; Danfoss and Alfa Laval are among the plate heat exchanger makers.",
            "The whole row, tagged.",
        )
        .detail(
            "Many suppliers; no share data here.",
            &["Delta", "Alfa Laval"],
        ),
];

/// 9 chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("leaks", BEAT_MS)
        .note(
            "Water near servers is the main fear. Quick disconnects and hoses are the usual leak points; leak sensors and alarms watch for them.",
            "Red drops fall from a tray onto the floor; the controller's red LED blinks.",
        )
        .detail(
            "Every joint is a risk.",
            &["QUICK DISCONNECT", "Leak detection"],
        ),
    Beat::new("a single point", BEAT_MS)
        .note(
            "One CDU can serve many racks, so a pump or controller failure would hit them all; redundant pumps and spare CDUs cover it.",
            "The standby pump spins up and takes the flow.",
        )
        .detail(
            "Redundancy at every level.",
            &["N+1 pumps"],
        ),
    Beat::new("rising heat", BEAT_MS)
        .note(
            "Racks have gone from about 130 kW to plans for 600 kW and more, so CDUs need more flow and bigger exchangers.",
            "The whole cabinet and rack running, GPUs glowing.",
        )
        .detail(
            "CDU capacity must track rack power.",
            &["~130 kW now", "~600 kW+ planned"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cdu_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
