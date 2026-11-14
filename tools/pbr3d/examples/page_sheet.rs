// Contact sheet of one Blender page scene as the TUI shows it: the scene in the left pane of a
// 1280 x 720 frame with its `label:` tags pinned on, every beat at two points in its time.
// `cargo run --release --example page_sheet -- <glb> <beats> <out.png> [sec_per_beat=8]`
use image::{Rgba, RgbaImage};

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let scene = pbr3d::scene_gltf::Scene::from_glb(&std::fs::read(&a[0]).unwrap()).unwrap();
    let beats: u32 = a[1].parse().unwrap();
    let out = &a[2];
    let sec: f32 = a.get(3).map(|s| s.parse().unwrap()).unwrap_or(8.0);
    let h = 720u32;
    let w = pbr3d::caption::scene_width(1280);
    let mut sheet = RgbaImage::from_pixel(w * 2, h * beats, Rgba([20, 20, 24, 255]));
    for b in 0..beats {
        for (col, local) in [0.3f32, 0.8].iter().enumerate() {
            let t = (b as f32 + local) * sec;
            let mut img = pbr3d::scene_gltf::render(&scene, t, w, h, [38, 42, 52]);
            let mut tags = pbr3d::caption::Tags::new();
            for (text, p) in scene.labels(t) {
                if let Some((x, y)) = pbr3d::scene_gltf::project(&scene, t, w, h, p) {
                    tags.add(&mut img, x, y, &text, w, h);
                }
            }
            image::imageops::replace(&mut sheet, &img, (col as u32 * w) as i64, (b * h) as i64);
        }
    }
    sheet.save(out).unwrap();
    println!("{out}");
}
