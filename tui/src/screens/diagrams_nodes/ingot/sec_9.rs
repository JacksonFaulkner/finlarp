// INGOT section 9 (Listed names): which exchange lines to look up for each wafer maker.
//
// Tickers and exchanges are general knowledge, not a fetched source, and no prices are shown.
// Checked once against a search: Siltronic trades on Xetra as WAF (ISIN DE000WAF3001), per
// Deutsche Borse's live Xetra page and Saxo. INGOT.txt lists it as SSG.DE, which does not match,
// so the board shows WAF and the page text should be corrected by its owner.
// Shin-Etsu 4063.T, SUMCO 3436.T, GlobalWafers 6488.TWO and SK Inc 034730.KS are the page's
// tickers and were not re-checked here.
// The ranking that orders the rows (Shin-Etsu and SUMCO first) is page text (section 7).

use crate::ui::anim::motion::lerp;
use crate::ui::anim::{flicker, Beat, Canvas, Scene, Time};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;
/// Table rows: first row, spacing (a frame is three rows tall), and the frame width.
const ROW_Y: i32 = 6;
const ROW_STEP: i32 = 3;
/// Column x positions inside the table.
const COL_CO: i32 = 3;
const COL_EX: i32 = 25;
const COL_TK: i32 = 40;
const COL_NOTE: i32 = 52;
/// Tape scrolls one character per this many milliseconds.
const TAPE_MS: u64 = 150;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

/// One row of the board.
struct Entry {
    company: &'static str,
    exchange: &'static str,
    ticker: &'static str,
    note: &'static str,
}

const ENTRIES: &[Entry] = &[
    Entry {
        company: "Shin-Etsu Chemical",
        exchange: "Tokyo",
        ticker: "4063.T",
        note: "#1 by share (page)",
    },
    Entry {
        company: "SUMCO",
        exchange: "Tokyo",
        ticker: "3436.T",
        note: "#2 by share (page)",
    },
    Entry {
        company: "GlobalWafers",
        exchange: "Taipei OTC",
        ticker: "6488.TWO",
        note: "Taiwan",
    },
    Entry {
        company: "Siltronic",
        exchange: "Xetra",
        ticker: "WAF",
        note: "Germany; page says SSG.DE",
    },
    Entry {
        company: "SK Siltron",
        exchange: "via parent",
        ticker: "034730.KS",
        note: "Korea; parent SK Inc",
    },
];

/// Entries lit in each beat, as [start, end) runs of ENTRIES.
const LIT: &[(usize, usize)] = &[(0, 2), (2, 4), (4, 5)];

const BEATS: &[Beat] = &[
    Beat::new(
        "Japan: Shin-Etsu (4063.T) and SUMCO (3436.T), the two largest shares",
        BEAT_MS,
    )
    .note(
        "The first two rows of the board are lit: the Tokyo listings for the two biggest wafer makers on the page.",
        "The frames draw in and a caret blinks beside each lit row. The tape along the bottom carries every ticker.",
    )
    .detail(
        "The page ranks Shin-Etsu and SUMCO first, and their combined share is above 55%. The tickers are general knowledge.",
        &[
            "Shin-Etsu + SUMCO above 55% (page text, Omdia 2020 note)",
            "4063.T Shin-Etsu Chemical, Tokyo (general knowledge, not fetched)",
            "3436.T SUMCO, Tokyo (general knowledge, not fetched)",
        ],
    ),
    Beat::new(
        "Taiwan and Germany: GlobalWafers (6488.TWO) and Siltronic (WAF on Xetra)",
        BEAT_MS,
    )
    .note(
        "The next two rows are lit. Siltronic's row carries a warning, because the page's SSG.DE does not match the Xetra listing.",
        "The frames move to the Taiwan and Germany rows. The caret blinks on the active row only.",
    )
    .detail(
        "Two listings are named here for their home markets. The Siltronic symbol was checked against an exchange page; the others were not.",
        &[
            "6488.TWO GlobalWafers, Taipei OTC (general knowledge, not fetched)",
            "WAF Siltronic on Xetra: Deutsche Borse live page, ISIN DE000WAF3001",
            "Page text gives SSG.DE for Siltronic: this does not match Xetra, so it is flagged",
        ],
    ),
    Beat::new(
        "Korea: SK Siltron has no line of its own here; its parent SK Inc (034730.KS) is the route",
        BEAT_MS,
    )
    .note(
        "The last row is lit. It is a subsidiary, so the board points at the listed parent rather than a separate ticker.",
        "The single row lights up and the tape scrolls through the full list again.",
    )
    .detail(
        "The page says SK Siltron is owned by SK Inc. Investors who want the wafer business through a listed line look at the parent.",
        &[
            "Page text: SK Siltron is owned by SK Inc, ticker 034730.KS (general knowledge)",
            "No separate SK Siltron ticker is shown on the board",
        ],
    ),
];

