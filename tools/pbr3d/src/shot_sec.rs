//! MELT + PULL sections 1-9, shaded like the overview. Section 1 is the puller itself, read
//! in time order; 2 and 3 are the puller and its physics; 4-6 and 8 are charts and plates
//! drawn to the page's figures; 7 is the risk list; 9 is the source pile.

use crate::math::V3;
use crate::melt::{self, state_at, State};
use crate::mesh::{Mat, Mesh};
use crate::shot::Pic;
use crate::shot_parts::*;

/// The picture of section `n` (1-9) at beat `beat` and local progress `local`.
pub fn section(n: u8, beat: usize, local: f32) -> Pic {
    match n {
        1 => s1(beat, local),
        2 => s2(beat, local),
        3 => s3(beat, local),
        4 => s4(beat, local),
        5 => s5(beat, local),
        6 => s6(beat, local),
        7 => s7(beat, local),
        8 => s8(beat, local),
        _ => s9(beat, local),
    }
}

/// The overview's camera: it follows the crystal up as the body grows.
fn overview_target(s: &State) -> V3 {
    [0.0, 60.0 + 260.0 * s.body.min(700.0) / 700.0, 0.0]
}

fn contact(s: &State) -> f32 {
    melt::level(s) + s.hang + s.lift
}

/// Gauge and chart colour: a plain metal bar, lit when `on`.
fn chart_mat(on: bool) -> Mat {
    if on {
        Mat::new([1.0, 0.55, 0.2], 0.0, 0.3).emit([1.6, 0.7, 0.25])
    } else {
        Mat::new([0.42, 0.44, 0.48], 0.6, 0.4)
    }
}

/// A row of value bars on the floor of a bare stage: value `v` drawn at `scale` mm per unit.
fn value_bars(
    m: &mut Mesh,
    xs: &[f32],
    vals: &[f32],
    lit: Option<usize>,
    scale: f32,
    grow: f32,
    floor: f32,
) {
    for (k, (&x, &v)) in xs.iter().zip(vals).enumerate() {
        let on = lit == Some(k);
        bar(m, x, 0.0, 120.0, floor, v * scale * grow, &chart_mat(on));
    }
}

// ---- 1: what happens -------------------------------------------------------------------

fn s1(beat: usize, local: f32) -> Pic {
    // the overview's own states, one per beat: load, melt, seed and neck, body, tail
    let s = match beat {
        0 => state_at(0, local),
        1 => state_at(1, local),
        2 => state_at(2, local),
        3 => state_at(4, local),
        _ => state_at(5, local),
    };
    let t = overview_target(&s);
    Pic::rig(s, t, 5000.0, 0.5, 0.06)
}

// ---- 2: inside a puller ----------------------------------------------------------------

fn s2(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the water-cooled chamber holds argon around the crucible and the melt
            let s = state_at(2, 0.0);
            let mut p = Pic::rig(s, [0.0, 300.0, 0.0], 5200.0, 0.5, 0.05);
            stream(&mut p.solid, &argon_route(), 50, local, 14.0, 1000, &ARGON);
            p
        }
        1 => {
            // the pull shaft lowers the seed, then the neck, shoulder and body form as it lifts
            let s = state_at(3, local);
            Pic::rig(s, [0.0, 900.0, 0.0], 4200.0, 0.5, 0.05)
        }
        2 => {
            // the crucible rises as the melt drops; a tick marks the melt level
            let s = state_at(4, 0.6 + 0.4 * local);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, -200.0, 0.0], 2600.0, 0.5, 0.1);
            p.solid.cuboid([380.0, lv, 0.0], [8.0, 4.0, 60.0], &METAL);
            p
        }
        _ => {
            // the heater and heat shield set the heat; argon carries SiO and CO out the base
            let s = state_at(5, 0.5);
            let mut p = Pic::rig(s, [0.0, -200.0, 0.0], 4600.0, 0.5, 0.05);
            stream(&mut p.solid, &argon_route(), 40, local, 14.0, 1100, &ARGON);
            stream(
                &mut p.solid,
                &argon_route(),
                16,
                local + 0.3,
                16.0,
                1200,
                &GAS_CO,
            );
            p
        }
    }
}

