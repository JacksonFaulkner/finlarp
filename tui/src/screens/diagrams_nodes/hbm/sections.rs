// HBM STACK sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/hbm_sections.py. Beat counts: 3, 5, 5, 3, 3, 3, 3, 3, 3, 3. Section 10 is
// the sources page, which is also a picture: source cards light up in groups.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("DRAM stacked beside the processor", BEAT_MS)
        .note(
            "HBM stacks DRAM dies on a base die and puts the stack next to the processor on an interposer.",
            "The package from the front: four stacks, a purple GPU, the grey interposer and the green substrate.",
        )
        .detail(
            "Very wide, very close memory.",
            &["1024 bits per HBM3 stack", "6.4 Gb/s per pin, 819 GB/s per stack (JEDEC JESD238)"],
        ),
    Beat::new("microbumps join the dies", BEAT_MS)
        .note(
            "Inside the stack, microbumps join each die to the next, and copper TSVs run up through every die.",
            "The dies pull apart and yellow microbumps show in each gap.",
        )
        .detail(
            "One bad die or joint spoils the stack.",
            &["Microbump pitch about 40 um, toward 10 um (SemiEngineering)"],
        ),
    Beat::new("a read reaches the GPU", BEAT_MS)
        .note(
            "Data runs down the TSVs to the base die and across the interposer to the GPU.",
            "Cyan dots leave each stack's PHY edge and cross the interposer to the purple GPU; the outer stacks arc over the inner ones.",
        )
        .detail(
            "Every stack's bus feeds the same GPU at once.",
            &["819 GB/s per HBM3 stack (JEDEC JESD238)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("DRAM dies: the memory itself", BEAT_MS)
        .note(
            "The memory itself, stacked 4 to 16 high. Each die is a full DRAM chip with its own banks and arrays.",
            "The orange DRAM dies, with the copper TSVs running through them.",
        )
        .detail(
            "Stacking puts many dies in the footprint of one, beside the GPU.",
            &["24 or 32 Gb per die (HBM4)", "HBM4 allows 4, 8, 12 or 16-high (JEDEC JESD270-4)"],
        ),
    Beat::new("base logic die: the interface to the GPU", BEAT_MS)
        .note(
            "The base logic die is the interface to the GPU, plus test logic; the TSVs land on it.",
            "The dies lift off and the blue base die stays, with its copper landing pads on top.",
        )
        .detail(
            "It decides how fast the stack can talk to the GPU. For HBM4 it is reportedly on foundry logic.",
            &["PHY plus test logic (page section 2)", "HBM4 base die on foundry logic (reported)"],
        ),
    Beat::new("TSVs: copper through each thinned die", BEAT_MS)
        .note(
            "Copper wires straight through each thinned die carry signals and power up and down the stack.",
            "The copper columns show through the cut face of the stack.",
        )
        .detail(
            "Only possible in thinned dies.",
            &["Dies thinned to 30-50 um (SemiEngineering)"],
        ),
    Beat::new("microbumps", BEAT_MS)
        .note(
            "Tiny joints that connect each die's TSVs to the next die.",
            "The dies pull apart and the yellow microbumps show in every gap.",
        )
        .detail(
            "Pitch shrinking from about 40 um.",
            &["Microbump pitch about 40 um, toward 10 um (SemiEngineering)"],
        ),
    Beat::new("silicon interposer and GPU", BEAT_MS)
        .note(
            "A slab of silicon wires the stacks to the GPU with thousands of short lines; the GPU is the processor the stacks feed.",
            "The grey interposer and the purple GPU appear beside the stack, on the green substrate.",
        )
        .detail(
            "The interposer is part of CoWoS packaging.",
            &["CoWoS (TSMC)", "819 GB/s per HBM3 stack (JEDEC JESD238)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. DRAM dies made and stacked one by one", BEAT_MS)
        .note(
            "DRAM dies made on DRAM wafers are placed one at a time onto the base die.",
            "Dies drop in one after another onto the blue base die.",
        )
        .detail(
            "Every die must be good: a bad one spoils the stack.",
            &["One bad die or joint spoils the stack (page section 9)"],
        ),
    Beat::new("2. thinned, with TSVs and bumps", BEAT_MS)
        .note(
            "Each die is thinned and carries TSVs and microbumps.",
            "The stack pulls apart and the yellow bumps show between the dies.",
        )
        .detail(
            "Thinning keeps the stack under the height limit.",
            &["Dies 30-50 um (SemiEngineering)"],
        ),
    Beat::new("3. bonded onto the base die", BEAT_MS)
        .note(
            "The dies are bonded down onto the base die into one stack.",
            "The gaps close and the stack comes back together, bumps still between the dies.",
        )
        .detail(
            "HBM4 keeps microbumps at this step.",
            &["HBM4 keeps microbumps (SemiEngineering)"],
        ),
    Beat::new("4. tested through the TSVs", BEAT_MS)
        .note(
            "The finished stack is tested by reading through its TSVs.",
            "A yellow test field lights on the base die, and the stack stands on it.",
        )
        .detail(
            "A bad die or joint spoils the whole stack.",
            &["Stack yield: one bad die or joint spoils the stack (page section 9)"],
        ),
    Beat::new("5. mounted beside the GPU", BEAT_MS)
        .note(
            "The stack is mounted on the interposer beside the GPU, and its bus runs across to the processor.",
            "The interposer and GPU appear; cyan dots run from the stack's PHY across to the GPU.",
        )
        .detail(
            "Stacks and GPU share one interposer in CoWoS packaging.",
            &["CoWoS packaging (TSMC)", "819 GB/s per HBM3 stack (JEDEC JESD238)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("data pins: 1024 to 2048", BEAT_MS)
        .note(
            "HBM4 doubles the interface width of HBM3, from 1024 data pins to 2048.",
            "Two bars: the HBM4 bar twice as tall as the HBM3 bar.",
        )
        .detail(
            "More pins, more channels.",
            &["HBM3 1024, HBM4 2048 data pins (JEDEC JESD238, JESD270-4)"],
        ),
    Beat::new("rate per pin: 6.4 to 8 Gb/s", BEAT_MS)
        .note(
            "The per-pin rate rises too, at the JEDEC baseline.",
            "Two bars, the second a quarter taller than the first.",
        )
        .detail(
            "Width and rate multiply, so both set the bandwidth of a stack.",
            &["HBM3 6.4 Gb/s, HBM4 8 Gb/s per pin"],
        ),
    Beat::new("bandwidth per stack: 819 GB/s to 2 TB/s", BEAT_MS)
        .note(
            "Width and rate together give up to 2 TB/s per HBM4 stack.",
            "Two bars, the second about 2.5 times the first.",
        )
        .detail(
            "Capacity rises to 64 GB at 16-high.",
            &[
                "HBM3: 819 GB/s per stack (JEDEC JESD238)",
                "HBM4: up to 2 TB/s per stack (JEDEC JESD270-4)",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("8-high, under the height limit", BEAT_MS)
        .note(
            "Eight DRAM dies on the base die, well under the height limit.",
            "An 8-high stack standing well under the pink limit plane.",
        )
        .detail(
            "Height includes every die and joint.",
            &["Height limit 720 um (press reports)"],
        ),
    Beat::new("12-high: heat starts to build", BEAT_MS)
        .note(
            "Four more dies add capacity and height, and the heat from the lower dies starts to build.",
            "The stack grows to 12 dies and its lower dies start to glow.",
        )
        .detail(
            "Taller stacks add capacity but trap more heat.",
            &["Taller stacks trap more heat (page section 5)"],
        ),
    Beat::new("16-high: the limit rose from 720 to 775 um", BEAT_MS)
        .note(
            "Sixteen dies need the limit raised from 720 to 775 um; the lower dies run hottest.",
            "The stack reaches 16 and pokes through the old plane; the plane rises; the bottom glows.",
        )
        .detail(
            "Heat leaves through the top, so the bottom of a tall stack runs hottest.",
            &["720 -> 775 um (press reports)", "Dies thinned to 30-50 um (SemiEngineering)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("microbumps between the dies", BEAT_MS)
        .note(
            "Opened up: microbumps sit between every pair of dies.",
            "The stack is pulled apart and the yellow bumps show at each joint.",
        )
        .detail(
            "Bump pitch about 40 um, shrinking.",
            &["Microbump pitch about 40 um (SemiEngineering)"],
        ),
    Beat::new("bonded on bumps", BEAT_MS)
        .note(
            "Closed, each joint still leaves a small gap.",
            "The stack closes up with the bumps still between the dies.",
        )
        .detail(
            "HBM4 keeps microbumps.",
            &["HBM4 keeps microbumps (SemiEngineering)"],
        ),
    Beat::new("hybrid bonding: no gap", BEAT_MS)
        .note(
            "Hybrid bonding joins copper directly; the gaps vanish and the stack gets shorter.",
            "The bumps disappear and the stack shrinks.",
        )
        .detail(
            "It is harder to make with good yield, so HBM4 postponed it.",
            &["Hybrid bonding expected beyond 16-high (SemiEngineering)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("the interposer's short, dense wiring", BEAT_MS)
        .note(
            "The interposer carries the wide buses between every stack and the GPU, on fine wiring.",
            "Close on the grey wiring lines of the interposer between a stack and the GPU.",
        )
        .detail(
            "A slab of silicon wires the stacks to the GPU with thousands of short lines.",
            &["Silicon interposer (page section 2)"],
        ),
    Beat::new("on a package substrate", BEAT_MS)
        .note(
            "The interposer sits on a package substrate that connects to the board.",
            "The whole package from the side: the stacks, GPU, interposer and substrate in layers.",
        )
        .detail(
            "Chip-on-Wafer-on-Substrate: TSMC's packaging.",
            &["CoWoS (TSMC)"],
        ),
    Beat::new("packaging capacity sets output", BEAT_MS)
        .note(
            "Almost every high-end AI accelerator uses CoWoS, and its capacity, not wafers, has limited how many ship.",
            "The package from above: four stacks and the GPU on the interposer.",
        )
        .detail(
            "TSMC has been expanding it with outside assembly houses.",
            &["CoWoS capacity constraint (Tom's Hardware, TrendForce)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note(
            "Micron makes HBM.",
            "The first wafer panel lights gold, tagged with Micron's name.",
        )
        .detail(
            "Market share is covered on the market pages.",
            &["HBM makers: SK hynix, Samsung, Micron (page section 8)"],
        ),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note(
            "SK hynix makes HBM.",
            "The second wafer panel lights gold, tagged with SK hynix.",
        )
        .detail(
            "Market share is covered on the market pages.",
            &["SK hynix ticker: 000660.KS (page section 8)"],
        ),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note(
            "Samsung makes HBM. Packaging is led by TSMC, with outside assembly houses.",
            "The third wafer panel lights gold, tagged with Samsung.",
        )
        .detail(
            "Packaging: TSMC (TSM), with ASE (ASX) and Amkor (AMKR).",
            &["Samsung ticker: 005930.KS (page section 8)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("packaging capacity", BEAT_MS)
        .note(
            "Finished GPUs wait on interposer packaging; one supplier does most of it.",
            "Purple GPU dies queue on a grey packaging line.",
        )
        .detail(
            "Capacity has been expanding but has stayed tight.",
            &["CoWoS (TSMC); CoWoS capacity shortage (TrendForce)"],
        ),
    Beat::new("stack yield falls with height", BEAT_MS)
        .note(
            "A stack is only good if every die and joint is good, so yield drops as stacks grow.",
            "Three orange bars for 8-, 12- and 16-high stacks, each one shorter than the last.",
        )
        .detail(
            "The bars show the direction only; the page gives no yield figures.",
            &["One bad die or joint spoils the stack (page section 9)"],
        ),
    Beat::new("heat in tall stacks", BEAT_MS)
        .note(
            "Heat from the lower dies must pass through the whole stack.",
            "A 16-high stack glowing hot at the bottom, with the heat leaving through the top.",
        )
        .detail(
            "Limits how fast and how tall stacks can go.",
            &["Heat leaves through the top (page section 5)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("JEDEC and SemiEngineering sources", BEAT_MS)
        .note(
            "Three source cards light up: the JEDEC standards for HBM3 and HBM4, and the SemiEngineering piece on microbumps.",
            "Three cards lit gold, each tagged with its source.",
        )
        .detail(
            "The page's numbers come from these standards and reports.",
            &["JESD238 (HBM3): 6.4 Gb/s, 819 GB/s", "JESD270-4 (HBM4): 2048 bits, 8 Gb/s, up to 2 TB/s"],
        ),
    Beat::new("Tom's Hardware sources", BEAT_MS)
        .note(
            "Two more cards: Tom's Hardware on hybrid bonding and on CoWoS capacity.",
            "Two more cards light, tagged Tom's Hardware.",
        )
        .detail(
            "The 720 to 775 um height limit and the CoWoS capacity limit come from press reports.",
            &["Height limit 720 -> 775 um (Tom's Hardware)", "CoWoS capacity (Tom's Hardware)"],
        ),
    Beat::new("TrendForce and PC Watch sources", BEAT_MS)
        .note(
            "The last two cards: TrendForce on CoWoS capacity and PC Watch on the HBM3 channel count. HBM4 base dies on foundry logic are reported, not confirmed here.",
            "The last two cards light, tagged TrendForce and PC Watch.",
        )
        .detail(
            "Reported claims are marked as such on the page.",
            &["CoWoS capacity shortage (TrendForce)", "HBM3 channels 8 to 16 (PC Watch)"],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/hbm_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order; section 10 is the sources.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [3, 5, 5, 3, 3, 3, 3, 3, 3, 3]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }

    #[test]
    fn one_scene_per_heading_of_the_page() {
        let heads = crate::screens::diagrams_desc::visual("HBM STACK")
            .expect("HBM STACK page text")
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(
            heads,
            SECTIONS.len(),
            "one picture per # heading, sources included"
        );
    }
}
