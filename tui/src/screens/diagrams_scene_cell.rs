// CELL page: one 1T1C DRAM cell, animated. The overview draws the schematic
// (word line, access transistor, storage capacitor, bit line, sense amp) and
// walks one bit through read, restore, leak and refresh. Zoom-ins: a the
// capacitor and its leak, b a read, c refresh across rows, d shrinking the cell.
//
// Sources: Jacob, ENEE 359a DRAM Circuits (slides 4, 9, 11-14); HiRA (arXiv
// 2209.10198, pp. 1-2); PROTEAS (arXiv 2404.16256, Table I, DDR4 refresh values).

use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, lerp, noise};

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 4600;

// overview beats
const IDLE: usize = 0;
const RISE: usize = 1;
const SHARE: usize = 2;
const SENSE: usize = 3;
const PRECHARGE: usize = 4;
const LEAK: usize = 5;
const REFRESH: usize = 6;

// schematic column of the cell
const XC: i32 = 34;

const P_SHARE: Particles = Particles::new(301, 240, 800);
const P_RESTORE: Particles = Particles::new(302, 240, 800);
const P_LEAK: Particles = Particles::new(303, 420, 1600);
const P_REFILL: Particles = Particles::new(304, 260, 900);

const BEATS: &[Beat] = &[
    Beat::new(
        "idle: the cell holds a full charge and the word line is low",
        BEAT_MS,
    )
    .note(
        "One bit sits on the storage capacitor as charge. The access transistor is off, so the cell is cut off from the bit line.",
        "The capacitor is full of + marks, the word line is a thin line, and the sense amp is idle.",
    )
    .detail(
        "A 1T1C cell is one transistor and one capacitor. Full charge reads as 1 and empty reads as 0.",
        &[
            "1T1C: one access transistor and one storage capacitor (Jacob, DRAM Systems slide 3)",
            "Cell area is 6F^2 with an open bit line (Jacob, DRAM Circuits slide 9)",
        ],
    ),
    Beat::new(
        "word line rises: the access transistor switches on",
        BEAT_MS,
    )
    .note(
        "The row decoder drives the word line high. Its gate turns on the access transistor, which joins the storage node to the bit line.",
        "The word line turns thick, the transistor switch fills in, and the bit line is connected to the cell.",
    )
    .detail(
        "The word line selects a whole row, so every cell in the row connects to its bit line at once.",
        &[
            "The word line is a row select: high turns the access transistor on (Jacob, DRAM Circuits slide 4)",
            "A typical array is 512 wordlines by 512 bitlines (Jacob, DRAM Circuits slide 5)",
        ],
    ),
    Beat::new(
        "charge sharing: charge flows from the cell onto the bit line, a small bump",
        BEAT_MS,
    )
    .note(
        "The bit line sits at VDD/2 before the read. The cell and the bit line share charge. The cell is much smaller than the bit line, so the bit line moves only a little, up for a 1.",
        "Dots flow from the capacitor up to the bit line, the capacitor loses a bit of its charge, and the gauge moves a little above the half mark.",
    )
    .detail(
        "This is why the read is destructive: the charge that leaves the cell is not all put back by the sharing itself.",
        &[
            "Charge sharing: Vx = (Vb Cb + Vc Cc) / (Cb + Cc) (Jacob, DRAM Circuits slides 4 and 11)",
            "Signal: Vsignal = Vc Cc / (Cb + Cc); the bit line precharge is VDD/2 (Jacob, slide 11)",
        ],
    ),
    Beat::new(
        "sense amp latches the bit line to full VDD and drives the cell back to full",
        BEAT_MS,
    )
    .note(
        "The sense amp is two cross-coupled inverters on the bit line pair. It detects the small bump and pushes the bit line to a full rail, and the open cell is driven back to full charge.",
        "The gauge snaps to the top, the sense amp box turns to latching, and the capacitor fills back up as dots flow back down.",
    )
    .detail(
        "The sense amp does two jobs in one step: it reads the bit, and it restores the charge the read drained from the cell.",
        &[
            "Sense amp: the latch drives BL to full VDD or GND (Jacob, DRAM Circuits slides 12-14)",
            "Restore: the cell is charged back to full through the same transistor",
        ],
    ),
    Beat::new(
        "restore done: word line falls and the bit line is precharged to VDD/2",
        BEAT_MS,
    )
    .note(
        "The word line drops and cuts the cell off. The bit line is precharged back to VDD/2, ready for the next read.",
        "The word line goes thin again, the gauge slides back to the middle, and the capacitor stays full.",
    )
    .detail(
        "Precharge to VDD/2 is what lets the next read see a small signal either way.",
        &[
            "Precharge: the bit line is held at Vcc/2 before a read (Jacob, DRAM Circuits slides 4 and 11)",
            "The cell keeps its restored charge after the word line falls",
        ],
    ),
    Beat::new(
        "leakage: a little charge drains from the capacitor while the row is idle",
        BEAT_MS,
    )
    .note(
        "With the transistor off, charge leaks out of the storage node through several small paths. The capacitor slowly loses charge.",
        "Faint dots leak out of the bottom of the capacitor and the charge bar shortens.",
    )
    .detail(
        "Leakage is why the cell fades. The window for a fully charged cell is set by the weakest cells on the chip.",
        &[
            "Retention varies cell to cell, and the minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)",
            "Leak paths are from DRAM patent backgrounds, to be verified against a device paper",
        ],
    ),
    Beat::new(
        "refresh: the row is read and rewritten before the charge is gone",
        BEAT_MS,
    )
    .note(
        "The controller opens the row, the sense amp reads it, and the restore step writes the full charge back. The capacitor is topped up before it fades too far.",
        "The word line pulses, the sense amp label reads read+rewrite, and the capacitor fills back to full.",
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
        build: || -> Box<dyn Scene> { Box::new(CapLeak) },
    },
    Zoom {
        key: 'b',
        label: "a read: charge sharing and restore",
        build: || -> Box<dyn Scene> { Box::new(CellRead) },
    },
    Zoom {
        key: 'c',
        label: "refresh across the rows",
        build: || -> Box<dyn Scene> { Box::new(RefreshRows) },
    },
    Zoom {
        key: 'd',
        label: "shrinking the cell",
        build: || -> Box<dyn Scene> { Box::new(Shrink) },
    },
    Zoom {
        key: 'e',
        label: "open vs folded bit lines: the layout",
        build: || -> Box<dyn Scene> { Box::new(BitLayout) },
    },
];

