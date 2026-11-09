// ARRAY page: one DRAM subarray, drawn in 3D by poly3d, on the CELL page's template.
// The overview walks one access: an address reaches the row decoder, ACTIVATE opens a
// row, the sense amps latch it (the row buffer), READ sends columns to the I/O, a
// second READ hits the open row, PRECHARGE closes it, and refresh walks the rows. Each
// zoom (a-e) is its own focused 3D scene: a the row buffer, b hit/miss/conflict
// timings, c mats and subarrays, d redundancy, e a burst. Sections 1-9 each have one.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: see section 10 of MEM_ARRAY.txt. Jacob, ENEE 359a DRAM Circuits (512 x 512
// array, sense amps, word line drivers); Kim et al., SALP retrospective (arXiv
// 1805.01966: a bank is many subarrays with local row buffers); DDR4-3200 22-22-22
// (13.75 ns tRCD/tCL/tRP, 32.5 ns tRAS); Kim et al., ISCA 2014 (RowHammer).

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::ArrayZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 6500;
const OVERVIEW_MS: u64 = 13000;

const BEATS: &[Beat] = &[
    Beat::new("an address arrives: the row decoder picks one row", OVERVIEW_MS)
        .note(
            "The memory controller sends a bank and row address. The row decoder turns it into one word line out of all the rows in the subarray.",
            "White dots run into the row decoder on the left; every bit line sits at the middle level, precharged.",
        )
        .detail(
            "The array is a grid: rows of cells on word lines, columns of cells on bit lines. Every access starts with a row.",
            &["Typical array: 512 word lines x 512 bit lines (Jacob, DRAM Circuits)"],
        ),
    Beat::new("ACTIVATE: one word line rises and the whole row shares its charge", OVERVIEW_MS)
        .note(
            "The decoder drives one word line high. Every access transistor in that row turns on, and each cell nudges its bit line a little up (1) or down (0).",
            "One word line thickens and turns orange; small dots run from each cell of that row onto its bit line.",
        )
        .detail(
            "A row is opened all at once: there is no way to read one cell on its own.",
            &["ACT opens one row of the bank"],
        ),
    Beat::new("sense: the sense amps latch the row, the row buffer", OVERVIEW_MS)
        .note(
            "Each bit line has a sense amp. They amplify the small nudges to full 1s and 0s and hold them. Together they are the row buffer, and they also rewrite the cells.",
            "The sense amp stripe at the front fills with orange (1) and dark (0) latches; the bit lines turn cyan or dark.",
        )
        .detail(
            "Opening a row takes tRCD before any column can be read.",
            &["tRCD = 13.75 ns (DDR4-3200 22-22-22)", "Row buffer: 1 KB per x8 DDR4 chip"],
        ),
    Beat::new("READ: the column decoder sends a burst of bits to the I/O", OVERVIEW_MS)
        .note(
            "READ carries a column address. The column decoder connects a few latches of the row buffer to the data lines, and the bits leave the chip as a burst.",
            "Green dots run from four sense amps through the column decoder to the I/O pad.",
        )
        .detail(
            "Data comes from the row buffer, not from the cells.",
            &["tCL = 13.75 ns from READ to data (DDR4-3200)", "Burst length 8 on DDR4"],
        ),
    Beat::new("row hit: another READ to the open row skips the activate", OVERVIEW_MS)
        .note(
            "The row is still open, so a second READ to other columns is served straight from the row buffer, with no ACTIVATE.",
            "Green dots run again, this time from four other sense amps.",
        )
        .detail(
            "A row hit costs tCL alone; a conflict costs tRP + tRCD + tCL, three times as long at DDR4-3200.",
            &["Hit 13.75 ns; conflict 41.25 ns (DDR4-3200)"],
        ),
    Beat::new("PRECHARGE: the word line falls and the bit lines return to the middle", OVERVIEW_MS)
        .note(
            "PRECHARGE closes the row: the word line drops, the cells are cut off holding their restored charge, and the bit lines go back to VDD/2.",
            "The orange word line fades, the latches empty, and the bit lines return to grey.",
        )
        .detail(
            "The next row in this bank cannot open until precharge is done.",
            &["tRP = 13.75 ns; tRAS (ACT to PRE) = 32.5 ns (DDR4-3200)"],
        ),
    Beat::new("refresh: every row is opened and closed in turn", OVERVIEW_MS)
        .note(
            "The cells leak, so the rows are refreshed on a timer: each is opened, sensed, rewritten and closed, one after another.",
            "Word lines rise and fall down the array, row by row, and the latches pulse with each.",
        )
        .detail(
            "Refresh is just ACT and PRE without the read; see the CELL node for the 64 ms window.",
            &["tREFW = 64 ms in DDR4 (CELL node)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "the row buffer: a whole row in the sense amps", build: || -> Box<dyn Scene> { Box::new(RowBufZ) } },
    Zoom { key: 'b', label: "row hit, row miss, row conflict", build: || -> Box<dyn Scene> { Box::new(HitsZ) } },
    Zoom { key: 'c', label: "mats, subarrays and the bank", build: || -> Box<dyn Scene> { Box::new(MatsZ) } },
    Zoom { key: 'd', label: "redundancy: a spare row takes over", build: || -> Box<dyn Scene> { Box::new(RedundancyZ) } },
    Zoom { key: 'e', label: "a burst: eight transfers from the open row", build: || -> Box<dyn Scene> { Box::new(BurstZ) } },
];

/// The overview at `t`, turned by the user's `view`, with the beat's notes on it.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes { what: b.what, why: b.why, facts: b.facts };
    poly3d::render_array_overview(t.beat, t.local as f64, view, Some(&notes), w as usize, h as usize, px::BG)
}

/// The ARRAY overview: one access through a subarray.
pub struct MemArray;

impl Scene for MemArray {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }
    fn beats(&self) -> &[Beat] {
        BEATS
    }
    fn draw(&self, _c: &mut Canvas, _t: &Time) {}
    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
        Some(overview_frame(t, &poly3d::View::default(), w, h))
    }
    fn notes_in_picture(&self) -> bool {
        true
    }
    fn rest_point(&self) -> f32 {
        0.4
    }
}

