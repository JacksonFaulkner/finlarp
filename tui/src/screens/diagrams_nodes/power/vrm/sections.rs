// POWER tab, VRM: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/PWR_VRM.txt, from the
// Blender scenes in tools/pbr3d/blender/power_vrm_sections.py (GLBs in tools/pbr3d/assets/power_vrm_section_<n>.glb).
// Three beats each. The Sources heading (10) is text only.

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

/// 1 what happens: 50 V into the brick; 12 V through the phases; over 1,000 A into the package.
const S1_B: &[Beat] = &[
    Beat::new("50 V into the brick", BEAT_MS)
        .note(
            "About 50 V DC arrives from the busbar and enters the board at its edge. The converter brick steps it down to 12 V before anything else happens.",
            "Yellow beads run along the copper busbar at the left and into the grey brick; a brown 12 V tab leaves its far side.",
        )
        .detail(
            "The brick makes the intermediate bus.",
            &["~50 V DC in", "INTERMEDIATE BUS: 12 V out"],
        ),
    Beat::new("12 V through the phases", BEAT_MS)
        .note(
            "The 12 V crosses a bare plane to the row of phases on each side. Each phase chops it into pulses, and its inductor smooths them.",
            "Amber dots spread across the tan 12 V plane toward the dark power stages and their copper inductors lining the board.",
        )
        .detail(
            "Many phases share the current.",
            &["MULTIPHASE", "POWER STAGE: 12 V in"],
        ),
    Beat::new("over 1,000 A into the package", BEAT_MS)
        .note(
            "The inductors feed about 0.8 V into the package, and the current that reaches the GPU is well over a thousand amps. It flows up into the purple die through the board.",
            "Hot red current streams from the inductors across the board into the purple GPU package, which glows at its core.",
        )
        .detail(
            "Over a thousand amps reach one package.",
            &["CORE VOLTAGE ~0.8 V", "Well over 1,000 A"],
        ),
];

/// 2 the parts: the board's parts; one phase cut open; core voltage, vertical power, I2R.
const S2_B: &[Beat] = &[
    Beat::new("the board's parts", BEAT_MS)
        .note(
            "The board carries a handful of named parts: the brick, the controller, the phases and the GPU. Each one is drawn at a larger scale here so its role can be seen.",
            "The board enlarged at the centre: a grey brick at the left, a controller block, rows of dark phases, and the GPU package on the right with its die glowing.",
        )
        .detail(
            "Each part has one job on the board.",
            &["INTERMEDIATE BUS: brick", "VOLTAGE REGULATOR: controller", "MULTIPHASE: phases"],
        ),
    Beat::new("one phase cut open", BEAT_MS)
        .note(
            "One phase is cut open to show its parts: the power stage's transistors and driver, and the inductor under them. Heat builds in the stage, and the inductor's copper carries the current out.",
            "A single phase enlarged: a dark power stage with its high- and low-side switches in a row, and a grey ferrite inductor with copper windings beside it.",
        )
        .detail(
            "The power stage and the inductor make one phase.",
            &["POWER STAGE: FETs + driver", "INDUCTOR: ferrite + copper"],
        ),
    Beat::new("core voltage, vertical power, I2R", BEAT_MS)
        .note(
            "Three terms tie the board together: the core voltage the GPU runs at, the vertical power layout that moves regulators under it, and the I2R loss that the path length drives up. Each is tagged on the board.",
            "The die glows at the centre with its tag; a row of grey modules sits on the back under the package, and a warm red patch marks the copper where loss builds up.",
        )
        .detail(
            "Three numbers to remember from the board.",
            &["CORE VOLTAGE ~0.8 V", "VERTICAL POWER: under the GPU", "I2R LOSS: hot copper"],
        ),
];

/// 3 in order: busbar and brick; controller and stages; inductor, board, package, GPU.
const S3_B: &[Beat] = &[
    Beat::new("busbar and brick", BEAT_MS)
        .note(
            "The chain starts at the busbar: about 50 V DC arrives at the board's edge and the brick steps it to 12 V. The 12 V then runs to the phases.",
            "Yellow beads ride the copper busbar into the grey brick at the left; amber beads leave the brick's tab toward the bare plane.",
        )
        .detail(
            "Steps 1 and 2 of the chain.",
            &["1. ~50 V DC arrives", "2. Brick makes 12 V"],
        ),
    Beat::new("controller and stages", BEAT_MS)
        .note(
            "The controller decides when each phase switches and sends the timing out on thin PWM traces. Each power stage then chops the 12 V into pulses on its own turn.",
            "The grey controller block sends green traces along the board to the row of dark power stages, each lighting in turn as its pulses start.",
        )
        .detail(
            "Steps 3 and 4 of the chain.",
            &["3. Controller sets timing", "4. Power stage chops 12 V"],
        ),
    Beat::new("inductor, board, package, GPU", BEAT_MS)
        .note(
            "Each inductor smooths its pulses into about 0.8 V of current. All the currents run through the board and the package into the GPU, the last link in the chain.",
            "Copper inductors glowing with current, red streams running through the board and up into the purple GPU package and die.",
        )
        .detail(
            "Steps 5 and 6 of the chain.",
            &["5. Inductor: ~0.8 V current", "6. Board and package into the GPU"],
        ),
];

