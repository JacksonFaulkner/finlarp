// Contact sheet of one Blender page scene as the TUI shows it: the scene in the left pane of a
// 1280 x 720 frame with its `label:` tags pinned on, every beat at a few points in its time.
// `cargo run --release --example page_sheet -- <glb> <beats> <out.png> [sec_per_beat=8]`
//
// Env (all optional; the defaults keep the old two-column sheet):
//   PBR3D_SAMPLES     comma list of fractions through each beat, e.g. "0.1,0.3,0.5,0.7,0.9"
//                     (default "0.3,0.8"); one sheet column per fraction
//   PBR3D_FRAMES_DIR  also write every frame as b<beat>_t<fraction>.png in this directory
//   PBR3D_MONTAGE_DIR write one montage per beat, b<beat>.png: its samples at half size, three
//                     to a row, so a whole beat can be checked in one image
use image::imageops::{self, FilterType};
use image::{Rgba, RgbaImage};

const MONTAGE_COLS: u32 = 3;
const GUTTER: u32 = 4;

fn samples() -> Vec<f32> {
    match std::env::var("PBR3D_SAMPLES") {
        Ok(s) if !s.trim().is_empty() => s
            .split(',')
            .map(|x| x.trim().parse::<f32>().expect("PBR3D_SAMPLES: a number per comma"))
            .collect(),
        _ => vec![0.3, 0.8],
    }
}

fn env_dir(name: &str) -> Option<String> {
    std::env::var(name).ok().filter(|d| !d.is_empty())
}

/// One beat's half-size samples, three to a row, on a dark ground.
fn montage(tiles: &[RgbaImage], tw: u32, th: u32) -> RgbaImage {
    let n = tiles.len() as u32;
    let rows = n.div_ceil(MONTAGE_COLS);
    let mut m = RgbaImage::from_pixel(
        MONTAGE_COLS * tw + (MONTAGE_COLS + 1) * GUTTER,
        rows * th + (rows + 1) * GUTTER,
        Rgba([32, 32, 40, 255]),
    );
    for (i, t) in tiles.iter().enumerate() {
        let c = i as u32 % MONTAGE_COLS;
        let r = i as u32 / MONTAGE_COLS;
        let x = GUTTER + c * (tw + GUTTER);
        let y = GUTTER + r * (th + GUTTER);
        imageops::replace(&mut m, t, x as i64, y as i64);
    }
    m
}

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    let scene = pbr3d::scene_gltf::Scene::from_glb(&std::fs::read(&a[0]).unwrap()).unwrap();
    let beats: u32 = a[1].parse().unwrap();
    let out = &a[2];
    let sec: f32 = a.get(3).map(|s| s.parse().unwrap()).unwrap_or(8.0);
    let frames_dir = env_dir("PBR3D_FRAMES_DIR");
    let montage_dir = env_dir("PBR3D_MONTAGE_DIR");
    for d in [&frames_dir, &montage_dir].into_iter().flatten() {
        std::fs::create_dir_all(d).unwrap();
    }
    let fr = samples();
    let h = 720u32;
    let w = pbr3d::caption::scene_width(1280);
    let mut sheet = RgbaImage::from_pixel(w * fr.len() as u32, h * beats, Rgba([20, 20, 24, 255]));
    let mut frames = 0u32;
    for b in 0..beats {
        let mut half = Vec::with_capacity(fr.len());
        for (col, local) in fr.iter().enumerate() {
            let t = (b as f32 + local) * sec;
            let mut img = pbr3d::scene_gltf::render(&scene, t, w, h, [38, 42, 52]);
            let mut tags = pbr3d::caption::Tags::new();
            for (text, p) in scene.labels(t) {
                if let Some((x, y)) = pbr3d::scene_gltf::project(&scene, t, w, h, p) {
                    tags.add(&mut img, x, y, &text, w, h);
                }
            }
            if let Some(d) = &frames_dir {
                img.save(format!("{d}/b{b}_t{local:.2}.png")).unwrap();
                frames += 1;
            }
            if montage_dir.is_some() {
                half.push(imageops::resize(&img, w / 2, h / 2, FilterType::Triangle));
            }
            imageops::replace(&mut sheet, &img, (col as u32 * w) as i64, (b * h) as i64);
        }
        if let Some(d) = &montage_dir {
            montage(&half, w / 2, h / 2).save(format!("{d}/b{b}.png")).unwrap();
        }
    }
    sheet.save(out).unwrap();
    println!("{out}");
    if let Some(d) = frames_dir {
        println!("{frames} frames in {d}");
    }
    if let Some(d) = montage_dir {
        println!("{beats} montages in {d}");
    }
}
