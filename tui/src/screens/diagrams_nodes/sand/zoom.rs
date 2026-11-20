// SAND zoom-ins a-d: each a Blender scene (tools/pbr3d/blender/sand_zooms.py) on the overview's
// layout, the 3D picture on the left with tags pinned on and the beat's text on the right.
//
//   a  cavity  the arc opens the cavity, quartz melts into SiO gas, Si drips, escaped SiO makes SiC
//   b  crust   steady sinking, SiO freezes into crust, the charge hangs, the stoking bar breaks it
//   c  tap     plugged pool, the lance opens it, metal runs under the hood, the mud gun re-plugs
//   d  bag     dusty gas in, a cake on the cloth, a pulse of air, microsilica out and clean gas up

use std::sync::OnceLock;

use super::{BEAT_MS, Page};
use crate::ui::anim::{Beat, Scene};

static CAVITY: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();
static CRUST: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();
static TAP: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();
static BAG: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();

pub fn cavity() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &CAVITY,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/sand_cavity.glb"),
        beats: CAV_BEATS,
        zooms: &[],
    })
}

pub fn crust() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &CRUST,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/sand_crust.glb"),
        beats: CRUST_BEATS,
        zooms: &[],
    })
}

pub fn tap() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &TAP,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/sand_tap.glb"),
        beats: TAP_BEATS,
        zooms: &[],
    })
}

pub fn bag() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &BAG,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/sand_bag.glb"),
        beats: BAG_BEATS,
        zooms: &[],
    })
}

// ---- a: the gas cavity ----------------------------------------------------------------

const CAV_BEATS: &[Beat] = &[
    Beat::new("the arc strikes and blows a gas cavity open under the electrode tip", BEAT_MS)
        .note(
            "Tens of kiloamps leave the carbon electrode as an arc. The heat opens a pocket of gas in the charge, lined with a hard green-grey shell of silicon carbide.",
            "the white arc under the tip, and the glowing cavity swelling to full size inside the SiC shell",
        )
        .detail(
            "Only the cavity is hot enough for the reactions that free silicon, so keeping it open and stable is the whole job of the furnace operator.",
            &[
                "Arc zone above 1800 C",
                "The electrode is carbon and burns away as it runs",
                "One cavity under each of the three electrodes",
            ],
        ),
    Beat::new("quartz at the hot wall melts: SiO2 + C gives SiO gas and CO", BEAT_MS)
        .note(
            "Quartz lumps that sink to the cavity wall melt and react with carbon. The products are both gases, SiO and CO, so the silicon leaves the quartz as a vapour.",
            "the white quartz lumps on the upper wall shrinking away, and yellow SiO bubbles drifting into the cavity",
        )
        .detail(
            "Turning silicon into SiO gas first is how the process works: the gas can reach the SiC in the shell, where the metal is actually made.",
            &[
                "SiO2 + C gives SiO + CO",
                "Strongly endothermic: the furnace uses 11-13 MWh per tonne",
                "The cavity gas is mostly SiO and CO (Sloman and Elkem)",
            ],
        ),
    Beat::new("SiO meets the SiC shell: SiO + SiC gives 2Si + CO, and silicon drips down", BEAT_MS)
        .note(
            "At the shell, SiO gas reacts with silicon carbide. Out comes liquid silicon, the product, which beads on the lower shell and drips into the pool below.",
            "bright beads forming on the bottom of the cavity and falling into the grey pool, which slowly rises",
        )
        .detail(
            "SiC is the intermediate the furnace lives on. It is made higher up and eaten here, so the balance of carbon decides how much silicon comes out.",
            &[
                "SiO + SiC gives 2 Si + CO",
                "SiC is a hard, porous solid (ESGI report)",
                "Silicon melts at 1414 C and runs down to the pool",
            ],
        ),
    Beat::new("SiO that escapes upward turns the coke above into SiC: SiO + 2C gives SiC + CO", BEAT_MS)
        .note(
            "Some SiO slips out of the top of the shell. In the cooler charge it meets coke and makes fresh SiC, which sinks back down to line the cavity again.",
            "bubbles leaving the top of the shell, and black coke lumps above turning the shell's green-grey",
        )
        .detail(
            "Every bit of SiO caught here is silicon kept. What gets past the charge leaves the lid and becomes fume.",
            &[
                "SiO + 2C gives SiC + CO",
                "Too little carbon lets SiO escape; too much grows SiC on the hearth",
                "Only 80-90% of the charged silicon ends up as product",
            ],
        ),
];

