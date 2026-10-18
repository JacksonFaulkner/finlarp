// MELT + PULL section 9 (Sources): the source list as a checklist, one beat per source group.
//
// Each numbered source is a card. A group's cards light up in turn (blinking while named, then
// checked off), and the bar at the bottom counts the checks. Groups follow the list's order.

use crate::ui::anim::{Beat, Canvas, Scene, Time, flicker};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Grid geometry: first card row, rows of cards, card height in rows.
const GRID_Y: i32 = 3;
const ROW_H: i32 = 5;
const CARD_H: i32 = 4;
/// Share of each beat spent checking; the rest is a pause on the finished group.
const CHECK_START: f32 = 0.1;
const CHECK_SPAN: f32 = 0.8;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// One numbered entry of the Sources list, as shown on its card.
struct Source {
    title: &'static str,
    line: &'static str,
}

/// Cards in list order, two per row, so each group is a contiguous run.
const SOURCES: &[Source] = &[
    Source {
        title: "[1] COMSOL",
        line: "furnace thermal analysis",
    },
    Source {
        title: "[4] Journal study, 2023",
        line: "300 mm pull-rate simulation",
    },
    Source {
        title: "[3] US patents",
        line: "neck rate, 100 kg limit",
    },
    Source {
        title: "[2] Wikipedia",
        line: "Czochralski method",
    },
    Source {
        title: "[8] Wikipedia",
        line: "Wafer (electronics)",
    },
    Source {
        title: "[5] Wafer shares",
        line: "reportprime",
    },
    Source {
        title: "[6] SEMI 2023",
        line: "revenue and shipments",
    },
    Source {
        title: "[7] Omdia 2020",
        line: "shares via KED Global",
    },
];

/// Beat groups: label, then the [start, end) run of SOURCES it covers.
const GROUPS: &[(&str, usize, usize)] = &[
    ("model and simulation", 0, 2),
    ("patents", 2, 3),
    ("general reference", 3, 5),
    ("market data", 5, 8),
];

const BEATS: &[Beat] = &[
    Beat::new(
        "model and simulation sources: the COMSOL furnace model and the 2023 pull-rate study",
        BEAT_MS,
    )
    .note(
        "Two cards cover the modelled numbers. [1] is COMSOL's thermal analysis of a Czochralski furnace; [4] is a journal study of a 300 mm pull-rate simulation.",
        "Cards [1] and [4] light up in turn, each one checked off once named.",
    )
    .detail(
        "Several figures on the page are tagged as model or study results, so they trace back to these two cards.",
        &[
            "[1] COMSOL, Thermal Analysis of a Czochralski Crystal Growth Furnace",
            "[4] 300 mm pull-rate simulation: Journal of Synthetic Crystals 52(4) 562 (2023)",
            "Model numbers on the page are tagged (model) (page text)",
        ],
    ),
    Beat::new(
        "patent sources: the neck rate and the 100 kg limit are named against patent texts",
        BEAT_MS,
    )
    .note(
        "Card [3] groups the patents cited for the dash neck: the neck pull rate and the roughly 100 kg limit on dash-necked crystals.",
        "Card [3] lights up, with the three patent numbers it lists.",
    )
    .detail(
        "The neck rate and the 100 kg limit both come from patent texts, so those are the claims to trace back to a patent.",
        &[
            "US 6,866,713: dash neck pulled to about 6 mm/min, limit about 100 kg",
            "US 5,578,284 is listed with it; it is cited for a slower neck method",
            "US 7,179,330 is listed with it; it is cited for the dash-free neck",
        ],
    ),
    Beat::new(
        "general reference: the Czochralski method and the wafer entry, both on Wikipedia",
        BEAT_MS,
    )
    .note(
        "Cards [2] and [8] are general reference: an encyclopedia entry on the Czochralski method and one on wafers.",
        "Cards [2] and [8] light up in turn, each one checked off once named.",
    )
    .detail(
        "The page cites Wikipedia for a few broad figures. Where the sources differ, the page says so.",
        &[
            "[2] Wikipedia, Czochralski method",
            "[8] Wikipedia, Wafer (electronics)",
            "Wikipedia is cited for 1425 C and about 1e18 oxygen per cm3 (page text)",
        ],
    ),
    Beat::new(
        "market sources: wafer shares, SEMI 2023 revenue and shipments, and Omdia 2020 shares",
        BEAT_MS,
    )
    .note(
        "Cards [5], [6] and [7] cover the market side: a wafer-share page, SEMI 2023 revenue and shipments, and Omdia 2020 shares via KED Global.",
        "Cards [5], [6] and [7] light up in turn, and the bar at the bottom fills to all eight.",
    )
    .detail(
        "These are market figures, not process figures. The years differ (2020 and 2023), so they should not be read as one period.",
        &[
            "[5] Wafer shares, reportprime",
            "[6] SEMI 2023 revenue and shipments, via a substack post",
            "[7] Omdia 2020 shares, via KED Global",
        ],
    ),
];

