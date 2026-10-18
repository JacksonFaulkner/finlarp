// Zoom-ins for the SLICE + POLISH overview. Each opens one part of the flow.
//
//   WebSaw   a: the wire web, one slot per pass; the kerf of one cut; wire wear makes waviness
//   Lap      b: two plates and loose slurry lap both faces at once; the lapped wafer is micro-cracked below
//   Preston  c: the pad softens and wipes the surface; removal follows RR = K*P + C; pH moves the rate
//   Budget   d: where the silicon goes, using the page's thickness-budget numbers
//
// Sources: the page's own list ([1]-[8] in SLICE_POLISH.txt), read as text. No PDF figure was drawn from,
// so every drawing is schematic and not to scale. Numbers are as the page quotes them.

use crate::ui::anim::shapes::{Path, ellipse_e, fill_disc, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, flicker, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Time through the current beat, 0..1.
fn local(t: &Time) -> f32 {
    t.local.clamp(0.0, 1.0)
}

// ---- a: wire web ----------------------------------------------------------

pub struct WebSaw;

const WEB_BEATS: &[Beat] = &[
    Beat::new("one wire runs round three sawing rollers; the brick comes down", BEAT_MS)
        .note(
            "the wire loops over rollers 1, 2 and 3; the brick is lowered toward the top run",
            "the arrows show the wire moving; the brick falls to just above the wire",
        )
        .detail(
            "Multi-wire diamond saw: the wire runs over grooved guide rollers, and each pass cuts one slot in every wafer at once (page section 2).",
            &[
                "kerf: wire plus diamond layer, about 125 um today (page source [1])",
                "coolant lubricates and cools the cut; vendor claim, not verified (Junhe 2523 product page)",
            ],
        ),
    Beat::new("the brick presses the top run down by dzmax", BEAT_MS)
        .note(
            "the top run bows down under the brick; dzmax is how far it is pressed",
            "the wire bows under the brick, and the arrows keep moving along it",
        )
        .detail(
            "Wire deflection under load is what makes the cut wavy and sets thickness variation (Springer 2026; page source [3]).",
            &["the cut is made where the wire is moving through the silicon (page section 2)"],
        ),
    Beat::new("a worn wire deflects more: the faces come out wavy", BEAT_MS)
        .note(
            "the same press, with a worn wire: the bow under the brick is deeper",
            "the dzmax marker is deeper than in the last beat",
        )
        .detail(
            "Wear raises wire deflection, thickness variation and kerf (Springer 2026; page source [3]).",
            &["a worn wire is the failure the page calls the highest-value risk (page section 7)"],
        ),
    Beat::new("near the end of the cut: wafers still attached look like teeth", BEAT_MS)
        .note(
            "the sawn wafers still hang from the block like teeth, one slot between each pair",
            "the wire runs through the slots; each tooth is a wafer not yet freed",
        )
        .detail(
            "Near the end of a cut the last wafers are still held by the block, so the cut face looks like a comb (photo of a multi-wire saw; source not checked).",
            &["the page gives no kerf count per slot; each slot is one wire pass (page section 2)"],
        ),
];

/// Roller radius in cells: x is twice y, so the wheel looks round in a terminal.
const ROLL_RX: f32 = 5.0;
const ROLL_RY: f32 = 2.5;

/// A sawing roller: a filled wheel with a hollow centre, the wire runs over its rim.
fn roller(c: &mut Canvas, x: i32, y: i32) {
    fill_disc(c, x, y, ROLL_RX, ROLL_RY, '▒');
    for dy in -2..=2 {
        for dx in -4..=4 {
            if ellipse_e(x + dx, y + dy, x, y, ROLL_RX, ROLL_RY) < 0.5 {
                c.put(x + dx, y + dy, ' ');
            }
        }
    }
    c.put(x, y, '+');
}

/// How far the top run is pulled down at `x`: full `dz` under the brick centre, none past its edge.
fn sag(x: i32, cx: i32, dz: f32) -> f32 {
    dz * (1.0 - ((x - cx) as f32 / 16.0).powi(2)).max(0.0)
}

/// The wire loop as cells, in run order: the top run (sagging under the brick), round roller 2,
/// under roller 3, back up round roller 1. Each cell carries the glyph of its local slope.
fn loop_cells(cx: i32, cy: i32, dz: f32) -> Vec<(i32, i32, char)> {
    let top = cy - 4;
    let run = |dx: i32| (cx + dx, top + sag(cx + dx, cx, dz).round() as i32);
    let mut corners: Vec<(i32, i32)> = [-20, -14, -7, 0, 7, 14, 20].iter().map(|&d| run(d)).collect();
    corners.extend([
        (cx + 25, cy - 2),
        (cx + 5, cy + 6),
        (cx, cy + 8),
        (cx - 5, cy + 6),
        (cx - 25, cy - 2),
        run(-20),
    ]);
    let mut out: Vec<(i32, i32, char)> = Vec::new();
    for w in corners.windows(2) {
        let ((x0, y0), (x1, y1)) = (w[0], w[1]);
        let (dx, dy) = (x1 - x0, y1 - y0);
        let n = dx.abs().max(dy.abs()).max(1);
        // a shallow run is '─'; a steep leg leans '╲' or '╱' by its direction
        let ch = if dy.abs() * 2 <= dx.abs() {
            '─'
        } else if (dx > 0) == (dy > 0) {
            '╲'
        } else {
            '╱'
        };
        for i in 0..n {
            let x = lerp(x0 as f32, x1 as f32, i as f32 / n as f32).round() as i32;
            let y = lerp(y0 as f32, y1 as f32, i as f32 / n as f32).round() as i32;
            if out.last().is_none_or(|&(px, py, _)| (px, py) != (x, y)) {
                out.push((x, y, ch));
            }
        }
    }
    out
}

fn web_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    let dz: f32 = match t.beat {
        0 => 0.0,
        1 => 2.0 * ease_in_out(local(t)),
        _ => 3.0,
    };
    let top = cy - 4;
    // the rest line of the top run, so the press reads against it
    for x in cx - 16..=cx + 16 {
        if x % 2 == 0 {
            c.put(x, top, '·');
        }
    }
    roller(c, cx - 20, cy - 2);
    roller(c, cx + 20, cy - 2);
    roller(c, cx, cy + 6);
    // the brick: falls in beat 0 as a flat block; from beat 1 its underside follows the sagging
    // run, column by column, so it reads as pressing down on the wire
    let bottom = match t.beat {
        0 => lerp(top as f32 - 12.0, top as f32 - 2.0, ease_in_out(local(t))),
        _ => top as f32 + dz - 1.0,
    }
    .round() as i32;
    for x in cx - 14..=cx + 14 {
        let wy = top + sag(x, cx, dz).round() as i32;
        let b = match t.beat {
            0 => bottom,
            3 => wy - 4,
            _ => wy - 1,
        };
        for y in b - 4..=b {
            c.put(x, y, '▓');
        }
        // near the end of the cut, the wafers not yet freed hang from the block as teeth;
        // the slots between them are the kerf, with the wire running through
        if t.beat == 3 {
            let glyph = if (x - cx).rem_euclid(3) == 0 { '┊' } else { '▓' };
            for y in b + 1..wy {
                c.put(x, y, glyph);
            }
        }
    }
    c.text(cx - 6, bottom - 2, "silicon brick");
    if t.beat == 3 {
        c.text(cx - 17, bottom - 7, "teeth: wafers not yet freed; slots are kerf");
    }
    // the wire: horizontal along the top run, diagonal down to roller 3
    let cells = loop_cells(cx, cy, dz);
    for &(x, y, ch) in &cells {
        c.put(x, y, ch);
    }
    // flow particles run along the same cells, so they follow the wire exactly
    let pts: Vec<(i32, i32)> = cells.iter().map(|&(x, y, _)| (x, y)).collect();
    flow(c, &Path::new(&pts), t.ms, Particles::new(41, 240, 2800), |_| '▸');
    if dz > 0.0 && t.beat < 3 {
        c.put(cx, bottom - 5, '▼');
        c.text(cx - 6, bottom - 6, "dzmax");
    }
}

