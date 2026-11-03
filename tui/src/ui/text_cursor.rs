// A Neovim-style cursor and visual mode over any list of rendered rows.
//
// The owner lays its content out into rows (Vec<Line>), hands the cursor the
// rows' plain text with `set_rows`, forwards keys to `on_key`, and draws the
// visible window through `decorate`, which paints the cursor cell and the
// selection on top of the owner's own styling. The cursor owns scrolling
// (`top`), so the owner renders rows[top .. top + height].
//
//   normal    h j k l  w b e  W B E  0 ^ $  gh gl  gg G  H M L  { }  zz zt zb
//             f t F T {char}, ; and , to repeat
//             ^d ^u (half page)  ^f ^b / space (page)  ^e ^y (scroll view)
//             counts: 5j, 3w, 10G
//   visual    v (characters)  V (lines)  o (other end)  esc (leave)
//             text objects: iw aw iW aW ip ap (ip = the paragraph / table / list)
//             y  yank: on_key returns Outcome::Yank(text)
//
// `center` keeps the cursor row mid-window (stay_centered); otherwise the
// view scrolls only to keep `scrolloff` rows around the cursor.
//
// `skip_blank` makes every motion pass over empty rows (j/k go straight to
// the next line of text), for readers whose blank rows are only spacing.
//
// Yanked text is the selected cells with the common left margin removed and
// trailing spaces trimmed, so a centred reading column pastes flush left.
// Screens expose the selection through Screen::take_selection, which the app's
// `<space>y` chord copies to the clipboard.
//
// Columns are char indices into a row's text (rows are mostly single-width).

use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};

use crate::ui::help::{Key, key, section};
use crate::ui::theme::Theme;

/// Every binding the cursor understands, for a screen's `?` overlay
/// (chain it with the screen's own keys).
pub const KEYS: &[Key] = &[
    section("move"),
    key("h j k l", "left / down / up / right"),
    key("w b e", "next word / back / word end"),
    key("W B E", "same, by WORD (spaces only)"),
    key("0 ^ $", "line start / first char / line end"),
    key("gh gl", "first / last non-blank"),
    key("f t {c}", "jump to / before char in the line"),
    key("F T {c}", "same, backwards"),
    key("; ,", "repeat / reverse last f t"),
    key("gg G", "top / bottom (5G: row 5)"),
    key("H M L", "window top / middle / bottom"),
    key("{ }", "previous / next paragraph"),
    key("3j 2w …", "counts repeat a motion"),
    section("scroll"),
    key("^d ^u", "half page down / up"),
    key("^f ^b spc", "page down / up"),
    key("^e ^y", "scroll the view one line"),
    key("zz zt zb", "cursor line to centre / top / bottom"),
    section("select"),
    key("v V", "visual / visual line (again: leave)"),
    key("o", "jump to the other end"),
    key("iw aw", "select word (aw: + space)"),
    key("iW aW", "select WORD"),
    key("ip ap", "select paragraph / table / list"),
    key("y  spc y", "copy selection"),
    key("spc a c", "open Claude with the selection"),
    key("spc a s", "add selection to Claude"),
    key("esc", "leave visual mode"),
];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Normal,
    /// Character-wise (`v`).
    Visual,
    /// Line-wise (`V`).
    VisualLine,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Default)]
pub struct Pos {
    pub row: usize,
    pub col: usize,
}

/// What a key did.
#[derive(Debug, Clone, PartialEq)]
pub enum Outcome {
    /// The cursor used the key (moved, scrolled, changed mode).
    Handled,
    /// Not a cursor key: the owner should handle it.
    Unhandled,
    /// `y` in visual mode: the selected text (visual mode has ended).
    Yank(String),
}

#[derive(Debug, Clone)]
pub struct TextCursor {
    pub pos: Pos,
    /// First visible row.
    pub top: usize,
    /// Visible rows, from the owner's last draw.
    pub height: usize,
    pub mode: Mode,
    /// Other end of the selection in visual modes.
    anchor: Pos,
    /// Column j/k try to return to (vim's curswant).
    want: usize,
    count: Option<usize>,
    /// First key of a two-key command (g, z).
    prefix: Option<char>,
    /// Rows kept between the cursor and the window edge.
    pub scrolloff: usize,
    /// Never rest on a blank row (see module comment).
    pub skip_blank: bool,
    /// Keep the cursor row centred in the window.
    pub center: bool,
    /// Last f/t/F/T and its char, for ; and ,
    last_find: Option<(char, char)>,
    rows: Vec<Vec<char>>,
}

impl Default for TextCursor {
    fn default() -> Self {
        Self {
            pos: Pos::default(),
            top: 0,
            height: 1,
            mode: Mode::Normal,
            anchor: Pos::default(),
            want: 0,
            count: None,
            prefix: None,
            scrolloff: 8,
            skip_blank: false,
            center: false,
            last_find: None,
            rows: Vec::new(),
        }
    }
}

#[derive(Clone, Copy, PartialEq)]
enum Class {
    Space,
    Word,
    Punct,
}

fn class(c: char, big: bool) -> Class {
    if c.is_whitespace() {
        Class::Space
    } else if big || c.is_alphanumeric() || c == '_' {
        Class::Word
    } else {
        Class::Punct
    }
}

impl TextCursor {
    pub fn new() -> Self {
        Self::default()
    }

    /// A cursor that never rests on blank rows.
    pub fn skipping_blanks() -> Self {
        Self {
            skip_blank: true,
            ..Self::default()
        }
    }

