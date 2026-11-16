// BOARD sandbox: power in, heat out. Arrow keys set the GPU's power, `[`/`]` its core voltage,
// `v` moves the voltage regulators from beside the package to underneath it, `c` cycles the
// cooling (air heatsink, cold plate, immersion), `g` the GPUs per rack. Left: the stack on its
// board in cross-section, power path coloured by how much voltage it loses, die coloured by its
// temperature; right: the rack.
//
// Sources: hundreds of amps under a volt, I x R drop at each stage; packages heading to thousands of
// watts; lid and cold plate, liquid cooling; NVLink racks (NVL72 ~120 kW). Resistances, thermal
// resistances and limits are this sandbox's round-number assumptions.

use ratatui::Frame;
use ratatui::crossterm::event::KeyCode;
use ratatui::layout::Rect;
use ratatui::style::Color;
use ratatui::text::Line;

use super::*;
use crate::ui::theme::Theme;

const WATTS: [f64; 12] = [
    300.0, 400.0, 500.0, 700.0, 1000.0, 1200.0, 1400.0, 1800.0, 2000.0, 2500.0, 3000.0, 3600.0,
];
const VOLTS: [f64; 7] = [0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0];
const RACK_GPUS: [u32; 4] = [8, 36, 72, 144];
/// Board-to-die resistance of the power path, ohms.
const R_LATERAL: f64 = 0.03e-3;
const R_VERTICAL: f64 = 0.012e-3;
/// Most voltage the path may lose before the die browns out.
const DROP_LIMIT: f64 = 0.05;
const TJ_MAX: f64 = 95.0;
/// Rack power per GPU includes CPUs, switches, fans, conversion losses.
const RACK_OVERHEAD: f64 = 1.35;
const AIR_RACK_KW: f64 = 40.0;

const C_HOT: Color = Color::Rgb(0xff, 0x55, 0x55);
const C_WATER: Color = Color::Rgb(0x3c, 0x7c, 0xd0);
const C_FLUID: Color = Color::Rgb(0x2c, 0x4c, 0x7a);

#[derive(Debug, Clone, Copy, PartialEq)]
enum Cooling {
    Air,
    ColdPlate,
    Immersion,
}

impl Cooling {
    /// Junction-to-coolant thermal resistance (K/W) and coolant inlet temperature (C).
    fn path(self) -> (f64, f64) {
        match self {
            Cooling::Air => (0.075, 30.0),
            Cooling::ColdPlate => (0.03, 35.0),
            Cooling::Immersion => (0.018, 35.0),
        }
    }

    fn name(self) -> &'static str {
        match self {
            Cooling::Air => "air: heatsink and fans",
            Cooling::ColdPlate => "liquid cold plate",
            Cooling::Immersion => "two-phase immersion",
        }
    }
}

#[derive(Debug, Clone)]
pub struct BoardLab {
    watts: f64,
    volts: f64,
    vertical: bool,
    cooling: Cooling,
    rack: u32,
}

impl Default for BoardLab {
    fn default() -> Self {
        Self {
            watts: 1000.0,
            volts: 0.8,
            vertical: false,
            cooling: Cooling::ColdPlate,
            rack: 72,
        }
    }
}

struct Stats {
    amps: f64,
    drop: f64,
    drop_pct: f64,
    loss_w: f64,
    tj: f64,
    flow_lpm: f64,
    rack_kw: f64,
}

impl BoardLab {
    fn stats(&self) -> Stats {
        let amps = self.watts / self.volts;
        let r = if self.vertical { R_VERTICAL } else { R_LATERAL };
        let drop = amps * r;
        let (rth, inlet) = self.cooling.path();
        Stats {
            amps,
            drop,
            drop_pct: drop / self.volts * 100.0,
            loss_w: amps * amps * r,
            tj: inlet + self.watts * rth,
            // water warming 10 K: 4186 J/kg/K, ~1 kg per litre
            flow_lpm: self.watts / (4186.0 * 10.0) * 60.0,
            rack_kw: self.watts * self.rack as f64 * RACK_OVERHEAD / 1000.0,
        }
    }
}

