// LOGIC DIE sandbox: the reticle limit, yield, chiplets and HBM shoreline as one model. Arrow keys
// grow or shrink the silicon, `c` splits it into chiplets, `+`/`-` ask for HBM stacks, `d` changes
// the defect density. The left picture is a 300 mm wafer cut into dies with a fixed scatter of
// defects (so a bigger die visibly catches more of them); the right is the package from above with
// the reticle field drawn around each die.
//
// Sources: reticle 26 x 33 mm (ASML), H100 ~814 mm2 and 6 HBM sites, B200 two ~800 mm2 dies with 8
// stacks and a ~10 TB/s die-to-die link (Nvidia, Tom's Hardware); wafer cost and defect density are
// public estimates.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::Rect;
use ratatui::style::Color;
use ratatui::text::Line;

use super::*;
use crate::ui::help::{Key, key};
use crate::ui::theme::Theme;

/// HBM3E-class stack: ~1 TB/s and 24 GB (B200: 8 stacks, ~8 TB/s, 192 GB).
const HBM_TBS: f64 = 1.0;
const HBM_GB: u32 = 24;
/// Die-to-die link per seam (Blackwell NV-HBI).
const D2D_TBS: f64 = 10.0;
/// A leading-edge (N4/N3-class) wafer, public estimate.
const WAFER_COST: f64 = 17_000.0;
/// Defects per cm2 the `d` key steps through; 0.1 puts an 814 mm2 die near the ~45% estimates.
const DENSITIES: [f64; 3] = [0.05, 0.1, 0.2];
const CHIPLETS: [u32; 3] = [1, 2, 4];
const AREA_MIN: f64 = 100.0;
const AREA_MAX: f64 = 3600.0;

struct Preset {
    name: &'static str,
    total: f64,
    dies: u32,
    hbm: u32,
}

const PRESETS: [Preset; 3] = [
    Preset {
        name: "H100-like: one big die",
        total: 814.0,
        dies: 1,
        hbm: 6,
    },
    Preset {
        name: "B200-like: two dies, one GPU",
        total: 1600.0,
        dies: 2,
        hbm: 8,
    },
    Preset {
        name: "four small chiplets",
        total: 1200.0,
        dies: 4,
        hbm: 8,
    },
];

#[derive(Debug, Clone)]
pub struct DieLab {
    pub total: f64,
    pub dies: u32,
    pub hbm: u32,
    density: usize,
    preset: Option<usize>,
}

impl Default for DieLab {
    fn default() -> Self {
        let mut l = Self {
            total: 0.0,
            dies: 1,
            hbm: 0,
            density: 1,
            preset: None,
        };
        l.apply(0);
        l
    }
}

#[derive(Debug, Clone)]
pub struct Stats {
    pub layout: PkgLayout,
    pub die_mm2: f64,
    pub reticle_pct: f64,
    pub fits_reticle: bool,
    pub per_wafer: usize,
    pub hit: usize,
    pub good: usize,
    pub yield_pct: f64,
    pub cost_die: f64,
    pub cost_gpu: f64,
    pub shoreline: f64,
}

impl DieLab {
    fn apply(&mut self, i: usize) {
        let p = &PRESETS[i];
        self.total = p.total;
        self.dies = p.dies;
        self.hbm = p.hbm;
        self.density = 1;
        self.preset = Some(i);
    }

    fn d0(&self) -> f64 {
        DENSITIES[self.density]
    }

    /// Which wafer sites a defect lands in.
    fn hits(&self, l: &PkgLayout) -> Vec<bool> {
        let defects = defects(self.d0());
        wafer_sites(l.w, l.h)
            .iter()
            .map(|&(x0, y0)| {
                defects
                    .iter()
                    .any(|&(x, y)| x >= x0 && x < x0 + l.w && y >= y0 && y < y0 + l.h)
            })
            .collect()
    }

