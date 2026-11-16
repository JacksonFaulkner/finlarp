// INTERPOSER sandbox: put dies and HBM stacks on an interposer and see how big it gets, in reticles,
// against what CoWoS-S (one silicon slab) and CoWoS-L (silicon bridges in an organic interposer)
// can build, and how few fit on a wafer. Arrow keys change the logic silicon, `c` the die count,
// `+`/`-` HBM stacks, `t` switches CoWoS-S / CoWoS-L.
//
// Sources: CoWoS-S up to ~3.3x reticle (~2,700 mm2, TSMC); CoWoS-L for Blackwell; ~5.5x reticle
// CoWoS-L for 2026 and 9.5x with 12 HBM stacks planned for 2027 (Tom's Hardware); HBM3 1024-bit bus
// per stack.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::Rect;
use ratatui::style::Color;
use ratatui::text::Line;

use super::*;
use crate::ui::theme::Theme;

const S_MAX: f64 = 3.3;
const L_NOW: f64 = 5.5;
const L_PLAN: f64 = 9.5;
const BITS_PER_STACK: u32 = 1024;
const CHIPLETS: [u32; 3] = [1, 2, 4];
/// The package view stays this many mm across so a growing interposer reads as growing.
const VIEW_MM: f64 = 70.0;

#[derive(Debug, Clone, Copy, PartialEq)]
enum Kind {
    S,
    L,
}

struct Preset {
    name: &'static str,
    total: f64,
    dies: u32,
    hbm: u32,
    kind: Kind,
}

const PRESETS: [Preset; 3] = [
    Preset {
        name: "H100-like on CoWoS-S",
        total: 814.0,
        dies: 1,
        hbm: 6,
        kind: Kind::S,
    },
    Preset {
        name: "B200-like on CoWoS-L",
        total: 1600.0,
        dies: 2,
        hbm: 8,
        kind: Kind::L,
    },
    Preset {
        name: "the 2027 plan: 4 dies, 12 stacks",
        total: 3200.0,
        dies: 4,
        hbm: 12,
        kind: Kind::L,
    },
];

#[derive(Debug, Clone)]
pub struct InterposerLab {
    total: f64,
    dies: u32,
    hbm: u32,
    kind: Kind,
    preset: Option<usize>,
}

impl Default for InterposerLab {
    fn default() -> Self {
        let mut l = Self {
            total: 0.0,
            dies: 1,
            hbm: 0,
            kind: Kind::S,
            preset: None,
        };
        l.apply(0);
        l
    }
}

struct Stats {
    layout: PkgLayout,
    iw: f64,
    ih: f64,
    area: f64,
    reticles: f64,
    per_wafer: usize,
    wires: u32,
    die_too_big: bool,
}

impl InterposerLab {
    fn apply(&mut self, i: usize) {
        let p = &PRESETS[i];
        self.total = p.total;
        self.dies = p.dies;
        self.hbm = p.hbm;
        self.kind = p.kind;
        self.preset = Some(i);
    }

    fn stats(&self) -> Stats {
        let layout = PkgLayout::new(self.total, self.dies, self.hbm);
        let (iw, ih) = layout.interposer();
        let area = iw * ih;
        Stats {
            iw,
            ih,
            area,
            reticles: area / RETICLE_MM2,
            per_wafer: wafer_sites(iw, ih).len(),
            wires: layout.hbm * BITS_PER_STACK,
            die_too_big: layout.w * layout.h > RETICLE_MM2 + 0.5,
            layout,
        }
    }

    fn limit(&self) -> f64 {
        match self.kind {
            Kind::S => S_MAX,
            Kind::L => L_PLAN,
        }
    }
}

