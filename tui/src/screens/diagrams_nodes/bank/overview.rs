// BANK overview: one DRAM die, face-on, played back from the Blender scene
// (tools/pbr3d/blender/bank_overview.py) in the picture-and-panel template. Sixteen banks in four
// groups share a command bus and a data bus: ACTIVATE bank A, ACTIVATE bank B in another group,
// READs alternate onto the data bus, four ACTIVATEs fill one tFAW window, a row conflict in A
// while B keeps reading, then an all-bank refresh. Zooms (a-e) open one bank, the bank groups,
// the four-activate window, address mapping and refresh (tools/pbr3d/blender/bank_zooms.py).
//
// Sources: DDR4-3200 module SPD values (tRRD, tCCD, tFAW); Micron DDR5 white paper; arXiv 1607.08578
// and 1509.03721 (address interleaving); PCPer (DDR4 refresh locks the rank).

use super::super::blender::{Cell, Page, BEAT_MS};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("a DRAM chip is many banks sharing one command bus and one data bus", BEAT_MS)
        .note(
            "A DDR4 chip has 16 banks in four bank groups. Each bank is a full array with its own row buffer, and all of them share the command bus and the data bus.",
            "sixteen orange bank tiles in four framed groups, a pale command bus along the top, and a green data lane through the middle running out to the I/O pad on the right",
        )
        .detail(
            "Separate banks let the chip work on several rows at once, even though data leaves one burst at a time.",
            &["DDR4: 16 banks in 4 bank groups (section 6)", "DDR5: 32 banks in 8 bank groups (section 6)"],
        ),
    Beat::new("ACTIVATE bank A: one bank opens a row", BEAT_MS)
        .note(
            "The controller sends ACTIVATE to bank A. Its row opens into its own row buffer, and the other banks are untouched.",
            "a white command dot drops onto the top-left bank, and a bright row-buffer plate stands up out of it while the other fifteen banks stay orange",
        )
        .detail(
            "Opening a row takes tRCD before it can be read (ARRAY node).",
            &["tRCD, tCL and tRP are set out on the ARRAY node (section 10)", "Each bank holds one open row (section 2)"],
        ),
    Beat::new("ACTIVATE bank B while A is still open", BEAT_MS)
        .note(
            "Bank B, in another group, gets its own ACTIVATE a few nanoseconds after A. Both rows are open at once: bank-level parallelism.",
            "a second white dot goes to a bank in the top-right group, and its row plate rises while bank A's plate is still standing",
        )
        .detail(
            "ACTs to different banks only need tRRD between them, far less than tRCD.",
            &["tRRD_S about 3.7 ns across groups (DDR4-3200 module SPD)", "tRRD_L about 5.3 ns within one group (module SPD)"],
        ),
    Beat::new("READs alternate between A and B, and the data bus stays busy", BEAT_MS)
        .note(
            "With two rows open, READs alternate between the banks. Alternating bank groups lets READs come one burst apart, so the data bus carries data back to back.",
            "green bursts leave bank A, then bank B, drop onto the green data lane and run out to the I/O pad; both row plates stay up",
        )
        .detail(
            "Across groups, READs need only tCCD_S, the length of one burst.",
            &["tCCD_S = 2.5 ns, one burst (DDR4-3200 module SPD)", "tCCD_L about 5.36 ns within one group (module SPD)"],
        ),
    Beat::new("four ACTIVATEs fill one tFAW window; the fifth bank waits", BEAT_MS)
        .note(
            "Banks C and D open too. Four ACTIVATEs now fall inside one tFAW window, so a fifth, to bank E, has to wait until the window has passed.",
            "the row plates of banks C and D rise in the bottom groups, and bank E in the top-left group has a pink frame while it waits",
        )
        .detail(
            "tFAW caps how fast rows can be opened, which limits the current they draw.",
            &["At most four ACTIVATEs in any tFAW window, about 21 ns (section 4)", "tFAW about 21 ns (DDR4-3200 module SPD)"],
        ),
    Beat::new("a row conflict in bank A; bank B keeps reading", BEAT_MS)
        .note(
            "A request needs a different row in bank A. Bank A has to precharge and reopen, but bank B keeps serving reads meanwhile.",
            "bank A turns pink and its row plate drops, while the plate on the top-right bank stays up and bursts keep leaving it along the data lane",
        )
        .detail(
            "A conflict costs tRP + tRCD + tCL in that bank only; other banks hide part of the wait.",
            &["Requests to different rows of one bank each pay tRP + tRCD + tCL (section 5)", "Banks working in parallel hide each other's waits (section 5)"],
        ),
    Beat::new("all-bank REFRESH: every bank closes, then all turn cyan", BEAT_MS)
        .note(
            "DDR4's REFRESH works on all banks at once: every open row is closed, then every bank refreshes and none can be used until it finishes.",
            "all sixteen banks turn pale cyan together and the row plates are gone",
        )
        .detail(
            "DDR5 adds same-bank refresh so the other banks keep working (zoom e).",
            &["DDR4 refresh works on all banks at once (section 7)", "DDR5 same-bank refresh (REFsb) refreshes one bank per group (section 7)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "one bank: its own row and states",
        build: || -> Box<dyn Scene> { zoom::one() },
    },
    Zoom {
        key: 'b',
        label: "bank groups: why alternating groups is faster",
        build: || -> Box<dyn Scene> { zoom::groups() },
    },
    Zoom {
        key: 'c',
        label: "the four-activate window",
        build: || -> Box<dyn Scene> { zoom::faw() },
    },
    Zoom {
        key: 'd',
        label: "address mapping: which bits pick the bank",
        build: || -> Box<dyn Scene> { zoom::map() },
    },
    Zoom {
        key: 'e',
        label: "refresh: all banks vs one bank per group",
        build: || -> Box<dyn Scene> { zoom::refresh() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/bank_overview.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "BANK overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "BANK overview");
    }
}
