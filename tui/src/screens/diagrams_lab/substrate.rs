// SUBSTRATE sandbox: the laminate under the interposer. Arrow keys change the interposer it must
// carry (in reticles), which sets the substrate's size; `+`/`-` the build-up layer count; `g`
// switches an organic core for a glass one. Left: the substrate in cross-section, thickness and
// warp drawn exaggerated; right: wires fanning out layer by layer from 150 um C4 bumps to 1 mm
// BGA balls.
//
// Sources: C4 ~150 um above, BGA ~1 mm below; 12-20 build-up layers of Ajinomoto ABF film
// (estimates); warpage of large thin laminates; glass cores not yet in volume. The size rule, the
// layer rule of thumb, the per-layer yield and the warp constant are this sandbox's assumptions,
// tuned to land near those figures.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Color;
use ratatui::text::Line;

use super::*;
use crate::ui::help::{Key, key};
use crate::ui::theme::Theme;

const C4_PITCH_MM: f64 = 0.15;
const BGA_PITCH_MM: f64 = 1.0;
const LAYER_YIELD: f64 = 0.985;
/// Warp at reflow, um, per (mm of side)^2 per ppm/K of mismatch with the silicon on top.
const WARP_K: f64 = 0.0019;
const WARP_LIMIT_UM: f64 = 150.0;
const CTE_SI: f64 = 2.6;
const CTE_ORGANIC: f64 = 12.0;
const CTE_GLASS: f64 = 5.0;

const C_ABF: Color = Color::Rgb(0x9a, 0x7e, 0x56);
const C_CORE: Color = Color::Rgb(0x6e, 0x5a, 0x3c);
const C_GLASS: Color = Color::Rgb(0x9c, 0xd0, 0xd8);

#[derive(Debug, Clone, Copy, PartialEq)]
enum Core {
    Organic,
    Glass,
}

struct Preset {
    name: &'static str,
    reticles: f64,
    layers: u32,
    core: Core,
}

const PRESETS: [Preset; 3] = [
    Preset {
        name: "H100-class: ~2x reticle interposer",
        reticles: 2.0,
        layers: 16,
        core: Core::Organic,
    },
    Preset {
        name: "B200-class: ~4x reticle interposer",
        reticles: 4.0,
        layers: 20,
        core: Core::Organic,
    },
    Preset {
        name: "2027-class: 9.5x reticle, glass core",
        reticles: 9.5,
        layers: 34,
        core: Core::Glass,
    },
];

#[derive(Debug, Clone)]
pub struct SubstrateLab {
    reticles: f64,
    layers: u32,
    core: Core,
    preset: Option<usize>,
}

impl Default for SubstrateLab {
    fn default() -> Self {
        let mut l = Self {
            reticles: 0.0,
            layers: 0,
            core: Core::Organic,
            preset: None,
        };
        l.apply(0);
        l
    }
}

struct Stats {
    interposer_side: f64,
    side: f64,
    need: u32,
    yield_pct: f64,
    warp: f64,
    c4: f64,
    bga: f64,
}

impl SubstrateLab {
    fn apply(&mut self, i: usize) {
        let p = &PRESETS[i];
        self.reticles = p.reticles;
        self.layers = p.layers;
        self.core = p.core;
        self.preset = Some(i);
    }

    fn stats(&self) -> Stats {
        let a = self.reticles * RETICLE_MM2;
        let interposer_side = a.sqrt();
        let side = 1.3 * interposer_side + 10.0;
        let need = ((10.0 + 2.5 * self.reticles) / 2.0).ceil() as u32 * 2;
        let cte = match self.core {
            Core::Organic => CTE_ORGANIC,
            Core::Glass => CTE_GLASS,
        };
        Stats {
            interposer_side,
            side,
            need,
            yield_pct: 100.0 * LAYER_YIELD.powi(self.layers as i32),
            warp: WARP_K * side * side * (cte - CTE_SI),
            c4: a / (C4_PITCH_MM * C4_PITCH_MM),
            bga: (side / BGA_PITCH_MM).powi(2) * 0.8,
        }
    }
}

const KEYS: &[Key] = &[
    key("h/l", "reticles"),
    key("+/=/k", "more layers"),
    key("-/j", "fewer layers"),
    key("g", "core material"),
    key("p", "next preset"),
    key("r", "reset"),
];

