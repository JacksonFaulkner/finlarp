// SAND write-up sections 1-10: each a Blender scene (tools/pbr3d/blender/sand_sections.py), three
// beats each, on the overview's layout: the 3D picture on the left with tags pinned on, the beat's
// text in a panel on the right. Section 10 is the sources page.

use std::sync::OnceLock;

use super::{Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

type Cell = OnceLock<pbr3d::scene_gltf::Scene>;
static CELLS: [Cell; 10] = [const { OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:expr) => {
        || -> Box<dyn Scene> {
            Box::new(Page {
                cell: &CELLS[$n - 1],
                glb: include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/sand_sec",
                    $n,
                    ".glb"
                )),
                beats: $beats,
                zooms: &[],
            })
        }
    };
}

/// The ten sections, in page order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1_BEATS),
    section!(2, SEC2_BEATS),
    section!(3, SEC3_BEATS),
    section!(4, SEC4_BEATS),
    section!(5, SEC5_BEATS),
    section!(6, SEC6_BEATS),
    section!(7, SEC7_BEATS),
    section!(8, SEC8_BEATS),
    section!(9, SEC9_BEATS),
    section!(10, SEC10_BEATS),
];

// ---- 1. what happens: rock to metallurgical-grade silicon ------------------------------

const SEC1_BEATS: &[Beat] = &[
    Beat::new("three raw piles: quartzite for silicon, coke and coal for carbon, wood chips for air", BEAT_MS)
        .note(
            "Plain quartzite (SiO2) brings the silicon. Coke and coal bring the carbon that strips the oxygen off it. Wood chips add carbon too and keep the burden open so gas can climb through.",
            "the white, black and tan piles, and lumps riding the belt toward the furnace",
        )
        .detail(
            "The feed is sized lumps, not dust. A loose, mixed burden lets hot gas through, and the rare high-purity quartz is a separate chain (section 8).",
            &[
                "Feed is plain quartzite, not high-purity quartz",
                "Reductants: coal, coke and wood chips",
                "Crushed to lumps, then blended",
            ],
        ),
    Beat::new("an electric arc furnace runs 24/7 and silicon is tapped from the base", BEAT_MS)
        .note(
            "Electrodes carry current into the burden and the arcs at their tips do the chemistry. The furnace never stops; liquid silicon is tapped from the bottom into a ladle.",
            "the glowing cavities under the electrodes, and the stream running down the launder into the ladle",
        )
        .detail(
            "Electricity is the main cost, so the furnace is kept running around the clock.",
            &[
                "Electric arc furnace, 24/7 operation",
                "11-13 MWh of power per tonne of silicon",
                "Tapped on a regular schedule",
            ],
        ),
    Beat::new("the metal is cast, crushed and screened into 98-99% pure silicon", BEAT_MS)
        .note(
            "The ladle is poured into a casting bed. The slab is crushed and screened to the lump size customers buy. That is metallurgical-grade silicon, about 2N.",
            "the slab setting in the bed, then lumps tumbling out of the crusher into a heap",
        )
        .detail(
            "Only 80-90% of the silicon charged ends up as product. The rest is lost to fume and slag.",
            &[
                "MG-Si: 98-99% pure (2N)",
                "Roughly 10,000 ppm impurities",
                "Cast, crushed and screened",
            ],
        ),
];

// ---- 2. inside a submerged arc furnace --------------------------------------------------

