// POLYSILICON page, overview: the Siemens route as one animation, left to
// right: crush metallurgical silicon, hydrochlorinate it in a fluidized bed,
// distil the chlorosilanes, deposit silicon on glowing rods in a bell jar,
// recycle the off-gas, finish the rods into product. Zooms (a-d) open the
// fluidized bed, the distillation column, the bell jar, and the recycle loop.
//
// Sources: Fraunhofer ISE (2025) flowchart + figures, Swetha Priya et al.
// (2015) Siemens CVD reactor, Geng & Yu (UMD 2011) process scenarios.

use super::diagrams_scene_column as col;
use super::diagrams_scene_poly_zoom as zoom;
use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, flicker, noise};

const BEAT_MS: u64 = 5200;
pub const MIN_W: u16 = 100;
pub const MIN_H: u16 = 30;

#[cfg(test)]
const CRUSH: usize = 0;
const FBR: usize = 1;
const DISTILL: usize = 2;
const DEPOSIT: usize = 3;
const RECYCLE: usize = 4;
const FINISH: usize = 5;

const BEATS: &[Beat] = &[
    Beat::new(
        "metallurgical silicon (98-99% pure) is crushed to a fine powder",
        BEAT_MS,
    )
    .note(
        "The feed is the metallurgical-grade silicon from the furnace on the SAND page. It is too impure for chips, so the plan is to turn it into a gas, clean the gas, and grow pure silicon back out of it. First it is crushed so it reacts fast.",
        "Lumps dropping from the MG-Si hopper through the crusher and out as a stream of fine grains toward the first vessel.",
    )
    .detail(
        "Grinding gives the HCl a large surface to work on, because the reactor can only convert what it touches.",
        &[
            "MG-Si is 98-99% pure",
            "Chip grade (Special EG) allows at most 1.5e12 donor atoms per cm3 (Fraunhofer)",
            "Silicon itself has about 5e22 atoms per cm3, so that is roughly one dopant atom in 30 billion",
        ],
    ),
    Beat::new(
        "fluidized bed, about 300 C: Si + HCl ─▶ trichlorosilane (SiHCl3, 'TCS') + H2, with some SiCl4",
        BEAT_MS,
    )
    .note(
        "HCl gas blown up from the bottom keeps the grains floating like a boiling liquid. Silicon reacts with it to make TCS, a liquid at room temperature that boils at 31.8 C. Many metal impurities form chlorides too, which is why the next step exists.",
        "Grains swirling and bubbling in the bed, HCl entering at the bottom, and product vapor leaving the top toward the columns.",
    )
    .detail(
        "Turning silicon into a gas is what makes purification possible. You can distil a gas but not a solid metal.",
        &[
            "About 300 C (Fraunhofer)",
            "TCS boils at 31.8 C, so it leaves as a vapor",
            "Practical mix: roughly 3.1 HCl per Si, giving mostly TCS with a little SiCl4 plus H2 (Fraunhofer)",
        ],
    ),
    Beat::new(
        "distillation: TCS boils at 31.8 C, SiCl4 at 56.8 C; boron, phosphorus and metal chlorides are split off",
        BEAT_MS,
    )
    .note(
        "Three columns in a row separate the mixture by boiling point. Light stuff such as H2 and BCl3 (°) boils off at the top, the product TCS (●) is in the middle, and heavy SiCl4 (■) sinks. Each hop between trays is richer in the light species going up and in SiCl4 going down, so the columns sort the mixture.",
        "Between trays: mostly ● and ° hopping near the top of each column, mostly ■ near the bottom of column 2. The pipes between columns carry less ■ each time as the TCS gets purer. Press b for one column up close.",
    )
    .detail(
        "Distillation is where purity is made. It removes the boron and phosphorus that would otherwise dope the silicon and ruin chips.",
        &[
            "TCS 31.8 C, SiCl4 56.8 C, DCS 8.1 C, H2 -252.8 C (Fraunhofer)",
            "Chip grade needs 1.66 times more distillation cycles than solar grade",
            "NASA 1986: phosphorus in TCS fell from 3.2 to about 0.05 ppba as reflux rose from 1.2 to 12.5",
        ],
    ),
    Beat::new(
        "bell jar at ~1100 C: SiHCl3 + H2 ─▶ Si + 3HCl; pure silicon grows on glowing rods from 20 mm to 150-180 mm",
        BEAT_MS,
    )
    .note(
        "Thin silicon rods are heated by electric current. TCS and hydrogen flow over them and silicon deposits layer by layer. The rods grow at up to 1.9 mm an hour, so a batch takes days. This is the Siemens reactor.",
        "The ▓ rods glowing and visibly fattening during this beat, gas ° rising from the base nozzles, and HCl leaving through the off-gas port.",
    )
    .detail(
        "Deposition is the slowest and most energy-hungry step, so it sets the cost. Growth rate trades off against how uniform the rods are.",
        &[
            "Rods grow from 20 mm to 150-180 mm at up to 1.9 mm an hour (Fraunhofer)",
            "Batch: about 3.5 days solar grade, about 6.7 days chip grade",
            "Rod temperature 1050-1100 C; supply 100-300 V at up to 5000 A (Swetha Priya et al.)",
        ],
    ),
    Beat::new(
        "off-gas is recovered: H2 back to the reactor, HCl back to the fluidized bed, SiCl4 to silicones",
        BEAT_MS,
    )
    .note(
        "The reactor exhaust is not wasted. A recovery unit separates hydrogen and HCl from the chlorosilanes. H2 returns to the bell jar, HCl returns to the first vessel, leftover chlorosilanes go back through distillation, and SiCl4 is sold on or converted back to TCS.",
        "Packets looping along the bottom lines: H2 ° back to the reactor, HCl * back to the bed, and SiCl4 · to its bin.",
    )
    .detail(
        "Recycling cuts raw material and energy cost. HCl and hydrogen are reused instead of bought again, and the silicon in SiCl4 is recovered.",
        &[
            "H2 returns to the CVD feed; HCl returns to hydrochlorination (Fraunhofer)",
            "SiCl4 goes to silicones and silica, or is converted back to TCS",
            "Condensation units separate H2 and HCl from the chlorosilane liquid",
        ],
    ),
    Beat::new(
        "finished rods are pulled, crushed, etched and packed as chunks or rods",
        BEAT_MS,
    )
    .note(
        "After the batch the reactor is cooled and opened and the rods are pulled out. They are crushed to size, etched with acid to clean the surface, and packed. Chip makers buy this as chunks or whole rods.",
        "▓ pieces moving down through crush, etch and pack on the right.",
    )
    .detail(
        "Handling can contaminate a surface that took days to grow, so the last steps are about cleaning and packing without recontaminating it.",
        &[
            "Sold as blocks (chunks of 6-150 mm) or as rods (Fraunhofer)",
            "Etching with HNO3 and HF mixtures or alkaline etching removes surface metals",
            "Surface should be dense and smooth",
        ],
    ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the fluidized bed",
        build: || -> Box<dyn Scene> { Box::new(zoom::FluidBed) },
    },
    Zoom {
        key: 'b',
        label: "inside a distillation column",
        build: || -> Box<dyn Scene> { Box::new(zoom::Column) },
    },
    Zoom {
        key: 'c',
        label: "the Siemens bell jar",
        build: || -> Box<dyn Scene> { Box::new(zoom::BellJar) },
    },
    Zoom {
        key: 'd',
        label: "recycling and the growth-rate trade-off",
        build: || -> Box<dyn Scene> { Box::new(zoom::Recycle) },
    },
];

