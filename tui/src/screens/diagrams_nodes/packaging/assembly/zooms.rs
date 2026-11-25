// PACKAGING tab, ASSEMBLY: lettered zoom-ins a-e, each its own Blender scene with three beats
// (tools/pbr3d/blender/pkg_assembly_zooms.py, GLBs in tools/pbr3d/assets/pkg_assembly_zoom_<letter>.glb):
// a chip on wafer, b mold and thin, c dice and on substrate, d the lid, e test and yield.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("bumps on the die's face", BEAT_MS)
        .note(
            "The logic die hangs face down over its site. Its metal wiring layers are on the bottom, and a row of copper pillars, each with a solder cap, stands ready to meet the pads on the interposer's top wiring.",
            "A purple die held under a grey bond head, its underside striped with fine copper lines and fringed with tiny pillars; below it the interposer's cut face shows copper TSV columns.",
        )
        .detail("Every signal and every amp passes through these bumps.", &["Cu pillar + solder cap", "Die face down (flip chip)"]),
    Beat::new("THERMOCOMPRESSION BOND", BEAT_MS)
        .note(
            "The bond head presses the die down and heats it, so the solder caps melt and wet the pads. With pillars about 40 micrometres apart, the die must land within a few micrometres.",
            "The head lowers the die onto the interposer; the bump row lights orange as the solder melts, then the head lifts away.",
        )
        .detail("Heat and force, one die at a time.", &["TCB: heat + force", "~40 um bump pitch"]),
    Beat::new("HBM joins; data crosses the RDL", BEAT_MS)
        .note(
            "The HBM stacks bond beside the die. Data leaves each stack's base die through a microbump, runs a few millimetres along the interposer's fine copper wiring, and climbs into the logic die.",
            "Orange stacks drop beside the die; cyan beads run down from a stack's blue base, along a copper line in the interposer's top layer and up into the die.",
        )
        .detail("The interposer's wiring is the memory bus.", &["1,024 data wires per stack", "Still on the wafer"]),
];

const B_B: &[Beat] = &[
    Beat::new("UNDERFILL wicks, MOLD fills", BEAT_MS)
        .note(
            "A needle runs epoxy along the die's edge and capillary action pulls it into the gap among the bumps. Molding compound then fills the spaces between the die and the stacks so the whole site is one solid block.",
            "A syringe needle travels along the die's front edge as a black layer spreads back under it; grey mold drops into the gaps between the purple die and the orange stacks.",
        )
        .detail("Underfill spreads the stress off the tiny joints.", &["UNDERFILL: capillary flow", "Mold: one solid block"]),
    Beat::new("the wafer is ground thin", BEAT_MS)
        .note(
            "The interposer wafer starts about 775 micrometres thick, with its TSVs buried in it. A grinding wheel takes the back down to about 100 micrometres until the copper TSVs reach the surface.",
            "Seen from below: a thick grey slab under the interposer shrinks away as a broad grey wheel on a dark spindle grinds against it.",
        )
        .detail("Thinning opens the TSVs.", &["~775 um > ~100 um (typical)", "Back-grind + polish"]),
    Beat::new("TSV tips revealed, C4 bumps grown", BEAT_MS)
        .note(
            "Each revealed TSV gets a pad, and a larger C4 solder bump is built on it. These bumps, about 130 micrometres across, will join the interposer to the substrate.",
            "A row of silver balls rises onto the bottom of the interposer under each copper TSV column, then glows as it reflows.",
        )
        .detail("Fine pitch on top, coarse pitch below.", &["C4: ~130 um bumps", "One per TSV group"]),
];