const SEC2_BEATS: &[Beat] = &[
    Beat::new("in section the furnace is layered: cool charge on top, SiC lower, cavities and pool at the bottom", BEAT_MS)
        .note(
            "Fresh charge preheats near the top. Lower down, rising SiO meets carbon and makes SiC. Around the electrode tips sit the hot cavities, and liquid silicon pools on the hearth.",
            "the bands in the cut face from the brown charge down to the glowing pool",
        )
        .detail(
            "Each layer does one job, and the furnace works only if the charge keeps moving down through all of them.",
            &[
                "Charge is fed continuously at the top",
                "SiC forms where SiO meets carbon",
                "Arc zone above 1800 C",
            ],
        ),
    Beat::new("from above: three carbon electrodes on three-phase power, one cavity each", BEAT_MS)
        .note(
            "Copper busbars bring current from a three-phase transformer to three electrodes set in a triangle. Each electrode holds its own arc cavity in the charge.",
            "the transformer and busbars, the three electrodes, and a glowing cavity under each tip",
        )
        .detail(
            "Three phases share the load evenly, which is why furnaces have three electrodes.",
            &[
                "Three electrodes on three-phase AC",
                "One gas cavity per electrode tip",
                "11-13 MWh per tonne of silicon",
            ],
        ),
    Beat::new("electrodes burn away and are slipped down; the pool is tapped from the side", BEAT_MS)
        .note(
            "The carbon electrodes are consumed as they run, so they are lowered a little at a time to hold the arc in place. Silicon on the hearth leaves through the tap hole.",
            "the electrodes inching down, and the tap hole at the base of the wall",
        )
        .detail(
            "Keeping the tips at the right depth keeps the cavities where the chemistry needs them.",
            &[
                "The electrodes are carbon and burn away",
                "Silicon melts at 1414 C",
                "The pool is tapped on a regular schedule",
            ],
        ),
];

// ---- 3. the chemistry -------------------------------------------------------------------

const SEC3_BEATS: &[Beat] = &[
    Beat::new("in the hot cavity: SiO2 + C gives SiO + CO", BEAT_MS)
        .note(
            "Quartz and carbon meet at the hot wall. The silicon leaves as SiO gas and the oxygen as CO. Grey is silicon, red oxygen, black carbon.",
            "a SiO2 molecule and a carbon atom sliding together, then SiO and CO flying apart",
        )
        .detail(
            "Making a gas first lets the silicon move to where the SiC is.",
            &[
                "SiO2 + C gives SiO + CO",
                "Strongly endothermic",
                "Arc zone above 1800 C",
            ],
        ),
    Beat::new("higher and cooler: SiO + 2C gives SiC + CO", BEAT_MS)
        .note(
            "SiO that climbs into the cooler charge meets carbon and becomes silicon carbide. The SiC sinks back down with the charge.",
            "SiO bubbles rising up the column, then SiO and two carbons turning into SiC and CO",
        )
        .detail(
            "This step catches silicon that would otherwise leave as fume, and makes the SiC the last step needs.",
            &[
                "SiO + 2C gives SiC + CO",
                "SiC is a hard, porous solid (ESGI report)",
                "SiO that escapes becomes fume",
            ],
        ),
    Beat::new("back at the cavity: SiO + SiC gives 2Si + CO, the liquid metal", BEAT_MS)
        .note(
            "SiC reaching the cavity reacts with more SiO. The result is two silicon atoms, liquid at this heat, and CO. Overall: SiO2 + 2C gives Si + 2CO.",
            "SiO and SiC sliding together, then two silicon atoms and a CO",
        )
        .detail(
            "This step makes the silicon that is tapped from the furnace.",
            &[
                "SiO + SiC gives 2 Si + CO",
                "Overall: SiO2 + 2C gives Si + 2CO",
                "Silicon melts at 1414 C",
            ],
        ),
];

// ---- 4. by the numbers ------------------------------------------------------------------