impl Lab for SubstrateLab {
    fn keys(&self) -> &'static [Key] {
        KEYS
    }

    fn menu(&self) -> &'static str {
        "substrate sandbox: size, layers, warpage, glass core"
    }

    fn name(&self) -> &'static str {
        "substrate sandbox"
    }

    fn head(&self) -> (String, &'static str) {
        (
            self.preset.map_or("your substrate".to_string(), |i| {
                PRESETS[i].name.to_string()
            }),
            "A bigger package needs a bigger, deeper laminate: watch it bend and yield fall.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        let s = self.stats();
        if self.layers < s.need {
            return (
                format!(
                    "Can't route it. {} C4 bumps above have to fan out to {} BGA balls below, and \
                     {} layers aren't enough wiring room (~{} needed here). Add layers with +.",
                    thousands(s.c4),
                    thousands(s.bga),
                    self.layers,
                    s.need
                ),
                true,
            );
        }
        if s.warp > WARP_LIMIT_UM {
            return (
                format!(
                    "Warps too much. A {:.0} mm organic laminate bows ~{:.0} um at reflow heat \
                     because it expands ~4x faster than the silicon on it; past ~{WARP_LIMIT_UM:.0} \
                     um the joints tear or never touch. Press g for a glass core, which expands \
                     closer to silicon.",
                    s.side, s.warp
                ),
                true,
            );
        }
        if self.layers > s.need + 4 {
            return (
                format!(
                    "Overbuilt: {} layers where ~{} would route. Every layer is another chance to \
                     scrap the whole laminate, so yield falls to {:.0}%.",
                    self.layers, s.need, s.yield_pct
                ),
                false,
            );
        }
        if self.core == Core::Glass {
            return (
                format!(
                    "A glass core stays flat ({:.0} um warp at {:.0} mm) where organic would bow \
                     ~{:.0} um. The catch: glass cores are only in pilot lines, not volume.",
                    s.warp,
                    s.side,
                    SubstrateLab {
                        core: Core::Organic,
                        ..self.clone()
                    }
                    .stats()
                    .warp
                ),
                false,
            );
        }
        (
            format!(
                "{} layers of ABF film and copper carry {} C4 bumps (150 um) down to {} BGA balls \
                 (1 mm): roughly {:.0} bumps per ball, merged in the power planes. {:.0}% of \
                 laminates come out good.",
                self.layers,
                thousands(s.c4),
                thousands(s.bga),
                s.c4 / s.bga,
                s.yield_pct
            ),
            false,
        )
    }

    fn key(&mut self, code: KeyCode) -> bool {
        match code {
            KeyCode::Right | KeyCode::Char('l') => self.reticles = (self.reticles + 0.5).min(12.0),
            KeyCode::Left | KeyCode::Char('h') => self.reticles = (self.reticles - 0.5).max(1.0),
            KeyCode::Char('+') | KeyCode::Char('=') | KeyCode::Up | KeyCode::Char('k') => {
                self.layers = (self.layers + 2).min(40)
            }
            KeyCode::Char('-') | KeyCode::Down | KeyCode::Char('j') => {
                self.layers = self.layers.saturating_sub(2).max(4)
            }
            KeyCode::Char('g') => {
                self.core = match self.core {
                    Core::Organic => Core::Glass,
                    Core::Glass => Core::Organic,
                }
            }
            KeyCode::Char('p') => {
                self.apply(self.preset.map_or(0, |i| (i + 1) % PRESETS.len()));
                return true;
            }
            KeyCode::Char('r') => {
                self.apply(0);
                return true;
            }
            _ => return false,
        }
        self.preset = None;
        true
    }

    fn body(&self, frame: &mut Frame, r: Rect, t: &Theme) {
        let s = self.stats();
        let bg = t.bg.unwrap_or(Color::Reset);
        let [pics, nums_r] =
            Layout::vertical([Constraint::Percentage(55), Constraint::Min(0)]).areas(r);
        let [side_r, _, fan_r] = Layout::horizontal([
            Constraint::Percentage(58),
            Constraint::Length(2),
            Constraint::Min(0),
        ])
        .areas(pics);
        let core = match self.core {
            Core::Organic => (C_CORE, "organic core"),
            Core::Glass => (C_GLASS, "glass core"),
        };
        let pr = panel(
            frame,
            side_r,
            "CROSS-SECTION",
            "hot (reflow); thickness and bow exaggerated",
            &[
                (C_GREY, "interposer"),
                (C_COPPER, "copper layer"),
                (C_ABF, "ABF film"),
                core,
                (C_SOLDER, "BGA ball"),
            ],
            t,
        );
        self.draw_side(frame, pr, &s, bg);
        let fr = panel(
            frame,
            fan_r,
            "FAN-OUT",
            "150 um above to 1 mm below",
            &[(C_SOLDER, "C4 / BGA"), (C_COPPER, "wire")],
            t,
        );
        self.draw_fan(frame, fr, bg);

        let mut layers = vec![k("LAYERS", t)];
        layers.extend(bar(
            self.layers as f64 / 40.0 * 100.0,
            20,
            if self.layers < s.need {
                C_BAD
            } else {
                C_COPPER
            },
            t,
        ));
        layers.push(good_or_bad(
            format!(" {} (need ~{})", self.layers, s.need),
            self.layers < s.need,
            t,
        ));
        let mut warp = vec![k("WARPAGE", t)];
        warp.extend(bar(
            s.warp / (2.0 * WARP_LIMIT_UM) * 100.0,
            20,
            if s.warp > WARP_LIMIT_UM { C_BAD } else { C_OK },
            t,
        ));
        warp.push(good_or_bad(
            format!(" {:.0} um (limit ~{WARP_LIMIT_UM:.0})", s.warp),
            s.warp > WARP_LIMIT_UM,
            t,
        ));
        let rows = vec![
            Line::from(vec![
                k("CARRIES", t),
                v(
                    format!(
                        "a {:.1}x-reticle interposer ({:.0} mm square)",
                        self.reticles, s.interposer_side
                    ),
                    t,
                ),
            ]),
            Line::from(vec![
                k("SUBSTRATE", t),
                v(format!("{:.0} x {:.0} mm", s.side, s.side), t),
            ]),
            Line::from(layers),
            Line::from(vec![
                k("YIELD", t),
                good_or_bad(
                    format!("{:.0}% of laminates good", s.yield_pct),
                    s.yield_pct < 70.0,
                    t,
                ),
                d(format!("  ({:.1}% per layer)", LAYER_YIELD * 100.0), t),
            ]),
            Line::from(warp),
            Line::from(vec![
                k("JOINTS", t),
                v(
                    format!(
                        "{} C4 on top \u{2192} {} BGA below",
                        thousands(s.c4),
                        thousands(s.bga)
                    ),
                    t,
                ),
            ]),
            Line::from(vec![k("CORE", t), v(core.1, t)]),
            Line::default(),
            Line::from(d(
                "Assumed: substrate side 1.3x the interposer's + 10 mm; ~10 + 2.5 layers per reticle.",
                t,
            )),
        ];
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "substrate sandbox: {:.1}x reticle interposer on {:.0} mm {:?}-core substrate, {} \
             layers (need {}), yield {:.0}%, warp {:.0} um",
            self.reticles, s.side, self.core, self.layers, s.need, s.yield_pct, s.warp
        )
    }
}

