// Zoom-ins for the POLYSILICON overview.
//
//   FluidBed  HCl lifts silicon grains; Si + HCl makes TCS vapor
//   Column    one distillation column: trays, reflux, boiling-point ladder
//   BellJar   Siemens reactor: evacuate, heat rods, deposit, time-lapse growth, open
//   Recycle   off-gas recovery loops, and growth rate vs TCS mole fraction

use super::diagrams_scene_column as col;
use crate::ui::anim::shapes::{Path, fill_ellipse, flow, titled_box};
use crate::ui::anim::{Beat, Canvas, Particles, Scene, Time, ease_in_out, flicker, lerp, noise};

const MIN_W: u16 = 80;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 5200;

fn dims(c: &Canvas) -> (i32, i32) {
    (
        c.width().max(MIN_W as usize) as i32,
        c.height().max(MIN_H as usize) as i32,
    )
}

// ---- a: the fluidized bed -----------------------------------------------------

pub struct FluidBed;

const FB_BEATS: &[Beat] = &[
    Beat::new(
        "HCl is blown up through the plate; the grains lift and flow like a boiling liquid",
        BEAT_MS,
    )
    .note(
        "Ground metallurgical silicon is fed in from the side. HCl gas enters from underneath through a perforated plate, fast enough to lift the grains so they float and tumble. That gives every grain surface contact with the gas.",
        "Bubbles ○ rising through the bed, grains · churning around them, and the HCl arrows ↑ under the plate.",
    )
    .detail(
        "Fluidization makes the reactor practical: it runs continuously and is well mixed, so heat and gas reach every grain.",
        &[
            "HCl enters through the bottom of the reactor (Geng and Yu)",
            "Solid silicon is fed in; unreacted material is removed from the bottom",
            "Vapor is collected from the top",
        ],
    ),
    Beat::new(
        "about 300 C: Si + HCl ─▶ SiHCl3 (TCS) + H2, at every grain surface",
        BEAT_MS,
    )
    .note(
        "Atoms swap partners. Three HCl molecules land on one silicon atom at the grain surface; the silicon keeps three chlorine atoms and picks up one hydrogen, and that small molecule (SiHCl3, called TCS) is a gas, so it floats away. The two leftover hydrogens pair up as H2. Si = silicon, Cl = chlorine, H = hydrogen.",
        "The close-up box on the right: three HCl arrive, the Si atom lifts off as SiHCl3, H2 drifts away, and a fresh Si atom becomes the surface. In the bed, * flashes mark this happening on every grain.",
    )
    .detail(
        "Chlorine atoms replace silicon-silicon bonds, breaking the solid apart into small gas molecules that can leave the grain.",
        &[
            "About 300 C (Fraunhofer)",
            "TCS boils at 31.8 C, so it leaves as a vapor",
            "Balance: Si + 3 HCl gives SiHCl3 + H2, with some SiCl4 forming too",
        ],
    ),
    Beat::new(
        "impurities react too: boron, phosphorus and metals leave as chlorides",
        BEAT_MS,
    )
    .note(
        "Metallurgical silicon carries boron, phosphorus and metal impurities. They react with HCl the same way a silicon atom does, so boron leaves as BCl3 and phosphorus as PCl5 gas, mixed in with the TCS. Distillation has to separate them later, because each boils at a different temperature.",
        "The close-up now shows a boron atom B being pulled off as BCl3 instead of Si as SiHCl3. In the bed, dark ▒ impurity grains react and ‡ chloride vapor leaves with the TCS.",
    )
    .detail(
        "Because the impurities become gases too, the bed cannot remove them. It only moves everything into a form that distillation can separate.",
        &[
            "BCl3 and PCl5 are among the products (Geng and Yu)",
            "Boron and phosphorus are the dopants that matter most for chips",
            "Each has its own boiling point, which is what the columns use",
        ],
    ),
    Beat::new(
        "vapor is collected at the top; unreacted solids leave through the bottom",
        BEAT_MS,
    )
    .note(
        "The product vapor, a mix of TCS, SiCl4, H2 and impurity chlorides, goes out the top toward the distillation train. Whatever solid has not reacted is drawn off the bottom of the bed.",
        "The vapor stream ▶ leaving at the top right, and heavy grains dropping out at the bottom right.",
    )
    .detail(
        "What leaves is a mixture of TCS, SiCl4, hydrogen and impurity chlorides. Nothing here is pure yet.",
        &[
            "Products: TCS, SiCl4, H2, BCl3 and PCl5 (Geng and Yu)",
            "Vapor goes on to the distillation train",
            "Unreacted solid leaves from the bottom",
        ],
    ),
];

