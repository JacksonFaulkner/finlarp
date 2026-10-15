// Zoom-ins for the POLYSILICON overview.
//
//   FluidBed  HCl lifts silicon grains; Si + HCl makes TCS vapor
//   Column    one distillation column: trays, reflux, boiling-point ladder
//   BellJar   Siemens reactor: evacuate, heat rods, deposit, time-lapse growth, open
//   Recycle   off-gas recovery loops, and growth rate vs TCS mole fraction

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
    ),
    Beat::new(
        "about 300 C: Si + HCl ─▶ SiHCl3 (TCS) + H2, at every grain surface",
        BEAT_MS,
    )
    .note(
        "Silicon reacts with HCl to make trichlorosilane, TCS, plus hydrogen. Fraunhofer's practical mix is roughly 3.1 HCl per Si, giving mostly TCS with a little SiCl4 (STC).",
        "* flashes on grain surfaces and : TCS vapor lifting off into the gas above the bed.",
    ),
    Beat::new(
        "impurities react too: boron, phosphorus and metals leave as chlorides",
        BEAT_MS,
    )
    .note(
        "Metallurgical silicon carries boron, phosphorus and metal impurities. Many of them form chlorides in the bed as well (BCl3, PCl5 and others), so they leave with the product vapor. Distillation has to remove them later.",
        "Dark ▒ impurity grains reacting and ‡ chloride vapor leaving with the TCS.",
    ),
    Beat::new(
        "vapor is collected at the top; unreacted solids leave through the bottom",
        BEAT_MS,
    )
    .note(
        "The product vapor, a mix of TCS, SiCl4, H2 and impurity chlorides, goes out the top toward the distillation train. Whatever solid has not reacted is drawn off the bottom of the bed.",
        "The vapor stream ▶ leaving at the top right, and heavy grains dropping out at the bottom right.",
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
    }
}

// ---- b: a distillation column ------------------------------------------------

pub struct Column;

