// MICROBUMP sandbox: bump pitch from C4 (~150 um) through copper-pillar microbumps (~40 um) to
// hybrid bonding (<10 um). Arrow keys change the pitch, `s` switches solder joints / hybrid bonds,
// `+`/`-` the die's current, `[`/`]` the share of joints given to power, `u` underfill. Left: six
// joints in cross-section (the joint's shape: ball, pillar and cap, or fused pads); right: a fixed
// 400 um square from above, so shrinking the pitch visibly packs in more joints.
//
// Sources: C4 ~150 um, microbump ~40 um (20-25 um bumps), hybrid bond <=10 um (TSMC SoIC); solder
// bridges near 10 um; underfill >10x thermal-cycle life for C4 (UCLA, Totta). Electromigration
// limits are order-of-magnitude current densities: solder ~1e4 A/cm2, copper-copper ~1e5 A/cm2.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::Rect;
use ratatui::style::Color;
use ratatui::text::Line;

use super::*;
use crate::ui::help::{Key, key};
use crate::ui::theme::Theme;

const PITCHES: [f64; 20] = [
    150.0, 130.0, 110.0, 90.0, 70.0, 55.0, 45.0, 40.0, 36.0, 30.0, 25.0, 20.0, 15.0, 10.0, 9.0,
    6.0, 4.0, 3.0, 2.0, 1.0,
];
/// Joints under one die this size.
const DIE_MM2: f64 = 800.0;
/// The top view shows this wide a square, in um.
const WINDOW_UM: f64 = 400.0;
const SOLDER_J: f64 = 1.0e4;
const COPPER_J: f64 = 1.0e5;
/// Solder joints stop working below this pitch: neighbouring caps melt together.
const SOLDER_WALL: f64 = 10.0;
const CURRENTS: [f64; 7] = [250.0, 500.0, 1000.0, 1500.0, 2000.0, 3000.0, 4000.0];
const SHARES: [f64; 7] = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6];

const C_UNDERFILL: Color = Color::Rgb(0x5a, 0x4a, 0x3a);
const C_OXIDE: Color = Color::Rgb(0x6a, 0x72, 0x88);

#[derive(Debug, Clone, Copy, PartialEq)]
enum Method {
    Solder,
    Hybrid,
}

struct Preset {
    name: &'static str,
    pitch: f64,
    method: Method,
}

const PRESETS: [Preset; 3] = [
    Preset {
        name: "microbumps under the GPU (40 um)",
        pitch: 40.0,
        method: Method::Solder,
    },
    Preset {
        name: "C4 bumps (150 um)",
        pitch: 150.0,
        method: Method::Solder,
    },
    Preset {
        name: "hybrid bond, SoIC-class (9 um)",
        pitch: 9.0,
        method: Method::Hybrid,
    },
];

#[derive(Debug, Clone)]
pub struct BumpLab {
    pitch: f64,
    method: Method,
    amps: f64,
    share: f64,
    underfill: bool,
    preset: Option<usize>,
}

impl Default for BumpLab {
    fn default() -> Self {
        let mut l = Self {
            pitch: 40.0,
            method: Method::Solder,
            amps: 1000.0,
            share: 0.4,
            underfill: true,
            preset: None,
        };
        l.apply(0);
        l
    }
}

#[derive(Debug, Clone)]
struct Stats {
    kind: &'static str,
    per_mm2: f64,
    joints: f64,
    vs_c4: f64,
    amps_each: f64,
    limit_each: f64,
    bridges: bool,
    /// Gap between the two faces, um (0 for a hybrid bond).
    gap: f64,
}

impl BumpLab {
    fn apply(&mut self, i: usize) {
        let p = &PRESETS[i];
        self.pitch = p.pitch;
        self.method = p.method;
        self.amps = 1000.0;
        self.share = 0.4;
        self.underfill = true;
        self.preset = Some(i);
    }

    /// Pad / bump diameter, um.
    fn pad(&self) -> f64 {
        match self.method {
            Method::Solder => self.pitch * 0.5,
            Method::Hybrid => self.pitch * 0.4,
        }
    }

