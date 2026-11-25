// NETWORK+COOL tab, CHILLER PLANT: lettered zoom-ins a-e (tools/pbr3d/blender/net_chiller_zooms.py, GLBs in
// tools/pbr3d/assets/net_chiller_zoom_<letter>.glb): a evaporator, b compressor, c condenser, d free cooling, e dry cooler.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

const BEAT_MS: u64 = 8000;

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/net_chiller_zoom_e.glb"),
        E_B,
    )
}

const A_B: &[Beat] = &[
    Beat::new("water in the tubes", BEAT_MS)
        .note(
            "The hall's warm water, around 25 to 30 C on a modern liquid-cooled site, enters one end of the evaporator and runs through a bundle of copper tubes.",
            "A big cut-open blue shell with copper tubes inside; amber beads enter at the left, blue beads leave at the right.",
        )
        .detail(
            "Shell-and-tube heat exchanger.",
            &["Warm water in", "Copper tube bundle"],
        ),
    Beat::new("refrigerant boils", BEAT_MS)
        .note(
            "Refrigerant fills the shell around the tubes. At the evaporator's low pressure it boils cold, and every gram that boils takes heat out of the water through the tube walls.",
            "Close on the shell: cyan bubbles rise from the bottom between the copper tubes.",
        )
        .detail(
            "Boiling takes the heat.",
            &["Low pressure", "Boils cold"],
        ),
    Beat::new("vapour leaves", BEAT_MS)
        .note(
            "Cold liquid arrives from the valve at the bottom, and the vapour it makes leaves from the top toward the compressor.",
            "Wide view of the bench: cyan beads come in from the valve at the lower left and leave toward the compressor at the right.",
        )
        .detail(
            "In as liquid, out as vapour.",
            &["Liquid in", "Vapour out"],
        ),
];

const B_B: &[Beat] = &[
    Beat::new("twin screws", BEAT_MS)
        .note(
            "A screw compressor has two meshing rotors, a male with four lobes and a female with six. Cold vapour enters at the suction end.",
            "A grey housing cut open on two silver helical rotors with a green motor at one end; a copper suction pipe on top.",
        )
        .detail(
            "Two rotors mesh.",
            &["SCREW COMPRESSOR", "4 + 6 lobes"],
        ),
    Beat::new("squeezed along the screws", BEAT_MS)
        .note(
            "As the rotors turn, each pocket of gas is carried along and shrinks, so the gas leaves hot and dense at the far end.",
            "Cyan beads ride the rotors left to right, turning red and closer together; red beads leave from the bottom pipe.",
        )
        .detail(
            "Smaller pocket, hotter gas.",
            &["Volume shrinks", "Hot gas out"],
        ),
    Beat::new("centrifugal and magnetic bearings", BEAT_MS)
        .note(
            "The biggest water-cooled chillers use a centrifugal compressor: an impeller flings the gas outward into a volute. Many now float the shaft on magnetic bearings, so there is no oil to manage.",
            "A spinning silver impeller with curved blades inside a spiral grey volute, purple bearing rings on its shaft, red beads spiralling out.",
        )
        .detail(
            "Oil-free, efficient at scale.",
            &["CENTRIFUGAL", "MAGNETIC BEARINGS"],
        ),
];

const C_B: &[Beat] = &[
    Beat::new("hot gas into the coils", BEAT_MS)
        .note(
            "The compressor's hot gas is piped up into the condenser coils that line the top of the chiller.",
            "The chiller's upper half: finned coil rows glowing orange, red beads entering them from the compressor.",
        )
        .detail(
            "Gas in at the top.",
            &["CONDENSER COILS", "V-bank"],
        ),
    Beat::new("fans pull air through", BEAT_MS)
        .note(
            "The fans on the deck pull outdoor air across the fins. The air leaves warmer, carrying the heat away from the building.",
            "Top view of four spinning fans with orange heat dots rising above them.",
        )
        .detail(
            "Outdoor air takes the heat.",
            &["Fans on the deck", "Air ~10-15 C warmer"],
        ),
    Beat::new("gas to liquid", BEAT_MS)
        .note(
            "Cooling the gas turns it back to liquid. The heat thrown out here is the hall's heat plus the compressor's own power.",
            "Wide view of the chiller with glowing coils and heat rising; the liquid line leaves the coils at the left.",
        )
        .detail(
            "Heat out = IT heat + compressor.",
            &["Condenses to liquid", "Rejects all the heat"],
        ),
];

const D_B: &[Beat] = &[
    Beat::new("hot day", BEAT_MS)
        .note(
            "On a hot day the compressor carries the whole load: every watt of heat goes through the refrigerant loop.",
            "The chiller running: refrigerant beads in the pipes, heat over the compressor, water beads in and out.",
        )
        .detail(
            "Compressor on.",
            &["Mechanical cooling", "Full power"],
        ),
    Beat::new("cold day", BEAT_MS)
        .note(
            "When the outside air is colder than the return water, the water goes through the free-cooling coil first and the compressor stops.",
            "The coil at the back of the chiller glows blue with beads zigzagging through it; the compressor is quiet.",
        )
        .detail(
            "Compressor off.",
            &["FREE COOLING", "Economizer"],
        ),
    Beat::new("warm water helps", BEAT_MS)
        .note(
            "Liquid-cooled GPUs accept warm water, around 30 C or more, so free cooling works on most hours of the year in many climates, cutting cooling energy sharply.",
            "The chiller from the other side, the free-cooling coil lit and the fans turning.",
        )
        .detail(
            "Warmer water, more free hours.",
            &["30 C+ supply", "Most hours free"],
        ),
];

const E_B: &[Beat] = &[
    Beat::new("no compressor", BEAT_MS)
        .note(
            "A dry cooler is just a finned coil and fans: the warm water runs through the coil and the outdoor air cools it. There is no refrigerant loop.",
            "A long grey unit with two finned coils leaning in to a V, glowing orange stripes, three fans on top; an amber pipe enters.",
        )
        .detail(
            "Coil + fans only.",
            &["DRY COOLER", "No compressor"],
        ),
    Beat::new("limited by the air", BEAT_MS)
        .note(
            "A dry cooler can only bring the water to a few degrees above the outdoor air temperature, so it suits warm-water liquid cooling.",
            "Top view: fans spinning, heat dots rising, pale air beads drawn in from both sides.",
        )
        .detail(
            "Water stays above air temperature.",
            &["~5 C above air", "Warm-water loops"],
        ),
    Beat::new("adiabatic assist", BEAT_MS)
        .note(
            "On the hottest days, adiabatic pads in front of the coils are wetted. Evaporation pre-cools the incoming air, using water only for the few hundred hours that need it.",
            "A tan pad along the back of the cooler with blue drops running down it; air beads pass through it into the coils.",
        )
        .detail(
            "Water only when it is hot.",
            &["ADIABATIC PADS", "Pre-cooled air"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "evaporator",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "compressor",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "condenser",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "free cooling",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "dry cooler",
        build: zoom_e,
    },
];