impl Scene for FluidBed {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        FB_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (x0, x1) = (w * 24 / 100, w * 62 / 100);
        let (top, bot) = (2, h - 6);
        titled_box(c, x0, top, x1 - x0, bot - top + 1, "fluidized bed reactor");
        let plate = bot - 3;
        let bed_top = top + (plate - top) * 38 / 100;
        c.hline(x0 + 1, plate, x1 - x0 - 1, '═');
        for x in (x0 + 3..x1 - 1).step_by(4) {
            c.put(x, plate, ' ');
        }
        // grains, re-rolled every ~200 ms, denser near the plate
        let active = ease_in_out((t.ms as f32 / 900.0).min(1.0));
        for y in bed_top..plate {
            for x in (x0 + 2..x1 - 1).step_by(2) {
                let k = noise(y as u64 * 977 + x as u64, t.ms / 200);
                let depth = (y - bed_top) as f32 / (plate - bed_top).max(1) as f32;
                if k < (0.25 + 0.5 * depth) * (0.4 + 0.6 * active) {
                    let impurity = t.beat == 2 && noise(5, (y * 131 + x) as u64) < 0.12;
                    c.put(x, y, if impurity { '▒' } else { '·' });
                }
            }
        }
        // bubbles: cleared pockets that rise through the bed
        Particles::new(201, 280, 2200).each(t.ms, |p| {
            let bx = x0 + 3 + (p.rand(1) * (x1 - x0 - 6) as f32) as i32;
            let by = plate - 1 - (p.age * (plate - bed_top) as f32) as i32;
            fill_ellipse(c, bx, by, 2.6, 1.0, ' ');
            c.put(bx, by, '○');
        });
        // reaction flashes and vapor
        if t.beat >= 1 {
            for k in 0..10u64 {
                let x = x0 + 2 + (noise(k, t.ms / 150) * (x1 - x0 - 4) as f32) as i32;
                let y = bed_top + (noise(k + 50, t.ms / 150) * (plate - bed_top) as f32) as i32;
                c.put(x, y, '*');
            }
        }
        let rate = if t.beat >= 1 { 120 } else { 900 };
        Particles::new(202, rate, 2400).each(t.ms, |p| {
            let x = x0 + 2 + (p.rand(1) * (x1 - x0 - 4) as f32) as i32;
            let y = bed_top as f32 - p.age * (bed_top - top - 1) as f32;
            let g = if t.beat == 2 && p.rand(2) > 0.5 {
                '‡'
            } else {
                ':'
            };
            c.put_if_blank(x, y as i32, g);
        });
        // plumbing
        let feed = Path::new(&[(1, bed_top + 3), (x0, bed_top + 3)]);
        feed.draw(c);
        flow(c, &feed, t.ms, Particles::new(203, 350, 1700), |_| '·');
        c.label(2, bed_top + 1, "MG-Si grains");
        let hx = (x0 + x1) / 2;
        let hcl = Path::new(&[(hx, h - 2), (hx, plate + 1)]);
        hcl.draw(c);
        flow(c, &hcl, t.ms, Particles::new(204, 200, 1400), |_| '*');
        c.label(hx + 2, h - 3, "HCl in");
        for x in (x0 + 3..x1 - 1).step_by(4) {
            c.put(x, plate + 1, '↑');
        }
        let out = Path::new(&[(x1, top + 2), (w - 3, top + 2)]);
        out.draw(c);
        flow(c, &out, t.ms, Particles::new(205, 260, 1800), |q| {
            if q.rand(1) > 0.5 { ':' } else { '°' }
        });
        c.label(x1 + 3, top + 3, "TCS + SiCl4 + H2 ▶");
        c.label(x1 + 3, top + 4, "+ impurity chlorides");
        let drain = Path::new(&[(x1, plate - 1), (x1 + 6, plate - 1), (x1 + 6, bot - 1)]);
        drain.draw(c);
        if t.beat == 3 {
            flow(c, &drain, t.ms, Particles::new(206, 450, 1800), |_| '▒');
        }
        c.label(x1 + 8, bot - 2, "unreacted solids");
        c.label(x0 + 2, top + 1, " ~300 C ");
        // close-up of one grain surface, to the right of the vessel
        let (ix, iy) = (x1 + 4, top + 7);
        let (iw, ih) = (w - ix - 2, (plate - iy - 1).min(19));
        if iw >= 36 && ih >= 17 && t.beat >= 1 {
            draw_reaction(c, ix, iy, iw, ih, t, t.beat == 2);
        }
    }
}

/// One surface atom reacting with HCl, drawn as atoms and bonds: three HCl land on it, the atom leaves as a
/// gas molecule (SiHCl3, or BCl3 for an impurity) and the spare hydrogens pair up as H2. Loops every 4.2 s.
fn draw_reaction(c: &mut Canvas, ix: i32, iy: i32, iw: i32, ih: i32, t: &Time, impurity: bool) {
    c.clear_rect(ix, iy, iw, ih);
    titled_box(c, ix, iy, iw, ih, "one grain, up close");
    c.text(ix + 2, iy + 1, "Si silicon  Cl chlorine  H hydrogen");
    let p = (t.ms % 4200) as f32 / 4200.0;
    let ease = |a: f32, b: f32| ease_in_out(((p - a) / (b - a)).clamp(0.0, 1.0));
    let mi = |a: i32, b: i32, e: f32| lerp(a as f32, b as f32, e).round() as i32;

    // the grain: two rows of atoms joined by bonds, with one atom perched on top (the one that will react)
    let n = ((iw - 6) / 6).max(3);
    let ax = |i: i32| ix + 3 + 6 * i;
    let k = n / 2;
    let (y0, y1) = (iy + ih - 8, iy + ih - 6);
    for (y, _) in [(y0, 0), (y1, 1)] {
        for i in 0..n {
            c.text(ax(i), y, "Si");
            if i + 1 < n {
                c.text(ax(i) + 2, y, "────");
            }
        }
    }
    for i in 0..n {
        c.put(ax(i), y0 + 1, '│');
        c.put(ax(i) + 1, y0 + 1, '│');
    }
    let (sx, ya) = (ax(k), y0 - 2);
    let gone = (0.45..0.9).contains(&p);
    if !gone {
        // the perched atom (fades back in at the end of the cycle as the next surface atom)
        c.text(sx, ya, if impurity { "B " } else { "Si" });
        c.put(sx, ya + 1, '│');
    }

    // three HCl approach it: from the left, from the right and from above
    let a = ease(0.0, 0.3);
    if p < 0.45 {
        let (lx, ly) = (mi(sx - 13, sx - 5, a), mi(ya - 3, ya, a));
        c.text(lx, ly, "H─Cl");
        if a >= 1.0 {
            c.put(lx + 4, ly, '─');
        }
        let (rx, ry) = (mi(sx + 10, sx + 2, a), mi(ya - 3, ya, a));
        c.text(rx + 1, ry, "Cl─H");
        if a >= 1.0 {
            c.put(rx, ry, '─');
        }
        let ty = mi((ya - 8).max(iy + 2), ya - 4, a);
        c.put(sx, ty, 'H');
        c.put(sx, ty + 1, '│');
        c.text(sx, ty + 2, "Cl");
        if a >= 1.0 {
            c.put(sx, ya - 1, '│');
        }
        if (0.3..0.45).contains(&p) {
            for (dx, dy) in [(-1, -1), (4, -1), (-2, 1), (5, 1)] {
                c.put(sx + dx, ya + dy, '*');
            }
        }
    }

    // the finished molecule lifts off; the two spare hydrogens leave as H2
    if (0.45..0.95).contains(&p) {
        let lift = ease(0.45, 0.85);
        let y = mi(ya, iy + 4, lift);
        if impurity {
            c.text(sx - 3, y - 1, "Cl─B─Cl");
            c.put(sx, y, '│');
            c.text(sx, y + 1, "Cl");
        } else {
            c.text(sx, y - 1, "Cl");
            c.text(sx - 3, y, "Cl─Si─Cl");
            c.put(sx, y + 1, 'H');
        }
        let hy = mi(ya - 2, iy + 3, ease(0.5, 0.95));
        c.text(mi(sx + 6, ix + iw - 6, ease(0.5, 0.95)), hy, "H─H");
    }

    // the equation, with a marker under the side that is happening now
    let ey = iy + ih - 4;
    let eq = if impurity {
        "B + 3 HCl ─▶ BCl3 + 1.5 H2"
    } else {
        "Si + 3 HCl ─▶ SiHCl3 + H2"
    };
    c.text(ix + 2, ey, eq);
    let (mx, ml) = if p < 0.45 {
        (ix + 2, 10)
    } else {
        (ix + 2 + eq.chars().count() as i32 - 12, 12)
    };
    c.hline(mx, ey + 1, ml, '▔');
    let step = match p {
        p if p < 0.3 => "1 three HCl reach a surface atom",
        p if p < 0.45 => "2 chlorines bond to the atom",
        p if p < 0.8 => {
            if impurity {
                "3 it leaves as BCl3 gas"
            } else {
                "3 SiHCl3 gas lifts off, H pairs up"
            }
        }
        _ => "4 a fresh atom is now the surface",
    };
    c.text(ix + 2, ey + 2, step);
}

