// Z flow: the chat as text around the picture. Claude runs headless (`claude -p
// --output-format stream-json`, one session per mode) and its reply streams into the empty
// space of the canvas, wrapping around the model, so turning the model moves the text.
//
// How the free space is found: the picture is rendered to pixels first, so each terminal
// cell it covers is marked busy when any pixel in it differs from the background (labels and
// leader lines are in the picture, so the text avoids them too), then the busy cells grow by a
// margin. Text rows are slots: full-width rows above the model, then the column left of it,
// then the column right of it, then full-width rows below. The newest text is always shown;
// older paragraphs drop off the top (J/K walks back through them).
//
// How text sits on the picture: kitty draws the image only in cells holding its placeholder
// character, so a text cell simply replaces a placeholder. ratatui-image gives only the first
// cell of each row its row/column diacritics and lets the rest count on from their left
// neighbour, so a placeholder right after text is rewritten with explicit diacritics.
//
// While the camera moves, the busy cells only grow (old and new picture both avoided), and
// they reset to the current picture once it has been still for SETTLE; that keeps text from
// jumping around or covering the model mid-orbit.

use std::io::{BufRead, BufReader};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::sync::mpsc::{Receiver, TryRecvError, channel};
use std::time::{Duration, Instant};

use image::RgbaImage;
use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::Style;
use unicode_width::{UnicodeWidthChar, UnicodeWidthStr};

use super::chat::{Ev, parse_line};
use crate::ui::theme::Theme;

/// Narrowest column worth putting text in.
const MIN_W: u16 = 12;
/// Widest a column reaches out from the picture's middle (long lines are hard to read).
const MAX_W: u16 = 64;
/// Widest the left column gets when the picture sits on the right.
const LEFT_MAX: u16 = 90;
/// How long the camera must be still before the text re-wraps to the picture as it is.
pub const SETTLE: Duration = Duration::from_millis(180);
/// A pixel this far from the background (sum of channel differences) is part of the picture.
const PIXEL_DIFF: u32 = 40;
/// A cell with at least this many such pixels is busy (one stray antialiased pixel is not).
const PIXELS_BUSY: u32 = 3;
/// kitty's image placeholder character.
const PLACEHOLDER: char = '\u{10EEEE}';
/// kitty's row/column diacritics, in order (index n encodes the number n). From
/// https://sw.kovidgoyal.net/kitty/_downloads/1792bad15b12979994cd6ecc54c967a6/rowcolumn-diacritics.txt
const DIACRITICS: &str = "\u{305}\u{30D}\u{30E}\u{310}\u{312}\u{33D}\u{33E}\u{33F}\u{346}\u{34A}\u{34B}\u{34C}\u{350}\u{351}\u{352}\u{357}\u{35B}\u{363}\u{364}\u{365}\u{366}\u{367}\u{368}\u{369}\u{36A}\u{36B}\u{36C}\u{36D}\u{36E}\u{36F}\u{483}\u{484}\u{485}\u{486}\u{487}\u{592}\u{593}\u{594}\u{595}\u{597}\u{598}\u{599}\u{59C}\u{59D}\u{59E}\u{59F}\u{5A0}\u{5A1}\u{5A8}\u{5A9}\u{5AB}\u{5AC}\u{5AF}\u{5C4}\u{610}\u{611}\u{612}\u{613}\u{614}\u{615}\u{616}\u{617}\u{657}\u{658}\u{659}\u{65A}\u{65B}\u{65D}\u{65E}\u{6D6}\u{6D7}\u{6D8}\u{6D9}\u{6DA}\u{6DB}\u{6DC}\u{6DF}\u{6E0}\u{6E1}\u{6E2}\u{6E4}\u{6E7}\u{6E8}\u{6EB}\u{6EC}\u{730}\u{732}\u{733}\u{735}\u{736}\u{73A}\u{73D}\u{73F}\u{740}\u{741}\u{743}\u{745}\u{747}\u{749}\u{74A}\u{7EB}\u{7EC}\u{7ED}\u{7EE}\u{7EF}\u{7F0}\u{7F1}\u{7F3}\u{816}\u{817}\u{818}\u{819}\u{81B}\u{81C}\u{81D}\u{81E}\u{81F}\u{820}\u{821}\u{822}\u{823}\u{825}\u{826}\u{827}\u{829}\u{82A}\u{82B}\u{82C}\u{82D}\u{951}\u{953}\u{954}\u{F82}\u{F83}\u{F86}\u{F87}\u{135D}\u{135E}\u{135F}\u{17DD}\u{193A}\u{1A17}\u{1A75}\u{1A76}\u{1A77}\u{1A78}\u{1A79}\u{1A7A}\u{1A7B}\u{1A7C}\u{1B6B}\u{1B6D}\u{1B6E}\u{1B6F}\u{1B70}\u{1B71}\u{1B72}\u{1B73}\u{1CD0}\u{1CD1}\u{1CD2}\u{1CDA}\u{1CDB}\u{1CE0}\u{1DC0}\u{1DC1}\u{1DC3}\u{1DC4}\u{1DC5}\u{1DC6}\u{1DC7}\u{1DC8}\u{1DC9}\u{1DCB}\u{1DCC}\u{1DD1}\u{1DD2}\u{1DD3}\u{1DD4}\u{1DD5}\u{1DD6}\u{1DD7}\u{1DD8}\u{1DD9}\u{1DDA}\u{1DDB}\u{1DDC}\u{1DDD}\u{1DDE}\u{1DDF}\u{1DE0}\u{1DE1}\u{1DE2}\u{1DE3}\u{1DE4}\u{1DE5}\u{1DE6}\u{1DFE}\u{20D0}\u{20D1}\u{20D4}\u{20D5}\u{20D6}\u{20D7}\u{20DB}\u{20DC}\u{20E1}\u{20E7}\u{20E9}\u{20F0}\u{2CEF}\u{2CF0}\u{2CF1}\u{2DE0}\u{2DE1}\u{2DE2}\u{2DE3}\u{2DE4}\u{2DE5}\u{2DE6}\u{2DE7}\u{2DE8}\u{2DE9}\u{2DEA}\u{2DEB}\u{2DEC}\u{2DED}\u{2DEE}\u{2DEF}\u{2DF0}\u{2DF1}\u{2DF2}\u{2DF3}\u{2DF4}\u{2DF5}\u{2DF6}\u{2DF7}\u{2DF8}\u{2DF9}\u{2DFA}\u{2DFB}\u{2DFC}\u{2DFD}\u{2DFE}\u{2DFF}\u{A66F}\u{A67C}\u{A67D}\u{A6F0}\u{A6F1}\u{A8E0}\u{A8E1}\u{A8E2}\u{A8E3}\u{A8E4}\u{A8E5}\u{A8E6}\u{A8E7}\u{A8E8}\u{A8E9}\u{A8EA}\u{A8EB}\u{A8EC}\u{A8ED}\u{A8EE}\u{A8EF}\u{A8F0}\u{A8F1}\u{AAB0}\u{AAB2}\u{AAB3}\u{AAB7}\u{AAB8}\u{AABE}\u{AABF}\u{AAC1}\u{FE20}\u{FE21}\u{FE22}\u{FE23}\u{FE24}\u{FE25}\u{FE26}\u{10A0F}\u{10A38}\u{1D185}\u{1D186}\u{1D187}\u{1D188}\u{1D189}\u{1D1AA}\u{1D1AB}\u{1D1AC}\u{1D1AD}\u{1D242}\u{1D243}\u{1D244}";