fn bar(q: f32) -> String {
    let n = (q * 8.0).round().clamp(0.0, 8.0) as usize;
    format!("{}{}", "█".repeat(n), "░".repeat(8 - n))
}

/// Word line level: 0 low .. 1 high.
fn wl(t: &Time) -> f32 {
    match t.beat {
        RISE => ease_in_out(t.local),
        SHARE | SENSE => 1.0,
        PRECHARGE => 1.0 - ease_in_out((t.local / 0.4).min(1.0)),
        REFRESH => {
            if t.local < 0.5 {
                1.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

/// Bit line level: 0 = GND, 0.5 = VDD/2, 1 = VDD.
fn bl(t: &Time) -> f32 {
    match t.beat {
        SHARE => 0.5 + 0.07 * ease_in_out(t.local),
        SENSE => lerp(0.57, 1.0, ease_in_out(t.local)),
        PRECHARGE => {
            if t.local < 0.4 {
                1.0
            } else {
                lerp(1.0, 0.5, ease_in_out((t.local - 0.4) / 0.6))
            }
        }
        REFRESH => lerp(0.5, 1.0, ease_in_out((t.local * 2.0).min(1.0))),
        _ => 0.5,
    }
}

/// Cell charge: 0 empty .. 1 full.
fn cap(t: &Time) -> f32 {
    match t.beat {
        SHARE => lerp(1.0, 0.72, ease_in_out(t.local)),
        SENSE => lerp(0.72, 1.0, ease_in_out(t.local)),
        LEAK => lerp(1.0, 0.82, t.local),
        REFRESH => lerp(0.82, 1.0, ease_in_out(t.local)),
        _ => 1.0,
    }
}

fn sa_state(t: &Time) -> &'static str {
    match t.beat {
        SHARE => "reading",
        SENSE => "latching",
        PRECHARGE => "restoring",
        REFRESH => "read+rewrite",
        _ => "idle",
    }
}

fn draw_cell(c: &mut Canvas, t: &Time) {
    // word line
    let high = wl(t) > 0.5;
    c.hline(12, 3, 48, if high { '━' } else { '─' });
    c.text(1, 3, "word line");
    c.text(
        1,
        2,
        if high {
            "word line: HIGH"
        } else {
            "word line: LOW"
        },
    );
    // gate drop to the access transistor
    c.vline(XC, 4, 10, '│');
    c.boxed(XC - 4, 14, 9, 3);
    c.text(XC - 3, 15, "access");
    // bit line into the sense amp
    c.hline(12, 13, 38, '─');
    c.put(XC, 13, '┼');
    c.text(1, 13, "bit line");
    // storage node and capacitor
    c.vline(XC, 17, 2, '│');
    c.text(XC + 3, 17, "storage node");
    let q = cap(t);
    c.hline(XC - 4, 19, 9, '━');
    c.hline(XC - 4, 21, 9, '━');
    let n = (q * 7.0).round() as i32;
    for i in 0..7 {
        c.put(XC - 3 + i, 20, if i < n { '+' } else { '·' });
    }
    c.vline(XC, 22, 2, '│');
    c.text(1, 19, "storage capacitor");
    c.text(1, 20, &format!("charge {}", bar(q)));
    c.text(1, 23, "plate VDD/2");
    c.text(XC - 13, 24, "leak");
    // sense amp
    titled_box(c, 50, 12, 15, 11, "sense amp");
    c.text(52, 14, sa_state(t));
    c.text(52, 16, "latch");
    c.text(52, 17, "restores");
    // bit line voltage gauge
    let (g_top, g_bot) = (5, 22);
    c.vline(68, g_top, g_bot - g_top + 1, '│');
    c.text(70, g_top, "VDD");
    c.text(70, 13, "VDD/2");
    c.text(70, g_bot, "GND");
    let v = bl(t);
    let y = g_bot - ((g_bot - g_top) as f32 * v).round() as i32;
    c.put(68, y, '◆');
    c.text(50, 24, &format!("bit line {:.2} VDD", v));
    // flows
    match t.beat {
        SHARE => flow(
            c,
            &Path::new(&[(XC + 1, 17), (XC + 1, 13), (48, 13)]),
            t.ms,
            P_SHARE,
            |_| '•',
        ),
        SENSE => flow(
            c,
            &Path::new(&[(48, 13), (XC + 1, 13), (XC + 1, 17)]),
            t.ms,
            P_RESTORE,
            |_| '•',
        ),
        LEAK => flow(
            c,
            &Path::new(&[(XC - 4, 20), (XC - 8, 20), (XC - 8, 25)]),
            t.ms,
            P_LEAK,
            |_| '·',
        ),
        REFRESH if t.local < 0.6 => flow(
            c,
            &Path::new(&[(48, 13), (XC + 1, 13), (XC + 1, 17)]),
            t.ms,
            P_REFILL,
            |_| '•',
        ),
        _ => {}
    }
    c.text(2, 25, "+ charge   ◆ bit line   ━ on   ─ off");
}

pub struct MemCell;

impl Scene for MemCell {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        draw_cell(c, t);
    }
}

// ---- a: the storage capacitor ----------------------------------------------

pub struct CapLeak;

const CAP_BEATS: &[Beat] = &[
    Beat::new("a full capacitor holds the bit as charge", BEAT_MS)
        .note(
            "The capacitor is full. Each + is a slice of stored charge between the plates.",
            "A dense block of + between two thick plates.",
        )
        .detail(
            "The bit lives in the charge on this plate pair. Full charge is a 1, empty is a 0.",
            &["1T1C storage element: the capacitor holds the bit (Jacob, DRAM Systems slide 3)"],
        ),
    Beat::new("leakage paths drain the charge while the row sits idle", BEAT_MS)
        .note(
            "Charge leaks out the sides of the storage node. The block of + thins as it drains.",
            "Dots escape left and right, and the charge bar shortens.",
        )
        .detail(
            "Leakage is slow, but it adds up. The minimum retention time of the weakest cells sets the refresh rate.",
            &["Retention and refresh are linked (Mutlu, arXiv 2306.16037, p. 1)"],
        ),
    Beat::new("refresh tops the charge back up to full", BEAT_MS)
        .note(
            "The sense amp reads the bit and writes it back at full charge. The + block fills in again.",
            "Dots flow back in from both sides and the block refills.",
        )
        .detail(
            "A refresh is a read and a rewrite. The rewrite is what restores the full charge.",
            &["DDR4 refresh window: tREFW = 64 ms (PROTEAS, arXiv 2404.16256, Table I)"],
        ),
];

impl Scene for CapLeak {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        CAP_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let q = match t.beat {
            0 => 1.0,
            1 => lerp(1.0, 0.5, t.local),
            _ => lerp(0.5, 1.0, ease_in_out(t.local)),
        };
        c.hline(20, 8, 40, '━');
        c.hline(20, 16, 40, '━');
        c.text(20, 6, "storage node (top plate)");
        c.text(20, 18, "plate VDD/2 (bottom plate)");
        let n = (q * 280.0).round() as i32;
        for k in 0..n {
            c.put(20 + k % 40, 9 + k / 40, '+');
        }
        match t.beat {
            1 => {
                flow(c, &Path::new(&[(19, 12), (4, 12)]), t.ms, P_LEAK, |_| '·');
                flow(c, &Path::new(&[(61, 12), (76, 12)]), t.ms, P_LEAK, |_| '·');
            }
            2 => {
                flow(c, &Path::new(&[(4, 12), (19, 12)]), t.ms, P_REFILL, |_| '•');
                flow(c, &Path::new(&[(76, 12), (61, 12)]), t.ms, P_REFILL, |_| {
                    '•'
                });
            }
            _ => {}
        }
        c.text(2, 10, "leak");
        c.text(2, 22, &format!("charge {}", bar(q)));
    }
}

// ---- b: a read ---------------------------------------------------------------

pub struct CellRead;

const READ_BEATS: &[Beat] = &[
    Beat::new("charge sharing: the cell and the bit line exchange charge", BEAT_MS)
        .note(
            "The access transistor is on. Charge moves from the cell onto the bit line, and the gauge moves a little.",
            "Dots flow from the capacitor to the bit line, and the gauge moves just above the half mark.",
        )
        .detail(
            "The bit line is much bigger than the cell, so the change it sees is small.",
            &["Vsignal = Vc Cc / (Cb + Cc) (Jacob, DRAM Circuits slide 11)"],
        ),
    Beat::new("sense and restore: the latch drives the bit line to a full rail", BEAT_MS)
        .note(
            "The sense amp latches the bit line to full VDD and drives the open cell back to full charge.",
            "The gauge snaps to VDD and dots flow back into the capacitor.",
        )
        .detail(
            "The restore is part of the read. Without it the bit would be lost.",
            &["Sense amp latch and restore (Jacob, DRAM Circuits slides 12-14)"],
        ),
    Beat::new("precharge: the word line falls and the bit line returns to VDD/2", BEAT_MS)
        .note(
            "The word line drops, cutting the cell off. The bit line returns to VDD/2 for the next access.",
            "The word line goes thin, and the gauge slides back to the middle.",
        )
        .detail(
            "Precharge sets up the next read, so it can see a small signal either way.",
            &["Bit line precharged to Vcc/2 (Jacob, DRAM Circuits slides 4 and 11)"],
        ),
];

impl Scene for CellRead {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        READ_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        // the read is the overview's beats 2-4, played on their own
        let at = Time {
            ms: t.ms,
            beat: SHARE + t.beat,
            local: t.local,
            beat_start: t.beat_start,
        };
        draw_cell(c, &at);
    }
}

