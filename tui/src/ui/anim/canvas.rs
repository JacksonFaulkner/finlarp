// A character grid scenes draw into. Coordinates are signed so scenes can
// place things partly off-canvas (particles, drifting smoke) without
// bounds checks of their own: anything outside is clipped.

#[derive(Debug, Clone)]
pub struct Canvas {
    w: usize,
    h: usize,
    cells: Vec<char>,
}

impl Canvas {
    pub fn new(w: u16, h: u16) -> Self {
        let (w, h) = (w as usize, h as usize);
        Self {
            w,
            h,
            cells: vec![' '; w * h],
        }
    }

    pub fn width(&self) -> usize {
        self.w
    }

    pub fn height(&self) -> usize {
        self.h
    }

    pub fn clear(&mut self) {
        self.cells.fill(' ');
    }

    fn idx(&self, x: i32, y: i32) -> Option<usize> {
        (x >= 0 && y >= 0 && (x as usize) < self.w && (y as usize) < self.h)
            .then(|| y as usize * self.w + x as usize)
    }

    pub fn get(&self, x: i32, y: i32) -> char {
        self.idx(x, y).map_or(' ', |i| self.cells[i])
    }

    pub fn put(&mut self, x: i32, y: i32, ch: char) {
        if let Some(i) = self.idx(x, y) {
            self.cells[i] = ch;
        }
    }

    /// Put `ch` only where nothing is drawn yet.
    pub fn put_if_blank(&mut self, x: i32, y: i32, ch: char) {
        if self.get(x, y) == ' ' {
            self.put(x, y, ch);
        }
    }

    pub fn text(&mut self, x: i32, y: i32, s: &str) {
        for (i, ch) in s.chars().enumerate() {
            self.put(x + i as i32, y, ch);
        }
    }

    /// Text with a blank cell on each side cleared first, so it reads over
    /// busy backgrounds.
    pub fn label(&mut self, x: i32, y: i32, s: &str) {
        let n = s.chars().count() as i32;
        self.hline(x - 1, y, n + 2, ' ');
        self.text(x, y, s);
    }

    pub fn hline(&mut self, x: i32, y: i32, len: i32, ch: char) {
        for dx in 0..len {
            self.put(x + dx, y, ch);
        }
    }

    pub fn vline(&mut self, x: i32, y: i32, len: i32, ch: char) {
        for dy in 0..len {
            self.put(x, y + dy, ch);
        }
    }

    /// Single-line box with its top-left corner at (x, y).
    pub fn boxed(&mut self, x: i32, y: i32, w: i32, h: i32) {
        if w < 2 || h < 2 {
            return;
        }
        self.hline(x + 1, y, w - 2, '─');
        self.hline(x + 1, y + h - 1, w - 2, '─');
        self.vline(x, y + 1, h - 2, '│');
        self.vline(x + w - 1, y + 1, h - 2, '│');
        self.put(x, y, '┌');
        self.put(x + w - 1, y, '┐');
        self.put(x, y + h - 1, '└');
        self.put(x + w - 1, y + h - 1, '┘');
    }

    /// Stamp art lines at (x, y); spaces are transparent.
    pub fn blit(&mut self, x: i32, y: i32, art: &[&str]) {
        for (dy, line) in art.iter().enumerate() {
            for (dx, ch) in line.chars().enumerate() {
                if ch != ' ' {
                    self.put(x + dx as i32, y + dy as i32, ch);
                }
            }
        }
    }

    /// Rows with trailing blanks trimmed.
    pub fn lines(&self) -> Vec<String> {
        self.cells
            .chunks(self.w.max(1))
            .map(|row| row.iter().collect::<String>().trim_end().to_string())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn clips_instead_of_panicking() {
        let mut c = Canvas::new(4, 2);
        c.put(-1, 0, 'x');
        c.put(4, 0, 'x');
        c.put(0, 2, 'x');
        c.text(2, 1, "abcdef");
        assert_eq!(c.lines(), vec!["", "  ab"]);
    }

    #[test]
    fn box_and_blit() {
        let mut c = Canvas::new(5, 3);
        c.boxed(0, 0, 5, 3);
        c.blit(1, 1, &["a b"]);
        assert_eq!(c.lines(), vec!["┌───┐", "│a b│", "└───┘"]);
        let mut d = Canvas::new(5, 1);
        d.text(0, 0, "-----");
        d.blit(0, 0, &["a b"]);
        assert_eq!(d.lines(), vec!["a-b--"]);
    }

    #[test]
    fn label_clears_behind_itself() {
        let mut c = Canvas::new(8, 1);
        c.text(0, 0, "xxxxxxxx");
        c.label(2, 0, "ab");
        assert_eq!(c.lines(), vec!["x ab xxx"]);
    }

    #[test]
    fn put_if_blank_keeps_existing() {
        let mut c = Canvas::new(2, 1);
        c.put(0, 0, 'a');
        c.put_if_blank(0, 0, 'b');
        c.put_if_blank(1, 0, 'c');
        assert_eq!(c.lines(), vec!["ac"]);
    }
}