const SEC4_BEATS: &[Beat] = &[
    Beat::new("temperature: the arc zone runs above 1800 C, well past silicon's 1414 C melt", BEAT_MS)
        .note(
            "The orange column fills past the 1414 C mark where silicon melts and on above 1800 C, the heat in the arc zone.",
            "the column rising past both tick marks",
        )
        .detail(
            "Temperature drives the reactions; the arc is the hottest place in the furnace.",
            &[
                "Arc zone above 1800 C",
                "Silicon melts at 1414 C",
                "Hearth at 2200-2400 K (Elkem and Oxford ESGI report)",
            ],
        ),
    Beat::new("power: 11 to 13 MWh of electricity per tonne of silicon", BEAT_MS)
        .note(
            "The blue column fills into the lit 11-13 MWh band. One patent example ran at 11.2 MWh per tonne. Bigger furnaces and better control keep pushing it down.",
            "the column climbing into the glowing band",
        )
        .detail(
            "Power is the largest cost of every tonne, so cheap electricity decides where smelters are built.",
            &[
                "11-13 MWh per tonne of silicon",
                "One patent example: 11.2 MWh/t",
                "Trend: bigger furnaces and better control",
            ],
        ),
    Beat::new("purity: the product is 98-99% silicon, about 2N", BEAT_MS)
        .note(
            "On a 90-100% scale the grey column stops between the 98% and 99% marks. The rest, about 10,000 ppm, is iron, aluminium, calcium and other impurities.",
            "the column filling to just under 99%",
        )
        .detail(
            "Purity sets the grade and the price. POLYSILICON, the next step, cleans it much further.",
            &[
                "98-99% pure, about 2N",
                "Roughly 10,000 ppm impurities",
                "Section 7 is the purity ladder",
            ],
        ),
];

// ---- 5. who makes it --------------------------------------------------------------------

const SEC5_BEATS: &[Beat] = &[
    Beat::new("China makes about 4,000 thousand tonnes of silicon metal a year", BEAT_MS)
        .note(
            "China's bar alone rises to 4,000 kt of Si in 2025e (USGS).",
            "one red bar climbing far above the plinth",
        )
        .detail(
            "Concentration is the market's main risk: one country sets most of the supply.",
            &[
                "China 4,000 kt Si (2025e)",
                "With ferrosilicon, almost 80% of all silicon materials",
                "Source: USGS Mineral Commodity Summaries 2026",
            ],
        ),
    Beat::new("everyone else is small: Brazil 180, Norway 130, France 68", BEAT_MS)
        .note(
            "Close up, the next producers barely leave the plinth. After them come Australia, Russia, Canada, Iceland, Germany, South Africa and others.",
            "the short blue bars beside the edge of China's",
        )
        .detail(
            "Outside China, output is spread across many small producers, so no one else moves the market alone.",
            &[
                "Brazil 180 kt",
                "Norway 130 kt",
                "France 68 kt",
            ],
        ),
    Beat::new("the world total is 4,600 thousand tonnes, about 87% of it Chinese", BEAT_MS)
        .note(
            "A stacked world bar: China's red share at the bottom, everyone else the thin blue cap.",
            "the world bar growing, red almost to the top",
        )
        .detail(
            "The figures are USGS estimates for 2025, not final reported output.",
            &[
                "World total 4,600 kt (2025e)",
                "China about 87%",
                "2025e is an estimate",
            ],
        ),
];

// ---- 6. price ---------------------------------------------------------------------------

const SEC6_BEATS: &[Beat] = &[
    Beat::new("US silicon metal jumped from 220 to 362 cents per pound in 2022", BEAT_MS)
        .note(
            "The 2021 bar rises to 220 cents per pound and the 2022 bar to 362, the peak of the series.",
            "two bars growing, the second, darker one tallest",
        )
        .detail(
            "Prices swing between tight markets and oversupply. 2022 was the tight market.",
            &[
                "2021: 220 cents per pound",
                "2022: 362 cents per pound",
                "USGS and S&P Platts",
            ],
        ),
    Beat::new("prices fell back to 180 and 170 cents in 2023 and 2024", BEAT_MS)
        .note(
            "As supply caught up, the price halved from the peak.",
            "the 2023 and 2024 bars rising only half as high",
        )
        .detail(
            "Imports and Chinese output are the swing factors in the US price.",
            &[
                "2023: 180 cents per pound",
                "2024: 170 cents per pound",
                "Supply grew through this period",
            ],
        ),
    Beat::new("2025e: about 130 cents, with China at its lowest since 2016", BEAT_MS)
        .note(
            "Oversupply and weak demand push the 2025 estimate down to about 130 cents per pound. China's prices in April were the lowest since November 2016.",
            "the shortest bar at the end of the row",
        )
        .detail(
            "The price series is from USGS and S&P Platts, and the 2025 figure is an estimate.",
            &[
                "2025e: 130 cents per pound",
                "China prices lowest since November 2016 (April)",
                "Oversupply and weak demand",
            ],
        ),
];

