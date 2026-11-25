// NETWORK+COOL tab, CHILLER PLANT: the page's overview, a Blender scene (tools/pbr3d/blender/net_chiller_overview.py, GLB
// tools/pbr3d/assets/net_chiller_overview.glb). Seven beats: a chiller beside the hall, the evaporator, the compressor, the
// condenser and fans, the expansion valve, free cooling, and the whole loop.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The 7 beats of the overview (match net_chiller_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a chiller beside the hall", BEAT_MS)
        .note(
            "A chiller is a refrigeration machine the size of a shipping container. It sends chilled water into the data hall, where coils in the air handlers or liquid-cooling units pick up the servers' heat, and takes the warmed water back.",
            "A cut-open grey hall with black rack rows on the left; on the right a long grey chiller with four fans on top; a blue pipe runs into the hall and an amber pipe comes back.",
        )
        .detail(
            "The chiller makes the cold water the hall runs on.",
            &["CHILLED WATER: out", "WARM WATER: back"],
        ),
    Beat::new("the evaporator", BEAT_MS)
        .note(
            "Warm water from the hall runs through copper tubes inside the evaporator shell. Refrigerant around the tubes boils at low pressure, near 5 C, and soaks up the water's heat, so the water leaves colder.",
            "A blue cylindrical shell cut open to show a bundle of copper tubes; small cyan bubbles rise inside it; a blue bead leaves its end.",
        )
        .detail(
            "Boiling refrigerant takes the heat out of the water.",
            &["EVAPORATOR", "Refrigerant boils ~5 C"],
        ),
    Beat::new("the compressor", BEAT_MS)
        .note(
            "The screw compressor pulls the cold vapour in and squeezes it hot and dense. This is where the chiller spends its electricity: it lifts the heat to a temperature high enough to dump outdoors.",
            "A grey compressor housing and a green ribbed motor; cyan beads enter it from the evaporator, and red beads leave from its top.",
        )
        .detail(
            "Squeezing the vapour lifts its temperature.",
            &["COMPRESSOR: screw", "Hot gas ~60-80 C"],
        ),
    Beat::new("the condenser and fans", BEAT_MS)
        .note(
            "The hot gas flows into the V-bank condenser coils under the deck. The fans pull outside air across the fins, the gas gives up its heat and condenses to liquid, and warm air rises off the top.",
            "Rows of finned coils under the deck glow orange; four fans spin on top and orange heat dots float up above them.",
        )
        .detail(
            "The heat leaves the machine here.",
            &["CONDENSER: air-cooled", "Fans pull outside air"],
        ),
    Beat::new("the expansion valve", BEAT_MS)
        .note(
            "The warm liquid passes through the expansion valve. Its pressure drops so suddenly that part of it flashes to vapour and the mix turns cold, ready to boil again in the evaporator.",
            "A small brass valve; cyan beads run along a thin copper line from the coils, through the valve and back to the evaporator.",
        )
        .detail(
            "The pressure drop closes the loop.",
            &["EXPANSION VALVE", "Flashes cold"],
        ),
    Beat::new("free cooling", BEAT_MS)
        .note(
            "On a cold day the outside air alone can chill the water. The return water is routed through a free-cooling coil, the compressor stops, and the fans do the work for a fraction of the power.",
            "A blue-glowing coil on the back of the chiller with blue beads zigzagging through it; the compressor is still; small heat dots over the fans.",
        )
        .detail(
            "Cold air instead of a compressor.",
            &["FREE COOLING", "Compressor off"],
        ),
    Beat::new("the whole loop", BEAT_MS)
        .note(
            "Everything runs at once: water to the hall and back, refrigerant round its loop, fans rejecting the heat. Each kW the compressor uses moves roughly 3 to 6 kW of heat, depending on the machine and the weather.",
            "A wide view: the hall with blinking racks, blue and amber water beads in the pipes, red and cyan refrigerant beads in the chiller, fans spinning.",
        )
        .detail(
            "Heat moves from racks to outdoors.",
            &["COP ~3-6", "1-2 MW per big unit"],
        ),
];