#[derive(Clone, Copy, PartialEq)]
enum State {
    Idle,
    Active,
    Checked,
}

/// Where card `i` stands at this moment of the current beat.
fn state_of(i: usize, t: &Time) -> State {
    let (start, end) = match GROUPS.get(t.beat) {
        Some(&(_, s, e)) => (s, e),
        None => return State::Checked,
    };
    if i < start {
        return State::Checked;
    }
    if i >= end || t.local < CHECK_START {
        return State::Idle;
    }
    // the group's cards are named one after another across the check span
    let p = ((t.local - CHECK_START) / CHECK_SPAN).clamp(0.0, 1.0);
    let step = p * (end - start) as f32;
    let k = (i - start) as f32;
    if step < k {
        State::Idle
    } else if step < k + 1.0 {
        State::Active
    } else {
        State::Checked
    }
}

fn fit(s: &str, n: i32) -> String {
    s.chars().take(n.max(0) as usize).collect()
}

/// One card. Idle is a light border, active a double border with a marker, checked a heavy border and a tick.
fn card(c: &mut Canvas, x: i32, y: i32, w: i32, src: &Source, state: State, t: &Time) {
    let (tl, tr, bl, br, hz, vt) = match state {
        State::Idle => ('┌', '┐', '└', '┘', '─', '│'),
        State::Active => ('╔', '╗', '╚', '╝', '═', '║'),
        State::Checked => ('┏', '┓', '┗', '┛', '━', '┃'),
    };
    c.hline(x + 1, y, w - 2, hz);
    c.hline(x + 1, y + CARD_H - 1, w - 2, hz);
    c.vline(x, y + 1, CARD_H - 2, vt);
    c.vline(x + w - 1, y + 1, CARD_H - 2, vt);
    c.put(x, y, tl);
    c.put(x + w - 1, y, tr);
    c.put(x, y + CARD_H - 1, bl);
    c.put(x + w - 1, y + CARD_H - 1, br);
    c.text(x + 2, y + 1, &fit(src.title, w - 4));
    c.text(x + 2, y + 2, &fit(src.line, w - 4));
    match state {
        State::Active => {
            if flicker(t.ms, 300, 4, 2) != 0 {
                c.put(x - 2, y + 1, '▸');
            }
        }
        State::Checked => c.put(x + w - 3, y, '✓'),
        State::Idle => {}
    }
}

pub struct Section;

impl Scene for Section {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let cw = ((w - 8) / 2).clamp(24, 44);
        let cols = [2, w - 2 - cw];
        let mut checked = 0;
        for (i, src) in SOURCES.iter().enumerate() {
            let state = state_of(i, t);
            if state == State::Checked {
                checked += 1;
            }
            let x = cols[i % 2];
            let y = GRID_Y + (i as i32 / 2) * ROW_H;
            card(c, x, y, cw, src, state, t);
        }
        let group = GROUPS.get(t.beat).map_or("all sources", |g| g.0);
        c.text(2, 1, &format!("checking: {group}"));
        // progress bar: one step per checked source
        let total = SOURCES.len() as i32;
        let bar = 40;
        let filled = checked * bar / total;
        c.text(2, h - 2, &format!("checked {checked} of {total}"));
        c.hline(22, h - 2, filled, '█');
        c.hline(22 + filled, h - 2, bar - filled, '░');
    }
}

pub fn build() -> Box<dyn Scene> {
    Box::new(Section)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn beats_are_captioned_and_grouped() {
        let s = build();
        assert!(s.beats().len() >= 3);
        assert_eq!(s.beats().len(), GROUPS.len());
        for (i, b) in s.beats().iter().enumerate() {
            assert!(
                !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
        // groups cover every source once, in order
        let mut next = 0;
        for &(_, start, end) in GROUPS {
            assert_eq!(start, next);
            assert!(end > start);
            next = end;
        }
        assert_eq!(next, SOURCES.len());
    }

    #[test]
    fn draws_at_sizes_and_times_without_panicking() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(build(), Instant::now());
            p.fit(w, h);
            for ms in [0, BEAT_MS / 2, 3 * BEAT_MS + BEAT_MS - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }

    #[test]
    fn cards_light_up_and_check_off() {
        let mut p = Player::new(build(), Instant::now());
        p.fit(120, 38);
        assert!(at(&mut p, 0, 0.5).contains("checking: model and simulation"));
        assert!(at(&mut p, 0, 0.5).contains("[1] COMSOL"));
        assert!(at(&mut p, 1, 0.5).contains("[3] US patents"));
        assert!(at(&mut p, 2, 0.9).contains("[8] Wikipedia"));
        // the last beat ends with every source checked off
        let last = at(&mut p, 3, 0.99);
        assert_eq!(last.matches('✓').count(), SOURCES.len());
        assert!(last.contains("checked 8 of 8"));
        // the first beat has checked nothing yet
        assert_eq!(at(&mut p, 0, 0.05).matches('✓').count(), 0);
    }
}
