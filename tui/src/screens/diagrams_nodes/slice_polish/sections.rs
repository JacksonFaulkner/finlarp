// SLICE + POLISH sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/slice_sections.py. Beats per section: 4, 4, 5, 4, 4, 4, 4, 3, 3, 3. Section 10 is
// the sources page.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("INGOT, then SLICE: the ingot becomes wafers at the saw", BEAT_MS)
        .note(
            "The line starts with the ground ingot and the saw. The wafer carrier moves from INGOT to SLICE, where the wire web cuts the ingot into slices.",
            "seven grey station blocks in a row, the wafer on the track moving from the first two toward the third",
        )
        .detail(
            "Each block is one step, in the order the page lists them.",
            &[
                "INGOT is a ground 300 mm cylinder (page section 1)",
                "SLICE is diamond wire, the first cut (page section 1)",
            ],
        ),
    Beat::new("GRIND/LAP and ETCH remove the saw damage", BEAT_MS)
        .note(
            "After slicing, lapping or grinding flattens the wafer, and etching removes the damaged layer the saw left behind.",
            "the wafer on the track between the lapping station and the etch bath",
        )
        .detail(
            "The saw leaves a cracked layer, and every later step exists to remove it.",
            &[
                "Double-side lapping removes 80 to 200 um in total (page section 4)",
                "Etch removes about 15-25 um after lapping (page section 4)",
            ],
        ),
    Beat::new("EDGE rounds the rim, POLISH makes the face", BEAT_MS)
        .note(
            "The rim is rounded so it does not chip, then the polish pad and slurry make the face flat and mirror-smooth.",
            "the wafer passing the edge station, then the polish station lit as the wafer arrives",
        )
        .detail(
            "Polish is the last removal step, and the flat face it leaves is the reference for lithography.",
            &[
                "Double-side polish removes 10-20 um total (page section 4)",
                "The polished surface is the flat reference for lithography (page section 8)",
            ],
        ),
    Beat::new("CLEAN, inspect, ship", BEAT_MS)
        .note(
            "The last station cleans and inspects the wafer, which then ships to the customer.",
            "the wafer at the last station, with the rest of the line behind it",
        )
        .detail(
            "Customers qualify the wafer, and that qualification is slow to change.",
            &[
                "775 um +/- 25 um thick, TTV 5 um or less (vendor datasheet)",
                "Inspection checks thickness, flatness and particles (textbook)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("the wire web: many parallel wires cut together", BEAT_MS)
        .note(
            "A multi-wire saw holds parallel diamond wires in a web. The wire runs over grooved rollers, so one wire serves every slot.",
            "six horizontal steel wires stretched between two posts, seen from the front",
        )
        .detail(
            "The roller pitch is about the wafer thickness plus the kerf, so the roller set defines the product.",
            &[
                "One wire, many parallel runs over grooved guide rollers (page section 2)",
                "Groove pitch is about wafer thickness plus kerf (page section 2)",
            ],
        ),
    Beat::new("the ingot is fed down into the web", BEAT_MS)
        .note(
            "The ingot is lowered into the web. Each wire pass cuts one slot, and each slot leaves a wafer standing.",
            "the grey ingot coming down through the horizontal wires",
        )
        .detail(
            "Diamond wire cuts by fixed grit, so the cut is brittle fracture rather than loose slurry grinding.",
            &[
                "Every wire is a steel core with diamond grit fixed on it (page section 2)",
                "Diamond wire replaced slurry sawing; it cuts about 2x faster (page section 4)",
            ],
        ),
    Beat::new("coolant washes out the swarf and cools the cut", BEAT_MS)
        .note(
            "A water-based coolant sprays the cut. It cools the wire and the cut zone, and washes out the silicon swarf.",
            "spray falling from two nozzles above the slices, with the wires in the gaps between them",
        )
        .detail(
            "Coolant temperature controls the thermal bow of the wafer, so the flow is a process control point.",
            &[
                "Water-based coolant washes out Si swarf and cools the cut (page section 2)",
                "Coolant temperature sets thermal bow of the wafer (page section 7; textbook)",
            ],
        ),
    Beat::new("a close look at one cut: grit tips chip the silicon", BEAT_MS)
        .note(
            "Up close, the wire is a steel core with diamond grit fixed on it. The grit tips scratch and chip the silicon in the slot, and the slot is the kerf.",
            "the wire passing a slice face, with a few small bright grit tips on it",
        )
        .detail(
            "The kerf is the effective wire diameter including the diamond layer, plus wobble.",
            &[
                "Kerf equals the effective wire diameter plus wobble (page section 2)",
                "Kerf about 125 um for diamond wire today (page section 4)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("slicing: fixed grit cuts by brittle fracture", BEAT_MS)
        .note(
            "Slicing cuts by brittle micro-fracture: the diamond grit on the wire chips the silicon as it passes. The cut leaves a cracked layer microns deep.",
            "a bright wire with grit tips above a silicon block, with chips falling away from the cut",
        )
        .detail(
            "Sawing leaves damage that every later step must remove.",
            &[
                "Slicing is brittle micro-fracture by fixed diamond grit (page section 3)",
                "Sawing leaves a cracked layer microns deep (page section 3)",
            ],
        ),
    Beat::new("lapping: loose slurry between two plates", BEAT_MS)
        .note(
            "Lapping uses loose abrasive slurry between two plates, which work both faces at once. It sets flatness and parallelism.",
            "the upper plate above a wafer on the lower plate, with slurry grains in the gap",
        )
        .detail(
            "Lapping sets flatness and parallelism; it works both faces at once.",
            &[
                "Lapping: loose abrasive slurry between two plates, both faces (page section 3)",
                "Double-side lapping removes 80 to 200 um in total (page section 4)",
            ],
        ),
    Beat::new("grinding: a resin-bond wheel takes 10-20 um off one side", BEAT_MS)
        .note(
            "Grinding is the fixed-abrasive alternative to lapping. A resin-bond wheel turns over the wafer and removes 10 to 20 um from one side.",
            "a tan resin wheel turning above the wafer, lowering toward it",
        )
        .detail(
            "Grinding is faster and can run in-line; lapping is the proven batch process (textbook).",
            &[
                "Resin-bond wheel removes 10-20 um on one side (page section 3, patents)",
                "Lapping and grinding are the two ways to flatten after the saw (page section 3)",
            ],
        ),
    Beat::new("etching: a wet bath strips the damaged layer", BEAT_MS)
        .note(
            "A wet alkali or acid bath removes the damaged layer. Etching is chemical, so it takes off the damage without adding stress.",
            "the wafer in a teal bath as the liquid rises, and the orange damage rings on its faces fading",
        )
        .detail(
            "Non-uniform etch from bath flow or temperature leaves thickness variation that polish must repair.",
            &[
                "Etch removes about 15-25 um after lapping (page section 4)",
                "Wet etch removes the damaged layer that lapping leaves (page section 3)",
            ],
        ),
    Beat::new("polishing: chemistry softens, abrasive wipes", BEAT_MS)
        .note(
            "Polishing is chemical and mechanical. The chemistry softens the surface and the abrasive wipes it off under a pad. A softened band on the top face wipes away from left to right.",
            "a tan pad above the wafer, and a softened band on its top face wiping away",
        )
        .detail(
            "Removal rate follows Preston's law, RR = K*P + C; pH changes the rate for oxide slurries.",
            &[
                "Preston law: RR = K*P + C (page section 3; source [5])",
                "Removal rises with pH for silica slurries (page section 3)",
            ],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("kerf: slurry about 150 um, diamond wire about 125 um", BEAT_MS)
        .note(
            "Each wire pass removes a slot, the kerf. A slurry saw leaves about 150 um; diamond wire leaves about 125 um today. The slurry stack is on the left and the diamond stack on the right.",
            "two stacks of three wafers, the slurry stack with wider gaps than the diamond stack",
        )
        .detail(
            "These are solar-grade roadmap numbers, the best sourced kerf data found.",
            &[
                "Kerf about 150 um for slurry saws (ITRPV roadmap via TaiyangNews)",
                "Kerf about 125 um for diamond wire today (page source [1])",
            ],
        ),
    Beat::new("the path to about 85 um, and fine wire under 35 um", BEAT_MS)
        .note(
            "The roadmap points to about 85 um of kerf for diamond wire. Research is heading to fine wire under 35 um in diameter. The third stack has the narrower gaps.",
            "a third stack with narrower gaps beside the diamond stack",
        )
        .detail(
            "Thinner wire cuts less kerf but is weaker, which limits how fast kerf can shrink.",
            &[
                "Path to about 85 um (page source [1])",
                "Fine wire under 35 um diameter is the research direction (Ge et al. 2026)",
            ],
        ),
    Beat::new("lapping: 80 um in 40 minutes, one patent example", BEAT_MS)
        .note(
            "One 200-300 mm patent example removes 80 um in 40 minutes. Double-side lapping removes 80 to 200 um in total. The red sliver marks the stock removed.",
            "a wafer with a red sliver of removed stock at its edge, and a gold time bar beside it",
        )
        .detail(
            "Lapping is the largest planned removal after kerf, so the lap-or-grind choice is a cost lever.",
            &[
                "One 200-300 mm patent example: 80 um in 40 min (page section 4)",
                "Double-side lapping removes 80 to 200 um in total (page section 4)",
            ],
        ),
    Beat::new("the end result: 775 um +/- 25 um, TTV 5 um or less", BEAT_MS)
        .note(
            "The finished wafer is 775 um thick, plus or minus 25 um, with total thickness variation of 5 um or less. The two gold plates mark that tolerance above and below the wafer.",
            "a wafer between two gold tolerance plates, one above and one below it",
        )
        .detail(
            "The vendor datasheet gives the spec; the page points to WAFER for the full picture.",
            &[
                "775 um +/- 25 um thick, TTV 5 um or less (vendor datasheet, see WAFER)",
                "The page's end result follows the polish step (page section 4)",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("saw kerf 125 um: the first loss", BEAT_MS)
        .note(
            "The saw kerf is the first and biggest pure loss in the budget: about 125 um of silicon per wafer cut becomes swarf. The bars are drawn to scale, two millimetres per micrometre.",
            "a grey bar grows to its length; the rows below it are still empty",
        )
        .detail(
            "The kerf is per wafer cut, and the wire sets it.",
            &[
                "Diamond wire kerf about 125 um (page source [1])",
                "Kerf is per wafer cut; the wire sets it (page section 2)",
            ],
        ),
    Beat::new("lapping 80 um: the next largest share", BEAT_MS)
        .note(
            "Double-side lapping takes the next biggest share. The 80 um bar is one patent example; the range is 80 to 200 um.",
            "a blue bar grows under the grey kerf bar, shorter than it",
        )
        .detail(
            "The ranges are shown in parentheses on the page; the 80 um bar is one example.",
            &[
                "Double-side lapping removes 80 to 200 um (page section 5)",
                "One 200-300 mm patent example: 80 um in 40 min (page section 4)",
            ],
        ),
    Beat::new("etch 20 um: a smaller share", BEAT_MS)
        .note(
            "The etch removes about 15 to 25 um, so the 20 um bar is the midpoint of that range.",
            "a short gold bar grows under the blue lapping bar",
        )
        .detail(
            "Etch removes the damage that lapping leaves behind.",
            &[
                "Etch removes about 15-25 um after lapping (page sections 4-5)",
                "Chemical etch: removes damage without adding mechanical stress (page section 4)",
            ],
        ),
    Beat::new("DSP polish 15 um: the smallest share", BEAT_MS)
        .note(
            "Double-side polish takes about 10 to 20 um; the 15 um bar is the midpoint. The four bars are patent and source examples, and they do not add up to one wafer's history.",
            "the last short gold bar grows at the bottom, and all four bars now stand together",
        )
        .detail(
            "Removal amounts are patent examples, not a standard; each maker tunes its own sequence.",
            &[
                "DSP removes 10-20 um total (page section 4)",
                "Removal amounts are patent examples, not a standard (page section 9)",
            ],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("AMAT and Ebara: about 80% of CMP tools (rough claim)", BEAT_MS)
        .note(
            "CMP tools are the polishing machines. Applied Materials and Ebara are said to hold about 80% of them. The claim comes from market research with weak sourcing.",
            "one tan column rising, with a tag reading about 80 percent, rough",
        )
        .detail(
            "Treat the 80 percent as rough; it is a market-research claim.",
            &[
                "AMAT (Applied) and Ebara (6361.T) about 80% of CMP tools (market-research claim)",
                "Market-research claim with weak sourcing (page section 6)",
            ],
        ),
    Beat::new("the 2001 and 2002 split: Applied 62% and Ebara 23%", BEAT_MS)
        .note(
            "The only quantified split found is old Dataquest data. Applied held about 62% in 2001 and Ebara about 23%; in 2002 the figures were 61% and 22%.",
            "four columns rising in turn, the two tall ones Applied and the two short ones Ebara, labelled by year",
        )
        .detail(
            "These are old figures; verify them before use.",
            &[
                "Applied 62.1% and Ebara 23% in 2001; 61.3% and 22% in 2002 (Silicon Semiconductor article)",
                "Old analyst data: verify before use (page section 9)",
            ],
        ),
    Beat::new("slurry: Fujifilm about 31%, the top six over 70%", BEAT_MS)
        .note(
            "Slurry is the main CMP consumable. Fujifilm is the largest supplier at about 31%, and the top six slurry makers hold over 70% of revenue.",
            "a short gold column for Fujifilm, and a taller blue column for the top six",
        )
        .detail(
            "Entegris is second after buying CMC Materials and others; the shares are probably from about 2023.",
            &[
                "Fujifilm (4901.T) about 31% per TECHCET (page section 6)",
                "Global top six slurry players hold over 70% of revenue (market-research summary)",
            ],
        ),
    Beat::new("pads: DuPont over 50% (undated)", BEAT_MS)
        .note(
            "Pads carry the slurry against the wafer. DuPont is said to hold over 50% of pads, from an undated article, so treat the figure as rough.",
            "a single tan column rising to the half-way mark",
        )
        .detail(
            "The same TECHCET-cited article gives the slurry shares; it is undated.",
            &[
                "DuPont (DD) over 50%, per the TECHCET-cited piece (undated, rough; page section 6)",
                "Pads are consumed in volume and qualified per line (page section 7)",
            ],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("wire wear: a worn wire bows and the faces come out wavy", BEAT_MS)
        .note(
            "Wear raises the wire's deflection under load, so the bow deepens. The wafers come out with more thickness variation and more kerf.",
            "a new wire straight, and a worn wire bowed into a V under the load",
        )
        .detail(
            "Wire wear is the main saw risk the page names, and it drives both TTV and kerf.",
            &[
                "Wear raises wire deflection, thickness variation and kerf (Springer 2026; source [3])",
                "Wire breakage and wear are the main saw risks (page section 7)",
            ],
        ),
    Beat::new("thin wire: less kerf, but weaker, and it can break", BEAT_MS)
        .note(
            "Thinner wire cuts less kerf but is weaker, so it can break mid-cut. That trade-off limits how fast the kerf can shrink.",
            "a thick wire holding its line, and a thin wire with a gap where it broke",
        )
        .detail(
            "A broken wire mid-cut can scrap the wafers still in the ingot.",
            &[
                "Research is heading under 35 um diameter (Ge et al. 2026)",
                "Older patents note wire drag raises breakage risk at 300-400 mm (page section 7)",
            ],
        ),
    Beat::new("consumables: a few vendors, qualified per fab line", BEAT_MS)
        .note(
            "Slurries and pads are consumables bought over and over, from a few vendors. Each one is qualified per fab line, so switching is slow.",
            "four drums of slurry and pad stock standing in a row",
        )
        .detail(
            "Consumable revenue follows wafer starts and the number of CMP steps per chip.",
            &[
                "CMP slurries and pads: few vendors, qualified per fab line (page section 7)",
                "Ceria and silica abrasive purity sits upstream (page section 7)",
            ],
        ),
    Beat::new("tools: two big suppliers, and Chinese toolmakers pushing in", BEAT_MS)
        .note(
            "The CMP tool market has two big suppliers. Chinese domestic toolmakers are pushing in, according to Applied's FY2025 10-K.",
            "two large tool blocks, gold and blue, with a small red block at the far end for the challenger",
        )
        .detail(
            "A two-supplier tool market with a rising challenger is a geopolitics and export-control story as well as a share story.",
            &[
                "Two-supplier CMP tool market; Chinese domestic toolmakers pushing in (AMAT FY2025 10-K)",
                "Applied's FY2025 10-K discusses CMP competition (page section 6)",
            ],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("a polished face is the flat reference for lithography", BEAT_MS)
        .note(
            "The polished wafer is the flat reference that lithography prints on. A bright mirror wafer sits under a steel beam, which marks the level the patterns are printed at.",
            "a bright mirror wafer under a steel beam set above it",
        )
        .detail(
            "Nanotopography and flatness are largely set by the polishing process.",
            &[
                "The polished surface is the reference plane for lithography (page section 8)",
                "The Preston law runs on both ends of the chip (page section 8)",
            ],
        ),
    Beat::new("films are planarised the same way: STI, copper, tungsten", BEAT_MS)
        .note(
            "Later in the fab, CMP flattens deposited films such as STI oxide, copper and tungsten. A tall film bump is pressed down by the pad until the top is flat.",
            "a grey base with a tall film bump on it, and a tan pad above it pressing the bump down",
        )
        .detail(
            "Pad asperities and slurry flow average out high spots; pressure and speed set the rate.",
            &[
                "Later fab CMP reuses the same physics on STI, copper and tungsten (page section 8)",
                "Planarity: pad asperities and slurry flow average out high spots (textbook)",
            ],
        ),
    Beat::new("the same law at both ends: wafer polish and fab CMP", BEAT_MS)
        .note(
            "The Preston law, RR = K*P + C, runs on the wafer maker's polish and on fab CMP. A bare grey silicon wafer is on the left and a cream film wafer on the right.",
            "a bare grey silicon wafer on the left and a cream film wafer on the right, with a label over each",
        )
        .detail(
            "The same physics runs on bare silicon at the wafer maker and on deposited films in the fab.",
            &[
                "Preston law: RR = K*P + C (page section 3; source [5])",
                "Wafer-level polishing is done in-house by the wafer makers (page section 6)",
            ],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("removal amounts are patent examples, not a standard", BEAT_MS)
        .note(
            "The removal amounts on this page come from patent examples. Each wafer maker tunes its own sequence, so the numbers are a guide and not a spec.",
            "a card lit with a gold strip, labelled as patent examples",
        )
        .detail(
            "Use the ranges as ranges; the page's own examples are single data points.",
            &[
                "Removal amounts are patent examples, not a standard (page section 9)",
                "Each wafer maker tunes its own sequence (page section 9)",
            ],
        ),
    Beat::new("market shares are old or from market research: verify", BEAT_MS)
        .note(
            "The market-share items come from market-research summaries and old analyst data. Verify them before you use them.",
            "the second card lit, labelled as needing verification",
        )
        .detail(
            "The only split found is from 2001 and 2002, so it says little about today.",
            &[
                "Market-share items are from summaries and old analyst data; verify (page section 9)",
                "Dataquest figures are from 2001 and 2002 (page section 6)",
            ],
        ),
    Beat::new("kerf: solar-grade roadmap numbers", BEAT_MS)
        .note(
            "The diamond-wire kerf numbers are solar-industry roadmap values. They are the best sourced kerf data on the page, but they are not a wafer-fab spec.",
            "the third card lit, labelled as solar-grade kerf numbers",
        )
        .detail(
            "Solar roadmap kerf is for solar-grade wafers; fab wafers can differ.",
            &[
                "Diamond-wire kerf numbers are solar roadmap values (page section 9)",
                "ITRPV roadmap via TaiyangNews (page section 4)",
            ],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("sources 1-3: diamond wire, fine wire, wear and kerf", BEAT_MS)
        .note(
            "Cards 1 to 3 cover the saw: the diamond-wire article, the fine-wire paper, and the 2026 paper on wear and kerf.",
            "eight cards on a grey board, with cards 1, 2 and 3 lit",
        )
        .detail(
            "The saw cards are the basis for the kerf and wear figures in sections 2 and 7.",
            &[
                "[1] TaiyangNews, Diamonds Are A Wafer's Friend",
                "[2] Ge et al., slicing with ultra-fine diamond wire; [3] Springer, wear and kerf (2026)",
            ],
        ),
    Beat::new("sources 4-5: lapping, etch and polish patents; the Preston law", BEAT_MS)
        .note(
            "Cards 4 and 5 are the patents for lapping, etching and polishing, and the Preston law and pH paper.",
            "cards 4 and 5 lit, with the other cards dark",
        )
        .detail(
            "The patents give the removal amounts; the Preston paper gives the pH results.",
            &[
                "[4] US 6,114,245; US 6,352,927; US 7,829,467 (lapping, etch, polish)",
                "[5] US 10,418,247 and doi 10.1149/2.0311910jss (Preston law and pH)",
            ],
        ),
    Beat::new("sources 6-8: slurry and tool shares, CMP competition, Dataquest", BEAT_MS)
        .note(
            "Cards 6 to 8 are the market sources: the slurry and tool share article, Applied's FY2025 10-K on CMP competition, and the Dataquest equipment split.",
            "cards 6, 7 and 8 lit, the rest dark",
        )
        .detail(
            "The market cards are the least certain part of the page; check them before use.",
            &[
                "[6] semiconductor-digest, slurry and tool shares",
                "[7] Applied FY2025 10-K; [8] Dataquest CMP equipment share (siliconsemiconductor.net)",
            ],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/slice_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
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
        assert_eq!(counts, [4, 4, 5, 4, 4, 4, 4, 3, 3, 3]);
        assert_eq!(counts.len(), 10);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
