// BANK page: one DRAM chip's banks, drawn in 3D by poly3d, on the CELL page's template.
// The overview shows banks working in parallel: ACTIVATE bank A, ACTIVATE bank B in
// another group while A opens, READs alternating so the shared data bus stays busy,
// the four-activate window holding back a fifth ACT, a row conflict in bank A while
// bank B keeps reading, and an all-bank refresh. Each zoom (a-e) is its own 3D scene:
// a one bank, b bank groups (tCCD), c the four-activate window, d address mapping,
// e refresh (DDR4 all-bank vs DDR5 same-bank). Sections 1-9 each have one.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: see section 10 of MEM_BANK.txt. Micron, DDR5 new features white paper (2x
// banks, 2x bank groups, BL16, same-bank refresh); DDR5 SDRAM (up to 8 groups of 4
// banks); DDR4-3200 module SPD dumps (tRRD, tCCD_L, tFAW); arXiv 1607.08578 and
// 1509.03721 (address interleaving across banks).

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::BankZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 6500;
const OVERVIEW_MS: u64 = 13000;

const BEATS: &[Beat] = &[
    Beat::new("a chip is many banks sharing one command bus and one data bus", OVERVIEW_MS)
        .note(
            "A DDR4 x8 chip has 16 banks in 4 bank groups. Each bank is a full array with its own row buffer; all of them share the command bus and the data bus.",
            "Sixteen orange tiles in four framed groups, a command bus from the back and a green data bus along the middle.",
        )
        .detail(
            "Separate banks let the chip work on several rows at once, even though data leaves one burst at a time.",
            &["DDR4: 16 banks in 4 bank groups", "DDR5: 32 banks in 8 bank groups (Micron)"],
        ),
    Beat::new("ACTIVATE bank A: one bank opens a row", OVERVIEW_MS)
        .note(
            "The controller sends ACTIVATE to bank A. Its row opens into its own row buffer; the other banks are untouched.",
            "White dots run up the command bus to one bank; a bright row line appears and its stripe fills.",
        )
        .detail("Opening a row takes tRCD before it can be read (ARRAY node).", &["tRCD = 13.75 ns (DDR4-3200)"]),
    Beat::new("ACTIVATE bank B while A is still opening", OVERVIEW_MS)
        .note(
            "Bank B in another group gets its own ACTIVATE a few nanoseconds later. Both rows open at the same time: bank-level parallelism.",
            "A second bank in the next group lights its row while the first is still open.",
        )
        .detail("ACTs to different banks only need tRRD between them, far less than tRCD.", &["tRRD_S about 3.7 ns (DDR4-3200 module SPD)"]),
    Beat::new("READs alternate between A and B and the data bus stays busy", OVERVIEW_MS)
        .note(
            "With two rows open, READs can alternate between the banks. Different bank groups let READs come one burst apart, so the data bus carries data back to back.",
            "Green dots leave bank A, then bank B, along the shared data bus to the I/O.",
        )
        .detail("Across groups, READs need only tCCD_S, the length of one burst.", &["tCCD_S = 4 clocks = 2.5 ns at DDR4-3200", "tCCD_L about 5.36 ns within a group (SPD)"]),
    Beat::new("four ACTIVATEs fill the window; the fifth waits", OVERVIEW_MS)
        .note(
            "Banks C and D open too. Four ACTIVATEs now fall inside one tFAW window, so a fifth, to bank E, has to wait until the window has passed.",
            "Two more banks open; a fifth bank gets a pink frame while it waits, then opens.",
        )
        .detail("tFAW caps how fast rows can be opened, which limits activation current.", &["tFAW about 21 ns (DDR4-3200 module SPD)"]),
    Beat::new("a row conflict in bank A; bank B keeps reading", OVERVIEW_MS)
        .note(
            "A request needs a different row in bank A. Bank A has to precharge and reopen, but bank B keeps serving reads meanwhile.",
            "Bank A turns pink, its row line vanishes and reappears elsewhere; green dots keep flowing from bank B.",
        )
        .detail("A conflict costs tRP + tRCD + tCL in that bank only; other banks hide part of it.", &["Conflict 41.25 ns vs hit 13.75 ns (ARRAY node)"]),
    Beat::new("all-bank refresh: every bank closes and refreshes at once", OVERVIEW_MS)
        .note(
            "DDR4's REFRESH command works on all banks: every open row is closed, then every bank refreshes and none can be used until it finishes.",
            "The open banks flash pink, then all sixteen turn cyan together.",
        )
        .detail("DDR5 adds same-bank refresh so the other banks keep working (zoom e).", &["DDR4 refresh locks the rank; DDR5 can refresh one bank per group"]),
];

