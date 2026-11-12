// Writes one frame as raw RGBA for timing the terminal encode: `raw <out.bin>`
fn main() {
    let out = std::env::args().nth(1).unwrap();
    let img = pbr3d::render_melt(2, 0.5, 0.6, 0.16, 1.0, 1200, 800, [40, 42, 54]);
    std::fs::write(&out, img.as_raw()).unwrap();
}