/// The 3D scene behind zoom `key`: letters are parts of the overview, numbers the
/// page's sections.
pub fn zoom_scene(key: char) -> Option<ArrayZoom> {
    Some(match key {
        'a' => ArrayZoom::RowBuffer,
        'b' => ArrayZoom::Hits,
        'c' => ArrayZoom::Mats,
        'd' => ArrayZoom::Redundancy,
        'e' => ArrayZoom::Burst,
        '1' => ArrayZoom::Grid,
        '2' => ArrayZoom::Parts,
        '3' => ArrayZoom::Order,
        '4' => ArrayZoom::RowHits,
        '5' => ArrayZoom::MatsWhy,
        '6' => ArrayZoom::Numbers,
        '7' => ArrayZoom::Repair,
        '8' => ArrayZoom::Makers,
        '9' => ArrayZoom::Risks,
        _ => return None,
    })
}

macro_rules! zoom_scene_impl {
    ($name:ident, $beats:ident, $zoom:expr) => {
        pub struct $name;

        impl Scene for $name {
            fn size(&self) -> (u16, u16) {
                (MIN_W, MIN_H)
            }
            fn beats(&self) -> &[Beat] {
                $beats
            }
            fn draw(&self, _c: &mut Canvas, _t: &Time) {}
            fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
                Some(poly3d::render_array_zoom(
                    $zoom,
                    t.beat,
                    t.local as f64,
                    &poly3d::View::default(),
                    w as usize,
                    h as usize,
                    px::BG,
                ))
            }
        }
    };
}

