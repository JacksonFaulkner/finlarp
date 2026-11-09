//! 3D render of one 1T1C DRAM cell, the CELL overview.
//!
//! Same renderer as the bell jar (`lib.rs`): z-buffered flat-shaded solids, then
//! alpha-blended wireframe, then flow overlays. Units are schematic mm-like, Y up,
//! ground at y = 0. Each part lives in its own file, all wired by `render_cell`:
//!
//!   solids.rs   substrate slab, capacitor plates, storage node, ground pillar
//!   wiring.rs   access transistor, gate, word line, bit line, sense amp
//!   charge.rs   charge spheres in the capacitor gap; leak and read/restore streams
//!   glass.rs    voltage gauge tube (glass wireframe + fill), cell footprint wireframe
//!
//! Every submodule exposes the same two shapes of function:
//!   build(p, a, m)            push solid triangles into `m` (depth tested)
//!   flows / frame(cv, cam, ..) draw onto the canvas after the solids

mod callout;
mod charge;
mod chip;
mod array;
mod bandwidth;
mod bank;
mod glass;
mod hbm;
mod litho;
mod pkg;
mod sec_bit;
mod sec_makers;
mod sec_numbers;
mod sec_order;
mod sec_parts;
mod sec_refresh;
mod sec_retention;
mod sec_risks;
mod sec_swing;
mod solids;
mod stage;
mod wiring;
mod zoom_cap;
mod zoom_layout;
mod zoom_read;
mod zoom_rows;
mod zoom_shrink;

use image::RgbaImage;

pub use bandwidth::{render_bw_overview, render_bw_zoom, BwZoom, BW_OVERVIEW_BEATS};
pub use bank::{render_bank_overview, render_bank_zoom, BankZoom, BANK_OVERVIEW_BEATS};
pub use chip::{part_at, render_chip, ChipKey, ChipPart, ChipState};
pub use pkg::{pkg_part_at, render_pkg, PkgKey, PkgPart, PkgState};
pub use hbm::{render_hbm_overview, render_hbm_zoom, HbmZoom, HBM_OVERVIEW_BEATS};
pub use array::{render_array_overview, render_array_zoom, ArrayZoom, ARRAY_OVERVIEW_BEATS};
pub use litho::{render_litho_overview, render_litho_zoom, LithoZoom, LITHO_OVERVIEW_BEATS};

use crate::{Cam, Canvas, Tri, View};

/// Scene layout, schematic units (mm-like), Y up, ground at y = 0.
#[derive(Clone, Copy, Debug)]
pub struct CellParams {
    /// camera look-at point
    pub target: [f64; 3],
    /// camera distance from the target
    pub cam_dist: f64,
    /// substrate slab: half-size in x and z, thickness
    pub substrate_half: f64,
    pub substrate_thick: f64,
    /// bit line x (vertical pillar from the sense amp up to the channel)
    pub bl_x: f64,
    /// sense amp block: half-width in x, height, half-depth in z
    pub sa_half_w: f64,
    pub sa_h: f64,
    pub sa_half_d: f64,
    /// channel height (the transistor body runs along x at this y)
    pub ch_y: f64,
    /// gate x position and half-width in x
    pub gate_x: f64,
    pub gate_half_w: f64,
    /// word line height and rod radius (runs along z over the gate)
    pub wl_y: f64,
    pub wl_r: f64,
    /// capacitor x position, plate radius, plate thickness
    pub cap_x: f64,
    pub plate_r: f64,
    pub plate_t: f64,
    /// bottom and top plate heights (the gap between them holds the dielectric)
    pub bot_plate_y: f64,
    pub top_plate_y: f64,
    /// gauge tube: x, z, radius, height
    pub gauge_x: f64,
    pub gauge_z: f64,
    pub gauge_r: f64,
    pub gauge_h: f64,
}

