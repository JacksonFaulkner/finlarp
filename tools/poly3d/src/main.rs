//! Offline GIF tool: renders a clip as numbered PNG frames.
//! `--scene bell` (default) is the bell-jar clip, `--scene cell` the DRAM cell clip,
//! and `--scene cell-a` .. `cell-e`, `cell-1` .. `cell-9` the focused CELL scenes over their beats.
//! `run.sh` turns the frames into mp4 + gif with ffmpeg. The renderers live in
//! `lib.rs` and are shared with the TUI's full-screen view.

use std::fs;
use std::path::PathBuf;

use poly3d::{
    clip_anim, clip_cell_anim, clip_cell_view, clip_view, render, render_cell, render_zoom,
    CellParams, CellZoom, Params,
};

/// One cell frame at clip position `t`: the whole cell, or a zoom playing its three
/// beats across the clip.
fn cell_frame(
    zoom: Option<CellZoom>,
    t: f64,
    view: Option<poly3d::View>,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> image::RgbaImage {
    match zoom {
        Some(z) => {
            let n = z.beats() as f64;
            let x = (t * n).min(n - 0.0001);
            let beat = x as usize;
            render_zoom(z, beat, x - beat as f64, &view.unwrap_or_default(), w, h, bg)
        }
        None => {
            let v = view.unwrap_or_else(|| clip_cell_view(t));
            render_cell(&CellParams::default(), &clip_cell_anim(t), &v, w, h, bg)
        }
    }
}

fn hex_rgb(s: &str) -> [u8; 3] {
    let n = u32::from_str_radix(s.trim_start_matches('#'), 16).expect("--bg RRGGBB");
    [(n >> 16) as u8, (n >> 8) as u8, n as u8]
}

fn main() -> std::io::Result<()> {
    let mut out = PathBuf::from("out/frames");
    let mut frames: usize = 240;
    let mut w: usize = 1280;
    let mut h: usize = 720;
    let mut only: Option<usize> = None;
    // Ghostty's Dracula background (#282a36), the TUI's terminal background.
    let mut bg = hex_rgb("282a36");
    let mut view: Option<poly3d::View> = None;
    let mut anim: Option<poly3d::Anim> = None;
    let mut scene = String::from("bell");

    let args: Vec<String> = std::env::args().collect();
    let mut i = 1;
    while i < args.len() {
        let next = || args.get(i + 1).cloned().unwrap_or_default();
        match args[i].as_str() {
            "--out" => out = PathBuf::from(next()),
            "--frames" => frames = next().parse().expect("--frames N"),
            "--width" => w = next().parse().expect("--width N"),
            "--height" => h = next().parse().expect("--height N"),
            "--bg" => bg = hex_rgb(&next()),
            // camera for --still: yaw,pitch,zoom,panx,pany (defaults: turntable at t=0)
            "--view" => {
                let v: Vec<f64> = next()
                    .split(',')
                    .map(|s| s.parse().expect("--view"))
                    .collect();
                view = Some(poly3d::View {
                    yaw: v[0],
                    pitch: v[1],
                    zoom: v[2],
                    pan: [v[3], v[4]],
                });
            }
            // rod state for --still: heat,rod_d (default: clip state at --still's t)
            "--anim" => {
                let v: Vec<f64> = next()
                    .split(',')
                    .map(|s| s.parse().expect("--anim"))
                    .collect();
                anim = Some(poly3d::Anim {
                    heat: v[0],
                    rod_d: v[1],
                    ..Default::default()
                });
            }
            // render one frame index only, for quick stills
            "--still" => only = Some(next().parse().expect("--still INDEX")),
            // bell (default) or cell
            "--scene" => scene = next(),
            other => panic!("unknown arg {other}"),
        }
        i += 2;
    }

    let (cell, zoom) = match scene.as_str() {
        "bell" => (false, None),
        "cell" => (true, None),
        "cell-a" => (true, Some(CellZoom::Capacitor)),
        "cell-b" => (true, Some(CellZoom::Read)),
        "cell-c" => (true, Some(CellZoom::Rows)),
        "cell-d" => (true, Some(CellZoom::Shrink)),
        "cell-e" => (true, Some(CellZoom::Layout)),
        "cell-1" => (true, Some(CellZoom::Bit)),
        "cell-2" => (true, Some(CellZoom::Parts)),
        "cell-3" => (true, Some(CellZoom::Order)),
        "cell-4" => (true, Some(CellZoom::RefreshCmds)),
        "cell-5" => (true, Some(CellZoom::Retention)),
        "cell-6" => (true, Some(CellZoom::Numbers)),
        "cell-7" => (true, Some(CellZoom::Swing)),
        "cell-8" => (true, Some(CellZoom::Makers)),
        "cell-9" => (true, Some(CellZoom::Risks)),
        other => panic!("unknown --scene {other}: use bell, cell, cell-a .. cell-e or cell-1 .. cell-9"),
    };
    if cell && anim.is_some() {
        panic!("--anim is not supported for --scene {scene}: the cell state comes from the clip");
    }

    fs::create_dir_all(&out)?;
    let p = Params::default();
    let last = (frames - 1).max(1) as f64;

    let draw = |idx: usize| {
        let t = idx as f64 / last;
        if cell {
            cell_frame(zoom, t, None, w, h, bg)
        } else {
            render(&p, clip_anim(&p, t), &clip_view(t), w, h, bg)
        }
    };
    match only {
        Some(idx) => {
            let path = out.join(format!("still_{idx:04}.png"));
            let t = idx as f64 / last;
            let img = if cell {
                cell_frame(zoom, t, view, w, h, bg)
            } else {
                render(
                    &p,
                    anim.unwrap_or_else(|| clip_anim(&p, t)),
                    &view.unwrap_or_else(|| clip_view(t)),
                    w,
                    h,
                    bg,
                )
            };
            img.save(&path).map_err(std::io::Error::other)?;
            println!("{}", path.display());
        }
        None => {
            for idx in 0..frames {
                draw(idx)
                    .save(out.join(format!("{:04}.png", idx + 1)))
                    .map_err(std::io::Error::other)?;
            }
            println!("wrote {frames} frames to {}", out.display());
        }
    }
    Ok(())
}
