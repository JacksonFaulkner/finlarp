// CELL zoom-ins a-f in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/cell_zooms.py: a the storage capacitor, b open vs folded bit lines, c refresh
// across the rows, d shrinking the cell, e a read (kept in code, moved off b), f the access
// transistor. Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const CAP_BEATS: &[Beat] = &[
    Beat::new("full charge: the capacitor holds the bit as a 1", BEAT_MS)
        .note(
            "The storage capacitor holds the bit as charge on its plate. Full charge reads as 1, and this capacitor is the only place the data lives.",
            "the orange charge filling the inner plate, the grey outer plate and the pale dielectric round it, and the grey storage node below",
        )
        .detail(
            "Everything else in the cell exists to read this charge or to keep it full.",
            &[
                "Storage capacitor holds the bit as charge on its plate (Jacob, DRAM Systems, slide 3)",
                "Full charge reads as 1, empty as 0 (page text)",
            ],
        ),
    Beat::new("charge leaks from the plate while the row sits idle", BEAT_MS)
        .note(
            "Charge leaves the storage node through the capacitor dielectric, the storage-node junction and the off access transistor. The loss is slow, but it does not stop.",
            "orange dots leaving the lower plate, running off to the side and into the silicon, and the charge level dropping",
        )
        .detail(
            "Leakage sets the refresh window. Cells differ in how fast they leak, and the window must cover the weakest cell on the chip.",
            &[
                "Retention varies cell to cell (Mutlu, arXiv 2306.16037, p. 1)",
                "The split between the three leak paths is not sourced here (general knowledge)",
            ],
        ),
    Beat::new("the charge drains away", BEAT_MS)
        .note(
            "After a while the capacitor holds less charge. A lower charge gives a smaller swing on the bit line, so the sense amp has less to work with.",
            "the orange fill lower in the inner plate, with a few dots still leaving the side",
        )
        .detail(
            "The minimum retention time of the weakest cells sets how long a charge can wait before it must be refreshed.",
            &[
                "The minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)",
                "A smaller storage capacitor gives a smaller swing (Jacob, DRAM Circuits, slides 4 and 11)",
            ],
        ),
    Beat::new("refresh tops the charge back up to full", BEAT_MS)
        .note(
            "A refresh reads the cell and writes it back at full charge, drawing from the bit line. The inner plate fills again.",
            "cyan dots coming down from the bit line into the storage node, and the orange charge relighting to full height",
        )
        .detail(
            "Refresh is the rewrite that keeps the bit above the level the sense amp can read.",
            &[
                "Refresh rewrites every row within the window (PROTEAS, arXiv 2404.16256, Table I)",
                "The restore step is the same write-back a read uses (HiRA, arXiv 2209.10198, p. 2)",
            ],
        ),
];

