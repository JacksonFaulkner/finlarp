// POLYSILICON overview: a Siemens-process plant cut open so the inside shows, from the
// fluidised bed to bagged chunks, played back from the Blender scene
// (tools/pbr3d/blender/poly_overview.py) in the picture-and-panel template (blender::Page).
// Zoom-ins a-d open the fluidised bed, the distillation column, the bell jar and the recycle loop
// (still in the older layout, from tools/pbr3d/blender/fab_poly.py).

use super::super::blender::{clip, Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene, Zoom};

const OVERVIEW_BEATS: &[Beat] = &[
    Beat::new("MG-Si and HCl meet in a fluidised bed at about 300 C and make trichlorosilane (TCS)", BEAT_MS)
        .note(
            "Metallurgical silicon from SAND drops into a bed of grains that hydrogen chloride gas keeps churning. Si + 3HCl gives SiHCl3 + H2. Distillation can only clean a liquid or a gas, so the silicon has to become one first.",
            "grey lumps sliding down the chute, green HCl bubbles climbing through the grains, yellow TCS gas rising out of the top",
        )
        .detail(
            "Turning the solid into a gas is what lets the next step clean it.",
            &[
                "Si + 3HCl gives SiHCl3 + H2, about 300 C",
                "Feed is 98-99% metallurgical silicon from SAND",
                "Some SiCl4 (STC) is made alongside (Fraunhofer)",
            ],
        ),
    Beat::new("the gas is condensed and distilled: pure TCS leaves the top, STC the bottom", BEAT_MS)
        .note(
            "The product gas is condensed to a liquid and fed to a multi-stage column at 30-60 C. TCS boils lower, so it climbs the trays and leaves the top. The heavier silicon tetrachloride (STC) collects at the bottom.",
            "the blue condenser, yellow vapour climbing the trays, purple STC dripping down into the sump and out to the tank",
        )
        .detail(
            "Purity is set here, before any silicon is deposited: what the column lets through ends up in the rods.",
            &[
                "SiHCl3 and SiCl4 separated at 30-60 C",
                "Multi-stage columns",
                "TCS boils lower than STC (textbook)",
            ],
        ),
    Beat::new("in the Siemens bell jar silicon deposits on U-rods heated to about 1100 C", BEAT_MS)
        .note(
            "TCS and hydrogen come in through nozzles in the base plate. Current runs up one rod, over the bridge and down the other, so the rods are their own heaters. SiHCl3 + H2 gives Si + 3HCl on their surface, and they thicken from 20 mm to 150-180 mm.",
            "yellow gas rising round the glowing rods, which grow fatter through the step, inside the blue water-cooled bell",
        )
        .detail(
            "The rods are the product. Power is the biggest cost, and most of it goes into keeping the rods hot for days.",
            &[
                "SiHCl3 + H2 gives Si + 3HCl on rods near 1100 C",
                "Slim rods 20 mm, final rods 150-180 mm, up to 1.9 mm per hour",
                "60-70 kWh per kg for solar grade in 2023, about 35-45 in this step (CPIA, Fraunhofer ISE)",
            ],
        ),
    Beat::new("off-gas is recovered: H2 and HCl go back to the bed, STC is converted back to TCS", BEAT_MS)
        .note(
            "The jar's exhaust goes to a recovery unit. Hydrogen and HCl are separated and piped back to the fluidised bed. In modified Siemens plants the STC from the column is hydrogenated back to TCS and fed to the column again.",
            "pale blue H2 and green HCl running along the back pipe to the bed, purple STC going up into the converter and yellow TCS coming back out",
        )
        .detail(
            "The loop is what keeps the chemical cost low. STC is a large share of the mass, so converting it matters.",
            &[
                "H2 and HCl recovered and re-fed",
                "Modified Siemens routes hydrogenate STC back to TCS",
                "Side reaction 4SiHCl3 gives Si + 3SiCl4 + 2H2 (textbook)",
            ],
        ),
    Beat::new("the bell is lifted off, the rods cool and go to the crusher", BEAT_MS)
        .note(
            "At the end of the batch the power is cut and the bell is lifted. The thick rods, now dull grey, are pulled out and broken into chunks.",
            "the bell rising, the grey rods riding over to the crusher, and chunks dropping into the basket below it",
        )
        .detail(
            "Each batch ends with the jar opened; the rods leave and the jar starts again with new slim rods.",
            &[
                "Final rods 150-180 mm",
                "Batch cycle repeats",
                "Rods are broken into chunks",
            ],
        ),
    Beat::new("the chunks are etched clean and packed as 9N+ polysilicon for MELT + PULL", BEAT_MS)
        .note(
            "Breaking the rods leaves surface dirt, so the chunks are etched in acid, then packed. They go to MELT + PULL, where the crystal is grown from them.",
            "the basket dipping into the green bath, then tipping its chunks into the bagged bin",
        )
        .detail(
            "The customer buys chunks by grade. Electronic grade needs purity near 11N.",
            &[
                "Acid or alkaline etch after the rods are broken",
                "Chunks are the product for the wafer chain",
                "Electronic grade is near 11N; solar is lower",
            ],
        ),
];