/// Blue (cool) to purple to red (hot) for a junction temperature.
fn heat(tj: f64) -> Color {
    let f = ((tj - 40.0) / (TJ_MAX + 10.0 - 40.0)).clamp(0.0, 1.0);
    let lerp = |a: u8, b: u8, f: f64| (a as f64 + (b as f64 - a as f64) * f) as u8;
    let (c0, c1, g) = if f < 0.6 {
        ((0x6c, 0x8c, 0xe0), (0xa9, 0x8b, 0xe0), f / 0.6)
    } else {
        ((0xa9, 0x8b, 0xe0), (0xff, 0x55, 0x55), (f - 0.6) / 0.4)
    };
    Color::Rgb(
        lerp(c0.0, c1.0, g),
        lerp(c0.1, c1.1, g),
        lerp(c0.2, c1.2, g),
    )
}

impl Lab for BoardLab {
    fn menu(&self) -> &'static str {
        "power & cooling sandbox: amps, voltage drop, heat, racks"
    }

    fn name(&self) -> &'static str {
        "power & cooling sandbox"
    }

    fn hint(&self) -> &'static str {
        "\u{2190}/\u{2192} watts  [/] volts  v VRM beside/under  c cooling  g GPUs/rack  r reset"
    }

    fn head(&self) -> (String, &'static str) {
        (
            format!("{:.0} W GPU, {}", self.watts, self.cooling.name()),
            "Push the watts: the power path and the cooler give out first.",
        )
    }

    fn verdict(&self) -> (String, bool) {
        let s = self.stats();
        if s.drop_pct > DROP_LIMIT * 100.0 {
            return (
                format!(
                    "Voltage droop. {:.0} A through the board, BGA, substrate and bumps loses {:.0} \
                     mV ({:.1}% of {:.2} V) before reaching the die, and the logic starts failing \
                     past ~5%. Press v to put the regulators right under the package (shorter, \
                     wider path), or raise the voltage.",
                    s.amps,
                    s.drop * 1000.0,
                    s.drop_pct,
                    self.volts
                ),
                true,
            );
        }
        if s.tj > TJ_MAX {
            return (
                format!(
                    "Too hot: the die would sit at {:.0} C (limit ~{TJ_MAX:.0} C). {:.0} W all \
                     becomes heat and has to cross the lid into the {}. Press c for stronger \
                     cooling.",
                    s.tj,
                    self.watts,
                    self.cooling.name()
                ),
                true,
            );
        }
        if self.cooling == Cooling::Air && s.rack_kw > AIR_RACK_KW {
            return (
                format!(
                    "Each GPU is fine, but a rack of {} draws {:.0} kW and air can carry away \
                     about {AIR_RACK_KW:.0} kW per rack. That's why NVL72-class racks (~120 kW) \
                     are liquid cooled: press c.",
                    self.rack, s.rack_kw
                ),
                true,
            );
        }
        (
            format!(
                "{:.0} A at {:.2} V: the path loses {:.0} mV ({:.1}%) and {:.0} W as heat on the \
                 way. The die runs at {:.0} C. A rack of {} draws {:.0} kW{}.",
                s.amps,
                self.volts,
                s.drop * 1000.0,
                s.drop_pct,
                s.loss_w,
                s.tj,
                self.rack,
                s.rack_kw,
                if self.cooling == Cooling::Air {
                    String::new()
                } else {
                    format!(" and needs {:.1} L/min of coolant per GPU", s.flow_lpm)
                }
            ),
            false,
        )
    }

    fn key(&mut self, code: KeyCode) -> bool {
        match code {
            KeyCode::Right | KeyCode::Char('l') => self.watts = step_in(&WATTS, self.watts, 1),
            KeyCode::Left | KeyCode::Char('h') => self.watts = step_in(&WATTS, self.watts, -1),
            KeyCode::Char(']') => self.volts = step_in(&VOLTS, self.volts, 1),
            KeyCode::Char('[') => self.volts = step_in(&VOLTS, self.volts, -1),
            KeyCode::Char('v') => self.vertical = !self.vertical,
            KeyCode::Char('c') => {
                self.cooling = match self.cooling {
                    Cooling::Air => Cooling::ColdPlate,
                    Cooling::ColdPlate => Cooling::Immersion,
                    Cooling::Immersion => Cooling::Air,
                }
            }
            KeyCode::Char('g') => self.rack = cycle(&RACK_GPUS, self.rack),
            KeyCode::Char('r') => *self = Self::default(),
            _ => return false,
        }
        true
    }

    fn body(&self, frame: &mut Frame, r: Rect, t: &Theme) {
        let s = self.stats();
        let bg = t.bg.unwrap_or(Color::Reset);
        let (side_r, rack_r, nums_r) = three_way(r, 52);
        let mut items = vec![
            (C_BOARD, "board"),
            (C_GREY, "VRM"),
            (C_POWER, "power path"),
            (C_ORGANIC, "substrate"),
            (heat(s.tj), "GPU die (by temp)"),
            (C_HBM, "HBM"),
        ];
        match self.cooling {
            Cooling::Air => items.push((C_SOLDER, "heatsink fins")),
            Cooling::ColdPlate => {
                items.push((C_COPPER, "cold plate"));
                items.push((C_WATER, "coolant"));
            }
            Cooling::Immersion => items.push((C_FLUID, "dielectric fluid")),
        }
        let pr = panel(
            frame,
            side_r,
            "CROSS-SECTION",
            "one GPU on its board",
            &items,
            t,
        );
        self.draw_side(frame, pr, &s, bg);

        let rr = panel(
            frame,
            rack_r,
            "RACK",
            &format!("{} GPUs, {:.0} kW", self.rack, s.rack_kw),
            &[(heat(s.tj), "one GPU")],
            t,
        );
        let n = self.rack as usize;
        let cols = if n <= 8 { 4 } else { 8 };
        let rows_n = n.div_ceil(cols);
        let (area, side) = square(rr);
        if side >= 8 {
            let cw = side as f64 / cols as f64;
            let ch = side as f64 / rows_n.max(cols) as f64;
            let col = heat(s.tj);
            paint(frame.buffer_mut(), area, bg, |px, py| {
                let (i, j) = ((px as f64 / cw) as usize, (py as f64 / ch) as usize);
                if i >= cols || j >= rows_n || j * cols + i >= n {
                    return None;
                }
                let (fx, fy) = ((px as f64 / cw).fract(), (py as f64 / ch).fract());
                (fx < 0.8 && fy < 0.7).then_some(col)
            });
        }

        let mut drop = vec![k("DROP", t)];
        let bad_drop = s.drop_pct > DROP_LIMIT * 100.0;
        drop.extend(bar(
            s.drop_pct / (2.0 * DROP_LIMIT * 100.0) * 100.0,
            20,
            if bad_drop { C_BAD } else { C_POWER },
            t,
        ));
        drop.push(good_or_bad(
            format!(" {:.0} mV = {:.1}% (limit 5%)", s.drop * 1000.0, s.drop_pct),
            bad_drop,
            t,
        ));
        let mut temp = vec![k("DIE TEMP", t)];
        let hot = s.tj > TJ_MAX;
        temp.extend(bar(
            s.tj / (TJ_MAX * 1.4) * 100.0,
            20,
            if hot { C_BAD } else { heat(s.tj) },
            t,
        ));
        temp.push(good_or_bad(
            format!(" {:.0} C (limit ~{TJ_MAX:.0})", s.tj),
            hot,
            t,
        ));
        let (rth, inlet) = self.cooling.path();
        let rows = vec![
            Line::from(vec![
                k("CURRENT", t),
                v(format!("{} A", thousands(s.amps)), t),
                d(format!(" = {:.0} W / {:.2} V", self.watts, self.volts), t),
            ]),
            Line::from(vec![
                k("VRM", t),
                v(
                    if self.vertical {
                        "under the package (vertical)"
                    } else {
                        "beside the package (lateral)"
                    },
                    t,
                ),
                d(
                    format!(
                        "  {:.3} mOhm path",
                        if self.vertical { R_VERTICAL } else { R_LATERAL } * 1e3
                    ),
                    t,
                ),
            ]),
            Line::from(drop),
            Line::from(vec![
                k("PATH LOSS", t),
                v(format!("{:.0} W turned to heat on the way", s.loss_w), t),
            ]),
            Line::from(temp),
            Line::from(vec![
                k("COOLING", t),
                v(self.cooling.name(), t),
                d(format!("  {rth} K/W, {inlet:.0} C in"), t),
            ]),
            Line::from(vec![
                k("COOLANT", t),
                if self.cooling == Cooling::Air {
                    d("air", t)
                } else {
                    v(format!("{:.1} L/min per GPU (10 K rise)", s.flow_lpm), t)
                },
            ]),
            Line::from(vec![
                k("RACK", t),
                good_or_bad(
                    format!("{:.0} kW for {} GPUs", s.rack_kw, self.rack),
                    self.cooling == Cooling::Air && s.rack_kw > AIR_RACK_KW,
                    t,
                ),
            ]),
            Line::default(),
            Line::from(d(
                "Resistances and thermal figures are round-number assumptions.",
                t,
            )),
        ];
        numbers(frame, nums_r, rows);
    }

    fn summary(&self) -> String {
        let s = self.stats();
        format!(
            "power & cooling sandbox: {:.0} W at {:.2} V = {:.0} A, VRM {}, drop {:.1}%, {}, Tj \
             {:.0} C, rack of {} = {:.0} kW",
            self.watts,
            self.volts,
            s.amps,
            if self.vertical { "vertical" } else { "lateral" },
            s.drop_pct,
            self.cooling.name(),
            s.tj,
            self.rack,
            s.rack_kw
        )
    }
}