const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "one bank: its own row and states", build: || -> Box<dyn Scene> { Box::new(OneZ) } },
    Zoom { key: 'b', label: "bank groups: why alternating groups is faster", build: || -> Box<dyn Scene> { Box::new(GroupsZ) } },
    Zoom { key: 'c', label: "the four-activate window", build: || -> Box<dyn Scene> { Box::new(FawZ) } },
    Zoom { key: 'd', label: "address mapping: which bits pick the bank", build: || -> Box<dyn Scene> { Box::new(MapZ) } },
    Zoom { key: 'e', label: "refresh: all banks vs one bank per group", build: || -> Box<dyn Scene> { Box::new(RefreshZ) } },
];

/// The overview at `t`, turned by the user's `view`, with the beat's notes on it.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes { what: b.what, why: b.why, facts: b.facts };
    poly3d::render_bank_overview(t.beat, t.local as f64, view, Some(&notes), w as usize, h as usize, px::BG)
}

/// The BANK overview: banks working in parallel.
pub struct MemBank;

impl Scene for MemBank {
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
        Some(overview_frame(t, &poly3d::View::default(), w, h))
    }
    fn notes_in_picture(&self) -> bool {
        true
    }
    fn rest_point(&self) -> f32 {
        0.4
    }
}

/// The 3D scene behind zoom `key`: letters are parts of the overview, numbers the
/// page's sections.
pub fn zoom_scene(key: char) -> Option<BankZoom> {
    Some(match key {
        'a' => BankZoom::OneBank,
        'b' => BankZoom::Groups,
        'c' => BankZoom::Faw,
        'd' => BankZoom::Mapping,
        'e' => BankZoom::Refresh,
        '1' => BankZoom::Banks,
        '2' => BankZoom::Parts,
        '3' => BankZoom::Order,
        '4' => BankZoom::Rules,
        '5' => BankZoom::Conflicts,
        '6' => BankZoom::Numbers,
        '7' => BankZoom::RefreshSec,
        '8' => BankZoom::Makers,
        '9' => BankZoom::Risks,
        _ => return None,
    })
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
                Some(poly3d::render_bank_zoom(
                    $zoom,
                    t.beat,
                    t.local as f64,
                    &poly3d::View::default(),
                    w as usize,
                    h as usize,
                    px::BG,
                ))
            }
        }
    };
}

const ONE_BEATS: &[Beat] = &[
    Beat::new("idle -> ACTIVATE: the bank opens a row", BEAT_MS)
        .note("A bank is a whole array (ARRAY node). ACTIVATE opens one of its rows into its own row buffer.", "Close on one bank: a command arrives and a row line lights.")
        .detail("Each bank tracks its own open row.", &["One open row per bank"]),
    Beat::new("active: READs come from its row buffer", BEAT_MS)
        .note("While the row is open, READs take data from this bank's row buffer onto the shared data bus.", "Green dots leave the bank's stripe for the data bus.")
        .detail("Other banks can be doing other things meanwhile.", &["Data bus shared by all banks"]),
    Beat::new("PRECHARGE -> idle", BEAT_MS)
        .note("PRECHARGE closes the row and returns the bank to idle, ready for a different row.", "The bank turns pink and the row line fades.")
        .detail("Only this bank is closed; others keep their rows.", &["tRP = 13.75 ns (DDR4-3200)"]),
];

