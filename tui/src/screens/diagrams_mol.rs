// Interactive atom grids for the `diagrams` detail cards. A card whose label
// has a `Mol` (see `mol_for`) shows the formula, a mass bar and a bonded atom
// grid with a movable cursor above its text. Neighbours of the atom under the
// cursor light up and the pane below explains it.
//
// To add one: build a `Mol` (atoms on a char grid, bonds as index pairs) and
// match its card label in `mol_for`.

use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};

use crate::ui::theme::Theme;

#[derive(Clone, Copy, PartialEq)]
pub enum El {
    Si,
    O,
    H,
    Cl,
}

impl El {
    fn label(self) -> &'static str {
        match self {
            El::Si => "Si",
            El::O => "O",
            El::H => "H",
            El::Cl => "Cl",
        }
    }

    fn width(self) -> u16 {
        self.label().len() as u16
    }

    fn mass(self) -> f64 {
        match self {
            El::Si => 28.09,
            El::O => 16.00,
            El::H => 1.008,
            El::Cl => 35.45,
        }
    }

    pub fn style(self, t: &Theme) -> Style {
        let fg = match self {
            El::Si => return t.accent().add_modifier(Modifier::BOLD),
            El::O => Color::Cyan,
            El::H => return t.base().add_modifier(Modifier::BOLD),
            El::Cl => Color::Green,
        };
        Style::new().fg(fg).add_modifier(Modifier::BOLD)
    }
}

pub struct Atom {
    pub el: El,
    pub row: u16,
    pub col: u16,
    pub info: &'static str,
}

/// Text segment, coloured by element when `Some`, dim otherwise.
type Seg = (&'static str, Option<El>);

pub struct Mol {
    pub atoms: Vec<Atom>,
    pub bonds: Vec<(usize, usize)>,
    /// Header formula, e.g. `SiO` `₂`.
    pub formula: Vec<Seg>,
    /// Atom ratio, e.g. `1 Si : 2 O`.
    pub ratio: Vec<Seg>,
    pub reaction: &'static str,
    /// Formula-unit composition for the mass bar.
    pub comp: Vec<(El, u32)>,
}

fn atom(el: El, row: u16, col: u16, info: &'static str) -> Atom {
    Atom { el, row, col, info }
}

const SI_INFO: &str = "Silicon. 4 bonds, one to each corner oxygen. Each of those oxygens is shared with a neighbouring Si, so this Si owns only 4 x 1/2 = 2 O. That is the 1:2 in SiO2. Mass 28.";
const BRIDGE_INFO: &str = "Oxygen, bridging. 2 bonds, one to each Si it sits between, so each Si counts half of it. Si-O is about 1.61 A and very strong, which is why quartz melts near 1700 C and the furnace needs so much power. Mass 16.";
const EDGE_INFO: &str = "Oxygen at the edge of this sketch. It bonds the Si shown here and a second Si off-screen, where the network keeps going. Quartz has no SiO2 molecules, only this repeating network. Mass 16.";
const CORNER_INFO: &str = "Oxygen, bridging. One bond is to the Si on screen, the other goes up or down out of this flat slice into the 3D network (each Si has 4 O in a tetrahedron). Shared by 2 Si. Mass 16.";

/// Quartz SiO2: two flat-projected Si, each with 4 O; the middle O is shared.
fn quartz() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 8, SI_INFO),
        atom(Si, 2, 21, SI_INFO),
        atom(O, 0, 8, CORNER_INFO),
        atom(O, 4, 8, CORNER_INFO),
        atom(O, 0, 21, CORNER_INFO),
        atom(O, 4, 21, CORNER_INFO),
        atom(O, 2, 2, EDGE_INFO),
        atom(O, 2, 15, BRIDGE_INFO),
        atom(O, 2, 28, EDGE_INFO),
    ];
    let bonds = vec![
        (0, 2),
        (0, 3),
        (0, 6),
        (0, 7),
        (1, 4),
        (1, 5),
        (1, 7),
        (1, 8),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![("SiO", Some(Si)), ("₂", Some(O))],
        ratio: vec![("1 Si", Some(Si)), (" : ", None), ("2 O", Some(O))],
        reaction: "SiO₂ + 2C ──▶ Si + 2CO",
        comp: vec![(Si, 1), (O, 2)],
    }
}

