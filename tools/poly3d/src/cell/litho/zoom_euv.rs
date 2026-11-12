//! Zoom f: why EUV is hard. Three beats. A CO2 laser hits each tin droplet twice, and
//! the second pulse turns it into the plasma that gives 13.5 nm light. With no glass to
//! carry that light, it bounces down a chain of multilayer mirrors, each keeping about
//! 70%, so a dozen of them leave about 1%. And every mirror and stage has to hold
//! sub-nanometre alignment, from parts built by a long global supply chain.

use super::super::stage::{
    self, glass_box, label, particles, text, Clock, Shot, CYAN, GLASS, GREEN, NO_GLOW, ORANGE,
    PINK, STEEL, TEXT, YELLOW,
};
use super::super::{push_box, push_sphere};
use crate::{Cam, Canvas, Col, Tri, V3};

const TIN: Col = [0.72, 0.76, 0.80];
const NOZZLE_Y: f64 = 460.0;
const IMPACT: V3 = [0.0, 250.0, 0.0];
const DROPLETS: usize = 5;
/// mirrors along the light's path: x and height. Each is 110 wide and 200 deep.
const MIRRORS: [(f64, f64); 6] = [
    (-375.0, 180.0),
    (-225.0, 240.0),
    (-75.0, 180.0),
    (75.0, 240.0),
    (225.0, 180.0),
    (375.0, 240.0),
];
/// share of the light one Mo/Si mirror keeps
const KEEP: f64 = 0.7;
/// the parts that make up the mirror stack, shown in a pile in beat 2
const PARTS: usize = 60;

const SHOTS: [Shot; 3] = [
    Shot {
        target: [0.0, 300.0, 0.0],
        dist: 1400.0,
        yaw: 0.35,
        pitch: 0.20,
    },
    Shot {
        target: [0.0, 190.0, 0.0],
        dist: 2000.0,
        yaw: 0.20,
        pitch: 0.30,
    },
    Shot {
        target: [-150.0, 130.0, 150.0],
        dist: 1450.0,
        yaw: 0.55,
        pitch: 0.30,
    },
];

pub(super) fn shot(c: &Clock) -> Shot {
    stage::shot_at(&SHOTS, c.beat, c.local)
}

/// The light's path: in from the left, off each mirror in turn, out to the right.
fn light_path() -> Vec<V3> {
    let mut p = vec![[-480.0, 260.0, 0.0]];
    p.extend(MIRRORS.iter().map(|&(x, y)| [x, y, 0.0]));
    p.push([480.0, 240.0, 0.0]);
    p
}

/// A cheap deterministic hash in 0..1, for scatter that stays put between frames.
fn hash(i: usize, s: f64) -> f64 {
    ((i as f64 * 12.9898 + s).sin() * 43758.5453).rem_euclid(1.0)
}

/// Beat 0 plasma: rises at the impact and fades after pulse 2.
fn plasma(c: &Clock) -> f64 {
    c.ramp(0, 0.5, 0.6) * (1.0 - c.ramp(0, 0.7, 0.9))
}

/// How far the light has got along the path, in segments: 0 at the start, 7 at the end.
fn front(c: &Clock) -> f64 {
    c.ramp(1, 0.1, 0.7) * (MIRRORS.len() + 1) as f64
}

/// The mirror chain rises from below during the end of beat 0, then stays.
fn chain_k(c: &Clock) -> f64 {
    c.ramp(0, 0.9, 1.0)
}

fn push_mirror(m: &mut Vec<Tri>, x: f64, y: f64, dx: f64, lit: f64) {
    let base = stage::mix(STEEL, CYAN, 0.45);
    push_box(
        m,
        [x - 55.0 + dx, y - 6.0, -100.0],
        [x + 55.0 + dx, y + 6.0, 100.0],
        base,
        stage::scaled(YELLOW, 0.25 * lit),
    );
}

