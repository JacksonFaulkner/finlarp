// ASSEMBLY sandbox: the yield stackup of CoWoS (chip on wafer on substrate). Every part and every
// bonding step has to succeed, so the package yield is the product of all of them, and a late
// failure scraps every good part already bonded. `+`/`-` HBM stacks, `c` logic dies, `k` known-good
// die testing on/off, `b` the yield of each bonding step, arrow keys CoWoS capacity in wafers a
// month. Left: the yield falling step by step; right: 100 packages, the scrapped ones in red.
//
// Sources: known-good dies; CoW, then dicing, then C4 reflow onto the substrate, underfill, lid;
// "10 parts at 99% = ~90%"; CoWoS capacity as the bottleneck (reports). Part yields, part prices
// and the capacity range are this sandbox's assumptions.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;

use super::*;
use crate::ui::help::{Key, key};
use crate::ui::theme::Theme;

/// Arriving yield of a part: tested at speed and burned in (KGD), or only probed at wafer sort.
const LOGIC_KGD: f64 = 0.995;
const LOGIC_RAW: f64 = 0.96;
const HBM_KGD: f64 = 0.99;
const HBM_RAW: f64 = 0.95;
const BOND_YIELDS: [f64; 3] = [0.99, 0.995, 0.999];
const LOGIC_COST: f64 = 1_500.0;
const HBM_COST: f64 = 400.0;
const PACKAGE_COST: f64 = 600.0;
/// CoWoS wafers a month the arrow keys step through (public estimates ~35k end-2024, ~75k end-2025).
const CAPACITY: [f64; 6] = [20_000.0, 35_000.0, 50_000.0, 75_000.0, 100_000.0, 130_000.0];
const DIES: [u32; 2] = [1, 2];
const DIE_MM2: f64 = 800.0;

#[derive(Debug, Clone)]
pub struct AssemblyLab {
    dies: u32,
    hbm: u32,
    kgd: bool,
    bond: f64,
    capacity: f64,
}

impl Default for AssemblyLab {
    fn default() -> Self {
        Self {
            dies: 2,
            hbm: 8,
            kgd: true,
            bond: 0.999,
            capacity: 75_000.0,
        }
    }
}

/// One step of the stackup: what it is, its yield, and the cumulative yield after it.
struct Step {
    what: String,
    each: f64,
    after: f64,
}

struct Stats {
    steps: Vec<Step>,
    yield_pct: f64,
    parts_cost: f64,
    scrap_per_good: f64,
    per_wafer: usize,
    per_month: f64,
}

impl AssemblyLab {
    fn stats(&self) -> Stats {
        let (logic, hbm) = if self.kgd {
            (LOGIC_KGD, HBM_KGD)
        } else {
            (LOGIC_RAW, HBM_RAW)
        };
        let mut cum = 1.0;
        let mut steps = Vec::new();
        let mut push = |what: String, each: f64, times: u32| {
            let all = each.powi(times as i32);
            cum *= all;
            steps.push(Step {
                what,
                each: all,
                after: cum,
            });
        };
        push(
            format!("{} logic die(s) arrive good", self.dies),
            logic,
            self.dies,
        );
        push(
            format!("{} HBM stacks arrive good", self.hbm),
            hbm,
            self.hbm,
        );
        push(
            format!("{} chips bonded onto the wafer (CoW)", self.dies + self.hbm),
            self.bond,
            self.dies + self.hbm,
        );
        push("diced out".into(), self.bond, 1);
        push("C4 reflow onto substrate (oS)".into(), self.bond, 1);
        push("underfill".into(), self.bond, 1);
        push("lid".into(), self.bond, 1);
        push("final test".into(), self.bond, 1);
        let parts_cost = self.dies as f64 * LOGIC_COST + self.hbm as f64 * HBM_COST + PACKAGE_COST;
        let layout = PkgLayout::new(DIE_MM2 * self.dies as f64, self.dies, self.hbm);
        let (iw, ih) = layout.interposer();
        let per_wafer = wafer_sites(iw, ih).len();
        Stats {
            yield_pct: cum * 100.0,
            parts_cost,
            scrap_per_good: parts_cost / cum - parts_cost,
            per_month: self.capacity * per_wafer as f64 * cum,
            per_wafer,
            steps,
        }
    }
}

