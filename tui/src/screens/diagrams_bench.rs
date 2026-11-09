//! Frame-cost bench for every 3D scene the diagrams screen can orbit.
//!
//! Renders each scene the way a held H/J/K/L key does: the camera yaws a little every
//! frame, so nothing is cached, at the size `paint_3d` uses while moving. Each frame is
//! timed through `render_model` (poly3d's own breakdown from `poly3d::prof`) and the kitty
//! encode the terminal path adds. Prints a table, slowest first.
//!
//!   just bench-3d                       # or:
//!   cargo test --release bench_3d -- --ignored --nocapture
//!
//! Env knobs:
//!   FL_BENCH_SIZE=1200x660   pixel size per frame (default: half of a ~2400x1320 popup,
//!                            what paint_3d renders while a key is held)
//!   FL_BENCH_FRAMES=12       frames per scene (spread over its beats, yawing)
//!   FL_BENCH_FILTER=CELL     only scenes whose name contains this
//!   FL_BENCH_TOP=40          rows to print
//!   FL_BENCH_ENCODE=0        skip the kitty encode timing
//!   FL_BENCH_JSON=path       also write every row as JSON lines (for agents / diffs)

use std::time::Instant;

use super::{Model, kitty_protocol, model_at, render_model};
use crate::ui::anim::Time;
use image::DynamicImage;
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::widgets::StatefulWidget;
use ratatui_image::picker::{Picker, ProtocolType};
use ratatui_image::{Resize, StatefulImage};

/// One scene to bench: a name and how to build its model at (beat, local).
struct Case {
    name: String,
    beats: usize,
    model: Box<dyn Fn(usize, f32) -> Model>,
}

fn time(beat: usize, local: f32) -> Time {
    Time { ms: (beat as u64) * 4000 + (local * 4000.0) as u64, beat, local, beat_start: beat as u64 * 4000 }
}

const KEYS: [char; 14] = ['a', 'b', 'c', 'd', 'e', '1', '2', '3', '4', '5', '6', '7', '8', '9'];

fn cases() -> Vec<Case> {
    use super::super::{diagrams_scene_chip as chip, diagrams_scene_link as link, diagrams_scene_pkg as pkg, diagrams_scene_pwr as pwr};
    let mut out: Vec<Case> = Vec::new();
    let mut pages: Vec<&'static str> = vec!["POLYSILICON", "CELL", "LITHO", "ARRAY", "BANK", "BANDWIDTH", "HBM STACK"];
    pages.extend(chip::nodes().iter().map(|n| n.page));
    pages.extend(pkg::nodes().iter().map(|n| n.page));
    pages.extend(link::nodes().iter().map(|n| n.page));
    pages.extend(pwr::nodes().iter().map(|n| n.page));

    for page in pages {
        // overviews
        let ov: Option<(usize, Box<dyn Fn(usize, f32) -> Model>)> = match page {
            "CELL" => Some((7, Box::new(|b, l| Model::CellOverview(time(b, l))))),
            "LITHO" => Some((poly3d::LITHO_OVERVIEW_BEATS, Box::new(|b, l| Model::LithoOverview(time(b, l))))),
            "ARRAY" => Some((poly3d::ARRAY_OVERVIEW_BEATS, Box::new(|b, l| Model::ArrayOverview(time(b, l))))),
            "BANK" => Some((poly3d::BANK_OVERVIEW_BEATS, Box::new(|b, l| Model::BankOverview(time(b, l))))),
            "BANDWIDTH" => Some((poly3d::BW_OVERVIEW_BEATS, Box::new(|b, l| Model::BwOverview(time(b, l))))),
            "HBM STACK" => Some((poly3d::HBM_OVERVIEW_BEATS, Box::new(|b, l| Model::HbmOverview(time(b, l))))),
            _ => {
                if let Some(n) = chip::node(page) {
                    Some((n.keys.len(), Box::new(move |b, l| Model::ChipOverview(n.beats, n.keys, time(b, l)))))
                } else if let Some(n) = pkg::node(page) {
                    Some((n.keys.len(), Box::new(move |b, l| Model::PkgOverview(n.beats, n.keys, time(b, l)))))
                } else if let Some(n) = link::node(page) {
                    Some((n.keys.len(), Box::new(move |b, l| Model::LinkOverview(n.beats, n.keys, time(b, l)))))
                } else if let Some(n) = pwr::node(page) {
                    Some((n.keys.len(), Box::new(move |b, l| Model::PwrOverview(n.beats, n.keys, time(b, l)))))
                } else {
                    None
                }
            }
        };
        if let Some((beats, model)) = ov {
            out.push(Case { name: format!("{page} overview"), beats: beats.max(1), model });
        }
        // zooms and sections
        for k in KEYS {
            if !super::super::diagrams_anim::orbitable(page, k) {
                continue;
            }
            let beats = match model_at(page, k, &time(0, 0.0)) {
                Model::Cell(z, ..) => z.beats(),
                Model::Litho(z, ..) => z.beats(),
                Model::Array(z, ..) => z.beats(),
                Model::Bank(z, ..) => z.beats(),
                Model::Bw(z, ..) => z.beats(),
                Model::Hbm(z, ..) => z.beats(),
                Model::Chip(keys, ..) => keys.len(),
                Model::Pkg(keys, ..) => keys.len(),
                Model::Link(keys, ..) => keys.len(),
                Model::Pwr(keys, ..) => keys.len(),
                _ => 3,
            };
            out.push(Case {
                name: format!("{page} {k}"),
                beats: beats.max(1),
                model: Box::new(move |b, l| model_at(page, k, &time(b, l))),
            });
        }
    }
    out
}

