// NETWORK+COOL tab, SPINE: the page's overview, a Blender scene (tools/pbr3d/blender/net_spine_overview.py, GLB
// tools/pbr3d/assets/net_spine_overview.glb). Seven beats: the spine tier, one spine opened, 64 ports of 800G, the
// 51.2 Tb/s ASIC, SerDes to the ports, fans and heat, and ECMP to every leaf.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_spine_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match net_spine_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the spine tier", BEAT_MS)
        .note(
            "The spine tier is the top row of a leaf-spine fabric. Four spine switches sit above eight leaf switches, and every leaf has a fibre to every spine, so any leaf reaches any other in two hops.",
            "Four grey switch boxes in a row at the top, eight more along the bottom, and a web of yellow fibres joining every bottom box to every top box, with coloured dots running along them.",
        )
        .detail(
            "Every leaf connects to every spine.",
            &["LEAF-SPINE: 2 tiers", "4 spines, 8 leaves"],
        ),
    Beat::new("one spine, opened", BEAT_MS)
        .note(
            "The lid lifts off one spine. Inside a 2RU box sit 64 optical cages across the front, one switch chip under a finned heatsink in the middle, a wall of fans and two power supplies at the back.",
            "A dark metal box with its lid gone: a green board, a row of silver cages at the front, a tall finned heatsink in the middle, four black fans and two grey power supplies at the back.",
        )
        .detail(
            "One chip does all the switching.",
            &["2RU: 88 mm tall", "1 ASIC, 64 ports"],
        ),
    Beat::new("64 ports of 800G", BEAT_MS)
        .note(
            "The front panel holds 64 OSFP cages in four rows of 16. Each takes an 800 Gb/s pluggable optic that turns electrical lanes into light on a fibre. Green LEDs blink with link activity.",
            "The front face up close: four rows of silver cages, a grey module with a blue pull tab in each, small green LEDs blinking above them and yellow fibres leaving the front.",
        )
        .detail(
            "64 x 800G = 51.2 Tb/s.",
            &["OSFP 800G", "64 PORTS"],
        ),
    Beat::new("one ASIC: 51.2 Tb/s", BEAT_MS)
        .note(
            "The heatsink lifts away to show the switch ASIC, a Broadcom Tomahawk 5 class chip. One piece of 5 nm silicon moves 51.2 terabits a second between all 64 ports, and its lid glows with the heat.",
            "The finned heatsink rises off the board; under it a square brown package with a silver lid glowing orange, ringed by small capacitors and fanned copper traces.",
        )
        .detail(
            "The whole switch is one chip.",
            &["SWITCH ASIC: 51.2 Tb/s", "Tomahawk 5: 5 nm, 2022"],
        ),
    Beat::new("SerDes to the ports", BEAT_MS)
        .note(
            "Copper traces fan out from the edge of the ASIC to every cage. Each carries 100 Gb/s serial lanes (SerDes); a packet comes in on one port's lanes, crosses the chip and leaves on another port's.",
            "Seen from above: thin copper traces spread from the chip to the 16 columns of cages; cyan dots ride in from the left ports to the chip and amber dots leave it toward the right ports.",
        )
        .detail(
            "512 lanes at 100G each.",
            &["SERDES: 512 x 100G", "8 lanes per 800G port"],
        ),
    Beat::new("fans and heat", BEAT_MS)
        .note(
            "Fans at the back pull cool air in through the front panel, over the optics and across the heatsink, and push it out the rear hot. The chip and 64 optics together put out on the order of a kilowatt or more.",
            "Blue dots stream in from the front, pass over the heatsink and turn orange as they go through the spinning black fans and out the back; orange heat shimmers up off the fins.",
        )
        .detail(
            "Air in the front, out the back.",
            &["AIR: front to back", "Optics: ~15 W each"],
        ),
    Beat::new("ECMP to every leaf", BEAT_MS)
        .note(
            "Traffic from one leaf to another can go through any spine. ECMP hashes each flow's headers to pick one of the four equal-cost paths, so the load spreads across all spines at once.",
            "Back to the whole fabric: four streams of different coloured dots leave one bottom box, each climbs to a different top box and comes back down to the same far bottom box.",
        )
        .detail(
            "Equal paths, spread by hash.",
            &["ECMP: 4 paths", "Any leaf, 2 hops"],
        ),
];
