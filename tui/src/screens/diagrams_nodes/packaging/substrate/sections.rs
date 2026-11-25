// PACKAGING tab, SUBSTRATE: numbered sections 1-9. Section N illustrates heading N of
// diagrams_pages/PKG_SUBSTRATE.txt, from the Blender scenes in tools/pbr3d/blender/pkg_substrate_sections.py
// (GLBs in tools/pbr3d/assets/pkg_substrate_section_<n>.glb). Three beats each. Sources (10) is text only.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

static S1: Cell = std::sync::OnceLock::new();
static S2: Cell = std::sync::OnceLock::new();
static S3: Cell = std::sync::OnceLock::new();
static S4: Cell = std::sync::OnceLock::new();
static S5: Cell = std::sync::OnceLock::new();
static S6: Cell = std::sync::OnceLock::new();
static S7: Cell = std::sync::OnceLock::new();
static S8: Cell = std::sync::OnceLock::new();
static S9: Cell = std::sync::OnceLock::new();

/// 1 what happens: the stack; fine bumps on top; signals out to coarse balls.
const S1_B: &[Beat] = &[
    Beat::new("between silicon and board", BEAT_MS)
        .note(
            "The package substrate sits under the interposer and on top of the server board. Its job is to connect the two, which have very different pitches.",
            "The whole cut-open stack from above at an angle: die and HBM on the interposer, the thick layered substrate, balls on the green board.",
        )
        .detail("A wiring bridge between two scales.", &["PACKAGE SUBSTRATE"]),
    Beat::new("fine bumps on top", BEAT_MS)
        .note(
            "The interposer's C4 bumps land on the substrate about 150 um apart. Signals enter the substrate here.",
            "Close on the top edge: rows of silver bumps on copper pads in green resist, a few cyan beads dropping into them.",
        )
        .detail("Top side matches the silicon.", &["C4 ~150 um"]),
    Beat::new("out to coarse balls", BEAT_MS)
        .note(
            "Inside, build-up layers carry each signal sideways and down through the core to BGA balls about 1 mm apart.",
            "The right half of the cut face: cyan beads run along glowing traces and down copper barrels into widely spaced balls.",
        )
        .detail("Bottom side matches the board.", &["BUILD-UP LAYERS", "BGA ~1 mm"]),
];

/// 2 the parts: the laminate's layers; one C4 and one BGA joint cut open; organic vs glass core.
const S2_B: &[Beat] = &[
    Beat::new("the laminate's layers", BEAT_MS)
        .note(
            "From the outside in: green solder resist, build-up layers of ABF film and copper, and the core in the middle, the same again on the other face.",
            "The left of the cut face: a green skin, thin cream and copper layers, the brown core with copper barrels.",
        )
        .detail("Resist, build-up, core.", &["ABF FILM", "BUILD-UP LAYERS", "CORE"]),
    Beat::new("one bump, one ball", BEAT_MS)
        .note(
            "A C4 joint is a solder bump on a copper pad in a resist opening, a microvia below the pad and the interposer's pad above. A BGA joint is a much larger ball between a substrate pad and a board pad.",
            "Two joints drawn huge and cut in half: on the left a small bump between copper pads with a tapered via under it; on the right a big ball between a brown substrate and a tan board.",
        )
        .detail("Same idea, two sizes.", &["C4", "BGA"]),
    Beat::new("organic core, glass core", BEAT_MS)
        .note(
            "Today's cores are glass cloth in epoxy, drilled for wide plated holes. A glass core is stiffer and flatter and takes much finer through-glass vias; it is in development.",
            "Two slabs side by side: a brown core with fibres and two fat copper barrels, and a clear blue glass slab with a row of thin copper vias.",
        )
        .detail("The core is changing.", &["GLASS CORE", "Through-glass vias"]),
];

