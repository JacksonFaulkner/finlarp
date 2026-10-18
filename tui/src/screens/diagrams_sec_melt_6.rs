// MELT + PULL section 6: who owns the crystal. Five 300 mm shares from one Report Prime estimate (low reliability),
// set against the other sources the page cites, then the point that each maker runs its own pullers.
//
// Sources: Report Prime, 300 mm wafer share 2024 (estimate, low reliability); Omdia 2020; Envisioning; 2023 vendor
// blurbs (as cited in the MELT + PULL page text).

use crate::ui::anim::shapes::titled_box;
use crate::ui::anim::{Beat, Canvas, Scene, Time, ease_in_out};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

/// Left label column, then the bar origin, and how many cells one percent is.
const X0: i32 = 16;
const COLS_PER_PCT: f32 = 1.5;
/// The other sources' scale: 100% spans 40 cells.
const SPAN_PER_PCT: f32 = 0.4;

const EST: &str = "300 mm share 2024: Report Prime estimate, low reliability";

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// The five shares as the page lists them, in percent.
const SHARES: [(&str, f32); 5] = [
    ("Shin-Etsu", 26.7),
    ("SUMCO", 25.0),
    ("GlobalWafers", 15.0),
    ("Siltronic", 11.7),
    ("SK Siltron", 9.2),
];

/// Short names for the puller boxes, so each fits its border.
const MAKERS: [&str; 5] = ["Shin-Etsu", "SUMCO", "GlobalWf", "Siltronic", "SK Siltron"];

/// Other sources: name, low and high share in percent, and the value label.
const OTHERS: [(&str, f32, f32, &str); 4] = [
    ("Report Prime", 77.0, 77.0, "~77% top five"),
    ("Omdia 2020", 94.0, 94.0, "94% top five"),
    ("Shin+SUMCO", 53.0, 55.0, "53-55%"),
    ("Blurbs 2023", 82.0, 85.0, "82-85% top five"),
];

fn bars(c: &mut Canvas, grow: f32, top_two: bool) {
    for (i, &(name, pct)) in SHARES.iter().enumerate() {
        let y = 3 + 2 * i as i32;
        let len = (pct * COLS_PER_PCT * grow).round() as i32;
        c.label(2, y, name);
        if len > 0 {
            let ch = if top_two && i < 2 { '▓' } else { '█' };
            c.hline(X0, y, len, ch);
        }
        c.label(X0 + len + 1, y, &format!("{pct:.1}%"));
    }
}

fn col(pct: f32) -> i32 {
    X0 + (pct * SPAN_PER_PCT).round() as i32
}

fn others(c: &mut Canvas, t: &Time) {
    for (i, &(name, lo, hi, label)) in OTHERS.iter().enumerate() {
        // rows appear one after another across the beat
        if t.local * OTHERS.len() as f32 <= i as f32 {
            continue;
        }
        let y = 3 + 2 * i as i32;
        let (a, b) = (col(lo), col(hi));
        c.label(2, y, name);
        if a == b {
            c.put(a, y, '◆');
        } else {
            c.hline(a, y, b - a + 1, '═');
            c.put(a, y, '├');
            c.put(b, y, '┤');
        }
        c.label(b + 2, y, label);
    }
    c.hline(X0, 11, 41, '─');
    c.label(X0, 12, "0%");
    c.label(X0 + 20, 12, "50%");
    c.label(X0 + 40, 12, "100%");
}

fn pullers(c: &mut Canvas, grow: f32) {
    for (i, name) in MAKERS.iter().enumerate() {
        let x = 2 + 15 * i as i32;
        let (y0, w, h) = (3, 14, 9);
        titled_box(c, x, y0, w, h, name);
        c.label(x + 3, y0 + 1, "puller");
        // the crystal grows up from the melt at the bottom of the box
        let cx = x + w / 2;
        let rows = (5.0 * grow).round() as i32;
        for k in 0..rows {
            c.hline(cx - 1, y0 + 7 - k, 3, '▓');
        }
    }
}

pub struct Owners;