/// Which cells of an area are taken by the picture.
#[derive(Clone, Debug, PartialEq)]
pub struct Mask {
    pub cols: u16,
    pub rows: u16,
    busy: Vec<bool>,
}

impl Mask {
    pub fn free(cols: u16, rows: u16) -> Self {
        Self {
            cols,
            rows,
            busy: vec![false; cols as usize * rows as usize],
        }
    }

    pub fn busy(&self, x: u16, y: u16) -> bool {
        x < self.cols && y < self.rows && self.busy[y as usize * self.cols as usize + x as usize]
    }

    fn set(&mut self, x: u16, y: u16) {
        if x < self.cols && y < self.rows {
            self.busy[y as usize * self.cols as usize + x as usize] = true;
        }
    }

    /// This mask moved `dx` columns right inside a `cols` x `rows` area (the picture drawn
    /// in part of the area).
    pub fn placed_in(&self, cols: u16, rows: u16, dx: u16) -> Mask {
        let mut out = Mask::free(cols, rows);
        for y in 0..self.rows {
            for x in 0..self.cols {
                if self.busy(x, y) {
                    out.set(x + dx, y);
                }
            }
        }
        out
    }

    fn same_size(&self, o: &Mask) -> bool {
        self.cols == o.cols && self.rows == o.rows
    }

    fn union(&mut self, o: &Mask) {
        for (a, b) in self.busy.iter_mut().zip(&o.busy) {
            *a |= *b;
        }
    }

    /// The busy cells grown by `dx` columns and `dy` rows each way.
    fn grown(&self, dx: u16, dy: u16) -> Mask {
        let mut out = Mask::free(self.cols, self.rows);
        for y in 0..self.rows {
            for x in 0..self.cols {
                if !self.busy(x, y) {
                    continue;
                }
                for yy in y.saturating_sub(dy)..=(y + dy).min(self.rows.saturating_sub(1)) {
                    for xx in x.saturating_sub(dx)..=(x + dx).min(self.cols.saturating_sub(1)) {
                        out.set(xx, yy);
                    }
                }
            }
        }
        out
    }
}

/// The cells of a `cols` x `rows` area that the rendered picture covers, with a margin. One
/// cell is `cell` pixels of `img` (the render may be smaller than the terminal draws it).
pub fn image_mask(img: &RgbaImage, cell: (f64, f64), cols: u16, rows: u16, bg: [u8; 3]) -> Mask {
    let mut counts = vec![0u32; cols as usize * rows as usize];
    let (cw, ch) = (cell.0.max(0.01), cell.1.max(0.01));
    for (px, py, p) in img.enumerate_pixels() {
        let d = (p[0] as i32 - bg[0] as i32).unsigned_abs()
            + (p[1] as i32 - bg[1] as i32).unsigned_abs()
            + (p[2] as i32 - bg[2] as i32).unsigned_abs();
        if d < PIXEL_DIFF {
            continue;
        }
        let (cx, cy) = ((px as f64 / cw) as usize, (py as f64 / ch) as usize);
        if cx < cols as usize && cy < rows as usize {
            counts[cy * cols as usize + cx] += 1;
        }
    }
    let mut m = Mask::free(cols, rows);
    for (b, n) in m.busy.iter_mut().zip(counts) {
        *b = n >= PIXELS_BUSY;
    }
    m.grown(2, 0).grown(0, 1)
}

/// The cells of `area` already drawn on (art, a message), with a margin.
pub fn buffer_mask(buf: &Buffer, area: Rect) -> Mask {
    let mut m = Mask::free(area.width, area.height);
    for y in 0..area.height {
        for x in 0..area.width {
            if let Some(c) = buf.cell((area.x + x, area.y + y)) {
                if !c.symbol().trim().is_empty() {
                    m.set(x, y);
                }
            }
        }
    }
    m.grown(2, 0).grown(0, 1)
}

/// The busy cells the text wraps around: they only grow while the picture moves and reset
/// to the picture as it is once it has been still for SETTLE.
#[derive(Default)]
pub struct Settle {
    mask: Option<Mask>,
    geom: u64,
    moved: Option<Instant>,
}

impl Settle {
    /// `latest` is the picture as last rendered; `geom` changes whenever the camera, the
    /// diagram or the area does (not with animation).
    pub fn update(&mut self, latest: &Mask, geom: u64) -> &Mask {
        match &mut self.mask {
            Some(m) if m.same_size(latest) => {
                if geom != self.geom {
                    self.geom = geom;
                    self.moved = Some(Instant::now());
                    m.union(latest);
                } else if self.moved.is_some_and(|t| t.elapsed() >= SETTLE) {
                    *m = latest.clone();
                    self.moved = None;
                } else {
                    m.union(latest);
                }
            }
            _ => {
                self.mask = Some(latest.clone());
                self.geom = geom;
                self.moved = None;
            }
        }
        self.mask.as_ref().expect("set above")
    }