const C_B: &[Beat] = &[
    Beat::new("DICING down the street", BEAT_MS)
        .note(
            "A thin diamond blade spinning at high speed cuts along the scribe street between sites. The cut-out interposer keeps its dies, its stacks and its mold.",
            "A steel blade on its axle runs toward the camera along the dark line between the hero site and the next site, throwing a spray of dust.",
        )
        .detail("Each cut-out is one future package.", &["Diamond blade", "Scribe streets between sites"]),
    Beat::new("C4 REFLOW onto the substrate", BEAT_MS)
        .note(
            "The cut interposer is placed on an organic substrate and passed through a reflow oven peaking around 250 C. The C4 bumps melt and join the substrate's copper pads.",
            "The interposer lifts free and settles onto a substrate whose cut face shows tan build-up layers, a green core and copper vias; the C4 row glows orange.",
        )
        .detail("On substrate: the S in CoWoS.", &["C4 REFLOW: ~250 C peak", "ABF build-up + core"]),
    Beat::new("UNDERFILL FLOW, second level", BEAT_MS)
        .note(
            "A needle dispenses underfill along the interposer's edge, and it wicks across the whole C4 field before curing. Without it, the substrate's thermal expansion would crack the C4 joints.",
            "A syringe needle travels along the front edge of the interposer while a black layer creeps back under it.",
        )
        .detail("Two levels of underfill in one package.", &["UNDERFILL FLOW", "Capillary, front to back"]),
];

const D_B: &[Beat] = &[
    Beat::new("TIM on the dies", BEAT_MS)
        .note(
            "A thermal interface sheet, often indium, goes over the logic die and the HBM stacks, which are ground to one height. It fills the microscopic gaps between the silicon and the lid.",
            "A silver sheet drops onto the purple die and the orange stacks, covering them edge to edge.",
        )
        .detail("Air gaps would block the heat.", &["TIM: indium sheet", "Dies + HBM at one height"]),
    Beat::new("the LID is glued on", BEAT_MS)
        .note(
            "A copper lid sits on the TIM and its legs are glued to the substrate. It spreads the heat and stiffens the package against warping.",
            "A copper-coloured lid drops over the package; its side legs land on a pale glue line on the green substrate.",
        )
        .detail("The lid is also a stiffener.", &["Copper lid", "Adhesive to the substrate"]),
    Beat::new("heat leaves through the lid", BEAT_MS)
        .note(
            "Running, the logic die makes on the order of 1,000 W. The heat crosses the TIM into the lid, and a cold plate on top carries it away.",
            "The die glows amber through the cut face and orange beads rise from it, through the silver TIM and the lid, and up out of the top.",
        )
        .detail("Die > TIM > lid > cold plate.", &["~1,000 W class accelerator", "Cold plate on the lid"]),
];

const E_B: &[Beat] = &[
    Beat::new("WAFER SORT: probe every die", BEAT_MS)
        .note(
            "Before assembly, each logic die is tested while still on its own wafer. A probe card lowers a field of fine needles onto the die's pads and runs it; a pass makes it a known-good die.",
            "A green probe card with a grey stiffener lowers its needles onto a purple die on a wafer; violet beads run down the needles and the die lights green.",
        )
        .detail("Catch bad dies while they are cheap.", &["Probe card", "KNOWN-GOOD DIE"]),
    Beat::new("final TEST in a socket", BEAT_MS)
        .note(
            "The finished package sits in a test socket, with a spring pin under every BGA ball. It runs at full power and speed, so power, data and heat all flow as they will in service.",
            "The lidded package sits in a dark socket on rows of pogo pins; yellow, cyan and orange beads run through it and the die glows.",
        )
        .detail("Burn-in and speed binning happen here.", &["Pogo pin on every ball", "At speed, hot"]),
    Beat::new("YIELD STACKUP: ten parts multiply", BEAT_MS)
        .note(
            "The package is good only if every part and every joint is good. Ten parts at 99% each give 0.99 to the tenth, about 90%. When one fails, the whole package is scrapped, HBM included.",
            "Ten bands on the cut face light green one after another, from the die down to the BGA balls; then they all turn red.",
        )
        .detail("Illustrative: 0.99^10 = 0.904.", &["10 parts x 99% = ~90%", "One fails: all scrapped"]),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "chip on wafer",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "mold and thin",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "dice + substrate",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "the lid",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "test and yield",
        build: zoom_e,
    },
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            super::super::super::super::blender::explained(s.as_ref(), z.label);
            super::super::super::super::blender::draws_every_beat(s.as_ref(), z.label);
        }
    }
}
