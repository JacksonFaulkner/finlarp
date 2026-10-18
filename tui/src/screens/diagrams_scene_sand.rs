// SAND page, overview: the whole silicon plant as one animation. Hoppers
// feed charge into a submerged-arc furnace (drawn as a cross-section with a
// gas cavity under each electrode), off-gas runs to a bag filter, metal is
// tapped to a ladle and finished into product. Zooms (a-d) open a close-up
// of the cavity, crust + stoking, tapping, and the filter.
//
// Sources: Sloman / Elkem (Oxford InFoMM), van de Fliert & Frigaard (ESGI 27),
// Schei, Tuset & Tveit (1998) via both.

use super::diagrams_scene_kit::{Cavity, paint};
use super::diagrams_scene_sand_zoom as zoom;
use crate::ui::anim::shapes::{Path, flow, titled_box};
use crate::ui::anim::{
    Beat, Canvas, Particles, Scene, Time, Zoom, ease_in_out, flicker, lerp, noise,
};

const BEAT_MS: u64 = 5000;
/// Time for the charge to sink one row.
const SINK_MS: u64 = 1100;
pub const MIN_W: u16 = 100;
pub const MIN_H: u16 = 30;

// beat indices
#[cfg(test)]
const FEED: usize = 0;
const CAVITIES: usize = 2;
const CRUST: usize = 3;
const STOKE: usize = 4;
const TAP: usize = 5;
const OFFGAS: usize = 6;
const FINISH: usize = 7;

