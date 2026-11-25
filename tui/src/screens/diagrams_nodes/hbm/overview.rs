// HBM STACK overview: four DRAM stacks beside a GPU on a silicon interposer, played back from the
// Blender scene (tools/pbr3d/blender/hbm_overview.py) in the picture-and-panel template. The
// stacks pull apart, a read runs down the TSVs, the buses cross the interposer, the stacks grow
// to sixteen dies, and the heat leaves through the top. Zoom-ins a-e are in zoom.rs
// (tools/pbr3d/blender/hbm_zooms.py).
//
// Sources: JEDEC JESD238 (HBM3); JEDEC JESD270-4 (HBM4); SemiEngineering, HBM4 sticks with
// microbumps; Tom's Hardware on the height limit and on CoWoS; TrendForce on CoWoS; PC Watch on
// the HBM3 channel count.

use super::super::blender::{BEAT_MS, Cell, Page};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("a GPU and HBM stacks sit side by side on one silicon interposer", BEAT_MS)
        .note(
            "High-end accelerators place stacks of DRAM right beside the GPU, on a slab of silicon called an interposer that carries thousands of short wires between them.",
            "A purple GPU in the middle, two HBM stacks on each side, all on a grey interposer over a green substrate.",
        )
        .detail(
            "Short wires make a very wide bus possible: 1024 bits per HBM3 stack, far wider than a DIMM.",
            &["HBM3: 1024 data pins, 6.4 Gb/s per pin, 819 GB/s per stack (JEDEC JESD238)"],
        ),
    Beat::new("one stack: a base logic die under DRAM dies", BEAT_MS)
        .note(
            "Each stack is a base logic die with DRAM dies piled on top. Every DRAM die holds memory arrays; the base die talks to the GPU.",
            "One stack close up: a blue base die at the bottom, orange DRAM dies above, and copper TSVs running up through them.",
        )
        .detail(
            "Stacking puts more memory in the same footprint beside the GPU.",
            &["HBM4 allows 4, 8, 12 or 16-high stacks (JEDEC JESD270-4)"],
        ),
    Beat::new("pulled apart: microbumps join each die to the next", BEAT_MS)
        .note(
            "Between the dies are microbumps, tiny solder joints that connect one die to the next at each vertical wire.",
            "The dies separate; yellow microbumps appear in each gap, one at every copper column.",
        )
        .detail(
            "Each joint adds height and must work for the stack to work. HBM4 kept microbumps rather than hybrid bonding.",
            &["Microbump pitch about 40 um, heading towards 10 um (SemiEngineering)"],
        ),
    Beat::new("a read runs down the TSVs to the base die", BEAT_MS)
        .note(
            "Through-silicon vias (TSVs) are copper wires running straight through each thinned die. A read travels down them to the base die.",
            "Yellow dots run down the three copper columns of each stack to the base; the dies close back together.",
        )
        .detail(
            "TSVs only work because the dies are thinned to tens of micrometres.",
            &["Dies thinned to 30-50 um (SemiEngineering)"],
        ),
    Beat::new("the stacks' buses cross the interposer to the GPU", BEAT_MS)
        .note(
            "The base die's PHY drives the wide bus across the interposer to the GPU, millimetres away. Every stack does this at once.",
            "Cyan dots leave each stack's PHY edge and cross the grey interposer into the purple GPU; the outer stacks' dots arc over the inner ones.",
        )
        .detail(
            "Several stacks feed one GPU, and each one adds its own bus.",
            &["HBM3: 819 GB/s per stack (JEDEC JESD238)", "PHY sends 1024 bits (HBM3) or 2048 bits (HBM4)"],
        ),
    Beat::new("taller stacks: more capacity in the same footprint", BEAT_MS)
        .note(
            "Adding dies adds capacity without taking more room beside the GPU. HBM4 allows up to 16-high.",
            "Eight dies grow to sixteen, each new die dropping onto the top of its stack.",
        )
        .detail(
            "Height is capped, so taller stacks need thinner dies and joints.",
            &["HBM4, 16-high with 32 Gb dies: up to 64 GB per stack (JEDEC JESD270-4)", "Height limit raised from 720 to 775 um (press reports)"],
        ),
    Beat::new("heat has to leave through the top", BEAT_MS)
        .note(
            "The dies make heat, and in a tall stack the heat from the lower dies has to pass up through all the others to escape.",
            "The lower dies glow orange, heat rises off the top of the stack, then the stacks settle back to eight dies.",
        )
        .detail(
            "Heat is one reason stack height and bonding are hard.",
            &["Taller stacks add capacity but trap more heat (page section 5)"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "a TSV and its microbumps, cut open",
        build: || -> Box<dyn Scene> { zoom::tsv() },
    },
    Zoom {
        key: 'b',
        label: "the base logic die",
        build: || -> Box<dyn Scene> { zoom::base() },
    },
    Zoom {
        key: 'c',
        label: "channels: one stack, many buses",
        build: || -> Box<dyn Scene> { zoom::channels() },
    },
    Zoom {
        key: 'd',
        label: "microbumps vs hybrid bonding",
        build: || -> Box<dyn Scene> { zoom::bond() },
    },
    Zoom {
        key: 'e',
        label: "CoWoS: more stacks, bigger interposer",
        build: || -> Box<dyn Scene> { zoom::cowos() },
    },
    Zoom {
        key: 'f',
        label: "inside one DRAM die: TSVs, banks, mats, cells",
        build: || -> Box<dyn Scene> { zoom::die() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/hbm_overview.glb"),
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
        super::super::super::blender::explained(s.as_ref(), "HBM STACK overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcdef");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "HBM STACK overview");
    }
}
