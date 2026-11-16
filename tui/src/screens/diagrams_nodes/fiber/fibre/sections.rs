// OPTICAL FIBER: numbered sections 1-9, one Blender close-up per idea (tools/pbr3d/blender/fiber_fibre_sections.py,
// GLBs in tools/pbr3d/assets/fiber_fibre_section_<n>.glb). Each section is three 8 s beats.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static S1_CELL: Cell = std::sync::OnceLock::new();
static S2_CELL: Cell = std::sync::OnceLock::new();
static S3_CELL: Cell = std::sync::OnceLock::new();
static S4_CELL: Cell = std::sync::OnceLock::new();
static S5_CELL: Cell = std::sync::OnceLock::new();
static S6_CELL: Cell = std::sync::OnceLock::new();
static S7_CELL: Cell = std::sync::OnceLock::new();
static S8_CELL: Cell = std::sync::OnceLock::new();
static S9_CELL: Cell = std::sync::OnceLock::new();

/// 1 What happens: light stays trapped in a glass core for kilometres.
const S1_B: &[Beat] = &[
    Beat::new("light rides a glass core", BEAT_MS)
        .note(
            "Light from the laser enters the core, a glass channel about 8 µm across. Around it, 125 µm of cladding glass with a slightly lower refractive index acts as a mirror, and a plastic coating 242 µm across protects the glass. Drawn to scale, 1 mm for 5 µm, and cut in half.",
            "The top fibre: the glowing orange core line through the middle, the grey cladding round it, then the cream and blue coating layers, stopped short at the right so the bare glass shows.",
        )
        .detail(
            "Only the glass carries light; the coating protects it.",
            &["Core ~8 µm (single-mode)", "Cladding 125 µm", "Coating 242 µm"],
        ),
    Beat::new("the cladding acts as a mirror", BEAT_MS)
        .note(
            "Light that meets the core-cladding boundary at a shallow angle reflects back in completely: total internal reflection. In this multimode fibre the core is 50 µm wide, so the reflections show as a ray bouncing from wall to wall.",
            "The bottom fibre: an orange ray zig-zags down the wide pale-blue core, turning back each time it reaches the grey cladding. Its coating is aqua.",
        )
        .detail(
            "A lower-index boundary at a shallow angle reflects all the light.",
            &["Multimode core: 50 µm", "Total internal reflection: no light lost at the wall"],
        ),
    Beat::new("one beam, or many paths", BEAT_MS)
        .note(
            "In single-mode fibre the core is so narrow that the light travels as one beam straight down it. In multimode fibre the wider core lets many paths bounce along at different angles. Both keep the light trapped for kilometres in single-mode, or about 100 m usefully in multimode.",
            "Both fibres together: the single beam glowing straight down the top core, and two orange rays at different angles bouncing down the wide bottom core.",
        )
        .detail(
            "Section 5 compares the two.",
            &["Single-mode: one path, buildings and beyond", "Multimode: many paths, up to ~100 m"],
        ),
];

/// 2 The parts.
const S2_B: &[Beat] = &[
    Beat::new("CORE, CLADDING, COATING", BEAT_MS)
        .note(
            "A single-mode fibre is stripped back in steps and cut in half so every part shows, to scale (1 mm for 5 µm). The core is glass with a slightly higher index; the cladding is glass with a lower index that keeps the light in; the acrylate coating protects the glass from scratches and bends.",
            "From the outside in: the blue outer coating and cream inner coating (stopped short), the grey cladding, and the thin glowing core ending at the half-disc end face on the right.",
        )
        .detail(
            "The coating is 242 µm on standard fibre, 200 µm on reduced-diameter versions.",
            &["Core: ~8.2 µm (single-mode)", "Cladding: 125 µm", "Coating: 242 µm (or 200 µm)"],
        ),
    Beat::new("CORE and MODE FIELD", BEAT_MS)
        .note(
            "Close up at the end face. The core is about 8.2 µm across, but the light it guides spreads slightly into the cladding: the mode field, the width the light actually occupies, is 9.2 µm at 1310 nm. In multimode fibre the core is far wider, 50 µm.",
            "The end face: the small bright core dot, the faint orange ring round it that marks the 9.2 µm mode field, and the grey cladding disc out to its 125 µm edge.",
        )
        .detail(
            "Connectors must line up the mode fields, not just the glass.",
            &["Core: ~8.2 µm (SM), 50 µm (MM)", "Mode field: 9.2 µm at 1310 nm"],
        ),
    Beat::new("COATING: protects the glass", BEAT_MS)
        .note(
            "Bare glass this thin scratches easily, and a scratch can grow into a break. The acrylate coating goes on in two layers: a soft inner one that cushions the glass against bends, and a harder outer one that resists scratches.",
            "The step where the coating ends: the cream inner layer against the grey glass, the blue outer layer over it, and the bare cladding running on to the right with the lit core inside.",
        )
        .detail(
            "Coating is applied as the fibre is drawn (section 8).",
            &["Coating: acrylate, 242 µm (or 200 µm)", "Cladding: 125 µm"],
        ),
];