const BEATS: &[Beat] = &[
    Beat::new(
        "hoppers feed quartzite (SiO2) and carbon (coke, wood chips) onto the burden",
        BEAT_MS,
    )
    .note(
        "Quartzite is the silicon source. Coke and wood chips are the reductant, and the chips keep the pile open for gas. They drop in continuously, so the whole burden slowly sinks.",
        "Packets sliding down both feed pipes and the charge creeping down a row at a time. Gas ° is already drifting up out of the lid.",
    )
    .detail(
        "Everything downstream depends on a loose, evenly mixed burden. Chips and coke open gaps so hot gas can climb through, and lumps rather than dust keep those gaps from clogging.",
        &[
            "Textbook overall reaction: SiO2 + 2C gives Si + 2CO, which absorbs a lot of heat",
            "Power: 11-13 MWh per tonne of silicon, the furnace's biggest cost",
            "The charge sinks continuously as it is consumed and refilled from the top",
        ],
    ),
    Beat::new(
        "in the cooler shaft, rising gas is recaptured: SiO + 2C ─▶ SiC + CO and 2SiO ─▶ SiO2 + Si",
        BEAT_MS,
    )
    .note(
        "Gas made lower down climbs through the gaps in the charge. In the cooler shaft SiO meets carbon and turns into SiC (reaction 4), or condenses into SiO2 + Si (reaction 3). Both keep silicon in the furnace.",
        "° bubbles rising from the cavities toward the lid. The SiC shell ░ around each cavity is where recapture piles up.",
    )
    .detail(
        "Recapturing SiO is what keeps the yield up. SiO that escapes is silicon lost, and what is recovered in the shaft does not have to be made again in the hot zone.",
        &[
            "Reaction 3: 2 SiO gives SiO2 + Si (condensation)",
            "Reaction 4: SiO + 2C gives SiC + CO (recapture)",
            "Shaft temperatures roughly 300-2200 K, hearth 2200-2400 K (Elkem and Oxford ESGI report)",
        ],
    ),
    Beat::new(
        "at each electrode tip an arc holds a gas cavity above 1800 C: SiO2 + C ─▶ SiO + CO, then SiC + SiO ─▶ 2Si + CO",
        BEAT_MS,
    )
    .note(
        "This is where silicon is made. The arc keeps a cavity of SiO and CO gas open under each electrode. SiC + SiO ─▶ 2Si + CO (reaction 1) yields liquid silicon that drains to the pool.",
        "The electrode glow flickering, ● drops falling from each cavity floor, and the ▓ pool rising under them.",
    )
    .detail(
        "The cavity is the engine of the furnace. It has to stay open and hot enough for the two key reactions, which is why electrode position and power are controlled so carefully.",
        &[
            "Reaction 1: SiO + SiC gives 2 Si + CO, which makes the tappable silicon",
            "Reaction 2: SiO2 + Si gives 2 SiO, which makes the SiO gas",
            "Arc zone above 1800 C; silicon melts at 1414 C",
        ],
    ),
    Beat::new(
        "SiO condenses on the cool charge and a crust builds around each cavity, choking charge flow",
        BEAT_MS,
    )
    .note(
        "Over hours a hard crust (SiO2, SiC, Si) grows around each cavity. It thickens, rises, and swells the cavity. Charge can no longer fall into the hot zone, so reactions stall.",
        "The ▒ crust ring growing out from the ░ shell, cavities widening, and the charge pattern stopping its slide.",
    )
    .detail(
        "Crust costs output and, if it gets too thick, can force the furnace to be emptied. Stoking is a trade-off between lost output and disturbing the furnace.",
        &[
            "Crust is mainly SiO2 with silicon and SiC mixed in (ESGI report)",
            "It forms where SiO condenses at low temperature: 2 SiO gives SiO2 + Si",
            "Crust thickens and rises, which increases the gas cavity volume (Sloman and Elkem)",
            "After months or years the crust or hearth layer may need the furnace emptied, with a productivity penalty",
        ],
    ),
    Beat::new(
        "about hourly, a stoking car breaks the crust with a bar so charge can fall again",
        BEAT_MS,
    )
    .note(
        "Operators stoke: a stoking car on the lid pushes a bar down into the crust and breaks it up by hand. Charge drops into the cavity zone and the furnace recovers.",
        "The car sliding along the lid, the bar ┃ jabbing in, sparks * at the break, ▒ shrinking back, and the charge sliding again.",
    )
    .detail(
        "The aim is to restore the downward flow of charge without disturbing the cavities that are actually making silicon.",
        &[
            "Typically about once an hour (Sloman and Elkem)",
            "A bar is pushed down through the charge from a stoking car on the lid",
            "Done by hand: the crust is broken up, not removed",
        ],
    ),
    Beat::new(
        "pool full: the tap hole is lanced, Si runs to the ladle, and a hood pulls fume off the spout",
        BEAT_MS,
    )
    .note(
        "Liquid silicon leaves from the base through the tap hole. Fume is worst during tapping, so a hood over the spout pulls it into the filter line.",
        "The ▓ stream dropping into the ladle while the pool level falls.",
    )
    .detail(
        "A full pool leaves the cavities nowhere to drip, so the furnace is tapped on a regular schedule. Tapping is also the dirtiest moment for fume.",
        &[
            "Hood over the taphole and spout, called a doghouse, pulls fume into the duct (USPTO 11874064)",
            "Fume is 40-80% of fugitive emissions from tapping, refining and casting at one Norwegian plant (Elkem Salten study)",
            "Only 80-90% of the silicon charged is recovered as product",
        ],
    ),
    Beat::new(
        "hot gas leaves the lid; bag filters catch silica fume and clean gas goes up the stack",
        BEAT_MS,
    )
    .note(
        "SiO that escapes the burden burns in air to ~150 nm SiO2 fume. The off-gas duct carries it to bag filters. The fume is caught and sold as microsilica; only clean gas goes up the stack.",
        "· fume and ° gas flowing right along the duct, dust building on the bags, a jet cleaning pulse, and the silica bin filling.",
    )
    .detail(
        "Catching the fume is both a legal need and a revenue stream. Microsilica is sold, and letting it escape means losing silicon and polluting.",
        &[
            "Fume particles are about 150 nm of SiO2",
            "In one DC furnace 19.5% of the charged silicon was lost as fume",
            "Briquetted microsilica plus carbon made up 0-50% of the charge in a 200 kVA test furnace (2024 preprint)",
        ],
    ),
    Beat::new(
        "ladle metal is refined, cast, crushed and sized into the product",
        BEAT_MS,
    )
    .note(
        "Tapped silicon is refined in the ladle, cast into a solid, crushed and screened to the grain size the customer wants. Only 80-90% of the charged silicon ends up as product.",
        "▓ packets moving ladle ─▶ cast ─▶ crush ─▶ Si bin along the bottom row.",
    )
    .detail(
        "Customers buy by grade and grain size, so purity and sizing decide the price per tonne.",
        &[
            "Ladle refining with air and oxygen mainly removes Ca and Al into slag (Springer review)",
            "The product is cast, crushed and screened",
            "80-90% of the charged silicon ends up as product",
        ],
    ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "gas cavity at the electrode tip",
        build: || -> Box<dyn Scene> { Box::new(zoom::Cavity1) },
    },
    Zoom {
        key: 'b',
        label: "crust growth and stoking",
        build: || -> Box<dyn Scene> { Box::new(zoom::CrustStoke) },
    },
    Zoom {
        key: 'c',
        label: "tapping the metal",
        build: || -> Box<dyn Scene> { Box::new(zoom::Tapping) },
    },
    Zoom {
        key: 'd',
        label: "off-gas and the bag filter",
        build: || -> Box<dyn Scene> { Box::new(zoom::BagHouse) },
    },
];