const ROWBUF_BEATS: &[Beat] = &[
    Beat::new("a row opens and the sense amps latch all of it", BEAT_MS)
        .note(
            "ACTIVATE raises one word line. Every cell in the row nudges its bit line, and the sense amp on each bit line latches the bit.",
            "Close on the stripe: dots run down every bit line and the latches fill one colour per bit.",
        )
        .detail("The whole row moves at once, thousands of bits per chip.", &["One sense amp per bit line"]),
    Beat::new("the row buffer serves reads", BEAT_MS)
        .note(
            "While the row stays open, READs pick latches out of the row buffer. The cells are not touched again.",
            "Green dots leave five latches for the column decoder.",
        )
        .detail("An open row works like a small cache.", &["Row buffer: 1 KB per x8 DDR4 chip"]),
    Beat::new("precharge empties it for the next row", BEAT_MS)
        .note(
            "The sense amps have already rewritten the cells. Precharge drops the word line and resets the bit lines and latches.",
            "The word line fades, then the latches and bit lines return to grey.",
        )
        .detail("Only then can another row in the subarray open.", &["tRP = 13.75 ns (DDR4-3200)"]),
];

const HITS_BEATS: &[Beat] = &[
    Beat::new("row hit: the row is already open, 13.75 ns", BEAT_MS)
        .note(
            "The requested row is in the row buffer, so the READ only waits tCL.",
            "A single green RD segment grows on the first lane.",
        )
        .detail("Controllers try to group requests to the same row for this reason.", &["tCL = 13.75 ns (DDR4-3200 22-22-22)"]),
    Beat::new("row miss: the bank is closed, 27.5 ns", BEAT_MS)
        .note(
            "No row is open. The row has to be activated (tRCD) before the read (tCL).",
            "An orange ACT segment then a green RD segment grow on the second lane.",
        )
        .detail("Twice a hit.", &["tRCD + tCL = 27.5 ns"]),
    Beat::new("row conflict: another row is open, 41.25 ns", BEAT_MS)
        .note(
            "The wrong row is open. It must be closed (tRP), the right one opened (tRCD), then read (tCL).",
            "Pink PRE, orange ACT and green RD segments grow on the third lane.",
        )
        .detail("Three times a hit: why access order matters.", &["tRP + tRCD + tCL = 41.25 ns"]),
];

const MATS_BEATS: &[Beat] = &[
    Beat::new("one mat: a small grid with its own drivers and sense amps", BEAT_MS)
        .note(
            "The array is built from small tiles called mats. Each has local word line drivers on one side and sense amp stripes on two.",
            "One orange tile with purple stripes front and back and a grey driver strip.",
        )
        .detail("Keeping mats small keeps word lines and bit lines short.", &["Typical array: 512 x 512 (Jacob, DRAM Circuits)"]),
    Beat::new("a subarray: mats in a row under one global word line", BEAT_MS)
        .note(
            "Mats line up into a subarray. A global word line runs over them and wakes the local drivers of the row being opened.",
            "Three more mats rise beside the first and an orange global word line runs across.",
        )
        .detail("A subarray has its own row of sense amps: its local row buffer.", &["Subarrays have local row buffers (Kim et al., arXiv 1805.01966)"]),
    Beat::new("a bank: subarrays share global bit lines", BEAT_MS)
        .note(
            "Many subarrays make a bank. They share global bit lines and the bank's I/O, so one subarray's row is open at a time in a standard bank.",
            "Twelve more mats rise; cyan global bit lines carry data from the open subarray to the front.",
        )
        .detail("Research designs (SALP) let several subarrays work at once for under 0.15% area.", &["SALP: <0.15% area overhead (Kim et al., arXiv 1805.01966)"]),
];

