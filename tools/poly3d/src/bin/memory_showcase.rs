use std::fs;
use std::path::PathBuf;

use poly3d::{render_cell, CellAnim, CellParams, View};

const FPS: usize = 30;
const DURATION: f64 = 10.0;

#[derive(Clone, Copy)]
struct Shot {
    at: f64,
    target: [f64; 3],
    distance: f64,
    yaw: f64,
    pitch: f64,
}

const SHOTS: [Shot; 9] = [
    // Hold the full cell, then move only at the transition between teaching beats.
    Shot { at: 0.0, target: [0.0, 280.0, 0.0], distance: 1500.0, yaw: 0.35, pitch: 0.30 },
    Shot { at: 1.4, target: [0.0, 280.0, 0.0], distance: 1500.0, yaw: 0.35, pitch: 0.30 },
    Shot { at: 2.0, target: [170.0, 290.0, 0.0], distance: 900.0, yaw: 0.35, pitch: 0.52 },
    Shot { at: 3.5, target: [170.0, 290.0, 0.0], distance: 900.0, yaw: 0.35, pitch: 0.52 },
    Shot { at: 4.1, target: [-20.0, 420.0, 0.0], distance: 780.0, yaw: 0.35, pitch: 0.36 },
    Shot { at: 5.4, target: [-20.0, 420.0, 0.0], distance: 780.0, yaw: 0.35, pitch: 0.36 },
    Shot { at: 6.0, target: [-75.0, 365.0, 0.0], distance: 1000.0, yaw: 0.48, pitch: 0.32 },
    Shot { at: 7.7, target: [-75.0, 365.0, 0.0], distance: 1000.0, yaw: 0.48, pitch: 0.32 },
    Shot { at: 8.5, target: [0.0, 280.0, 0.0], distance: 1500.0, yaw: 0.58, pitch: 0.30 },
];

fn smooth(x: f64) -> f64 {
    let x = x.clamp(0.0, 1.0);
    x * x * (3.0 - 2.0 * x)
}

fn ramp(t: f64, a: f64, b: f64) -> f64 {
    smooth((t - a) / (b - a))
}

fn camera(t: f64) -> (CellParams, View) {
    let i = SHOTS.windows(2).position(|pair| t <= pair[1].at).unwrap_or(SHOTS.len() - 2);
    let a = SHOTS[i];
    let b = SHOTS[i + 1];
    let k = smooth((t - a.at) / (b.at - a.at));
    let mix = |x: f64, y: f64| x + (y - x) * k;
    let target = std::array::from_fn(|axis| mix(a.target[axis], b.target[axis]));
    let params = CellParams { target, cam_dist: mix(a.distance, b.distance), ..CellParams::default() };
    let view = View { yaw: mix(a.yaw, b.yaw), pitch: mix(a.pitch, b.pitch), ..View::default() };
    (params, view)
}

fn cell_state(t: f64) -> CellAnim {
    let word_line = ramp(t, 3.8, 4.2) * (1.0 - ramp(t, 9.0, 9.5));
    let sharing = ramp(t, 5.9, 6.2) * (1.0 - ramp(t, 6.9, 7.2));
    let sense = ramp(t, 6.7, 7.1) * (1.0 - ramp(t, 8.8, 9.1));
    let restore = ramp(t, 8.0, 8.3) * (1.0 - ramp(t, 9.0, 9.3));
    let drained = ramp(t, 6.0, 6.6) * (1.0 - ramp(t, 8.0, 8.8));
    let cap = 1.0 - 0.28 * drained + 0.28 * restore;
    let bl = 0.5 + 0.07 * sharing + 0.43 * sense;
    let sa = sense.max(restore) as f32;
    CellAnim {
        wl: word_line,
        bl,
        cap: cap.clamp(0.0, 1.0),
        sa_rgb: [
            0.35 + 0.65 * sense as f32 + 0.05 * restore as f32,
            0.36 + 0.49 * sa,
            0.42 - 0.17 * sense as f32 + 0.03 * restore as f32,
        ],
        read: sharing,
        restore,
        leak: 0.0,
        phase: (t * 2.2).fract(),
    }
}

fn main() -> std::io::Result<()> {
    let mut args = std::env::args().skip(1);
    let out = PathBuf::from(args.next().unwrap_or_else(|| "artifacts/memory-model-showcase/frames".into()));
    let width: usize = args.next().as_deref().unwrap_or("1920").parse().expect("width");
    let height: usize = args.next().as_deref().unwrap_or("1080").parse().expect("height");
    fs::create_dir_all(&out)?;
    let frames = (DURATION * FPS as f64) as usize;
    for frame in 0..frames {
        let t = frame as f64 / FPS as f64;
        let (params, view) = camera(t);
        let image = render_cell(&params, &cell_state(t), &view, width, height, [40, 42, 54]);
        image.save(out.join(format!("{frame:04}.png"))).map_err(std::io::Error::other)?;
    }
    println!("Rendered {frames} frames to {}", out.display());
    Ok(())
}
