//! The Czochralski puller, overview: charge loads into a quartz crucible, melts under a
//! graphite heater, a seed touches the melt and a dash neck is pulled, the shoulder
//! flares to full diameter, the body grows, the tail tapers and the crystal lifts clear.
//!
//! Units are millimetres, Y up, the crystal axis is X = Z = 0. Each beat is a time
//! window on one clock `t` in beats (0..6); the chamber is cut away on the camera side
//! so the furnace reads from inside.

use crate::gpu::Frame;
use crate::math::{self, V3};
use crate::mesh::{hash01, Kind, Mat, Mesh};

pub const BEATS: usize = 6;

// ---- fixed dimensions ----
pub const CRU_BOT: f32 = -480.0; // crucible bottom at rest
pub const CRU_H: f32 = 420.0; // crucible height to the rim
pub const MELT_Y: f32 = -120.0; // melt surface, full crucible, at rest
pub const CRU_R: f32 = 305.0; // crucible outer radius
pub const HEATER_R: f32 = 420.0;
pub const FELT_R: f32 = 520.0;
pub const CHAMBER_R: f32 = 1000.0;
pub const SEED_L: f32 = 60.0;
pub const NECK_R: f32 = 14.0; // exaggerated from the real 2-4 mm so it reads at this scale
pub const BODY_R: f32 = 150.0;
pub const CHUCK_H: f32 = 70.0;
pub const PULL_TOP: f32 = 2050.0;

/// The crystal and the stack above the melt at time `t`.
#[derive(Clone, Copy, Debug, Default)]
pub struct State {
    /// seed bottom above the melt
    pub hang: f32,
    /// the whole stack lifted clear of the melt
    pub lift: f32,
    /// grown lengths, mm: neck, shoulder, body, tail
    pub neck: f32,
    pub shoulder: f32,
    pub body: f32,
    pub tail: f32,
    /// melt fill, 0..1
    pub fill: f32,
    /// graphite heater power, 0..1
    pub heat: f32,
    /// crystal radius scale, 0..1 (the crystal is cooled and removed at the loop)
    pub vanish: f32,
    /// crucible rise to keep the melt level, mm
    pub cru_up: f32,
    /// chunk fall (beat 0) and chunk melt (beat 1), 0..1
    pub fall: f32,
    pub melt_in: f32,
    /// beat index and its local progress
    pub beat: usize,
    pub local: f32,
}