impl Default for CellParams {
    fn default() -> Self {
        CellParams {
            target: [0.0, 280.0, 0.0],
            cam_dist: 1500.0,
            substrate_half: 360.0,
            substrate_thick: 40.0,
            bl_x: -150.0,
            sa_half_w: 90.0,
            sa_h: 110.0,
            sa_half_d: 70.0,
            ch_y: 420.0,
            gate_x: -20.0,
            gate_half_w: 22.0,
            wl_y: 540.0,
            wl_r: 9.0,
            cap_x: 170.0,
            plate_r: 110.0,
            plate_t: 10.0,
            bot_plate_y: 250.0,
            top_plate_y: 330.0,
            gauge_x: -400.0,
            gauge_z: 0.0,
            gauge_r: 40.0,
            gauge_h: 600.0,
        }
    }
}

/// Cell state at one instant, all levels 0..1 unless noted.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct CellAnim {
    /// word line level: 0 low .. 1 high (thickens, turns orange when high)
    pub wl: f64,
    /// bit line voltage: 0 = GND, 0.5 = VDD/2, 1 = VDD (drives the gauge)
    pub bl: f64,
    /// charge in the cell: 0 empty .. 1 full (lit charge spheres)
    pub cap: f64,
    /// sense amp colour
    pub sa_rgb: [f32; 3],
    /// strength of charge flowing from the cell up to the bit line (read)
    pub read: f64,
    /// strength of charge flowing back into the cell (restore / rewrite)
    pub restore: f64,
    /// strength of sideways leakage out of both plates
    pub leak: f64,
    /// 0..1 moves the dashes and dots
    pub phase: f64,
}

impl Default for CellAnim {
    fn default() -> Self {
        CellAnim {
            wl: 0.0,
            bl: 0.5,
            cap: 1.0,
            sa_rgb: [0.35, 0.36, 0.42],
            read: 0.0,
            restore: 0.0,
            leak: 0.0,
            phase: 0.0,
        }
    }
}

fn lerp(a: f64, b: f64, t: f64) -> f64 {
    a + (b - a) * t
}