/// The zoom beats are still in the older layout (5.2 s, caption over the picture).
const ZOOM_MS: u64 = 5200;

const BED_BEATS: &[Beat] = &[
    Beat::new("silicon and HCl meet in the bed at about 300 C", ZOOM_MS)
        .note(
            "Silicon granules are lifted by a gas flow so the whole bed moves like a boiling liquid. That gives a large surface for the reaction.",
            "grains lifting and falling in the bed",
        )
        .detail(
            "A fluid bed keeps the reaction even across the whole charge.",
            &["About 300 C", "Si + 3HCl gives SiHCl3 + H2", "The practical mix also makes some SiCl4"],
        ),
    Beat::new("gas bubbles carry the mixture up through the bed", ZOOM_MS)
        .note(
            "Hydrogen and HCl bubble up through the bed, lifting and mixing the grains.",
            "gas bubbles rising through the grains",
        )
        .detail(
            "Good mixing keeps hot spots down and the reaction even.",
            &["Gas flow sets how high the bed lifts", "Bubbles carry the mixing"],
        ),
    Beat::new("TCS and hydrogen leave the top; unreacted gas is recycled", ZOOM_MS)
        .note(
            "The product gas leaves the top of the bed and goes on to condensing and distillation. Unreacted HCl and H2 are recovered and fed back.",
            "gas leaving the top and a few particles carried with it",
        )
        .detail(
            "Recycling H2 and HCl is what keeps the process economic.",
            &["H2 and HCl are recovered and re-fed", "STC is a byproduct of the same step"],
        ),
    Beat::new("the bed is topped up and the cycle repeats", ZOOM_MS)
        .note(
            "Fresh silicon is added to replace what has reacted, and the bed keeps running.",
            "grains settling and fresh feed going in",
        )
        .detail(
            "Bed operation is continuous; the top-up sets the feed rate.",
            &["Continuous operation", "Fresh feed replaces reacted silicon"],
        ),
];

const COLUMN_BEATS: &[Beat] = &[
    Beat::new("vapour rises through the trays of the column", ZOOM_MS)
        .note(
            "The condensed chlorosilanes are fed in the middle of a multi-stage column. Vapour rises from tray to tray.",
            "vapour climbing and liquid dripping back on the trays",
        )
        .detail(
            "Each tray is one stage of separation. More stages give a cleaner product.",
            &["Separation at 30-60 C", "Multi-stage columns"],
        ),
    Beat::new("TCS is the lighter component, so it climbs and STC stays low", ZOOM_MS)
        .note(
            "The components boil at different temperatures. TCS boils lower, so it climbs the column while STC drops out lower down.",
            "the lighter vapour rising and the heavier liquid staying low",
        )
        .detail(
            "The boiling-point gap is what makes the separation work.",
            &["TCS boils lower than STC (textbook)", "Distillation, not chemistry, does this step"],
        ),
    Beat::new("purified TCS is drawn off at the top", ZOOM_MS)
        .note(
            "The purified TCS leaves the top of the column and goes to the bell jars.",
            "a clean stream drawn off the top tray",
        )
        .detail(
            "This is the feed for deposition: the purity set here carries through.",
            &["TCS is the deposition feed", "Electronic grade is set by this purity"],
        ),
    Beat::new("STC and the heavier residue leave the bottom", ZOOM_MS)
        .note(
            "The heavier residue, including STC, leaves the bottom. STC is a byproduct, used or hydrogenated back to TCS in modern routes.",
            "heavier liquid collecting in the sump at the bottom",
        )
        .detail(
            "Recovering STC matters because it is a large share of the mass.",
            &["STC is a byproduct", "Modified Siemens routes hydrogenate STC back to TCS"],
        ),
];