    /// Still waiting for the picture to stay put (redraw soon to re-wrap).
    pub fn pending(&self) -> bool {
        self.moved.is_some()
    }
}

/// One row of text: where it goes.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Slot {
    pub y: u16,
    pub x: u16,
    pub w: u16,
}

/// Where text can go, in reading order: a column left of the picture, top to bottom, then a
/// column right of it. Each hugs the picture: its inner edge follows the model's outline row by
/// row, its outer edge is straight, at most MAX_W from the picture's middle. Column 0 and the
/// last column stay empty.
pub fn slots(m: &Mask) -> Vec<Slot> {
    let (cols, rows) = (m.cols, m.rows);
    if cols < 3 {
        return Vec::new();
    }
    let (lo, hi) = (1u16, cols - 1);
    // The picture's middle column splits the two sides (the area's middle when it is empty).
    let (bx0, bx1) = (lo..hi)
        .filter(|&x| (0..rows).any(|y| m.busy(x, y)))
        .fold((hi, lo), |(a, b), x| (a.min(x), b.max(x + 1)));
    let mid = if bx0 < bx1 { (bx0 + bx1) / 2 } else { cols / 2 };
    // Per row: where the left side ends and the right side starts.
    let edges: Vec<(u16, u16)> = (0..rows)
        .map(|y| {
            let l = (lo..hi).find(|&x| m.busy(x, y)).unwrap_or(mid).min(mid);
            let r = (lo..hi)
                .rev()
                .find(|&x| m.busy(x, y))
                .map_or(mid, |x| x + 1)
                .max(mid);
            (l, r)
        })
        .collect();
    let l0 = mid.saturating_sub(MAX_W).max(lo);
    let r1 = (mid + MAX_W).min(hi);
    let mut out = Vec::new();
    for (y, &(l, _)) in edges.iter().enumerate() {
        if l >= l0 + MIN_W {
            out.push(Slot {
                y: y as u16,
                x: l0,
                w: l - l0,
            });
        }
    }
    for (y, &(_, r)) in edges.iter().enumerate() {
        if r1 >= r + MIN_W {
            out.push(Slot {
                y: y as u16,
                x: r,
                w: r1 - r,
            });
        }
    }
    out
}

/// Where text can go when the picture sits on the right: one column from the left edge, top
/// to bottom, its right edge following the model's left outline row by row (straight, at the
/// model's leftmost column, in rows the model does not reach). At most LEFT_MAX wide.
pub fn left_slots(m: &Mask) -> Vec<Slot> {
    let (cols, rows) = (m.cols, m.rows);
    if cols < 3 {
        return Vec::new();
    }
    let (lo, hi) = (1u16, cols - 1);
    let bx0 = (lo..hi)
        .find(|&x| (0..rows).any(|y| m.busy(x, y)))
        .unwrap_or(hi);
    (0..rows)
        .filter_map(|y| {
            let l = (lo..hi)
                .find(|&x| m.busy(x, y))
                .unwrap_or(bx0)
                .min(lo + LEFT_MAX);
            (l >= lo + MIN_W).then_some(Slot {
                y,
                x: lo,
                w: l - lo,
            })
        })
        .collect()
}

/// A paragraph of the chat: its style, its text, and whether a blank row goes before it.
#[derive(Clone, Debug)]
pub struct Para {
    pub style: Style,
    pub text: String,
    pub gap: bool,
}

/// A line of text in a slot.
#[derive(Clone, Debug, PartialEq)]
pub struct Placed {
    pub slot: Slot,
    pub text: String,
    pub style: Style,
}

/// Lays `paras` into `slots` in order, word-wrapped; None when they do not all fit.
fn place(paras: &[Para], slots: &[Slot]) -> Option<Vec<Placed>> {
    let mut out = Vec::new();
    let mut i = 0usize;
    for (n, p) in paras.iter().enumerate() {
        if p.gap && n > 0 {
            i += 1;
        }
        if p.text.trim().is_empty() {
            continue;
        }
        let mut line = String::new();
        let mut words = p
            .text
            .split_whitespace()
            .map(str::to_string)
            .collect::<Vec<_>>();
        words.reverse();
        while let Some(word) = words.pop() {
            let slot = *slots.get(i)?;
            let w = slot.w as usize;
            let lw = line.width();
            let need = if line.is_empty() {
                word.width()
            } else {
                lw + 1 + word.width()
            };
            if need <= w {
                if !line.is_empty() {
                    line.push(' ');
                }
                line.push_str(&word);
                continue;
            }
            if line.is_empty() {
                // a word wider than the column: as much as fits, the rest goes on
                let (head, tail) = split_at_width(&word, w);
                line = head;
                if !tail.is_empty() {
                    words.push(tail);
                }
            } else {
                words.push(word);
            }
            out.push(Placed {
                slot,
                text: std::mem::take(&mut line),
                style: p.style,
            });
            i += 1;
        }
        if !line.is_empty() {
            let slot = *slots.get(i)?;
            out.push(Placed {
                slot,
                text: line,
                style: p.style,
            });
            i += 1;
        }
    }
    Some(out)
}

fn split_at_width(s: &str, w: usize) -> (String, String) {
    let mut head = String::new();
    let mut used = 0;
    let mut chars = s.chars().peekable();
    while let Some(&c) = chars.peek() {
        let cw = c.width().unwrap_or(0);
        if used + cw > w.max(1) {
            break;
        }
        used += cw;
        head.push(c);
        chars.next();
    }
    (head, chars.collect())
}

/// The whole chat word-wrapped into one `w`-wide column, blank rows kept: the rows
/// Z's read mode puts a cursor over.
pub fn column(paras: &[Para], w: u16) -> Vec<(String, Style)> {
    let w = w.max(4);
    let n: usize = paras
        .iter()
        .map(|p| p.text.width() / w as usize + 2 + p.text.split_whitespace().count())
        .sum::<usize>()
        + 1;
    let slots: Vec<Slot> = (0..n)
        .map(|y| Slot {
            y: y.min(u16::MAX as usize) as u16,
            x: 0,
            w,
        })
        .collect();
    let mut ps = paras.to_vec();
    if let Some(p) = ps.first_mut() {
        p.gap = false;
    }
    let placed = place(&ps, &slots).unwrap_or_default();
    let rows = placed.last().map_or(0, |p| p.slot.y as usize + 1);
    let mut out = vec![(String::new(), Style::default()); rows];
    for p in placed {
        out[p.slot.y as usize] = (p.text, p.style);
    }
    out
}

