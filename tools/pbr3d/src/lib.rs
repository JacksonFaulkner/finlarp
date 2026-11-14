//! Physically based GPU renderer for the realistic machine overviews.
//!
//! Headless wgpu (Metal here): a sun shadow map with PCF, 4x MSAA HDR, glass drawn
//! last, bloom from the emissive parts, and an ACES tone map into display sRGB.
//! `melt` is the first machine built on it.

pub mod caption;
pub mod font;
pub mod gpu;
pub mod math;
pub mod melt;
pub mod mesh;
pub mod scene_gltf;
pub mod text;
mod shot;
mod shot_parts;
mod shot_sec;
mod shot_zoom;

pub use shot::{beats as shot_beats, pic as shot_pic, render_shot, Pic, Shot};

pub use gpu::{Frame, Renderer};
pub use mesh::{Kind, Mat, Mesh, Vertex};

use image::RgbaImage;

/// Renders the melt overview at beat `beat` (0..6), local progress `local` (0..1),
/// with the user's orbit `yaw`/`pitch` (radians) and `zoom` (1 = default distance).
pub fn render_melt(beat: usize, local: f32, yaw: f32, pitch: f32, zoom: f32, w: u32, h: u32, bg: [u8; 3]) -> RgbaImage {
    let s = melt::state_at(beat, local);
    let cam = melt::Cam {
        target: [0.0, 60.0 + 260.0 * s.body.min(700.0) / 700.0, 0.0],
        dist: 5600.0 / zoom.max(0.2),
        yaw,
        pitch,
    };
    let bgf = [bg[0] as f32 / 255.0, bg[1] as f32 / 255.0, bg[2] as f32 / 255.0];
    let f = melt::frame_for(&s, &cam, w, h, s.local + s.beat as f32, bgf);
    let (solid, glass) = melt::build(&s);
    gpu::with_renderer(|r| r.render(&f, &solid, &glass, w, h))
}

/// Creates the GPU device and compiles the pipelines now, so the first picture does not
/// stall the caller. Safe to call from a background thread; later renders wait for it.
pub fn warm() {
    gpu::with_renderer(|_| {});
}