/// The same web from above: each wire pass runs along x, and the passes sit side by side in z.
/// The brick covers the middle of them; the passes show either side, with arrows moving along.
fn web_above(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    let half = 11;
    for k in 0..5 {
        let z = cy - 4 + 2 * k;
        c.hline(cx - half, z, 2 * half + 1, '─');
        let pass = Path::new(&[(cx - half, z), (cx + half, z)]);
        flow(c, &pass, t.ms + k as u64 * 300, Particles::new(50 + k as u64, 220, 900), |_| '▸');
    }
    fill_disc_rect(c, cx - 7, cy - 5, 15, 11, '▓');
}

/// A filled rectangle of cells.
fn fill_disc_rect(c: &mut Canvas, x: i32, y: i32, w: i32, h: i32, ch: char) {
    for yy in y..y + h {
        c.hline(x, yy, w, ch);
    }
}

impl Scene for WebSaw {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        WEB_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        c.text(2, h - 2, "SIDE: one wire on three rollers");
        c.text(57, h - 2, "FROM ABOVE: the passes");
        web_side(c, w / 2 - 14, cy, t);
        web_above(c, w - 12, cy, t);
    }
}

// ---- b: lapping -----------------------------------------------------------

pub struct Lap;

const LAP_BEATS: &[Beat] = &[
    Beat::new("the wafers sit between two plates, with slurry in the gap", BEAT_MS)
        .note(
            "side: the upper plate hangs above the wafer; top-down: the wafers ride the lower plate",
            "slurry grains flicker in the gaps; the wafers orbit in the top-down view",
        )
        .detail(
            "Lapping uses loose abrasive slurry between two plates, both faces at once; it sets flatness and parallelism (page section 3).",
            &["double-side lapping removes 80 to 200 um in total (page section 4)"],
        ),
    Beat::new("the upper plate presses down: both faces wear at once", BEAT_MS)
        .note(
            "side: the gap closes and the pressure arrows show the load; top-down: the wafers keep orbiting",
            "the upper plate drops onto the wafer; the grains keep flickering",
        )
        .detail(
            "Both faces are lapped together, so the wafer comes out flat and parallel (page section 3).",
            &["lapping stock removal: one 200-300 mm patent example is 80 um, 40 min (page section 4)"],
        ),
    Beat::new("lapped: flat and parallel, but cracked underneath", BEAT_MS)
        .note(
            "side: the wafer is flat; cracks run under its surface. top-down: flat discs",
            "short cracks sit under the surface; the wafers are flat, and no longer orbit as bright",
        )
        .detail(
            "The lapped wafer is flat and parallel but micro-cracked underneath (SLICE_POLISH.anim.txt storyboard; page section 3 on damage).",
            &["etch removes about 15-25 um after lapping (page section 4)"],
        ),
];

