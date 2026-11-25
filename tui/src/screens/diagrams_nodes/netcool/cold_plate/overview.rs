// NETWORK+COOL tab, COLD PLATE: the page's overview, a Blender scene (tools/pbr3d/blender/net_cold_plate_overview.py, GLB
// tools/pbr3d/assets/net_cold_plate_overview.glb). Seven beats: a liquid-cooled tray, cool water in, heat into the copper,
// the microchannels, warm water out, the quick disconnects, and the whole rack.

use super::super::super::blender::{Cell, Page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../../tools/pbr3d/assets/net_cold_plate_overview.glb"),
        beats: BEATS,
        zooms: super::zooms::ZOOMS,
    })
}

/// The seven beats of the overview, one per step (match net_cold_plate_overview.py's beats).
pub const BEATS: &[Beat] = &[
    Beat::new("a liquid-cooled tray", BEAT_MS)
        .note(
            "A GPU sits under a copper cold plate in its tray. Hoses run from the plate back to quick disconnects at the tray's rear, which plug into the rack's supply and return manifolds.",
            "A green board in a grey tray, a grey cold plate block on the GPU with two black hoses running back to couplings and a blue and a red vertical pipe.",
        )
        .detail(
            "Direct-to-chip: water goes to the GPU itself.",
            &["COLD PLATE on the GPU", "QUICK DISCONNECT + MANIFOLD"],
        ),
    Beat::new("cool water in", BEAT_MS)
        .note(
            "Coolant at roughly 25-45 C climbs the supply manifold, crosses a quick disconnect and runs down a hose into the cold plate, entering right over the dies.",
            "Blue beads rise up the blue pipe, pass the coupling and ride the black hose to the riser on top of the plate.",
        )
        .detail(
            "Supply side of the loop.",
            &["MANIFOLD: supply", "~25-45 C in"],
        ),
    Beat::new("heat into the copper", BEAT_MS)
        .note(
            "The GPU draws about 1,000-1,400 W. Its heat crosses the thin TIM into the copper base and climbs into the fins.",
            "The plate cut open: purple dies glowing amber, a thin silver TIM layer, a copper base, and orange dots rising through them into the fins.",
        )
        .detail(
            "The TIM is the thinnest and hardest layer.",
            &["TIM", "BASE: spreads the heat"],
        ),
    Beat::new("through the microchannels", BEAT_MS)
        .note(
            "The water splits along dozens of thin copper fins. It touches a huge surface and warms as it goes, from blue to orange.",
            "Rows of copper fins seen end-on, glowing blue then orange, with beads running along the slots between them.",
        )
        .detail(
            "Surface area does the work.",
            &["MICROCHANNEL fins", "Water warms as it passes"],
        ),
    Beat::new("warm water out", BEAT_MS)
        .note(
            "The warm water leaves through the outlet hose and quick disconnect and rises up the return manifold at about 45-60 C.",
            "Orange beads leave the plate's back riser, run along the hose and climb the red pipe.",
        )
        .detail(
            "Warm enough to skip the chiller.",
            &["WARM WATER: ~45-60 C", "MANIFOLD: return"],
        ),
    Beat::new("quick disconnects", BEAT_MS)
        .note(
            "The tray slides out for service. Its quick disconnects part from the manifold's and spring valves seal both sides, so nothing spills.",
            "The whole tray slides toward the viewer; the blue and red couplings separate from the halves left on the pipes.",
        )
        .detail(
            "Service without draining the rack.",
            &["QUICK DISCONNECT: dripless", "Blind-mate"],
        ),
    Beat::new("the whole rack", BEAT_MS)
        .note(
            "Every tray taps the same pair of manifolds. The loop carries a rack's 120-130 kW back to the CDU.",
            "Pulled back: several trays stacked in the rack, blue beads rising in one pipe and orange in the other, green LEDs blinking.",
        )
        .detail(
            "One loop per rack.",
            &["NVL72: ~120-130 kW", "CDU"],
        ),
];