const CHUTE: Particles = Particles::new(102, 300, 1800);
const VAPOR: Particles = Particles::new(103, 380, 2400);
const DRAFT: Particles = Particles::new(104, 150, 1900);
const OFFGAS: Particles = Particles::new(105, 320, 2600);
const LOOP_H2: Particles = Particles::new(106, 420, 3200);
const LOOP_HCL: Particles = Particles::new(107, 460, 3200);
const LOOP_STC: Particles = Particles::new(108, 520, 3200);
const PIECES: Particles = Particles::new(109, 700, 3600);

fn at(w: i32, f: f32) -> i32 {
    (w as f32 * f).round() as i32
}

struct Plant {
    w: i32,
    h: i32,
    top: i32,
    bot: i32,
    s1: (i32, i32),
    fbr: (i32, i32),
    dist: [i32; 3],
    cvd: (i32, i32),
    prod: (i32, i32),
    rec: (i32, i32, i32, i32),
}

impl Plant {
    fn new(w: usize, h: usize) -> Self {
        let (w, h) = (w.max(MIN_W as usize) as i32, h.max(MIN_H as usize) as i32);
        let col_w = at(w, 0.07).max(7);
        let d0 = at(w, 0.355);
        let step = (at(w, 0.57) - d0 - col_w) / 2;
        Self {
            w,
            h,
            top: 3,
            bot: h - 11,
            s1: (at(w, 0.01), at(w, 0.135)),
            fbr: (at(w, 0.17), at(w, 0.31)),
            dist: [d0, d0 + step, d0 + 2 * step],
            cvd: (at(w, 0.62), at(w, 0.84)),
            prod: (at(w, 0.875), w - 2),
            rec: (at(w, 0.38), h - 8, at(w, 0.62), h - 4),
        }
    }

