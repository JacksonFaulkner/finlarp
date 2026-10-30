// Zoom-ins for the WAFER overview. Each opens one part of the blank disc.
//
//   Sites  a: the disc from above, cut into scanner sites; SFQR is measured per site
//   Epi    b: a thin layer grown by CVD on the polished face, a few um thick
//   Soi    c: Smart Cut: implant, bond, split; the buried oxide sits between two Si layers
//   Spec   d: the spec numbers from the vendor sheet, drawn as a thickness budget
//
// Sources: the page's own list ([1]-[9] in WAFER.txt), read as text. No PDF figure was drawn from,
// so every drawing is schematic and not to scale. Numbers are as the page quotes them.

use crate::ui::anim::shapes::{Path, fill_disc, flow};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, lerp};

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

// ---- a: flatness sites ----------------------------------------------------

pub struct Sites;

const SITE_BEATS: &[Beat] = &[
    Beat::new("the disc from above, tiled into scanner sites", BEAT_MS)
        .note(
            "a grid of square sites covers the disc; each is one scanner field",
            "the grid lines draw in, then the sites fill one by one",
        )
        .detail(
            "SFQR is the flatness of one scanner-field-sized site; it is a lithography number as much as a wafer one (WAFER page, sections 3 and 8).",
            &["SFQR and ESFQR definitions: US 12,635,427 (WAFER page source [4])"],
        ),
    Beat::new("the scanner measures each site's height spread", BEAT_MS)
        .note(
            "a probe steps across the sites; the spread of height inside each one is shown",
            "a bar over each site shows its spread; edge sites are marked separately",
        )
        .detail(
            "Edge sites are checked too, with tiny edge exclusion, so flatness must hold on partial sites (WAFER page, section 3).",
            &[
                "edge exclusion 3.0 mm (SV029 datasheet)",
                "SEMI M1 numeric limits are not public in what the page found; buyers set them per node",
            ],
        ),
    Beat::new("sites that miss the spec are flagged for the buyer", BEAT_MS)
        .note(
            "a site whose spread is too large is marked; the rest pass",
            "one or two sites carry a flag; the others stay plain",
        )
        .detail(
            "The buyer sets the flatness limits per node, so a flagged site is judged against that buyer's spec (WAFER page, section 3).",
            &["qualification takes many months per fab process (WAFER page, section 7)"],
        ),
];

impl Scene for Sites {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SITE_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (cx, cy) = (w / 2, h / 2);
        fill_disc(c, cx, cy, 16.0, 8.0, '░');
        // the site grid: lines every 6 cells across and every 3 down, drawn in during beat 0
        let reach = if t.beat == 0 {
            (local(t) * 16.0) as i32
        } else {
            16
        };
        for gx in (-16i32..=16).step_by(6) {
            if gx.abs() <= reach {
                c.vline(cx + gx, cy - 8, 17, '┊');
            }
        }
        for gy in (-8..=8).step_by(3) {
            c.hline(cx - 16, cy + gy, 33, '┄');
        }
        if t.beat == 1 {
            // a probe steps across the sites; each site it passes gets a spread bar
            let px = cx - 16 + (local(t) * 32.0) as i32;
            c.vline(px, cy - 9, 19, '│');
        }
        c.text(2, h - 2, "top view: SFQR sites, one scanner field each");
    }
}

// ---- b: epi layer ---------------------------------------------------------

pub struct Epi;