impl BoardLab {
    /// One GPU on its board, side on: board, VRMs, BGA, substrate, interposer, die and HBM, lid,
    /// cooler; the power path from the VRMs to the die tinted by how much voltage it has lost.
    fn draw_side(&self, frame: &mut Frame, r: Rect, s: &Stats, bg: Color) {
        let (scale, ox, oy) = fit(r, 140.0, 72.0);
        let vertical = self.vertical;
        let cooling = self.cooling;
        let die_col = heat(s.tj);
        let lost = (s.drop_pct / (DROP_LIMIT * 100.0)).clamp(0.0, 1.0);
        let path_col = |f: f64| {
            // yellow at the regulator, toward red by the die as voltage is lost
            let g = f * lost;
            let lerp = |a: f64, b: f64| (a + (b - a) * g) as u8;
            Color::Rgb(lerp(241.0, 255.0), lerp(208.0, 85.0), lerp(92.0, 85.0))
        };
        // heights (mm, y down, 0 at the board's top face); drawn taller than life
        let board = (0.0, 8.0);
        let bga = (-2.0, 0.0);
        let sub = (-8.0, -2.0);
        let inter = (-11.0, -8.0);
        let die = (-15.0, -11.0);
        let lid = (-18.0, -15.0);
        let pkg_w = 34.0;
        let die_w = 14.0;
        paint(frame.buffer_mut(), r, bg, |px, py| {
            let x = (px as f64 + 0.5) * scale - ox;
            let y = (py as f64 + 0.5) * scale - oy + 10.0;
            let inside = |(a, b): (f64, f64)| y >= a && y < b;
            // power path: VRM -> along/through the board -> up the middle into the die
            let path_w = 1.4 * scale.max(0.6);
            if vertical {
                let up = x.abs() < path_w && y >= die.0 + 1.0 && y < board.1 + 10.0;
                if up {
                    let f = 1.0 - ((y - die.0) / (board.1 + 10.0 - die.0)).clamp(0.0, 1.0);
                    return Some(path_col(f));
                }
                if inside((board.1 + 2.0, board.1 + 10.0)) && x.abs() < 16.0 {
                    return Some(C_GREY);
                }
            } else {
                let run = inside((board.1 * 0.4, board.1 * 0.4 + path_w * 1.5))
                    && x.abs() < 55.0
                    && x.abs() > 0.0;
                let up = x.abs() < path_w && y >= die.0 + 1.0 && y < board.1 * 0.4 + path_w;
                if run {
                    let f = 1.0 - (x.abs() / 55.0) * 0.6;
                    return Some(path_col(f * 0.6));
                }
                if up {
                    let f =
                        0.6 + 0.4 * (1.0 - ((y - die.0) / (board.1 * 0.4 - die.0)).clamp(0.0, 1.0));
                    return Some(path_col(f));
                }
                if inside((-7.0, 0.0)) && (x.abs() > 48.0 && x.abs() < 62.0) {
                    return Some(C_GREY);
                }
            }
            if inside(board) && x.abs() < 68.0 {
                return Some(C_BOARD);
            }
            if inside(bga) && x.abs() < pkg_w / 2.0 {
                return ((x + 50.0).rem_euclid(2.5) < 1.4).then_some(C_SOLDER);
            }
            if inside(sub) && x.abs() < pkg_w / 2.0 {
                return Some(C_ORGANIC);
            }
            if inside(inter) && x.abs() < pkg_w / 2.0 - 4.0 {
                return Some(C_INTERPOSER);
            }
            if inside(die) {
                if x.abs() < die_w / 2.0 {
                    return Some(die_col);
                }
                if x.abs() > die_w / 2.0 + 1.0 && x.abs() < pkg_w / 2.0 - 4.0 {
                    let mid = ((x.abs() - (die_w / 2.0 + 1.0)) - 3.0).abs() < 0.6;
                    return Some(if mid { C_TSV } else { C_HBM });
                }
            }
            if inside(lid) && x.abs() < pkg_w / 2.0 - 2.0 {
                return Some(C_SOLDER);
            }
            match cooling {
                Cooling::Air => {
                    if inside((-21.0, lid.0)) && x.abs() < 40.0 {
                        return Some(C_SOLDER);
                    }
                    if inside((-55.0, -21.0)) && x.abs() < 40.0 && (x + 40.0).rem_euclid(4.0) < 1.6
                    {
                        return Some(C_SOLDER);
                    }
                }
                Cooling::ColdPlate => {
                    if inside((-26.0, lid.0)) && x.abs() < 24.0 {
                        let chan = inside((-23.0, -20.0)) && (x + 24.0).rem_euclid(6.0) < 3.0;
                        return Some(if chan { C_WATER } else { C_COPPER });
                    }
                    if inside((-40.0, -26.0)) && (x.abs() - 18.0).abs() < 2.5 {
                        return Some(C_WATER);
                    }
                }
                Cooling::Immersion => {
                    if inside((-60.0, board.1)) && x.abs() < 66.0 {
                        let bubble = ((x * 0.7 + y * 1.3).sin() * (x * 1.1 - y * 0.4).cos()) > 0.93
                            && y < lid.0;
                        return Some(if bubble { C_SOLDER } else { C_FLUID });
                    }
                }
            }
            if s.tj > TJ_MAX && inside((-60.0, lid.0)) && x.abs() < 6.0 && (y as i64 % 6 < 2) {
                return Some(C_HOT);
            }
            None
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_is_a_working_b200_class_setup() {
        let l = BoardLab::default();
        assert!(!l.verdict().1, "{}", l.verdict().0);
        assert!((l.stats().amps - 1250.0).abs() < 1.0);
    }

    #[test]
    fn high_power_droops_until_the_vrm_moves_under() {
        let mut l = BoardLab::default();
        l.watts = 2000.0;
        l.cooling = Cooling::Immersion;
        assert!(l.verdict().1);
        l.key(KeyCode::Char('v'));
        assert!(!l.verdict().1, "{}", l.verdict().0);
    }

    #[test]
    fn air_cannot_cool_a_kilowatt() {
        let mut l = BoardLab::default();
        l.vertical = true;
        l.cooling = Cooling::Air;
        assert!(l.stats().tj > TJ_MAX);
    }

    #[test]
    fn draws_through_every_key() {
        let keys = [
            KeyCode::Right,
            KeyCode::Char(']'),
            KeyCode::Char('v'),
            KeyCode::Char('c'),
            KeyCode::Char('g'),
            KeyCode::Left,
            KeyCode::Char('['),
        ];
        renders(&mut BoardLab::default(), &keys);
    }
}
