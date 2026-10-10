// Visuals for pages SAND, POLYSILICON, MELT + PULL, INGOT, SLICE + POLISH
// (see diagrams_vis.rs for the template). GENERATED from a scratch data set;
// edit freely, but keep spot needles in sync with the art.

#[allow(unused_imports)]
use super::diagrams_vis::{Spot, TO_EOL, Visual, spot};

pub fn lookup(page: &str, card: &str, section: &str) -> Option<Visual> {
    match (page, card, section) {
        (r#"SAND"#, r#"CRUSH"#, r#"Sizing the burden"#) => Some(Visual {
            art: V0_0_ART,
            spots: V0_0_SPOTS,
        }),
        (r#"SAND"#, r#"CRUSH"#, r#"Keep impurities out"#) => Some(Visual {
            art: V0_1_ART,
            spots: V0_1_SPOTS,
        }),
        (r#"SAND"#, r#"CRUSH"#, r#"Fume loss"#) => Some(Visual {
            art: V0_2_ART,
            spots: V0_2_SPOTS,
        }),
        (r#"SAND"#, r#"BLEND"#, r#"The mix"#) => Some(Visual {
            art: V1_0_ART,
            spots: V1_0_SPOTS,
        }),
        (r#"SAND"#, r#"BLEND"#, r#"Carbon purity"#) => Some(Visual {
            art: V1_1_ART,
            spots: V1_1_SPOTS,
        }),
        (r#"SAND"#, r#"BLEND"#, r#"Carbon balance"#) => Some(Visual {
            art: V1_2_ART,
            spots: V1_2_SPOTS,
        }),
        (r#"SAND"#, r#"ARC FURNACE"#, r#"Submerged arc"#) => Some(Visual {
            art: V2_0_ART,
            spots: V2_0_SPOTS,
        }),
        (r#"SAND"#, r#"ARC FURNACE"#, r#"Power and cost"#) => Some(Visual {
            art: V2_1_ART,
            spots: V2_1_SPOTS,
        }),
        (r#"SAND"#, r#"ARC FURNACE"#, r#"Why 24/7 and why hydro"#) => Some(Visual {
            art: V2_2_ART,
            spots: V2_2_SPOTS,
        }),
        (r#"SAND"#, r#"TAP"#, r#"Tapping the metal"#) => Some(Visual {
            art: V3_0_ART,
            spots: V3_0_SPOTS,
        }),
        (r#"SAND"#, r#"TAP"#, r#"Fume at the tap floor"#) => Some(Visual {
            art: V3_1_ART,
            spots: V3_1_SPOTS,
        }),
        (r#"SAND"#, r#"TAP"#, r#"Recovery"#) => Some(Visual {
            art: V3_2_ART,
            spots: V3_2_SPOTS,
        }),
        (r#"SAND"#, r#"CAST + CRUSH"#, r#"Product form and grade"#) => Some(Visual {
            art: V4_0_ART,
            spots: V4_0_SPOTS,
        }),
        (r#"SAND"#, r#"CAST + CRUSH"#, r#"Where it goes"#) => Some(Visual {
            art: V4_1_ART,
            spots: V4_1_SPOTS,
        }),
        (r#"SAND"#, r#"CAST + CRUSH"#, r#"Price"#) => Some(Visual {
            art: V4_2_ART,
            spots: V4_2_SPOTS,
        }),
        (r#"SAND"#, r#"ELECTRODE 2"#, r#"Carbon columns"#) => Some(Visual {
            art: V5_0_ART,
            spots: V5_0_SPOTS,
        }),
        (r#"SAND"#, r#"ELECTRODE 2"#, r#"Three phases"#) => Some(Visual {
            art: V5_1_ART,
            spots: V5_1_SPOTS,
        }),
        (r#"SAND"#, r#"ELECTRODE 2"#, r#"Wear and contamination"#) => Some(Visual {
            art: V5_2_ART,
            spots: V5_2_SPOTS,
        }),
        (r#"SAND"#, r#"CHARGE"#, r#"The sinking burden"#) => Some(Visual {
            art: V6_0_ART,
            spots: V6_0_SPOTS,
        }),
        (r#"SAND"#, r#"CHARGE"#, r#"When it goes wrong"#) => Some(Visual {
            art: V6_1_ART,
            spots: V6_1_SPOTS,
        }),
        (r#"SAND"#, r#"CHARGE"#, r#"Fume loss"#) => Some(Visual {
            art: V6_2_ART,
            spots: V6_2_SPOTS,
        }),
        (r#"SAND"#, r#"ARC CAVITIES"#, r#"Where the chemistry happens"#) => Some(Visual {
            art: V7_0_ART,
            spots: V7_0_SPOTS,
        }),
        (r#"SAND"#, r#"ARC CAVITIES"#, r#"Recapture and fume"#) => Some(Visual {
            art: V7_1_ART,
            spots: V7_1_SPOTS,
        }),
        (r#"SAND"#, r#"MOLTEN SILICON POOL"#, r#"Silicon hearth"#) => Some(Visual {
            art: V8_0_ART,
            spots: V8_0_SPOTS,
        }),
        (r#"SAND"#, r#"MOLTEN SILICON POOL"#, r#"Purity is set here"#) => Some(Visual {
            art: V8_1_ART,
            spots: V8_1_SPOTS,
        }),
        (r#"SAND"#, r#"tap hole"#, r#"Opening and closing"#) => Some(Visual {
            art: V9_0_ART,
            spots: V9_0_SPOTS,
        }),
        (r#"SAND"#, r#"tap hole"#, r#"Fume and environment"#) => Some(Visual {
            art: V9_1_ART,
            spots: V9_1_SPOTS,
        }),
        (r#"SAND"#, r#"tap hole"#, r#"Wear"#) => Some(Visual {
            art: V9_2_ART,
            spots: V9_2_SPOTS,
        }),
        (r#"SAND"#, r#"CO + SiO fume"#, r#"Off-gas"#) => Some(Visual {
            art: V10_0_ART,
            spots: V10_0_SPOTS,
        }),
        (r#"SAND"#, r#"CO + SiO fume"#, r#"Silica fume"#) => Some(Visual {
            art: V10_1_ART,
            spots: V10_1_SPOTS,
        }),
        (r#"SAND"#, r#"CO + SiO fume"#, r#"Yield lost"#) => Some(Visual {
            art: V10_2_ART,
            spots: V10_2_SPOTS,
        }),
        (r#"SAND"#, r#"electricity"#, r#"The cost line"#) => Some(Visual {
            art: V11_0_ART,
            spots: V11_0_SPOTS,
        }),
        (r#"SAND"#, r#"electricity"#, r#"Power contracts"#) => Some(Visual {
            art: V11_1_ART,
            spots: V11_1_SPOTS,
        }),
        (r#"SAND"#, r#"electricity"#, r#"What it means for chips"#) => Some(Visual {
            art: V11_2_ART,
            spots: V11_2_SPOTS,
        }),
        (r#"SAND"#, r#"World total"#, r#"Concentration"#) => Some(Visual {
            art: V12_0_ART,
            spots: V12_0_SPOTS,
        }),
        (r#"SAND"#, r#"World total"#, r#"Trade pressure"#) => Some(Visual {
            art: V12_1_ART,
            spots: V12_1_SPOTS,
        }),
        (r#"SAND"#, r#"World total"#, r#"Price"#) => Some(Visual {
            art: V12_2_ART,
            spots: V12_2_SPOTS,
        }),
        (r#"SAND"#, r#"Spruce Pine"#, r#"Crucible quartz chokepoint"#) => Some(Visual {
            art: V13_0_ART,
            spots: V13_0_SPOTS,
        }),
        (r#"SAND"#, r#"Spruce Pine"#, r#"Helene timeline"#) => Some(Visual {
            art: V13_1_ART,
            spots: V13_1_SPOTS,
        }),
        (r#"SAND"#, r#"Spruce Pine"#, r#"No easy substitute"#) => Some(Visual {
            art: V13_2_ART,
            spots: V13_2_SPOTS,
        }),
        (r#"SAND"#, r#"Ferroglobe"#, r#"Q2 2026"#) => Some(Visual {
            art: V14_0_ART,
            spots: V14_0_SPOTS,
        }),
        (r#"SAND"#, r#"Ferroglobe"#, r#"Read-through"#) => Some(Visual {
            art: V14_1_ART,
            spots: V14_1_SPOTS,
        }),
        (r#"SAND"#, r#"Ferroglobe"#, r#"Other listed names"#) => Some(Visual {
            art: V14_2_ART,
            spots: V14_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"MG-Si"#, r#"Why go through chlorides"#) => Some(Visual {
            art: V15_0_ART,
            spots: V15_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"MG-Si"#, r#"Where the feed comes from"#) => Some(Visual {
            art: V15_1_ART,
            spots: V15_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Si + HCl"#, r#"Trichlorosilane synthesis"#) => Some(Visual {
            art: V16_0_ART,
            spots: V16_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Si + HCl"#, r#"TCS properties"#) => Some(Visual {
            art: V16_1_ART,
            spots: V16_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Si + HCl"#, r#"Alternative: granules"#) => Some(Visual {
            art: V16_2_ART,
            spots: V16_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"DISTILL"#, r#"Boiling points"#) => Some(Visual {
            art: V17_0_ART,
            spots: V17_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"DISTILL"#, r#"Spec ladder"#) => Some(Visual {
            art: V17_1_ART,
            spots: V17_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"DISTILL"#, r#"Capacity"#) => Some(Visual {
            art: V17_2_ART,
            spots: V17_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"BELL JAR"#, r#"Deposition batch"#) => Some(Visual {
            art: V18_0_ART,
            spots: V18_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"BELL JAR"#, r#"Growth and power"#) => Some(Visual {
            art: V18_1_ART,
            spots: V18_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"BELL JAR"#, r#"After the batch"#) => Some(Visual {
            art: V18_2_ART,
            spots: V18_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"CRUSH"#, r#"Crushing and etching"#) => Some(Visual {
            art: V19_0_ART,
            spots: V19_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"CRUSH"#, r#"Popcorn grading"#) => Some(Visual {
            art: V19_1_ART,
            spots: V19_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"CRUSH"#, r#"Etch capacity"#) => Some(Visual {
            art: V19_2_ART,
            spots: V19_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"POLY"#, r#"What the customer buys"#) => Some(Visual {
            art: V20_0_ART,
            spots: V20_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"POLY"#, r#"Chunks vs granules"#) => Some(Visual {
            art: V20_1_ART,
            spots: V20_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"POLY"#, r#"Demand"#) => Some(Visual {
            art: V20_2_ART,
            spots: V20_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"WATER-COOLED STEEL BELL JAR"#, r#"Why a cold wall"#) => {
            Some(Visual {
                art: V21_0_ART,
                spots: V21_0_SPOTS,
            })
        }
        (r#"POLYSILICON"#, r#"WATER-COOLED STEEL BELL JAR"#, r#"Heat recovery"#) => Some(Visual {
            art: V21_1_ART,
            spots: V21_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"WATER-COOLED STEEL BELL JAR"#, r#"Popcorn causes"#) => Some(Visual {
            art: V21_2_ART,
            spots: V21_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"U-bridge"#, r#"Rod pairs"#) => Some(Visual {
            art: V22_0_ART,
            spots: V22_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"U-bridge"#, r#"Failure risks"#) => Some(Visual {
            art: V22_1_ART,
            spots: V22_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"graphite chucks"#, r#"Contacts"#) => Some(Visual {
            art: V23_0_ART,
            spots: V23_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"graphite chucks"#, r#"Contamination"#) => Some(Visual {
            art: V23_1_ART,
            spots: V23_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"slim rod 20 mm"#, r#"Growth to 150-180 mm"#) => Some(Visual {
            art: V24_0_ART,
            spots: V24_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"slim rod 20 mm"#, r#"Popcorn"#) => Some(Visual {
            art: V24_1_ART,
            spots: V24_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"slim rod 20 mm"#, r#"EG is not solar"#) => Some(Visual {
            art: V24_2_ART,
            spots: V24_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Special EG"#, r#"Purity spec"#) => Some(Visual {
            art: V25_0_ART,
            spots: V25_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Special EG"#, r#"Why chips need it"#) => Some(Visual {
            art: V25_1_ART,
            spots: V25_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Special EG"#, r#"A moving ladder"#) => Some(Visual {
            art: V25_2_ART,
            spots: V25_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Tongwei"#, r#"Capacity ranks"#) => Some(Visual {
            art: V26_0_ART,
            spots: V26_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Tongwei"#, r#"Price glut"#) => Some(Visual {
            art: V26_1_ART,
            spots: V26_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Tongwei"#, r#"Relevance to chips"#) => Some(Visual {
            art: V26_2_ART,
            spots: V26_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Wacker"#, r#"The leading EG supplier"#) => Some(Visual {
            art: V27_0_ART,
            spots: V27_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Wacker"#, r#"2025 expansion"#) => Some(Visual {
            art: V27_1_ART,
            spots: V27_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Wacker"#, r#"Energy intensity"#) => Some(Visual {
            art: V27_2_ART,
            spots: V27_2_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Hemlock"#, r#"US chip-grade supply"#) => Some(Visual {
            art: V28_0_ART,
            spots: V28_0_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Hemlock"#, r#"Section 232 prices"#) => Some(Visual {
            art: V28_1_ART,
            spots: V28_1_SPOTS,
        }),
        (r#"POLYSILICON"#, r#"Hemlock"#, r#"Effect on makers"#) => Some(Visual {
            art: V28_2_ART,
            spots: V28_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"LOAD"#, r#"The charge"#) => Some(Visual {
            art: V29_0_ART,
            spots: V29_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"LOAD"#, r#"Dopant compromise"#) => Some(Visual {
            art: V29_1_ART,
            spots: V29_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"LOAD"#, r#"Batch economics"#) => Some(Visual {
            art: V29_2_ART,
            spots: V29_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"~1414 C, argon"#, r#"Melt under argon"#) => Some(Visual {
            art: V30_0_ART,
            spots: V30_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"~1414 C, argon"#, r#"What argon does"#) => Some(Visual {
            art: V30_1_ART,
            spots: V30_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"~1414 C, argon"#, r#"Slow thermal loop"#) => Some(Visual {
            art: V30_2_ART,
            spots: V30_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"Seed and neck"#) => Some(Visual {
            art: V31_0_ART,
            spots: V31_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"The limit"#) => Some(Visual {
            art: V31_1_ART,
            spots: V31_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"Failure mode"#) => Some(Visual {
            art: V31_2_ART,
            spots: V31_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Flaring out"#) => Some(Visual {
            art: V32_0_ART,
            spots: V32_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Temperature takes over"#) => Some(Visual {
            art: V32_1_ART,
            spots: V32_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Scrap and risk"#) => Some(Visual {
            art: V32_2_ART,
            spots: V32_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"300 mm, slow"#, r#"Body growth"#) => Some(Visual {
            art: V33_0_ART,
            spots: V33_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"300 mm, slow"#, r#"Throughput arithmetic"#) => Some(Visual {
            art: V33_1_ART,
            spots: V33_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"300 mm, slow"#, r#"Controls during the body"#) => Some(Visual {
            art: V33_2_ART,
            spots: V33_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"TAIL"#, r#"End cone"#) => Some(Visual {
            art: V34_0_ART,
            spots: V34_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"TAIL"#, r#"Segregation"#) => Some(Visual {
            art: V34_1_ART,
            spots: V34_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"TAIL"#, r#"Yield cost"#) => Some(Visual {
            art: V34_2_ART,
            spots: V34_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"A consumable"#) => Some(Visual {
            art: V35_0_ART,
            spots: V35_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"Supply"#) => Some(Visual {
            art: V35_1_ART,
            spots: V35_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"Why it matters"#) => Some(Visual {
            art: V35_2_ART,
            spots: V35_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Melt convection"#) => Some(Visual {
            art: V36_0_ART,
            spots: V36_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Magnetic damping"#) => Some(Visual {
            art: V36_1_ART,
            spots: V36_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Axial gradient"#) => Some(Visual {
            art: V36_2_ART,
            spots: V36_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"GRAPHITE HEATER"#, r#"Hot zone"#) => Some(Visual {
            art: V37_0_ART,
            spots: V37_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"GRAPHITE HEATER"#, r#"Graphite and SiO"#) => Some(Visual {
            art: V37_1_ART,
            spots: V37_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"GRAPHITE HEATER"#, r#"Power per kg"#) => Some(Visual {
            art: V37_2_ART,
            spots: V37_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"The envelope"#) => Some(Visual {
            art: V38_0_ART,
            spots: V38_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"Diameter control"#) => Some(Visual {
            art: V38_1_ART,
            spots: V38_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"Failure modes"#) => Some(Visual {
            art: V38_2_ART,
            spots: V38_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Oxygen"#, r#"Where oxygen comes from"#) => Some(Visual {
            art: V39_0_ART,
            spots: V39_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Oxygen"#, r#"Villain and tool"#) => Some(Visual {
            art: V39_1_ART,
            spots: V39_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Oxygen"#, r#"Control at 300 mm"#) => Some(Visual {
            art: V39_2_ART,
            spots: V39_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Dash neck"#, r#"Necking"#) => Some(Visual {
            art: V40_0_ART,
            spots: V40_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Dash neck"#, r#"The trade-off"#) => Some(Visual {
            art: V40_1_ART,
            spots: V40_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Dash neck"#, r#"Pull rate in context"#) => Some(Visual {
            art: V40_2_ART,
            spots: V40_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"Top two"#) => Some(Visual {
            art: V41_0_ART,
            spots: V41_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"The cycle"#) => Some(Visual {
            art: V41_1_ART,
            spots: V41_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"Pricing power"#) => Some(Visual {
            art: V41_2_ART,
            spots: V41_2_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Yield"#, r#"Structure losses"#) => Some(Visual {
            art: V42_0_ART,
            spots: V42_0_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Yield"#, r#"Cyclicality"#) => Some(Visual {
            art: V42_1_ART,
            spots: V42_1_SPOTS,
        }),
        (r#"MELT + PULL"#, r#"Yield"#, r#"Open problems"#) => Some(Visual {
            art: V42_2_ART,
            spots: V42_2_SPOTS,
        }),
        (r#"INGOT"#, r#"AS-PULLED"#, r#"A rough cylinder"#) => Some(Visual {
            art: V43_0_ART,
            spots: V43_0_SPOTS,
        }),
        (r#"INGOT"#, r#"AS-PULLED"#, r#"Handling"#) => Some(Visual {
            art: V43_1_ART,
            spots: V43_1_SPOTS,
        }),
        (r#"INGOT"#, r#"AS-PULLED"#, r#"Capacity limit"#) => Some(Visual {
            art: V43_2_ART,
            spots: V43_2_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP"#, r#"The cuts"#) => Some(Visual {
            art: V44_0_ART,
            spots: V44_0_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP"#, r#"Measured, not fixed"#) => Some(Visual {
            art: V44_1_ART,
            spots: V44_1_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP"#, r#"Missed defects"#) => Some(Visual {
            art: V44_2_ART,
            spots: V44_2_SPOTS,
        }),
        (r#"INGOT"#, r#"TEST"#, r#"Orientation check"#) => Some(Visual {
            art: V45_0_ART,
            spots: V45_0_SPOTS,
        }),
        (r#"INGOT"#, r#"TEST"#, r#"Orientation matters"#) => Some(Visual {
            art: V45_1_ART,
            spots: V45_1_SPOTS,
        }),
        (r#"INGOT"#, r#"TEST"#, r#"Last cheap point"#) => Some(Visual {
            art: V45_2_ART,
            spots: V45_2_SPOTS,
        }),
        (r#"INGOT"#, r#"GRIND OD"#, r#"Grinding to size"#) => Some(Visual {
            art: V46_0_ART,
            spots: V46_0_SPOTS,
        }),
        (r#"INGOT"#, r#"GRIND OD"#, r#"Why diameter matters"#) => Some(Visual {
            art: V46_1_ART,
            spots: V46_1_SPOTS,
        }),
        (r#"INGOT"#, r#"GRIND OD"#, r#"Silicon lost"#) => Some(Visual {
            art: V46_2_ART,
            spots: V46_2_SPOTS,
        }),
        (r#"INGOT"#, r#"NOTCH"#, r#"The groove"#) => Some(Visual {
            art: V47_0_ART,
            spots: V47_0_SPOTS,
        }),
        (r#"INGOT"#, r#"NOTCH"#, r#"Why <110>"#) => Some(Visual {
            art: V47_1_ART,
            spots: V47_1_SPOTS,
        }),
        (r#"INGOT"#, r#"NOTCH"#, r#"Notch vs flat"#) => Some(Visual {
            art: V47_2_ART,
            spots: V47_2_SPOTS,
        }),
        (r#"INGOT"#, r#"WIRE SAW"#, r#"Wire web"#) => Some(Visual {
            art: V48_0_ART,
            spots: V48_0_SPOTS,
        }),
        (r#"INGOT"#, r#"WIRE SAW"#, r#"Kerf"#) => Some(Visual {
            art: V48_1_ART,
            spots: V48_1_SPOTS,
        }),
        (r#"INGOT"#, r#"WIRE SAW"#, r#"Cut geometry"#) => Some(Visual {
            art: V48_2_ART,
            spots: V48_2_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP LINE"#, r#"Where the lines go"#) => Some(Visual {
            art: V49_0_ART,
            spots: V49_0_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP LINE"#, r#"Decided by measurement"#) => Some(Visual {
            art: V49_1_ART,
            spots: V49_1_SPOTS,
        }),
        (r#"INGOT"#, r#"CROP LINE"#, r#"Trade-off"#) => Some(Visual {
            art: V49_2_ART,
            spots: V49_2_SPOTS,
        }),
        (r#"INGOT"#, r#"tail cone off"#, r#"Most contaminated"#) => Some(Visual {
            art: V50_0_ART,
            spots: V50_0_SPOTS,
        }),
        (r#"INGOT"#, r#"tail cone off"#, r#"Slip dislocations"#) => Some(Visual {
            art: V50_1_ART,
            spots: V50_1_SPOTS,
        }),
        (r#"INGOT"#, r#"tail cone off"#, r#"Value hit"#) => Some(Visual {
            art: V50_2_ART,
            spots: V50_2_SPOTS,
        }),
        (r#"INGOT"#, r#"mounting beam"#, r#"Glue-on plate"#) => Some(Visual {
            art: V51_0_ART,
            spots: V51_0_SPOTS,
        }),
        (r#"INGOT"#, r#"mounting beam"#, r#"Thickness reference"#) => Some(Visual {
            art: V51_1_ART,
            spots: V51_1_SPOTS,
        }),
        (r#"INGOT"#, r#"mounting beam"#, r#"Alignment"#) => Some(Visual {
            art: V51_2_ART,
            spots: V51_2_SPOTS,
        }),
        (r#"INGOT"#, r#"Orientation"#, r#"Miller indices"#) => Some(Visual {
            art: V52_0_ART,
            spots: V52_0_SPOTS,
        }),
        (r#"INGOT"#, r#"Orientation"#, r#"Why {100}"#) => Some(Visual {
            art: V52_1_ART,
            spots: V52_1_SPOTS,
        }),
        (r#"INGOT"#, r#"Orientation"#, r#"Industry constant"#) => Some(Visual {
            art: V52_2_ART,
            spots: V52_2_SPOTS,
        }),
        (r#"INGOT"#, r#"Doping"#, r#"Dopants"#) => Some(Visual {
            art: V53_0_ART,
            spots: V53_0_SPOTS,
        }),
        (r#"INGOT"#, r#"Doping"#, r#"Segregation"#) => Some(Visual {
            art: V53_1_ART,
            spots: V53_1_SPOTS,
        }),
        (r#"INGOT"#, r#"Doping"#, r#"Purity and binning"#) => Some(Visual {
            art: V53_2_ART,
            spots: V53_2_SPOTS,
        }),
        (r#"INGOT"#, r#"775 um"#, r#"Size ladder"#) => Some(Visual {
            art: V54_0_ART,
            spots: V54_0_SPOTS,
        }),
        (r#"INGOT"#, r#"775 um"#, r#"Why thicker"#) => Some(Visual {
            art: V54_1_ART,
            spots: V54_1_SPOTS,
        }),
        (r#"INGOT"#, r#"775 um"#, r#"Why 450 mm died"#) => Some(Visual {
            art: V54_2_ART,
            spots: V54_2_SPOTS,
        }),
        (r#"INGOT"#, r#"Pricing"#, r#"Long-term agreements"#) => Some(Visual {
            art: V55_0_ART,
            spots: V55_0_SPOTS,
        }),
        (r#"INGOT"#, r#"Pricing"#, r#"Tightening since"#) => Some(Visual {
            art: V55_1_ART,
            spots: V55_1_SPOTS,
        }),
        (r#"INGOT"#, r#"Pricing"#, r#"Investor read"#) => Some(Visual {
            art: V55_2_ART,
            spots: V55_2_SPOTS,
        }),
        (r#"INGOT"#, r#"Five firms"#, r#"Share"#) => Some(Visual {
            art: V56_0_ART,
            spots: V56_0_SPOTS,
        }),
        (r#"INGOT"#, r#"Five firms"#, r#"Moat"#) => Some(Visual {
            art: V56_1_ART,
            spots: V56_1_SPOTS,
        }),
        (r#"INGOT"#, r#"Five firms"#, r#"Analyst moves"#) => Some(Visual {
            art: V56_2_ART,
            spots: V56_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Diamond wire"#) => Some(Visual {
            art: V57_0_ART,
            spots: V57_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Damage layer"#) => Some(Visual {
            art: V57_1_ART,
            spots: V57_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Kerf"#) => Some(Visual {
            art: V57_2_ART,
            spots: V57_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"GRIND/LAP"#, r#"Lap or grind"#) => Some(Visual {
            art: V58_0_ART,
            spots: V58_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"GRIND/LAP"#, r#"How much comes off"#) => Some(Visual {
            art: V58_1_ART,
            spots: V58_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"GRIND/LAP"#, r#"Purpose and failure"#) => Some(Visual {
            art: V58_2_ART,
            spots: V58_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"ETCH"#, r#"Etching the damage away"#) => Some(Visual {
            art: V59_0_ART,
            spots: V59_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"ETCH"#, r#"One patent sequence"#) => Some(Visual {
            art: V59_1_ART,
            spots: V59_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"ETCH"#, r#"Alkali vs acid"#) => Some(Visual {
            art: V59_2_ART,
            spots: V59_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"EDGE"#, r#"A rounded rim"#) => Some(Visual {
            art: V60_0_ART,
            spots: V60_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"EDGE"#, r#"Why it matters"#) => Some(Visual {
            art: V60_1_ART,
            spots: V60_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"EDGE"#, r#"Order of steps"#) => Some(Visual {
            art: V60_2_ART,
            spots: V60_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"POLISH"#, r#"DSP then final polish"#) => Some(Visual {
            art: V61_0_ART,
            spots: V61_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"POLISH"#, r#"Nanotopography"#) => Some(Visual {
            art: V61_1_ART,
            spots: V61_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"POLISH"#, r#"Result and control"#) => Some(Visual {
            art: V61_2_ART,
            spots: V61_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Clean and inspect"#) => Some(Visual {
            art: V62_0_ART,
            spots: V62_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Metrology example"#) => Some(Visual {
            art: V62_1_ART,
            spots: V62_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Qualification"#) => Some(Visual {
            art: V62_2_ART,
            spots: V62_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Web geometry"#) => Some(Visual {
            art: V63_0_ART,
            spots: V63_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Wear"#) => Some(Visual {
            art: V63_1_ART,
            spots: V63_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Fine wire limits"#) => Some(Visual {
            art: V63_2_ART,
            spots: V63_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"coolant spray"#, r#"Cooling and flushing"#) => Some(Visual {
            art: V64_0_ART,
            spots: V64_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"coolant spray"#, r#"Swarf"#) => Some(Visual {
            art: V64_1_ART,
            spots: V64_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"coolant spray"#, r#"Water not oil"#) => Some(Visual {
            art: V64_2_ART,
            spots: V64_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"kerf"#, r#"Kerf numbers"#) => Some(Visual {
            art: V65_0_ART,
            spots: V65_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"kerf"#, r#"What it costs"#) => Some(Visual {
            art: V65_1_ART,
            spots: V65_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"kerf"#, r#"Thickness budget"#) => Some(Visual {
            art: V65_2_ART,
            spots: V65_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SILICON INGOT"#, r#"Feed into the saw"#) => Some(Visual {
            art: V66_0_ART,
            spots: V66_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SILICON INGOT"#, r#"Wire drag"#) => Some(Visual {
            art: V66_1_ART,
            spots: V66_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"SILICON INGOT"#, r#"Highest-value failure"#) => Some(Visual {
            art: V66_2_ART,
            spots: V66_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"Preston"#, r#"Preston's law"#) => Some(Visual {
            art: V67_0_ART,
            spots: V67_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"Preston"#, r#"Slurry pH"#) => Some(Visual {
            art: V67_1_ART,
            spots: V67_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"Preston"#, r#"Used at both ends"#) => Some(Visual {
            art: V67_2_ART,
            spots: V67_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Two big suppliers"#) => Some(Visual {
            art: V68_0_ART,
            spots: V68_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Competition"#) => Some(Visual {
            art: V68_1_ART,
            spots: V68_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Scope note"#) => Some(Visual {
            art: V68_2_ART,
            spots: V68_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP slurry"#, r#"Slurry share"#) => Some(Visual {
            art: V69_0_ART,
            spots: V69_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP slurry"#, r#"Market structure"#) => Some(Visual {
            art: V69_1_ART,
            spots: V69_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP slurry"#, r#"Qualified per line"#) => Some(Visual {
            art: V69_2_ART,
            spots: V69_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"What pads do"#) => Some(Visual {
            art: V70_0_ART,
            spots: V70_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"Share"#) => Some(Visual {
            art: V70_1_ART,
            spots: V70_1_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"Wear"#) => Some(Visual {
            art: V70_2_ART,
            spots: V70_2_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"wire breakage and wear"#, r#"Wear raises kerf"#) => Some(Visual {
            art: V71_0_ART,
            spots: V71_0_SPOTS,
        }),
        (r#"SLICE + POLISH"#, r#"wire breakage and wear"#, r#"Thinner is weaker"#) => {
            Some(Visual {
                art: V71_1_ART,
                spots: V71_1_SPOTS,
            })
        }
        (r#"SLICE + POLISH"#, r#"wire breakage and wear"#, r#"Other chokepoints"#) => {
            Some(Visual {
                art: V71_2_ART,
                spots: V71_2_SPOTS,
            })
        }
        _ => None,
    }
}

