// CLEAN: the page's overview, a Blender scene (tools/pbr3d/blender/clean_overview.py, GLB
// tools/pbr3d/assets/clean_overview.glb). One wet bench, cut open: five chemistry tanks in a row (SPM,
// DHF, SC-1, SC-2, rinse), a wafer carrier that moves from tank to tank, and a hooded dryer at the end.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/clean_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match clean_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a row of tanks strips and rinses", BEAT_MS)
        .note(
            "A wet bench is a row of chemical tanks. A carrier of wafers goes down into each tank in turn, and ultrapure water rinses the wafers between them. Each chemistry removes a different kind of contamination, and the sequence ends with the wafers dried. Cleaning follows many other steps so that residue and particles from one step do not carry into the next.",
            "The whole bench, cut open: five open tanks in a row on a steel bench, with the wafer carrier hanging over the first one. A hooded dryer stands at the right end. Nothing moves yet; the carrier waits above the first tank.",
        )
        .detail(
            "Each tank does one job, in a set order.",
            &[
                "Wet bench: immersion, rinse, then spin dry (MKS)",
                "Typical order: SPM, DHF, SC-1, SC-2, rinse, dry",
            ],
        ),
    Beat::new("SPM: hot sulfuric acid and peroxide", BEAT_MS)
        .note(
            "SPM is sulfuric acid mixed with hydrogen peroxide, run hot. It strips photoresist and other organic residue left by the step before. It is the hot first tank in the sequence.",
            "The carrier sinks into a dark amber bath, and bubbles rise through the liquid around the wafers.",
        )
        .detail(
            "Hot acid burns off the organic residue.",
            &[
                "H2SO4 + H2O2, run hot (SPM)",
                "Photoresist strip at 170 C (ACMR)",
            ],
        ),
    Beat::new("DHF: dilute hydrofluoric acid", BEAT_MS)
        .note(
            "Dilute hydrofluoric acid, HF in water, etches away the thin oxide on the wafer, along with some of the metal ions caught in it. It works in a short dip of a few seconds. The bare silicon left behind is very reactive, so the wafers move on quickly.",
            "The carrier lifts out of the amber bath, slides across, and dips into a clear tank. Fine bubbles lift off the wafer faces.",
        )
        .detail(
            "A short dip removes the oxide.",
            &[
                "HF : water, 1:100 or 1:50, at 25 C for about 15 s (Wikipedia RCA clean)",
                "Bare silicon is very reactive after the dip",
            ],
        ),
    Beat::new("SC-1: ammonia and peroxide", BEAT_MS)
        .note(
            "SC-1 is ammonia and hydrogen peroxide in water, heated to about 75 to 80 C for about ten minutes. It removes organic residue and particles. It leaves a thin oxide and some iron on the surface, which the next tank removes.",
            "The carrier moves into a light blue bath, and bubbles rise off the wafer faces.",
        )
        .detail(
            "Removes organic residue and particles.",
            &[
                "5 water : 1 NH3 (29%) : 1 H2O2 (30%)",
                "75-80 C, about 10 min (Wikipedia RCA clean)",
                "Leaves ~1 nm oxide and some iron",
            ],
        ),
    Beat::new("SC-2: hydrochloric acid and peroxide", BEAT_MS)
        .note(
            "SC-2 is hydrochloric acid and hydrogen peroxide in water, at the same heat and time as SC-1. It dissolves the metal ions that remain, including the iron SC-1 left behind. It also leaves a thin layer that protects the clean surface from picking up new contamination.",
            "The carrier moves into a pale green bath. Under the bath the wafers stay still while the tank works.",
        )
        .detail(
            "Removes the remaining metal ions.",
            &[
                "6 water : 1 HCl (37%) : 1 H2O2 (30%)",
                "75-80 C, about 10 min (Wikipedia RCA clean)",
                "Leaves a passivating layer that protects the surface",
            ],
        ),
    Beat::new("ultrapure water rinse, then dry", BEAT_MS)
        .note(
            "Ultrapure water rinses the chemistry off the wafers. The carrier moves through the rinse tank, then the wafers are spin dried, with megasonic energy or isopropyl alcohol sometimes used to help. A single-wafer tool does the same job one wafer at a time.",
            "A stream of clear water falls into the last tank, and the carrier rises and moves into the dryer hood at the right end.",
        )
        .detail(
            "Water rinses the chemistry off; spin dry finishes.",
            &[
                "UPW spray, overflow dump and cyclic rinse (MKS)",
                "Spin dry; megasonics or IPA can help (MKS)",
                "Single-wafer tool: SU-2000, 150-200 mm, 2 or 4 chambers (SCREEN)",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "CLEAN overview");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "CLEAN overview");
    }
}