const GROUPS_BEATS: &[Beat] = &[
    Beat::new("READs within one bank group: tCCD_L apart", BEAT_MS)
        .note("Banks in a group share some circuits, so back-to-back READs in one group must wait tCCD_L, longer than a burst.", "Orange RD blocks with gaps between them.")
        .detail("About 5.36 ns at DDR4-3200, versus a 2.5 ns burst.", &["tCCD_L about 5.36 ns (module SPD)"]),
    Beat::new("READs alternating groups: one burst apart", BEAT_MS)
        .note("Alternating between groups only needs tCCD_S, which equals one burst, so READs line up back to back.", "Green and cyan RD blocks fill the lane with no gaps.")
        .detail("Bank groups were added in DDR4 to raise speed this way.", &["tCCD_S = 4 clocks = 2.5 ns at DDR4-3200"]),
    Beat::new("the gaps are idle bus time", BEAT_MS)
        .note("Every gap in the same-group lane is time the data bus carries nothing.", "Pink gap blocks fill the middle lane.")
        .detail("Controllers spread consecutive READs across groups.", &["Idle gap = tCCD_L - burst"]),
];

const FAW_BEATS: &[Beat] = &[
    Beat::new("four ACTIVATEs, tRRD apart", BEAT_MS)
        .note("ACTIVATEs to different banks need tRRD between them.", "Four orange ACT blocks step along the time axis.")
        .detail("About 3.7 ns across groups at DDR4-3200.", &["tRRD_S about 3.7 ns (module SPD)"]),
    Beat::new("the window: no more than four in tFAW", BEAT_MS)
        .note("Any tFAW window may hold at most four ACTIVATEs.", "A long pink window block grows from the first ACT.")
        .detail("Opening rows draws current; the window caps it.", &["tFAW about 21 ns (module SPD)"]),
    Beat::new("the fifth ACTIVATE waits for the window", BEAT_MS)
        .note("A fifth ACTIVATE wanted early has to wait until the first one's window ends.", "A pink 'wanted' block, then ACT 5 at the end of the window.")
        .detail("With many banks, tFAW often sets the pace, not tRRD.", &["4 x 3.7 ns = 14.8 ns < 21 ns"]),
];

const MAP_BEATS: &[Beat] = &[
    Beat::new("the address is split into row, bank, group and column", BEAT_MS)
        .note("The memory controller chooses which address bits pick the row, the bank, the bank group and the column.", "A strip of bit cubes coloured by field behind the chip.")
        .detail("The mapping is a controller design choice.", &["Common mapping puts the column bits lowest (arXiv 1509.03721)"]),
    Beat::new("consecutive addresses: the same open row", BEAT_MS)
        .note("Counting up changes only the column bits, so neighbouring addresses land in one row of one bank: row hits.", "The green column bits count; requests all go to one bank, which reads steadily.")
        .detail("Good for streaming, bad if two streams share the bank.", &["Interleaving unit is often one row (arXiv 1607.08578)"]),
    Beat::new("a stride flips the bank bits: many banks at once", BEAT_MS)
        .note("Addresses that differ in the bank bits go to different banks, which can work in parallel.", "The purple and cyan bits change; each request goes to a different bank.")
        .detail("Interleaving across banks buys bank-level parallelism.", &["Addresses are interleaved across banks and ranks (arXiv 1607.08578)"]),
];

const REFRESH_BEATS: &[Beat] = &[
    Beat::new("DDR4 all-bank refresh: the rank is blocked", BEAT_MS)
        .note("REFRESH in DDR4 refreshes every bank at once; reads waiting for any bank must wait.", "All sixteen banks turn cyan; three banks with queued reads get pink frames.")
        .detail("The whole rank is locked while it runs.", &["DDR4: entire rank locked during refresh (PCPer)"]),
    Beat::new("DDR5 same-bank refresh: one bank per group", BEAT_MS)
        .note("DDR5's REFsb refreshes the same bank in every group, one bank index at a time.", "One bank in each group turns cyan, stepping through the four.")
        .detail("The other banks stay available.", &["REFsb targets the same bank in every bank group (Micron)"]),
    Beat::new("the other banks keep serving reads", BEAT_MS)
        .note("While one bank per group refreshes, reads to the rest carry on.", "Green dots keep leaving banks that are not refreshing.")
        .detail("Refresh costs less throughput as chips get denser.", &["Drawn with 16 banks; DDR5 has 32"]),
];