/// The newest text that fits: whole paragraphs from the latest back, and when even the last
/// one is too long, its end. `back` hides that many of the newest paragraphs (scrollback).
pub fn fit(paras: &[Para], slots: &[Slot], back: usize) -> Vec<Placed> {
    let end = paras.len().saturating_sub(back);
    let paras = &paras[..end];
    if paras.is_empty() || slots.is_empty() {
        return Vec::new();
    }
    let mut best = None;
    for start in (0..paras.len()).rev() {
        let mut ps = paras[start..].to_vec();
        ps[0].gap = false;
        match place(&ps, slots) {
            Some(p) => best = Some(p),
            None => break,
        }
    }
    if let Some(p) = best {
        return p;
    }
    // The last paragraph alone is too long: drop words off its front until it fits.
    let last = &paras[paras.len() - 1];
    let words: Vec<&str> = last.text.split_whitespace().collect();
    let try_from = |k: usize| {
        let p = Para {
            style: last.style,
            text: format!("… {}", words[k..].join(" ")),
            gap: false,
        };
        place(&[p], slots)
    };
    let (mut lo, mut hi) = (0usize, words.len());
    while lo < hi {
        let mid = (lo + hi) / 2;
        if try_from(mid).is_some() {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    try_from(lo).unwrap_or_default()
}

/// Writes the placed text into `buf` over `area`, then repairs the placeholders the text cut
/// in the image drawn at `img` (see the top of the file).
pub fn draw(buf: &mut Buffer, area: Rect, img: Rect, placed: &[Placed]) {
    // Read each image row's markers first: text may land on the row's first cell, the only
    // one that carries them (and, on the first row, the image upload itself).
    let rows = row_marks(buf, img);
    for p in placed {
        let (x, y) = (area.x + p.slot.x, area.y + p.slot.y);
        let w = p.text.width().min(p.slot.w as usize) as u16;
        for dx in 0..w {
            if let Some(c) = buf.cell_mut((x + dx, y)) {
                c.reset();
            }
        }
        buf.set_stringn(x, y, &p.text, p.slot.w as usize, p.style);
        // the diagram LSP: known terms underlined (`o` lists them)
        let cols: Vec<u16> = p
            .text
            .chars()
            .scan(0u16, |at, c| {
                let x = *at;
                *at += c.width().unwrap_or(0) as u16;
                Some(x)
            })
            .collect();
        for h in super::lsp::index().hits(&p.text) {
            for i in h.start..h.end {
                let dx = cols.get(i).copied().unwrap_or(u16::MAX);
                if dx < w {
                    if let Some(c) = buf.cell_mut((x + dx, y)) {
                        c.modifier.insert(ratatui::style::Modifier::UNDERLINED);
                    }
                }
            }
        }
    }
    fix_placeholders(buf, img, &rows);
}

/// What the first cell of an image row says: anything before the placeholder (the upload,
/// on the first frame), the row diacritic and the image-id diacritic.
struct RowMarks {
    upload: String,
    row: char,
    id: char,
}

fn row_marks(buf: &Buffer, img: Rect) -> Vec<Option<RowMarks>> {
    (img.top()..img.bottom())
        .map(|y| {
            let sym = buf.cell((img.x, y))?.symbol();
            let at = sym.find(PLACEHOLDER)?;
            let marks: Vec<char> = sym[at + PLACEHOLDER.len_utf8()..].chars().collect();
            Some(RowMarks {
                upload: sym[..at].to_string(),
                row: *marks.first()?,
                id: *marks.get(2)?,
            })
        })
        .collect()
}

/// Gives every image placeholder whose left neighbour is not one (the row's first cell
/// included, when text took the cells before it) its row, column and image diacritics, so
/// kitty does not count it as column 0. An upload whose cell text took moves to the next
/// placeholder still on screen.
fn fix_placeholders(buf: &mut Buffer, img: Rect, rows: &[Option<RowMarks>]) {
    let diacritic = |n: u16| DIACRITICS.chars().nth(n as usize);
    let mut upload = String::new();
    for (i, y) in (img.top()..img.bottom()).enumerate() {
        let Some(Some(m)) = rows.get(i) else {
            continue;
        };
        upload.push_str(&m.upload);
        let mut prev = false;
        for x in img.x..img.right() {
            let Some(cell) = buf.cell_mut((x, y)) else {
                continue;
            };
            let is = cell.symbol().contains(PLACEHOLDER);
            if is && (!prev || !upload.is_empty()) {
                if let Some(col) = diacritic(x - img.x) {
                    let mut s = std::mem::take(&mut upload);
                    s.extend([PLACEHOLDER, m.row, col, m.id]);
                    cell.set_symbol(&s);
                }
            }
            prev = is;
        }
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Role {
    User,
    Claude,
    Tool,
    Error,
}

/// One mode's conversation with headless Claude.
pub struct Talk {
    pub log: Vec<(Role, String)>,
    session: Option<String>,
    rx: Option<Receiver<Ev>>,
    child: Option<Child>,
    /// Where the conversation is kept between visits (None: not kept).
    file: Option<PathBuf>,
    /// `--model` for every turn (`/model`); None: Claude's default.
    pub model: Option<String>,
    /// Running totals over the kept conversation (`/usage`).
    pub usage: Usage,
    /// The sessions `/resume` listed last, so `/resume 2` picks one.
    picks: Vec<String>,
}

/// Cost and tokens summed over every turn of a conversation.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Usage {
    pub turns: u32,
    pub cost: f64,
    pub input: u64,
    pub output: u64,
}

/// Model names `/model` accepts as they are; anything else passes through to Claude.
const MODELS: &[&str] = &["opus", "sonnet", "haiku", "fable"];
/// How many past sessions `/resume` lists.
const RESUME_LIST: usize = 8;

impl Role {
    fn name(self) -> &'static str {
        match self {
            Role::User => "user",
            Role::Claude => "claude",
            Role::Tool => "tool",
            Role::Error => "error",
        }
    }
    fn from_name(s: &str) -> Option<Role> {
        [Role::User, Role::Claude, Role::Tool, Role::Error]
            .into_iter()
            .find(|r| r.name() == s)
    }
}

impl Talk {
    pub fn new() -> Self {
        Self {
            log: Vec::new(),
            session: None,
            rx: None,
            child: None,
            file: None,
            model: None,
            usage: Usage::default(),
            picks: Vec::new(),
        }
    }

    /// The conversation kept in `file`, picked up where it was left (the text, and Claude's
    /// session so it remembers too). A missing or unreadable file starts empty.
    pub fn kept(file: PathBuf) -> Self {
        // a reply still running since the screen closed comes back live
        if let Ok(mut away) = AWAY.lock() {
            if let Some(i) = away.iter().position(|t| t.file.as_ref() == Some(&file)) {
                return away.swap_remove(i);
            }
        }
        let mut t = Self::new();
        if let Some(v) = std::fs::read_to_string(&file)
            .ok()
            .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
        {
            t.session = v["session"].as_str().map(str::to_string);
            t.model = v["model"].as_str().map(str::to_string);
            let u = &v["usage"];
            t.usage = Usage {
                turns: u["turns"].as_u64().unwrap_or(0) as u32,
                cost: u["cost"].as_f64().unwrap_or(0.0),
                input: u["input"].as_u64().unwrap_or(0),
                output: u["output"].as_u64().unwrap_or(0),
            };
            t.log = v["log"]
                .as_array()
                .into_iter()
                .flatten()
                .filter_map(|e| {
                    Some((Role::from_name(e[0].as_str()?)?, e[1].as_str()?.to_string()))
                })
                .collect();
        }
        t.file = Some(file);
        t
    }

    /// Writes the conversation to its file, if it has one.
    fn save(&self) {
        let Some(f) = &self.file else { return };
        let log: Vec<serde_json::Value> = self
            .log
            .iter()
            .map(|(r, t)| serde_json::json!([r.name(), t]))
            .collect();
        let u = self.usage;
        let v = serde_json::json!({
            "session": self.session,
            "model": self.model,
            "usage": { "turns": u.turns, "cost": u.cost, "input": u.input, "output": u.output },
            "log": log,
        });
        let _ = std::fs::write(f, serde_json::to_string_pretty(&v).unwrap_or_default());
    }

    pub fn busy(&self) -> bool {
        self.rx.is_some()
    }

    /// Looks mid-reply, for tests; the sender feeds the reply.
    #[cfg(test)]
    pub fn fake_busy(&mut self) -> std::sync::mpsc::Sender<Ev> {
        let (tx, rx) = channel();
        self.rx = Some(rx);
        tx
    }

    /// Starts a turn: `claude -p` with the mode's system prompt and tools, resuming the
    /// conversation so far.
    pub fn send(&mut self, prompt: &str, system: &str, tools: &[String]) {
        self.send_shown(prompt, prompt, system, tools);
    }

    /// As `send`, but the chat shows `shown` while Claude gets `prompt` (an attached view's
    /// path stays out of the flowing text).
    pub fn send_shown(&mut self, shown: &str, prompt: &str, system: &str, tools: &[String]) {
        let prompt = prompt.trim();
        if prompt.is_empty() || self.busy() {
            return;
        }
        if self.command(prompt) {
            self.save();
            return;
        }
        self.log.push((Role::User, shown.trim().to_string()));
        self.save();
        let mut cmd = Command::new("claude");
        cmd.args([
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--append-system-prompt",
            system,
            "--allowedTools",
        ]);
        cmd.args(tools);
        if let Some(m) = &self.model {
            cmd.args(["--model", m]);
        }
        if let Some(s) = &self.session {
            cmd.args(["--resume", s]);
        }
        cmd.stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        let mut child = match cmd.spawn() {
            Ok(c) => c,
            Err(e) => {
                self.log
                    .push((Role::Error, format!("can't run claude: {e}")));
                return;
            }
        };
        let Some(stdout) = child.stdout.take() else {
            return;
        };
        let (tx, rx) = channel();
        std::thread::spawn(move || {
            for line in BufReader::new(stdout).lines().map_while(Result::ok) {
                for ev in parse_line(&line) {
                    if tx.send(ev).is_err() {
                        return;
                    }
                }
            }
            let _ = tx.send(Ev::Done);
        });
        self.child = Some(child);
        self.rx = Some(rx);
    }

    pub fn cancel(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
        if self.rx.take().is_some() {
            self.log.push((Role::Tool, "stopped".into()));
            self.save();
        }
    }

    /// Takes what Claude said since the last call; true when anything changed.
    pub fn poll(&mut self) -> bool {
        let mut evs = Vec::new();
        if let Some(rx) = &self.rx {
            loop {
                match rx.try_recv() {
                    Ok(ev) => evs.push(ev),
                    Err(TryRecvError::Empty) => break,
                    Err(TryRecvError::Disconnected) => {
                        evs.push(Ev::Done);
                        break;
                    }
                }
            }
        }
        let changed = !evs.is_empty();
        for ev in evs {
            self.apply(ev);
        }
        changed
    }

    pub fn apply(&mut self, ev: Ev) {
        match ev {
            Ev::Session(s) => {
                self.session = Some(s);
                self.register(None);
            }
            Ev::Message => {
                if let Some((Role::Claude, t)) = self.log.last_mut() {
                    if !t.is_empty() && !t.ends_with('\n') {
                        t.push_str("\n\n");
                    }
                }
            }
            Ev::Text(t) => {
                if self.log.last().is_none_or(|(r, _)| *r != Role::Claude) {
                    self.log.push((Role::Claude, String::new()));
                }
                if let Some((_, s)) = self.log.last_mut() {
                    s.push_str(&t);
                }
            }
            Ev::Tool(n) => {
                let n = short_tool(&n);
                match self.log.last_mut() {
                    Some((Role::Tool, t)) if t.starts_with('⚙') => {
                        if !t.ends_with(&n) {
                            t.push_str(&format!(" · {n}"));
                        }
                    }
                    _ => self.log.push((Role::Tool, format!("⚙ {n}"))),
                }
            }
            Ev::Failed(m) => self.log.push((Role::Error, m)),
            Ev::Usage {
                cost,
                input,
                output,
            } => {
                self.usage.turns += 1;
                self.usage.cost += cost;
                self.usage.input += input;
                self.usage.output += output;
                self.register(Some((cost, input, output)));
            }
            Ev::Done => {
                if let Some(mut c) = self.child.take() {
                    let _ = c.wait();
                }
                self.rx = None;
                self.save();
            }
        }
    }

    /// Records this chat in the shared registry (the `L` screen).
    fn register(&self, turn: Option<(f64, u64, u64)>) {
        let Some(session) = &self.session else { return };
        let mode = self
            .file
            .as_ref()
            .and_then(|f| f.file_stem())
            .map(|s| s.to_string_lossy().trim_start_matches(".chat-").to_string())
            .unwrap_or_else(|| "chat".into());
        let title = self
            .log
            .iter()
            .rev()
            .find(|(r, _)| *r == Role::User)
            .map(|(_, t)| t.as_str())
            .unwrap_or("");
        let file = self.file.as_ref().map(|f| f.to_string_lossy().into_owned());
        crate::chats::record(crate::chats::Note {
            session,
            source: &format!("z:{mode}"),
            title,
            model: self.model.as_deref(),
            file: file.as_deref(),
            turn,
        });
    }

    /// Runs a Z slash command (`/model`, `/resume`, `/usage`, `/new`, `/help`) on the spot
    /// instead of sending it to Claude, which can't run slash commands headless. False
    /// when `line` is not one, so it goes to Claude as typed.
    pub fn command(&mut self, line: &str) -> bool {
        let mut words = line.split_whitespace();
        let name = words.next().unwrap_or("");
        let arg = words.next();
        let say = |t: &mut Self, s: String| t.log.push((Role::Tool, s));
        match name {
            "/model" => match arg {
                None => {
                    let m = self.model.as_deref().unwrap_or("default").to_string();
                    say(self, format!("model: {m} · /model {} · /model default", MODELS.join("|")));
                }
                Some("default") => {
                    self.model = None;
                    say(self, "model: default".into());
                }
                Some(m) => {
                    self.model = Some(m.to_string());
                    say(self, format!("model: {m} (from the next turn)"));
                }
            },
            "/usage" => {
                let u = self.usage;
                say(
                    self,
                    format!(
                        "usage: {} turns · ${:.2} · {} in · {} out · model {}",
                        u.turns,
                        u.cost,
                        tokens(u.input),
                        tokens(u.output),
                        self.model.as_deref().unwrap_or("default"),
                    ),
                );
            }
            "/new" | "/clear" => {
                self.session = None;
                self.log.clear();
                self.usage = Usage::default();
                say(self, "new conversation".into());
            }
            "/resume" => self.resume(arg),
            "/help" => say(
                self,
                "/model [name] · /resume [n|id] · /usage · /new · /help".into(),
            ),
            _ => return false,
        }
        true
    }

    /// `/resume`: no argument lists this folder's latest Claude sessions; a number picks
    /// one from that list, a session id picks that session.
    fn resume(&mut self, arg: Option<&str>) {
        let pick = match arg {
            Some(a) => a
                .parse::<usize>()
                .ok()
                .and_then(|n| self.picks.get(n.wrapping_sub(1)).cloned())
                .or_else(|| {
                    super::claude_history::valid_session_id(a).then(|| a.to_string())
                }),
            None => None,
        };
        if let Some(id) = pick {
            self.session = Some(id.clone());
            self.log
                .push((Role::Tool, format!("resumed {}", &id[..id.len().min(8)])));
            return;
        }
        if arg.is_some() {
            self.log.push((Role::Error, "no such session; /resume to list".into()));
            return;
        }
        let here = std::env::current_dir().unwrap_or_default();
        let here = here.to_string_lossy();
        let mut found = super::claude_history::list_sessions(&super::claude_history::projects_dir());
        let mut lines = Vec::new();
        self.picks.clear();
        for s in found.iter_mut() {
            if self.picks.len() >= RESUME_LIST {
                break;
            }
            s.load();
            if s.cwd != here || s.prompt.is_empty() {
                continue;
            }
            self.picks.push(s.id.clone());
            let p: String = s.prompt.chars().take(60).collect();
            lines.push(format!("{}. {p}", self.picks.len()));
        }
        if lines.is_empty() {
            self.log.push((Role::Tool, "no sessions in this folder".into()));
        } else {
            lines.push("/resume <n> to pick".into());
            self.log.push((Role::Tool, lines.join("\n")));
        }
    }

    /// The conversation as paragraphs, markdown taken out.
    pub fn paras(&self, t: &Theme) -> Vec<Para> {
        let mut out = Vec::new();
        for (role, body) in &self.log {
            match role {
                Role::User => out.push(Para {
                    style: t.accent(),
                    text: format!("› {body}"),
                    gap: true,
                }),
                Role::Claude => {
                    let mut gap = true;
                    let mut fence = false;
                    for line in body.lines() {
                        if line.trim_start().starts_with("```") {
                            fence = !fence;
                            continue;
                        }
                        let text = if fence { line.to_string() } else { plain(line) };
                        if text.trim().is_empty() {
                            gap = true;
                            continue;
                        }
                        out.push(Para {
                            style: t.base(),
                            text,
                            gap,
                        });
                        gap = false;
                    }
                }
                Role::Tool => out.extend(body.lines().map(|l| Para {
                    style: t.dim(),
                    text: l.to_string(),
                    gap: false,
                })),
                Role::Error => out.push(Para {
                    style: t.down(),
                    text: format!("✗ {body}"),
                    gap: true,
                }),
            }
        }
        if self.busy() && !matches!(self.log.last(), Some((Role::Claude, _))) {
            out.push(Para {
                style: t.dim(),
                text: "…".into(),
                gap: false,
            });
        }
        out
    }
}

/// 12345 -> "12.3k".
fn tokens(n: u64) -> String {
    match n {
        n if n >= 1_000_000 => format!("{:.1}M", n as f64 / 1e6),
        n if n >= 1_000 => format!("{:.1}k", n as f64 / 1e3),
        n => n.to_string(),
    }
}

/// Replies that were still running when their screen closed. A thread keeps reading them
/// and saving to their files until they finish; `Talk::kept` takes one back.
static AWAY: Mutex<Vec<Talk>> = Mutex::new(Vec::new());

/// Keeps the replies in AWAY going until none is left.
fn tend_away() {
    std::thread::spawn(|| {
        loop {
            std::thread::sleep(Duration::from_millis(200));
            let Ok(mut away) = AWAY.lock() else { return };
            for t in away.iter_mut() {
                if t.poll() {
                    t.save();
                }
            }
            away.retain(Talk::busy);
            if away.is_empty() {
                return;
            }
        }
    });
}

impl Drop for Talk {
    fn drop(&mut self) {
        // leaving the screen mid-reply lets Claude finish in the background (kept talks only)
        if self.busy() && self.file.is_some() {
            let t = Talk {
                log: std::mem::take(&mut self.log),
                session: self.session.take(),
                rx: self.rx.take(),
                child: self.child.take(),
                file: self.file.take(),
                model: self.model.take(),
                usage: self.usage,
                picks: std::mem::take(&mut self.picks),
            };
            if let Ok(mut away) = AWAY.lock() {
                away.push(t);
            }
            tend_away();
            return;
        }
        // otherwise stop it, keeping what Claude had said so far
        if let Some(mut c) = self.child.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
        self.save();
    }
}

/// `mcp__x__y` as `y`; built-in tool names as they are.
fn short_tool(n: &str) -> String {
    n.rsplit("__").next().unwrap_or(n).to_string()
}

/// One line of markdown as plain text: no heading marks, emphasis or backticks; bullets as •.
fn plain(line: &str) -> String {
    let t = line.trim_start();
    let t = t.trim_start_matches('#').trim_start();
    let t = if let Some(rest) = t.strip_prefix("- ").or_else(|| t.strip_prefix("* ")) {
        format!("• {rest}")
    } else {
        t.to_string()
    };
    t.replace("**", "").replace("__", "").replace('`', "")
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::style::Style;

    fn mask(rows: &[&str]) -> Mask {
        let mut m = Mask::free(rows[0].len() as u16, rows.len() as u16);
        for (y, r) in rows.iter().enumerate() {
            for (x, c) in r.chars().enumerate() {
                if c == '#' {
                    m.set(x as u16, y as u16);
                }
            }
        }
        m
    }

    fn para(s: &str) -> Para {
        Para {
            style: Style::default(),
            text: s.into(),
            gap: false,
        }
    }

    #[test]
    fn slots_read_down_the_left_then_down_the_right_hugging_the_picture() {
        let m = mask(&[
            "........................................",
            "...............########.................",
            "................######..................",
            "........................................",
        ]);
        let s = slots(&m);
        // middle is column 19; the left column runs 1..19 above and below, 1..15/16 beside
        let left: Vec<Slot> = s.iter().copied().filter(|s| s.x == 1).collect();
        assert_eq!(
            left,
            [
                Slot { y: 0, x: 1, w: 18 },
                Slot { y: 1, x: 1, w: 14 },
                Slot { y: 2, x: 1, w: 15 },
                Slot { y: 3, x: 1, w: 18 },
            ]
        );
        // then the right column, top to bottom, its inner edge along the outline
        let right: Vec<Slot> = s[4..].to_vec();
        assert_eq!(
            right,
            [
                Slot { y: 0, x: 19, w: 20 },
                Slot { y: 1, x: 23, w: 16 },
                Slot { y: 2, x: 22, w: 17 },
                Slot { y: 3, x: 19, w: 20 },
            ]
        );
    }

    #[test]
    fn left_slots_follow_the_models_left_outline() {
        let m = mask(&[
            "........................................",
            "...............########.................",
            "...................####.................",
            "........................................",
        ]);
        let s = left_slots(&m);
        let widths: Vec<(u16, u16)> = s.iter().map(|s| (s.y, s.w)).collect();
        assert_eq!(widths, [(0, 14), (1, 14), (2, 18), (3, 14)]);
        assert!(s.iter().all(|s| s.x == 1));
        let moved = m.placed_in(50, 4, 10);
        assert!(moved.busy(25, 1) && !moved.busy(15, 1));
    }

    #[test]
    fn narrow_gutters_get_no_text() {
        let m = mask(&["....######################################.."]);
        assert!(slots(&m).is_empty());
    }

    #[test]
    fn the_newest_paragraphs_win_and_a_long_one_shows_its_end() {
        let s: Vec<Slot> = (0..2).map(|y| Slot { y, x: 0, w: 12 }).collect();
        let ps = [para("old words here"), para("new one"), para("newest")];
        let got = fit(&ps, &s, 0);
        let lines: Vec<&str> = got.iter().map(|p| p.text.as_str()).collect();
        assert_eq!(lines, ["new one", "newest"]);
        // scrollback hides the newest
        let got = fit(&ps, &s, 1);
        let lines: Vec<&str> = got.iter().map(|p| p.text.as_str()).collect();
        assert_eq!(lines, ["new one"], "the older one does not fit with it");
        let got = fit(&ps, &s, 2);
        let lines: Vec<&str> = got.iter().map(|p| p.text.as_str()).collect();
        assert_eq!(lines, ["old words", "here"]);
        // one paragraph too long for the space: its end, marked
        let long = [para("one two three four five six seven eight")];
        let got = fit(&long, &s, 0);
        let all: Vec<&str> = got.iter().map(|p| p.text.as_str()).collect();
        assert_eq!(all.last(), Some(&"seven eight"), "{all:?}");
        assert!(all[0].starts_with('…'), "{all:?}");
    }

    #[test]
    fn image_mask_marks_cells_with_picture_pixels_and_a_margin() {
        let bg = [10, 10, 10];
        let mut img = RgbaImage::from_pixel(40, 20, image::Rgba([10, 10, 10, 255]));
        // a 2x2-pixel blob per cell in cell (5, 2) with 4x4-pixel cells
        for (x, y) in [(20, 8), (21, 8), (20, 9), (21, 9)] {
            img.put_pixel(x, y, image::Rgba([200, 200, 200, 255]));
        }
        let m = image_mask(&img, (4.0, 4.0), 10, 5, bg);
        assert!(m.busy(5, 2) && m.busy(3, 2) && m.busy(7, 2) && m.busy(5, 1) && m.busy(5, 3));
        assert!(!m.busy(2, 2) && !m.busy(8, 2) && !m.busy(5, 0) && !m.busy(5, 4));
    }

    #[test]
    fn settle_grows_while_moving_and_resets_when_still() {
        let a = mask(&["##......"]);
        let b = mask(&["......##"]);
        let mut s = Settle::default();
        assert_eq!(s.update(&a, 1), &a);
        // camera moved: both old and new picture are avoided
        let both = s.update(&b, 2).clone();
        assert!(both.busy(0, 0) && both.busy(7, 0));
        assert!(s.pending());
        std::thread::sleep(SETTLE + Duration::from_millis(20));
        assert_eq!(s.update(&b, 2), &b);
        assert!(!s.pending());
    }

    #[test]
    fn text_after_a_cut_placeholder_row_gets_its_column() {
        let d: Vec<char> = DIACRITICS.chars().collect();
        assert_eq!(d.len(), 297);
        let area = Rect::new(0, 0, 6, 1);
        let mut buf = Buffer::empty(area);
        // as ratatui-image draws a row: diacritics only on the first cell
        let first: String = [PLACEHOLDER, d[0], d[0], d[0]].iter().collect();
        buf[(0, 0)].set_symbol(&first);
        for x in 1..6 {
            buf[(x, 0)].set_symbol(&PLACEHOLDER.to_string());
        }
        let slot = Slot { y: 0, x: 1, w: 2 };
        draw(
            &mut buf,
            area,
            area,
            &[Placed {
                slot,
                text: "hi".into(),
                style: Style::default(),
            }],
        );
        assert_eq!(buf[(1, 0)].symbol(), "h");
        let want: String = [PLACEHOLDER, d[0], d[3], d[0]].iter().collect();
        assert_eq!(buf[(3, 0)].symbol(), want, "column 3 says so explicitly");
        assert_eq!(
            buf[(4, 0)].symbol(),
            PLACEHOLDER.to_string(),
            "the rest count on"
        );

        // text over the row's first cell, which also held the upload: the first placeholder
        // left gets the row's diacritics and the upload
        let mut buf = Buffer::empty(area);
        let first: String = ['\x1b', '_', 'G', PLACEHOLDER, d[7], d[0], d[2]]
            .iter()
            .collect();
        buf[(0, 0)].set_symbol(&first);
        for x in 1..6 {
            buf[(x, 0)].set_symbol(&PLACEHOLDER.to_string());
        }
        let slot = Slot { y: 0, x: 0, w: 3 };
        draw(
            &mut buf,
            area,
            area,
            &[Placed {
                slot,
                text: "abc".into(),
                style: Style::default(),
            }],
        );
        let want: String = ['\x1b', '_', 'G', PLACEHOLDER, d[7], d[3], d[2]]
            .iter()
            .collect();
        assert_eq!(buf[(3, 0)].symbol(), want);
        assert_eq!(buf[(4, 0)].symbol(), PLACEHOLDER.to_string());
    }

    #[test]
    fn a_kept_conversation_comes_back_with_its_session() {
        let f = std::env::temp_dir().join(format!("fl-z-chat-{}.json", std::process::id()));
        let _ = std::fs::remove_file(&f);
        {
            let mut t = Talk::kept(f.clone());
            assert!(t.log.is_empty());
            t.log.push((Role::User, "why TSVs?".into()));
            t.apply(Ev::Session("abc".into()));
            t.apply(Ev::Text("Short wires.".into()));
            t.apply(Ev::Done);
        }
        let t = Talk::kept(f.clone());
        assert_eq!(t.session.as_deref(), Some("abc"));
        assert_eq!(
            t.log,
            [
                (Role::User, "why TSVs?".into()),
                (Role::Claude, "Short wires.".into())
            ]
        );
        let _ = std::fs::remove_file(&f);
    }

    #[test]
    fn markdown_comes_out_plain() {
        assert_eq!(plain("## A **bold** `x`"), "A bold x");
        assert_eq!(plain("- item"), "• item");
        let mut t = Talk::new();
        t.apply(Ev::Tool("Write".into()));
        t.apply(Ev::Tool("mcp__finlarp__sql".into()));
        t.apply(Ev::Text("Hello\n\nworld".into()));
        let ps = t.paras(&Theme::default());
        let texts: Vec<&str> = ps.iter().map(|p| p.text.as_str()).collect();
        assert_eq!(texts, ["⚙ Write · sql", "Hello", "world"]);
        assert!(ps[2].gap);
    }

    #[test]
    fn slash_commands_run_locally() {
        let mut t = Talk::new();
        assert!(t.command("/model sonnet"));
        assert_eq!(t.model.as_deref(), Some("sonnet"));
        assert!(t.command("/model default"));
        assert_eq!(t.model, None);
        t.apply(Ev::Usage { cost: 0.5, input: 1200, output: 30 });
        t.apply(Ev::Usage { cost: 0.25, input: 800, output: 20 });
        assert!(t.command("/usage"));
        let last = &t.log.last().unwrap().1;
        assert!(last.contains("2 turns") && last.contains("$0.75") && last.contains("2.0k in"), "{last}");
        assert!(t.command("/resume 3f2a9c1e-0000-0000-0000-000000000000"));
        assert_eq!(t.session.as_deref(), Some("3f2a9c1e-0000-0000-0000-000000000000"));
        assert!(t.command("/new"));
        assert_eq!(t.session, None);
        assert!(!t.command("/compact"));
        assert!(!t.command("why is HBM hot"));
    }
}