    /// Keeps the cursor row centred (builder).
    pub fn centered(mut self) -> Self {
        self.center = true;
        self
    }

    /// Row `n` text rows away from `row` (blank rows don't count when
    /// skip_blank is on); stops at the last text row in that direction.
    fn step_rows(&self, row: usize, n: usize, down: bool) -> usize {
        if !self.skip_blank {
            return if down { row + n } else { row.saturating_sub(n) };
        }
        let mut r = row;
        let mut left = n;
        let mut cand = row;
        while left > 0 {
            let next = if down { r + 1 } else { match r.checked_sub(1) { Some(x) => x, None => break } };
            if next >= self.rows.len() {
                break;
            }
            r = next;
            if !self.blank(r) {
                cand = r;
                left -= 1;
            }
        }
        cand
    }

    /// With skip_blank, moves off a blank row: onward in the direction of
    /// travel, else back. Keeps the wanted column.
    fn settle(&mut self, down: bool) {
        if !self.skip_blank || self.rows.is_empty() || !self.blank(self.pos.row) {
            return;
        }
        let row = self.pos.row;
        let fwd = (row + 1..self.rows.len()).find(|r| !self.blank(*r));
        let back = (0..row).rev().find(|r| !self.blank(*r));
        let target = if down { fwd.or(back) } else { back.or(fwd) };
        if let Some(r) = target {
            self.pos.row = r;
            self.pos.col = self.want.min(self.last_col(r));
        }
    }

    /// Replaces the row text (after a layout). Clamps the cursor; the owner
    /// can `remap` first to keep it on the same content across a reflow.
    pub fn set_rows<S: AsRef<str>>(&mut self, rows: &[S]) {
        self.rows = rows.iter().map(|r| r.as_ref().chars().collect()).collect();
        self.pos = self.clamp(self.pos);
        self.anchor = self.clamp(self.anchor);
        self.top = self.top.min(self.max_top());
    }

    /// Plain text of rendered lines, for `set_rows`.
    pub fn line_text(line: &Line) -> String {
        line.spans.iter().map(|s| s.content.as_ref()).collect()
    }

    /// Moves cursor, anchor and view through `f` (old row -> new row), e.g.
    /// to the same block after the owner re-wraps at a new width.
    pub fn remap(&mut self, f: impl Fn(usize) -> usize) {
        self.pos.row = f(self.pos.row);
        self.anchor.row = f(self.anchor.row);
        self.top = f(self.top);
    }

    pub fn len(&self) -> usize {
        self.rows.len()
    }

    pub fn is_empty(&self) -> bool {
        self.rows.is_empty()
    }

    pub fn is_visual(&self) -> bool {
        self.mode != Mode::Normal
    }

    /// Call from draw with the body height before rendering rows.
    pub fn set_height(&mut self, h: usize) {
        self.height = h.max(1);
        self.follow();
    }

    pub fn max_top(&self) -> usize {
        self.rows.len().saturating_sub(self.height)
    }

    /// Visible row range for rendering.
    pub fn visible(&self) -> std::ops::Range<usize> {
        let end = (self.top + self.height).min(self.rows.len());
        self.top.min(end)..end
    }

    fn row_len(&self, row: usize) -> usize {
        self.rows.get(row).map_or(0, Vec::len)
    }

    fn last_col(&self, row: usize) -> usize {
        self.row_len(row).saturating_sub(1)
    }

    fn clamp(&self, p: Pos) -> Pos {
        if self.rows.is_empty() {
            return Pos::default();
        }
        let row = p.row.min(self.rows.len() - 1);
        Pos {
            row,
            col: p.col.min(self.last_col(row)),
        }
    }

    fn first_nonblank(&self, row: usize) -> usize {
        self.rows
            .get(row)
            .and_then(|r| r.iter().position(|c| !c.is_whitespace()))
            .unwrap_or(0)
    }

    /// Jumps the cursor to a row (first non-blank) and puts that row near the
    /// top of the window, for owner-driven jumps (headings, search matches).
    pub fn goto_row(&mut self, row: usize) {
        if self.rows.is_empty() {
            return;
        }
        let row = row.min(self.rows.len() - 1);
        self.pos = Pos {
            row,
            col: self.first_nonblank(row),
        };
        self.settle(true);
        self.pos.col = self.first_nonblank(self.pos.row);
        self.want = self.pos.col;
        self.top = if self.center {
            self.pos.row.saturating_sub(self.height / 2).min(self.max_top())
        } else {
            self.pos.row.saturating_sub(self.scrolloff.min(self.height / 3)).min(self.max_top())
        };
    }

    /// Scrolls the view, dragging the cursor along when it would leave it.
    pub fn scroll(&mut self, delta: isize) {
        self.top = (self.top as isize + delta).clamp(0, self.max_top() as isize) as usize;
        let lo = self.top + self.off();
        let hi = (self.top + self.height).saturating_sub(1 + self.off());
        if self.pos.row < lo && self.top > 0 {
            self.set_row(lo);
            self.settle(true);
        } else if self.pos.row > hi && self.top < self.max_top() {
            self.set_row(hi);
            self.settle(false);
        }
    }

    fn off(&self) -> usize {
        self.scrolloff.min(self.height.saturating_sub(1) / 2)
    }

    /// Keeps the cursor inside the window (with scrolloff).
    fn follow(&mut self) {
        if self.center {
            self.top = self.pos.row.saturating_sub(self.height / 2).min(self.max_top());
            return;
        }
        let off = self.off();
        if self.pos.row < self.top + off {
            self.top = self.pos.row.saturating_sub(off);
        } else if self.pos.row + off >= self.top + self.height {
            self.top = (self.pos.row + off + 1).saturating_sub(self.height);
        }
        self.top = self.top.min(self.max_top());
    }