// ---- b: a distillation column ------------------------------------------------

pub struct Column;

const COL_BEATS: &[Beat] = &[
    Beat::new(
        "the mixture enters the middle of the column: light °, TCS ● and heavy SiCl4 ■ all mixed",
        BEAT_MS,
    )
    .note(
        "A column is a tall vessel full of trays. The liquid from the fluidized bed is a mixture of three kinds of molecule that boil at different temperatures: light gases such as H2 and BCl3, the product TCS (boils at 31.8 C) and heavy SiCl4 (56.8 C). Right now every tray holds the same mix.",
        "The feed pipe at the left, the ▓ bars at the left of each tray all reading about the same, and a ° ● ■ mixture on every tray.",
    )
    .detail(
        "Everything downstream depends on this split. The three kinds of molecule boil at different temperatures, and the column exploits exactly that.",
        &[
            "Feed: TCS, SiCl4, BCl3, PCl5 and H2 (Geng and Yu)",
            "Boiling points: H2 -252.8, DCS 8.1, TCS 31.8, SiCl4 56.8 C",
            "Columns run at about 30-60 C (Fraunhofer)",
        ],
    ),
    Beat::new(
        "the reboiler boils the bottom; vapor hops up a tray, liquid hops down, and the species start to sort",
        BEAT_MS,
    )
    .note(
        "Heat at the bottom boils liquid and the vapor climbs through holes in each tray. On every tray vapor and liquid meet, and the easier-boiling molecules (° and ●) end up in the vapor while the heavier ones (■) stay in the liquid. Each hop between two trays is a little richer in the light stuff going up and in SiCl4 going down.",
        "The two tracked molecules [●] and [■]: the TCS one climbs a tray at a time with an occasional slip back, the SiCl4 one sinks. The ▓ bars on the left fill toward the top, and ■ crowds the bottom trays while ● and ° crowd the top.",
    )
    .detail(
        "Each tray is one small purification. A column is many of them stacked, which is how a small boiling-point difference becomes a big purity difference.",
        &[
            "Light components exit at the top, heavy ones at the bottom (Geng and Yu)",
            "Vapor climbs through holes in each tray; liquid flows down",
            "Every tray contact moves the volatile species up a little",
        ],
    ),
    Beat::new(
        "reflux: part of the condensed top product is sent back down, so each tray gets purer",
        BEAT_MS,
    )
    .note(
        "At the top a condenser turns the vapor back into liquid and some of it is returned down the column. A higher reflux ratio makes every tray purer but costs more energy. In the NASA study phosphorus in TCS falls steeply as reflux rises, then flattens out.",
        "The reflux line curling back into the top, the top trays' TCS bars reaching nearly full, and the ● marker moving along the impurity curve at the bottom right.",
    )
    .detail(
        "Reflux ratio is the main dial: more reflux gives a purer product but costs more energy per kilogram.",
        &[
            "NASA 1986: phosphorus in TCS 3.2 ppba at reflux 1.2, about 0.05 at 12.5",
            "The curve drops steeply then flattens, so past a point extra reflux buys little",
            "A condenser at the top returns part of the liquid",
        ],
    ),
    Beat::new(
        "TCS leaves the top almost pure; SiCl4 leaves the bottom",
        BEAT_MS,
    )
    .note(
        "In steady state the top trays are nearly all TCS and the bottom trays nearly all SiCl4. TCS is drawn off the top (the next column removes the last boron compounds) and SiCl4 from the bottom is sold on. Repeating this over several columns is how the purity gets to parts per billion.",
        "The top product ▶ labelled TCS, the bottom product ▼ labelled SiCl4, the top bars near 100%, the bottom bars near 0%, and the ladder arrow on 31.8 C.",
    )
    .detail(
        "The cost of purity shows up here: chip grade needs more cycles than solar grade, and every extra cycle is extra energy.",
        &[
            "TCS boils at 31.8 C and SiCl4 at 56.8 C",
            "Chip grade needs 1.66 times more distillation cycles than solar grade (Fraunhofer)",
            "Separate columns remove H2, BCl3 and PCl5 (Geng and Yu)",
        ],
    ),
];

/// Hops one tracked molecule makes (-1 = up a tray, +1 = down), one per `HOP_MS`.
const HOP_MS: u64 = 900;
const TCS_PATH: [i32; 8] = [-1, -1, 1, -1, -1, -1, 1, -1];
const STC_PATH: [i32; 8] = [1, 1, -1, 1, 1, 1, -1, 1];

/// Row of a tracked molecule that starts at tray `start` and follows `path`, repeating every cycle.
fn tracked_y(ms: u64, start: i32, path: &[i32; 8], trays: &[i32]) -> i32 {
    let n = trays.len() as i32;
    let cyc = ms % (HOP_MS * path.len() as u64);
    let (hop, frac) = (
        (cyc / HOP_MS) as usize,
        (cyc % HOP_MS) as f32 / HOP_MS as f32,
    );
    let clamp = |i: i32| i.clamp(0, n - 1);
    let mut idx = clamp(start);
    for d in &path[..hop] {
        idx = clamp(idx + d);
    }
    let next = clamp(idx + path[hop]);
    let (ya, yb) = (trays[idx as usize] - 1, trays[next as usize] - 1);
    lerp(ya as f32, yb as f32, ease_in_out((frac * 1.4).min(1.0))).round() as i32
}

