// NETWORK+COOL tab, COOLING TOWERS: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_COOLING_TOWER.txt, from the
// Blender scenes in tools/pbr3d/blender/net_cooling_tower_sections.py (GLBs in tools/pbr3d/assets/net_cooling_tower_section_<n>.glb).
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

/// 1 what happens: warm water falls through air, heat leaves as vapour.
const S1_B: &[Beat] = &[
    Beat::new("warm water in", BEAT_MS)
        .note(
            "The chiller's condenser sends warm water, around 35 C, to the tower.",
            "Wide view of the plant and the tower with water beads in the pipes.",
        )
        .detail(
            "Heat arrives as warm water.",
            &["~35 C in", "Condenser water"],
        ),
    Beat::new("falls through air", BEAT_MS)
        .note(
            "The water is sprayed over the fill and falls through air drawn in at the sides.",
            "Inside the tower: films on the fill, drops falling, air beads entering.",
        )
        .detail("Water meets air.", &["Spray + fill", "Air in"]),
    Beat::new("vapour out", BEAT_MS)
        .note(
            "Some evaporates and leaves as vapour; the cooled water goes back to the chiller.",
            "A tall white plume over the tower.",
        )
        .detail("Heat leaves as vapour.", &["Plume", "~29 C back"]),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("basin and louvers", BEAT_MS)
        .note(
            "The basin collects the cooled water; louvers on the sides let air in and keep water from splashing out.",
            "The bottom of the tower: blue water in a concrete basin, slatted louvers at the sides.",
        )
        .detail(
            "The bottom.",
            &["BASIN", "LOUVERS"],
        ),
    Beat::new("fill and spray", BEAT_MS)
        .note(
            "Spray nozzles spread the warm water over the fill, which turns it into thin films.",
            "The middle of the tower with the header above and fill below.",
        )
        .detail(
            "The middle.",
            &["SPRAY NOZZLES", "FILL"],
        ),
    Beat::new("drift and fan", BEAT_MS)
        .note(
            "Drift eliminators catch droplets above the spray, and the fan on top pulls the air through.",
            "The top: zig-zag blades and the fan in its stack.",
        )
        .detail(
            "The top.",
            &["DRIFT ELIMINATORS", "FAN"],
        ),
];

/// 3 in order.
const S3_B: &[Beat] = &[
    Beat::new("pump and spray", BEAT_MS)
        .note(
            "1. warm water is pumped up. 2. it is sprayed over the fill.",
            "Amber beads climbing to the header and out of the nozzles.",
        )
        .detail("Steps 1-2.", &["Pump", "Spray"]),
    Beat::new("films and evaporation", BEAT_MS)
        .note(
            "3. films on the fill meet rising air. 4. some water evaporates.",
            "The fill with films and drops, air beads rising.",
        )
        .detail("Steps 3-4.", &["Films", "Evaporate"]),
    Beat::new("basin and back", BEAT_MS)
        .note(
            "5. the cooled water rains into the basin. 6. it is pumped back to the chiller.",
            "Blue drops falling into the basin.",
        )
        .detail("Steps 5-6.", &["Basin", "Back to chiller"]),
];

/// 4 the physics: latent heat, range and approach.
const S4_B: &[Beat] = &[
    Beat::new("latent heat", BEAT_MS)
        .note(
            "Evaporating water takes about 2,400 kJ per kilogram, which is why a little evaporation cools a lot of water.",
            "One drop falling and shedding vapour.",
        )
        .detail(
            "Evaporation is powerful.",
            &["~2,400 kJ/kg", "Latent heat"],
        ),
    Beat::new("three temperatures", BEAT_MS)
        .note(
            "Hot water in near 35 C, cold water out near 29 C, and the outdoor wet-bulb near 25 C on a design day.",
            "Three bars: red, blue and green, stepping down.",
        )
        .detail(
            "In, out, wet-bulb.",
            &["~35 C in", "~29 C out, ~25 C WB"],
        ),
    Beat::new("range and approach", BEAT_MS)
        .note(
            "Range is in minus out, about 6 C here. Approach is out minus the wet-bulb, typically 3-5 C; a closer approach needs a bigger tower.",
            "The same bars from another angle.",
        )
        .detail(
            "Two numbers size a tower.",
            &["RANGE ~6 C", "APPROACH ~3-5 C"],
        ),
];