const TCS_SI: &str = "Silicon at the centre, bonded to 3 Cl and 1 H. Unlike quartz this is a real molecule, not a network, so it is small and volatile. Mass 28.";
const TCS_H: &str = "Hydrogen. The only H on the molecule. Mass 1, so almost no weight, but it is what lets the Si-H form that H2 later reduces.";
const TCS_CL: &str = "Chlorine. Heavy: 3 Cl make up about 79% of the molecule's mass. On the hot rod at ~1100 C they leave as HCl and the Si stays behind. Mass 35.";

/// Trichlorosilane SiHCl3: the gas that carries silicon to the bell jar.
fn tcs() -> Mol {
    use El::*;
    let atoms = vec![
        atom(Si, 2, 8, TCS_SI),
        atom(H, 2, 2, TCS_H),
        atom(Cl, 0, 8, TCS_CL),
        atom(Cl, 4, 8, TCS_CL),
        atom(Cl, 2, 15, TCS_CL),
    ];
    Mol {
        atoms,
        bonds: vec![(0, 1), (0, 2), (0, 3), (0, 4)],
        formula: vec![("SiHCl", None), ("₃", None)],
        ratio: vec![
            ("1 Si", Some(Si)),
            (" : ", None),
            ("1 H", Some(H)),
            (" : ", None),
            ("3 Cl", Some(Cl)),
        ],
        reaction: "SiHCl₃ + H₂ ──▶ Si + 3HCl",
        comp: vec![(Si, 1), (H, 1), (Cl, 3)],
    }
}

pub fn mol_for(label: &str) -> Option<Mol> {
    match label.trim() {
        "QUARTZITE" => Some(quartz()),
        "SiHCl3 + H2" => Some(tcs()),
        _ => None,
    }
}

impl Mol {
    pub fn neighbours(&self, cur: usize) -> Vec<usize> {
        self.bonds
            .iter()
            .filter_map(|&(a, b)| match (a == cur, b == cur) {
                (true, _) => Some(b),
                (_, true) => Some(a),
                _ => None,
            })
            .collect()
    }

    /// Nearest atom in direction (dx, dy). Terminal cells are about twice as
    /// tall as wide, so rows count triple to keep "nearest" visually honest.
    pub fn step(&self, cur: usize, dx: i32, dy: i32) -> usize {
        let c = &self.atoms[cur];
        let (cx, cy) = (c.col as i32, c.row as i32 * 3);
        self.atoms
            .iter()
            .enumerate()
            .filter(|(i, _)| *i != cur)
            .filter_map(|(i, a)| {
                let (ddx, ddy) = (a.col as i32 - cx, a.row as i32 * 3 - cy);
                let (along, across) = if dx != 0 {
                    (ddx * dx, ddy.abs())
                } else {
                    (ddy * dy, ddx.abs())
                };
                (along > 0).then_some((along + 2 * across, i))
            })
            .min()
            .map_or(cur, |(_, i)| i)
    }