/// 3 in order: core + PTH; build-up layers one by one; resist, pads, bumps.
const S3_B: &[Beat] = &[
    Beat::new("1 a drilled core", BEAT_MS)
        .note(
            "Start with a copper-clad core. Drill through it, plate the holes with copper and plug them with resin.",
            "The bare brown core over the board, copper-lined holes cut in half with dark resin inside.",
        )
        .detail("Step 1.", &["CORE", "Plated through-holes"]),
    Beat::new("2-4 film, via, copper, repeat", BEAT_MS)
        .note(
            "Laminate ABF film, laser-drill microvias through it, then plate and pattern copper. Repeat, each via landing on the pad below it.",
            "A close-up column: cream film layers and copper pads appear one at a time, each with a tapered copper via stacked on the last.",
        )
        .detail("Steps 2 to 4, once per layer.", &["ABF FILM", "Laser microvias"]),
    Beat::new("5 resist and pads", BEAT_MS)
        .note(
            "With all layers on both sides, add solder resist, open it at the pads, then put C4 pads on top and BGA pads below.",
            "Back on the stack: the layers drop onto the core, a green skin covers both faces, then bumps and balls appear.",
        )
        .detail("Step 5.", &["Solder resist", "C4 + BGA pads"]),
];

/// 4 ABF film: the roll; the film in every layer; one supplier's share.
const S4_B: &[Beat] = &[
    Beat::new("a roll of film", BEAT_MS)
        .note(
            "ABF is Ajinomoto Build-up Film: an epoxy resin filled with silica, cast on a PET carrier and covered with a protective film.",
            "A cream roll on a spool with its end unrolled: a clear carrier, the cream film and a clear cover on top.",
        )
        .detail("A film, not a woven sheet.", &["ABF FILM"]),
    Beat::new("between every copper layer", BEAT_MS)
        .note(
            "Each build-up layer starts as a sheet of ABF. It is the insulator in almost every high-end CPU and GPU substrate.",
            "The top build-up up close: cream films between each copper layer, vias through every one.",
        )
        .detail("Twelve films in this stack.", &["In almost every GPU + CPU"]),
    Beat::new("one supplier", BEAT_MS)
        .note(
            "Ajinomoto is estimated to supply about 95% of CPU/GPU-grade build-up film. A single supplier for a material in every AI package is a known chokepoint.",
            "The roll again with two bars beside it: a tall orange bar for Ajinomoto and a sliver of blue for everyone else.",
        )
        .detail("~95% from one maker (estimate).", &["Ajinomoto ~95% (est.)"]),
];

/// 5 layers and size: counting layers; footprints to scale; stacked vs staggered microvias.
const S5_B: &[Beat] = &[
    Beat::new("counting layers", BEAT_MS)
        .note(
            "This drawing has six build-up layers on each face, twelve in all. AI GPU substrates use about 12 to 20.",
            "The cut face from the left, the stacked cream and copper layers above and below the core.",
        )
        .detail("More layers, more routing.", &["12-20 for AI GPUs"]),
    Beat::new("footprints to scale", BEAT_MS)
        .note(
            "Substrate size has grown with the silicon on top: from about 55 mm square for a server CPU to over 100 mm, and an estimated 120 mm class for the biggest AI packages.",
            "Four square slabs stacked like a stepped pyramid, 120, 100, 77.5 and 55 mm, seen from above.",
        )
        .detail("Area goes up with the square.", &["Up to ~120 mm (est.)"]),
    Beat::new("stacked or staggered vias", BEAT_MS)
        .note(
            "Microvias can stack straight on top of each other or step sideways layer by layer. Stacking saves room, which dense GPU routing needs, but is harder to make reliable.",
            "Two columns of four layers: on the left tapered vias stacked straight up, on the right vias stepping sideways at each layer.",
        )
        .detail("Density versus reliability.", &["Stacked microvias"]),
];

/// 6 warpage and glass cores: bowing in reflow; strained corner joints; glass core beside organic.
const S6_B: &[Beat] = &[
    Beat::new("bowing in reflow", BEAT_MS)
        .note(
            "Copper, resin and glass cloth expand by different amounts, so in the reflow oven the big thin laminate bows.",
            "The substrate alone as a hinged slab: heat rises and it bends, middle up and ends down.",
        )
        .detail("Heat makes it bend.", &["WARPAGE"]),
    Beat::new("strained corners", BEAT_MS)
        .note(
            "As it cools it bows the other way. The joints at the ends take the most strain and can crack or open.",
            "Close on the right end: the slab curls up and the last ball glows red.",
        )
        .detail("Corner joints fail first.", &["Corner joint strain"]),
    Beat::new("a stiffer core", BEAT_MS)
        .note(
            "A glass core is stiffer and flatter than an organic one and could carry finer wiring. It is under development.",
            "An organic core with fat copper barrels beside a clear blue glass slab with fine copper vias.",
        )
        .detail("Glass could keep it flat.", &["GLASS CORE"]),
];