    fn col_w(&self) -> i32 {
        at(self.w, 0.07).max(7)
    }

    fn feed_path(&self) -> Path {
        let cx = (self.s1.0 + self.s1.1) / 2;
        Path::new(&[(cx, 7), (cx, self.top + 7), (self.fbr.0, self.top + 7)])
    }

    fn fbr_out(&self) -> Path {
        Path::new(&[(self.fbr.1, self.top + 2), (self.dist[0], self.top + 2)])
    }

    fn pipes(&self) -> [Path; 3] {
        let y = self.top + 2;
        let cw = self.col_w();
        [
            Path::new(&[(self.dist[0] + cw, y), (self.dist[1], y)]),
            Path::new(&[(self.dist[1] + cw, y), (self.dist[2], y)]),
            Path::new(&[
                (self.dist[2] + cw, y),
                (self.feed_x(), y),
                (self.feed_x(), self.bot + 1),
                ((self.cvd.0 + self.cvd.1) / 2, self.bot + 1),
                ((self.cvd.0 + self.cvd.1) / 2, self.bot),
            ]),
        ]
    }

    /// Column where the TCS feed drops down beside the jar to the base plate.
    fn feed_x(&self) -> i32 {
        (self.dist[2] + self.col_w() + self.cvd.0) / 2
    }

    fn offgas(&self) -> Path {
        let x = self.cvd.1 - 3;
        let y = self.rec.1 + 2;
        Path::new(&[(x, self.bot), (x, y), (self.rec.2, y)])
    }

    fn h2_back(&self) -> Path {
        let (x, y) = (self.rec.2 - 4, self.bot + 2);
        Path::new(&[
            (x, self.rec.1),
            (x, y),
            (self.feed_x(), y),
            (self.feed_x(), self.bot + 1),
        ])
    }

    fn hcl_back(&self) -> Path {
        let (x, y) = (self.rec.0 + 14, self.bot + 2);
        let fx = (self.fbr.0 + self.fbr.1) / 2;
        Path::new(&[(x, self.rec.1), (x, y), (fx, y), (fx, self.bot)])
    }

    fn stc_path(&self) -> Path {
        let x = (self.rec.0 + self.rec.2) / 2;
        let y = self.h - 3;
        Path::new(&[(x, self.rec.3), (x, y), (self.prod.0 - 1, y)])
    }

    fn rod_exit(&self) -> Path {
        Path::new(&[(self.cvd.1, 5), (self.prod.0, 5)])
    }
}

/// Rod thickness in cells (1..3): grows through DEPOSIT, stays full after.
fn rod_thick(t: &Time) -> i32 {
    match t.beat {
        DEPOSIT => 1 + (2.0 * ease_in_out(t.local)).round() as i32,
        b if b > DEPOSIT => 3,
        _ => 1,
    }
}

pub struct Poly;