    fn set_row(&mut self, row: usize) {
        if self.rows.is_empty() {
            return;
        }
        self.pos.row = row.min(self.rows.len() - 1);
        self.pos.col = self.want.min(self.last_col(self.pos.row));
    }

    fn set_col(&mut self, col: usize) {
        self.pos.col = col.min(self.last_col(self.pos.row));
        self.want = self.pos.col;
    }

    fn char_at(&self, p: Pos) -> Option<char> {
        self.rows.get(p.row)?.get(p.col).copied()
    }

    /// Next position in reading order (rows joined by a virtual newline,
    /// which counts as whitespace). None at the end.
    fn next(&self, p: Pos) -> Option<Pos> {
        if p.col + 1 < self.row_len(p.row) {
            Some(Pos { row: p.row, col: p.col + 1 })
        } else if p.row + 1 < self.rows.len() {
            Some(Pos { row: p.row + 1, col: 0 })
        } else {
            None
        }
    }

    fn prev(&self, p: Pos) -> Option<Pos> {
        if p.col > 0 {
            Some(Pos { row: p.row, col: p.col - 1 })
        } else if p.row > 0 {
            Some(Pos { row: p.row - 1, col: self.last_col(p.row - 1) })
        } else {
            None
        }
    }

    /// Class at p; empty rows and row ends read as whitespace.
    fn class_at(&self, p: Pos, big: bool) -> Class {
        self.char_at(p).map_or(Class::Space, |c| class(c, big))
    }

    fn word_forward(&self, p: Pos, big: bool) -> Pos {
        let start = self.class_at(p, big);
        let mut q = p;
        let mut row = p.row;
        // leave the current word
        while self.class_at(q, big) == start && start != Class::Space {
            match self.next(q) {
                Some(n) => q = n,
                None => return q,
            }
            if q.row != row {
                break;
            }
        }
        // skip whitespace (an empty row is a word stop, as in vim)
        loop {
            if q.row != row {
                row = q.row;
                if self.row_len(row) == 0 && !self.skip_blank {
                    return q;
                }
            }
            if self.class_at(q, big) != Class::Space {
                return q;
            }
            match self.next(q) {
                Some(n) => q = n,
                None => return q,
            }
        }
    }

    fn word_end(&self, p: Pos, big: bool) -> Pos {
        let mut q = match self.next(p) {
            Some(n) => n,
            None => return p,
        };
        while self.class_at(q, big) == Class::Space {
            match self.next(q) {
                Some(n) => q = n,
                None => return q,
            }
        }
        let c = self.class_at(q, big);
        while let Some(n) = self.next(q) {
            if n.row != q.row || self.class_at(n, big) != c {
                break;
            }
            q = n;
        }
        q
    }

    fn word_back(&self, p: Pos, big: bool) -> Pos {
        let mut q = match self.prev(p) {
            Some(n) => n,
            None => return p,
        };
        while self.class_at(q, big) == Class::Space {
            if self.row_len(q.row) == 0 && q.row != p.row && !self.skip_blank {
                return q;
            }
            match self.prev(q) {
                Some(n) => q = n,
                None => return q,
            }
        }
        let c = self.class_at(q, big);
        while let Some(n) = self.prev(q) {
            if n.row != q.row || self.class_at(n, big) != c {
                break;
            }
            q = n;
        }
        q
    }

    fn blank(&self, row: usize) -> bool {
        self.rows.get(row).is_none_or(|r| r.iter().all(|c| c.is_whitespace()))
    }

    /// `}`: next blank row after a non-blank run.
    fn paragraph_forward(&self, row: usize) -> usize {
        let n = self.rows.len();
        let mut r = row;
        while r + 1 < n && self.blank(r) {
            r += 1;
        }
        while r + 1 < n && !self.blank(r) {
            r += 1;
        }
        r
    }

    fn paragraph_back(&self, row: usize) -> usize {
        let mut r = row;
        while r > 0 && self.blank(r) {
            r -= 1;
        }
        while r > 0 && !self.blank(r) {
            r -= 1;
        }
        r
    }

    /// Ordered selection ends (inclusive), None in normal mode.
    pub fn selection(&self) -> Option<(Pos, Pos)> {
        if self.mode == Mode::Normal {
            return None;
        }
        let (a, b) = if self.anchor <= self.pos {
            (self.anchor, self.pos)
        } else {
            (self.pos, self.anchor)
        };
        Some(match self.mode {
            Mode::VisualLine => (
                Pos { row: a.row, col: 0 },
                Pos { row: b.row, col: usize::MAX },
            ),
            _ => (a, b),
        })
    }