const COL_BEATS: &[Beat] = &[
    Beat::new(
        "the chlorosilane mixture enters the middle of the column",
        BEAT_MS,
    )
    .note(
        "A column is a tall vessel full of trays. The feed from the fluidized bed enters in the middle. Everything in it boils at a different temperature, and that difference is what the column exploits.",
        "The feed pipe at the left entering mid-column, and the boiling-point ladder at the right.",
    ),
    Beat::new(
        "vapor rises and liquid falls; on every tray the light parts go up, the heavy parts go down",
        BEAT_MS,
    )
    .note(
        "A reboiler at the bottom boils liquid into vapor that climbs through holes in each tray. Liquid flows down from tray to tray. Each contact moves the more volatile molecules up and the less volatile ones down, so the mixture gradually separates.",
        "° vapor bubbling up through each tray, · liquid dripping down the weirs, and ≈ heat at the reboiler.",
    ),
    Beat::new(
        "reflux: part of the condensed top product is sent back down to sharpen the split",
        BEAT_MS,
    )
    .note(
        "At the top a condenser turns the vapor into liquid and some of it is returned to the column. A higher reflux ratio gives purer product but costs more energy. In the NASA study phosphorus in TCS falls steeply as reflux goes up and then flattens out.",
        "The reflux line curling back into the top, and the ● marker moving along the impurity curve at the bottom right.",
    ),
    Beat::new(
        "TCS leaves the top, heavier SiCl4 from the bottom; impurities leave at the extremes",
        BEAT_MS,
    )
    .note(
        "In this column TCS (boils at 31.8 C) is taken off at the top and SiCl4 (56.8 C) from the bottom. Other columns in the train remove H2, boron trichloride and phosphorus compounds. Repeating this several times is how the purity gets to parts-per-billion.",
        "The top product ▶ labelled TCS, the bottom product ▼ labelled SiCl4, and the ladder marker on 31.8 C.",
    ),
];

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
        // trays with a down-comer gap that alternates side
        let mut k = 0;
        let mut y = top + 3;
        while y < bot - 1 {
            let gap_left = k % 2 == 0;
            for x in x0 + 1..x1 - 1 {
                let in_gap = if gap_left { x < x0 + 4 } else { x > x1 - 5 };
                c.put(x, y, if in_gap { ' ' } else { '═' });
            }
            // liquid layer on the tray
            if t.beat >= 1 {
                for x in x0 + 4..x1 - 3 {
                    c.put_if_blank(x, y - 1, '~');
                }
            }
            y += 3;
            k += 1;
        }
        let live = t.beat >= 1;
        let every = if live { 120 } else { 1500 };
        Particles::new(211, every, 2400).each(t.ms, |p| {
            let x = x0 + 2 + (p.rand(1) * (x1 - x0 - 4) as f32) as i32;
            let yy = bot - 1 - (p.age * (bot - top - 2) as f32) as i32;
            c.put_if_blank(x, yy, '°');
        });
        Particles::new(212, every + 80, 2600).each(t.ms, |p| {
            let side = if (p.id / 3) % 2 == 0 { x0 + 2 } else { x1 - 2 };
            let yy = top + 1 + (p.age * (bot - top - 2) as f32) as i32;
            c.put_if_blank(side, yy, '·');
        });
        // feed
        let feed_y = (top + bot) / 2;
        let feed = Path::new(&[(1, feed_y), (x0, feed_y)]);
        feed.draw(c);
        flow(c, &feed, t.ms, Particles::new(213, 300, 1500), |_| '·');
        c.label(2, feed_y - 1, "feed from fluid bed");
        // condenser + reflux at the top
        let cx = x1 + 6;
        titled_box(c, cx, top - 1, 14, 4, "condenser");
        let vap = Path::new(&[
            (x1 - 3, top),
            (x1 - 3, top - 2),
            (cx + 3, top - 2),
            (cx + 3, top - 1),
        ]);
        let _ = vap;
        let tp = Path::new(&[(x1, top + 1), (cx, top + 1)]);
        tp.draw(c);
        flow(c, &tp, t.ms, Particles::new(214, 300, 1200), |_| '°');
        let reflux = Path::new(&[(cx + 7, top + 3), (cx + 7, top + 6), (x1, top + 6)]);
        reflux.draw(c);
        if t.beat >= 2 {
            flow(c, &reflux, t.ms, Particles::new(215, 260, 1600), |_| '·');
        }
        c.label(cx + 9, top + 5, "reflux");
        let product = Path::new(&[(cx + 12, top + 3), (cx + 12, top + 6), (w - 3, top + 6)]);
        let _ = product;
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
            flow(c, &bp, t.ms, Particles::new(216, 350, 1100), |_| '▓');
            c.label((x0 + x1) / 2 + 2, h - 2, "SiCl4 ▼");
        }
        // boiling-point ladder
        let lx = w * 60 / 100;
        c.label(lx, 3, "boiling point (C)");
        let rows = [
            ("H2", "-252.8", "lightest: leaves the top"),
            ("DCS (SiH2Cl2)", "8.1", ""),
            ("TCS (SiHCl3)", "31.8", "the product"),
            ("STC (SiCl4)", "56.8", "heavy: leaves the bottom"),
        ];
        for (i, (n, bp, note)) in rows.iter().enumerate() {
            let y = 5 + i as i32 * 2;
            let hot = (t.beat >= 3 && i == 2) || (t.beat == 3 && i == 3);
            let mark = if hot { '▶' } else { ' ' };
            c.label(lx, y, &format!("{mark} {n:<14}{bp:>7}   {note}"));
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
        "The vacuum pump ▐▇▌ on the right running, the pressure reading falling to 1e-5, and the rods dark.",
    ),
    Beat::new(
        "current through the thin start rods heats them until they glow, about 1100 C",
        BEAT_MS,
    )
    .note(
        "Silicon is a poor conductor cold, so the start rods are first brought up to temperature. Then 100-300 V at up to 5000 A, stepped down from the 11 kV supply, runs up one rod, across the bridge and down the other. Pyrometers watch the surface temperature.",
        "Power ↯ along the base cables, the rods turning ▓ and glowing, the temperature readout climbing, and the pyrometer sight line - - -.",
    ),
    Beat::new(
        "TCS + H2 flow in from nozzles in the base: SiHCl3 + H2 ─▶ Si + 3HCl on the hot rods",
        BEAT_MS,
    )
    .note(
        "Trichlorosilane and hydrogen are fed in through nozzles in the base plate. At the hot rod surface they react and silicon deposits as a solid. HCl and unreacted gas leave through off-gas ports in the base.",
        "° gas rising from the center nozzles, · specks settling on the glowing rods, and * HCl streaming out on the right.",
    ),
    Beat::new(
        "time-lapse: the rods fatten from 20 mm to 150-180 mm, at most 1.9 mm an hour",
        BEAT_MS,
    )
    .note(
        "Deposition continues for days. Rods start about 20 mm across and end at 150-180 mm. A solar-grade batch takes about 3.5 days; chip grade grows slower and more uniformly, about 6.7 days. The water-cooled jar keeps its own wall cool.",
        "The rods visibly thickening, the day counter running, and ~ cooling water moving on the jar wall.",
    ),
    Beat::new(
        "hydrogen keeps silicon growing on the rods, not as dust in the gas",
        BEAT_MS,
    )
    .note(
        "Hydrogen's role is to suppress homogeneous nucleation: without it silicon would form as dust in the gas phase instead of depositing on the rods. The TCS-to-hydrogen ratio also sets how fast and how evenly the rods grow.",
        "· particles in the gas drifting to the rods instead of clumping, and the rods smooth and even.",
    ),
    Beat::new(
        "shutdown: power down, cool, lift the jar and cut the rods free",
        BEAT_MS,
    )
    .note(
        "At the target diameter the current is ramped to zero and the feeds changed. When cool the jar is lifted, the finished rods are cut free of their graphite stubs, and a new set of thin rods is loaded for the next batch.",
        "The rods going dark ▒, the jar lifting off, and the pump and power meters at zero.",
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
    ),
    Beat::new(
        "condensing separates gas (H2 + HCl) from liquid chlorosilanes",
        BEAT_MS,
    )
    .note(
        "Fraunhofer describes condensation units that cool the off-gas. Hydrogen and HCl stay as gas while the chlorosilanes condense to liquid. That is the split that makes recycling possible.",
        "Two streams leaving the recovery box: gas ° going up and liquid · going down.",
    ),
    Beat::new(
        "H2 returns to the reactor; HCl returns to the fluidized bed",
        BEAT_MS,
    )
    .note(
        "Hydrogen goes straight back to the CVD inlet feed. HCl goes back to the first step to make more TCS. Nothing valuable is thrown away, which is also what keeps the cost down.",
        "° H2 looping back over the top to the reactor, and * HCl running down to the fluid bed box.",
    ),
    Beat::new(
        "chlorosilanes are redistilled and TCS goes back to the reactor; SiCl4 becomes silicones",
        BEAT_MS,
    )
    .note(
        "The liquid chlorosilanes go through distillation again to recover TCS and DCS for the reactor feed. SiCl4 is a byproduct sold for silicones and silica, or converted back to TCS in a separate reactor.",
        "· flowing through the distillation box, ▶ TCS returning to the reactor, and SiCl4 ▼ to the silicones bin.",
    ),
    Beat::new(
        "growth rate vs TCS fraction: richer feed grows faster but less evenly",
        BEAT_MS,
    )
    .note(
        "Growth rate peaks near 0.4 TCS mole fraction (about 30 microns a minute) and then drops fast. Solar-grade silicon runs faster, about 1.9 mm an hour for 3.5 days. Chip-grade runs slower, about 1 mm an hour for 6.7 days, for a more uniform rod.",
        "The ● marker sliding up the curve to the peak and over it, with the SoG and EG rows highlighted in turn.",
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
                assert!(!b.what.is_empty() && !b.look.is_empty(), "{name} {i} note");
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
        let mut p = mk(Box::new(Column));
        assert!(at(&mut p, 3, 0.5).contains("TCS") && at(&mut p, 3, 0.5).contains("56.8"));
        assert!(at(&mut p, 2, 0.9).contains('●'));
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
