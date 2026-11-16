// TRANSCEIVER: lettered zoom-ins a-e. Each is its own three-beat close-up built from the overview's parts
// (tools/pbr3d/blender/fiber_module_zooms.py, GLBs in tools/pbr3d/assets/fiber_module_zoom_<letter>.glb): a the finned lid, b the TOSA port, c the ROSA can, d the PCB and chips,
// e the gold edge pins.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_zoom_e.glb"),
        E_B,
    )
}

/// Zoom a: the finned lid: fins, heat off them, cover and heat sink in one.
const A_B: &[Beat] = &[
    Beat::new("the finned lid", BEAT_MS)
        .note(
            "An OSFP's top cover is cast with fins running front to back, so the lid is also the module's heat sink. That is why OSFP has room for about 25 W, more than the smaller QSFP-DD.",
            "The module in its cage: the grey finned lid on top, the fins parallel to the module's length.",
        )
        .detail(
            "Fins add area for the air to take the heat.",
            &["OSFP: room for about 25 W", "Fins run front to back"],
        ),
    Beat::new("heat rises off the fins", BEAT_MS)
        .note(
            "Running, the module's power ends up as heat in the lid, and the fins shed it into the air the switch's fans push across them. Listings put 1.6T DSP modules at up to about 25-26 W each.",
            "Orange heat beads rising off the fin tops.",
        )
        .detail(
            "Heat sets how much a module can do.",
            &["1.6T DSP modules: up to ~25-26 W"],
        ),
    Beat::new("the lid is cover and heat sink", BEAT_MS)
        .note(
            "A cut across the module through the DSP shows why: a pedestal cast into the lid presses on a thermal pad over the hot DSP die, so the heat flows straight up through the lid and out into the fins.",
            "A cross-section: the DSP glowing orange on the board, the pedestal and lid above it, the comb of fins, orange beads rising from the die into the fins.",
        )
        .detail(
            "One metal part closes the module and cools it.",
            &["DSP: the hottest chip", "Pad, pedestal, lid, fins"],
        ),
];

/// Zoom b: the transmit side of the MPO port.
const B_B: &[Beat] = &[
    Beat::new("TOSA: the transmit port", BEAT_MS)
        .note(
            "The module's optical port is one MPO connector in its nose. In a DR8 module, eight of its sixteen fibre positions carry the transmit light from the TOSA, one fibre per lane.",
            "The module's nose: the black MPO port with its row of fibre ends, the white fibres running back to the open TOSA package behind it.",
        )
        .detail(
            "Transmit and receive share one connector.",
            &["MPO: 12 or 16 fibres in one plug", "DR8: 8 transmit fibres"],
        ),
    Beat::new("light leaves through the port", BEAT_MS)
        .note(
            "The eight lasers light, and their beams run along the fibres to the MPO face and out into the cable, one lane per fibre. Single-mode DR8 links reach about 500 m.",
            "The lasers glowing orange in the TOSA, orange beads running along the fibres and out of the port, the eight transmit fibre ends lit.",
        )
        .detail(
            "Reach decides the optics.",
            &["DR8: ~500 m", "2xFR4: 4 wavelengths per fibre, 2 km"],
        ),
    Beat::new("the receive port beside it", BEAT_MS)
        .note(
            "Right beside the transmit fibres in the same MPO are eight receive fibres, bringing light from the far end back to the ROSA. A 2xFR4 module instead puts four wavelengths on each fibre and uses two duplex LC ports.",
            "Orange beads coming in at the port and running back along the receive fibres toward the ROSA; the other eight fibre ends now lit.",
        )
        .detail(
            "DR8 needs 16 fibres; 2xFR4 only 4.",
            &["DR8: 8 out + 8 in", "2xFR4: 4 fibres in all"],
        ),
];

