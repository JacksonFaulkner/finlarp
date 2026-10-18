// INGOT section 2: the rod in side view, the notch ground along it, and the wire saw that cuts it.
//
//   Crop   the as-pulled rod has seed and tail cones; crop lines are placed by measurement
//   Cones  the cones come off, the single-crystal body is kept
//   Notch  a V groove is ground along the full length of the body, marking <110>
//   Wire   the ingot is bonded to a mounting beam and lowered onto a web of diamond wire
//
// Sources (PDFs read with WebFetch):
//   US 8,256,407 B2, multi-wire saw (wire pitch, kerf and wire diameter numbers):
//     https://patents.google.com/patent/US8256407
//   US 9,873,159, diamond-coated wire saw (wire web from guide rollers, beam lowered at table speed):
//     https://patents.google.com/patent/US9873159
//   US 12,183,616, V-type notch on wafers over 200 mm (1.0 to 1.05 mm deep, 90 deg):
//     https://patents.google.com/patent/US12183616
// The rod, notch and saw drawings are schematic. The page text gives no kerf, speed or pitch
// number for 300 mm sawing, and no PDF read gave one. The 0.33 mm pitch and 0.13 mm kerf below
// come from a 150 mm test cut in US 8,256,407, not from a 300 mm process.

use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out, lerp};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

// rod in side view: seed cone, body, tail cone
const ROD_X0: i32 = 6;
const BODY_X0: i32 = 12;
const BODY_X1: i32 = 56;
const ROD_X1: i32 = 62;
const BODY_HH: i32 = 3; // body half-height in rows
const TIP_HH: i32 = 1; // cone tip half-height in rows
const ROD_CY: i32 = 11;
const CONE_DROP: i32 = 6; // how far the scrapped cones fall

// wire saw
const SAW_X0: i32 = 18; // ingot left edge
const SAW_X1: i32 = 50; // ingot right edge
const SAW_TOP: i32 = 6; // strand top row
const SAW_BOT: i32 = 20; // strand bottom row
const INGOT_H: i32 = 4;
const INGOT_Y0: i32 = 6; // ingot top row at the start of the lower
const INGOT_Y1: i32 = 13; // ingot top row once fed through the web
const STRAND_STEP: i32 = 3;
const STRANDS: i32 = 9;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// Half-height of the rod at column `x`: the cones taper to a tip, the body is flat.
fn half_h(x: i32) -> i32 {
    if x < BODY_X0 {
        let f = (x - ROD_X0) as f32 / (BODY_X0 - ROD_X0) as f32;
        lerp(TIP_HH as f32, BODY_HH as f32, f).round() as i32
    } else if x > BODY_X1 {
        let f = (x - BODY_X1) as f32 / (ROD_X1 - BODY_X1) as f32;
        lerp(BODY_HH as f32, TIP_HH as f32, f).round() as i32
    } else {
        BODY_HH
    }
}

/// The rod in side view. Cones may be dropped (scrap) by `drop` rows, shown as shaded.
fn draw_rod(c: &mut Canvas, cy: i32, drop: i32) {
    for x in ROD_X0..=ROD_X1 {
        let cone = x < BODY_X0 || x > BODY_X1;
        let dy = if cone { drop } else { 0 };
        let h = half_h(x);
        let ch = if cone && drop > 0 { '░' } else { '▓' };
        c.vline(x, cy - h + dy, 2 * h + 1, ch);
    }
}

/// Crop lines at the cone-to-body joints, drawn over the rod.
fn draw_crop(c: &mut Canvas, cy: i32) {
    for x in [BODY_X0, BODY_X1] {
        c.vline(x, cy - BODY_HH - 2, 2 * BODY_HH + 5, '┊');
    }
    c.label(BODY_X0 - 2, cy - 5, "CROP");
    c.label(BODY_X1 - 2, cy - 5, "CROP");
}

