// CELL sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/cell_sections.py. One picture per `# ` heading of MEM_CELL.txt, in order:
// 1 what happens (3 beats), 2 the parts (5), 3 one read (5), 4 refresh (3), 5 leakage (3),
// 6 by the numbers (3), 7 shrinking (3), 8 who makes it (3), 9 chokepoints and risks (3),
// 10 sources (4).

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("a full capacitor reads as 1", BEAT_MS)
        .note(
            "A DRAM bit is a packet of charge on one tiny capacitor. The cell is one transistor and one capacitor, so it is called 1T1C.",
            "the full orange capacitor on its storage node, the transistor beside it, and the bit line above with the gauge at the VDD/2 ring",
        )
        .detail(
            "An array is this one small part, repeated.",
            &[
                "The cell is 1 transistor and 1 capacitor, 1T1C (page text, section 1)",
                "Full charge reads as 1, empty as 0 (page text, section 1)",
            ],
        ),
    Beat::new("an empty capacitor reads as 0", BEAT_MS)
        .note(
            "The same cell holds a 0 when its capacitor is empty. A bit is an amount of charge, and a read pulls the line the other way.",
            "the capacitor empty and dark, the transistor and bit line as before, the gauge dipping below the ring",
        )
        .detail(
            "A bit is not a switch that stays set. It is an amount of charge, which is why the rest of this page is about keeping it.",
            &[
                "Empty = 0 (page text, section 1)",
                "The bit is charge that leaks, so it needs refresh (page text, section 5)",
            ],
        ),
    Beat::new("every cell in the array holds its own bit", BEAT_MS)
        .note(
            "Zoom out and the cell is one of many, each with its own transistor and capacitor, each storing its own 1 or 0.",
            "a 3 by 3 block of storage capacitors with alternate ones full and empty; the picture is schematic, not to scale",
        )
        .detail(
            "Each bit gets its own transistor and capacitor.",
            &[
                "A typical array is 512 wordlines by 512 bitlines (Jacob, DRAM Circuits, slide 5)",
                "Each bit has its own transistor and capacitor (page text, section 1)",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("word line: the row select", BEAT_MS)
        .note(
            "The word line runs along a row. Driving it high turns on every access transistor in that row at once.",
            "the pink word line lit, the channel glowing under its gate, and the drain and source blocks either side",
        )
        .detail(
            "One word line opens a whole row, not a single cell.",
            &[
                "Word line: high turns on every access transistor in its row (page text, section 2)",
                "Word line: a row select (page text, section 2)",
            ],
        ),
    Beat::new("access transistor: the switch", BEAT_MS)
        .note(
            "The access transistor is a switch between the bit line and the storage node. Off, the cell is cut off. On, charge can move.",
            "the channel lit under the gate, with dots crossing from the capacitor toward the bit line",
        )
        .detail(
            "While it is off the transistor is meant to hold the charge in, but it still leaks a little.",
            &[
                "Access transistor: a switch between the bit line and the storage node (page text, section 2)",
                "Its leakage when off sets how long the charge lasts (page text, section 5)",
            ],
        ),
    Beat::new("storage capacitor: the bit itself", BEAT_MS)
        .note(
            "The storage capacitor holds the bit as charge on its plate. Everything else in the cell exists to read or refill it.",
            "the inner plate filled with orange charge, the outer plate and the dielectric around it",
        )
        .detail(
            "Nearly all of the bit is here, so its size sets how strong a read can be.",
            &[
                "Storage capacitor holds the bit as charge on its plate (page text, section 2)",
                "The capacitance sets the swing the sense amp sees (page text, section 7)",
            ],
        ),
    Beat::new("bit line: the column wire", BEAT_MS)
        .note(
            "The bit line is the column wire that carries charge to and from the cell. It is precharged to VDD/2 before each read.",
            "the cyan bit line running across the top, its plug down to the drain, and the green precharge block at its far end",
        )
        .detail(
            "The cell is tiny, so its charge moves a much bigger bit line only a little. The sense amp has to detect that move.",
            &[
                "Bit line precharged to VDD/2 before each read (Jacob, DRAM Circuits, slides 4 and 11)",
                "Bit line: the column wire (page text, section 2)",
            ],
        ),
    Beat::new("sense amp: the latch", BEAT_MS)
        .note(
            "The sense amp is two cross-coupled inverters on a bit line pair. It sees a small difference and latches to a full rail.",
            "the purple sense amp block lit at the end of the bit line",
        )
        .detail(
            "It turns a tiny bump into a full 1 or 0, and it writes the cell back.",
            &[
                "Sense amp: two cross-coupled inverters on a bit line pair (Jacob, DRAM Circuits, slides 12-14)",
                "The sense amp latches to a full rail (page text, section 2)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. precharge: the bit line sits at VDD/2", BEAT_MS)
        .note(
            "Before the read the bit line waits at the middle, VDD/2, and the cell is full. Every read starts from this same state.",
            "the green precharge block lit, the gauge on the VDD/2 ring, the capacitor full and the word line low",
        )
        .detail(
            "Every read starts from this same state, so the swing is always small and centred.",
            &[
                "The bit line is precharged to VDD/2 (page text, section 3)",
                "Precharge to Vcc/2 before a read (Jacob, DRAM Circuits, slides 4 and 11)",
            ],
        ),
    Beat::new("2. word line rises: the access transistor switches on", BEAT_MS)
        .note(
            "The word line goes high and the transistor switches on. Nothing else has moved yet, but the cell is now joined to the bit line.",
            "the pink word line lit, the channel glowing under the gate",
        )
        .detail(
            "The word line opens the whole row, so all its cells start a read together.",
            &[
                "High turns on every access transistor in the row (page text, section 3)",
                "A typical array is 512 by 512 (Jacob, DRAM Circuits, slide 5)",
            ],
        ),
    Beat::new("3. charge sharing: the bit line moves a small amount", BEAT_MS)
        .note(
            "Charge moves between the cell and the bit line. The bit line moves a small amount, up for a 1 and down for a 0.",
            "cyan dots crossing from the storage node to the bit line, and the gauge bumping just off the VDD/2 ring",
        )
        .detail(
            "The read has already put the stored bit at risk here; the restore in step 5 puts it back.",
            &[
                "The bit line moves up for a 1, down for a 0 (page text, section 3)",
                "Final voltage (Cb VBL + Cc Vcell) / (Cb + Cc) (Jacob, DRAM Circuits, slides 4 and 11)",
            ],
        ),
    Beat::new("4. sense amp: the latch drives the bit line to a full rail", BEAT_MS)
        .note(
            "The sense amp detects the small move and drives the bit line all the way to full VDD, or to GND for a 0. This is where the bit is read.",
            "the purple sense amp lit and the gauge climbing to the top",
        )
        .detail(
            "The latch is the read. Everything before it only made the difference big enough to see.",
            &[
                "The latch drives the bit line to a full VDD or full GND (page text, section 3)",
                "Sense amp latches the bit line to full VDD or GND (Jacob, DRAM Circuits, slides 12-14)",
            ],
        ),
    Beat::new("5. restore: the still-connected cell returns to full charge", BEAT_MS)
        .note(
            "The cell is still connected, so the driven bit line pushes it back to full charge. The read drains the cell, so the restore is part of every read.",
            "violet dots refilling the capacitor to full height, the gauge at the top, and then the word line falling",
        )
        .detail(
            "A DRAM read destroys what it reads and then writes it back.",
            &[
                "The restore step is part of every read (page text, section 3)",
                "Restore: the read drains the cell and the sense amp writes it back (HiRA, arXiv 2209.10198, p. 2)",
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
    Beat::new("charge drains from every cell", BEAT_MS)
        .note(
            "Charge drains from the storage node through the dielectric, the junction and the off transistor. The loss is slow and differs from cell to cell.",
            "three cylinders of charge, each one falling at its own speed",
        )
        .detail(
            "The leak rates in the picture are illustrative. The point is that they vary.",
            &[
                "Retention varies cell to cell (Mutlu, arXiv 2306.16037, p. 1)",
                "Leak paths: dielectric, junction, off transistor (general knowledge; the split is not sourced here)",
            ],
        ),
    Beat::new("the weakest cell sets the deadline", BEAT_MS)
        .note(
            "Most cells could wait longer. The weakest cannot, and one refresh window applies to them all, so the window has to cover the weakest.",
            "the lowest cylinder falling fastest toward the floor of the chart",
        )
        .detail(
            "One rule for all the cells means the worst cell sets the pace for the rest.",
            &[
                "The minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)",
                "The refresh window has to cover the weakest cells (page text, section 5)",
            ],
        ),
    Beat::new("refresh arrives just in time", BEAT_MS)
        .note(
            "The refresh rewrites every cell before the weakest crosses the line. Cells that still had charge left get rewritten too.",
            "all three columns rising back to full, the weakest one just above the floor when the refresh arrives",
        )
        .detail(
            "Most of the refresh work goes to cells that did not need it yet.",
            &[
                "The refresh window has to cover the weakest cells (page text, section 5)",
                "tREFW = 64 ms (DDR4; PROTEAS, arXiv 2404.16256, Table I)",
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
    Beat::new("a wide cell: a big capacitor, a big swing", BEAT_MS)
        .note(
            "The bit line's move on a read is (Vcell - VDD/2) x Cc / (Cc + Cb). Cc is the cell's capacitance and Cb the bit line's. A wide cell has a big Cc, so the swing is big.",
            "the wide grey outer plate, the orange charge in the inner plate, and the storage node below",
        )
        .detail(
            "Cb is much bigger than Cc, so the swing is a small fraction of the voltage.",
            &[
                "Swing = (Vcell - VDD/2) x Cc / (Cc + Cb) (Jacob, DRAM Circuits, slides 4 and 11)",
                "Cell area 6F^2 with an open bit line (Jacob, DRAM Circuits, slide 9)",
            ],
        ),
    Beat::new("shrink the cell and the swing shrinks", BEAT_MS)
        .note(
            "A smaller feature size F means a smaller capacitor, so a smaller Cc. Cb has not changed, so the swing drops and the sense amp has less to work with.",
            "the plates narrowing inside their old outline and the orange fill getting smaller",
        )
        .detail(
            "Less signal is what shrinking the cell costs.",
            &[
                "A smaller storage capacitor gives a smaller swing (page text, section 7)",
                "Cell area is set by F, the minimum feature size (page text, section 7)",
            ],
        ),
    Beat::new("a taller capacitor brings the swing back", BEAT_MS)
        .note(
            "Designs keep Cc up with a taller capacitor or a better dielectric. The cell's footprint stays small, and the capacitance returns.",
            "the orange cell growing upward, the plates stretching, and the footprint at the base staying narrow",
        )
        .detail(
            "The footprint keeps shrinking while the height does the work.",
            &[
                "Designs keep Cc up with a taller capacitor or a better dielectric (page text, section 7)",
                "The swing depends on Cc against Cb (page text, section 7)",
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
        assert_eq!(counts, [3, 5, 5, 3, 3, 3, 3, 3, 3, 4]);
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