/// 4 why so much current: 1,000-1,200 W; at 0.8 V that is 1,250-1,500 A; split across 16 phases.
const S4_B: &[Beat] = &[
    Beat::new("1,000-1,200 W", BEAT_MS)
        .note(
            "A Blackwell GPU draws about 1,000 to 1,200 W. That is the power the board must deliver to a single chip, and the figure drives every choice in the layout.",
            "The GPU package enlarged at the centre: a grey substrate, the purple die, and HBM stacks at its sides, with the power figure beside it.",
        )
        .detail(
            "One GPU is a large load.",
            &["Blackwell GPU", "1,000-1,200 W"],
        ),
    Beat::new("0.8 V: 1,250-1,500 A", BEAT_MS)
        .note(
            "At a core voltage near 0.8 V, that power is 1,250 to 1,500 amps. The current is what makes the board hard, because it has to pass through copper rather than wire.",
            "The die face lit amber at the centre, with a row of current arrows coming up from the board and the power equation P = V x I floating beside it.",
        )
        .detail(
            "Low volts, high amps.",
            &["CORE VOLTAGE ~0.8 V", "~1,250-1,500 A"],
        ),
    Beat::new("split across 16 phases", BEAT_MS)
        .note(
            "No single regulator can switch that much current, so the design splits it across 16 phases, each carrying tens of amps. Infineon's 16-phase design was the first to deliver over 1,000 A, in 2019.",
            "The phases along both sides of the board, each lit with its own amber stream, converging on the GPU die at the centre.",
        )
        .detail(
            "Sixteen phases share the load.",
            &["16 phases", "Infineon: first 1,000+ A, 2019"],
        ),
];

/// 5 phases: one phase's inductor storing energy; staggered ripples cancel; capacitors answer first.
const S5_B: &[Beat] = &[
    Beat::new("tens of amps per phase", BEAT_MS)
        .note(
            "Each phase carries only tens of amps, and its inductor is the part that holds that current. The inductor stores energy during each pulse and releases it between them.",
            "A phase drawn large: a grey ferrite inductor with copper windings at the centre, and a power stage on top switching on and off in a small scope trace.",
        )
        .detail(
            "The inductor stores energy between pulses.",
            &["INDUCTOR stores energy", "Tens of amps per phase"],
        ),
    Beat::new("the ripples cancel", BEAT_MS)
        .note(
            "Each phase makes its own ripple, but the controller staggers them in time. The ripples of the phases together cancel, so the sum is nearly steady.",
            "Several amber ripple traces, each offset in time, sum into one flat amber line at the top of a small scope.",
        )
        .detail(
            "Staggering the phases smooths the sum.",
            &["Staggered in time", "Ripples cancel"],
        ),
    Beat::new("capacitors answer first", BEAT_MS)
        .note(
            "Capacitors near the GPU supply the instant current when the chip's load jumps. They react faster than any regulator, which is why they sit so close to the die.",
            "Grey capacitor cans in a row by the GPU package, with a bright flash at the die as the current steps up and the capacitors discharge into it.",
        )
        .detail(
            "The capacitors cover the gap until the regulators catch up.",
            &["Capacitors by the GPU", "Faster than the regulator"],
        ),
];

/// 6 I2R loss: twice the current, four times the heat; 225 W in 0.1 milliohm; shorter path.
const S6_B: &[Beat] = &[
    Beat::new("2x current, 4x heat", BEAT_MS)
        .note(
            "Loss in the copper goes with the square of the current. Double the current and the heat goes up four times, so the hottest copper is the one carrying the most amps.",
            "Two copper bars side by side: the one at the left carries one unit of current and glows dim, the one at the right carries two and glows far hotter.",
        )
        .detail(
            "Heat goes as the current squared.",
            &["1x current: 1x heat", "2x current: 4x heat"],
        ),
    Beat::new("0.1 mOhm = 225 W", BEAT_MS)
        .note(
            "At 1,500 A, a tenth of a milliohm of resistance wastes about 225 watts. The 0.8 V plane is where this happens, and the heat it makes warms the board.",
            "The 0.8 V plane laid bare and glowing orange along its length, with a bright hot spot at the centre where the current crosses it.",
        )
        .detail(
            "225 W from a tenth of a milliohm.",
            &["0.1 mOhm at 1,500 A", "= 225 W"],
        ),
    Beat::new("every millimetre costs", BEAT_MS)
        .note(
            "Every millimetre of the current path costs power and voltage drop. This is why designers push the regulators as close to the GPU as they can get them.",
            "A short red path running from a regulator to the GPU package, with the regulator and the die both lit and the path between them shortened to a few millimetres.",
        )
        .detail(
            "The shorter the path, the less it loses.",
            &["Path: millimetres", "Regulators as close as possible"],
        ),
];

