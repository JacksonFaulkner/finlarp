// BANK zoom-ins a-e in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/bank_zooms.py: a one bank and its row buffer, b bank groups and tCCD,
// c the four-activate window, d address mapping, e refresh (all-bank vs same-bank). Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const ONE_BEATS: &[Beat] = &[
    Beat::new("ACTIVATE: the bank opens a row into its row buffer", BEAT_MS)
        .note(
            "A bank is a whole array (ARRAY node). ACTIVATE opens one of its rows into its own row buffer.",
            "a white command dot drops onto the orange bank, and a bright row-buffer stripe rises across it",
        )
        .detail(
            "Each bank tracks its own open row.",
            &["One open row per bank (section 2)", "tRCD, tCL and tRP are on the ARRAY node (section 10)"],
        ),
    Beat::new("READs leave the open row for the data bus", BEAT_MS)
        .note(
            "While the row is open, READs take data from this bank's row buffer onto the shared data bus.",
            "green dots leave the row-buffer stripe and run off to the right, toward the data bus and the I/O pins",
        )
        .detail(
            "Other banks can be doing other things meanwhile.",
            &["The data bus is shared by all banks (section 2)", "DDR4 burst length 8 (section 6)"],
        ),
    Beat::new("PRECHARGE closes the row and the bank goes idle", BEAT_MS)
        .note(
            "PRECHARGE closes the row and returns the bank to idle, ready for a different row.",
            "the bank turns pink, the row stripe goes out, and a white command dot lands on it",
        )
        .detail(
            "Only this bank is closed; the others keep their rows.",
            &["A row conflict costs tRP + tRCD + tCL (section 5)", "tRP is on the ARRAY node (section 10)"],
        ),
    Beat::new("the next ACTIVATE opens a new row in the same bank", BEAT_MS)
        .note(
            "A new ACTIVATE opens a different row in the same bank. The cycle is ACTIVATE, READ, PRECHARGE, and then again for the next row.",
            "the bank is orange again, a white command dot comes in, and a bright row stripe rises lower on the bank",
        )
        .detail(
            "Each conflict costs a full close and reopen before the new row can be read.",
            &["Requests to different rows of one bank queue up (section 5)", "One open row per bank at a time (section 2)"],
        ),
];

const GROUPS_BEATS: &[Beat] = &[
    Beat::new("READs in one bank group must be tCCD_L apart", BEAT_MS)
        .note(
            "Banks in a group share some circuits, so back-to-back READs to one group must wait tCCD_L, which is longer than a burst.",
            "gold READ blocks in one lane with a dark gap between each pair",
        )
        .detail(
            "About 5.36 ns at DDR4-3200, against a 2.5 ns burst.",
            &["tCCD_L about 5.36 ns (DDR4-3200 module SPD)", "tCCD_S is one burst, 2.5 ns (module SPD)"],
        ),
    Beat::new("READs alternating groups fill the bus with no gaps", BEAT_MS)
        .note(
            "Alternating between groups only needs tCCD_S, which equals one burst, so READs line up back to back.",
            "gold and cyan READ blocks alternate along one lane with no gaps between them",
        )
        .detail(
            "Bank groups were added in DDR4 to raise speed this way.",
            &["tCCD_S = 4 clocks = 2.5 ns at DDR4-3200 (section 4)", "DDR4 has 4 bank groups; DDR5 has 8 (section 6)"],
        ),
    Beat::new("the gaps are idle data bus time", BEAT_MS)
        .note(
            "Every gap in the same-group lane is time the data bus carries nothing.",
            "pale pink gap blocks fill the spaces between the gold READs in the same-group lane",
        )
        .detail(
            "Controllers spread consecutive READs across groups to close the gaps.",
            &["The gap is tCCD_L minus one burst (figures in section 4)", "Alternating groups keeps the bus full (section 4)"],
        ),
    Beat::new("the same bus: alternating groups fills it", BEAT_MS)
        .note(
            "Both lanes use the same data bus. The upper lane is one group, with gaps; the lower lane alternates groups, with none.",
            "the upper lane of gold blocks has gaps, and the lower lane of gold and cyan blocks runs back to back",
        )
        .detail(
            "The data bus carries one burst at a time, so alternating groups is how the controller keeps it full.",
            &["Data bus: one burst at a time (section 2)", "A DDR4-3200 burst of 8 is 2.5 ns, so alternating groups keeps the bus full (section 4)"],
        ),
];