pub(super) fn solids(c: &Clock, m: &mut Vec<Tri>) {
    let u = c.u();

    // beat 0: the nozzle and the droplets falling onto the impact point
    push_box(
        m,
        [-14.0, NOZZLE_Y - 12.0, -14.0],
        [14.0, NOZZLE_Y + 12.0, 14.0],
        STEEL,
        NO_GLOW,
    );
    for i in 0..DROPLETS {
        let p = (u * 2.0 + i as f64 / DROPLETS as f64).rem_euclid(1.0);
        if p > 0.9 {
            continue;
        }
        let y = NOZZLE_Y - (NOZZLE_Y - IMPACT[1]) * p;
        push_sphere(m, [0.0, y, 0.0], 9.0, 8, TIN, NO_GLOW);
    }
    // pulse 1 flattens the droplet into a disc
    if c.during(0, 0.36, 0.5) > 0.01 {
        push_box(
            m,
            [IMPACT[0] - 26.0, IMPACT[1] - 3.0, -26.0],
            [IMPACT[0] + 26.0, IMPACT[1] + 3.0, 26.0],
            TIN,
            NO_GLOW,
        );
    }
    // pulse 2 turns it into plasma, which emits 13.5 nm light
    let k = plasma(c);
    if k > 0.01 {
        push_sphere(
            m,
            IMPACT,
            12.0 + 40.0 * k,
            12,
            stage::mix(TIN, YELLOW, k),
            stage::scaled(YELLOW, 0.9 * k),
        );
    }

    // beats 1 and 2: the mirror chain, and the vacuum that holds it
    let ck = chain_k(c);
    let dy = -260.0 * (1.0 - ck);
    let shake = c.ramp(2, 0.0, 0.2);
    let lit = front(c).min(MIRRORS.len() as f64 + 1.0) / (MIRRORS.len() as f64 + 1.0);
    for (i, &(x, y)) in MIRRORS.iter().enumerate() {
        // beat 2: one mirror shakes, a picture of the sub-nanometre drift
        let dx = if i == 2 {
            3.0 * shake * (u * 7.0).sin()
        } else {
            0.0
        };
        push_mirror(m, x, y + dy, dx, lit * ck);
    }

    // the parts: they grow in during the end of beat 1, scatter, then settle into a pile
    // in front of the stack during beat 2
    let appear = c.ramp(1, 0.6, 1.0);
    let settle = c.ramp(2, 0.0, 0.5);
    if appear > 0.01 {
        let half = 4.5 * appear;
        for i in 0..PARTS {
            let (a, b, cc) = (i % 5, (i / 5) % 3, i / 15);
            let home = [
                -330.0 + 26.0 * a as f64,
                10.0 + 22.0 * b as f64,
                250.0 + 26.0 * cc as f64,
            ];
            let scatter = [
                (hash(i, 1.0) - 0.5) * 220.0,
                120.0 + 200.0 * hash(i, 2.0),
                (hash(i, 3.0) - 0.5) * 220.0,
            ];
            let p = [
                home[0] + (1.0 - settle) * scatter[0],
                home[1] + (1.0 - settle) * scatter[1],
                home[2] + (1.0 - settle) * scatter[2],
            ];
            let col = stage::mix(STEEL, GREEN, 0.2 + 0.4 * hash(i, 4.0));
            push_box(
                m,
                [p[0] - half, p[1] - half, p[2] - half],
                [p[0] + half, p[1] + half, p[2] + half],
                col,
                NO_GLOW,
            );
        }
    }
}