// ---- 3: physics and chemistry ----------------------------------------------------------

fn s3(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // growth: atoms lock onto the crystal's edge at the freezing point, in its orientation
            let s = state_at(4, 0.4);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv + 60.0, 0.0], 900.0, 0.4, 0.1);
            let n = 16;
            for k in 0..n {
                let a = std::f32::consts::TAU * k as f32 / n as f32;
                let at = [158.0 * a.cos(), lv + 12.0, 158.0 * a.sin()];
                let lit = (k as f32) < local * n as f32;
                let m = if lit { &ATOM_LIT } else { &ATOM };
                p.solid.shard(at, 16.0, 2000 + k as u32, m);
            }
            p
        }
        1 => {
            // mass flow: pull rate x cross-section x density is the silicon frozen each hour
            let s = state_at(4, 0.7);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv + 300.0, 0.0], 1900.0, 0.4, 0.02);
            let rise = line([172.0, lv + 10.0, 0.0], [172.0, lv + 420.0, 0.0], 10);
            stream(&mut p.solid, &rise, 10, local, 12.0, 2100, &ATOM_LIT);
            p
        }
        2 => {
            // oxygen: the quartz wall gives up SiO, and some oxygen freezes into the crystal
            let s = state_at(4, 0.7);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [200.0, lv, 0.0], 1000.0, 0.9, 0.1);
            let path = line([300.0, lv + 12.0, 0.0], [150.0, lv + 14.0, 0.0], 8);
            stream(&mut p.solid, &path, 6, local, 10.0, 2200, &GAS_CO);
            p
        }
        _ => {
            // segregation: the solute prefers the liquid, so the melt gets richer as the pull goes
            let s = state_at(5, 0.4);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [0.0, lv, 0.0], 1700.0, 0.2, 0.9);
            let n = 6 + (30.0 * local) as usize;
            cloud(&mut p.solid, n, lv + 6.0, 260.0, 6.0, 2300, 10.0, &DOPANT);
            p
        }
    }
}

// ---- 4: by the numbers -----------------------------------------------------------------

fn s4(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the melt sits near 1414 C; the gradient runs from hot at the melt to cool up the rod
            let s = state_at(4, 0.8);
            let lv = melt::level(&s);
            let mut p = Pic::rig(s, [1000.0, 400.0, 0.0], 4200.0, 0.55, 0.05);
            let bands = 8;
            for k in 0..bands {
                let t = k as f32 / (bands - 1) as f32;
                let y0 = lv + 1500.0 * k as f32 / bands as f32;
                let e = [
                    1.6 * (1.0 - t) + 0.1,
                    0.6 * (1.0 - t) + 0.2,
                    0.2 * (1.0 - t) + 0.6,
                ];
                let m = Mat::new([0.2, 0.2, 0.22], 0.0, 0.4).emit(e);
                bar(
                    &mut p.solid,
                    1350.0,
                    0.0,
                    90.0,
                    y0,
                    1500.0 / bands as f32 - 4.0,
                    &m,
                );
            }
            p.solid.cuboid([1350.0, lv, 0.0], [120.0, 4.0, 4.0], &METAL);
            p
        }
        1 => {
            // the furnace settings as gauges: argon 100 L/min, 2500 Pa, a 310 kW heater; counter-rotation
            let s = state_at(4, 0.8);
            let mut p = Pic::rig(s, [1100.0, -300.0, 0.0], 4200.0, 0.55, 0.05);
            let g = local;
            bar(
                &mut p.solid,
                1350.0,
                0.0,
                110.0,
                -1100.0,
                600.0 * g,
                &chart_mat(true),
            );
            bar(
                &mut p.solid,
                1560.0,
                0.0,
                110.0,
                -1100.0,
                625.0 * g,
                &chart_mat(true),
            );
            bar(
                &mut p.solid,
                1770.0,
                0.0,
                110.0,
                -1100.0,
                620.0 * g,
                &chart_mat(true),
            );
            let up = arc(470.0, -300.0, -0.2, 2.6, 40);
            let down: Vec<V3> = arc(470.0, -300.0, 2.6, -0.2, 40);
            p.solid.tube(&up, 8.0, 8, &HOT);
            p.solid.tube(&down, 8.0, 8, &FIELD);
            p
        }
        2 => {
            // a 300 mm wafer needs a body of 300 mm or more; the body can reach 2 m
            let s = state_at(5, 0.0);
            let mut p = Pic::rig(s, [800.0, 0.0, 0.0], 4000.0, 0.5, 0.05);
            p.solid
                .cuboid([1250.0, 100.0, 0.0], [20.0, 1000.0, 20.0], &METAL);
            p.solid.disc(150.0, -1095.0, true, 64, &ATOM);
            p
        }
        _ => {
            // a 1.6 mm/min simulated pull shifts the interface 33 mm over the run
            let s = state_at(5, 0.5);
            let base = contact(&s);
            let mut p = Pic::rig(s, [0.0, base + 60.0, 0.0], 1200.0, 0.4, 0.1);
            p.solid
                .cuboid([0.0, base, 0.0], [175.0, 1.5, 175.0], &METAL);
            let moved = base + 33.0 * local;
            p.solid
                .cuboid([0.0, moved, 0.0], [178.0, 2.5, 178.0], &chart_mat(true));
            p
        }
    }
}