/// Two panels split at the middle; `row` is where the titles sit.
fn panels(c: &mut Canvas, w: i32, h: i32, row: i32, left: &str, right: &str) {
    c.vline(w / 2, row, h - row - 3, '┊');
    c.text(w / 4 - left.chars().count() as i32 / 2, row, left);
    c.text(3 * w / 4 - right.chars().count() as i32 / 2, row, right);
}

/// Side view of the lapping stack: the upper plate, the wafer, the lower plate, slurry between.
fn lap_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    let gap = match t.beat {
        0 => 4.0,
        1 => lerp(4.0, 1.0, ease_in_out(local(t))),
        _ => 1.0,
    }
    .round() as i32;
    let upper = cy - 2 - gap;
    let lower = cy + 6;
    c.hline(cx - 15, upper, 31, '═');
    c.hline(cx - 15, lower, 31, '═');
    for y in cy - 1..=cy + 1 {
        c.hline(cx - 12, y, 25, '▓');
    }
    // slurry grains in both gaps, flickering
    for i in 0..10 {
        let x = cx - 13 + i * 3;
        if flicker(t.ms, 300, 11 + i as u64, 2) == 0 {
            c.put(x, upper + 1, '·');
            c.put(x, cy - 2, '·');
            c.put(x, cy + 2, '·');
            c.put(x, lower - 1, '·');
        }
    }
    if t.beat == 1 {
        for x in [cx - 8, cx, cx + 8] {
            c.put(x, upper - 1, '▼');
        }
    }
    if t.beat == 2 {
        // micro-cracks, drawn over the wafer body
        for i in 0..5 {
            let x = cx - 10 + i * 4;
            c.put(x, cy, '╱');
            c.put(x + 1, cy + 1, '╲');
        }
    }
}