const REDUNDANCY_BEATS: &[Beat] = &[
    Beat::new("test finds a bad cell", BEAT_MS)
        .note(
            "At wafer test every cell is written and read. One fails.",
            "A yellow probe line walks down the rows and one cell turns pink.",
        )
        .detail("With billions of cells per die, some always fail.", &["Defects are found at wafer test"]),
    Beat::new("a laser blows a fuse to store the bad address", BEAT_MS)
        .note(
            "The bad row's address is written into a fuse bank by cutting fuses with a laser (or electrical fuses).",
            "A pink beam hits the fuse bank and one fuse goes dark; the spare rows light green.",
        )
        .detail("The fuses are the die's repair map.", &["Laser or electrical fuses program the redundant decoder (DRAM redundancy patents)"]),
    Beat::new("the decoder sends that address to a spare row", BEAT_MS)
        .note(
            "From now on, the bad row's address opens a spare row at the edge of the array instead. Nothing outside the chip can tell.",
            "Green dots run from the decoder past the bad row to the first spare row.",
        )
        .detail("Spares turn would-be scrap into good dies.", &["Spare rows and columns replace bad ones"]),
];

const BURST_BEATS: &[Beat] = &[
    Beat::new("a column address picks 64 bits of the open row", BEAT_MS)
        .note(
            "READ's column address selects a group of latches in the row buffer: 64 bits on a x8 chip.",
            "Two rows of the latch strip rise and turn green.",
        )
        .detail("8 pins x burst length 8 = 64 bits per READ.", &["x8 DDR4: 8 data pins", "Burst length 8"]),
    Beat::new("they leave as eight transfers on eight pins", BEAT_MS)
        .note(
            "The 64 bits go out in 8 beats on the 8 data pins, two beats per clock.",
            "Waves of green dots run down the eight pins.",
        )
        .detail("DDR moves data on both clock edges.", &["DDR4-3200: 3200 million transfers per second per pin"]),
    Beat::new("the next READ to the open row: another 64, no activate", BEAT_MS)
        .note(
            "Another column of the same open row needs no ACT: it is a row hit.",
            "A different pair of latch rows lights and the pins run again.",
        )
        .detail("Streaming through an open row is the fastest way to read DRAM.", &["Row hit: tCL only"]),
];

zoom_scene_impl!(RowBufZ, ROWBUF_BEATS, ArrayZoom::RowBuffer);
zoom_scene_impl!(HitsZ, HITS_BEATS, ArrayZoom::Hits);
zoom_scene_impl!(MatsZ, MATS_BEATS, ArrayZoom::Mats);
zoom_scene_impl!(RedundancyZ, REDUNDANCY_BEATS, ArrayZoom::Redundancy);
zoom_scene_impl!(BurstZ, BURST_BEATS, ArrayZoom::Burst);

// ---- 1-9: the write-up's sections ---------------------------------------------

const GRID_BEATS: &[Beat] = &[
    Beat::new("a grid of cells: rows on word lines, columns on bit lines", BEAT_MS)
        .note(
            "The array is a grid of 1T1C cells. Each row shares a word line; each column shares a bit line.",
            "Looking down on rows of orange and dark cells, with an address arriving at the decoder.",
        )
        .detail("One cell sits at each crossing.", &["Typical array: 512 x 512"]),
    Beat::new("a whole row is opened into the sense amps", BEAT_MS)
        .note("One word line opens a whole row, and the sense amps latch it.", "A row lights orange and the sense amp stripe fills.")
        .detail("The row is the unit of access inside the array.", &["ACT opens one row"]),
    Beat::new("columns are read out of the sense amps", BEAT_MS)
        .note("The column decoder picks some of the latched bits and sends them to the I/O.", "Green dots leave four latches for the I/O pad.")
        .detail("Then the row closes and the array is ready again.", &["READ picks columns"]),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("cells: one bit each", BEAT_MS)
        .note("Each cell is one transistor and one capacitor holding one bit.", "The cells keep their colour; the rest go grey.")
        .detail("See the CELL node for how one works.", &["1T1C cell"]),
    Beat::new("row decoder and word lines: pick a row", BEAT_MS)
        .note("The row decoder turns the row address into one high word line.", "An address runs into the decoder and one word line turns orange.")
        .detail("One word line per row.", &["ACT raises one word line"]),
    Beat::new("bit lines: one per column", BEAT_MS)
        .note("Each bit line carries the charge of the one cell in the open row that sits on it.", "Dots run from the open row down the bit lines.")
        .detail("Bit line capacitance grows with its length.", &["One bit line per column"]),
    Beat::new("sense amps: the row buffer", BEAT_MS)
        .note("A sense amp on each bit line amplifies and latches the bit, and restores the cell.", "The sense amp stripe fills with the row's bits.")
        .detail("The latched row is the row buffer.", &["Row buffer: 1 KB per x8 DDR4 chip"]),
    Beat::new("column decoder: pick the bits", BEAT_MS)
        .note("The column decoder connects a few latches to the data lines.", "Four column decoder slots light green.")
        .detail("Only a small part of the row leaves per READ.", &["64 bits per READ on a x8 chip"]),
    Beat::new("I/O: off the chip", BEAT_MS)
        .note("The bits leave the chip on the data pins as a burst.", "Green dots reach the I/O pad.")
        .detail("BANK and BANDWIDTH take it from here.", &["Burst length 8"]),
];