struct Row {
    name: String,
    s: poly3d::prof::Stats,
    /// wall time of render_model, ms per frame
    render_ms: f64,
    /// kitty encode (zlib + base64 + escape codes), ms per frame
    encode_ms: f64,
}

fn env<T: std::str::FromStr>(k: &str, d: T) -> T {
    std::env::var(k).ok().and_then(|v| v.parse().ok()).unwrap_or(d)
}

fn kitty_encode_ms(img: image::RgbaImage) -> f64 {
    let mut picker = Picker::halfblocks();
    picker.set_protocol_type(ProtocolType::Kitty);
    let font = picker.font_size();
    let (w, h) = (img.width(), img.height());
    let area = Rect::new(0, 0, (w / font.width as u32).max(1) as u16, (h / font.height as u32).max(1) as u16);
    let t0 = Instant::now();
    let mut proto = kitty_protocol(&picker, DynamicImage::ImageRgba8(img), font, 0x00F3_D101);
    let mut buf = Buffer::empty(area);
    StatefulImage::default().resize(Resize::Fit(None)).render(area, &mut buf, &mut proto);
    t0.elapsed().as_secs_f64() * 1e3
}

#[test]
#[ignore = "bench: cargo test --release bench_3d -- --ignored --nocapture"]
fn bench_3d() {
    let size = std::env::var("FL_BENCH_SIZE").unwrap_or_else(|_| "1200x660".into());
    let (w, h) = size.split_once('x').map(|(a, b)| (a.parse().unwrap(), b.parse().unwrap())).unwrap_or((1200usize, 660usize));
    let frames: usize = env("FL_BENCH_FRAMES", 12);
    let top: usize = env("FL_BENCH_TOP", 40);
    let encode = env("FL_BENCH_ENCODE", 1) != 0;
    let filter = std::env::var("FL_BENCH_FILTER").unwrap_or_default();

    let mut rows = Vec::new();
    for c in cases().into_iter().filter(|c| c.name.contains(&filter)) {
        let mut sum = poly3d::prof::Stats::default();
        let (mut wall, mut enc) = (0.0, 0.0);
        let mut view = poly3d::View::default();
        // one warm-up frame: first-touch allocations should not count
        let _ = render_model((c.model)(0, 0.5), &view, w, h);
        for f in 0..frames {
            // spread frames over every beat, and turn the camera like a held `l`
            let x = (f as f64 + 0.5) / frames as f64 * c.beats as f64;
            let (beat, local) = (x as usize, x.fract() as f32);
            view.orbit(0.04, 0.0);
            poly3d::prof::begin();
            let t0 = Instant::now();
            let img = render_model((c.model)(beat, local), &view, w, h);
            wall += t0.elapsed().as_secs_f64() * 1e3;
            sum.add(&poly3d::prof::take());
            if encode && f % 4 == 0 {
                enc += kitty_encode_ms(img) * 4.0;
            }
        }
        let k = 1.0 / frames as f64;
        rows.push(Row { name: c.name, s: sum.scaled(k), render_ms: wall * k, encode_ms: enc * k });
    }
    rows.sort_by(|a, b| (b.render_ms + b.encode_ms).total_cmp(&(a.render_ms + a.encode_ms)));

    println!("\n3D frame cost at {w}x{h}, {frames} frames/scene, yawing (what a held HJKL key renders)");
    println!("budget: MOTION_FRAME is 30 ms. 'frame' = render + kitty encode.\n");
    println!(
        "{:<30} {:>7} {:>7} {:>6} | {:>6} {:>5} {:>6} {:>7} {:>6} | {:>7} {:>7} {:>6} {:>7} {:>7}",
        "scene", "frame", "render", "enc", "build", "sort", "raster", "overlay", "image", "tris", "drawn", "ovrdr", "linepx", "dotpx"
    );
    for r in rows.iter().take(top) {
        let s = &r.s;
        println!(
            "{:<30} {:>7.1} {:>7.1} {:>6.1} | {:>6.1} {:>5.1} {:>6.1} {:>7.1} {:>6.1} | {:>7} {:>7} {:>6.2} {:>7} {:>7}",
            r.name.chars().take(30).collect::<String>(),
            r.render_ms + r.encode_ms,
            r.render_ms,
            r.encode_ms,
            s.build_ms,
            s.sort_ms,
            s.raster_ms,
            s.overlay_ms,
            s.image_ms,
            s.tris,
            s.tris_drawn,
            s.overdraw(),
            s.line_px,
            s.dot_px,
        );
    }
    let n = rows.len().max(1) as f64;
    let mean = |f: &dyn Fn(&Row) -> f64| rows.iter().map(f).sum::<f64>() / n;
    println!(
        "\n{} scenes. mean frame {:.1} ms (render {:.1}: build {:.1} sort {:.1} raster {:.1} overlay {:.1} image {:.1}; encode {:.1})",
        rows.len(),
        mean(&|r| r.render_ms + r.encode_ms),
        mean(&|r| r.render_ms),
        mean(&|r| r.s.build_ms),
        mean(&|r| r.s.sort_ms),
        mean(&|r| r.s.raster_ms),
        mean(&|r| r.s.overlay_ms),
        mean(&|r| r.s.image_ms),
        mean(&|r| r.encode_ms),
    );
    println!("over budget (>30 ms): {}", rows.iter().filter(|r| r.render_ms + r.encode_ms > 30.0).count());

    if let Ok(path) = std::env::var("FL_BENCH_JSON") {
        let lines: Vec<String> = rows
            .iter()
            .map(|r| {
                let s = &r.s;
                serde_json::json!({
                    "scene": r.name, "w": w, "h": h, "frame_ms": r.render_ms + r.encode_ms,
                    "render_ms": r.render_ms, "encode_ms": r.encode_ms, "build_ms": s.build_ms,
                    "sort_ms": s.sort_ms, "raster_ms": s.raster_ms, "overlay_ms": s.overlay_ms,
                    "image_ms": s.image_ms, "tris": s.tris, "tris_drawn": s.tris_drawn,
                    "px_tested": s.px_tested, "px_written": s.px_written, "overdraw": s.overdraw(),
                    "lines": s.lines, "line_px": s.line_px, "dot_px": s.dot_px,
                })
                .to_string()
            })
            .collect();
        std::fs::write(&path, lines.join("\n") + "\n").expect("write FL_BENCH_JSON");
        println!("json: {path}");
    }
}