/// 3 Light down the fiber, in order.
const S3_B: &[Beat] = &[
    Beat::new("1-2: a lens focuses light into the core", BEAT_MS)
        .note(
            "Step 1: a lens focuses the laser's light onto the core's end. Step 2: light that enters within the acceptance angle stays in the core; light outside that cone is lost. The fibre is drawn to scale, the laser and lenses are not.",
            "On the left, the steel laser can on its block, its pale orange beam spreading to the glass lens on its post, then narrowing to a point on the end of the cut fibre's core.",
        )
        .detail(
            "Focusing onto an ~8 µm core needs precise alignment.",
            &["Core ~8.2 µm", "Light must arrive inside the acceptance angle"],
        ),
    Beat::new("3-4: guided along, a little lost", BEAT_MS)
        .note(
            "Step 3: the light is guided along the core (in multimode fibre it reflects; in single-mode it travels as one guided mode). Step 4: a little is scattered and absorbed in every kilometre of glass.",
            "The middle of the cut fibre: pulses running along the glowing core, and small bright sparks flying out sideways through the cladding and coating.",
        )
        .detail(
            "Section 6 puts a number on the loss.",
            &["~0.32 dB/km at 1310 nm (SMF-28 Ultra, max)", "~0.18 dB/km at 1550 nm"],
        ),
    Beat::new("5: out into the receiver's lens", BEAT_MS)
        .note(
            "Step 5: the light leaves the far end of the core as a widening cone, and the receiver's lens collects it onto the photodiode, which turns it back into an electrical signal.",
            "On the right, the pale cone leaving the fibre's end face, the receiver lens on its post, and the light narrowing onto the window of the steel photodiode can.",
        )
        .detail(
            "Next station: the PHOTODIODE.",
            &["Light leaves the core into the receiver's lens"],
        ),
];

/// 4 Why the light stays in.
const S4_B: &[Beat] = &[
    Beat::new("light meets the wall at a grazing angle", BEAT_MS)
        .note(
            "Light travelling nearly along the fibre meets the core-cladding boundary at a grazing angle. The core here is drawn wide (a multimode-sized 50 µm, to scale) and the angles steep, so the bounces fit in the picture.",
            "The orange ray comes in from the upper left, enters the round end face and runs into the pale-blue core band between the grey cladding bands.",
        )
        .detail(
            "The core's index is only slightly above the cladding's.",
            &["Index step ~1/3 % (single-mode)", "Grazing rays are the ones kept"],
        ),
    Beat::new("total internal reflection", BEAT_MS)
        .note(
            "At a grazing angle the boundary reflects the light completely: total internal reflection. A ray that hits the wall too steeply is not reflected; it crosses into the cladding and leaks out of the fibre.",
            "The orange ray turns back at the top wall of the core; the dashed white line is the normal to the wall there. The blue ray comes in steeply, crosses the core and cladding, and escapes upward.",
        )
        .detail(
            "That is enough to keep light in for kilometres.",
            &["Shallow angle: reflects completely", "Steep angle: leaks out"],
        ),
    Beat::new("single-mode: one guided mode", BEAT_MS)
        .note(
            "In single-mode fibre the core is only a few wavelengths across, so the light travels as one guided mode rather than as bouncing rays. That mode runs partly in the cladding: it is 9.2 µm wide at 1310 nm, a little wider than the ~8.2 µm core.",
            "A single-mode fibre to scale: the thin glowing core, the faint orange band round it showing the wider mode field, and the orange ring on the end face where the mode meets the air.",
        )
        .detail(
            "The index step is only about a third of a percent.",
            &["Mode field: 9.2 µm at 1310 nm", "Core ~8.2 µm", "Index step ~1/3 %"],
        ),
];