/// Top-down view of the same plate: a disc, with two wafers riding it on a circle.
fn lap_top(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    fill_disc(c, cx, cy, 11.0, 5.0, '░');
    c.put(cx, cy, '+');
    let a = t.ms as f32 / 1400.0;
    let wafer = if t.beat == 2 { '▓' } else { '█' };
    for k in 0..2 {
        let th = a + k as f32 * std::f32::consts::PI;
        let px = cx + (7.0 * th.cos()).round() as i32;
        let py = cy + (3.0 * th.sin()).round() as i32;
        fill_disc(c, px, py, 3.0, 1.5, wafer);
    }
}

impl Scene for Lap {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        LAP_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        panels(c, w, h, 5, "SIDE: plates and wafer", "TOP-DOWN: wafers on the plate");
        lap_side(c, w / 4, cy, t);
        lap_top(c, 3 * w / 4, cy, t);
    }
}

// ---- c: Preston polish ----------------------------------------------------

pub struct Preston;

const PRESTON_BEATS: &[Beat] = &[
    Beat::new("the pad sits on the wafer; abrasive grains move under it", BEAT_MS)
        .note(
            "side: the pad over the wafer, grains flowing between them; graph: removal rate at the start",
            "a soft band sits on the top of the wafer; the grains keep flowing",
        )
        .detail(
            "Polishing is chemical plus mechanical: the chemistry softens the surface and the abrasive removes it (page section 3).",
            &["the surface is softened or oxidised, then wiped off (textbook picture, page)"],
        ),
    Beat::new("pressure sets the rate: RR = K*P + C", BEAT_MS)
        .note(
            "side: the pad presses and the softened band is wiped away; graph: the marker climbs with pressure",
            "arrows press on the pad; the wipe runs left to right; the marker rises along the line",
        )
        .detail(
            "Preston's law: removal rate RR = K*P + C, with K the Preston constant, P the pressure, and C the zero-pressure term (page section 3; source [5]).",
            &["double-side polish removes 10 to 20 um in total (page section 4)"],
        ),
    Beat::new("pH moves the rate: silica, ceria, and pitting", BEAT_MS)
        .note(
            "side: the surface is polished; graph: a pH scale with the page's two markers",
            "markers at about pH 8.5 (ceria peak) and at pH 13 (pitting)",
        )
        .detail(
            "Removal rises with pH for silica slurries; pitting was seen at pH 13; ceria peaks near pH 8-9 (page section 3; source [5]).",
            &["the Preston law runs on both ends of the chip: polish and later CMP (page section 8)"],
        ),
];

/// Side view of the pad, the softened band on the wafer, and the abrasive grains between them.
fn preston_side(c: &mut Canvas, cx: i32, cy: i32, t: &Time) {
    c.hline(cx - 16, cy - 5, 33, '░');
    for y in cy - 1..=cy + 1 {
        c.hline(cx - 14, y, 29, '▓');
    }
    match t.beat {
        0 => c.hline(cx - 14, cy - 1, 29, '▒'),
        1 => {
            // the softened row is wiped away from the left as the pad presses
            c.hline(cx - 14, cy - 1, 29, '▒');
            let wiped = (ease_in_out(local(t)) * 29.0).round() as i32;
            c.hline(cx - 14, cy - 1, wiped, ' ');
            for x in [cx - 8, cx, cx + 8] {
                c.put(x, cy - 7, '▼');
            }
        }
        _ => c.hline(cx - 14, cy - 1, 29, '░'),
    }
    let grains = Path::new(&[(cx - 14, cy - 3), (cx + 14, cy - 3)]);
    flow(c, &grains, t.ms, Particles::new(77, 180, 1400), |_| '·');
}

/// Graph of removal rate against pressure: the line RR = K*P + C, with a marker at pressure `f`.
fn preston_graph(c: &mut Canvas, x0: i32, yb: i32, f: f32) {
    c.vline(x0, yb - 9, 10, '│');
    c.hline(x0, yb, 27, '─');
    c.put(x0, yb, '└');
    c.text(x0 + 1, yb - 9, "RR");
    c.text(x0 + 22, yb + 1, "P");
    for i in 0..=24 {
        let g = i as f32 / 24.0;
        c.put(x0 + 1 + i, yb - 1 - (2.0 + 6.0 * g).round() as i32, '·');
    }
    let mx = x0 + 1 + (f * 24.0).round() as i32;
    let my = yb - 1 - (2.0 + 6.0 * f).round() as i32;
    c.put(mx, my, '●');
    c.text(x0 + 1, yb + 2, "RR = K*P + C");
}