    pub fn stats(&self) -> Stats {
        let layout = PkgLayout::new(self.total, self.dies, self.hbm);
        let die_mm2 = layout.w * layout.h;
        let hits = self.hits(&layout);
        let per_wafer = hits.len();
        let hit = hits.iter().filter(|&&h| h).count();
        let good = per_wafer - hit;
        let yield_pct = if per_wafer == 0 {
            0.0
        } else {
            100.0 * good as f64 / per_wafer as f64
        };
        let cost_die = if good == 0 {
            f64::INFINITY
        } else {
            WAFER_COST / good as f64
        };
        Stats {
            die_mm2,
            reticle_pct: 100.0 * die_mm2 / RETICLE_MM2,
            fits_reticle: die_mm2 <= RETICLE_MM2 + 0.5,
            per_wafer,
            hit,
            good,
            yield_pct,
            cost_die,
            // known-good dies: only tested-good dies are assembled, so a GPU costs n good dies
            cost_gpu: cost_die * self.dies as f64,
            shoreline: 2.0 * self.dies as f64 * layout.w,
            layout,
        }
    }

    fn verdict_for(&self, s: &Stats) -> (String, bool) {
        let n = self.dies;
        let l = &s.layout;
        if !s.fits_reticle {
            return (
                format!(
                    "Too big to print. A scanner exposes at most {RETICLE_W:.0} x {RETICLE_H:.0} mm \
                     ({RETICLE_MM2:.0} mm2) at once, and this die is {:.0} mm2. Press c to split it \
                     into chiplets, or shrink it with the left arrow.",
                    s.die_mm2
                ),
                true,
            );
        }
        if self.hbm > l.hbm_fit {
            return (
                format!(
                    "Not enough edge for memory. HBM has to sit right against the die's edge, and \
                     {:.0} mm of edge only has room for {} stacks, not {}. A longer edge (bigger \
                     die, or more chiplets in a row) adds shoreline.",
                    s.shoreline, l.hbm_fit, self.hbm
                ),
                true,
            );
        }
        if n == 1 && s.yield_pct < 60.0 {
            return (
                format!(
                    "Fits the reticle ({:.0}% full) but yield hurts: one defect anywhere scraps all \
                     {:.0} mm2, so {:.0}% of dies are thrown away. Press c to split the same \
                     silicon into chiplets and compare the cost per GPU.",
                    s.reticle_pct,
                    s.die_mm2,
                    100.0 - s.yield_pct
                ),
                false,
            );
        }
        if n > 1 {
            let one = DieLab {
                dies: 1,
                ..self.clone()
            }
            .stats();
            let versus = if one.fits_reticle {
                format!(
                    "{:.0}% good vs {:.0}% as one die, {} vs {} per GPU",
                    s.yield_pct,
                    one.yield_pct,
                    money(s.cost_gpu),
                    money(one.cost_gpu)
                )
            } else {
                format!(
                    "{:.0}% good; as one die it would not even print",
                    s.yield_pct
                )
            };
            return (
                format!(
                    "{n} dies act as one GPU, joined by {} die-to-die link{} (~{D2D_TBS:.0} TB/s \
                     each). A defect now scraps only one small die: {versus}. The price: the \
                     links and a bigger, harder package.",
                    n - 1,
                    if n == 2 { "" } else { "s" },
                ),
                false,
            );
        }
        (
            format!(
                "A modest die: {:.0}% of the reticle, {:.0}% come out good. Push it bigger with the \
                 right arrow to see yield fall and the reticle fill up.",
                s.reticle_pct, s.yield_pct
            ),
            false,
        )
    }
}

const KEYS: &[Key] = &[
    key("h/l H/L", "die area (H/L in bigger steps)"),
    key("c", "chiplets"),
    key("+/=/k", "more HBM stacks"),
    key("-/j", "fewer HBM stacks"),
    key("d", "defect density"),
    key("p", "next preset"),
    key("r", "reset"),
];