const ORDER_BEATS: &[Beat] = &[
    Beat::new("1. idle: bit lines precharged to VDD/2", BEAT_MS)
        .note("Every bit line rests at the middle level; an address arrives.", "Grey bit lines; dots run into the row decoder.")
        .detail("Every access starts from this state.", &["Bit lines at VDD/2"]),
    Beat::new("2. ACT: the word line rises", BEAT_MS)
        .note("The row's word line goes high and its cells share charge with the bit lines.", "One word line turns orange; dots run onto the bit lines.")
        .detail("The read has started to drain the cells.", &["ACT"]),
    Beat::new("3. sense: the row is latched", BEAT_MS)
        .note("The sense amps drive each bit line to a full level and hold it.", "The latches fill; bit lines turn cyan or dark.")
        .detail("Columns can be read after tRCD.", &["tRCD = 13.75 ns"]),
    Beat::new("4. READ: columns to the I/O", BEAT_MS)
        .note("The column decoder sends the chosen bits to the I/O.", "Green dots run to the I/O pad.")
        .detail("Data arrives tCL after READ.", &["tCL = 13.75 ns"]),
    Beat::new("5. PRE: the row closes", BEAT_MS)
        .note("The word line falls and the bit lines return to VDD/2.", "The row fades and the stripe empties.")
        .detail("Another row can open after tRP.", &["tRP = 13.75 ns"]),
];

const ROWHITS_BEATS: &[Beat] = &[
    Beat::new("row hit: read the open row again", BEAT_MS)
        .note("Row A is open, so the READ goes straight to the row buffer.", "Row A stays orange and green dots leave the latches.")
        .detail("13.75 ns at DDR4-3200.", &["Hit: tCL"]),
    Beat::new("row conflict: close A, open B, then read", BEAT_MS)
        .note("A request for row B finds A open: precharge A, activate B, then read.", "Row A fades, the latches empty, row B opens and they refill.")
        .detail("41.25 ns: three times the hit.", &["Conflict: tRP + tRCD + tCL"]),
    Beat::new("row miss: the bank is closed, open A and read", BEAT_MS)
        .note("With the bank closed, the next request only has to activate and read.", "Row B closes; later row A opens and is read.")
        .detail("27.5 ns: twice the hit.", &["Miss: tRCD + tCL"]),
];

const MATSWHY_BEATS: &[Beat] = &[
    Beat::new("a short bit line: a usable signal", BEAT_MS)
        .note("Every cell on a bit line adds capacitance (Cb). The swing the sense amp sees is Cc / (Cc + Cb).", "A line of cells with a sense amp at the end and a cyan swing bar.")
        .detail("The Cb per cell here is illustrative.", &["swing = (Vcell - VDD/2) x Cc / (Cc + Cb) (Jacob, DRAM Circuits)"]),
    Beat::new("double the line: half the signal", BEAT_MS)
        .note("Twice the cells means about twice Cb, and the swing shrinks.", "More cells rise along the line and the bar drops.")
        .detail("Long bit lines save sense amps but cost signal.", &["Bigger Cb, smaller swing"]),
    Beat::new("cut it with a stripe: the signal is back", BEAT_MS)
        .note("A sense amp stripe in the middle makes two short lines, each with a good swing. That is why arrays are tiled into mats.", "A purple stripe rises mid-line and the bar climbs back.")
        .detail("The price is the area of the extra stripes.", &["Mats keep bit lines short"]),
];