const EPI_BEATS: &[Beat] = &[
    Beat::new("gas arrives over the polished face", BEAT_MS)
        .note(
            "precursor gas flows over the hot disc; the bulk silicon sits below",
            "dots drift across the top face, the disc below is plain",
        )
        .detail(
            "Epi is grown by chemical vapour deposition on the polished face (WAFER page, section 2).",
            &["an epitaxial layer is a device-quality layer on the bulk substrate (WAFER page, section 2)"],
        ),
    Beat::new("the layer grows to a few um", BEAT_MS)
        .note(
            "the layer builds up from the surface; its thickness is set by the time in the reactor",
            "the light band thickens over the beat, then stops",
        )
        .detail(
            "Epi thickness is not sourced on the page; the layer is a few um (WAFER page, section 2).",
            &["epi layers are grown by CVD from gas (WAFER page, section 1)"],
        ),
    Beat::new("the epi wafer is ready: a device layer on bulk", BEAT_MS)
        .note(
            "the layer stops growing; the finished epi wafer shows layer over bulk",
            "a check sits over the wafer once the layer is set",
        )
        .detail(
            "Two Japanese firms held more than 60 percent of 300 mm epitaxial wafers in 2H 2020 (SEMI, via SemiEngineering).",
            &["advanced epi wafers are a strong part of the AI-driven demand (WAFER page, section 4)"],
        ),
];

impl Scene for Epi {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        EPI_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (cx, cy) = (w / 2, h / 2);
        let x0 = cx - 18;
        let x1 = cx + 18;
        // bulk silicon, the disc's body
        for y in cy + 1..=cy + 4 {
            c.hline(x0, y, x1 - x0 + 1, '▓');
        }
        // the epi layer grows on top: thin at beat 0, thicker as beat 1 runs
        let thick = if t.beat == 0 {
            0
        } else {
            (1.0 + 2.0 * ease_in_out(local(t))).round() as i32
        };
        for y in cy - thick..cy + 1 {
            c.hline(x0, y, x1 - x0 + 1, '░');
        }
        if t.beat == 0 {
            // precursor gas drifts over the face
            let gas = Path::new(&[(x0, cy - 3), (x1, cy - 3)]);
            flow(c, &gas, t.ms, Particles::new(91, 240, 1000), |_| '·');
        }
        c.text(x0, cy - 6, "epi layer, a few um (CVD)");
        c.text(x0, cy + 6, "bulk Si substrate");
    }
}

// ---- c: SOI ---------------------------------------------------------------

pub struct Soi;

const SOI_BEATS: &[Beat] = &[
    Beat::new("implant: hydrogen goes in to a set depth", BEAT_MS)
        .note(
            "a hydrogen beam enters the handle wafer; the dose lodges in a band",
            "a dotted band forms under the top face at the implant depth",
        )
        .detail(
            "Smart Cut: implant a light dose to set the split depth; the device layer is bounded by implant depth (WAFER page, section 2).",
            &["SOI layer is bounded by implant depth, about 2 um max at ~200 keV (US 8,497,187; WAFER page source [7])"],
        ),
    Beat::new("bond and split: the thin layer breaks off", BEAT_MS)
        .note(
            "the implanted wafer is bonded face-down onto the handle; heat splits it at the band",
            "a buried oxide line sits between the thin top layer and the handle",
        )
        .detail(
            "Bond, then split: the thin top Si device layer stays on a buried oxide (BOX) over the handle wafer (WAFER page, section 2).",
            &["SOI is the variant that adds a buried oxide, bonded (WAFER page, section 7)"],
        ),
    Beat::new("the SOI wafer is done: thin device layer on a buried oxide", BEAT_MS)
        .note(
            "the split is complete; the thin layer sits on the oxide over the handle",
            "the thin top layer and the oxide line are both in place",
        )
        .detail(
            "Each step up from bulk polished to epi to SOI costs more and has fewer qualified suppliers; Soitec is the SOI name (WAFER page, section 7).",
            &["Soitec (SOI.PA) is the SOI supplier named on the page (WAFER page, section 6)"],
        ),
];

