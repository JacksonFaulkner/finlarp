// INGOT section 3: the crystal physics behind the cuts. Four close-ups in one loop:
//
//   Orientation  the Miller index sets which atomic plane faces up: a square {100} grid
//                for standard logic / CMOS, a triangular {111} grid for bipolar, power, MEMS
//   Notch        one small notch marks <110> on 200 mm and up, where a flat wastes edge area
//   Doping       boron, phosphorus, arsenic or antimony atoms in the lattice, 1e13 to 1e16 /cm3
//   Cropping     seed and tail cones are sawn off, the ingot is ground to diameter, then sliced
//
// Sources:
//   https://patents.google.com/patent/US5529051 (read): ingot ground to diameter, (110) found by
//     X-ray and marked along the ingot, flat or notch ground to it "with a tolerance of
//     approximately 1 degree", seed and tail ends removed before slicing.
//   https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10056395 (search snippet only):
//     a <100> wafer has a (100) surface, notch along [100]; a <110> notch is along [110].
//   https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5993292 (search snippet only):
//     usual <110> orientation tolerance +/-1 degree.
//   Orientation, doping range and purity figures: from the INGOT page text (Wikipedia-attributed);
//     the Wikipedia pages were not re-read here.
//   Not read: SEMI M1 and the SV029 datasheet (no text extracted), USPTO 12617032 and 12605863.
//   Atom lattices are schematic, not to scale. Dopant and wafer slice positions are schematic.

use crate::ui::anim::motion::{hash, unit};
use crate::ui::anim::shapes::{fill_ellipse, titled_box};
use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

// lattice spacing in cells: one atom every 4 columns and every 2 rows
const DX: i32 = 4;
const DY: i32 = 2;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// One atomic layer. `tri` offsets every other row by half a spacing, giving the triangular
/// {111} arrangement; `sweep` lights the top row up to that column (the exposed plane).
fn layer(c: &mut Canvas, x0: i32, x1: i32, y0: i32, y1: i32, tri: bool, sweep: i32) {
    let mut y = y0;
    let mut k = 0;
    while y <= y1 {
        let off = if tri && k % 2 == 1 { DX / 2 } else { 0 };
        let mut x = x0 + off;
        while x <= x1 {
            let ch = if y == y0 && x <= sweep { 'O' } else { 'o' };
            c.put(x, y, ch);
            x += DX;
        }
        y += DY;
        k += 1;
    }
}

/// Beat 0: the same atoms seen as {100} (square, CMOS) and {111} (triangular, bipolar/power/MEMS).
fn orientation(c: &mut Canvas, w: i32, h: i32, t: &Time) {
    let half = w / 2;
    titled_box(c, 2, 3, half - 3, h - 8, "{100}");
    titled_box(c, half + 1, 3, w - half - 3, h - 8, "{111}");
    let lx0 = 5;
    let lx1 = half - 6;
    let rx0 = half + 4;
    let rx1 = w - 6;
    let sweep_l = lerp(lx0 as f32, lx1 as f32, ease_in_out(t.local)).round() as i32;
    let sweep_r = lerp(rx0 as f32, rx1 as f32, ease_in_out(t.local)).round() as i32;
    layer(c, lx0, lx1, 6, h - 10, false, sweep_l);
    layer(c, rx0, rx1, 6, h - 10, true, sweep_r);
    c.label(3, h - 5, "(100) faces up: standard logic, CMOS");
    c.label(half + 2, h - 5, "(111) faces up: bipolar, power, MEMS");
    c.label(3, h - 4, "Miller index set by the seed in MELT + PULL");
}

/// Beat 1: a flat (left) and a notch (right) on the wafer edge, seen from above.
fn notch(c: &mut Canvas, w: i32, h: i32, t: &Time) {
    let cy = h / 2 - 2;
    let ry = ((h - 10) / 2).min(8);
    let rx = ry * 2;
    let cl = w / 4;
    let cr = 3 * w / 4;
    fill_ellipse(c, cl, cy, rx as f32, ry as f32, '░');
    fill_ellipse(c, cr, cy, rx as f32, ry as f32, '░');

    // flat: chord cut across the bottom third, the cut-off segment is cleared
    let cut = cy + (ry as f32 * 0.7).round() as i32;
    let chord = (rx as f32 * (1.0 - 0.7f32 * 0.7).sqrt()).round() as i32;
    c.clear_rect(cl - rx - 1, cut + 1, 2 * rx + 3, ry + 2);
    c.hline(cl - chord, cut, 2 * chord + 1, '─');

    // notch: a V cut into the bottom edge, grown row by row as the grind runs
    let rows = (t.local * 4.0).floor() as i32;
    let edge = cy + ry;
    for r in 0..=3 {
        if r >= rows.max(1).min(4) {
            break;
        }
        let y = edge - 2 + r;
        c.clear_rect(cr - r, y, 2 * r + 1, 1);
    }
    c.put(cr, edge + 1, '^');
    c.label(cr + 2, edge + 1, "notch = <110>");
    c.label(cl - 6, edge + 1, "flat: wastes edge");

    c.label(3, h - 5, "~1 deg orientation tolerance (US5529051)");
    c.label(3, h - 4, "no area lost on the notched wafer");
}

