// ARRAY zoom-ins a-e in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/array_zooms.py: a the row buffer, b row hit / miss / conflict, c mats,
// subarrays and the bank, d redundancy, e a burst. Four beats each.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

pub const ROWBUF_BEATS: &[Beat] = &[
    Beat::new("ACTIVATE raises one word line; each cell nudges its bit line", BEAT_MS)
        .note(
            "ACTIVATE drives one word line high. Every cell in that row shares its charge with its bit line, so each bit line moves a little up for a 1 or down for a 0.",
            "one orange word line across the array, pale blue cells in that row, and small dots running up each bit line to the sense amps",
        )
        .detail(
            "The whole row opens at once: no single cell can be read on its own.",
            &[
                "Swing on a bit line is Cc / (Cc + Cb) (UMD ENEE 359a, DRAM circuits)",
                "tRCD = 13.75 ns before a column can be read (DDR4-3200, AnandTech)",
            ],
        ),
    Beat::new("sense amps latch each bit: the open row is now in the row buffer", BEAT_MS)
        .note(
            "Each bit line has a sense amp. It amplifies the small nudge to a full 1 or 0, latches it and drives it back into the cell to restore it. Together the latches are the row buffer.",
            "the sense amp row at the bottom fills with orange latches for the 1s and dark ones for the 0s, and the bit lines turn bright cyan",
        )
        .detail(
            "Reads come from the latches, not from the cells, so the cells can be rewritten while the row stays open.",
            &[
                "Row buffer holds 1 KB on an x8 DDR4 chip (page text; Micron datasheet, not yet linked)",
                "Sense amps restore the cells they read (Kim et al., arXiv 1805.01966)",
            ],
        ),
    Beat::new("READ: latches feed the I/O while the row stays open", BEAT_MS)
        .note(
            "The column decoder picks a few latches and connects them to the data lines. Their bits leave the chip, and the cells are not touched again.",
            "four green marks lit on the column decoder bar and green dots running from them to the I/O pad at the right",
        )
        .detail(
            "Data arrives tCL after READ; the row itself stays open for more READs.",
            &[
                "tCL = 13.75 ns from READ to data (DDR4-3200 22-22-22, AnandTech)",
                "64 bits per READ on a x8 chip (page section 6)",
            ],
        ),
    Beat::new("precharge empties the row buffer for the next row", BEAT_MS)
        .note(
            "PRECHARGE drops the word line, the sense amps let go and the bit lines return to VDD/2. Only then can another row open.",
            "the word line fades and the bright latches and bit lines go dark, the sense amp row turning back to purple",
        )
        .detail(
            "Closing the row is what makes a later access to another row a conflict.",
            &[
                "tRP = 13.75 ns (DDR4-3200 22-22-22, AnandTech)",
                "tRAS = 32.5 ns from ACTIVATE to PRECHARGE (DDR4-3200 JEDEC listing, geizhals)",
            ],
        ),
];