const READ_BEATS: &[Beat] = &[
    Beat::new("charge sharing: the cell and the bit line exchange charge", BEAT_MS)
        .note(
            "The access transistor opens and the cell shares its charge with the bit line. The bit line is much bigger than the cell, so the cell's level falls a lot and the line moves only a little.",
            "cyan dots crossing from the storage node to the bit line, the cell's charge dimming, and the gauge bumping just above the VDD/2 ring",
        )
        .detail(
            "The move is small because the bit line capacitance is far larger than the cell's. The sense amp has to amplify it.",
            &[
                "Final voltage (Cb VBL + Cc Vcell) / (Cb + Cc) (Jacob, DRAM Circuits, slides 4 and 11)",
                "Swing dV = (Vcell - VDD/2) Cc / (Cc + Cb) (same slides; derived from charge conservation)",
            ],
        ),
    Beat::new("sense amp restores the cell", BEAT_MS)
        .note(
            "The sense amp latches the small bump to a full rail. The transistor is still open, so the same drive writes the cell back to full charge.",
            "the purple sense amp lit, the gauge climbing to the top, and violet dots running back into the capacitor",
        )
        .detail(
            "Without restore, the read would destroy the bit. The latch does both jobs at once.",
            &[
                "The sense amp latches the bit line to full VDD or GND (Jacob, DRAM Circuits, slides 12-14)",
                "Restore is part of every read (HiRA, arXiv 2209.10198, p. 2)",
            ],
        ),
    Beat::new("precharge: the word line falls and the bit line returns to VDD/2", BEAT_MS)
        .note(
            "The transistor closes first, so the cell keeps its restored charge. The bit line is then brought back to the middle, ready for the next read.",
            "the pink word line dropping, the green precharge block lit, the gauge sliding back to the VDD/2 ring, and the capacitor full",
        )
        .detail(
            "Precharge to the midpoint means the next read starts from the same place, so a 1 and a 0 move the line in opposite directions.",
            &[
                "Precharge to VDD/2 before a read (Jacob, DRAM Circuits, slides 4 and 11)",
                "The bit line moves up for a 1 and down for a 0 (page text)",
            ],
        ),
    Beat::new("a 0 pulls the line down", BEAT_MS)
        .note(
            "An empty cell shares its charge the other way: the bit line dips below VDD/2, and the sense amp latches it down to ground.",
            "the capacitor empty and dark, the gauge dipping below the ring and then falling to the bottom, and the purple sense amp lit",
        )
        .detail(
            "Reads go both ways. A 1 pushes the line up and a 0 pulls it down; the sense amp turns either move into a full 1 or 0.",
            &[
                "The bit line moves up for a 1, down for a 0 (page text)",
                "The latch drives the bit line to a full VDD or full GND (page text)",
            ],
        ),
];

const ROWS_BEATS: &[Beat] = &[
    Beat::new("the refresh pointer walks down the rows", BEAT_MS)
        .note(
            "Each bar is a row, and its height is the charge. Rows sag until a refresh reaches them. The pointer walks the array one row at a time.",
            "the white pointer bar moving along the rows; rows ahead of it are slightly low, and rows behind it stand at full height",
        )
        .detail(
            "Every row gets a turn inside the window, so no row is left to sag for long.",
            &[
                "tREFW = 64 ms (DDR4, Micron datasheet value; PROTEAS, arXiv 2404.16256, Table I)",
                "tREFI = 7800 ns, 8192 REF commands per window (PROTEAS, arXiv 2404.16256, Table I)",
            ],
        ),
    Beat::new("each row is read, then rewritten at full charge", BEAT_MS)
        .note(
            "The row under the pointer is read and then rewritten at full charge. The pointer then moves to the next row.",
            "the row under the pointer rising to full height as it passes, and the rows either side unchanged",
        )
        .detail(
            "Refresh is a read followed by a write-back, done for every row on a timer.",
            &[
                "Refresh is a read followed by a rewrite (page text)",
                "Refresh blocks access to the bank while it runs (HiRA, arXiv 2209.10198, p. 1)",
            ],
        ),
    Beat::new("every row is rewritten within the refresh window", BEAT_MS)
        .note(
            "The window is 64 ms in DDR4. Every row must get its turn before the window closes.",
            "the pointer at the far end of the rows, and every row now at full height",
        )
        .detail(
            "8192 commands at 7800 ns each come to about 64 ms, so the numbers fit together.",
            &[
                "tREFW = 64 ms (DDR4; PROTEAS, arXiv 2404.16256, Table I)",
                "8192 x 7800 ns = 63.9 ms (computed)",
            ],
        ),
    Beat::new("the cycle starts again", BEAT_MS)
        .note(
            "Once the window closes the cells begin to sag again, and the pointer returns to the first row. The controller keeps refreshing while the chip is powered.",
            "all rows full, the pointer back at the first row, and the rows beginning to sag as the next window starts",
        )
        .detail(
            "The loop never stops: leakage does not wait for a quiet moment.",
            &[
                "The controller issues 8192 refresh commands in each window (page text, section 4)",
                "Refresh runs on a clock (page text, section 4)",
            ],
        ),
];

