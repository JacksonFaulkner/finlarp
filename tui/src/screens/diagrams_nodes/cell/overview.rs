// CELL overview: one 1T1C DRAM cell cut open at its centre plane, played back from the Blender
// scene (tools/pbr3d/blender/cell_overview.py, built on cell_kit.py) in the picture-and-panel
// template. Seven beats walk one bit through idle, word line, charge sharing, sense and restore,
// precharge, leakage and refresh. Zoom-ins a-f open the capacitor, a read, the rows, the shrink,
// the bit-line layouts and the access transistor (tools/pbr3d/blender/cell_zooms.py).
//
// Sources: UMD ENEE 359a, DRAM Systems (Jacob), slide 3, and DRAM Circuits (Jacob), slides 4, 5, 9,
// 11-14; Mutlu, arXiv 2306.16037, p. 1; HiRA, arXiv 2209.10198, pp. 1-2; PROTEAS, arXiv 2404.16256,
// Table I.

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("idle: a full capacitor holds the bit; the word line is low", BEAT_MS)
        .note(
            "One bit sits on the storage capacitor as charge. The access transistor is off, so the cell is cut off from the bit line. Between accesses the bit line rests at VDD/2.",
            "the orange charge filling the capacitor, the pink word line dim, the cyan bit line level with the gauge's VDD/2 ring, and the green precharge block lit",
        )
        .detail(
            "A 1T1C cell is one transistor and one capacitor. Full charge reads as 1 and empty reads as 0.",
            &[
                "1T1C: one transistor and one storage capacitor (Jacob, DRAM Systems, slide 3)",
                "Full charge reads as 1, empty as 0 (page text)",
            ],
        ),
    Beat::new("word line rises: the access transistor switches on", BEAT_MS)
        .note(
            "The row decoder drives the word line high. Its gate turns on the access transistor, which joins the storage node to the bit line. Every cell in the row connects at once.",
            "the pink word line lit, the channel glowing under the gate, and the bit-line precharge block still green",
        )
        .detail(
            "The word line is a row select: high turns on every access transistor in its row.",
            &[
                "Word line: high turns on every access transistor in its row (Jacob, DRAM Systems, slide 3; DRAM Circuits, slide 5)",
                "A typical array is 512 wordlines by 512 bitlines (Jacob, DRAM Circuits, slide 5)",
            ],
        ),
    Beat::new("charge sharing: charge moves onto the bit line, a small bump up", BEAT_MS)
        .note(
            "The cell and the bit line share charge. The bit line holds far more capacitance than the cell, so it moves only a little, up for a 1.",
            "a few cyan dots running from the storage node, over the source and channel, up the drain plug to the bit line, the charge level dropping as each leaves; when they land the gauge bumps just above the VDD/2 ring, and a gold bracket marks that small dV while a gold tick below the ring shows where a 0 would dip",
        )
        .detail(
            "The move is small because the bit line capacitance is much bigger than the cell's. The sense amp must amplify it.",
            &[
                "Final bit-line voltage (Cb VBL + Cc Vcell) / (Cb + Cc) (Jacob, DRAM Circuits, slides 4 and 11)",
                "Swing dV = (Vcell - VDD/2) Cc / (Cc + Cb) (same slides; derived from charge conservation)",
            ],
        ),
    Beat::new("sense amp latches the bit line to a full rail and restores the cell", BEAT_MS)
        .note(
            "The sense amp detects the small move and drives the bit line to full VDD, or to GND for a 0. The transistor is still open, so the same drive writes the cell back to full charge.",
            "the purple sense amp block lit, the gauge climbing to the top, and violet dots running back into the capacitor until it fills again",
        )
        .detail(
            "This latch does two jobs: it reads the bit and it restores the charge the read drained from the cell.",
            &[
                "The sense amp latches the bit line to full VDD or GND (Jacob, DRAM Circuits, slides 12-14)",
                "Restore: the read drains the cell and the sense amp writes it back (HiRA, arXiv 2209.10198, p. 2)",
            ],
        ),
    Beat::new("precharge: the word line falls and the bit line returns to VDD/2", BEAT_MS)
        .note(
            "The word line drops and cuts the cell off, so it keeps its restored charge. The precharge block then holds the bit line at VDD/2, ready for the next read.",
            "the pink word line dimming, the gauge sliding back to the VDD/2 ring, the green precharge block lit, and the capacitor full",
        )
        .detail(
            "Precharge to VDD/2 is what lets the next read see a small swing either way.",
            &[
                "Precharge holds the bit line at VDD/2 before a read (Jacob, DRAM Circuits, slides 4 and 11)",
                "The cell keeps its restored charge after the word line falls (page text)",
            ],
        ),
    Beat::new("leakage: charge drains from the capacitor while the row sits idle", BEAT_MS)
        .note(
            "With the transistor off, charge leaks out of the storage node through several small paths. The capacitor slowly loses charge, and the loss does not stop.",
            "orange dots leaving the capacitor's side one by one, the charge sinking toward the red mark (the level below which a read fails), and the gold clock beside it filling toward the refresh window",
        )
        .detail(
            "Leakage is why the cell fades. The window for a fully charged cell is set by the weakest cells on the chip.",
            &[
                "Retention varies cell to cell; the minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)",
                "Three leak paths: capacitor dielectric, storage-node junction, off transistor (general knowledge; the split is not sourced here)",
            ],
        ),
    Beat::new("refresh: the row is read and rewritten before the charge is gone", BEAT_MS)
        .note(
            "The controller reads the row and writes it back at full charge, on a timer. The capacitor is topped up before it fades too far.",
            "cyan dots reading the cell up to the bit line, the purple sense amp lighting to latch it, violet dots rewriting the cell, the capacitor refilling above the red mark, and the gold clock dropping back to empty",
        )
        .detail(
            "Refresh is a read followed by a rewrite. It must finish within the refresh window, so every row gets a turn.",
            &[
                "DDR4: tREFW = 64 ms, tREFI = 7800 ns, 8192 REF commands per window (PROTEAS, arXiv 2404.16256, Table I)",
                "Refresh blocks access to the bank while it runs (HiRA, arXiv 2209.10198, p. 1)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the storage capacitor: charge in, leak out",
        build: || -> Box<dyn Scene> { zoom::cap() },
    },
    Zoom {
        key: 'b',
        label: "open vs folded bit lines: the layout",
        build: || -> Box<dyn Scene> { zoom::layout() },
    },
    Zoom {
        key: 'c',
        label: "refresh across the rows",
        build: || -> Box<dyn Scene> { zoom::rows() },
    },
    Zoom {
        key: 'd',
        label: "shrinking the cell",
        build: || -> Box<dyn Scene> { zoom::shrink() },
    },
    Zoom {
        key: 'e',
        label: "a read: charge sharing and restore",
        build: || -> Box<dyn Scene> { zoom::read() },
    },
    Zoom {
        key: 'f',
        label: "the transistor: gate, source, drain",
        build: || -> Box<dyn Scene> { zoom::transistor() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/cell_overview.glb"),
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
        super::super::super::blender::explained(s.as_ref(), "CELL overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcdef");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "CELL overview");
    }
}