    /// The atom grid as styled lines. Cursor atom is inverted, its neighbours
    /// and the bonds touching it are bold.
    pub fn lines(&self, cur: usize, t: &Theme) -> Vec<Line<'static>> {
        let w = self
            .atoms
            .iter()
            .map(|a| a.col + a.el.width())
            .max()
            .unwrap_or(0) as usize
            + 1;
        let h = self.atoms.iter().map(|a| a.row).max().unwrap_or(0) as usize + 1;
        // (char, style) per cell
        let mut grid: Vec<Vec<(char, Style)>> = vec![vec![(' ', t.base()); w]; h];
        let near = self.neighbours(cur);
        let bond_on = t.accent().add_modifier(Modifier::BOLD);
        for &(a, b) in &self.bonds {
            let (pa, pb) = (&self.atoms[a], &self.atoms[b]);
            let style = if a == cur || b == cur {
                bond_on
            } else {
                t.border()
            };
            if pa.row == pb.row {
                let (l, r) = if pa.col < pb.col { (pa, pb) } else { (pb, pa) };
                for x in l.col + l.el.width() + 1..r.col - 1 {
                    grid[l.row as usize][x as usize] = ('─', style);
                }
            } else {
                let (u, d) = if pa.row < pb.row { (pa, pb) } else { (pb, pa) };
                for y in u.row + 1..d.row {
                    grid[y as usize][u.col as usize] = ('│', style);
                }
            }
        }
        for (i, a) in self.atoms.iter().enumerate() {
            let style = if i == cur {
                t.on_cursor(a.el.style(t))
            } else if near.contains(&i) {
                a.el.style(t).add_modifier(Modifier::UNDERLINED)
            } else {
                a.el.style(t)
            };
            for (k, ch) in a.el.label().chars().enumerate() {
                grid[a.row as usize][a.col as usize + k] = (ch, style);
            }
        }
        grid.into_iter()
            .map(|row| {
                Line::from(
                    row.into_iter()
                        .map(|(c, s)| Span::styled(c.to_string(), s))
                        .collect::<Vec<_>>(),
                )
            })
            .collect()
    }
}

fn segs(segs: &[Seg], t: &Theme) -> Vec<Span<'static>> {
    segs.iter()
        .map(|&(text, el)| match el {
            Some(e) => Span::styled(text, e.style(t)),
            None => Span::styled(text, t.title()),
        })
        .collect()
}

impl Mol {
    /// `SiO₂   =   1 Si : 2 O      SiO₂ + 2C ──▶ Si + 2CO` with element colours.
    pub fn formula_line(&self, t: &Theme) -> Line<'static> {
        let mut spans = segs(&self.formula, t);
        spans.push(Span::styled("   =   ", t.dim()));
        spans.extend(segs(&self.ratio, t).into_iter().map(|mut s| {
            if s.content.trim() == ":" {
                s.style = t.dim();
            }
            s
        }));
        spans.push(Span::styled(format!("      {}", self.reaction), t.dim()));
        Line::from(spans)
    }

    /// Mass share bar from the composition.
    pub fn mass_line(&self, t: &Theme) -> Line<'static> {
        const W: usize = 30;
        let total: f64 = self.comp.iter().map(|&(e, n)| e.mass() * n as f64).sum();
        let mut spans = vec![Span::styled("mass  ", t.dim())];
        let mut label = String::new();
        let mut used = 0usize;
        for (k, &(e, n)) in self.comp.iter().enumerate() {
            let frac = e.mass() * n as f64 / total;
            let cells = if k + 1 == self.comp.len() {
                W - used
            } else {
                (frac * W as f64).round() as usize
            };
            used += cells;
            spans.push(Span::styled("█".repeat(cells), e.style(t)));
            label.push_str(&format!("  {} {:.0}%", e.label(), frac * 100.0));
        }
        spans.push(Span::styled(label, t.dim()));
        Line::from(spans)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn quartz_grid_shape() {
        let t = Theme::default();
        let m = quartz();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  O ─── Si ─── O ─── Si ─── O");
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.step(0, 1, 0), 7);
    }

    #[test]
    fn tcs_and_mass() {
        let t = Theme::default();
        let m = tcs();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  H ─── Si ─── Cl");
        let bar: String = m
            .mass_line(&t)
            .spans
            .iter()
            .map(|s| s.content.as_ref())
            .collect();
        println!("{bar}");
        assert!(bar.contains("Si 21%") && bar.contains("Cl 79%"));
        assert_eq!(
            m.mass_line(&t)
                .spans
                .iter()
                .filter(|s| s.content.contains('█'))
                .map(|s| s.content.chars().count())
                .sum::<usize>(),
            30
        );
    }
}