impl Scene for Poly {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BEATS
    }

    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let p = Plant::new(c.width(), c.height());
        draw_feed(c, &p, t);
        draw_fbr(c, &p, t);
        draw_columns(c, &p, t);
        draw_bell(c, &p, t);
        draw_product(c, &p, t);
        draw_stage_labels(c, &p);
    }
}

fn draw_feed(c: &mut Canvas, p: &Plant, t: &Time) {
    let (x0, x1) = p.s1;
    let w = x1 - x0;
    titled_box(c, x0, 0, w, 4, "MG-Si");
    c.text(x0 + 2, 1, "98-99% Si");
    titled_box(c, x0, 5, w, 3, "crush");
    let cx = (x0 + x1) / 2;
    // lumps drop from the hopper into the crusher, fines leave below it
    let drop = Path::new(&[(x1 - 3, 1), (x1 - 3, 6)]);
    let lumps = Particles::new(111, 450, 1100);
    flow(c, &drop, t.ms, lumps, |_| 'O');
    c.put(cx, 4, '▼');
    let feed = p.feed_path();
    feed.draw(c);
    let rate = if t.beat == FBR || t.beat == 0 {
        CHUTE
    } else {
        Particles::new(112, 900, 1800)
    };
    flow(c, &feed, t.ms, rate, |q| {
        if q.rand(1) > 0.5 { '·' } else { '•' }
    });
}

fn draw_fbr(c: &mut Canvas, p: &Plant, t: &Time) {
    let (x0, x1) = p.fbr;
    let w = x1 - x0;
    let h = p.bot - p.top;
    titled_box(c, x0, p.top, w, h + 1, "fluid bed");
    let plate = p.bot - 3;
    c.hline(x0 + 1, plate, w - 1, '═');
    // bubbling grains: cells re-roll every ~200 ms, denser toward the plate
    for y in p.top + 6..plate {
        for x in (x0 + 2..x1 - 1).step_by(2) {
            let k = noise(y as u64 * 977 + x as u64, t.ms / 210);
            let depth = (y - (p.top + 6)) as f32 / (plate - p.top - 6).max(1) as f32;
            if k < 0.12 + 0.55 * depth {
                c.put(x, y, if k < 0.05 { '°' } else { '·' });
            }
        }
    }
    c.text(x0 + 2, p.top + 1, "~300 C");
    // HCl jets under the plate rise as bubbles
    let n = ((w - 2) / 3).max(2);
    for i in 0..n {
        let x = x0 + 2 + i * 3;
        c.text(x, plate + 1, "↑");
    }
    flow(
        c,
        &Path::new(&[((x0 + x1) / 2, p.bot + 1), ((x0 + x1) / 2, p.top + 6)]),
        t.ms,
        DRAFT,
        |_| '°',
    );
    let out = p.fbr_out();
    out.draw(c);
    let stream = if t.beat >= FBR {
        VAPOR
    } else {
        Particles::new(113, 1500, 2400)
    };
    flow(c, &out, t.ms, stream, |q| col::pick(col::FEED, q.rand(1)));
    c.put(x1, p.top + 2, '┤');
}

fn draw_columns(c: &mut Canvas, p: &Plant, t: &Time) {
    let cw = p.col_w();
    // how far the sorting has developed: idle until the distillation beat, complete by its end
    let sep = match t.beat {
        0 | 1 => 0.0,
        DISTILL => ease_in_out(t.local),
        _ => 1.0,
    };
    let roles = [col::LIGHTS, col::STC_CUT, col::POLISH];
    for (i, x) in p.dist.iter().enumerate() {
        titled_box(c, *x, p.top, cw, p.bot - p.top + 1, &(i + 1).to_string());
        let trays = col::tray_rows(p.top, p.bot);
        for y in &trays {
            c.hline(x + 1, *y, cw - 3, '═');
        }
        // vapor hops up a tray, liquid hops down; the species sort as the columns do their jobs
        col::draw_hops(
            c,
            (*x, x + cw - 1),
            &trays,
            roles[i],
            col::FEED,
            sep,
            t.ms,
            120 + 20 * i as u64,
            t.beat >= DISTILL - 1,
        );
    }
    // what travels between the columns: lighter ends first removed, then TCS getting purer
    let between = [
        col::Mix::new(0.0, 0.70, 0.30),
        col::Mix::new(0.02, 0.98, 0.0),
        col::Mix::new(0.0, 1.0, 0.0),
    ];
    for (i, pipe) in p.pipes().iter().enumerate() {
        pipe.draw(c);
        let rate = if t.beat >= DISTILL {
            Particles::new(140 + i as u64, 420, 1500)
        } else {
            Particles::new(140 + i as u64, 1800, 1500)
        };
        let mix = if t.beat >= DISTILL {
            between[i]
        } else {
            col::FEED
        };
        flow(c, pipe, t.ms, rate, |q| col::pick(mix, q.rand(1)));
    }
    // side streams and what the symbols mean
    let [a, b, d] = p.dist;
    c.label(a, p.bot + 1, "H2 ▼");
    c.label(b, p.bot + 1, "SiCl4 ▼");
    c.label(d, p.bot + 1, "BCl3 ▼");
    c.label(d, p.top - 1, "TCS ▶");
    c.label(a, 0, col::LEGEND);
}