    /// Selected text with the common left margin removed, or None.
    pub fn selected_text(&self) -> Option<String> {
        let (a, b) = self.selection()?;
        let mut lines: Vec<String> = Vec::new();
        for row in a.row..=b.row.min(self.rows.len().saturating_sub(1)) {
            let r = &self.rows[row];
            let from = if row == a.row { a.col.min(r.len()) } else { 0 };
            let to = if row == b.row { b.col.saturating_add(1).min(r.len()) } else { r.len() };
            let s: String = r[from..to.max(from)].iter().collect();
            lines.push(s.trim_end().to_string());
        }
        // Dedent: the reading column's margin isn't part of the text. A
        // char-wise selection's first line starts mid-row, so it's left alone.
        let skip_first = self.mode == Mode::Visual && a.col > self.first_nonblank(a.row);
        let margin = lines
            .iter()
            .enumerate()
            .filter(|(i, l)| !l.trim().is_empty() && !(skip_first && *i == 0))
            .map(|(_, l)| l.chars().take_while(|c| *c == ' ').count())
            .min()
            .unwrap_or(0);
        let out: Vec<String> = lines
            .iter()
            .enumerate()
            .map(|(i, l)| {
                if skip_first && i == 0 {
                    l.clone()
                } else {
                    l.chars().skip(margin.min(l.chars().take_while(|c| *c == ' ').count())).collect()
                }
            })
            .collect();
        let text = out.join("\n").trim_matches('\n').to_string();
        (!text.trim().is_empty()).then_some(text)
    }

    /// The selection as text, leaving visual mode (for `<space>y`).
    pub fn take_selection(&mut self) -> Option<String> {
        let text = self.selected_text();
        self.mode = Mode::Normal;
        text
    }

    /// Footer tag: "-- VISUAL --" etc., or a pending count/prefix.
    pub fn status(&self) -> Option<String> {
        let mode = match self.mode {
            Mode::Normal => None,
            Mode::Visual => Some("-- VISUAL --"),
            Mode::VisualLine => Some("-- VISUAL LINE --"),
        };
        let pending = match (self.count, self.prefix) {
            (Some(n), Some(p)) => Some(format!("{n}{p}")),
            (Some(n), None) => Some(n.to_string()),
            (None, Some(p)) => Some(p.to_string()),
            _ => None,
        };
        match (mode, pending) {
            (Some(m), Some(p)) => Some(format!("{m} {p}")),
            (Some(m), None) => Some(m.to_string()),
            (None, p) => p,
        }
    }

    /// Position in the document as "row:col".
    pub fn ruler(&self) -> String {
        format!("{}:{}", self.pos.row + 1, self.pos.col + 1)
    }

    fn last_nonblank(&self, row: usize) -> usize {
        self.rows
            .get(row)
            .and_then(|r| r.iter().rposition(|c| !c.is_whitespace()))
            .unwrap_or(0)
    }

    /// f/t/F/T: column of the n-th `ch` on the cursor row, if any.
    fn find(&self, kind: char, ch: char, n: usize, repeat: bool) -> Option<usize> {
        let row = self.rows.get(self.pos.row)?;
        let col = self.pos.col;
        let forward = matches!(kind, 'f' | 't');
        // ; after t/T must not stick on the char right next to the cursor
        let skip = usize::from(repeat && matches!(kind, 't' | 'T'));
        let mut hits = 0;
        if forward {
            for (i, c) in row.iter().enumerate().skip(col + 1 + skip) {
                if *c == ch {
                    hits += 1;
                    if hits == n {
                        return Some(if kind == 't' { i - 1 } else { i });
                    }
                }
            }
        } else {
            for i in (0..col.saturating_sub(skip)).rev() {
                if row[i] == ch {
                    hits += 1;
                    if hits == n {
                        return Some(if kind == 'T' { i + 1 } else { i });
                    }
                }
            }
        }
        None
    }

    /// iw/aw/iW/aW and ip/ap: sets the selection to the object at the cursor.
    fn text_object(&mut self, around: bool, obj: char) {
        let row = self.pos.row;
        match obj {
            'w' | 'W' => {
                let big = obj == 'W';
                let r = &self.rows[row];
                if r.is_empty() {
                    return;
                }
                let col = self.pos.col.min(r.len() - 1);
                let c = class(r[col], big);
                let mut a = col;
                while a > 0 && class(r[a - 1], big) == c {
                    a -= 1;
                }
                let mut b = col;
                while b + 1 < r.len() && class(r[b + 1], big) == c {
                    b += 1;
                }
                if around {
                    let before = b;
                    while b + 1 < r.len() && r[b + 1].is_whitespace() {
                        b += 1;
                    }
                    if b == before {
                        while a > 0 && r[a - 1].is_whitespace() {
                            a -= 1;
                        }
                    }
                }
                self.anchor = Pos { row, col: a };
                self.pos = Pos { row, col: b };
                self.mode = Mode::Visual;
            }
            'p' => {
                let mut a = row;
                while a > 0 && !self.blank(a - 1) {
                    a -= 1;
                }
                let mut b = row;
                while b + 1 < self.rows.len() && !self.blank(b + 1) {
                    b += 1;
                }
                if around {
                    while b + 1 < self.rows.len() && self.blank(b + 1) {
                        b += 1;
                    }
                }
                self.anchor = Pos { row: a, col: 0 };
                self.pos = Pos { row: b, col: self.last_col(b) };
                self.mode = Mode::VisualLine;
            }
            _ => return,
        }
        self.want = self.pos.col;
    }