// ---- c: refresh across the rows -----------------------------------------------

pub struct RefreshRows;

const ROW_BEATS: &[Beat] = &[
    Beat::new("the refresh pointer walks down the rows", BEAT_MS)
        .note(
            "The controller points at one row at a time. Rows above the pointer are fresh. Rows below it are still drifting.",
            "A pointer marks the row being refreshed, and the bars above it are full.",
        )
        .detail(
            "Each refresh command covers a slice of rows, so the whole array is visited in one window.",
            &["8192 REF commands per 64 ms window in DDR4 (PROTEAS, arXiv 2404.16256, Table I)"],
        ),
    Beat::new("each row is read, then rewritten at full charge", BEAT_MS)
        .note(
            "The sense amp reads the row and the restore writes it back. The bar for that row fills.",
            "The row marked with the pointer fills to full.",
        )
        .detail(
            "The read and the rewrite are one operation, so refresh costs a row cycle.",
            &["Refresh is a row read plus restore (HiRA, arXiv 2209.10198, p. 2)"],
        ),
    Beat::new("every row is rewritten within the refresh window", BEAT_MS)
        .note(
            "Once the pointer reaches the bottom, every row has been rewritten. The cycle starts again.",
            "All rows are full again, and the pointer returns to the top.",
        )
        .detail(
            "Refresh is what keeps cells from losing their data. The window is set by the weakest cells.",
            &["tREFW = 64 ms, tREFI = 7800 ns (PROTEAS, arXiv 2404.16256, Table I)"],
        ),
];