/// 7 fan-out: the bump field; signals across layers; power and signals into the balls.
const S7_B: &[Beat] = &[
    Beat::new("the bump field", BEAT_MS)
        .note(
            "Tens of thousands of bumps sit about 150 um apart on top of the substrate.",
            "Looking down on the dense grid of silver bumps in green resist.",
        )
        .detail("Every bump needs a path.", &["C4 ~150 um"]),
    Beat::new("one route per signal", BEAT_MS)
        .note(
            "Each signal takes a stack of microvias down to its layer, a trace across it and a through-hole down the core.",
            "The cut face from the right: cyan beads drop down via stacks and run along glowing traces on four layers.",
        )
        .detail("Fan-out, layer by layer.", &["FAN-OUT"]),
    Beat::new("power and signals together", BEAT_MS)
        .note(
            "Power rides the solid planes while signals ride the traces, all of it ending on balls about 1 mm apart.",
            "The whole cut face: amber planes glowing with yellow beads, cyan traces with cyan beads, all reaching the balls.",
        )
        .detail("Two networks in one laminate.", &["Power planes", "Signal traces"]),
];

/// 8 who makes it: share bars; the film maker; makers tagged on the stack.
const S8_B: &[Beat] = &[
    Beat::new("substrate makers", BEAT_MS)
        .note(
            "One estimate puts high-end FC-BGA share at Ibiden about 35%, Shinko 18%, Unimicron 14%, AT&S 10% and Nan Ya 5%. Another has Unimicron leading by capacity; they measure different things.",
            "Five bars: a tall orange one for Ibiden and shorter blue ones for Shinko, Unimicron, AT&S and Nan Ya.",
        )
        .detail("A handful of makers.", &["SUBSTRATE MAKERS", "Estimates differ"]),
    Beat::new("the film maker", BEAT_MS)
        .note(
            "All of them build on the same film: Ajinomoto's ABF, an estimated 95% of the GPU-grade market.",
            "The roll of ABF, unrolled toward the camera.",
        )
        .detail("One film under all of them.", &["Ajinomoto"]),
    Beat::new("on the stack", BEAT_MS)
        .note(
            "The substrate makers build the laminate; Ajinomoto supplies the film inside it. Ibiden has committed about JPY 500B to new capacity ramping from fiscal 2027.",
            "The whole cut-open stack, tags naming the makers on the laminate and the film.",
        )
        .detail("Capacity is being added.", &["Ibiden ~JPY 500B"]),
];

/// 9 chokepoints: one film supplier; layer-count yield; warpage at size.
const S9_B: &[Beat] = &[
    Beat::new("one film supplier", BEAT_MS)
        .note(
            "Almost all GPU-grade build-up film comes from one company. There is no second source at the same scale.",
            "The roll of ABF alone.",
        )
        .detail("Single source.", &["ABF FILM"]),
    Beat::new("every layer is a yield step", BEAT_MS)
        .note(
            "Each build-up layer is another lamination, drill and plating step that can fail. Few makers can yield 14-plus layer GPU-class substrates.",
            "The left edge of the top build-up, every copper layer glowing red.",
        )
        .detail("Yield compounds by layer.", &["14+ layers"]),
    Beat::new("warpage at size", BEAT_MS)
        .note(
            "Bigger packages warp more, and the joints at their corners take the strain.",
            "The substrate alone bowing with its ends up, its end balls under strain.",
        )
        .detail("Size makes it harder.", &["WARPAGE"]),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9,
        include_bytes!("../../../../../../tools/pbr3d/assets/pkg_substrate_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