impl Scene for Column {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        COL_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (x0, x1) = (w * 22 / 100, w * 40 / 100);
        let (top, bot) = (3, h - 5);
        titled_box(c, x0, top, x1 - x0, bot - top + 1, "column");
        let xr = x1 - 1; // right wall
        let trays = col::tray_rows(top, bot);
        let n = trays.len();
        // how far the separation has developed by now
        let sep = match t.beat {
            0 => 0.0,
            1 => lerp(0.0, 0.7, ease_in_out(t.local)),
            2 => lerp(0.7, 1.0, ease_in_out(t.local)),
            _ => 1.0,
        };
        // trays with a down-comer gap that alternates side, and a liquid layer on each
        for (k, y) in trays.iter().enumerate() {
            let gap_left = k % 2 == 0;
            for x in x0 + 1..xr {
                let in_gap = if gap_left { x < x0 + 4 } else { x > xr - 4 };
                c.put(x, *y, if in_gap { ' ' } else { '═' });
            }
            if t.beat >= 1 {
                for x in x0 + 4..xr - 3 {
                    c.put_if_blank(x, y - 1, '~');
                }
            }
        }
        col::draw_hops(
            c,
            (x0, xr),
            &trays,
            col::ZOOM,
            col::FEED_ZOOM,
            sep,
            t.ms,
            211,
            t.beat >= 1,
        );
        // the two tracked molecules, drawn on top
        if t.beat >= 1 && n >= 4 {
            let (lx_t, lx_s) = (x0 + (xr - x0) * 35 / 100, x0 + (xr - x0) * 65 / 100);
            let ty = tracked_y(t.ms, n as i32 - 3, &TCS_PATH, &trays);
            let sy = tracked_y(t.ms, 1, &STC_PATH, &trays);
            c.text(lx_t - 1, ty, "[●]");
            c.text(lx_s - 1, sy, "[■]");
        }
        // feed
        let feed_y = (top + bot) / 2;
        let feed = Path::new(&[(1, feed_y), (x0, feed_y)]);
        feed.draw(c);
        flow(c, &feed, t.ms, Particles::new(213, 300, 1500), |p| {
            col::pick(col::FEED_ZOOM, p.rand(1))
        });
        c.label(2, feed_y - 1, "feed from fluid bed");
        // composition of the liquid on every tray (left of the column), plus a temperature strip
        let narrow = x0 < 22;
        for (k, y) in trays.iter().enumerate() {
            if (*y - feed_y).abs() <= 1 {
                continue;
            }
            let m = col::liquid(col::ZOOM, col::FEED_ZOOM, col::tray_f(k, n), sep);
            let pct = (m.tcs * 100.0).round() as i32;
            let text = if narrow {
                format!("{pct:>3}%")
            } else {
                let fill = (m.tcs * 8.0).round() as usize;
                format!("TCS {}{} {pct:>3}%", "▓".repeat(fill), "·".repeat(8 - fill))
            };
            let len = text.chars().count() as i32;
            c.text(x0 - 4 - len, *y, &text);
        }
        for y in top + 1..bot {
            if y == feed_y {
                continue;
            }
            let f = (y - top) as f32 / (bot - top) as f32;
            c.put(
                x0 - 2,
                y,
                if f < 0.34 {
                    '░'
                } else if f < 0.67 {
                    '▒'
                } else {
                    '▓'
                },
            );
        }
        c.label(x0 - 9, top + 1, "cooler");
        c.label(x0 - 9, bot - 1, "hotter");
        // condenser + reflux at the top
        let cx = x1 + 6;
        titled_box(c, cx, top - 1, 14, 4, "condenser");
        let tp = Path::new(&[(x1, top + 1), (cx, top + 1)]);
        tp.draw(c);
        flow(c, &tp, t.ms, Particles::new(214, 300, 1200), |_| '°');
        let reflux = Path::new(&[(cx + 7, top + 3), (cx + 7, top + 6), (x1, top + 6)]);
        reflux.draw(c);
        if t.beat >= 2 {
            flow(c, &reflux, t.ms, Particles::new(215, 260, 1600), |_| '●');
        }
        c.label(cx + 9, top + 5, "reflux");
        c.label(cx + 2, top + 4, if t.beat >= 3 { "TCS ▶" } else { "" });
        // reboiler at the bottom
        let rb = bot - 3;
        titled_box(c, x1 + 6, rb - 1, 14, 4, "reboiler");
        for x in x1 + 8..x1 + 18 {
            c.put(x, rb + 1, '≈');
        }
        Path::new(&[(x1, bot - 2), (x1 + 6, bot - 2)]).draw(c);
        // bottom product
        if t.beat >= 3 {
            let bp = Path::new(&[((x0 + x1) / 2, bot), ((x0 + x1) / 2, h - 2)]);
            bp.draw(c);
            flow(c, &bp, t.ms, Particles::new(216, 350, 1100), |_| '■');
            c.label((x0 + x1) / 2 + 2, h - 2, "SiCl4 ▼");
        }
        // legend, boiling-point ladder and what the tracked molecules are
        let lx = w * 60 / 100;
        c.label(lx, 3, "boiling point (C)");
        c.label(lx, 4, col::LEGEND);
        let rows = [
            ("° H2", "-252.8", "lightest: leaves the top"),
            ("° DCS (SiH2Cl2)", "8.1", ""),
            ("● TCS (SiHCl3)", "31.8", "the product"),
            ("■ STC (SiCl4)", "56.8", "heavy: leaves the bottom"),
        ];
        for (i, (nm, bp, note)) in rows.iter().enumerate() {
            let y = 6 + i as i32 * 2;
            let hot = (t.beat >= 3 && i == 2) || (t.beat == 3 && i == 3);
            let mark = if hot { '▶' } else { ' ' };
            c.label(lx, y, &format!("{mark} {nm:<16}{bp:>7}   {note}"));
        }
        if h >= 34 && t.beat >= 1 {
            c.label(lx, 15, "[●] a TCS molecule climbs, a tray at a time");
            c.label(lx, 16, "[■] a SiCl4 molecule sinks the other way");
        }
        // impurity vs reflux curve (NASA 1986, fig 2B, phosphorus in TCS)
        let (cx0, cy0, cw, ch) = (lx, h - 14, w * 30 / 100, 8);
        c.label(cx0, cy0 - 1, "P in TCS (ppba) vs reflux ratio");
        c.vline(cx0, cy0, ch, '│');
        c.hline(cx0, cy0 + ch, cw, '─');
        c.put(cx0, cy0 + ch, '└');
        let pts = [
            (1.2, 3.2),
            (2.0, 1.15),
            (2.5, 0.6),
            (4.0, 0.18),
            (5.0, 0.13),
            (6.0, 0.1),
            (8.0, 0.06),
            (10.0, 0.05),
            (12.5, 0.04),
        ];
        let curve = |rr: f32| -> f32 {
            for pair in pts.windows(2) {
                let ((x0, y0), (x1, y1)) = (pair[0], pair[1]);
                if rr <= x1 {
                    return lerp(y0, y1, ((rr - x0) / (x1 - x0)).clamp(0.0, 1.0));
                }
            }
            pts[pts.len() - 1].1
        };
        let plot = |rr: f32| -> (i32, i32) {
            let x = cx0 + 1 + ((rr - 1.2) / 11.3 * (cw - 2) as f32) as i32;
            let y = cy0 + ch - 1 - (curve(rr) / 3.3 * (ch - 1) as f32) as i32;
            (x, y)
        };
        for i in 0..(cw - 2) {
            let rr = 1.2 + 11.3 * i as f32 / (cw - 3).max(1) as f32;
            let (x, y) = plot(rr);
            c.put(x, y, '•');
        }
        if t.beat >= 2 {
            let rr = if t.beat == 2 {
                lerp(1.2, 12.5, ease_in_out(t.local))
            } else {
                12.5
            };
            let (x, y) = plot(rr);
            c.put(x, y, '●');
        }
    }
}

