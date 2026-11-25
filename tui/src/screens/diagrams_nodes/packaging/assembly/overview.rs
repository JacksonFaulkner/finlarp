// PACKAGING tab, ASSEMBLY: the page's overview, a Blender scene (tools/pbr3d/blender/pkg_assembly_overview.py, GLB
// tools/pbr3d/assets/pkg_assembly_overview.glb). Seven beats: known-good dies, chip on wafer, HBM joins, underfill,
// mold and dicing, on substrate, lid and test, and the capacity of the line.

use super::super::super::blender::{BEAT_MS, Cell, Page};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/pkg_assembly_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview (match pkg_assembly_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("known-good dies arrive", BEAT_MS)
        .note(
            "Logic dies and HBM stacks reach assembly only after they pass wafer-level test. A die that failed at sort is left out, because once it is bonded it takes every other part down with it.",
            "A dark tray at the left: six purple logic dies in pockets and six orange HBM stacks; green marks light on the good dies, and one die lights red.",
        )
        .detail(
            "Assembly starts from tested parts only.",
            &["KNOWN-GOOD DIE: tested at wafer sort", "One bad die scraps the package"],
        ),
    Beat::new("CHIP ON WAFER: the die bonds", BEAT_MS)
        .note(
            "The interposer is still part of a whole 300 mm silicon wafer. A bond head picks the logic die, flips it face down and presses it onto its site with heat and force, so its microbumps join the interposer's pads.",
            "A grey wafer with ruled streets and dies on its other sites; at the front edge, cut open, the bond head lowers a purple die onto the hero site and a row of microbumps glows.",
        )
        .detail(
            "Chip on wafer: bonding before cutting.",
            &["CHIP ON WAFER", "Microbumps: ~40 um pitch"],
        ),
    Beat::new("HBM stacks join", BEAT_MS)
        .note(
            "Four HBM stacks land beside the die, one at a time, and bond the same way. Every site on the wafer is filled before anything is cut.",
            "Orange stacks drop onto the interposer either side of the purple die; across the wafer every site gains its four stacks.",
        )
        .detail(
            "Memory sits millimetres from the logic.",
            &["4 HBM stacks per site here", "Every site filled at once"],
        ),
    Beat::new("underfill, mold, then dice", BEAT_MS)
        .note(
            "Epoxy underfill wicks under the dies and cures, and molding compound fills the gaps between them. The wafer is thinned to its TSVs and then a diamond blade cuts along the streets into separate interposers.",
            "Black underfill appears under the die and grey mold between the dies; the camera pulls back and two thin dicing blades run down the streets either side of the site.",
        )
        .detail(
            "Protect the joints, then cut.",
            &["UNDERFILL + mold", "Dicing along the scribe streets"],
        ),
    Beat::new("ON SUBSTRATE: C4 reflow and underfill", BEAT_MS)
        .note(
            "The cut interposer, now carrying C4 bumps on its back, lands on an organic substrate. Reflow melts the C4 solder into joints, and a needle dispenses a second underfill along the edge that wicks in under the whole interposer.",
            "The package lifts and settles on a green and tan substrate with copper layers in its cut face; the C4 row glows, then a syringe needle travels along the front edge.",
        )
        .detail(
            "Chip on wafer on substrate: CoWoS.",
            &["C4 REFLOW", "UNDERFILL FLOW: second level"],
        ),
    Beat::new("lid on, powered up for TEST", BEAT_MS)
        .note(
            "An indium thermal interface goes on the dies and a copper lid is glued to the substrate over them. At final test, power climbs up from the BGA balls, data crosses between HBM and die, and heat leaves up through the lid.",
            "A silver sheet and then a copper lid drop onto the package; yellow beads rise through the substrate into the die, cyan beads cross the interposer and orange beads leave through the lid.",
        )
        .detail(
            "Test the finished package before it ships.",
            &["TIM + lid", "TEST: full power, at speed"],
        ),
    Beat::new("CAPACITY: the line sets the output", BEAT_MS)
        .note(
            "Each finished package used one site on an interposer wafer, and a 300 mm wafer holds only about 15 to 20 of the largest ones. CoWoS capacity, counted in wafers a month, has limited how many AI accelerators ship.",
            "A dark conveyor belt with lidded packages moving along it in a row.",
        )
        .detail(
            "Packaging, not wafers, has been the limit.",
            &["CAPACITY: wafers a month", "~15-20 big packages per wafer"],
        ),
];
