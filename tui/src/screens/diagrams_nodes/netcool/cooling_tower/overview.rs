// NETWORK+COOL tab, COOLING TOWERS: the page's overview, a Blender scene (tools/pbr3d/blender/net_cooling_tower_overview.py, GLB
// tools/pbr3d/assets/net_cooling_tower_overview.glb). Seven beats: a tower beside the plant, spray, fill, fan and evaporation,
// drift eliminators, water use, and heat out to the air.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_cooling_tower_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The 7 beats of the overview (match net_cooling_tower_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a tower beside the plant", BEAT_MS)
        .note(
            "A water-cooled chiller plant needs somewhere to dump its heat. Its condenser sends warm water, around 35 C, to a cooling tower outside and gets it back about 6 C cooler.",
            "A grey chiller barrel on a skid at the left, an open-fronted tower at the right with a fan on top; an amber pipe climbs to the tower and a blue pipe returns.",
        )
        .detail(
            "The tower is where the heat leaves.",
            &["WARM WATER ~35 C out", "COOLED ~29 C back"],
        ),
    Beat::new("spray", BEAT_MS)
        .note(
            "The warm water is pumped to the top of the tower and spread over the fill by a header and rows of nozzles.",
            "A white pipe header across the top of the tower with amber beads running along it and out of the nozzle arms.",
        )
        .detail(
            "Spread the water wide.",
            &["SPRAY HEADER", "Nozzles"],
        ),
    Beat::new("fill", BEAT_MS)
        .note(
            "The water runs down the fill, stacks of corrugated plastic sheets that spread it into thin films. Air drawn in through the louvers rises through it.",
            "Blue film lines on the grey fill; amber drops above turn blue below; pale air beads enter from both sides.",
        )
        .detail(
            "Thin films, lots of surface.",
            &["FILL", "Air in through louvers"],
        ),
    Beat::new("fan and evaporation", BEAT_MS)
        .note(
            "The fan on top pulls the air up and out. About 1% of the water evaporates on its way down, and that carries away most of the heat.",
            "The fan spinning in its stack; white vapour beads rise in a plume above the tower.",
        )
        .detail(
            "Evaporation does the cooling.",
            &["FAN: induced draft", "~1% evaporates"],
        ),
    Beat::new("drift eliminators", BEAT_MS)
        .note(
            "Above the spray, chevron blades make the air turn sharply. Droplets can't follow the turn, hit the blades and drain back; only vapour leaves.",
            "Close on the zig-zag blades above the header; amber droplets rise, hit them and fall back.",
        )
        .detail(
            "Keep the water in.",
            &["DRIFT ELIMINATORS", "Droplets fall back"],
        ),
    Beat::new("water use", BEAT_MS)
        .note(
            "The evaporated water has to be replaced through a make-up meter, and some basin water is bled off as blowdown so minerals do not build up.",
            "A brass meter with a spinning needle; green beads run into the basin; blue beads drain out at the far corner.",
        )
        .detail(
            "Water in, water out.",
            &["MAKE-UP WATER", "BLOWDOWN"],
        ),
    Beat::new("heat out", BEAT_MS)
        .note(
            "Everything runs at once. The heat from the racks, carried by water through the chiller, finally leaves the site as water vapour into the outdoor air.",
            "A wide view: pipes lit, fan spinning, a tall white plume climbing into the sky.",
        )
        .detail(
            "Where every watt ends up.",
            &["HEAT OUT: to the air", "~1.5-2 L per kWh"],
        ),
];