/// pH scale from 1 to 14, two cells per unit, with the page's markers.
fn ph_scale(c: &mut Canvas, x0: i32, yb: i32) {
    c.hline(x0, yb, 27, '─');
    let at = |ph: f32| x0 + ((ph - 1.0) * 2.0).round() as i32;
    c.put(at(8.5), yb - 1, '▲');
    c.text(at(8.5) - 4, yb - 2, "ceria peak");
    c.put(at(13.0), yb - 1, '▲');
    c.text(at(13.0) - 3, yb + 1, "pitting");
    c.text(x0, yb + 2, "pH 1");
    c.text(x0 + 22, yb + 2, "pH 14");
}

impl Scene for Preston {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        PRESTON_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        panels(c, w, h, 5, "SIDE: pad, grains, wafer", "GRAPH: removal vs pressure");
        preston_side(c, w / 4, cy, t);
        match t.beat {
            0 => preston_graph(c, 3 * w / 4 - 13, cy + 4, 0.0),
            1 => preston_graph(c, 3 * w / 4 - 13, cy + 4, ease_in_out(local(t))),
            _ => ph_scale(c, 3 * w / 4 - 13, cy + 4),
        }
    }
}

// ---- d: thickness budget --------------------------------------------------

pub struct Budget;

/// One bar cell is 8 um; one stack row is 25 um. Values are the page's sampled numbers.
const BAR_UM: f32 = 8.0;
const ROW_UM: f32 = 25.0;

/// (um, glyph, label) per removal, in process order.
const REMOVALS: [(f32, char, &str); 4] = [
    (125.0, '░', "kerf 125 um"),
    (80.0, '▒', "lapping 80 um"),
    (20.0, '▓', "etch 20 um"),
    (15.0, '█', "polish 15 um"),
];

const BUDGET_BEATS: &[Beat] = &[
    Beat::new("kerf: the first loss, at the saw", BEAT_MS)
        .note(
            "bars: the kerf grows first; stack: its rows are the first layer to be removed",
            "a shaded bar grows left to right; the stack builds from the top",
        )
        .detail(
            "Diamond wire kerf is about 125 um today, per the page's thickness budget (source [1]).",
            &["kerf is per wafer cut; the wire sets it (page section 2)"],
        ),
    Beat::new("lapping takes the next biggest share", BEAT_MS)
        .note(
            "bars: lapping grows after the kerf; stack: its rows are added below",
            "a second shade grows; the stack gains its rows",
        )
        .detail(
            "Double-side lapping removes 80 to 200 um; the 80 um bar is one patent example (page section 5).",
            &["the ranges are shown in parentheses on the page"],
        ),
    Beat::new("etch and polish: small, and not one wafer's history", BEAT_MS)
        .note(
            "bars: the last two shades grow; stack: the thinnest rows are added",
            "the bars do not add up to one wafer's history: each number comes from a different example",
        )
        .detail(
            "Etch removes about 15-25 um after lapping; double-side polish 10-20 um (page sections 4-5).",
            &["each number is a different patent or source; they do not close into one wafer (page caveat)"],
        ),
];

/// Horizontal bars, one per removal, on the left: a bar grows in its beat and stays after.
fn budget_bars(c: &mut Canvas, x0: i32, cy: i32, t: &Time) {
    for (i, (um, ch, label)) in REMOVALS.iter().enumerate() {
        let y = cy - 6 + 3 * i as i32;
        let full = (um / BAR_UM).round() as i32;
        let beat_for = if i < 2 { i } else { 2 };
        let len = if t.beat > beat_for {
            full
        } else if t.beat == beat_for {
            (full as f32 * ease_in_out(local(t))).round() as i32
        } else {
            0
        };
        if len == 0 {
            continue;
        }
        c.text(x0, y - 1, label);
        c.hline(x0, y, len, *ch);
    }
    c.text(x0, cy + 7, "bar: one cell = 8 um");
}

