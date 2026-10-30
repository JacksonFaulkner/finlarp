// WAFER page overview: the polished blank disc goes through four stations in page order: the
// polished disc, an optional epi or SOI layer, inspection, then packing into a FOUP. The disc rides
// a track from station to station. Zoom-ins (a-d) open the flatness sites, the epi layer, the SOI
// bond and the spec sheet.
//
//   Disc     schematic side view; the layer and the sheen change with each station
//   Stations the boxes across the top; the disc rides the track below them
//
// Sources: see zoom.rs and the page's own list ([1]-[9] in WAFER.txt). Drawings are schematic.

use super::zoom;
use crate::ui::anim::shapes::{Path, fill_disc, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, lerp};

const MIN_W: u16 = 100;
const MIN_H: u16 = 30;
const BEAT_MS: u64 = 5200;

// stations: boxes SW columns wide, PITCH apart, from column X0; the disc rides the track below
const SW: i32 = 15;
const PITCH: i32 = 22;
const X0: i32 = 4;
const BOX_TOP: i32 = 2;
const BOX_BOT: i32 = 13;
const DISC_Y: i32 = 16;
const TRACK: i32 = 18;

const STATIONS: [&str; 4] = ["POLISHED", "EPI or SOI", "INSPECT", "PACK"];

const BEATS: &[Beat] = &[
    Beat::new("polished: a blank 300 mm disc, mirror on the top face", BEAT_MS)
        .note(
            "the blank disc, side view; a sheen sits on the mirror top face",
            "a flat disc, edges rounded, top face bright",
        )
        .detail(
            "The blank wafer is a 300 mm disc about 775 um thick, polished to a mirror finish (WAFER page, section 1).",
            &["thickness 775 +/- 25 um; TTV 5 um or less; edge exclusion 3.0 mm (SV029 datasheet)"],
        ),
    Beat::new("epi or SOI: a device layer is grown or bonded on top", BEAT_MS)
        .note(
            "a thin layer builds on the top face; the SOI variant adds a buried oxide line",
            "the layer thickens over the beat; the oxide line appears under it for SOI",
        )
        .detail(
            "Epi is grown by CVD from gas, a few um thick; SOI is bonded with a buried oxide (WAFER page, section 2).",
            &["SOI layer is bounded by implant depth, about 2 um max at ~200 keV (US 8,497,187)"],
        ),
    Beat::new("inspect: a scanner checks flatness and particles", BEAT_MS)
        .note(
            "a scan bar crosses the disc; each site it passes is measured for flatness",
            "the scan bar moves across the disc and the sites under it light up",
        )
        .detail(
            "Flatness is measured per site (SFQR) and at the edge (ESFQR); particles are counted on the surface (WAFER page, section 3).",
            &["SFQR is a lithography number as much as a wafer one (WAFER page, section 8)"],
        ),
    Beat::new("pack: discs go into a FOUP box, ready for the fab", BEAT_MS)
        .note(
            "the inspected disc drops into a FOUP; the box holds the discs in order",
            "a check mark sits above the box once the disc is sealed in",
        )
        .detail(
            "Packed in FOUP-ready boxes; a wafer is bought, not made, by almost every chipmaker (WAFER page, section 1).",
            &["five makers supply about 85 percent of the world's wafers (WAFER page, section 6)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "flatness sites across the disc",
        build: || -> Box<dyn Scene> { Box::new(zoom::Sites) },
    },
    Zoom {
        key: 'b',
        label: "an epi layer grown by CVD",
        build: || -> Box<dyn Scene> { Box::new(zoom::Epi) },
    },
    Zoom {
        key: 'c',
        label: "SOI: implant, bond, split",
        build: || -> Box<dyn Scene> { Box::new(zoom::Soi) },
    },
    Zoom {
        key: 'd',
        label: "the spec sheet",
        build: || -> Box<dyn Scene> { Box::new(zoom::Spec) },
    },
];

fn station_x(i: usize) -> i32 {
    X0 + i as i32 * PITCH
}

fn station_mid(i: usize) -> i32 {
    station_x(i) + SW / 2
}

pub struct Blank;

/// One station box with its equipment drawn inside. Station i is the step for beat i.
fn station(c: &mut Canvas, i: usize, t: &Time) {
    let x = station_x(i);
    titled_box(c, x, BOX_TOP, SW, BOX_BOT - BOX_TOP + 1, STATIONS[i]);
    let cx = x + SW / 2;
    match i {
        0 => {
            // the polishing sheen: a bright band crosses the blank disc's top face
            let sheen = Path::new(&[(x + 2, 5), (x + SW - 3, 5)]);
            flow(c, &sheen, t.ms, Particles::new(81, 200, 1100), |_| '░');
            c.text(x + 2, 11, "mirror top");
        }
        1 => {
            // the source: gas flows in over the disc; the oxide line marks SOI
            let gas = Path::new(&[(x + 2, 4), (cx, 6)]);
            flow(c, &gas, t.ms, Particles::new(82, 260, 900), |_| '·');
            c.text(x + 2, 11, "CVD or bond");
        }
        2 => {
            // the scanner: a vertical bar sweeps back and forth across the station
            let span = (SW - 4) as f32;
            let sweep = lerp(
                0.0,
                span,
                ease_in_out(0.5 + 0.5 * (t.ms as f32 / 1400.0).sin()),
            );
            c.vline(x + 2 + sweep.round() as i32, 4, 6, '│');
            c.text(x + 2, 11, "flatness, particles");
        }
        _ => {
            // the FOUP: a box with discs stacked inside, a seal line at the top
            c.boxed(x + 3, 5, SW - 6, 7);
            for y in 7..=9 {
                c.hline(x + 4, y, SW - 8, '▓');
            }
            c.text(x + 2, 11, "sealed");
        }
    }
}

/// The disc on the track. Blank in the first beat; a thin layer from epi on; it rides from the
/// previous station to this one during the first quarter of each beat.
fn disc(c: &mut Canvas, t: &Time) {
    let moved = ease_in_out((t.local / 0.25).clamp(0.0, 1.0));
    let cx = if t.beat == 0 {
        station_mid(0)
    } else {
        lerp(
            station_mid(t.beat - 1) as f32,
            station_mid(t.beat) as f32,
            moved,
        )
        .round() as i32
    };
    let (x0, x1) = (cx - 6, cx + 6);
    for y in DISC_Y - 1..=DISC_Y + 1 {
        c.hline(x0, y, x1 - x0 + 1, '▓');
    }
    match t.beat {
        // epi or SOI: the layer grows on the top face; SOI adds a buried oxide line
        1 => {
            let grow = (t.local.clamp(0.0, 1.0) * 3.0).ceil() as i32;
            c.hline(
                x0,
                DISC_Y - 2,
                x1 - x0 + 1,
                if grow > 0 { '░' } else { ' ' },
            );
            c.hline(x0, DISC_Y, x1 - x0 + 1, '═');
        }
        // inspect: the sites the scan bar passes over light up
        2 => {
            let sx = lerp(x0 as f32, x1 as f32, t.local.clamp(0.0, 1.0)).round() as i32;
            c.put(sx, DISC_Y - 2, '▼');
        }
        _ => {}
    }
    if t.beat == 3 {
        c.put(cx, DISC_Y - 4, '✓');
    }
}

impl Scene for Blank {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let w = c.width().max(MIN_W as usize) as i32;
        for i in 0..STATIONS.len() {
            station(c, i, t);
        }
        // the track the disc rides on, and a marker over the station that is active now
        c.hline(2, TRACK, w - 4, '═');
        c.put(station_mid(t.beat), BOX_BOT + 1, '▼');
        disc(c, t);
        // a ship box under the pack station
        titled_box(c, station_x(3), 20, SW, 3, "ship");
        fill_disc(c, station_mid(0), 22, 2.0, 1.0, '▒');
        c.text(
            X0,
            25,
            "▓ disc   ░ sheen or layer   ═ track   ▼ station now   │ scan bar",
        );
        c.text(
            X0,
            27,
            "next: WAFER SORT (the disc is inspected, then cut into dice)",
        );
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Blank)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    #[test]
    fn beats_are_captioned_and_explained() {
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
    fn zooms_are_keyed_a_to_d() {
        let s = build();
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
    }

    #[test]
    fn draws_at_several_sizes_and_times() {
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