pub const HITS_BEATS: &[Beat] = &[
    Beat::new("row hit: the row is already open, 13.75 ns", BEAT_MS)
        .note(
            "The requested row is already in the row buffer, so the READ only waits for tCL.",
            "a single green bar, 13.75 ns long, on the first lane",
        )
        .detail(
            "Controllers try to group requests to the same row for this reason.",
            &["tCL = 13.75 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("row miss: the bank is closed, 27.5 ns", BEAT_MS)
        .note(
            "No row is open. The row has to be activated (tRCD) before the read (tCL).",
            "an orange ACT bar followed by a green READ bar on the second lane",
        )
        .detail(
            "A miss costs twice a hit.",
            &["tRCD + tCL = 27.5 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("row conflict: another row is open, 41.25 ns", BEAT_MS)
        .note(
            "The wrong row is open. It must be closed (tRP), the right one opened (tRCD), then read (tCL).",
            "a pink PRE bar, an orange ACT bar and a green READ bar in a row on the third lane",
        )
        .detail(
            "Three times a hit, which is why access order matters.",
            &["tRP + tRCD + tCL = 41.25 ns (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("the three cases to scale: a conflict is three times a hit", BEAT_MS)
        .note(
            "All three lanes are shown together on one time scale, so the hit, the miss and the conflict can be compared directly.",
            "the three lanes stacked: a short green bar, a longer orange-and-green one, and the longest pink-orange-green one",
        )
        .detail(
            "Only the order of commands changes between the three; the wires and the cells are the same.",
            &[
                "Hit 13.75 ns, miss 27.5 ns, conflict 41.25 ns (DDR4-3200 22-22-22)",
                "Conflict costs three times a hit (page section 4)",
            ],
        ),
];

pub const MATS_BEATS: &[Beat] = &[
    Beat::new("one mat: a small grid with its own drivers and sense amps", BEAT_MS)
        .note(
            "The array is built from small tiles called mats. Each has local word line drivers on one side and sense amp stripes on two.",
            "one grid of cells with a grey driver strip on the left and purple sense amps along the bottom",
        )
        .detail(
            "Keeping mats small keeps the word lines and bit lines short.",
            &["Typical array: 512 x 512 cells (UMD ENEE 359a, DRAM circuits)"],
        ),
    Beat::new("a subarray: mats in a row under one global word line", BEAT_MS)
        .note(
            "Mats line up into a subarray. A global word line runs over them and wakes the local drivers of the row being opened.",
            "three mats side by side with one bright orange global word line running across all of them",
        )
        .detail(
            "A subarray has its own row of sense amps: a local row buffer.",
            &["Subarrays with local row buffers (Kim et al., arXiv 1805.01966)"],
        ),
    Beat::new("a bank: subarrays share global bit lines and the I/O", BEAT_MS)
        .note(
            "Many subarrays make a bank. They share global bit lines and the bank's I/O, so in a standard bank only one subarray's row is open at a time.",
            "three subarrays in a row with a long cyan global bit line running beneath them",
        )
        .detail(
            "Research designs (SALP) let several subarrays work at once for under 0.15% area.",
            &["SALP: under 0.15% area overhead (Kim et al., arXiv 1805.01966)"],
        ),
    Beat::new("one subarray's row is open; the others stay closed", BEAT_MS)
        .note(
            "The row of the first subarray is open, its cells lit and its sense amps holding the row. The other subarrays hold no open row in this picture.",
            "the first subarray's row of cells glowing and its sense amp stripe lit, with the global word line over it",
        )
        .detail(
            "Opening a second row in the same standard bank means closing the first, which is a conflict.",
            &["Only one subarray's row is open at a time in a standard bank (page section 5)"],
        ),
];

pub const REDUNDANCY_BEATS: &[Beat] = &[
    Beat::new("wafer test finds a bad cell", BEAT_MS)
        .note(
            "At wafer test the array is written and read. One cell fails; a yellow probe walks down the rows and the bad cell turns red.",
            "a yellow probe bar moving down the rows and a single red cell in the array",
        )
        .detail(
            "Wafer test finds the defects; the repair is decided after it.",
            &["Defects are found at wafer test (page section 7)"],
        ),
    Beat::new("a laser blows a fuse to store the bad address", BEAT_MS)
        .note(
            "The bad address is written into a fuse bank. A laser cuts a fuse, or an electrical fuse is blown, so the address is stored on the die.",
            "a red laser beam hitting the fuse bank at the top right and one fuse going dark",
        )
        .detail(
            "The fuses are the die's repair map.",
            &["Laser or electrical fuses, decoders that route to spares (US 6,731,550; US 5,325,334)"],
        ),
    Beat::new("the decoder sends that address to a spare row", BEAT_MS)
        .note(
            "From now on the bad row's address opens a spare row at the edge of the array instead. Outside the chip nothing changes.",
            "green dots running from the decoder up past the bad row to the spare row at the top, which lights green",
        )
        .detail(
            "Spare rows and columns replace the bad ones; each spare is area that holds no data.",
            &["Spares sit at the edge of the array (page section 7)"],
        ),
    Beat::new("the bad row is no longer used; spares sit at the array's edge", BEAT_MS)
        .note(
            "The bad cell's row is no longer addressed, and the spare row takes its place. Redundancy turns dies that would be scrap into good ones.",
            "the spare row lit green at the top edge and the red cell left in the array, no longer driven by the decoder",
        )
        .detail(
            "The number of spares is a yield-versus-area trade.",
            &["Redundancy trades area that holds no data for yield (page section 7)"],
        ),
];

pub const BURST_BEATS: &[Beat] = &[
    Beat::new("a column address picks 64 bits of the open row", BEAT_MS)
        .note(
            "The column address of a READ selects a group of latches in the row buffer: 64 bits on a x8 chip.",
            "eight of the sixteen latches lit green on the column decoder bar, with green dots running to the I/O",
        )
        .detail(
            "Only a small part of the open row leaves per READ.",
            &["64 bits per READ on a x8 chip (page section 6)"],
        ),
    Beat::new("they leave as eight transfers on eight pins", BEAT_MS)
        .note(
            "The 64 bits go out as a burst of eight transfers, one on each of the eight data pins.",
            "eight pins at the right of the I/O, each sending one green dot down its length in turn",
        )
        .detail(
            "Burst length 8 on DDR4 means 8 transfers on each data pin.",
            &["8 data pins x burst length 8 = 64 bits (Micron DDR4 datasheet, not yet linked)"],
        ),
    Beat::new("the next READ to the open row: another 64, no activate", BEAT_MS)
        .note(
            "Another group of columns in the same open row is read with no ACTIVATE. The other eight latches light and the pins run again.",
            "the other eight latches lit green and the green dots running to the pins a second time",
        )
        .detail(
            "Streaming through an open row is the fastest way to read DRAM.",
            &["Row hit: tCL only (DDR4-3200 22-22-22, AnandTech)"],
        ),
    Beat::new("one ACTIVATE serves many READs from the open row", BEAT_MS)
        .note(
            "The whole row is open in the sense amps, so each READ only chooses which columns to send out. Many READs share one ACTIVATE.",
            "all sixteen latches lit and the column decoder bar green where the READs pick columns",
        )
        .detail(
            "Each READ moves a 64-bit chunk; the ACTIVATE is paid once for the row.",
            &["tRCD = 13.75 ns is paid once per row opened (DDR4-3200, AnandTech)"],
        ),
];

static ROWBUF: Cell = std::sync::OnceLock::new();
static HITS: Cell = std::sync::OnceLock::new();
static MATS: Cell = std::sync::OnceLock::new();
static REDUND: Cell = std::sync::OnceLock::new();
static BURST: Cell = std::sync::OnceLock::new();

pub fn rowbuf() -> Box<dyn Scene> {
    page(
        &ROWBUF,
        include_bytes!("../../../../../tools/pbr3d/assets/array_rowbuf.glb"),
        ROWBUF_BEATS,
    )
}

pub fn hits() -> Box<dyn Scene> {
    page(
        &HITS,
        include_bytes!("../../../../../tools/pbr3d/assets/array_hits.glb"),
        HITS_BEATS,
    )
}

pub fn mats() -> Box<dyn Scene> {
    page(
        &MATS,
        include_bytes!("../../../../../tools/pbr3d/assets/array_mats.glb"),
        MATS_BEATS,
    )
}

pub fn redund() -> Box<dyn Scene> {
    page(
        &REDUND,
        include_bytes!("../../../../../tools/pbr3d/assets/array_redund.glb"),
        REDUNDANCY_BEATS,
    )
}

pub fn burst() -> Box<dyn Scene> {
    page(
        &BURST,
        include_bytes!("../../../../../tools/pbr3d/assets/array_burst.glb"),
        BURST_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("rowbuf", rowbuf as fn() -> Box<dyn Scene>),
            ("hits", hits),
            ("mats", mats),
            ("redund", redund),
            ("burst", burst),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
