// Aggregate frame rate of N threads rendering one GLB scene at once:
// `cargo run --release --example thread_bench -- <glb> <threads> [frames per thread]`
// Set PBR3D_PER_THREAD=1 to give each thread its own GPU device and queue.
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let path = args[0].clone();
    let threads: usize = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(4);
    let frames: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(60);
    let bytes = std::fs::read(&path).unwrap();
    let scene = pbr3d::scene_gltf::Scene::from_glb(&bytes).unwrap();
    // warm every thread's device before timing
    std::thread::scope(|s| {
        for _ in 0..threads {
            s.spawn(|| {
                let _ = pbr3d::scene_gltf::render(&scene, 0.5, 1280, 720, [40, 42, 54]);
            });
        }
    });
    let t0 = Instant::now();
    std::thread::scope(|s| {
        for k in 0..threads {
            let scene = &scene;
            s.spawn(move || {
                for i in 0..frames {
                    let t = (k * frames + i) as f32 * 0.01;
                    let _ = pbr3d::scene_gltf::render(scene, t, 1280, 720, [40, 42, 54]);
                }
            });
        }
    });
    let secs = t0.elapsed().as_secs_f64();
    let total = threads * frames;
    println!("{threads} threads: {total} frames in {secs:.2} s = {:.0} fps ({:.2} ms/frame)", total as f64 / secs, secs * 1e3 / total as f64);
}