const V0_0_ART: &str = r#"# Crush, screen, split

  quartzite ──▶ ┌─────────┐ ──▶ ┌─────────┐ ──▶ lumps ──▶ furnace
                │  CRUSH  │     │ SCREEN  │
                └─────────┘     └────┬────┘
                                     │ fines
                                     ▼
                              sold or briquetted
                              (not fed raw)

# What size does to the furnace

  too many fines  gas channels, charge sinters, SiO lost as fume
  right size      porous burden, gas rises evenly, charge sinks evenly
  too coarse      cool-zone reaction slow, carbon and quartz segregate
  (textbook furnace practice)
"#;
const V0_0_SPOTS: &[Spot] = &[
    spot(
        r#"CRUSH"#,
        0,
        0,
        r#"Crushing breaks quarry quartzite into lumps. The target is a controlled size range, not a fine powder."#,
    ),
    spot(
        r#"SCREEN"#,
        0,
        0,
        r#"Screens sort the crushed rock by size so only the right lumps reach the furnace charge."#,
    ),
    spot(
        r#"sold or briquetted"#,
        0,
        0,
        r#"Fines are usually sold or briquetted rather than fed, because they would choke the gas flow (textbook)."#,
    ),
    spot(
        r#"too many fines"#,
        0,
        TO_EOL,
        r#"Fines fill the gaps, gas channels, the charge sinters, and the furnace loses silicon as fume (textbook furnace practice)."#,
    ),
    spot(
        r#"right size"#,
        0,
        TO_EOL,
        r#"A porous, evenly sinking burden lets hot CO and SiO rise through it and gives steady reactions."#,
    ),
    spot(
        r#"too coarse"#,
        0,
        TO_EOL,
        r#"Coarse rock reacts slowly in the cooler zone, and carbon and quartz can segregate (textbook furnace practice)."#,
    ),
];

const V0_1_ART: &str = r#"# Impurities ride through

  clay, iron, aluminum in the rock
        │
        ▼
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │ ARC FURNACE  │ ──▶ │ MG-Si metal  │ ──▶ │ POLYSILICON  │
  │ (no cleanup) │     │ 98-99% pure  │     │ cleans 7+    │
  └──────────────┘     └──────────────┘     │ orders       │
                                            └──────────────┘
  (so the rock is pre-washed and sorted)
"#;
const V0_1_SPOTS: &[Spot] = &[
    spot(
        r#"clay, iron, aluminum"#,
        0,
        0,
        r#"These come with the rock and are not removed in the furnace, so they end up in the silicon metal."#,
    ),
    spot(
        r#"ARC FURNACE"#,
        0,
        0,
        r#"The furnace reduces SiO2 but does not purify the metal much. Whatever metals the charge brings in end up in it."#,
    ),
    spot(
        r#"MG-Si metal"#,
        0,
        0,
        r#"Metallurgical-grade silicon is 98-99% pure, roughly 10,000 ppm impurities."#,
    ),
    spot(
        r#"POLYSILICON"#,
        0,
        0,
        r#"The next stage removes the impurities, from about 10,000 ppm down toward 1 ppb for electronic grade."#,
    ),
    spot(
        r#"pre-washed and sorted"#,
        0,
        0,
        r#"Washing and sorting the quartz is the cheap place to stop clay, iron and aluminum."#,
    ),
];

const V0_2_ART: &str = r#"# Where the silicon charged ends up (DOE DC furnace study)

  to metal       ████████████████████████████████████████ about 80%
  lost to fume   ██████████ 19.5%

  (the fume is mostly unreacted SiO vapour that burns above the pile)
"#;
const V0_2_SPOTS: &[Spot] = &[
    spot(
        r#"to metal"#,
        0,
        TO_EOL,
        r#"Roughly the remainder of the silicon charged leaves as tapped metal. A metallurgical overview puts recovery at 80-90%."#,
    ),
    spot(
        r#"lost to fume"#,
        0,
        TO_EOL,
        r#"The DOE study of a DC furnace measured about 19.5% of silicon charged lost to fume."#,
    ),
    spot(
        r#"unreacted SiO vapour"#,
        0,
        0,
        r#"SiO is gaseous at reaction temperature. If it does not react with carbon higher in the burden it leaves the top and burns to silica fume."#,
    ),
];

const V1_0_ART: &str = r#"# Three ingredients, three jobs

  ┌───────────┐   ┌─────────────┐   ┌─────────────┐
  │ QUARTZITE │   │ COAL, COKE  │   │ WOOD CHIPS  │
  │ SiO2      │   │ fixed C     │   │ open burden │
  └─────┬─────┘   └──────┬──────┘   └──────┬──────┘
        └────────────────┼─────────────────┘
                         ▼
                 ┌────────────────┐
                 │  BLENDED       │
                 │  CHARGE        │
                 └────────────────┘
  (charcoal is sometimes used instead of coal or coke)
"#;
const V1_0_SPOTS: &[Spot] = &[
    spot(
        r#"QUARTZITE"#,
        0,
        0,
        r#"The silicon source: SiO2 rock, sized into lumps."#,
    ),
    spot(
        r#"COAL, COKE"#,
        0,
        0,
        r#"Coal and coke supply the fixed carbon that strips oxygen from SiO2 (textbook)."#,
    ),
    spot(
        r#"WOOD CHIPS"#,
        0,
        0,
        r#"Wood chips open the burden so gas can rise through it. They are volatile and low in ash, so they add little contamination (textbook)."#,
    ),
    spot(
        r#"BLENDED"#,
        0,
        0,
        r#"The blend goes into the top of the furnace and sinks slowly through it."#,
    ),
    spot(
        r#"charcoal"#,
        0,
        0,
        r#"Charcoal is sometimes used where cost and purity targets call for it."#,
    ),
];

const V1_1_ART: &str = r#"# Ash in the carbon goes into the metal

  carbon ash:  Al   Fe   Ca   B   P
                │    │    │   │   │
                └────┴────┴───┴───┘
                         ▼
               ┌───────────────────┐
               │ molten silicon    │
               └─────────┬─────────┘
                         ▼
        B and P are the hard ones to remove later
        (dopants: polysilicon must get them to ppb)
"#;
const V1_1_SPOTS: &[Spot] = &[
    spot(
        r#"Al   Fe   Ca"#,
        0,
        0,
        r#"Aluminum, iron and calcium in the ash end up in the silicon. Some can be removed in ladle refining or leave in slag."#,
    ),
    spot(
        r#"B   P"#,
        0,
        0,
        r#"Boron (acceptor) and phosphorus (donor) are dopants. Their chlorides boil near trichlorosilane, which makes them hard to distill out later."#,
    ),
    spot(
        r#"molten silicon"#,
        0,
        0,
        r#"The pool collects everything the charge delivers. It is the only place metal purity is set."#,
    ),
    spot(
        r#"polysilicon must get them to ppb"#,
        0,
        0,
        r#"Electronic-grade donor limits are in atoms per cm3. The POLYSILICON stage does the cleaning, not the furnace."#,
    ),
];

const V1_2_ART: &str = r#"# Carbon dial

   too little C        about right         too much C
  ──────────────────────────────────────────────────────
  SiO escapes up      SiO2 + 2C ──▶       SiC builds up
  the stack           Si + 2CO            on the hearth

  overall: 2 C per Si (textbook)
  tapping gets hard when SiC piles up
"#;
const V1_2_SPOTS: &[Spot] = &[
    spot(
        r#"too little C"#,
        0,
        0,
        r#"With too little carbon, SiO gas is not recaptured and leaves the furnace as fume, so silicon yield drops (textbook)."#,
    ),
    spot(
        r#"about right"#,
        0,
        0,
        r#"At the balanced ratio the overall reaction runs: SiO2 + 2C gives Si + 2CO."#,
    ),
    spot(
        r#"too much C"#,
        0,
        0,
        r#"Excess carbon forms silicon carbide at the bottom of the furnace, which makes tapping hard (textbook)."#,
    ),
    spot(
        r#"2 C per Si"#,
        0,
        0,
        r#"The overall reaction consumes about two carbon atoms per silicon atom, ignoring losses (textbook)."#,
    ),
];

const V2_0_ART: &str = r#"# Cross-section

        E1       E2       E3     (three electrodes, 3-phase AC)
        ║        ║        ║
  ┌─────╨────────╨────────╨─────┐
  │ charge: quartzite + carbon  │
  │ ≈≈ arc cavities > 1800 C ≈≈ │
  │ ▓▓▓ molten silicon pool ▓▓▓ │
  └──────────────┬──────────────┘
                 ▼ tap hole
  (steel shell, carbon-lined; the burden is the resistor)
"#;
const V2_0_SPOTS: &[Spot] = &[
    spot(
        r#"E2"#,
        0,
        0,
        r#"Each electrode carries one phase of the three-phase AC supply. They are buried in the charge, not held in open air."#,
    ),
    spot(
        r#"charge: quartzite + carbon"#,
        0,
        0,
        r#"The burden acts as the resistor. Heat is released deep inside the pile where the arcs burn."#,
    ),
    spot(
        r#"arc cavities > 1800 C"#,
        0,
        0,
        r#"Each electrode tip sits in a gas-filled cavity where the arc burns above 1800 C (page figure)."#,
    ),
    spot(
        r#"molten silicon pool"#,
        0,
        0,
        r#"Liquid silicon collects at the bottom and is tapped out periodically."#,
    ),
    spot(
        r#"tap hole"#,
        0,
        0,
        r#"Metal leaves through a refractory-lined hole near the bottom."#,
    ),
];

const V2_1_ART: &str = r#"# Energy per tonne of silicon

  theoretical  ██████████ about 1x
  commercial   ██████████████████████████████ about 3x (DOE-linked)

  actual draw  11 to 13 MWh per tonne Si   (patent example: 11.2)
  electrodes   0.144 lb per lb Si          (much burns above the pile)
"#;
const V2_1_SPOTS: &[Spot] = &[
    spot(
        r#"theoretical"#,
        0,
        TO_EOL,
        r#"The minimum energy the reaction needs, used as the 1x reference."#,
    ),
    spot(
        r#"commercial"#,
        0,
        TO_EOL,
        r#"A DOE-linked study of a DC furnace reported commercial units using roughly three times the theoretical energy."#,
    ),
    spot(
        r#"11 to 13 MWh per tonne Si"#,
        0,
        TO_EOL,
        r#"The page's electricity range. One patent example is 11.2 MWh per tonne."#,
    ),
    spot(
        r#"0.144 lb per lb Si"#,
        0,
        TO_EOL,
        r#"DOE study figure for electrode consumption in a DC furnace. Much is burned off above the burden pile."#,
    ),
];

const V2_2_ART: &str = r#"# Why the plants sit where they do

  power off ──▶ charge freezes ──▶ costly restart
                    │
                    ▼
  so: long power contracts + cheap hydro

  Norway   Iceland   Brazil   Canada   (hydro-heavy smelter regions)

  Ferroglobe Q2 2026: $59.9M fair-value gain on energy contracts
"#;
const V2_2_SPOTS: &[Spot] = &[
    spot(
        r#"charge freezes"#,
        0,
        0,
        r#"If power stops, the charge solidifies in the furnace and restarting is costly (textbook)."#,
    ),
    spot(
        r#"long power contracts"#,
        0,
        0,
        r#"Power is the largest cost line, so smelters lock in electricity under long-term contracts."#,
    ),
    spot(
        r#"Norway   Iceland   Brazil   Canada"#,
        0,
        0,
        r#"Smelters cluster by cheap hydro power in these regions."#,
    ),
    spot(
        r#"$59.9M fair-value gain"#,
        0,
        0,
        r#"Ferroglobe's Q2 2026 6-K booked a $59.9 million fair-value gain on long-term energy contracts."#,
    ),
];

const V3_0_ART: &str = r#"# Tap to casting bed

  ┌──────────┐    ┌───────────┐    ┌────────────┐    ┌──────────┐
  │ TAP HOLE │──▶ │ LAUNDER   │──▶ │ LADLE      │──▶ │ CASTING  │
  │ opened   │    │ channel   │    │ O2 or slag │    │ BED      │
  └──────────┘    └───────────┘    │ additions  │    └──────────┘
                                   └────────────┘
  (refining removes calcium and aluminum before casting)
"#;
const V3_0_SPOTS: &[Spot] = &[
    spot(
        r#"TAP HOLE"#,
        0,
        0,
        r#"Opened periodically by burning or drilling so liquid silicon flows out."#,
    ),
    spot(
        r#"LAUNDER"#,
        0,
        0,
        r#"A refractory-lined channel carries the metal to the ladle (textbook)."#,
    ),
    spot(
        r#"LADLE"#,
        0,
        0,
        r#"Oxygen or slag-forming additions can be used here to refine the metal (textbook; refining is standard practice but no source was fetched)."#,
    ),
    spot(
        r#"CASTING"#,
        0,
        0,
        r#"Refined silicon is cast into beds or ingots, then crushed in the next step."#,
    ),
    spot(
        r#"calcium and aluminum"#,
        0,
        0,
        r#"These are the main metals the ladle treatment targets (textbook)."#,
    ),
];

const V3_1_ART: &str = r#"# Where the fume goes

  tapping ──▶ SiO-rich gas ──▶ burns in air ──▶ fine SiO2 particles
                                     │
                                     ▼
                    ┌───────────────────────────┐
                    │ hood over the tap floor   │
                    └─────────────┬─────────────┘
                                  ▼
                           bag-house filter
  (Thamshavn, Norway: tapping gas, dust and NOx measured)
"#;
const V3_1_SPOTS: &[Spot] = &[
    spot(
        r#"SiO-rich gas"#,
        0,
        0,
        r#"SiO escapes with the CO during tapping."#,
    ),
    spot(
        r#"fine SiO2 particles"#,
        0,
        0,
        r#"SiO burns in air to very fine silica, which is fugitive dust if not captured."#,
    ),
    spot(
        r#"hood over the tap floor"#,
        0,
        0,
        r#"Hoods over the tap floor are linked to a bag-house system, as over the furnace top."#,
    ),
    spot(
        r#"bag-house filter"#,
        0,
        0,
        r#"Bag-house filters trap the fume. It can be sold as microsilica."#,
    ),
    spot(
        r#"Thamshavn"#,
        0,
        0,
        r#"Elkem's Thamshavn plant in Norway hosted a measurement campaign on tapping-gas composition, dust and NOx (Springer paper)."#,
    ),
];

const V3_2_ART: &str = r#"# Silicon charged, split three ways

  tapped metal   ██████████████████████████████████ 80-90%
  fume           ██████ the rest (10-20%)
                   │
                   ▼
            sold as microsilica (concrete)
            = by-product credit
"#;
const V3_2_SPOTS: &[Spot] = &[
    spot(
        r#"tapped metal"#,
        0,
        TO_EOL,
        r#"A metallurgical overview puts silicon recovery at 80-90% of the silicon charged."#,
    ),
    spot(
        r#"fume"#,
        0,
        TO_EOL,
        r#"The rest leaves as fume, mostly SiO that oxidises to silica."#,
    ),
    spot(
        r#"microsilica"#,
        0,
        0,
        r#"Silica fume is sold as microsilica for concrete, which offsets some of the silicon lost."#,
    ),
];

const V4_0_ART: &str = r#"# From ladle to lumps

  ┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌──────────────┐
  │ LADLE   │──▶│ CAST    │──▶│ CRUSH +     │──▶│ LUMPS AND    │
  │ molten  │   │ bed or  │   │ SCREEN      │   │ POWDER       │
  │ Si      │   │ ingot   │   │             │   │ 98-99% (2N)  │
  └─────────┘   └─────────┘   └─────────────┘   └──────────────┘

  about 10,000 ppm impurities
"#;
const V4_0_SPOTS: &[Spot] = &[
    spot(
        r#"CAST"#,
        0,
        0,
        r#"Silicon is poured into beds or ingots and left to cool."#,
    ),
    spot(
        r#"CRUSH +"#,
        0,
        0,
        r#"Cooled metal is crushed and screened into the sizes customers buy."#,
    ),
    spot(
        r#"LUMPS AND"#,
        0,
        0,
        r#"Both lumps and powder are sold, depending on the customer's process."#,
    ),
    spot(
        r#"98-99% (2N)"#,
        0,
        0,
        r#"About 2N purity. The next stage, POLYSILICON, does the rest of the cleaning."#,
    ),
    spot(
        r#"10,000 ppm"#,
        0,
        0,
        r#"Roughly 10,000 ppm impurities, per the page."#,
    ),
];

const V4_1_ART: &str = r#"# Uses of silicon metal (shares not sourced)

              ┌──▶ aluminum alloys
  MG-Si ──────┼──▶ silicones
              └──▶ polysilicon ──▶ solar, chips   (minority)

  fine powder is useful for the TCS reactor:
  more surface area in the fluidised bed (textbook)
"#;
const V4_1_SPOTS: &[Spot] = &[
    spot(
        r#"aluminum alloys"#,
        0,
        0,
        r#"A large share of silicon metal goes into aluminum alloying (textbook; no share figure fetched)."#,
    ),
    spot(
        r#"silicones"#,
        0,
        0,
        r#"Silicones are another large use of silicon metal (textbook; no share figure fetched)."#,
    ),
    spot(
        r#"polysilicon"#,
        0,
        0,
        r#"Only a minority of silicon metal reaches polysilicon, the feed for solar cells and chips (textbook)."#,
    ),
    spot(
        r#"fine powder"#,
        0,
        0,
        r#"In the TCS reactor, small particles give surface area for the fluidised bed (textbook)."#,
    ),
];

const V4_2_ART: &str = r#"# Ferroglobe silicon metal, Q2 2026

  avg price      $2,592 per tonne      down 5.9% on the quarter
  shipments      40,818 tonnes
  revenue        $105.8 million        up 25.8% on Q1
  seg. EBITDA    about -$2.7 million   (adjusted, still a loss)

  pressure: Chinese and Angolan imports in Europe
"#;
const V4_2_SPOTS: &[Spot] = &[
    spot(
        r#"avg price"#,
        0,
        TO_EOL,
        r#"Average silicon metal selling price: $2,592 per tonne, down 5.9% on the quarter."#,
    ),
    spot(
        r#"shipments"#,
        0,
        TO_EOL,
        r#"About 40,818 tonnes shipped in the quarter."#,
    ),
    spot(
        r#"revenue"#,
        0,
        TO_EOL,
        r#"Silicon metal revenue of $105.8 million, up 25.8% from Q1."#,
    ),
    spot(
        r#"seg. EBITDA"#,
        0,
        TO_EOL,
        r#"The segment still lost about $2.7 million at adjusted EBITDA."#,
    ),
    spot(
        r#"Chinese and Angolan imports"#,
        0,
        0,
        r#"Management cited imports from China and Angola pressing European prices."#,
    ),
];

const V5_0_ART: &str = r#"# Two electrode types (textbook)

  baked graphite              self-baking (Soderberg)
  ┌──────┐                    paste ──▶ ┌──────┐
  │ pre- │                              │ soft │ top
  │ baked│                              ├──────┤
  │ rod  │                              │ baked│ in the heat
  └──┬───┘                              └──┬───┘
     ▼                                     ▼
  consumed slowly in the charge     paste fed from above
"#;
const V5_0_SPOTS: &[Spot] = &[
    spot(
        r#"baked graphite"#,
        0,
        0,
        r#"Pre-baked graphite electrodes are added in sections and consumed slowly (textbook)."#,
    ),
    spot(
        r#"self-baking (Soderberg)"#,
        0,
        0,
        r#"The paste is fed from above and bakes hard in the heat of the furnace (textbook; the type used varies by plant)."#,
    ),
    spot(
        r#"consumed slowly in the charge"#,
        0,
        0,
        r#"Electrodes carry tens of kiloamperes into the charge and are worn away slowly."#,
    ),
];

const V5_1_ART: &str = r#"# Top view

           E1
          /  \
         /    \          one electrode per phase
       E2 ──── E3        each makes its own arc cavity

  depth too high: heat wasted up the stack
  depth too deep: cavity shifts, tapping goes cold
  (textbook)
"#;
const V5_1_SPOTS: &[Spot] = &[
    spot(
        r#"E1"#,
        0,
        0,
        r#"Each electrode takes one phase of the three-phase AC supply."#,
    ),
    spot(
        r#"one electrode per phase"#,
        0,
        0,
        r#"Current flows from each electrode through the charge and returns through the molten pool."#,
    ),
    spot(
        r#"depth too high"#,
        0,
        TO_EOL,
        r#"If electrodes sit too high, heat is wasted up the stack (textbook)."#,
    ),
    spot(
        r#"depth too deep"#,
        0,
        TO_EOL,
        r#"If electrodes sit too deep, the arc cavity shifts and tapping goes cold (textbook)."#,
    ),
];

const V5_2_ART: &str = r#"# Where the electrode goes

  0.144 lb per lb of silicon (DOE, DC furnace)

  above the pile   ████████████████ burns off (oxidises)
  in the charge    ██████ consumed in the reaction zone

  ash in the carbon ──▶ ends up in the metal
  (split shown is illustrative; the DOE study says "much" burns above)
"#;
const V5_2_SPOTS: &[Spot] = &[
    spot(
        r#"0.144 lb per lb"#,
        0,
        0,
        r#"DOE study figure for a DC furnace."#,
    ),
    spot(
        r#"above the pile"#,
        0,
        TO_EOL,
        r#"The study noted much of the electrode is consumed above the burden pile, where it oxidises."#,
    ),
    spot(
        r#"ash in the carbon"#,
        0,
        0,
        r#"Electrode ash is a contamination source. Smelters balance electrode cost against metal purity."#,
    ),
];

const V6_0_ART: &str = r#"# Three jobs of the burden

  fresh charge in ──▶  ┌────────────────────────┐
                       │ upper zone: cooler     │ ▲ gas up
                       │ SiO + C ──▶ SiC (traps │ │
                       │ some SiO)              │ │
                       │ lower zone: hot, arcs  │ │
                       └────────────────────────┘
  1 resistor   2 reactant bed   3 filter
"#;
const V6_0_SPOTS: &[Spot] = &[
    spot(
        r#"fresh charge in"#,
        0,
        0,
        r#"New quartzite and carbon are fed on top as the lower layers are consumed."#,
    ),
    spot(
        r#"upper zone"#,
        0,
        0,
        r#"In the cooler upper zone SiO reacts with carbon to form SiC and captures part of the SiO (page: SiO2 + 3C giving SiC + 2CO)."#,
    ),
    spot(
        r#"lower zone"#,
        0,
        0,
        r#"The hot lower zone holds the arc cavities and the molten pool."#,
    ),
    spot(
        r#"1 resistor"#,
        0,
        0,
        r#"The burden's electrical resistance is what turns current into heat."#,
    ),
    spot(
        r#"3 filter"#,
        0,
        0,
        r#"The burden filters the rising gas, recapturing SiO before it escapes."#,
    ),
];

const V6_1_ART: &str = r#"# Healthy vs blocked burden

  porous, even sink          crusted, sintered
  ┌────────────┐             ┌────────────┐
  │ ▓ ▓ ▓ ▓ ▓ │ gas ▲▲▲    │ ▓▓▓▓▓▓▓▓▓ │ gas blocked
  │ ▓ ▓ ▓ ▓ ▓ │             │ ▓▓▓▓▓▓▓▓▓ │
  └────────────┘             └────────────┘
  steady output              pressure ──▶ eruption
                             (gas and SiO burst through)
"#;
const V6_1_SPOTS: &[Spot] = &[
    spot(
        r#"porous, even sink"#,
        0,
        0,
        r#"A porous burden lets gas through evenly while the charge sinks smoothly."#,
    ),
    spot(
        r#"crusted, sintered"#,
        0,
        0,
        r#"When the charge crusts or sinters, gas cannot get through."#,
    ),
    spot(
        r#"gas blocked"#,
        0,
        0,
        r#"Blocked gas builds pressure below the crust."#,
    ),
    spot(
        r#"eruption"#,
        0,
        0,
        r#"Gas and SiO burst up through the surface, an eruption (textbook). It wastes silicon as fume."#,
    ),
];

const V6_2_ART: &str = r#"# Control levers

  burden control ──▶ steady gas flow ──▶ less SiO lost
       │
       ▼
  DOE DC furnace case: 19.5% of Si charged lost to fume

  trend (page): bigger furnaces + better control
  push MWh per tonne down
"#;
const V6_2_SPOTS: &[Spot] = &[
    spot(
        r#"burden control"#,
        0,
        0,
        r#"Part skill, part automation: keeping the burden porous and evenly sinking."#,
    ),
    spot(
        r#"less SiO lost"#,
        0,
        0,
        r#"More SiO recaptured as SiC higher in the burden means more silicon reaches the pool."#,
    ),
    spot(
        r#"19.5%"#,
        0,
        0,
        r#"DOE study of a DC furnace: about 19.5% of silicon charged lost to fume."#,
    ),
    spot(
        r#"MWh per tonne down"#,
        0,
        0,
        r#"Bigger furnaces and better control keep pushing energy per tonne down (page)."#,
    ),
];

const V7_0_ART: &str = r#"# One cavity, bottom up

  upper, cooler:  SiO + 2C ──▶ SiC + CO   (recaptures SiO)
                          ▲ SiO gas rises
        ≈≈≈≈≈≈≈≈ ARC CAVITY, above 1800 C ≈≈≈≈≈≈≈≈
        SiO2 + C ──▶ SiO(gas) + CO
        SiC + SiO ──▶ 2Si + CO
                          │
                          ▼
              ▓▓▓ liquid silicon pool ▓▓▓
"#;
const V7_0_SPOTS: &[Spot] = &[
    spot(
        r#"SiO + 2C ──▶ SiC + CO"#,
        0,
        0,
        r#"In the cooler upper charge, rising SiO reacts with carbon to make SiC, recapturing silicon (textbook)."#,
    ),
    spot(
        r#"ARC CAVITY, above 1800 C"#,
        0,
        0,
        r#"Each electrode tip burns in a gas-filled cavity above 1800 C (page figure)."#,
    ),
    spot(
        r#"SiO2 + C ──▶ SiO(gas) + CO"#,
        0,
        0,
        r#"The hot-zone step: quartz and carbon make SiO gas and CO."#,
    ),
    spot(
        r#"SiC + SiO ──▶ 2Si + CO"#,
        0,
        0,
        r#"The closing step (textbook): silicon carbide and SiO give liquid silicon."#,
    ),
    spot(
        r#"liquid silicon pool"#,
        0,
        0,
        r#"Liquid silicon collects at the bottom and is tapped."#,
    ),
];

const V7_1_ART: &str = r#"# SiO that is not recaptured

  cavity ──▶ SiO gas ──▶ rises ──▶ recaptured as SiC ──▶ more Si
                           │
                           ▼ escapes the top
                   meets air, burns
                           │
                           ▼
        silica fume: spherical SiO2, average about 150 nm
        caught in bag-house filters
"#;
const V7_1_SPOTS: &[Spot] = &[
    spot(
        r#"recaptured as SiC"#,
        0,
        0,
        r#"SiO that reacts with carbon in the upper burden stays in the furnace and is recovered as silicon."#,
    ),
    spot(
        r#"escapes the top"#,
        0,
        0,
        r#"Unreacted SiO vapour leaves with the CO."#,
    ),
    spot(
        r#"meets air, burns"#,
        0,
        0,
        r#"SiO oxidises to silica as it meets air above the pile."#,
    ),
    spot(
        r#"about 150 nm"#,
        0,
        0,
        r#"Silica fume consists of spherical particles with an average diameter of about 150 nm (Wikipedia)."#,
    ),
    spot(
        r#"bag-house filters"#,
        0,
        0,
        r#"Large filters beside the furnaces trap the fume."#,
    ),
];

const V8_0_ART: &str = r#"# Hearth cross-section

      arc cavities (hot, above 1800 C)
   ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈
   ▓▓▓▓▓▓▓▓▓ liquid silicon pool ▓▓▓▓▓▓▓▓▓   Si melts at 1414 C
   ░░░░░░░░░░░░░ SiC buildup? ░░░░░░░░░░░░░░   (textbook)
   ──────────────────────────────────────── carbon hearth
                                      ▼ tap
