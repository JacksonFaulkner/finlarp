// Contact sheet of the Blender-authored WAFER overview: every beat at two points in its time.
// `cargo run --release --example wafer_sheet -- <out.png>`
use image::{Rgba, RgbaImage};

fn main() {
    let out = std::env::args().nth(1).unwrap_or_else(|| "wafer_sheet.png".into());
    let bytes = std::fs::read(concat!(env!("CARGO_MANIFEST_DIR"), "/assets/wafer_overview.glb")).unwrap();
    let scene = pbr3d::scene_gltf::Scene::from_glb(&bytes).unwrap();
    let (w, h) = (480u32, 320u32);
    let beats = 4;
    let mut sheet = RgbaImage::from_pixel(w * beats, h * 2, Rgba([20, 20, 24, 255]));
    for b in 0..beats {
        for (row, local) in [0.25f32, 0.8].iter().enumerate() {
            let img = pbr3d::scene_gltf::render(&scene, b as f32 + local, w, h, [38, 42, 52]);
            image::imageops::replace(&mut sheet, &img, (b * w) as i64, (row as u32 * h) as i64);
        }
    }
    sheet.save(&out).unwrap();
    println!("{out}");
}
