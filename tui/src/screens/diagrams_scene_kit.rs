// Furnace drawing pieces shared by the SAND scenes (plant overview and its
// zoom-ins): the layered cavity around an electrode tip, and the charge
// (burden) that fills everything else.

use crate::ui::anim::shapes::ellipse_e;
use crate::ui::anim::{Canvas, noise};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Layer {
    Cavity,
    Sic,
    Crust,
}

/// A gas cavity under one electrode: cavity, a SiC shell around it, and a
/// crust that grows outward with `crust` (0 = none .. 2 = thick) while also
/// swelling the cavity, as the Elkem reports describe.
#[derive(Debug, Clone, Copy)]
pub struct Cavity {
    pub cx: i32,
    pub cy: i32,
    pub rx: f32,
    pub ry: f32,
}

impl Cavity {
    pub fn radii(&self, crust: f32) -> (f32, f32) {
        (self.rx + crust * 1.2, self.ry + crust * 0.4)
    }

    pub fn layer(&self, x: i32, y: i32, crust: f32) -> Option<Layer> {
        let (rx, ry) = self.radii(crust);
        let e = |rx, ry| ellipse_e(x, y, self.cx, self.cy, rx, ry);
        if e(rx, ry) <= 1.0 {
            Some(Layer::Cavity)
        } else if e(rx + 2.0, ry + 1.2) <= 1.0 {
            Some(Layer::Sic)
        } else if crust > 0.05 && e(rx + 2.0 + 2.5 * crust, ry + 1.2 + 1.4 * crust) <= 1.0 {
            Some(Layer::Crust)
        } else {
            None
        }
    }
}

/// One cell of loose charge: quartzite o, coke •, wood chips ‡, or a gap.
pub fn charge_glyph(world_row: i64, x: i32) -> char {
    let u = noise((world_row as u64).wrapping_mul(7919), x as u64);
    match u {
        u if u < 0.30 => ' ',
        u if u < 0.58 => 'o',
        u if u < 0.80 => '•',
        u if u < 0.92 => '‡',
        _ => ' ',
    }
}

/// Paint charge and cavity layers over `x0..x1` x `y0..y1`. `k` is how many
/// rows the charge has sunk (the endless pattern slides down as it grows).
pub fn paint(
    c: &mut Canvas,
    cavities: &[Cavity],
    crust: f32,
    (x0, x1, y0, y1): (i32, i32, i32, i32),
    k: i64,
) {
    for y in y0..y1 {
        for x in x0..x1 {
            let layer = cavities.iter().find_map(|cv| cv.layer(x, y, crust));
            match layer {
                Some(Layer::Cavity) => {}
                Some(Layer::Sic) => c.put(x, y, '░'),
                Some(Layer::Crust) => c.put(x, y, '▒'),
                None if (x - x0) % 2 == 0 => c.put(x, y, charge_glyph(y as i64 - k, x)),
                None => {}
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn layers_nest_and_crust_grows() {
        let cv = Cavity {
            cx: 20,
            cy: 10,
            rx: 4.0,
            ry: 2.0,
        };
        assert_eq!(cv.layer(20, 10, 0.0), Some(Layer::Cavity));
        assert_eq!(cv.layer(26, 10, 0.0), Some(Layer::Sic));
        assert_eq!(cv.layer(29, 10, 0.0), None);
        assert_eq!(cv.layer(29, 10, 2.0), Some(Layer::Crust));
        // the cavity swells with the crust
        assert_eq!(cv.layer(25, 10, 0.0), Some(Layer::Sic));
        assert_eq!(cv.layer(25, 10, 2.0), Some(Layer::Cavity));
    }

    #[test]
    fn paint_leaves_cavity_empty_and_fills_charge() {
        let mut c = Canvas::new(40, 14);
        let cv = Cavity {
            cx: 20,
            cy: 7,
            rx: 4.0,
            ry: 2.0,
        };
        paint(&mut c, &[cv], 0.0, (0, 40, 0, 14), 0);
        assert_eq!(c.get(20, 7), ' ');
        assert!("░".contains(c.get(26, 7)));
        let any = (0..40).any(|x| "o•‡".contains(c.get(x, 0)));
        assert!(any);
    }
}