"#;
const V8_0_SPOTS: &[Spot] = &[
    spot(
        r#"arc cavities"#,
        0,
        0,
        r#"The arcs superheat the zone above the pool, so the pool is hotter than the 1414 C melting point."#,
    ),
    spot(
        r#"liquid silicon pool"#,
        0,
        0,
        r#"Liquid silicon collects here as SiC and SiO react. Depth and condition set how steady tapping is."#,
    ),
    spot(r#"1414 C"#, 0, 0, r#"Silicon's melting point (textbook)."#),
    spot(
        r#"SiC buildup"#,
        0,
        0,
        r#"Too much silicon carbide on the hearth shrinks the effective pool and forces operators to change the carbon ratio (textbook)."#,
    ),
    spot(
        r#"carbon hearth"#,
        0,
        0,
        r#"The furnace floor is carbon refractory."#,
    ),
];

const V8_1_ART: &str = r#"# What goes in is what you get

  charge delivers: Al  Fe  Ca  B  P
        │
        ▼
  ┌───────────────────────┐ ──▶ slag (some leaves here)
  │ pool: 98-99% Si       │
  │ ~10,000 ppm impurity  │ ──▶ ladle refining (some)
  └───────────────────────┘
        │
        ▼ next: POLYSILICON (chlorides, distillation)
"#;
const V8_1_SPOTS: &[Spot] = &[
    spot(
        r#"Al  Fe  Ca  B  P"#,
        0,
        0,
        r#"These elements arrive with quartz, carbon and electrodes. The pool is where they are locked into the metal."#,
    ),
    spot(
        r#"98-99% Si"#,
        0,
        0,
        r#"Metallurgical-grade silicon, about 2N."#,
    ),
    spot(
        r#"slag"#,
        0,
        0,
        r#"Some impurities leave in slag (textbook)."#,
    ),
    spot(
        r#"ladle refining"#,
        0,
        0,
        r#"Calcium and aluminum can be reduced in the ladle (textbook)."#,
    ),
    spot(
        r#"POLYSILICON"#,
        0,
        0,
        r#"The next node converts the metal to chlorosilanes and distills them. Distillation separates by boiling point and can cut boron and phosphorus chlorides to ppb levels."#,
    ),
];

const V9_0_ART: &str = r#"# One tap cycle (textbook)

  plug (clay)
     │ opened: oxygen lance or drill
     ▼
  metal flows ──▶ launder ──▶ ladle ──▶ casting bed
     │
     ▼ closed: mud gun re-plugs the hole
"#;
const V9_0_SPOTS: &[Spot] = &[
    spot(
        r#"plug (clay)"#,
        0,
        0,
        r#"The hole is plugged with clay between taps (textbook)."#,
    ),
    spot(
        r#"oxygen lance or drill"#,
        0,
        0,
        r#"Opening is by oxygen lancing or drilling (textbook)."#,
    ),
    spot(
        r#"launder"#,
        0,
        0,
        r#"A channel carrying metal from the hole to the ladle."#,
    ),
    spot(
        r#"mud gun"#,
        0,
        0,
        r#"A mud gun pushes clay back in to close the hole (textbook)."#,
    ),
];

const V9_1_ART: &str = r#"# Tap floor capture

   tap ──▶ SiO gas + dust ──▶ ┌─────────┐ ──▶ ┌────────────┐
                              │  HOOD   │     │ BAG-HOUSE  │
                              └─────────┘     └────────────┘
   uncaptured: fugitive SiO2 dust, NOx

   measured at Thamshavn (Elkem, Norway):
   gas composition, dust, NOx
"#;
const V9_1_SPOTS: &[Spot] = &[
    spot(
        r#"SiO gas + dust"#,
        0,
        0,
        r#"SiO in the tapping gas burns to fine SiO2 particles."#,
    ),
    spot(
        r#"HOOD"#,
        0,
        0,
        r#"A hood over the tap floor captures the gas."#,
    ),
    spot(
        r#"BAG-HOUSE"#,
        0,
        0,
        r#"Hoods connect to the same bag-house system as the main stack."#,
    ),
    spot(
        r#"fugitive SiO2 dust"#,
        0,
        0,
        r#"What escapes capture is fugitive emissions and poor working conditions (Springer paper)."#,
    ),
    spot(
        r#"Thamshavn"#,
        0,
        0,
        r#"A measurement campaign at Elkem's Thamshavn plant covered tapping gas composition, dust and NOx."#,
    ),
];

const V9_2_ART: &str = r#"# What wears out

  clay plug      replaced every tap
  hole lining    erodes with each tap     ──▶ limits campaign life
  mud gun        consumable seals

  (textbook: tap hole wear usually sets how long a furnace
   can run before a rebuild)
"#;
const V9_2_SPOTS: &[Spot] = &[
    spot(
        r#"clay plug"#,
        0,
        TO_EOL,
        r#"Clay plugs are used up each tap."#,
    ),
    spot(
        r#"hole lining"#,
        0,
        TO_EOL,
        r#"Refractory at the hole erodes with every tap and is the usual limit on furnace campaign life (textbook)."#,
    ),
    spot(
        r#"mud gun"#,
        0,
        TO_EOL,
        r#"The gun and its seals are maintenance items (textbook)."#,
    ),
];

const V10_0_ART: &str = r#"# Off-gas path

  furnace top ──▶ CO + SiO
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  CO burns              SiO meets air
  heat recovery         ──▶ silica fume
  (some plants:         ──▶ bag-house
   electricity)
"#;
const V10_0_SPOTS: &[Spot] = &[
    spot(
        r#"CO + SiO"#,
        0,
        0,
        r#"The gas leaving the top is mostly CO plus SiO."#,
    ),
    spot(
        r#"CO burns"#,
        0,
        0,
        r#"CO is combustible. Many plants burn it for heat."#,
    ),
    spot(
        r#"heat recovery"#,
        0,
        0,
        r#"Some plants use waste-heat boilers to generate electricity (textbook). A Chinese patent abstract describes afterheat recovery and fume purification for silicon ore furnaces."#,
    ),
    spot(
        r#"silica fume"#,
        0,
        0,
        r#"SiO oxidises to amorphous silica, particles well under a micron."#,
    ),
    spot(
        r#"bag-house"#,
        0,
        0,
        r#"Large filters beside the furnaces trap the fume."#,
    ),
];

const V10_1_ART: &str = r#"# Size of silica fume particles

  upper bound   ████████████████████████████████████████ below 1,000 nm
  average       ██████ about 150 nm

  sold as microsilica: concrete, refractories
"#;
const V10_1_SPOTS: &[Spot] = &[
    spot(
        r#"upper bound"#,
        0,
        TO_EOL,
        r#"Silica fume particles are below 1 micron (1,000 nm), per the metallurgical overview."#,
    ),
    spot(
        r#"average"#,
        0,
        TO_EOL,
        r#"Average diameter about 150 nm (Wikipedia)."#,
    ),
    spot(
        r#"microsilica"#,
        0,
        0,
        r#"Sold for concrete and refractories (textbook), a credit against the silicon lost."#,
    ),
];

const V10_2_ART: &str = r#"# What a point of recapture is worth

  silicon lost to fume   19.5% of charge (DOE DC case)
  price 2025e            130 cents per lb (page, USGS)
  price 2022 peak        362 cents per lb

  recapture 1 point ──▶ about 1% more silicon per tonne charged
"#;
const V10_2_SPOTS: &[Spot] = &[
    spot(r#"19.5% of charge"#, 0, 0, r#"DOE study of a DC furnace."#),
    spot(
        r#"130 cents per lb"#,
        0,
        0,
        r#"USGS / S&P Platts price for US silicon metal in 2025e, per the page."#,
    ),
    spot(
        r#"362 cents per lb"#,
        0,
        0,
        r#"The 2022 price peak per the page."#,
    ),
    spot(
        r#"1% more silicon"#,
        0,
        0,
        r#"Illustrative arithmetic: one point less lost to fume is one point more silicon from the same charge."#,
    ),
];

const V11_0_ART: &str = r#"# What $10/MWh does to a tonne

  power use      12 MWh per tonne Si  (page: 11 to 13)
  +$10/MWh       +$120 per tonne      (12 x 10)
  price          $2,592 per tonne     (Ferroglobe Q2 2026)
  share          about 4.6% of price per +$10/MWh
"#;
const V11_0_SPOTS: &[Spot] = &[
    spot(
        r#"power use"#,
        0,
        TO_EOL,
        r#"The page's range is 11 to 13 MWh per tonne of silicon. A single large furnace draws tens of megawatts."#,
    ),
    spot(
        r#"+$10/MWh"#,
        0,
        TO_EOL,
        r#"Simple arithmetic: 12 MWh/t times $10/MWh is $120 per tonne."#,
    ),
    spot(
        r#"price"#,
        0,
        TO_EOL,
        r#"Ferroglobe's Q2 2026 average silicon metal selling price."#,
    ),
    spot(r#"share"#, 0, TO_EOL, r#"120 / 2,592 is about 4.6%."#),
];

const V11_1_ART: &str = r#"# Ferroglobe Q2 2026

  net profit        $60.4M
  of which          $59.9M fair-value gain on energy contracts
  silicon metal     still lost money (adj. EBITDA about -$2.7M)

  patent example: 11.2 MWh/t
  commercial: about 3x theoretical energy
"#;
const V11_1_SPOTS: &[Spot] = &[
    spot(
        r#"net profit"#,
        0,
        TO_EOL,
        r#"Ferroglobe's Q2 2026 net profit was $60.4 million."#,
    ),
    spot(
        r#"fair-value gain"#,
        0,
        TO_EOL,
        r#"A $59.9 million fair-value gain on long-term energy contracts drove the profit."#,
    ),
    spot(
        r#"still lost money"#,
        0,
        TO_EOL,
        r#"The silicon metal segment's adjusted EBITDA was about -$2.7 million."#,
    ),
    spot(
        r#"11.2 MWh/t"#,
        0,
        0,
        r#"The cited patent's example figure."#,
    ),
    spot(
        r#"about 3x theoretical"#,
        0,
        0,
        r#"Commercial units use roughly three times the reaction's theoretical energy (DOE-linked study)."#,
    ),
];

const V11_2_ART: &str = r#"# What sets the price of the feedstock

  chip demand  ·········▶  small effect on MG-Si price
  power cost   ━━━━━━━━━▶  large effect
  trade policy ━━━━━━━━━▶  large effect

  (qualitative, from the page's reading of Ferroglobe's results)
"#;
const V11_2_SPOTS: &[Spot] = &[
    spot(
        r#"chip demand"#,
        0,
        0,
        r#"Silicon metal goes mostly to aluminum and silicones, so chip demand barely moves its price."#,
    ),
    spot(
        r#"power cost"#,
        0,
        0,
        r#"Electricity is the largest cost line in silicon metal."#,
    ),
    spot(
        r#"trade policy"#,
        0,
        0,
        r#"Ferroglobe points to import pressure and pending European Commission trade action."#,
    ),
];

const V12_0_ART: &str = r#"# Silicon metal output 2025e, kt Si (USGS)

  China        ██████████████████████████████████████████████ 4,000
  Brazil       ██ 180
  Norway       █ 130
  France       █ 68
  Australia    ▌ 47
  Russia       ▌ 35
  Canada       ▌ 34
  Other        ▌ 85      (Iceland 16, Germany 13, S. Africa 10, rest 46)
  World        4,600     (rounded) China about 87%
"#;
const V12_0_SPOTS: &[Spot] = &[
    spot(
        r#"China"#,
        0,
        TO_EOL,
        r#"China produced about 4.0 million tonnes, roughly 87% of the world total (USGS 2025e)."#,
    ),
    spot(
        r#"Brazil"#,
        0,
        TO_EOL,
        r#"Brazil: about 180 thousand tonnes."#,
    ),
    spot(
        r#"Norway"#,
        0,
        TO_EOL,
        r#"Norway: about 130 thousand tonnes."#,
    ),
    spot(
        r#"Other"#,
        0,
        TO_EOL,
        r#"Iceland 16, Germany 13, South Africa 10 and 46 from others (page); rounding leaves the total at 4,600."#,
    ),
    spot(
        r#"World"#,
        0,
        TO_EOL,
        r#"World total about 4.6 million tonnes, including ferrosilicon."#,
    ),
];

const V12_1_ART: &str = r#"# Policy and trade (2024 to 2026)

  US imports      117 kt (2024) ──▶ 180 kt (2025e)
  US policy       silicon on critical minerals list, Nov 2025
  Europe          imports from China and Angola press prices
                  EC trade action pending (Ferroglobe, Q2 2026)
  China           cheap coal power; some hydro in wet season
"#;
const V12_1_SPOTS: &[Spot] = &[
    spot(
        r#"US imports"#,
        0,
        TO_EOL,
        r#"USGS: US imports rose from 117 kt in 2024 to 180 kt in 2025e."#,
    ),
    spot(
        r#"US policy"#,
        0,
        TO_EOL,
        r#"Silicon was added to the US critical minerals list in November 2025 (USGS, per the page)."#,
    ),
    spot(
        r#"Europe"#,
        0,
        0,
        r#"Ferroglobe's Q2 2026 report cites Chinese and Angolan imports and pending European Commission trade action."#,
    ),
    spot(
        r#"China"#,
        0,
        0,
        r#"Cheap coal power and, in some provinces, wet-season hydro (textbook; seasonal pattern not sourced)."#,
    ),
];

const V12_2_ART: &str = r#"# US silicon metal, cents per lb (USGS / S&P Platts)

  2021   ████████████████████████████ 220
  2022   █████████████████████████████████████████████ 362
  2023   ██████████████████████ 180
  2024   █████████████████████ 170
  2025e  ████████████████ 130
"#;
const V12_2_SPOTS: &[Spot] = &[
    spot(
        r#"2021"#,
        0,
        TO_EOL,
        r#"US silicon metal averaged 220 cents per pound in 2021 (USGS / S&P Platts)."#,
    ),
    spot(
        r#"2022"#,
        0,
        TO_EOL,
        r#"The peak of the series: 362 cents per pound (USGS / S&P Platts)."#,
    ),
    spot(
        r#"2023"#,
        0,
        TO_EOL,
        r#"Prices fell back to 180 cents per pound (USGS / S&P Platts)."#,
    ),
    spot(
        r#"2025e"#,
        0,
        TO_EOL,
        r#"130 cents per pound estimated, on oversupply and weak demand (page)."#,
    ),
];

const V13_0_ART: &str = r#"# Who supplies the crucible quartz

  Spruce Pine, NC   est. 70-90% of crucible quartz
  Sibelco + Quartz Corp  about 95% of ultra-high-purity quartz

  mine ──▶ HPQ ──▶ fused-quartz crucible ──▶ MELT + PULL
                     (consumed per pull)
"#;
const V13_0_SPOTS: &[Spot] = &[
    spot(
        r#"Spruce Pine, NC"#,
        0,
        TO_EOL,
        r#"An estimated 70-90% of the quartz for polysilicon-melting crucibles comes from here (Vince Beiser, via news coverage)."#,
    ),
    spot(
        r#"Sibelco + Quartz Corp"#,
        0,
        TO_EOL,
        r#"Together about 95% of ultra-high-purity quartz (ABC News / Konvoy)."#,
    ),
    spot(
        r#"fused-quartz crucible"#,
        0,
        0,
        r#"HPQ is fused into crucibles that hold the silicon melt."#,
    ),
    spot(
        r#"MELT + PULL"#,
        0,
        0,
        r#"Crucibles are consumed in the crystal-pulling step."#,
    ),
];

const V13_1_ART: &str = r#"# Helene, 2024

  Sept 26   both producers halt
  ~2 weeks  Sibelco restarts, ramps to full capacity
  after     no public wafer shortage found (beyond Oct 2024
            not confirmed)

  earlier:  Sibelco $200M to double Spruce Pine capacity
"#;
const V13_1_SPOTS: &[Spot] = &[
    spot(
        r#"Sept 26"#,
        0,
        TO_EOL,
        r#"Hurricane Helene halted both Sibelco and The Quartz Corp (ABC News / Konvoy)."#,
    ),
    spot(
        r#"~2 weeks"#,
        0,
        TO_EOL,
        r#"Sibelco restarted about two weeks later and ramped back up."#,
    ),
    spot(
        r#"no public wafer shortage"#,
        0,
        0,
        r#"Commentators expected limited near-term effect because of buffer inventory. Outcome beyond October 2024 was not confirmed."#,
    ),
    spot(
        r#"$200M"#,
        0,
        0,
        r#"Sibelco had earlier announced $200 million to double capacity at Spruce Pine."#,
    ),
];

const V13_2_ART: &str = r#"# Same chemistry, very different spec

  furnace quartzite   bulk lump rock, cheap, plentiful
  crucible HPQ        ppm-level metal limits, few sources

  no HPQ ──▶ no crucible ──▶ no ingot ──▶ no wafer ──▶ no chip
"#;
const V13_2_SPOTS: &[Spot] = &[
    spot(
        r#"furnace quartzite"#,
        0,
        TO_EOL,
        r#"Bulk quartzite feeds the arc furnace and is plentiful."#,
    ),
    spot(
        r#"crucible HPQ"#,
        0,
        TO_EOL,
        r#"Crucible quartz must meet ppm-level metal limits and has few qualified sources."#,
    ),
    spot(
        r#"no HPQ"#,
        0,
        TO_EOL,
        r#"A chain with no short cuts: each crystal needs a crucible."#,
    ),
];

const V14_0_ART: &str = r#"# Ferroglobe, Q2 2026

  sales          $378.6M
  net profit     $60.4M
  driver         $59.9M fair-value gain, energy contracts
  silicon metal  revenue $105.8M, price $2,592/t, 40,818 t
                 segment adj. EBITDA about -$2.7M
  outlook        better in H2 2026, if EC trade action lands
"#;
const V14_0_SPOTS: &[Spot] = &[
    spot(
        r#"sales"#,
        0,
        TO_EOL,
        r#"Company sales were $378.6 million."#,
    ),
    spot(
        r#"net profit"#,
        0,
        TO_EOL,
        r#"Net profit was $60.4 million."#,
    ),
    spot(
        r#"driver"#,
        0,
        TO_EOL,
        r#"Nearly all of the profit was a $59.9 million fair-value gain on long-term energy contracts."#,
    ),
    spot(
        r#"silicon metal"#,
        0,
        0,
        r#"Silicon metal revenue $105.8M, up 25.8% from Q1, at $2,592 per tonne (down 5.9%)."#,
    ),
    spot(
        r#"outlook"#,
        0,
        TO_EOL,
        r#"Management expects improvement in H2 2026 pending European Commission trade actions."#,
    ),
];

const V14_1_ART: &str = r#"# What moves the stock (page's read)

  price   362 c/lb (2022) ──▶ 130 c/lb (2025e)
  cost    power contracts
  swing   tariffs, critical-mineral policy, EC trade action
"#;
const V14_1_SPOTS: &[Spot] = &[
    spot(
        r#"price"#,
        0,
        TO_EOL,
        r#"US silicon metal fell from 362 to 130 cents per pound (USGS / S&P Platts, per the page)."#,
    ),
    spot(
        r#"cost"#,
        0,
        TO_EOL,
        r#"Long-term power contracts shape margins."#,
    ),
    spot(
        r#"swing"#,
        0,
        TO_EOL,
        r#"Trade and critical-mineral policy are the swing factor."#,
    ),
];

const V14_2_ART: &str = r#"# Who you can buy

  Ferroglobe   GSM       silicon metal, Western
  Elkem        ELK.OL    silicon metal and products
  Sibelco      private   Spruce Pine quartz
  Quartz Corp  private   Spruce Pine quartz
"#;
const V14_2_SPOTS: &[Spot] = &[
    spot(
        r#"Ferroglobe"#,
        0,
        TO_EOL,
        r#"Largest listed pure play on Western silicon metal."#,
    ),
    spot(
        r#"Elkem"#,
        0,
        TO_EOL,
        r#"The other listed name, per the page."#,
    ),
    spot(
        r#"Sibelco"#,
        0,
        TO_EOL,
        r#"Private, so no direct stock exposure to Spruce Pine quartz."#,
    ),
    spot(
        r#"Quartz Corp"#,
        0,
        TO_EOL,
        r#"Private (Imerys / Norsk Mineral JV, per the SAND page)."#,
    ),
];

const V15_0_ART: &str = r#"# Chemistry as a filter

  MG-Si (98-99%) ──▶ + HCl ──▶ chlorosilanes (volatile)
       │                          │
       │                          ▼ distill by boiling point
       ▼
  metal chlorides: different boiling points ──▶ separated out
  B and P chlorides: boil near TCS ──▶ the hard ones
  (textbook chemistry)
"#;
const V15_0_SPOTS: &[Spot] = &[
    spot(
        r#"MG-Si (98-99%)"#,
        0,
        0,
        r#"The feed from the SAND page's arc furnaces: about 2N, with roughly 10,000 ppm impurities."#,
    ),
    spot(
        r#"chlorosilanes (volatile)"#,
        0,
        0,
        r#"Only silicon reacts with HCl to make volatile chlorosilanes such as trichlorosilane (textbook chemistry)."#,
    ),
    spot(
        r#"metal chlorides"#,
        0,
        0,
        r#"Many metal impurities form chlorides with different boiling points, so distillation can separate them (textbook)."#,
    ),
    spot(
        r#"B and P chlorides"#,
        0,
        0,
        r#"Boron and phosphorus chlorides boil near TCS, so they are the stubborn dopants. The page's donor limits (atoms per cm3) are built around them."#,
    ),
];

const V15_1_ART: &str = r#"# Supply chain into the reactor

  smelter (power-priced) ──▶ MG-Si ──▶ TCS reactor ──▶ Siemens CVD
          ▲                                               │
   own supply or bought                                   ▼
                                                 polysilicon + STC
                                                 (STC is a by-product)
"#;
const V15_1_SPOTS: &[Spot] = &[
    spot(
        r#"smelter (power-priced)"#,
        0,
        0,
        r#"Silicon metal is priced by power cost and trade policy, not by chip demand (textbook)."#,
    ),
    spot(
        r#"own supply or bought"#,
        0,
        0,
        r#"Polysilicon makers either run their own silicon-metal supply or buy from smelters (textbook)."#,
    ),
    spot(
        r#"TCS reactor"#,
        0,
        0,
        r#"Ground metal reacts with HCl to make trichlorosilane (next card)."#,
    ),
    spot(
        r#"Siemens CVD"#,
        0,
        0,
        r#"Trichlorosilane is heated in the presence of silicon rods and silicon deposits on them (patent descriptions)."#,
    ),
    spot(
        r#"STC is a by-product"#,
        0,
        0,
        r#"Siemens production makes large quantities of silicon tetrachloride, per patent descriptions."#,
    ),
];

const V16_0_ART: &str = r#"# Fluidised-bed reactor

   HCl gas in            off: TCS + STC + H2
      │                        ▲
      ▼                        │
   ┌───────────────────────────────┐
   │  ground Si powder, bubbling   │  about 300 C
   │  (exothermic: cooled)         │
   └───────────────────────────────┘
  Si + 3.1 HCl ──▶ 0.9 SiHCl3 + 0.1 SiCl4 + 1.1 H2
  (Fraunhofer ISE practical mix)
"#;
const V16_0_SPOTS: &[Spot] = &[
    spot(
        r#"HCl gas in"#,
        0,
        0,
        r#"HCl gas fluidises the ground silicon powder."#,
    ),
    spot(
        r#"about 300 C"#,
        0,
        0,
        r#"The bed runs at about 300 C (page)."#,
    ),
    spot(
        r#"exothermic: cooled"#,
        0,
        0,
        r#"The reaction releases heat, so the bed needs cooling rather than heating (textbook)."#,
    ),
    spot(
        r#"0.9 SiHCl3"#,
        0,
        0,
        r#"Fraunhofer ISE's practical mix: about 90% of the chlorosilane product is TCS."#,
    ),
    spot(
        r#"0.1 SiCl4"#,
        0,
        0,
        r#"About 10% of the product is silicon tetrachloride (STC)."#,
    ),
];

const V16_1_ART: &str = r#"# TCS at a glance

  boils at     31.8 C       (so distillable at 30-60 C)
  liquid       at ordinary conditions
  hazards      hydrolyses to HCl; flammable
  energy       about 9 kWh/kg of Si
               of 60-70 kWh/kg total (solar grade, 2023)
"#;
const V16_1_SPOTS: &[Spot] = &[
    spot(
        r#"boils at"#,
        0,
        TO_EOL,
        r#"Trichlorosilane boils at 31.8 C (Wikipedia; one older reference gives 36.5 C)."#,
    ),
    spot(
        r#"liquid"#,
        0,
        TO_EOL,
        r#"A liquid at ordinary conditions that boils near room temperature."#,
    ),
    spot(
        r#"hazards"#,
        0,
        TO_EOL,
        r#"TCS hydrolyses to HCl and is flammable."#,
    ),
    spot(
        r#"energy"#,
        0,
        0,
        r#"Fraunhofer ISE electricity breakdown: TCS synthesis about 9 kWh/kg, within 60-70 kWh/kg for solar grade in 2023."#,
    ),
];

const V16_2_ART: &str = r#"# Two ways to deposit

  Siemens                        Fluidised bed
  batch, hot rods                continuous, silicon granules
  high power per kg              potential for large energy savings
  chunks after crushing          free-flowing granules
  (Hemlock patents combine the two)
"#;
const V16_2_SPOTS: &[Spot] = &[
    spot(
        r#"Siemens"#,
        0,
        0,
        r#"Batch deposition on hot rods, the process this page follows."#,
    ),
    spot(
        r#"Fluidised bed"#,
        0,
        0,
        r#"Continuous deposition onto silicon granules, per patent descriptions."#,
    ),
    spot(
        r#"potential for large energy savings"#,
        0,
        0,
        r#"Patents describe large electrical energy savings potential (inventor claim)."#,
    ),
    spot(
        r#"Hemlock patents"#,
        0,
        0,
        r#"Hemlock holds patents on fluidised-bed processes and on integrating them with Siemens reactors (US7927984, US8609058)."#,
    ),
];

const V17_0_ART: &str = r#"# Column separates by boiling point

         ┌────────┐
   TCS ◀─┤  top   │ 31.8 C   lights out the top
         │ column │
         │        │
   STC ◀─┤ bottom │ 57.7 C   heavier goes down
         └────────┘
  metal, B and P chlorides split off at other stages
  (30-60 C range from the page)
"#;
const V17_0_SPOTS: &[Spot] = &[
    spot(
        r#"TCS ◀"#,
        0,
        0,
        r#"Trichlorosilane boils at 31.8 C and comes off the top (Wikipedia)."#,
    ),
    spot(
        r#"STC ◀"#,
        0,
        0,
        r#"Silicon tetrachloride boils at about 57.7 C (Wikipedia) and leaves lower."#,
    ),
    spot(
        r#"metal, B and P chlorides"#,
        0,
        0,
        r#"Metal chlorides and the boron and phosphorus chlorides are separated at other points. Repeated stages push donor impurities down."#,
    ),
    spot(
        r#"30-60 C range"#,
        0,
        0,
        r#"The page quotes distillation at 30-60 C."#,
    ),
];

const V17_1_ART: &str = r#"# Donors, atoms per cm3 (lower is purer)

  solar grade  ███████████████████████████████████ 2.5e14
  EG3          ██████████████████████ 5e12
  Special EG   ██████████████████ 1.5e12
  (bar length = log10 of the limit, minus 10: a log scale)
  solar is more than 100x looser than Special EG
"#;
const V17_1_SPOTS: &[Spot] = &[
    spot(
        r#"solar grade"#,
        0,
        TO_EOL,
        r#"Solar grade allows 2.5e14 donor atoms per cm3 (GB/T 12963-2022 / Fraunhofer ISE, per the page)."#,
    ),
    spot(
        r#"EG3"#,
        0,
        TO_EOL,
        r#"EG3 allows 5e12 donor atoms per cm3."#,
    ),
    spot(
        r#"Special EG"#,
        0,
        TO_EOL,
        r#"Special EG allows 1.5e12 atoms per cm3 donors and 0.1 ppbw base metals or less."#,
    ),
    spot(
        r#"more than 100x looser"#,
        0,
        0,
        r#"2.5e14 divided by 1.5e12 is about 167, so solar allows well over 100 times more donors than Special EG."#,
    ),
];

const V17_2_ART: &str = r#"# Wacker Burghausen, July 2025

  new etching line   over EUR 300 million
  capacity           hyperpure cleaning up more than 50%
  purity             EG about 11N (Bernreuter: 12N claims not achieved)
"#;
const V17_2_SPOTS: &[Spot] = &[
    spot(
        r#"new etching line"#,
        0,
        TO_EOL,
        r#"Wacker commissioned the line in July 2025 at a cost above 300 million euros, its largest single investment in ten years."#,
    ),
    spot(
        r#"capacity"#,
        0,
        TO_EOL,
        r#"Hyperpure cleaning capacity rises by more than 50% over the long term."#,
    ),
    spot(
        r#"purity"#,
        0,
        TO_EOL,
        r#"Electronic grade is near 11N. Bernreuter says claims of 12N are not achieved for EG polysilicon."#,
    ),
];

const V18_0_ART: &str = r#"# Reactor cross-section

        ┌──────────────────────┐
        │   ┌────┐    ┌────┐   │  bell jar
        │   │    └────┘    │   │  U-shaped rod pairs
        │   │              │   │  (bridge on top)
        ├───┴─┐          ┌─┴───┤
        │ elec│          │elec │  base plate electrodes
        └─────┴──────────┴─────┘
          gas in            off-gas out
"#;
const V18_0_SPOTS: &[Spot] = &[
    spot(
        r#"bell jar"#,
        0,
        0,
        r#"The jar mates with the base plate to form a batch reactor, under vacuum or positive pressure (patent descriptions)."#,
    ),
    spot(
        r#"U-shaped rod pairs"#,
        0,
        0,
        r#"Filament rods are usually joined in inverted U pairs with a bridge on top."#,
    ),
    spot(
        r#"base plate electrodes"#,
        0,
        0,
        r#"Electrodes in the base plate hold the rods and carry the current."#,
    ),
    spot(
        r#"gas in"#,
        0,
        0,
        r#"TCS and hydrogen enter through nozzles in the base plate."#,
    ),
    spot(
        r#"off-gas out"#,
        0,
        0,
        r#"Off-gas (HCl, H2, STC, unreacted TCS) leaves through the base plate and goes to recovery."#,
    ),
];

const V18_1_ART: &str = r#"# One batch

  start 20 mm ──────────────────────────▶ 150-180 mm
  growth at most 1.9 mm per hour (diameter)

  CVD step power   35-45 kWh/kg
  heat recoverable 70-85%
  (batch duration: not in the sources used)
"#;
const V18_1_SPOTS: &[Spot] = &[
    spot(
        r#"start 20 mm"#,
        0,
        0,
        r#"Deposition begins on a slim 20 mm silicon rod."#,
    ),
    spot(
        r#"150-180 mm"#,
        0,
        0,
        r#"Rods are grown to a final diameter of 150-180 mm (page)."#,
    ),
    spot(
        r#"1.9 mm per hour"#,
        0,
        0,
        r#"Diameter grows at most about 1.9 mm per hour (page figure)."#,
    ),
    spot(
        r#"35-45 kWh/kg"#,
        0,
        0,
        r#"Electricity for the CVD step alone, per the page."#,
    ),
    spot(
        r#"heat recoverable"#,
        0,
        0,
        r#"The page cites 70-85% of the heat as recoverable."#,
    ),
];

const V18_2_ART: &str = r#"# Unloading (textbook)

  cool down ──▶ lift jar ──▶ remove rods ──▶ cut off graphite stubs
                                  │
                                  ▼
                           to CRUSH + etch
"#;
const V18_2_SPOTS: &[Spot] = &[
    spot(
        r#"cool down"#,
        0,
        0,
        r#"The reactor is cooled before opening (textbook)."#,
    ),
    spot(
        r#"lift jar"#,
        0,
        0,
        r#"The jar is lifted off the base plate (textbook)."#,
    ),
    spot(
        r#"cut off graphite stubs"#,
        0,
        0,
        r#"The foot of each rod, where it met the graphite chuck, is cut off (textbook)."#,
    ),
    spot(
        r#"to CRUSH + etch"#,
        0,
        0,
        r#"Rods go to crushing and etching next."#,
    ),
];

const V19_0_ART: &str = r#"# Rod to bag

  rod ──▶ ┌────────┐ ──▶ ┌─────────────────┐ ──▶ ┌───────────┐
          │ CRUSH  │     │ ETCH            │     │ PACK      │
          │ chunks │     │ HNO3 + HF, room │     │ clean bag │
          └────────┘     │ T, or alkali    │     │ cleanroom │
                         │ 70-80 C         │     └───────────┘
                         └─────────────────┘
  etch strips contamination from tools and handling
"#;
const V19_0_SPOTS: &[Spot] = &[
    spot(
        r#"CRUSH"#,
        0,
        0,
        r#"Rods are broken into chunks sized for crystal-puller crucibles."#,
    ),
    spot(
        r#"HNO3 + HF"#,
        0,
        0,
        r#"Acid etch at room temperature strips surface contamination (page)."#,
    ),
    spot(
        r#"alkali"#,
        0,
        0,
        r#"Alkaline etching at 70-80 C is the alternative (page)."#,
    ),
    spot(
        r#"PACK"#,
        0,
        0,
        r#"Chunks are packed in clean bags in cleanroom conditions (textbook)."#,
    ),
    spot(
        r#"strips contamination"#,
        0,
        0,
        r#"Etching removes contamination picked up from crushing tools and handling."#,
    ),
];

const V19_1_ART: &str = r#"# Smooth vs popcorn surface (patent descriptions)

  dense rod                  popcorn rod (above ~150 mm)
  ┌──────────┐               ┌─╮─╭╮─╮─╭─╮┐
  │ smooth   │               │ porous,    │
  │ dense    │               │ fissured   │
  └──────────┘               └────────────┘
  full grade                 deep popcorn ──▶ downgraded
"#;
const V19_1_SPOTS: &[Spot] = &[
    spot(
        r#"dense rod"#,
        0,
        0,
        r#"Smooth, dense rods are the full-grade product."#,
    ),
    spot(
        r#"popcorn rod"#,
        0,
        0,
        r#"A porous, fissured surface layer, common on large-diameter rods above about 150 mm (patent descriptions)."#,
    ),
    spot(
        r#"downgraded"#,
        0,
        0,
        r#"Rod pieces with excessively deep popcorn must be downgraded (patent descriptions)."#,
    ),
];

const V19_2_ART: &str = r#"# Capacity addition

  Wacker Etching Line Next, Burghausen
  commissioned  July 2025
  role          etch + clean chunk polysilicon for chip customers
  status        first deliveries started by July 2025 (company)
"#;
const V19_2_SPOTS: &[Spot] = &[
    spot(
        r#"commissioned"#,
        0,
        TO_EOL,
        r#"Commissioned in July 2025 (company press release)."#,
    ),
    spot(
        r#"role"#,
        0,
        TO_EOL,
        r#"The new line is the etch and clean step for chunk polysilicon."#,
    ),
    spot(
        r#"status"#,
        0,
        TO_EOL,
        r#"Wacker says first deliveries to chip customers had started by July 2025."#,
    ),
];

const V20_0_ART: &str = r#"# Hand-off to the crystal puller

  POLY chunks (9N+) ──▶ qualified lot by lot (years)
        │
        ▼
  MELT + PULL: quartz crucible ──▶ single crystal
  (switching supplier is slow)
"#;
const V20_0_SPOTS: &[Spot] = &[
    spot(
        r#"POLY chunks"#,
        0,
        0,
        r#"Chunk polysilicon of 9N or better for electronics (page)."#,
    ),
    spot(
        r#"qualified lot by lot"#,
        0,
        0,
        r#"Wafer makers qualify lots, often over years, so switching is slow."#,
    ),
    spot(
        r#"MELT + PULL"#,
        0,
        0,
        r#"The next node melts the chunks in a quartz crucible and pulls a single crystal."#,
    ),
];

const V20_1_ART: &str = r#"# Two product forms

  Siemens chunks               FBR granules
  broken rods, sharp           spherical, free-flowing
  etched, bagged               easier to handle (patent text)
"#;
const V20_1_SPOTS: &[Spot] = &[
    spot(
        r#"Siemens chunks"#,
        0,
        TO_EOL,
        r#"Rod-derived chunks, the form on this page."#,
    ),
    spot(
        r#"FBR granules"#,
        0,
        TO_EOL,
        r#"Fluidised-bed reactor output: approximately spherical, free-flowing particles (patent description)."#,
    ),
    spot(
        r#"easier to handle"#,
        0,
        TO_EOL,
        r#"Patent text says granules are easier to handle mechanically than Siemens rods."#,
    ),
];

const V20_2_ART: &str = r#"# Wacker's stated goal (company statements)

  2024  semiconductor sales   ████████████ baseline
  2030  target                ████████████████████████ about double
  drivers: AI chips, data centers, digitalisation
"#;
const V20_2_SPOTS: &[Spot] = &[
    spot(r#"2024"#, 0, TO_EOL, r#"The baseline for Wacker's goal."#),
    spot(
        r#"2030"#,
        0,
        TO_EOL,
        r#"Wacker aims to double semiconductor sales by 2030 versus 2024 (company statement)."#,
    ),
    spot(
        r#"drivers"#,
        0,
        TO_EOL,
        r#"The company ties demand to AI chips, data centers and digitalisation."#,
    ),
];

const V21_0_ART: &str = r#"# Hot rod, cold wall

  ┃ water cooled steel wall (cool)        ┃
  ┃        ~~~ heat radiates out ~~~▶     ┃
  ┃    ┌──┐                               ┃
  ┃    │▓▓│ rod surface about 1100 C      ┃
  ┃    └──┘ silicon deposits here only    ┃
"#;
const V21_0_SPOTS: &[Spot] = &[
    spot(
        r#"water cooled steel wall"#,
        0,
        0,
        r#"The jar wall is water-cooled so silicon does not deposit on it (textbook)."#,
    ),
    spot(
        r#"heat radiates out"#,
        0,
        0,
        r#"The rods radiate to the cold wall, which is why a large share of CVD power is lost as heat."#,
    ),
    spot(
        r#"about 1100 C"#,
        0,
        0,
        r#"Rod surface temperature per the page."#,
    ),
    spot(
        r#"deposits here only"#,
        0,
        0,
        r#"Silicon deposits only on the hot rods."#,
    ),
];

const V21_1_ART: &str = r#"# Where the CVD power goes

  35-45 kWh/kg in
        │
        ├──▶ silicon deposition
        └──▶ heat to the cold wall: 70-85% recoverable (page)
"#;
const V21_1_SPOTS: &[Spot] = &[
    spot(
        r#"35-45 kWh/kg"#,
        0,
        0,
        r#"Electricity for the CVD step alone, per the page."#,
    ),
    spot(
        r#"silicon deposition"#,
        0,
        0,
        r#"Only part of the power drives the deposition itself."#,
    ),
    spot(
        r#"70-85% recoverable"#,
        0,
        0,
        r#"The page cites 70-85% of CVD heat as recoverable."#,
    ),
];

const V21_2_ART: &str = r#"# What makes popcorn (patent text)

  gas backup            ─┐
  extra vortices         ├──▶ popcorn growth + dust deposition
  overheated gas        ─┘
  blocked feed/offgas paths make it worse

  fix: adjust parameters ──▶ longer process, lower output
"#;
const V21_2_SPOTS: &[Spot] = &[
    spot(
        r#"gas backup"#,
        0,
        0,
        r#"Patent text lists gas backup as a cause of popcorn growth."#,
    ),
    spot(
        r#"extra vortices"#,
        0,
        0,
        r#"Extra vortices in the reactor are another cause (patent text)."#,
    ),
    spot(
        r#"overheated gas"#,
        0,
        0,
        r#"Overheated reaction gas is a third cause (patent text)."#,
    ),
    spot(
        r#"longer process, lower output"#,
        0,
        0,
        r#"Tuning parameters to suppress popcorn usually lengthens the process and reduces output (patent text)."#,
    ),
];

const V22_0_ART: &str = r#"# Current path

        ┌────────── bridge ──────────┐
        │                            │
        │ up                    down │
        │                            │
     ┌──┴──┐                      ┌──┴──┐
     │chuck│                      │chuck│
     └──┬──┘                      └──┬──┘
      electrode +                 electrode -
"#;
const V22_0_SPOTS: &[Spot] = &[
    spot(
        r#"bridge"#,
        0,
        0,
        r#"A horizontal rod joins the tops so current flows up one rod, across and down the other."#,
    ),
    spot(r#"up"#, 0, 0, r#"Current rises through one rod."#),
    spot(
        r#"chuck"#,
        0,
        0,
        r#"Graphite chucks hold the rod base and carry current from the electrode."#,
    ),
    spot(
        r#"electrode +"#,
        0,
        0,
        r#"Base-plate electrodes feed the pair; polarity shown for illustration."#,
    ),
];

const V22_1_ART: &str = r#"# What can go wrong (textbook)

  thick rod + weak bridge ──▶ rod falls
                                │
                                ▼
          batch contaminated by the jar floor
  layout: spacing and symmetry set gas flow + radiation
"#;
const V22_1_SPOTS: &[Spot] = &[
    spot(
        r#"weak bridge"#,
        0,
        0,
        r#"The bridge is the usual weak point on thick rods (textbook)."#,
    ),
    spot(
        r#"rod falls"#,
        0,
        0,
        r#"A collapsed rod is a known yield loss in Siemens reactors (textbook)."#,
    ),
    spot(
        r#"jar floor"#,
        0,
        0,
        r#"A fallen rod contaminates the batch with the jar floor (textbook)."#,
    ),
    spot(
        r#"layout"#,
        0,
        0,
        r#"Rod spacing and symmetry affect gas flow and radiation exchange, so layout is core reactor design."#,
    ),
];

const V23_0_ART: &str = r#"# Chuck in the chain

  power feed ──▶ base-plate electrode ──▶ graphite chuck ──▶ rod
  (high current through the base plate)

        rod
         │
      ┌──┴──┐
      │chuck│ graphite, hyperpure
      └──┬──┘
         │ electrode
"#;
const V23_0_SPOTS: &[Spot] = &[
    spot(
        r#"power feed"#,
        0,
        0,
        r#"High-current power feeds pass through the base plate (page)."#,
    ),
    spot(
        r#"graphite chuck"#,
        0,
        0,
        r#"Graphite chucks hold the rod base and carry current (SGL Carbon lists graphite components for polysilicon production)."#,
    ),
    spot(
        r#"graphite, hyperpure"#,
        0,
        0,
        r#"The carbon has to be hyperpure because the rod foot is a contamination path (textbook)."#,
    ),
];

const V23_1_ART: &str = r#"# Why the foot is cut off (textbook)

  chuck ──▶ carbon + metal diffusion into the rod foot
                          │
                          ▼
              foot cut off after the batch
  carbon limit in the spec: not found in sources
"#;
const V23_1_SPOTS: &[Spot] = &[
    spot(
        r#"carbon + metal diffusion"#,
        0,
        0,
        r#"Diffusion at the rod foot is a contamination path (textbook)."#,
    ),
    spot(
        r#"foot cut off"#,
        0,
        0,
        r#"The foot is cut off after the batch (textbook), so the chuck region is the lowest-value part of a rod."#,
    ),
    spot(
        r#"not found in sources"#,
        0,
        0,
        r#"Electronics specs track carbon, but the specific limits were not found in the sources used."#,
    ),
];

const V24_0_ART: &str = r#"# Rod diameter over a batch

  20 mm   ██
  60 mm   ██████
  100 mm  ██████████
  150 mm  ███████████████
  180 mm  ██████████████████   (growth at most 1.9 mm/h)

  EG: slow, uniform     solar: faster, rougher
"#;
const V24_0_SPOTS: &[Spot] = &[
    spot(r#"20 mm"#, 0, TO_EOL, r#"The slim starter rod."#),
    spot(
        r#"150 mm"#,
        0,
        TO_EOL,
        r#"The lower end of the final diameter range (page)."#,
    ),
    spot(
        r#"180 mm"#,
        0,
        0,
        r#"The upper end of the final diameter range; growth is at most 1.9 mm/h on diameter (page)."#,
    ),
    spot(
        r#"EG: slow, uniform"#,
        0,
        0,
        r#"Electronic grade uses a steady H2:TCS ratio, low HCl and even temperature for a smooth, dense rod."#,
    ),
];

const V24_1_ART: &str = r#"# The speed tradeoff

  faster growth ──▶ more popcorn ──▶ downgraded pieces
  slower growth ──▶ smoother rod ──▶ less output per jar

  EG plants choose slower
"#;
const V24_1_SPOTS: &[Spot] = &[
    spot(
        r#"faster growth"#,
        0,
        TO_EOL,
        r#"Higher growth rate raises popcorn risk (patents)."#,
    ),
    spot(
        r#"slower growth"#,
        0,
        TO_EOL,
        r#"Slower growth reduces popcorn but cuts output (patents)."#,
    ),
    spot(
        r#"EG plants choose slower"#,
        0,
        0,
        r#"Electronic-grade plants accept lower throughput per jar."#,
    ),
];

const V24_2_ART: &str = r#"# Same chemistry, different regime

                 solar grade        electronic grade
  growth speed   high               slow, uniform
  surface        tolerates rough    smooth and dense
  H2:TCS, HCl    wider window       steady, low HCl
"#;
const V24_2_SPOTS: &[Spot] = &[
    spot(
        r#"growth speed"#,
        0,
        TO_EOL,
        r#"Solar pushes speed; EG runs slower for uniform growth."#,
    ),
    spot(
        r#"surface"#,
        0,
        TO_EOL,
        r#"Solar tolerates rough surfaces; EG needs smooth, dense rods."#,
    ),
    spot(
        r#"H2:TCS, HCl"#,
        0,
        TO_EOL,
        r#"EG holds a steady H2:TCS ratio and low HCl (patents)."#,
    ),
];

const V25_0_ART: &str = r#"# Donor limit, atoms per cm3

  Special EG  1.5e12   ██████████████████
  EG3         5e12     ██████████████████████
  solar       2.5e14   ███████████████████████████████████
  (log scale: bar = log10(limit) minus 10)
  base metals, Special EG: at or below 0.1 ppbw
"#;
const V25_0_SPOTS: &[Spot] = &[
    spot(
        r#"Special EG"#,
        0,
        0,
        r#"Donors at or below 1.5e12 atoms per cm3 (GB/T 12963-2022 / Fraunhofer ISE, per the page)."#,
    ),
    spot(r#"EG3"#, 0, 0, r#"EG3 allows 5e12 donor atoms per cm3."#),
    spot(
        r#"solar"#,
        0,
        0,
        r#"Solar grade allows 2.5e14, over 100 times more than Special EG."#,
    ),
    spot(
        r#"0.1 ppbw"#,
        0,
        0,
        r#"Base metals are at or below 0.1 ppbw for Special EG."#,
    ),
];

const V25_1_ART: &str = r#"# One dopant atom in 1e12

  1e12 silicon atoms:  Si Si Si Si P Si Si Si ...
                                   │
                                   ▼
                     shifts the crystal's resistivity
  device wafers need controlled dopant levels (textbook)
"#;
const V25_1_SPOTS: &[Spot] = &[
    spot(
        r#"1e12 silicon atoms"#,
        0,
        0,
        r#"One dopant atom per 1e12 silicon atoms is enough to shift resistivity (textbook)."#,
    ),
    spot(
        r#"shifts the crystal's resistivity"#,
        0,
        0,
        r#"Boron is the acceptor and phosphorus the donor dopant (textbook)."#,
    ),
    spot(
        r#"controlled dopant levels"#,
        0,
        0,
        r#"Device wafers must have controlled dopant levels (textbook)."#,
    ),
];

const V25_2_ART: &str = r#"# Share and grade

  EG share of volume   about 5%
  purity               near 11N
  12N claims           not achieved (Bernreuter)
  qualification        per customer, a moving ladder
"#;
const V25_2_SPOTS: &[Spot] = &[
    spot(
        r#"EG share of volume"#,
        0,
        TO_EOL,
        r#"Electronics grade is only about 5% of polysilicon volume (page)."#,
    ),
    spot(r#"purity"#, 0, TO_EOL, r#"About 11N for electronic grade."#),
    spot(
        r#"12N claims"#,
        0,
        TO_EOL,
        r#"Bernreuter says 12N claims for EG polysilicon are not achieved."#,
    ),
    spot(
        r#"qualification"#,
        0,
        TO_EOL,
        r#"Each customer qualifies the grade separately."#,
    ),
];

const V26_0_ART: &str = r#"# Capacity 2024, kt (Bernreuter)

  Tongwei  ██████████████████████████████████████ 910
  GCL      ████████████████████ 480
  Daqo     ██████████████ 350
  Xinte    ████████████ 300
  top four = 65% of global output
"#;
const V26_0_SPOTS: &[Spot] = &[
    spot(
        r#"Tongwei"#,
        0,
        TO_EOL,
        r#"Ranked first at 910 thousand tonnes in 2024 (Bernreuter)."#,
    ),
    spot(r#"GCL"#, 0, TO_EOL, r#"GCL: 480 thousand tonnes."#),
    spot(r#"Daqo"#, 0, TO_EOL, r#"Daqo: 350 thousand tonnes."#),
    spot(r#"Xinte"#, 0, TO_EOL, r#"Xinte: 300 thousand tonnes."#),
    spot(
        r#"top four"#,
        0,
        0,
        r#"The top four hold 65% of global output (page, Bernreuter)."#,
    ),
];

const V26_1_ART: &str = r#"# China Mono Premium, yuan per kg (OPIS)

  mid-2025 low   ███████████████ just above 30
  Mar 17 2026    ██████████████████████ 44.583 (-16.4% since Jan)

  consolidation plan: acquire and idle ~1/3 of capacity
  status: stalled since mid-January (regulators)
"#;
const V26_1_SPOTS: &[Spot] = &[
    spot(
        r#"mid-2025 low"#,
        0,
        TO_EOL,
        r#"The mid-2025 low was just above 30 yuan/kg (OPIS)."#,
    ),
    spot(
        r#"Mar 17 2026"#,
        0,
        TO_EOL,
        r#"OPIS assessed China Mono Premium at 44.583 yuan/kg, down 16.4% since January."#,
    ),
    spot(
        r#"consolidation plan"#,
        0,
        0,
        r#"A plan to acquire and idle about one-third of Chinese capacity, with about CNY 50 billion raised by leaders (OPIS)."#,
    ),
    spot(
        r#"stalled since mid-January"#,
        0,
        0,
        r#"Regulators barred coordinated production and pricing controls over monopoly concerns (OPIS)."#,
    ),
];

const V26_2_ART: &str = r#"# Indirect link

  Chinese solar poly (cheap)
      │ pressures
      ▼
  Western makers
      ╳ not a substitute: not electronic grade

  Tongwei 2024: expected loss 7 to 7.5 billion yuan
"#;
const V26_2_SPOTS: &[Spot] = &[
    spot(
        r#"Chinese solar poly"#,
        0,
        0,
        r#"The Chinese output is solar grade, priced in a glut."#,
    ),
    spot(
        r#"Western makers"#,
        0,
        0,
        r#"Cheap Chinese poly pressures Western makers' margins."#,
    ),
    spot(
        r#"not electronic grade"#,
        0,
        0,
        r#"Solar grade cannot replace electronic grade: the purity gap is about 100x in donors."#,
    ),
    spot(
        r#"expected loss"#,
        0,
        0,
        r#"Tongwei was expected to lose 7 to 7.5 billion yuan in 2024 (Yicai). 2025-26 results were not found."#,
    ),
];

const V27_0_ART: &str = r#"# Wacker (WCH.DE)

  claim     world's leading producer of semiconductor polysilicon
  claim     only European producer of ultra-pure polysilicon
  goal      double semiconductor sales by 2030 vs 2024
  demand    AI chips, data centers (company's own statements)
"#;
const V27_0_SPOTS: &[Spot] = &[
    spot(
        r#"claim     world"#,
        0,
        TO_EOL,
        r#"A company claim, not independent."#,
    ),
    spot(
        r#"claim     only"#,
        0,
        TO_EOL,
        r#"The company says it is the only European producer of ultra-pure polysilicon."#,
    ),
    spot(
        r#"goal"#,
        0,
        TO_EOL,
        r#"Double semiconductor sales by 2030 versus 2024."#,
    ),
    spot(
        r#"demand"#,
        0,
        TO_EOL,
        r#"Wacker ties demand to AI chips and data centers."#,
    ),
];

const V27_1_ART: &str = r#"# Burghausen, July 2025

  cost       over EUR 300 million
  scale      largest single investment in ten years
  effect     ultra-pure capacity up more than 50% (long term)
"#;
const V27_1_SPOTS: &[Spot] = &[
    spot(r#"cost"#, 0, TO_EOL, r#"Above 300 million euros."#),
    spot(
        r#"scale"#,
        0,
        TO_EOL,
        r#"Its largest single investment in ten years (company)."#,
    ),
    spot(
        r#"effect"#,
        0,
        TO_EOL,
        r#"Ultra-pure capacity up by more than 50% over the long term."#,
    ),
];

const V27_2_ART: &str = r#"# Electricity per kg (Fraunhofer ISE)

  Wacker EG only, 2002     ██████████████████████████████ 150 kWh/kg
  Wacker average, 2020     ██████████████████ 91.9 kWh/kg
  rank by capacity: 8th, about 80 kt
"#;
const V27_2_SPOTS: &[Spot] = &[
    spot(
        r#"Wacker EG only, 2002"#,
        0,
        TO_EOL,
        r#"Fraunhofer ISE reports 150 kWh/kg for Wacker electronic-grade-only in 2002."#,
    ),
    spot(
        r#"Wacker average, 2020"#,
        0,
        TO_EOL,
        r#"A multi-product average of 91.9 kWh/kg in 2020."#,
    ),
    spot(
        r#"rank by capacity"#,
        0,
        0,
        r#"Wacker ranks 8th by capacity at about 80 thousand tonnes (page)."#,
    ),
];

const V28_0_ART: &str = r#"# Hemlock Semiconductor, Michigan

  rank          14th overall (page)
  grade         US electronic-grade producer
  patents       FBR with STC: less wall deposition   US7927984
                Siemens-integrated FBR               US8609058
"#;
const V28_0_SPOTS: &[Spot] = &[
    spot(
        r#"rank"#,
        0,
        TO_EOL,
        r#"The page ranks Hemlock 14th overall."#,
    ),
    spot(r#"grade"#, 0, TO_EOL, r#"A US electronic-grade producer."#),
    spot(
        r#"FBR with STC"#,
        0,
        0,
        r#"A fluidised-bed process using tetrachlorosilane to reduce wall deposition (US7927984)."#,
    ),
    spot(
        r#"Siemens-integrated FBR"#,
        0,
        0,
        r#"Integrating fluidised beds with Siemens reactors (US8609058)."#,
    ),
];

const V28_1_ART: &str = r#"# Minimum import prices (Proclamation 11052)

  polysilicon     $21 per kg
  ingots, wafers  $100 per kg
  cells           $0.22 per W
  modules         $0.38 per W
  signed 6 Aug 2026, effective 4 Dec 2026
"#;
const V28_1_SPOTS: &[Spot] = &[
    spot(
        r#"polysilicon"#,
        0,
        TO_EOL,
        r#"Minimum import price $21 per kg for polysilicon."#,
    ),
    spot(
        r#"ingots, wafers"#,
        0,
        TO_EOL,
        r#"$100 per kg for ingots and wafers."#,
    ),
    spot(r#"cells"#, 0, TO_EOL, r#"$0.22 per watt for cells."#),
    spot(r#"modules"#, 0, TO_EOL, r#"$0.38 per watt for modules."#),
    spot(
        r#"signed 6 Aug 2026"#,
        0,
        0,
        r#"Proclamation 11052 follows a Commerce Section 232 investigation."#,
    ),
];

const V28_2_ART: &str = r#"# What it does and does not say

  raw polysilicon   exempt from 15% derivative tariff
                    but subject to the minimum price
  framing           semiconductor supply-chain security
  waivers           onshoring plans may earn them
  Hemlock, Wacker   specific effects: not found
"#;
const V28_2_SPOTS: &[Spot] = &[
    spot(
        r#"raw polysilicon"#,
        0,
        0,
        r#"Exempt from the 15% tariff on derivatives but subject to the minimum price."#,
    ),
    spot(
        r#"framing"#,
        0,
        TO_EOL,
        r#"The action is framed around semiconductor supply-chain security."#,
    ),
    spot(
        r#"waivers"#,
        0,
        TO_EOL,
        r#"Onshoring plans may earn waivers."#,
    ),
    spot(
        r#"Hemlock, Wacker"#,
        0,
        TO_EOL,
        r#"No source found on specific effects for these makers."#,
    ),
];

const V29_0_ART: &str = r#"# What goes in the crucible

  ┌──────────────── quartz crucible ───────────────┐
  │  polysilicon chunks (electronic grade, 9N+)    │
  │  + dopant dose (boron or phosphorus, etc.)     │
  │  voids between chunks ──▶ recharge tops up     │
  └────────────────────────────────────────────────┘
  chamber sealed, then argon on
"#;
const V29_0_SPOTS: &[Spot] = &[
    spot(
        r#"polysilicon chunks"#,
        0,
        0,
        r#"Electronic-grade chunks from the POLYSILICON node (Wacker, Hemlock, OCI, Tokuyama)."#,
    ),
    spot(
        r#"dopant dose"#,
        0,
        0,
        r#"A measured amount of dopant sets the target resistivity of the whole crystal (textbook)."#,
    ),
    spot(
        r#"voids between chunks"#,
        0,
        0,
        r#"Chunks pack with gaps, so many fabs recharge with extra poly during the pull (textbook)."#,
    ),
    spot(
        r#"quartz crucible"#,
        0,
        0,
        r#"A fused-quartz crucible holds the charge and the melt."#,
    ),
];

const V29_1_ART: &str = r#"# Doping along the crystal (segregation)

  head ░░░░░░▒▒▒▒▒▒▓▓▓▓▓▓████ tail
       lighter doped          heavier doped
  recipe = compromise across the length
  contamination loaded here stays in the melt for good
"#;
const V29_1_SPOTS: &[Spot] = &[
    spot(
        r#"head"#,
        0,
        0,
        r#"The first-frozen head is lighter doped (textbook, segregation)."#,
    ),
    spot(
        r#"tail"#,
        0,
        0,
        r#"Dopant concentrates in the remaining liquid, so the tail is heavier doped."#,
    ),
    spot(
        r#"recipe = compromise"#,
        0,
        0,
        r#"One dopant dose has to serve the whole length of the crystal."#,
    ),
    spot(
        r#"stays in the melt for good"#,
        0,
        0,
        r#"Any metal or carbon loaded here dissolves in the melt and cannot be removed later; the melt only gets dirtier as impurities concentrate in the liquid."#,
    ),
];

const V29_2_ART: &str = r#"# One pull, one batch

  poly in ──▶ crystal out (a bit less than 1:1)
  scrapped:   leftover melt, the crucible (textbook)

  poly shortage or bad lot ──▶ puller idle
  so: long-term supply deals
"#;
const V29_2_SPOTS: &[Spot] = &[
    spot(
        r#"poly in"#,
        0,
        0,
        r#"Roughly 1 kg of poly in gives a bit less of crystal out (textbook)."#,
    ),
    spot(
        r#"scrapped"#,
        0,
        0,
        r#"The leftover melt and the crucible are scrapped (textbook)."#,
    ),
    spot(
        r#"puller idle"#,
        0,
        0,
        r#"A shortage or a quality excursion idles whole pullers."#,
    ),
    spot(
        r#"long-term supply deals"#,
        0,
        0,
        r#"Wafer makers sign long-term poly deals for this reason."#,
    ),
];

const V30_0_ART: &str = r#"# COMSOL furnace model values

  melt                 about 1414 C
  contact temperature  1403 to 1407.5 C
  argon flow           100 L/min
  furnace pressure     2500 Pa
  Wikipedia says 1425 C: the exact figure depends on the source
"#;
const V30_0_SPOTS: &[Spot] = &[
    spot(
        r#"melt"#,
        0,
        TO_EOL,
        r#"The COMSOL model uses a melt near 1414 C."#,
    ),
    spot(
        r#"contact temperature"#,
        0,
        TO_EOL,
        r#"The temperature the seed touches the melt: 1403-1407.5 C in the model."#,
    ),
    spot(
        r#"argon flow"#,
        0,
        TO_EOL,
        r#"Argon flows at 100 L/min in the model."#,
    ),
    spot(
        r#"furnace pressure"#,
        0,
        TO_EOL,
        r#"2500 Pa in the model (a model value, not a vendor spec)."#,
    ),
    spot(
        r#"Wikipedia says 1425 C"#,
        0,
        0,
        r#"Wikipedia quotes 1425 C for semiconductor-grade silicon."#,
    ),
];

const V30_1_ART: &str = r#"# Argon flow path

   argon in at the top
        │
        ▼ past the crystal
   ┌───────────────┐
   │     melt      │ ──▶ SiO and CO evaporate
   └───────────────┘
        │ swept down and out the bottom
        ▼
   exhaust: SiO, CO, argon
"#;
const V30_1_SPOTS: &[Spot] = &[
    spot(
        r#"argon in at the top"#,
        0,
        0,
        r#"Argon enters at the top of the chamber."#,
    ),
    spot(
        r#"past the crystal"#,
        0,
        0,
        r#"It sweeps down past the crystal."#,
    ),
    spot(
        r#"SiO and CO evaporate"#,
        0,
        0,
        r#"SiO and CO leave the melt surface and are carried away."#,
    ),
    spot(
        r#"exhaust"#,
        0,
        0,
        r#"Carrying SiO and CO out stops them condensing on cold parts and raining back into the melt."#,
    ),
];

const V30_2_ART: &str = r#"# Time to a steady contact temperature

  COMSOL model  ████████████████████████████ about 400 min
  rushed seeding ──▶ temperature drift ──▶ diameter wanders
  so: hold a stable melt before the seed goes in
"#;
const V30_2_SPOTS: &[Spot] = &[
    spot(
        r#"COMSOL model"#,
        0,
        TO_EOL,
        r#"The model needs about 400 minutes to reach a steady contact temperature."#,
    ),
    spot(
        r#"rushed seeding"#,
        0,
        0,
        r#"Rushing causes temperature drift and a diameter that wanders (page)."#,
    ),
    spot(
        r#"hold a stable melt"#,
        0,
        0,
        r#"Operators hold a stable melt before seeding."#,
    ),
];

const V31_0_ART: &str = r#"# Seed to neck

      seed (oriented {100} or {111})
        ║
        ║  dipped into the melt
        ║
       ─╨─  neck 2-4 mm, pulled fast
        ║   up to about 6 mm/min
        ║   100-125 mm long
       ═╩═  dislocations slide to the surface and exit
"#;
const V31_0_SPOTS: &[Spot] = &[
    spot(
        r#"seed (oriented"#,
        0,
        0,
        r#"A small single crystal, orientation set to {100} or {111}. Silicon, not quartz."#,
    ),
    spot(
        r#"dipped into the melt"#,
        0,
        0,
        r#"Thermal shock on contact creates dislocations."#,
    ),
    spot(
        r#"neck 2-4 mm"#,
        0,
        0,
        r#"A thin neck, 2-4 mm in diameter (US 6,866,713)."#,
    ),
    spot(
        r#"up to about 6 mm/min"#,
        0,
        0,
        r#"Fast pulling lets dislocations slide to the surface and leave (US 6,866,713)."#,
    ),
    spot(
        r#"100-125 mm long"#,
        0,
        0,
        r#"That patent gives roughly 100-125 mm of neck."#,
    ),
];

const V31_1_ART: &str = r#"# Load on the neck

  Dash neck limit         ████████ about 100 kg
  300 mm crystal          ████████████████████████ several hundred kg

  fixes: sharp-tipped seed (no Dash neck)
         dash-free neck at 0.5 mm/min or less (US 7,179,330)
"#;
const V31_1_SPOTS: &[Spot] = &[
    spot(
        r#"Dash neck limit"#,
        0,
        TO_EOL,
        r#"About 100 kg per patent text for 200 mm crystals."#,
    ),
    spot(
        r#"300 mm crystal"#,
        0,
        TO_EOL,
        r#"A 300 mm crystal weighs several hundred kg (Wikipedia), far beyond the Dash neck limit."#,
    ),
    spot(
        r#"sharp-tipped seed"#,
        0,
        0,
        r#"A shaped seed that avoids Dash necking is one industry answer."#,
    ),
    spot(
        r#"dash-free neck"#,
        0,
        0,
        r#"A slower neck pulled at 0.5 mm/min or less (US 7,179,330, as cited on this page)."#,
    ),
];

const V31_2_ART: &str = r#"# Two ways a neck fails

  dislocation survives ──▶ runs into the body ──▶ remelt
  neck snaps ──▶ crystal drops into hot silicon
              (the most expensive single failure)

  other patents: slower neck 1.0 to 3.0 mm/min
"#;
const V31_2_SPOTS: &[Spot] = &[
    spot(
        r#"dislocation survives"#,
        0,
        0,
        r#"A dislocation that survives the neck propagates into the body and forces a remelt."#,
    ),
    spot(
        r#"neck snaps"#,
        0,
        0,
        r#"A broken neck drops the whole crystal into the melt, the most expensive single failure."#,
    ),
    spot(
        r#"slower neck"#,
        0,
        0,
        r#"Other patents quote 1.0-3.0 mm/min, for example 2.4 mm/min over 200 mm."#,
    ),
];

const V32_0_ART: &str = r#"# Neck to full diameter

         neck 2-4 mm
            ║
           ╱ ╲
          ╱   ╲   cone: cool the melt slightly,
         ╱     ╲  slow the pull
        ╱       ╲
       │         │ 300 mm body starts
"#;
const V32_0_SPOTS: &[Spot] = &[
    spot(
        r#"neck 2-4 mm"#,
        0,
        0,
        r#"The shoulder starts from the thin neck."#,
    ),
    spot(
        r#"cone"#,
        0,
        0,
        r#"The crystal flares out along a cone as the melt is cooled slightly and the pull slowed."#,
    ),
    spot(
        r#"300 mm body starts"#,
        0,
        0,
        r#"The target diameter for modern wafers."#,
    ),
];

const V32_1_ART: &str = r#"# Control loop

  freezing area grows ──▶ latent heat released at interface
        │
        ▼
  controller trims heater power to hold the shape
  (diameter now set by temperature, not only pull speed)
"#;
const V32_1_SPOTS: &[Spot] = &[
    spot(
        r#"freezing area grows"#,
        0,
        0,
        r#"As the cone widens, more silicon freezes per second."#,
    ),
    spot(
        r#"latent heat"#,
        0,
        0,
        r#"Freezing releases latent heat at the interface (textbook)."#,
    ),
    spot(
        r#"controller trims heater power"#,
        0,
        0,
        r#"Heater power is adjusted continuously to hold the cone shape."#,
    ),
];

const V32_2_ART: &str = r#"# Short vs steep

  shorter, steeper   more usable body per charge
                     risk: new dislocations, twisted crystal
  longer, gentler    safer, more scrap
  at 300 mm the load on the neck climbs through the shoulder
"#;
const V32_2_SPOTS: &[Spot] = &[
    spot(
        r#"shorter, steeper"#,
        0,
        0,
        r#"A steeper cone wastes less silicon in the cut-off cone (textbook flare mechanics)."#,
    ),
    spot(
        r#"longer, gentler"#,
        0,
        0,
        r#"A gentler cone is safer but makes more scrap."#,
    ),
    spot(
        r#"load on the neck"#,
        0,
        0,
        r#"The weight hanging from the neck climbs steadily through this phase, so seed-neck strength limits ingot mass."#,
    ),
];

const V33_0_ART: &str = r#"# Interface shape

  slow pull          too fast
  ──────────         ╲──────╱    or    ╱──────╲
  flat front         concave           convex
  stable, in spec    locks in stress and defects, shifts oxygen

  body: up to about 2 m, several hundred kg
"#;
const V33_0_SPOTS: &[Spot] = &[
    spot(
        r#"slow pull"#,
        0,
        0,
        r#"Around 1.0 to 1.6 mm/min in the examples on this page."#,
    ),
    spot(
        r#"flat front"#,
        0,
        0,
        r#"A flat, stable freezing front is the goal."#,
    ),
    spot(
        r#"too fast"#,
        0,
        0,
        r#"A faster pull bends the interface, locking in stress and defects and shifting oxygen."#,
    ),
    spot(
        r#"up to about 2 m"#,
        0,
        0,
        r#"The body is up to roughly 2 m long and several hundred kg (Wikipedia)."#,
    ),
];

const V33_1_ART: &str = r#"# Mass per hour, 300 mm crystal

  1.0 mm/min   ██████████ 9.9 kg/h
  1.6 mm/min   ████████████████ 15.8 kg/h

  300 kg takes about 19 to 30 hours: roughly a day
  2023 simulation at 1.6: interface moved 33 mm,
  growth time -46.4%, power -4.97% (PV-oriented study)
"#;
const V33_1_SPOTS: &[Spot] = &[
    spot(
        r#"1.0 mm/min"#,
        0,
        TO_EOL,
        r#"Cross-section about 707 cm2 times 0.1 cm/min times 2.33 g/cm3 is about 9.9 kg per hour."#,
    ),
    spot(
        r#"1.6 mm/min"#,
        0,
        TO_EOL,
        r#"The same arithmetic gives about 15.8 kg per hour."#,
    ),
    spot(
        r#"300 kg takes"#,
        0,
        0,
        r#"300 kg divided by 15.8 and 9.9 kg/h is about 19 to 30 hours."#,
    ),
    spot(
        r#"2023 simulation"#,
        0,
        0,
        r#"A PV-oriented 2023 study: interface moved 33 mm, growth time down 46.4%, power down 4.97%."#,
    ),
];

const V33_2_ART: &str = r#"# Knobs running at once

  crystal rotation    +5 rpm   (COMSOL example)
  crucible rotation   -5 rpm   (opposite direction)
  crucible lift       up as the melt level falls
  heater power        trimmed to hold diameter
  magnetic field      horizontal or cusp, calms the melt
"#;
const V33_2_SPOTS: &[Spot] = &[
    spot(
        r#"crystal rotation"#,
        0,
        TO_EOL,
        r#"+5 rpm in the COMSOL example."#,
    ),
    spot(
        r#"crucible rotation"#,
        0,
        TO_EOL,
        r#"-5 rpm: the crucible counter-rotates (COMSOL example)."#,
    ),
    spot(
        r#"crucible lift"#,
        0,
        TO_EOL,
        r#"The crucible rises as the melt level falls, keeping the interface in place."#,
    ),
    spot(
        r#"heater power"#,
        0,
        TO_EOL,
        r#"Power is trimmed to hold diameter."#,
    ),
    spot(
        r#"magnetic field"#,
        0,
        TO_EOL,
        r#"Horizontal or cusp fields are commonly added at 300 mm to calm melt convection (patent descriptions)."#,
    ),
];

const V34_0_ART: &str = r#"# Ending a pull

  body ──▶ taper to an end cone ──▶ lift clear, cool

  abrupt pull-off ──▶ thermal shock
                          │
                          ▼
              slip dislocations run up into the body
  (US 9,988,736 grows the tail to suppress them)
"#;
const V34_0_SPOTS: &[Spot] = &[
    spot(
        r#"taper to an end cone"#,
        0,
        0,
        r#"The diameter is tapered rather than cut off."#,
    ),
    spot(
        r#"abrupt pull-off"#,
        0,
        0,
        r#"Pulling the crystal off the melt abruptly causes thermal shock."#,
    ),
    spot(
        r#"slip dislocations"#,
        0,
        0,
        r#"Slip lines run back up into the body and cost usable length."#,
    ),
    spot(
        r#"US 9,988,736"#,
        0,
        0,
        r#"A patent on growing the tail so as to suppress slip dislocation generation."#,
    ),
];

const V34_1_ART: &str = r#"# Impurities pile up in the liquid

  early freeze ░░░░  cleanest
                ▒▒▒▒
                ▓▓▓▓
  last freeze  ████  richest in dopant and metals

  so the tail cone is cropped off (INGOT step)
"#;
const V34_1_SPOTS: &[Spot] = &[
    spot(
        r#"early freeze"#,
        0,
        0,
        r#"The first silicon to freeze has the lowest impurity and dopant level."#,
    ),
    spot(
        r#"last freeze"#,
        0,
        0,
        r#"The last silicon to freeze is richest in dopants and metals (textbook segregation)."#,
    ),
    spot(
        r#"cropped off"#,
        0,
        0,
        r#"The tail cone is cut off in the INGOT step along with the seed cone."#,
    ),
];

const V34_2_ART: &str = r#"# Non-wafer silicon per pull

  seed end        scrap
  tail cone       scrap
  melt left over  scrap
  slip line up the body: lost body length
"#;
const V34_2_SPOTS: &[Spot] = &[
    spot(
        r#"seed end"#,
        0,
        TO_EOL,
        r#"The seed cone and neck are cropped off."#,
    ),
    spot(
        r#"tail cone"#,
        0,
        TO_EOL,
        r#"The tail cone is cropped off."#,
    ),
    spot(
        r#"melt left over"#,
        0,
        TO_EOL,
        r#"Silicon left in the crucible is not crystal."#,
    ),
    spot(
        r#"slip line"#,
        0,
        TO_EOL,
        r#"A slip that runs far up the body costs usable length."#,
    ),
];

const V35_0_ART: &str = r#"# Crucible cross-section

     ┌─────────────────────┐
     │▓ graphite susceptor ▓│  outside
     │ ┌─────────────────┐ │
     │ │ fused quartz    │ │  inner surface dissolves
     │ │  ≈≈ melt ≈≈     │ │  ──▶ SiO2 + Si ──▶ 2SiO
     │ └─────────────────┘ │  ──▶ oxygen in the crystal
     └─────────────────────┘  about 1e18 atoms per cm3
"#;
const V35_0_SPOTS: &[Spot] = &[
    spot(
        r#"graphite susceptor"#,
        0,
        0,
        r#"Graphite holds the quartz crucible in the hot zone."#,
    ),
    spot(
        r#"fused quartz"#,
        0,
        0,
        r#"High-purity fused quartz, from Spruce Pine quartz."#,
    ),
    spot(
        r#"inner surface dissolves"#,
        0,
        0,
        r#"The melt slowly dissolves the quartz wall."#,
    ),
    spot(
        r#"SiO2 + Si ──▶ 2SiO"#,
        0,
        0,
        r#"Dissolving quartz makes SiO; most evaporates, some freezes into the crystal (textbook)."#,
    ),
    spot(
        r#"about 1e18 atoms per cm3"#,
        0,
        0,
        r#"Oxygen level in the crystal per Wikipedia."#,
    ),
];

const V35_1_ART: &str = r#"# Single point of failure

  Spruce Pine, NC
  Sibelco + Quartz Corp   about 95% of ultra-high-purity quartz
  crucibles               est. 70-90% use Spruce Pine quartz
  Sept 26 2024            Helene halts both producers
  Sibelco                 restarts about two weeks later
"#;
const V35_1_SPOTS: &[Spot] = &[
    spot(
        r#"Sibelco + Quartz Corp"#,
        0,
        0,
        r#"Together about 95% of ultra-high-purity quartz (ABC News / Konvoy)."#,
    ),
    spot(
        r#"crucibles"#,
        0,
        0,
        r#"An estimated 70-90% of polysilicon-melting crucibles use Spruce Pine quartz (Vince Beiser)."#,
    ),
    spot(
        r#"Sept 26 2024"#,
        0,
        0,
        r#"Hurricane Helene halted both producers."#,
    ),
    spot(
        r#"restarts about two weeks later"#,
        0,
        0,
        r#"Commentators expected limited near-term effect because of buffer inventory."#,
    ),
];

const V35_2_ART: &str = r#"# The chain

  quartz ──▶ crucible ──▶ crystal ──▶ wafer ──▶ chip
  cut any link and the chain stops
"#;
const V35_2_SPOTS: &[Spot] = &[
    spot(r#"quartz"#, 0, 0, r#"High-purity quartz from Spruce Pine."#),
    spot(r#"crucible"#, 0, 0, r#"Consumed in each pull."#),
    spot(
        r#"wafer"#,
        0,
        0,
        r#"Every wafer starts as a crystal grown in one of these crucibles."#,
    ),
];

const V36_0_ART: &str = r#"# Flow in the melt

         crystal (cool)
            ║
   ┌────────╨────────┐
   │ ~ ~  interface    │ ◀ buoyancy + rotation flows
   │ ~ ~   ≈≈≈≈≈≈     │
   └──────────────────┘
   hot crucible wall
   result: uneven temperature, growth rate and oxygen
"#;
const V36_0_SPOTS: &[Spot] = &[
    spot(
        r#"crystal (cool)"#,
        0,
        0,
        r#"The crystal is the cool end; the crucible wall is the hot end."#,
    ),
    spot(
        r#"buoyancy + rotation flows"#,
        0,
        0,
        r#"Temperature differences drive buoyancy flow; rotation adds forced convection."#,
    ),
    spot(
        r#"hot crucible wall"#,
        0,
        0,
        r#"The hot wall drives the flow."#,
    ),
    spot(
        r#"uneven temperature, growth rate and oxygen"#,
        0,
        0,
        r#"A 2023 modelling study ties convection to non-uniform temperature, growth rate and oxygen at the interface."#,
    ),
];

const V36_1_ART: &str = r#"# Field types

  HMCZ: horizontal field        cusp field: opposed coils
     ═══▶ ═══▶                     ◀═ ═▶   zero-Gauss plane
  ┌─────────┐                   ┌─────────┐
  │ ≈ melt ≈ │                   │ ≈ melt ≈ │
  └─────────┘                   └─────────┘
  both calm the flow; each maker tunes its own
"#;
const V36_1_SPOTS: &[Spot] = &[
    spot(
        r#"HMCZ"#,
        0,
        0,
        r#"Horizontal-field Czochralski, adopted as 300 mm made melts larger (patent background)."#,
    ),
    spot(
        r#"cusp field"#,
        0,
        0,
        r#"Opposed coils make a cusp field. Each wafer maker tunes its own."#,
    ),
    spot(
        r#"zero-Gauss plane"#,
        0,
        0,
        r#"Its position changes melt convection and oxygen transport (cusp-field study)."#,
    ),
    spot(
        r#"both calm the flow"#,
        0,
        0,
        r#"Molten silicon conducts, so the field acts directly on it and gives a calmer interface."#,
    ),
];

const V36_2_ART: &str = r#"# Gradient along the crystal (COMSOL model)

  near the melt   ████████████████████ 500 C per m
  up the rod      ████ 100 C per m

  calmer interface ──▶ uniform oxygen and dopant ──▶ more in-spec wafers
"#;
const V36_2_SPOTS: &[Spot] = &[
    spot(
        r#"near the melt"#,
        0,
        TO_EOL,
        r#"In the COMSOL model the axial gradient starts at 500 C per metre."#,
    ),
    spot(
        r#"up the rod"#,
        0,
        TO_EOL,
        r#"It drops to 100 C per metre along the rod."#,
    ),
    spot(
        r#"calmer interface"#,
        0,
        0,
        r#"Stable melt flow means uniform oxygen and dopant and a higher yield of in-spec wafers."#,
    ),
];

const V37_0_ART: &str = r#"# Hot zone, outside in

  ┌─────────────────────────┐
  │ graphite felt insulation │
  │ ┌─────────────────────┐ │
  │ │ graphite heater     │ │  310 kW (COMSOL)
  │ │ ┌─────────────────┐ │ │
  │ │ │ susceptor + SiO2│ │ │
  │ │ └─────────────────┘ │ │
  └─┴─┴─────────────────────┘
"#;
const V37_0_SPOTS: &[Spot] = &[
    spot(
        r#"graphite felt insulation"#,
        0,
        0,
        r#"Felt insulation sits outside the heater (textbook)."#,
    ),
    spot(
        r#"graphite heater"#,
        0,
        0,
        r#"A resistive graphite heater surrounds the crucible. The COMSOL model uses 310 kW."#,
    ),
    spot(
        r#"susceptor + SiO2"#,
        0,
        0,
        r#"The graphite susceptor holds the quartz crucible."#,
    ),
    spot(r#"310 kW"#, 0, 0, r#"The COMSOL model's heater power."#),
];

const V37_1_ART: &str = r#"# Graphite vs the melt's vapour

  melt ──▶ SiO ──▶ touches hot graphite ──▶ CO
                                            │
  argon flow down and out ◀─────────────────┘
  carries SiO and CO away from the hot zone
"#;
const V37_1_SPOTS: &[Spot] = &[
    spot(r#"SiO"#, 0, 0, r#"SiO evaporates from the melt."#),
    spot(
        r#"hot graphite"#,
        0,
        0,
        r#"SiO reacts with graphite to form CO, wearing the parts."#,
    ),
    spot(
        r#"argon flow down and out"#,
        0,
        0,
        r#"Argon carries SiO and CO away so they do not return to the melt."#,
    ),
];

const V37_2_ART: &str = r#"# Optimisation target

  base case          power 100%
  1.6 mm/min pull    power 95.03%   (-4.97%, 2023 study)
  but: defects, interface, oxygen trade against power
  hot-zone design = maker's own know-how
"#;
const V37_2_SPOTS: &[Spot] = &[
    spot(
        r#"base case"#,
        0,
        TO_EOL,
        r#"The reference in the 2023 pull-rate study."#,
    ),
    spot(
        r#"1.6 mm/min pull"#,
        0,
        TO_EOL,
        r#"A faster pull cut power use by 4.97% versus the base case."#,
    ),
    spot(
        r#"but: defects"#,
        0,
        0,
        r#"Power is optimised together with defects, not alone."#,
    ),
    spot(
        r#"hot-zone design"#,
        0,
        0,
        r#"Typically proprietary and tuned in-house. Puller makers (PVA TePla, Ferrotec) sell furnaces, but no vendor-specific hot-zone data was found."#,
    ),
];

const V38_0_ART: &str = r#"# Chamber parts

          pull shaft (lift + rotate)
               ║
   ┌───────────╨────────────┐
   │ water-cooled steel     │ ◀ viewing port (diameter camera)
   │   crystal              │
   │   hot zone + melt      │   argon about 2500 Pa (model)
   └───────────┬────────────┘
               ▼ exhaust
"#;
const V38_0_SPOTS: &[Spot] = &[
    spot(r#"pull shaft"#, 0, 0, r#"Lifts and rotates the crystal."#),
    spot(
        r#"water-cooled steel"#,
        0,
        0,
        r#"Water cooling pulls heat out of the crystal and protects the seals."#,
    ),
    spot(
        r#"viewing port"#,
        0,
        0,
        r#"Gives the diameter camera a view of the meniscus."#,
    ),
    spot(
        r#"argon about 2500 Pa"#,
        0,
        0,
        r#"A model value in COMSOL, not a vendor spec."#,
    ),
    spot(
        r#"exhaust"#,
        0,
        0,
        r#"SiO and CO are exhausted downstream, keeping the hot zone clean."#,
    ),
];

const V38_1_ART: &str = r#"# Closed loop (textbook)

  camera reads bright ring at the meniscus
        │
        ▼
  diameter error ──▶ trim heater power + pull speed
        │
        ▼
  diameter held constant
"#;
const V38_1_SPOTS: &[Spot] = &[
    spot(
        r#"camera reads bright ring"#,
        0,
        0,
        r#"An optical sensor reads the bright ring at the meniscus."#,
    ),
    spot(
        r#"diameter error"#,
        0,
        0,
        r#"The controller compares measured and target diameter."#,
    ),
    spot(
        r#"heater power + pull speed"#,
        0,
        0,
        r#"Both are trimmed to keep the diameter constant."#,
    ),
];

const V38_2_ART: &str = r#"# What interrupts a pull

  argon leak       ──▶ contamination, oxygen shifts
  pump issue       ──▶ pressure off spec
  dropped crystal  ──▶ scrapped pull

  300 mm utilisation is full in 2026: puller count caps supply
"#;
const V38_2_SPOTS: &[Spot] = &[
    spot(
        r#"argon leak"#,
        0,
        0,
        r#"A leak breaks the controlled atmosphere (page)."#,
    ),
    spot(
        r#"pump issue"#,
        0,
        0,
        r#"Pump problems upset the pressure and gas flow."#,
    ),
    spot(
        r#"dropped crystal"#,
        0,
        0,
        r#"A dropped crystal scraps the whole pull."#,
    ),
    spot(
        r#"300 mm utilisation is full"#,
        0,
        0,
        r#"GlobalWafers said in August 2026 that its existing 300 mm capacity was at full utilisation (XenoSpectrum)."#,
    ),
];

const V39_0_ART: &str = r#"# Oxygen path

  quartz wall ──▶ SiO2 + Si ──▶ 2SiO
                                 │
              ┌──────────────────┴─────────────┐
              ▼                                ▼
  most: evaporates, swept by argon    some: freezes into the crystal
                                      about 1e18 atoms per cm3
  knobs: crucible rotation, melt depth, pull speed, magnets
"#;
const V39_0_SPOTS: &[Spot] = &[
    spot(
        r#"quartz wall"#,
        0,
        0,
        r#"The crucible's inner surface dissolves into the melt."#,
    ),
    spot(
        r#"SiO2 + Si ──▶ 2SiO"#,
        0,
        0,
        r#"The dissolving reaction (textbook)."#,
    ),
    spot(
        r#"most: evaporates"#,
        0,
        0,
        r#"Most SiO evaporates and is swept away by argon."#,
    ),
    spot(
        r#"about 1e18 atoms per cm3"#,
        0,
        0,
        r#"What remains in the crystal (Wikipedia)."#,
    ),
    spot(
        r#"knobs"#,
        0,
        0,
        r#"Crucible rotation, melt depth, pull speed and magnetic fields tune the level."#,
    ),
];

const V39_1_ART: &str = r#"# Two faces of oxygen (textbook)

  too much / uneven    precipitates and defects hurt devices
  controlled           stronger bulk
                       traps metals away from the surface (gettering)
  logic: defined mid-range, tight uniformity
  power and memory: different targets
"#;
const V39_1_SPOTS: &[Spot] = &[
    spot(
        r#"too much / uneven"#,
        0,
        TO_EOL,
        r#"Oxygen can form precipitates and defects that hurt devices."#,
    ),
    spot(
        r#"controlled"#,
        0,
        0,
        r#"It strengthens the bulk and traps metals away from the device surface (gettering)."#,
    ),
    spot(
        r#"logic: defined"#,
        0,
        TO_EOL,
        r#"Many logic wafers want a defined mid-range level and tight uniformity."#,
    ),
    spot(
        r#"power and memory"#,
        0,
        TO_EOL,
        r#"Different products have different oxygen targets."#,
    ),
];

const V39_2_ART: &str = r#"# Drift along the pull

  start   deep melt, big wall area     oxygen high
  middle  melt falls                   oxygen drifts
  end     shallow melt                 oxygen low
  fix: schedule crucible rotation + magnetic field
  (direction illustrative; the page says it drifts)
"#;
const V39_2_SPOTS: &[Spot] = &[
    spot(
        r#"start"#,
        0,
        TO_EOL,
        r#"Large wall area contacts a deep melt early in the pull."#,
    ),
    spot(
        r#"middle"#,
        0,
        TO_EOL,
        r#"As melt depth falls, oxygen drifts along the crystal."#,
    ),
    spot(
        r#"fix:"#,
        0,
        TO_EOL,
        r#"Crucible rotation and the magnetic field are scheduled to hold the level."#,
    ),
];

const V40_0_ART: &str = r#"# Dislocations leave through the side

    ║  seed
   ─╨─
    ║   dislocation slips along an inclined plane
    ║  ╱
    ║ ╱  reaches the surface ──▶ exits
   ═╩═  clean crystal continues below
"#;
const V40_0_SPOTS: &[Spot] = &[
    spot(r#"seed"#, 0, 0, r#"The seed is narrowed to 2-4 mm."#),
    spot(
        r#"dislocation slips"#,
        0,
        0,
        r#"Dislocations follow slip planes at an angle."#,
    ),
    spot(
        r#"exits"#,
        0,
        0,
        r#"In a thin, fast-pulled neck they reach the side and leave the crystal."#,
    ),
    spot(
        r#"clean crystal continues"#,
        0,
        0,
        r#"About 100-125 mm of neck purges them (US 6,866,713)."#,
    ),
];

const V40_1_ART: &str = r#"# Weak link

  Dash neck 2-4 mm carries the whole crystal
  limit about 100 kg  (200 mm crystals, patent text)
  300 mm ingot: well over that
  ──▶ newer methods: shaped seed, dash-free neck
"#;
const V40_1_SPOTS: &[Spot] = &[
    spot(
        r#"Dash neck 2-4 mm"#,
        0,
        0,
        r#"The neck carries the whole crystal's weight."#,
    ),
    spot(
        r#"limit about 100 kg"#,
        0,
        0,
        r#"Patent text for 200 mm crystals."#,
    ),
    spot(
        r#"300 mm ingot"#,
        0,
        0,
        r#"Several hundred kg (Wikipedia), far beyond the Dash limit."#,
    ),
    spot(
        r#"shaped seed"#,
        0,
        0,
        r#"Industry answers include shaped seeds that avoid Dash necking, and slower dash-free necks (0.5 mm/min or less, US 7,179,330)."#,
    ),
];

const V40_2_ART: &str = r#"# Pull rate, mm/min (examples from the page)

  Dash max         ████████████████████████ 6.0
  neck example     ██████████ 2.4
  300 mm body      ██████ 1.6
  dash-free neck   ██ 0.5 or less
"#;
const V40_2_SPOTS: &[Spot] = &[
    spot(
        r#"Dash max"#,
        0,
        TO_EOL,
        r#"As high as 6 mm/min (US 6,866,713)."#,
    ),
    spot(
        r#"neck example"#,
        0,
        TO_EOL,
        r#"One patent example is 2.4 mm/min over 200 mm."#,
    ),
    spot(
        r#"300 mm body"#,
        0,
        TO_EOL,
        r#"Body growth examples on this page are 1.0-1.6 mm/min."#,
    ),
    spot(
        r#"dash-free neck"#,
        0,
        TO_EOL,
        r#"0.5 mm/min or less (US 7,179,330, as cited)."#,
    ),
];

const V41_0_ART: &str = r#"# 300 mm wafer share, 2024 (Report Prime, low reliability)

  Shin-Etsu 4063.T  █████████████████████████████ 26.7%
  SUMCO 3436.T      ███████████████████████████ 25.0%
  other sources: the two together exceed 55%
"#;
const V41_0_SPOTS: &[Spot] = &[
    spot(
        r#"Shin-Etsu 4063.T"#,
        0,
        TO_EOL,
        r#"26.7% in the Report Prime 2024 estimate (low reliability)."#,
    ),
    spot(
        r#"SUMCO 3436.T"#,
        0,
        TO_EOL,
        r#"25.0% in the same estimate."#,
    ),
    spot(
        r#"exceed 55%"#,
        0,
        0,
        r#"Other sources say the two together hold more than 55% of 300 mm wafers."#,
    ),
];

const V41_1_ART: &str = r#"# 2025 to 2026

  2025 shipments   12,973 M sq in   +5.8%   (SEMI)
  2025 revenue     $11.4B           -1.2%
  growth from      advanced epi (logic), polished (HBM)
  Jan 2026         SUMCO raises 300 mm forecast 12% (report)
  Aug 2026         GlobalWafers: 300 mm at full utilisation
"#;
const V41_1_SPOTS: &[Spot] = &[
    spot(
        r#"2025 shipments"#,
        0,
        TO_EOL,
        r#"SEMI: shipments rose 5.8% to 12,973 million square inches."#,
    ),
    spot(
        r#"2025 revenue"#,
        0,
        TO_EOL,
        r#"Revenue fell 1.2% to $11.4B."#,
    ),
    spot(
        r#"growth from"#,
        0,
        TO_EOL,
        r#"Advanced epitaxial wafers for logic and polished wafers for HBM drove growth."#,
    ),
    spot(
        r#"Jan 2026"#,
        0,
        TO_EOL,
        r#"A report says SUMCO raised its 2026 300 mm shipment forecast by 12%."#,
    ),
    spot(
        r#"Aug 2026"#,
        0,
        TO_EOL,
        r#"GlobalWafers said existing 300 mm capacity is at full utilisation, tied to AI demand."#,
    ),
];

const V41_2_ART: &str = r#"# Why prices can rise

  tight pullers ─┐
                 ├──▶ pricing power
  long qualification ─┘
  claim: +18 to 22% on AI-dedicated wafers (one source, unconfirmed)
"#;
const V41_2_SPOTS: &[Spot] = &[
    spot(
        r#"tight pullers"#,
        0,
        0,
        r#"Puller count caps 300 mm supply."#,
    ),
    spot(
        r#"long qualification"#,
        0,
        0,
        r#"Chipmakers take years to qualify a wafer supplier."#,
    ),
    spot(
        r#"pricing power"#,
        0,
        0,
        r#"Together these give wafer makers pricing power."#,
    ),
    spot(
        r#"+18 to 22%"#,
        0,
        0,
        r#"A single source claims this on AI-dedicated wafers. It is unconfirmed."#,
    ),
];

const V42_0_ART: &str = r#"# Where a pull loses value

  thermal shock     ──▶ slip dislocations
  neck failure      ──▶ crystal drops
  loss of zero-dislocation state ──▶ remelt and restart
  diameter excursion ──▶ out-of-spec length
  cost: puller time, poly, crucible, power
"#;
const V42_0_SPOTS: &[Spot] = &[
    spot(
        r#"thermal shock"#,
        0,
        0,
        r#"Slip dislocations from thermal shock cost body length."#,
    ),
    spot(
        r#"neck failure"#,
        0,
        0,
        r#"A broken neck drops the crystal into the melt."#,
    ),
    spot(
        r#"loss of zero-dislocation"#,
        0,
        0,
        r#"A dislocation anywhere in the body means the affected length is lost, often with a remelt."#,
    ),
    spot(
        r#"diameter excursion"#,
        0,
        0,
        r#"Diameter drift puts length out of spec."#,
    ),
    spot(
        r#"cost:"#,
        0,
        0,
        r#"A ruined pull wastes puller time, poly, crucible and power."#,
    ),
];

const V42_1_ART: &str = r#"# SEMI wafer data

  2023 revenue   $12.3B  (-10.9%)    2023 area  12,602 M sq in (-14.3%)
  2025 revenue   $11.4B  (-1.2%)     2025 area  12,973 M sq in (+5.8%)
  AI logic and HBM wafers are tight; the rest lags
"#;
const V42_1_SPOTS: &[Spot] = &[
    spot(
        r#"2023 revenue"#,
        0,
        0,
        r#"SEMI: 2023 silicon wafer revenue fell 10.9% to $12.3B."#,
    ),
    spot(
        r#"2025 revenue"#,
        0,
        0,
        r#"2025 revenue was $11.4B, down 1.2%."#,
    ),
    spot(
        r#"AI logic and HBM"#,
        0,
        0,
        r#"Advanced epitaxial logic and HBM polished wafers sell tight while mature demand lags."#,
    ),
];

const V42_2_ART: &str = r#"# Active patent areas

  tail slip dislocations   US 9,988,736
  neck dislocation removal US 5,628,823, US 6,080,237
  margin: yield x utilisation; a lost crystal = lost revenue
"#;
const V42_2_SPOTS: &[Spot] = &[
    spot(
        r#"tail slip"#,
        0,
        TO_EOL,
        r#"US 9,988,736 addresses growing the tail to suppress slip."#,
    ),
    spot(
        r#"neck dislocation removal"#,
        0,
        TO_EOL,
        r#"US 5,628,823 and US 6,080,237 address removing neck dislocations."#,
    ),
    spot(
        r#"margin:"#,
        0,
        TO_EOL,
        r#"When 300 mm lines are full, each lost crystal costs real revenue."#,
    ),
];

const V43_0_ART: &str = r#"# As-pulled crystal

         ║  neck
        ╱ ╲  seed cone
       ╱   ╲
      ┌─────┐
      │     │  body, a bit over 300 mm
      │     │  up to about 2 m, several hundred kg
      └─────┘
       ╲   ╱
        ╲ ╱   tail cone
         ╵
"#;
const V43_0_SPOTS: &[Spot] = &[
    spot(r#"neck"#, 0, 0, r#"The seed end carries the thin neck."#),
    spot(
        r#"seed cone"#,
        0,
        0,
        r#"The shoulder cone is cropped off later."#,
    ),
    spot(
        r#"body, a bit over 300 mm"#,
        0,
        0,
        r#"Deliberately slightly oversize so it can be ground to a true 300 mm."#,
    ),
    spot(
        r#"up to about 2 m"#,
        0,
        0,
        r#"Up to about 2 m long (Wikipedia)."#,
    ),
    spot(
        r#"tail cone"#,
        0,
        0,
        r#"The last frozen section, also cropped off."#,
    ),
];

const V43_1_ART: &str = r#"# Weight and risk

  300 mm crystal   ████████ several hundred kg
  450 mm crystal   ████████████████████ about 1 tonne (program dropped)

  built-in thermal stress ──▶ a crack scraps the lot
"#;
const V43_1_SPOTS: &[Spot] = &[
    spot(
        r#"300 mm crystal"#,
        0,
        TO_EOL,
        r#"Several hundred kg (Wikipedia)."#,
    ),
    spot(
        r#"450 mm crystal"#,
        0,
        TO_EOL,
        r#"A 450 mm crystal would have weighed about 1 tonne, one reason that program was dropped."#,
    ),
    spot(
        r#"built-in thermal stress"#,
        0,
        0,
        r#"The thermal gradient it grew in leaves residual stress, and a crack scraps the whole ingot."#,
    ),
];

const V43_2_ART: &str = r#"# Where the bottleneck sits

  crystal growth ━━━━▶ ingot ━━━▶ sawing ━━▶ wafers
  bottleneck: pullers (full utilisation, Aug 2026)
"#;
const V43_2_SPOTS: &[Spot] = &[
    spot(
        r#"crystal growth"#,
        0,
        0,
        r#"Pulling is the slow, capital-heavy step."#,
    ),
    spot(
        r#"bottleneck: pullers"#,
        0,
        0,
        r#"GlobalWafers said in August 2026 its existing 300 mm capacity is at full utilisation, tied to AI demand."#,
    ),
    spot(
        r#"sawing"#,
        0,
        0,
        r#"Sawing is faster than growing, so it is not the limit."#,
    ),
];

const V44_0_ART: &str = r#"# Where the cuts fall

   seed cone + neck   |   body kept   |   tail cone
        ✂ cut off ─────┘               └───── cut off ✂

  off-cuts: recycled as feedstock or sold to solar (textbook)
"#;
const V44_0_SPOTS: &[Spot] = &[
    spot(
        r#"seed cone + neck"#,
        0,
        0,
        r#"Cut off first, along with its neck."#,
    ),
    spot(
        r#"body kept"#,
        0,
        0,
        r#"The cylinder between the cuts goes on to grinding and slicing."#,
    ),
    spot(r#"tail cone"#, 0, 0, r#"Cut off at the other end."#),
    spot(
        r#"recycled as feedstock"#,
        0,
        0,
        r#"Scrap can be recycled as feedstock or sold into solar (textbook)."#,
    ),
];

const V44_1_ART: &str = r#"# Crop length trade-off

  longer crop   cleaner wafers, fewer per ingot
  shorter crop  more wafers, risk of bad ones
  set by measuring each crystal (textbook)
"#;
const V44_1_SPOTS: &[Spot] = &[
    spot(
        r#"longer crop"#,
        0,
        TO_EOL,
        r#"Cleaner wafers but fewer per ingot."#,
    ),
    spot(
        r#"shorter crop"#,
        0,
        TO_EOL,
        r#"More wafers, but marginal zones may slip through."#,
    ),
    spot(
        r#"set by measuring"#,
        0,
        0,
        r#"Cut positions follow measurement of each crystal."#,
    ),
];

const V44_2_ART: &str = r#"# Cost of a miss

  defect zone not cropped ──▶ slicing ──▶ inspection finds it
                                  │
                                  ▼
                   saw time and wire already spent
  wafers per pull: no number found in sources
"#;
const V44_2_SPOTS: &[Spot] = &[
    spot(
        r#"defect zone not cropped"#,
        0,
        0,
        r#"A missed zone passes into the kept body."#,
    ),
    spot(
        r#"inspection finds it"#,
        0,
        0,
        r#"It is found only at slicing or inspection."#,
    ),
    spot(
        r#"saw time and wire"#,
        0,
        0,
        r#"The cost is already sunk by then."#,
    ),
    spot(
        r#"no number found"#,
        0,
        0,
        r#"No source here quantifies wafers per pull."#,
    ),
];

const V45_0_ART: &str = r#"# Cut-face test

  cut face ──▶ X-ray diffraction ──▶ plane matches the seed?
                                       │
                                       ▼
                       notch tolerance: <110> +/- 1 degree
  also checked: doping type, resistivity
"#;
const V45_0_SPOTS: &[Spot] = &[
    spot(
        r#"cut face"#,
        0,
        0,
        r#"Samples come from the cut faces after cropping."#,
    ),
    spot(
        r#"X-ray diffraction"#,
        0,
        0,
        r#"Orientation is checked against the intended Miller plane."#,
    ),
    spot(
        r#"<110> +/- 1 degree"#,
        0,
        0,
        r#"The vendor-datasheet notch tolerance, so the angular error budget is tight."#,
    ),
    spot(
        r#"doping type, resistivity"#,
        0,
        0,
        r#"Also confirmed before the ingot is committed to grinding and slicing."#,
    ),
];

const V45_1_ART: &str = r#"# Which plane faces up

  {100}   logic and CMOS (the standard)
  {111}   bipolar, power, MEMS
  set by the seed in MELT + PULL; a mis-seeded crystal shows up here
"#;
const V45_1_SPOTS: &[Spot] = &[
    spot(
        r#"{100}"#,
        0,
        TO_EOL,
        r#"The standard for logic and CMOS (Wikipedia infobox)."#,
    ),
    spot(
        r#"{111}"#,
        0,
        TO_EOL,
        r#"Used for bipolar, power and MEMS."#,
    ),
    spot(
        r#"set by the seed"#,
        0,
        0,
        r#"A wrong seed orientation is discovered at this test."#,
    ),
];

const V45_2_ART: &str = r#"# Cost of rejecting later

  reject here        ingot only
  reject after saw   saw time + wire wasted
  qualification of a wafer supplier takes years (page text)
  resistivity: four-point probe on a slice (textbook, unsourced)
"#;
const V45_2_SPOTS: &[Spot] = &[
    spot(
        r#"reject here"#,
        0,
        TO_EOL,
        r#"Cheapest: only the ingot is lost."#,
    ),
    spot(
        r#"reject after saw"#,
        0,
        TO_EOL,
        r#"Saw time and wire are wasted as well."#,
    ),
    spot(
        r#"qualification of a wafer supplier"#,
        0,
        0,
        r#"Customers audit these specs during qualification, which takes years (page text)."#,
    ),
    spot(
        r#"four-point probe"#,
        0,
        0,
        r#"Textbook method for resistivity; the page found no source for this step."#,
    ),
];

const V46_0_ART: &str = r#"# Oversize to true

   as pulled            ground
    ╭───────╮          ┌───────┐
   (  wavy   )  ──▶    │ 300mm │  +/- 0.2 mm
    ╰───────╯          └───────┘
   diamond wheel, ingot turning between centres (textbook)
"#;
const V46_0_SPOTS: &[Spot] = &[
    spot(r#"as pulled"#, 0, 0, r#"Slightly oversize and not round."#),
    spot(
        r#"300mm"#,
        0,
        0,
        r#"The finished cylinder meets the 300 mm spec."#,
    ),
    spot(
        r#"+/- 0.2 mm"#,
        0,
        0,
        r#"Vendor datasheet tolerance for the finished wafer."#,
    ),
    spot(
        r#"diamond wheel"#,
        0,
        0,
        r#"Textbook process: a bonded-diamond wheel, coolant, ingot rotating between centres."#,
    ),
];

const V46_1_ART: &str = r#"# Everything downstream assumes 300 mm

  robots ─┐
  FOUPs  ─┼──▶ expect 300 mm +/- 0.2
  tools  ─┘
  grinding also removes the outer skin from the hot zone
"#;
const V46_1_SPOTS: &[Spot] = &[
    spot(
        r#"robots"#,
        0,
        0,
        r#"Wafer-handling robots assume the standard diameter."#,
    ),
    spot(
        r#"FOUPs"#,
        0,
        0,
        r#"Wafer carriers (FOUPs) are built for 300 mm."#,
    ),
    spot(r#"tools"#, 0, 0, r#"Every downstream tool assumes it."#),
    spot(
        r#"outer skin"#,
        0,
        0,
        r#"The surface layer grew in contact with the hot zone and may carry contamination."#,
    ),
];

const V46_2_ART: &str = r#"# Loss and failure

  tighter as-grown diameter ──▶ less grind time, less silicon lost
  failure modes: chipping at the ends, wheel wear ──▶ taper
"#;
const V46_2_SPOTS: &[Spot] = &[
    spot(
        r#"tighter as-grown diameter"#,
        0,
        0,
        r#"Less oversize means less to grind off."#,
    ),
    spot(
        r#"chipping at the ends"#,
        0,
        0,
        r#"A grinding failure mode."#,
    ),
    spot(
        r#"wheel wear"#,
        0,
        0,
        r#"A worn wheel leaves a tapered cylinder."#,
    ),
];

const V47_0_ART: &str = r#"# Notch cross-section (vendor datasheet)

        ╲        ╱
         ╲      ╱     wafer edge
          ╲    ╱
           ╲  ╱  <---- 90 degree included angle
            ╲╱         depth 1.0 mm (+0.25 / -0.00)
       on <110>, +/- 1 degree
"#;
const V47_0_SPOTS: &[Spot] = &[
    spot(
        r#"90 degree included angle"#,
        0,
        0,
        r#"From a vendor datasheet."#,
    ),
    spot(r#"depth 1.0 mm"#, 0, 0, r#"Depth 1.0 mm (+0.25 / -0.00)."#),
    spot(
        r#"<110>"#,
        0,
        0,
        r#"The notch sits on the <110> direction with +/- 1 degree tolerance."#,
    ),
];

const V47_1_ART: &str = r#"# Notch ties the fab to the lattice

  notch ──▶ <110> ──▶ cleavage planes of a {100} wafer
     │
     ▼
  tools align the wafer by it, litho to dicing
  (textbook)
"#;
const V47_1_SPOTS: &[Spot] = &[
    spot(
        r#"notch"#,
        0,
        0,
        r#"A tiny mark that fixes the wafer's crystal direction."#,
    ),
    spot(
        r#"cleavage planes"#,
        0,
        0,
        r#"Silicon cleaves along {110}-family directions in a {100} wafer (textbook)."#,
    ),
    spot(
        r#"tools align"#,
        0,
        0,
        r#"Lithography through dicing use the notch for alignment."#,
    ),
];

const V47_2_ART: &str = r#"# What the notch does and does not say

  200 mm and up   one notch, wastes less area than flats
  notch shows     <110> direction
  notch does NOT show doping type (check by test)
  450 mm plan     notchless, laser mark
"#;
const V47_2_SPOTS: &[Spot] = &[
    spot(
        r#"200 mm and up"#,
        0,
        TO_EOL,
        r#"A single notch replaces flats at 200 mm and above."#,
    ),
    spot(r#"notch shows"#, 0, TO_EOL, r#"It marks <110>."#),
    spot(
        r#"notch does NOT show"#,
        0,
        TO_EOL,
        r#"Doping type must be checked by test."#,
    ),
    spot(
        r#"450 mm plan"#,
        0,
        TO_EOL,
        r#"450 mm wafers were planned to be notchless with a laser mark."#,
    ),
];

const V48_0_ART: &str = r#"# Wire web

     guide roller ◯════════════════◯ guide roller
                  ═════ wire web ═════   (many parallel wire segments)
                       ▼ ▼ ▼ ▼
                  ┌───────────────┐
                  │     ingot     │ fed downward
                  └───────┬───────┘
                      mounting beam
"#;
const V48_0_SPOTS: &[Spot] = &[
    spot(
        r#"guide roller"#,
        0,
        0,
        r#"Grooved rollers hold the wire at a set pitch, which sets thickness plus kerf."#,
    ),
    spot(
        r#"wire web"#,
        0,
        0,
        r#"One long wire wound back and forth forms many parallel cutting segments."#,
    ),
    spot(
        r#"ingot"#,
        0,
        0,
        r#"The ingot is fed down through the web and cut into wafers all at once."#,
    ),
    spot(
        r#"mounting beam"#,
        0,
        0,
        r#"The ingot is bonded to a beam that holds it during the cut."#,
    ),
];

const V48_1_ART: &str = r#"# Kerf, solar-wafer numbers (no 300 mm figure found)

  slurry wire     ███████████████ about 150 um
  diamond wire    ████████████▌ about 125 um   (about 2x faster)
  path to         ████████▌ about 85 um
"#;
const V48_1_SPOTS: &[Spot] = &[
    spot(
        r#"slurry wire"#,
        0,
        TO_EOL,
        r#"About 150 um kerf for slurry sawing (TaiyangNews/ITRPV, solar)."#,
    ),
    spot(
        r#"diamond wire"#,
        0,
        TO_EOL,
        r#"About 125 um kerf and about 2x faster than slurry (solar)."#,
    ),
    spot(
        r#"path to"#,
        0,
        TO_EOL,
        r#"ITRPV roadmap path to about 85 um."#,
    ),
];

const V48_2_ART: &str = r#"# Wafers per ingot

  wafers = ingot length / (thickness + kerf)   (textbook)

  | wafer | kerf | wafer | kerf | wafer |
  thinner wire ──▶ smaller kerf ──▶ more wafers per ingot
"#;
const V48_2_SPOTS: &[Spot] = &[
    spot(
        r#"wafers = ingot length"#,
        0,
        0,
        r#"Textbook arithmetic: each wafer uses its thickness plus one kerf of length."#,
    ),
    spot(
        r#"| wafer | kerf | wafer"#,
        0,
        0,
        r#"Each wafer uses its own thickness plus one kerf slot of the ingot's length."#,
    ),
    spot(
        r#"thinner wire"#,
        0,
        0,
        r#"Thinner wire cuts a smaller kerf, a direct yield gain (but weaker wire breaks more)."#,
    ),
];

const V49_0_ART: &str = r#"# Layout of a crystal

   seed cone + neck │ ground body, 300 mm │ tail cone
                    ↑                     ↑
                crop line             crop line
  seed side: dislocation-free start limits it
  tail side: dopant build-up and end taper limit it
"#;
const V49_0_SPOTS: &[Spot] = &[
    spot(
        r#"seed cone + neck"#,
        0,
        0,
        r#"Outside the first crop line."#,
    ),
    spot(
        r#"ground body, 300 mm"#,
        0,
        0,
        r#"The usable body between the lines."#,
    ),
    spot(r#"tail cone"#, 0, 0, r#"Outside the second crop line."#),
    spot(
        r#"seed side:"#,
        0,
        TO_EOL,
        r#"Limited by the dislocation-free start."#,
    ),
    spot(
        r#"tail side:"#,
        0,
        TO_EOL,
        r#"Limited by dopant build-up and the end taper."#,
    ),
];

const V49_1_ART: &str = r#"# Measure, then cut

  measure resistivity at the cut face
        │
        ▼
  out of spec? remove more ──▶ in spec: stop
  (textbook)
"#;
const V49_1_SPOTS: &[Spot] = &[
    spot(
        r#"measure resistivity"#,
        0,
        0,
        r#"Resistivity at the cut face tells where the crystal is in spec."#,
    ),
    spot(
        r#"out of spec?"#,
        0,
        0,
        r#"If not in spec, more is removed."#,
    ),
    spot(
        r#"in spec: stop"#,
        0,
        0,
        r#"Cutting stops at the first in-spec face."#,
    ),
];

const V49_2_ART: &str = r#"# The dial

  conservative crop ──▶ more silicon lost
  aggressive crop   ──▶ marginal wafers shipped
                         └─▶ customer audits: relationship risk
"#;
const V49_2_SPOTS: &[Spot] = &[
    spot(
        r#"conservative crop"#,
        0,
        0,
        r#"More silicon lost per ingot."#,
    ),
    spot(
        r#"aggressive crop"#,
        0,
        0,
        r#"Marginal wafers can reach customers."#,
    ),
    spot(
        r#"customer audits"#,
        0,
        0,
        r#"Qualification takes years, so a poor batch puts the relationship at risk (page text)."#,
    ),
];

const V50_0_ART: &str = r#"# Last to freeze, dirtiest

   body         clean
   ...
   tail cone    ▓▓▓▓▓ highest dopant and impurity levels
                       (page: "defects, impurities")
"#;
const V50_0_SPOTS: &[Spot] = &[
    spot(
        r#"body"#,
        0,
        0,
        r#"The body freezes earlier, from cleaner liquid."#,
    ),
    spot(
        r#"tail cone"#,
        0,
        0,
        r#"Segregation leaves the highest dopant and impurity levels here (textbook)."#,
    ),
    spot(
        r#"defects, impurities"#,
        0,
        0,
        r#"The page labels the tail end this way."#,
    ),
];

const V50_1_ART: &str = r#"# What a slip costs

  tail pulled off too fast ──▶ slip line runs up the body
                                  │
                                  ▼
                      longer slip = more body lost
  US 9,988,736: grow the tail to suppress slip
"#;
const V50_1_SPOTS: &[Spot] = &[
    spot(
        r#"tail pulled off too fast"#,
        0,
        0,
        r#"Too fast a pull-off thermally shocks the crystal."#,
    ),
    spot(r#"slip line"#, 0, 0, r#"Slip lines run up into the body."#),
    spot(
        r#"US 9,988,736"#,
        0,
        0,
        r#"Describes growing the tail so as to suppress slip dislocation generation."#,
    ),
];

const V50_2_ART: &str = r#"# What better tail control buys

  shorter taper + fewer slips ──▶ less scrap
                                  └─▶ more wafers per kg of polysilicon
"#;
const V50_2_SPOTS: &[Spot] = &[
    spot(
        r#"shorter taper"#,
        0,
        0,
        r#"Less taper length means less silicon scrapped."#,
    ),
    spot(
        r#"less scrap"#,
        0,
        0,
        r#"Reduced waste directly raises usable silicon per pull."#,
    ),
    spot(
        r#"more wafers per kg"#,
        0,
        0,
        r#"Polysilicon is the scarce input."#,
    ),
];

const V51_0_ART: &str = r#"# Ingot on the beam

       ┌────────────────────┐
       │       ingot        │
       └────────────────────┘
       ░░░░░░ glue ░░░░░░░░░░
       ████ mounting beam ███   wires cut into the beam at the end
"#;
const V51_0_SPOTS: &[Spot] = &[
    spot(
        r#"ingot"#,
        0,
        0,
        r#"Held during the cut so wafers stay aligned."#,
    ),
    spot(
        r#"glue"#,
        0,
        0,
        r#"Quality matters: a weak bond lets wafers shift or fall; a stiff bond that does not release cleanly can crack wafers (textbook)."#,
    ),
    spot(
        r#"mounting beam"#,
        0,
        0,
        r#"A consumable: the wires cut into it at the end."#,
    ),
];

const V51_1_ART: &str = r#"# Thickness spec (vendor sheets)

  target       775 um
  tolerance    +/- 25 um   (a drawing shows +/- 20 um)
  held along the whole ingot, beam as reference
"#;
const V51_1_SPOTS: &[Spot] = &[
    spot(r#"target"#, 0, TO_EOL, r#"775 um for 300 mm wafers."#),
    spot(
        r#"tolerance"#,
        0,
        TO_EOL,
        r#"+/- 25 um in vendor sheets; a drawing shows +/- 20 um."#,
    ),
    spot(
        r#"beam as reference"#,
        0,
        0,
        r#"The saw holds thickness along the ingot length relative to the beam."#,
    ),
];

const V51_2_ART: &str = r#"# Before bonding (textbook)

  X-ray find the crystal planes ──▶ align ingot to the beam ──▶ glue
  beam angle sets the wafer's crystal angle
"#;
const V51_2_SPOTS: &[Spot] = &[
    spot(
        r#"X-ray"#,
        0,
        0,
        r#"Textbook practice: the planes are found by X-ray before bonding."#,
    ),
    spot(
        r#"align ingot"#,
        0,
        0,
        r#"Orientation relative to the beam sets the wafer's crystal angle."#,
    ),
    spot(
        r#"glue"#,
        0,
        0,
        r#"Bonding fixes the alignment for the whole cut."#,
    ),
];

const V52_0_ART: &str = r#"# Which face is up

  {100}  cube face       logic, CMOS (standard)
  {111}  diagonal face   bipolar, power, MEMS
  set by the seed in MELT + PULL, verified in TEST
"#;
const V52_0_SPOTS: &[Spot] = &[
    spot(r#"{100}"#, 0, 0, r#"Standard for logic and CMOS."#),
    spot(r#"{111}"#, 0, 0, r#"Used for bipolar, power and MEMS."#),
    spot(
        r#"set by the seed"#,
        0,
        0,
        r#"The seed crystal in MELT + PULL sets orientation; the TEST step verifies it."#,
    ),
];

const V52_1_ART: &str = r#"# Interface traps (textbook)

  {100}/SiO2   low trap density   ──▶ good transistors
  {111}/SiO2   higher trap density ──▶ fine for some power and MEMS
"#;
const V52_1_SPOTS: &[Spot] = &[
    spot(
        r#"{100}/SiO2"#,
        0,
        TO_EOL,
        r#"Low density of interface traps gives good transistor behaviour (textbook)."#,
    ),
    spot(
        r#"{111}/SiO2"#,
        0,
        TO_EOL,
        r#"Higher trap density, but attractive for some power and MEMS uses."#,
    ),
    spot(
        r#"good transistors"#,
        0,
        0,
        r#"Low interface-trap density is what makes {100} the choice for CMOS (textbook)."#,
    ),
];

const V52_2_ART: &str = r#"# A design constant

  every AI accelerator, HBM stack, CPU die: {100} wafers
  notch on <110>  +/- 1 degree
  governing standard: SEMI M1 (tables not fetched)
"#;
const V52_2_SPOTS: &[Spot] = &[
    spot(
        r#"every AI accelerator"#,
        0,
        0,
        r#"The whole industry designs for this orientation."#,
    ),
    spot(
        r#"notch on <110>"#,
        0,
        0,
        r#"Tolerance +/- 1 degree (vendor datasheet)."#,
    ),
    spot(
        r#"SEMI M1"#,
        0,
        0,
        r#"The governing standard for polished single-crystal silicon wafers. Its tables were not fetched."#,
    ),
];

const V53_0_ART: &str = r#"# Dopants in the melt

  doping range: 1e13 to 1e16 atoms per cm3
  boron       ──▶ p-type
  phosphorus  ──▶ n-type
  arsenic, antimony ──▶ low-resistivity substrates (textbook)
  sets: conductivity type and resistivity
"#;
const V53_0_SPOTS: &[Spot] = &[
    spot(r#"boron"#, 0, 0, r#"p-type dopant (textbook)."#),
    spot(r#"phosphorus"#, 0, 0, r#"n-type dopant (textbook)."#),
    spot(
        r#"arsenic, antimony"#,
        0,
        0,
        r#"Heavier dopants used for low-resistivity substrates (textbook)."#,
    ),
    spot(
        r#"1e13 to 1e16"#,
        0,
        0,
        r#"Doping range per Wikipedia, in atoms per cm3."#,
    ),
];

const V53_1_ART: &str = r#"# Concentration along the crystal

  head ░░░░▒▒▒▒▓▓▓▓████ tail
       less doped      more doped
  wafers then binned by measured resistivity
"#;
const V53_1_SPOTS: &[Spot] = &[
    spot(r#"head"#, 0, 0, r#"The head is less doped."#),
    spot(
        r#"tail"#,
        0,
        0,
        r#"Dopant concentrates in the liquid, so the tail is more doped (textbook)."#,
    ),
    spot(
        r#"binned by measured resistivity"#,
        0,
        0,
        r#"Wafers are sorted into customer resistivity bins."#,
    ),
];

const V53_2_ART: &str = r#"# Spec points

  purity            above 99.9999%
  transition metals below parts per billion
  metals hurt: deep traps and leakage in transistors
  failure: out-of-range resistivity at the crystal ends
"#;
const V53_2_SPOTS: &[Spot] = &[
    spot(r#"purity"#, 0, TO_EOL, r#"Above 99.9999% (Wikipedia)."#),
    spot(
        r#"transition metals"#,
        0,
        TO_EOL,
        r#"Below parts per billion."#,
    ),
    spot(
        r#"metals hurt"#,
        0,
        TO_EOL,
        r#"Metals create deep traps and leakage in transistors."#,
    ),
    spot(
        r#"failure:"#,
        0,
        TO_EOL,
        r#"Out-of-range resistivity at the ends, or radial variation if the interface is not flat."#,
    ),
];

const V54_0_ART: &str = r#"# Thickness by wafer size (um)

  100 mm   ███████████████ 525
  150 mm   ███████████████████ 675
  200 mm   █████████████████████ 725
  300 mm   ██████████████████████ 775
  450 mm   ██████████████████████████ 925 (cancelled)
"#;
const V54_0_SPOTS: &[Spot] = &[
    spot(
        r#"100 mm"#,
        0,
        TO_EOL,
        r#"525 um thick for 100 mm wafers (page size ladder)."#,
    ),
    spot(r#"150 mm"#, 0, TO_EOL, r#"675 um thick for 150 mm wafers."#),
    spot(r#"200 mm"#, 0, TO_EOL, r#"725 um thick for 200 mm wafers."#),
    spot(
        r#"300 mm"#,
        0,
        TO_EOL,
        r#"775 um, introduced in 1999 (Wikipedia)."#,
    ),
    spot(
        r#"450 mm"#,
        0,
        TO_EOL,
        r#"925 um for the cancelled 450 mm program."#,
    ),
];

const V54_1_ART: &str = r#"# Thickness has a job

  bigger wafer ──▶ heavier ──▶ thicker to resist breakage and warp
  300 mm: about 125 g, 640 ideal dies of 100 mm2
  later: thinned for packaging (separate step)
"#;
const V54_1_SPOTS: &[Spot] = &[
    spot(
        r#"bigger wafer"#,
        0,
        0,
        r#"Larger wafers need more thickness to hold up under their own weight (textbook)."#,
    ),
    spot(
        r#"about 125 g"#,
        0,
        0,
        r#"Mass of a 300 mm wafer, with 640 ideal dies of 100 mm2 (Wikipedia table)."#,
    ),
    spot(
        r#"thinned for packaging"#,
        0,
        0,
        r#"Thinning happens later and separately."#,
    ),
];

const V54_2_ART: &str = r#"# Dies per wafer (100 mm2 ideal dies)

  200 mm   █████ 269
  300 mm   █████████████ 640
  450 mm   ██████████████████████████████ 1490 (342 g, stopped 2016)
"#;
const V54_2_SPOTS: &[Spot] = &[
    spot(r#"200 mm"#, 0, TO_EOL, r#"269 ideal dies."#),
    spot(r#"300 mm"#, 0, TO_EOL, r#"640 ideal dies."#),
    spot(
        r#"450 mm"#,
        0,
        TO_EOL,
        r#"1490 dies, 342 g. It was proposed for 2018 and stopped in 2016 because tool makers declined retooling costs."#,
    ),
];

const V55_0_ART: &str = r#"# Two kinds of LTA

  fixed LTA    no 2024 increase
  step-up LTA  might rise
  Shin-Etsu: prices should rise on capex and raw materials
"#;
const V55_0_SPOTS: &[Spot] = &[
    spot(
        r#"fixed LTA"#,
        0,
        TO_EOL,
        r#"Customers on fixed LTAs saw no 2024 increase (LaPedus summary)."#,
    ),
    spot(
        r#"step-up LTA"#,
        0,
        TO_EOL,
        r#"Step-up LTAs might see increases."#,
    ),
    spot(
        r#"Shin-Etsu:"#,
        0,
        TO_EOL,
        r#"Shin-Etsu said LTA prices should rise on capex and raw material costs."#,
    ),
];

const V55_1_ART: &str = r#"# Signals

  2025  shipments +5.8%, revenue -1.2% (SEMI)
  May 2026  plans to raise prices, Asian capacity fully booked
  Aug 2026  GlobalWafers: 300 mm capacity fully used
  unconfirmed: +18 to 22% on AI-dedicated wafers
"#;
const V55_1_SPOTS: &[Spot] = &[
    spot(
        r#"2025"#,
        0,
        TO_EOL,
        r#"SEMI: shipments up 5.8% to 12,973 million sq in, revenue down 1.2% to $11.4B."#,
    ),
    spot(
        r#"May 2026"#,
        0,
        TO_EOL,
        r#"A shareholder-meeting summary reported plans to raise prices with Asian capacity fully booked."#,
    ),
    spot(
        r#"Aug 2026"#,
        0,
        TO_EOL,
        r#"GlobalWafers said existing 300 mm capacity was fully used."#,
    ),
    spot(
        r#"unconfirmed"#,
        0,
        TO_EOL,
        r#"A single source claims 18-22% increases for AI-dedicated wafers."#,
    ),
];

const V55_2_ART: &str = r#"# Two demand worlds

  mature nodes        weak
  HBM, advanced logic strong  ──▶ carries the growth
  names: Shin-Etsu 4063.T, SUMCO 3436.T,
         GlobalWafers 6488.TWO, Siltronic
"#;
const V55_2_SPOTS: &[Spot] = &[
    spot(
        r#"mature nodes"#,
        0,
        TO_EOL,
        r#"Weak demand in mature-node wafers."#,
    ),
    spot(
        r#"HBM, advanced logic"#,
        0,
        0,
        r#"Polished wafers for HBM and advanced epitaxial logic wafers drive growth."#,
    ),
    spot(
        r#"names:"#,
        0,
        TO_EOL,
        r#"The listed wafer makers named on the page."#,
    ),
];

const V56_0_ART: &str = r#"# Share, 2024 (Report Prime, low reliability)

  Shin-Etsu    ████████████████████ 19.9%
  SUMCO        █████████████████ 17.2%
  GlobalWafers █████████████ 12.9%
  Siltronic    ██████████ 9.9%
  SK Siltron   █████████ 8.6%
  combined: 82-94% depending on source and year
"#;
const V56_0_SPOTS: &[Spot] = &[
    spot(
        r#"Shin-Etsu"#,
        0,
        TO_EOL,
        r#"19.9% in the Report Prime 2024 estimate (low reliability)."#,
    ),
    spot(
        r#"SUMCO"#,
        0,
        TO_EOL,
        r#"SUMCO at 17.2% in the same estimate."#,
    ),
    spot(
        r#"GlobalWafers"#,
        0,
        TO_EOL,
        r#"GlobalWafers at 12.9% in the same estimate."#,
    ),
    spot(
        r#"Siltronic"#,
        0,
        TO_EOL,
        r#"Siltronic at 9.9% in the same estimate."#,
    ),
    spot(
        r#"SK Siltron"#,
        0,
        TO_EOL,
        r#"SK Siltron at 8.6% in the same estimate."#,
    ),
    spot(
        r#"combined:"#,
        0,
        0,
        r#"The page's sources put the five at 82-94% depending on year; Omdia 2020 said 94% of an $11.2B market."#,
    ),
];

const V56_1_ART: &str = r#"# Chokepoints stacked

  Spruce Pine quartz ─▶ crucible ─┐
  electronic-grade poly ──────────┼──▶ five wafer makers
  qualification takes years ──────┘     (Japan, Taiwan, Germany, Korea)
"#;
const V56_1_SPOTS: &[Spot] = &[
    spot(
        r#"Spruce Pine quartz"#,
        0,
        0,
        r#"Sibelco and The Quartz Corp supply about 95% of ultra-high-purity quartz."#,
    ),
    spot(
        r#"electronic-grade poly"#,
        0,
        0,
        r#"A small set of makers (Wacker, Hemlock, OCI, Tokuyama)."#,
    ),
    spot(
        r#"qualification takes years"#,
        0,
        0,
        r#"New entrants rarely win share."#,
    ),
    spot(
        r#"five wafer makers"#,
        0,
        0,
        r#"Concentrated in Japan, Taiwan, Germany and Korea."#,
    ),
];

const V56_2_ART: &str = r#"# Siltronic upgrades, Aug 2026

  UBS, Deutsche Bank, Kepler Cheuvreux, DZ Bank: Buy
  UBS case: needs significantly higher prices (not yet proven)
  read-through: wafer volume ──▶ leading-edge fab activity
"#;
const V56_2_SPOTS: &[Spot] = &[
    spot(
        r#"UBS, Deutsche Bank"#,
        0,
        0,
        r#"Upgrades to Buy per an August 2026 report (stock3)."#,
    ),
    spot(
        r#"UBS case"#,
        0,
        0,
        r#"The UBS case rests on significantly higher prices still to be proven."#,
    ),
    spot(
        r#"read-through"#,
        0,
        0,
        r#"Wafer volume is a read-through to leading-edge fab activity."#,
    ),
];

const V57_0_ART: &str = r#"# One pass, many wafers

   ingot ──▶ fed down through the wire web
             ═════ diamond wire ═════
   cutting = brittle micro-fracture by diamond grit
   vs slurry sawing: diamond wire about 2x faster (solar)
   result: hundreds of thin discs
"#;
const V57_0_SPOTS: &[Spot] = &[
    spot(
        r#"ingot"#,
        0,
        0,
        r#"The notched, ground cylinder from the INGOT stage."#,
    ),
    spot(
        r#"diamond wire"#,
        0,
        0,
        r#"Fixed diamond abrasive on the wire cuts all wafers at once."#,
    ),
    spot(
        r#"brittle micro-fracture"#,
        0,
        0,
        r#"Grit chips the silicon away rather than cutting it smoothly."#,
    ),
    spot(
        r#"about 2x faster"#,
        0,
        0,
        r#"TaiyangNews, solar context; diamond-wire patents also describe slurry sawing as slow with frequent wire breakage."#,
    ),
];

const V57_1_ART: &str = r#"# What the saw leaves

   ┌───────────────────────┐
   │ ░░░ cracked layer ░░░ │ microns deep, both faces
   │       good silicon    │
   │ ░░░ cracked layer ░░░ │
   └───────────────────────┘
   plus: initial bow, warp, thickness variation
   later steps (lap, etch, polish) remove them
"#;
const V57_1_SPOTS: &[Spot] = &[
    spot(
        r#"cracked layer"#,
        0,
        0,
        r#"A layer microns deep on every face, which the later steps remove (page)."#,
    ),
    spot(r#"good silicon"#, 0, 0, r#"The undamaged wafer interior."#),
    spot(
        r#"initial bow, warp"#,
        0,
        0,
        r#"Slicing sets the wafer's initial bow, warp and thickness variation."#,
    ),
    spot(
        r#"later steps"#,
        0,
        0,
        r#"Lapping or grinding, etching and polishing each remove part of the damage."#,
    ),
];

const V57_2_ART: &str = r#"# Kerf, solar numbers (um)

  slurry        ███████████████ 150
  diamond wire  ████████████▌ 125
  roadmap       ████████▌ 85
  research      under 35 um wire diameter
"#;
const V57_2_SPOTS: &[Spot] = &[
    spot(r#"slurry"#, 0, TO_EOL, r#"About 150 um kerf."#),
    spot(r#"diamond wire"#, 0, TO_EOL, r#"About 125 um kerf."#),
    spot(r#"roadmap"#, 0, TO_EOL, r#"ITRPV path to about 85 um."#),
    spot(
        r#"research"#,
        0,
        TO_EOL,
        r#"Under 35 um fine wire is the research direction (Ge et al.)."#,
    ),
];

const V58_0_ART: &str = r#"# Two ways to flatten

  LAPPING                      GRINDING
  ┌──────── plate ────────┐        ╭─ wheel ─╮
  │  slurry + wafer       │        │ resin   │
  └──────── plate ────────┘        ╰────┬────╯
  both faces at once              one side, 10-20 um
  sets flatness + parallelism     (patents)
"#;
const V58_0_SPOTS: &[Spot] = &[
    spot(
        r#"LAPPING"#,
        0,
        0,
        r#"Loose abrasive slurry between two plates, both faces at once; sets flatness and parallelism."#,
    ),
    spot(
        r#"GRINDING"#,
        0,
        0,
        r#"Fixed-abrasive resin-bond wheel; the alternative to lapping."#,
    ),
    spot(
        r#"both faces at once"#,
        0,
        0,
        r#"Double-side lapping works both sides together."#,
    ),
    spot(
        r#"one side, 10-20 um"#,
        0,
        0,
        r#"A resin-bond wheel removes 10-20 um on one side (page, from patents)."#,
    ),
];

const V58_1_ART: &str = r#"# Removal examples from patents (um)

  one-side grind        ██ 10-20
  rough grind (DS)      ███████ 45-75   (before lapping)
  lapping (DS) example  ████████ 80    (in 40 minutes)
  lapping range         ████████████████████ up to 200
"#;
const V58_1_SPOTS: &[Spot] = &[
    spot(
        r#"one-side grind"#,
        0,
        TO_EOL,
        r#"A resin-bond wheel: 10-20 um."#,
    ),
    spot(
        r#"rough grind (DS)"#,
        0,
        TO_EOL,
        r#"Double-side rough grind example: about 45-75 um before lapping."#,
    ),
    spot(
        r#"lapping (DS) example"#,
        0,
        TO_EOL,
        r#"A 200-300 mm patent example: 80 um in 40 minutes."#,
    ),
    spot(
        r#"lapping range"#,
        0,
        TO_EOL,
        r#"Total double-side lapping removes 80-200 um."#,
    ),
];

const V58_2_ART: &str = r#"# Why this step exists

  saw waviness + sawing damage ──▶ removed
  uniform thickness before the chemical steps
  too aggressive ──▶ scratches, subsurface damage ──▶ polish defects
  grinding: faster, in-line     lapping: proven batch (textbook)
"#;
const V58_2_SPOTS: &[Spot] = &[
    spot(
        r#"saw waviness"#,
        0,
        0,
        r#"Lapping or grinding removes waviness and sawing damage."#,
    ),
    spot(
        r#"uniform thickness"#,
        0,
        0,
        r#"The wafer is brought to uniform thickness before etching."#,
    ),
    spot(
        r#"too aggressive"#,
        0,
        0,
        r#"Over-aggressive removal leaves scratches and damage that show up as polish defects."#,
    ),
    spot(
        r#"grinding: faster"#,
        0,
        0,
        r#"Textbook comparison: grinding can be in-line, lapping is a proven batch process."#,
    ),
];

const V59_0_ART: &str = r#"# Chemical removal

  lapped wafer ──▶ ┌───────────────┐ ──▶ damage-free surface
                   │ alkali or acid│
                   │ bath          │  removes about 15-25 um
                   └───────────────┘  (patent examples)
  no added mechanical stress
"#;
const V59_0_SPOTS: &[Spot] = &[
    spot(
        r#"lapped wafer"#,
        0,
        0,
        r#"Arrives with a damaged layer left by lapping or grinding."#,
    ),
    spot(
        r#"alkali or acid"#,
        0,
        0,
        r#"A wet bath: temperature and time are the control points (page, textbook)."#,
    ),
    spot(
        r#"15-25 um"#,
        0,
        0,
        r#"Patent examples on this page; not a standard."#,
    ),
    spot(
        r#"no added mechanical stress"#,
        0,
        0,
        r#"Chemical etching removes damage without adding stress."#,
    ),
];

const V59_1_ART: &str = r#"# 300 mm example (one patent)

  acid etch        ██████████ 10 um
  gas-phase etch   ██ 2 um
  final polish     █████ 5 um (front)
  (an example, not a standard)
"#;
const V59_1_SPOTS: &[Spot] = &[
    spot(
        r#"acid etch"#,
        0,
        TO_EOL,
        r#"10 um removed in one patent example."#,
    ),
    spot(r#"gas-phase etch"#, 0, TO_EOL, r#"2 um removed."#),
    spot(
        r#"final polish"#,
        0,
        TO_EOL,
        r#"5 um removed from the front."#,
    ),
    spot(
        r#"an example"#,
        0,
        0,
        r#"The page notes these are patent examples, not a standard."#,
    ),
];

const V59_2_ART: &str = r#"# Trade-off (textbook, unsourced)

  alkali  flatter, rougher
  acid    smoother, less flat
  failure: uneven bath flow or temperature
           ──▶ thickness variation for the polish to repair
           contamination from chemicals goes into the surface
"#;
const V59_2_SPOTS: &[Spot] = &[
    spot(
        r#"alkali"#,
        0,
        TO_EOL,
        r#"Textbook: flatter but rougher surface."#,
    ),
    spot(r#"acid"#, 0, TO_EOL, r#"Textbook: smoother but less flat."#),
    spot(
        r#"failure:"#,
        0,
        TO_EOL,
        r#"Uneven flow or temperature leaves thickness variation; chemicals can add metal contamination."#,
    ),
];

const V60_0_ART: &str = r#"# Rim profile

   as sliced           after edge grinding
   ┌──────┐            ╭──────╮
   │      │ sharp      │      │ rounded
   └──────┘ corner     ╰──────╯ chamfered
"#;
const V60_0_SPOTS: &[Spot] = &[
    spot(
        r#"as sliced"#,
        0,
        0,
        r#"The cut edge is sharp and brittle."#,
    ),
    spot(
        r#"after edge grinding"#,
        0,
        0,
        r#"Ground, chamfered and polished into a rounded profile."#,
    ),
    spot(r#"sharp"#, 0, 0, r#"Sharp corners chip during handling."#),
    spot(r#"rounded"#, 0, 0, r#"A rounded profile resists chipping."#),
];

const V60_1_ART: &str = r#"# What a broken rim causes (textbook)

  sharp edge ──▶ chip ──▶ particles on the wafer
                   └──▶ crack runs across under thermal stress
  also: edge beads and defects in coating and deposition
"#;
const V60_1_SPOTS: &[Spot] = &[
    spot(r#"chip"#, 0, 0, r#"Chips shed particles."#),
    spot(
        r#"particles on the wafer"#,
        0,
        0,
        r#"Particles contaminate the wafer and tools."#,
    ),
    spot(
        r#"crack runs across"#,
        0,
        0,
        r#"Cracks can grow under thermal stress in the fab (textbook)."#,
    ),
    spot(
        r#"edge beads"#,
        0,
        0,
        r#"Edge defects can affect photoresist coating and film deposition (textbook)."#,
    ),
];

const V60_2_ART: &str = r#"# Edge before polish

  slice ──▶ lap/grind ──▶ edge ──▶ etch ──▶ polish
                           ▲
         debris here cannot scratch the polished face
  removal amount: no figure found
"#;
const V60_2_SPOTS: &[Spot] = &[
    spot(
        r#"edge"#,
        0,
        0,
        r#"Edge grinding comes before final polish."#,
    ),
    spot(
        r#"debris here"#,
        0,
        0,
        r#"Doing the edge first keeps debris from scratching the polished face."#,
    ),
    spot(
        r#"removal amount"#,
        0,
        0,
        r#"No source gave a removal figure."#,
    ),
];

const V61_0_ART: &str = r#"# Two polish stages

  DSP: both faces, free-floating carriers     10-20 um total
        │
        ▼
  final CMP: front only                        10-15 um, 5-15 min
  chemistry softens + abrasive wipes (textbook)
"#;
const V61_0_SPOTS: &[Spot] = &[
    spot(
        r#"DSP:"#,
        0,
        TO_EOL,
        r#"Double-side polish removes 10-20 um total (patent examples)."#,
    ),
    spot(
        r#"final CMP"#,
        0,
        TO_EOL,
        r#"A final chemical-mechanical polish on the front removes 10-15 um in 5-15 minutes."#,
    ),
    spot(
        r#"chemistry softens"#,
        0,
        0,
        r#"Chemistry softens or oxidises the surface and abrasive wipes it off (textbook)."#,
    ),
];

const V61_1_ART: &str = r#"# What nanotopography means

  surface deviation over wavelengths 0.2 to 20 mm
  ──▶ height differences of tens of nanometres
  set mostly by the polishing process
  older ITRS targets: 300 mm site flatness under 45 nm by 2010,
  possibly 25 nm by 2015
"#;
const V61_1_SPOTS: &[Spot] = &[
    spot(
        r#"wavelengths 0.2 to 20 mm"#,
        0,
        0,
        r#"Surface deviation over spatial wavelengths of about 0.2 to 20 mm (SEMI 3089 definition per the patent)."#,
    ),
    spot(
        r#"set mostly by the polishing process"#,
        0,
        0,
        r#"A KLA-related patent says nanotopography is largely set by polishing."#,
    ),
    spot(
        r#"under 45 nm by 2010"#,
        0,
        0,
        r#"Older ITRS projection for 300 mm site flatness."#,
    ),
    spot(
        r#"25 nm by 2015"#,
        0,
        0,
        r#"The same ITRS projection allowed possibly 25 nm by 2015."#,
    ),
];

const V61_2_ART: &str = r#"# Spec and controls

  thickness   775 um +/- 25 um
  TTV         5 um or less
  knobs       pad wear, slurry mix, pressure, speed
  2013 study  Taguchi design picked pressure, speed, slurry ratio
"#;
const V61_2_SPOTS: &[Spot] = &[
    spot(
        r#"thickness"#,
        0,
        TO_EOL,
        r#"775 um +/- 25 um per vendor datasheet."#,
    ),
    spot(
        r#"TTV"#,
        0,
        TO_EOL,
        r#"Total thickness variation 5 um or less (vendor datasheet)."#,
    ),
    spot(
        r#"knobs"#,
        0,
        TO_EOL,
        r#"Pad wear, slurry mix, pressure and speed are the control points."#,
    ),
    spot(
        r#"2013 study"#,
        0,
        TO_EOL,
        r#"A 2013 study on 300 mm final polishing used a Taguchi design."#,
    ),
];

const V62_0_ART: &str = r#"# Last box

  polished wafer: slurry residue, abrasive, metal traces
        │
        ▼
  chemical clean (RCA-type, textbook)
        │
        ▼
  inspect: thickness, flatness, nanotopography, particles
        │
        ▼
  ship
"#;
const V62_0_SPOTS: &[Spot] = &[
    spot(
        r#"slurry residue"#,
        0,
        0,
        r#"Polishing leaves slurry residue, abrasive particles and metal traces."#,
    ),
    spot(
        r#"chemical clean"#,
        0,
        0,
        r#"Removed with chemical cleans (textbook; the common RCA-type sequence). The page gives no cleaning chemistry or numbers."#,
    ),
    spot(
        r#"inspect:"#,
        0,
        TO_EOL,
        r#"Measured against the customer's spec."#,
    ),
    spot(r#"ship"#, 0, 0, r#"Wafers go to the chipmaker."#),
];

const V62_1_ART: &str = r#"# Fraunhofer 2014 tool

  300 mm wafer surface
  ┌───┬───┬───┬───┐
  │ 1 │ 2 │ 3 │ 4 │  16 single measurements
  ├───┼───┼───┼───┤  stitched into one map
  │ 5 │ 6 │ 7 │ 8 │  of nanotopography
  ├───┼───┼───┼───┤
  │ 9 │10 │11 │12 │  (grid is illustrative)
  ├───┼───┼───┼───┤
  │13 │14 │15 │16 │
  └───┴───┴───┴───┘
"#;
const V62_1_SPOTS: &[Spot] = &[
    spot(
        r#"16 single measurements"#,
        0,
        0,
        r#"The tool stitches 16 single measurements to cover the entire surface."#,
    ),
    spot(
        r#"stitched into one map"#,
        0,
        0,
        r#"The result is a nanotopography map of the whole wafer."#,
    ),
    spot(
        r#"illustrative"#,
        0,
        0,
        r#"The 4x4 layout is only a sketch of the idea; the source says 16 measurements."#,
    ),
];

const V62_2_ART: &str = r#"# Why customers stay

  clean + inspect results ──▶ customer qualification (years)
                                   │
                                   ▼
                    approved line: rarely switched
  2025 shipments 12,973 M sq in (SEMI)
"#;
const V62_2_SPOTS: &[Spot] = &[
    spot(
        r#"clean + inspect results"#,
        0,
        0,
        r#"These are what the customer audits."#,
    ),
    spot(
        r#"qualification (years)"#,
        0,
        0,
        r#"Qualification takes years (INGOT page)."#,
    ),
    spot(
        r#"rarely switched"#,
        0,
        0,
        r#"Once approved, buyers rarely switch, which supports the oligopoly."#,
    ),
    spot(r#"12,973 M sq in"#, 0, 0, r#"SEMI 2025 shipments."#),
];

const V63_0_ART: &str = r#"# Wire path

   spool A ──▶ ═══ guide roller ═══▶ guide roller ──▶ spool B
               groove pitch about wafer thickness + kerf
   forward, then back: wire wears evenly
"#;
const V63_0_SPOTS: &[Spot] = &[
    spot(r#"spool A"#, 0, 0, r#"The wire spools forward, then back."#),
    spot(
        r#"guide roller"#,
        0,
        0,
        r#"Grooved rollers hold the wire at a set pitch."#,
    ),
    spot(
        r#"groove pitch"#,
        0,
        0,
        r#"Roughly the wafer thickness plus kerf, so the roller set defines the product."#,
    ),
    spot(
        r#"wire wears evenly"#,
        0,
        0,
        r#"Reversing spreads abrasive wear along the wire."#,
    ),
];

const V63_1_ART: &str = r#"# Worn wire

  new wire    straight, small kerf
  worn wire   deflects ──▶ more TTV, wavier surface
              kerf grows
  controls: wire tension, wire speed (no numbers sourced)
"#;
const V63_1_SPOTS: &[Spot] = &[
    spot(
        r#"new wire"#,
        0,
        TO_EOL,
        r#"Straight cutting and small kerf."#,
    ),
    spot(
        r#"worn wire"#,
        0,
        0,
        r#"Wear raises deflection, thickness variation and kerf (Springer 2026)."#,
    ),
    spot(
        r#"controls:"#,
        0,
        TO_EOL,
        r#"Tension and speed are the control points (page, textbook)."#,
    ),
];

const V63_2_ART: &str = r#"# Thinner is weaker

  thinner wire ──▶ smaller kerf ──▶ more wafers per ingot
       └──────────▶ lower strength ──▶ more breakage
  research target: under 35 um (Ge et al. 2026)
"#;
const V63_2_SPOTS: &[Spot] = &[
    spot(
        r#"thinner wire"#,
        0,
        0,
        r#"Smaller kerf, more wafers per ingot."#,
    ),
    spot(
        r#"lower strength"#,
        0,
        0,
        r#"Thinner wire is weaker and breaks more."#,
    ),
    spot(
        r#"under 35 um"#,
        0,
        0,
        r#"The research target (Ge et al. 2026)."#,
    ),
];

const V64_0_ART: &str = r#"# Coolant at the cut

   spray ══▶ wire + cut zone
        │
        ├──▶ cools: controls thermal bow (textbook)
        └──▶ flushes out silicon swarf
"#;
const V64_0_SPOTS: &[Spot] = &[
    spot(
        r#"spray"#,
        0,
        0,
        r#"Water-based coolant sprayed on the cut."#,
    ),
    spot(
        r#"cools:"#,
        0,
        0,
        r#"Heat expands the ingot and beam during the cut, so coolant temperature is a control point (textbook)."#,
    ),
    spot(
        r#"flushes out silicon swarf"#,
        0,
        0,
        r#"Washes the fine silicon powder out of the cut."#,
    ),
];

const V64_1_ART: &str = r#"# Swarf = lost silicon

  per wafer: about 125 um becomes powder (diamond wire, solar)
  recovery: active topic, no figure sourced
  build-up in the cut ──▶ more wire load ──▶ breakage risk
"#;
const V64_1_SPOTS: &[Spot] = &[
    spot(
        r#"per wafer"#,
        0,
        0,
        r#"About 125 um for diamond wire (solar roadmap number)."#,
    ),
    spot(
        r#"recovery"#,
        0,
        0,
        r#"Swarf recovery from solar sawing is an active topic; no figure was found."#,
    ),
    spot(
        r#"build-up in the cut"#,
        0,
        0,
        r#"Swarf building up raises wire load and breakage risk."#,
    ),
];

const V64_2_ART: &str = r#"# Old vs new

  slurry saw     loose abrasive in oil-based slurry
  diamond wire   fixed abrasive, water-based coolant (textbook)
  poor coolant flow ──▶ thermal bow, thickness variation
"#;
const V64_2_SPOTS: &[Spot] = &[
    spot(
        r#"slurry saw"#,
        0,
        TO_EOL,
        r#"Older saws used loose abrasive in oil-based slurry (textbook)."#,
    ),
    spot(
        r#"diamond wire"#,
        0,
        TO_EOL,
        r#"Fixed abrasive with water-based coolant simplifies the process (textbook)."#,
    ),
    spot(
        r#"poor coolant flow"#,
        0,
        0,
        r#"Causes thermal bow and thickness variation."#,
    ),
];

const V65_0_ART: &str = r#"# The slot lost per cut (solar numbers)

   wafer │ kerf │ wafer │ kerf │ wafer
         ↑      ↑
         wire pass destroys this slot
  slurry 150 um   diamond 125 um   roadmap 85 um
"#;
const V65_0_SPOTS: &[Spot] = &[
    spot(
        r#"kerf"#,
        0,
        0,
        r#"The slot of silicon destroyed by each wire pass."#,
    ),
    spot(
        r#"slurry 150 um"#,
        0,
        0,
        r#"About 150 um (ITRPV roadmap via TaiyangNews, solar)."#,
    ),
    spot(r#"diamond 125 um"#, 0, 0, r#"About 125 um today."#),
    spot(r#"roadmap 85 um"#, 0, 0, r#"Path to about 85 um."#),
];

const V65_1_ART: &str = r#"# Kerf as a share of ingot length (775 um wafer)

  125 um kerf  █████████████▉ 13.9% swarf
   85 um kerf  █████████▉ 9.9% swarf
  wafers per ingot: +4.7% going from 125 to 85 um
  (my arithmetic, solar kerf values applied to a 775 um wafer)
"#;
const V65_1_SPOTS: &[Spot] = &[
    spot(r#"125 um kerf"#, 0, TO_EOL, r#"125 / (775 + 125) = 13.9%."#),
    spot(r#"85 um kerf"#, 0, TO_EOL, r#"85 / (775 + 85) = 9.9%."#),
    spot(
        r#"wafers per ingot"#,
        0,
        0,
        r#"Wafers scale as 1 / (775 + kerf): 900 / 860 is about +4.7% (illustrative)."#,
    ),
];

const V65_2_ART: &str = r#"# Silicon lost per wafer, midpoint examples (um)

  kerf     ████████████▌ 125
  lapping  ████████ 80
  etch     ██ 20
  DSP      █▌ 15
  (sawing and lapping dominate)
"#;
const V65_2_SPOTS: &[Spot] = &[
    spot(r#"kerf"#, 0, TO_EOL, r#"Pure loss: 125 um midpoint."#),
    spot(r#"lapping"#, 0, TO_EOL, r#"80 um midpoint example."#),
    spot(r#"etch"#, 0, TO_EOL, r#"20 um midpoint example."#),
    spot(r#"DSP"#, 0, TO_EOL, r#"15 um midpoint example."#),
];

const V66_0_ART: &str = r#"# Ingot in the saw

     ┌─────────────┐
     │   ingot     │ ground to 300 mm, notched
     └──────┬──────┘
         glue + beam
   fed downward through the web
"#;
const V66_0_SPOTS: &[Spot] = &[
    spot(
        r#"ingot"#,
        0,
        0,
        r#"Ground to 300 mm and notched, several hundred kg of crystal (Wikipedia)."#,
    ),
    spot(
        r#"glue + beam"#,
        0,
        0,
        r#"Bonded to a beam, so its orientation relative to the wire matters."#,
    ),
    spot(
        r#"fed downward"#,
        0,
        0,
        r#"The saw feeds it down through the wire web."#,
    ),
];

const V66_1_ART: &str = r#"# Bigger ingot, more drag

  200 mm   less wire drag
  300-400 mm  more drag ──▶ breakage risk
                  └─▶ thicker wire ──▶ more kerf
  tangential-feed patent claims fast cut, minimal kerf
  (inventor claims, not independent)
"#;
const V66_1_SPOTS: &[Spot] = &[
    spot(
        r#"200 mm"#,
        0,
        TO_EOL,
        r#"Smaller diameters have less drag."#,
    ),
    spot(
        r#"300-400 mm"#,
        0,
        0,
        r#"Drag grows with diameter and makes breakage more likely, unless thicker wire is used."#,
    ),
    spot(
        r#"tangential-feed"#,
        0,
        0,
        r#"One patent family claims fast cutting with minimal kerf and less lapping (inventor claims)."#,
    ),
];

const V66_2_ART: &str = r#"# Value per event

  crystal growth: a day of furnace time ──▶ ingot
  saw failure: wire break near the end ──▶ ruined wafers
  worn wire: deflection + thickness variation
"#;
const V66_2_SPOTS: &[Spot] = &[
    spot(
        r#"crystal growth"#,
        0,
        0,
        r#"A day-long pull produced this ingot."#,
    ),
    spot(
        r#"saw failure"#,
        0,
        0,
        r#"A wire break during the cut can ruin a large batch of wafers."#,
    ),
    spot(
        r#"worn wire"#,
        0,
        0,
        r#"Wear raises deflection and thickness variation (Springer 2026)."#,
    ),
];

const V67_0_ART: &str = r#"# Removal rate

   RR = K * P + C

   RR  removal rate        P  pressure
   K   Preston constant    C  zero-pressure term
   pad, slurry, temperature all fold into K
"#;
const V67_0_SPOTS: &[Spot] = &[
    spot(
        r#"RR = K * P + C"#,
        0,
        0,
        r#"Preston's law as given on the page (patent and paper)."#,
    ),
    spot(
        r#"K   Preston constant"#,
        0,
        0,
        r#"Pad, slurry and temperature fold into K."#,
    ),
    spot(r#"P  pressure"#, 0, 0, r#"Higher pressure raises removal."#),
];

const V67_1_ART: &str = r#"# Oxide removal vs pH

  silica slurry   removal rises with pH ──▶ pitting at pH 13
  ceria slurry    peaks near pH 8-9
  chemistry is a tuning axis, not just grit size
"#;
const V67_1_SPOTS: &[Spot] = &[
    spot(
        r#"silica slurry"#,
        0,
        TO_EOL,
        r#"Removal rises with pH, with pitting seen at pH 13 (patent and journal citations)."#,
    ),
    spot(r#"ceria slurry"#, 0, TO_EOL, r#"Peaks near pH 8-9."#),
    spot(
        r#"chemistry is a tuning axis"#,
        0,
        0,
        r#"Slurry chemistry matters as much as abrasive size."#,
    ),
];

const V67_2_ART: &str = r#"# One law, two places

  wafer maker polish ─┐
                      ├──▶ Preston physics
  fab CMP of films ───┘    (STI, copper, tungsten)
  Sept 2025: Fujifilm slurry for hybrid bonding
             (advanced packaging for AI memory and logic stacks)
"#;
const V67_2_SPOTS: &[Spot] = &[
    spot(
        r#"wafer maker polish"#,
        0,
        0,
        r#"Bare-silicon polishing at the wafer maker."#,
    ),
    spot(
        r#"fab CMP of films"#,
        0,
        0,
        r#"Fab CMP planarises deposited films such as STI, copper and tungsten."#,
    ),
    spot(
        r#"Fujifilm slurry"#,
        0,
        0,
        r#"Fujifilm launched a copper and oxide CMP slurry for hybrid bonding in September 2025 (PS Market Research summary)."#,
    ),
    spot(
        r#"advanced packaging"#,
        0,
        0,
        r#"Hybrid bonding is used in advanced packaging for AI memory and logic stacks."#,
    ),
];

const V68_0_ART: &str = r#"# CMP tool share (Dataquest, old)

           2001                    2002
  Applied  ███████████████ 62.1%   ███████████████ 61.3%
  Ebara    █████▌ 23%              █████▌ 22%
  today: "about 80% for the two" (weakly sourced)
"#;
const V68_0_SPOTS: &[Spot] = &[
    spot(
        r#"Applied"#,
        0,
        TO_EOL,
        r#"Applied Materials: 62.1% in 2001, 61.3% in 2002 (Dataquest, via Silicon Semiconductor)."#,
    ),
    spot(r#"Ebara"#, 0, TO_EOL, r#"Ebara: 23% in 2001, 22% in 2002."#),
    spot(
        r#"about 80% for the two"#,
        0,
        0,
        r#"A market-research claim with weak sourcing."#,
    ),
];

const V68_1_ART: &str = r#"# Who else

  Applied + Ebara     incumbents
  Lam Research, Hitachi High-Tech, Tokyo Seimitsu (no shares)
  Chinese domestic toolmakers pushing in (AMAT FY2025 10-K)
"#;
const V68_1_SPOTS: &[Spot] = &[
    spot(r#"Applied + Ebara"#, 0, TO_EOL, r#"The incumbents."#),
    spot(
        r#"Lam Research"#,
        0,
        0,
        r#"Named in a market-research listing, with no shares."#,
    ),
    spot(
        r#"Chinese domestic toolmakers"#,
        0,
        0,
        r#"Applied's FY2025 10-K discusses CMP competition including Chinese domestic toolmakers."#,
    ),
];

const V68_2_ART: &str = r#"# Two kinds of polisher

  fab CMP tool        polishes deposited films
  wafer-maker polish  polishes bare silicon (vendors: no source found)
  read: share + geopolitics + export controls
"#;
const V68_2_SPOTS: &[Spot] = &[
    spot(
        r#"fab CMP tool"#,
        0,
        TO_EOL,
        r#"Planarises deposited films in the chip fab."#,
    ),
    spot(
        r#"wafer-maker polish"#,
        0,
        TO_EOL,
        r#"Bare-silicon polishers. The page found no source on which vendors supply them."#,
    ),
    spot(
        r#"read:"#,
        0,
        TO_EOL,
        r#"A two-supplier market with a Chinese challenger is also a geopolitics story."#,
    ),
];

const V69_0_ART: &str = r#"# CMP slurry leaders (TECHCET-cited, about 2023)

  Fujifilm 4901.T  ███████████████ about 31%  (copper slurry strength)
  Entegris ENTG    second, after Sinmat, Chemetall PM, CMC Materials
  check against current TECHCET data
"#;
const V69_0_SPOTS: &[Spot] = &[
    spot(
        r#"Fujifilm 4901.T"#,
        0,
        TO_EOL,
        r#"The largest supplier at about 31% in a TECHCET-cited article."#,
    ),
    spot(
        r#"Entegris ENTG"#,
        0,
        TO_EOL,
        r#"Second, after acquiring Sinmat, Chemetall Precision Microchemicals and CMC Materials."#,
    ),
    spot(
        r#"check against"#,
        0,
        0,
        r#"The article forecasts 2024 growth, so the shares are probably from around 2023."#,
    ),
];

const V69_1_ART: &str = r#"# Concentrated

  top six players: over 70% of revenue (market research)
  named: Entegris, Resonac, Fujimi, DuPont, Fujifilm
  (no figures retrieved)
"#;
const V69_1_SPOTS: &[Spot] = &[
    spot(
        r#"top six players"#,
        0,
        TO_EOL,
        r#"The global top six hold over 70% of slurry revenue (market-research summary)."#,
    ),
    spot(
        r#"named:"#,
        0,
        TO_EOL,
        r#"A 2024-base report lists these as key players."#,
    ),
    spot(
        r#"no figures"#,
        0,
        0,
        r#"No per-company figures were retrieved."#,
    ),
];

const V69_2_ART: &str = r#"# Why revenue is sticky

  qualified per fab line ──▶ switching is slow
  revenue scales with wafer starts x CMP steps per chip
  advanced nodes + hybrid bonding add steps
"#;
const V69_2_SPOTS: &[Spot] = &[
    spot(
        r#"qualified per fab line"#,
        0,
        0,
        r#"Slurries are qualified per line, so switching is slow (page)."#,
    ),
    spot(
        r#"wafer starts x CMP steps"#,
        0,
        0,
        r#"Consumable revenue scales with both."#,
    ),
    spot(
        r#"hybrid bonding"#,
        0,
        0,
        r#"Advanced nodes and hybrid bonding add CMP steps."#,
    ),
];

const V70_0_ART: &str = r#"# Pad in the polisher

   wafer carrier ↓ pressure
   ┌───────────────────┐
   │      wafer        │
   └─────────┬─────────┘
   slurry ══▶│ polyurethane pad (asperities + channels)
   ══════════╧════════════════ rotating platen
"#;
const V70_0_SPOTS: &[Spot] = &[
    spot(
        r#"wafer carrier"#,
        0,
        0,
        r#"Presses the wafer face down on the pad."#,
    ),
    spot(
        r#"slurry"#,
        0,
        0,
        r#"The slurry flows between wafer and pad."#,
    ),
    spot(
        r#"polyurethane pad"#,
        0,
        0,
        r#"Its asperities and flow channels average out high spots (page; the material is textbook)."#,
    ),
    spot(
        r#"rotating platen"#,
        0,
        0,
        r#"The pad sits on a rotating platen."#,
    ),
];

const V70_1_ART: &str = r#"# Pad supplier (TECHCET-cited, undated)

  DuPont DD   ███████████████ over 50%
  rough: probably about 2023; no market size found
"#;
const V70_1_SPOTS: &[Spot] = &[
    spot(
        r#"DuPont DD"#,
        0,
        TO_EOL,
        r#"Said to hold over 50% of pads (TECHCET-cited, undated)."#,
    ),
    spot(
        r#"rough:"#,
        0,
        TO_EOL,
        r#"Treat as rough: probably about 2023, and no pad market size was found."#,
    ),
    spot(
        r#"over 50%"#,
        0,
        0,
        r#"The figure comes from the same article as the slurry shares."#,
    ),
];

const V70_2_ART: &str = r#"# Pad life (textbook)

  new pad ──▶ glazes and wears ──▶ rate and uniformity drift
                  │
                  ▼
  conditioned, then replaced on a schedule
  failure: scratches from large particles or pad debris
"#;
const V70_2_SPOTS: &[Spot] = &[
    spot(
        r#"glazes and wears"#,
        0,
        0,
        r#"Removal rate and uniformity drift as the pad wears (textbook)."#,
    ),
    spot(
        r#"conditioned, then replaced"#,
        0,
        0,
        r#"Pads are conditioned and replaced on a schedule."#,
    ),
    spot(
        r#"failure:"#,
        0,
        TO_EOL,
        r#"Scratches from large particles or pad debris."#,
    ),
];

const V71_0_ART: &str = r#"# Wear effects (Springer 2026)

  wire wears ──▶ deflection up
              ├─▶ thickness variation up
              └─▶ kerf up
  wire breaks mid-cut ──▶ ingot's wafers scrapped
"#;
const V71_0_SPOTS: &[Spot] = &[
    spot(
        r#"wire wears"#,
        0,
        0,
        r#"Wear is the root cause of drift in the cut."#,
    ),
    spot(r#"deflection up"#, 0, 0, r#"Wear raises wire deflection."#),
    spot(
        r#"thickness variation up"#,
        0,
        0,
        r#"Worn wire gives wafers more thickness variation."#,
    ),
    spot(r#"kerf up"#, 0, 0, r#"Kerf grows as the wire wears."#),
    spot(
        r#"wire breaks mid-cut"#,
        0,
        0,
        r#"A broken wire can scrap the ingot's wafers."#,
    ),
];

const V71_1_ART: &str = r#"# Wire gauge dilemma

  thin   less kerf, weaker, breaks more
  thick  stronger, more kerf loss
  300-400 mm ingots: drag pushes toward thicker wire
  research: under 35 um (Ge et al. 2026)
"#;
const V71_1_SPOTS: &[Spot] = &[
    spot(
        r#"thin"#,
        0,
        TO_EOL,
        r#"Less kerf but weaker, so more breakage."#,
    ),
    spot(r#"thick"#, 0, TO_EOL, r#"Stronger but more kerf loss."#),
    spot(
        r#"300-400 mm ingots"#,
        0,
        TO_EOL,
        r#"Older patents note wire drag raises breakage risk unless the gauge increases."#,
    ),
    spot(
        r#"research:"#,
        0,
        TO_EOL,
        r#"Heading under 35 um diameter (Ge et al. 2026)."#,
    ),
];

const V71_2_ART: &str = r#"# Risks across the module

  saw      wire breakage, wear
  CMP      slurries + pads: few vendors
           tools: two suppliers, Chinese challengers
  abrasive ceria and silica purity upstream
  control  tension, speed, feed rate, coolant temperature
"#;
const V71_2_SPOTS: &[Spot] = &[
    spot(r#"saw"#, 0, TO_EOL, r#"Wire breakage and wear."#),
    spot(
        r#"CMP"#,
        0,
        0,
        r#"Few vendors in slurries and pads; a two-supplier tool market with Chinese challengers (AMAT FY2025 10-K)."#,
    ),
    spot(
        r#"abrasive"#,
        0,
        TO_EOL,
        r#"Ceria and silica abrasive purity is an upstream supply question."#,
    ),
    spot(
        r#"control"#,
        0,
        TO_EOL,
        r#"Textbook control points; no numbers sourced."#,
    ),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::diagrams_vis::check;

    #[test]
    fn all_visuals_resolve() {
        let keys: &[(&str, &str, &str)] = &[
            (r#"SAND"#, r#"CRUSH"#, r#"Sizing the burden"#),
            (r#"SAND"#, r#"CRUSH"#, r#"Keep impurities out"#),
            (r#"SAND"#, r#"CRUSH"#, r#"Fume loss"#),
            (r#"SAND"#, r#"BLEND"#, r#"The mix"#),
            (r#"SAND"#, r#"BLEND"#, r#"Carbon purity"#),
            (r#"SAND"#, r#"BLEND"#, r#"Carbon balance"#),
            (r#"SAND"#, r#"ARC FURNACE"#, r#"Submerged arc"#),
            (r#"SAND"#, r#"ARC FURNACE"#, r#"Power and cost"#),
            (r#"SAND"#, r#"ARC FURNACE"#, r#"Why 24/7 and why hydro"#),
            (r#"SAND"#, r#"TAP"#, r#"Tapping the metal"#),
            (r#"SAND"#, r#"TAP"#, r#"Fume at the tap floor"#),
            (r#"SAND"#, r#"TAP"#, r#"Recovery"#),
            (r#"SAND"#, r#"CAST + CRUSH"#, r#"Product form and grade"#),
            (r#"SAND"#, r#"CAST + CRUSH"#, r#"Where it goes"#),
            (r#"SAND"#, r#"CAST + CRUSH"#, r#"Price"#),
            (r#"SAND"#, r#"ELECTRODE 2"#, r#"Carbon columns"#),
            (r#"SAND"#, r#"ELECTRODE 2"#, r#"Three phases"#),
            (r#"SAND"#, r#"ELECTRODE 2"#, r#"Wear and contamination"#),
            (r#"SAND"#, r#"CHARGE"#, r#"The sinking burden"#),
            (r#"SAND"#, r#"CHARGE"#, r#"When it goes wrong"#),
            (r#"SAND"#, r#"CHARGE"#, r#"Fume loss"#),
            (
                r#"SAND"#,
                r#"ARC CAVITIES"#,
                r#"Where the chemistry happens"#,
            ),
            (r#"SAND"#, r#"ARC CAVITIES"#, r#"Recapture and fume"#),
            (r#"SAND"#, r#"MOLTEN SILICON POOL"#, r#"Silicon hearth"#),
            (r#"SAND"#, r#"MOLTEN SILICON POOL"#, r#"Purity is set here"#),
            (r#"SAND"#, r#"tap hole"#, r#"Opening and closing"#),
            (r#"SAND"#, r#"tap hole"#, r#"Fume and environment"#),
            (r#"SAND"#, r#"tap hole"#, r#"Wear"#),
            (r#"SAND"#, r#"CO + SiO fume"#, r#"Off-gas"#),
            (r#"SAND"#, r#"CO + SiO fume"#, r#"Silica fume"#),
            (r#"SAND"#, r#"CO + SiO fume"#, r#"Yield lost"#),
            (r#"SAND"#, r#"electricity"#, r#"The cost line"#),
            (r#"SAND"#, r#"electricity"#, r#"Power contracts"#),
            (r#"SAND"#, r#"electricity"#, r#"What it means for chips"#),
            (r#"SAND"#, r#"World total"#, r#"Concentration"#),
            (r#"SAND"#, r#"World total"#, r#"Trade pressure"#),
            (r#"SAND"#, r#"World total"#, r#"Price"#),
            (r#"SAND"#, r#"Spruce Pine"#, r#"Crucible quartz chokepoint"#),
            (r#"SAND"#, r#"Spruce Pine"#, r#"Helene timeline"#),
            (r#"SAND"#, r#"Spruce Pine"#, r#"No easy substitute"#),
            (r#"SAND"#, r#"Ferroglobe"#, r#"Q2 2026"#),
            (r#"SAND"#, r#"Ferroglobe"#, r#"Read-through"#),
            (r#"SAND"#, r#"Ferroglobe"#, r#"Other listed names"#),
            (r#"POLYSILICON"#, r#"MG-Si"#, r#"Why go through chlorides"#),
            (r#"POLYSILICON"#, r#"MG-Si"#, r#"Where the feed comes from"#),
            (
                r#"POLYSILICON"#,
                r#"Si + HCl"#,
                r#"Trichlorosilane synthesis"#,
            ),
            (r#"POLYSILICON"#, r#"Si + HCl"#, r#"TCS properties"#),
            (r#"POLYSILICON"#, r#"Si + HCl"#, r#"Alternative: granules"#),
            (r#"POLYSILICON"#, r#"DISTILL"#, r#"Boiling points"#),
            (r#"POLYSILICON"#, r#"DISTILL"#, r#"Spec ladder"#),
            (r#"POLYSILICON"#, r#"DISTILL"#, r#"Capacity"#),
            (r#"POLYSILICON"#, r#"BELL JAR"#, r#"Deposition batch"#),
            (r#"POLYSILICON"#, r#"BELL JAR"#, r#"Growth and power"#),
            (r#"POLYSILICON"#, r#"BELL JAR"#, r#"After the batch"#),
            (r#"POLYSILICON"#, r#"CRUSH"#, r#"Crushing and etching"#),
            (r#"POLYSILICON"#, r#"CRUSH"#, r#"Popcorn grading"#),
            (r#"POLYSILICON"#, r#"CRUSH"#, r#"Etch capacity"#),
            (r#"POLYSILICON"#, r#"POLY"#, r#"What the customer buys"#),
            (r#"POLYSILICON"#, r#"POLY"#, r#"Chunks vs granules"#),
            (r#"POLYSILICON"#, r#"POLY"#, r#"Demand"#),
            (
                r#"POLYSILICON"#,
                r#"WATER-COOLED STEEL BELL JAR"#,
                r#"Why a cold wall"#,
            ),
            (
                r#"POLYSILICON"#,
                r#"WATER-COOLED STEEL BELL JAR"#,
                r#"Heat recovery"#,
            ),
            (
                r#"POLYSILICON"#,
                r#"WATER-COOLED STEEL BELL JAR"#,
                r#"Popcorn causes"#,
            ),
            (r#"POLYSILICON"#, r#"U-bridge"#, r#"Rod pairs"#),
            (r#"POLYSILICON"#, r#"U-bridge"#, r#"Failure risks"#),
            (r#"POLYSILICON"#, r#"graphite chucks"#, r#"Contacts"#),
            (r#"POLYSILICON"#, r#"graphite chucks"#, r#"Contamination"#),
            (
                r#"POLYSILICON"#,
                r#"slim rod 20 mm"#,
                r#"Growth to 150-180 mm"#,
            ),
            (r#"POLYSILICON"#, r#"slim rod 20 mm"#, r#"Popcorn"#),
            (r#"POLYSILICON"#, r#"slim rod 20 mm"#, r#"EG is not solar"#),
            (r#"POLYSILICON"#, r#"Special EG"#, r#"Purity spec"#),
            (r#"POLYSILICON"#, r#"Special EG"#, r#"Why chips need it"#),
            (r#"POLYSILICON"#, r#"Special EG"#, r#"A moving ladder"#),
            (r#"POLYSILICON"#, r#"Tongwei"#, r#"Capacity ranks"#),
            (r#"POLYSILICON"#, r#"Tongwei"#, r#"Price glut"#),
            (r#"POLYSILICON"#, r#"Tongwei"#, r#"Relevance to chips"#),
            (r#"POLYSILICON"#, r#"Wacker"#, r#"The leading EG supplier"#),
            (r#"POLYSILICON"#, r#"Wacker"#, r#"2025 expansion"#),
            (r#"POLYSILICON"#, r#"Wacker"#, r#"Energy intensity"#),
            (r#"POLYSILICON"#, r#"Hemlock"#, r#"US chip-grade supply"#),
            (r#"POLYSILICON"#, r#"Hemlock"#, r#"Section 232 prices"#),
            (r#"POLYSILICON"#, r#"Hemlock"#, r#"Effect on makers"#),
            (r#"MELT + PULL"#, r#"LOAD"#, r#"The charge"#),
            (r#"MELT + PULL"#, r#"LOAD"#, r#"Dopant compromise"#),
            (r#"MELT + PULL"#, r#"LOAD"#, r#"Batch economics"#),
            (r#"MELT + PULL"#, r#"~1414 C, argon"#, r#"Melt under argon"#),
            (r#"MELT + PULL"#, r#"~1414 C, argon"#, r#"What argon does"#),
            (
                r#"MELT + PULL"#,
                r#"~1414 C, argon"#,
                r#"Slow thermal loop"#,
            ),
            (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"Seed and neck"#),
            (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"The limit"#),
            (r#"MELT + PULL"#, r#"SEED + NECK"#, r#"Failure mode"#),
            (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Flaring out"#),
            (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Temperature takes over"#),
            (r#"MELT + PULL"#, r#"SHOULDER"#, r#"Scrap and risk"#),
            (r#"MELT + PULL"#, r#"300 mm, slow"#, r#"Body growth"#),
            (
                r#"MELT + PULL"#,
                r#"300 mm, slow"#,
                r#"Throughput arithmetic"#,
            ),
            (
                r#"MELT + PULL"#,
                r#"300 mm, slow"#,
                r#"Controls during the body"#,
            ),
            (r#"MELT + PULL"#, r#"TAIL"#, r#"End cone"#),
            (r#"MELT + PULL"#, r#"TAIL"#, r#"Segregation"#),
            (r#"MELT + PULL"#, r#"TAIL"#, r#"Yield cost"#),
            (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"A consumable"#),
            (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"Supply"#),
            (r#"MELT + PULL"#, r#"QUARTZ CRUCIBLE"#, r#"Why it matters"#),
            (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Melt convection"#),
            (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Magnetic damping"#),
            (r#"MELT + PULL"#, r#"MOLTEN SILICON"#, r#"Axial gradient"#),
            (r#"MELT + PULL"#, r#"GRAPHITE HEATER"#, r#"Hot zone"#),
            (
                r#"MELT + PULL"#,
                r#"GRAPHITE HEATER"#,
                r#"Graphite and SiO"#,
            ),
            (r#"MELT + PULL"#, r#"GRAPHITE HEATER"#, r#"Power per kg"#),
            (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"The envelope"#),
            (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"Diameter control"#),
            (r#"MELT + PULL"#, r#"PULL CHAMBER"#, r#"Failure modes"#),
            (r#"MELT + PULL"#, r#"Oxygen"#, r#"Where oxygen comes from"#),
            (r#"MELT + PULL"#, r#"Oxygen"#, r#"Villain and tool"#),
            (r#"MELT + PULL"#, r#"Oxygen"#, r#"Control at 300 mm"#),
            (r#"MELT + PULL"#, r#"Dash neck"#, r#"Necking"#),
            (r#"MELT + PULL"#, r#"Dash neck"#, r#"The trade-off"#),
            (r#"MELT + PULL"#, r#"Dash neck"#, r#"Pull rate in context"#),
            (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"Top two"#),
            (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"The cycle"#),
            (r#"MELT + PULL"#, r#"Shin-Etsu"#, r#"Pricing power"#),
            (r#"MELT + PULL"#, r#"Yield"#, r#"Structure losses"#),
            (r#"MELT + PULL"#, r#"Yield"#, r#"Cyclicality"#),
            (r#"MELT + PULL"#, r#"Yield"#, r#"Open problems"#),
            (r#"INGOT"#, r#"AS-PULLED"#, r#"A rough cylinder"#),
            (r#"INGOT"#, r#"AS-PULLED"#, r#"Handling"#),
            (r#"INGOT"#, r#"AS-PULLED"#, r#"Capacity limit"#),
            (r#"INGOT"#, r#"CROP"#, r#"The cuts"#),
            (r#"INGOT"#, r#"CROP"#, r#"Measured, not fixed"#),
            (r#"INGOT"#, r#"CROP"#, r#"Missed defects"#),
            (r#"INGOT"#, r#"TEST"#, r#"Orientation check"#),
            (r#"INGOT"#, r#"TEST"#, r#"Orientation matters"#),
            (r#"INGOT"#, r#"TEST"#, r#"Last cheap point"#),
            (r#"INGOT"#, r#"GRIND OD"#, r#"Grinding to size"#),
            (r#"INGOT"#, r#"GRIND OD"#, r#"Why diameter matters"#),
            (r#"INGOT"#, r#"GRIND OD"#, r#"Silicon lost"#),
            (r#"INGOT"#, r#"NOTCH"#, r#"The groove"#),
            (r#"INGOT"#, r#"NOTCH"#, r#"Why <110>"#),
            (r#"INGOT"#, r#"NOTCH"#, r#"Notch vs flat"#),
            (r#"INGOT"#, r#"WIRE SAW"#, r#"Wire web"#),
            (r#"INGOT"#, r#"WIRE SAW"#, r#"Kerf"#),
            (r#"INGOT"#, r#"WIRE SAW"#, r#"Cut geometry"#),
            (r#"INGOT"#, r#"CROP LINE"#, r#"Where the lines go"#),
            (r#"INGOT"#, r#"CROP LINE"#, r#"Decided by measurement"#),
            (r#"INGOT"#, r#"CROP LINE"#, r#"Trade-off"#),
            (r#"INGOT"#, r#"tail cone off"#, r#"Most contaminated"#),
            (r#"INGOT"#, r#"tail cone off"#, r#"Slip dislocations"#),
            (r#"INGOT"#, r#"tail cone off"#, r#"Value hit"#),
            (r#"INGOT"#, r#"mounting beam"#, r#"Glue-on plate"#),
            (r#"INGOT"#, r#"mounting beam"#, r#"Thickness reference"#),
            (r#"INGOT"#, r#"mounting beam"#, r#"Alignment"#),
            (r#"INGOT"#, r#"Orientation"#, r#"Miller indices"#),
            (r#"INGOT"#, r#"Orientation"#, r#"Why {100}"#),
            (r#"INGOT"#, r#"Orientation"#, r#"Industry constant"#),
            (r#"INGOT"#, r#"Doping"#, r#"Dopants"#),
            (r#"INGOT"#, r#"Doping"#, r#"Segregation"#),
            (r#"INGOT"#, r#"Doping"#, r#"Purity and binning"#),
            (r#"INGOT"#, r#"775 um"#, r#"Size ladder"#),
            (r#"INGOT"#, r#"775 um"#, r#"Why thicker"#),
            (r#"INGOT"#, r#"775 um"#, r#"Why 450 mm died"#),
            (r#"INGOT"#, r#"Pricing"#, r#"Long-term agreements"#),
            (r#"INGOT"#, r#"Pricing"#, r#"Tightening since"#),
            (r#"INGOT"#, r#"Pricing"#, r#"Investor read"#),
            (r#"INGOT"#, r#"Five firms"#, r#"Share"#),
            (r#"INGOT"#, r#"Five firms"#, r#"Moat"#),
            (r#"INGOT"#, r#"Five firms"#, r#"Analyst moves"#),
            (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Diamond wire"#),
            (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Damage layer"#),
            (r#"SLICE + POLISH"#, r#"SLICE"#, r#"Kerf"#),
            (r#"SLICE + POLISH"#, r#"GRIND/LAP"#, r#"Lap or grind"#),
            (r#"SLICE + POLISH"#, r#"GRIND/LAP"#, r#"How much comes off"#),
            (
                r#"SLICE + POLISH"#,
                r#"GRIND/LAP"#,
                r#"Purpose and failure"#,
            ),
            (r#"SLICE + POLISH"#, r#"ETCH"#, r#"Etching the damage away"#),
            (r#"SLICE + POLISH"#, r#"ETCH"#, r#"One patent sequence"#),
            (r#"SLICE + POLISH"#, r#"ETCH"#, r#"Alkali vs acid"#),
            (r#"SLICE + POLISH"#, r#"EDGE"#, r#"A rounded rim"#),
            (r#"SLICE + POLISH"#, r#"EDGE"#, r#"Why it matters"#),
            (r#"SLICE + POLISH"#, r#"EDGE"#, r#"Order of steps"#),
            (r#"SLICE + POLISH"#, r#"POLISH"#, r#"DSP then final polish"#),
            (r#"SLICE + POLISH"#, r#"POLISH"#, r#"Nanotopography"#),
            (r#"SLICE + POLISH"#, r#"POLISH"#, r#"Result and control"#),
            (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Clean and inspect"#),
            (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Metrology example"#),
            (r#"SLICE + POLISH"#, r#"CLEAN"#, r#"Qualification"#),
            (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Web geometry"#),
            (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Wear"#),
            (r#"SLICE + POLISH"#, r#"WIRE WEB"#, r#"Fine wire limits"#),
            (
                r#"SLICE + POLISH"#,
                r#"coolant spray"#,
                r#"Cooling and flushing"#,
            ),
            (r#"SLICE + POLISH"#, r#"coolant spray"#, r#"Swarf"#),
            (r#"SLICE + POLISH"#, r#"coolant spray"#, r#"Water not oil"#),
            (r#"SLICE + POLISH"#, r#"kerf"#, r#"Kerf numbers"#),
            (r#"SLICE + POLISH"#, r#"kerf"#, r#"What it costs"#),
            (r#"SLICE + POLISH"#, r#"kerf"#, r#"Thickness budget"#),
            (
                r#"SLICE + POLISH"#,
                r#"SILICON INGOT"#,
                r#"Feed into the saw"#,
            ),
            (r#"SLICE + POLISH"#, r#"SILICON INGOT"#, r#"Wire drag"#),
            (
                r#"SLICE + POLISH"#,
                r#"SILICON INGOT"#,
                r#"Highest-value failure"#,
            ),
            (r#"SLICE + POLISH"#, r#"Preston"#, r#"Preston's law"#),
            (r#"SLICE + POLISH"#, r#"Preston"#, r#"Slurry pH"#),
            (r#"SLICE + POLISH"#, r#"Preston"#, r#"Used at both ends"#),
            (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Two big suppliers"#),
            (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Competition"#),
            (r#"SLICE + POLISH"#, r#"CMP tools"#, r#"Scope note"#),
            (r#"SLICE + POLISH"#, r#"CMP slurry"#, r#"Slurry share"#),
            (r#"SLICE + POLISH"#, r#"CMP slurry"#, r#"Market structure"#),
            (
                r#"SLICE + POLISH"#,
                r#"CMP slurry"#,
                r#"Qualified per line"#,
            ),
            (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"What pads do"#),
            (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"Share"#),
            (r#"SLICE + POLISH"#, r#"CMP pads"#, r#"Wear"#),
            (
                r#"SLICE + POLISH"#,
                r#"wire breakage and wear"#,
                r#"Wear raises kerf"#,
            ),
            (
                r#"SLICE + POLISH"#,
                r#"wire breakage and wear"#,
                r#"Thinner is weaker"#,
            ),
            (
                r#"SLICE + POLISH"#,
                r#"wire breakage and wear"#,
                r#"Other chokepoints"#,
            ),
        ];
        for (p, c, s) in keys {
            let v = lookup(p, c, s).unwrap_or_else(|| panic!("missing {p}/{c}/{s}"));
            check(&v, &format!("{p}/{c}/{s}"));
        }
    }
}