impl SubstrateLab {
    /// The laminate in cross-section: interposer on top, build-up layers around the core, BGA
    /// balls below, the whole thing bowed by its warp (exaggerated).
    fn draw_side(&self, frame: &mut Frame, r: Rect, s: &Stats, bg: Color) {
        let (pw, ph) = (r.width as f64, r.height as f64 * 2.0);
        if pw < 10.0 || ph < 8.0 {
            return;
        }
        // x in mm across a 100 mm field (wider for big substrates) so a bigger substrate reads as bigger
        let field = 100.0f64.max(s.side + 10.0);
        let sx = field / pw;
        let half = s.side / 2.0;
        let ihalf = s.interposer_side / 2.0;
        // vertical in pixels: interposer, layers, core, layers, balls
        let per_side = self.layers / 2;
        let layer_px = ((ph * 0.5) / (self.layers as f64 + 4.0)).clamp(0.5, 2.0);
        let core_px = (layer_px * 4.0).max(2.0);
        let stack = per_side as f64 * layer_px * 2.0 + core_px;
        let inter_px = 3.0;
        let ball_px = 3.0;
        let bow_max = ph * 0.22;
        let bow = (s.warp / 300.0).min(1.0) * bow_max;
        let top0 = (ph - (stack + inter_px + ball_px)) / 2.0 - bow / 2.0;
        let core_col = match self.core {
            Core::Organic => C_CORE,
            Core::Glass => C_GLASS,
        };
        paint(frame.buffer_mut(), r, bg, |px, py| {
            let x = (px as f64 + 0.5) * sx - field / 2.0;
            let y = py as f64 + 0.5;
            if x.abs() > half + 1.0 {
                return None;
            }
            // a smile when hot: the edges rise
            let u = (x / half).clamp(-1.0, 1.0);
            let off = -bow * u * u;
            let y = y - off - top0;
            if y < 0.0 {
                return None;
            }
            if y < inter_px {
                return (x.abs() < ihalf).then_some(C_GREY);
            }
            let y = y - inter_px;
            if x.abs() > half {
                return None;
            }
            if y < stack {
                let upper = per_side as f64 * layer_px;
                if y >= upper && y < upper + core_px {
                    return Some(core_col);
                }
                let yy = if y < upper { y } else { y - upper - core_px };
                let i = (yy / layer_px) as u32;
                return Some(if i % 2 == 0 { C_COPPER } else { C_ABF });
            }
            let y = y - stack;
            if y < ball_px {
                let pitch = (6.0 * sx).max(BGA_PITCH_MM);
                let fx = (x + half).rem_euclid(pitch) / pitch - 0.5;
                return (fx.abs() < 0.25).then_some(C_SOLDER);
            }
            None
        });
    }