    pub fn on_key(&mut self, key: KeyEvent) -> Outcome {
        if self.rows.is_empty() {
            return Outcome::Unhandled;
        }
        let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
        if key.modifiers.contains(KeyModifiers::ALT) {
            return Outcome::Unhandled;
        }
        let count = self.count.take();
        let n = count.unwrap_or(1);
        let before_row = self.pos.row;
        let half = (self.height / 2).max(1);

        if let Some(p) = self.prefix.take() {
            match (p, key.code) {
                ('g', KeyCode::Char('g')) => {
                    let row = count.map_or(0, |c| c.saturating_sub(1));
                    self.set_row(row);
                    self.set_col(self.first_nonblank(self.pos.row));
                }
                ('z', KeyCode::Char('z')) => {
                    self.top = self.pos.row.saturating_sub(self.height / 2).min(self.max_top());
                    return Outcome::Handled;
                }
                ('z', KeyCode::Char('t')) => {
                    self.top = self.pos.row.min(self.max_top());
                    return Outcome::Handled;
                }
                ('z', KeyCode::Char('b')) => {
                    self.top = (self.pos.row + 1).saturating_sub(self.height).min(self.max_top());
                    return Outcome::Handled;
                }
                ('g', KeyCode::Char('h')) => self.set_col(self.first_nonblank(self.pos.row)),
                ('g', KeyCode::Char('l')) => self.set_col(self.last_nonblank(self.pos.row)),
                (kind @ ('f' | 't' | 'F' | 'T'), KeyCode::Char(ch)) => {
                    self.last_find = Some((kind, ch));
                    if let Some(col) = self.find(kind, ch, count.unwrap_or(1), false) {
                        self.set_col(col);
                    }
                    return Outcome::Handled;
                }
                (side @ ('i' | 'a'), KeyCode::Char(obj @ ('w' | 'W' | 'p'))) => {
                    self.text_object(side == 'a', obj);
                    self.follow();
                    return Outcome::Handled;
                }
                _ => return Outcome::Handled, // unknown pair: swallow, like vim
            }
            self.settle(false);
            self.follow();
            return Outcome::Handled;
        }

        match key.code {
            KeyCode::Char(c @ '1'..='9') if !ctrl => {
                self.count = Some(count.unwrap_or(0) * 10 + c.to_digit(10).unwrap_or(0) as usize);
                return Outcome::Handled;
            }
            KeyCode::Char('0') if !ctrl && count.is_some() => {
                self.count = count.map(|c| c * 10);
                return Outcome::Handled;
            }
            KeyCode::Char(c @ ('g' | 'z' | 'f' | 't' | 'F' | 'T')) if !ctrl => {
                self.count = count;
                self.prefix = Some(c);
                return Outcome::Handled;
            }
            KeyCode::Char(c @ ('i' | 'a')) if !ctrl && self.is_visual() => {
                self.prefix = Some(c);
                return Outcome::Handled;
            }
            KeyCode::Char(c @ (';' | ',')) if !ctrl => {
                if let Some((kind, ch)) = self.last_find {
                    let kind = if c == ';' {
                        kind
                    } else {
                        match kind {
                            'f' => 'F',
                            'F' => 'f',
                            't' => 'T',
                            _ => 't',
                        }
                    };
                    if let Some(col) = self.find(kind, ch, n, true) {
                        self.set_col(col);
                    }
                }
                return Outcome::Handled;
            }
            KeyCode::Char('d') if ctrl => {
                self.scroll_with_cursor(half as isize);
                return Outcome::Handled;
            }
            KeyCode::Char('u') if ctrl => {
                self.scroll_with_cursor(-(half as isize));
                return Outcome::Handled;
            }
            KeyCode::Char('f') if ctrl => {
                self.scroll_with_cursor(self.height as isize);
                return Outcome::Handled;
            }
            KeyCode::Char('b') if ctrl => {
                self.scroll_with_cursor(-(self.height as isize));
                return Outcome::Handled;
            }
            KeyCode::Char(' ') | KeyCode::PageDown => {
                self.scroll_with_cursor(self.height as isize);
                return Outcome::Handled;
            }
            KeyCode::PageUp => {
                self.scroll_with_cursor(-(self.height as isize));
                return Outcome::Handled;
            }
            KeyCode::Char('e') if ctrl => {
                self.scroll(n as isize);
                return Outcome::Handled;
            }
            KeyCode::Char('y') if ctrl => {
                self.scroll(-(n as isize));
                return Outcome::Handled;
            }
            _ if ctrl => return Outcome::Unhandled,
            KeyCode::Char('j') | KeyCode::Down => self.set_row(self.step_rows(self.pos.row, n, true)),
            KeyCode::Char('k') | KeyCode::Up => self.set_row(self.step_rows(self.pos.row, n, false)),
            KeyCode::Char('h') | KeyCode::Left => self.set_col(self.pos.col.saturating_sub(n)),
            KeyCode::Char('l') | KeyCode::Right => self.set_col(self.pos.col + n),
            KeyCode::Char('0') | KeyCode::Home => self.set_col(0),
            KeyCode::Char('^') => self.set_col(self.first_nonblank(self.pos.row)),
            KeyCode::Char('$') | KeyCode::End => {
                self.pos.col = self.last_col(self.pos.row);
                self.want = usize::MAX;
            }
            KeyCode::Char(c @ ('w' | 'W' | 'b' | 'B' | 'e' | 'E')) => {
                let big = c.is_uppercase();
                for _ in 0..n {
                    self.pos = match c.to_ascii_lowercase() {
                        'w' => self.word_forward(self.pos, big),
                        'b' => self.word_back(self.pos, big),
                        _ => self.word_end(self.pos, big),
                    };
                }
                self.pos = self.clamp(self.pos);
                self.want = self.pos.col;
            }
            KeyCode::Char('G') => {
                let row = count.map_or(self.rows.len() - 1, |c| c.saturating_sub(1));
                self.set_row(row);
                self.set_col(self.first_nonblank(self.pos.row));
            }
            KeyCode::Char('H') => self.set_row(self.top + self.off()),
            KeyCode::Char('M') => {
                let shown = self.visible().len();
                self.set_row(self.top + shown / 2);
            }
            KeyCode::Char('L') => {
                let last = self.visible().end.saturating_sub(1);
                self.set_row(last.saturating_sub(self.off()).max(self.top));
            }
            KeyCode::Char('}') => {
                let mut r = self.pos.row;
                for _ in 0..n {
                    r = self.paragraph_forward(r);
                }
                self.set_row(r);
                self.set_col(0);
            }
            KeyCode::Char('{') => {
                let mut r = self.pos.row;
                for _ in 0..n {
                    r = self.paragraph_back(r);
                }
                self.set_row(r);
                self.set_col(0);
            }
            KeyCode::Char(c @ ('v' | 'V')) => {
                let want = if c == 'v' { Mode::Visual } else { Mode::VisualLine };
                if self.mode == Mode::Normal {
                    self.anchor = self.pos;
                }
                // same key leaves visual; the other key switches kind, keeping the selection
                self.mode = if self.mode == want { Mode::Normal } else { want };
            }
            KeyCode::Char('o') if self.is_visual() => {
                std::mem::swap(&mut self.anchor, &mut self.pos);
                self.want = self.pos.col;
            }
            KeyCode::Char('y') if self.is_visual() => {
                let text = self.take_selection();
                return text.map_or(Outcome::Handled, Outcome::Yank);
            }
            KeyCode::Esc if self.is_visual() => self.mode = Mode::Normal,
            KeyCode::Esc if count.is_some() => {}
            _ => {
                self.count = None;
                return Outcome::Unhandled;
            }
        }
        self.settle(self.pos.row >= before_row);
        self.follow();
        Outcome::Handled
    }