const KEYS: &[Key] = &[
    key("+/=", "more HBM stacks"),
    key("-/j", "fewer HBM stacks"),
    key("c", "dies per package"),
    key("k", "known-good-die test on or off"),
    key("b", "bond yield"),
    key("h/l", "capacity"),
    key("r", "reset"),
];

impl Lab for AssemblyLab {
    fn keys(&self) -> &'static [Key] {
        KEYS
    }

    fn menu(&self) -> &'static str {
        "assembly sandbox: yield stackup, known-good dies, capacity"
    }

    fn name(&self) -> &'static str {
        "assembly sandbox"
    }

    fn head(&self) -> (String, &'static str) {
        (
            format!("{} logic + {} HBM per package", self.dies, self.hbm),
            "Every part and every step must work: yields multiply.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        let s = self.stats();
        if !self.kgd {
            let tested = AssemblyLab {
                kgd: true,
                ..self.clone()
            }
            .stats();
            return (
                format!(
                    "No known-good-die testing: parts are only probed at wafer sort, so bad ones \
                     slip in and each failure scraps the good HBM bonded beside it. {:.0}% of \
                     packages work vs {:.0}% with testing. Press k.",
                    s.yield_pct, tested.yield_pct
                ),
                true,
            );
        }
        if s.yield_pct < 85.0 {
            return (
                format!(
                    "{} parts and steps multiply to {:.0}%: each failed package throws away {} of \
                     parts on average per good one. Better bonding (b) or fewer stacks help.",
                    self.dies + self.hbm + 5,
                    s.yield_pct,
                    money(s.scrap_per_good)
                ),
                true,
            );
        }
        (
            format!(
                "{:.0}% of packages work. At {} CoWoS wafers a month and {} packages per wafer, \
                 that's ~{} GPUs a month: the packaging line, not the GPU dies, sets the output.",
                s.yield_pct,
                thousands(self.capacity),
                s.per_wafer,
                thousands(s.per_month)
            ),
            false,
        )
    }

    fn key(&mut self, code: KeyCode) -> bool {
        match code {
            KeyCode::Char('+') | KeyCode::Char('=') | KeyCode::Up => {
                self.hbm = (self.hbm + 1).min(16)
            }
            KeyCode::Char('-') | KeyCode::Down | KeyCode::Char('j') => {
                self.hbm = self.hbm.saturating_sub(1).max(1)
            }
            KeyCode::Char('c') => self.dies = cycle(&DIES, self.dies),
            KeyCode::Char('k') => self.kgd = !self.kgd,
            KeyCode::Char('b') => self.bond = cycle(&BOND_YIELDS, self.bond),
            KeyCode::Right | KeyCode::Char('l') => {
                self.capacity = step_in(&CAPACITY, self.capacity, 1)
            }
            KeyCode::Left | KeyCode::Char('h') => {
                self.capacity = step_in(&CAPACITY, self.capacity, -1)
            }
            KeyCode::Char('r') => *self = Self::default(),
            _ => return false,
        }
        true
    }

    fn body(&self, frame: &mut Frame, r: Rect, t: &Theme) {
        let s = self.stats();
        let bg = t.bg.unwrap_or(Color::Reset);
        let (fall_r, grid_r, nums_r) = three_way(r, 50);

        // the stackup: a bar per step, the cumulative yield after it
        let [ft, fb] = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(fall_r);
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled("YIELD STACKUP", t.accent()),
                Span::styled(" \u{00B7} packages still good after each step", t.dim()),
            ])),
            ft,
        );
        let bar_w = (fb.width as usize).saturating_sub(14).clamp(8, 40);
        let mut lines = Vec::new();
        for st in &s.steps {
            let pct = st.after * 100.0;
            let col = if pct < 85.0 { C_BAD } else { C_OK };
            lines.push(Line::from(vec![
                Span::styled(format!("{}", st.what), t.base()),
                Span::styled(format!("  x{:.1}%", st.each * 100.0), t.dim()),
            ]));
            let mut b = bar(pct, bar_w, col, t);
            b.push(Span::styled(format!(" {pct:.1}%"), Style::new().fg(col)));
            lines.push(Line::from(b));
        }
        frame.render_widget(Paragraph::new(lines), fb);

        let gr = panel(
            frame,
            grid_r,
            "100 PACKAGES",
            "built this way",
            &[(C_OK, "works"), (C_BAD, "scrapped, parts and all")],
            t,
        );
        let bad = (100.0 - s.yield_pct).round().clamp(0.0, 100.0) as usize;
        // scatter the scrapped ones with a fixed shuffle so they don't pile in one corner
        let mut order: Vec<usize> = (0..100).collect();
        let mut seed = 0x2545_f491_4f6c_dd1du64;
        for i in (1..100).rev() {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            order.swap(i, (seed % (i as u64 + 1)) as usize);
        }
        let scrapped: std::collections::HashSet<usize> = order[..bad].iter().copied().collect();
        let (area, side) = square(gr);
        if side >= 10 {
            let cell = side as f64 / 10.0;
            paint(frame.buffer_mut(), area, bg, |px, py| {
                let (cx, cy) = (px as f64 / cell, py as f64 / cell);
                let (i, j) = (cx as usize, cy as usize);
                if i >= 10 || j >= 10 {
                    return None;
                }
                let (fx, fy) = (cx.fract(), cy.fract());
                if fx > 0.8 || fy > 0.8 {
                    return None;
                }
                Some(if scrapped.contains(&(j * 10 + i)) {
                    C_BAD
                } else {
                    C_OK
                })
            });
        }

        let rows = vec![
            Line::from(vec![
                k("PACKAGE", t),
                good_or_bad(format!("{:.1}% good", s.yield_pct), s.yield_pct < 85.0, t),
            ]),
            Line::from(vec![
                k("TESTING", t),
                good_or_bad(
                    if self.kgd {
                        "known-good dies: every part tested first"
                    } else {
                        "wafer-sort probe only"
                    },
                    !self.kgd,
                    t,
                ),
            ]),
            Line::from(vec![
                k("PARTS", t),
                v(format!("{} per package", money(s.parts_cost)), t),
                d(
                    format!(
                        "  ({} x {}, {} x {}, {} package)",
                        self.dies,
                        money(LOGIC_COST),
                        self.hbm,
                        money(HBM_COST),
                        money(PACKAGE_COST)
                    ),
                    t,
                ),
            ]),
            Line::from(vec![
                k("SCRAP", t),
                v(
                    format!("{} lost per good package", money(s.scrap_per_good)),
                    t,
                ),
            ]),
            Line::from(vec![
                k("PER WAFER", t),
                v(format!("{} packages", s.per_wafer), t),
                d(" per CoWoS interposer wafer", t),
            ]),
            Line::from(vec![
                k("CAPACITY", t),
                v(format!("{} wafers/month", thousands(self.capacity)), t),
                d(
                    format!(" \u{2192} ~{} GPUs/month", thousands(s.per_month)),
                    t,
                ),
            ]),
            Line::default(),
            Line::from(d(
                "Part yields and prices are assumptions for illustration.",
                t,
            )),
        ];
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "assembly sandbox: {} logic + {} HBM, KGD {}, bond yield {:.1}%, package yield \
             {:.1}%, ~{} GPUs/month at {} wafers/month",
            self.dies,
            self.hbm,
            self.kgd,
            self.bond * 100.0,
            s.yield_pct,
            thousands(s.per_month),
            thousands(self.capacity)
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ten_parts_near_99_is_about_90() {
        let l = AssemblyLab {
            dies: 1,
            hbm: 9,
            kgd: true,
            bond: 0.999,
            capacity: 75_000.0,
        };
        let s = l.stats();
        assert!((80.0..92.0).contains(&s.yield_pct), "{}", s.yield_pct);
    }

    #[test]
    fn known_good_dies_raise_yield() {
        let mut l = AssemblyLab::default();
        let tested = l.stats().yield_pct;
        l.key(KeyCode::Char('k'));
        assert!(l.stats().yield_pct < tested);
        assert!(l.verdict().1);
    }

    #[test]
    fn more_stacks_lower_yield() {
        let mut l = AssemblyLab::default();
        let a = l.stats().yield_pct;
        l.key(KeyCode::Char('+'));
        assert!(l.stats().yield_pct < a);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Char('+'),
            KeyCode::Char('c'),
            KeyCode::Char('k'),
            KeyCode::Char('b'),
            KeyCode::Right,
            KeyCode::Left,
            KeyCode::Char('-'),
        ];
        renders(&mut AssemblyLab::default(), &keys);
    }
}