/// Cost budget every orbitable scene must stay inside. Counters, not timings, so the test is
/// deterministic and runs in debug. A new or edited scene that trips it will stutter under a
/// held HJKL; run `just bench-3d` to see where its time goes (see tools/poly3d/CLAUDE.md).
const MAX_TRIS: u64 = 40_000;
/// pixels walked by triangle fills, per screen pixel
const MAX_TESTED_PER_PX: f64 = 6.0;
/// depth-passing writes per screen pixel (hidden layers drawn then covered)
const MAX_OVERDRAW: f64 = 4.0;
/// pixels visited by glowing dots, per screen pixel
const MAX_DOT_PER_PX: f64 = 3.0;
/// alpha line steps, per screen pixel
const MAX_LINE_PER_PX: f64 = 1.0;

#[test]
fn scenes_stay_inside_frame_budget() {
    let (w, h) = (480usize, 264usize);
    let px = (w * h) as f64;
    let mut over = Vec::new();
    for c in cases() {
        let mut view = poly3d::View::default();
        view.orbit(0.3, 0.1);
        for beat in 0..c.beats {
            poly3d::prof::begin();
            let _ = render_model((c.model)(beat, 0.6), &view, w, h);
            let s = poly3d::prof::take();
            let checks = [
                ("tris", s.tris as f64, MAX_TRIS as f64),
                ("px_tested/px", s.px_tested as f64 / px, MAX_TESTED_PER_PX),
                ("overdraw", s.overdraw(), MAX_OVERDRAW),
                ("dot_px/px", s.dot_px as f64 / px, MAX_DOT_PER_PX),
                ("line_px/px", s.line_px as f64 / px, MAX_LINE_PER_PX),
            ];
            for (what, got, max) in checks {
                if got > max {
                    over.push(format!("{} beat {beat}: {what} {got:.2} > {max}", c.name));
                }
            }
        }
    }
    assert!(over.is_empty(), "scenes over the frame budget:\n{}", over.join("\n"));
}