    fn scroll_with_cursor(&mut self, delta: isize) {
        if self.center {
            // cursor moves by the delta and the view recentres on it
            let row = (self.pos.row as isize + delta).clamp(0, self.rows.len() as isize - 1) as usize;
            self.set_row(row);
            self.settle(delta > 0);
            self.follow();
            return;
        }
        let before = self.top;
        self.top = (self.top as isize + delta).clamp(0, self.max_top() as isize) as usize;
        let moved = self.top as isize - before as isize;
        // Move the cursor by the same amount; at the ends, by the full delta.
        let step = if moved == 0 { delta } else { moved };
        let mut row = (self.pos.row as isize + step).clamp(0, self.rows.len() as isize - 1) as usize;
        // Keep scrolloff by nudging the cursor, not the view (the view moved
        // exactly one half page, as in vim).
        let off = self.off();
        let lo = if self.top > 0 { self.top + off } else { 0 };
        let hi = if self.top < self.max_top() {
            (self.top + self.height).saturating_sub(1 + off)
        } else {
            self.rows.len() - 1
        };
        row = row.clamp(lo.min(hi), hi);
        self.set_row(row);
        self.settle(delta > 0);
    }

    /// Paints the cursor cell and selection onto row `row` as drawn.
    pub fn decorate(&self, row: usize, line: Line<'static>, theme: &Theme) -> Line<'static> {
        let sel = self.selection().and_then(|(a, b)| {
            (a.row..=b.row).contains(&row).then(|| {
                let from = if row == a.row { a.col } else { 0 };
                let to = if row == b.row { b.col } else { usize::MAX };
                (from, to)
            })
        });
        let cursor = (row == self.pos.row).then_some(self.pos.col);
        if sel.is_none() && cursor.is_none() {
            return line;
        }
        let sel_style = |s: Style| theme.on_cursor(s);
        let cur_style = |s: Style| s.add_modifier(Modifier::REVERSED);
        let mut out: Vec<Span<'static>> = Vec::new();
        let mut idx = 0usize;
        let push = |text: String, style: Style, out: &mut Vec<Span<'static>>| {
            if text.is_empty() {
                return;
            }
            match out.last_mut() {
                Some(last) if last.style == style => {
                    let mut s = last.content.to_string();
                    s.push_str(&text);
                    last.content = s.into();
                }
                _ => out.push(Span::styled(text, style)),
            }
        };
        let line_style = line.style;
        for span in &line.spans {
            let base = line_style.patch(span.style);
            for c in span.content.chars() {
                let mut st = base;
                if sel.is_some_and(|(f, t)| idx >= f && idx <= t) {
                    st = sel_style(st);
                }
                if cursor == Some(idx) {
                    st = cur_style(st);
                }
                push(c.to_string(), st, &mut out);
                idx += 1;
            }
        }
        // Cursor or selection past the text (blank rows, short rows): draw a cell.
        let len = idx;
        if let Some(c) = cursor.filter(|c| *c >= len) {
            let pad = " ".repeat(c - len);
            let st = sel.map_or(Style::default(), |_| sel_style(Style::default()));
            push(pad, st, &mut out);
            push(" ".into(), cur_style(Style::default()), &mut out);
        } else if sel.is_some_and(|(_, t)| t == usize::MAX) && len == 0 {
            push(" ".into(), sel_style(Style::default()), &mut out);
        }
        Line::from(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn k(c: char) -> KeyEvent {
        KeyEvent::new(KeyCode::Char(c), KeyModifiers::NONE)
    }

    fn ctrl(c: char) -> KeyEvent {
        KeyEvent::new(KeyCode::Char(c), KeyModifiers::CONTROL)
    }

    fn cur(rows: &[&str], height: usize) -> TextCursor {
        let mut t = TextCursor::new();
        t.set_rows(rows);
        t.set_height(height);
        t
    }

    fn keys(t: &mut TextCursor, s: &str) -> Outcome {
        let mut last = Outcome::Handled;
        for c in s.chars() {
            last = t.on_key(k(c));
        }
        last
    }

    #[test]
    fn hjkl_keep_the_wanted_column_and_clamp() {
        let mut t = cur(&["hello world", "hi", "", "another line"], 10);
        keys(&mut t, "$");
        assert_eq!(t.pos, Pos { row: 0, col: 10 });
        keys(&mut t, "j");
        assert_eq!(t.pos, Pos { row: 1, col: 1 }, "clamped to the short row");
        keys(&mut t, "jj");
        assert_eq!(t.pos, Pos { row: 3, col: 11 }, "$ sticks to the row end");
        keys(&mut t, "0");
        assert_eq!(t.pos.col, 0);
        keys(&mut t, "3l");
        assert_eq!(t.pos.col, 3);
        keys(&mut t, "gg");
        assert_eq!(t.pos.row, 0);
        keys(&mut t, "G");
        assert_eq!(t.pos.row, 3);
        keys(&mut t, "2G");
        assert_eq!(t.pos.row, 1);
    }

    #[test]
    fn word_motions_cross_rows_and_punctuation() {
        let mut t = cur(&["  Net revenue: $18.8 million", "up 85%"], 10);
        keys(&mut t, "^");
        assert_eq!(t.pos.col, 2);
        keys(&mut t, "w");
        assert_eq!(t.pos.col, 6, "revenue");
        keys(&mut t, "w");
        assert_eq!(t.pos.col, 13, ":");
        keys(&mut t, "W");
        assert_eq!(t.pos.col, 15, "$18.8 is one WORD");
        keys(&mut t, "w");
        assert_eq!(t.pos.col, 16, "but w stops after the $");
        keys(&mut t, "W");
        assert_eq!(t.pos.col, 21, "million");
        keys(&mut t, "w");
        assert_eq!(t.pos, Pos { row: 1, col: 0 }, "w wraps to the next row");
        keys(&mut t, "b");
        assert_eq!(t.pos, Pos { row: 0, col: 21 });
        keys(&mut t, "e");
        assert_eq!(t.pos, Pos { row: 0, col: 27 });
    }

    #[test]
    fn paragraphs_jump_between_blank_rows() {
        let mut t = cur(&["a", "b", "", "c", "d", "", "e"], 10);
        keys(&mut t, "}");
        assert_eq!(t.pos.row, 2);
        keys(&mut t, "}");
        assert_eq!(t.pos.row, 5);
        keys(&mut t, "{");
        assert_eq!(t.pos.row, 2);
    }

    #[test]
    fn skip_blank_never_rests_on_empty_rows() {
        let mut t = TextCursor::skipping_blanks();
        t.set_rows(&["  intro line", "", "  • first bullet", "    wraps here", "", "", "  • second"]);
        t.set_height(20);
        keys(&mut t, "^");
        keys(&mut t, "j");
        assert_eq!(t.pos, Pos { row: 2, col: 2 }, "j jumps the blank row");
        keys(&mut t, "j");
        assert_eq!(t.pos.row, 3);
        keys(&mut t, "j");
        assert_eq!(t.pos.row, 6, "two blank rows skipped");
        keys(&mut t, "j");
        assert_eq!(t.pos.row, 6, "nothing below: stay");
        keys(&mut t, "2k");
        assert_eq!(t.pos.row, 2, "counts count text rows");
        keys(&mut t, "gg}");
        assert_eq!(t.pos.row, 2, "}} lands on the next paragraph's text");
        keys(&mut t, "gg$w");
        assert_eq!(t.pos, Pos { row: 2, col: 2 }, "w passes the empty row");
        t.goto_row(4);
        assert_eq!(t.pos.row, 6, "jumps onto a blank row settle forward");
        // the default cursor still stops on blanks
        let mut plain = cur(&["a", "", "b"], 5);
        keys(&mut plain, "j");
        assert_eq!(plain.pos.row, 1);
    }

    #[test]
    fn gh_gl_and_find_char_motions() {
        let mut t = cur(&["   Net revenue: $18.8 million, up 85%.   "], 5);
        keys(&mut t, "gl");
        assert_eq!(t.pos.col, 37, "last non-blank");
        keys(&mut t, "gh");
        assert_eq!(t.pos.col, 3);
        keys(&mut t, "f$");
        assert_eq!(t.pos.col, 16);
        keys(&mut t, "t,");
        assert_eq!(t.pos.col, 28, "just before the comma");
        keys(&mut t, "0fe");
        assert_eq!(t.pos.col, 4);
        keys(&mut t, ";");
        assert_eq!(t.pos.col, 8, "; repeats f e");
        keys(&mut t, ",");
        assert_eq!(t.pos.col, 4, ", reverses it");
        keys(&mut t, "2;");
        assert_eq!(t.pos.col, 10, "counted repeat");
        keys(&mut t, "Fv");
        assert_eq!(t.pos.col, 9);
        keys(&mut t, "fz");
        assert_eq!(t.pos.col, 9, "no match: stay");
    }

    #[test]
    fn text_objects_select_words_and_paragraphs() {
        let mut t = cur(&["  intro text here", "", "  Revenue  $1,200", "  Cost       (300)", "", "  after"], 20);
        keys(&mut t, "^wviw");
        assert_eq!(t.selected_text().as_deref(), Some("text"));
        t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        keys(&mut t, "vaw");
        assert_eq!(t.selection().map(|(a, b)| (a.col, b.col)), Some((8, 12)), "aw takes the trailing space");
        t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        keys(&mut t, "jjviW");
        t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        keys(&mut t, "vip");
        assert_eq!(t.mode, Mode::VisualLine);
        assert_eq!(t.selected_text().as_deref(), Some("Revenue  $1,200\nCost       (300)"));
        t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        keys(&mut t, "vap");
        assert_eq!(t.selection().map(|(a, b)| (a.row, b.row)), Some((2, 4)), "ap takes the blank after");
        // i / a outside visual mode are the owner's keys
        t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE));
        assert_eq!(t.on_key(k('i')), Outcome::Unhandled);
    }