// ---- 5: pull-rate figures --------------------------------------------------------------

fn s5(beat: usize, local: f32) -> Pic {
    // the four rates as bars to scale: 6.0 dash neck, 1.6 body, 2.4 neck example, 0.5 dash-free
    let xs = [-360.0, -120.0, 120.0, 360.0];
    let vals = [6.0, 1.6, 2.4, 0.5];
    let mut p = Pic::bare(beat, local, [0.0, 500.0, 0.0], 2600.0, 0.35, 0.2);
    ground(&mut p.solid, 0.0, 1400.0);
    let lit = Some(beat.min(3));
    value_bars(&mut p.solid, &xs, &vals, lit, 320.0, smooth(local), 0.0);
    p
}

// ---- 6: who owns the crystal -----------------------------------------------------------

fn s6(beat: usize, local: f32) -> Pic {
    // the five 300 mm shares as the page lists them: 26.7, 25.0, 15.0, 11.7, 9.2 (sum 87.6)
    let names_x = [-480.0, -240.0, 0.0, 240.0, 480.0];
    let shares = [26.7, 25.0, 15.0, 11.7, 9.2];
    let mut p = Pic::bare(beat, local, [0.0, 500.0, 0.0], 2800.0, 0.3, 0.2);
    ground(&mut p.solid, 0.0, 1400.0);
    let g = smooth(local);
    match beat {
        0 => value_bars(
            &mut p.solid,
            &names_x[..2],
            &shares[..2],
            Some(0),
            40.0,
            g,
            0.0,
        ),
        1 => {
            // all five add up to 87.6%, and the top two hold about 51.7%
            value_bars(&mut p.solid, &names_x, &shares, None, 40.0, g, 0.0);
            p.solid.cuboid(
                [0.0, 87.6 * 40.0 * g, 0.0],
                [560.0, 1.5, 4.0],
                &chart_mat(true),
            );
            p.glass.cuboid(
                [0.0, 77.0 * 40.0, 0.0],
                [580.0, 2.0, 6.0],
                &Mat::new([0.9, 0.93, 0.96], 0.0, 0.03)
                    .alpha(0.3)
                    .kind(crate::mesh::Kind::Glass),
            );
        }
        2 => {
            // other sources disagree: each bar sits in a band of uncertainty, not one value
            value_bars(&mut p.solid, &names_x, &shares, None, 40.0, 1.0, 0.0);
            for (k, (&x, &share)) in names_x.iter().zip(&shares).enumerate() {
                let h = share * 40.0;
                let spread = 40.0 + 60.0 * hash_unit(k as u32);
                p.glass.cuboid(
                    [x, h * 0.5, 0.0],
                    [84.0, h * 0.5 + spread * g, 84.0],
                    &Mat::new([0.9, 0.93, 0.96], 0.0, 0.03)
                        .alpha(0.14)
                        .kind(crate::mesh::Kind::Glass),
                );
            }
        }
        _ => {
            // each maker grows its own crystals in-house: a puller stands on every bar
            value_bars(&mut p.solid, &names_x, &shares, None, 40.0, 1.0, 0.0);
            let puller = Mat::new([0.55, 0.55, 0.57], 1.0, 0.32).cut();
            for &share in &shares {
                let top = share * 40.0;
                p.solid
                    .frustum(60.0, top, 60.0, top + 180.0 * g, 36, &puller);
                p.solid.disc(60.0, top + 180.0 * g, true, 36, &puller);
            }
        }
    }
    p
}