/// Smoothstep from `e0` to `e1`, clamped outside, as in `lib.rs`.
fn smooth(e0: f64, e1: f64, x: f64) -> f64 {
    let t = ((x - e0) / (e1 - e0)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Move level `x` to `to` across the clip window [a, b]. Holds `x` before it and `to` after.
/// Chain calls in time order to build a level with several beats.
fn ease(x: f64, t: f64, a: f64, b: f64, to: f64) -> f64 {
    lerp(x, to, smooth(a, b, t))
}

/// 1 across the window [a, b], with smooth edges of width `edge`, 0 outside.
fn pulse(t: f64, a: f64, b: f64, edge: f64) -> f64 {
    smooth(a, a + edge, t) * (1.0 - smooth(b - edge, b, t))
}

/// Cell state at clip position `t` (0..1). Beats, as fractions of the clip:
/// idle 0.00-0.14, word line rises 0.14-0.28, charge sharing 0.28-0.42,
/// sense 0.42-0.56, precharge 0.56-0.70, leak 0.70-0.84, refresh 0.84-1.00.
/// The clip ends in the idle state, so it loops.
pub fn clip_cell_anim(t: f64) -> CellAnim {
    let t = t.clamp(0.0, 1.0);

    // word line: up after idle, down in precharge, up again for refresh, down at its end
    let mut wl = 0.0;
    wl = ease(wl, t, 0.14, 0.28, 1.0);
    wl = ease(wl, t, 0.56, 0.70, 0.0);
    wl = ease(wl, t, 0.84, 0.87, 1.0);
    wl = ease(wl, t, 0.93, 0.97, 0.0);

    // bit line: 0.5 idle, nudged to 0.57 by charge sharing, sense drives it to 1.0,
    // precharge brings it back to 0.5. Refresh drives it high for the restore, then back.
    let mut bl = 0.5;
    bl = ease(bl, t, 0.28, 0.42, 0.57);
    bl = ease(bl, t, 0.42, 0.56, 1.0);
    bl = ease(bl, t, 0.56, 0.70, 0.5);
    bl = ease(bl, t, 0.90, 0.93, 1.0);
    bl = ease(bl, t, 0.95, 1.0, 0.5);

    // charge: full, drained to 0.72 by sharing, refilled by sense, leaks to 0.82, refresh to 1
    let mut cap = 1.0;
    cap = ease(cap, t, 0.28, 0.42, 0.72);
    cap = ease(cap, t, 0.42, 0.56, 1.0);
    cap = ease(cap, t, 0.70, 0.84, 0.82);
    cap = ease(cap, t, 0.84, 1.0, 1.0);

    // streams: read out during sharing and refresh, restore in sense and refresh, leak in leak
    let read = pulse(t, 0.28, 0.42, 0.01) + pulse(t, 0.87, 0.90, 0.01);
    let restore = pulse(t, 0.42, 0.56, 0.01) + pulse(t, 0.90, 0.93, 0.01);
    let leak = pulse(t, 0.70, 0.84, 0.01);

    // sense amp lights up while it senses and fades back in precharge
    let k = smooth(0.42, 0.50, t) * (1.0 - smooth(0.56, 0.70, t));
    let grey = [0.35, 0.36, 0.42];
    let yellow = [1.0, 0.85, 0.25];
    let sa_rgb: [f32; 3] = std::array::from_fn(|i| lerp(grey[i], yellow[i], k) as f32);

    // three dash cycles over the clip; the clip loops, so the phase wraps cleanly
    let phase = (t * 3.0).fract();

    CellAnim {
        wl,
        bl,
        cap,
        sa_rgb,
        read,
        restore,
        leak,
        phase,
    }
}

/// The clip's camera: a slow turntable with a gentle bob in pitch.
pub fn clip_cell_view(t: f64) -> View {
    View {
        yaw: 0.35 + 0.9 * t,
        pitch: 0.25 + 0.05 * (std::f64::consts::TAU * t).sin(),
        ..View::default()
    }
}

/// The overview's layout at `beat` of its seven beats: the camera glides to the part
/// the beat is about (idle, word line, sharing, sense, precharge, leak, refresh).
pub fn overview_params(beat: usize, local: f64) -> CellParams {
    use stage::Shot;
    let d = CellParams::default();
    let whole = Shot { target: d.target, dist: 1440.0, yaw: 0.0, pitch: 0.0 };
    let gate = Shot { target: [0.0, 400.0, 0.0], dist: 1080.0, yaw: 0.0, pitch: 0.0 };
    let path = Shot { target: [0.0, 320.0, 0.0], dist: 1180.0, yaw: 0.0, pitch: 0.0 };
    let amp = Shot { target: [-130.0, 230.0, 0.0], dist: 1120.0, yaw: 0.0, pitch: 0.0 };
    let cap = Shot { target: [d.cap_x, 290.0, 0.0], dist: 860.0, yaw: 0.0, pitch: 0.0 };
    let s = stage::shot_at(&[whole, gate, path, amp, whole, cap, path], beat, local);
    CellParams { target: s.target, cam_dist: s.dist, ..d }
}

/// The focused scenes behind the CELL page: the lettered zooms look closer at parts of
/// the overview, and the numbered ones illustrate the sections of the write-up.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CellZoom {
    /// a: the capacitor, its charge and its leak paths
    Capacitor,
    /// b: a read, as a small cell tank and a big bit line tank
    Read,
    /// c: the rows of an array, sagging and being refreshed
    Rows,
    /// d: one capacitor shrinking, then growing taller
    Shrink,
    /// e: a bit line pair, open and then folded, with noise
    Layout,
    /// 1: a bit is charge: one cell, then a field of ones and zeros
    Bit,
    /// 2: the six parts, one in the spotlight at a time
    Parts,
    /// 3: the five steps of a read as a timing diagram
    Order,
    /// 4: REF commands around the 64 ms window, each refreshing a slice of rows
    RefreshCmds,
    /// 5: cells leaking at different rates, the weakest setting the deadline
    Retention,
    /// 6: cell area in F squares, then the array
    Numbers,
    /// 7: the swing formula: smaller Cc, smaller signal
    Swing,
    /// 8: the three makers
    Makers,
    /// 9: three risks: refresh cost, blocked access, RowHammer
    Risks,
}

/// One scene's camera, solids and overlays.
struct SceneFns {
    beats: usize,
    shot: fn(&stage::Clock) -> stage::Shot,
    solids: fn(&stage::Clock, &mut Vec<Tri>),
    overlay: fn(&mut Canvas, &Cam, &stage::Clock),
}

macro_rules! scene_fns {
    ($m:ident, $beats:expr) => {
        SceneFns {
            beats: $beats,
            shot: $m::shot,
            solids: $m::solids,
            overlay: $m::overlay,
        }
    };
}

impl CellZoom {
    fn scene(self) -> SceneFns {
        match self {
            CellZoom::Capacitor => scene_fns!(zoom_cap, 3),
            CellZoom::Read => scene_fns!(zoom_read, 3),
            CellZoom::Rows => scene_fns!(zoom_rows, 3),
            CellZoom::Shrink => scene_fns!(zoom_shrink, 3),
            CellZoom::Layout => scene_fns!(zoom_layout, 3),
            CellZoom::Bit => scene_fns!(sec_bit, 3),
            CellZoom::Parts => scene_fns!(sec_parts, sec_parts::BEATS),
            CellZoom::Order => scene_fns!(sec_order, sec_order::BEATS),
            CellZoom::RefreshCmds => scene_fns!(sec_refresh, 3),
            CellZoom::Retention => scene_fns!(sec_retention, 3),
            CellZoom::Numbers => scene_fns!(sec_numbers, 3),
            CellZoom::Swing => scene_fns!(sec_swing, 3),
            CellZoom::Makers => scene_fns!(sec_makers, 3),
            CellZoom::Risks => scene_fns!(sec_risks, 3),
        }
    }

    /// How many beats the scene's loop has.
    pub fn beats(self) -> usize {
        self.scene().beats
    }
}

/// One frame of a scene at `beat` and `local` (0..1 through the beat). `view` is the
/// user's orbit, measured from `View::default()`.
pub fn render_zoom(
    z: CellZoom,
    beat: usize,
    local: f64,
    view: &View,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> RgbaImage {
    let f = z.scene();
    let c = stage::Clock {
        beat: beat.min(f.beats - 1),
        local: local.clamp(0.0, 1.0),
    };
    let cam = stage::camera(&(f.shot)(&c), view, w, h);
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    let mut tris: Vec<Tri> = Vec::new();
    (f.solids)(&c, &mut tris);
    rasterize(&mut cv, &cam, tris);
    (f.overlay)(&mut cv, &cam, &c);
    to_image(&cv)
}

/// Opaque solids, depth-tested, back to front.
fn rasterize(cv: &mut Canvas, cam: &Cam, mut tris: Vec<Tri>) {
    tris.sort_by(|x, y| {
        let dx: f64 = x.p.iter().map(|q| cam.view(*q)[2]).sum();
        let dy: f64 = y.p.iter().map(|q| cam.view(*q)[2]).sum();
        dy.partial_cmp(&dx).unwrap_or(std::cmp::Ordering::Equal)
    });
    for tri in &tris {
        cv.fill_tri(cam, tri.p, crate::shade(tri));
    }
}

fn to_image(cv: &Canvas) -> RgbaImage {
    let mut img = RgbaImage::new(cv.w as u32, cv.h as u32);
    for (i, px) in cv.rgb.iter().enumerate() {
        let c = px.map(|c| (c.clamp(0.0, 1.0) * 255.0).round() as u8);
        let (x, y) = ((i % cv.w) as u32, (i / cv.w) as u32);
        img.put_pixel(x, y, image::Rgba([c[0], c[1], c[2], 255]));
    }
    img
}

/// Render one frame at `w` x `h` pixels on a flat `bg` (RGB).
pub fn render_cell(
    p: &CellParams,
    a: &CellAnim,
    view: &View,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> RgbaImage {
    let bg_f = bg.map(|c| c as f32 / 255.0);
    let mut cv = Canvas::new(w, h, bg_f);
    let mut cam = Cam::orbit_at(view, p.target, p.cam_dist, w, h);
    stage::fit_width(&mut cam, w, h);

    let mut tris: Vec<Tri> = Vec::new();
    solids::build(p, a, &mut tris);
    wiring::build(p, a, &mut tris);
    charge::build(p, a, &mut tris);
    glass::build(p, a, &mut tris);
    rasterize(&mut cv, &cam, tris);

    // translucent wireframe, then the flows and names over everything
    glass::frame(&mut cv, &cam, p, a);
    charge::flows(&mut cv, &cam, p, a);
    names(&mut cv, &cam, p, a);
    to_image(&cv)
}

/// A beat's notes, to be drawn on the picture beside the parts they are about.
#[derive(Clone, Copy, Debug, Default)]
pub struct Notes<'a> {
    /// what is happening right now
    pub what: &'a str,
    /// why it matters
    pub why: &'a str,
    /// sourced numbers
    pub facts: &'a [&'a str],
}

/// The parts a note can point at.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Part {
    WordLine,
    Transistor,
    BitLine,
    SenseAmp,
    Capacitor,
    Gauge,
}

