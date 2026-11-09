// CELL page: one 1T1C DRAM cell, drawn in 3D by poly3d. The overview walks one bit
// through read, restore, leak and refresh, with the camera gliding to the part each
// beat is about. Each zoom is its own focused 3D scene showing only its subject: a the
// capacitor and its leak paths, b a read as a small cell tank and a big bit line tank,
// c refresh across the rows, d shrinking the capacitor, e open vs folded bit lines.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: Jacob, ENEE 359a DRAM Systems (slide 3) and DRAM Circuits (slides 4,
// 5, 9, 11-14); HiRA (arXiv 2209.10198, pp. 1-2); PROTEAS (arXiv 2404.16256,
// Table I, DDR4 refresh values); Mutlu (arXiv 2306.16037, p. 1).

use image::RgbaImage;

use super::diagrams_px::{self as px, Rgb};
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom, ease_in_out, lerp};
use poly3d::CellZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
// long enough to read the notes while the beat plays
const BEAT_MS: u64 = 6500;
// the overview's notes sit on the picture and show once the camera settles, so its
// beats run longer
const OVERVIEW_MS: u64 = 13000;

// overview beats
const RISE: usize = 1;
const SHARE: usize = 2;
const SENSE: usize = 3;
const PRECHARGE: usize = 4;
const LEAK: usize = 5;
const REFRESH: usize = 6;