/// Zoom c: the ROSA, its photodiodes, and the TIA beside it.
const C_B: &[Beat] = &[
    Beat::new("ROSA: the receive optics", BEAT_MS)
        .note(
            "The ROSA (receiver optical sub-assembly) is a small gold-plated package that takes the incoming fibres and turns their light back into electrical signals. It sits beside the TOSA at the front of the board.",
            "The closed tan ROSA package, with white fibres coming in from the MPO on the left and gold leads out to the chip behind it.",
        )
        .detail(
            "The same module sends and receives.",
            &["Photodiodes and TIAs turn light back into lanes"],
        ),
    Beat::new("light lands on the photodiodes", BEAT_MS)
        .note(
            "Inside, each fibre's light passes a small lens that focuses it onto its own photodiode. The photodiode releases a current that follows the light's four PAM4 levels.",
            "Lid off: orange beads arriving along the fibres through the clear fibre block and the row of lenses onto the eight photodiodes, which glow orange.",
        )
        .detail(
            "One photodiode per lane.",
            &["8 photodiodes (DR8)", "Lenses couple fibre to chip"],
        ),
    Beat::new("the amplifier beside the package", BEAT_MS)
        .note(
            "The photodiode current is tiny, so arched gold bond wires carry it a few millimetres to the TIA (transimpedance amplifier), which turns it into a voltage the DSP can read. Short wires mean less noise.",
            "Cyan beads riding the arched gold bond wires from the photodiodes to the TIA chip, which glows cyan.",
        )
        .detail(
            "The TIA's noise sets how weak a signal the module can read.",
            &["TIA: current in, voltage out"],
        ),
];

/// Zoom d: the module PCB, the laser driver, the TIA.
const D_B: &[Beat] = &[
    Beat::new("the PCB: the module's circuit board", BEAT_MS)
        .note(
            "Everything in the module sits on one small circuit board: the optics at the front, the laser driver and TIA behind them, the PAM4 DSP in the middle, a small controller and power parts at the back, and the gold card edge at the very end.",
            "The open board from above: the two optics packages, two dark chips, the tan DSP package and the small black controller.",
        )
        .detail(
            "One board, both directions.",
            &["DSP, driver, TIA, controller", "Controller reports power, temperature, light"],
        ),
    Beat::new("the laser driver chip", BEAT_MS)
        .note(
            "The laser driver takes each retimed lane from the DSP and amplifies it into the drive the laser needs. Arched gold bond wires carry each channel over to its lead and on to its laser chip.",
            "The driver glowing cyan; beads ride in along the traces from the DSP and over the arched bond wires to the eight lasers, which glow orange.",
        )
        .detail(
            "One driver channel per laser.",
            &["8 channels (DR8)", "Bond wires a few mm long"],
        ),
    Beat::new("the amplifier chip (TIA)", BEAT_MS)
        .note(
            "On the receive side, the TIA takes the photodiodes' currents over the bond wires, turns them into voltages and sends them along the traces to the DSP, which cleans them up and sends them out to the host.",
            "The TIA glowing cyan; beads ride from the photodiodes over the bond wires into it, then out along the traces toward the DSP.",
        )
        .detail(
            "Driver and TIA are the analog pair.",
            &["LPO drops the DSP; these two remain"],
        ),
];

/// Zoom e: the gold card edge and the host connector.
const E_B: &[Beat] = &[
    Beat::new("gold edge pins", BEAT_MS)
        .note(
            "The module's plug is the end of its circuit board, plated with gold fingers on both faces. The switch's connector at the back of the cage is a slot lined with spring contacts at the same pitch.",
            "The module just short of the connector: the green board end with gold stripes, and the black connector cut open to show its gold springs.",
        )
        .detail(
            "Gold for many clean insertions.",
            &["OSFP: 60 contacts", "QSFP-DD: 76 contacts"],
        ),
    Beat::new("data comes in to the pins", BEAT_MS)
        .note(
            "Pushed home, each finger lands on its spring and the switch's lanes run in along the board traces into the module. Each lane is a differential pair carrying 100 Gb/s PAM4 in an 800G module.",
            "The card edge sliding into the slot; then cyan beads running in along the copper traces to the connector.",
        )
        .detail(
            "8 electrical lanes from the host chip.",
            &["800G: 8 x 100G lanes", "1.6T: 8 x 200G lanes"],
        ),
    Beat::new("data in and out at the pins", BEAT_MS)
        .note(
            "The same fingers carry both directions at once: eight lanes in to be sent as light, eight lanes out with what the module received, plus power and the management bus.",
            "Cyan beads running in along the traces and others running back out from the connector.",
        )
        .detail(
            "One plug, two directions.",
            &["8 lanes in, 8 lanes out", "Plus power and management"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the finned lid",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "TOSA: transmit port",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "ROSA: receive can",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "PCB and chips",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "gold edge pins",
        build: zoom_e,
    },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            super::super::super::super::blender::explained(s.as_ref(), z.label);
            super::super::super::super::blender::draws_every_beat(s.as_ref(), z.label);
        }
    }
}
