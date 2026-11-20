// POLYSILICON sections 1-10: each a Blender picture (tools/pbr3d/blender/fab_poly.py), three beats
// each. Section 10 is the sources page, drawn as cards filing into a stack.

use super::super::blender::{Cell, clip};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 5200;

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();
static S10: Cell = std::sync::OnceLock::new();

const S1_BEATS: &[Beat] = &[
    Beat::new("MG-Si lumps go in at the first station", BEAT_MS)
        .note(
            "Metallurgical silicon from SAND moves along the line: the feed, then the bed, then the column.",
            "lumps moving along the line from the first station",
        )
        .detail(
            "Polysilicon is the input to MELT + PULL, so this chain sets the purity of every crystal.",
            &["MG-Si is 98-99% pure", "Feed from SAND", "Output is 9N+ chunks"],
        ),
    Beat::new("the silicon is turned into TCS, then purified by distillation", BEAT_MS)
        .note(
            "The feed reacts with HCl in the bed, and the gas is distilled clean in the column.",
            "lumps going into the bed and then the column",
        )
        .detail(
            "Distillation is where the silicon becomes clean enough to deposit.",
            &["Si + HCl at about 300 C", "Distillation at 30-60 C"],
        ),
    Beat::new("rods grow in the bell jar, and chunks come out", BEAT_MS)
        .note(
            "Purified TCS deposits silicon on the rods. The rods are then crushed into chunks.",
            "chunks moving into the bin at the end of the line",
        )
        .detail(
            "The chunks are what the customer buys.",
            &["Deposition near 1100 C", "Chunks are the 9N+ product"],
        ),
];

const S2_BEATS: &[Beat] = &[
    Beat::new("the bell jar: gas in at the base, a rod pair in the middle", BEAT_MS)
        .note(
            "TCS and hydrogen come in through nozzles in the base plate, and the exhaust leaves the same plate.",
            "gas nozzles in the base and the rod pair in the jar",
        )
        .detail(
            "The jar is water-cooled steel, so the walls stay cold and the silicon does not plate them.",
            &["Water-cooled steel jar", "Gas in and out through the base"],
        ),
    Beat::new("current heats the rods to about 1100 C", BEAT_MS)
        .note(
            "The current goes up one rod, over the bridge and down the other. The rods are their own heater.",
            "the glowing core and the current in the rods",
        )
        .detail(
            "Self-heating is why the jar needs no separate furnace.",
            &["Rods heated by their own current", "U-bridge joins the pair"],
        ),
    Beat::new("silicon deposits, and the rods grow toward 150-180 mm", BEAT_MS)
        .note(
            "Deposition thickens the rods over the batch. A slim 20 mm rod becomes a 150-180 mm rod.",
            "the rods thickening through the batch",
        )
        .detail(
            "The growth rate sets the length of the batch.",
            &["Slim rod 20 mm", "Final rods 150-180 mm", "Growth up to 1.9 mm/h"],
        ),
];

const S3_BEATS: &[Beat] = &[
    Beat::new("TCS synthesis: Si + 3HCl gives SiHCl3 + H2 at about 300 C", BEAT_MS)
        .note(
            "Silicon and HCl make trichlorosilane and hydrogen in a fluidised bed, with some SiCl4 alongside.",
            "atoms rearranging into the trichlorosilane molecule",
        )
        .detail(
            "This is the step that makes the gas that can be distilled.",
            &["Si + 3HCl gives SiHCl3 + H2", "Fluidised bed near 300 C", "Practical mix includes SiCl4 (Fraunhofer)"],
        ),
    Beat::new("deposition: SiHCl3 + H2 gives Si + 3HCl on the rods", BEAT_MS)
        .note(
            "On the hot rods, TCS and hydrogen leave silicon behind, and HCl goes out with the gas.",
            "atoms moving onto the rod surface and HCl leaving",
        )
        .detail(
            "This is the main reaction: the silicon that becomes the product.",
            &["Main reaction on rods near 1100 C", "HCl is recovered and re-fed"],
        ),
    Beat::new("side reaction: 4SiHCl3 gives Si + 3SiCl4 + 2H2, which makes STC", BEAT_MS)
        .note(
            "A side reaction makes STC. It is recovered, and in modern routes it can be hydrogenated back to TCS.",
            "STC molecules forming beside the rod",
        )
        .detail(
            "The side reaction costs feed; recovering STC gets some of it back.",
            &["Side reaction (textbook)", "STC is a byproduct"],
        ),
];

