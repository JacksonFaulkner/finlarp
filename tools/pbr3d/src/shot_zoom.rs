//! MELT + PULL zooms, shaded like the overview: a the dash neck, b the melt convection and
//! the magnetic field, c the hot zone and the argon sweep. Four beats each.

use crate::math::V3;
use crate::melt::{self, state_at, State};
use crate::mesh::Mat;
use crate::shot::Pic;
use crate::shot_parts::*;

/// Where the crystal meets the melt: its tail, at the melt level plus the hang and lift.
fn contact(s: &State) -> f32 {
    melt::level(s) + s.hang + s.lift
}

/// The top of the grown crystal, below the seed.
fn stack_top(s: &State) -> f32 {
    contact(s) + s.tail + s.body + s.shoulder + s.neck
}

/// A quadratic curve from `a` to `c` bending through `b`.
fn bezier(a: V3, b: V3, c: V3, n: usize) -> Vec<V3> {
    (0..=n)
        .map(|i| {
            let t = i as f32 / n as f32;
            let u = 1.0 - t;
            let mut p = [0.0f32; 3];
            for k in 0..3 {
                p[k] = u * u * a[k] + 2.0 * u * t * b[k] + t * t * c[k];
            }
            p
        })
        .collect()
}

// ---- a: the dash neck ------------------------------------------------------------------

pub fn neck(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the seed touches the melt; the contact throws dislocations up into the crystal
            let s = state_at(2, 0.4);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv + 150.0, 0.0], 1000.0, 0.5, 0.1);
            let ring = arc(
                40.0 + 300.0 * local,
                lv + 3.0,
                0.0,
                std::f32::consts::TAU,
                48,
            );
            p.solid.tube(&ring, 9.0, 8, &HOT);
            let up = line([24.0, lv, 0.0], [24.0, lv + 260.0, 0.0], 8);
            stream(&mut p.solid, &up, 10, local, 9.0, 7, &DISLOC);
            p
        }
        1 => {
            // the dash neck is pulled; dislocations slide out of it, sideways and up
            let s = state_at(2, 0.9);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv + 200.0, 0.0], 900.0, 0.5, 0.1);
            for k in 0..6 {
                let y = lv + 80.0 + 40.0 * k as f32;
                let out = line([15.0, y, 0.0], [70.0 + 10.0 * k as f32, y + 90.0, 0.0], 6);
                stream(&mut p.solid, &out, 2, local, 7.0, 40 + k, &DISLOC);
            }
            p
        }
        2 => {
            // the neck carries the whole crystal: a load arrow hangs above it
            let s = state_at(4, 0.6);
            let top = stack_top(&s);
            let mut p = Pic::rig(s, [0.0, top - 300.0, 0.0], 2000.0, 0.3, 0.05);
            p.solid
                .cuboid([0.0, top + 140.0, 0.0], [6.0, 140.0, 6.0], &METAL);
            p.solid
                .cuboid([0.0, top - 10.0, 0.0], [30.0, 20.0, 30.0], &METAL);
            p
        }
        _ => {
            // a dislocation that stays in the neck runs down the body and forces a remelt
            let mut s = state_at(5, 0.5);
            s.lift = -250.0 * local;
            let lv = melt::level(&s);
            let base = contact(&s);
            let mut p = Pic::rig(s, [0.0, lv + 300.0, 0.0], 1500.0, 0.3, 0.08);
            let line_d = line([162.0, base + 260.0, 0.0], [162.0, base + 40.0, 0.0], 12);
            p.solid.tube(&line_d, 6.0, 8, &DISLOC);
            let splash = arc(170.0, lv + 2.0, 0.0, std::f32::consts::TAU, 16);
            stream(&mut p.solid, &splash, 12, local, 10.0, 90, &HOT);
            p
        }
    }
}

// ---- b: melt convection and the magnetic field -----------------------------------------