const BEATS: &[Beat] = &[
    Beat::new(
        "idle: the cell holds a full charge and the word line is low",
        OVERVIEW_MS,
    )
    .note(
        "One bit sits on the storage capacitor as charge. The access transistor is off, so the cell is cut off from the bit line.",
        "Orange charge fills the capacitor. The word line and the access transistor are dim, and the bit line voltage gauge rests at the VDD/2 ring.",
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
        OVERVIEW_MS,
    )
    .note(
        "The row decoder drives the word line high. Its gate turns on the access transistor, which joins the storage node to the bit line.",
        "The camera moves in on the gate. The word line thickens and turns orange, and the access transistor lights pink.",
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
        OVERVIEW_MS,
    )
    .note(
        "The bit line sits at VDD/2 before the read. The cell and the bit line share charge. The bit line is much bigger than the cell, so it moves only a little, up for a 1.",
        "Cyan dots run from the capacitor to the bit line, the capacitor dims from its rim, and the gauge rises just above the VDD/2 ring.",
    )
    .detail(
        "The read is destructive: the charge that leaves the cell is not all put back by the sharing itself.",
        &[
            "Charge sharing conserves charge: the final bit-line voltage is (Cb VBL + Cc Vcell) / (Cb + Cc) (Jacob, DRAM Circuits slides 4 and 11)",
            "Signal swing: dV = (Vcell - VDD/2) Cc / (Cc + Cb), so a smaller storage capacitor gives a smaller swing (same slides; derived from the sharing formula)",
        ],
    ),
    Beat::new(
        "sense amp latches the bit line to full VDD and drives the cell back to full",
        OVERVIEW_MS,
    )
    .note(
        "The sense amp is two cross-coupled inverters on the bit line pair. It detects the small bump and pushes the bit line to a full rail, and the open cell is driven back to full charge.",
        "The gauge climbs to the top, the sense amp turns purple, and violet dots run back into the capacitor until it is full again.",
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
        OVERVIEW_MS,
    )
    .note(
        "The word line drops and cuts the cell off. The bit line is precharged back to VDD/2, ready for the next read.",
        "The word line thins and dims, the gauge slides back to the VDD/2 ring, the capacitor stays full, and the sense amp turns green.",
    )
    .detail(
        "Precharge to VDD/2 is what lets the next read see a small swing either way.",
        &[
            "Precharge: the bit line is held at Vcc/2 before a read (Jacob, DRAM Circuits slides 4 and 11)",
            "The cell keeps its restored charge after the word line falls",
        ],
    ),
    Beat::new(
        "leakage: a little charge drains from the capacitor while the row is idle",
        OVERVIEW_MS,
    )
    .note(
        "With the transistor off, charge leaks out of the storage node through several small paths. The capacitor slowly loses charge.",
        "The camera moves in on the capacitor. Dots leak off both plates and fade as they go, and the charge dims from the rim inward.",
    )
    .detail(
        "Leakage is why the cell fades. The window for a fully charged cell is set by the weakest cells on the chip.",
        &[
            "Retention varies cell to cell, and the minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)",
            "Three leak paths (capacitor dielectric, storage-node junction, off transistor) is the standard list; no source here splits the loss between them",
        ],
    ),
    Beat::new(
        "refresh: the row is read and rewritten before the charge is gone",
        OVERVIEW_MS,
    )
    .note(
        "The controller opens the row, the sense amp reads it, and the restore step writes the full charge back. The capacitor is topped up before it fades too far.",
        "The word line pulses, cyan dots read the cell, violet dots rewrite it, and the capacitor refills.",
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

/// `ease_in_out` over the window [a, b] of the beat: 0 before, 1 after.
fn window(t: &Time, a: f32, b: f32) -> f32 {
    ease_in_out((t.local - a) / (b - a))
}

/// Word line level: 0 low .. 1 high. Every beat starts where the last one ended.
fn wl(t: &Time) -> f32 {
    match t.beat {
        RISE => ease_in_out(t.local),
        SHARE | SENSE => 1.0,
        PRECHARGE => 1.0 - window(t, 0.0, 0.4),
        REFRESH => window(t, 0.0, 0.14) * (1.0 - window(t, 0.74, 0.92)),
        _ => 0.0,
    }
}

/// Bit line level: 0 = GND, 0.5 = VDD/2, 1 = VDD.
fn bl(t: &Time) -> f32 {
    match t.beat {
        SHARE => 0.5 + 0.07 * ease_in_out(t.local),
        SENSE => lerp(0.57, 1.0, ease_in_out(t.local)),
        PRECHARGE => lerp(1.0, 0.5, window(t, 0.4, 1.0)),
        REFRESH => 0.5 + 0.5 * window(t, 0.14, 0.45) * (1.0 - window(t, 0.74, 1.0)),
        _ => 0.5,
    }
}

/// Cell charge: 0 empty .. 1 full.
fn cap(t: &Time) -> f32 {
    match t.beat {
        SHARE => lerp(1.0, 0.72, ease_in_out(t.local)),
        SENSE => lerp(0.72, 1.0, ease_in_out(t.local)),
        LEAK => lerp(1.0, 0.82, window(t, 0.05, 0.95)),
        REFRESH => lerp(0.82, 1.0, window(t, 0.42, 0.74)),
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

fn sa_color(t: &Time) -> Rgb {
    match sa_state(t) {
        "reading" => px::YELLOW,
        "latching" => px::PURPLE,
        "restoring" | "read+rewrite" => px::GREEN,
        _ => px::DIM,
    }
}

/// Sense amp colour, blending from the previous beat's over the start of this one.
fn sa_rgb(t: &Time) -> [f32; 3] {
    let prev = Time {
        beat: (t.beat + BEATS.len() - 1) % BEATS.len(),
        ..*t
    };
    let (a, b) = (sa_color(&prev), sa_color(t));
    let k = window(t, 0.0, 0.3);
    std::array::from_fn(|i| lerp(f32::from(a[i]), f32::from(b[i]), k) / 255.0)
}

/// Soft on and off inside the window [a, b] of the beat.
fn envelope(t: &Time, a: f32, b: f32) -> f64 {
    (window(t, a, a + 0.1) * (1.0 - window(t, b - 0.1, b))) as f64
}

/// The 3D cell's state at this instant. Flows fade in and out, and `phase` runs on the
/// loop clock rather than the beat, so dots do not jump when the beat changes.
fn cell_anim(t: &Time) -> poly3d::CellAnim {
    let (read, restore) = match t.beat {
        SHARE => (envelope(t, 0.05, 1.0), 0.0),
        SENSE => (0.0, envelope(t, 0.0, 0.95)),
        REFRESH => (envelope(t, 0.14, 0.46), envelope(t, 0.40, 0.76)),
        _ => (0.0, 0.0),
    };
    poly3d::CellAnim {
        wl: wl(t) as f64,
        bl: bl(t) as f64,
        cap: cap(t) as f64,
        sa_rgb: sa_rgb(t),
        read,
        restore,
        leak: if t.beat == LEAK { envelope(t, 0.0, 1.0) } else { 0.0 },
        phase: t.ms as f64 / 2600.0,
    }
}

/// The overview at `t`, turned by the user's `view`, with the beat's notes drawn
/// on the picture beside the parts they are about.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes {
        what: b.what,
        why: b.why,
        facts: b.facts,
    };
    poly3d::render_overview(
        t.beat,
        t.local as f64,
        &cell_anim(t),
        view,
        Some(&notes),
        w as usize,
        h as usize,
        px::BG,
    )
}

fn overview(t: &Time, w: u32, h: u32) -> RgbaImage {
    overview_frame(t, &poly3d::View::default(), w, h)
}

/// The CELL overview: the schematic, walking one bit through its beats.
pub struct MemCell;

impl Scene for MemCell {
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
        Some(overview(t, w, h))
    }
    fn notes_in_picture(&self) -> bool {
        true
    }
    fn rest_point(&self) -> f32 {
        0.4
    }
}

// ---- the zooms: each is a focused 3D scene from poly3d ------------------------

/// The 3D scene behind zoom `key`: letters are parts of the overview, numbers the
/// page's sections.
pub fn zoom_scene(key: char) -> Option<CellZoom> {
    Some(match key {
        'a' => CellZoom::Capacitor,
        'b' => CellZoom::Read,
        'c' => CellZoom::Rows,
        'd' => CellZoom::Shrink,
        'e' => CellZoom::Layout,
        '1' => CellZoom::Bit,
        '2' => CellZoom::Parts,
        '3' => CellZoom::Order,
        '4' => CellZoom::RefreshCmds,
        '5' => CellZoom::Retention,
        '6' => CellZoom::Numbers,
        '7' => CellZoom::Swing,
        '8' => CellZoom::Makers,
        '9' => CellZoom::Risks,
        _ => return None,
    })
}

fn zoom_frame(z: CellZoom, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
    Some(poly3d::render_zoom(
        z,
        t.beat,
        t.local as f64,
        &poly3d::View::default(),
        w as usize,
        h as usize,
        px::BG,
    ))
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
                zoom_frame($zoom, t, w, h)
            }
        }
    };
}

