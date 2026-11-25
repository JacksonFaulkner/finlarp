// NETWORK+COOL tab, CHILLER PLANT: numbered sections 1-9. Section N illustrates heading N of diagrams_pages/NET_CHILLER.txt, from the
// Blender scenes in tools/pbr3d/blender/net_chiller_sections.py (GLBs in tools/pbr3d/assets/net_chiller_section_<n>.glb).
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

/// 1 what happens: water out, heat lifted, heat dumped.
const S1_B: &[Beat] = &[
    Beat::new("water out to the hall", BEAT_MS)
        .note(
            "The chiller sends chilled water to the hall's air handlers or liquid-cooling units and gets warm water back.",
            "The hall and the chiller side by side with blue and amber beads in the pipes between them.",
        )
        .detail(
            "A closed water loop.",
            &["CHILLED WATER", "Warm return"],
        ),
    Beat::new("refrigerant lifts the heat", BEAT_MS)
        .note(
            "Inside, a refrigerant loop pumps the heat from the cold water up to a temperature hot enough to dump outdoors.",
            "Inside the cut-open chiller: cyan and red refrigerant beads circling between the evaporator and compressor.",
        )
        .detail(
            "A heat pump.",
            &["Evaporator > compressor", "Condenser > valve"],
        ),
    Beat::new("heat dumped outdoors", BEAT_MS)
        .note(
            "The condenser and its fans throw the heat into the outside air.",
            "The chiller's deck with spinning fans and orange heat rising.",
        )
        .detail(
            "Out to the air.",
            &["CONDENSER", "Fans"],
        ),
];

/// 2 the parts.
const S2_B: &[Beat] = &[
    Beat::new("evaporator and condenser", BEAT_MS)
        .note(
            "The evaporator, where refrigerant boils and takes heat from the water, and the condenser, where it gives that heat away.",
            "A big four-part loop: a blue shell below and a copper-red shell above, both cut open on copper tube bundles.",
        )
        .detail(
            "Two heat exchangers.",
            &["EVAPORATOR", "CONDENSER"],
        ),
    Beat::new("compressor and valve", BEAT_MS)
        .note(
            "The compressor, which squeezes the vapour hot, and the expansion valve, which drops the pressure so it can boil again.",
            "A grey compressor with green motor on the right; a brass valve on the left; copper pipes join them to the shells.",
        )
        .detail(
            "The pressure changers.",
            &["COMPRESSOR", "EXPANSION VALVE"],
        ),
    Beat::new("refrigerant and water", BEAT_MS)
        .note(
            "The refrigerant circulates inside the machine; the chilled water is the separate loop that serves the building.",
            "The whole loop lit: refrigerant beads circling, water beads crossing the shells.",
        )
        .detail(
            "Two fluids, never mixed.",
            &["REFRIGERANT", "CHILLED WATER"],
        ),
];

/// 3 in order.
const S3_B: &[Beat] = &[
    Beat::new("boil, then suction", BEAT_MS)
        .note(
            "1. warm water makes the refrigerant boil in the evaporator. 2. the vapour is drawn to the compressor.",
            "Bubbles rise in the lower shell; cyan beads run to the compressor.",
        )
        .detail(
            "Steps 1-2.",
            &["Boil", "Suction"],
        ),
    Beat::new("compress, condense", BEAT_MS)
        .note(
            "3. the compressor squeezes it hot. 4. in the condenser it gives up its heat and turns liquid.",
            "Red beads climb from the compressor into the upper shell; drops fall inside it.",
        )
        .detail(
            "Steps 3-4.",
            &["Compress", "Condense"],
        ),
    Beat::new("expand, return", BEAT_MS)
        .note(
            "5. the expansion valve drops the pressure. 6. the cold mix flows back into the evaporator.",
            "Beads run down through the brass valve and back into the lower shell.",
        )
        .detail(
            "Steps 5-6.",
            &["Expand", "Return"],
        ),
];

/// 4 how much heat.
const S4_B: &[Beat] = &[
    Beat::new("tons and kW", BEAT_MS)
        .note(
            "Chillers are rated in tons of refrigeration: one ton is 3.5 kW of cooling, so 1 MW is about 285 tons. Large units run 1-2 MW.",
            "Three glowing bars rising in steps: light blue, amber and a tall red one.",
        )
        .detail(
            "1 ton = 3.5 kW.",
            &["1 MW ~285 tons", "Big units 1-2 MW"],
        ),
    Beat::new("a rack and a campus", BEAT_MS)
        .note(
            "One 130 kW GB200 NVL72 rack needs about 37 tons. A 100 MW campus that relied on chillers alone would need dozens of large units.",
            "The same bars with new tags.",
        )
        .detail(
            "Scale adds up fast.",
            &["Rack ~37 tons", "Campus: dozens of units"],
        ),
    Beat::new("one unit", BEAT_MS)
        .note(
            "One air-cooled chiller beside the hall it serves.",
            "Wide view of the site.",
        )
        .detail(
            "One of many.",
            &["One chiller", "One hall"],
        ),
];