// ---- b: crust and stoking -------------------------------------------------------------

const CRUST_BEATS: &[Beat] = &[
    Beat::new("in a healthy furnace the charge sinks as fast as it is used up", BEAT_MS)
        .note(
            "Raw material is fed at the top and slides down through the shaft. Around the cavity there is only a thin SiC shell, so fresh charge keeps reaching the heat.",
            "quartz and coke lumps on the cut face all sliding down together, and the thin shell round the cavity",
        )
        .detail(
            "When the charge moves evenly the cavity stays the same size and output is steady.",
            &[
                "Charge is fed continuously at the top",
                "A gas cavity of SiO and CO sits round each electrode tip",
                "A SiC layer forms in the hotter regions below the charge",
            ],
        ),
    Beat::new("SiO freezes out on the cooler outside: 2SiO gives SiO2 + Si, and a crust builds", BEAT_MS)
        .note(
            "SiO gas rising out of the cavity cools as it climbs. Where it is cool enough it condenses to a sticky mix of SiO2 and Si that sets hard as crust.",
            "yellow gas drifting outward and the pale crust ring thickening round the cavity",
        )
        .detail(
            "The same condensation that saves silicon in the shaft builds crust when it happens too close to the cavity.",
            &[
                "2 SiO gives SiO2 + Si where it is cool enough",
                "The condensate is sticky and sets hard",
                "Crust is mainly SiO2 with Si and SiC mixed in (ESGI report)",
            ],
        ),
    Beat::new("the charge hangs on the crust and the cavity swells", BEAT_MS)
        .note(
            "The crust bridges over the cavity. Charge above it stops moving while the cavity below keeps eating, so the gap grows and less material reaches the heat.",
            "lumps over the crust standing still while those at the sides keep sinking, and the cavity growing",
        )
        .detail(
            "Output falls even though the same power goes in: the reactions have nothing to work on.",
            &[
                "Crust thickens and rises, increasing the cavity volume (Sloman and Elkem)",
                "It stops solids and liquids reaching the lower furnace",
                "Less charge reaches the heat, so less silicon is made",
            ],
        ),
    Beat::new("stoking: a car on the roof drives a bar into the crust and the charge falls in", BEAT_MS)
        .note(
            "A stoking car rolls along the lid and pushes a long bar down through the charge onto the crust. The crust breaks, the pieces drop into the cavity and the charge follows.",
            "the car arriving, the bar plunging down, crust chunks falling and the cavity shrinking back",
        )
        .detail(
            "Stoking keeps the furnace moving, but each stroke disturbs it, and a hard layer on the hearth cannot be stoked away.",
            &[
                "Typically about once an hour (Sloman and Elkem)",
                "Done with a long bar from a stoking car on the lid",
                "After months or years the furnace may need emptying, with a productivity penalty (ESGI report)",
            ],
        ),
];

// ---- c: tapping -----------------------------------------------------------------------