const S4_BEATS: &[Beat] = &[
    Beat::new("rods grow from 20 mm to 150-180 mm", BEAT_MS)
        .note(
            "The bars show a slim rod going in and a thick rod coming out.",
            "the slim rod bar and the final rod bar",
        )
        .detail(
            "Diameter is the progress measure through the batch.",
            &["20 mm in", "150-180 mm out", "Growth up to 1.9 mm/h"],
        ),
    Beat::new("electricity: 60-70 kWh per kg for solar grade in 2023", BEAT_MS)
        .note(
            "Power is the largest cost: 60-70 kWh per kg for solar grade in 2023, most of it in the CVD step.",
            "the power bar filling to 60-70",
        )
        .detail(
            "Electronic grade uses more power than solar grade.",
            &["60-70 kWh/kg (CPIA and Fraunhofer ISE, 2023)", "About 35-45 kWh/kg in CVD", "TCS synthesis about 9 kWh/kg"],
        ),
    Beat::new("deposition runs at about 1100 C at the rod surface", BEAT_MS)
        .note(
            "The rod surface is the hot spot. Patents quote 1000-1150 C for the deposition range.",
            "the temperature bar rising to the rod surface",
        )
        .detail(
            "Temperature is what drives the deposition.",
            &["About 1100 C at the rod surface", "1000-1150 C in patents"],
        ),
];

const S5_BEATS: &[Beat] = &[
    Beat::new("special EG allows about 1.5e12 donor atoms per cm3", BEAT_MS)
        .note(
            "The electronic-grade donor limit is tight: about 1.5e12 phosphorus, arsenic or antimony atoms per cm3.",
            "the short bar for special electronic grade",
        )
        .detail(
            "Base metals are held below 0.1 ppbw as well.",
            &["Special EG: donors <= 1.5e12 atoms/cm3", "Base metals <= 0.1 ppbw (GB/T 12963-2022)"],
        ),
    Beat::new("EG3 allows about 5e12", BEAT_MS)
        .note(
            "A looser electronic grade allows about 5e12 donor atoms per cm3.",
            "the middle bar for EG3",
        )
        .detail(
            "Each grade sets a different donor limit.",
            &["EG3: donors about 5e12 atoms/cm3"],
        ),
    Beat::new("solar grade allows about 2.5e14, about 100 times dirtier", BEAT_MS)
        .note(
            "Solar grade allows donors about 100 times higher than special electronic grade. The bar is much taller because the scale is logarithmic.",
            "the tall solar bar",
        )
        .detail(
            "Each step right on the scale is ten times dirtier.",
            &["Solar: donors <= 2.5e14 atoms/cm3", "About 100 times special EG (page)"],
        ),
];

const S6_BEATS: &[Beat] = &[
    Beat::new("Tongwei is the largest maker at 910 thousand tonnes in 2024", BEAT_MS)
        .note(
            "The largest maker is Tongwei at 910 thousand tonnes, with GCL Technology second at 480.",
            "the tallest bar, Tongwei, then GCL",
        )
        .detail(
            "The figures are indicative: one source calls them output, another capacity.",
            &["Tongwei 910 kt", "GCL Technology 480 kt", "2024 ranking (Bernreuter, TaiyangNews)"],
        ),
    Beat::new("Daqo and Xinte follow; Wacker is eighth at about 80", BEAT_MS)
        .note(
            "Daqo is at 350 and Xinte at 300. Wacker, the largest non-Chinese name in this ranking, is eighth at about 80, a capacity figure.",
            "the Daqo and Xinte bars, and the small Wacker bar",
        )
        .detail(
            "Ranks five to ten are Qinghai Lihao, Wacker, Hongyuan and others (page).",
            &["Daqo 350 kt", "Xinte 300 kt", "Wacker about 80 kt (capacity)"],
        ),
    Beat::new("the top four make 65% of 2024 output; China makes 93.5%", BEAT_MS)
        .note(
            "The top four makers produce 65% of 2024 global output. China produces 93.5% of it.",
            "the bracket over the top four and the China share",
        )
        .detail(
            "Almost all of the tonnes are solar grade.",
            &["Top four = 65% of 2024 output", "China = 93.5% of 2024 output (Bernreuter)"],
        ),
];