const CAP_BEATS: &[Beat] = &[
    Beat::new("a full capacitor holds the bit as charge", BEAT_MS).note(
        "The cell is full: charge sits between the two plates. Nearly all of the bit is in this capacitor.",
        "The space between the plates is full of orange charge and the charge level gauge reads full.",
    ),
    Beat::new("leakage paths drain the charge while the row sits idle", BEAT_MS).note(
        "Charge escapes through the dielectric, the storage-node junction and the off transistor. The loss is slow, but it does not stop.",
        "Dots leave along the three named paths. The charge dims from the rim inward and the gauge drops.",
    ),
    Beat::new("refresh tops the charge back up to full", BEAT_MS).note(
        "A refresh read and rewrite pushes charge back in from the bit line.",
        "Cyan dots come down the top lead, the charge relights from the centre outward, and the gauge climbs back to full.",
    ),
];

const READ_BEATS: &[Beat] = &[
    Beat::new("charge sharing: the cell and the bit line exchange charge", BEAT_MS).note(
        "Think of two tanks. The bit line sits at VDD/2 and is much bigger than the cell. When the transistor opens, their levels meet, so the cell falls a lot and the bit line moves only a little.",
        "The valve lifts, dots cross the pipe, and the two levels meet. The trace at the foot bumps just above VDD/2.",
    ),
    Beat::new("sense and restore: the latch drives the bit line to a full rail", BEAT_MS).note(
        "The sense amp amplifies the small bump to a full rail. The transistor is still open, so driving the bit line high also writes the cell back.",
        "The sense amp lights purple. Both tanks fill to the top, and the trace climbs to VDD.",
    ),
    Beat::new("precharge: the word line falls and the bit line returns to VDD/2", BEAT_MS).note(
        "The transistor closes first, so the cell keeps its restored charge. The bit line is then brought back to the middle, ready for the next read.",
        "The valve drops, the cell stays full, the bit line tank falls to the VDD/2 ring, and the trace returns to the middle.",
    ),
];

const REFRESH_BEATS: &[Beat] = &[
    Beat::new("the refresh pointer walks down the rows", BEAT_MS).note(
        "Each bar is a row and its height is the charge. Every row sags until a refresh command reaches it, and the pointer walks the array one row at a time.",
        "The white pointer moves along the rows. Rows ahead of it are short and dim, and rows behind it are tall and green.",
    ),
    Beat::new("each row is read, then rewritten at full charge", BEAT_MS).note(
        "The camera follows the pointer. The row under it is read (yellow) and then rewritten (green) before the pointer moves on.",
        "One row flashes yellow, rises to full height and turns green, and the pointer steps to the next.",
    ),
    Beat::new("every row is rewritten within the refresh window", BEAT_MS).note(
        "The window is 64 ms in DDR4. Every row must get its turn before the window closes, and then the cycle starts again.",
        "All rows are green and the window bar along the front fills to the end. The first rows are already starting to sag.",
    ),
];