// ---- c: the Siemens bell jar ------------------------------------------------

pub struct BellJar;

const BJ_BEATS: &[Beat] = &[
    Beat::new(
        "evacuate to 10^-5 torr and leak-test before anything is heated",
        BEAT_MS,
    )
    .note(
        "The reactor handles toxic, corrosive, flammable gases, so the first step is a pump-down and leak test. Air is removed so it cannot form a flammable mixture with hydrogen, and a leak-tight vessel is confirmed.",
        "The vacuum pump box on the right running, the pressure reading falling to 1e-5, and the rods dark.",
    )
    .detail(
        "Oxygen and moisture would contaminate and oxidise the silicon, and air mixed with hydrogen can burn. The vacuum also proves the vessel is leak tight before toxic gas goes in.",
        &[
            "10^-5 torr is roughly 76 million times below atmospheric pressure (760 torr)",
            "The reactor handles toxic, corrosive, flammable gases (Swetha Priya et al.)",
            "A leak test and checklist come before heating",
        ],
    ),
    Beat::new(
        "current through the thin start rods heats them until they glow, about 1100 C",
        BEAT_MS,
    )
    .note(
        "Silicon is a poor conductor cold, so the start rods are first brought up to temperature. Then 100-300 V at up to 5000 A, stepped down from the 11 kV supply, runs up one rod, across the bridge and down the other. Pyrometers watch the surface temperature.",
        "Power ↯ along the base cables, the rods turning ▓ and glowing, the temperature readout climbing, and the pyrometer sight line - - -.",
    )
    .detail(
        "Silicon conducts better as it heats, so the current rises as the rods warm. That makes temperature control the hard part of this step.",
        &[
            "Resistivity falls as temperature rises (Swetha Priya et al.)",
            "100-300 V at up to 5000 A, stepped down from an 11 kV supply",
            "Too hot: the surface softens and a filament can fail. Too cool: deposition slows",
        ],
    ),
    Beat::new(
        "TCS + H2 flow in from nozzles in the base: SiHCl3 + H2 ─▶ Si + 3HCl on the hot rods",
        BEAT_MS,
    )
    .note(
        "Trichlorosilane and hydrogen are fed in through nozzles in the base plate. At the hot rod surface they react and silicon deposits as a solid. HCl and unreacted gas leave through off-gas ports in the base.",
        "° gas rising from the center nozzles, · specks settling on the glowing rods, and * HCl streaming out on the right.",
    )
    .detail(
        "Temperature and gas ratio decide whether silicon grows smoothly on the rods or forms dust. This is the heart of the process.",
        &[
            "SiHCl3 + H2 gives Si + 3 HCl",
            "Overall with SiCl4 forming: H2 + 3 SiHCl3 gives 2 Si + 5 HCl + SiCl4 (Swetha Priya et al.)",
            "Gas nozzles in the base plate face upward (USPTO patent text)",
        ],
    ),
    Beat::new(
        "time-lapse: the rods fatten from 20 mm to 150-180 mm, at most 1.9 mm an hour",
        BEAT_MS,
    )
    .note(
        "Deposition continues for days. Rods start about 20 mm across and end at 150-180 mm. A solar-grade batch takes about 3.5 days; chip grade grows slower and more uniformly, about 6.7 days. The water-cooled jar keeps its own wall cool.",
        "The rods visibly thickening, the day counter running, and ~ cooling water moving on the jar wall.",
    )
    .detail(
        "A rod grows slowly, so the batch time sets output. Growth rate trades off against how evenly the rod grows.",
        &[
            "20 mm start rods to 150-180 mm, at most 1.9 mm an hour (Fraunhofer)",
            "Solar-grade batch about 3.5 days; chip grade about 6.7 days at about 1 mm an hour",
            "A lower TCS fraction lowers gas density and heat loss, so the rod surface is more uniform",
        ],
    ),
    Beat::new(
        "hydrogen keeps silicon growing on the rods, not as dust in the gas",
        BEAT_MS,
    )
    .note(
        "Hydrogen's role is to suppress homogeneous nucleation: without it silicon would form as dust in the gas phase instead of depositing on the rods. The TCS-to-hydrogen ratio also sets how fast and how evenly the rods grow.",
        "· particles in the gas drifting to the rods instead of clumping, and the rods smooth and even.",
    )
    .detail(
        "Hydrogen's job is to keep the chemistry on the rod surface instead of in the gas, where it would make useless dust.",
        &[
            "Hydrogen prevents homogeneous nucleation, which creates dust (review)",
            "Growth rate peaks near 0.4 TCS mole fraction, about 30 microns a minute (Fraunhofer figure)",
            "Past the peak growth falls quickly",
        ],
    ),
    Beat::new(
        "shutdown: power down, cool, lift the jar and cut the rods free",
        BEAT_MS,
    )
    .note(
        "At the target diameter the current is ramped to zero and the feeds changed. When cool the jar is lifted, the finished rods are cut free of their graphite stubs, and a new set of thin rods is loaded for the next batch.",
        "The rods going dark ▒, the jar lifting off, and the pump and power meters at zero.",
    )
    .detail(
        "Each batch is a discrete unit. Output is limited by how many rods fit in the jar and how long each batch takes.",
        &[
            "Power is ramped to zero and the feeds changed (Swetha Priya et al.)",
            "The reactor is opened only when cool",
            "Solar-grade batch about 3.5 days; chip grade about 6.7 days",
        ],
    ),
];