/// 5 fill and air.
const S5_B: &[Beat] = &[
    Beat::new("fill", BEAT_MS)
        .note(
            "Fill gives the water a huge wet surface by spreading it into films instead of drops.",
            "Four large corrugated sheets with films running down them.",
        )
        .detail(
            "Films, not drops.",
            &["FILL", "Huge surface"],
        ),
    Beat::new("counterflow", BEAT_MS)
        .note(
            "In a counterflow tower the air rises straight against the falling water, giving a closer approach in less space.",
            "Air beads rising between the sheets as water runs down.",
        )
        .detail(
            "Air up, water down.",
            &["COUNTERFLOW", "Closer approach"],
        ),
    Beat::new("fan", BEAT_MS)
        .note(
            "Big induced-draft fans pull air out of the top, usually on variable-speed drives so they slow down when it is cool.",
            "The tower top with the fan spinning and the plume rising.",
        )
        .detail(
            "Induced draft.",
            &["FAN on VFD", "Pulls from the top"],
        ),
];

/// 6 water use.
const S6_B: &[Beat] = &[
    Beat::new("evaporation", BEAT_MS)
        .note(
            "About 1% of the flow evaporates per 6 C of cooling, roughly 1.5 litres for every kWh of heat rejected.",
            "The tower with its plume.",
        )
        .detail(
            "The main loss.",
            &["~1% per 6 C", "~1.5 L/kWh"],
        ),
    Beat::new("make-up and blowdown", BEAT_MS)
        .note(
            "The make-up meter replaces it; blowdown drains a little more to control minerals.",
            "The meter spinning and the blowdown draining.",
        )
        .detail(
            "In and out.",
            &["MAKE-UP", "BLOWDOWN"],
        ),
    Beat::new("scale", BEAT_MS)
        .note(
            "100 MW of heat evaporates about 3.6 million litres a day; a 1 GW campus cooled this way would use ten times that.",
            "Three bars rising: blue, amber and a tall red one.",
        )
        .detail(
            "Town-sized water use.",
            &["100 MW ~3.6M L/day", "1 GW ~36M L/day"],
        ),
];

/// 7 drift, blowdown and safety.
const S7_B: &[Beat] = &[
    Beat::new("drift", BEAT_MS)
        .note(
            "Drift eliminators hold droplet loss to about 0.0005-0.001% of the circulating flow.",
            "The chevron blades catching droplets.",
        )
        .detail(
            "Droplets caught.",
            &["DRIFT", "~0.001% or less"],
        ),
    Beat::new("blowdown", BEAT_MS)
        .note(
            "Without blowdown, minerals build up and cause scale and corrosion.",
            "The basin corner draining.",
        )
        .detail(
            "Keep the water clean.",
            &["BLOWDOWN", "Scale + corrosion"],
        ),
    Beat::new("treatment", BEAT_MS)
        .note(
            "Tower water is treated with biocides and inhibitors and managed under plans such as ASHRAE 188 to control Legionella.",
            "The tower basin and meter with tags.",
        )
        .detail(
            "Health risk managed.",
            &["Water treatment", "ASHRAE 188"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("SPX and EVAPCO", BEAT_MS)
        .note(
            "SPX Technologies (SPXC) makes Marley towers; EVAPCO is a large private maker.",
            "The site with maker tags on the tower.",
        )
        .detail(
            "Tower makers.",
            &["SPXC: Marley", "EVAPCO"],
        ),
    Beat::new("BAC, JCI, Trane", BEAT_MS)
        .note(
            "Baltimore Aircoil (owned by private Amsted) builds towers; Johnson Controls (JCI) and Trane (TT) make the water-cooled chillers beside them.",
            "The tower from another angle with tags on the plant.",
        )
        .detail(
            "Towers and chillers.",
            &["BAC", "JCI, TT"],
        ),
    Beat::new("Modine and Vertiv", BEAT_MS)
        .note(
            "Modine (MOD) sells dry coolers, the waterless alternative; Vertiv (VRT) supplies the thermal chain from plant to rack.",
            "The whole site.",
        )
        .detail(
            "Alternatives and chain.",
            &["MOD", "VRT"],
        ),
];

/// 9 heat out: chokepoints.
const S9_B: &[Beat] = &[
    Beat::new("every watt ends in the air", BEAT_MS)
        .note(
            "Heat out is the last step: all the power a campus draws leaves as heat to the outdoor air. Wet towers do it most cheaply, with water.",
            "A tall plume over the tower against the sky.",
        )
        .detail(
            "The final sink.",
            &["HEAT OUT", "Wet: cheapest"],
        ),
    Beat::new("water stress", BEAT_MS)
        .note(
            "In dry or water-stressed regions, towers' water use draws pushback, permit fights and local politics.",
            "The tower with its make-up meter spinning.",
        )
        .detail(
            "Water can decide sites.",
            &["Drought areas", "Permits"],
        ),
    Beat::new("dry coolers", BEAT_MS)
        .note(
            "Dry coolers use no water but more power; warm-water liquid cooling lets more sites use them for most of the year.",
            "A dry cooler with spinning fans and warm air rising.",
        )
        .detail(
            "Trade water for power.",
            &["DRY COOLERS", "Warm water helps"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
