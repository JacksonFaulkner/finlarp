// NETWORK+COOL tab, SPINE: lettered zoom-ins a-e (tools/pbr3d/blender/net_spine_zooms.py, GLBs in
// tools/pbr3d/assets/net_spine_zoom_<letter>.glb): a front panel, b the ASIC, c SerDes lanes, d fans and power, e ECMP.

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
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("64 ports, 4 rows of 16", BEAT_MS)
        .note(
            "The front panel of a 51.2T spine: 64 OSFP cages in four rows of 16, belly to belly, in a box just 88 mm tall.",
            "The switch face-on: a dark faceplate with four rows of silver cages, each with a module inside and a blue tab, yellow fibres leaving.",
        )
        .detail(
            "Port count sets the fabric's size.",
            &["64 x OSFP", "2RU"],
        ),
    Beat::new("the 800G module", BEAT_MS)
        .note(
            "Each cage holds an 800G OSFP module. Light arrives on its fibre, and the module turns it into eight 100G electrical lanes for the board.",
            "A close look at the cages: grey modules with blue pull tabs and fins on top; red dots of light run in from a fibre into one module.",
        )
        .detail(
            "One module, eight lanes.",
            &["OSFP 800G", "8 x 100G electrical"],
        ),
    Beat::new("into the board", BEAT_MS)
        .note(
            "The module slides into its cage and its edge connector meets the board at the back of the cage, where the copper traces start.",
            "From above: the tops of the cage row and, behind them, copper traces fanning back toward the heatsink.",
        )
        .detail(
            "The cage is the electrical handoff.",
            &["Edge connector", "Cage to trace"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("the heatsink", BEAT_MS)
        .note(
            "A finned heatsink with heat pipes sits on the ASIC; air from the front flows between its fins and carries the heat away.",
            "A tall block of thin silver fins with copper heat pipes, orange dots rising off it, fans behind.",
        )
        .detail(
            "The chip needs a big cooler.",
            &["Finned heatsink", "Heat pipes"],
        ),
    Beat::new("heatsink off", BEAT_MS)
        .note(
            "The heatsink lifts off to reveal the switch ASIC underneath, sitting on the board with traces running forward from it.",
            "The heatsink rises into the air; below it a small square package on the green board.",
        )
        .detail(
            "One package under the cooler.",
            &["Switch ASIC", "Lid + substrate"],
        ),
    Beat::new("51.2 Tb/s in 5 nm", BEAT_MS)
        .note(
            "Broadcom's Tomahawk 5 moves 51.2 Tb/s on one 5 nm die. Decoupling capacitors ring the package, and its lid glows with the heat.",
            "A brown package with a glowing orange lid, small silver capacitors along two edges and dozens of copper traces leaving the front.",
        )
        .detail(
            "Bandwidth doubles every ~2 years.",
            &["Tomahawk 5: 51.2T", "5 nm"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("traces from the edge", BEAT_MS)
        .note(
            "Copper traces leave the ASIC's edge and run across the board. SerDes circuits on the chip push serial data down each one.",
            "Looking down on the chip: copper traces fan out from its front edge, bright dots moving along them.",
        )
        .detail(
            "Short copper, very fast.",
            &["SERDES", "Board traces"],
        ),
    Beat::new("8 lanes per port", BEAT_MS)
        .note(
            "Eight 100G lanes make one 800G port, so each column of cages gets its own bundle of traces.",
            "Traces reaching the cage columns, dots running into the cages at the front.",
        )
        .detail(
            "8 x 100G = 800G.",
            &["8 lanes / port", "100G PAM4"],
        ),
    Beat::new("in one port, out another", BEAT_MS)
        .note(
            "A packet comes in on one port's lanes, crosses the chip, and goes out on another port's lanes: 512 lanes in all.",
            "The whole board from above: cyan dots flow in from left ports to the chip, amber dots leave toward the right ports.",
        )
        .detail(
            "Any port to any port.",
            &["512 lanes", "Full crossbar"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("the fan wall", BEAT_MS)
        .note(
            "Four fans in a wall behind the ASIC pull air from the front of the box to the back.",
            "Four black fans spinning in their frames, blue dots coming toward them.",
        )
        .detail(
            "Front-to-back air.",
            &["4 fans", "Front to back"],
        ),
    Beat::new("heat off the chip", BEAT_MS)
        .note(
            "The air crosses the heatsink, which carries the ASIC's heat; the 64 optics at the front each add around 15 W more.",
            "The whole open box from above: blue dots in at the front, turning orange over the heatsink, heat rising.",
        )
        .detail(
            "Optics rival the chip for heat.",
            &["ASIC heat", "~15 W per optic"],
        ),
    Beat::new("power and exhaust", BEAT_MS)
        .note(
            "Two redundant power supplies sit at the rear corners, and hot air leaves out the back of the box.",
            "Seen from behind: the rear wall, two grey power supplies, orange dots leaving the fans.",
        )
        .detail(
            "1+1 redundant power.",
            &["2 PSUs", "Hot air out"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("a link to every spine", BEAT_MS)
        .note(
            "Each leaf has an uplink to each of the four spines, so the fabric is a full mesh between the tiers.",
            "The fabric: four spines on top, eight leaves below, yellow fibres joining each leaf to each spine.",
        )
        .detail(
            "Full mesh between tiers.",
            &["LEAF-SPINE", "4 uplinks per leaf"],
        ),
    Beat::new("hashed over 4 paths", BEAT_MS)
        .note(
            "ECMP hashes each flow's headers so its packets keep one path while different flows spread across all four spines.",
            "Coloured dot streams climb from leaves to different spines and back down.",
        )
        .detail(
            "Load spreads by hash.",
            &["ECMP", "Per-flow hashing"],
        ),
    Beat::new("a link fails", BEAT_MS)
        .note(
            "When a link fails, the leaf drops that path and rehashes its flows onto the remaining three; the fabric keeps running at 75% of its uplink capacity.",
            "One fibre turns red; the dot streams now use only three spines.",
        )
        .detail(
            "Graceful degradation.",
            &["Rehash onto 3", "75% capacity"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "front panel",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "the ASIC",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "SerDes lanes",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "fans and power",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "ECMP",
        build: zoom_e,
    },
];
