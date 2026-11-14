// ARRAY overview: a 10 x 10 subarray of 1T1C cells, drawn in 3D and played back from the Blender
// scene (tools/pbr3d/blender/array_overview.py) in the picture-and-panel template. One access
// walks through it: the row decoder picks a row, ACTIVATE opens it, the sense amps latch it, READs
// send columns to the I/O, a second READ hits the open row, PRECHARGE closes it, and refresh walks
// the rows. Zoom-ins a-e open the row buffer, the three access cases, the mats, the redundancy and
// the burst (tools/pbr3d/blender/array_zooms.py).
//
// Sources: section 10 of MEM_ARRAY.txt (UMD ENEE 359a; Kim et al., arXiv 1805.01966; AnandTech;
// geizhals DDR4 listing; US 6,731,550 and US 5,325,334; Kim et al., ISCA 2014).

use super::super::blender::{Cell, Page, BEAT_MS};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("an address reaches the row decoder, which picks one row", BEAT_MS)
        .note(
            "The memory controller sends a row address. The row decoder turns it into one word line high out of all the rows; the others stay low.",
            "white dots running in from the left into the row decoder; every bit line sits at the middle level, precharged",
        )
        .detail(
            "The array is a grid: cells on word lines, columns of cells on bit lines. Every access starts by choosing a row.",
            &[
                "512 word lines x 512 bit lines = 262,144 cells (UMD ENEE 359a, DRAM circuits)",
                "Every bit line is precharged to VDD/2 before an access (page section 3)",
            ],
        ),
    Beat::new("ACTIVATE: one word line rises and the whole row shares its charge", BEAT_MS)
        .note(
            "The decoder drives one word line high. Every cell in that row connects to its bit line and nudges it up for a 1 or down for a 0.",
            "one word line glowing orange across the row, the cells of that row lit pale blue, and small dots running up each bit line",
        )
        .detail(
            "A row opens all at once: there is no way to read one cell alone.",
            &[
                "tRCD = 13.75 ns before a column can be read (DDR4-3200 22-22-22, AnandTech)",
                "Swing on a bit line is Cc / (Cc + Cb) (UMD ENEE 359a)",
            ],
        ),
    Beat::new("sense: the sense amps latch the row, which is the row buffer", BEAT_MS)
        .note(
            "Each bit line has a sense amp. It amplifies the small nudge to a full 1 or 0 and holds it. Together the sense amps are the row buffer, and they rewrite the cells.",
            "the sense amp row at the bottom filling with orange latches for the 1s and dark ones for the 0s; the bit lines turn bright cyan",
        )
        .detail(
            "Reads come from the latches, not from the cells.",
            &[
                "Row buffer: 1 KB per x8 DDR4 chip (page section 6)",
                "Sense amps latch each bit line and restore the cell (Kim et al., arXiv 1805.01966)",
            ],
        ),
    Beat::new("READ: the column decoder sends a burst of bits to the I/O", BEAT_MS)
        .note(
            "READ carries a column address. The column decoder connects a few latches of the row buffer to the data lines, and the bits leave the chip as a burst.",
            "four green marks lit on the column decoder bar and green dots running from them to the I/O pad at the right",
        )
        .detail(
            "Data comes from the row buffer, not from the cells.",
            &[
                "tCL = 13.75 ns from READ to data (DDR4-3200 22-22-22, AnandTech)",
                "Burst length 8 on DDR4: 64 bits per READ on a x8 chip (page section 6)",
            ],
        ),
    Beat::new("row hit: another READ to the open row skips the activate", BEAT_MS)
        .note(
            "The row is still open, so a second READ to other columns is served straight from the row buffer, with no ACTIVATE.",
            "four other green marks lit on the column decoder bar and the dots running to the I/O pad again",
        )
        .detail(
            "A row hit costs tCL alone; a conflict costs tRP + tRCD + tCL, three times as long at DDR4-3200.",
            &[
                "Hit 13.75 ns; conflict 41.25 ns (DDR4-3200 22-22-22, AnandTech)",
                "Controllers group requests to the same row (page section 4)",
            ],
        ),
    Beat::new("precharge: the word line falls and the bit lines return to VDD/2", BEAT_MS)
        .note(
            "PRECHARGE closes the row. The word line drops, the sense amps let go and the bit lines return to the middle level before another row can open.",
            "the orange word line fading, the bright latches and bit lines going dark, and the sense amp row turning back to purple",
        )
        .detail(
            "The next row in this bank cannot open until precharge is done.",
            &[
                "tRP = 13.75 ns (DDR4-3200 22-22-22, AnandTech)",
                "tRAS = 32.5 ns from ACTIVATE to PRECHARGE (DDR4-3200 JEDEC listing, geizhals)",
            ],
        ),
    Beat::new("refresh: every row is opened and closed in turn", BEAT_MS)
        .note(
            "The cells leak, so every row is refreshed on a timer: each one is opened, sensed, rewritten and closed in turn.",
            "the bright word line stepping down the array one row at a time, from the bottom row to the top",
        )
        .detail(
            "Refresh opens every row on a timer and blocks the bank while it runs (see the CELL node).",
            &[
                "One refresh pass opens and closes each row: tRAS 32.5 ns plus tRP 13.75 ns per row (AnandTech, geizhals; sum computed)",
                "Refresh blocks the bank while it runs (page section 9)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the row buffer: a whole row in the sense amps",
        build: || -> Box<dyn Scene> { zoom::rowbuf() },
    },
    Zoom {
        key: 'b',
        label: "row hit, row miss, row conflict",
        build: || -> Box<dyn Scene> { zoom::hits() },
    },
    Zoom {
        key: 'c',
        label: "mats, subarrays and the bank",
        build: || -> Box<dyn Scene> { zoom::mats() },
    },
    Zoom {
        key: 'd',
        label: "redundancy: a spare row takes over",
        build: || -> Box<dyn Scene> { zoom::redund() },
    },
    Zoom {
        key: 'e',
        label: "a burst: eight transfers from the open row",
        build: || -> Box<dyn Scene> { zoom::burst() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/array_overview.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "ARRAY overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "ARRAY overview");
    }
}