const FEED_C: Particles = Particles::new(21, 520, 1800);
const FEED_Q: Particles = Particles::new(22, 640, 1800);
const GAS: Particles = Particles::new(23, 130, 2200);
const DUCT_GAS: Particles = Particles::new(24, 260, 3000);
const DUCT_GAS_HEAVY: Particles = Particles::new(25, 110, 3000);
const DRIP: Particles = Particles::new(26, 650, 900);
const DIRTY: Particles = Particles::new(27, 230, 1800);
const CLEAN: Particles = Particles::new(28, 420, 1500);
const POUR: Particles = Particles::new(29, 90, 500);
const PRODUCT: Particles = Particles::new(30, 700, 3600);

/// Where everything sits for a canvas size.
struct Plant {
    fx: i32,
    right: i32,
    ft: i32,
    fb: i32,
    pool_top: i32,
    cy: i32,
    elec: [i32; 3],
    tap: i32,
    outlet: i32,
    bag_x: i32,
    chain_x: i32,
    chain_y: i32,
}

impl Plant {
    fn new(w: usize, h: usize) -> Self {
        let (w, h) = (w.max(MIN_W as usize) as i32, h.max(MIN_H as usize) as i32);
        let fx = 2;
        let fw = (w - 44).clamp(54, 96);
        let right = fx + fw;
        let ft = 7;
        let fb = h - 8;
        let body = fb - ft - 1;
        let pool = (body * 22 / 100).max(3);
        let pool_top = fb - pool;
        let e0 = fx + 20;
        let step = ((right - 8) - e0) / 2;
        Self {
            fx,
            right,
            ft,
            fb,
            pool_top,
            cy: pool_top - 4,
            elec: [e0, e0 + step, e0 + 2 * step],
            tap: right - 5,
            outlet: right - 3,
            bag_x: w - 20,
            chain_x: right - 5 - 4,
            chain_y: fb + 2,
        }
    }

    fn cavities(&self) -> [Cavity; 3] {
        self.elec.map(|cx| Cavity {
            cx,
            cy: self.cy,
            rx: 4.0,
            ry: 2.0,
        })
    }

    fn duct(&self) -> Path {
        Path::new(&[(self.outlet, self.ft), (self.outlet, 6), (self.bag_x, 6)])
    }
}

/// Crust thickness (0..2): grows through CRUST, breaks during STOKE.
fn crust_t(t: &Time) -> f32 {
    match t.beat {
        CRUST => lerp(0.25, 2.0, ease_in_out(t.local)),
        STOKE if t.local < 0.5 => 2.0,
        STOKE => lerp(2.0, 0.25, ease_in_out((t.local - 0.5) / 0.4)),
        _ => 0.25,
    }
}

fn pool_level(t: &Time) -> f32 {
    let e = ease_in_out(t.local);
    match t.beat {
        0 | 1 => lerp(0.22, 0.3, e),
        CAVITIES => lerp(0.3, 0.6, e),
        CRUST => lerp(0.6, 0.8, e),
        STOKE => 0.8,
        TAP => lerp(0.8, 0.2, e),
        OFFGAS => lerp(0.2, 0.25, e),
        _ => lerp(0.25, 0.22, e),
    }
}

/// Rows the charge has sunk: it stops while the crust blocks it.
fn sink_rows(t: &Time) -> i64 {
    let frozen = CRUST as u64 * BEAT_MS;
    let ms = match t.beat {
        CRUST => frozen,
        STOKE if t.local < 0.55 => frozen,
        STOKE => frozen + ((t.local - 0.55) * BEAT_MS as f32) as u64,
        b if b > STOKE => frozen + (t.ms - (STOKE as u64 + 1) * BEAT_MS) + BEAT_MS,
        _ => t.ms,
    };
    (ms / SINK_MS) as i64
}

fn blocked(t: &Time) -> bool {
    t.beat == CRUST || (t.beat == STOKE && t.local < 0.55)
}

pub struct Sand;