impl Scene for RefreshRows {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        ROW_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let p = ((t.beat as f32 + t.local) / ROW_BEATS.len() as f32).clamp(0.0, 0.999);
        let ptr = (p * 8.0) as i32;
        c.text(
            2,
            1,
            "eight rows shown; each refresh command covers a slice of the array",
        );
        for i in 0..8 {
            let y = 4 + i * 2;
            let frac = (p * 8.0).fract();
            let q = if i < ptr { 1.0 } else { 0.9 - 0.3 * frac };
            c.text(2, y, &format!("row {i}"));
            c.text(11, y, &bar(q));
            if i == ptr {
                c.text(22, y, "<- refreshing: read, then rewrite");
            }
        }
        c.text(
            2,
            22,
            "rows below the pointer are still drifting toward empty",
        );
    }
}

// ---- d: shrinking the cell -----------------------------------------------------

pub struct Shrink;

const SHRINK_BEATS: &[Beat] = &[
    Beat::new("a bigger cell: a wide capacitor holds plenty of charge", BEAT_MS)
        .note(
            "A wide capacitor has plenty of area, so its plates hold a full block of charge.",
            "A wide box full of + marks.",
        )
        .detail(
            "Charge scales with the capacitor's area and its height.",
            &["Cell area is 6F^2 with an open bit line (Jacob, DRAM Circuits slide 9)"],
        ),
    Beat::new("shrink: the cell area drops with F^2, so the capacitor gets narrow", BEAT_MS)
        .note(
            "The cell shrinks with the feature size. The capacitor loses area, so the same height holds much less charge.",
            "The box narrows, and the + count drops.",
        )
        .detail(
            "Less charge means a smaller signal on the bit line, which makes the sense amp's job harder.",
            &["Signal: Vsignal = Vc Cc / (Cb + Cc) (Jacob, DRAM Circuits slide 11)"],
        ),
    Beat::new("to hold the charge, the capacitor grows taller", BEAT_MS)
        .note(
            "The capacitor is built taller to get its area back. The + count recovers.",
            "The narrow box grows upward until it holds the charge again.",
        )
        .detail(
            "This is why memory capacitors are built as tall structures. The etch that makes them is the hard part.",
            &["LITHO node for the pattern side of the shrink"],
        ),
];