const S7_BEATS: &[Beat] = &[
    Beat::new("almost all tonnes are solar grade", BEAT_MS)
        .note(
            "Solar is the volume. The solar tower is nearly the whole market.",
            "the tall solar block",
        )
        .detail(
            "Volume and margin point in opposite directions in this market.",
            &["Almost all tonnes are solar"],
        ),
    Beat::new("chip-grade is a small, high-margin niche", BEAT_MS)
        .note(
            "Electronic grade is only about 5% of volume, but needs purity near 11N and earns a high margin.",
            "the small chip-grade block lighting up",
        )
        .detail(
            "Non-Chinese producers still matter in this niche.",
            &["Electronic grade about 5% of volume", "Purity near 11N"],
        ),
    Beat::new("Wacker about 22.6% and Hemlock about 19.2% of EG (low reliability)", BEAT_MS)
        .note(
            "A paid-report aggregator lists these shares for electronic grade. The page treats them as unverified.",
            "the two labelled blocks, marked as low reliability",
        )
        .detail(
            "Tokuyama, Mitsubishi Materials and REC Silicon are the other names usually cited.",
            &["Wacker about 22.6% (low reliability)", "Hemlock about 19.2% (low reliability)", "Shares are not published openly"],
        ),
];

const S8_BEATS: &[Beat] = &[
    Beat::new("9N-11N supply sits with a handful of plants", BEAT_MS)
        .note(
            "Wacker in Germany, Hemlock in Michigan and Tokuyama in Japan make most electronic grade. Wafer makers qualify lots for years, so switching is slow.",
            "a valve on the line that is hard to switch",
        )
        .detail(
            "A plant outage or a qualification gap reaches the whole wafer chain.",
            &["Wacker (Burghausen), Hemlock (Michigan), Tokuyama (Japan)", "Qualification takes years"],
        ),
    Beat::new("China's overcapacity glut hit producers in 2024", BEAT_MS)
        .note(
            "Chinese output piled up in 2024 and prices fell. The top four Chinese producers lost money in the first half.",
            "the glut stacking up beside the chart",
        )
        .detail(
            "The glut is a market problem more than a technology one.",
            &["Top four Chinese producers lost money in H1 2024 (Bernreuter)"],
        ),
    Beat::new("power price decides who survives; Wacker is investing", BEAT_MS)
        .note(
            "Electricity is a large cost line, so power price decides who survives. Wacker is investing to lift hyperpure cleaning capacity by more than 50%.",
            "the power bar set against the price",
        )
        .detail(
            "Hyperpure cleaning is the bottleneck for the top grades.",
            &["Electricity a large cost line", "Wacker: more than 50% more hyperpure cleaning (2024 annual report)"],
        ),
];