impl Scene for BellJar {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        BJ_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let (x0, x1) = (w * 22 / 100, w * 62 / 100);
        let base = h - 8;
        let lift = if t.beat == 5 {
            (5.0 * ease_in_out(((t.local - 0.35) / 0.4).clamp(0.0, 1.0))).round() as i32
        } else {
            0
        };
        let top = 7 - lift;
        let jw = x1 - x0;
        // jar: dome, double wall with cooling water, open at the base
        let jb = base - lift;
        c.text(x0 + 1, top, &format!("╭{}╮", "─".repeat((jw - 3) as usize)));
        c.vline(x0, top + 1, jb - top - 1, '│');
        c.vline(x1, top + 1, jb - top - 1, '│');
        c.vline(x0 + 2, top + 2, jb - top - 2, '│');
        c.vline(x1 - 2, top + 2, jb - top - 2, '│');
        for y in top + 2..jb {
            let on = (y as u64 + t.ms / 300).is_multiple_of(3);
            let ch = if on { '~' } else { ' ' };
            c.put(x0 + 1, y, ch);
            c.put(x1 - 1, y, ch);
        }
        c.text(x0 + 4, top - 1, "water-cooled steel bell jar");
        // base plate
        c.hline(x0 - 3, base, jw + 7, '═');
        c.label(x0, base + 1, "base plate");
        // rods: two U-shaped pairs on electrodes
        let hot = ease_in_out(match t.beat {
            0 => 0.0,
            1 => t.local,
            b if b < 5 => 1.0,
            _ => 1.0 - t.local,
        });
        let thick = match t.beat {
            0..=2 => 1,
            3 => 1 + (3.0 * ease_in_out(t.local)).round() as i32,
            _ => 4,
        };
        let rod_top = top + 4;
        let rod_glyph = if hot > 0.2 { '▓' } else { '▒' };
        let centers = [x0 + jw / 4, x0 + 3 * jw / 4];
        for cx in centers {
            let (l, r) = (cx - 5, cx + 5);
            for dx in 0..thick {
                let off = dx - thick / 2;
                c.vline(l + off, rod_top, base - rod_top, rod_glyph);
                c.vline(r + off, rod_top, base - rod_top, rod_glyph);
            }
            c.hline(l - thick / 2, rod_top, 11 + thick - 1, rod_glyph);
            c.put(l, base, '┴');
            c.put(r, base, '┴');
            if hot > 0.5 && flicker(t.ms, 120, cx as u64, 3) != 0 {
                for y in (rod_top + 2..base - 1).step_by(4) {
                    c.put(l - thick / 2 - 1, y, '·');
                    c.put(r + thick / 2 + 1, y, '·');
                }
            }
        }
        // gas: nozzles in the base plate
        let mid = (x0 + x1) / 2;
        for dx in [-3, 0, 3] {
            c.put(mid + dx, base + 1, '↑');
        }
        if t.beat >= 2 && t.beat <= 4 {
            Particles::new(301, 110, 2200).each(t.ms, |p| {
                let x = mid + ((p.rand(1) - 0.5) * 12.0) as i32;
                let y = base - 1 - (p.age * (base - rod_top - 1) as f32) as i32;
                c.put_if_blank(x, y, if p.rand(2) > 0.6 { '°' } else { '·' });
            });
            // silicon settling on the hot surface
            for cx in centers {
                for k in 0..5u64 {
                    let n = noise(k + cx as u64, t.ms / 140);
                    let y = rod_top + 1 + (n * (base - rod_top - 2) as f32) as i32;
                    let side = if k % 2 == 0 {
                        cx - 5 - thick / 2 - 1
                    } else {
                        cx + 5 + thick / 2 + 1
                    };
                    c.put_if_blank(side, y, '·');
                }
            }
        }
        c.label(mid - 6, base + 2, "TCS + H2 from base nozzles");
        // off-gas port on the right
        let og = Path::new(&[(x1 - 4, base), (x1 - 4, base + 3), (x1 + 9, base + 3)]);
        og.draw(c);
        if t.beat >= 2 && t.beat <= 4 {
            flow(c, &og, t.ms, Particles::new(302, 260, 2000), |_| '*');
        }
        c.label(x1 + 11, base + 3, "off-gas ▶");
        // vacuum pump (beat 0) and pressure
        titled_box(c, x1 + 10, base - 6, 13, 4, "vacuum");
        c.text(x1 + 12, base - 5, "▐▇▌");
        if t.beat == 0 {
            let spin = ['|', '/', '─', '\\'][((t.ms / 110) % 4) as usize];
            c.put(x1 + 16, base - 5, spin);
            let vac = Path::new(&[(x1, base - 2), (x1 + 10, base - 2)]);
            vac.draw(c);
            flow(c, &vac, t.ms, Particles::new(303, 200, 1200), |_| '°');
        }
        let torr = match t.beat {
            0 => format!(
                "{:.0e} torr",
                760.0f32 * (1e-5f32 / 760.0).powf(ease_in_out(t.local))
            )
            .replace("e0", "e"),
            5 => "vent".to_string(),
            _ => "10^-5 torr hold".to_string(),
        };
        c.label(x1 + 12, base - 2, &torr);
        // temperature readout and pyrometer sight line
        let temp = (20.0 + 1080.0 * hot).round() as i32;
        c.label(x0 + 4, top + 2, &format!("rod surface {temp} C"));
        c.text(x1 + 4, top + 5, "◉ pyrometer");
        if hot > 0.1 {
            for x in (centers[1] + 7..x1 + 3).step_by(2) {
                c.put(x, top + 5, '-');
            }
        }
        // power: supply box on the left feeding the base electrodes
        titled_box(c, 1, base - 6, 15, 4, "power");
        c.text(3, base - 5, if hot > 0.1 { "5000 A ↯" } else { "off" });
        let cable = Path::new(&[(16, base - 4), (x0 - 3, base - 4), (x0 - 3, base)]);
        cable.draw(c);
        if hot > 0.1 && t.beat < 5 {
            flow(c, &cable, t.ms, Particles::new(304, 220, 1300), |_| '↯');
        }
        // batch clock
        if t.beat >= 2 && t.beat <= 4 {
            let day = match t.beat {
                2 => 0.0,
                3 => 5.0 * t.local,
                _ => 5.0,
            };
            c.label(x0 + 4, top + 1, &format!("day {day:.1} of ~5"));
        }
    }
}

// ---- d: recycle loops + growth-rate curve --------------------------------------

pub struct Recycle;