// ---- 7: chokepoints and risks ----------------------------------------------------------

fn s7(beat: usize, local: f32) -> Pic {
    match beat {
        0 => {
            // the quartz crucible is consumed in every pull; its supply can stop
            let mut p = Pic::bare(beat, local, [0.0, -150.0, 0.0], 2400.0, 0.5, 0.08);
            ground(&mut p.solid, -480.0, 1800.0);
            let k = 1.0 - 0.25 * local;
            // the rig's crucible profile, shrunk about the crucible bottom
            let prof: Vec<(f32, f32)> = [
                (0.0, -460.0),
                (120.0, -472.0),
                (220.0, -450.0),
                (282.0, -390.0),
                (305.0, -310.0),
                (305.0, -60.0),
            ]
            .iter()
            .map(|&(r, y)| (r * k, -480.0 + (y + 480.0) * k))
            .collect();
            p.glass
                .lathe(&prof, 0.0, std::f32::consts::TAU, 96, true, &QUARTZ);
            cloud(
                &mut p.solid,
                14,
                -480.0,
                500.0,
                60.0,
                2500,
                60.0,
                &Mat::new([0.6, 0.6, 0.62], 0.0, 0.9),
            );
            p
        }
        1 => {
            // one dislocation anywhere in the body means the crystal is remelted
            let mut s = state_at(5, 0.5);
            s.lift = -300.0 * local;
            let lv = melt::level(&s);
            let base = contact(&s);
            let mut p = Pic::rig(s, [0.0, lv + 300.0, 0.0], 2800.0, 0.3, 0.06);
            let dislocation = line([162.0, base + 500.0, 0.0], [162.0, base + 40.0, 0.0], 14);
            p.solid.tube(&dislocation, 6.0, 8, &DISLOC);
            p
        }
        2 => {
            // oxygen and dopant uniformity across a 300 mm wafer is the hard control problem
            let mut p = Pic::bare(beat, local, [0.0, 0.0, 0.0], 520.0, 0.3, 1.1);
            p.solid.disc(150.0, 0.0, true, 96, &ATOM);
            for i in -5i32..=5 {
                for j in -5i32..=5 {
                    let (x, z) = (i as f32 * 26.0, j as f32 * 26.0);
                    if x * x + z * z > 140.0 * 140.0 {
                        continue;
                    }
                    let h = hash_unit((i * 31 + j) as u32);
                    let m = if h > 0.5 { &HOT } else { &DOPANT };
                    p.solid
                        .shard([x, 6.0, z], 10.0 + 8.0 * h, (i * 17 + j) as u32 + 3000, m);
                }
            }
            p
        }
        _ => {
            // demand is cyclical: wafer revenue and shipments rise and fall
            let mut p = Pic::bare(beat, local, [0.0, 500.0, 0.0], 2800.0, 0.35, 0.2);
            ground(&mut p.solid, 0.0, 1400.0);
            for i in 0..10 {
                let x = -540.0 + 120.0 * i as f32;
                let phase = i as f32 / 10.0 + local;
                let h = 700.0 + 500.0 * (std::f32::consts::TAU * phase).sin();
                bar(&mut p.solid, x, 0.0, 90.0, 0.0, h, &chart_mat(i % 3 == 0));
            }
            p
        }
    }
}