/// 5 Single-mode vs multimode.
const S5_B: &[Beat] = &[
    Beat::new("MULTIMODE: easy to light", BEAT_MS)
        .note(
            "Multimode fibre's 50 µm core accepts light easily from cheap 850 nm VCSELs: a laser chip that emits straight up from its surface, here butted almost against the fibre end. No precise lens is needed.",
            "Top left: the dark VCSEL chip on its brown submount and steel post, its round glowing aperture throwing a short cone into the wide pale-blue core.",
        )
        .detail(
            "Cheap light, easy alignment.",
            &["Multimode core: 50 µm", "Source: 850 nm VCSEL"],
        ),
    Beat::new("many paths: pulses smear", BEAT_MS)
        .note(
            "Inside the wide core light takes many paths of different lengths. Pulses sent together arrive spread out, and after about 100 m they smear into each other.",
            "The multimode core: three orange paths, one straight and two zig-zags at different angles, with pulses on each drifting apart (timing exaggerated).",
        )
        .detail(
            "Path-length differences set the reach.",
            &["Multimode reach: up to ~100 m"],
        ),
    Beat::new("SINGLE-MODE: precise, but far", BEAT_MS)
        .note(
            "Single-mode fibre's narrow core needs precise alignment and InP lasers, focused through a lens. In exchange, pulses stay sharp over kilometres. AI clusters increasingly use single-mode even inside the building.",
            "Bottom: the small blue InP laser chip on its submount, its beam through a glass ball lens on a post, narrowing onto the thin core; one orange path runs straight down it with sharp pulses.",
        )
        .detail(
            "Single-mode reaches buildings and beyond.",
            &["Single-mode core ~8.2 µm", "Source: InP laser", "Pulses sharp over km"],
        ),
];

/// 6 Attenuation: how little light is lost.
const S6_B: &[Beat] = &[
    Beat::new("loss: scattering in the glass", BEAT_MS)
        .note(
            "Attenuation comes from scattering in the glass itself, plus residual absorption. A tiny fraction of the light is thrown out of the core in every kilometre.",
            "A close-up of the cut single-mode fibre (to scale): pulses on the glowing core and small bright sparks flying out sideways through the grey cladding and the coatings.",
        )
        .detail(
            "Loss is lower at 1550 nm than at 1310 nm.",
            &["≤0.32 dB/km at 1310 nm (SMF-28 Ultra)", "≤0.18 dB/km at 1550 nm"],
        ),
    Beat::new("1 km: about 7% lost", BEAT_MS)
        .note(
            "Power meters at each end of a kilometre at 1310 nm would read at most 0.32 dB apart. That is about 7% of the light; more than nine-tenths arrives.",
            "Two handheld power meters joined by the fibre: the green input bar on the left and the output bar on the right, only slightly shorter.",
        )
        .detail(
            "Decibels add along a link.",
            &["0.32 dB ≈ 7% of the light", "Corning SMF-28 Ultra, max at 1310 nm"],
        ),
    Beat::new("the connectors cost more than the glass", BEAT_MS)
        .note(
            "A 2 km data-center link loses under 1 dB in the glass. That is less than its connectors, so in a building it is the joints, not the fibre, that use up most of the loss.",
            "The output end close up: the fibre running into the black connector boot on the meter, with the output bar on the screen.",
        )
        .detail(
            "Inside a data center the glass is almost lossless.",
            &["2 km × 0.32 dB/km ≈ 0.64 dB", "Connectors lose more than the glass"],
        ),
];

/// 7 Latency: the speed of light in glass.
const S7_B: &[Beat] = &[
    Beat::new("1 km of glass: ~5 µs", BEAT_MS)
        .note(
            "Light in glass travels at about two-thirds of its speed in vacuum: roughly 5 microseconds per kilometre. A spool of fibre holds kilometres of it. Not to scale.",
            "A dark spool on a steel axle and stand, wound with blue coated fibre; a bright pulse runs round the outer turns.",
        )
        .detail(
            "About 5 µs per km.",
            &["Speed in glass: ~2/3 of vacuum", "~5 µs per km"],
        ),
    Beat::new("negligible in a building, not between sites", BEAT_MS)
        .note(
            "Across a building those microseconds are negligible next to the electronics. Across a campus, or between data centers, they add up.",
            "The outer turns light up orange one after another as the light runs the whole length of the spool.",
        )
        .detail(
            "Distance, not the glass, sets the delay.",
            &["~5 µs per km", "Campus or DC-to-DC: it adds up"],
        ),
    Beat::new("HOLLOW-CORE: light in air", BEAT_MS)
        .note(
            "Hollow-core fibre guides light in air instead of glass, through a central hole surrounded by thin glass tubes. Light in air is faster, so it cuts latency by about a third.",
            "Two cut samples on stands. Top: hollow-core fibre, a ring of thin glass tubes inside an outer glass tube, with an open centre. Bottom: ordinary solid glass fibre. Pulses start together; the top ones arrive first.",
        )
        .detail(
            "Hollow-core is newer and less common.",
            &["Hollow-core: ~1/3 less latency"],
        ),
];