const RC_BEATS: &[Beat] = &[
    Beat::new(
        "off-gas leaves the reactor: HCl, H2, unreacted chlorosilanes and SiCl4",
        BEAT_MS,
    )
    .note(
        "Silicon deposition releases HCl and leaves some TCS unreacted. Together with hydrogen and the SiCl4 byproduct, the whole stream is collected from the base of the reactor.",
        "The mixed stream ░ leaving the bell jar on the left and heading right into the recovery unit.",
    )
    .detail(
        "The exhaust is not waste. It holds hydrogen and chlorine that can be reused and silicon in the SiCl4 that can be recovered.",
        &[
            "Contains HCl, H2, unreacted chlorosilanes and SiCl4",
            "Collected from the base plate",
            "Overall reaction releases 5 HCl for every 2 Si",
        ],
    ),
    Beat::new(
        "condensing separates gas (H2 + HCl) from liquid chlorosilanes",
        BEAT_MS,
    )
    .note(
        "Fraunhofer describes condensation units that cool the off-gas. Hydrogen and HCl stay as gas while the chlorosilanes condense to liquid. That is the split that makes recycling possible.",
        "Two streams leaving the recovery box: gas ° going up and liquid · going down.",
    )
    .detail(
        "This split makes recycling possible. Gases and liquids go different ways.",
        &[
            "H2 boils at -252.8 C and HCl at -85.1 C, so they stay gas",
            "TCS 31.8 C and SiCl4 56.8 C condense",
            "Vacuum gas recovery and condensation units do the split (Fraunhofer)",
        ],
    ),
    Beat::new(
        "H2 returns to the reactor; HCl returns to the fluidized bed",
        BEAT_MS,
    )
    .note(
        "Hydrogen goes straight back to the CVD inlet feed. HCl goes back to the first step to make more TCS. Nothing valuable is thrown away, which is also what keeps the cost down.",
        "° H2 looping back over the top to the reactor, and * HCl running down to the fluid bed box.",
    )
    .detail(
        "Reusing hydrogen and HCl keeps the plant from buying them again.",
        &[
            "Hydrogen goes back to the CVD inlet feed (Fraunhofer)",
            "HCl goes back to the hydrochlorination step",
            "Nothing valuable is thrown away",
        ],
    ),
    Beat::new(
        "chlorosilanes are redistilled and TCS goes back to the reactor; SiCl4 becomes silicones",
        BEAT_MS,
    )
    .note(
        "The liquid chlorosilanes go through distillation again to recover TCS and DCS for the reactor feed. SiCl4 is a byproduct sold for silicones and silica, or converted back to TCS in a separate reactor.",
        "· flowing through the distillation box, ▶ TCS returning to the reactor, and SiCl4 ▼ to the silicones bin.",
    )
    .detail(
        "Recovering TCS from the liquid and selling or converting SiCl4 is what keeps the loop efficient.",
        &[
            "TCS and DCS recovered for the reactor feed (Fraunhofer)",
            "SiCl4 goes to silicones and silica, or converted back to TCS",
            "Geng and Yu convert SiCl4 to SiO2 for the silicone industry",
        ],
    ),
    Beat::new(
        "growth rate vs TCS fraction: richer feed grows faster but less evenly",
        BEAT_MS,
    )
    .note(
        "Growth rate peaks near 0.4 TCS mole fraction (about 30 microns a minute) and then drops fast. Solar-grade silicon runs faster, about 1.9 mm an hour for 3.5 days. Chip-grade runs slower, about 1 mm an hour for 6.7 days, for a more uniform rod.",
        "The ● marker sliding up the curve to the peak and over it, with the SoG and EG rows highlighted in turn.",
    )
    .detail(
        "The curve explains the batch times: faster growth is cheaper per rod but less uniform, so chip grade runs slower.",
        &[
            "Peak near 0.4 TCS mole fraction, about 30 microns a minute",
            "Solar grade: 3.5 days, 1.9 mm an hour",
            "Chip grade: 6.7 days, about 1 mm an hour",
        ],
    ),
];