    #[test]
    fn center_recentres_on_jumps_and_half_pages() {
        let rows: Vec<String> = (0..100).map(|i| format!("row {i}")).collect();
        let mut t = TextCursor::new();
        t.center = true;
        t.set_rows(&rows);
        t.set_height(10);
        t.goto_row(50);
        assert_eq!((t.pos.row, t.top), (50, 45));
        t.on_key(ctrl('d'));
        assert_eq!((t.pos.row, t.top), (55, 50));
    }

    #[test]
    fn center_keeps_the_cursor_mid_window() {
        let rows: Vec<String> = (0..100).map(|i| format!("row {i}")).collect();
        let mut t = TextCursor::new();
        t.center = true;
        t.set_rows(&rows);
        t.set_height(10);
        keys(&mut t, "20j");
        assert_eq!(t.top, 15);
        keys(&mut t, "j");
        assert_eq!(t.top, 16, "every line move recentres");
        keys(&mut t, "gg");
        assert_eq!(t.top, 0, "clamped at the top");
    }

    #[test]
    fn view_follows_the_cursor_with_scrolloff() {
        let rows: Vec<String> = (0..100).map(|i| format!("row {i}")).collect();
        let mut t = TextCursor::new();
        t.scrolloff = 3;
        t.set_rows(&rows);
        t.set_height(10);
        keys(&mut t, "9j");
        assert_eq!(t.top, 3, "row 9 sits 3 rows above the bottom edge");
        t.on_key(ctrl('d'));
        assert_eq!((t.top, t.pos.row), (8, 14));
        t.on_key(ctrl('u'));
        assert_eq!((t.top, t.pos.row), (3, 9));
        keys(&mut t, "G");
        assert_eq!(t.top, 90);
        keys(&mut t, "gg");
        assert_eq!(t.top, 0);
        t.goto_row(50);
        assert_eq!((t.pos.row, t.top), (50, 47));
        keys(&mut t, "zz");
        assert_eq!(t.top, 45);
    }

