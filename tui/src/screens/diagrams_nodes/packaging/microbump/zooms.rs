// PACKAGING tab, MICROBUMP: lettered zoom-ins a-e, each its own Blender scene with its own parts, beads and
// cameras (tools/pbr3d/blender/pkg_microbump_zooms.py, GLBs in tools/pbr3d/assets/pkg_microbump_zoom_<letter>.glb):
// a C4, microbump, hybrid bond; b making a joint; c pitch and the solder wall; d stress, warpage and underfill;
// e current through the bumps.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(&ZA, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_zoom_a.glb"), A_B)
}

fn zoom_b() -> Box<dyn Scene> {
    page(&ZB, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_zoom_b.glb"), B_B)
}

fn zoom_c() -> Box<dyn Scene> {
    page(&ZC, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_zoom_c.glb"), C_B)
}

fn zoom_d() -> Box<dyn Scene> {
    page(&ZD, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_zoom_d.glb"), D_B)
}

fn zoom_e() -> Box<dyn Scene> {
    page(&ZE, include_bytes!("../../../../../../tools/pbr3d/assets/pkg_microbump_zoom_e.glb"), E_B)
}

const A_B: &[Beat] = &[
    Beat::new("C4 BUMP: ~150 um pitch", BEAT_MS)
        .note(
            "A C4 bump is a solder ball about 100 um across, set on 150 um centres between the interposer and the substrate. It is cut in half here so its solid solder body shows between its two pads.",
            "A large grey ball, sliced flat on the front, between a copper pad below and a grey pad above; an amber bead climbs through it.",
        )
        .detail(
            "The coarsest joint inside the package.",
            &["C4 BUMP ~150 um", "Interposer to substrate"],
        ),
    Beat::new("MICROBUMP: ~40 um pitch", BEAT_MS)
        .note(
            "A microbump is a copper pillar about 25 um wide with a thin tin-silver cap, set on 40 um centres under the dies. The copper does not melt, so neighbours stay apart at a pitch a ball could not reach.",
            "A cut-open column: a brown copper post on top, a grey nickel band, then grey solder with thin bronze layers, standing on a copper pad.",
        )
        .detail(
            "About 14x the joints per mm2 of C4 ((150/40)^2).",
            &["MICROBUMP ~40 um", "CU PILLAR + solder cap"],
        ),
    Beat::new("HYBRID BOND: <=10 um pitch", BEAT_MS)
        .note(
            "A hybrid bond has no bump at all: copper pads set flush in oxide on both faces, bonded directly. Side by side at one scale, the C4 ball dwarfs the microbump, and the microbump dwarfs the hybrid pads.",
            "The three joints in a row at the same scale: the big ball at the left, the slim pillar in the middle, and a thin pale strip with tiny copper pads at the right.",
        )
        .detail(
            "Each step down multiplies the connections.",
            &["HYBRID BOND <=10 um", "No solder"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("plate the pillars, cap them", BEAT_MS)
        .note(
            "On the wafer, copper pillars are electroplated up through a patterned resist onto the die's pads, a nickel barrier goes on top, and then a tin-silver solder cap.",
            "A die hangs face down above a slab: copper beads drift up onto bare brown pillars, then grey beads build a rounded solder dome on each tip.",
        )
        .detail(
            "Plating sets the pillar's height and width.",
            &["CU PILLAR", "SnAg cap on Ni"],
        ),
    Beat::new("place face down, reflow", BEAT_MS)
        .note(
            "The die is flipped and placed so each pillar lands on its pad. Heated to about 250 C, the solder melts, wets the pad and freezes into a joint, growing thin intermetallic layers at both ends.",
            "The die lowers onto the pads; the solder flashes orange as it melts, heat rises from below, and the domes settle into straight-sided joints.",
        )
        .detail(
            "Thermocompression bonding is used at the finest pitches.",
            &["REFLOW ~250 C", "IMC forms at both ends"],
        ),
    Beat::new("underfill", BEAT_MS)
        .note(
            "Liquid epoxy is dispensed along one edge and drawn into the gap by capillary action, then cured into a solid that grips every joint.",
            "Warm beads run along the gap; dark fill appears between the pillars and forms a fillet at the die edge.",
        )
        .detail(
            "The joints now share the load with the epoxy.",
            &["UNDERFILL", "Capillary flow, then cure"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("halve the pitch, 4x the joints", BEAT_MS)
        .note(
            "Connection density goes with one over the pitch squared: halve the spacing and four times as many joints fit under the same die. Three rows show the same bumps closing up.",
            "Three rows of solder bumps on a pale slab, each row spaced closer than the one in front.",
        )
        .detail(
            "Density is what limits die-to-die bandwidth.",
            &["BUMP PITCH", "density ~ 1 / pitch^2"],
        ),
    Beat::new("solder bridges near 10 um", BEAT_MS)
        .note(
            "A solder cap needs a minimum volume to make a good joint. At the tightest pitch the molten caps touch and bridge their neighbours, shorting them; microbumps hit this wall around 10 um.",
            "The back row's balls almost touch; red glowing bridges join each one to the next.",
        )
        .detail(
            "Below the wall, solder stops working.",
            &["Solder bridging", "~10 um wall"],
        ),
    Beat::new("hybrid bonds past the wall", BEAT_MS)
        .note(
            "Hybrid bonding drops the solder entirely: copper pads set flush in oxide on both faces bond directly, so the pitch can fall to a few um. The price is surfaces that must be almost perfectly flat and clean.",
            "A cut-open block: a purple die on top, a pale oxide layer with copper pads joined straight through it to matching pads below.",
        )
        .detail(
            "TSMC uses this for SoIC die stacking.",
            &["HYBRID BOND", "SoIC"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("different expansion rates", BEAT_MS)
        .note(
            "The die and interposer are silicon, which grows about 3 ppm per degree. The organic substrate grows several times more. As the package heats in use, the levels want to change size by different amounts.",
            "A small cut-away package, die on microbumps on an interposer on C4 balls on a green-and-tan substrate, with heat rising off the die.",
        )
        .detail(
            "The joints sit between materials that disagree.",
            &["CTE mismatch", "Si ~3 ppm/C"],
        ),
    Beat::new("the substrate bows, the corners strain", BEAT_MS)
        .note(
            "The substrate grows more than the silicon above it, so the package bows. The joints at the outer edges move the most and take the most shear; that is where fatigue cracks start.",
            "The substrate bends at its middle; the outermost C4 balls glow red.",
        )
        .detail(
            "Warpage also makes assembly harder.",
            &["WARPAGE", "Corner joints first"],
        ),
    Beat::new("underfill spreads the load", BEAT_MS)
        .note(
            "With underfill, the epoxy bonds the levels together so the strain is spread over the whole area instead of the outer joints; for C4 joints it gives over ten times the thermal-cycle life.",
            "The substrate flattens again and dark underfill fills between the balls; the red glow is gone.",
        )
        .detail(
            "Totta (UCLA Pb-free workshop).",
            &["UNDERFILL", ">10x C4 cycle life"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("current through one joint", BEAT_MS)
        .note(
            "All the power for the die enters through its bumps; a large die has thousands of them given over to power and ground. Electrons stream down through each pillar, its solder and its pad.",
            "One microbump drawn large and cut open between a slab of die and a slab of interposer, with blue beads streaming down through it.",
        )
        .detail(
            "Each joint carries its share of hundreds of amps.",
            &["Power bumps", "1,000s per die"],
        ),
    Beat::new("electromigration opens a void", BEAT_MS)
        .note(
            "At high current density the electron flow pushes metal atoms along with it. Over time atoms leave the solder by the intermetallic layer where the current crowds in, and a void opens and grows until the joint fails.",
            "Close on the top of the solder: a dark gap spreads along the thin bronze layer under the nickel.",
        )
        .detail(
            "Smaller bumps mean more current density each.",
            &["ELECTROMIGRATION", "Void at the IMC"],
        ),
    Beat::new("more bumps share the load", BEAT_MS)
        .note(
            "The fix is more joints: split the same current across many smaller bumps and the density in each falls. That is one reason power delivery eats so many bump sites under a big die.",
            "A row of six smaller pillars beside the big one, each with a thin stream of blue beads.",
        )
        .detail(
            "Bump count is a power budget as much as a signal one.",
            &["Split the current", "Lower density per bump"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "C4, microbump, hybrid bond", build: zoom_a },
    Zoom { key: 'b', label: "making a joint", build: zoom_b },
    Zoom { key: 'c', label: "pitch and the solder wall", build: zoom_c },
    Zoom { key: 'd', label: "stress, warpage and underfill", build: zoom_d },
    Zoom { key: 'e', label: "current through the bumps", build: zoom_e },
];