const SHRINK_BEATS: &[Beat] = &[
    Beat::new("a bigger cell: a wide capacitor holds plenty of charge", BEAT_MS).note(
        "At a larger feature size the capacitor is a wide, shallow plate pair, with room for plenty of charge.",
        "The plates are wide, the purple square under them is the cell's area, and the gauge is full.",
    ),
    Beat::new("shrink: the cell area drops with F^2, so the capacitor gets narrow", BEAT_MS).note(
        "A smaller cell leaves a narrower capacitor. Less area holds less charge, and the bit line swing shrinks with it.",
        "The plates and the purple square shrink inside the glass outline of the old size, and the gauge falls as charge disappears.",
    ),
    Beat::new("to hold the charge, the capacitor grows taller", BEAT_MS).note(
        "Designs keep the capacitance up by making the capacitor taller, or by using a better dielectric. The footprint stays small.",
        "The capacitor stretches upward, charge fills it, and the gauge climbs back up while the purple square stays small.",
    ),
];

const LAYOUT_BEATS: &[Beat] = &[
    Beat::new("open bit lines: the reference line sits in the other array", BEAT_MS).note(
        "A sense amp compares two lines. In an open layout the signal and the reference bit lines sit in different arrays, with the sense amp between them.",
        "Two arrays, one sense amp between them. The cyan line carries the cell's signal and the orange line the reference.",
    ),
    Beat::new("folded bit lines: the pair sits side by side in one array", BEAT_MS).note(
        "In a folded layout both bit lines of a pair run side by side in one array, so noise couples onto both lines.",
        "The orange line lifts over the sense amp and settles beside the cyan one, and the second array fades away.",
    ),
    Beat::new("noise: the same bump lands on both folded lines, so the sense amp cancels it", BEAT_MS).note(
        "Noise that couples onto both lines looks the same on each, so the sense amp sees only the difference, which does not change.",
        "A pink band crosses the array and bumps both lines together. The green difference line on the floor stays flat.",
    ),
];

zoom_scene_impl!(CapLeak, CAP_BEATS, CellZoom::Capacitor);
zoom_scene_impl!(CellRead, READ_BEATS, CellZoom::Read);
zoom_scene_impl!(RefreshRows, REFRESH_BEATS, CellZoom::Rows);
zoom_scene_impl!(Shrink, SHRINK_BEATS, CellZoom::Shrink);
zoom_scene_impl!(BitLayout, LAYOUT_BEATS, CellZoom::Layout);

// ---- 1-9: the write-up's sections, on the same 3D template ----------------------