fn smooth(a: f32, b: f32, x: f32) -> f32 {
    let t = ((x - a) / (b - a)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// The state at beat `beat` with local progress `local` (0..1 through the beat).
pub fn state_at(beat: usize, local: f32) -> State {
    let beat = beat % BEATS;
    let t = beat as f32 + local.clamp(0.0, 1.0);
    let mut s = State { beat, local, ..Default::default() };

    // loop reset in beat 0: the crystal cools and vanishes, the melt drains, the seed rises
    let reset = smooth(0.0, 0.5, t);
    // the crystal appears after the loop reset and is taken out at the loop's end
    s.vanish = smooth(0.0, 0.3, t) * (1.0 - smooth(5.7, 6.0, t));
    s.hang = 900.0 * reset;
    s.lift = 500.0 * (1.0 - reset);
    s.fill = if t < 1.0 { 1.0 - smooth(0.0, 0.2, t) } else { smooth(1.0, 1.9, t) };
    s.heat = if t < 1.0 {
        1.0 - smooth(0.0, 0.4, t)
    } else {
        smooth(1.0, 1.9, t)
    };
    s.fall = if beat == 0 { smooth(0.0, 0.9, local) } else { 1.0 };
    s.melt_in = if beat == 1 { smooth(0.0, 0.95, local) } else if beat > 1 { 1.0 } else { 0.0 };

    // SEED: hold the seed up, lower it until it touches the melt, then pull the neck
    s.hang = if t < 0.5 {
        900.0 * reset
    } else if t < 2.0 {
        900.0
    } else {
        900.0 * (1.0 - smooth(2.0, 2.4, t))
    };
    s.neck = 140.0 * smooth(2.4, 3.0, t);
    // SHOULDER: flare out to full diameter
    s.shoulder = 260.0 * smooth(3.0, 4.0, t);
    // BODY: grow at about the same pace; the crucible rises to hold the melt level
    s.body = 700.0 * smooth(4.0, 5.0, t);
    s.cru_up = 60.0 * smooth(4.0, 5.0, t);
    // TAIL: taper, then lift clear of the melt
    s.tail = 240.0 * smooth(5.0, 5.6, t);
    s.lift = if t < 0.5 {
        500.0 * (1.0 - reset)
    } else if t < 5.6 {
        0.0
    } else {
        500.0 * smooth(5.6, 6.0, t)
    };
    s
}

/// The camera: orbit around `target` at `dist`, looking at the cut.
#[derive(Clone, Copy, Debug)]
pub struct Cam {
    pub target: V3,
    pub dist: f32,
    pub yaw: f32,
    pub pitch: f32,
}

/// Lighting and camera for a beat, from a state.
pub fn frame_for(s: &State, cam: &Cam, w: u32, h: u32, time: f32, bg: [f32; 3]) -> Frame {
    let (sy, cy) = cam.yaw.sin_cos();
    let (sp, cp) = cam.pitch.sin_cos();
    let eye = math::add(cam.target, [cam.dist * cp * sy, cam.dist * sp, cam.dist * cp * cy]);
    let view = math::look_at(eye, cam.target, [0.0, 1.0, 0.0]);
    let proj = math::perspective(0.52, w as f32 / h.max(1) as f32, 40.0, 40000.0);
    let view_proj = math::mul(proj, view);

    // sun: fixed in the world, shadows the furnace onto the crucible and the crystal
    let sun = math::norm([-0.55, 0.8, 0.42]);
    let light_c = [0.0, 300.0, 0.0];
    let light_eye = math::add(light_c, math::scale(sun, 9000.0));
    let light_view = math::look_at(light_eye, light_c, [0.0, 1.0, 0.0]);
    let light_proj = math::ortho(-3600.0, 3600.0, -3600.0, 3600.0, 2000.0, 16000.0);
    let light_vp = math::mul(light_proj, light_view);

    let melt_y = cru_level(s);
    let heat = s.heat;
    Frame {
        view_proj,
        light_vp,
        cam_pos: eye,
        sun_dir: sun,
        sun_col: [3.2, 3.0, 2.7],
        pt_pos: [0.0, melt_y + 260.0, 0.0],
        pt_radius: 1100.0,
        pt_col: [2.2 * heat, 0.8 * heat, 0.3 * heat],
        clip_n: [sy, 0.0, cy],
        clip_d: 0.0,
        sky: [0.5, 0.56, 0.68],
        ground: [0.05, 0.045, 0.04],
        time,
        bg,
        bloom: 0.22,
        exposure: 0.9,
        proj_diag: [1.0 / (0.26f32).tan() / (w as f32 / h.max(1) as f32), 1.0 / (0.26f32).tan()],
        near_far: [40.0, 40000.0],
        ao_radius: 110.0,
        ao_strength: 0.85,
    }
}

/// The melt surface height for the state.
pub fn level(s: &State) -> f32 {
    cru_level(s)
}

fn cru_level(s: &State) -> f32 {
    let base = CRU_BOT + s.cru_up;
    let full = MELT_Y;
    base + 60.0 + (full - base - 60.0) * s.fill
}

/// Builds the opaque and glass meshes for a state.
pub fn build(s: &State) -> (Mesh, Mesh) {
    let mut solid = Mesh::new();
    let mut glass = Mesh::new();
    let b = CRU_BOT + s.cru_up; // crucible bottom
    let level = cru_level(s);

    // ---- chamber: steel, cut ----
    let steel = Mat::new([0.55, 0.55, 0.57], 1.0, 0.32).cut().tex(3.0);
    let floor = -1100.0;
    solid.frustum(CHAMBER_R, floor, CHAMBER_R, 500.0, 128, &steel);
    solid.disc(CHAMBER_R, floor, true, 128, &steel.tex(1.0));
    solid.lathe(
        &dome(CHAMBER_R, 500.0, 900.0, 430.0, 14),
        0.0,
        std::f32::consts::TAU,
        128,
        true,
        &steel,
    );
    solid.frustum(430.0, 900.0, 430.0, PULL_TOP, 96, &steel);
    solid.disc(430.0, PULL_TOP, true, 96, &steel);

    // flanges and bolt rings on the chamber, with the pull chamber's own flange
    let bolt = Mat::new([0.4, 0.4, 0.42], 1.0, 0.35).cut();
    let mut bolts = Mesh::new();
    bolts.frustum(14.0, 0.0, 14.0, 46.0, 14, &bolt);
    for (y, r) in [(500.0f32, 1030.0f32), (-1040.0, 1030.0), (900.0, 430.0 + 40.0), (PULL_TOP - 60.0, 430.0 + 40.0)] {
        let n = if r > 500.0 { 24 } else { 18 };
        solid.lathe(&[(r + 60.0, y), (r + 60.0, y + 24.0), (r, y + 24.0), (r, y + 60.0)], 0.0, std::f32::consts::TAU, 96, false, &steel);
        for k in 0..n {
            let a = std::f32::consts::TAU * k as f32 / n as f32;
            solid.append_at(&bolts, [(r + 30.0) * a.cos(), y + 46.0, (r + 30.0) * a.sin()]);
        }
    }

    // ---- chamber hardware: sight windows, gas outlet, winch housing, cooling pipes ----
    let frame = Mat::new([0.42, 0.42, 0.44], 1.0, 0.3).tex(3.0);
    let pane = Mat::new([0.9, 0.93, 0.96], 0.0, 0.03).alpha(0.16).kind(Kind::Glass);
    for side in [1.0f32, -1.0] {
        let x = 1000.0 * side;
        let yc = -150.0;
        // frame: top and bottom rails, two posts, as flat bars on the wall
        solid.cuboid([x + 8.0 * side, yc + 146.0, 0.0], [14.0, 12.0, 160.0], &frame);
        solid.cuboid([x + 8.0 * side, yc - 146.0, 0.0], [14.0, 12.0, 160.0], &frame);
        solid.cuboid([x + 8.0 * side, yc, 148.0], [14.0, 134.0, 12.0], &frame);
        solid.cuboid([x + 8.0 * side, yc, -148.0], [14.0, 134.0, 12.0], &frame);
        glass.cuboid([x, yc, 0.0], [2.0, 136.0, 146.0], &pane);
    }
    // gas outlet on the -X side: a pipe through the wall with a flange
    let mut outlet = Mesh::new();
    outlet.frustum(55.0, 0.0, 55.0, 460.0, 32, &frame);
    outlet.disc(90.0, 0.0, true, 32, &frame);
    solid.append_at(&outlet.swapped_xy(), [-1460.0, -600.0, 0.0]);
    // winch housing on the pull chamber, and its motor
    solid.cuboid([0.0, PULL_TOP + 230.0, 0.0], [300.0, 230.0, 300.0], &frame.tex(3.0));
    solid.cuboid([0.0, PULL_TOP + 560.0, 0.0], [150.0, 110.0, 150.0], &Mat::new([0.1, 0.1, 0.11], 0.2, 0.45));
    // water cooling pipes down the pull chamber
    let copper = Mat::new([0.82, 0.46, 0.26], 1.0, 0.28).tex(4.0);
    let mut pipe = Mesh::new();
    pipe.frustum(16.0, 0.0, 16.0, 1140.0, 16, &copper);
    for k in 0..4 {
        let a = std::f32::consts::FRAC_PI_2 * k as f32 + 0.3;
        solid.append_at(&pipe, [452.0 * a.cos(), 880.0, 452.0 * a.sin()]);
    }

    // ---- insulation felt: dark, fibrous, cut ----
    let felt = Mat::new([0.10, 0.095, 0.09], 0.0, 0.92).kind(Kind::Felt).cut();
    solid.frustum(FELT_R, -820.0, FELT_R, 180.0, 128, &felt);
    solid.disc(FELT_R, -820.0, true, 128, &felt);

    // ---- graphite heater: slotted panels, glowing with power ----
    let graphite = Mat::new([0.075, 0.072, 0.07], 0.0, 0.55).cut().tex(2.0);
    let glow = [1.0 * 1.8 * s.heat, 0.36 * 1.8 * s.heat, 0.1 * 1.8 * s.heat];
    let heater = graphite.emit(glow);
    let n_panels = 26;
    let slot = 0.20;
    for k in 0..n_panels {
        let a0 = std::f32::consts::TAU * k as f32 / n_panels as f32;
        let a1 = a0 + std::f32::consts::TAU / n_panels as f32 * (1.0 - slot);
        solid.panel(HEATER_R, -520.0, 40.0, a0, a1, 4, 14, &heater);
    }

    // ---- upper heat shield and its lid, graphite, cut ----
    solid.lathe(
        &[(430.0, 40.0), (260.0, 210.0), (170.0, 420.0), (150.0, 520.0)],
        0.0,
        std::f32::consts::TAU,
        96,
        true,
        &graphite,
    );
    solid.lathe(&[(150.0, 40.0), (430.0, 40.0)], 0.0, std::f32::consts::TAU, 96, false, &graphite);

    // ---- crucible support (bowl) and the shaft ----
    let shaft = Mat::new([0.09, 0.085, 0.08], 0.0, 0.5).tex(2.0);
    solid.frustum(55.0, -1100.0, 55.0, b + 10.0, 48, &shaft);
    let bowl = graphite.clone();
    solid.lathe(
        &[
            (0.0, b - 30.0),
            (200.0, b - 22.0),
            (300.0, b + 4.0),
            (336.0, b + 50.0),
            (340.0, b + 140.0),
            (338.0, b + 170.0),
        ],
        0.0,
        std::f32::consts::TAU,
        96,
        true,
        &bowl,
    );

    // ---- melt: the glowing body and surface ----
    let melt_r = 230.0 + 66.0 * s.fill;
    let melt = Mat::new([0.035, 0.02, 0.014], 0.0, 0.04)
        .kind(Kind::Melt)
        .emit([1.0 * 1.6 * s.heat, 0.42 * 1.6 * s.heat, 0.12 * 1.6 * s.heat]);
    if s.fill > 0.01 {
        // the body of the melt is dimmer than its surface: the glow comes off the top
        let body = Mat::new([0.05, 0.03, 0.02], 0.0, 0.1).kind(Kind::Melt).emit([0.7 * s.heat, 0.22 * s.heat, 0.06 * s.heat]);
        solid.lathe(&[(0.0, b + 40.0), (melt_r * 0.92, b + 40.0), (melt_r * 0.92, level)], 0.0, std::f32::consts::TAU, 96, false, &body);
        solid.disc(melt_r, level, true, 96, &melt);
    }

    // ---- the quartz crucible: glass, drawn last ----
    let quartz = Mat::new([0.9, 0.92, 0.95], 0.0, 0.04).alpha(0.22).kind(Kind::Glass);
    glass.lathe(
        &[
            (0.0, b + 20.0),
            (120.0, b + 8.0),
            (220.0, b + 30.0),
            (282.0, b + 90.0),
            (CRU_R, b + 170.0),
            (CRU_R, b + CRU_H),
        ],
        0.0,
        std::f32::consts::TAU,
        96,
        true,
        &quartz,
    );

    // ---- charge: polysilicon chunks falling in, then melting ----
    let poly = Mat::new([0.44, 0.46, 0.5], 0.92, 0.28);
    let molten = Mat::new([0.9, 0.5, 0.2], 0.0, 0.1).emit([1.4, 0.55, 0.2]);
    for k in 0..26u32 {
        let r = 120.0 * hash01(k * 3 + 1).sqrt();
        let th = hash01(k * 3 + 2) * std::f32::consts::TAU;
        let x = r * th.cos();
        let z = r * th.sin();
        let rest_y = b + 90.0 + 120.0 * hash01(k * 3 + 3);
        let drop_from = 1100.0;
        let fall = s.fall;
        let y = rest_y + (drop_from - rest_y) * (1.0 - fall) * (1.0 - fall);
        // size shrinks as the chunk dissolves
        let mut size = 60.0 + 40.0 * hash01(k + 77);
        let melt_t = s.melt_in * (0.6 + 0.4 * hash01(k + 11));
        size *= (1.0 - melt_t).max(0.0);
        if size < 2.0 {
            continue;
        }
        let mat = if melt_t > 0.05 && s.fall >= 1.0 { molten } else { poly };
        // chunks are only in the crucible until they melt, and fall in beat 0
        if s.melt_in >= 1.0 {
            continue;
        }
        solid.shard([x, y, z], size, k + 5, &mat);
    }

    // ---- the crystal: silicon, seed through tail, bottom at the melt ----
    let si = Mat::new([0.035, 0.045, 0.06], 0.75, 0.16).kind(Kind::Silicon);
    let base = level + s.hang + s.lift;
    if s.vanish > 0.02 {
        let v = s.vanish;
        let mut y = base;
        let tail_r = 40.0;
        // tail (bottom): cone from a point up to the body
        if s.tail > 0.5 {
            let prof: Vec<(f32, f32)> = (0..=10)
                .map(|i| {
                    let u = i as f32 / 10.0;
                    let r = lerp(tail_r, BODY_R, u * u * (3.0 - 2.0 * u));
                    (r * v, y + s.tail * u)
                })
                .collect();
            solid.lathe(&prof, 0.0, std::f32::consts::TAU, 72, true, &si);
            y += s.tail;
        }
        if s.body > 0.5 {
            solid.frustum(BODY_R * v, y, BODY_R * v, y + s.body, 72, &si);
            y += s.body;
        }
        if s.shoulder > 0.5 {
            let prof: Vec<(f32, f32)> = (0..=12)
                .map(|i| {
                    let u = i as f32 / 12.0;
                    let e = 0.5 - 0.5 * (std::f32::consts::PI * u).cos();
                    (lerp(BODY_R, NECK_R, e) * v, y + s.shoulder * u)
                })
                .collect();
            solid.lathe(&prof, 0.0, std::f32::consts::TAU, 72, true, &si);
            y += s.shoulder;
        }
        if s.neck > 0.5 {
            solid.frustum(NECK_R * v, y, NECK_R * v, y + s.neck, 24, &si);
            y += s.neck;
        }
        // the seed itself, held in the chuck
        solid.frustum(NECK_R * v, y, NECK_R * v, y + SEED_L, 24, &si);
        y += SEED_L;

        // chuck and pull rod up to the pull chamber
        let steel_c = Mat::new([0.7, 0.7, 0.72], 1.0, 0.25);
        solid.frustum(32.0, y, 32.0, y + CHUCK_H, 48, &steel_c);
        solid.frustum(3.0, y + CHUCK_H, 3.0, PULL_TOP, 12, &steel_c);
    }

    (solid, glass)
}

fn lerp(a: f32, b: f32, t: f32) -> f32 {
    a + (b - a) * t
}

/// The chamber dome: from radius `r0` at height `y0` in to radius `r1` at height `y1`.
fn dome(r0: f32, y0: f32, y1: f32, r1: f32, n: usize) -> Vec<(f32, f32)> {
    (0..=n)
        .map(|i| {
            let u = i as f32 / n as f32;
            let a = u * std::f32::consts::FRAC_PI_2;
            (r1 + (r0 - r1) * a.cos(), y0 + (y1 - y0) * a.sin())
        })
        .collect()
}
