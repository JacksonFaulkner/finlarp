// NETWORK+COOL tab, SERVER: lettered zoom-ins a-e (tools/pbr3d/blender/net_server_zooms.py, GLBs in
// tools/pbr3d/assets/net_server_zoom_<letter>.glb): a GPU + cold plate, b NVSwitch, c PCIe switches, d NICs and DPUs,
// e out to the leaf.

use super::super::super::blender::{page, Cell};
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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("dies and HBM", BEAT_MS)
        .note(
            "The cut-open module: two GPU dies in the middle of the package and HBM stacks beside them. The dies glow as they work.",
            "A close view of a cut-away module: purple dies glowing amber, blue HBM blocks either side, a copper plate above.",
        )
        .detail(
            "About a kilowatt from one package.",
            &["~1 kW per GPU", "8 HBM stacks"],
        ),
    Beat::new("coolant through the fins", BEAT_MS)
        .note(
            "Cool liquid drops into the plate and runs between thin copper fins just above the dies, picking up their heat.",
            "Blue beads drop down the blue barb and stream across the copper comb of fins.",
        )
        .detail(
            "Microchannels give the water a large copper surface.",
            &["COLD PLATE", "Microchannel fins"],
        ),
    Beat::new("warm coolant out", BEAT_MS)
        .note(
            "The water leaves warmer through the outlet barb and rises to the return rail running back to the header.",
            "Orange beads leave the plate by the orange barb and travel back along the orange rail.",
        )
        .detail(
            "Warm water goes back to the CDU.",
            &["Return rail", "To the rack manifold"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("GPU to switch to GPU", BEAT_MS)
        .note(
            "A packet from one GPU travels along copper lanes to an NVSwitch chip and back out to another GPU.",
            "Green beads run along copper traces from a cold plate to a finned switch chip and on to a plate in the other row.",
        )
        .detail(
            "Every hop goes through a switch.",
            &["NVLINK", "GPU > NVSwitch > GPU"],
        ),
    Beat::new("every GPU wired to both", BEAT_MS)
        .note(
            "Each GPU's lanes are split between the two switch chips, so either switch can reach every GPU.",
            "A closer view of the two finned chips with traces arriving from all eight plates and green beads on every one.",
        )
        .detail(
            "Two chips, eight GPUs, full connectivity.",
            &["NVSWITCH x2", "18 links per GPU"],
        ),
    Beat::new("all to all", BEAT_MS)
        .note(
            "All pairs talk at once at full speed. Each GPU gets 1.8 TB/s; the board totals 14.4 TB/s.",
            "The whole baseboard from above with green beads crossing between all eight plates through the two chips.",
        )
        .detail(
            "Full bandwidth between any pair.",
            &["1.8 TB/s per GPU", "14.4 TB/s total"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("GPU, switch, NIC", BEAT_MS)
        .note(
            "A GPU's PCIe link crosses a ribbon cable to a PCIe switch on the host board and on to its own NIC.",
            "Amber beads run from a cold plate, over grey ribbon cables, into a finned switch and forward to a card.",
        )
        .detail(
            "The PCIe switch is the GPU's road to the network.",
            &["PCIE SWITCH", "1 GPU : 1 NIC"],
        ),
    Beat::new("the CPU at the root", BEAT_MS)
        .note(
            "The CPU sits at the top of the PCIe tree, and an NVMe drive hangs off each switch for fast local storage.",
            "Violet beads run from a copper CPU plate to the switches, and short beads into the small NVMe sticks beside them.",
        )
        .detail(
            "The CPU sets up the transfers.",
            &["CPU: PCIe root", "NVMe per switch"],
        ),
    Beat::new("GPUDirect RDMA", BEAT_MS)
        .note(
            "With GPUDirect RDMA the NIC reads GPU memory straight through the switch, skipping the CPU and its memory.",
            "Amber beads run from all eight GPUs through the four switches to the NICs, with the CPUs left quiet.",
        )
        .detail(
            "The data never touches CPU memory.",
            &["GPUDirect RDMA", "No CPU copy"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("ConnectX NIC", BEAT_MS)
        .note(
            "Each NIC is a ConnectX chip under a small heatsink on a card at the front edge, with an OSFP cage poking out of the front panel.",
            "A close view of the front row: green cards with finned chips and silver cages, magenta packets leaving the cages.",
        )
        .detail(
            "One NIC per GPU.",
            &["CONNECTX-7: 400G", "CONNECTX-8: 800G"],
        ),
    Beat::new("cages and LEDs", BEAT_MS)
        .note(
            "A transceiver plugs into each cage and turns the electrical signal into light. Port LEDs blink as traffic flows.",
            "Silver cages with transceivers and aqua pull tabs; small green LEDs blink on top.",
        )
        .detail(
            "The cage is where copper becomes optics.",
            &["OSFP", "Transceivers"],
        ),
    Beat::new("BlueField DPUs", BEAT_MS)
        .note(
            "Two DPUs sit in the middle of the row with two ports each. They run storage and front-end traffic to a separate switch.",
            "Two purple-boarded cards with double cages, cyan beads leaving along aqua cables to a small switch at the right.",
        )
        .detail(
            "The DPU offloads networking and storage.",
            &["BLUEFIELD-3", "Front end + storage"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("one cable per NIC", BEAT_MS)
        .note(
            "Each NIC's transceiver sends light up its own cable. Eight cables leave the node.",
            "Gold cables climb from the front cages with magenta packets on them.",
        )
        .detail(
            "Eight cables, one per GPU.",
            &["8 cables", "Optics or copper"],
        ),
    Beat::new("the leaf switch", BEAT_MS)
        .note(
            "The cables land on a leaf switch at the top of the rack or the end of the row. Its port LEDs blink with the traffic.",
            "A dark switch above the node with rows of black ports, green LEDs blinking, cables arriving from below.",
        )
        .detail(
            "The leaf is the first hop of the fabric.",
            &["LEAF SWITCH", "400-800 Gb/s a port"],
        ),
    Beat::new("rail-optimised", BEAT_MS)
        .note(
            "In a rail-optimised fabric, NIC 1 of every server goes to rail switch 1, NIC 2 to rail 2, and so on, so GPUs of the same rank are one hop apart.",
            "Eight small rail switches above the node, with cables from the node and from two neighbouring servers all landing on matching rails.",
        )
        .detail(
            "GPU k in every server shares a rail.",
            &["RAIL-OPTIMISED", "8 rails"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "GPU + cold plate",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "NVSwitch",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "PCIe switches",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "NICs and DPUs",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "out to the leaf",
        build: zoom_e,
    },
];
