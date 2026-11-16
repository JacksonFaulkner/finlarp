// POWER tab, UPS: lettered zoom-ins a-e. Each is the overview's scene with the camera held on one subject
// (tools/pbr3d/blender/power_ups_zooms.py, GLBs in tools/pbr3d/assets/power_ups_zoom_<letter>.glb):
// a inside a UPS, b a power cut second by second, c batteries and runtime, d generators, e efficiency.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_ups_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the rectifier", BEAT_MS)
        .note(
            "Inside the cabinet, incoming AC meets the rectifier: an input inductor and a bridge of power transistors on a finned heatsink. Its output is DC, which charges the batteries and feeds the inverter.",
            "The cabinet's door swung open: a dark input inductor at the left, a grey IGBT bridge on its heatsink, and copper bus bars running out to the DC link.",
        )
        .detail(
            "The rectifier is the first conversion and the first place power becomes heat.",
            &["RECTIFIER: AC to DC", "Input inductor and IGBT bridge"],
        ),
    Beat::new("the DC link and the batteries", BEAT_MS)
        .note(
            "The DC link is a bank of capacitors that holds the DC steady between the rectifier and the inverter. From it, DC runs out to the lithium-ion cabinets, which charge as long as the utility is up.",
            "Grey capacitor cans in a row in the middle of the cabinet; cyan dots run out of the link toward the blue battery modules, whose charge LEDs light.",
        )
        .detail(
            "The link keeps the battery and the inverter fed from one DC bus.",
            &["DC LINK: capacitors", "Li-ion cabinets charge from it"],
        ),
    Beat::new("the inverter makes clean AC", BEAT_MS)
        .note(
            "The inverter is a second IGBT bridge with an output filter. It switches the DC back into a clean AC waveform, which runs out to the racks; the load never sees the utility directly.",
            "The inverter's bridge and filter inductor glow at the right of the cabinet, and clean AC beads run out of its top to the racks.",
        )
        .detail(
            "Double conversion: the load always runs from the inverter.",
            &["INVERTER: DC to AC", "Output filter, then the racks"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("0 s: the utility is lost", BEAT_MS)
        .note(
            "At the instant of the outage the utility line goes red at the pole. Nothing moves at the racks: the batteries take over the DC link, and the inverter keeps running with no break.",
            "The utility cable turns red at the top of the pole; orange battery power flows into the DC link and the inverter stays lit.",
        )
        .detail(
            "The inverter never stops, so the racks see no interruption.",
            &["0 ms interruption at the racks", "Batteries feed the DC link"],
        ),
    Beat::new("~10 s: the generator is up", BEAT_MS)
        .note(
            "The diesel engine cranks and fires, its pistons and crankshaft turning as the alternator spins up. Within about ten seconds it reaches voltage and speed, and its exhaust rises from the stack.",
            "The engine's row of pistons moves at the left, the alternator turns at the right, and a plume of exhaust climbs from the stack.",
        )
        .detail(
            "NFPA 110 Type 10 requires standby power within 10 seconds.",
            &["~10 s to voltage and frequency"],
        ),
    Beat::new("the transfer switch hands over", BEAT_MS)
        .note(
            "The transfer switch's blade swings from the utility to the generator, so green generator power runs back into the UPS input. The generator then carries the load, and the batteries recharge.",
            "The switch's blade rotates on its top; green beads run from the generator to the UPS input, and the rectifier's red lamp comes back on.",
        )
        .detail(
            "The UPS input moves from utility to generator.",
            &["TRANSFER SWITCH", "Batteries recharge on generator power"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("the lithium-ion cabinets", BEAT_MS)
        .note(
            "The lithium-ion cabinets are rows of battery modules, each a stack of prismatic cells with its own charge LED. They take a fraction of the space and weight of lead-acid for the same energy.",
            "A tall blue cabinet with stacked modules, each with a small green LED; cyan dots show the charge coming in at its top.",
        )
        .detail(
            "Lithium-ion replaces lead-acid in UPS rooms.",
            &["LITHIUM-ION cells", "Charge LEDs per module"],
        ),
    Beat::new("the modules drain", BEAT_MS)
        .note(
            "On battery power the modules drain one LED at a time, and orange battery DC flows out of the cabinets to the inverter. The runtime is measured in minutes, long enough to cover generator start.",
            "The modules' LEDs go dark from the top down; orange dots run out of the cabinet's base toward the DC link.",
        )
        .detail(
            "RUNTIME is typically minutes, not hours.",
            &["Sized to bridge the generator start", "Hours would need far more cells"],
        ),
    Beat::new("the recharge", BEAT_MS)
        .note(
            "Once the generator carries the site, DC from the rectifier flows back through the link into the cabinets, and their LEDs fill again. The cycle restarts until the batteries are full.",
            "Cyan dots run from the DC link into the cabinets, and the module LEDs light again from the bottom up.",
        )
        .detail(
            "Recharging takes the place of the outage's draw.",
            &["DC from the rectifier", "The DC link feeds the cabinets"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("the diesel and the alternator", BEAT_MS)
        .note(
            "A standby generator is a large diesel engine driving an alternator. Its radiator sits above the engine and the panel at the end reports its output, which is about 2-3 MW per set.",
            "The cut-away generator: the grey diesel engine at the left, the copper-wound alternator at the right, a radiator above and the control panel at the end.",
        )
        .detail(
            "Each set is about 2-3 MW.",
            &["Diesel engine + alternator", "About 2-3 MW per set"],
        ),
    Beat::new("pistons and the crank", BEAT_MS)
        .note(
            "With the start signal, the pistons move and the crankshaft turns, and the turbocharger and exhaust spin up. The engine reaches its speed within about ten seconds.",
            "Close in on the pistons in their row and the crankshaft between them, with the turbo and exhaust pipe glowing at the top.",
        )
        .detail(
            "Start within 10 seconds is the standby rule.",
            &["~10 s to speed and voltage"],
        ),
    Beat::new("the fuel tank", BEAT_MS)
        .note(
            "The belly fuel tank under the set is cut open to show the diesel inside. Fuel on site is what sets how long a site can run on generators in a long outage.",
            "The tank under the engine, cut open, with the diesel in it, and the running engine and alternator above.",
        )
        .detail(
            "Fuel on site sets how long a site survives a long outage.",
            &["Diesel fuel on site", "Typically a day or more"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("two conversions", BEAT_MS)
        .note(
            "Each watt passes through the rectifier and then the inverter. Both are drawn in the cabinet at the left; the orange and cyan beads show the power on its way through them.",
            "The rectifier and inverter bridges in their cabinets, with a bead of power passing through each and the DC link between.",
        )
        .detail(
            "Every watt is converted twice.",
            &["Conversion 1: rectifier", "Conversion 2: inverter"],
        ),
    Beat::new("3-5% lost as heat", BEAT_MS)
        .note(
            "The losses in the two bridges turn into heat, which rises off their heatsinks. On a 100 MW site a few percent is several megawatts that the cooling plant must also remove.",
            "Close in on the heatsinks: heat shimmer rises from the rectifier and the inverter, and the cooling fins glow faintly warm.",
        )
        .detail(
            "Two conversions lose a few percent, this page's example puts it at 3-5%.",
            &["3-5% lost as heat (this page's example)", "~3-5 MW heat on a 100 MW site"],
        ),
    Beat::new("eco mode: the static bypass", BEAT_MS)
        .note(
            "In eco mode the static bypass closes and the utility feeds the racks directly, so the rectifier and inverter sit idle. The cost is that the racks lose the conversion's protection from sags and spikes.",
            "The static bypass switch closes at the left; a yellow line runs straight from the utility to the racks, and the rectifier and inverter go dim.",
        )
        .detail(
            "Eco modes bypass conversion when the utility is clean.",
            &["Static bypass: utility straight through", "Conversion idle in eco mode"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "inside a UPS",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "a power cut, second by second",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "batteries and runtime",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "generators",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "efficiency",
        build: zoom_e,
    },
];
