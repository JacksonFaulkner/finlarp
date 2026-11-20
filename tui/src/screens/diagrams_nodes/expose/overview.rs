// EXPOSE, the page's overview: a Blender scene (tools/pbr3d/blender/expose_overview.py, GLB
// tools/pbr3d/assets/expose_overview.glb). One EUV tool cut open, left to right: the CO2 drive laser
// cabinet, the tin-droplet source vessel with its collector mirror, the intermediate focus, and the
// scanner (illuminator mirrors, reflective reticle, six projection mirrors, wafer on its stage).
// Glowing beads ride the light path; tin drops fall from the nozzle.

use super::super::blender::{Cell, Page, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/expose_overview.glb"),
        beats: BEATS,
        zooms: &[],
    })
}

/// The seven beats of the overview, one per step (match expose_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("light from tin, printed on a wafer", BEAT_MS)
        .note(
            "A scanner prints a circuit pattern with light at 13.5 nm, far shorter than the 193 nm of older tools. The light is made by a plasma of hot tin, steered by mirrors, and it lands on a wafer coated with light-sensitive resist. Only the exposed resist changes, and that sets the pattern for the etch.",
            "The whole tool, left to right: an orange CO2 laser cabinet, a cut-open source vessel with a silver collector dish over a violet plasma, the scanner housing with its mirrors, and the wafer on its stage at the far right. Glowing blue beads run from the source through the scanner to the wafer.",
        )
        .detail(
            "The wavelength sets the smallest print.",
            &["13.5 nm EUV light", "193 nm for the older ArF tools", "EUV is absorbed by all materials, air included (ZEISS)"],
        ),
    Beat::new("tin drops, 50,000 a second", BEAT_MS)
        .note(
            "A nozzle fires tiny drops of molten tin down through the source vessel. Each drop is hit by a laser pulse at the exact moment it arrives, tens of thousands of times a second. Every hit must land in the same spot, or the light output drops.",
            "Close on the source: the silver nozzle above the vessel releases a stream of tin drops that fall toward the plasma point in the middle of the collector dish. The drops glow faintly as they pass the light.",
        )
        .detail(
            "Drops are fired at about 50 kHz.",
            &["50,000 hits per second (TRUMPF)", "Drop about 30 um across before the laser hits it (Laser Focus World)"],
        ),
    Beat::new("two laser shots make the light", BEAT_MS)
        .note(
            "The first laser pulse is weak and flattens the drop, swelling it from about 30 micrometres to over 100 micrometres, a pancake for the second pulse. The second pulse is a high-power CO2 laser shot that turns the tin into a plasma, which radiates 13.5 nm light. Most of the laser energy is lost as heat, so the drive laser must be very powerful.",
            "The orange pre-pulse beam hits the drop, which spreads into a flat pancake. Then the thicker main pulse fires, and the pancake flashes into a violet plasma that glows at the centre of the collector.",
        )
        .detail(
            "The pre-pulse makes the plasma more efficient.",
            &["Pre-pulse: about 30 um to over 100 um", "About 2x conversion efficiency from the pre-pulse (Laser Focus World)", "CO2 drive laser: over 10 kW (TRUMPF)"],
        ),
    Beat::new("the collector mirror", BEAT_MS)
        .note(
            "A large curved mirror wraps the plasma and gathers as much of its light as it can. The light is then handed off at the intermediate focus, the point where the source meets the scanner. The collector is a multilayer mirror, and it is the most exposed part of the source: tin debris slowly coats it.",
            "The silver collector dish is cut open to show the inside around the plasma, and the blue beads run from the plasma to the collector edge and on through the wall into the scanner at the intermediate focus, a small dark aperture.",
        )
        .detail(
            "Light leaves the source at the intermediate focus.",
            &["Source power at the intermediate focus: over 200 W (Laser Focus World)", "Multilayer mirror: molybdenum and silicon layers"],
        ),
    Beat::new("mirrors only, in vacuum", BEAT_MS)
        .note(
            "Inside the scanner, every optic is a mirror, because EUV light is absorbed by all materials, air included. The illuminator shapes the light, a reflective reticle carries the pattern, six projection mirrors shrink it, and the wafer takes the image. Each mirror keeps only about 70 percent of the light, so most of it is lost along the way.",
            "The scanner housing cut open: two illuminator mirrors, the reticle plate at the top, six projection mirrors zig-zagging down, and the wafer on its stage at the right. Blue beads follow the light from the intermediate focus, reflecting off each mirror, to the wafer.",
        )
        .detail(
            "Mirrors are the only way to steer EUV.",
            &["About 70% reflectivity per mirror", "Six-mirror projection lens passes about 12%", "Whole optical train: under 1% reaches the wafer"],
        ),
    Beat::new("one maker: ASML", BEAT_MS)
        .note(
            "ASML is the only company that makes EUV lithography machines. It integrates them from about 100,000 parts supplied by roughly 5,100 suppliers. ZEISS is the strategic partner that supplies the optics, the mirrors that every EUV machine depends on. Building a mirror that reflects this light takes precision coatings and polishing that few companies can match.",
            "The whole tool again, with the scanner in front. Tags mark ASML over the housing, ZEISS at the mirrors, and the parts count over the source vessel, as the beads run along the light path.",
        )
        .detail(
            "One integrator, one optics maker.",
            &["ASML: the only maker of EUV machines (ZEISS)", "About 100,000 parts, ~5,100 suppliers (lightsource.ai)", "ZEISS SMT exclusively supplies the optics (ZEISS)"],
        ),
    Beat::new("High-NA: 0.55 NA", BEAT_MS)
        .note(
            "The next generation, High-NA, raises the numerical aperture from 0.33 to 0.55, which lets the mirrors gather a wider cone of light. The critical dimension falls from 13 nm to 8 nm. The mirrors demagnify 4x in one direction and 8x in the other, so the field is half the size and each wafer takes twice as many exposures. ASML's EXE:5000 prints more than 185 wafers per hour.",
            "The scanner, with tags on the wider aperture and the smaller print. The beads run the light path again, and the anamorphic mirrors fold the light at a steeper angle.",
        )
        .detail(
            "Higher NA means finer lines, at a cost in speed.",
            &["NA 0.33 to 0.55; CD 13 nm to 8 nm (ASML)", "Anamorphic 4x / 8x; half-size fields, 2x exposures", "EXE:5000: more than 185 wafers per hour (ASML)"],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_captioned_and_draws_every_beat() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "EXPOSE overview");
        super::super::super::blender::draws_every_beat(s.as_ref(), "EXPOSE overview");
    }
}