const BANKS_BEATS: &[Beat] = &[
    Beat::new("one bank at a time: the bus waits", BEAT_MS)
        .note("If every request goes to one bank, each must open its row before data can flow, and the data bus sits idle meanwhile.", "One bank opens, reads, closes, then again.")
        .detail("This is the worst case.", &["One bank: serial"]),
    Beat::new("two banks overlap", BEAT_MS)
        .note("A second bank opens while the first reads, hiding part of the wait.", "Two banks cycle with their windows overlapping.")
        .detail("Bank-level parallelism.", &["ACTs to different banks: tRRD apart"]),
    Beat::new("four banks in turn: the bus stays busy", BEAT_MS)
        .note("With enough banks in flight, one is always ready to send data.", "Four banks open in a stagger and take turns on the bus.")
        .detail("This is why chips have many banks.", &["DDR4 16 banks, DDR5 32"]),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("bank: an array with its own row buffer", BEAT_MS)
        .note("Each bank keeps one open row of its own.", "One bank lights; the rest go grey.")
        .detail("See the ARRAY node for what is inside.", &["One open row per bank"]),
    Beat::new("bank group: four banks sharing circuits", BEAT_MS)
        .note("Banks are grouped; READs within a group must be further apart than across groups.", "The four group frames and one bank in each light up.")
        .detail("DDR4 has 4 groups, DDR5 8.", &["4 banks per group"]),
    Beat::new("command bus: one command at a time", BEAT_MS)
        .note("ACTIVATE, READ, PRECHARGE and REFRESH all share one command bus.", "A command runs from the back to one bank.")
        .detail("The controller has to fit every command into it.", &["One command bus per channel"]),
    Beat::new("data bus: shared by every bank", BEAT_MS)
        .note("All banks send their data on the same bus, one burst at a time.", "Green dots run along the spine.")
        .detail("Keeping it full is the controller's job.", &["Burst 8 (DDR4), 16 (DDR5)"]),
    Beat::new("I/O: the chip's data pins", BEAT_MS)
        .note("The data bus ends at the chip's pins.", "The I/O pad at the front glows.")
        .detail("BANDWIDTH takes it from here.", &["x8: 8 data pins"]),
    Beat::new("controller: decides the order", BEAT_MS)
        .note("The memory controller in the processor picks which command to send next, within all the timing rules.", "Commands leave the controller pad at the back.")
        .detail("Its ordering decides how often rows hit.", &["Controller lives in the CPU/GPU"]),
];

const ORDER_BEATS: &[Beat] = &[
    Beat::new("1. ACT bank A", BEAT_MS)
        .note("Bank A opens its row.", "A command reaches bank A and a row lights.")
        .detail("tRCD until it can be read.", &["tRCD = 13.75 ns"]),
    Beat::new("2. ACT bank B (another group)", BEAT_MS)
        .note("Bank B opens a row while A is still opening.", "Bank B lights its row too.")
        .detail("Only tRRD after A's ACT.", &["tRRD_S about 3.7 ns"]),
    Beat::new("3. READ A", BEAT_MS)
        .note("A's row buffer sends a burst.", "Green dots from bank A.")
        .detail("Data tCL after the READ.", &["tCL = 13.75 ns"]),
    Beat::new("4. READ B", BEAT_MS)
        .note("B's burst follows straight after on the bus.", "Green dots from bank B.")
        .detail("Across groups: tCCD_S apart.", &["tCCD_S = 2.5 ns"]),
    Beat::new("5. PRECHARGE both", BEAT_MS)
        .note("Both banks close their rows.", "Both banks flash pink and go idle.")
        .detail("Ready for new rows.", &["tRP = 13.75 ns"]),
];

const RULES_BEATS: &[Beat] = &[
    Beat::new("tRRD: ACTIVATE to ACTIVATE", BEAT_MS)
        .note("ACTIVATEs to different banks must be tRRD apart, longer within a group (tRRD_L) than across (tRRD_S).", "Three ACT blocks: 3.7 ns apart across groups, 5.3 ns within one.")
        .detail("DDR4-3200 module SPD values.", &["tRRD_S about 3.7 ns, tRRD_L about 5.3 ns"]),
    Beat::new("tCCD: READ to READ", BEAT_MS)
        .note("READs need tCCD between them: one burst across groups, longer within a group.", "RD blocks: back to back across groups, a gap within one.")
        .detail("Bank groups trade this rule for speed.", &["tCCD_S 2.5 ns, tCCD_L about 5.36 ns"]),
    Beat::new("tFAW: four ACTIVATEs per window", BEAT_MS)
        .note("No more than four ACTIVATEs may fall in any tFAW window.", "Four ACTs inside a long pink window.")
        .detail("A power limit on opening rows.", &["tFAW about 21 ns (SPD)"]),
];

