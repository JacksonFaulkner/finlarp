// Times one frame of a Blender GLB scene, split into CPU mesh build and the full render
// (GPU + readback). `cargo run --release --example scene_bench -- <glb> [WxH] [frames]`
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let path = args.first().expect("usage: scene_bench <glb> [WxH] [frames]");
    let (w, h) = args
        .get(1)
        .and_then(|s| s.split_once('x'))
        .map(|(a, b)| (a.parse().unwrap(), b.parse().unwrap()))
        .unwrap_or((1280u32, 720u32));
    let frames: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(30);
    let scene = pbr3d::scene_gltf::Scene::from_glb(&std::fs::read(path).unwrap()).unwrap();
    let bg = [40, 42, 54];
    // warm up the device, pipelines and target textures
    let _ = pbr3d::scene_gltf::render(&scene, 0.5, w, h, bg);

    let _ = pbr3d::gpu::prof::take();
    let (mut build_ms, mut total_ms) = (0.0, 0.0);
    for k in 0..frames {
        let t = k as f32 * (5.0 / frames as f32);
        let s0 = Instant::now();
        let _ = scene.meshes(t);
        build_ms += s0.elapsed().as_secs_f64() * 1e3;
        let s1 = Instant::now();
        let _ = pbr3d::scene_gltf::render(&scene, t, w, h, bg);
        total_ms += s1.elapsed().as_secs_f64() * 1e3;
    }
    let n = frames as f64;
    let (pf, setup, wait, copy) = pbr3d::gpu::prof::take();
    let pf = pf as f64;
    println!(
        "  inside render: setup+encode {:.2} ms, GPU wait {:.2} ms, readback copy {:.2} ms",
        setup / pf,
        wait / pf,
        copy / pf
    );
    println!(
        "{path} {w}x{h}: {:.1} ms/frame total (mesh build {:.2} ms, GPU+readback {:.1} ms), {:.1} fps",
        total_ms / n,
        build_ms / n,
        (total_ms - build_ms) / n,
        1000.0 / (total_ms / n)
    );
}