/// Stack of the removed layers, one row per 25 um, on the right: rows are added in their beat.
fn budget_stack(c: &mut Canvas, x0: i32, cy: i32, t: &Time) {
    let mut y = cy - 5;
    for (i, (um, ch, label)) in REMOVALS.iter().enumerate() {
        let rows = (um / ROW_UM).round() as i32;
        let beat_for = if i < 2 { i } else { 2 };
        let shown = if t.beat > beat_for {
            rows
        } else if t.beat == beat_for {
            (rows as f32 * ease_in_out(local(t))).round() as i32
        } else {
            0
        };
        for k in 0..shown {
            c.hline(x0, y + k, 12, *ch);
        }
        if shown > 0 {
            c.text(x0 + 14, y, label);
        }
        y += rows;
    }
    c.text(x0, cy + 7, "stack: one row = 25 um");
}

impl Scene for Budget {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BUDGET_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cy = h / 2 + 1;
        panels(c, w, h, 5, "BARS: each removal", "STACK: the removed layers");
        budget_bars(c, 4, cy, t);
        budget_stack(c, 3 * w / 4 - 12, cy, t);
        if t.beat == 2 {
            c.text(2, h - 3, "page example values; they do not close into one wafer's history");
        }
    }
}

// ---- e: 3D screen --------------------------------------------------
//
// Isometric wireframes, turning about the vertical axis with time. The axis of the ingot is
// vertical, so the wire passes are horizontal planes stacked down the brick. Schematic, not to scale.

/// A straight run between two projected cells. `ch` fixes the glyph; otherwise it follows the slope.
fn line3(c: &mut Canvas, a: (i32, i32), b: (i32, i32), ch: Option<char>) {
    let (dx, dy) = (b.0 - a.0, b.1 - a.1);
    let n = dx.abs().max(dy.abs()).max(1);
    let glyph = ch.unwrap_or(if dy.abs() * 2 <= dx.abs() {
        '─'
    } else if dx.abs() * 2 <= dy.abs() {
        '│'
    } else if (dx > 0) == (dy > 0) {
        '╲'
    } else {
        '╱'
    });
    for i in 0..=n {
        let f = i as f32 / n as f32;
        let x = lerp(a.0 as f32, b.0 as f32, f).round() as i32;
        let y = lerp(a.1 as f32, b.1 as f32, f).round() as i32;
        c.put(x, y, glyph);
    }
}

/// Project a point for a camera turned by `yaw` about the vertical axis and tipped down by `pitch`.
/// A cell is about twice as tall as wide, so x is doubled.
fn project_tilt(p: (f32, f32, f32), yaw: f32, pitch: f32, cx: i32, cy: i32) -> (i32, i32) {
    let (s, c) = yaw.sin_cos();
    let (x, y, z) = p;
    let xr = x * c + z * s;
    let zr = -x * s + z * c;
    let (sp, cp) = pitch.sin_cos();
    let yr = y * cp - zr * sp;
    ((cx as f32 + xr * 2.0).round() as i32, (cy as f32 - yr).round() as i32)
}

/// Roller centres in the x-y plane (the roller axes run along z), and their radius.
const ROLLERS: [(f32, f32); 3] = [(-14.0, 0.0), (14.0, 0.0), (0.0, -14.0)];
const ROLLER_R: f32 = 4.0;
/// Depths of the wire passes along the brick: each pass cuts one slot in it.
const WIRE_Z: [f32; 7] = [-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0];

/// One wire loop at depth `z`: the top run over rollers 1 and 2, round roller 3, and back.
fn wire_loop(z: f32) -> Vec<(f32, f32, f32)> {
    [
        (-14.0, 4.0),
        (14.0, 4.0),
        (18.0, 0.0),
        (14.0, -4.0),
        (4.0, -14.0),
        (0.0, -18.0),
        (-4.0, -14.0),
        (-14.0, -4.0),
        (-18.0, 0.0),
        (-14.0, 4.0),
    ]
    .iter()
    .map(|&(x, y)| (x, y, z))
    .collect()
}

pub struct Cut3d;