impl Scene for Shrink {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SHRINK_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let e = ease_in_out(t.local);
        let (w, h) = match t.beat {
            0 => (20.0, 6.0),
            1 => (lerp(20.0, 8.0, e), 6.0),
            _ => (8.0, lerp(6.0, 14.0, e)),
        };
        let (w, h) = (w.round() as i32, h.round() as i32);
        let (x0, y0) = (10, 6);
        titled_box(c, x0, y0, w, h, "");
        let inner = (w - 2).max(1);
        let n = (w * h) / 6;
        for k in 0..n {
            c.put(x0 + 1 + k % inner, y0 + 1 + k / inner, '+');
        }
        c.text(x0 + w + 3, y0, "cell area ~ F^2");
        c.text(x0 + w + 3, y0 + 2, &format!("width {w}, height {h}"));
        c.text(x0 + w + 3, y0 + 3, &format!("charge ~ {n} units"));
    }
}

// ---- e: open vs folded bit lines -------------------------------------------------

pub struct BitLayout;

const BIT_BEATS: &[Beat] = &[
    Beat::new("open bit lines: the reference line sits in the other array", BEAT_MS)
        .note(
            "Each bit line runs through the sense amp. The true line is in array A and its complement is in array B, so the pair is split across two arrays.",
            "A straight line through the sense amp: BL on the left in array A, BL* on the right in array B, and a cell on every crossing.",
        )
        .detail(
            "The open layout packs the cells tightly, so it is the denser choice.",
            &[
                "Open bit line cell: 1F x 3F = 6F^2 (Jacob, DRAM Circuits slide 9)",
                "Open array: the two bit lines of a pair sit in different sub-arrays (Jacob, DRAM Circuits slides 6 and 7)",
            ],
        ),
    Beat::new("folded bit lines: the pair sits side by side in one array", BEAT_MS)
        .note(
            "Both lines of the pair run next to each other in the same array. The cells stagger between the two lines.",
            "Two parallel lines (BL and BL*) into one sense amp, with the cells alternating between them.",
        )
        .detail(
            "The folded layout gives up area, so each cell is bigger, in exchange for lines that see the same environment.",
            &[
                "Folded bit line cell: 2F x 4F = 8F^2 (Jacob, DRAM Circuits slide 9)",
                "Folded: BLX and BLX* routed together improves noise immunity (Jacob, DRAM Circuits slide 8)",
            ],
        ),
    Beat::new("noise: the same bump lands on both folded lines, so the sense amp cancels it", BEAT_MS)
        .note(
            "A noise bump is common to both lines of the pair. The sense amp reads the difference between the two lines, so the bump drops out.",
            "Wavy marks ~ hit BL and BL* at the same column at the same time. The SA readout stays clean.",
        )
        .detail(
            "Noise common to both lines cancels in a differential sense amp. In the open layout the bump lands on one array only, so it does not cancel.",
            &[
                "Routing both lines together, with twisting, improves noise immunity (Jacob, DRAM Circuits slide 8)",
                "The sense amp compares the two lines (Jacob, DRAM Circuits slides 12 to 14)",
            ],
        ),
];