const BIT_BEATS: &[Beat] = &[
    Beat::new("a full capacitor reads as 1", BEAT_MS)
        .note(
            "A DRAM bit is a packet of charge on one tiny capacitor. The cell is one transistor and one capacitor, so it is called 1T1C.",
            "Charge comes down the bit line through the open transistor and fills the capacitor. The transistor then closes and the charge stays.",
        )
        .detail(
            "An array is this one small part, repeated.",
            &["The cell is 1 transistor + 1 capacitor (1T1C)", "Full charge reads as 1, empty reads as 0"],
        ),
    Beat::new("an empty capacitor reads as 0", BEAT_MS)
        .note(
            "The same cell holds a 0 when its capacitor is empty. Opening the transistor lets the charge run out onto the bit line.",
            "The transistor lights pink, orange dots run out along the wires, and the charge goes dark from the rim inward.",
        )
        .detail(
            "A bit is not a switch that stays set. It is an amount of charge, which is why the rest of this page is about keeping it.",
            &["Full charge = 1", "Empty = 0"],
        ),
    Beat::new("every cell in the array holds its own bit", BEAT_MS)
        .note(
            "Zoom out and the cell is one of many, each with its own transistor and capacitor, each storing its own 1 or 0.",
            "The camera lifts. Cells with an orange band hold a 1, and the rest hold a 0. The cell we emptied is at the centre.",
        )
        .detail(
            "Each bit gets its own transistor and capacitor.",
            &["A typical array is 512 wordlines x 512 bitlines"],
        ),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("word line: the row select", BEAT_MS)
        .note(
            "The word line runs along a row. Driving it high turns on every access transistor in that row at once.",
            "The rod lights orange, and dots run along it past the gate of this cell.",
        )
        .detail("One word line opens a whole row, not a single cell.", &["word line: row select; high turns on every access transistor in its row"]),
    Beat::new("access transistor: the switch", BEAT_MS)
        .note(
            "The access transistor is a switch between the bit line and the storage node. Off, the cell is cut off. On, charge can move.",
            "The channel lights pink under its gate, with dots crossing from the capacitor toward the bit line.",
        )
        .detail("While it is off, the transistor is meant to hold the charge in. It still leaks a little.", &["access transistor: a switch between the bit line and the storage node"]),
    Beat::new("storage capacitor: the bit itself", BEAT_MS)
        .note(
            "The storage capacitor holds the bit as charge on its plate. Everything else in the cell exists to read or refill this.",
            "The plates brighten and the charge between them glows.",
        )
        .detail("Nearly all of the bit is here, so its size sets how strong a read can be.", &["storage capacitor: holds the bit as charge on its plate"]),
    Beat::new("bit line: the column wire", BEAT_MS)
        .note(
            "The bit line is the column wire that carries charge to and from the cell. It is precharged to VDD/2 before each read.",
            "The vertical wire lights cyan, with dots moving along it.",
        )
        .detail("Sitting at the midpoint lets a read move it up for a 1 or down for a 0.", &["bit line: the column wire; precharged to VDD/2 before each read"]),
    Beat::new("sense amp: the latch", BEAT_MS)
        .note(
            "The sense amp is two cross-coupled inverters on a bit line pair. It sees a small difference and latches to a full rail.",
            "The block at the foot of the bit line lights purple.",
        )
        .detail("It turns a tiny bump into a full 1 or 0.", &["sense amp: two cross-coupled inverters on a bit line pair; latches to a full rail"]),
    Beat::new("precharge: back to the middle", BEAT_MS)
        .note(
            "Precharge holds the bit line at VDD/2 between accesses, so every read starts from the same place.",
            "The block beside the bit line lights green, feeding dots into the wire.",
        )
        .detail("Without it the next read would start from wherever the last one ended.", &["precharge: holds the bit line at VDD/2 between accesses"]),
];

const ORDER_BEATS: &[Beat] = &[
    Beat::new("1. precharge: the bit line sits at VDD/2", BEAT_MS).note(
        "Each lane is a signal over time, and its height is the level. The playhead draws them left to right. Before the read, the bit line waits at the middle and the cell is full.",
        "The cyan wall sits at the VDD/2 line, the orange wall is at full height, and the pink word line is flat.",
    )
    .detail("Every read starts from this same state.", &["The bit line is precharged to VDD/2", "The tiles at the front number the five steps"]),
    Beat::new("2. word line rises: the access transistor switches on", BEAT_MS).note(
        "The word line goes high and the transistor switches on. Nothing else has moved yet, but the cell is now joined to the bit line.",
        "The pink wall climbs to full height.",
    )
    .detail("The word line opens the whole row, so all its cells start a read together.", &["high turns on every access transistor in the row"]),
    Beat::new("3. charge sharing: the bit line moves a small amount", BEAT_MS).note(
        "Charge moves between the cell and the bit line. The bit line moves a small amount, up for a 1 and down for a 0. The cell falls a long way to meet it.",
        "The orange wall drops a lot, and the cyan wall rises only slightly.",
    )
    .detail("The read has already damaged the stored bit at this point.", &["The bit line moves up for a 1, down for a 0"]),
    Beat::new("4. sense amp: the latch drives the bit line to a full rail", BEAT_MS).note(
        "The sense amp detects that small move and drives the bit line all the way to full VDD, or to GND for a 0.",
        "The cyan wall climbs to full height. The orange wall has not recovered yet.",
    )
    .detail("This is where the bit is actually read.", &["The latch drives the bit line to a full VDD or full GND"]),
    Beat::new("5. restore: the still-connected cell returns to full charge", BEAT_MS).note(
        "The cell is still connected, so the driven bit line pushes it back to its full charge. The read drains the cell, so the restore is part of every read, not an extra.",
        "The orange wall climbs back to full height. Then the diagram clears for the next read.",
    )
    .detail("A DRAM read destroys what it reads and then writes it back.", &["The restore step is part of every read"]),
];