pub fn convection(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the melt convects: the hot wall drives rolls, and the rotation adds a swirl
            let mut s = state_at(3, 0.5);
            s.vanish = 0.0;
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv, 0.0], 1300.0, 0.2, 0.7);
            // on the surface: a swirl about the axis, and the wall-fed flow sinking back in
            let swirl = arc(200.0, lv + 10.0, 0.0, std::f32::consts::TAU, 48);
            stream(&mut p.solid, &swirl, 16, local * 0.5, 14.0, 300, &TRACER);
            for k in 0..4u32 {
                let a = std::f32::consts::FRAC_PI_2 * k as f32 + 0.4;
                let back = line(
                    [260.0 * a.cos(), lv + 10.0, 260.0 * a.sin()],
                    [60.0 * a.cos(), lv + 10.0, 60.0 * a.sin()],
                    6,
                );
                stream(&mut p.solid, &back, 3, local, 12.0, 320 + k * 7, &TRACER);
            }
            p
        }
        1 => {
            // a horizontal magnetic field brakes the flow: the rolls slow as the field grips
            let mut s = state_at(3, 0.5);
            s.vanish = 0.0;
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv, 0.0], 1300.0, 0.2, 0.7);
            for z in [-150.0f32, 0.0, 150.0] {
                let field: Vec<V3> = (0..=40)
                    .map(|i| {
                        let u = i as f32 / 40.0;
                        [
                            -280.0 + 560.0 * u,
                            lv - 40.0 + 90.0 * (std::f32::consts::PI * u).sin(),
                            z,
                        ]
                    })
                    .collect();
                p.solid.tube(&field, 7.0, 8, &FIELD);
            }
            let slow = 1.0 - 0.7 * local;
            let swirl = arc(200.0, lv + 10.0, 0.0, std::f32::consts::TAU, 48);
            stream(
                &mut p.solid,
                &swirl,
                (16.0 * slow) as usize + 2,
                local * 0.15,
                14.0,
                300,
                &TRACER,
            );
            p
        }
        2 => {
            // the solid-liquid interface flattens: a bulge under the crystal goes flat
            let s = state_at(4, 0.5);
            let base = contact(&s);
            let mut p = Pic::rig(s, [0.0, base + 120.0, 0.0], 1500.0, 0.2, 0.1);
            let depth = 80.0 * (1.0 - local);
            let mut prof = Vec::new();
            for i in 0..=8 {
                let u = i as f32 / 8.0;
                prof.push((150.0 * u, base - depth * (1.0 - u * u)));
            }
            p.solid
                .lathe(&prof, 0.0, std::f32::consts::TAU, 72, true, &HOT);
            p
        }
        _ => {
            // SiO from the quartz wall: flakes slough into the melt, and bubbles rise
            let s = state_at(4, 0.9);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [260.0, lv - 20.0, 0.0], 800.0, 0.9, 0.1);
            for k in 0..8u32 {
                let a = -0.6 + 1.2 * hash(k);
                let fall = 160.0 * local * (0.5 + hash(k + 9));
                let pos = [305.0 * a.cos(), lv + 40.0 - fall, 305.0 * a.sin()];
                p.solid.shard(pos, 26.0, 500 + k, &QUARTZ);
            }
            let bubbles = line([235.0, lv - 120.0, 0.0], [235.0, lv + 60.0, 0.0], 8);
            stream(&mut p.solid, &bubbles, 6, local, 10.0, 540, &GAS_CO);
            p
        }
    }
}

/// Flow tracers on the bright melt: dark, so they read against it.
const TRACER: Mat = Mat::new([0.04, 0.04, 0.05], 0.0, 0.5);

/// Deterministic 0..1 from a small integer.
fn hash(k: u32) -> f32 {
    crate::mesh::hash01(k * 2654 + 17)
}

// ---- c: the hot zone and the argon sweep ------------------------------------------------

pub fn hot_zone(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the graphite heater surrounds the crucible, wrapped in felt
            let s = state_at(3, 0.5);
            Pic::rig(s, [0.0, -420.0, 0.0], 2500.0, 0.45, 0.05)
        }
        1 => {
            // heat leaves through the crystal: the gradient runs hot at the melt, cool up top
            let s = state_at(4, 0.9);
            let base = contact(&s);
            let body = s.body;
            let mut p = Pic::rig(s, [0.0, base + body * 0.5, 0.0], 2200.0, 0.45, 0.05);
            let bands = 6;
            for k in 0..bands {
                let y0 = base + body * k as f32 / bands as f32;
                let y1 = base + body * (k + 1) as f32 / bands as f32;
                let t = k as f32 / (bands - 1) as f32;
                let e = [
                    1.5 * (1.0 - t) + 0.1,
                    0.45 * (1.0 - t) + 0.2,
                    0.12 * (1.0 - t) + 0.5,
                ];
                let m = Mat::new([0.2, 0.2, 0.22], 0.0, 0.4).emit(e);
                p.solid.frustum(155.0, y0, 155.0, y1, 72, &m);
            }
            let flux = line([185.0, base, 0.0], [185.0, base + body, 0.0], 8);
            stream(&mut p.solid, &flux, 8, local, 11.0, 600, &HOT);
            p
        }
        2 => {
            // the heat shield above the melt limits the radiant heat reaching the crystal
            let s = state_at(5, 0.3);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv + 500.0, 0.0], 2600.0, 0.45, 0.1);
            for k in 0..5 {
                let a = -0.9 + 0.45 * k as f32;
                let from = [300.0 * a.cos(), lv + 2.0, 300.0 * a.sin()];
                let to = [250.0 * a.cos(), 230.0, 250.0 * a.sin()];
                let ctrl = [340.0 * a.cos(), 60.0, 340.0 * a.sin()];
                let path = bezier(from, ctrl, to, 14);
                let cut = ((local * 2.0) * 14.0) as usize + 1;
                p.solid.tube(&path[..cut.min(path.len())], 6.0, 8, &HOT);
            }
            p
        }
        _ => {
            // argon enters at the top, sweeps past the crystal and leaves the base with SiO and CO
            let s = state_at(5, 0.9);
            let mut p = Pic::rig(s, [0.0, 0.0, 0.0], 4300.0, 0.4, 0.08);
            let route = argon_route();
            stream(&mut p.solid, &route, 60, local, 14.0, 700, &ARGON);
            stream(&mut p.solid, &route, 20, local + 0.3, 16.0, 800, &GAS_CO);
            p
        }
    }
}