/// 7 vertical: beside the GPU; modules under it; seen from below.
const S7_B: &[Beat] = &[
    Beat::new("beside the GPU", BEAT_MS)
        .note(
            "Today the regulators sit beside the GPU. The current has to cross the board sideways to reach the package, and that path is the source of much of the loss.",
            "The usual layout: dark phases lined up beside the purple GPU, with amber current arcing sideways across the green board.",
        )
        .detail(
            "Beside the GPU is the usual layout.",
            &["Phases beside the GPU", "Current crosses the board"],
        ),
    Beat::new("onto the board's back", BEAT_MS)
        .note(
            "Vertical power moves the regulators onto the back of the board, directly under the GPU package. The current goes straight up through the board instead of across it.",
            "The phases slide off the sides; grey vertical modules sit on the board's back beneath the purple package, and an amber column rises up through the board.",
        )
        .detail(
            "Vertical power puts the modules under the package.",
            &["VERTICAL POWER: on the back", "Straight up through the board"],
        ),
    Beat::new("16 stacked regulators", BEAT_MS)
        .note(
            "Crescendo showed 16 stacked regulators delivering close to 1,000 A at 0.75 V in this layout. Infineon introduced its vertical modules in 2026.",
            "A seen-from-below view: a stack of grey regulator modules under the board, with the amber current rising from them to the GPU die above.",
        )
        .detail(
            "Two vertical-power designs, 2026.",
            &["Crescendo: ~1,000 A at 0.75 V", "Infineon modules: 2026"],
        ),
];

/// 8 who makes it: makers tagged on controller, stages, brick and vertical modules.
const S8_B: &[Beat] = &[
    Beat::new("controllers and stages", BEAT_MS)
        .note(
            "The controller and the power stages come from a small group of chip makers. Infineon and Renesas make them, with Monolithic Power Systems and Texas Instruments also in the field.",
            "The controller block and the row of power stages tagged with their maker names in small labels along the board.",
        )
        .detail(
            "Makers of controllers and power stages.",
            &["Infineon, Renesas", "MPS (MPWR), Texas Instruments"],
        ),
    Beat::new("the bus converter brick", BEAT_MS)
        .note(
            "The 50 V to 12 V brick is made by power-module makers. Vicor is among them, and the same group of chip makers also supplies parts for the brick.",
            "The grey brick at the left edge tagged with its maker's name, and the converter's transformer shown with a second tag.",
        )
        .detail(
            "Brick makers overlap with the chip makers.",
            &["Vicor (VICR)", "Infineon, MPS, TI, Renesas"],
        ),
    Beat::new("vertical modules", BEAT_MS)
        .note(
            "Vertical power modules come from Delta and others, with Infineon's 2026 vertical modules on the same list. Market shares are not sourced here, so the tags name makers only.",
            "The grey vertical modules under the GPU tagged with the makers' names; the GPU die beside them carries a note that shares are not sourced.",
        )
        .detail(
            "Shares are not sourced here.",
            &["Delta, others", "Infineon: vertical, 2026"],
        ),
];

/// 9 chokepoints: rising current; crowded board; regulator heat under a cold plate.
const S9_B: &[Beat] = &[
    Beat::new("current outruns voltage", BEAT_MS)
        .note(
            "The current the GPU needs keeps rising faster than its core voltage falls. Each generation asks for more amps through the same board, and that gets harder to deliver.",
            "The die glowing amber with a rising amber current trace beside it, climbing above a flat, lower voltage trace.",
        )
        .detail(
            "Current rises faster than voltage falls.",
            &["More amps every generation", "Core voltage ~0.8 V"],
        ),
    Beat::new("a crowded board", BEAT_MS)
        .note(
            "The memory and the I/O around the GPU take up space that the regulators would like. The phases end up squeezed beside the HBM stacks, with little room to spare.",
            "HBM stacks along the die in grey, the phases squeezed in beside them in a tight row, and the I/O edges of the package crowded in red.",
        )
        .detail(
            "The board area is crowded.",
            &["HBM along the dies", "I/O needs this space too"],
        ),
    Beat::new("regulator heat under a cold plate", BEAT_MS)
        .note(
            "In a liquid-cooled tray, the cold plate sits on the GPU and carries away its heat. The regulator heat has to be added to that same load.",
            "A blue cold plate laid over the GPU package with its pipes in and out at the top; the phases below it glow warm, and their heat rises toward the plate.",
        )
        .detail(
            "Regulator heat adds to the GPU's own.",
            &["Liquid cold plate on the GPU", "Regulator heat adds to it"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_vrm_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