const CUT3D_BEATS: &[Beat] = &[
    Beat::new("a three-roller saw: the brick sits above the wire web", BEAT_MS)
        .note(
            "the rollers, the wire looping round them, and the brick above the top run, seen at an angle",
            "the wire passes run across the brick's underside, one per slot",
        )
        .detail(
            "The wire runs over three sawing rollers, and its top run presses on the silicon (SLICE + POLISH page; source [1]).",
            &["the rollers, passes and brick are schematic; no page source gives their size"],
        ),
    Beat::new("the brick is fed down; each pass cuts a slot", BEAT_MS)
        .note(
            "the brick comes down through the web; the wire passes cut into its bottom",
            "the brick's underside drops through the passes",
        )
        .detail(
            "Each pass cuts one slot in every wafer at once (page section 2).",
            &["kerf: wire plus diamond layer, about 125 um today (page source [1])"],
        ),
    Beat::new("spin to the side: the bottom of the brick, with its cut slots", BEAT_MS)
        .note(
            "the view turns to the side; the bottom of the brick shows a slot where each pass was",
            "the slots line up along the brick; the wires sit in them",
        )
        .detail(
            "Near the end of a cut the wafers still attached show as teeth, one slot between each pair (photo of a multi-wire saw; source not checked).",
            &["the page gives no kerf count per slot; each slot is one wire pass (page section 2)"],
        ),
];

impl Scene for Cut3d {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        CUT3D_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (cx, cy) = (w / 2, h / 2 + 3);
        let f = ease_in_out(t.local.clamp(0.0, 1.0));
        // the view: angled from the start; in beat 2 it turns to the side and levels off
        let (yaw, pitch, bottom) = match t.beat {
            0 => (0.7, 0.35, 7.0),
            1 => (0.7, 0.35, lerp(7.0, 0.0, f)),
            _ => (lerp(0.7, std::f32::consts::FRAC_PI_2, f), lerp(0.35, 0.0, f), 0.0),
        };
        let proj = |p: (f32, f32, f32)| project_tilt(p, yaw, pitch, cx, cy);

        // the rollers: a ring at each end of the roller
        for &(rx, ry) in &ROLLERS {
            for z in [-8.0, 8.0] {
                let pts: Vec<_> = (0..=16)
                    .map(|i| {
                        let th = i as f32 / 16.0 * std::f32::consts::TAU;
                        proj((rx + ROLLER_R * th.cos(), ry + ROLLER_R * th.sin(), z))
                    })
                    .collect();
                for pair in pts.windows(2) {
                    line3(c, pair[0], pair[1], None);
                }
            }
        }

        // the wire passes, each a loop in the x-y plane at its depth
        for &z in &WIRE_Z {
            let pts: Vec<_> = wire_loop(z).into_iter().map(proj).collect();
            for pair in pts.windows(2) {
                line3(c, pair[0], pair[1], Some('·'));
            }
        }

        // the brick: a box, long along z, its underside at `bottom`
        let (hx, hz, depth) = (9.0_f32, 8.0_f32, 10.0_f32);
        let mut p = [(0, 0); 8];
        for (k, cell) in p.iter_mut().enumerate() {
            let x = if k & 1 == 0 { -hx } else { hx };
            let y = bottom + if k & 2 == 0 { 0.0 } else { depth };
            let z = if k & 4 == 0 { -hz } else { hz };
            *cell = proj((x, y, z));
        }
        for k in 0..8 {
            for bit in [1, 2, 4] {
                let j = k ^ bit;
                if j > k {
                    line3(c, p[k], p[j], None);
                }
            }
        }

        // once cut, the slots sit on the underside where each wire passed
        if t.beat == 2 {
            for &z in &WIRE_Z {
                let a = proj((-hx, bottom, z));
                let b = proj((hx, bottom, z));
                line3(c, a, b, Some('░'));
            }
        }
        c.text(2, h - 2, "3D: the three-roller saw, from an angle, then from the side");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn beats_ok(s: &dyn Scene) {
        assert!(s.beats().len() >= 3);
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.caption.is_empty()
                    && !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty()
                    && b.facts.iter().all(|f| !f.is_empty()),
                "beat {i}"
            );
        }
    }

    #[test]
    fn beats_are_captioned_and_explained() {
        beats_ok(&WebSaw);
        beats_ok(&Lap);
        beats_ok(&Preston);
        beats_ok(&Budget);
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
        for build in [
            || -> Box<dyn Scene> { Box::new(WebSaw) },
            || -> Box<dyn Scene> { Box::new(Lap) },
            || -> Box<dyn Scene> { Box::new(Preston) },
            || -> Box<dyn Scene> { Box::new(Budget) },
        ] {
            for (w, h) in [(80, 26), (120, 40), (200, 60)] {
                let mut p = Player::new(build(), Instant::now());
                p.fit(w, h);
                for k in 0..p.loop_ms() / 500 {
                    let s = p.shot_at(k * 500);
                    assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                }
            }
        }
    }
}