/// The notch inset from the page: V shape on the wafer rim, 90 deg, not to scale.
fn draw_notch_inset(c: &mut Canvas, x0: i32, y0: i32) {
    c.hline(x0, y0, 10, '─');
    c.put(x0 + 10, y0, '╲');
    c.put(x0 + 14, y0, '╱');
    c.hline(x0 + 15, y0, 10, '─');
    c.put(x0 + 11, y0 + 1, '╲');
    c.put(x0 + 13, y0 + 1, '╱');
    c.put(x0 + 12, y0 + 2, 'V');
    c.label(x0 - 2, y0 + 3, "notch cross-section (not to scale)");
}

/// The wire saw: rollers, one wire run, the strand web, and the ingot lowered onto it.
fn draw_saw(c: &mut Canvas, ingot_top: i32, kerf: bool) {
    // guide rollers at the top corners, one wire looped between them
    c.boxed(6, 2, 7, 3);
    c.boxed(70, 2, 7, 3);
    c.put(9, 3, '◀');
    c.put(73, 3, '▶');
    c.hline(13, 3, 57, '═');
    // the strands of the web, one per wire pitch
    for k in 0..STRANDS {
        let x = SAW_X0 + 2 + STRAND_STEP * k;
        c.vline(x, SAW_TOP, SAW_BOT - SAW_TOP, '│');
    }
    // mounting beam, then the ingot bonded under it
    c.hline(SAW_X0, ingot_top - 1, SAW_X1 - SAW_X0 + 1, '═');
    for y in ingot_top..ingot_top + INGOT_H {
        c.hline(SAW_X0, y, SAW_X1 - SAW_X0 + 1, '▓');
    }
    // kerf: each strand that has passed through the ingot leaves a gap in it
    if kerf {
        for k in 0..STRANDS {
            let x = SAW_X0 + 2 + STRAND_STEP * k;
            for y in ingot_top..ingot_top + INGOT_H {
                c.put(x, y, '┊');
            }
        }
    }
    c.label(52, 1, "guide rollers, one wire");
    c.label(SAW_X0, ingot_top - 2, "mounting beam");
    c.label(SAW_X0 - 2, SAW_BOT + 1, "wire pitch sets wafer thickness + kerf");
}

const BEATS: &[Beat] = &[
    Beat::new(
        "the as-pulled rod: seed cone and tail cone at each end, crop lines placed by measurement",
        BEAT_MS,
    )
    .note(
        "The pulled crystal has a seed cone at one end and a tail cone at the other, with the body between. Crop lines are set where the cones meet the body.",
        "Crop lines ┊ fade in at the cone joints. The body is the straight run between them.",
    )
    .detail(
        "The crop is placed by measurement. A longer crop gives a cleaner body but fewer wafers.",
        &[
            "Crop lines are placed by measurement; longer crop = cleaner but fewer wafers (INGOT page, section 2)",
            "Seed cone and neck come off at the start of the pull; tail cone holds defects and impurities (INGOT page, section 2)",
        ],
    ),
    Beat::new(
        "the cones come off at the crop lines, and the body is kept",
        BEAT_MS,
    )
    .note(
        "The seed and tail cones drop away at the crop lines. Only the single-crystal body is kept for wafers.",
        "The shaded cones fall away from the body. The straight body stays.",
    )
    .detail(
        "The cones are scrap. The body is the only part that is cut into wafers.",
        &[
            "Cones off: scrap goes back as feedstock or to solar (INGOT page, storyboard)",
            "Body is the single-crystal part ground and sliced into wafers (INGOT page, section 2)",
        ],
    ),
    Beat::new(
        "a V notch is ground along the full length of the body, marking <110>",
        BEAT_MS,
    )
    .note(
        "A grinding wheel runs along the body and cuts a V groove on the rim the full length. The V marks the <110> direction.",
        "The wheel ◎ moves along the top of the body, and the groove ∨ opens behind it. The inset shows the rim section.",
    )
    .detail(
        "The notch fixes the crystal direction for every later step. Its shape and tolerance are the spec the grinder hits.",
        &[
            "V groove: 90 deg, depth 1.0 mm (+0.25 / -0.00), marks <110> (INGOT page, section 2)",
            "<110> +/- 1 degree (vendor datasheet, cited on the INGOT page)",
            "V-type notch, 1.0 to 1.05 mm deep, 90 deg, on wafers over 200 mm (US 12,183,616)",
        ],
    ),
    Beat::new(
        "the ingot is bonded to a beam and lowered through a web of diamond wire",
        BEAT_MS,
    )
    .note(
        "One wire runs over two guide rollers into a web of parallel strands. The ingot, bonded to a beam, is lowered down through the web and every strand cuts a kerf.",
        "The ingot ▓ drops onto the strands │, and each strand leaves a gap ┊ as it passes through.",
    )
    .detail(
        "The web cuts every wafer at once. The wire pitch and kerf set how thick each wafer is and how much silicon is lost.",
        &[
            "Wire web: wire fed from a spool around two guide rollers; beam lowered onto the web at table speed (US 9,873,159)",
            "Test cut: wire pitch 0.33 mm, wafer 0.2 mm, kerf allowance 0.13 mm, 0.1 mm wire, 150 mm ingot (US 8,256,407)",
            "Conventional wire pitch about 0.3 to 0.4 mm (US 8,256,407). No 300 mm kerf or speed number found",
        ],
    ),
];