    /// Wires leaving tightly packed C4 bumps and spreading, a step per layer, to wide BGA balls.
    fn draw_fan(&self, frame: &mut Frame, r: Rect, bg: Color) {
        let (pw, ph) = (r.width as f64, r.height as f64 * 2.0);
        if pw < 10.0 || ph < 8.0 {
            return;
        }
        let n = 7usize;
        let steps = (self.layers / 2).max(1) as f64;
        let top_gap = (pw * 0.06).max(1.5);
        let bot_gap = pw * 0.9 / n as f64;
        let tops: Vec<f64> = (0..n)
            .map(|i| pw / 2.0 + (i as f64 - (n as f64 - 1.0) / 2.0) * top_gap)
            .collect();
        let bots: Vec<f64> = (0..n)
            .map(|i| pw / 2.0 + (i as f64 - (n as f64 - 1.0) / 2.0) * bot_gap)
            .collect();
        let y0 = 2.0;
        let y1 = ph - 3.0;
        let layer_h = (y1 - y0) / steps;
        paint(frame.buffer_mut(), r, bg, |px, py| {
            let (x, y) = (px as f64 + 0.5, py as f64 + 0.5);
            if y < y0 {
                return tops
                    .iter()
                    .any(|&tx| (x - tx).abs() < 0.6)
                    .then_some(C_SOLDER);
            }
            if y > y1 {
                return bots
                    .iter()
                    .any(|&bx| (x - bx).abs() < bot_gap * 0.3)
                    .then_some(C_SOLDER);
            }
            // each layer moves every wire a step outward; vias drop between layers
            let step = ((y - y0) / layer_h).floor().min(steps - 1.0);
            let f = (step + 1.0) / steps;
            for i in 0..n {
                let a = tops[i] + (bots[i] - tops[i]) * (step / steps);
                let b = tops[i] + (bots[i] - tops[i]) * f;
                let in_layer = (y - y0) - step * layer_h;
                let on_run = in_layer < 1.0 && x >= a.min(b) - 0.5 && x <= a.max(b) + 0.5;
                let on_via = (x - b).abs() < 0.6;
                if on_run || on_via {
                    return Some(C_COPPER);
                }
            }
            let layer = ((y - y0) / layer_h) as u32;
            Some(if layer % 2 == 0 { C_ABF } else { C_CORE })
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn presets_land_in_the_12_to_20_layer_range_and_route() {
        for i in 0..2 {
            let mut l = SubstrateLab::default();
            l.apply(i);
            let s = l.stats();
            assert!((12..=20).contains(&s.need), "{}", s.need);
            assert!(!l.verdict().1, "{}", l.verdict().0);
        }
    }

    #[test]
    fn big_organic_substrates_warp_and_glass_fixes_it() {
        let mut l = SubstrateLab::default();
        l.apply(2);
        l.core = Core::Organic;
        assert!(l.stats().warp > WARP_LIMIT_UM);
        l.key(KeyCode::Char('g'));
        assert!(l.stats().warp < WARP_LIMIT_UM);
    }

    #[test]
    fn too_few_layers_fail() {
        let mut l = SubstrateLab::default();
        for _ in 0..10 {
            l.key(KeyCode::Char('-'));
        }
        assert!(l.verdict().1);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Right,
            KeyCode::Char('+'),
            KeyCode::Char('g'),
            KeyCode::Char('p'),
            KeyCode::Left,
            KeyCode::Char('-'),
        ];
        renders(&mut SubstrateLab::default(), &keys);
    }
}
