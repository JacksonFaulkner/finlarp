// NETWORK+COOL tab, SPINE: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_SPINE.txt, from the
// Blender scenes in tools/pbr3d/blender/net_spine_sections.py (GLBs in tools/pbr3d/assets/net_spine_section_<n>.glb).
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
    Beat::new("leaf to spine to leaf", BEAT_MS)
        .note(
            "A packet leaves a leaf switch, climbs a fibre to a spine, and comes back down to another leaf. That is every trip in a two-tier fabric: two hops.",
            "The fabric from afar: big cyan dots climb from a bottom box to the third top box and down to another bottom box.",
        )
        .detail(
            "Two hops, any leaf to any leaf.",
            &["LEAF-SPINE", "2 hops"],
        ),
    Beat::new("across the ASIC", BEAT_MS)
        .note(
            "Inside the spine the packet enters an 800G port, rides SerDes traces into the ASIC, which looks up where it goes, and leaves on the port facing the destination leaf.",
            "The open spine from above: dots run in from a front port, along a trace into the chip and back out to another port.",
        )
        .detail(
            "The ASIC picks the output port.",
            &["800G port in", "800G port out"],
        ),
    Beat::new("four equal paths", BEAT_MS)
        .note(
            "Every spine is one hop from every leaf, so there are four equal paths; ECMP spreads flows over all of them.",
            "The fabric again with four colours of dots, one per spine.",
        )
        .detail(
            "More spines, more bandwidth.",
            &["ECMP", "4 spines"],
        ),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("ports and optics", BEAT_MS)
        .note(
            "The front holds 64 OSFP cages with 800G optics plugged in, in a 2RU box.",
            "The box face-on with four rows of cages and modules.",
        )
        .detail(
            "The ports face the leaves.",
            &["OSFP CAGE", "800G OPTIC"],
        ),
    Beat::new("ASIC, traces, CPU", BEAT_MS)
        .note(
            "Behind them, copper traces run to one switch ASIC under its heatsink. A small CPU board runs the network operating system (Arista EOS, Cisco NX-OS or SONiC) and programs the chip.",
            "The open box from above: heatsink in the middle, traces in front, a small board with a chip and a memory stick on the right.",
        )
        .detail(
            "The CPU controls; the ASIC forwards.",
            &["SWITCH ASIC", "CPU + NOS"],
        ),
    Beat::new("fans and power", BEAT_MS)
        .note(
            "At the back, a fan wall and two power supplies. Air moves front to back.",
            "The rear of the box: four black fans, two grey power supplies, blue and orange dots.",
        )
        .detail(
            "Cooling and power fill the back.",
            &["FAN WALL", "2 PSUs"],
        ),
];

/// 3 in order.
const S3_B: &[Beat] = &[
    Beat::new("SerDes and ingress", BEAT_MS)
        .note(
            "Bits arrive on SerDes lanes at the chip's edge. Ingress pipelines parse each packet's headers and look up its destination.",
            "A big chip close-up: gold tiles ring the die edge, green blocks on the left; cyan dots arrive at the left edge.",
        )
        .detail(
            "Parse, then look up.",
            &["SERDES in", "INGRESS PIPE"],
        ),
    Beat::new("the shared buffer", BEAT_MS)
        .note(
            "Packets wait in one shared on-die packet buffer, queued by output port, so bursts from many ports can be absorbed.",
            "A large pale blue block in the middle of the die, glowing, with dots passing through.",
        )
        .detail(
            "Buffer absorbs bursts.",
            &["SHARED BUFFER", "Queues per port"],
        ),
    Beat::new("egress and out", BEAT_MS)
        .note(
            "Egress pipelines rewrite headers and schedule each queue, then SerDes lanes on the far edge send the packet out.",
            "Orange blocks on the right of the die; amber dots leave through the gold tiles on the right edge.",
        )
        .detail(
            "Rewrite, schedule, transmit.",
            &["EGRESS PIPE", "SERDES out"],
        ),
];

/// 4 51.2 Tb/s.
const S4_B: &[Beat] = &[
    Beat::new("512 lanes", BEAT_MS)
        .note(
            "The ASIC has 512 SerDes lanes at about 100 Gb/s each.",
            "Top view: the chip glowing, traces fanning to the cages, dots running along.",
        )
        .detail(
            "512 x 100G = 51.2T.",
            &["512 SERDES", "100G each"],
        ),
    Beat::new("8 lanes a port", BEAT_MS)
        .note(
            "Eight lanes make one 800G port: 512 / 8 = 64 ports.",
            "Traces reaching every column of cages, dots on all of them.",
        )
        .detail(
            "Lanes group into ports.",
            &["8 lanes = 800G", "64 ports"],
        ),
    Beat::new("64 x 800G", BEAT_MS)
        .note(
            "64 ports of 800G is 51.2 Tb/s. The same chip can run 128 ports of 400G for a larger radix.",
            "Front view: red light dots arrive on fibres at the top row of ports.",
        )
        .detail(
            "Speed or radix: same chip.",
            &["64 x 800G", "128 x 400G"],
        ),
];

