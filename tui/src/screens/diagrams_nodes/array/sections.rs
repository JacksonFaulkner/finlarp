// ARRAY sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/array_sections.py. Beat counts per section: 4, 4, 5, 3, 4, 4, 3, 3, 4, 4.
// Section 10 is the sources page.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("a grid of 1T1C cells: rows on word lines, columns on bit lines", BEAT_MS)
        .note(
            "The array is a grid of cells, one transistor and one capacitor each. Each row shares a word line and each column shares a bit line.",
            "a grid of cells with a word line along every row and a bit line down every column, sense amps at the bottom",
        )
        .detail(
            "One cell sits at each crossing of a word line and a bit line.",
            &["512 x 512 cells in a typical array (UMD ENEE 359a, DRAM circuits)"],
        ),
    Beat::new("ACTIVATE: one word line opens and its row shares charge with the bit lines", BEAT_MS)
        .note(
            "One word line goes high and opens a whole row. Each cell in the row shares its charge with its bit line.",
            "one word line glowing orange across the row, with the cells of that row lit and small dots running up the bit lines",
        )
        .detail(
            "The row is the unit of access inside the array.",
            &["tRCD = 13.75 ns to open a row (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("sense amps latch the row: the row buffer", BEAT_MS)
        .note(
            "The sense amps amplify each bit line to a full 1 or 0 and hold the whole row. The latched row is the row buffer, and reads come from it.",
            "the sense amp row filling with orange latches for the 1s and dark ones for the 0s, and the bit lines turning cyan",
        )
        .detail(
            "The sense amps restore the cells as they latch them.",
            &["Row buffer: 1 KB per x8 DDR4 chip (page section 6)"],
        ),
    Beat::new("READ picks columns out of the row buffer", BEAT_MS)
        .note(
            "The column decoder sends a burst of the latched columns to the I/O. The row stays open for more READs and then closes.",
            "four green marks on the column decoder bar and green dots running to the I/O pad at the right",
        )
        .detail(
            "Only a small part of the open row leaves per READ.",
            &["64 bits per READ on a x8 chip (page section 6)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("cell: one transistor and one capacitor per bit", BEAT_MS)
        .note(
            "Each cell is one transistor and one capacitor, which holds one bit as a charge. The whole array is these cells.",
            "every cell in the array lit pale blue at once, with the word lines and bit lines running through them",
        )
        .detail(
            "The CELL node shows how one cell and its refresh work.",
            &["1T1C cell (page section 2; see the CELL node)"],
        ),
    Beat::new("row decoder and word line: one row goes high", BEAT_MS)
        .note(
            "The row decoder takes the row part of the address and drives exactly one word line high. Each row has one word line.",
            "one orange word line lit across its row, with the grey row decoder block on the left",
        )
        .detail(
            "Every access starts here; opening a row takes tRCD.",
            &["tRCD = 13.75 ns at DDR4-3200 (AnandTech)"],
        ),
    Beat::new("bit lines and sense amps: the row buffer", BEAT_MS)
        .note(
            "Each bit line carries the charge of the cell in the open row that sits on it. A sense amp on each bit line latches the bit and restores the cell.",
            "bright cyan bit lines running down to a row of purple sense amps, with the orange latches on top of them",
        )
        .detail(
            "The latched row is the row buffer.",
            &["Row buffer: 1 KB per x8 DDR4 chip (page section 6)"],
        ),
    Beat::new("column decoder and I/O: the chosen bits leave the chip", BEAT_MS)
        .note(
            "The column decoder connects a few latches to the data lines. The bits leave the chip on the data pins as a burst.",
            "four green marks on the column decoder bar, green dots running to the grey I/O block at the right",
        )
        .detail(
            "Burst length 8 on a x8 DDR4 chip: 64 bits per READ (page section 6).",
            &["8 data pins x burst length 8 = 64 bits (Micron DDR4 datasheet, not yet linked)"],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. idle: every bit line precharged to VDD/2", BEAT_MS)
        .note(
            "Every bit line rests at the middle level and an address is about to arrive. Every access starts from this state.",
            "grey bit lines at rest, a single white dot entering from the left toward the row decoder",
        )
        .detail(
            "The precharge level is VDD/2 on every bit line.",
            &["Bit lines held at VDD/2 (page section 3)"],
        ),
    Beat::new("2. ACT: the word line rises and the row shares charge", BEAT_MS)
        .note(
            "The row's word line goes high, and its cells share charge with their bit lines, nudging each one up or down.",
            "one word line turning orange, and dots running from the cells of that row onto the bit lines",
        )
        .detail(
            "Columns can be read only after the row has been sensed.",
            &["tRCD = 13.75 ns (DDR4-3200 22-22-22)"],
        ),
    Beat::new("3. sense: the row is latched", BEAT_MS)
        .note(
            "The sense amps drive each bit line to a full level and hold it. The latches fill with the row's bits.",
            "the latch row filling with orange and dark latches, and the bit lines turning bright cyan",
        )
        .detail(
            "The row is now in the row buffer.",
            &["Row buffer: 1 KB per x8 DDR4 chip (page section 6)"],
        ),
    Beat::new("4. READ: columns to the I/O", BEAT_MS)
        .note(
            "The column decoder sends the chosen bits to the I/O. The data comes out tCL after the READ.",
            "green marks on the column decoder bar and green dots running to the I/O pad",
        )
        .detail(
            "Data arrives tCL after READ.",
            &["tCL = 13.75 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("5. PRE: the word line falls and the bit lines return to VDD/2", BEAT_MS)
        .note(
            "PRECHARGE drops the word line and returns the bit lines to VDD/2. The row is closed and another row can open after tRP.",
            "the orange word line fading, the latches and bit lines going dark, and the bit lines back to grey",
        )
        .detail(
            "Another row can open only after tRP.",
            &["tRP = 13.75 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("row hit: 13.75 ns, the open row is read", BEAT_MS)
        .note(
            "The requested row is already open, so the READ only waits for tCL. The lane is one green bar.",
            "a single green bar on the top lane, 13.75 ns long",
        )
        .detail(
            "A hit is the fastest case, and the reason controllers group requests to one row.",
            &["Hit: tCL = 13.75 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("row miss: the bank is closed, 27.5 ns", BEAT_MS)
        .note(
            "No row is open. The row must be activated (tRCD) before the read (tCL): an orange bar, then a green one.",
            "an orange ACT bar followed by a green READ bar on the middle lane",
        )
        .detail(
            "A miss costs twice a hit.",
            &["Miss: tRCD + tCL = 27.5 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("row conflict: close, open, read, 41.25 ns", BEAT_MS)
        .note(
            "Another row is open. It must be closed (tRP), the right one opened (tRCD), then read (tCL): a pink bar, an orange bar, a green bar.",
            "a pink PRE bar, an orange ACT bar and a green READ bar in a row on the bottom lane",
        )
        .detail(
            "A conflict costs three times a hit, so access order matters.",
            &["Conflict: tRP + tRCD + tCL = 41.25 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("a short bit line: a usable signal", BEAT_MS)
        .note(
            "Every cell on a bit line adds capacitance (Cb). The swing the sense amp sees is Cc / (Cc + Cb), so a short line gives a strong swing.",
            "a short bit line of four cells with a purple sense amp at its foot and a tall cyan swing bar beside it",
        )
        .detail(
            "The swing formula is from the DRAM circuits notes; the picture's bar heights are schematic.",
            &["Swing = Cc / (Cc + Cb) (UMD ENEE 359a, DRAM circuits)"],
        ),
    Beat::new("a long bit line: a weaker swing", BEAT_MS)
        .note(
            "Twice the cells means about twice Cb, so the swing shrinks. The bar beside the longer line is shorter.",
            "a bit line of eight cells with a short cyan swing bar beside it",
        )
        .detail(
            "Long bit lines save sense amps but cost signal.",
            &["Bigger Cb, smaller swing (UMD ENEE 359a)"],
        ),
    Beat::new("a sense amp stripe cuts it: the signal comes back", BEAT_MS)
        .note(
            "A sense amp stripe in the middle makes two short lines, each with a good swing. That is why arrays are tiled into mats.",
            "the long bit line cut by a purple stripe, two cyan swing bars each as tall as the short line's",
        )
        .detail(
            "The price is the area of the extra stripes.",
            &["Mats keep bit lines short (page section 5)"],
        ),
    Beat::new("mats form a subarray, and subarrays form a bank", BEAT_MS)
        .note(
            "Mats in a row under one global word line make a subarray with its own local row buffer. Subarrays share global bit lines to form a bank.",
            "three mats side by side under an orange global word line, with a long cyan global bit line beneath them",
        )
        .detail(
            "Each subarray has a local row buffer; SALP designs let subarrays work at once for under 0.15% area.",
            &["Subarrays with local row buffers; SALP under 0.15% (Kim et al., arXiv 1805.01966)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("one array: 512 word lines x 512 bit lines", BEAT_MS)
        .note(
            "A typical array is 512 word lines by 512 bit lines, 262,144 cells. The picture shows a small grid of the same shape.",
            "a square grid of cells with a word line on each row and a bit line on each column",
        )
        .detail(
            "Size is set by the bit line length and the signal it gives.",
            &["512 x 512 array (UMD ENEE 359a, DRAM circuits)"],
        ),
    Beat::new("one row: 1 KB = 8192 bits on an x8 DDR4 chip", BEAT_MS)
        .note(
            "A DDR4 row (page) on an x8 chip is 1 KB, or 8192 bits, spread over many arrays opened together.",
            "sixteen small arrays in a line with one orange word line lit across all of them",
        )
        .detail(
            "Row size 8192 bits (page section 6)",
            &["Page size 1 KB for x8 DDR4 (page section 6; Micron datasheet, not yet linked)"],
        ),
    Beat::new("burst: 8 transfers on 8 pins = 64 bits per READ", BEAT_MS)
        .note(
            "A READ sends 64 bits out of an x8 chip as a burst: eight transfers on each of eight data pins.",
            "eight pins, each sending one green dot down its length in turn",
        )
        .detail(
            "Burst length 8 on DDR4.",
            &["8 pins x burst length 8 = 64 bits (Micron DDR4 datasheet, not yet linked)"],
        ),
    Beat::new("timings: DDR4-3200 22-22-22, tRAS 32.5 ns", BEAT_MS)
        .note(
            "tRCD, tCL and tRP are 13.75 ns each. A row must stay open at least tRAS, which is 32.5 ns, so the pink bar is the longest.",
            "three equal bars for tRCD, tCL and tRP, and a grey tRAS bar more than twice as long",
        )
        .detail(
            "22 clocks x 0.625 ns = 13.75 ns.",
            &["tRCD = tCL = tRP = 13.75 ns; tRAS = 32.5 ns (AnandTech; geizhals DDR4 listing)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("test: some dies have defects", BEAT_MS)
        .note(
            "Wafer test writes and reads the array. A defective cell shows up as a red cell, found by a yellow probe walking the rows.",
            "a yellow probe bar walking down the rows and one red cell in the array",
        )
        .detail(
            "Wafer test finds the defects.",
            &["Defects are found at wafer test (page section 7)"],
        ),
    Beat::new("repair: a laser or electrical fuse stores the bad address", BEAT_MS)
        .note(
            "The bad address is stored in fuses, blown by a laser or electrically. The decoder then knows which row to replace.",
            "a red laser beam hitting the fuse bank at the top right, and one fuse going dark",
        )
        .detail(
            "The fuses are the die's repair map.",
            &["DRAM redundancy patents: fuse-programmed decoders (US 6,731,550; US 5,325,334)"],
        ),
    Beat::new("the decoder sends that address to a spare row", BEAT_MS)
        .note(
            "The bad address now opens a spare row at the edge of the array. The spare row lights green; the bad row is not used.",
            "green dots running from the decoder past the bad row up to the spare row, which lights green",
        )
        .detail(
            "Spares turn would-be scrap into good dies; each spare is area that holds no data.",
            &["Spare rows and columns at the edge of the array (page section 7)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("Micron (MU): commodity DRAM", BEAT_MS)
        .note(
            "Micron is one of the three makers of commodity DRAM. Its card lights up first.",
            "the first paper card on the left with its gold strip lit",
        )
        .detail(
            "Market share is covered on the market pages.",
            &["Commodity DRAM is made by Micron, SK hynix and Samsung (page section 8)"],
        ),
    Beat::new("SK hynix (000660.KS): commodity DRAM", BEAT_MS)
        .note(
            "SK hynix is the second commodity DRAM maker. Its card lights up.",
            "the middle paper card with its gold strip lit, the first card still lit",
        )
        .detail(
            "SK hynix ticker 000660.KS (page section 8)",
            &["SK hynix ticker: 000660.KS (page section 8)"],
        ),
    Beat::new("Samsung (005930.KS): commodity DRAM", BEAT_MS)
        .note(
            "Samsung is the third commodity DRAM maker. Its card lights up last, so all three are lit.",
            "all three paper cards lit, the third on the right",
        )
        .detail(
            "Samsung ticker 005930.KS (page section 8)",
            &["Samsung ticker: 005930.KS (page section 8)"],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("row conflicts cost three times a row hit", BEAT_MS)
        .note(
            "Access patterns that jump between rows of one bank pay tRP + tRCD + tCL every time. The short green hit lane is beside the long conflict lane.",
            "a short green bar for a hit and a conflict bar three times as long, pink, orange and green",
        )
        .detail(
            "Bad access order wastes bandwidth.",
            &["Hit 13.75 ns, conflict 41.25 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("RowHammer: opening one row again and again leaks charge from its neighbours", BEAT_MS)
        .note(
            "Opening one row over and over leaks charge from the cells in the rows beside it, until bits flip. Those neighbour cells turn red.",
            "one word line flickering, and the cells of the rows above and below it turning red",
        )
        .detail(
            "A reliability and security risk.",
            &["Kim et al., Flipping Bits in Memory Without Accessing Them (ISCA 2014)"],
        ),
    Beat::new("the periphery takes area from the cells", BEAT_MS)
        .note(
            "Decoders and sense amp stripes sit around the mats. The shorter the lines, the more of them there are, and they hold no bits.",
            "the sense amp row lit purple and the decoder block on the left lit up around the array",
        )
        .detail(
            "Shorter lines need more periphery; that area stores no data.",
            &["The periphery takes area from the cells (page section 9)"],
        ),
    Beat::new("refresh opens every row in turn", BEAT_MS)
        .note(
            "Refresh opens every row on a timer, one after another, and blocks the bank while it runs.",
            "the bright word line stepping from the bottom row up to the top, one row at a time",
        )
        .detail(
            "Refresh blocks the bank while it runs (see the CELL node).",
            &["Refresh opens every row on a timer (page section 9)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("sources: the DRAM circuits notes and the SALP paper", BEAT_MS)
        .note(
            "Two cards cover the array itself: UMD's ENEE 359a notes on DRAM circuits, and Kim et al.'s SALP retrospective on subarrays with local row buffers.",
            "cards [1] and [2] lit at the top",
        )
        .detail(
            "The 512 x 512 array, sense amps, word line drivers and the swing formula come from [1]; subarrays with local row buffers from [2].",
            &["[1] UMD ENEE 359a, DRAM circuits (Jacob)", "[2] Kim et al., arXiv 1805.01966"],
        ),
    Beat::new("sources: DDR4-3200 timings from AnandTech and a JEDEC profile listing", BEAT_MS)
        .note(
            "Cards [3] and [4] give the timings: AnandTech's DDR5 sub-timings article for DDR4-3200 22-22-22, and a DDR4 listing of CL22-22-22-52.",
            "cards [3] and [4] lit in the second row",
        )
        .detail(
            "DDR4-3200 22-22-22 gives 13.75 ns for tRCD, tCL and tRP; tRAS 52 clocks is 32.5 ns.",
            &["[3] AnandTech, DDR5 sub-timings", "[4] geizhals, DDR4 CL22-22-22-52 listing"],
        ),
    Beat::new("sources: DRAM redundancy patents", BEAT_MS)
        .note(
            "Card [5] covers the repair story: the DRAM redundancy patents for spare rows and columns and fuse-programmed decoders.",
            "card [5] lit in the second row",
        )
        .detail(
            "Spare rows and columns, and the fuses that store bad addresses.",
            &["[5] US 6,731,550; US 5,325,334 (redundancy patents)"],
        ),
    Beat::new("sources: RowHammer, Kim et al., ISCA 2014", BEAT_MS)
        .note(
            "Card [6] is the RowHammer paper: flipping bits in memory by opening rows, without accessing the bits themselves.",
            "card [6] lit in the second row",
        )
        .detail(
            "RowHammer is the disturb effect on the neighbouring rows.",
            &["[6] Kim et al., Flipping Bits in Memory Without Accessing Them (ISCA 2014)"],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/array_sec",
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
        assert_eq!(counts, [4, 4, 5, 3, 4, 4, 3, 3, 4, 4]);
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