const CONFLICT_BEATS: &[Beat] = &[
    Beat::new("requests spread over banks overlap", BEAT_MS)
        .note("Eight requests to eight banks open and read in a quick stagger.", "Banks across the chip light in turn and send data.")
        .detail("Parallel banks hide each other's waits.", &["Bank-level parallelism"]),
    Beat::new("all on one bank, different rows: each waits", BEAT_MS)
        .note("The same requests aimed at one bank, each at a new row, must precharge and reopen one by one.", "One bank flashes pink between short reads; its row line jumps each time.")
        .detail("Each costs a full row conflict.", &["Conflict: tRP + tRCD + tCL = 41.25 ns"]),
    Beat::new("reordered: same-row hits together, the rest spread", BEAT_MS)
        .note("A controller that groups same-row requests and spreads the rest across banks gets hits and parallelism.", "Bank 0 reads steadily while three other banks open and read.")
        .detail("Real controllers reorder within limits for fairness.", &["Row hits first, spread the rest"]),
];

const NUMBERS_BEATS: &[Beat] = &[
    Beat::new("DDR4: 16 banks in 4 groups", BEAT_MS)
        .note("A DDR4 x4/x8 chip has 4 bank groups of 4 banks.", "Sixteen tiles in four groups.")
        .detail("x16 parts have 2 groups of 4.", &["DDR4: 16 banks, 4 groups"]),
    Beat::new("DDR5: 32 banks in 8 groups", BEAT_MS)
        .note("DDR5 doubles both: 8 groups of 4 banks.", "Thirty-two tiles in eight groups.")
        .detail("More banks, more rows open at once.", &["DDR5: 2x banks, 2x bank groups (Micron)", "Up to 8 groups of 4 banks"]),
    Beat::new("bursts: 8 transfers on DDR4, 16 on DDR5", BEAT_MS)
        .note("DDR5 doubles the minimum burst length to 16.", "Two lanes of transfer blocks, 8 and 16 long.")
        .detail("Longer bursts keep a narrower channel full.", &["DDR5 BL16, burst chop after 8"]),
];