const WL_ALL: [i32; 11] = [9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89];
const WL_LEFT: [i32; 6] = [9, 17, 25, 33, 41, 49];
const WL_RIGHT: [i32; 6] = [73, 81, 89, 97, 105, 113];

fn draw_open(c: &mut Canvas) {
    // true and complement share one straight line through the sense amp
    c.hline(6, 12, 110, '─');
    c.hline(6, 16, 110, '─');
    for x in WL_LEFT.iter().chain(WL_RIGHT.iter()) {
        c.vline(*x, 6, 22, '┊');
    }
    for x in WL_LEFT.iter().chain(WL_RIGHT.iter()) {
        c.put(*x, 12, '●');
        c.put(*x, 16, '●');
    }
    titled_box(c, 4, 4, 50, 26, "array A: true bit lines");
    titled_box(c, 66, 4, 50, 26, "array B: complement bit lines");
    titled_box(c, 56, 11, 9, 7, "SA");
}

fn draw_folded(c: &mut Canvas, noise_ms: Option<u64>) {
    titled_box(
        c,
        4,
        4,
        92,
        26,
        "one array: true and complement side by side",
    );
    // one pair: BL on row 12, BL* on row 13, both into the sense amp
    c.hline(6, 12, 92, '─');
    c.hline(6, 13, 92, '─');
    for x in WL_ALL {
        c.vline(x, 6, 22, '┊');
    }
    for (i, x) in WL_ALL.iter().enumerate() {
        if i % 2 == 0 {
            c.put(*x, 12, '●');
        } else {
            c.put(*x, 13, '●');
        }
    }
    titled_box(c, 98, 11, 9, 5, "SA");
    if let Some(ms) = noise_ms {
        for x in 6..=97 {
            if noise(x as u64 * 31 + 7, ms / 100) < 0.22 {
                c.put(x, 12, '~');
                c.put(x, 13, '~');
            }
        }
        c.text(98, 17, "SA out:");
        c.text(98, 18, "BL - BL*");
        c.text(98, 19, "= clean");
    }
}

impl Scene for BitLayout {
    fn size(&self) -> (u16, u16) {
        (120, 34)
    }