fn draw_bell(c: &mut Canvas, p: &Plant, t: &Time) {
    let (x0, x1) = p.cvd;
    let w = x1 - x0;
    let top = p.top + 1;
    // jar: domed top, straight walls, base plate
    c.text(x0 + 1, top, &format!("╭{}╮", "─".repeat((w - 3) as usize)));
    c.vline(x0, top + 1, p.bot - top - 1, '│');
    c.vline(x1, top + 1, p.bot - top - 1, '│');
    c.text(
        x0 - 1,
        p.bot,
        &format!("═{}═", "═".repeat((w + 1) as usize)),
    );
    c.text(x0 + 3, top - 1, "Siemens reactor");
    // cooling water jacket marks on the outside wall
    for y in (top + 2..p.bot - 1).step_by(3) {
        let on = (y as u64 + t.ms / 400).is_multiple_of(2);
        c.put(x0 - 1, y, if on { '~' } else { ' ' });
        c.put(x1 + 1, y, if on { '~' } else { ' ' });
    }
    // two U-shaped rod pairs standing on electrodes
    let thick = rod_thick(t);
    let rod_h = p.bot - top - 4;
    let centers = [x0 + w / 4, x0 + 3 * w / 4];
    for cx in centers {
        let (l, r) = (cx - 4, cx + 4);
        for dx in 0..thick {
            c.vline(l + dx - thick / 2, p.bot - rod_h, rod_h, '▓');
            c.vline(r + dx - thick / 2, p.bot - rod_h, rod_h, '▓');
        }
        c.hline(l - thick / 2, p.bot - rod_h, 9 + thick - 1, '▓');
        c.put(l, p.bot, '┴');
        c.put(r, p.bot, '┴');
        // glow flicker next to the hot surface
        if flicker(t.ms, 140, cx as u64, 3) != 0 {
            c.put(l - thick / 2 - 1, p.bot - rod_h / 2, '·');
            c.put(r + thick / 2 + 1, p.bot - rod_h / 2, '·');
        }
    }
    // feed gas up from the base, off-gas leaving on the right
    let nozzle = (x0 + x1) / 2;
    flow(
        c,
        &Path::new(&[(nozzle, p.bot - 1), (nozzle, top + 3)]),
        t.ms,
        Particles::new(150, 160, 2000),
        |q| if q.rand(1) > 0.4 { '°' } else { '·' },
    );
    let og = p.offgas();
    og.draw(c);
    let stream = if t.beat == RECYCLE || t.beat == DEPOSIT {
        OFFGAS
    } else {
        Particles::new(160, 1400, 2600)
    };
    flow(c, &og, t.ms, stream, |q| {
        if q.rand(1) > 0.5 { '*' } else { '·' }
    });
    c.text(x0 + 1, p.bot - rod_h - 1, "~1100 C");
}