    #[test]
    fn visual_yank_dedents_the_reading_margin() {
        let mut t = cur(&["    Revenue grew 85%.", "    Margins held.", "", "    Next."], 10);
        keys(&mut t, "^V");
        assert_eq!(t.status().as_deref(), Some("-- VISUAL LINE --"));
        keys(&mut t, "j");
        assert_eq!(keys(&mut t, "y"), Outcome::Yank("Revenue grew 85%.\nMargins held.".into()));
        assert_eq!(t.mode, Mode::Normal);

        // charwise, mid-row start, across rows
        keys(&mut t, "gg^w");
        keys(&mut t, "vje");
        assert_eq!(t.selected_text().as_deref(), Some("grew 85%.\nMargins held"));
        keys(&mut t, "o");
        assert_eq!(t.pos, Pos { row: 0, col: 12 }, "o swaps ends");
        assert_eq!(t.take_selection().as_deref(), Some("grew 85%.\nMargins held"));
        assert!(!t.is_visual());
        assert_eq!(t.take_selection(), None, "nothing selected in normal mode");
    }

    #[test]
    fn counts_prefixes_and_unhandled_keys() {
        let rows: Vec<String> = (0..30).map(|i| format!("r{i}")).collect();
        let mut t = TextCursor::new();
        t.set_rows(&rows);
        t.set_height(10);
        keys(&mut t, "12");
        assert_eq!(t.status().as_deref(), Some("12"));
        keys(&mut t, "j");
        assert_eq!(t.pos.row, 12);
        assert_eq!(t.on_key(k('q')), Outcome::Unhandled);
        assert_eq!(t.on_key(k('n')), Outcome::Unhandled);
        assert_eq!(t.on_key(KeyEvent::new(KeyCode::Esc, KeyModifiers::NONE)), Outcome::Unhandled);
        assert_eq!(t.on_key(k('y')), Outcome::Unhandled, "y outside visual is the owner's");
    }

    #[test]
    fn decorate_marks_cursor_and_selection_cells() {
        let th = Theme::default();
        let mut t = cur(&["abcdef"], 5);
        keys(&mut t, "lvll");
        let line = t.decorate(0, Line::from("abcdef"), &th);
        let text: String = line.spans.iter().map(|s| s.content.as_ref()).collect();
        assert_eq!(text, "abcdef", "decoration never changes the text");
        let cursor_span = line.spans.iter().find(|s| s.style.add_modifier.contains(Modifier::REVERSED)).expect("cursor");
        assert_eq!(cursor_span.content, "d");
        // a blank row still shows the cursor cell
        let mut t = cur(&[""], 5);
        t.pos = Pos { row: 0, col: 0 };
        let line = t.decorate(0, Line::default(), &th);
        assert_eq!(line.spans.len(), 1);
    }

    #[test]
    fn reflow_keeps_position_via_remap() {
        let mut t = cur(&["a", "b", "c", "d"], 3);
        keys(&mut t, "3j");
        t.remap(|r| r * 2);
        t.set_rows(&["a", "", "b", "", "c", "", "d", ""]);
        assert_eq!(t.pos.row, 6);
    }
}