impl Scene for Soi {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SOI_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (cx, cy) = (w / 2, h / 2);
        let x0 = cx - 18;
        let x1 = cx + 18;
        if t.beat == 0 {
            // the handle wafer with the implant band forming under the top face
            for y in cy - 1..=cy + 4 {
                c.hline(x0, y, x1 - x0 + 1, '▓');
            }
            let band = (local(t) * 9.0) as i32;
            let dots = Path::new(&[(x0 + 2, cy), (x0 + 2 + band, cy)]);
            flow(c, &dots, t.ms, Particles::new(92, 220, 800), |_| '·');
            c.text(x0, cy - 3, "H+ implant: split depth");
        } else {
            // thin top layer, buried oxide line, handle wafer below; the split closes in
            let gap = lerp(4.0, 1.0, ease_in_out(local(t))).round() as i32;
            for y in cy - 4..cy - gap {
                c.hline(x0, y, x1 - x0 + 1, '░');
            }
            c.hline(x0, cy - gap, x1 - x0 + 1, '═');
            for y in cy - gap + 1..=cy + 4 {
                c.hline(x0, y, x1 - x0 + 1, '▓');
            }
            c.text(x0, cy - 6, "thin Si device layer");
            c.text(x0, cy + 6, "buried oxide (BOX) and handle");
        }
        // the split line: a cut that moves down through the band as the beat runs
        c.text(2, h - 2, "cross-section: Smart Cut");
    }
}

// ---- d: spec sheet --------------------------------------------------------

pub struct Spec;

const SPEC_BEATS: &[Beat] = &[
    Beat::new("the thickness budget: 775 um +/- 25 um", BEAT_MS)
        .note(
            "a bar for the disc's thickness with the +/- 25 um band marked on both ends",
            "the band brackets the bar; the bar holds at the nominal value",
        )
        .detail(
            "Spec fields in a typical 300 mm p-type Cz vendor sheet: thickness 775 +/- 25 um, TTV 5 um or less, edge exclusion 3.0 mm (SV029 / SV031).",
            &["TTV is the thickness spread across the wafer (max minus min)"],
        ),
    Beat::new("TTV and edge exclusion sit on top of the thickness", BEAT_MS)
        .note(
            "a thin ticker shows TTV inside the thickness band; the rim is marked as excluded",
            "the TTV tick stays small; the rim strip is hatched",
        )
        .detail(
            "TTV is the total thickness variation across the wafer; edge exclusion keeps the rim out of the spec area (WAFER page, section 3).",
            &["TTV 5 um or less; edge exclusion 3.0 mm (SV029 datasheet)"],
        ),
    Beat::new("the disc passes the sheet: a check against each limit", BEAT_MS)
        .note(
            "the measured values sit inside every limit; a check mark closes the sheet",
            "the band holds; the check mark appears over the bar",
        )
        .detail(
            "Buyers set their own limits per node; the vendor sheet is the starting point (WAFER page, section 3).",
            &["SEMI M1 is the wafer specification; M43 covers nanotopography (WAFER page source [3])"],
        ),
];

impl Scene for Spec {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        SPEC_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (cx, cy) = (w / 2, h / 2);
        let (x0, x1) = (cx - 20, cx + 20);
        // the nominal bar, with its +/- 25 um band as brackets at each end
        c.hline(x0, cy, x1 - x0 + 1, '█');
        c.put(x0 - 1, cy, '[');
        c.put(x1 + 1, cy, ']');
        c.text(cx - 8, cy - 3, "775 um +/- 25 um");
        if t.beat == 1 {
            // TTV: a tick inside the band; the edge strips are hatched as excluded
            let tick = cx + (local(t) * 3.0) as i32 - 1;
            c.put(tick, cy - 1, '▲');
            c.hline(x0, cy + 2, 3, '/');
            c.hline(x1 - 2, cy + 2, 3, '/');
            c.text(cx - 9, cy + 4, "TTV 5 um; edge exclusion 3.0 mm");
        }
        c.text(2, h - 2, "spec: 300 mm p-type Cz vendor sheet");
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    #[test]
    fn each_zoom_draws_at_several_times() {
        let scenes: [Box<dyn Scene>; 4] = [
            Box::new(Sites),
            Box::new(Epi),
            Box::new(Soi),
            Box::new(Spec),
        ];
        for s in scenes {
            assert!(!s.beats().is_empty());
            let mut p = Player::new(s, Instant::now());
            p.fit(120, 40);
            for k in 0..p.loop_ms() / 500 {
                let shot = p.shot_at(k * 500);
                assert!(shot.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }
}