/// Beat 2: dopant atoms settle into lattice sites of the melt-grown silicon.
fn doping(c: &mut Canvas, w: i32, h: i32, t: &Time) {
    let x0 = 6;
    let x1 = w - 7;
    let y0 = 5;
    let y1 = h - 10;
    layer_grid(c, x0, x1, y0, y1);
    let mut k: u64 = 0;
    let mut y = y0;
    while y <= y1 {
        let mut x = x0;
        while x <= x1 {
            let seed = hash(k, 11);
            if unit(seed) < 0.14 {
                let settle = 0.1 + 0.6 * unit(hash(k, 3));
                let f = (t.local - settle) / 0.2;
                if f >= 1.0 {
                    c.put(x, y, '@');
                } else if f >= 0.0 {
                    let fy = lerp(y0 as f32 - 2.0, y as f32, ease_in_out(f)).round() as i32;
                    c.put(x, fy, '*');
                }
            }
            k += 1;
            x += DX;
        }
        y += DY;
    }

    // concentration scale, endpoints from the page text
    let bar_y = h - 7;
    c.hline(x0, bar_y, x1 - x0 + 1, '─');
    c.label(x0, bar_y + 1, "1e13");
    c.label(x1 - 4, bar_y + 1, "1e16");
    c.label(x0 + 12, bar_y - 1, "dopant atoms/cm3");
    c.label(3, h - 4, "boron, phosphorus, arsenic, antimony added to the melt");
    c.label(3, h - 3, "purity above 99.9999%; transition metals below ppb");
}

/// Plain lattice used as the backdrop of beat 2.
fn layer_grid(c: &mut Canvas, x0: i32, x1: i32, y0: i32, y1: i32) {
    layer(c, x0, x1, y0, y1, false, -1);
}

/// Beat 3: the ingot is cropped at both cones, ground to diameter, then sliced.
fn cut_and_slice(c: &mut Canvas, w: i32, h: i32, t: &Time) {
    let bh = (h / 6).clamp(3, 6);
    let cy = h / 2 - 2;
    let xl = 14;
    let xr = w - 14;
    let cone = 8;
    let ease = ease_in_out;

    // grinding trims the oversize body from bh+1 down to bh
    let rows_body = if t.local < 0.5 {
        bh + 1
    } else {
        let g = ease(((t.local - 0.5) / 0.2).clamp(0.0, 1.0));
        lerp((bh + 1) as f32, bh as f32, g).round() as i32
    };

    // cone pieces: attached until the crop, then they drop away as scrap
    let drop = if t.local < 0.3 {
        0.0
    } else {
        lerp(0.0, 5.0, ease(((t.local - 0.3) / 0.2).clamp(0.0, 1.0)))
    };
    let scrap = if drop > 0.0 { '░' } else { '▓' };
    let sy = drop.round() as i32;
    for d in 0..=cone {
        let hw = bh * (cone - d) / cone;
        let hw = hw.max(1);
        // seed cone, left of the body
        let x = xl - cone + d;
        for y in cy - hw..=cy + hw {
            c.put(x, y + sy, scrap);
        }
        // tail cone, right of the body
        let x = xr + cone - d;
        for y in cy - hw..=cy + hw {
            c.put(x, y + sy, scrap);
        }
    }

    // body: solid silicon between the crop lines
    let body_x0 = xl;
    let body_x1 = xr;
    let slicing = t.local > 0.7;
    let wire_x = if slicing {
        lerp(body_x0 as f32, body_x1 as f32, ease(((t.local - 0.7) / 0.3).clamp(0.0, 1.0)))
            .round() as i32
    } else {
        body_x0 - 1
    };
    for x in body_x0..=body_x1 {
        let kerf = slicing && x < wire_x && (x - body_x0) % 4 == 3;
        if kerf {
            continue;
        }
        for y in cy - rows_body..=cy + rows_body {
            c.put(x, y, '▓');
        }
    }

    // crop lines at the two cut positions, shown before and while the cones drop
    if t.local < 0.3 {
        c.vline(xl, cy - bh - 2, 2 * bh + 5, ':');
        c.vline(xr, cy - bh - 2, 2 * bh + 5, ':');
    }

    // grind wheel rides over the body while it is trimmed
    if (0.5..0.7).contains(&t.local) {
        let gx = (xl + xr) / 2;
        c.label(gx - 4, cy - bh - 3, "grind wheel");
        c.put(gx, cy - rows_body - 1, 'O');
    }

    // wire saw sweeps left to right, leaving kerf gaps behind it
    if slicing {
        c.vline(wire_x, cy - bh - 2, 2 * bh + 5, '│');
        c.label(wire_x - 3, cy + bh + 3, "wire saw");
    }

    c.label(3, h - 5, "seed and tail cones cropped, then ground to 300 mm");
    c.label(3, h - 4, "slices: schematic, not to scale");
}