const JAR_BEATS: &[Beat] = &[
    Beat::new("the current runs up one rod, over the bridge and down the other", ZOOM_MS)
        .note(
            "The rods are their own heaters. The current goes up one rod, over the U-bridge, and back down the other.",
            "current pulses along the rods and the bridge glowing",
        )
        .detail(
            "Self-heated rods are why the jar needs no separate furnace.",
            &["Rods heated by their own current", "U-bridge joins each rod pair", "Water-cooled steel jar keeps the walls cold"],
        ),
    Beat::new("silicon grows on the hot rods from the gas", ZOOM_MS)
        .note(
            "TCS and hydrogen flow past the rods at about 1100 C, and silicon deposits on the surface.",
            "gas circulating and the rods thickening",
        )
        .detail(
            "Deposition happens on the hot skin of the rod.",
            &["SiHCl3 + H2 gives Si + 3HCl", "Deposition near 1100 C"],
        ),
    Beat::new("the rods thicken over the batch", ZOOM_MS)
        .note(
            "Growth is up to 1.9 mm per hour on the diameter. At that top rate, going from 20 mm to 150 mm takes roughly 35 hours (my arithmetic).",
            "the rods visibly thicker as the batch runs",
        )
        .detail(
            "The growth rate sets how long the jar runs, and so the cost per kilogram.",
            &["Slim rod 20 mm", "Final rods 150-180 mm", "Growth up to 1.9 mm/h"],
        ),
    Beat::new("the batch is cooled, opened and the rods are broken out", ZOOM_MS)
        .note(
            "The jar is cooled and opened. The rods are broken out and sent for crushing and etching.",
            "the thick rods coming out of the jar",
        )
        .detail(
            "After the batch the rods go to the crusher; the jar starts again.",
            &["Rods to the crusher", "Batch cycle repeats"],
        ),
];

const LOOP_BEATS: &[Beat] = &[
    Beat::new("H2 and HCl are recovered and fed back round the loop", ZOOM_MS)
        .note(
            "Hydrogen and hydrogen chloride leave the reactors, are recovered, and are fed round the loop again.",
            "pulses of gas going round the ring of pipe",
        )
        .detail(
            "The loop is the reason the chemical cost stays low.",
            &["H2 and HCl recycled", "STC byproduct leaves the loop"],
        ),
    Beat::new("STC can be hydrogenated back to TCS in modern routes", ZOOM_MS)
        .note(
            "In modified Siemens routes the STC byproduct is hydrogenated back to TCS, so it is not lost.",
            "a pulse going the other way round, carrying STC back to TCS",
        )
        .detail(
            "Hydrogenating STC keeps the feed up and the byproduct down.",
            &["Modified Siemens routes", "STC back to TCS"],
        ),
    Beat::new("the growth-rate trade-off: fast growth gives rougher rods", ZOOM_MS)
        .note(
            "Solar grade pushes growth speed and accepts a rough surface. Electronic grade grows slowly and evenly, with a steady ratio and an even temperature.",
            "the fast bar and the slow bar, and the rod thickening more slowly",
        )
        .detail(
            "The same reactor makes two different products depending on speed.",
            &["Electronic: slow, uniform growth", "Solar: speed over surface finish"],
        ),
    Beat::new("rod diameter sets the batch: 20 mm in, 150-180 mm out", ZOOM_MS)
        .note(
            "A slim 20 mm rod goes in and a 150-180 mm rod comes out. The diameter is the measure of the batch.",
            "the rod diameter bar growing to the final size",
        )
        .detail(
            "Diameter is the progress measure through the whole batch.",
            &["20 mm in", "150-180 mm out", "Growth up to 1.9 mm/h"],
        ),
];

/// The four zoom-ins, in the page's order.
pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the fluidized bed",
        build: || -> Box<dyn Scene> {
            clip(
                &BED,
                &include_bytes!("../../../../../tools/pbr3d/assets/poly_zoom_bed.glb")[..],
                BED_BEATS,
            )
        },
    },
    Zoom {
        key: 'b',
        label: "inside a distillation column",
        build: || -> Box<dyn Scene> {
            clip(
                &COLUMN,
                &include_bytes!("../../../../../tools/pbr3d/assets/poly_zoom_column.glb")[..],
                COLUMN_BEATS,
            )
        },
    },
    Zoom {
        key: 'c',
        label: "the Siemens bell jar",
        build: || -> Box<dyn Scene> {
            clip(
                &JAR,
                &include_bytes!("../../../../../tools/pbr3d/assets/poly_zoom_jar.glb")[..],
                JAR_BEATS,
            )
        },
    },
    Zoom {
        key: 'd',
        label: "recycling and the growth-rate trade-off",
        build: || -> Box<dyn Scene> {
            clip(
                &LOOP,
                &include_bytes!("../../../../../tools/pbr3d/assets/poly_zoom_loop.glb")[..],
                LOOP_BEATS,
            )
        },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();
static BED: Cell = std::sync::OnceLock::new();
static COLUMN: Cell = std::sync::OnceLock::new();
static JAR: Cell = std::sync::OnceLock::new();
static LOOP: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/poly_overview.glb"),
        beats: OVERVIEW_BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_and_zooms_are_captioned_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "POLYSILICON overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcd");
        for z in s.zooms() {
            let zs = (z.build)();
            assert_eq!(zs.beats().len(), 4, "zoom {}", z.key);
        }
    }

    #[test]
    fn every_overview_and_zoom_draws_every_beat() {
        let s = build();
        super::super::super::blender::draws_every_beat(s.as_ref(), "POLYSILICON overview");
        for z in s.zooms() {
            super::super::super::blender::draws_every_beat(
                (z.build)().as_ref(),
                "POLYSILICON zoom",
            );
        }
    }
}