impl Part {
    fn at(self, p: &CellParams) -> [f64; 3] {
        match self {
            Part::WordLine => [p.gate_x, p.wl_y, -120.0],
            Part::Transistor => [(p.gate_x + p.cap_x) / 2.0 + 30.0, p.ch_y, 0.0],
            Part::BitLine => [p.bl_x, p.ch_y * 0.62, 0.0],
            Part::SenseAmp => [p.bl_x, p.sa_h * 0.6, p.sa_half_d],
            Part::Capacitor => [p.cap_x + p.plate_r * 0.9, (p.bot_plate_y + p.top_plate_y) / 2.0, 0.0],
            Part::Gauge => [p.gauge_x, p.gauge_h * 0.62, p.gauge_z],
        }
    }
}

/// One overview beat: where the camera sits and which parts its notes point at.
struct Stop {
    shot: stage::Shot,
    what: Part,
    why: Option<Part>,
}

/// The overview's seven beats (idle, word line, sharing, sense, precharge, leak,
/// refresh). Each angle leaves open floor beside the parts its notes are about.
fn stops() -> [Stop; 7] {
    use stage::Shot;
    let d = CellParams::default();
    let shot = |target: [f64; 3], dist: f64, yaw: f64, pitch: f64| Shot { target, dist, yaw, pitch };
    [
        Stop { shot: shot([60.0, 300.0, 0.0], 1500.0, 0.45, 0.25), what: Part::Capacitor, why: Some(Part::Transistor) },
        Stop { shot: shot([20.0, 420.0, 0.0], 1250.0, 0.25, 0.30), what: Part::WordLine, why: Some(Part::Transistor) },
        Stop { shot: shot([-60.0, 330.0, 0.0], 1450.0, 0.55, 0.22), what: Part::BitLine, why: Some(Part::Capacitor) },
        Stop { shot: shot([-20.0, 280.0, 0.0], 1450.0, -0.15, 0.25), what: Part::SenseAmp, why: Some(Part::Gauge) },
        Stop { shot: shot([-80.0, 330.0, 0.0], 1500.0, 0.10, 0.28), what: Part::WordLine, why: Some(Part::Gauge) },
        Stop { shot: shot([d.cap_x, 290.0, 0.0], 1050.0, 0.75, 0.30), what: Part::Capacitor, why: None },
        Stop { shot: shot([0.0, 330.0, 0.0], 1450.0, 0.40, 0.25), what: Part::WordLine, why: Some(Part::SenseAmp) },
    ]
}

