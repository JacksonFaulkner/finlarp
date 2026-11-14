// Saves frames of a GLB scene for visual comparison:
// `cargo run --release --example frames_dump -- <glb> <out-dir> [times...]`
fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let scene = pbr3d::scene_gltf::Scene::from_glb(&std::fs::read(&args[0]).unwrap()).unwrap();
    let out = std::path::Path::new(&args[1]);
    std::fs::create_dir_all(out).unwrap();
    let times: Vec<f32> = if args.len() > 2 {
        args[2..].iter().map(|s| s.parse().unwrap()).collect()
    } else {
        vec![0.5, 1.5, 2.5, 3.5, 4.5]
    };
    for t in times {
        let img = pbr3d::scene_gltf::render(&scene, t, 1280, 720, [40, 42, 54]);
        img.save(out.join(format!("t{t:.2}.png"))).unwrap();
    }
}
