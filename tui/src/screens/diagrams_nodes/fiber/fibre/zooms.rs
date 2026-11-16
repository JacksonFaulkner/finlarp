// OPTICAL FIBER: lettered zoom-ins a-e. Each zoom beat is one frozen overview state with its own camera pose on
// the zoom's subject (tools/pbr3d/blender/fiber_fibre_zooms.py, GLBs in tools/pbr3d/assets/fiber_fibre_zoom_<letter>.glb).

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
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_fibre_zoom_e.glb"),
        E_B,
    )
}

/// Zoom a, laser end: laser can, lens and the ferrule tip.
const A_B: &[Beat] = &[
    Beat::new("LASER END: a lens aims the light", BEAT_MS)
        .note(
            "The laser's light leaves its window as a spreading beam. A lens gathers it and focuses it to a point on the end of the core, about 8 µm across, so as much light as possible enters the fibre.",
            "The steel laser can on its block, the pale orange cone to the glass lens on its post, and the cone narrowing onto the ferrule's tip, where the glowing core begins.",
        )
        .detail(
            "Light that misses the core is lost.",
            &["Single-mode core ~8.2 µm", "Light must arrive within the acceptance angle"],
        ),
    Beat::new("LASER END: the ferrule holds the glass", BEAT_MS)
        .note(
            "The bare glass is glued into a precise bore down the middle of a ceramic ferrule. A steel holder grips the ferrule, and a spring behind it keeps the tip pressed forward, so the core sits in the same place every time.",
            "Behind the laser and lens: the white zirconia ferrule cut in half with the glowing core through its centre, the amber epoxy in its funnel, the grey holder and flange, and the steel spring round the blue coated fibre.",
        )
        .detail(
            "The ferrule lines up the glass, not the light.",
            &["Cladding 125 µm in the bore", "Coating 242 µm, stripped inside the ferrule"],
        ),
    Beat::new("LASER END: into the core", BEAT_MS)
        .note(
            "Seen from the laser's side, the focused light meets the polished end of the ferrule exactly where the core is. From there the core carries it on; total internal reflection keeps it in (zoom b).",
            "Close up from the laser side: the lens, the narrowing cone of light, and its point landing on the ferrule's end where the glowing core line starts.",
        )
        .detail(
            "Alignment here sets how much light starts the trip.",
            &["Core ~8.2 µm", "Mode field 9.2 µm at 1310 nm"],
        ),
];

/// Zoom b, glass core: the magnified slice, rays turning back at the core wall.
const B_B: &[Beat] = &[
    Beat::new("GLASS CORE: a ray in the core", BEAT_MS)
        .note(
            "A slice of the fibre, magnified with the core drawn wide so the light's path can be drawn as a ray. The core is glass with a slightly higher refractive index than the cladding round it.",
            "The cut slice: a pale-blue core band between grey cladding bands, with an orange ray running in from the left.",
        )
        .detail(
            "The real single-mode core is only ~8.2 µm across.",
            &["Core ~8.2 µm (SM), 50 µm (MM)", "Cladding 125 µm"],
        ),
    Beat::new("GLASS CORE: turned back at the wall", BEAT_MS)
        .note(
            "The ray meets the core-cladding boundary at a shallow angle and reflects back in completely. This is total internal reflection: the cladding acts as a mirror with no light lost at the wall.",
            "Close up: the orange ray reaching the top of the core and turning back down, with a bright pulse riding it.",
        )
        .detail(
            "A small index step is enough at grazing angles.",
            &["Index step ~1/3 % (single-mode)", "Shallow angle: reflects completely"],
        ),
    Beat::new("GLASS CORE: all along the run", BEAT_MS)
        .note(
            "The same happens all the way along the fibre, so light stays trapped in the glass for kilometres. In single-mode fibre the light travels as one guided mode, partly in the cladding.",
            "Pulled back: the magnified slice with its zig-zag ray, the white guide lines down to the ring on the blue fibre run, and the run itself on its clamps.",
        )
        .detail(
            "The mode field is 9.2 µm at 1310 nm.",
            &["Mode field 9.2 µm at 1310 nm", "Light kept for kilometres"],
        ),
];

