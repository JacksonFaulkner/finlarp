// SLICE + POLISH zoom-ins a-d in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/slice_zooms.py: a the wire web and its kerf, b lapping both faces, c the Preston
// polish and pH, d the thickness budget. Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const WEB_BEATS: &[Beat] = &[
    Beat::new("the ingot is fed down through a wire web of parallel diamond wires", BEAT_MS)
        .note(
            "A multi-wire saw holds a web of parallel wires. The ingot comes down into the web, and each wire will cut one slot as it passes through.",
            "the grey ingot sinking through six horizontal steel wires strung between two posts",
        )
        .detail(
            "Each slot is one wire pass across every wafer at once, so the web is what sets the number of wafers.",
            &[
                "Multi-wire diamond saw: grooved guide rollers, one pass per slot (page section 2)",
                "Each wire is a steel core with diamond grit fixed on it (page section 2)",
            ],
        ),
    Beat::new("one wire pass cuts one slot: the kerf is about 125 um", BEAT_MS)
        .note(
            "The wire removes a slot as wide as its diamond layer plus wobble. The wafers stand in a stack with a thin gap between them, and the wire lies in each gap.",
            "seven slices standing one above another, a wire lying in each gap",
        )
        .detail(
            "The kerf is silicon grown at great cost and lost as swarf, so a thinner wire yields more wafers per ingot.",
            &[
                "Kerf about 125 um per slot for diamond wire today (page source [1])",
                "Kerf is the effective wire diameter including the diamond layer, plus wobble (page section 2)",
            ],
        ),
    Beat::new("a worn wire bows under the load: the cut gets wavier", BEAT_MS)
        .note(
            "A worn wire deflects more under the load, so it bows deeper at the middle. The wafers that come out have more thickness variation and a wavier surface.",
            "one wire bowed into a V under the load, its dzmax marker deeper than the straight wires beside it",
        )
        .detail(
            "Wire breakage and wear are the main saw risks on the page, and the worn wire is the one to watch.",
            &[
                "Wear raises wire deflection, thickness variation and kerf (Springer 2026; source [3])",
                "A worn wire is the highest-value risk for the saw (page section 7)",
            ],
        ),
    Beat::new("near the end of the cut, the last wafers still hang from the block", BEAT_MS)
        .note(
            "Near the end of the cut the last wafers are still held by the uncut base of the block, so the face looks like a comb of teeth.",
            "the slices stacked on an uncut base, the last wire passing through the bottom gap",
        )
        .detail(
            "The wire has to finish every slot before the wafers are free, so a late wire break costs the whole cut.",
            &[
                "The page gives no kerf count per slot; each slot is one wire pass (page section 2)",
                "Wafers held by the block until the cut finishes (general knowledge)",
            ],
        ),
];

const LAP_BEATS: &[Beat] = &[
    Beat::new("the wafers sit between two plates, with slurry in the gap", BEAT_MS)
        .note(
            "The wafer sits between two flat plates with loose abrasive slurry in the gap. Both faces are worked at the same time.",
            "the upper plate hanging above the wafer on the lower plate, with slurry grains in the gap",
        )
        .detail(
            "Lapping sets flatness and parallelism, and it is the step that takes the saw damage down.",
            &[
                "Double-side lapping removes 80 to 200 um in total (page section 4)",
                "Lapping uses loose abrasive slurry between two plates (page section 3)",
            ],
        ),
    Beat::new("the upper plate presses down: both faces wear at once", BEAT_MS)
        .note(
            "Pressure from the upper plate drives the slurry grains into both faces. The wafer thins on both sides together.",
            "red pressure arrows on the upper plate, which drops onto the wafer",
        )
        .detail(
            "Pressure and speed set how fast the wafer thins, and the slurry sets how fine the finish is.",
            &[
                "One 200-300 mm patent example: 80 um in 40 min (page section 4)",
                "Lapping stock removal is the second-largest planned loss (page section 5)",
            ],
        ),
    Beat::new("lapped: flat and parallel, but cracked underneath", BEAT_MS)
        .note(
            "The wafer comes out flat and parallel, but cracks run under its surface. Those cracks are what the etch has to remove next.",
            "the plate closing on a flat wafer, with an orange damage layer showing at its faces",
        )
        .detail(
            "The lapped wafer is flat but micro-cracked underneath, so the etch step is not optional.",
            &[
                "Sawing and lapping leave a cracked layer microns deep (page section 3)",
                "Etch removes about 15-25 um after lapping (page section 4)",
            ],
        ),
    Beat::new("the plate lifts away: 80 to 200 um came off in total", BEAT_MS)
        .note(
            "The upper plate lifts clear, and the wafer is ready for the etch. The 80 um in this picture is one patent example; the range is 80 to 200 um.",
            "the upper plate lifted clear above the wafer on its lower plate",
        )
        .detail(
            "The figure depends on the process; the page calls it a patent example, not a standard.",
            &[
                "80 um in one 200-300 mm patent example (page section 4)",
                "Removal amounts are patent examples, not a standard (page section 9)",
            ],
        ),
];