    fn stats(&self) -> Stats {
        let per_mm2 = (1000.0 / self.pitch).powi(2);
        let joints = per_mm2 * DIE_MM2;
        let power = (joints * self.share).max(1.0);
        let area_cm2 = std::f64::consts::PI * (self.pad() * 1e-4 / 2.0).powi(2);
        let (j, kind) = match self.method {
            Method::Hybrid => (COPPER_J, "hybrid bond: copper pads fused, no solder"),
            Method::Solder if self.pitch >= 100.0 => (SOLDER_J, "C4: a solder ball"),
            Method::Solder => (SOLDER_J, "microbump: copper pillar + solder cap"),
        };
        Stats {
            kind,
            per_mm2,
            joints,
            vs_c4: per_mm2 / (1000.0f64 / 150.0).powi(2),
            amps_each: self.amps / power,
            limit_each: j * area_cm2,
            bridges: self.method == Method::Solder && self.pitch < SOLDER_WALL,
            gap: match self.method {
                Method::Solder => self.pitch * 0.6,
                Method::Hybrid => 0.0,
            },
        }
    }
}

fn amps(a: f64) -> String {
    if a >= 1.0 {
        format!("{a:.2} A")
    } else if a >= 1e-3 {
        format!("{:.1} mA", a * 1e3)
    } else {
        format!("{:.1} uA", a * 1e6)
    }
}

const KEYS: &[Key] = &[
    key("h/l", "bump pitch"),
    key("s", "bonding method"),
    key("+/=/k", "more current"),
    key("-/j", "less current"),
    key("[/]", "share of joints given to power"),
    key("u", "underfill on or off"),
    key("p", "next preset"),
    key("r", "reset"),
];