    fn beats(&self) -> &[Beat] {
        BIT_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        match t.beat {
            0 => {
                draw_open(c);
                c.text(4, 31, "open: the reference line sits in the other array");
                c.text(
                    4,
                    32,
                    "1F x 3F = 6F^2 per cell: denser, but a bump in one array hits one line",
                );
            }
            1 => {
                draw_folded(c, None);
                c.text(4, 31, "folded: BL and BL* sit side by side in one array");
                c.text(
                    4,
                    32,
                    "2F x 4F = 8F^2 per cell: less dense, but both lines see the same environment",
                );
            }
            _ => {
                draw_folded(c, Some(t.ms));
                c.text(
                    4,
                    31,
                    "noise: the same bump lands on both lines of the pair",
                );
                c.text(
                    4,
                    32,
                    "the sense amp reads BL minus BL*, so the common bump cancels",
                );
            }
        }
    }
}

#[cfg(test)]
mod layout_tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    #[test]
    fn layout_beats_show_their_point() {
        let mut p = Player::new(Box::new(BitLayout), Instant::now());
        p.fit(120, 34);
        let at = |p: &mut Player, beat: usize| {
            p.shot_at(beat as u64 * BEAT_MS + BEAT_MS / 2)
                .lines
                .join("\n")
        };
        assert!(at(&mut p, 0).contains("1F x 3F"));
        assert!(at(&mut p, 1).contains("2F x 4F"));
        assert!(at(&mut p, 2).contains("~"));
        assert!(at(&mut p, 2).contains("= clean"));
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn zoom_scenes() -> Vec<(&'static str, fn() -> Box<dyn Scene>)> {
        vec![
            ("cap", || Box::new(CapLeak)),
            ("read", || Box::new(CellRead)),
            ("rows", || Box::new(RefreshRows)),
            ("shrink", || Box::new(Shrink)),
            ("layout", || Box::new(BitLayout)),
        ]
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        let mut all: Vec<(&str, &[Beat])> = vec![("overview", BEATS)];
        all.push(("cap", CAP_BEATS));
        all.push(("read", READ_BEATS));
        all.push(("rows", ROW_BEATS));
        all.push(("shrink", SHRINK_BEATS));
        all.push(("layout", BIT_BEATS));
        for (name, beats) in all {
            assert!(beats.len() >= 3, "{name}");
            for (i, b) in beats.iter().enumerate() {
                assert!(!b.caption.is_empty(), "{name} {i}");
                assert!(
                    !b.what.is_empty()
                        && !b.look.is_empty()
                        && !b.why.is_empty()
                        && !b.facts.is_empty(),
                    "{name} {i} note"
                );
            }
        }
    }

    fn all_scenes() -> Vec<(&'static str, fn() -> Box<dyn Scene>)> {
        let mut v = zoom_scenes();
        v.insert(0, ("overview", || Box::new(MemCell)));
        v
    }

    #[test]
    fn overview_and_zooms_scale_and_move() {
        for (name, mk) in all_scenes() {
            for (w, h) in [(84, 26), (120, 38), (200, 60)] {
                let mut p = Player::new(mk(), Instant::now());
                p.fit(w, h);
                let mut seen = std::collections::HashSet::new();
                for ms in (0..p.loop_ms()).step_by(173) {
                    let shot = p.shot_at(ms);
                    assert_eq!(shot.lines.len(), p.height());
                    assert!(shot.lines.iter().all(|l| l.chars().count() <= p.width()));
                    seen.insert(shot.lines.join("\n"));
                }
                assert!(seen.len() > 12, "{name} {w}x{h}: {}", seen.len());
            }
        }
    }

    #[test]
    fn overview_shows_the_story_by_beat() {
        let mut p = Player::new(Box::new(MemCell), Instant::now());
        p.fit(84, 26);
        let at = |p: &mut Player, beat: usize| {
            p.shot_at((beat as u64) * BEAT_MS + BEAT_MS / 2)
                .lines
                .join("\n")
        };
        assert!(at(&mut p, IDLE).contains("word line: LOW"));
        assert!(
            p.shot_at(RISE as u64 * BEAT_MS + BEAT_MS * 4 / 5)
                .lines
                .join("\n")
                .contains("word line: HIGH")
        );
        assert!(at(&mut p, SENSE).contains("latching"));
        assert!(at(&mut p, LEAK).contains("draining") || at(&mut p, LEAK).contains("leak"));
        assert!(at(&mut p, REFRESH).contains("read+rewrite"));
    }
}