const SHRINK_BEATS: &[Beat] = &[
    Beat::new("a wide cell: a big capacitor holds plenty of charge", BEAT_MS)
        .note(
            "At a larger feature size the capacitor is a wide, tall plate pair, with room for plenty of charge.",
            "the wide grey outer plate, the orange charge filling the inner plate, and the storage node below",
        )
        .detail(
            "Cell area is set by F, the minimum feature size, so a bigger cell has more room for capacitance.",
            &[
                "Cell area 6F^2 with an open bit line (Jacob, DRAM Circuits, slide 9)",
                "The cell area is set by F (page text, section 7)",
            ],
        ),
    Beat::new("smaller F: the capacitor narrows, and the swing drops", BEAT_MS)
        .note(
            "A smaller F means a narrower capacitor, so a smaller Cc. Cb has not changed, so the swing drops and the sense amp has less to work with.",
            "the plates narrowing inside the old outline, and the orange fill getting smaller",
        )
        .detail(
            "Less signal is what shrinking the cell costs.",
            &[
                "Swing = (Vcell - VDD/2) Cc / (Cc + Cb) (Jacob, DRAM Circuits, slides 4 and 11)",
                "A smaller storage capacitor gives a smaller swing (page text, section 7)",
            ],
        ),
    Beat::new("taller plates keep Cc up", BEAT_MS)
        .note(
            "Designs keep the capacitance up by making the capacitor taller, or by using a better dielectric. The footprint stays small, and the capacitance returns.",
            "the orange cell growing upward, the plates stretching, and the footprint at the base staying narrow",
        )
        .detail(
            "The footprint keeps shrinking while the height does the work.",
            &[
                "Designs keep Cc up with a taller capacitor or a better dielectric (page text, section 7)",
                "The swing depends on Cc against Cb (page text, section 7)",
            ],
        ),
    Beat::new("same charge, smaller footprint", BEAT_MS)
        .note(
            "The cell now takes less area and still holds enough charge for a readable swing.",
            "the narrow tall capacitor with its fill at full height and a small footprint on the storage node",
        )
        .detail(
            "Area falls with F squared while the height keeps the capacitance up.",
            &[
                "Cell area in F squared (Jacob, DRAM Circuits, slide 9)",
                "The swing is set by Cc against Cb (page text, section 7)",
            ],
        ),
];

const LAYOUT_BEATS: &[Beat] = &[
    Beat::new("open bit lines: the reference line sits in the other array", BEAT_MS)
        .note(
            "A sense amp compares two lines. In an open layout the signal and the reference bit lines sit in different arrays, with the sense amp between them.",
            "two arrays with one sense amp between them; the cyan line carries the cell's signal and the orange line the reference",
        )
        .detail(
            "The open layout takes 6F^2 per cell, the smaller of the two areas.",
            &[
                "Open bit line: 6F^2 cell (Jacob, DRAM Circuits, slide 9)",
                "The sense amp compares the pair (page text, section 6)",
            ],
        ),
    Beat::new("folded bit lines: the pair sits side by side in one array", BEAT_MS)
        .note(
            "In a folded layout both bit lines of a pair run side by side in one array, so noise couples onto both lines.",
            "the orange line sliding over and settling beside the cyan line in the same array",
        )
        .detail(
            "The folded layout takes 8F^2 per cell, a third more area than open.",
            &[
                "Folded bit line: 8F^2 cell (Jacob, DRAM Circuits, slide 9)",
                "The folded pair is the price of its better noise behaviour (textbook)",
            ],
        ),
    Beat::new("noise: the same bump lands on both folded lines", BEAT_MS)
        .note(
            "Noise that couples onto both lines looks the same on each, so the sense amp sees only the difference between them.",
            "a pink band crossing the array and bumping both lines up together",
        )
        .detail(
            "Noise common to both lines cancels in their difference, which is what the sense amp reads.",
            &[
                "Common-mode noise cancels in the difference of a folded pair (textbook)",
                "Folded layout: 8F^2 per cell (page text, section 6)",
            ],
        ),
    Beat::new("the difference stays flat, so the read is right", BEAT_MS)
        .note(
            "The difference between the two lines stays flat on the floor while both lines move together, so the sense amp still reads the right bit.",
            "the gold difference trace lying flat on the floor, with both lines lifted above it",
        )
        .detail(
            "Folding costs a third more area per cell for this noise immunity.",
            &[
                "Folded 8F^2 against open 6F^2 (page text, section 6)",
                "Noise on both lines cancels in the difference (textbook)",
            ],
        ),
];