/// 8 Who makes it.
const S8_B: &[Beat] = &[
    Beat::new("PREFORM: where fibre starts", BEAT_MS)
        .note(
            "Fiber is drawn from a glass preform: a large rod of glass with the core already inside it, in the same proportions as the finished fibre. Corning (GLW) is the largest maker of optical fiber. Not to scale.",
            "The top of a draw tower cut in half: the grey-blue preform rod with its thin pale core rod down the centre, hung from a seed rod and holder above the glowing furnace.",
        )
        .detail(
            "A few companies make most of the world's fibre.",
            &["Corning (GLW): largest maker", "Also Prysmian, Fujikura, Sumitomo Electric"],
        ),
    Beat::new("drawn in a tower", BEAT_MS)
        .note(
            "The tip of the preform softens in the furnace and is pulled into a thin fibre; the core shrinks with it. A gauge below checks that the glass comes out 125 µm across.",
            "Inside the glowing orange furnace the rod narrows into a cone and becomes a thin fibre; below, it passes between the two grey gauge heads and their red laser line. Bright marks ride down with the moving fibre.",
        )
        .detail(
            "Every fibre must come out the same size.",
            &["Cladding: 125 µm", "Also Furukawa (OFS), YOFC"],
        ),
    Beat::new("coated on the fly, wound on spools", BEAT_MS)
        .note(
            "The fibre is coated on the fly, cured, and pulled by a capstan onto spools many kilometres long.",
            "The grey coating die where the fibre turns blue, two UV lamp housings glowing violet on either side, and the spoked capstan wheel at the bottom with the blue fibre wrapped round it.",
        )
        .detail(
            "Coating protects the glass before anything touches it.",
            &["Coated on the fly", "Spools many km long"],
        ),
];

/// 9 Chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("many times more fibre per rack", BEAT_MS)
        .note(
            "AI data centers use many times more fiber per rack than cloud ones, which strains cable and connector capacity. Multi-fibre MPO connectors like this one carry a whole ribbon of fibres in one plug, lined up by steel guide pins.",
            "Two dark MT ferrules, turned so their row of 12 fibres lies in the cut, slide together and mate; the ribbon behind shows the 12 colour-coded fibres, and pulses cross all 12 joints at once.",
        )
        .detail(
            "Cable and connector supply is the pinch point.",
            &["AI racks: many times more fibre than cloud", "MPO: 12 fibres per plug"],
        ),
    Beat::new("tight bends leak light", BEAT_MS)
        .note(
            "Bend a fibre too tightly and the light meets the core wall too steeply to be reflected, so it leaks out. Dense cabling makes tight bends common, so it needs bend-insensitive fiber.",
            "A yellow-jacketed fibre with a tight loop round a dark peg: pulses run along its glowing core, and bright sparks fly outward from the loop where light escapes. Not to scale.",
        )
        .detail(
            "Bend-insensitive fibre tolerates tighter bends.",
            &["Tight bends leak light", "Dense cabling needs bend-insensitive fibre"],
        ),
    Beat::new("dirty end faces fail links", BEAT_MS)
        .note(
            "Dirty connector end faces are a leading cause of link failures. A speck of dust on the polished tip of a ferrule blocks or scatters the light where it should cross into the next fibre.",
            "An LC ferrule tip close up: the white zirconia body and its polished end face with brown dust specks on it, and bright sparks scattering off the face as light arrives along the core.",
        )
        .detail(
            "Inspect and clean before plugging in.",
            &["Dirty end faces: a leading cause of link failures"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &S1_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &S2_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &S3_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &S4_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &S5_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &S6_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &S7_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &S8_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &S9_CELL,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