const REFSEC_BEATS: &[Beat] = &[
    Beat::new("DDR4 all-bank refresh blocks everything", BEAT_MS)
        .note("REFab refreshes all banks; none can be used until it ends.", "One long pink block across the first lane.")
        .detail("Block lengths are illustrative.", &["DDR4 refresh locks the rank"]),
    Beat::new("DDR5 same-bank refresh, staggered", BEAT_MS)
        .note("REFsb refreshes one bank index in every group, then the next.", "Cyan blocks step down the bank lanes.")
        .detail("One bank per group busy at a time.", &["REFsb (Micron)"]),
    Beat::new("reads carry on around it", BEAT_MS)
        .note("Reads to the other banks keep going during same-bank refresh.", "A lane of green RD blocks fills in.")
        .detail("Refresh steals less bandwidth.", &["Other banks stay available"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note("Micron makes commodity DRAM.", "The first wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["Commodity DRAM makers: Micron, SK hynix, Samsung"]),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note("SK hynix makes commodity DRAM and HBM.", "The second wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["SK hynix ticker: 000660.KS"]),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note("Samsung makes commodity DRAM and HBM.", "The third wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["Samsung ticker: 005930.KS"]),
];

const RISKS_BEATS: &[Beat] = &[
    Beat::new("interference: two cores fight over one bank", BEAT_MS)
        .note("Requests from different cores to different rows of one bank keep closing each other's rows.", "Orange and cyan streams converge on one pink bank.")
        .detail("Research partitions banks between threads to avoid it.", &["Bank partitioning (HPCA 2012)"]),
    Beat::new("tFAW caps how fast rows open", BEAT_MS)
        .note("No more than four ACTIVATEs per window, however many banks are free.", "Four lit bars under a pink lid, two dark ones waiting.")
        .detail("A power limit becomes a speed limit.", &["tFAW about 21 ns (DDR4-3200)"]),
    Beat::new("denser chips: more rows to refresh", BEAT_MS)
        .note("Every doubling of rows means more refresh work inside the same window.", "Three cyan stacks, each twice the last.")
        .detail("Same-bank refresh softens it; it does not remove it.", &["Refresh window stays 64 ms (CELL node)"]),
];

zoom_scene_impl!(OneZ, ONE_BEATS, BankZoom::OneBank);
zoom_scene_impl!(GroupsZ, GROUPS_BEATS, BankZoom::Groups);
zoom_scene_impl!(FawZ, FAW_BEATS, BankZoom::Faw);
zoom_scene_impl!(MapZ, MAP_BEATS, BankZoom::Mapping);
zoom_scene_impl!(RefreshZ, REFRESH_BEATS, BankZoom::Refresh);
zoom_scene_impl!(SecBanks, BANKS_BEATS, BankZoom::Banks);
zoom_scene_impl!(SecParts, PARTS_BEATS, BankZoom::Parts);
zoom_scene_impl!(SecOrder, ORDER_BEATS, BankZoom::Order);
zoom_scene_impl!(SecRules, RULES_BEATS, BankZoom::Rules);
zoom_scene_impl!(SecConflicts, CONFLICT_BEATS, BankZoom::Conflicts);
zoom_scene_impl!(SecNumbers, NUMBERS_BEATS, BankZoom::Numbers);
zoom_scene_impl!(SecRefresh, REFSEC_BEATS, BankZoom::RefreshSec);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, BankZoom::Makers);
zoom_scene_impl!(SecRisks, RISKS_BEATS, BankZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecBanks),
    || Box::new(SecParts),
    || Box::new(SecOrder),
    || Box::new(SecRules),
    || Box::new(SecConflicts),
    || Box::new(SecNumbers),
    || Box::new(SecRefresh),
    || Box::new(SecMakers),
    || Box::new(SecRisks),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(beat: usize, local: f32) -> Time {
        Time { ms: 0, beat, local, beat_start: 0 }
    }

    fn scenes() -> Vec<(String, Box<dyn Scene>)> {
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), Box::new(MemBank))];
        for z in ZOOMS {
            v.push((z.key.to_string(), (z.build)()));
        }
        for (i, mk) in SECTIONS.iter().enumerate() {
            v.push(((i + 1).to_string(), mk()));
        }
        v
    }

    #[test]
    fn every_frame_is_a_picture_that_moves() {
        for (name, scene) in scenes() {
            let p = Player::new(scene, Instant::now());
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(397) {
                let img = p.pixels(&p.time_at(ms), 160, 90).expect("pixel frame");
                assert_eq!(img.dimensions(), (160, 90), "{name}");
                seen.insert(img.into_raw());
            }
            assert!(seen.len() > 12, "{name}: {} distinct frames", seen.len());
        }
    }

    /// Text and picture agree on how many beats each scene has.
    #[test]
    fn beats_match_their_pictures() {
        assert_eq!(BEATS.len(), poly3d::BANK_OVERVIEW_BEATS);
        for z in ZOOMS {
            assert_eq!((z.build)().beats().len(), zoom_scene(z.key).unwrap().beats(), "zoom {}", z.key);
        }
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            assert_eq!(mk().beats().len(), zoom_scene(key).unwrap().beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("BANK")
            .unwrap()
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(heads, SECTIONS.len() + 1, "one scene per section but the sources");
    }

    #[test]
    fn beats_have_text_for_the_popup() {
        let all = BEATS
            .iter()
            .chain(ONE_BEATS)
            .chain(GROUPS_BEATS)
            .chain(FAW_BEATS)
            .chain(MAP_BEATS)
            .chain(REFRESH_BEATS)
            .chain(BANKS_BEATS)
            .chain(PARTS_BEATS)
            .chain(ORDER_BEATS)
            .chain(RULES_BEATS)
            .chain(CONFLICT_BEATS)
            .chain(NUMBERS_BEATS)
            .chain(REFSEC_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISKS_BEATS);
        for b in all {
            assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}", b.caption);
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_bank_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_bank_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else {
            return;
        };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for (name, scene) in scenes() {
            let beats = scene.beats().len();
            let p = Player::new(scene, Instant::now());
            for beat in 0..beats {
                let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                let img = p.pixels(&at(beat, 0.6), w, h).expect("pixel frame");
                img.save(dir.join(format!("{name}_{beat}.png"))).unwrap();
            }
        }
    }
}
