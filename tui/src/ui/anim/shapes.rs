// Drawing helpers on top of Canvas: orthogonal paths with things flowing
// along them, ellipses, and titled boxes. Positions are cell coordinates;
// terminal cells are about twice as tall as wide, so ellipses want rx ~ 2*ry
// to look round.

use super::canvas::Canvas;
use super::motion::{Particle, Particles};

/// `((x-cx)/rx)^2 + ((y-cy)/ry)^2`: <= 1 inside the ellipse.
pub fn ellipse_e(x: i32, y: i32, cx: i32, cy: i32, rx: f32, ry: f32) -> f32 {
    let dx = (x - cx) as f32 / rx.max(0.01);
    let dy = (y - cy) as f32 / ry.max(0.01);
    dx * dx + dy * dy
}

pub fn fill_ellipse(c: &mut Canvas, cx: i32, cy: i32, rx: f32, ry: f32, ch: char) {
    for y in cy - ry.ceil() as i32..=cy + ry.ceil() as i32 {
        for x in cx - rx.ceil() as i32..=cx + rx.ceil() as i32 {
            if ellipse_e(x, y, cx, cy, rx, ry) <= 1.0 {
                c.put(x, y, ch);
            }
        }
    }
}

/// Box with a title set into its top border.
pub fn titled_box(c: &mut Canvas, x: i32, y: i32, w: i32, h: i32, title: &str) {
    c.boxed(x, y, w, h);
    if !title.is_empty() && w > 5 {
        let t: String = title.chars().take((w - 5) as usize).collect();
        c.text(x + 2, y, &format!(" {t} "));
    }
}

/// A polyline of horizontal and vertical segments.
#[derive(Debug, Clone)]
pub struct Path {
    pts: Vec<(i32, i32)>,
}

impl Path {
    pub fn new(pts: &[(i32, i32)]) -> Self {
        Self { pts: pts.to_vec() }
    }

    /// Every cell the path covers, in order.
    pub fn cells(&self) -> Vec<(i32, i32)> {
        let mut out = Vec::new();
        for w in self.pts.windows(2) {
            let ((x0, y0), (x1, y1)) = (w[0], w[1]);
            let (dx, dy) = ((x1 - x0).signum(), (y1 - y0).signum());
            let n = (x1 - x0).abs().max((y1 - y0).abs());
            for i in 0..n {
                out.push((x0 + dx * i, y0 + dy * i));
            }
        }
        if let Some(last) = self.pts.last() {
            out.push(*last);
        }
        out
    }

    /// Cell at fraction `f` (0..=1) along the path.
    pub fn at(&self, f: f32) -> (i32, i32) {
        let cells = self.cells();
        if cells.is_empty() {
            return (0, 0);
        }
        let i = (f.clamp(0.0, 1.0) * (cells.len() - 1) as f32).round() as usize;
        cells[i]
    }

    /// Draw the pipe with line glyphs and corners.
    pub fn draw(&self, c: &mut Canvas) {
        for (k, w) in self.pts.windows(2).enumerate() {
            let ((x0, y0), (x1, y1)) = (w[0], w[1]);
            let (dx, dy) = ((x1 - x0).signum(), (y1 - y0).signum());
            let n = (x1 - x0).abs().max((y1 - y0).abs());
            let glyph = if dy == 0 { '─' } else { '│' };
            for i in 1..n {
                c.put(x0 + dx * i, y0 + dy * i, glyph);
            }
            if k == 0 {
                c.put(x0, y0, glyph);
            }
            let end = if let Some(next) = self.pts.get(k + 2) {
                // corner: connects back toward the previous point and on to the next
                let (nx, ny) = ((next.0 - x1).signum(), (next.1 - y1).signum());
                corner((-dx, -dy), (nx, ny))
            } else {
                glyph
            };
            c.put(x1, y1, end);
        }
    }
}

fn corner(a: (i32, i32), b: (i32, i32)) -> char {
    let has = |d: (i32, i32)| a == d || b == d;
    match (has((-1, 0)), has((1, 0)), has((0, -1)), has((0, 1))) {
        (true, true, _, _) => '─',
        (_, _, true, true) => '│',
        (true, _, _, true) => '┐',
        (true, _, true, _) => '┘',
        (_, true, _, true) => '┌',
        (_, true, true, _) => '└',
        _ => '┼',
    }
}

/// Things streaming along `path`: one glyph per live particle, chosen by
/// the caller from the particle's id / randomness.
pub fn flow(
    c: &mut Canvas,
    path: &Path,
    now_ms: u64,
    stream: Particles,
    glyph: impl Fn(&Particle) -> char,
) {
    let cells = path.cells();
    if cells.is_empty() {
        return;
    }
    stream.each(now_ms, |p| {
        let i = (p.age * (cells.len() - 1) as f32).round() as usize;
        let (x, y) = cells[i];
        c.put(x, y, glyph(&p));
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn path_cells_and_corners() {
        let p = Path::new(&[(0, 0), (3, 0), (3, 2)]);
        assert_eq!(
            p.cells(),
            vec![(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)]
        );
        assert_eq!(p.at(0.0), (0, 0));
        assert_eq!(p.at(1.0), (3, 2));
        let mut c = Canvas::new(5, 3);
        p.draw(&mut c);
        assert_eq!(c.lines(), vec!["───┐", "   │", "   │"]);
        let mut c = Canvas::new(5, 3);
        Path::new(&[(3, 0), (3, 2), (0, 2)]).draw(&mut c);
        assert_eq!(c.lines(), vec!["   │", "   │", "───┘"]);
    }

    #[test]
    fn ellipse_membership() {
        assert!(ellipse_e(0, 0, 0, 0, 4.0, 2.0) <= 1.0);
        assert!(ellipse_e(4, 0, 0, 0, 4.0, 2.0) <= 1.0);
        assert!(ellipse_e(5, 0, 0, 0, 4.0, 2.0) > 1.0);
        let mut c = Canvas::new(9, 5);
        fill_ellipse(&mut c, 4, 2, 3.0, 1.0, '#');
        assert_eq!(c.lines()[2], " #######");
        assert_eq!(c.lines()[0], "");
    }

    #[test]
    fn flows_stay_on_the_path() {
        let p = Path::new(&[(0, 0), (9, 0)]);
        let mut c = Canvas::new(10, 1);
        flow(&mut c, &p, 500, Particles::new(1, 200, 1000), |_| 'o');
        assert!(c.lines()[0].contains('o'));
    }
}