const FAW_BEATS: &[Beat] = &[
    Beat::new("four ACTIVATEs, tRRD apart", BEAT_MS)
        .note(
            "ACTIVATEs to different banks need tRRD between them. Four ACT blocks step along the time axis.",
            "four gold ACT blocks stand in a row on the grey time axis, a slot apart",
        )
        .detail(
            "About 3.7 ns across groups at DDR4-3200.",
            &["tRRD_S about 3.7 ns (module SPD)", "tRRD_L about 5.3 ns within one group (module SPD)"],
        ),
    Beat::new("the window: no more than four in tFAW", BEAT_MS)
        .note(
            "Any tFAW window may hold at most four ACTIVATEs.",
            "a long pink window bar runs under the four blocks and spans about five and a half slots",
        )
        .detail(
            "Opening rows draws current; the window caps it.",
            &["tFAW about 21 ns (module SPD)", "tFAW 21-23 ns in the SPD dumps (section 10)"],
        ),
    Beat::new("the fifth ACTIVATE waits for the window", BEAT_MS)
        .note(
            "A fifth ACTIVATE wanted early has to wait until the first one's window ends.",
            "a faint pink ghost marks the wanted slot inside the window, and the real fifth block stands past the window's end",
        )
        .detail(
            "With many banks, tFAW often sets the pace, not tRRD.",
            &["Four times 3.7 ns is 14.8 ns, less than tFAW's 21 ns (section 4 figures)"],
        ),
    Beat::new("the window slides on, so ACT 5 now fits", BEAT_MS)
        .note(
            "The window moves on as the first ACT leaves it, so the fifth ACT sits inside the new window with four others.",
            "the pink window bar has shifted right, the first gold block stands outside it, and the fifth block sits at its end",
        )
        .detail(
            "The count is per window, not per bank.",
            &["No more than four ACTIVATEs in any tFAW window (section 4)", "tFAW about 21 ns (module SPD)"],
        ),
];

const MAP_BEATS: &[Beat] = &[
    Beat::new("the address is split into row, bank, group and column", BEAT_MS)
        .note(
            "The memory controller chooses which address bits pick the row, the bank, the bank group and the column.",
            "a strip of four fields: purple row bits on the left, then cyan bank bits, gold group bits and green column bits on the right",
        )
        .detail(
            "The mapping is a controller design choice.",
            &["Column bits lowest keeps neighbouring addresses in one row (arXiv 1509.03721)", "Interleaving across banks (arXiv 1607.08578)"],
        ),
    Beat::new("consecutive addresses: one open row", BEAT_MS)
        .note(
            "Counting up changes only the column bits, so neighbouring addresses land in one row of one bank: row hits.",
            "white request dots drop from the column field onto the first bank, whose row is open; the other banks stay closed",
        )
        .detail(
            "Good for streaming, bad if two streams share the bank.",
            &["Column bits lowest (arXiv 1509.03721)", "The interleaving unit is often one row (arXiv 1607.08578)"],
        ),
    Beat::new("a stride flips the bank bits: many banks at once", BEAT_MS)
        .note(
            "Addresses that differ in the bank bits go to different banks, which can then work in parallel.",
            "each request dot goes to a different bank, and four banks light their open rows in turn",
        )
        .detail(
            "Interleaving across banks buys bank-level parallelism.",
            &["Addresses are interleaved across banks and ranks (arXiv 1607.08578)"],
        ),
    Beat::new("row hits first, the rest spread out", BEAT_MS)
        .note(
            "A controller that groups same-row requests and spreads the rest across banks gets hits and parallelism.",
            "the first bank reads steadily, its row open, while the other three open and read in turn",
        )
        .detail(
            "Real controllers reorder within limits for fairness.",
            &["Row hits first, spread the rest (section 5)", "Throughput depends on the mapping and ordering, not only the chip (section 9)"],
        ),
];

