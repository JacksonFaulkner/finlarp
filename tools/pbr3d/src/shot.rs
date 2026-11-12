//! The MELT + PULL close-ups, drawn in the same shaded style as the overview: zooms a-c
//! (the dash neck, the melt convection, the hot zone) and sections 1-9. Each beat is a
//! camera, a state of the furnace rig and the meshes the beat adds on top of it.

use image::RgbaImage;

use crate::gpu;
use crate::math::V3;
use crate::melt::{self, Cam, State};
use crate::mesh::Mesh;
use crate::shot_sec;
use crate::shot_zoom;

/// One close-up of the MELT + PULL node.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Shot {
    /// zoom a: the dash neck
    Neck,
    /// zoom b: melt convection and the magnetic field
    Convection,
    /// zoom c: the hot zone and the argon sweep
    HotZone,
    /// sections 1-9
    Sec(u8),
}

/// What one beat draws: the rig state, the camera and the meshes (opaque and glass).
pub struct Pic {
    pub s: State,
    pub cam: Cam,
    pub solid: Mesh,
    pub glass: Mesh,
}

impl Pic {
    /// The furnace rig in state `s`, seen from `target` at `dist`, on `yaw`/`pitch`.
    pub fn rig(s: State, target: V3, dist: f32, yaw: f32, pitch: f32) -> Pic {
        let (solid, glass) = melt::build(&s);
        Pic {
            s,
            cam: Cam {
                target,
                dist,
                yaw,
                pitch,
            },
            solid,
            glass,
        }
    }

    /// No furnace: the beat's own meshes on a bare stage, with the clock set for the light.
    pub fn bare(beat: usize, local: f32, target: V3, dist: f32, yaw: f32, pitch: f32) -> Pic {
        let s = State {
            beat,
            local,
            ..Default::default()
        };
        Pic {
            s,
            cam: Cam {
                target,
                dist,
                yaw,
                pitch,
            },
            solid: Mesh::new(),
            glass: Mesh::new(),
        }
    }
}

/// How many beats a shot has.
pub fn beats(shot: Shot) -> usize {
    match shot {
        Shot::Neck | Shot::Convection | Shot::HotZone => 4,
        Shot::Sec(1) => 5,
        Shot::Sec(_) => 4,
    }
}

/// The picture of `shot` at beat `beat` (clamped), local progress `local` (0..1).
pub fn pic(shot: Shot, beat: usize, local: f32) -> Pic {
    let beat = beat.min(beats(shot) - 1);
    let local = local.clamp(0.0, 1.0);
    match shot {
        Shot::Neck => shot_zoom::neck(beat, local),
        Shot::Convection => shot_zoom::convection(beat, local),
        Shot::HotZone => shot_zoom::hot_zone(beat, local),
        Shot::Sec(n) => shot_sec::section(n, beat, local),
    }
}

/// Renders one beat. `d_yaw`, `d_pitch` turn the camera from the user's orbit, and
/// `zoom` (1 = the shot's own distance) moves it in and out.
#[allow(clippy::too_many_arguments)]
pub fn render_shot(
    shot: Shot,
    beat: usize,
    local: f32,
    d_yaw: f32,
    d_pitch: f32,
    zoom: f32,
    w: u32,
    h: u32,
    bg: [u8; 3],
) -> RgbaImage {
    let p = pic(shot, beat, local);
    let cam = Cam {
        target: p.cam.target,
        dist: p.cam.dist / zoom.max(0.2),
        yaw: p.cam.yaw + d_yaw,
        pitch: p.cam.pitch + d_pitch,
    };
    let bgf = [
        bg[0] as f32 / 255.0,
        bg[1] as f32 / 255.0,
        bg[2] as f32 / 255.0,
    ];
    let f = melt::frame_for(&p.s, &cam, w, h, p.s.local + p.s.beat as f32, bgf);
    gpu::with_renderer(|r| r.render(&f, &p.solid, &p.glass, w, h))
}