const TRANSISTOR_BEATS: &[Beat] = &[
    Beat::new("three connections: gate, source, drain", BEAT_MS)
        .note(
            "A transistor has three connections. The gate is the word line on top. The source is the end on the storage-node side and the drain is the end on the bit-line side. Current flows between source and drain only when the gate is driven.",
            "the pink gate on top, the blue drain on the bit-line side, the blue source on the storage-node side, all on the grey silicon",
        )
        .detail(
            "The gate controls the channel; the drain and source are the two ends of the channel.",
            &[
                "The gate controls the channel; the drain and source are the two ends of the channel (textbook)",
                "Access transistor on the word line (page text, section 2)",
            ],
        ),
    Beat::new("read: the gate opens the channel, charge leaves the cell", BEAT_MS)
        .note(
            "The word line goes high and the channel under the gate opens. Charge leaves the storage node through the open channel toward the bit line.",
            "the pink gate lit, the cyan channel glowing, cyan dots moving from source to drain",
        )
        .detail(
            "A high gate forms a conducting channel between source and drain, so charge can pass through it.",
            &[
                "Gate high forms a channel that conducts source to drain (textbook)",
                "Word line high turns on every access transistor in its row (Jacob, DRAM Systems, slide 3)",
            ],
        ),
    Beat::new("gate low: the channel closes, the cell is cut off", BEAT_MS)
        .note(
            "With the word line low the channel closes, so the storage node is cut off from the bit line and holds its charge.",
            "the gate dim, the channel dark, no dots moving",
        )
        .detail(
            "With no gate drive the channel is gone, so the transistor acts as an open switch.",
            &[
                "Gate low: no channel, the transistor is off (textbook)",
                "The cell keeps its restored charge after the word line falls (page text)",
            ],
        ),
    Beat::new("write: the bit line drives charge back through the channel", BEAT_MS)
        .note(
            "The word line goes high again and the bit line drives its level into the cell through the open channel, from drain to source.",
            "the pink gate lit, the channel glowing, violet dots moving from drain to source",
        )
        .detail(
            "The same channel carries charge in either direction once the gate opens it.",
            &[
                "Current flows between source and drain when the gate is driven (textbook)",
                "The restore step is the same write-back a read uses (HiRA, arXiv 2209.10198, p. 2)",
            ],
        ),
];

static CAP: Cell = std::sync::OnceLock::new();
static READ: Cell = std::sync::OnceLock::new();
static ROWS: Cell = std::sync::OnceLock::new();
static SHRINK: Cell = std::sync::OnceLock::new();
static LAYOUT: Cell = std::sync::OnceLock::new();
static TRANSISTOR: Cell = std::sync::OnceLock::new();

pub fn cap() -> Box<dyn Scene> {
    page(
        &CAP,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_cap.glb"),
        CAP_BEATS,
    )
}

pub fn read() -> Box<dyn Scene> {
    page(
        &READ,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_read.glb"),
        READ_BEATS,
    )
}

pub fn rows() -> Box<dyn Scene> {
    page(
        &ROWS,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_rows.glb"),
        ROWS_BEATS,
    )
}

pub fn shrink() -> Box<dyn Scene> {
    page(
        &SHRINK,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_shrink.glb"),
        SHRINK_BEATS,
    )
}

pub fn layout() -> Box<dyn Scene> {
    page(
        &LAYOUT,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_layout.glb"),
        LAYOUT_BEATS,
    )
}

pub fn transistor() -> Box<dyn Scene> {
    page(
        &TRANSISTOR,
        include_bytes!("../../../../../tools/pbr3d/assets/cell_transistor.glb"),
        TRANSISTOR_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("cap", cap as fn() -> Box<dyn Scene>),
            ("read", read),
            ("rows", rows),
            ("shrink", shrink),
            ("layout", layout),
            ("transistor", transistor),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
