// DEVELOP: the page's overview, a Blender scene (tools/pbr3d/blender/develop_overview.py, GLB
// tools/pbr3d/assets/develop_overview.glb). A slice across the wafer on a vacuum chuck, inside a
// cut-away develop cup on the track: a TMAH puddle, the exposed resist dissolving and draining, the
// rinse, a bridge, and the stencil going on to etch. Six beats, no zoom-ins.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/develop_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The six beats of the overview, one per step (match develop_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("the pattern is still hidden", BEAT_MS)
        .note(
            "Exposure and the bake leave an invisible pattern. In a positive resist, the light has changed the exposed resist so the developer will dissolve it, but nothing has come off the wafer yet. The develop module on the coater/developer track is where the pattern appears.",
            "A slice across the wafer: silicon, a film, and amber resist lines standing on it. The spaces between the lines glow pale amber, the latent image. Behind, the hot plate and the cool plate of the track.",
        )
        .detail(
            "Positive resist: exposed areas dissolve.",
            &["Developer: aqueous TMAH, 2.38 wt%", "Dissolves only the exposed resist"],
        ),
    Beat::new("a puddle of developer", BEAT_MS)
        .note(
            "A nozzle lays a puddle of developer on the wafer, held there by surface tension. The TMAH dissolves the exposed resist and leaves the rest. The developer can also be applied by dip or spray, depending on the product.",
            "The develop nozzle swings in over the wafer. A translucent blue puddle spreads across the resist. The amber spaces sink away, and orange flecks of dissolved resist run down the cup drain.",
        )
        .detail(
            "Developer sits on the wafer as a puddle.",
            &["2.38 wt% TMAH in water", "Typical process: a 60 s puddle (SST study)"],
        ),
    Beat::new("trenches open", BEAT_MS)
        .note(
            "Where the resist was exposed, it is gone and a trench opens down to the film. The resist that light never reached stands in lines. This open pattern is the stencil that etch will copy into the film.",
            "The profile across the slice: resist lines standing tall, a clean trench between each pair, and the puddle drained away into the cup.",
        )
        .detail(
            "The developed resist is a stencil.",
            &["Unexposed resist stays; exposed resist goes", "Etch copies the open pattern into the film"],
        ),
    Beat::new("rinse and dry", BEAT_MS)
        .note(
            "A deionized water rinse washes away the developer and the dissolved resist, then the wafer spins dry. As the liquid pulls back, tall, thin lines can lean together and collapse.",
            "A steel nozzle swings in and cyan water runs across the lines and off the edge. One thin line leans toward its neighbour.",
        )
        .detail(
            "The rinse can break the pattern.",
            &["DI water rinse, then spin or nitrogen dry", "Tall, thin lines can collapse in rinse and dry"],
        ),
    Beat::new("bridges and scum", BEAT_MS)
        .note(
            "Dissolved resist that does not wash away can settle back onto the wafer. Resist that precipitates during the rinse can bridge two neighbouring lines, and resist that should have cleared can be left as scum. Inspection after develop looks for these.",
            "A magenta bridge joins two neighbouring lines. The rest of the pattern is clean, and the bridge is the kind of defect inspection would flag.",
        )
        .detail(
            "Redeposited resist makes bridges.",
            &["Precipitate in the rinse can lead to bridging (EP0794463)", "Slow dissolution and redeposition cause defects (SST study)"],
        ),
    Beat::new("the stencil goes to etch", BEAT_MS)
        .note(
            "The developed resist goes on to etch, which carves the film beneath wherever the trenches are open. Afterward the resist is stripped. Coater/developer tracks are dominated by two makers, Tokyo Electron and Screen.",
            "Violet ions drop into the open trenches and cut the film; the resist lines stand over it as a stencil.",
        )
        .detail(
            "Track market: two makers.",
            &["TEL 8035.T and Screen 7735.T: about 88% (secondary estimate)", "Next step: ETCH carves the film"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_draws_every_beat() {
        let s = build();
        assert_eq!(s.beats().len(), 6);
        super::super::super::blender::explained(s.as_ref(), "DEVELOP overview");
        super::super::super::blender::draws_every_beat(s.as_ref(), "DEVELOP overview");
    }
}
