// NETWORK+COOL tab, SERVER: the page's overview, a Blender scene (tools/pbr3d/blender/net_server_overview.py, GLB
// tools/pbr3d/assets/net_server_overview.glb). Eight beats: an 8-GPU node, its GPUs, NVLink, PCIe, the NICs out to the
// leaf, the DPUs, cooling, and everything at once.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_server_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The eight beats of the overview (match net_server_overview.py).
pub const BEATS: &[Beat] = &[
    Beat::new("an 8-GPU node", BEAT_MS)
        .note(
            "An HGX-class server with its lid off: the GPU baseboard at the back carries eight GPUs under cold plates, the host board at the front carries two CPUs and four PCIe switches, and ten cards line the front edge.",
            "A grey open chassis: a green baseboard with eight grey cold plates and blue and orange coolant pipes at the back, a teal host board with copper CPU plates and green DIMM rows in front, and a row of silver cages along the front edge.",
        )
        .detail(
            "One node, eight GPUs, one chassis.",
            &["HGX B200: 8 GPUs", "~14 kW per node"],
        ),
    Beat::new("eight GPUs under cold plates", BEAT_MS)
        .note(
            "Each GPU module is a package with two dies and eight HBM stacks, and a copper cold plate sits on top. The front-left plate is cut open to show its fins.",
            "Two rows of four grey cold plates on the green board; the front-left one is cut away, showing purple dies, blue HBM blocks and copper fins, with the dies glowing amber.",
        )
        .detail(
            "Each GPU has its own HBM and its own cold plate.",
            &["180 GB HBM3e per GPU", "2 dies + 8 HBM stacks"],
        ),
    Beat::new("NVLink inside the node", BEAT_MS)
        .note(
            "Every GPU has copper NVLink lanes to both NVSwitch chips in the middle of the board, so any GPU can reach any other at full speed. Green packets run GPU to switch to GPU.",
            "Thin copper traces fan from every cold plate to two finned switch chips between the rows; green beads race along them in both directions.",
        )
        .detail(
            "NVLink keeps the eight GPUs acting as one.",
            &["NVLINK: 1.8 TB/s per GPU", "2 NVSwitch chips: 14.4 TB/s"],
        ),
    Beat::new("PCIe to the NICs", BEAT_MS)
        .note(
            "Each GPU also has a PCIe link. It runs over cables to a PCIe switch on the host board, which pairs two GPUs with two NICs and an NVMe drive. The CPUs sit at the top of the same switches.",
            "Amber beads leave each GPU, cross grey ribbon cables to four finned PCIe switches, then run forward to the cards at the front; violet beads run from the CPUs to the switches.",
        )
        .detail(
            "One NIC per GPU, through a PCIe switch.",
            &["PCIE SWITCH: Gen5", "GPUDirect RDMA"],
        ),
    Beat::new("out to the leaf", BEAT_MS)
        .note(
            "Each GPU's NIC sends its traffic out of an OSFP cage through a transceiver and a cable to the leaf switch above. The port LEDs blink as packets leave.",
            "Magenta packets leave eight silver cages at the front, climb gold cables to a dark leaf switch overhead, whose ports blink green.",
        )
        .detail(
            "Eight NICs, eight cables, one per GPU.",
            &["CONNECTX: 400-800 Gb/s", "3.2-6.4 Tb/s per node"],
        ),
    Beat::new("DPUs: front end and storage", BEAT_MS)
        .note(
            "Two BlueField DPUs in the middle of the front edge carry the node's other network: storage, management and user traffic, to a separate front-end switch. The CPUs and their memory run the operating system.",
            "Cyan beads leave two purple-boarded cards in the middle of the front row and run along aqua cables to a small switch at the right.",
        )
        .detail(
            "The compute fabric and the front end are separate networks.",
            &["BLUEFIELD-3 DPU", "2x 400 Gb/s"],
        ),
    Beat::new("coolant in, heat out", BEAT_MS)
        .note(
            "Cool liquid enters from the rack manifold through quick disconnects, runs down a supply rail to every cold plate, and leaves warm on a return rail. Each GPU puts about a kilowatt into the water.",
            "Blue beads come down a tall blue pipe at the rear, along the headers and into each cold plate; orange beads leave by the orange rails; amber heat lifts off every plate.",
        )
        .detail(
            "Liquid carries most of the node's heat away.",
            &["COLD PLATE: per GPU", "~1 kW per GPU"],
        ),
    Beat::new("the whole node", BEAT_MS)
        .note(
            "Everything at once: NVLink inside, PCIe to the NICs, memory traffic and coolant. About 14 kW goes into one chassis and leaves as data and warm water.",
            "The whole chassis from the other side, with green, amber, violet, blue and orange beads all moving and the GPU dies glowing.",
        )
        .detail(
            "One node is a small supercomputer.",
            &["~14 kW in", "8 GPUs, 10 NICs"],
        ),
];
