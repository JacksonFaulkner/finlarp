// CELL sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/cell_sections.py. One picture per `# ` heading of MEM_CELL.txt, in order:
// 1 what happens (3 beats), 2 the parts (6), 3 one read (5), 4 refresh (3), 5 leakage (5),
// 6 by the numbers (3), 7 shrinking (4), 8 who makes it (3), 9 chokepoints and risks (3),
// 10 sources (4).

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("a full capacitor reads as 1", BEAT_MS)
        .note(
            "A DRAM bit is a packet of charge on one tiny capacitor. One transistor plus one capacitor makes the 1T1C cell.",
            "today's cell cut open: the buried word line in its trench, the tall cylinder capacitor on top with orange charge on its inner electrode",
        )
        .detail(
            "The cell is a switch and a bucket. The rest of the page is about filling, reading and keeping that bucket.",
            &[
                "The cell is 1 transistor and 1 capacitor, 1T1C (page text, section 1)",
                "Full charge reads as 1, empty as 0 (page text, section 1)",
            ],
        ),
    Beat::new("an empty capacitor reads as 0", BEAT_MS)
        .note(
            "The same cell holds a 0 when its capacitor is empty. The bit is an amount of charge, not a latch.",
            "the orange charge drains down the electrode until the capacitor is dark",
        )
        .detail(
            "Because the bit is charge, it leaks, and has to be refreshed (section 5).",
            &[
                "Empty = 0 (page text, section 1)",
                "The bit is charge that leaks, so it needs refresh (page text, section 5)",
            ],
        ),
    Beat::new("a field of cells, each its own bit", BEAT_MS)
        .note(
            "Zoom out: a forest of tall capacitors, each on its own transistor, each holding its own 1 or 0. A silicon-nitride lattice braces them so they do not lean into each other.",
            "a 4 by 3 block of cells, front row cut open with alternate capacitors charged; nitride rings at two heights",
        )
        .detail(
            "The capacitors are so tall and thin that they need a support lattice.",
            &[
                "A typical array is 512 wordlines by 512 bitlines (Jacob, DRAM Circuits, slide 5)",
                "Each bit has its own transistor and capacitor (page text, section 1)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("word line: buried in a trench", BEAT_MS)
        .note(
            "The word line is a metal rod buried in a trench in the silicon, running into the page along a row. A nitride cap seals its top. Driving it high turns on every transistor in the row.",
            "the word line lit pink inside its oxide-lined trench, nitride cap above it, a passing word line in the isolation to the right",
        )
        .detail(
            "Burying the gate makes the channel longer without making the cell wider, which cuts leakage.",
            &[
                "Word line: high turns on every access transistor in its row (page text, section 2)",
                "Buried-channel array transistor (BCAT) is the 6F2 standard (R&D 3D DRAM page)",
            ],
        ),
    Beat::new("access transistor: the switch", BEAT_MS)
        .note(
            "The transistor is the switch. Charge never goes through the gate oxide: the gate's voltage pulls a thin conducting channel into the silicon, and charge flows through that channel between drain and source.",
            "close-up of the trench: the thin oxide liner, and the cyan U-shaped channel lit round the trench bottom between the drain n+ and source n+",
        )
        .detail(
            "Oxide insulates; the channel conducts. The U shape is the buried gate's trick for a long channel.",
            &[
                "Access transistor: a switch between the bit line and the storage node (page text, section 2)",
                "Chip tab, NMOS page (access transistor)",
            ],
        ),
    Beat::new("storage capacitor: the bit itself", BEAT_MS)
        .note(
            "The capacitor is a tall cylinder: a TiN storage electrode, a thin high-k dielectric (ZrO2 stacks), and a TiN plate. It sits on a landing pad and a storage-node contact down to the source.",
            "the capacitor cut open: plate, yellow dielectric layers, storage electrode, with orange charge on it; the contact and pad underneath",
        )
        .detail(
            "High-k beats SiO2 here: more charge in the same area.",
            &[
                "Storage capacitor: holds the bit as charge (page text, section 2)",
                "Cell capacitance on the order of 10 fF (Jacob, DRAM Circuits)",
            ],
        ),
    Beat::new("bit line: the column wire", BEAT_MS)
        .note(
            "The bit line runs across the word lines, behind the cut. A contact drops from it to the drain. One bit line serves every cell in its column.",
            "the bit line glowing cyan behind the cell, its contact down to the drain, and running left to the sense amp",
        )
        .detail(
            "Word lines pick the row, bit lines carry the data: a grid, one cell at each crossing.",
            &[
                "Bit line: the column wire (page text, section 2)",
                "Precharged to VDD/2 before each read (page text, section 2)",
            ],
        ),
    Beat::new("sense amp: two cross-coupled inverters", BEAT_MS)
        .note(
            "The sense amp sits between two lines: BL from this mat and BL-bar from the next. It is two inverters wired in a loop, so any small difference between the lines snowballs into a full 1 or 0.",
            "the sense amp lit violet with its two inverter symbols and crossed wires; the BL and BL-bar gauges above it",
        )
        .detail(
            "It is a comparator plus a latch in one.",
            &[
                "Sense amp: two cross-coupled inverters on a bit line pair (page text, section 2)",
                "Open bit line: BL and BL-bar come from mats on either side (Jacob, DRAM Circuits)",
            ],
        ),
    Beat::new("BL-bar and the equaliser", BEAT_MS)
        .note(
            "BL-bar is the twin line. It runs to cells that are not being read, so it stays at VDD/2 and serves as the reference. The equaliser shorts BL to BL-bar to set both to exactly VDD/2 before each read.",
            "BL-bar lit to the left with its unread cells, and the green equaliser under the sense amp",
        )
        .detail(
            "The comparison is BL against BL-bar, not against a stored charge in the sense amp.",
            &[
                "Precharge holds the bit line at VDD/2 between accesses (page text, section 2)",
                "Reference comes from the twin bit line (Jacob, DRAM Circuits)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. precharge: BL and BL-bar at VDD/2", BEAT_MS)
        .note(
            "Before the read, the equaliser holds both lines at exactly half the supply. Both gauges sit on the white VDD/2 line.",
            "the green equaliser lit under the sense amp; both gauge bars at the half line",
        )
        .detail(
            "Starting both lines equal means any difference after is from the cell.",
            &[
                "Precharge: the bit line sits at VDD/2 (page text, section 3)",
            ],
        ),
    Beat::new("2. word line rises: the channel opens", BEAT_MS)
        .note(
            "The word line goes high. The buried gate pulls a channel round the trench, and the cell's capacitor is now connected to the bit line.",
            "close-up: the word line lit, the U channel glowing cyan",
        )
        .detail(
            "Every cell on this row connects to its own bit line at once.",
            &[
                "Word line rises: the access transistor switches on (page text, section 3)",
            ],
        ),
    Beat::new("3. charge sharing: BL moves a little", BEAT_MS)
        .note(
            "The cell's charge spreads onto the bit line. The bit line has about ten times the capacitance, so it only moves a little: up about 60 mV for a 1, down for a 0. BL-bar stays put.",
            "beads flow from the capacitor down through the channel and out along the bit line; the BL gauge creeps just above the half line",
        )
        .detail(
            "Swing = (Vcell - VDD/2) x Cc / (Cc + Cb): a small cell on a big line gives a small signal.",
            &[
                "Charge sharing: the bit line moves a small amount (page text, section 3)",
                "Swing formula (page text, section 7)",
            ],
        ),
    Beat::new("4. sense: compare, then slam apart", BEAT_MS)
        .note(
            "The sense amp compares BL with BL-bar. BL is a hair higher, so the latch drives BL all the way to VDD and BL-bar to ground.",
            "the sense amp lit violet; the BL gauge shoots to full, the BL-bar gauge drops to zero",
        )
        .detail(
            "Now the bit is a full-size 1 on the bit line, ready to send out.",
            &[
                "Sense amp: the latch drives the bit line to a full rail (page text, section 3)",
            ],
        ),
    Beat::new("5. restore: the cell refills", BEAT_MS)
        .note(
            "The read drained the cell, but the transistor is still on, so the full VDD on the bit line flows back into the capacitor. Then the word line drops and the equaliser resets both lines.",
            "beads flow back from the bit line into the capacitor, which glows full again; then the gauges return to VDD/2",
        )
        .detail(
            "Every read is also a write-back. Refresh is the same thing, done on a timer.",
            &[
                "Restore: the still-connected cell returns to full charge (page text, section 3)",
                "The read drains the cell, so restore is part of every read (page text, section 3)",
            ],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("the controller issues a refresh command on a timer", BEAT_MS)
        .note(
            "Refresh runs on a clock, because leakage does not wait. The controller issues one REF command every 7.8 us, whatever else is going on.",
            "the row of cells in a line, the white pointer at the first cell, and the charge in each sagging a little",
        )
        .detail(
            "The interval is set so that all the commands fit inside the 64 ms window.",
            &[
                "tREFI = 7800 ns (PROTEAS, arXiv 2404.16256, Table I)",
                "8192 REF commands per window (PROTEAS, arXiv 2404.16256, Table I)",
            ],
        ),
    Beat::new("each command refreshes a slice of rows", BEAT_MS)
        .note(
            "A REF command does not refresh the whole array. It covers one slice of rows, and the next command takes the next slice.",
            "the pointer stepping along the row, and the row under it filling to full charge",
        )
        .detail(
            "No single command covers every row. It takes the whole window to get round them all.",
            &[
                "Each command refreshes a slice of rows (page text, section 4)",
                "The controller issues 8192 refresh commands in each window (page text, section 4)",
            ],
        ),
    Beat::new("the window closes with every row done", BEAT_MS)
        .note(
            "By the end of the window every slice has had its turn, so every row was rewritten within 64 ms. Then the cycle starts again.",
            "all rows at full height and the pointer at the far end of the row",
        )
        .detail(
            "8192 commands at 7800 ns each come to about 64 ms, so the numbers fit together.",
            &[
                "tREFW = 64 ms (DDR4; PROTEAS, arXiv 2404.16256, Table I)",
                "8192 x 7800 ns = 63.9 ms (computed)",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("charge leaks out four ways", BEAT_MS)
        .note(
            "A charged cell is not sealed. Charge escapes through four paths, each shown in its own colour.",
            "the cell with all four bead streams at once, the charge level dropping",
        )
        .detail(
            "No path is ever fully off, so the cell always fades.",
            &[
                "Leakage through the dielectric, the junction and the off transistor (page text, section 5)",
            ],
        ),
    Beat::new("subthreshold: the off transistor trickles", BEAT_MS)
        .note(
            "With the word line low the transistor is off, but not perfectly. A tiny current leaks from the storage node round the channel to the drain and the bit line.",
            "cyan beads run from the capacitor down, round the trench bottom and out the drain",
        )
        .detail(
            "This is usually the biggest leak, and it rises as transistors shrink.",
            &[
                "Access transistor leaks while off (page text, section 5)",
            ],
        ),
    Beat::new("junction and GIDL", BEAT_MS)
        .note(
            "The source n+ sits in p-type silicon, a diode; charge leaks across it into the substrate. GIDL is leakage pulled out by the strong field where the gate edge meets the drain. Both get worse with heat.",
            "red beads leave the source down into the substrate; pink beads leave the drain edge beside the gate",
        )
        .detail(
            "Hot DRAM refreshes twice as often (32 ms above 85 C).",
            &[
                "Storage-node junction leakage (page text, section 5)",
                "GIDL at the gate-drain overlap (Mutlu, retention retrospective)",
            ],
        ),
    Beat::new("dielectric: through the thin high-k", BEAT_MS)
        .note(
            "Some charge tunnels straight through the capacitor's thin dielectric to the plate.",
            "close-up on the capacitor wall: yellow beads cross the dielectric",
        )
        .detail(
            "Thinner dielectric holds more charge but leaks more: a trade-off.",
            &[
                "Leakage through the capacitor dielectric (page text, section 5)",
            ],
        ),
    Beat::new("the weakest cell sets the deadline", BEAT_MS)
        .note(
            "Three cells drain at different rates. The refresh window (64 ms) has to be short enough for the leakiest cell, then refresh fills them all back up.",
            "three cut cells draining to different levels, then all refilled to full",
        )
        .detail(
            "Most cells could wait far longer; a few weak ones set the rule.",
            &[
                "Retention differs cell to cell; refresh covers the weakest (page text, section 5)",
                "tREFW = 64 ms (PROTEAS, Table I)",
            ],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("6F^2: the cell area with an open bit line", BEAT_MS)
        .note(
            "Cell area is counted in squares of F, the minimum feature size. With an open bit line a cell takes 6 of them.",
            "six orange tiles in a block, standing for the area in F squares; not to scale",
        )
        .detail(
            "Counting in F lets you compare layouts on any process.",
            &[
                "Cell area 6F^2 with an open bit line (Jacob, DRAM Circuits, slide 9)",
                "Cell area is set by F, the minimum feature size (page text, section 7)",
            ],
        ),
    Beat::new("8F^2: the cell area with a folded bit line", BEAT_MS)
        .note(
            "A folded bit line takes 8 squares, a third more area per cell. That is the price of its better noise behaviour.",
            "eight cyan tiles, four across and two deep, a third more than the six orange tiles before",
        )
        .detail(
            "Going from 8 to 6 squares fits more cells in the same area.",
            &[
                "Cell area 8F^2 with a folded bit line (Jacob, DRAM Circuits, slide 9)",
                "The folded layout's noise behaviour (textbook)",
            ],
        ),
    Beat::new("512 x 512 cells in one array", BEAT_MS)
        .note(
            "A typical array has 512 word lines and 512 bit lines, one cell at each crossing. The array is refreshed within the 64 ms window.",
            "a grid of small grey tiles standing for the cells; the picture shows only part of the array, and is not to scale",
        )
        .detail(
            "512 x 512 is 262,144 cells in one array.",
            &[
                "Typical array: 512 wordlines by 512 bitlines (Jacob, DRAM Circuits, slide 5)",
                "tREFW = 64 ms, tREFI = 7800 ns (DDR4; PROTEAS, arXiv 2404.16256, Table I)",
            ],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("6F2 today: a 3F x 2F cell", BEAT_MS)
        .note(
            "Today's cell takes 6F2 of floor space. The capacitor must hold about 10 fF no matter how small the cell gets, so it stands tall on that small footprint.",
            "the planar cell with its glowing 3F x 2F footprint tile above the capacitor",
        )
        .detail(
            "Charge capacity comes from surface area, so the only spare direction is up.",
            &[
                "6F2 with an open bit line (page text, section 6)",
                "Designs keep Cc up with a taller capacitor or a better dielectric (page text, section 7)",
            ],
        ),
    Beat::new("thinner cap, same charge: grow taller", BEAT_MS)
        .note(
            "Shrink the footprint and the capacitor has to get thinner, so it grows taller to keep its wall area. Real ones are about 40 times taller than wide; they can lean and touch.",
            "the capacitor squeezes thinner and stretches upward",
        )
        .detail(
            "This is why DRAM scaling has slowed: the capacitor, not the transistor, is the wall.",
            &[
                "Smaller storage capacitor gives a smaller swing (page text, section 7)",
            ],
        ),
    Beat::new("4F2: the transistor stands up", BEAT_MS)
        .note(
            "The next step stands the transistor upright: a silicon pillar, the gate wrapped round it, the bit line buried below and the capacitor on top. The cell shrinks to 2F x 2F.",
            "the vertical-channel cell: buried bit line, pillar with glowing channel, word line wrapped round it, capacitor above",
        )
        .detail(
            "4F2 is the smallest square cell possible. Leakage in the pillar and aligning the cap are the hard parts.",
            &[
                "4F2 vertical channel transistor (R&D 3D DRAM page)",
            ],
        ),
    Beat::new("3D DRAM: lay the cells down and stack them", BEAT_MS)
        .note(
            "3D DRAM stops shrinking and starts stacking: each cell lies on its side, capacitor horizontal, and dozens of layers stack up like NAND. The bit line runs vertically through all the layers.",
            "a five-layer stack, word lines lighting layer by layer, sideways capacitors either side of the vertical bit line",
        )
        .detail(
            "This stacks cells inside one die. HBM stacks whole dies: a different level.",
            &[
                "Stacked 3D DRAM (R&D 3D DRAM page)",
            ],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note(
            "Commodity DRAM is made by three companies. Micron is the first of them.",
            "three wafers, one per maker, all the same size on purpose; the Micron wafer glowing with its label",
        )
        .detail(
            "Market share and the split between commodity and HBM are on the market pages, not here.",
            &[
                "Commodity DRAM is made by Micron (MU), SK hynix (000660.KS) and Samsung (005930.KS) (page text, section 8)",
                "Micron ticker: MU (page text, section 8)",
            ],
        ),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note(
            "SK hynix is the second maker. Its ticker is 000660.KS.",
            "the middle wafer glowing, with its label shown",
        )
        .detail(
            "Market share and the split between commodity and HBM are on the market pages, not here.",
            &[
                "SK hynix ticker: 000660.KS (page text, section 8)",
                "Commodity DRAM is made by three companies (page text, section 8)",
            ],
        ),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note(
            "Samsung is the third maker. Its ticker is 005930.KS.",
            "the right wafer glowing, with its label shown",
        )
        .detail(
            "Market share and the split between commodity and HBM are on the market pages, not here.",
            &[
                "Samsung ticker: 005930.KS (page text, section 8)",
                "Commodity DRAM is made by these three (page text, section 8)",
            ],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("covering the weakest cells costs time", BEAT_MS)
        .note(
            "Retention varies from cell to cell, and the refresh window has to cover the weakest cells. Every row pays for that in time and in power.",
            "the refresh sweep moving along the rows, and the meter on the left climbing; the meter is illustrative, not a measurement",
        )
        .detail(
            "The whole chip runs at the pace of its worst cells.",
            &[
                "Retention varies cell to cell (Mutlu, arXiv 2306.16037, p. 1)",
                "The refresh window has to cover the weakest cells (page text, section 9)",
            ],
        ),
    Beat::new("refresh blocks memory access while it runs", BEAT_MS)
        .note(
            "While a refresh runs, the bank cannot serve requests, so they wait. That slows the whole system.",
            "a red gate closed in front of the bank, with cyan requests queuing behind it",
        )
        .detail(
            "The bank does no other work until the refresh finishes.",
            &[
                "Refresh blocks access to the bank while it runs (HiRA, arXiv 2209.10198, p. 1)",
                "Refresh slows the system (page text, section 9)",
            ],
        ),
    Beat::new("RowHammer: one row leaks charge into its neighbours", BEAT_MS)
        .note(
            "Rapidly activating one row can leak charge into the rows beside it. It is both a reliability risk and a security risk.",
            "three cells in a line: the middle one at full height, and the two beside it lower",
        )
        .detail(
            "The neighbours lose charge without ever being accessed themselves.",
            &[
                "Rapid activation of one row can leak charge into its neighbours (page text, section 9)",
                "A reliability and security risk (page text, section 9)",
            ],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("UMD ENEE 359a, Jacob: the DRAM slides", BEAT_MS)
        .note(
            "Two sets of UMD ENEE 359a slides by Jacob cover the DRAM systems and the circuits. Most of the cell's numbers come from them.",
            "the first source card lit gold",
        )
        .detail(
            "The slide numbers are the references for each step on this page.",
            &[
                "UMD ENEE 359a, DRAM Systems (Jacob), slide 3: https://ece.umd.edu/class/enee359a.S2007/enee359a-DRAM-i.pdf",
                "UMD ENEE 359a, DRAM Circuits (Jacob), slides 4, 5, 9, 11, 12-14: https://ece.umd.edu/class/enee359a.S2007/enee359a-DRAM-ii.pdf",
            ],
        ),
    Beat::new("Mutlu: retention in modern DRAM", BEAT_MS)
        .note(
            "Mutlu's retrospective on data retention in modern DRAM is the source for the cell-to-cell variation in leakage.",
            "the Mutlu card lit gold",
        )
        .detail(
            "Retention varies cell to cell, so the refresh window has to cover the weakest cell.",
            &[
                "Mutlu, Retrospective: Data Retention Behavior in Modern DRAM (arXiv 2306.16037): https://arxiv.org/pdf/2306.16037",
                "Retention varies cell to cell (page text, section 9)",
            ],
        ),
    Beat::new("HiRA: sensing, restore and refresh", BEAT_MS)
        .note(
            "The HiRA paper covers the sense amp, the restore step and refresh blocking access to the bank.",
            "the HiRA card lit gold",
        )
        .detail(
            "These are the sources for the read sequence and for the cost of refresh.",
            &[
                "Yaglikci et al., HiRA (arXiv 2209.10198), pp. 1-2: https://arxiv.org/pdf/2209.10198",
                "Refresh blocks access to the bank while it runs (HiRA, p. 1)",
            ],
        ),
    Beat::new("PROTEAS: the DDR4 refresh timing", BEAT_MS)
        .note(
            "The PROTEAS paper gives the Micron DDR4 datasheet values for refresh: the window, the interval and the command count.",
            "the PROTEAS card lit gold",
        )
        .detail(
            "The 64 ms window, the 7800 ns interval and the 8192 commands are all from its Table I.",
            &[
                "PROTEAS (arXiv 2404.16256), Table I (Micron DDR4 datasheet values), pp. 2-3: https://arxiv.org/pdf/2404.16256",
                "tREFW = 64 ms, tREFI = 7800 ns, 8192 REF per window (PROTEAS, Table I)",
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
                    "../../../../../tools/pbr3d/assets/cell_sec",
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
        assert_eq!(counts, [3, 6, 5, 3, 5, 3, 4, 3, 3, 4]);
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
