// Renders one frame to a PNG: `cargo run --release --example still -- <beat> <local> <yaw> <pitch> <zoom> <out.png>`
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let beat: usize = a.get(1).map_or(2, |s| s.parse().unwrap());
    let local: f32 = a.get(2).map_or(0.5, |s| s.parse().unwrap());
    let yaw: f32 = a.get(3).map_or(0.6, |s| s.parse().unwrap());
    let pitch: f32 = a.get(4).map_or(0.16, |s| s.parse().unwrap());
    let zoom: f32 = a.get(5).map_or(1.0, |s| s.parse().unwrap());
    let out = a.get(6).cloned().unwrap_or_else(|| "melt.png".into());
    let t = std::time::Instant::now();
    let img = pbr3d::render_melt(beat, local, yaw, pitch, zoom, 1200, 800, [38, 42, 52]);
    eprintln!("frame in {:?}", t.elapsed());
    img.save(&out).unwrap();
}