/// Double-line frame for an active row. The top and bottom rules grow over the beat's start.
fn frame(c: &mut Canvas, y: i32, grow: f32, fw: i32) {
    let len = lerp(0.0, fw as f32, grow) as i32;
    let x = 1;
    c.hline(x + 1, y - 1, len - 2, '═');
    c.hline(x + 1, y + 1, len - 2, '═');
    c.put(x, y - 1, '╔');
    c.put(x + fw - 1, y - 1, '╗');
    c.put(x, y + 1, '╚');
    c.put(x + fw - 1, y + 1, '╝');
    c.put(x, y, '║');
    c.put(x + fw - 1, y, '║');
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
        c.text(2, 1, "listed names: exchange lines for each maker");
        c.text(
            2,
            2,
            "tickers are general knowledge, not fetched; no prices are shown",
        );
        // table header and rule
        c.text(COL_CO, 4, "COMPANY");
        c.text(COL_EX, 4, "EXCHANGE");
        c.text(COL_TK, 4, "TICKER");
        c.text(COL_NOTE, 4, "NOTE");
        c.hline(2, 5, w - 4, '─');

        let (lo, hi) = LIT.get(t.beat).copied().unwrap_or((0, 0));
        let grow = (t.local / 0.3).clamp(0.0, 1.0);
        for (i, e) in ENTRIES.iter().enumerate() {
            let y = ROW_Y + i as i32 * ROW_STEP;
            let lit = i >= lo && i < hi;
            if lit {
                frame(c, y, grow, w - 4);
                if flicker(t.ms, 300, 4, 2) != 0 {
                    c.put(0, y, '▸');
                }
            }
            c.text(COL_CO, y, e.company);
            c.text(COL_EX, y, e.exchange);
            c.text(COL_TK, y, e.ticker);
            c.text(
                COL_NOTE,
                y,
                &e.note[..e.note.len().min((w - COL_NOTE - 2) as usize)],
            );
        }

        // tape along the bottom: every ticker, scrolled one column per TAPE_MS
        let tape: String = ENTRIES
            .iter()
            .map(|e| format!("{} {}   ", e.ticker, e.company))
            .collect();
        let chars: Vec<char> = tape.chars().collect();
        let off = (t.ms / TAPE_MS) as usize % chars.len();
        let line: String = (0..(w - 4) as usize)
            .map(|k| chars[(off + k) % chars.len()])
            .collect();
        c.hline(2, h - 5, w - 4, '─');
        c.text(2, h - 4, &line);
        c.text(2, h - 2, &format!("beat {} of {}", t.beat + 1, BEATS.len()));
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

    #[test]
    fn beats_are_captioned() {
        let s = build();
        assert!(s.beats().len() >= 3);
        assert_eq!(s.beats().len(), LIT.len());
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
        // the lit runs cover every entry once, in order
        let mut next = 0;
        for &(lo, hi) in LIT {
            assert_eq!(lo, next);
            assert!(hi > lo);
            next = hi;
        }
        assert_eq!(next, ENTRIES.len());
    }

    #[test]
    fn draws_at_sizes_and_times_without_panicking() {
        for (w, h) in [(80, 26), (120, 40), (200, 60)] {
            let mut p = Player::new(build(), Instant::now());
            p.fit(w, h);
            for ms in [0, BEAT_MS / 2, 2 * BEAT_MS + BEAT_MS - 1] {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }
}