const PRESTON_BEATS: &[Beat] = &[
    Beat::new("the pad sits on the wafer; abrasive grains move under it", BEAT_MS)
        .note(
            "A pad sits over the wafer with slurry grains between them. The pad averages out the high spots as it works.",
            "a tan pad above a grey wafer, with dark grains scattered over the wafer's top face",
        )
        .detail(
            "Planarity comes from the pad asperities and the slurry flow averaging out high spots (textbook).",
            &[
                "Polishing is chemical plus mechanical: the chemistry softens the surface and the abrasive removes it (page section 3)",
                "Surface softened or oxidised, then wiped off (textbook picture, page section 3)",
            ],
        ),
    Beat::new("pressure sets the rate: RR = K*P + C", BEAT_MS)
        .note(
            "The pad presses on the softened top layer and wipes it off. The removal rate follows Preston's law, RR = K*P + C, so more pressure removes more. The gold bar climbs with the pressure.",
            "the pad lowered onto the wafer and the gold bar at the right growing with the pressure",
        )
        .detail(
            "Higher pressure and speed raise the removal rate; the pad, slurry and temperature fold into K.",
            &[
                "Preston law: K the Preston constant, P pressure, C the zero-pressure term (page section 3; source [5])",
                "Double-side polish removes 10 to 20 um in total (page section 4)",
            ],
        ),
    Beat::new("pH moves the rate: silica rises with pH, ceria peaks near 8-9", BEAT_MS)
        .note(
            "For oxide CMP the slurry pH matters. Removal rises with pH for silica slurries, and ceria slurries peak between about pH 8 and 9. The pad is lifted to show the pH scale along the front.",
            "a long grey pH scale along the front edge of the wafer, with two small red markers on it",
        )
        .detail(
            "So slurry chemistry is a real tuning axis, not only the abrasive size.",
            &[
                "Removal rises with pH for silica slurries; ceria peaks near pH 8-9 (page section 3; source [5])",
                "The Preston law runs on both ends of the chip (page section 8)",
            ],
        ),
    Beat::new("at pH 13 the surface pits", BEAT_MS)
        .note(
            "At pH 13 the surface pits, so the chemistry has to be held inside a window. The pits are shown as dark red dots in a patch on the wafer top.",
            "a patch of dark red pits on the top of the wafer, with the pad gone",
        )
        .detail(
            "Pitting is the failure the pH window is there to avoid.",
            &[
                "Pitting seen at pH 13 (page section 3; source [5])",
                "Oxide CMP chemistry is tuned by pH (page section 3)",
            ],
        ),
];

const BUDGET_BEATS: &[Beat] = &[
    Beat::new("kerf: the first loss, at the saw", BEAT_MS)
        .note(
            "The kerf is the first loss. About 125 um of silicon per wafer cut becomes swarf at the saw. The top slab peels off to the side.",
            "the top slab sliding off to the left of a grey stack of layers",
        )
        .detail(
            "The kerf is the one part of the budget that is pure loss.",
            &[
                "Diamond wire kerf about 125 um, per the page's thickness budget (source [1])",
                "Kerf is per wafer cut; the wire sets it (page section 2)",
            ],
        ),
    Beat::new("lapping takes the next biggest share", BEAT_MS)
        .note(
            "Lapping takes the next layer. The 80 um layer is one patent example; the range is 80 to 200 um, and the page shows the ranges in parentheses.",
            "the second slab, thicker than the etch and polish layers, sliding off to the left",
        )
        .detail(
            "Double-side lapping removes 80 to 200 um, and the 80 um figure is one example.",
            &[
                "Lapping removes 80 to 200 um double-side (page section 5)",
                "One 200-300 mm patent example: 80 um, 40 min (page section 4)",
            ],
        ),
    Beat::new("etch: a thin layer, 15 to 25 um", BEAT_MS)
        .note(
            "The etch removes a thin layer of about 15 to 25 um. The 20 um slab is the midpoint of that range.",
            "a thin slab sliding off to the left, between the lapped layer and the wafer below",
        )
        .detail(
            "Etch removes the damage that lapping leaves behind.",
            &[
                "Etch removes about 15-25 um after lapping (page sections 4-5)",
                "Etch is chemical, so it removes damage without adding mechanical stress (page section 4)",
            ],
        ),
    Beat::new("DSP polish: 10 to 20 um, and 775 um is left", BEAT_MS)
        .note(
            "Double-side polish takes the last thin layer, about 10 to 20 um, and the 15 um slab is the midpoint. What is left is the 775 um wafer. The four layers are patent and source examples that do not close into one wafer's history.",
            "the last thin slab sliding off, and the finished wafer standing alone in the middle",
        )
        .detail(
            "Each number comes from a different source, so they do not close into one wafer's history.",
            &[
                "DSP removes 10 to 20 um total (page section 4)",
                "End result: 775 um +/- 25 um thick (vendor datasheet, see WAFER)",
            ],
        ),
];

static WEB: Cell = std::sync::OnceLock::new();
static LAP: Cell = std::sync::OnceLock::new();
static PRESTON: Cell = std::sync::OnceLock::new();
static BUDGET: Cell = std::sync::OnceLock::new();

pub fn web() -> Box<dyn Scene> {
    page(
        &WEB,
        include_bytes!("../../../../../tools/pbr3d/assets/slice_zoom_web.glb"),
        WEB_BEATS,
    )
}

pub fn lap() -> Box<dyn Scene> {
    page(
        &LAP,
        include_bytes!("../../../../../tools/pbr3d/assets/slice_zoom_lap.glb"),
        LAP_BEATS,
    )
}

pub fn preston() -> Box<dyn Scene> {
    page(
        &PRESTON,
        include_bytes!("../../../../../tools/pbr3d/assets/slice_zoom_preston.glb"),
        PRESTON_BEATS,
    )
}

pub fn budget() -> Box<dyn Scene> {
    page(
        &BUDGET,
        include_bytes!("../../../../../tools/pbr3d/assets/slice_zoom_budget.glb"),
        BUDGET_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("web", web as fn() -> Box<dyn Scene>),
            ("lap", lap),
            ("preston", preston),
            ("budget", budget),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
