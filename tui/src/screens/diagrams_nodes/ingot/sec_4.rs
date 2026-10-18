// INGOT section 4: the 300 mm wafer in numbers, drawn as a wafer with its dimensions called out.
//
//   Sources  the numbers come from the page text (INGOT.txt section 4) and these reads:
//            https://en.wikipedia.org/wiki/Wafer_(electronics) (standards table: 775 um, 125 g, 640 dies)
//            https://www.universitywafer.com/300mm-silicon-wafers.html (300 +/- 0.2 mm, <110> +/- 1 deg)
//            https://svmi.com/wp-content/uploads/2020/09/SV027.pdf (300 +/- 0.20 mm, 775 +/- 25 um;
//              the PDF itself could not be parsed, so these values come from a search snippet)
//            notch depth 1.0 mm (+0.25/-0.00) and 90 deg angle: vendor sheet SV025 search snippet
//              (https://svmi.com/wp-content/uploads/2020/09/SV025.pdf), PDF not parsed
//            SEMI M1 governs polished wafers; the M1 PDF was not read (draft 5441 seen in search only).
//   Drawings are schematic: the wafer is not to scale in thickness, and the die grid is illustrative.

use crate::ui::anim::shapes::fill_ellipse;
use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

// wafer ellipse in cells: terminal cells are about twice as tall as wide
const RX: i32 = 18;
const RY: i32 = 8;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Wafer centre column and row.
fn centre(h: i32) -> (i32, i32) {
    (40, h / 2 - 2)
}

/// Blank a V-shaped notch into the bottom rim of the wafer.
fn cut_notch(c: &mut Canvas, cx: i32, rim: i32) {
    for y in rim - 2..=rim {
        let half = (y - (rim - 2)).max(0);
        for dx in -half..=half {
            c.put(cx + dx, y, ' ');
        }
    }
}

/// Die grid inside the wafer, cells that fall inside the circle, lit up to `frac`.
fn dies(c: &mut Canvas, cx: i32, cy: i32, frac: f32) {
    let total = ((RY * 2 + 1) * (RX * 2 + 1)) as f32;
    let mut seen = 0.0_f32;
    for y in cy - RY + 1..cy + RY {
        for x in cx - RX + 1..cx + RX {
            if x % 3 != 0 || y % 2 != 0 {
                continue;
            }
            let dx = (x - cx) as f32 / RX as f32;
            let dy = (y - cy) as f32 / RY as f32;
            if dx * dx + dy * dy > 0.82 {
                continue;
            }
            seen += 1.0;
            if seen / total <= frac {
                c.put(x, y, '▪');
            }
        }
    }
}

pub struct Wafer;

const BEATS: &[Beat] = &[
    Beat::new("a 300 mm wafer is 300 mm across, +/- 0.2 mm", BEAT_MS)
        .note(
            "The wafer is a flat disc. Its diameter is set to 300 mm, held to a tolerance of +/- 0.2 mm.",
            "A disc, then the dimension line spanning it across the middle, with the tolerance under it.",
        )
        .detail(
            "Diameter is the size everything else on the line is built to. Tools and carriers are made for 300 mm.",
            &[
                "300 mm, +/- 0.2 mm (universitywafer, MSE, SVMI SV027 sheet)",
                "The 300 mm size is the one this INGOT is ground to (section 1)",
                "Wafer size ladder and 450 mm history are sections 5 and 6",
            ],
        ),
    Beat::new("the wafer is about 775 um thick, +/- 25 um", BEAT_MS)
        .note(
            "Seen edge-on, the wafer is a thin slab. Its thickness is about 775 um, with a tolerance of +/- 25 um.",
            "A slab seen from the side, with a bracket on its edge marking the thickness (schematic, not to scale).",
        )
        .detail(
            "Thickness is set by the wire saw pitch plus kerf, and the wafer is then ground and polished to it.",
            &[
                "775 um, introduced 1999 (Wikipedia standards table)",
                "+/- 25 um (SVMI SV027 and vendor sheets; a drawing shows +/- 20 um)",
                "Slicing and kerf are in section 2 and section 3",
            ],
        ),
    Beat::new("a notch 1.0 mm deep marks <110>, and replaces the flat", BEAT_MS)
        .note(
            "The rim has one V notch at the bottom. It is 1.0 mm deep with a 90 deg angle, and marks the <110> direction.",
            "The disc with a V bit out of the bottom edge, and labels for depth, angle and orientation.",
        )
        .detail(
            "The notch tells the tools the crystal orientation, so the wafer does not need flats that waste area.",
            &[
                "Depth 1.0 mm (+0.25 / -0.00); 90 deg (vendor sheet, search snippet)",
                "Orientation <110> +/- 1 deg (universitywafer)",
                "The notch is ground along the full ingot length (section 2)",
            ],
        ),
    Beat::new("about 125 g per wafer, and about 640 dies of 100 mm2", BEAT_MS)
        .note(
            "Each wafer weighs about 125 g. Laid out as dies of 100 mm2, the ideal count is about 640 per wafer.",
            "The die grid filling the disc, lit up cell by cell (schematic grid, not the real layout).",
        )
        .detail(
            "Mass and die count are what the wafer is worth. Each one is silicon already pulled and ground.",
            &[
                "About 125 g per wafer (Wikipedia standards table)",
                "640 dies of 100 mm2, ideal count (Wikipedia standards table)",
                "The 450 mm row, 342 g and 1490 dies, is in section 6",
            ],
        ),
];