const TAP_BEATS: &[Beat] = &[
    Beat::new("the pool is full behind a clay plug in the tap hole", BEAT_MS)
        .note(
            "Liquid silicon collects on the hearth for hours. The tap hole runs through the wall at the bottom and is kept shut with packed clay.",
            "the glowing pool on the left, the wall cut open, and the brown plug in the hole",
        )
        .detail(
            "A full pool leaves the cavities nowhere to drain, so the furnace is tapped on a regular schedule.",
            &[
                "Silicon melts at 1414 C",
                "The pool sits on the hearth at the base",
                "The tap hole is low in the wall, sealed with clay",
            ],
        ),
    Beat::new("an oxygen lance burns through the plug", BEAT_MS)
        .note(
            "The crew pushes a steel pipe into the hole and feeds it oxygen. The pipe itself burns at the tip, hot enough to eat through the clay in seconds.",
            "the lance sliding in along the launder, its flame at the plug, and the hole opening",
        )
        .detail(
            "Opening the hole is quick and violent and starts the dirtiest minutes of the cycle for fume.",
            &[
                "An oxygen lance burns through the clay plug",
                "The lance is a steel pipe; the oxygen makes the flame",
                "The hole opens in seconds",
            ],
        ),
    Beat::new("metal runs down the launder into the ladle; a hood catches the fume", BEAT_MS)
        .note(
            "Silicon pours out along a refractory launder and falls into a ladle in a pit. Hot metal in air throws off SiO that burns to white silica fume, and a hood over the spout pulls it into a duct.",
            "the pool level dropping, the ladle filling, and grey fume rising into the hood",
        )
        .detail(
            "Capture at the source is the best fix for tap fume, and how well it works depends on the hood and duct shape.",
            &[
                "Hood over the taphole and spout, called a doghouse (USPTO 11874064)",
                "Fume is 40-80% of fugitive emissions from tapping, refining and casting at one plant (Elkem Salten study)",
                "Ladle refining with air or oxygen mainly removes Ca and Al into slag",
            ],
        ),
    Beat::new("the mud gun packs fresh clay into the hole and the pool starts again", BEAT_MS)
        .note(
            "A hydraulic mud gun swings in and presses clay into the hole until it seals. The stream stops and the furnace starts filling a new pool.",
            "the gun barrel meeting the wall, the new plug growing into the hole, and the launder going dark",
        )
        .detail(
            "Re-plugging quickly keeps the furnace sealed and stops metal and gas leaking out.",
            &[
                "A mud gun packs fresh clay into the hole",
                "Only 80-90% of the silicon charged is recovered as product",
                "The furnace builds a new pool until the next tap",
            ],
        ),
];

// ---- d: the bag filter ----------------------------------------------------------------

const BAG_BEATS: &[Beat] = &[
    Beat::new("dusty off-gas from the furnace enters the baghouse under the bags", BEAT_MS)
        .note(
            "SiO escaping the charge burns in air to SiO2 particles about 150 nm across. A duct brings that hot, dusty gas into the space below a forest of cloth bags.",
            "hot gas arriving along the duct on the left and spreading up between the bags",
        )
        .detail(
            "The fume is silicon the furnace lost, so catching it is part of the economics and not only compliance.",
            &[
                "Fume particles are about 150 nm of SiO2",
                "A duct carries the gas from the furnace lid to the filter",
                "In one DC furnace 19.5% of the charged silicon was lost as fume",
            ],
        ),
    Beat::new("gas passes through the cloth; the dust stays outside as a cake", BEAT_MS)
        .note(
            "The bags let gas through and stop the particles. Clean gas rises inside each bag into the plenum above, while a grey cake builds up on the outside of the cloth.",
            "the bags darkening as the cake grows, and clean gas moving up into the plenum",
        )
        .detail(
            "The cake makes the filter catch finer dust but chokes the flow, so it has to be shed regularly.",
            &[
                "Cloth bags let gas through and stop the particles",
                "The cake builds on the outside of each bag",
                "The cake filters finer but slows the flow",
            ],
        ),
    Beat::new("a pulse of compressed air down each row knocks the cake off", BEAT_MS)
        .note(
            "A blowpipe over each row fires a short blast of air down into the bags. The cloth snaps outward and the cake falls off into the hopper.",
            "the jets flashing at the top of each row and cake chunks dropping into the hopper",
        )
        .detail(
            "Rows are cleaned in turn, so the filter never has to stop.",
            &[
                "A short blast of compressed air is fired down the inside of each bag",
                "The bag flexes and the cake drops into the hopper",
                "Each row is cleaned while the others keep filtering",
            ],
        ),
    Beat::new("the dust is bagged as microsilica and clean gas leaves the stack", BEAT_MS)
        .note(
            "The hopper empties into bulk bags of microsilica, a product sold for high-strength concrete or briquetted with carbon and fed back. A fan pulls the cleaned gas out through the stack.",
            "the hopper pile shrinking as the sack fills, and clear gas leaving the top of the stack",
        )
        .detail(
            "What the filter catches is sold or reused, so the baghouse earns some of its keep.",
            &[
                "Microsilica is used in concrete",
                "Briquetted microsilica plus carbon: 0-50% of the charge in a 200 kVA test (2024 preprint)",
                "Only clean gas goes up the stack",
            ],
        ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zoom_beat_counts_match_the_blender_scenes() {
        // tools/pbr3d/blender/sand_zooms.py builds every zoom with four beats
        for beats in [CAV_BEATS, CRUST_BEATS, TAP_BEATS, BAG_BEATS] {
            assert_eq!(beats.len(), 4);
        }
    }
}