// ---- 8: listed names -------------------------------------------------------------------

fn s8(beat: usize, local: f32) -> Pic {
    // four listed makers as plates; SK Siltron sits under SK Inc; two puller makers apart
    let mut p = Pic::bare(beat, local, [0.0, 60.0, 0.0], 1700.0, 0.3, 0.25);
    ground(&mut p.solid, 0.0, 1400.0);
    let g = smooth(local);
    let xs = [-480.0, -160.0, 160.0, 480.0];
    let up = 60.0 + 120.0 * g;
    let plate = |on: bool| {
        if on {
            Mat::new([0.95, 0.9, 0.85], 0.2, 0.2).emit([0.7, 0.6, 0.4])
        } else {
            Mat::new([0.4, 0.42, 0.46], 0.5, 0.35)
        }
    };
    for (k, &x) in xs.iter().enumerate() {
        let on = beat == 0 || (beat == 1 && k == 2);
        p.solid
            .cuboid([x, up * 0.5, 0.0], [130.0, up * 0.5, 130.0], &plate(on));
    }
    match beat {
        1 => {
            // SK Siltron, held by SK Inc: a small plate under the bigger one, joined by a link
            p.solid
                .cuboid([160.0, -120.0, 0.0], [70.0, 40.0, 70.0], &plate(true));
            p.solid.tube(
                &line([160.0, -60.0, 0.0], [160.0, -80.0, 0.0], 2),
                10.0,
                8,
                &METAL,
            );
        }
        2 => {
            // the puller makers are a separate list: two small plates set apart
            for (k, &x) in [-200.0f32, 200.0].iter().enumerate() {
                let m =
                    Mat::new([0.7, 0.5, 0.25], 0.3, 0.3).emit([0.4, 0.22, 0.05 * (k as f32 + 1.0)]);
                p.solid
                    .cuboid([x, 120.0 * g * 0.5, -420.0], [80.0, 60.0 * g, 80.0], &m);
            }
        }
        3 => {
            // the tickers and puller makers are general knowledge: the plates turn to glass
            for &x in &xs {
                p.glass.cuboid(
                    [x, up * 0.5, 0.0],
                    [134.0, up * 0.5 + 4.0, 134.0],
                    &Mat::new([0.9, 0.93, 0.96], 0.0, 0.03)
                        .alpha(0.2)
                        .kind(crate::mesh::Kind::Glass),
                );
            }
        }
        _ => {}
    }
    p
}

// ---- 9: sources ------------------------------------------------------------------------

fn s9(beat: usize, local: f32) -> Pic {
    // four piles of documents, one per source group; the one for this beat rises and lights
    let mut p = Pic::bare(beat, local, [0.0, 60.0, 0.0], 1700.0, 0.35, 0.25);
    ground(&mut p.solid, 0.0, 1400.0);
    let xs = [-480.0, -160.0, 160.0, 480.0];
    for (k, &x) in xs.iter().enumerate() {
        let on = k == beat;
        let pages = if on {
            8 + (6.0 * smooth(local)) as usize
        } else {
            8
        };
        let m = if on {
            Mat::new([0.95, 0.94, 0.9], 0.0, 0.5).emit([0.5, 0.45, 0.35])
        } else {
            Mat::new([0.82, 0.8, 0.76], 0.0, 0.6)
        };
        for q in 0..pages {
            let y = 4.0 + 8.0 * q as f32;
            p.solid.cuboid([x, y, 0.0], [120.0, 4.0, 110.0], &m);
        }
    }
    p
}

// ---- helpers ---------------------------------------------------------------------------

fn smooth(x: f32) -> f32 {
    let t = x.clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// Deterministic 0..1 from a small integer.
fn hash_unit(k: u32) -> f32 {
    crate::mesh::hash01(k.wrapping_mul(977).wrapping_add(13))
}
