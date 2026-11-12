// Times the stages of one frame: `cargo run --release --example bench`
use std::time::Instant;
fn main() {
    let (w, h) = (1200u32, 800u32);
    // warm up the device and pipelines
    let _ = pbr3d::render_melt(2, 0.5, 0.6, 0.16, 1.0, w, h, [40, 42, 54]);
    for &(label, ww, hh) in &[("full 1200x800", w, h), ("half 600x400", w / 2, h / 2)] {
        let mut total = 0.0;
        let n = 10;
        for k in 0..n {
            let t = Instant::now();
            let _ = pbr3d::render_melt(2, 0.1 + 0.08 * k as f32, 0.6, 0.16, 1.0, ww, hh, [40, 42, 54]);
            total += t.elapsed().as_secs_f64() * 1000.0;
        }
        println!("{label}: {:.1} ms per frame (build + GPU + readback)", total / n as f64);
    }
    let s = pbr3d::melt::state_at(2, 0.5);
    let t = Instant::now();
    for _ in 0..20 {
        let _ = pbr3d::melt::build(&s);
    }
    println!("mesh build: {:.2} ms", t.elapsed().as_secs_f64() * 1000.0 / 20.0);
}