const NUMBERS_BEATS: &[Beat] = &[
    Beat::new("one array: 512 x 512 cells", BEAT_MS)
        .note("A typical array is 512 word lines by 512 bit lines: 262,144 cells.", "A square grid, one line per 8 cells.")
        .detail("Size is set by bit line length and signal.", &["512 x 512 (Jacob, DRAM Circuits)"]),
    Beat::new("one row: 1 KB on a x8 DDR4 chip", BEAT_MS)
        .note("A DDR4 row (page) on a x8 chip is 8 Kb, spread over many arrays opened together.", "Sixteen arrays in a line with one row lit across them.")
        .detail("8192 bits / 512 per array = 16 arrays.", &["Page size 1 KB for x8 (Micron DDR4 datasheet)"]),
    Beat::new("the timings: DDR4-3200 22-22-22", BEAT_MS)
        .note("tRCD, tCL and tRP are 13.75 ns each; a row must stay open at least tRAS, 32.5 ns.", "Three equal green bars and a taller pink one.")
        .detail("22 clocks x 0.625 ns = 13.75 ns.", &["tRCD = tCL = tRP = 13.75 ns", "tRAS = 32.5 ns (52 clocks)"]),
];

const REPAIR_BEATS: &[Beat] = &[
    Beat::new("test: some dies have defects", BEAT_MS)
        .note("Every die is tested; defects show up scattered across the wafer.", "Pink dots appear on some dies.")
        .detail("Defect counts per die are illustrative.", &["Defects found at wafer test"]),
    Beat::new("repair: spares fix the dies with a few", BEAT_MS)
        .note("Dies with no more defects than spares are repaired by remapping the bad rows and columns.", "Most dies turn green as their dots fade.")
        .detail("Here each die has two spares.", &["Spare rows and columns"]),
    Beat::new("too many defects: the die is scrap", BEAT_MS)
        .note("Dies with more defects than spares stay bad. Spares raise yield but take area.", "A few dies turn dark red; a count of good dies appears.")
        .detail("Choosing how many spares is a yield-versus-area trade.", &["Spare rows hold no data"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note("Micron makes commodity DRAM.", "The first wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["Commodity DRAM makers: Micron, SK hynix, Samsung"]),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note("SK hynix makes commodity DRAM and HBM.", "The second wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["SK hynix ticker: 000660.KS"]),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note("Samsung makes commodity DRAM and HBM.", "The third wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["Samsung ticker: 005930.KS"]),
];

const RISKS_BEATS: &[Beat] = &[
    Beat::new("row conflicts cost three times a hit", BEAT_MS)
        .note("Access patterns that jump between rows of one bank pay tRP + tRCD + tCL each time.", "A short green bar beside a pink one three times taller.")
        .detail("Bad access order wastes bandwidth.", &["Hit 13.75 ns, conflict 41.25 ns (DDR4-3200)"]),
    Beat::new("RowHammer: opening one row drains its neighbours", BEAT_MS)
        .note("Opening one row again and again leaks charge from cells in the rows next to it, until bits flip.", "One word line flickers; cells in the rows beside it dim and one turns pink.")
        .detail("A reliability and security risk.", &["Kim et al., Flipping Bits in Memory Without Accessing Them (ISCA 2014)"]),
    Beat::new("the periphery takes area from the cells", BEAT_MS)
        .note("Decoders and sense amp stripes sit around every mat; the shorter the lines, the more of them.", "A mat with purple stripes and a cyan decoder strip around the orange cells.")
        .detail("Every stripe added is area that stores no bits.", &["Periphery vs cell area trade-off"]),
];

zoom_scene_impl!(SecGrid, GRID_BEATS, ArrayZoom::Grid);
zoom_scene_impl!(SecParts, PARTS_BEATS, ArrayZoom::Parts);
zoom_scene_impl!(SecOrder, ORDER_BEATS, ArrayZoom::Order);
zoom_scene_impl!(SecRowHits, ROWHITS_BEATS, ArrayZoom::RowHits);
zoom_scene_impl!(SecMatsWhy, MATSWHY_BEATS, ArrayZoom::MatsWhy);
zoom_scene_impl!(SecNumbers, NUMBERS_BEATS, ArrayZoom::Numbers);
zoom_scene_impl!(SecRepair, REPAIR_BEATS, ArrayZoom::Repair);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, ArrayZoom::Makers);
zoom_scene_impl!(SecRisks, RISKS_BEATS, ArrayZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecGrid),
    || Box::new(SecParts),
    || Box::new(SecOrder),
    || Box::new(SecRowHits),
    || Box::new(SecMatsWhy),
    || Box::new(SecNumbers),
    || Box::new(SecRepair),
    || Box::new(SecMakers),
    || Box::new(SecRisks),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(beat: usize, local: f32) -> Time {
        Time { ms: 0, beat, local, beat_start: 0 }
    }

    fn scenes() -> Vec<(String, Box<dyn Scene>)> {
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), Box::new(MemArray))];
        for z in ZOOMS {
            v.push((z.key.to_string(), (z.build)()));
        }
        for (i, mk) in SECTIONS.iter().enumerate() {
            v.push(((i + 1).to_string(), mk()));
        }
        v
    }

    #[test]
    fn every_frame_is_a_picture_that_moves() {
        for (name, scene) in scenes() {
            let p = Player::new(scene, Instant::now());
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(397) {
                let img = p.pixels(&p.time_at(ms), 160, 90).expect("pixel frame");
                assert_eq!(img.dimensions(), (160, 90), "{name}");
                seen.insert(img.into_raw());
            }
            assert!(seen.len() > 12, "{name}: {} distinct frames", seen.len());
        }
    }

    /// Text and picture agree on how many beats each scene has.
    #[test]
    fn beats_match_their_pictures() {
        assert_eq!(BEATS.len(), poly3d::ARRAY_OVERVIEW_BEATS);
        for z in ZOOMS {
            assert_eq!((z.build)().beats().len(), zoom_scene(z.key).unwrap().beats(), "zoom {}", z.key);
        }
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            assert_eq!(mk().beats().len(), zoom_scene(key).unwrap().beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("ARRAY")
            .unwrap()
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(heads, SECTIONS.len() + 1, "one scene per section but the sources");
    }

    #[test]
    fn beats_have_text_for_the_popup() {
        let all = BEATS
            .iter()
            .chain(ROWBUF_BEATS)
            .chain(HITS_BEATS)
            .chain(MATS_BEATS)
            .chain(REDUNDANCY_BEATS)
            .chain(BURST_BEATS)
            .chain(GRID_BEATS)
            .chain(PARTS_BEATS)
            .chain(ORDER_BEATS)
            .chain(ROWHITS_BEATS)
            .chain(MATSWHY_BEATS)
            .chain(NUMBERS_BEATS)
            .chain(REPAIR_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISKS_BEATS);
        for b in all {
            assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}", b.caption);
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_array_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_array_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else {
            return;
        };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for (name, scene) in scenes() {
            let beats = scene.beats().len();
            let p = Player::new(scene, Instant::now());
            for beat in 0..beats {
                let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                let img = p.pixels(&at(beat, 0.6), w, h).expect("pixel frame");
                img.save(dir.join(format!("{name}_{beat}.png"))).unwrap();
            }
        }
    }
}