impl Lab for DieLab {
    fn keys(&self) -> &'static [Key] {
        KEYS
    }

    fn menu(&self) -> &'static str {
        "die-size sandbox: reticle, yield, chiplets, HBM"
    }

    fn name(&self) -> &'static str {
        "die-size sandbox"
    }

    fn head(&self) -> (String, &'static str) {
        (
            self.preset
                .map_or("your design".to_string(), |i| PRESETS[i].name.to_string()),
            "Change the die and watch what breaks: the reticle, yield, or memory edge.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        self.verdict_for(&self.stats())
    }

    fn key(&mut self, code: KeyCode) -> bool {
        let step = |l: &mut Self, d: f64| {
            l.total = (l.total + d).clamp(AREA_MIN, AREA_MAX);
            l.preset = None;
        };
        match code {
            KeyCode::Right | KeyCode::Char('l') => step(self, 25.0),
            KeyCode::Left | KeyCode::Char('h') => step(self, -25.0),
            KeyCode::Char('L') => step(self, 200.0),
            KeyCode::Char('H') => step(self, -200.0),
            KeyCode::Char('c') => {
                self.dies = cycle(&CHIPLETS, self.dies);
                self.preset = None;
            }
            KeyCode::Char('+') | KeyCode::Char('=') | KeyCode::Up | KeyCode::Char('k') => {
                self.hbm = (self.hbm + 1).min(16);
                self.preset = None;
            }
            KeyCode::Char('-') | KeyCode::Down | KeyCode::Char('j') => {
                self.hbm = self.hbm.saturating_sub(1);
                self.preset = None;
            }
            KeyCode::Char('d') => self.density = (self.density + 1) % DENSITIES.len(),
            KeyCode::Char('p') => self.apply(self.preset.map_or(0, |i| (i + 1) % PRESETS.len())),
            KeyCode::Char('r') => self.apply(0),
            _ => return false,
        }
        true
    }

    fn body(&self, frame: &mut Frame, r: Rect, t: &Theme) {
        let s = self.stats();
        let l = &s.layout;
        let bg = t.bg.unwrap_or(Color::Reset);
        let (wafer_r, pkg_r, nums_r) = three_way(r, 38);

        let wp = panel(
            frame,
            wafer_r,
            "WAFER",
            "300 mm, cut into dies",
            &[
                (C_DIE, "good die"),
                (C_BAD, "scrapped (has a defect)"),
                (C_DEFECT, "defect"),
            ],
            t,
        );
        let hits = self.hits(l);
        draw_wafer(
            frame.buffer_mut(),
            wp,
            l.w,
            l.h,
            |i| if hits[i] { C_BAD } else { C_DIE },
            &defects(self.d0()),
            bg,
        );

        let mut items = vec![
            (C_DIE, "GPU die"),
            (C_HBM, "HBM stack"),
            (C_TSV, "TSVs"),
            (C_RETICLE, "reticle limit (26x33 mm)"),
        ];
        if self.dies > 1 {
            items.push((C_BRIDGE, "die-to-die bridge"));
        }
        items.push((C_INTERPOSER, "interposer"));
        let pp = panel(
            frame,
            pkg_r,
            "PACKAGE",
            "seen from above, to scale",
            &items,
            t,
        );
        let style = PkgStyle {
            die: if s.fits_reticle { C_DIE } else { C_BAD },
            interposer: C_INTERPOSER,
            reticle: true,
            bridges: true,
            span: None,
        };
        draw_package(frame.buffer_mut(), pp, l, &style, bg);

        let n = self.dies;
        let hbm_line = if self.hbm > l.hbm_fit {
            red(format!(
                "{} wanted, {} fit, {} left off",
                self.hbm,
                l.hbm_fit,
                self.hbm - l.hbm_fit
            ))
        } else {
            v(
                format!(
                    "{} stacks \u{2192} {:.0} TB/s, {} GB",
                    l.hbm,
                    l.hbm as f64 * HBM_TBS,
                    l.hbm * HBM_GB
                ),
                t,
            )
        };
        let mut ret = vec![k("RETICLE", t)];
        ret.extend(bar(
            s.reticle_pct,
            20,
            if s.fits_reticle { C_RETICLE } else { C_BAD },
            t,
        ));
        ret.push(v(format!(" {:.0}% of one exposure", s.reticle_pct), t));
        let mut rows = vec![
            Line::from(vec![
                k("DIE", t),
                v(format!("{:.0} mm2", s.die_mm2), t),
                d(format!(" ({:.1} x {:.1} mm)", l.w, l.h), t),
                v(
                    if n > 1 {
                        format!("  x {n} dies")
                    } else {
                        String::new()
                    },
                    t,
                ),
            ]),
            Line::from(ret),
            Line::from(vec![
                k("WAFER", t),
                v(format!("{} whole dies", s.per_wafer), t),
                d(format!(", {} hit by {} defects/cm2", s.hit, self.d0()), t),
            ]),
            Line::from(vec![
                k("YIELD", t),
                good_or_bad(format!("{:.0}% good", s.yield_pct), s.yield_pct < 50.0, t),
                d(format!("  ({} good per wafer)", s.good), t),
            ]),
            Line::from(vec![
                k("COST", t),
                v(format!("{} per GPU", money(s.cost_gpu)), t),
                d(
                    if n > 1 {
                        format!("  ({n} x {} per good die)", money(s.cost_die))
                    } else {
                        "  (one good die)".to_string()
                    },
                    t,
                ),
            ]),
            Line::from(vec![
                k("SHORELINE", t),
                v(format!("{:.0} mm of edge", s.shoreline), t),
                d(format!(" \u{2192} room for {} HBM", l.hbm_fit), t),
            ]),
            Line::from(vec![k("MEMORY", t), hbm_line]),
        ];
        if n > 1 {
            rows.push(Line::from(vec![
                k("DIE-TO-DIE", t),
                v(
                    format!(
                        "{} link{} x ~{D2D_TBS:.0} TB/s",
                        n - 1,
                        if n == 2 { "" } else { "s" }
                    ),
                    t,
                ),
            ]));
        }
        rows.push(Line::default());
        rows.push(Line::from(d(
            format!(
                "Assumes {} per wafer and a fixed scatter of defects; cost counts silicon only.",
                money(WAFER_COST)
            ),
            t,
        )));
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "die-size sandbox: {} die(s) of {:.0} mm2 ({:.0}% of the reticle), {} per wafer, {:.0}% \
             good at {} defects/cm2, ${:.0} per GPU, HBM {} asked / {} fit",
            self.dies,
            s.die_mm2,
            s.reticle_pct,
            s.per_wafer,
            s.yield_pct,
            self.d0(),
            s.cost_gpu,
            self.hbm,
            s.layout.hbm_fit
        )
    }
}