const CMD_BEATS: &[Beat] = &[
    Beat::new("the controller issues a refresh command on a timer", BEAT_MS)
        .note(
            "The ring is the 64 ms refresh window and each tick is a REF command. The controller issues one every 7800 ns, whatever else is going on.",
            "The white hand moves round the ring, lighting a tick for each command. The ring shows 64 ticks in place of the real 8192.",
        )
        .detail("Refresh runs on a clock, because leakage does not wait.", &["tREFI = 7800 ns", "8192 REF commands per window"]),
    Beat::new("each command refreshes a slice of rows", BEAT_MS)
        .note(
            "A REF command does not refresh the whole array. It covers one slice of rows, and the next command takes the next slice.",
            "The camera moves in on the stack. The next slice flashes yellow and turns green as the hand reaches it.",
        )
        .detail("No single command covers every row: it takes the whole window to get round them all.", &["Each command refreshes a slice of rows"]),
    Beat::new("the window closes with every row done", BEAT_MS)
        .note(
            "By the end of the window every slice has had its turn, so every row was rewritten within 64 ms. Then it starts again.",
            "The ring closes, the stack is all green, and both fade out as the next window begins.",
        )
        .detail("8192 commands at 7800 ns each come to about 64 ms, so the numbers fit together.", &["tREFW = 64 ms (DDR4)", "8192 x 7800 ns is about 64 ms"]),
];

const RETENTION_BEATS: &[Beat] = &[
    Beat::new("charge drains from every cell, each at its own rate", BEAT_MS)
        .note(
            "Charge drains from the storage node through the dielectric, the junction and the off transistor. The loss is slow and differs from cell to cell.",
            "Each column is a cell's charge. They all fall, but not together. The pink grid marks where a cell becomes too low to read.",
        )
        .detail("The leak rates here are illustrative. The point is that they vary.", &["Retention varies cell to cell (Mutlu, arXiv 2306.16037, p. 1)"]),
    Beat::new("the weakest cell sets the deadline", BEAT_MS)
        .note(
            "Most cells could wait longer. The weakest cannot, and one refresh window applies to them all, so it has to cover the weakest.",
            "The camera moves to the pink column, falling fastest and heading for the pink grid.",
        )
        .detail("One rule for all the cells means the worst cell sets the pace for the rest.", &["The minimum retention time sets the refresh rate (Mutlu, arXiv 2306.16037, p. 1)"]),
    Beat::new("refresh arrives just in time", BEAT_MS)
        .note(
            "The refresh rewrites every cell before the weakest crosses the line. Cells that had plenty of charge left get rewritten too.",
            "A wave crosses the field and all the columns rise back to full, with the pink one just above the grid when it arrives.",
        )
        .detail("Most of the refresh work goes to cells that did not need it yet.", &["The refresh window has to cover the weakest cells"]),
];

const NUMBERS_BEATS: &[Beat] = &[
    Beat::new("6F^2: the cell area with an open bit line", BEAT_MS)
        .note(
            "Cell area is counted in squares of F, the minimum feature size. With an open bit line a cell takes 6 of them.",
            "Six orange tiles, with a ruler along the side marked in F.",
        )
        .detail("Counting in F lets you compare layouts on any process.", &["cell area: 6F^2 with an open bit line (Jacob, DRAM Circuits slide 9)"]),
    Beat::new("8F^2: the cell area with a folded bit line", BEAT_MS)
        .note(
            "A folded bit line takes 8 squares, a third more area per cell. That is the price of its better noise behaviour, shown in zoom e.",
            "Two cyan tiles grow onto the end, and the ruler extends with them.",
        )
        .detail("Going from 8 to 6 squares fits more cells in the same area.", &["cell area: 8F^2 with a folded bit line"]),
    Beat::new("one cell in a 512 by 512 array", BEAT_MS)
        .note(
            "A typical array has 512 word lines and 512 bit lines, one cell at each crossing. The array is refreshed on the 64 ms window from section 4.",
            "The camera lifts off the cell to show the array around it. The grid draws every 16th line, and the cell is not to scale.",
        )
        .detail("512 x 512 is 262,144 cells in one array.", &["typical array: 512 wordlines x 512 bitlines", "tREFW = 64 ms, tREFI = 7800 ns (DDR4)"]),
];