/// The camera glides to the beat's angle in this first part of the beat, then holds.
const GLIDE: f64 = 0.25;

/// How strongly the beat's notes show at `local`: they fade in once the camera has
/// settled and out at the very end, so nothing cuts between beats.
pub fn notes_alpha(local: f64) -> f64 {
    smooth(GLIDE, GLIDE + 0.08, local) * (1.0 - smooth(0.965, 0.998, local))
}

/// One overview frame at `beat` and `local` (0..1 through it): the camera at the
/// beat's angle turned by the user's `view` (measured from `View::default()`), the
/// parts named, and the beat's `notes` as boxes beside them.
pub fn render_overview(
    beat: usize,
    local: f64,
    a: &CellAnim,
    view: &View,
    notes: Option<&Notes>,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> RgbaImage {
    let p = CellParams::default();
    let all = stops();
    let keys: Vec<stage::Shot> = all.iter().map(|s| s.shot).collect();
    let n = all.len();
    let beat = beat % n;
    let shot = stage::shot_glide(&keys, beat, local, GLIDE);
    let mut cam = stage::camera(&shot, view, w, h);
    // the cell sits left of centre in a wide frame, leaving the right for the notes
    if w as f64 > h as f64 * 1.3 {
        cam.cx -= w as f64 * 0.13;
    }
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    let mut tris: Vec<Tri> = Vec::new();
    solids::build(&p, a, &mut tris);
    wiring::build(&p, a, &mut tris);
    charge::build(&p, a, &mut tris);
    glass::build(&p, a, &mut tris);
    rasterize(&mut cv, &cam, tris);
    glass::frame(&mut cv, &cam, &p, a);
    charge::flows(&mut cv, &cam, &p, a);
    let mut avoid = names(&mut cv, &cam, &p, a);
    avoid.extend(gauge_rect(&cam, &p));
    if let Some(nt) = notes {
        let stop = &all[beat];
        let mut boxes = Vec::new();
        if !nt.what.is_empty() {
            boxes.push(callout::Callout {
                title: "what's happening",
                body: vec![nt.what.to_string()],
                col: stage::ORANGE,
                anchor: Some(stop.what.at(&p)),
                prefer: (0.7, 0.2),
            });
        }
        if !nt.why.is_empty() {
            boxes.push(callout::Callout {
                title: "why it matters",
                body: vec![nt.why.to_string()],
                col: stage::CYAN,
                anchor: stop.why.map(|q| q.at(&p)),
                prefer: (0.75, 0.55),
            });
        }
        if !nt.facts.is_empty() {
            boxes.push(callout::Callout {
                title: "key numbers",
                body: nt.facts.iter().map(|f| format!("- {f}")).collect(),
                col: stage::PURPLE,
                anchor: None,
                prefer: (1.0, 1.0),
            });
        }
        callout::draw(&mut cv, &cam, &boxes, &avoid, notes_alpha(local));
    }
    to_image(&cv)
}

/// The gauge is glass (lines, not solids), so it is not in the depth buffer: its
/// screen box, for the callouts to keep clear of.
fn gauge_rect(cam: &Cam, p: &CellParams) -> Option<stage::Rect> {
    let mut r = (i64::MAX, i64::MAX, i64::MIN, i64::MIN);
    for k in 0..8 {
        let th = std::f64::consts::TAU * k as f64 / 8.0;
        for y in [0.0, p.gauge_h] {
            let q = [p.gauge_x + p.gauge_r * th.cos(), y, p.gauge_z + p.gauge_r * th.sin()];
            let (x, y, _) = cam.project(q)?;
            r = (r.0.min(x as i64), r.1.min(y as i64), r.2.max(x as i64), r.3.max(y as i64));
        }
    }
    Some(r)
}

/// The overview's parts, named on the picture. A part is brightest while it is acting.
/// Returns where the names went.
fn names(cv: &mut Canvas, cam: &Cam, p: &CellParams, a: &CellAnim) -> Vec<stage::Rect> {
    use stage::label;
    let text = [0.97, 0.97, 0.95];
    let rest = 0.62;
    let lit = |x: f64| rest + (1.0 - rest) * x.clamp(0.0, 1.0);
    let mut out = Vec::new();
    out.extend(label(cv, cam, [p.gate_x, p.wl_y, -150.0], (0.10, -0.03), "word line", [1.0, 0.72, 0.42], lit(a.wl)));
    out.extend(label(cv, cam, [(p.gate_x + p.cap_x) / 2.0, p.ch_y, 0.0], (0.04, -0.11), "access transistor", [1.0, 0.47, 0.78], lit(a.wl)));
    out.extend(label(cv, cam, [p.bl_x, p.ch_y * 0.86, 0.0], (0.03, 0.0), "bit line", [0.55, 0.91, 0.99], lit(a.read + a.restore)));
    out.extend(label(cv, cam, [p.bl_x, p.sa_h, p.sa_half_d], (-0.10, 0.20), "sense amp", text, lit(a.read + a.restore)));
    out.extend(label(cv, cam, [p.cap_x + p.plate_r, p.top_plate_y, 0.0], (0.05, -0.06), "storage capacitor", text, lit(a.leak + a.read)));
    out.extend(label(cv, cam, [p.gauge_x, p.gauge_h, p.gauge_z], (-0.12, -0.05), "bit line voltage", [0.55, 0.91, 0.99], lit(a.read + a.restore)));
    out.extend(label(cv, cam, [p.gauge_x + p.gauge_r, p.gauge_h * 0.5, p.gauge_z], (-0.13, 0.05), "VDD/2", text, 0.85));
    out.extend(label(cv, cam, [p.cap_x + p.plate_r, p.bot_plate_y, 0.0], (0.06, 0.08), "leak", [1.0, 0.50, 0.25], a.leak));
    out
}

/// Axis-aligned box from `lo` to `hi` as 12 triangles. Shading is two-sided, so winding does not matter.
pub(super) fn push_box(m: &mut Vec<Tri>, lo: [f64; 3], hi: [f64; 3], base: [f32; 3], emit: [f32; 3]) {
    let [x0, y0, z0] = lo;
    let [x1, y1, z1] = hi;
    let c = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1],
    ];
    const FACES: [[usize; 4]; 6] = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [0, 1, 5, 4],
        [2, 3, 7, 6],
        [1, 2, 6, 5],
        [0, 3, 7, 4],
    ];
    for f in FACES {
        m.push(Tri { p: [c[f[0]], c[f[1]], c[f[2]]], base, emit });
        m.push(Tri { p: [c[f[0]], c[f[2]], c[f[3]]], base, emit });
    }
}