/// Zoom c, the run: the magnified slice, light dimming as it goes.
const C_B: &[Beat] = &[
    Beat::new("THE RUN: packets dim", BEAT_MS)
        .note(
            "As light runs down the fibre a little is lost in every kilometre: attenuation. The magnified slice shows packets of light growing dimmer along the core.",
            "In the magnified slice: glowing packets shrinking as they move left to right along the pale-blue core.",
        )
        .detail(
            "Attenuation sets how far light can go.",
            &["≤0.32 dB/km at 1310 nm (SMF-28 Ultra)"],
        ),
    Beat::new("THE RUN: scattering in the glass", BEAT_MS)
        .note(
            "Most of the loss is scattering in the glass itself, with a little residual absorption. The light that scatters leaves the core sideways and is gone.",
            "Small bright sparks fly out of the core through the grey cladding while the packets keep going.",
        )
        .detail(
            "Longer wavelengths lose less.",
            &["≤0.32 dB/km at 1310 nm", "≤0.18 dB/km at 1550 nm"],
        ),
    Beat::new("THE RUN: under 1 dB in 2 km", BEAT_MS)
        .note(
            "0.32 dB is about 7% of the light. A 2 km data-center link loses under 1 dB in the glass, less than its connectors, so most of the light arrives.",
            "Pulled back: the slice above the fibre run, joined to the ring on the run by the white guide lines.",
        )
        .detail(
            "In a building the connectors cost more than the glass.",
            &["0.32 dB ≈ 7% of the light", "2 km: under 1 dB"],
        ),
];

/// Zoom d, photodiode end: the far ferrule tip, lens, photodiode and wire.
const D_B: &[Beat] = &[
    Beat::new("PHOTODIODE END: light leaves the glass", BEAT_MS)
        .note(
            "At the far end the ferrule holds the polished glass end steady. Light leaves the core as a widening cone and crosses a short gap to a lens.",
            "The white ferrule cut in half with the glowing core ending at its chamfered tip, the pale cone of light, and the glass lens on its post.",
        )
        .detail(
            "Light leaves the far end into the receiver's lens.",
            &["Core ~8.2 µm"],
        ),
    Beat::new("PHOTODIODE END: onto the window", BEAT_MS)
        .note(
            "The lens focuses the light onto the window of the photodiode can, where the light-sensitive chip sits inside.",
            "The lens, the light narrowing onto the bright window of the steel photodiode can, and the can's dark header and block.",
        )
        .detail(
            "The photodiode turns light into current.",
            &["Light in, current out"],
        ),
    Beat::new("PHOTODIODE END: current to the amplifier", BEAT_MS)
        .note(
            "The photodiode turns the light back into a small current. A wire carries it to an amplifier chip (a TIA), which turns it into a voltage for the receiver's DSP.",
            "Glowing cyan beads ride the arched copper wire from the back of the photodiode can down to the dark amplifier chip on the green board.",
        )
        .detail(
            "Next station: the PHOTODIODE page.",
            &["Light to current to voltage"],
        ),
];

/// Zoom e, whole reach: the whole link from above.
const E_B: &[Beat] = &[
    Beat::new("WHOLE REACH: laser to photodiode", BEAT_MS)
        .note(
            "Light runs the whole length of the glass, from the ferrule at the laser to the ferrule at the photodiode. On a real link this run is kilometres; here it is drawn short.",
            "From above: the two white ferrule assemblies with their springs, the blue coated fibre on its clamps between them, and packets of light along the glowing core.",
        )
        .detail(
            "Single-mode reaches buildings and beyond.",
            &["Single-mode: km reach", "Multimode: up to ~100 m"],
        ),
    Beat::new("WHOLE REACH: ~5 µs per km", BEAT_MS)
        .note(
            "Light in glass travels at about two-thirds of its speed in vacuum, roughly 5 microseconds per kilometre. Across a building that is negligible; across a campus or between data centers it adds up.",
            "The same run from a lower angle, with the magnified slice above it and light moving along the core.",
        )
        .detail(
            "Hollow-core fibre cuts latency by about a third.",
            &["~5 µs per km", "Hollow-core: ~1/3 less"],
        ),
    Beat::new("WHOLE REACH: the loss is small", BEAT_MS)
        .note(
            "Over 2 km the glass loses under 1 dB, less than the connectors at each end, so reach inside a data center is set by the optics and joints, not by the fibre.",
            "Side on: the whole run between the two ferrules, packets of light running end to end.",
        )
        .detail(
            "Attenuation: ≤0.32 dB/km at 1310 nm.",
            &["2 km: under 1 dB in the glass", "Connectors lose more"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "laser end",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "glass core",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "the run",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "photodiode end",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "whole reach",
        build: zoom_e,
    },
];