impl Scene for Sand {
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
        draw_chain(c, &p, t);
        draw_furnace(c, &p, t);
        draw_hoppers(c, &p, t);
        draw_pool(c, &p, t);
        draw_gas(c, &p, t);
        draw_offgas(c, &p, t);
        draw_tap(c, &p, t);
        draw_stoker(c, &p, t);
        draw_labels(c, &p, t);
    }
}

fn draw_hoppers(c: &mut Canvas, p: &Plant, t: &Time) {
    titled_box(c, 2, 0, 10, 4, "coke");
    c.text(3, 1, "+ chips");
    titled_box(c, 13, 0, 11, 4, "quartz");
    c.text(14, 1, "SiO2");
    for (x, stream, glyph) in [(6, FEED_C, ['•', '‡']), (18, FEED_Q, ['o', 'o'])] {
        let pipe = Path::new(&[(x, 4), (x, p.ft - 1)]);
        pipe.draw(c);
        c.put(x, p.ft, '╥');
        if !blocked(t) {
            flow(c, &pipe, t.ms, stream, |q| {
                glyph[(q.rand(1) > 0.5) as usize]
            });
        }
    }
}

fn draw_furnace(c: &mut Canvas, p: &Plant, t: &Time) {
    let (l, r) = (p.fx, p.right);
    // walls
    c.hline(l + 1, p.ft, r - l - 1, '─');
    c.put(l, p.ft, '┌');
    c.put(r, p.ft, '┐');
    c.vline(l, p.ft + 1, p.fb - p.ft - 1, '│');
    c.vline(r, p.ft + 1, p.fb - p.ft - 1, '│');
    c.hline(l + 1, p.fb, r - l - 1, '─');
    c.put(l, p.fb, '└');
    c.put(r, p.fb, '┘');
    // charge and the layered cavities
    paint(
        c,
        &p.cavities(),
        crust_t(t),
        (l + 1, r, p.ft + 1, p.pool_top),
        sink_rows(t),
    );
    // electrodes: through the lid down into each cavity, arc at the tip
    for (i, e) in p.elec.iter().enumerate() {
        c.text(e - 1, 4, &format!("E{}", i + 1));
        c.vline(*e, 5, p.cy - 4, '║');
        c.put(*e, p.ft, '╨');
        let glyph = match flicker(t.ms, 130, i as u64 + 1, 5) {
            0 | 1 => "╲┃╱",
            2 | 3 => "╱┃╲",
            _ => "─●─",
        };
        c.text(e - 1, p.cy, glyph);
    }
}

fn draw_pool(c: &mut Canvas, p: &Plant, t: &Time) {
    let rows = p.fb - p.pool_top;
    let filled = (pool_level(t) * rows as f32).round() as i32;
    for r in 0..filled {
        c.hline(p.fx + 1, p.fb - 1 - r, p.right - p.fx - 1, '▓');
    }
    let surface = p.fb - filled;
    if filled < rows && t.beat != TAP {
        DRIP.each(t.ms, |q| {
            let e = p.elec[(q.id % 3) as usize];
            let y0 = p.cy + 3;
            let y = y0 + (q.age * (surface - y0).max(0) as f32) as i32;
            if y < surface {
                c.put_if_blank(e + (q.id % 2) as i32 * 2 - 1, y, '●');
            }
        });
    }
}

fn draw_gas(c: &mut Canvas, p: &Plant, t: &Time) {
    // cavity gas flickering inside each cavity
    let crust = crust_t(t);
    for (i, cv) in p.cavities().iter().enumerate() {
        let (rx, ry) = cv.radii(crust);
        for k in 0..4u64 {
            let n = noise(i as u64 * 13 + k, t.ms / 170);
            let n2 = noise(i as u64 * 17 + k + 5, t.ms / 170);
            let x = cv.cx + ((n * 2.0 - 1.0) * (rx - 1.0)) as i32;
            let y = cv.cy + ((n2 * 2.0 - 1.0) * (ry - 0.5)) as i32;
            c.put_if_blank(x, y, '°');
        }
    }
    // gas rising from the cavities through the charge to the lid
    let every = if blocked(t) { 400 } else { 130 };
    let stream = Particles::new(GAS.seed, every, GAS.life_ms);
    let span = (p.cy - p.ft - 1).max(1) as f32;
    stream.each(t.ms, |q| {
        let e = p.elec[(q.id % 3) as usize];
        let x = e + ((q.rand(1) - 0.5) * 12.0) as i32 + (q.age * 3.0 * (q.rand(2) - 0.5)) as i32;
        let y = p.cy - 3 - (q.age * span) as i32;
        if y > p.ft && y < p.cy - 2 {
            c.put_if_blank(x, y, '°');
        }
    });
}

