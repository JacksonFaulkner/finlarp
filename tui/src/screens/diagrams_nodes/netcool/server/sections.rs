// NETWORK+COOL tab, SERVER: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_SERVER.txt,
// from tools/pbr3d/blender/net_server_sections.py (GLBs in tools/pbr3d/assets/net_server_section_<n>.glb).
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
    Beat::new("GPU to GPU inside", BEAT_MS)
        .note(
            "Inside the node, GPUs talk over NVLink through the NVSwitch chips.",
            "Green beads cross the baseboard between plates through the two switch chips.",
        )
        .detail("Inside: NVLink.", &["NVLINK", "NVSWITCH"]),
    Beat::new("off the node", BEAT_MS)
        .note(
            "To reach another server, a GPU's data goes over PCIe to its NIC.",
            "Amber beads run from the GPUs through the PCIe switches to the cards at the front.",
        )
        .detail("Outside: a NIC per GPU.", &["PCIE SWITCH", "CONNECTX"]),
    Beat::new("up to the leaf", BEAT_MS)
        .note(
            "The NIC sends it out a cable to the leaf switch.",
            "Magenta packets climb gold cables to the leaf switch above.",
        )
        .detail(
            "The first hop of the fabric.",
            &["LEAF SWITCH", "400-800 Gb/s"],
        ),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("the baseboard", BEAT_MS)
        .note(
            "The HGX baseboard holds eight GPUs and two NVSwitch chips.",
            "The baseboard from above, dies glowing.",
        )
        .detail(
            "The GPU half.",
            &["HGX BASEBOARD", "NVSWITCH"],
        ),
    Beat::new("the host board", BEAT_MS)
        .note(
            "The host board holds two CPUs, their DDR5 and four PCIe switches, cabled to the baseboard.",
            "The teal host board with CPU plates, DIMMs, switches and ribbon cables.",
        )
        .detail(
            "The host half.",
            &["CPU", "PCIE SWITCH"],
        ),
    Beat::new("cards and coolant", BEAT_MS)
        .note(
            "Eight NICs and two DPUs line the front; coolant headers run along the rear.",
            "The whole node with tags on the cards and the headers.",
        )
        .detail(
            "The edges of the node.",
            &["CONNECTX", "BLUEFIELD-3 DPU", "COLD PLATE"],
        ),
];

/// 3 a packet's path.
const S3_B: &[Beat] = &[
    Beat::new("out of HBM", BEAT_MS)
        .note(
            "Data leaves the GPU's HBM and crosses the baseboard.",
            "Amber beads leave a GPU's HBM and run down its column.",
        )
        .detail("Start: GPU memory.", &["HBM", "Baseboard"]),
    Beat::new("switch and NIC", BEAT_MS)
        .note(
            "It passes the PCIe switch, enters the NIC and reaches the cage.",
            "Amber beads pass a finned switch and run into a card.",
        )
        .detail("PCIe all the way.", &["PCIE SWITCH", "CONNECTX"]),
    Beat::new("light and leaf", BEAT_MS)
        .note(
            "The transceiver turns it into light and the cable carries it to the leaf port.",
            "Magenta packets climb one gold cable to the leaf.",
        )
        .detail("Copper becomes optics.", &["OSFP", "LEAF SWITCH"]),
];

/// 4 NVLink and NVSwitch.
const S4_B: &[Beat] = &[
    Beat::new("one GPU's links", BEAT_MS)
        .note(
            "One GPU has 18 NVLink links, 1.8 TB/s in all, spread over both switch chips.",
            "Green beads leave one plate to all seven others.",
        )
        .detail("1.8 TB/s per GPU.", &["NVLINK 5", "18 links"]),
    Beat::new("two switches", BEAT_MS)
        .note(
            "Each NVSwitch chip takes half of every GPU's links.",
            "Green beads run through each switch chip in turn.",
        )
        .detail("Each switch reaches every GPU.", &["NVSWITCH x2"]),
    Beat::new("every pair at once", BEAT_MS)
        .note(
            "All 28 GPU pairs can run at full speed together; the board totals 14.4 TB/s.",
            "Green beads cross between all eight plates.",
        )
        .detail(
            "Non-blocking inside the node.",
            &["14.4 TB/s total", "28 pairs"],
        ),
];

/// 5 PCIe and the CPU.
const S5_B: &[Beat] = &[
    Beat::new("the switch tree", BEAT_MS)
        .note(
            "Four PCIe Gen5 switches each pair two GPUs with two NICs.",
            "Amber beads run from all eight GPUs into the four switches.",
        )
        .detail(
            "Two GPUs and two NICs per switch.",
            &["PCIE SWITCH x4", "Gen5 x16"],
        ),
    Beat::new("the CPU's memory", BEAT_MS)
        .note(
            "The two CPUs run the operating system from about 2 TB of DDR5.",
            "Violet beads run between the DIMM rows and the CPU plates.",
        )
        .detail("The host runs the jobs.", &["CPU x2", "DDR5 ~2 TB"]),
    Beat::new("GPUDirect RDMA", BEAT_MS)
        .note(
            "The NIC reads GPU memory straight through the switch; the CPU's memory is skipped.",
            "Amber beads from four GPUs go straight to their NICs.",
        )
        .detail("No bounce through the CPU.", &["GPUDirect RDMA"]),
];