impl Lab for InterposerLab {
    fn menu(&self) -> &'static str {
        "interposer sandbox: size in reticles, CoWoS-S vs -L"
    }

    fn name(&self) -> &'static str {
        "interposer sandbox"
    }

    fn hint(&self) -> &'static str {
        "\u{2190}/\u{2192} logic silicon  c dies  +/- HBM  t CoWoS-S/-L  p preset  r reset"
    }

    fn head(&self) -> (String, &'static str) {
        (
            self.preset
                .map_or("your package".to_string(), |i| PRESETS[i].name.to_string()),
            "Add dies and memory: the interposer under them grows past one reticle.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        let s = self.stats();
        if s.die_too_big {
            return (
                "Each logic die is bigger than one reticle and can't be printed: press c for \
                 more, smaller dies (see LOGIC DIE)."
                    .to_string(),
                true,
            );
        }
        if self.hbm > s.layout.hbm_fit {
            return (
                format!(
                    "Only {} HBM stacks fit along the dies' edges, not {}. HBM must sit right \
                     beside the logic so its 1024 wires stay short; more stacks need more edge.",
                    s.layout.hbm_fit, self.hbm
                ),
                true,
            );
        }
        if self.kind == Kind::S && s.reticles > S_MAX {
            return (
                format!(
                    "Too big for CoWoS-S. One silicon slab is printed in stitched reticle fields \
                     and tops out near {S_MAX}x reticle (~2,700 mm2); this needs {:.1}x. Press t \
                     for CoWoS-L: an organic interposer with small silicon bridges only under the \
                     die-to-die and die-to-HBM joints.",
                    s.reticles
                ),
                true,
            );
        }
        if s.reticles > L_PLAN {
            return (
                format!(
                    "{:.1}x reticle is past even the 2027 plan ({L_PLAN}x). Nobody builds this \
                     yet.",
                    s.reticles
                ),
                true,
            );
        }
        if self.kind == Kind::L && s.reticles > L_NOW {
            return (
                format!(
                    "{:.1}x reticle: past what CoWoS-L ships today (~{L_NOW}x), inside the 2027 \
                     plan ({L_PLAN}x). Only {} fit on a 300 mm wafer.",
                    s.reticles, s.per_wafer
                ),
                false,
            );
        }
        (
            format!(
                "A {:.1}x-reticle interposer ({:.0} mm2). Only {} fit on a 300 mm wafer, and each \
                 GPU needs a whole one, so CoWoS capacity, not GPU dies, often limits how many \
                 ship. {} wires cross it from the HBM.",
                s.reticles,
                s.area,
                s.per_wafer,
                thousands(s.wires as f64)
            ),
            false,
        )
    }

    fn key(&mut self, code: KeyCode) -> bool {
        match code {
            KeyCode::Right | KeyCode::Char('l') => self.total = (self.total + 50.0).min(4000.0),
            KeyCode::Left | KeyCode::Char('h') => self.total = (self.total - 50.0).max(200.0),
            KeyCode::Char('c') => self.dies = cycle(&CHIPLETS, self.dies),
            KeyCode::Char('+') | KeyCode::Char('=') | KeyCode::Up | KeyCode::Char('k') => {
                self.hbm = (self.hbm + 1).min(20)
            }
            KeyCode::Char('-') | KeyCode::Down | KeyCode::Char('j') => {
                self.hbm = self.hbm.saturating_sub(1)
            }
            KeyCode::Char('t') => {
                self.kind = match self.kind {
                    Kind::S => Kind::L,
                    Kind::L => Kind::S,
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
        let (wafer_r, pkg_r, nums_r) = three_way(r, 38);
        let base = match self.kind {
            Kind::S => C_INTERPOSER,
            Kind::L => C_ORGANIC,
        };
        let over = s.reticles > self.limit();
        let wp = panel(
            frame,
            wafer_r,
            "WAFER",
            "300 mm, cut into interposers",
            &[(if over { C_BAD } else { base }, "one interposer")],
            t,
        );
        draw_wafer(
            frame.buffer_mut(),
            wp,
            s.iw,
            s.ih,
            |_| if over { C_BAD } else { base },
            &[],
            bg,
        );

        let mut items = vec![
            (C_DIE, "GPU die"),
            (C_HBM, "HBM stack"),
            (C_TSV, "TSVs"),
            (
                base,
                match self.kind {
                    Kind::S => "silicon interposer",
                    Kind::L => "organic interposer",
                },
            ),
        ];
        if self.kind == Kind::L {
            items.push((C_BRIDGE, "silicon bridge"));
        }
        let pp = panel(
            frame,
            pkg_r,
            "PACKAGE",
            &format!("from above, {VIEW_MM:.0} mm across"),
            &items,
            t,
        );
        let span = VIEW_MM.max(s.iw + 4.0).max(s.ih + 4.0);
        let style = PkgStyle {
            die: if s.die_too_big { C_BAD } else { C_DIE },
            interposer: if over { C_BAD } else { base },
            reticle: false,
            bridges: self.kind == Kind::L,
            span: Some((span, span)),
        };
        draw_package(frame.buffer_mut(), pp, &s.layout, &style, bg);

        let mut size = vec![k("SIZE", t)];
        size.extend(bar(
            s.reticles / L_PLAN * 100.0,
            20,
            if over { C_BAD } else { base },
            t,
        ));
        size.push(good_or_bad(format!(" {:.1}x reticle", s.reticles), over, t));
        let rows = vec![
            Line::from(vec![
                k("INTERPOSER", t),
                v(format!("{:.0} x {:.0} mm", s.iw, s.ih), t),
                d(format!(" = {} mm2", thousands(s.area)), t),
            ]),
            Line::from(size),
            Line::from(vec![
                k("LIMITS", t),
                d(
                    format!(
                        "CoWoS-S {S_MAX}x \u{00B7} CoWoS-L ~{L_NOW}x today, {L_PLAN}x planned 2027"
                    ),
                    t,
                ),
            ]),
            Line::from(vec![
                k("PER WAFER", t),
                good_or_bad(format!("{} interposers", s.per_wafer), s.per_wafer < 10, t),
                d(" = GPUs per CoWoS wafer, at best", t),
            ]),
            Line::from(vec![
                k("ON TOP", t),
                v(
                    format!(
                        "{} logic die{} ({:.0} mm2 each), {} HBM",
                        self.dies,
                        if self.dies == 1 { "" } else { "s" },
                        s.layout.w * s.layout.h,
                        s.layout.hbm
                    ),
                    t,
                ),
            ]),
            Line::from(vec![
                k("WIRES", t),
                v(
                    format!("{} HBM data wires cross it", thousands(s.wires as f64)),
                    t,
                ),
                d(" (1024 per stack)", t),
            ]),
            Line::from(vec![
                k("HOW", t),
                d(
                    match self.kind {
                        Kind::S => "one silicon slab, fine wiring everywhere, TSVs for power",
                        Kind::L => "organic RDL, silicon bridges only under the fine joints",
                    },
                    t,
                ),
            ]),
        ];
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "interposer sandbox: {:?}, {} dies, {} HBM, interposer {:.0} x {:.0} mm = {:.1}x \
             reticle, {} per wafer",
            self.kind, self.dies, s.layout.hbm, s.iw, s.ih, s.reticles, s.per_wafer
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn h100_fits_cowos_s_and_b200_needs_l() {
        let mut l = InterposerLab::default();
        let s = l.stats();
        assert!(s.reticles < S_MAX, "{}", s.reticles);
        assert!(!l.verdict().1, "{}", l.verdict().0);
        l.key(KeyCode::Char('p'));
        assert!(l.stats().reticles > S_MAX);
        l.key(KeyCode::Char('t'));
        assert!(l.verdict().1, "B200 on CoWoS-S is too big");
    }

    #[test]
    fn plan_preset_is_inside_the_2027_limit() {
        let mut l = InterposerLab::default();
        l.apply(2);
        let s = l.stats();
        assert!(s.reticles > L_NOW && s.reticles < L_PLAN, "{}", s.reticles);
        assert_eq!(s.layout.hbm, 12);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Right,
            KeyCode::Char('c'),
            KeyCode::Char('+'),
            KeyCode::Char('t'),
            KeyCode::Char('p'),
            KeyCode::Left,
            KeyCode::Char('-'),
        ];
        renders(&mut InterposerLab::default(), &keys);
    }
}