fn draw_offgas(c: &mut Canvas, p: &Plant, t: &Time) {
    let duct = p.duct();
    duct.draw(c);
    let stream = if t.beat == OFFGAS {
        DUCT_GAS_HEAVY
    } else {
        DUCT_GAS
    };
    flow(c, &duct, t.ms, stream, |q| {
        if q.rand(1) > 0.5 { '·' } else { '°' }
    });
    // baghouse
    let bx = p.bag_x;
    titled_box(c, bx, 3, 18, 11, "baghouse");
    for i in 0..4 {
        let x = bx + 4 + i * 4;
        c.vline(x, 5, 6, '║');
        // dust cake builds on the bags, a pulse jet knocks it off
        let cycle = t.ms % 4000;
        let cake = (cycle as f32 / 4000.0 * 4.0).floor() as i32;
        for k in 0..cake {
            c.put(x - 1, 5 + 5 - k, '▒');
            c.put(x + 1, 5 + 5 - k, '▒');
        }
        if cycle < 350 {
            c.put(x, 4, '↓');
            c.put(x, 3 + 1, '↓');
        }
    }
    let dirty = Path::new(&[(bx + 1, 6), (bx + 3, 6)]);
    flow(c, &dirty, t.ms, DIRTY, |_| '·');
    let stack = Path::new(&[(bx + 14, 3), (bx + 14, 0)]);
    flow(c, &stack, t.ms, CLEAN, |_| '°');
    c.put(bx + 14, 2, '║');
    c.put(bx + 14, 1, '║');
    c.text(bx + 15, 1, "stack");
    // hopper and silica bin
    c.text(bx + 6, 14, "\\____/");
    let bin = Path::new(&[(bx + 8, 15), (bx + 8, 16)]);
    bin.draw(c);
    titled_box(c, bx + 2, 17, 14, 5, "silica");
    let level = if t.beat == OFFGAS {
        1 + (2.0 * t.local) as i32
    } else if t.beat > OFFGAS {
        3
    } else {
        1
    };
    for r in 0..level {
        c.hline(bx + 3, 20 - r, 12, '▒');
    }
}

fn draw_tap(c: &mut Canvas, p: &Plant, t: &Time) {
    c.put(p.tap, p.fb, '┬');
    c.text(p.tap + 2, p.fb + 1, "tap hole");
    if t.beat == TAP {
        POUR.each(t.ms, |q| {
            let y = p.fb + (q.age * 2.0) as i32;
            c.put(p.tap, y, '▓');
        });
        // hood over the spout, fume pulled up toward the filter line
        c.text(p.tap - 5, p.fb + 1, "hood");
    }
}

fn draw_chain(c: &mut Canvas, p: &Plant, t: &Time) {
    let (x0, y) = (p.chain_x, p.chain_y);
    // ladle -> cast -> crush -> Si bin
    let xs = [x0, x0 + 12, x0 + 24, x0 + 36];
    let widths = [10, 10, 10, 11];
    let flow_path = Path::new(&[(xs[0] + 4, y + 1), (xs[3] + 4, y + 1)]);
    if matches!(t.beat, FINISH) || (t.beat == TAP && t.local > 0.5) {
        flow(c, &flow_path, t.ms, PRODUCT, |_| '▓');
    }
    for (i, name) in ["ladle", "cast", "crush", "Si bin"].iter().enumerate() {
        titled_box(c, xs[i], y, widths[i], 4, name);
        if i < 3 {
            c.text(xs[i] + 10, y + 1, "─▶");
        }
    }
    // the ladle fills while tapping
    let fill = match t.beat {
        TAP => (3.0 * ease_in_out(t.local)).round() as i32,
        OFFGAS => 3,
        _ => 0,
    };
    c.hline(xs[0] + 2, y + 2, fill.min(5), '▓');
    if t.beat == FINISH {
        c.hline(xs[3] + 2, y + 2, (1.0 + 4.0 * t.local) as i32, '▓');
    }
}