pub struct Section;

const BEATS: &[Beat] = &[
    Beat::new(
        "the crystal orientation sets which atom plane faces up",
        BEAT_MS,
    )
    .note(
        "Two atom grids are the same silicon cut two ways. The square face is {100}, the triangular face is {111}.",
        "Square grid o on the left for CMOS. Triangular grid o on the right for bipolar, power and MEMS.",
    )
    .detail(
        "The Miller index picks the plane that faces up. Logic and CMOS use {100}, other devices use {111}.",
        &[
            "{100} is the standard for logic and CMOS (Wikipedia, INGOT page)",
            "{111} goes to bipolar, power and MEMS (Wikipedia, INGOT page)",
            "The seed sets the orientation in MELT + PULL (INGOT page)",
        ],
    ),
    Beat::new(
        "a notch marks <110> and wastes less edge than a flat",
        BEAT_MS,
    )
    .note(
        "Seen from above, a flat cuts off a chord of the wafer edge. The notch is a small V cut into the edge.",
        "Left: a flat chord ─ and the lost sliver. Right: a V notch ^ grown into the bottom edge.",
    )
    .detail(
        "The notch marks the <110> direction and takes less space than a flat, so more of the wafer is usable.",
        &[
            "200 mm and up use one notch, not flats (INGOT page)",
            "Flat or notch set to (110) with about 1 degree tolerance (US5529051, read)",
            "The notch does not show doping type (INGOT page)",
        ],
    ),
    Beat::new(
        "dopant atoms are added to the melt at 1e13 to 1e16 per cm3",
        BEAT_MS,
    )
    .note(
        "Dopant atoms drop into the lattice and settle on sites, replacing a few silicon atoms.",
        "Silicon o in a grid. Dopant @ falls in as * and settles on a site.",
    )
    .detail(
        "Dopant sets the resistivity. The concentration is set in the melt, before the pull.",
        &[
            "Boron, phosphorus, arsenic or antimony (INGOT page)",
            "1e13 to 1e16 atoms/cm3 (INGOT page, Wikipedia)",
            "Purity above 99.9999%, transition metals below ppb (INGOT page)",
        ],
    ),
    Beat::new(
        "the seed and tail cones are cropped, the ingot is ground, then sliced",
        BEAT_MS,
    )
    .note(
        "The cones are sawn off, the oversize body is ground to a true 300 mm cylinder, then a wire saw slices it.",
        "Cone pieces drop away as scrap. A grind wheel trims the body. A wire | sweeps and leaves kerf gaps.",
    )
    .detail(
        "Cropping removes the cones and zones with voids or contamination. Grinding brings the diameter to spec. Slicing makes the wafers.",
        &[
            "Seed and tail cones removed before slicing (US5529051, read)",
            "Ingot ground to diameter before slicing (US5529051, read)",
            "Wire saw, diamond wire, then edge grind and polish (INGOT page)",
        ],
    ),
];

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        match t.beat {
            0 => orientation(c, w, h, t),
            1 => notch(c, w, h, t),
            2 => doping(c, w, h, t),
            _ => cut_and_slice(c, w, h, t),
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Section)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn time(beat: usize, local: f32) -> Time {
        Time {
            ms: beat as u64 * BEAT_MS + (local * BEAT_MS as f32) as u64,
            beat,
            local,
            beat_start: beat as u64 * BEAT_MS,
        }
    }

    fn at(beat: usize, local: f32, w: usize, h: usize) -> String {
        let mut c = Canvas::new(w as u16, h as u16);
        Section.draw(&mut c, &time(beat, local));
        c.lines().join("\n")
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        let s = build();
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
    fn draws_at_several_sizes_and_times() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            for beat in 0..BEATS.len() {
                for local in [0.0, 0.5, 0.99] {
                    let mut c = Canvas::new(w, h);
                    Section.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.5, 80, 26).contains("{111}"));
        assert!(at(1, 0.9, 80, 26).contains("notch = <110>"));
        assert!(at(2, 0.9, 80, 26).contains('@'));
        assert!(at(3, 0.2, 80, 26).contains(':'));
    }
}
