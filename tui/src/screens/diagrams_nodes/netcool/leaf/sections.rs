// NETWORK+COOL tab, LEAF: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_LEAF.txt, from the
// Blender scenes in tools/pbr3d/blender/net_leaf_sections.py (GLBs in tools/pbr3d/assets/net_leaf_section_<n>.glb).
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

const S1_B: &[Beat] = &[
    Beat::new("servers to the leaf", BEAT_MS)
        .note(
            "Each server's NIC ports connect to the row's leaf switch over short cables.",
            "Cyan packets rise from the server ports to the leaf near the top of the network rack.",
        )
        .detail(
            "Every server port meets the leaf.",
            &["LEAF SWITCH", "DAC / AOC"],
        ),
    Beat::new("the leaf forwards", BEAT_MS)
        .note(
            "The leaf's ASIC reads each packet and switches it to the right port.",
            "The switch cut open from above, its heatsink glowing.",
        )
        .detail(
            "One chip decides.",
            &["SWITCH ASIC"],
        ),
    Beat::new("up to every spine", BEAT_MS)
        .note(
            "Uplinks leave on 800G optics over single-mode fibre to every spine.",
            "Yellow light runs from the leaf along the overhead tray to the spine racks.",
        )
        .detail(
            "Every leaf to every spine.",
            &["800G OPTICS", "LEAF-SPINE"],
        ),
];

const S2_B: &[Beat] = &[
    Beat::new("the ports", BEAT_MS)
        .note(
            "Sixty-four 800G OSFP cages across the front: downlinks below, uplinks above.",
            "The switch drawn large: two long rows of silver cages on a black face.",
        )
        .detail(
            "64 x 800G.",
            &["OSFP", "64 ports"],
        ),
    Beat::new("the ASIC and traces", BEAT_MS)
        .note(
            "One switch chip under a finned heatsink, wired to every cage by SerDes traces.",
            "The green board from above, the heatsink in the middle, copper traces fanning out.",
        )
        .detail(
            "51.2 Tb/s in one package.",
            &["SWITCH ASIC", "SERDES"],
        ),
    Beat::new("fans, power, CPU", BEAT_MS)
        .note(
            "Fans and two power supplies at the back, a small control CPU running the switch OS.",
            "The back of the box: black fans, grey PSUs, a small board at the left.",
        )
        .detail(
            "The rest of the box.",
            &["SONiC, EOS, Cumulus", "~1-2 kW"],
        ),
];

const S3_B: &[Beat] = &[
    Beat::new("inside a DAC", BEAT_MS)
        .note(
            "A DAC is eight twinax pairs in a shielded jacket, one pair per 100G lane, with no electronics at all.",
            "A cable cut across: a grey jacket, a silver shield, eight white pairs with copper cores, cyan signals running along them.",
        )
        .detail(
            "Passive copper.",
            &["DAC: ~2 m at 800G", "8 x 100G pairs"],
        ),
    Beat::new("an AOC plug", BEAT_MS)
        .note(
            "An AOC puts lasers, receivers and a DSP into each plug, so thin fibre carries the signal tens of metres.",
            "An open transceiver plug: green board, a dark DSP, a row of red lasers feeding fibres.",
        )
        .detail(
            "Optics in the plug.",
            &["AOC", "Lasers per lane"],
        ),
    Beat::new("which goes where", BEAT_MS)
        .note(
            "Copper serves the racks beside the leaf; optics the outer racks. Active electrical cables (AECs) add retimers to stretch copper to about 7 m.",
            "The row: grey cables from the near racks, aqua from the far ones.",
        )
        .detail(
            "Reach decides the cable.",
            &["DAC / AOC / AEC", "CRDO: AECs"],
        ),
];

const S4_B: &[Beat] = &[
    Beat::new("electrical in", BEAT_MS)
        .note(
            "The module takes eight 100G electrical lanes from the switch; a DSP retimes and drives them.",
            "An 800G module drawn large and cut open: gold edge fingers, a dark DSP chip, cyan beads entering.",
        )
        .detail(
            "The DSP cleans the signal.",
            &["800G OPTICS", "DSP"],
        ),
    Beat::new("eight lasers", BEAT_MS)
        .note(
            "Eight lasers turn the lanes into light on eight single-mode fibres through an MPO connector: DR8, 500 m.",
            "Red lasers in a row, red beads running out through thin glass guides to a clear connector.",
        )
        .detail(
            "Light on eight fibres.",
            &["DR8: 500 m", "SINGLE-MODE FIBRE"],
        ),
    Beat::new("to the spines", BEAT_MS)
        .note(
            "The 32 uplinks gather into bundles in the overhead tray and run to the spine row.",
            "Yellow bundles leaving the rack top and running along the tray.",
        )
        .detail(
            "Up and over to the spines.",
            &["Overhead tray", "LEAF-SPINE"],
        ),
];