impl Lab for BumpLab {
    fn keys(&self) -> &'static [Key] {
        KEYS
    }

    fn menu(&self) -> &'static str {
        "bump-pitch sandbox: C4, microbump, hybrid bond"
    }

    fn name(&self) -> &'static str {
        "bump-pitch sandbox"
    }

    fn head(&self) -> (String, &'static str) {
        (
            self.preset
                .map_or("your joint".to_string(), |i| PRESETS[i].name.to_string()),
            "Shrink the pitch: more joints per mm2, until solder can't keep up.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        let s = self.stats();
        if s.bridges {
            return (
                format!(
                    "Solder bridges. At {:.0} um pitch the solder caps are only a few microns \
                     apart and melt into their neighbours during reflow, shorting them. Below \
                     ~10 um the industry switches to hybrid bonding: press s.",
                    self.pitch
                ),
                true,
            );
        }
        if s.amps_each > s.limit_each {
            return (
                format!(
                    "Electromigration. Each power joint carries {} but this joint size handles \
                     about {}; the current slowly pushes the metal apart and the joint fails. Give \
                     more joints to power ([/]), shrink the pitch for more joints, or draw less \
                     current.",
                    amps(s.amps_each),
                    amps(s.limit_each)
                ),
                true,
            );
        }
        if self.method == Method::Solder && !self.underfill {
            return (
                "No underfill. The die and what's under it expand at different rates as they \
                 heat and cool, and the corner joints take all of that strain; epoxy underfill \
                 spreads it over the whole area (>10x the thermal-cycle life for C4). Press u."
                    .to_string(),
                true,
            );
        }
        if self.method == Method::Hybrid && self.pitch > 20.0 {
            return (
                format!(
                    "Hybrid bonding works at {:.0} um, but solder bumps do this pitch cheaper. It \
                     needs atomically flat, spotless surfaces; it pays off below ~10 um where \
                     solder can't go.",
                    self.pitch
                ),
                false,
            );
        }
        (
            format!(
                "{} at {:.0} um: {} joints/mm2, {:.0}x the density of C4. Each power joint \
                 carries {} (limit ~{}). Halving the pitch gives 4x the joints.",
                s.kind,
                self.pitch,
                thousands(s.per_mm2),
                s.vs_c4,
                amps(s.amps_each),
                amps(s.limit_each)
            ),
            false,
        )
    }

    fn key(&mut self, code: KeyCode) -> bool {
        match code {
            KeyCode::Right | KeyCode::Char('l') => self.pitch = step_in(&PITCHES, self.pitch, 1),
            KeyCode::Left | KeyCode::Char('h') => self.pitch = step_in(&PITCHES, self.pitch, -1),
            KeyCode::Char('s') => {
                self.method = match self.method {
                    Method::Solder => Method::Hybrid,
                    Method::Hybrid => Method::Solder,
                }
            }
            KeyCode::Char('+') | KeyCode::Char('=') | KeyCode::Up | KeyCode::Char('k') => {
                self.amps = step_in(&CURRENTS, self.amps, 1)
            }
            KeyCode::Char('-') | KeyCode::Down | KeyCode::Char('j') => {
                self.amps = step_in(&CURRENTS, self.amps, -1)
            }
            KeyCode::Char(']') => self.share = step_in(&SHARES, self.share, 1),
            KeyCode::Char('[') => self.share = step_in(&SHARES, self.share, -1),
            KeyCode::Char('u') => self.underfill = !self.underfill,
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
        let (side_r, top_r, nums_r) = three_way(r, 50);
        let mut items = vec![(C_DIE, "die (above)"), (C_GREY, "interposer (below)")];
        match self.method {
            Method::Solder if self.pitch >= 100.0 => items.push((C_SOLDER, "solder ball")),
            Method::Solder => {
                items.push((C_COPPER, "copper pillar"));
                items.push((C_SOLDER, "solder cap"));
            }
            Method::Hybrid => {
                items.push((C_COPPER, "copper pad"));
                items.push((C_OXIDE, "bonded oxide"));
            }
        }
        if self.method == Method::Solder && self.underfill {
            items.push((C_UNDERFILL, "underfill"));
        }
        if s.bridges {
            items.push((C_BAD, "bridged solder"));
        }
        let pr = panel(
            frame,
            side_r,
            "CROSS-SECTION",
            "six joints, to scale",
            &items,
            t,
        );
        self.draw_side(frame, pr, &s, bg);
        let tr = panel(
            frame,
            top_r,
            "FROM ABOVE",
            "a 400 um square: count the joints",
            &[(C_COPPER, "one joint"), (C_GREY, "between")],
            t,
        );
        self.draw_top(frame, tr, &s, bg);

        let mut density = vec![k("DENSITY", t)];
        density.extend(bar(
            (s.per_mm2.log10() / 1e6f64.log10() * 100.0).max(2.0),
            20,
            C_COPPER,
            t,
        ));
        density.push(v(
            format!(" {} /mm2 ({:.0}x C4)", thousands(s.per_mm2), s.vs_c4),
            t,
        ));
        let ok_amps = s.amps_each <= s.limit_each;
        let rows = vec![
            Line::from(vec![
                k("PITCH", t),
                v(format!("{:.0} um", self.pitch), t),
                d(format!("  ({})", s.kind), t),
            ]),
            Line::from(density),
            Line::from(vec![
                k("UNDER DIE", t),
                v(format!("{} joints", thousands(s.joints)), t),
                d(format!(" under an {DIE_MM2:.0} mm2 die"), t),
            ]),
            Line::from(vec![
                k("GAP", t),
                v(
                    if s.gap > 0.0 {
                        format!("{:.0} um between die and interposer", s.gap)
                    } else {
                        "none: the faces bond directly".to_string()
                    },
                    t,
                ),
            ]),
            Line::from(vec![
                k("POWER", t),
                v(
                    format!(
                        "{:.0} A over {:.0}% of joints",
                        self.amps,
                        self.share * 100.0
                    ),
                    t,
                ),
            ]),
            Line::from(vec![
                k("PER JOINT", t),
                good_or_bad(amps(s.amps_each), !ok_amps, t),
                d(format!("  (limit ~{})", amps(s.limit_each)), t),
            ]),
            Line::from(vec![
                k("SOLDER", t),
                if self.method == Method::Hybrid {
                    v("none", t)
                } else {
                    good_or_bad(
                        if s.bridges {
                            "bridges: below the ~10 um wall".to_string()
                        } else {
                            "ok".to_string()
                        },
                        s.bridges,
                        t,
                    )
                },
            ]),
            Line::from(vec![
                k("UNDERFILL", t),
                if self.method == Method::Hybrid {
                    d("not needed: no gap to fill", t)
                } else {
                    good_or_bad(
                        if self.underfill {
                            "yes: stress spread over the area"
                        } else {
                            "none: corner joints take the strain"
                        },
                        !self.underfill,
                        t,
                    )
                },
            ]),
            Line::default(),
            Line::from(d(
                "Electromigration limits are rough: ~1e4 A/cm2 for solder, ~1e5 for copper.",
                t,
            )),
        ];
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "bump-pitch sandbox: {:.0} um {:?}, {} joints/mm2, {} per power joint (limit {}), \
             underfill {}, bridges {}",
            self.pitch,
            self.method,
            thousands(s.per_mm2),
            amps(s.amps_each),
            amps(s.limit_each),
            self.underfill,
            s.bridges
        )
    }
}