pub(super) fn overlay(cv: &mut Canvas, cam: &Cam, c: &Clock) {
    let u = c.u();
    let (w, h) = (cv.w as f64, cv.h as f64);

    // beat 0: the CO2 laser, two pulses, debris and the EUV light
    let p1 = c.during(0, 0.22, 0.36);
    let p2 = c.during(0, 0.5, 0.66);
    let laser = c.during(0, 0.18, 0.7);
    if laser > 0.01 {
        let a = (0.15 + 0.6 * (p1 + p2)).min(1.0) * laser;
        cv.line(cam, [-420.0, IMPACT[1], 0.0], IMPACT, ORANGE, a as f32);
    }
    let k = plasma(c);
    particles(
        cv,
        cam,
        &[IMPACT, [0.0, 120.0, 0.0]],
        6,
        u * 1.5,
        6.0,
        YELLOW,
        k,
    );
    let debris = c.ramp(0, 0.6, 0.7) * (1.0 - c.ramp(0, 0.9, 1.0));
    for j in 0..4 {
        let ang = j as f64 * std::f64::consts::FRAC_PI_2 + 0.4;
        let end = [
            IMPACT[0] + 150.0 * ang.cos(),
            IMPACT[1] + 40.0,
            IMPACT[2] + 150.0 * ang.sin(),
        ];
        particles(
            cv,
            cam,
            &[IMPACT, end],
            3,
            u * 1.3 + j as f64 * 0.25,
            5.0,
            PINK,
            debris,
        );
    }
    label(
        cv,
        cam,
        [0.0, NOZZLE_Y, 0.0],
        (0.06, -0.04),
        "tin droplets: about 50,000 a second",
        TEXT,
        c.during(0, 0.0, 0.95),
    );
    label(
        cv,
        cam,
        [-200.0, IMPACT[1], 0.0],
        (0.0, -0.08),
        "CO2 laser pulse 1 flattens the droplet",
        ORANGE,
        p1,
    );
    label(
        cv,
        cam,
        [-200.0, IMPACT[1] - 40.0, 0.0],
        (0.0, -0.08),
        "pulse 2 vaporises it: 13.5 nm light",
        YELLOW,
        p2,
    );
    label(
        cv,
        cam,
        [150.0, IMPACT[1] + 40.0, 0.0],
        (0.04, -0.05),
        "debris and splatter",
        PINK,
        debris,
    );

    // beats 1 and 2: the light, reflecting off each mirror and losing a share
    let fr = front(c);
    let ck = chain_k(c);
    let path = light_path();
    for i in 0..path.len() - 1 {
        let f = (fr - i as f64).clamp(0.0, 1.0);
        if f <= 0.0 {
            continue;
        }
        let a = 0.9 * f * KEEP.powi(i as i32) * ck;
        let p0 = path[i];
        let q = [
            p0[0] + (path[i + 1][0] - p0[0]) * f,
            p0[1] + (path[i + 1][1] - p0[1]) * f,
            0.0,
        ];
        cv.line(cam, p0, q, YELLOW, a as f32);
    }
    let dy = -260.0 * (1.0 - ck);
    for (i, &(x, y)) in MIRRORS.iter().enumerate() {
        let reached = (fr - (i + 1) as f64).clamp(0.0, 1.0) * ck;
        let yy = y + dy;
        // the share a mirror does not reflect falls away as heat
        particles(
            cv,
            cam,
            &[[x, yy - 8.0, 0.0], [x, yy - 90.0, 0.0]],
            3,
            u * 1.1 + i as f64 * 0.3,
            5.0,
            ORANGE,
            reached * 0.8,
        );
        label(
            cv,
            cam,
            [x, yy + 34.0, 0.0],
            (-0.02, -0.05),
            "70%",
            YELLOW,
            reached * c.during(1, 0.0, 0.95),
        );
    }
    let vac = c.ramp(1, 0.0, 0.25) * ck;
    glass_box(
        cv,
        cam,
        [-470.0, 80.0, -150.0],
        [470.0, 300.0, 150.0],
        GLASS,
        (0.14 * vac) as f32,
    );
    label(
        cv,
        cam,
        [-470.0, 300.0, 0.0],
        (0.0, -0.06),
        "vacuum: air and glass absorb EUV",
        TEXT,
        c.during(1, 0.0, 0.95),
    );
    label(
        cv,
        cam,
        [400.0, 120.0, 0.0],
        (0.0, 0.05),
        "after 6 mirrors: 12% left",
        YELLOW,
        c.during(1, 0.5, 0.95),
    );
    text(
        cv,
        (w * 0.04) as i64,
        (h * 0.04) as i64,
        "no glass: the light must bounce",
        TEXT,
        c.during(1, 0.0, 0.95),
    );
    text(
        cv,
        (w * 0.04) as i64,
        (h * 0.10) as i64,
        "each mirror keeps about 70%; a dozen leave about 1%",
        ORANGE,
        c.during(1, 0.3, 0.95),
    );

    // beat 2: sub-nanometre alignment and the parts behind it
    label(
        cv,
        cam,
        [-75.0, 240.0 + 40.0, 0.0],
        (-0.25, -0.12),
        "a mirror off by a nanometre ruins the layer",
        PINK,
        c.during(2, 0.2, 0.95),
    );
    label(
        cv,
        cam,
        [-200.0, 60.0, 280.0],
        (0.0, 0.08),
        "hundreds of thousands of parts",
        GREEN,
        c.during(2, 0.4, 0.95),
    );
    label(
        cv,
        cam,
        [375.0, 260.0, 0.0],
        (0.0, -0.06),
        "Zeiss ultra-flat optics",
        CYAN,
        c.during(2, 0.3, 0.95),
    );
    text(
        cv,
        (w * 0.04) as i64,
        (h * 0.04) as i64,
        "sub-nanometre alignment, held in vacuum",
        TEXT,
        c.during(2, 0.0, 0.95),
    );
    text(
        cv,
        (w * 0.04) as i64,
        (h * 0.10) as i64,
        "built from a long chain of specialist suppliers",
        CYAN,
        c.during(2, 0.3, 0.95),
    );
}
