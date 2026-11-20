// BANK sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/bank_sections.py: 1 what happens, 2 the parts, 3 one interleaved access,
// 4 timing rules, 5 conflicts, 6 numbers, 7 refresh, 8 makers, 9 risks, 10 sources. Beats per
// section: 3, 5, 5, 3, 3, 3, 3, 3, 3, 3.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("one bank works alone: the bus waits", BEAT_MS)
        .note(
            "If every request goes to one bank, each must open its row before data can flow, and the data bus sits idle meanwhile.",
            "one orange bank opens under a white command dot, its row plate lights, and green bursts leave it; the other banks stay orange",
        )
        .detail(
            "This is the worst case.",
            &["Each bank has its own row buffer (section 1)", "All banks share one command bus and one data bus (section 1)"],
        ),
    Beat::new("two banks overlap", BEAT_MS)
        .note(
            "A second bank opens while the first reads, hiding part of the wait.",
            "two row plates stand up on two banks, and a green burst leaves each in turn along the data lane",
        )
        .detail(
            "Bank-level parallelism: ACTs to different banks are tRRD apart.",
            &["tRRD_S about 3.7 ns across groups (section 4)", "Requests overlap across banks (section 1)"],
        ),
    Beat::new("four banks take turns: the bus stays busy", BEAT_MS)
        .note(
            "With enough banks in flight, one is always ready to send data.",
            "four banks have open rows in staggered order, and their bursts leave one after another so the data lane stays lit",
        )
        .detail(
            "This is why chips have many banks.",
            &["DDR4 has 16 banks, DDR5 has 32 (section 6)", "The data bus carries one burst at a time (section 2)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("bank: an array with its own row buffer", BEAT_MS)
        .note(
            "A bank is a full array with its own row buffer, and it holds one open row at a time.",
            "one bank is lit with a bright row plate while the rest of the die stays orange",
        )
        .detail(
            "See the ARRAY node for what is inside.",
            &["Each bank holds one open row (section 2)", "The row buffer belongs to its bank (section 1)"],
        ),
    Beat::new("bank group: four banks sharing circuits", BEAT_MS)
        .note(
            "Banks are grouped; READs within a group must be further apart than READs across groups.",
            "the four banks of the top-left group light their row plates inside the grey group frame",
        )
        .detail(
            "DDR4 has 4 groups, DDR5 has 8.",
            &["4 banks per group (section 2)", "DDR4 has 4 bank groups, DDR5 has 8 (section 6)"],
        ),
    Beat::new("command bus: one command at a time", BEAT_MS)
        .note(
            "ACTIVATE, READ, PRECHARGE and REFRESH all share one command bus.",
            "white command dots run one after another along the pale command bus at the top of the die",
        )
        .detail(
            "The controller has to fit every command into it.",
            &["ACTIVATE, READ, PRECHARGE and REFRESH share the bus (section 2)"],
        ),
    Beat::new("data bus: shared by every bank", BEAT_MS)
        .note(
            "All banks send their data on the same bus, one burst at a time, out to the chip's pins.",
            "green bursts leave several banks and run along the green lane to the I/O pad on the right",
        )
        .detail(
            "Keeping it full is the controller's job.",
            &["DDR4 burst length 8, DDR5 burst length 16 (section 6)", "One burst at a time (section 2)"],
        ),
    Beat::new("controller: picks the order of commands", BEAT_MS)
        .note(
            "The memory controller in the processor picks which command to send next, within all the timing rules.",
            "the grey controller block on the left sends white command dots toward the command bus",
        )
        .detail(
            "Its ordering decides how often rows hit.",
            &["The controller sits in the processor (section 2)", "Controllers serve row hits first (section 5)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. ACT bank A", BEAT_MS)
        .note(
            "Bank A opens its row.",
            "a white command dot reaches the top-left bank, and its row plate rises",
        )
        .detail(
            "tRCD must pass before the row can be read.",
            &["ACTIVATE opens a row (section 3)", "tRCD is on the ARRAY node (section 10)"],
        ),
    Beat::new("2. ACT bank B (another group)", BEAT_MS)
        .note(
            "Bank B opens a row while A is still opening.",
            "a second command dot goes to a bank in another group, and its row plate rises beside A's, which stays up",
        )
        .detail(
            "Only tRRD after A's ACT.",
            &["tRRD_S about 3.7 ns (section 4)", "Bank B is in another group (section 3)"],
        ),
    Beat::new("3. READ A", BEAT_MS)
        .note(
            "A's row buffer sends a burst.",
            "green bursts leave bank A's row plate and run toward the data lane",
        )
        .detail(
            "The data follows the READ after tCL.",
            &["A READ sends one burst (section 3)", "DDR4 burst length 8 (section 6)"],
        ),
    Beat::new("4. READ B", BEAT_MS)
        .note(
            "B's burst follows straight after on the bus.",
            "green bursts now leave bank B, and the data lane carries them one after another",
        )
        .detail(
            "Across groups the READs are tCCD_S apart, one burst.",
            &["tCCD_S 2.5 ns (section 4)", "tCCD_L about 5.36 ns within one group (section 4)"],
        ),
    Beat::new("5. PRECHARGE both", BEAT_MS)
        .note(
            "Both banks close their rows.",
            "both banks turn pink and their row plates drop, with a white command dot going to each",
        )
        .detail(
            "Ready for new rows.",
            &["tRP is on the ARRAY node (section 10)", "PRECHARGE closes the open row (section 3)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("tRRD: ACTIVATE to ACTIVATE", BEAT_MS)
        .note(
            "ACTIVATEs to different banks must be tRRD apart, longer within a group (tRRD_L) than across groups (tRRD_S).",
            "three gold ACT blocks on a grey time axis: tRRD_S is labelled over the first gap and tRRD_L under the longer second gap",
        )
        .detail(
            "DDR4-3200 module SPD values.",
            &["tRRD_S about 3.7 ns, tRRD_L about 5.3 ns (module SPD)"],
        ),
    Beat::new("tCCD: READ to READ", BEAT_MS)
        .note(
            "READs need tCCD between them: one burst across groups, longer within a group.",
            "pale cyan READ blocks line up back to back on the upper lane, and the gold lower lane has a gap labelled tCCD_L",
        )
        .detail(
            "Bank groups trade this rule for speed.",
            &["tCCD_S 2.5 ns, tCCD_L about 5.36 ns (module SPD)"],
        ),
    Beat::new("tFAW: four ACTIVATEs per window", BEAT_MS)
        .note(
            "No more than four ACTIVATEs may fall in any tFAW window.",
            "four gold ACT blocks sit under a pink window bar, and a fifth stands past the bar's end",
        )
        .detail(
            "A power limit on opening rows.",
            &["tFAW about 21 ns (module SPD)", "tFAW 21-23 ns in the SPD dumps (section 10)"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("requests spread over banks overlap", BEAT_MS)
        .note(
            "Requests to eight banks open and read in a quick stagger, so each bank's wait is hidden.",
            "eight banks light their row plates in a stagger across the two left groups and the two right groups, and green bursts leave them",
        )
        .detail(
            "Parallel banks hide each other's waits.",
            &["Bank-level parallelism (section 1)", "Requests spread over banks overlap (section 5)"],
        ),
    Beat::new("same bank, new row: a full conflict each time", BEAT_MS)
        .note(
            "Requests aimed at one bank, each at a new row, must precharge and reopen one by one.",
            "bank A flashes pink between each row, and its row plate jumps when the row changes",
        )
        .detail(
            "Each costs a full row conflict.",
            &["Conflict: tRP + tRCD + tCL (section 5)", "Requests to different rows of one bank queue up (section 5)"],
        ),
    Beat::new("row hits first, the rest spread out", BEAT_MS)
        .note(
            "A controller that groups same-row requests and spreads the rest across banks gets hits and parallelism.",
            "bank A's row plate stays up and reads steadily, while three other banks open and read in turn",
        )
        .detail(
            "Real controllers reorder within limits for fairness.",
            &["Controllers serve row hits first (section 5)", "Throughput depends on the mapping and ordering (section 9)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("DDR4: 16 banks in 4 groups", BEAT_MS)
        .note(
            "A DDR4 x4/x8 chip has 16 banks in four bank groups of four, with burst length 8.",
            "sixteen orange tiles in four framed groups of four on the die",
        )
        .detail(
            "x16 parts have 2 groups of 4.",
            &["DDR4: 16 banks in 4 bank groups, burst length 8 (section 6)"],
        ),
    Beat::new("DDR5: 32 banks in 8 groups", BEAT_MS)
        .note(
            "DDR5 doubles both: 8 bank groups of 4 banks.",
            "thirty-two orange tiles in eight framed groups of four on the die",
        )
        .detail(
            "More banks, so more rows can be open at once.",
            &["DDR5: 32 banks in 8 bank groups (section 6)", "DDR5 doubles banks and bank groups (Micron white paper)"],
        ),
    Beat::new("bursts: 8 transfers on DDR4, 16 on DDR5", BEAT_MS)
        .note(
            "DDR5 doubles the burst length to 16 transfers.",
            "a short gold row of eight blocks for DDR4, above a longer pale cyan row of sixteen for DDR5",
        )
        .detail(
            "Longer bursts keep a narrower channel full.",
            &["DDR4 burst length 8 (section 6)", "DDR5 burst length 16 (section 6, Micron white paper)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("DDR4 all-bank refresh blocks everything", BEAT_MS)
        .note(
            "REFab refreshes all banks; none can be used until it ends.",
            "all sixteen banks turn pale cyan, and a red bar across the data lane shows the rank is locked",
        )
        .detail(
            "Block lengths are illustrative.",
            &["DDR4 refresh locks the rank (section 7)", "PCPer: DDR4 refresh locks the rank (section 10)"],
        ),
    Beat::new("DDR5 same-bank refresh, staggered", BEAT_MS)
        .note(
            "REFsb refreshes one bank index in every group, then the next.",
            "one bank in each group turns cyan, and the cyan moves through the four bank positions",
        )
        .detail(
            "One bank per group is busy at a time.",
            &["REFsb targets the same bank in every bank group (Micron white paper)", "DDR5 adds same-bank refresh (section 7)"],
        ),
    Beat::new("reads carry on around it", BEAT_MS)
        .note(
            "Reads to the other banks keep going during same-bank refresh.",
            "cyan banks in one position while the others stay orange, and green bursts keep leaving them",
        )
        .detail(
            "Refresh steals less bandwidth.",
            &["Other banks stay available during REFsb (section 7)", "Denser chips add refresh work (section 9)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note(
            "Micron makes commodity DRAM, with SK hynix and Samsung.",
            "the first chip is lit gold-white, and the other two stay orange",
        )
        .detail(
            "Market share is on the market pages.",
            &["Commodity DRAM is made by Micron (MU), SK hynix and Samsung (section 8)"],
        ),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note(
            "SK hynix also makes commodity DRAM.",
            "the middle chip is lit, and Micron and Samsung stay orange",
        )
        .detail(
            "Market share is on the market pages.",
            &["SK hynix ticker: 000660.KS (section 8)"],
        ),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note(
            "Samsung also makes commodity DRAM.",
            "the right-hand chip is lit, and Micron and SK hynix stay orange",
        )
        .detail(
            "Market share is on the market pages.",
            &["Samsung ticker: 005930.KS (section 8)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("interference: two cores fight over one bank", BEAT_MS)
        .note(
            "Requests from different cores to different rows of one bank keep closing each other's rows.",
            "two streams, one white and one cyan, converge on a bank whose row plate is pink",
        )
        .detail(
            "Research partitions banks between threads to avoid it.",
            &["Interference: different rows of one bank close each other's rows (section 9)", "Bank partitioning to cut interference, HPCA 2012 (section 10)"],
        ),
    Beat::new("tFAW caps how fast rows open", BEAT_MS)
        .note(
            "No more than four ACTIVATEs per window, however many banks are free.",
            "four lit bars stand under a pink lid, and two grey bars wait outside it",
        )
        .detail(
            "A power limit becomes a speed limit.",
            &["tFAW about 21 ns (DDR4-3200 module SPD)", "tFAW caps how fast rows can be opened (section 9)"],
        ),
    Beat::new("denser chips: more rows to refresh", BEAT_MS)
        .note(
            "Every doubling of rows means more refresh work inside the same window.",
            "three cyan stacks, each about twice the height of the one before",
        )
        .detail(
            "Same-bank refresh softens it; it does not remove it.",
            &["Denser chips have more rows to refresh in the same window (section 9)", "DDR5 same-bank refresh (section 7)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("Micron, PCPer and Wikipedia on DDR5 and refresh", BEAT_MS)
        .note(
            "Cards [1] to [3] cover DDR5 and refresh: Micron's white paper on the new features, Wikipedia on DDR5 bank groups, and PCPer on Micron's program.",
            "cards [1], [2] and [3] light up in the top row, and the rest stay dim",
        )
        .detail(
            "The Micron white paper gives 2x banks, 2x bank groups, BL16 and same-bank refresh.",
            &["[1] Micron DDR5 new features white paper", "[2] Wikipedia, DDR5 SDRAM; [3] PCPer, DDR4 refresh locks the rank"],
        ),
    Beat::new("DDR4-3200 module SPD dumps", BEAT_MS)
        .note(
            "Cards [4] and [5] are the module SPD dumps behind the DDR4-3200 timing values.",
            "cards [4] and [5] light up; the module-dump cards carry tRRD, tCCD and tFAW",
        )
        .detail(
            "The SPD values are the source of the ns figures on these pages.",
            &["[4] tRRD_S ~3.7 ns, tRRD_L ~5.3 ns, tCCD_L ~5.36 ns, tFAW 21-23 ns", "[5] DDR4-3200 SPD dump (G.Skill module)"],
        ),
    Beat::new("papers on interleaving, mapping and bank partitioning", BEAT_MS)
        .note(
            "Cards [6] to [8] are papers: interleaving across banks, address mapping with column bits lowest, and bank partitioning to cut interference.",
            "cards [6], [7] and [8] light up in the bottom row",
        )
        .detail(
            "They support the address-mapping and interference claims. JEDEC JESD79-4 is not yet linked.",
            &["[6] arXiv 1607.08578, interleaving across banks", "[7] arXiv 1509.03721 (DReAM); [8] HPCA 2012, bank partitioning"],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/bank_sec",
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
}