const REFRESH_BEATS: &[Beat] = &[
    Beat::new("DDR4 all-bank refresh: the rank is blocked", BEAT_MS)
        .note(
            "REFRESH in DDR4 refreshes every bank at once; reads waiting for any bank must wait.",
            "all sixteen banks turn pale cyan, and a red bar across the data lane marks the blocked rank",
        )
        .detail(
            "The whole rank is locked while it runs.",
            &["DDR4 refresh locks the whole rank (PCPer, section 10)", "DDR4's REFRESH works on all banks at once (section 7)"],
        ),
    Beat::new("DDR5 same-bank refresh: one bank per group", BEAT_MS)
        .note(
            "DDR5's REFsb refreshes the same bank in every group, one bank index at a time.",
            "one bank in each group turns cyan, and the cyan steps through the four bank positions over the beat",
        )
        .detail(
            "The other banks stay available.",
            &["REFsb targets the same bank in every bank group (Micron white paper)", "DDR5 adds same-bank refresh (section 7)"],
        ),
    Beat::new("the other banks keep serving reads", BEAT_MS)
        .note(
            "While one bank per group refreshes, reads to the rest carry on.",
            "pale cyan banks in one position while the others stay orange, and green bursts keep leaving them",
        )
        .detail(
            "Refresh costs less throughput than an all-bank refresh.",
            &["Other banks stay available during same-bank refresh (section 7)", "PCPer: DDR4 refresh locks the rank (section 10)"],
        ),
    Beat::new("denser chips: refresh eats more of the bank time", BEAT_MS)
        .note(
            "Denser chips have more rows to refresh in the same window, which eats into bank time.",
            "two bank positions in every group are cyan at once, so more of the chip is busy refreshing",
        )
        .detail(
            "Same-bank refresh softens the cost; it does not remove it.",
            &["Denser chips have more rows to refresh in the same window (section 9)", "Same-bank refresh softens it (section 7)"],
        ),
];

static ONE: Cell = std::sync::OnceLock::new();
static GROUPS: Cell = std::sync::OnceLock::new();
static FAW: Cell = std::sync::OnceLock::new();
static MAP: Cell = std::sync::OnceLock::new();
static REFRESH: Cell = std::sync::OnceLock::new();

pub fn one() -> Box<dyn Scene> {
    page(
        &ONE,
        include_bytes!("../../../../../tools/pbr3d/assets/bank_one.glb"),
        ONE_BEATS,
    )
}

pub fn groups() -> Box<dyn Scene> {
    page(
        &GROUPS,
        include_bytes!("../../../../../tools/pbr3d/assets/bank_groups.glb"),
        GROUPS_BEATS,
    )
}

pub fn faw() -> Box<dyn Scene> {
    page(
        &FAW,
        include_bytes!("../../../../../tools/pbr3d/assets/bank_faw.glb"),
        FAW_BEATS,
    )
}

pub fn map() -> Box<dyn Scene> {
    page(
        &MAP,
        include_bytes!("../../../../../tools/pbr3d/assets/bank_map.glb"),
        MAP_BEATS,
    )
}

pub fn refresh() -> Box<dyn Scene> {
    page(
        &REFRESH,
        include_bytes!("../../../../../tools/pbr3d/assets/bank_refresh.glb"),
        REFRESH_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};
    use super::*;

    #[test]
    fn zooms_match_the_blender_beats_and_draw() {
        let zooms: [(&str, fn() -> Box<dyn Scene>); 5] = [
            ("one", one),
            ("groups", groups),
            ("faw", faw),
            ("map", map),
            ("refresh", refresh),
        ];
        for (name, f) in zooms {
            let s = f();
            assert_eq!(s.beats().len(), 4, "zoom {name} has four beats");
            explained(s.as_ref(), &format!("BANK zoom {name}"));
            draws_every_beat(s.as_ref(), &format!("BANK zoom {name}"));
        }
    }
}
