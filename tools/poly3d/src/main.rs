//! Offline GIF tool: renders the bell-jar clip as numbered PNG frames.
//! `run.sh` turns them into mp4 + gif with ffmpeg. The renderer lives in
//! `lib.rs` and is shared with the TUI's full-screen view.

use std::fs;
use std::path::PathBuf;

use poly3d::{clip_anim, clip_view, render, Params};

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
            other => panic!("unknown arg {other}"),
        }
        i += 2;
    }

    fs::create_dir_all(&out)?;
    let p = Params::default();
    let last = (frames - 1).max(1) as f64;

    let draw = |idx: usize| {
        let t = idx as f64 / last;
        render(&p, clip_anim(&p, t), &clip_view(t), w, h, bg)
    };
    match only {
        Some(idx) => {
            let path = out.join(format!("still_{idx:04}.png"));
            let t = idx as f64 / last;
            let img = render(
                &p,
                anim.unwrap_or_else(|| clip_anim(&p, t)),
                &view.unwrap_or_else(|| clip_view(t)),
                w,
                h,
                bg,
            );
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