const SWING_BEATS: &[Beat] = &[
    Beat::new("the swing depends on Cc against Cb", BEAT_MS)
        .note(
            "The bit line's move on a read is (Vcell - VDD/2) x Cc / (Cc + Cb). Cc is the cell's capacitance, Cb the bit line's. The purple bar is that swing, enlarged.",
            "A small orange cell, a big cyan bit line, and a tall purple bar for the swing. The sizes are schematic.",
        )
        .detail("Cb is much bigger than Cc, so the swing is a small fraction of the voltage.", &["swing = (Vcell - VDD/2) x Cc / (Cc + Cb) (Jacob, DRAM Circuits slides 4 and 11)"]),
    Beat::new("shrink the cell and the swing shrinks", BEAT_MS)
        .note(
            "A smaller feature size F means a smaller capacitor, so a smaller Cc. Cb has not changed, so the swing drops, and the sense amp has less to work with.",
            "The orange cell narrows inside its old outline, and the purple bar falls away from the white ring marking where it started.",
        )
        .detail("Less signal is what shrinking the cell costs.", &["A smaller storage capacitor gives a smaller swing"]),
    Beat::new("a taller capacitor brings the swing back", BEAT_MS)
        .note(
            "Designs keep Cc up with a taller capacitor or a better dielectric. The cell's footprint stays small, and the capacitance returns.",
            "The orange cell grows upward, and the purple bar climbs back to the white ring.",
        )
        .detail("The footprint keeps shrinking while the height does the work.", &["Designs keep Cc up with a taller capacitor or a better dielectric"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note(
            "Commodity DRAM is made by three companies. Micron is the first of them.",
            "Three wafers, one per maker. The wafers are the same size on purpose: this is not a market share chart.",
        )
        .detail("Market share and the split between commodity and HBM are on the market pages.", &["Commodity DRAM makers: Micron, SK hynix, Samsung"]),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note(
            "SK hynix is the second maker, listed in Korea.",
            "The middle wafer brightens and its ticker appears.",
        )
        .detail("Market share and the split between commodity and HBM are on the market pages.", &["SK hynix ticker: 000660.KS"]),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note(
            "Samsung is the third maker, also listed in Korea.",
            "The right wafer brightens and its ticker appears.",
        )
        .detail("Market share and the split between commodity and HBM are on the market pages.", &["Samsung ticker: 005930.KS"]),
];

const RISK_BEATS: &[Beat] = &[
    Beat::new("covering the weakest cells costs refresh time and power", BEAT_MS)
        .note(
            "Retention varies from cell to cell, and the refresh window has to cover the weakest cells. Every row pays for that, in time and in power.",
            "A green refresh sweeps across the rows, and the meter on the left climbs. The meter is illustrative, not a measurement.",
        )
        .detail("The whole chip runs at the pace of its worst cells.", &["The refresh window has to cover the weakest cells"]),
    Beat::new("refresh blocks memory access while it runs", BEAT_MS)
        .note(
            "While a refresh runs, the bank cannot serve requests, so they have to wait. That slows the whole system.",
            "A pink gate rises, and cyan requests bunch up behind it until the sweep ends and the gate drops.",
        )
        .detail("The bank does no other work until the refresh finishes.", &["Refresh blocks access to the bank while it runs (HiRA, arXiv 2209.10198, p. 1)"]),
    Beat::new("RowHammer: hammering one row leaks charge into its neighbours", BEAT_MS)
        .note(
            "Rapidly activating one row can leak charge into the rows beside it. It is both a reliability risk and a security risk.",
            "We look along the rows from the end. The yellow row flickers as it is activated, and the pink rows on each side lose height.",
        )
        .detail("The neighbours lose charge without ever being accessed themselves.", &["Rapid activation of one row can leak charge into its neighbours (RowHammer)"]),
];

zoom_scene_impl!(SecBit, BIT_BEATS, CellZoom::Bit);
zoom_scene_impl!(SecParts, PARTS_BEATS, CellZoom::Parts);
zoom_scene_impl!(SecOrder, ORDER_BEATS, CellZoom::Order);
zoom_scene_impl!(SecCommands, CMD_BEATS, CellZoom::RefreshCmds);
zoom_scene_impl!(SecRetention, RETENTION_BEATS, CellZoom::Retention);
zoom_scene_impl!(SecNumbers, NUMBERS_BEATS, CellZoom::Numbers);
zoom_scene_impl!(SecSwing, SWING_BEATS, CellZoom::Swing);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, CellZoom::Makers);
zoom_scene_impl!(SecRisks, RISK_BEATS, CellZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecBit),
    || Box::new(SecParts),
    || Box::new(SecOrder),
    || Box::new(SecCommands),
    || Box::new(SecRetention),
    || Box::new(SecNumbers),
    || Box::new(SecSwing),
    || Box::new(SecMakers),
    || Box::new(SecRisks),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(beat: usize, local: f32) -> Time {
        Time {
            ms: 0,
            beat,
            local,
            beat_start: 0,
        }
    }

    fn scenes() -> Vec<(&'static str, Box<dyn Scene>)> {
        let mut v: Vec<(&'static str, Box<dyn Scene>)> = vec![("overview", Box::new(MemCell))];
        for (name, mk) in [
            ("a", (ZOOMS[0].build)()),
            ("b", (ZOOMS[1].build)()),
            ("c", (ZOOMS[2].build)()),
            ("d", (ZOOMS[3].build)()),
            ("e", (ZOOMS[4].build)()),
        ] {
            v.push((name, mk));
        }
        const NAMES: [&str; 9] = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
        for (name, mk) in NAMES.into_iter().zip(SECTIONS) {
            v.push((name, mk()));
        }
        v
    }

    #[test]
    fn every_frame_is_a_picture_that_moves() {
        for (name, scene) in scenes() {
            let p = Player::new(scene, Instant::now());
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(397) {
                let t = p.time_at(ms);
                let img = p.pixels(&t, 160, 90).expect("pixel frame");
                assert_eq!(img.dimensions(), (160, 90), "{name}");
                seen.insert(img.into_raw());
            }
            assert!(seen.len() > 12, "{name}: {} distinct frames", seen.len());
        }
    }

    #[test]
    fn overview_shows_the_story_by_beat() {
        assert_eq!(sa_state(&at(0, 0.5)), "idle");
        assert_eq!(sa_state(&at(SENSE, 0.5)), "latching");
        assert_eq!(sa_state(&at(REFRESH, 0.5)), "read+rewrite");
        assert_eq!(wl(&at(RISE, 1.0)), 1.0);
        assert_eq!(wl(&at(0, 0.5)), 0.0);
        assert!(bl(&at(SENSE, 1.0)) > 0.99);
        assert!(cap(&at(LEAK, 1.0)) < 0.9);
    }

    /// A scene's text and its picture must agree on how many beats there are, or the
    /// picture would stick on its last beat or skip its end.
    #[test]
    fn section_beats_match_their_pictures() {
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            let z = zoom_scene(key).expect("scene");
            assert_eq!(mk().beats().len(), z.beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("CELL")
            .unwrap()
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(heads, SECTIONS.len() + 1, "one scene per section but the sources");
    }

    /// Each beat starts where the last ended, including the wrap back to the first.
    #[test]
    fn overview_state_has_no_cut_between_beats() {
        let n = BEATS.len();
        for beat in 0..n {
            let (a, b) = (at(beat, 1.0), at((beat + 1) % n, 0.0));
            let (x, y) = (cell_anim(&a), cell_anim(&b));
            for (name, p, q) in [
                ("wl", x.wl, y.wl),
                ("bl", x.bl, y.bl),
                ("cap", x.cap, y.cap),
                ("read", x.read, y.read),
                ("restore", x.restore, y.restore),
                ("leak", x.leak, y.leak),
            ] {
                assert!((p - q).abs() < 0.02, "beat {beat} {name}: {p} -> {q}");
            }
            for i in 0..3 {
                assert!((x.sa_rgb[i] - y.sa_rgb[i]).abs() < 0.02, "beat {beat} sense amp colour");
            }
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_cell_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_cell_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else {
            return;
        };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for (name, scene) in scenes() {
            let beats = scene.beats().len();
            let p = Player::new(scene, Instant::now());
            for beat in 0..beats {
                for (k, local) in [0.25_f32, 0.6].into_iter().enumerate() {
                    let t = at(beat, local);
                    // the overview fills a whole popup, so check it at that size
                    let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                    let img = p.pixels(&t, w, h).expect("pixel frame");
                    img.save(dir.join(format!("{name}_{beat}_{k}.png"))).unwrap();
                }
            }
        }
    }

    #[test]
    fn beats_have_text_for_the_popup() {
        let all = BEATS
            .iter()
            .chain(CAP_BEATS)
            .chain(READ_BEATS)
            .chain(REFRESH_BEATS)
            .chain(SHRINK_BEATS)
            .chain(LAYOUT_BEATS)
            .chain(BIT_BEATS)
            .chain(PARTS_BEATS)
            .chain(ORDER_BEATS)
            .chain(CMD_BEATS)
            .chain(RETENTION_BEATS)
            .chain(NUMBERS_BEATS)
            .chain(SWING_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISK_BEATS);
        for b in all {
            assert!(!b.caption.is_empty());
        }
    }
}