fn draw_product(c: &mut Canvas, p: &Plant, t: &Time) {
    let (x0, x1) = p.prod;
    let w = x1 - x0;
    for (i, name) in ["crush", "etch", "pack"].iter().enumerate() {
        titled_box(c, x0, 3 + 5 * i as i32, w, 4, name);
    }
    for i in 0..2 {
        let y = 7 + 5 * i;
        c.put((x0 + x1) / 2, y, '▼');
    }
    let exit = p.rod_exit();
    exit.draw(c);
    if t.beat == FINISH {
        flow(c, &exit, t.ms, Particles::new(170, 500, 1600), |_| '▓');
        PIECES.each(t.ms, |q| {
            let y = 4 + (q.age * 13.0) as i32;
            c.put_if_blank(x0 + 2 + (q.rand(1) * (w - 4) as f32) as i32, y, '▓');
        });
    }
    // recovery unit, loops and the SiCl4 bin
    let (rx0, ry0, rx1, ry1) = p.rec;
    titled_box(c, rx0, ry0, rx1 - rx0, ry1 - ry0 + 1, "recovery");
    c.text(rx0 + 2, ry0 + 2, "condense: H2 + HCl");
    titled_box(c, x0 - 1, p.h - 6, w + 2, 5, "SiCl4");
    c.text(x0, p.h - 5, "silicones");
    for (path, stream, glyph) in [
        (p.h2_back(), LOOP_H2, '°'),
        (p.hcl_back(), LOOP_HCL, '*'),
        (p.stc_path(), LOOP_STC, '·'),
    ] {
        path.draw(c);
        let s = if t.beat == RECYCLE {
            Particles::new(stream.seed, stream.every_ms / 3, stream.life_ms)
        } else {
            stream
        };
        flow(c, &path, t.ms, s, |_| glyph);
    }
}

fn draw_stage_labels(c: &mut Canvas, p: &Plant) {
    c.label(p.rec.2 - 2, p.bot + 2, "H2 ▶");
    c.label(p.rec.0 - 7, p.bot + 2, "◀ HCl");
    c.label(p.feed_x() + 2, p.bot + 1, "TCS + H2 ▶");
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn player() -> Player {
        Player::new(Box::new(Poly), Instant::now())
    }

    fn at_beat(p: &mut Player, beat: usize, frac: f32) -> Vec<String> {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
    }

    fn has(ls: &[String], s: &str) -> bool {
        ls.iter().any(|l| l.contains(s))
    }

    #[test]
    fn six_beats_four_zooms_all_annotated() {
        let p = player();
        assert_eq!(p.loop_ms(), BEAT_MS * 6);
        assert_eq!(p.zooms().iter().map(|z| z.key).collect::<String>(), "abcd");
        for (i, b) in BEATS.iter().enumerate() {
            assert!(
                !b.what.is_empty()
                    && !b.look.is_empty()
                    && !b.why.is_empty()
                    && !b.facts.is_empty(),
                "beat {i}"
            );
        }
    }

    #[test]
    fn every_stage_is_on_screen() {
        let mut p = player();
        p.fit(120, 36);
        let l = at_beat(&mut p, CRUSH, 0.5);
        for want in [
            "MG-Si",
            "crush",
            "fluid bed",
            "Siemens reactor",
            "recovery",
            "etch",
            "pack",
            "SiCl4",
            "H2 ▶",
            "◀ HCl",
            "TCS ▶",
        ] {
            assert!(has(&l, want), "missing {want}");
        }
    }

    #[test]
    fn rods_grow_during_deposition_and_reset_for_the_next_batch() {
        let mut p = player();
        p.fit(120, 36);
        let rods = |l: &[String]| l.iter().map(|r| r.matches('▓').count()).sum::<usize>();
        let thin = rods(&at_beat(&mut p, DISTILL, 0.5));
        let fat = rods(&at_beat(&mut p, DEPOSIT, 0.99));
        assert!(fat > thin + 10, "{thin} -> {fat}");
        assert_eq!(rods(&at_beat(&mut p, RECYCLE, 0.5)) > thin, true);
    }

    #[test]
    fn scales_without_panicking_and_moves() {
        for (w, h) in [(60, 10), (100, 30), (140, 40), (230, 70)] {
            let mut p = player();
            p.fit(w, h);
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(211) {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                seen.insert(s.lines.join("\n"));
            }
            assert!(seen.len() > 20, "{w}x{h}: {}", seen.len());
        }
    }
}