/// 5 SerDes and PAM4.
const S5_B: &[Beat] = &[
    Beat::new("four levels", BEAT_MS)
        .note(
            "Each lane sends PAM4: four voltage levels instead of two, one symbol at a time.",
            "A dark scope with four bright horizontal lines and crossing transition curves between them; a gold dot hops between levels.",
        )
        .detail(
            "Four levels, two bits.",
            &["PAM4", "4 levels"],
        ),
    Beat::new("two bits a symbol", BEAT_MS)
        .note(
            "Each level stands for two bits: 00, 01, 10, 11.",
            "The same eye with the four levels labelled 00 to 11 on the right.",
        )
        .detail(
            "Twice the bits per symbol.",
            &["2 bits / symbol", "00 01 10 11"],
        ),
    Beat::new("the eye", BEAT_MS)
        .note(
            "At about 53 gigabaud and two bits a symbol, a lane carries about 106 Gb/s raw (100G after coding). The receiver decides at the centre of each eye opening.",
            "The full eye diagram with three openings stacked between the four levels.",
        )
        .detail(
            "Smaller eyes, harder links.",
            &["~53 GBd", "~106 Gb/s raw"],
        ),
];

/// 6 the optic.
const S6_B: &[Beat] = &[
    Beat::new("OSFP 800G", BEAT_MS)
        .note(
            "An 800G OSFP module carries 8 lanes in a shell with fins on top for cooling.",
            "A long grey module drawn large with fins along its top.",
        )
        .detail(
            "A pluggable optic.",
            &["OSFP 800G", "Top fins"],
        ),
    Beat::new("electrical side", BEAT_MS)
        .note(
            "Gold edge fingers bring in 8 x 100G lanes; a DSP cleans up and retimes them, and drivers feed the lasers.",
            "The shell open: green board, gold fingers at the back, a grey DSP chip and a row of small black drivers; cyan dots run forward.",
        )
        .detail(
            "DSP retimes every lane.",
            &["DSP", "Drivers"],
        ),
    Beat::new("light out", BEAT_MS)
        .note(
            "Eight lasers turn each lane into light, and a fibre ribbon carries it to the MPO connector at the front. A module draws about 15 W.",
            "Red laser chips, a lens bar and yellow fibres to a black connector at the front; red dots leave out the end.",
        )
        .detail(
            "Electrons in, photons out.",
            &["8 lasers", "MPO, ~15 W"],
        ),
];

/// 7 ECMP.
const S7_B: &[Beat] = &[
    Beat::new("every leaf, every spine", BEAT_MS)
        .note(
            "In a two-tier Clos, each leaf is wired to all four spines.",
            "The fabric with all 32 fibres.",
        )
        .detail(
            "Full mesh.",
            &["2-TIER CLOS", "32 links"],
        ),
    Beat::new("hash picks a path", BEAT_MS)
        .note(
            "A hash of the flow's headers picks one of four equal-cost paths; a flow stays on one path so its packets stay in order.",
            "Four colours of dots from one leaf through four spines to another.",
        )
        .detail(
            "Per-flow, in order.",
            &["ECMP hash", "5-tuple"],
        ),
    Beat::new("a spine fails", BEAT_MS)
        .note(
            "When a spine fails, leaves rehash onto the remaining three and keep 75% of their uplink capacity.",
            "One spine glows red; dots now use three spines.",
        )
        .detail(
            "N spines: lose 1/N.",
            &["Spine fails", "75% left"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("the chip", BEAT_MS)
        .note(
            "Broadcom (AVGO) Tomahawk leads merchant switch silicon; Marvell (MRVL) Teralynx and Cisco (CSCO) Silicon One also reach 51.2T, and NVIDIA (NVDA) sells Spectrum-X.",
            "A close look at the ASIC on the board with three maker tags.",
        )
        .detail(
            "Few chip makers.",
            &["AVGO, MRVL", "CSCO, NVDA"],
        ),
    Beat::new("the optics", BEAT_MS)
        .note(
            "Coherent (COHR) and Lumentum (LITE) make lasers and modules; Fabrinet (FN) builds them; Applied Optoelectronics (AAOI) and InnoLight also ship; Credo (CRDO) makes copper AECs and DSPs.",
            "The front ports with tags on the modules.",
        )
        .detail(
            "Optics are a second supply chain.",
            &["COHR, LITE, FN", "AAOI, CRDO"],
        ),
    Beat::new("the box", BEAT_MS)
        .note(
            "Arista (ANET) and Cisco build branded switches; Celestica (CLS) builds white boxes for hyperscalers running SONiC.",
            "The fabric with tags on the spines.",
        )
        .detail(
            "Branded vs white box.",
            &["ANET, CSCO", "CLS"],
        ),
];

/// 9 chokepoints.
const S9_B: &[Beat] = &[
    Beat::new("heat", BEAT_MS)
        .note(
            "The ASIC alone is a several-hundred-watt class part, and air cooling is near its limit; new boxes add liquid cooling.",
            "The open box from above with air dots and a glowing chip.",
        )
        .detail(
            "Air is running out.",
            &["~500 W class ASIC", "Liquid next"],
        ),
    Beat::new("optics power", BEAT_MS)
        .note(
            "64 optics at about 15 W is roughly a kilowatt. Linear pluggable optics (LPO) drop the DSP and cut that power sharply.",
            "The front ports with orange heat rising off the modules.",
        )
        .detail(
            "Optics can outdraw the chip.",
            &["~1 kW of optics", "LPO"],
        ),
    Beat::new("what comes next", BEAT_MS)
        .note(
            "Tomahawk 6 doubles to 102.4 Tb/s, and co-packaged optics put the lasers right beside the die.",
            "The ASIC close-up again, labelled with the next steps.",
        )
        .detail(
            "Double again, optics move in.",
            &["102.4T", "CO-PACKAGED OPTICS"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