/// 5 compressors.
const S5_B: &[Beat] = &[
    Beat::new("screw", BEAT_MS)
        .note(
            "Screw compressors use two meshing rotors and are common in air-cooled chillers of a few hundred tons.",
            "A cut-open twin-screw compressor with gas beads riding its rotors.",
        )
        .detail(
            "Mid-size workhorse.",
            &["SCREW", "Air-cooled units"],
        ),
    Beat::new("centrifugal", BEAT_MS)
        .note(
            "Centrifugal compressors spin an impeller to fling gas outward; they dominate large water-cooled chillers.",
            "A spinning impeller in a spiral volute with red beads spiralling out.",
        )
        .detail(
            "Large plants.",
            &["CENTRIFUGAL", "Water-cooled"],
        ),
    Beat::new("magnetic bearings", BEAT_MS)
        .note(
            "Magnetic bearings float the shaft with no oil, cutting friction; the best water-cooled machines reach about 0.5 kW per ton.",
            "The impeller from the side, its shaft passing through two purple bearing rings and a green motor.",
        )
        .detail(
            "Oil-free.",
            &["MAGNETIC BEARINGS", "~0.5 kW/ton"],
        ),
];

/// 6 COP and water temperature.
const S6_B: &[Beat] = &[
    Beat::new("COP by machine", BEAT_MS)
        .note(
            "COP is heat moved divided by power used. Air-cooled chillers manage about 3, water-cooled about 6-7, and warmer water pushes it higher; free cooling is higher still.",
            "Four bars growing: red, amber, blue and a tall green one.",
        )
        .detail(
            "Heat moved per watt.",
            &["Air-cooled ~3", "Water-cooled ~6-7"],
        ),
    Beat::new("lift", BEAT_MS)
        .note(
            "The compressor's work depends on the lift between the water temperature and the outdoor air. Warmer chilled water means less lift.",
            "Two bars: a tall red one for 7 C water and a short blue one for 18 C water.",
        )
        .detail(
            "Less lift, less power.",
            &["7 C: big lift", "18 C: half"],
        ),
    Beat::new("each degree counts", BEAT_MS)
        .note(
            "Each degree warmer on the chilled water saves roughly 2-3% of the compressor's power.",
            "The COP bars from another angle.",
        )
        .detail(
            "Run water warm.",
            &["~2-3% per C", "COP = heat / power"],
        ),
];

/// 7 free cooling and dry coolers.
const S7_B: &[Beat] = &[
    Beat::new("free-cooling coil", BEAT_MS)
        .note(
            "A free-cooling chiller adds a coil that uses cold outdoor air directly, so the compressor can stop on cold days.",
            "The chiller's back coil glowing blue, compressor still.",
        )
        .detail(
            "Economizer.",
            &["FREE COOLING", "Compressor off"],
        ),
    Beat::new("dry cooler", BEAT_MS)
        .note(
            "A dry cooler drops the compressor entirely: coil and fans only. It suits liquid loops running 30-45 C.",
            "The V-bank dry cooler with fans spinning and warm air rising.",
        )
        .detail(
            "No refrigerant.",
            &["DRY COOLER", "30-45 C loops"],
        ),
    Beat::new("adiabatic", BEAT_MS)
        .note(
            "Adiabatic pads add a little evaporation on the hottest days to pre-cool the air.",
            "The back pad of the dry cooler with water running down it.",
        )
        .detail(
            "Water on peak days only.",
            &["ADIABATIC", "Few hundred hours"],
        ),
];

/// 8 who makes it.
const S8_B: &[Beat] = &[
    Beat::new("Trane, Carrier, Johnson Controls", BEAT_MS)
        .note(
            "Trane Technologies (TT), Carrier (CARR) and Johnson Controls' York (JCI) sell the large chillers used at data centers.",
            "The chiller close up with maker tags.",
        )
        .detail(
            "The big three in the US.",
            &["TT", "CARR, JCI"],
        ),
    Beat::new("Daikin, Modine", BEAT_MS)
        .note(
            "Daikin, Mitsubishi and LG compete globally; Modine (MOD) sells data-center chillers and dry coolers, including Airedale.",
            "The chiller's deck and fans with tags.",
        )
        .detail(
            "Global and niche.",
            &["Daikin", "MOD"],
        ),
    Beat::new("Vertiv, Danfoss", BEAT_MS)
        .note(
            "Vertiv (VRT) sells chillers alongside its CDUs and air handlers; Danfoss makes the Turbocor oil-free compressors many chillers use.",
            "The whole site with tags on the hall and the compressor.",
        )
        .detail(
            "Chain and parts.",
            &["VRT", "Danfoss Turbocor"],
        ),
];

/// 9 chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("refrigerant rules", BEAT_MS)
        .note(
            "The US HFC phase-down caps the global-warming potential of refrigerants in new chillers, pushing makers to R-1234ze, R-513A and similar.",
            "The refrigeration loop with tags on its shells.",
        )
        .detail(
            "New refrigerants.",
            &["AIM Act phase-down", "GWP limit 700"],
        ),
    Beat::new("heat waves", BEAT_MS)
        .note(
            "An air-cooled chiller has the least capacity on the hottest day, exactly when it is needed most.",
            "The chiller with fans racing and heavy heat rising.",
        )
        .detail(
            "Peak load, least capacity.",
            &["Hot day", "Compressor at max"],
        ),
    Beat::new("lead times", BEAT_MS)
        .note(
            "Large chillers have long lead times while data-center demand surges; makers are adding capacity.",
            "Wide view of the chiller.",
        )
        .detail(
            "Supply has to keep up.",
            &["Long lead times", "Factories expanding"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