impl BumpLab {
    /// The joint in cross-section, six pitches wide: die on top, interposer below.
    fn draw_side(&self, frame: &mut Frame, r: Rect, s: &Stats, bg: Color) {
        // six joints across, so the joint's shape reads at any pitch
        let p = self.pitch;
        let window = 6.0 * p;
        let slab = 1.2 * p;
        let span_h = 2.0 * slab + p * 0.6 + p * 0.3;
        let (scale, ox, oy) = fit(r, window, span_h);
        let pad = self.pad();
        let gap = s.gap;
        let top_face = -gap / 2.0;
        let bot_face = gap / 2.0;
        let fine = p < scale * 2.5;
        let method = self.method;
        let c4 = p >= 100.0;
        let underfill = self.underfill;
        let bridges = s.bridges;
        paint(frame.buffer_mut(), r, bg, |px, py| {
            let x = (px as f64 + 0.5) * scale - ox;
            let y = (py as f64 + 0.5) * scale - oy;
            if x.abs() > window / 2.0 {
                return None;
            }
            // position within one pitch, centred on the joint
            let fx = (x + window / 2.0).rem_euclid(p) - p / 2.0;
            let in_pad = fx.abs() < pad / 2.0;
            if method == Method::Hybrid {
                let pad_depth = p * 0.25;
                if y < -slab || y > slab {
                    return None;
                }
                if y.abs() < pad_depth {
                    if fine {
                        return Some(C_COPPER);
                    }
                    return Some(if in_pad { C_COPPER } else { C_OXIDE });
                }
                return Some(if y < 0.0 { C_DIE } else { C_GREY });
            }
            if y < top_face - slab || y > bot_face + slab {
                return None;
            }
            if y < top_face {
                return Some(C_DIE);
            }
            if y >= bot_face {
                return Some(C_GREY);
            }
            if bridges {
                return Some(if y > bot_face - gap * 0.5 {
                    C_BAD
                } else {
                    C_COPPER
                });
            }
            let fill = if underfill { Some(C_UNDERFILL) } else { None };
            if c4 {
                // a ball: circle of the gap's height, a little wider than tall
                let cy = 0.0;
                let rx = pad * 0.6;
                let ry = gap / 2.0;
                let inside = (fx / rx).powi(2) + ((y - cy) / ry).powi(2) <= 1.0;
                return if inside { Some(C_SOLDER) } else { fill };
            }
            // copper pillar from the die, solder cap at the bottom
            if in_pad || fine {
                let cap_top = top_face + gap * 0.62;
                return Some(if y < cap_top { C_COPPER } else { C_SOLDER });
            }
            fill
        });
    }

    /// The window from above: one dot per joint, a fill when they are finer than a pixel.
    fn draw_top(&self, frame: &mut Frame, r: Rect, _s: &Stats, bg: Color) {
        let (area, side) = square(r);
        if side < 6 {
            return;
        }
        let scale = WINDOW_UM / side as f64;
        let p = self.pitch;
        let pad = self.pad();
        let fine = p < scale * 2.5;
        paint(frame.buffer_mut(), area, bg, |px, py| {
            let x = (px as f64 + 0.5) * scale;
            let y = (py as f64 + 0.5) * scale;
            if fine {
                return Some(C_COPPER);
            }
            let fx = x.rem_euclid(p) - p / 2.0;
            let fy = y.rem_euclid(p) - p / 2.0;
            if fx * fx + fy * fy <= (pad / 2.0).powi(2) {
                Some(C_COPPER)
            } else {
                Some(C_GREY)
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn halving_the_pitch_quadruples_the_joints() {
        let mut l = BumpLab::default();
        l.pitch = 40.0;
        let a = l.stats().per_mm2;
        l.pitch = 20.0;
        assert!((l.stats().per_mm2 / a - 4.0).abs() < 1e-9);
    }

    #[test]
    fn solder_hits_the_wall_and_hybrid_gets_past_it() {
        let mut l = BumpLab::default();
        l.pitch = 6.0;
        assert!(l.stats().bridges && l.verdict().1);
        l.key(KeyCode::Char('s'));
        assert!(!l.stats().bridges);
    }

    #[test]
    fn microbump_preset_is_fine_and_c4_is_16x_coarser() {
        let l = BumpLab::default();
        let s = l.stats();
        assert!(!l.verdict().1, "{}", l.verdict().0);
        assert!((s.vs_c4 - 14.06).abs() < 0.1);
    }

    #[test]
    fn too_few_power_joints_at_c4_fail_electromigration() {
        let mut l = BumpLab::default();
        l.pitch = 150.0;
        l.amps = 4000.0;
        l.share = 0.05;
        assert!(l.stats().amps_each > l.stats().limit_each);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Left,
            KeyCode::Right,
            KeyCode::Char('s'),
            KeyCode::Char('+'),
            KeyCode::Char('['),
            KeyCode::Char('u'),
            KeyCode::Char('p'),
        ];
        renders(&mut BumpLab::default(), &keys);
    }
}