/// 6 NICs, SuperNICs and the DPU.
const S6_B: &[Beat] = &[
    Beat::new("a NIC, enlarged", BEAT_MS)
        .note(
            "A ConnectX card three times larger: the chip under its heatsink takes PCIe in.",
            "A large green card with a finned chip and a big silver cage, amber beads arriving.",
        )
        .detail(
            "PCIe in, Ethernet or InfiniBand out.",
            &["CONNECTX"],
        ),
    Beat::new("the cage", BEAT_MS)
        .note(
            "Packets leave through the OSFP cage at 400 Gb/s (ConnectX-7) or 800 Gb/s (ConnectX-8 SuperNIC).",
            "Magenta packets stream out of the big cage; its LED blinks.",
        )
        .detail(
            "Speed doubles with ConnectX-8.",
            &["400G CX-7", "800G CX-8"],
        ),
    Beat::new("the DPUs", BEAT_MS)
        .note(
            "Two BlueField-3 DPUs carry storage and front-end traffic to their own switch.",
            "Cyan beads leave the two purple cards for the front-end switch.",
        )
        .detail(
            "A second network.",
            &["BLUEFIELD-3 DPU"],
        ),
];

/// 7 cooling the node.
const S7_B: &[Beat] = &[
    Beat::new("inside a cold plate", BEAT_MS)
        .note(
            "A cold plate three times larger, cut open: coolant runs through microchannels just above the dies.",
            "A large cut-away plate with blue beads crossing the fins and heat rising from glowing dies.",
        )
        .detail(
            "Heat goes straight into copper, then water.",
            &["COLD PLATE", "Microchannels"],
        ),
    Beat::new("supply and return", BEAT_MS)
        .note(
            "A supply rail feeds every plate; a return rail takes the warm water back.",
            "Blue beads run down the rails into the plates and orange beads come back.",
        )
        .detail(
            "Every GPU gets fresh coolant.",
            &["Supply rail", "Return rail"],
        ),
    Beat::new("to the rack manifold", BEAT_MS)
        .note(
            "Quick disconnects at the rear join the node to the rack manifold and the CDU.",
            "The two tall rear pipes with blue going down and orange going up.",
        )
        .detail(
            "Unplug without draining.",
            &["Quick disconnects", "Rack manifold"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("GPUs and memory", BEAT_MS)
        .note(
            "NVIDIA makes the GPUs, NVSwitch and baseboard; SK hynix, Micron and Samsung supply the HBM.",
            "Tags over the GPU plates.",
        )
        .detail(
            "NVIDIA designs the core.",
            &["NVDA", "MU"],
        ),
    Beat::new("switches, CPUs, NICs", BEAT_MS)
        .note(
            "Broadcom and Astera Labs supply PCIe switches and retimers; Intel and AMD the CPUs; NVIDIA the NICs and DPUs.",
            "Tags over the host board and front cards.",
        )
        .detail(
            "Many vendors in one box.",
            &["AVGO", "ALAB", "INTC", "AMD"],
        ),
    Beat::new("servers and cooling", BEAT_MS)
        .note(
            "Supermicro, Dell, HPE and Foxconn build the servers; Vertiv, CoolIT and Boyd the liquid cooling.",
            "Tags over the chassis and coolant headers.",
        )
        .detail(
            "Assembly and plumbing.",
            &["SMCI", "DELL", "VRT"],
        ),
];

/// 9 chokepoints.
const S9_B: &[Beat] = &[
    Beat::new("bandwidth per GPU", BEAT_MS)
        .note(
            "Network bandwidth per GPU has doubled to 800 Gb/s, and every port needs optics.",
            "Magenta packets fill all eight cables to the leaf.",
        )
        .detail("Optics scale with GPUs.", &["800G per GPU"]),
    Beat::new("PCIe lanes", BEAT_MS)
        .note(
            "Every GPU, NIC and drive shares the PCIe switches; Gen6 is arriving to keep up.",
            "Dense amber traffic through the four switches.",
        )
        .detail("PCIe is the inner bottleneck.", &["PCIe Gen5 > Gen6"]),
    Beat::new("heat", BEAT_MS)
        .note(
            "About 14 kW in one chassis: air cannot keep up and liquid is now standard.",
            "Dies glowing, heat rising, coolant running everywhere.",
        )
        .detail("Liquid is no longer optional.", &["~14 kW per node"]),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_server_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