struct Section;

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (_w, _h) = dims(c);
        let cy = ROD_CY;
        match t.beat {
            0 => {
                // the as-pulled rod, crop lines appear once the rod is drawn
                draw_rod(c, cy, 0);
                if t.local > 0.25 {
                    draw_crop(c, cy);
                }
                c.label(ROD_X0 - 1, cy - 6, "seed");
                c.label(ROD_X1 - 3, cy - 6, "tail");
                c.label(16, cy + 5, "single-crystal body, ground to 300 mm");
            }
            1 => {
                // cones fall off at the crop lines, the body stays
                let f = ease_in_out(t.local);
                let drop = (CONE_DROP as f32 * f).round() as i32;
                draw_rod(c, cy, drop);
                draw_crop(c, cy);
                c.label(16, cy + 5, "single-crystal body, ground to 300 mm");
                if t.local > 0.5 {
                    c.label(4, cy + 9, "scrap: feedstock or solar");
                }
            }
            2 => {
                // a grinder runs along the top of the body, cutting the V groove behind it
                draw_rod(c, cy, 0);
                let head = lerp(BODY_X0 as f32, BODY_X1 as f32, ease_in_out(t.local)).round() as i32;
                for x in BODY_X0..=head {
                    c.put(x, cy - BODY_HH, '∨');
                }
                c.put(head, cy - BODY_HH - 2, '◎');
                c.put(head, cy - BODY_HH - 1, '│');
                c.label(BODY_X0, cy - 6, "notch: V groove along full length");
                c.label(BODY_X0, cy + 5, "marks <110>, 1.0 mm deep");
                draw_notch_inset(c, 28, 20);
            }
            _ => {
                // the ingot is lowered through the strands of the wire web
                let f = ease_in_out((t.local / 0.75).clamp(0.0, 1.0));
                let top = lerp(INGOT_Y0 as f32, INGOT_Y1 as f32, f).round() as i32;
                let kerf = t.local > 0.2;
                draw_saw(c, top, kerf);
            }
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
            for beat in [0, BEATS.len() / 2, BEATS.len() - 1] {
                for local in [0.0, 0.5, 0.99] {
                    let mut c = Canvas::new(w, h);
                    Section.draw(&mut c, &time(beat, local));
                }
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        assert!(at(0, 0.9, 80, 26).contains("CROP"));
        assert!(at(1, 0.9, 80, 26).contains("scrap"));
        assert!(at(2, 0.9, 80, 26).contains("<110>"));
        assert!(at(3, 0.9, 80, 26).contains('┊'));
    }
}