/// UV sphere of radius `r` at `c`, `seg` segments around and `seg / 2` rings. Flat-shaded.
pub(super) fn push_sphere(m: &mut Vec<Tri>, c: [f64; 3], r: f64, seg: usize, base: [f32; 3], emit: [f32; 3]) {
    let rings = (seg / 2).max(2);
    let pt = |i: usize, j: usize| {
        let phi = std::f64::consts::PI * j as f64 / rings as f64;
        let th = std::f64::consts::TAU * i as f64 / seg as f64;
        [
            c[0] + r * phi.sin() * th.cos(),
            c[1] + r * phi.cos(),
            c[2] + r * phi.sin() * th.sin(),
        ]
    };
    for j in 0..rings {
        for i in 0..seg {
            let (a, b, cc, d) = (pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1));
            m.push(Tri { p: [a, b, cc], base, emit });
            m.push(Tri { p: [a, cc, d], base, emit });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const ZOOMS: [CellZoom; 14] = [
        CellZoom::Capacitor,
        CellZoom::Read,
        CellZoom::Rows,
        CellZoom::Shrink,
        CellZoom::Layout,
        CellZoom::Bit,
        CellZoom::Parts,
        CellZoom::Order,
        CellZoom::RefreshCmds,
        CellZoom::Retention,
        CellZoom::Numbers,
        CellZoom::Swing,
        CellZoom::Makers,
        CellZoom::Risks,
    ];

    fn zoom(z: CellZoom, beat: usize, local: f64) -> RgbaImage {
        render_zoom(z, beat, local, &View::default(), 320, 276, [0x28, 0x2a, 0x36])
    }

    fn mean_diff(a: &RgbaImage, b: &RgbaImage) -> f64 {
        let sum: u64 = a
            .as_raw()
            .iter()
            .zip(b.as_raw())
            .map(|(x, y)| u64::from(x.abs_diff(*y)))
            .sum();
        sum as f64 / a.as_raw().len() as f64
    }

    /// No cuts: the last frame of each beat nearly matches the first of the next, and
    /// the last beat runs back into the first, so the loop has no seam either.
    #[test]
    fn zooms_have_no_cut_between_beats() {
        for z in ZOOMS {
            let n = z.beats();
            for beat in 0..n {
                let end = zoom(z, beat, 0.9995);
                let next = zoom(z, (beat + 1) % n, 0.0);
                let d = mean_diff(&end, &next);
                assert!(d < 0.6, "{z:?} beat {beat} jumps by {d}");
            }
        }
    }

    #[test]
    fn zooms_change_over_a_beat_and_orbit() {
        for z in ZOOMS {
            let a = zoom(z, 1, 0.1);
            let b = zoom(z, 1, 0.8);
            assert!(mean_diff(&a, &b) > 0.3, "{z:?} barely moves");
            let mut v = View::default();
            v.orbit(0.5, 0.0);
            let turned = render_zoom(z, 1, 0.1, &v, 320, 276, [0x28, 0x2a, 0x36]);
            assert_ne!(a.as_raw(), turned.as_raw(), "{z:?} ignores the orbit");
        }
    }


    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn frame(a: &CellAnim) -> RgbaImage {
        render_cell(&CellParams::default(), a, &View::default(), 160, 90, BG)
    }

    #[test]
    fn default_state_has_flat_background_and_draws() {
        let img = frame(&CellAnim::default());
        assert_eq!(img.get_pixel(0, 0).0, [BG[0], BG[1], BG[2], 255]);
        assert!(
            img.pixels().any(|px| px.0[..3] != BG),
            "the cell draws something"
        );
    }

    #[test]
    fn charge_changes_the_frame() {
        let full = frame(&CellAnim { cap: 1.0, ..CellAnim::default() });
        let empty = frame(&CellAnim { cap: 0.0, ..CellAnim::default() });
        assert_ne!(full.as_raw(), empty.as_raw(), "cap 1 and cap 0 differ");
    }

    #[test]
    fn leak_changes_the_frame() {
        let off = frame(&CellAnim { leak: 0.0, ..CellAnim::default() });
        let on = frame(&CellAnim { leak: 1.0, ..CellAnim::default() });
        assert_ne!(off.as_raw(), on.as_raw(), "leak 1 and leak 0 differ");
    }

    #[test]
    fn clip_starts_charged_and_word_line_rises() {
        let start = clip_cell_anim(0.0);
        assert_eq!(start.cap, 1.0);
        assert_eq!(start.wl, 0.0);
        assert!(clip_cell_anim(0.3).wl > 0.9);
    }
}