impl Scene for Recycle {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }

    fn beats(&self) -> &[Beat] {
        RC_BEATS
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        let (w, h) = dims(c);
        let lw = w * 56 / 100;
        let bw = (lw / 4).max(14);
        let (rx, mx) = (2, lw / 2 - bw / 2);
        titled_box(c, rx, 4, bw, 6, "bell jar");
        titled_box(c, mx, 4, bw, 6, "recovery");
        c.text(mx + 2, 8, "condense");
        let fy = h - 9;
        titled_box(c, mx - bw, fy, bw, 5, "fluid bed");
        titled_box(c, mx + bw, fy, bw, 5, "distill");
        titled_box(c, mx + bw, h - 3, bw, 3, "silicones");
        let live = |lo: usize, hi: usize| t.beat >= lo && t.beat <= hi;
        let rate = |base: u64, on: bool| if on { base } else { base * 5 };
        let hx = mx + bw - 3; // right of the box titles
        type Stream<'a> = (Path, char, bool, &'a str, (i32, i32));
        let paths: [Stream; 6] = [
            (
                Path::new(&[(rx + bw, 7), (mx, 7)]),
                '░',
                live(0, 1),
                "off-gas",
                (rx + bw + 1, 6),
            ),
            (
                Path::new(&[(hx, 4), (hx, 2), (rx + bw - 3, 2), (rx + bw - 3, 4)]),
                '°',
                live(1, 2),
                "H2 back",
                (mx + 2, 1),
            ),
            (
                Path::new(&[
                    (mx + 3, 10),
                    (mx + 3, fy - 1),
                    (mx - 3, fy - 1),
                    (mx - 3, fy),
                ]),
                '*',
                live(1, 2),
                "HCl back",
                (mx - bw + 1, fy - 2),
            ),
            (
                Path::new(&[
                    (hx, 10),
                    (hx, fy - 1),
                    (mx + 2 * bw - 3, fy - 1),
                    (mx + 2 * bw - 3, fy),
                ]),
                '·',
                live(1, 3),
                "liquid",
                (hx + 3, fy - 2),
            ),
            (
                Path::new(&[
                    (mx + bw, fy + 3),
                    (mx + bw - 6, fy + 3),
                    (mx + bw - 6, 12),
                    (rx + bw - 6, 12),
                    (rx + bw - 6, 10),
                ]),
                '▶',
                live(3, 3),
                "TCS back",
                (rx + 1, 13),
            ),
            (
                Path::new(&[(mx + 2 * bw - 3, fy + 5), (mx + 2 * bw - 3, h - 3)]),
                '▼',
                live(3, 3),
                "SiCl4",
                (mx + 2 * bw - 1, fy + 6),
            ),
        ];
        for (path, glyph, on, label, (lx, ly)) in paths {
            path.draw(c);
            flow(
                c,
                &path,
                t.ms,
                Particles::new(401 + glyph as u64, rate(260, on), 2600),
                |_| glyph,
            );
            if !label.is_empty() {
                c.label(lx, ly, label);
            }
        }
        // growth-rate curve (Fraunhofer fig 2): rate vs TCS mole fraction
        let (cx0, cy0) = (lw + 6, 5);
        let (cw, ch) = (w - cx0 - 4, (h - 14).max(8));
        c.label(cx0, cy0 - 2, "growth rate (um/min) vs TCS mole fraction");
        c.vline(cx0, cy0, ch, '│');
        c.hline(cx0, cy0 + ch, cw, '─');
        c.put(cx0, cy0 + ch, '└');
        let pts = [
            (0.1, 10.0),
            (0.2, 19.0),
            (0.3, 26.0),
            (0.4, 30.0),
            (0.45, 28.0),
            (0.5, 3.0),
        ];
        let curve = |f: f32| -> f32 {
            for pair in pts.windows(2) {
                let ((x0, y0), (x1, y1)) = (pair[0], pair[1]);
                if f <= x1 {
                    return lerp(y0, y1, ((f - x0) / (x1 - x0)).clamp(0.0, 1.0));
                }
            }
            pts[pts.len() - 1].1
        };
        let plot = |f: f32| -> (i32, i32) {
            (
                cx0 + 1 + ((f - 0.1) / 0.4 * (cw - 2) as f32) as i32,
                cy0 + ch - 1 - (curve(f) / 31.0 * (ch - 1) as f32) as i32,
            )
        };
        for i in 0..(cw - 2) {
            let f = 0.1 + 0.4 * i as f32 / (cw - 3).max(1) as f32;
            let (x, y) = plot(f);
            c.put(x, y, '•');
        }
        for f in [0.1, 0.2, 0.3, 0.4, 0.5] {
            let (x, _) = plot(f);
            c.put(x, cy0 + ch + 1, '|');
            c.text(x - 1, cy0 + ch + 2, &format!("{f:.1}"));
        }
        let f = if t.beat == 4 {
            lerp(0.1, 0.5, ease_in_out(t.local))
        } else {
            0.1
        };
        let (mx2, my2) = plot(f);
        c.put(mx2, my2, '●');
        let (px, py) = plot(0.4);
        c.label(px + 2, py, "peak: faster but less uniform");
        let (qx, qy) = plot(0.2);
        c.label(qx - 2, qy + 3, "slower, more uniform");
        // SoG vs EG table (Fraunhofer fig 2)
        let ty = cy0 + ch + 4;
        let sog = t.beat == 4 && t.local < 0.5;
        let eg = t.beat == 4 && t.local >= 0.5;
        c.label(
            cx0,
            ty,
            &format!(
                "{} solar grade  3.5 days  1.9 mm/h",
                if sog { '▶' } else { ' ' }
            ),
        );
        c.label(
            cx0,
            ty + 1,
            &format!(
                "{} chip grade   6.7 days  1.0 mm/h",
                if eg { '▶' } else { ' ' }
            ),
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn scenes() -> Vec<(&'static str, fn() -> Box<dyn Scene>)> {
        vec![
            ("fluid", || Box::new(FluidBed)),
            ("column", || Box::new(Column)),
            ("belljar", || Box::new(BellJar)),
            ("recycle", || Box::new(Recycle)),
        ]
    }

    #[test]
    fn every_beat_is_captioned_and_explained() {
        for (name, mk) in scenes() {
            let s = mk();
            assert!(s.beats().len() >= 4, "{name}");
            for (i, b) in s.beats().iter().enumerate() {
                assert!(!b.caption.is_empty(), "{name} {i}");
                assert!(
                    !b.what.is_empty()
                        && !b.look.is_empty()
                        && !b.why.is_empty()
                        && !b.facts.is_empty(),
                    "{name} {i} note"
                );
            }
        }
    }

    #[test]
    fn zooms_scale_and_move() {
        for (name, mk) in scenes() {
            for (w, h) in [(50, 10), (80, 26), (130, 40), (240, 80)] {
                let mut p = Player::new(mk(), Instant::now());
                p.fit(w, h);
                let mut seen = std::collections::HashSet::new();
                for ms in (0..p.loop_ms()).step_by(173) {
                    let s = p.shot_at(ms);
                    assert_eq!(s.lines.len(), p.height());
                    assert!(s.lines.iter().all(|l| l.chars().count() <= p.width()));
                    seen.insert(s.lines.join("\n"));
                }
                assert!(seen.len() > 15, "{name} {w}x{h}: {}", seen.len());
            }
        }
    }

    fn at(p: &mut Player, beat: usize, frac: f32) -> String {
        p.shot_at((beat as f32 * BEAT_MS as f32 + frac * BEAT_MS as f32) as u64)
            .lines
            .join("\n")
    }

    #[test]
    fn each_zoom_shows_its_story() {
        let mk = |s: Box<dyn Scene>| {
            let mut p = Player::new(s, Instant::now());
            p.fit(120, 38);
            p
        };
        let mut p = mk(Box::new(FluidBed));
        assert!(at(&mut p, 1, 0.5).contains('*') && at(&mut p, 0, 0.5).contains('○'));
        assert!(at(&mut p, 3, 0.5).contains("unreacted solids"));
        // the atom-level close-up plays through its four steps in the reaction beats
        let mut step = |ms: u64| p.shot_at(ms).lines.join("\n");
        assert!(
            step(8820).contains("one grain, up close") && step(8820).contains("1 three HCl reach")
        );
        assert!(
            step(9996).contains("H─Cl─Si─Cl─H"),
            "HCl bonded to the surface atom"
        );
        assert!(
            step(6720).contains("Cl─Si─Cl") && step(6720).contains("H─H"),
            "TCS leaves, H pairs up"
        );
        assert!(step(14700).contains("Cl─B─Cl"), "impurity beat shows BCl3");
        assert!(
            !step(1000).contains("one grain"),
            "not shown while the grains are just lifting"
        );
        let mut p = mk(Box::new(Column));
        assert!(at(&mut p, 3, 0.5).contains("TCS") && at(&mut p, 3, 0.5).contains("56.8"));
        assert!(at(&mut p, 2, 0.9).contains('●'));
        // the column sorts: tracked molecules appear, tray bars start even and end separated
        let beat1 = at(&mut p, 1, 0.5);
        assert!(beat1.contains("[●]") && beat1.contains("[■]") && beat1.contains("cooler"));
        let pcts = |s: &str| -> Vec<i32> {
            s.lines()
                .filter_map(|l| l.split("TCS ").nth(1))
                .filter_map(|r| r.split('%').next()?.split_whitespace().last()?.parse().ok())
                .collect()
        };
        let (even, done) = (pcts(&at(&mut p, 0, 0.5)), pcts(&at(&mut p, 3, 0.9)));
        assert!(
            even.windows(2).all(|w| (w[0] - w[1]).abs() <= 1),
            "every tray holds the feed at first: {even:?}"
        );
        assert!(
            done.first() > Some(&85) && done.last() < Some(&15),
            "top ~pure TCS, bottom ~none: {done:?}"
        );
        let mut p = mk(Box::new(BellJar));
        let rods = |s: &str| s.matches('▓').count();
        assert!(rods(&at(&mut p, 3, 0.99)) > rods(&at(&mut p, 2, 0.5)) + 15);
        assert!(at(&mut p, 0, 0.9).contains("torr"));
        assert!(at(&mut p, 1, 0.99).contains("rod surface 1100 C"));
        let mut p = mk(Box::new(Recycle));
        assert!(at(&mut p, 4, 0.99).contains('●') && at(&mut p, 4, 0.8).contains("chip grade"));
        assert!(at(&mut p, 2, 0.5).contains("HCl back"));
    }
}