// ---- 7. purity ladder -------------------------------------------------------------------

const SEC7_BEATS: &[Beat] = &[
    Beat::new("metallurgical grade: 98-99% pure, about 10,000 ppm of impurities", BEAT_MS)
        .note(
            "A block of furnace silicon. The red dots stand for impurity atoms: plenty of them.",
            "the first block rising, then filling with red dots",
        )
        .detail(
            "This is what the furnace makes, before any cleaning.",
            &[
                "98-99% pure (2N)",
                "About 10,000 ppm impurities",
                "POLYSILICON does the cleaning",
            ],
        ),
    Beat::new("solar grade: 99.9999% pure, about 1 ppm", BEAT_MS)
        .note(
            "After refining, only a handful of dots remain.",
            "the second block with just four dots",
        )
        .detail(
            "Solar cells need about four orders of magnitude less impurity than metallurgical grade.",
            &[
                "99.9999% (6N)",
                "About 1 ppm impurities",
                "Solar grade, after POLYSILICON",
            ],
        ),
    Beat::new("electronic grade: 99.9999999% pure, about 1 ppb", BEAT_MS)
        .note(
            "Chip-grade silicon. At this scale not one dot is left.",
            "the third block, clear",
        )
        .detail(
            "POLYSILICON does the seven orders of magnitude of cleaning between the first block and the last.",
            &[
                "99.9999999% (9N)",
                "About 1 ppb impurities",
                "Seven orders of magnitude of cleaning",
            ],
        ),
];

// ---- 8. chokepoint: high-purity quartz --------------------------------------------------

const SEC8_BEATS: &[Beat] = &[
    Beat::new("Spruce Pine, North Carolina, supplies an estimated 70-90% of high-purity quartz", BEAT_MS)
        .note(
            "One district of white quartz benches produces most of the world's quartz pure enough for crucibles. The ring fills to 80%, the middle of the estimate.",
            "the terraced quartz hill, and the gold ring segments lighting up",
        )
        .detail(
            "Concentration makes the crucible supply a chokepoint for the whole wafer chain.",
            &[
                "Spruce Pine: estimated 70-90% of commercial high-purity quartz",
                "Mines: Sibelco and The Quartz Corp (Imerys / Norsk Mineral JV)",
                "Source 3 on the sources page",
            ],
        ),
    Beat::new("the quartz becomes crucibles that hold the melt in MELT + PULL", BEAT_MS)
        .note(
            "Quartz rides the line into a crystal puller, where a quartz crucible holds the molten silicon the ingot is pulled from. Each crucible lasts hundreds of hours.",
            "lumps travelling into the puller and the glowing melt in the white crucible",
        )
        .detail(
            "The crucible is used up in the pull, so the supply has to keep coming.",
            &[
                "Crucibles are used in MELT + PULL",
                "They last hundreds of hours",
                "This is quartz, not the furnace's quartzite",
            ],
        ),
    Beat::new("one outage breaks the line: Hurricane Helene in 2024", BEAT_MS)
        .note(
            "Helene flooded the region in 2024 and the supply line broke. With few other mines making this grade, the gap reaches wafer makers.",
            "the black gap in the belt and the red alarm flashing over it",
        )
        .detail(
            "One region's outage reaches the wafer supply because so few mines make this grade.",
            &[
                "Hurricane Helene, 2024",
                "The outage shook wafer supply",
                "Crucibles last hundreds of hours, then need replacing",
            ],
        ),
];

// ---- 9. market context ------------------------------------------------------------------

