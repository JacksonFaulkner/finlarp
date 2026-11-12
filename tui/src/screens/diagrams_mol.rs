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
    B,
    P,
}

impl El {
    fn label(self) -> &'static str {
        match self {
            El::Si => "Si",
            El::O => "O",
            El::H => "H",
            El::Cl => "Cl",
            El::B => "B",
            El::P => "P",
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
            El::B => 10.81,
            El::P => 30.97,
        }
    }

    pub fn style(self, t: &Theme) -> Style {
        let fg = match self {
            El::Si => return t.accent().add_modifier(Modifier::BOLD),
            El::O => Color::Cyan,
            El::H => return t.base().add_modifier(Modifier::BOLD),
            El::Cl => Color::Green,
            El::B => Color::Magenta,
            El::P => Color::Yellow,
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

// LOAD card: substitutional B (p-type) and P (n-type) sitting in Si lattice sites.
// Sources: k0 B 0.8 / As 0.3 (US 9,634,098), P 0.35 (US 9,580,327, US 7,811,356),
// Si 5e22 atoms/cm3 (Berkeley EE105), Si-Si 2.35 A / 109.5 deg (MicroChemicals),
// ionization B 45, P 44, As 54 meV (Chenming Hu ch1 slides), 4.6 ohm-cm at 1e15
// (BYU cleanroom calculator, Masetti 1983).

const DOP_B: &str = "Boron, substitutional p-type dopant. Only 3 valence electrons, so of its 4 bonds to Si one is missing an electron: a hole. It costs only ~45 meV to set that hole free, so at room temperature nearly every B gives one. k0 = 0.8, so B freezes in almost as fast as it arrives: resistivity stays fairly even along the ingot. Mass 11.";
const DOP_P: &str = "Phosphorus, substitutional n-type dopant. 5 valence electrons: 4 make the bonds to Si, the 5th is held by only ~44 meV and roams free at room temperature. k0 = 0.35 (arsenic is similar at 0.3), so the crystal takes only about a third of what the melt holds and the rest piles up in the liquid. Mass 31.";
const DOP_SI_W: &str = "Silicon at the edge of this sketch; the lattice keeps going off-screen. A crystal holds about 5e22 Si atoms per cm3. Every Si here has 4 neighbours, each sharing one pair of electrons, which is why pure Si conducts so poorly: no electron is left over. Mass 28.";
const DOP_SI_BN: &str = "Silicon bonded to the boron. The real bonds point to the corners of a tetrahedron, 109.5 degrees apart, flattened here into a cross. The Si-Si spacing is 2.35 A, and B is small enough to sit in a Si site without any extra bonds. Mass 28.";
const DOP_SI_BS: &str = "Silicon bonded to the boron. Its bond to B is short one electron. A neighbouring electron hops in to fill it, and the gap moves on: the hole drifts through the lattice as a positive carrier, while B is left as a fixed negative ion. Mass 28.";
const DOP_SI_MID: &str = "Silicon between both dopants, drawn bonded to B and to P. Real doping is far thinner: 1e15 dopants in 5e22 Si per cm3 is 1 per 5e7 Si, so dopants sit ~100 nm apart. If B and P met in one crystal they would cancel (compensation). Mass 28.";
const DOP_SI_PN: &str = "Silicon bonded to the phosphorus. All 4 of its electrons go into normal pairs, one of them shared with P. P's 5th electron fits no bond, so it drifts away as a negative carrier, leaving P as a fixed positive ion. Mass 28.";
const DOP_SI_PS: &str = "Silicon bonded to the phosphorus. Since P's k0 is 0.35, the melt gets richer in P as the crystal grows (Scheil equation, textbook), so later Si sites take in more P. The tail ends up more heavily doped and lower in resistivity than the head. Mass 28.";
const DOP_SI_E: &str = "Silicon at the edge of the sketch. Why one dopant per ~5e7 Si matters: at 1e15 per cm3 the resistivity is about 4.6 ohm-cm (BYU calculator, varies by dopant), and the dose loaded with the charge sets it for the whole ingot. Mass 28.";

/// Substitutional dopants: B (p-type) and P (n-type), each in a Si site with 4 Si neighbours.
fn dopants() -> Mol {
    use El::*;
    let atoms = vec![
        atom(B, 2, 9, DOP_B),
        atom(P, 2, 22, DOP_P),
        atom(Si, 2, 2, DOP_SI_W),
        atom(Si, 2, 15, DOP_SI_MID),
        atom(Si, 2, 28, DOP_SI_E),
        atom(Si, 0, 9, DOP_SI_BN),
        atom(Si, 4, 9, DOP_SI_BS),
        atom(Si, 0, 22, DOP_SI_PN),
        atom(Si, 4, 22, DOP_SI_PS),
    ];
    let bonds = vec![
        (0, 2),
        (0, 3),
        (0, 5),
        (0, 6),
        (1, 3),
        (1, 4),
        (1, 7),
        (1, 8),
    ];
    Mol {
        atoms,
        bonds,
        formula: vec![
            ("Si", Some(Si)),
            (":B", Some(B)),
            (" / ", None),
            ("Si", Some(Si)),
            (":P", Some(P)),
        ],
        ratio: vec![
            ("1 B", Some(B)),
            (" : ", None),
            ("1 P", Some(P)),
            (" : ", None),
            ("7 Si", Some(Si)),
        ],
        reaction: "melt + dopant ──▶ Si:B (k0 0.8), Si:P (k0 0.35)",
        comp: vec![(Si, 7), (B, 1), (P, 1)],
    }
}

// Sources for the numbers below:
//   SiO attacks graphite, CO back-diffuses: https://ecs.confex.com/ecs/226/webprogram/Paper39706.html ;
//     https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/4956153 (0.5 ppma breakdown limit)
//   graphite -> SiC surface: https://patents.google.com/patent/US9212431 ; https://patents.google.com/patent/US6221478 (SiO at ~1410 C)
//   Ar 50-200 L/min, 20-80 kPa: https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12297560
//   Ar 100 L/min, 1200 Pa: https://www.researching.cn/ArticlePdf/m00098/2020/41/10/102702.pdf
//   Ar 100 L/min, 2500 Pa: https://www.comsol.com/blogs/thermal-analysis-of-a-czochralski-crystal-growth-furnace
//   C < 2e14 /cm3, poly ~5e14: https://www.scientific.net/SSP.242.3 ; FT-IR limit ~1e15: US 10,355,092
//   SGL SIGRAFINE hot zone ~1500 C: https://www.sglcarbon.com/en/markets-solutions/material/sigrafine-isostatic-graphite/
//   Toyo Tanso isotropic graphite since 1974: https://www.toyotanso.co.jp/introduction/products_en.html

/// Hot zone: SiO from the melt eats graphite (SiO + 2C -> SiC + CO); CO
/// back-dissolves as substitutional carbon; argon sweeps the gases out.

// Interstitial oxygen (Oi) in the Si lattice, for the MELT + PULL "Oxygen" card.
// Sources: arxiv.org/pdf/mtrl-th/9504001 (bond-centre site, 1.563 A);
// patents.google.com/patent/USH520 (12-18 ppma, bulk 12-16 ppma);
// patents.google.com/patent/US4545849 (1.6e18 cm-3 = about 32 ppma; SiO evaporation);
// patents.google.com/patent/US4010064 (oxygen falls as crucible dissolution slows);
// SEMI MF1188 (1107 cm-1 band); core.ac.uk/works/140288043 + Cambridge JMR (450 C thermal
// donors, 2-5 O cores; C suppresses them); ecs.confex.com/ecs/aimes2018/webprogram/Paper113734.html
// (Oi strengthens vs slip, bulk precipitates getter metals); image-ppubs 6503594 (precipitates pin
// slip dislocations); image-ppubs 7397110 (carbon >= 0.5e16 vs BMD strength loss);
// jstage jjacg vol 26 (segregation coefficient 0.8 +- 0.1).

/// Interstitial oxygen: an O in a bond-centred site between two Si, in a Si lattice.

// Sources for the numbers below:
//   lattice 5.431 A, 5.0e22 atoms/cm3, 109.5 deg: pv-manufacturing.org/solar-cell-manufacturing/silicon-crystallograpy/ ;
//     tricor.readthedocs.io/en/latest/examples/silicon/index.html
//   8 atoms/cell, 2.33 g/cm3: faculty-web.msoe.edu/johnsontimoj/CE3101/files3101/silicon_crystal_structure.pdf
//   bond 2.35 A = a*sqrt(3)/4 = 2.352 A (geometry from a = 5.431 A)
//   1414 C, 1826 J/g: link.springer.com/article/10.1007/s10973-019-08716-5
//   50.21 kJ/mol: en.wikipedia.org/wiki/Enthalpy_of_fusion
//   melt ~10% denser, metallic: patent US 6,800,540 ; link.aps.org/accepted/10.1103/PhysRevB.97.140103
//   melt coordination 5.5-6: arxiv.org/pdf/1201.0401
//   1e18 O/cm3, 9.9 kg/h, 1403-1407.5 C: MELT_PULL.details.txt (Wikipedia, COMSOL)

/// Diamond-cubic Si above a disordered melt: the Czochralski growth front.

// Sources: US 7,226,508 ; US 9,593,432 ; US 11,466,381 ; US 11,821,103 ;
// US 4,010,064 ; US 6,302,957 ; Cz crucible patents (1817 K flow point, graphite
// susceptor) ; arXiv 1109.2852 (a-SiO2 angle) ; Mauri et al. PRB 62 R4786 (2000) ;
// https://en.wikipedia.org/wiki/High-purity_quartz (BNEF ~80%) ;
// https://en.wikipedia.org/wiki/Czochralski_method (1e18 O/cm3) ;
// J. Jpn. Assoc. Cryst. Growth vol 26 (sessile-drop triple junction).

/// Crucible wall: graphite | fused SiO2 glass | inner (cristobalite) wall | Si(l), with SiO leaving.

pub fn mol_for(label: &str) -> Option<Mol> {
    match label.trim() {
        "QUARTZITE" => Some(quartz()),
        "SiHCl3 + H2" => Some(tcs()),
        "LOAD" => Some(dopants()),
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

    #[test]
    fn dopants_grid() {
        let t = Theme::default();
        let m = dopants();
        let rows: Vec<String> = m
            .lines(0, &t)
            .iter()
            .map(|l| l.spans.iter().map(|s| s.content.as_ref()).collect())
            .collect();
        println!("{}", rows.join("\n"));
        assert_eq!(rows[2].trim_end(), "  Si ─── B ─── Si ─── P ─── Si");
        assert_eq!(m.neighbours(0).len(), 4);
        assert_eq!(m.neighbours(1).len(), 4);
        assert_eq!(m.step(0, 1, 0), 3);
    }
}
