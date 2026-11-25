// NETWORK+COOL tab, LEAF: lettered zoom-ins a-e. Each is the overview's fabric with the camera held on one subject
// (tools/pbr3d/blender/net_leaf_zooms.py, GLBs in tools/pbr3d/assets/net_leaf_zoom_<letter>.glb):
// a downlinks, b the switch, c uplinks, d ECMP, e congestion.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("the server's NIC", BEAT_MS)
        .note(
            "Each 8-GPU server carries NICs with 800G ports, about one per GPU pair or GPU in newer builds. The port cages sit on the server's front, nearest the leaf.",
            "A close view of a server's front: small silver port cages near its edge, with grey cables leaving them.",
        )
        .detail(
            "The NIC is where the fabric starts.",
            &["NIC: 400G-800G per GPU", "8-GPU server"],
        ),
    Beat::new("copper DAC", BEAT_MS)
        .note(
            "The racks beside the leaf use direct-attach copper: twinax pairs with no electronics, the cheapest and lowest-power link. At 100G per lane its reach is only about two metres.",
            "Grey cables run up the rack edges, across under the switch and into the bottom port row, cyan packets riding them.",
        )
        .detail(
            "Passive copper: cheap, short.",
            &["DAC: ~2 m at 800G", "No power, ~0 latency"],
        ),
    Beat::new("AOC from the outer racks", BEAT_MS)
        .note(
            "The outer racks are too far for passive copper, so they use active optical cables: lasers and receivers built into each plug, joined by thin fibre. They reach tens of metres but cost more.",
            "Aqua cables from the outermost racks join the grey ones into the switch; the whole row's cabling visible.",
        )
        .detail(
            "Optics in the plug buy distance.",
            &["AOC: up to ~30 m+", "AEC: copper with retimers"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("64 ports", BEAT_MS)
        .note(
            "The leaf is a 2U box with 64 OSFP cages, each 800G. The bottom row takes the server downlinks, the top row the uplinks.",
            "The switch's front from above: two rows of silver cages, cables entering the lower row and fibres leaving the upper.",
        )
        .detail(
            "64 x 800G = 51.2 Tb/s.",
            &["OSFP: 800G cage", "SERDES: 512 lanes"],
        ),
    Beat::new("the ASIC", BEAT_MS)
        .note(
            "Every port's SerDes lanes run to one switch chip, such as Broadcom's Tomahawk 5 or NVIDIA's Spectrum-4, under a finned heatsink. It reads each header and forwards the packet in under a microsecond.",
            "Looking down on the board: a large finned heatsink in the middle with an orange glow beneath, copper traces fanning to the ports.",
        )
        .detail(
            "One chip, every port.",
            &["SWITCH ASIC: 51.2 Tb/s", "Tomahawk 5, Spectrum-4"],
        ),
    Beat::new("fans and power", BEAT_MS)
        .note(
            "Fans along the back pull air from front to back across the chip and optics. Two power supplies feed the box, which draws one to two kilowatts with optics fitted.",
            "The rear of the open box: a row of black fans with blue air leaving, two grey power supplies at the corners, heat rising off the heatsink.",
        )
        .detail(
            "Air-cooled, front to back.",
            &["~1-2 kW per box", "Redundant PSUs"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("the uplink row", BEAT_MS)
        .note(
            "The top row's 32 ports hold 800G optical transceivers. Half the switch's bandwidth faces up, toward the spines.",
            "The top row of cages with yellow fibres leaving each one.",
        )
        .detail(
            "Half the ports face the spines.",
            &["800G OPTICS: OSFP", "32 uplinks"],
        ),
    Beat::new("eight fibres a module", BEAT_MS)
        .note(
            "A DR8 module sends eight 100G lanes on eight single-mode fibres through one MPO connector, reaching 500 m. 2xFR4 modules reach 2 km on duplex fibre.",
            "Yellow fibres climbing from the switch, gathering into four bundles above the rack.",
        )
        .detail(
            "Parallel single-mode light.",
            &["DR8: 8 fibres, 500 m", "2xFR4: 2 km"],
        ),
    Beat::new("to every spine", BEAT_MS)
        .note(
            "The bundles run in the overhead tray to the spine row. Each spine gets a quarter of this leaf's uplinks, so every leaf meets every spine.",
            "Four yellow bundles running along the tray to the spine racks at the right.",
        )
        .detail(
            "Every leaf to every spine.",
            &["LEAF-SPINE", "8 x 800G per spine"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("hash a flow", BEAT_MS)
        .note(
            "The leaf hashes a flow's header fields (addresses, ports) to pick one uplink. Every packet of that flow follows the same spine, so they arrive in order.",
            "Green packets leaving the front leaf, each following one of the four bundles.",
        )
        .detail(
            "The hash picks the path.",
            &["ECMP: per-flow hash", "5-tuple"],
        ),
    Beat::new("four equal paths", BEAT_MS)
        .note(
            "With four spines there are four equal-cost paths between any two leaves. Adding spines adds paths and bandwidth.",
            "The spine row lit, packets dropping from each spine toward a leaf in the back row.",
        )
        .detail(
            "Scale out by adding spines.",
            &["4 equal-cost paths", "LEAF-SPINE: 3 hops"],
        ),
    Beat::new("collisions", BEAT_MS)
        .note(
            "AI traffic is a few huge flows. If two elephant flows hash onto the same spine, that link saturates while others sit idle; adaptive routing and packet spraying fix this.",
            "The whole hall: green flows into two different back rows, several sharing one spine.",
        )
        .detail(
            "Few big flows hash badly.",
            &["ELEPHANT FLOWS", "ADAPTIVE ROUTING"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("many to one", BEAT_MS)
        .note(
            "In an all-to-all or incast, many senders aim at one egress port at once. Its buffer fills faster than the link can drain it.",
            "Cyan packets from every server converge on the leaf; an orange stack grows at one uplink port.",
        )
        .detail(
            "Incast fills the buffer.",
            &["INCAST", "Shared buffer: tens of MB"],
        ),
    Beat::new("PFC pause", BEAT_MS)
        .note(
            "RoCE needs a lossless network, so the leaf sends priority flow control pause frames upstream. Senders stop, but pauses can spread and stall innocent traffic.",
            "Red beads run back down several cables from the leaf to the servers.",
        )
        .detail(
            "Lossless, at a price.",
            &["PFC: pause frames", "ROCE: RDMA over Ethernet"],
        ),
    Beat::new("ECN slows senders", BEAT_MS)
        .note(
            "Better: the switch marks packets with ECN as the queue grows, and the receivers tell senders to cut their rate (DCQCN). The queue drains without pausing the link.",
            "Purple marked packets leave on the uplink; the orange queue shrinks.",
        )
        .detail(
            "Mark early, pause rarely.",
            &["ECN: congestion mark", "DCQCN"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "downlinks",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "the switch",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "uplinks",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "ECMP",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "congestion",
        build: zoom_e,
    },
];