/// A fixed scatter of defects over the wafer (cm2 density x wafer area of them), the same points
/// every time so growing a die visibly catches more of them; a higher density adds points.
pub fn defects(d0: f64) -> Vec<(f64, f64)> {
    let r = WAFER_D / 2.0;
    let area_cm2 = std::f64::consts::PI * r * r / 100.0;
    let n = (d0 * area_cm2).round() as usize;
    let mut seed: u64 = 0x9e37_79b9_7f4a_7c15;
    let mut next = || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        (seed >> 11) as f64 / (1u64 << 53) as f64
    };
    let mut out = Vec::with_capacity(n);
    while out.len() < n {
        let x = (next() * 2.0 - 1.0) * r;
        let y = (next() * 2.0 - 1.0) * r;
        if x * x + y * y <= r * r {
            out.push((x, y));
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn h100_preset_matches_the_public_numbers() {
        let s = DieLab::default().stats();
        assert!((s.die_mm2 - 814.0).abs() < 1.0);
        assert!(s.fits_reticle);
        assert!((90.0..100.0).contains(&s.reticle_pct));
        assert!((55..=75).contains(&s.per_wafer), "{}", s.per_wafer);
        assert!((30.0..65.0).contains(&s.yield_pct), "{}", s.yield_pct);
        assert_eq!(s.layout.hbm_fit, 6);
    }

    #[test]
    fn b200_preset_fits_eight_stacks_and_the_reticle() {
        let mut l = DieLab::default();
        l.key(KeyCode::Char('p'));
        let s = l.stats();
        assert_eq!(l.dies, 2);
        assert!(s.fits_reticle);
        assert_eq!(s.layout.hbm_fit, 8);
        assert_eq!(s.layout.hbm, 8);
    }

    #[test]
    fn too_big_for_one_die_until_split() {
        let mut l = DieLab::default();
        for _ in 0..10 {
            l.key(KeyCode::Right);
        }
        assert!(!l.stats().fits_reticle);
        assert!(l.verdict().1);
        l.key(KeyCode::Char('c'));
        assert!(l.stats().fits_reticle);
    }

    #[test]
    fn splitting_raises_yield() {
        let mut l = DieLab::default();
        let one = l.stats().yield_pct;
        l.key(KeyCode::Char('c'));
        l.key(KeyCode::Char('c'));
        assert!(l.stats().yield_pct > one);
    }

    #[test]
    fn bigger_dies_catch_more_defects() {
        let mut l = DieLab::default();
        l.total = 200.0;
        let small = l.stats().yield_pct;
        l.total = 800.0;
        assert!(l.stats().yield_pct < small);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Right,
            KeyCode::Char('c'),
            KeyCode::Char('+'),
            KeyCode::Char('d'),
            KeyCode::Char('p'),
            KeyCode::Left,
            KeyCode::Char('-'),
        ];
        renders(&mut DieLab::default(), &keys);
    }
}