const SEC9_BEATS: &[Beat] = &[
    Beat::new("US silicon metal imports rose from 117 to about 180 thousand tonnes", BEAT_MS)
        .note(
            "Imports were 117 kt in 2024 and an estimated 180 kt in 2025, amid worries about tariffs and export curbs.",
            "two blue bars, the 2025e one much taller",
        )
        .detail(
            "Imports show how much of the US supply comes from outside.",
            &[
                "2024: 117 kt",
                "2025e: 180 kt",
                "Tariff and export-curb worries",
            ],
        ),
    Beat::new("tariffs and export curbs decide what crosses the border", BEAT_MS)
        .note(
            "Containers pass through the trade gate. Silicon was added to the US critical minerals list in November 2025.",
            "containers rolling through the gold gate",
        )
        .detail(
            "Trade policy is one of the factors in the price, alongside supply and demand.",
            &[
                "Silicon added to the US critical minerals list, November 2025",
                "Tariff and export-curb worries",
                "Imports 180 kt (2025e)",
            ],
        ),
    Beat::new("China's #553 grade traded near 10,600 yuan per tonne in early 2025", BEAT_MS)
        .note(
            "The red bar is China's #553 reference grade, about 10,500-10,700 yuan per tonne in February and March 2025 (SMM). Listed names: Ferroglobe (GSM) and Elkem (ELK.OL).",
            "the red China price bar rising at the end of the row",
        )
        .detail(
            "This is a daily market reference, not a US quote. Sibelco and Quartz Corp are private.",
            &[
                "China #553: about 10,500-10,700 yuan per tonne (Feb-Mar 2025)",
                "Listed: Ferroglobe (GSM), Elkem (ELK.OL)",
                "Sibelco and Quartz Corp are private",
            ],
        ),
];

// ---- 10. sources ------------------------------------------------------------------------

const SEC10_BEATS: &[Beat] = &[
    Beat::new("sources 1 and 2: USGS for output and price, a patent and paper for the process", BEAT_MS)
        .note(
            "The USGS report gives production, price, imports and the China share. The patent and the Hrcak paper cover the energy figures and the reaction steps.",
            "two cards dropping onto the stack",
        )
        .detail(
            "Each number on the page traces back to one of these sources.",
            &[
                "[1] USGS Mineral Commodity Summaries 2026, silicon",
                "[2] US patent 12157671; hrcak.srce.hr/347941",
                "The full list is the Sources section of the page",
            ],
        ),
    Beat::new("sources 3 and 4: the quartz chain and the China price", BEAT_MS)
        .note(
            "The Spruce Pine share of high-purity quartz, and the China #553 price from the SMM daily review.",
            "two more cards filing onto the stack",
        )
        .detail(
            "The market figures are the least certain part of the page, so they are the ones to check first.",
            &[
                "[3] Spruce Pine HPQ: konvoy.beehiiv.com",
                "[4] China #553: news.metal.com (SMM daily review)",
                "Prices come from daily reviews, not contracts",
            ],
        ),
    Beat::new("four sources, one stack", BEAT_MS)
        .note(
            "Production, price and energy come from sources 1 and 2; the quartz chain and the China price from 3 and 4.",
            "the finished, fanned stack of four cards",
        )
        .detail(
            "Four sources back every figure on this page.",
            &[
                "Four sources on this page",
                "Sources 1 and 2: production, price, energy",
                "Sources 3 and 4: quartz and the China price",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_section_has_three_explained_beats() {
        for (n, build) in SECTIONS.iter().enumerate() {
            let s = build();
            assert_eq!(s.beats().len(), 3, "section {}", n + 1);
            super::super::tests::explained(s.as_ref(), &format!("section {}", n + 1));
        }
    }

    #[test]
    fn every_section_draws_every_beat() {
        for (n, build) in SECTIONS.iter().enumerate() {
            super::super::tests::draws_every_beat(build().as_ref(), &format!("section {}", n + 1));
        }
    }
}