const S9_BEATS: &[Beat] = &[
    Beat::new("Tongwei, GCL Technology, Daqo and Xinte", BEAT_MS)
        .note(
            "The four Chinese names at the top of the ranking. Their listings are in Shanghai, Hong Kong and New York.",
            "the first four tiles arriving",
        )
        .detail(
            "Tickers are from the page, not a fetched source.",
            &["Tongwei 600438.SS", "GCL Technology 3800.HK", "Daqo DQ, Xinte 1799.HK"],
        ),
    Beat::new("Wacker, OCI and Tokuyama", BEAT_MS)
        .note(
            "The non-Chinese names in the chain: Wacker Chemie, OCI Holdings and Tokuyama.",
            "the next tiles arriving",
        )
        .detail(
            "Tickers come from general knowledge, not a fetched source.",
            &["Wacker Chemie WCH.DE", "OCI Holdings 010060.KS", "Tokuyama 4043.T"],
        ),
    Beat::new("Hemlock is private: a JV of Dow, Corning and Shin-Etsu", BEAT_MS)
        .note(
            "Hemlock is a joint venture, not a listed company, so it has no ticker here.",
            "the last tile arriving, marked private",
        )
        .detail(
            "Hemlock ownership is from general knowledge.",
            &["Hemlock = private JV (Dow, Corning, Shin-Etsu stakes)"],
        ),
];

const S10_BEATS: &[Beat] = &[
    Beat::new("sources 1 and 2: Bernreuter's top ten makers and TaiyangNews", BEAT_MS)
        .note(
            "Bernreuter's ranking of the top ten makers, and TaiyangNews on the 2024 production split.",
            "two source cards sliding into the stack",
        )
        .detail(
            "The rankings are the basis for the market-share figures.",
            &["[1] Bernreuter, Top Ten Polysilicon Makers (Nov 2025)", "[2] TaiyangNews, China dominates 2024 polysilicon production"],
        ),
    Beat::new("sources 3 and 4: Fraunhofer for power, and the rest of the page", BEAT_MS)
        .note(
            "Fraunhofer ISE for Wacker on the electricity of electronic-grade polysilicon, and the remaining references on the page.",
            "two more cards filing into the stack",
        )
        .detail(
            "The electricity figures are the most cited on this page.",
            &["[3] Fraunhofer ISE for Wacker, EG electricity (Aug 2025)", "[4] further references on the page"],
        ),
    Beat::new("the stack is what a reader keeps", BEAT_MS)
        .note(
            "The sources back the page's numbers; each section names the figures it uses.",
            "the finished stack of cards",
        )
        .detail(
            "Each number carries its source in the section it is in.",
            &["Sources are the page's own list", "Numbers are sourced in each section"],
        ),
];

/// The ten sections, in page order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    || {
        clip(
            &S1,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec1.glb")[..],
            S1_BEATS,
        )
    },
    || {
        clip(
            &S2,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec2.glb")[..],
            S2_BEATS,
        )
    },
    || {
        clip(
            &S3,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec3.glb")[..],
            S3_BEATS,
        )
    },
    || {
        clip(
            &S4,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec4.glb")[..],
            S4_BEATS,
        )
    },
    || {
        clip(
            &S5,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec5.glb")[..],
            S5_BEATS,
        )
    },
    || {
        clip(
            &S6,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec6.glb")[..],
            S6_BEATS,
        )
    },
    || {
        clip(
            &S7,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec7.glb")[..],
            S7_BEATS,
        )
    },
    || {
        clip(
            &S8,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec8.glb")[..],
            S8_BEATS,
        )
    },
    || {
        clip(
            &S9,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec9.glb")[..],
            S9_BEATS,
        )
    },
    || {
        clip(
            &S10,
            &include_bytes!("../../../../../tools/pbr3d/assets/poly_sec10.glb")[..],
            S10_BEATS,
        )
    },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_section_has_three_captioned_beats_and_draws_them() {
        let all = [
            S1_BEATS, S2_BEATS, S3_BEATS, S4_BEATS, S5_BEATS, S6_BEATS, S7_BEATS, S8_BEATS,
            S9_BEATS, S10_BEATS,
        ];
        for (n, beats) in all.iter().enumerate() {
            assert_eq!(beats.len(), 3, "section {}", n + 1);
        }
        for (n, build) in SECTIONS.iter().enumerate() {
            super::super::super::blender::draws_every_beat(
                build().as_ref(),
                &format!("POLYSILICON section {}", n + 1),
            );
        }
    }
}