const BEATS: &[Beat] = &[
    Beat::new(
        "Report Prime estimate: Shin-Etsu leads 300 mm wafer share with 26.7%, SUMCO next at 25.0%",
        BEAT_MS,
    )
    .note(
        "Five wafer makers, each with its share of the 300 mm market in 2024 according to one market-research estimate. The bars grow from the same origin, so their lengths compare directly.",
        "The five bars growing from the left, each with its percentage at the end, and the estimate label on the top row.",
    )
    .detail(
        "The shares come from a single market-research estimate that the source itself rates as low reliability. The order is indicative; do not quote the numbers as measured.",
        &[
            "Shin-Etsu 26.7%, SUMCO 25.0%, GlobalWafers 15.0% (Report Prime, page text)",
            "Siltronic 11.7%, SK Siltron 9.2% (Report Prime, page text)",
            "Report Prime estimate, low reliability (page text)",
        ],
    ),
    Beat::new(
        "the top two hold about 51.7%, but the five listed shares add to 87.6%, not the 77% quoted",
        BEAT_MS,
    )
    .note(
        "The two largest makers are shaded. Their combined share is the top-two figure. The page also gives a top-five figure, which does not match the five bars it sits under.",
        "The top two bars shaded ▓, and the two summary lines under the axis of bars.",
    )
    .detail(
        "The section's own top-five number does not agree with its own list. Use the listed shares and check the source before quoting a concentration figure.",
        &[
            "Top two: 26.7 + 25.0 = 51.7% (page text)",
            "Listed five: 26.7 + 25.0 + 15.0 + 11.7 + 9.2 = 87.6%",
            "The page gives the top five as about 77% (page text)",
        ],
    ),
    Beat::new(
        "other sources disagree: Omdia, Envisioning and 2023 vendor blurbs give different concentrations",
        BEAT_MS,
    )
    .note(
        "Each marker is a figure from another source, placed on a 0-100% scale. Single points are one figure; bars are a range between two cited figures. The spread is the point: these sources do not agree.",
        "Four rows appearing one at a time on a 0-100% axis, with the labels at the right of each marker.",
    )
    .detail(
        "The sources differ in year, market size and method, so none of these numbers can be compared directly with the Report Prime bars.",
        &[
            "Omdia 2020: top five 94% of an $11.2B market (page text)",
            "Shin-Etsu + SUMCO above 55% (2020) or about 53% (Envisioning) (page text)",
            "Top five 82-85% in 2023 (vendor blurbs, page text)",
        ],
    ),
    Beat::new(
        "each maker grows its own crystals in-house, so the puller is the capital item",
        BEAT_MS,
    )
    .note(
        "Each company gets its own puller box, and its crystal grows up from the melt. The crystal fills in as the beat plays, showing that ownership of the crystal means owning the pullers.",
        "Five puller boxes, each with a ▓ crystal growing up from its base, and the capital-item line below.",
    )
    .detail(
        "Share of wafer revenue does not show how many pullers a maker runs or what they cost. Those figures are not in this section, so none are shown.",
        &[
            "Wafer makers grow their own crystals in-house (page text)",
            "The puller is the capital item (page text)",
            "Puller cost and count are not given in the section (gap)",
        ],
    ),
];

impl Scene for Owners {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, _) = dims(c);
        // the estimate label stays on screen in every beat
        c.label(2, 0, EST);
        c.hline(0, 1, w, '─');
        match t.beat {
            0 => bars(c, ease_in_out(t.local), false),
            1 => {
                bars(c, 1.0, true);
                c.label(2, 12, "top two: 26.7 + 25.0 = 51.7%");
                c.label(
                    2,
                    13,
                    "listed five add to 87.6%; the text says top five about 77%",
                );
            }
            2 => others(c, t),
            _ => {
                pullers(c, ease_in_out(t.local));
                c.label(2, 13, "each maker grows its own crystals in-house");
                c.label(
                    2,
                    14,
                    "the puller is the capital item; its cost is not in this section",
                );
            }
        }
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Owners)
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

    fn lines_at(scene: &dyn Scene, w: u16, h: u16, t: &Time) -> String {
        let mut c = Canvas::new(w, h);
        scene.draw(&mut c, t);
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
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
    }

    #[test]
    fn draws_at_sizes_and_times_without_panicking() {
        let s = build();
        let last = s.beats().len() - 1;
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            for (beat, local) in [(0, 0.0), (1, 0.5), (2, 0.5), (last, 0.99)] {
                let out = lines_at(s.as_ref(), w, h, &time(beat, local));
                assert!(out.contains("Report Prime estimate"), "{w}x{h} beat {beat}");
            }
        }
    }

    #[test]
    fn each_beat_shows_its_story() {
        let s = build();
        assert!(lines_at(s.as_ref(), 120, 40, &time(0, 1.0)).contains("26.7%"));
        assert!(lines_at(s.as_ref(), 120, 40, &time(1, 0.5)).contains("87.6%"));
        assert!(lines_at(s.as_ref(), 120, 40, &time(2, 0.99)).contains("94% top five"));
        assert!(lines_at(s.as_ref(), 120, 40, &time(3, 0.99)).contains("puller"));
    }
}
