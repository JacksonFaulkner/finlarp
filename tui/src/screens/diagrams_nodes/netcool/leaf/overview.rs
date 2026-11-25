// NETWORK+COOL tab, LEAF: the page's overview, a Blender scene (tools/pbr3d/blender/net_leaf_overview.py, GLB
// tools/pbr3d/assets/net_leaf_overview.glb). Seven beats: the leaf tier, downlinks, the ASIC, uplinks, ECMP,
// congestion, the whole fabric.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match net_leaf_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the leaf tier", BEAT_MS)
        .note(
            "Every row of GPU racks has a network rack in the middle, and near its top sits the leaf switch. Behind are more rows, each with its own leaf, and at the right four spine switches tie them all together.",
            "A row of dark racks with an open network rack in the middle; a cut-open switch near its top; three more rows behind; four tall spine racks at the right; grey cable trays overhead.",
        )
        .detail(
            "One leaf per row; every leaf talks to every spine.",
            &["LEAF SWITCH: top of the row", "SPINE SWITCH: 4 here"],
        ),
    Beat::new("servers to the leaf", BEAT_MS)
        .note(
            "Each 8-GPU server has 800G NIC ports. Short passive copper DAC cables reach the leaf from the racks beside it; the outer racks need active optical cables.",
            "Cyan packets run from small port cages on each server along grey and aqua cables up to the bottom row of the leaf's ports.",
        )
        .detail(
            "32 downlinks, one per server port.",
            &["DAC: ~2 m at 800G", "AOC: the outer racks"],
        ),
    Beat::new("inside the leaf", BEAT_MS)
        .note(
            "Packets ride copper SerDes traces from the port cages into one switch ASIC under a finned heatsink. It looks up each header and sends the packet out of the right port. Fans push air front to back.",
            "The switch lid cut away: a green board, a grey finned heatsink in the middle glowing underneath, copper traces fanning to the cages, fans along the back with blue air leaving.",
        )
        .detail(
            "One chip switches 51.2 Tb/s.",
            &["SWITCH ASIC: 51.2 Tb/s", "SERDES: 512 x 100G"],
        ),
    Beat::new("uplinks to the spines", BEAT_MS)
        .note(
            "The top row of 32 ports carries 800G optical modules. Yellow single-mode fibre rises to the overhead tray and runs to the spine row, a quarter of the uplinks to each spine.",
            "Yellow fibres gather from the top port row into four bundles that climb to the tray and run right to the spine racks.",
        )
        .detail(
            "Uplinks leave on light, not copper.",
            &["800G OPTICS: DR8", "SINGLE-MODE FIBRE: 500 m"],
        ),
    Beat::new("leaf-spine and ECMP", BEAT_MS)
        .note(
            "Any leaf reaches any other through one spine, so every path is three hops. The leaf hashes each flow onto one of four equal-cost paths, spreading traffic across all spines.",
            "Green packets leave the front row's leaf, split over the four spine bundles, and drop into the leaf of the back row.",
        )
        .detail(
            "Equal-cost multipath across the spines.",
            &["ECMP: hash per flow", "LEAF-SPINE: 3 hops"],
        ),
    Beat::new("congestion", BEAT_MS)
        .note(
            "When many servers send to one place at once, an egress port's queue fills. Lossless RoCE fabrics then send pause frames back toward the senders, and ECN marks tell them to slow down.",
            "Cyan packets crowd into the leaf; an orange stack builds at one uplink port; red beads run back down the cables to the servers.",
        )
        .detail(
            "Lossless Ethernet needs flow control.",
            &["PFC: pause frames", "OVERSUBSCRIPTION: 1:1 here"],
        ),
    Beat::new("the whole fabric", BEAT_MS)
        .note(
            "Every row's leaf carries traffic to every spine at once. With 32 ports down and 32 up, this leaf is non-blocking, the rule for AI training clusters.",
            "The whole hall from above: every overhead fibre bundle lit, packets moving between rows and the spine racks.",
        )
        .detail(
            "A non-blocking two-tier fabric.",
            &["32 down, 32 up", "4 rows x 4 spines"],
        ),
];