impl Scene for Wafer {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (_, h) = dims(c);
        let (cx, cy) = centre(h);
        match t.beat {
            0 => {
                // the disc, then a dimension line grows across its middle
                fill_ellipse(c, cx, cy, RX as f32, RY as f32, '░');
                let grow = ease_in_out(t.local);
                let len = (lerp(0.0, (2 * RX) as f32, grow)).round() as i32;
                let dy = cy + RY + 3;
                c.hline(cx - RX, dy, len.max(1), '─');
                if len > 2 * RX - 1 {
                    c.put(cx - RX, dy, '├');
                    c.put(cx + RX, dy, '┤');
                    c.label(cx - 8, dy + 1, "300 mm  +/- 0.2 mm");
                }
            }
            1 => {
                // edge-on slab with a thickness bracket on the right
                let grow = ease_in_out(t.local);
                let half = (RX as f32 * (0.3 + 0.7 * grow)).round() as i32;
                c.hline(cx - half, cy, 2 * half + 1, '█');
                c.hline(cx - half, cy + 1, 2 * half + 1, '█');
                let bx = cx + half + 3;
                c.put(bx, cy, '┐');
                c.put(bx, cy + 1, '┘');
                c.label(bx + 2, cy, "775 um");
                c.label(bx + 2, cy + 1, "+/- 25 um");
                c.label(cx - 12, cy + RY + 2, "schematic, not to scale");
            }
            2 => {
                // disc with the V notch cut into its bottom rim, then labelled
                fill_ellipse(c, cx, cy, RX as f32, RY as f32, '░');
                let rim = cy + RY;
                cut_notch(c, cx, rim);
                c.put(cx, rim + 1, 'V');
                let reveal = ease_in_out(t.local);
                if reveal > 0.2 {
                    c.label(cx + RX + 3, cy - 1, "depth 1.0 mm");
                    c.label(cx + RX + 3, cy, "+0.25/-0.00");
                }
                if reveal > 0.6 {
                    c.label(cx + RX + 3, cy + 1, "angle 90 deg");
                    c.label(cx + RX + 3, cy + 2, "<110> +/- 1 deg");
                }
            }
            _ => {
                // disc with die grid lighting up, then the mass and count
                fill_ellipse(c, cx, cy, RX as f32, RY as f32, '░');
                let f = ease_in_out((t.local / 0.7).clamp(0.0, 1.0));
                dies(c, cx, cy, f);
                if t.local > 0.6 {
                    c.label(cx - 14, cy + RY + 2, "about 125 g per wafer");
                    c.label(cx - 14, cy + RY + 3, "640 dies, 100 mm2 (ideal)");
                    c.label(cx - 14, cy + RY + 4, "schematic grid, not to scale");
                }
            }
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Wafer)
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
        Wafer.draw(&mut c, &time(beat, local));
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
                    Wafer.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.99, 80, 26).contains("+/- 0.2 mm"));
        assert!(at(1, 0.99, 80, 26).contains("775 um"));
        assert!(at(2, 0.99, 80, 26).contains("depth 1.0 mm"));
        assert!(at(3, 0.99, 80, 26).contains("640 dies"));
    }
}