fn draw_stoker(c: &mut Canvas, p: &Plant, t: &Time) {
    if t.beat != STOKE {
        return;
    }
    let mid = (p.elec[0] + p.elec[1]) / 2;
    let slide = ease_in_out((t.local / 0.2).min(1.0));
    let x = lerp((p.fx + 4) as f32, mid as f32, slide) as i32;
    c.text(x - 2, p.ft - 2, "▐███▌");
    c.text(x - 2, p.ft - 1, " o o ");
    let cv = p.cavities()[0];
    let (rx, ry) = cv.radii(2.0);
    let target = cv.cy - (ry + 2.0) as i32;
    // jab: down (0.2-0.5), pause while the crust breaks, back up (0.8-1.0)
    let depth = if t.local < 0.2 {
        0.0
    } else if t.local < 0.5 {
        (t.local - 0.2) / 0.3
    } else if t.local < 0.8 {
        1.0
    } else {
        1.0 - (t.local - 0.8) / 0.2
    };
    let bar_x = x;
    let bottom = p.ft + ((target - p.ft) as f32 * depth) as i32;
    if depth > 0.0 {
        c.vline(bar_x, p.ft + 1, bottom - p.ft, '┃');
        if (0.45..0.85).contains(&t.local) {
            let _ = rx;
            for (dx, dy) in [(-2, 0), (2, 0), (0, 1), (-1, -1), (1, -1)] {
                if noise(7, t.ms / 90 + (dx + 5) as u64) > 0.4 {
                    c.put(bar_x + dx, bottom + dy, '*');
                }
            }
        }
    }
}

fn draw_labels(c: &mut Canvas, p: &Plant, _t: &Time) {
    // legend in the free band between the hoppers and the stack
    let x = 28;
    c.text(x, 1, "░ SiC shell   ▒ crust   ° gas   ▓ liquid Si");
    c.text(x, 2, "o quartz   • coke   ‡ wood chips");
    c.text(p.fx + 3, p.fb - 1, "liquid Si");
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn player() -> Player {
        Player::new(Box::new(Sand), Instant::now())
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> Vec<String> {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
    }

    fn has(ls: &[String], s: &str) -> bool {
        ls.iter().any(|l| l.contains(s))
    }

    #[test]
    fn eight_beats_and_four_zooms_all_annotated() {
        let p = player();
        assert_eq!(p.loop_ms(), BEAT_MS * 8);
        assert_eq!(p.zooms().len(), 4);
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
    fn plant_parts_are_all_on_screen() {
        let mut p = player();
        p.fit(110, 36);
        let l = at(&mut p, FEED, 0.5);
        for want in [
            "coke",
            "quartz",
            "E1",
            "E3",
            "baghouse",
            "silica",
            "ladle",
            "cast",
            "crush",
            "Si bin",
            "░ SiC shell",
            "liquid Si",
            "tap hole",
            "stack",
        ] {
            assert!(has(&l, want), "missing {want}");
        }
    }

    #[test]
    fn crust_grows_then_the_stoker_breaks_it() {
        let mut p = player();
        p.fit(120, 38);
        let count = |l: &[String]| l.iter().map(|r| r.matches('▒').count()).sum::<usize>();
        let early = count(&at(&mut p, CAVITIES, 0.5));
        let thick = count(&at(&mut p, CRUST, 0.99));
        let after = count(&at(&mut p, STOKE, 0.95));
        assert!(thick > early + 20, "{early} -> {thick}");
        assert!(after < thick, "{thick} -> {after}");
        assert!(has(&at(&mut p, STOKE, 0.4), "▐███▌"));
        assert!(!has(&at(&mut p, TAP, 0.4), "▐███▌"));
    }

    #[test]
    fn tapping_and_finishing_show_flow() {
        let mut p = player();
        p.fit(110, 36);
        assert!(has(&at(&mut p, TAP, 0.9), "hood"));
        let l = at(&mut p, FINISH, 0.5);
        assert!(has(&l, "─▶"));
    }

    #[test]
    fn scales_without_panicking_and_stays_in_bounds() {
        for (w, h) in [(60, 10), (100, 30), (140, 40), (220, 70)] {
            let mut p = player();
            p.fit(w, h);
            for ms in (0..p.loop_ms()).step_by(233) {
                let s = p.shot_at(ms);
                assert_eq!(s.lines.len(), p.height());
                assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
            }
        }
    }

    #[test]
    fn deterministic_and_moving() {
        let (mut a, mut b) = (player(), player());
        assert_eq!(a.shot_at(7_777).lines, b.shot_at(7_777).lines);
        let distinct: std::collections::HashSet<_> = (0..15)
            .map(|i| a.shot_at(i * 100).lines.join("\n"))
            .collect();
        assert!(distinct.len() >= 10, "{}", distinct.len());
    }
}