const S5_B: &[Beat] = &[
    Beat::new("packets in", BEAT_MS)
        .note(
            "Packets arrive on SerDes lanes from the cages into the ASIC, which parses each header.",
            "The large switch: cyan beads running copper traces into the heatsink.",
        )
        .detail(
            "Parse the header.",
            &["SERDES", "SWITCH ASIC"],
        ),
    Beat::new("buffer and forward", BEAT_MS)
        .note(
            "The chip holds packets in a shared on-chip buffer while their output port is busy, then sends them out.",
            "An orange stack beside the heatsink; yellow beads leaving toward the top port row.",
        )
        .detail(
            "Queue, then send.",
            &["Shared buffer: tens of MB", "Sub-microsecond"],
        ),
    Beat::new("heat out the back", BEAT_MS)
        .note(
            "The chip and optics turn their power into heat; fans push it out the back.",
            "Blue air through the rear fans, orange heat rising above the box.",
        )
        .detail(
            "Air-cooled.",
            &["~1-2 kW", "Front-to-back air"],
        ),
];

const S6_B: &[Beat] = &[
    Beat::new("three hops", BEAT_MS)
        .note(
            "Leaf to spine to leaf: any two servers in different rows are three switch hops apart.",
            "Green packets from the front leaf up through the spines and into a back row.",
        )
        .detail(
            "Short, uniform paths.",
            &["LEAF-SPINE: 3 hops"],
        ),
    Beat::new("ECMP", BEAT_MS)
        .note(
            "Each flow is hashed to one of four equal-cost spines.",
            "The spine row with packets fanning across all four.",
        )
        .detail(
            "Hash to spread.",
            &["ECMP"],
        ),
    Beat::new("scale out", BEAT_MS)
        .note(
            "Every leaf uses every spine; adding spines adds bandwidth, adding leaves adds rows.",
            "All rows sending to all spines at once.",
        )
        .detail(
            "The fabric grows sideways.",
            &["Add spines, add bandwidth"],
        ),
];

const S7_B: &[Beat] = &[
    Beat::new("1:1", BEAT_MS)
        .note(
            "32 ports down and 32 up: the leaf can send all its servers' traffic up at once. Non-blocking.",
            "Two equal blocks of bars, cyan down and yellow up, packets crossing evenly.",
        )
        .detail(
            "Non-blocking.",
            &["OVERSUBSCRIPTION: 1:1"],
        ),
    Beat::new("3:1", BEAT_MS)
        .note(
            "Enterprise fabrics often use 48 ports down and 16 up, 3:1. Fine for bursty web traffic, but bursts queue and drop.",
            "More cyan bars than yellow; packets pile into a red stack.",
        )
        .detail(
            "Cheaper, but it blocks.",
            &["OVERSUBSCRIPTION: 3:1"],
        ),
    Beat::new("why AI uses 1:1", BEAT_MS)
        .note(
            "Training's all-reduce drives every GPU's link at once, so any oversubscription stalls the whole job.",
            "The equal blocks again.",
        )
        .detail(
            "AI needs full bisection.",
            &["All-reduce", "Full bisection bandwidth"],
        ),
];

const S8_B: &[Beat] = &[
    Beat::new("RoCE", BEAT_MS)
        .note(
            "RDMA over Converged Ethernet runs GPU-to-GPU transfers over Ethernet, kept lossless with PFC pauses and ECN marks.",
            "Packets crowding the leaf, red pauses running back, purple marks leaving.",
        )
        .detail(
            "Ethernet made lossless.",
            &["ROCE", "PFC / ECN"],
        ),
    Beat::new("InfiniBand", BEAT_MS)
        .note(
            "InfiniBand uses credits: a sender transmits only when the next hop has buffer room, so it never drops. NVIDIA's Quantum-X800 runs it at 800G.",
            "Green credit beads running from the leaf back to the servers.",
        )
        .detail(
            "Credit-based, lossless by design.",
            &["INFINIBAND", "Quantum-X800"],
        ),
    Beat::new("Ultra Ethernet", BEAT_MS)
        .note(
            "The Ultra Ethernet spec (1.0, June 2025) sprays one flow's packets over every path and lets the NIC reorder them, ending ECMP collisions.",
            "Green packets from one leaf spread over every spine bundle at once.",
        )
        .detail(
            "Spray, then reorder.",
            &["ULTRA ETHERNET", "Packet spraying"],
        ),
];

const S9_B: &[Beat] = &[
    Beat::new("switches and chips", BEAT_MS)
        .note(
            "Arista, Cisco, NVIDIA and Celestica build the switches; Broadcom, NVIDIA and Marvell make the chips. Copper comes from Amphenol and Credo.",
            "The leaf near the rack top with tags on the box, its chip and the cables.",
        )
        .detail(
            "Who builds the leaf.",
            &["ANET, CSCO, NVDA, CLS", "AVGO, MRVL, APH, CRDO"],
        ),
    Beat::new("optics and fibre", BEAT_MS)
        .note(
            "Coherent, Lumentum, Fabrinet, InnoLight and Eoptolink supply transceivers and lasers; Corning the fibre.",
            "The uplink row and the overhead tray.",
        )
        .detail(
            "Who makes the light.",
            &["COHR, LITE, FN", "GLW"],
        ),
    Beat::new("risks", BEAT_MS)
        .note(
            "800G optics and their lasers have run short; switch power climbs with each speed; copper reach shrinks every generation, pushing optics closer to the chip.",
            "The leaf glowing, heat rising off it.",
        )
        .detail(
            "Light and power are the limits.",
            &["Optics supply", "CPO next"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_leaf_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
