// Contact sheets of the MELT + PULL close-ups: one PNG per shot, its beats in a row.
// `cargo run --release --example sheet -- <out_dir> [shot]`, shot = neck|conv|hot|1..9 (default all).
use image::{Rgba, RgbaImage};
use pbr3d::Shot;

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let dir = a.get(1).cloned().unwrap_or_else(|| "sheets".into());
    std::fs::create_dir_all(&dir).unwrap();
    let only = a.get(2).cloned();
    let shots: Vec<(String, Shot)> = vec![
        ("neck".into(), Shot::Neck),
        ("conv".into(), Shot::Convection),
        ("hot".into(), Shot::HotZone),
    ]
    .into_iter()
    .chain((1..=9u8).map(|n| (format!("sec{n}"), Shot::Sec(n))))
    .filter(|(name, _)| {
        only.as_ref().map_or(true, |o| {
            o == name || (o.len() == 1 && name == &format!("sec{o}"))
        })
    })
    .collect();
    let (w, h) = (480u32, 320u32);
    for (name, shot) in shots {
        let n = pbr3d::shot_beats(shot);
        let mut sheet = RgbaImage::from_pixel(w * n as u32, h * 2, Rgba([20, 20, 24, 255]));
        for b in 0..n {
            for (row, local) in [0.25f32, 0.8].iter().enumerate() {
                let img = pbr3d::render_shot(shot, b, *local, 0.0, 0.0, 1.0, w, h, [38, 42, 52]);
                image::imageops::replace(
                    &mut sheet,
                    &img,
                    (b as u32 * w) as i64,
                    (row as u32 * h) as i64,
                );
            }
        }
        let path = format!("{dir}/{name}.png");
        sheet.save(&path).unwrap();
        println!("{path}");
    }
}
