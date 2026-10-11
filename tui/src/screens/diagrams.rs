// `fl diagrams [name]`: explainer diagrams (chip fab, fiber optics, data
// center power and cooling) as box-drawing art, one tab each.
//
//   fl diagrams                 browse
//   fl diagrams fiber           open on the tab whose name starts with "fiber"
//   fl diagrams pdf [dir]       headless: write one PDF per diagram (default ./diagrams-pdf)
//
// The art lives in diagrams_art.rs as plain text; this file colours it by
// character class so the same lines draw in the TUI and in the PDF export.

use std::io;
use std::path::Path;
use std::process::Command;

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph, Widget, Wrap};

use super::diagrams_art::{DIAGRAMS, Diagram};
use super::diagrams_desc::{cards, describe, page_key, visual};
use super::diagrams_mol::{Mol, mol_for};
use super::diagrams_vis::{Placed, step as vis_step, visual_for};
use crate::app::{Action, Ctx, Screen};
use crate::ui::help::{Key, key, render_footer, render_overlay};
use crate::ui::text;
use crate::ui::theme::Theme;

const KEYS: &[Key] = &[
    key("h/l", "previous / next node"),
    key("j/k", "node below / above (scrolls if none)"),
    key("tab/S-tab", "next / previous node"),
    key("enter", "open selected node's page"),
    key("H/L, [/]", "previous / next diagram"),
    key("1-6", "jump to diagram"),
    key("g/G", "top / bottom"),
    key("?", "this help"),
    key("q", "back"),
];

/// Where the cursor is inside a detail card: atom grid, a pane's tab strip, or its text.
#[derive(Clone, Copy, PartialEq)]
enum Focus {
    Grid,
    Tabs,
    Text,
    Visual,
}

pub struct Diagrams {
    theme: Theme,
    tab: usize,
    scroll: u16,
    body_h: u16,
    help: bool,
    nodes: Vec<Vec<Node>>,
    sel: usize,
    popup: bool,
    popup_scroll: u16,
    hots: Vec<Hot>,
    hsel: usize,
    hot_moved: bool,
    detail: bool,
    /// Detail card sections (`# heading` split), tab, scroll and cursor.
    secs: Vec<(&'static str, &'static str)>,
    ptab: usize,
    pscroll: u16,
    /// Cursor row (wrapped line) in the text.
    pcur: u16,
    focus: Focus,
    /// Selected spot in the right-hand visual.
    vcur: usize,
    /// First visible row of the right-hand visual (J/K, follows the cursor).
    vscroll: u16,
    mol: Option<Mol>,
    /// New-template card (big top visual + sub sections), when one exists.
    card: Option<&'static super::diagrams_cards::Card>,
    mol_cur: usize,
}

/// A selectable spot on a node's page; (row, col) index the page art.
struct Hot {
    row: u16,
    col: u16,
    len: u16,
    label: &'static str,
    body: &'static str,
}

fn find_hots(label: &str) -> Vec<Hot> {
    let Some(art) = visual(label) else {
        return Vec::new();
    };
    let lines: Vec<&str> = art.lines().collect();
    let mut out: Vec<Hot> = cards(label)
        .into_iter()
        .filter_map(|c| {
            let row = match c.line {
                Some(n) => n
                    .checked_sub(1)
                    .filter(|&r| lines.get(r).is_some_and(|l| l.contains(c.label)))?,
                None => lines.iter().position(|l| l.contains(c.label))?,
            };
            let byte = lines[row].find(c.label)?;
            Some(Hot {
                row: row as u16,
                col: lines[row][..byte].chars().count() as u16,
                len: c.label.chars().count() as u16,
                label: c.label,
                body: c.body,
            })
        })
        .collect();
    out.sort_by_key(|h| (h.row, h.col));
    out
}

/// Greedy word wrap to `width` columns.
fn wrap_words(text: &str, width: usize) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for w in text.split_whitespace() {
        if !cur.is_empty() && text::width(&cur) + 1 + text::width(w) > width {
            out.push(std::mem::take(&mut cur));
        }
        if !cur.is_empty() {
            cur.push(' ');
        }
        cur.push_str(w);
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

/// A selectable box in the art: top-left cell, size, and its first label line.
struct Node {
    row: u16,
    col: u16,
    w: u16,
    h: u16,
    label: String,
}

/// Finds `┌─┐ / │ text │ / └─┘` boxes, plus `┌── text ──┘` banner lines.
fn find_nodes(art: &str) -> Vec<Node> {
    let g: Vec<Vec<char>> = art.lines().map(|l| l.chars().collect()).collect();
    let at = |r: usize, c: usize| g.get(r).and_then(|l| l.get(c)).copied().unwrap_or(' ');
    let mut out = Vec::new();
    for (r, line) in g.iter().enumerate() {
        for (c, &ch) in line.iter().enumerate() {
            if ch != '\u{250C}' {
                continue;
            }
            let mut x = c + 1;
            while x < line.len()
                && !matches!(at(r, x), '\u{2510}' | '\u{2518}' | '\u{250C}' | '\u{2502}')
            {
                x += 1;
            }
            match at(r, x) {
                '\u{2510}' if (c + 1..x).all(|i| at(r, i) == '\u{2500}') => {
                    let mut y = r + 1;
                    while at(y, c) == '\u{2502}' && at(y, x) == '\u{2502}' {
                        y += 1;
                    }
                    if y > r + 1 && at(y, c) == '\u{2514}' && at(y, x) == '\u{2518}' {
                        let label: String = (c + 1..x).map(|i| at(r + 1, i)).collect();
                        out.push(Node {
                            row: r as u16,
                            col: c as u16,
                            w: (x - c + 1) as u16,
                            h: (y - r + 1) as u16,
                            label: label.trim().to_string(),
                        });
                    }
                }
                '\u{2518}' => {
                    let label: String = (c + 1..x)
                        .map(|i| at(r, i))
                        .filter(|&ch| ch != '\u{2500}')
                        .collect();
                    if !label.trim().is_empty() {
                        out.push(Node {
                            row: r as u16,
                            col: c as u16,
                            w: (x - c + 1) as u16,
                            h: 1,
                            label: label.trim().to_string(),
                        });
                    }
                }
                _ => {}
            }
        }
    }
    out.sort_by_key(|n| (n.row, n.col));
    out
}

/// Splits a card body on `# heading` lines; text before the first heading is
/// an "overview" section. Always returns at least one section.
fn sections(body: &'static str) -> Vec<(&'static str, &'static str)> {
    let mut heads: Vec<(usize, usize, &'static str)> = Vec::new();
    let mut off = 0;
    for line in body.split_inclusive('\n') {
        if let Some(title) = line.trim_end().strip_prefix("# ") {
            heads.push((off, off + line.len(), title.trim()));
        }
        off += line.len();
    }
    let mut out = Vec::new();
    let first = heads.first().map_or(body.len(), |h| h.0);
    if heads.is_empty() || !body[..first].trim().is_empty() {
        out.push(("overview", body[..first].trim()));
    }
    for (i, &(_, end, title)) in heads.iter().enumerate() {
        let next = heads.get(i + 1).map_or(body.len(), |h| h.0);
        out.push((title, body[end..next].trim()));
    }
    out
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Diagrams> {
    let tab = arg
        .as_deref()
        .map(str::to_lowercase)
        .and_then(|a| {
            DIAGRAMS
                .iter()
                .position(|d| d.tab.to_lowercase().starts_with(&a))
        })
        .unwrap_or(0);
    Ok(Diagrams {
        theme: ctx.theme,
        tab,
        scroll: 0,
        body_h: 0,
        help: false,
        nodes: DIAGRAMS.iter().map(|d| find_nodes(d.art)).collect(),
        sel: 0,
        popup: false,
        popup_scroll: 0,
        hots: Vec::new(),
        hsel: 0,
        hot_moved: false,
        detail: false,
        secs: Vec::new(),
        ptab: 0,
        pscroll: 0,
        pcur: 0,
        focus: Focus::Text,
        vcur: 0,
        vscroll: 0,
        mol: None,
        card: None,
        mol_cur: 0,
    })
}

fn class_style(c: char, in_note: bool, t: &Theme) -> Style {
    match c {
        _ if in_note => t.dim().add_modifier(Modifier::ITALIC),
        '\u{2500}'..='\u{257F}' => t.border(),
        '▶' | '▼' | '◀' | '▲' | '●' | '▓' | '≈' => t.accent(),
        '█' | '▌' => t.up(),
        _ => t.base(),
    }
}

/// Art -> styled lines. `# ` lines are section headings; `(...)` is a note.
fn styled_lines<'a>(art: &'a str, t: &Theme) -> Vec<Line<'a>> {
    art.lines()
        .map(|line| {
            if let Some(h) = line.strip_prefix("# ") {
                return Line::from(Span::styled(
                    format!("▎{h}"),
                    t.accent().add_modifier(Modifier::BOLD),
                ));
            }
            let mut spans: Vec<Span> = Vec::new();
            let (mut run, mut run_style) = (String::new(), t.base());
            let mut depth = 0u32;
            for c in line.chars() {
                if c == '(' {
                    depth += 1;
                }
                let style = class_style(c, depth > 0, t);
                if style != run_style && !run.is_empty() {
                    spans.push(Span::styled(std::mem::take(&mut run), run_style));
                }
                run_style = style;
                run.push(c);
                if c == ')' {
                    depth = depth.saturating_sub(1);
                }
            }
            if !run.is_empty() {
                spans.push(Span::styled(run, run_style));
            }
            Line::from(spans)
        })
        .collect()
}

fn art_size(d: &Diagram) -> (u16, u16) {
    let w = d.art.lines().map(text::width).max().unwrap_or(0);
    (w as u16, d.art.lines().count() as u16)
}

fn tab_line(sel: usize, t: &Theme) -> Line<'static> {
    let mut spans = vec![Span::raw(" ")];
    for (i, d) in DIAGRAMS.iter().enumerate() {
        let label = format!(" {} {} ", i + 1, d.tab);
        spans.push(if i == sel {
            Span::styled(label, t.selected().add_modifier(Modifier::BOLD))
        } else {
            Span::styled(label, t.dim())
        });
        spans.push(Span::raw(" "));
    }
    Line::from(spans)
}

impl Diagrams {
    fn goto(&mut self, tab: usize) {
        self.tab = tab % DIAGRAMS.len();
        self.scroll = 0;
        self.sel = 0;
    }

    fn step_node(&mut self, delta: isize) {
        let n = self.nodes[self.tab].len();
        if n == 0 {
            return;
        }
        self.sel = (self.sel as isize + delta).rem_euclid(n as isize) as usize;
        let node = &self.nodes[self.tab][self.sel];
        let (top, bot) = (node.row, node.row + node.h);
        if top < self.scroll {
            self.scroll = top;
        } else if bot > self.scroll + self.body_h {
            self.scroll = bot.saturating_sub(self.body_h);
        }
    }

    /// Moves the selection to the nearest node in the next row down (dir > 0)
    /// or up (dir < 0), closest by column; returns false when there is none.
    fn step_row(&mut self, dir: i32) -> bool {
        let nodes = &self.nodes[self.tab];
        let Some(cur) = nodes.get(self.sel) else {
            return false;
        };
        let best = nodes
            .iter()
            .enumerate()
            .filter(|(_, n)| {
                if dir > 0 {
                    n.row > cur.row
                } else {
                    n.row < cur.row
                }
            })
            .min_by_key(|(_, n)| (n.row.abs_diff(cur.row), n.col.abs_diff(cur.col)));
        match best {
            Some((i, _)) => {
                let delta = i as isize - self.sel as isize;
                self.step_node(delta);
                true
            }
            None => false,
        }
    }

    fn draw_selection(&self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(n) = self.nodes[self.tab].get(self.sel) else {
            return;
        };
        let buf = frame.buffer_mut();
        for dy in 0..n.h {
            let Some(y) = (n.row + dy).checked_sub(self.scroll) else {
                continue;
            };
            if y >= area.height {
                continue;
            }
            for dx in 0..n.w {
                let x = n.col + dx;
                if x < area.width {
                    buf[(area.x + x, area.y + y)].set_style(t.selected());
                }
            }
        }
    }

    fn step_hot(&mut self, delta: isize) {
        let n = self.hots.len();
        if n > 0 {
            self.hsel = (self.hsel as isize + delta).rem_euclid(n as isize) as usize;
            self.hot_moved = true;
        }
    }

    /// Nearest spot in the next row down/up (closest by column).
    fn step_hot_row(&mut self, dir: i32) -> bool {
        let Some(cur) = self.hots.get(self.hsel) else {
            return false;
        };
        let best = self
            .hots
            .iter()
            .enumerate()
            .filter(|(_, h)| {
                if dir > 0 {
                    h.row > cur.row
                } else {
                    h.row < cur.row
                }
            })
            .min_by_key(|(_, h)| (h.row.abs_diff(cur.row), h.col.abs_diff(cur.col)));
        match best {
            Some((i, _)) => {
                self.hsel = i;
                self.hot_moved = true;
                true
            }
            None => false,
        }
    }

    fn draw_popup(&mut self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(n) = self.nodes[self.tab].get(self.sel) else {
            return;
        };
        let text = describe(&n.label).unwrap_or("No description yet.");
        let art = visual(&n.label).unwrap_or("");
        let art_w = art.lines().map(text::width).max().unwrap_or(0) as u16;
        let w = (art_w + 6).max(70).min(area.width.saturating_sub(2));
        let r = Rect::new(
            area.x + area.width.saturating_sub(w) / 2,
            area.y + 1,
            w,
            area.height.saturating_sub(2).max(3),
        );
        let wrap_w = w.saturating_sub(4).max(1) as usize;
        let desc = wrap_words(text, wrap_w);
        let art_start = desc.len() as u16 + 1;
        let mut lines: Vec<Line> = desc
            .into_iter()
            .map(|l| Line::from(Span::styled(l, t.base())))
            .collect();
        lines.push(Line::default());
        lines.extend(styled_lines(art, t));
        let total = lines.len() as u16;
        let inner_h = r.height.saturating_sub(2);
        if self.hot_moved {
            if let Some(h) = self.hots.get(self.hsel) {
                let y = art_start + h.row;
                if y < self.popup_scroll {
                    self.popup_scroll = y.saturating_sub(2);
                } else if y >= self.popup_scroll + inner_h {
                    self.popup_scroll = (y + 3).saturating_sub(inner_h);
                }
            }
            self.hot_moved = false;
        }
        self.popup_scroll = self.popup_scroll.min(total.saturating_sub(inner_h));
        frame.render_widget(Clear, r);
        let hint = if self.hots.is_empty() {
            " j/k scroll  g/G top/bottom  q close "
        } else {
            " h/l/tab spot  j/k spot above/below  enter details  ctrl-d/u scroll  q close "
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(format!(" {} ", n.label), t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(
            Paragraph::new(lines)
                .style(t.base())
                .scroll((self.popup_scroll, 0))
                .block(block),
            r,
        );
        let buf = frame.buffer_mut();
        for (i, h) in self.hots.iter().enumerate() {
            let Some(y) = (art_start + h.row).checked_sub(self.popup_scroll) else {
                continue;
            };
            if y >= inner.height {
                continue;
            }
            let style = if i == self.hsel {
                t.selected().add_modifier(Modifier::BOLD)
            } else {
                t.accent().add_modifier(Modifier::UNDERLINED)
            };
            for dx in 0..h.len {
                let x = h.col + dx;
                if x < inner.width {
                    buf[(inner.x + x, inner.y + y)].set_style(style);
                }
            }
        }
        if self.detail {
            self.draw_detail(frame, area, t);
        }
    }

    fn draw_detail(&mut self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(h) = self.hots.get(self.hsel) else {
            return;
        };
        let r = area;
        let hint =
            " hjkl move (l into the visual)  J/K scroll visual  H/L section  space page  q back ";
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(format!(" {} ", h.label), t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(Clear, r);
        frame.render_widget(block, r);

        let ov = self.ptab == 0 && (self.card.is_some() || self.mol.is_some());
        let [tab_r, body] =
            Layout::vertical([Constraint::Length(2), Constraint::Min(1)]).areas(inner);
        let tabs: Vec<Span> = self
            .secs
            .iter()
            .enumerate()
            .map(|(i, (title, _))| {
                let label = format!(" {title} ");
                if i != self.ptab {
                    Span::styled(label, t.dim())
                } else if self.focus == Focus::Tabs {
                    Span::styled(label, t.selected().add_modifier(Modifier::BOLD))
                } else {
                    Span::styled(label, t.accent().add_modifier(Modifier::UNDERLINED))
                }
            })
            .collect();
        frame.render_widget(
            Paragraph::new(Line::from(tabs)).wrap(Wrap { trim: false }),
            tab_r,
        );

        // Overview tab: summary first, then the diagram (or atom grid) under it.
        if ov {
            if let Some(card) = self.card {
                let desc = wrap_words(card.desc, body.width.max(1) as usize);
                let mut lines: Vec<Line> = desc
                    .into_iter()
                    .map(|l| Line::from(Span::styled(l, t.base())))
                    .collect();
                lines.push(Line::default());
                lines.extend(styled_lines(card.top.art, t));
                let total = lines.len() as u16;
                self.vscroll = self.vscroll.min(total.saturating_sub(body.height));
                frame.render_widget(
                    Paragraph::new(lines)
                        .style(t.base())
                        .scroll((self.vscroll, 0)),
                    body,
                );
            } else if let Some(mol) = &self.mol {
                let mut head = vec![mol.formula_line(t), mol.mass_line(t), Line::default()];
                head.extend(mol.lines(
                    if self.focus == Focus::Grid {
                        self.mol_cur
                    } else {
                        usize::MAX
                    },
                    t,
                ));
                head.push(Line::default());
                let info = wrap_words(mol.atoms[self.mol_cur].info, body.width.max(1) as usize);
                for i in 0..4 {
                    head.push(Line::from(Span::styled(
                        info.get(i).cloned().unwrap_or_default(),
                        t.base(),
                    )));
                }
                frame.render_widget(Paragraph::new(head).style(t.base()), body);
            }
            return;
        }
        let body_full = body;

        // Left: section tabs + text with a line cursor. Right: that section's visual.
        let n = self.secs.len();
        let card = h.label;
        self.ptab = self.ptab.min(n.saturating_sub(1));
        let (sec_title, sec_text) = self.secs.get(self.ptab).copied().unwrap_or(("", ""));
        let page = self
            .nodes
            .get(self.tab)
            .and_then(|n| n.get(self.sel))
            .and_then(|n| page_key(&n.label))
            .unwrap_or("");
        let vis = match self.card {
            Some(c) => c.secs.get(self.ptab - 1).map(|s| s.vis),
            None => visual_for(page, card, sec_title),
        };
        const GAP: u16 = 3;
        let lw = if vis.is_some() && body.width >= 70 {
            body.width * 38 / 100
        } else {
            body.width
        };
        let body = body_full;
        let text_r = Rect::new(body.x, body.y, lw, body.height);
        let para = Paragraph::new(styled_lines(sec_text, t))
            .style(t.base())
            .wrap(Wrap { trim: false });
        let total = para.line_count(text_r.width) as u16;
        self.pcur = self.pcur.min(total.saturating_sub(1));
        // Keep the cursor row on screen.
        if self.pcur < self.pscroll {
            self.pscroll = self.pcur;
        } else if self.pcur >= self.pscroll + text_r.height {
            self.pscroll = self.pcur + 1 - text_r.height;
        }
        self.pscroll = self.pscroll.min(total.saturating_sub(text_r.height));
        frame.render_widget(para.scroll((self.pscroll, 0)), text_r);
        if self.focus == Focus::Text && text_r.height > 0 {
            let y = text_r.y + self.pcur - self.pscroll;
            let buf = frame.buffer_mut();
            for x in text_r.x..text_r.x + text_r.width {
                buf[(x, y)].set_style(t.selected());
            }
        }
        if let (Some(vis), true) = (&vis, lw < body.width) {
            let x = body.x + lw + GAP;
            let right = Rect::new(
                x,
                body.y,
                (body.x + body.width).saturating_sub(x),
                body.height,
            );
            let spots = vis.placed();
            self.vcur = self.vcur.min(spots.len().saturating_sub(1));
            let art_h = vis.art.lines().count() as u16;
            if self.focus == Focus::Visual {
                if let Some(sp) = spots.get(self.vcur) {
                    if sp.row < self.vscroll {
                        self.vscroll = sp.row;
                    } else if sp.row >= self.vscroll + right.height {
                        self.vscroll = sp.row + 1 - right.height;
                    }
                }
            }
            self.vscroll = self.vscroll.min(art_h.saturating_sub(right.height));
            let vs = self.vscroll;
            frame.render_widget(
                Paragraph::new(styled_lines(vis.art, t))
                    .style(t.base())
                    .scroll((vs, 0)),
                right,
            );
            let info_y = right.y + art_h.saturating_sub(vs).min(right.height) + 1;
            let info_h = (right.y + right.height).saturating_sub(info_y);
            if self.focus == Focus::Visual {
                let buf = frame.buffer_mut();
                for (i, sp) in spots.iter().enumerate() {
                    let style = if i == self.vcur {
                        t.selected().add_modifier(Modifier::BOLD)
                    } else {
                        t.accent().add_modifier(Modifier::UNDERLINED)
                    };
                    if sp.row < vs || sp.row - vs >= right.height {
                        continue;
                    }
                    for dx in 0..sp.len {
                        if sp.col + dx < right.width {
                            buf[(right.x + sp.col + dx, right.y + sp.row - vs)].set_style(style);
                        }
                    }
                }
                if let Some(sp) = spots.get(self.vcur) {
                    let lines: Vec<Line> = wrap_words(sp.info, right.width.max(1) as usize)
                        .into_iter()
                        .take(info_h as usize)
                        .map(|l| Line::from(Span::styled(l, t.base())))
                        .collect();
                    frame.render_widget(
                        Paragraph::new(lines),
                        Rect::new(right.x, info_y, right.width, info_h),
                    );
                }
            } else if !spots.is_empty() && info_h > 0 {
                frame.render_widget(
                    Paragraph::new(Span::styled("l to explore this visual", t.dim())),
                    Rect::new(right.x, info_y, right.width, 1),
                );
            }
        }
    }

    fn cur_visual(&self) -> Option<super::diagrams_vis::Visual> {
        if let Some(c) = self.card {
            return c.secs.get(self.ptab.checked_sub(1)?).map(|s| s.vis);
        }
        let card = self.hots.get(self.hsel)?.label;
        let page = page_key(&self.nodes.get(self.tab)?.get(self.sel)?.label)?;
        visual_for(page, card, self.secs.get(self.ptab)?.0)
    }

    /// Keys inside a detail card. The cursor walks atom grid -> tab strip ->
    /// text with j/k; h/l move along the tab strip or the atom grid.
    fn detail_key(&mut self, key: KeyEvent) {
        let n = self.secs.len().max(1);
        let spots: Vec<Placed> = self.cur_visual().map(|v| v.placed()).unwrap_or_default();
        let set_tab = |s: &mut Self, tab: usize| {
            s.ptab = tab;
            if tab > 0 && s.focus == Focus::Grid {
                s.focus = Focus::Tabs;
            } else if tab == 0 && s.focus != Focus::Grid {
                s.focus = Focus::Tabs;
            }
            s.vcur = 0;
            s.vscroll = 0;
            s.pcur = 0;
            s.pscroll = 0;
        };
        let (h, j, k, l) = (
            matches!(key.code, KeyCode::Char('h') | KeyCode::Left),
            matches!(key.code, KeyCode::Char('j') | KeyCode::Down),
            matches!(key.code, KeyCode::Char('k') | KeyCode::Up),
            matches!(key.code, KeyCode::Char('l') | KeyCode::Right),
        );
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => self.detail = false,
            KeyCode::Tab | KeyCode::Char('L') => set_tab(self, (self.ptab + 1) % n),
            KeyCode::BackTab | KeyCode::Char('H') => set_tab(self, (self.ptab + n - 1) % n),
            KeyCode::Char('J') => self.vscroll = self.vscroll.saturating_add(3),
            KeyCode::Char('K') => self.vscroll = self.vscroll.saturating_sub(3),
            KeyCode::Char(' ') | KeyCode::PageDown => self.pcur = self.pcur.saturating_add(8),
            KeyCode::PageUp => self.pcur = self.pcur.saturating_sub(8),
            _ => match self.focus {
                Focus::Grid => {
                    let Some(mol) = &self.mol else {
                        self.focus = Focus::Tabs;
                        return;
                    };
                    let (dx, dy) = (i32::from(l) - i32::from(h), i32::from(j) - i32::from(k));
                    let next = mol.step(self.mol_cur, dx, dy);
                    if j && next == self.mol_cur {
                        self.focus = Focus::Tabs;
                    } else {
                        self.mol_cur = next;
                    }
                }
                Focus::Tabs => {
                    if l {
                        set_tab(self, (self.ptab + 1).min(n - 1));
                    } else if h {
                        set_tab(self, self.ptab.saturating_sub(1));
                    } else if j {
                        if self.ptab > 0 || (self.card.is_none() && self.mol.is_none()) {
                            self.focus = Focus::Text;
                        }
                    } else if k && self.mol.is_some() && self.ptab == 0 {
                        self.focus = Focus::Grid;
                    }
                }
                Focus::Text => {
                    if j {
                        self.pcur = self.pcur.saturating_add(1);
                    } else if k {
                        if self.pcur == 0 {
                            self.focus = Focus::Tabs;
                        } else {
                            self.pcur -= 1;
                        }
                    } else if l && !spots.is_empty() {
                        self.focus = Focus::Visual;
                    }
                }
                Focus::Visual => {
                    let (dx, dy) = (i32::from(l) - i32::from(h), i32::from(j) - i32::from(k));
                    let next = vis_step(&spots, self.vcur, dx, dy);
                    if h && next == self.vcur {
                        self.focus = Focus::Text;
                    } else {
                        self.vcur = next;
                    }
                }
            },
        }
    }

    fn max_scroll(&self) -> u16 {
        // title + blank + footer rows are outside the body
        art_size(&DIAGRAMS[self.tab]).1.saturating_sub(self.body_h)
    }
}

impl Screen for Diagrams {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [tabs, title, body, tickers, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .areas(area);
        let d = &DIAGRAMS[self.tab];
        self.body_h = body.height;
        self.scroll = self.scroll.min(self.max_scroll());

        frame.render_widget(Paragraph::new(tab_line(self.tab, &t)), tabs);
        frame.render_widget(
            Paragraph::new(Line::from(Span::styled(format!(" {}", d.title), t.title()))),
            title,
        );
        let art_area = body.inner(ratatui::layout::Margin::new(1, 0));
        frame.render_widget(
            Paragraph::new(styled_lines(d.art, &t))
                .style(t.base())
                .scroll((self.scroll, 0)),
            art_area,
        );
        self.draw_selection(frame, art_area, &t);
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" related: ", t.dim()),
                Span::styled(d.tickers, t.accent()),
            ])),
            tickers,
        );
        render_footer(frame, foot, KEYS, None, &t);
        if self.popup {
            self.draw_popup(frame, area, &t);
        }
        if self.help {
            render_overlay(frame, area, "diagrams", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        if self.popup && self.detail {
            self.detail_key(key);
            return Action::None;
        }
        if self.popup {
            let half = (self.body_h / 2).max(1);
            let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
            match key.code {
                KeyCode::Char('q') | KeyCode::Esc => self.popup = false,
                KeyCode::Enter => {
                    if let Some(h) = self.hots.get(self.hsel) {
                        self.detail = true;
                        let page = self
                            .nodes
                            .get(self.tab)
                            .and_then(|n| n.get(self.sel))
                            .and_then(|n| page_key(&n.label))
                            .unwrap_or("");
                        self.card = super::diagrams_cards::find(page, h.label);
                        self.secs = match self.card {
                            Some(c) => c.secs.iter().map(|s| (s.title, s.text)).collect(),
                            None => sections(h.body),
                        };
                        let has_mol = self.card.is_none() && mol_for(h.label).is_some();
                        if self.card.is_some() || has_mol {
                            self.secs.insert(0, ("Overview", ""));
                        }
                        self.vscroll = 0;
                        self.ptab = 0;
                        self.pscroll = 0;
                        self.pcur = 0;
                        self.vcur = 0;
                        self.mol = if self.card.is_some() {
                            None
                        } else {
                            mol_for(h.label)
                        };
                        self.mol_cur = 0;
                        self.focus = if self.mol.is_some() {
                            Focus::Grid
                        } else if self.card.is_some() {
                            Focus::Tabs
                        } else {
                            Focus::Text
                        };
                    }
                }
                KeyCode::Char('l') | KeyCode::Right | KeyCode::Tab => self.step_hot(1),
                KeyCode::Char('h') | KeyCode::Left | KeyCode::BackTab => self.step_hot(-1),
                KeyCode::Char('j') | KeyCode::Down => {
                    if !self.step_hot_row(1) {
                        self.popup_scroll = self.popup_scroll.saturating_add(1)
                    }
                }
                KeyCode::Char('k') | KeyCode::Up => {
                    if !self.step_hot_row(-1) {
                        self.popup_scroll = self.popup_scroll.saturating_sub(1)
                    }
                }
                KeyCode::Char('d') if ctrl => {
                    self.popup_scroll = self.popup_scroll.saturating_add(half)
                }
                KeyCode::Char('u') if ctrl => {
                    self.popup_scroll = self.popup_scroll.saturating_sub(half)
                }
                KeyCode::PageDown | KeyCode::Char(' ') => {
                    self.popup_scroll = self.popup_scroll.saturating_add(half * 2)
                }
                KeyCode::PageUp => self.popup_scroll = self.popup_scroll.saturating_sub(half * 2),
                KeyCode::Char('g') | KeyCode::Home => self.popup_scroll = 0,
                KeyCode::Char('G') | KeyCode::End => self.popup_scroll = u16::MAX,
                _ => {}
            }
            return Action::None;
        }
        let half = (self.body_h / 2).max(1);
        if key.modifiers.contains(KeyModifiers::CONTROL) {
            match key.code {
                KeyCode::Char('d') => self.scroll = self.scroll.saturating_add(half),
                KeyCode::Char('u') => self.scroll = self.scroll.saturating_sub(half),
                _ => {}
            }
            return Action::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char('L') | KeyCode::Char(']') => self.goto(self.tab + 1),
            KeyCode::Char('H') | KeyCode::Char('[') => self.goto(self.tab + DIAGRAMS.len() - 1),
            KeyCode::Char('l') | KeyCode::Right | KeyCode::Tab => self.step_node(1),
            KeyCode::Char('h') | KeyCode::Left | KeyCode::BackTab => self.step_node(-1),
            KeyCode::Enter => {
                self.popup = !self.nodes[self.tab].is_empty();
                self.popup_scroll = 0;
                self.detail = false;
                self.hsel = 0;
                self.hots = self.nodes[self.tab]
                    .get(self.sel)
                    .map(|n| find_hots(&n.label))
                    .unwrap_or_default();
            }
            KeyCode::Char('j') | KeyCode::Down => {
                if !self.step_row(1) {
                    self.scroll = self.scroll.saturating_add(1)
                }
            }
            KeyCode::Char('k') | KeyCode::Up => {
                if !self.step_row(-1) {
                    self.scroll = self.scroll.saturating_sub(1)
                }
            }
            KeyCode::Char('g') | KeyCode::Home => self.scroll = 0,
            KeyCode::Char('G') | KeyCode::End => self.scroll = self.max_scroll(),
            KeyCode::Char(c @ '1'..='9') => {
                let i = c as usize - '1' as usize;
                if i < DIAGRAMS.len() {
                    self.goto(i);
                }
            }
            _ => {}
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        false
    }
}

// ---- PDF export ------------------------------------------------------

const CELL_W: f64 = 8.43;
const CELL_H: f64 = 17.0;
const PAGE_BG: &str = "#1e1f29";

fn hex(c: Color, fallback: &str) -> String {
    match c {
        Color::Rgb(r, g, b) => format!("#{r:02x}{g:02x}{b:02x}"),
        Color::White => "#e6e6e6".into(),
        Color::DarkGray => "#6b6f85".into(),
        Color::Gray => "#a0a3b5".into(),
        _ => fallback.into(),
    }
}

fn xml(c: char) -> String {
    match c {
        '&' => "&amp;".into(),
        '<' => "&lt;".into(),
        '>' => "&gt;".into(),
        _ => c.to_string(),
    }
}

/// (left, right, up, down) arms of a box-drawing char: 0 none, 1 light,
/// 2 double. Drawn as strokes because font corner glyphs do not line up
/// with their straight neighbours.
fn box_arms(c: char) -> Option<(u8, u8, u8, u8)> {
    Some(match c {
        '─' => (1, 1, 0, 0),
        '│' => (0, 0, 1, 1),
        '┌' => (0, 1, 0, 1),
        '┐' => (1, 0, 0, 1),
        '└' => (0, 1, 1, 0),
        '┘' => (1, 0, 1, 0),
        '├' => (0, 1, 1, 1),
        '┤' => (1, 0, 1, 1),
        '┬' => (1, 1, 0, 1),
        '┴' => (1, 1, 1, 0),
        '┼' => (1, 1, 1, 1),
        '═' => (2, 2, 0, 0),
        '║' => (0, 0, 2, 2),
        '╔' => (0, 2, 0, 2),
        '╗' => (2, 0, 0, 2),
        '╚' => (0, 2, 2, 0),
        '╝' => (2, 0, 2, 0),
        _ => return None,
    })
}

fn box_strokes(x: f64, y: f64, arms: (u8, u8, u8, u8), color: &str) -> String {
    let (cx, cy) = (x + CELL_W / 2.0, y + CELL_H / 2.0 - 1.0);
    let mut s = String::new();
    let mut seg = |kind: u8, dx: f64, dy: f64| {
        let offs: &[f64] = match kind {
            0 => return,
            1 => &[0.0],
            _ => &[-1.6, 1.6],
        };
        let (ex, ey) = (cx + dx * CELL_W / 2.0, cy + dy * CELL_H / 2.0);
        for o in offs {
            // perpendicular offset: horizontal arms shift in y, vertical in x
            let (ox, oy) = if dy == 0.0 { (0.0, *o) } else { (*o, 0.0) };
            s.push_str(&format!(
                "<line x1='{:.2}' y1='{:.2}' x2='{:.2}' y2='{:.2}' stroke='{color}' stroke-width='1.1'/>",
                cx + ox,
                cy + oy,
                ex + ox,
                ey + oy
            ));
        }
    };
    seg(arms.0, -1.0, 0.0);
    seg(arms.1, 1.0, 0.0);
    seg(arms.2, 0.0, -1.0);
    seg(arms.3, 0.0, 1.0);
    s
}

/// One cell per glyph at a fixed pitch; box lines are strokes.
fn buffer_to_svg(buf: &Buffer) -> String {
    let (w, h) = (buf.area.width, buf.area.height);
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' \
         font-family='Menlo, DejaVu Sans Mono, monospace' font-size='14'>\
         <rect width='100%' height='100%' fill='{PAGE_BG}'/>",
        f64::from(w) * CELL_W,
        f64::from(h) * CELL_H
    );
    for y in 0..h {
        for x in 0..w {
            let cell = &buf[(x, y)];
            let sym = cell.symbol();
            if sym.trim().is_empty() {
                continue;
            }
            if let Some(arms) = sym.chars().next().and_then(box_arms) {
                svg.push_str(&box_strokes(
                    f64::from(x) * CELL_W,
                    f64::from(y) * CELL_H,
                    arms,
                    &hex(cell.fg, "#6b6f85"),
                ));
                continue;
            }
            let weight = if cell.modifier.contains(Modifier::BOLD) {
                " font-weight='bold'"
            } else {
                ""
            };
            let slant = if cell.modifier.contains(Modifier::ITALIC) {
                " font-style='italic'"
            } else {
                ""
            };
            svg.push_str(&format!(
                "<text x='{:.2}' y='{:.2}' fill='{}'{weight}{slant}>{}</text>",
                f64::from(x) * CELL_W,
                f64::from(y) * CELL_H + CELL_H - 4.0,
                hex(cell.fg, "#e6e6e6"),
                sym.chars().map(xml).collect::<String>(),
            ));
        }
    }
    svg.push_str("</svg>");
    svg
}

fn render_page(d: &Diagram, t: &Theme) -> Buffer {
    let (aw, ah) = art_size(d);
    let area = Rect::new(0, 0, aw + 4, ah + 5);
    let mut buf = Buffer::empty(area);
    let [title, body, tickers] = Layout::vertical([
        Constraint::Length(2),
        Constraint::Min(1),
        Constraint::Length(1),
    ])
    .areas(area.inner(ratatui::layout::Margin::new(2, 1)));
    Paragraph::new(Line::from(Span::styled(d.title, t.title()))).render(title, &mut buf);
    Paragraph::new(styled_lines(d.art, t)).render(body, &mut buf);
    Paragraph::new(Line::from(vec![
        Span::styled("related: ", t.dim()),
        Span::styled(d.tickers, t.accent()),
        Span::styled("   finlarp diagrams", t.dim()),
    ]))
    .render(tickers, &mut buf);
    buf
}

/// Writes `<dir>/NN-<tab>.pdf` for every diagram via rsvg-convert. Returns
/// the paths written.
pub fn export_pdfs(dir: &Path, t: &Theme) -> io::Result<Vec<String>> {
    // white-on-dark theme colours need an explicit bg; default() has fg=White
    let mut t = *t;
    t.bg = None;
    std::fs::create_dir_all(dir)?;
    let mut out = Vec::new();
    for (i, d) in DIAGRAMS.iter().enumerate() {
        let slug: String = d
            .tab
            .to_lowercase()
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
            .collect();
        let svg_path = dir.join(format!("{:02}-{slug}.svg", i + 1));
        let pdf_path = dir.join(format!("{:02}-{slug}.pdf", i + 1));
        std::fs::write(&svg_path, buffer_to_svg(&render_page(d, &t)))?;
        let status = Command::new("rsvg-convert")
            .args(["-f", "pdf", "-o"])
            .arg(&pdf_path)
            .arg(&svg_path)
            .status()
            .map_err(|e| io::Error::other(format!("rsvg-convert (brew install librsvg): {e}")))?;
        if !status.success() {
            return Err(io::Error::other(format!("rsvg-convert failed on {slug}")));
        }
        out.push(pdf_path.display().to_string());
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_diagram_fits_a_sane_page() {
        for d in DIAGRAMS {
            let (w, h) = art_size(d);
            assert!(w <= 140, "{} is {w} cols wide", d.tab);
            assert!(h >= 10, "{} is only {h} rows", d.tab);
        }
    }

    #[test]
    fn open_matches_tab_prefix() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        assert_eq!(open(&ctx, Some("fib".into())).unwrap().tab, 3);
        assert_eq!(open(&ctx, Some("zzz".into())).unwrap().tab, 0);
    }

    #[test]
    fn fab_nodes_all_described() {
        let nodes = find_nodes(DIAGRAMS[0].art);
        let labels: Vec<_> = nodes.iter().map(|n| n.label.as_str()).collect();
        assert_eq!(nodes.len(), 20, "{labels:?}");
        for n in &nodes {
            assert!(describe(&n.label).is_some(), "no desc: {}", n.label);
            assert!(visual(&n.label).is_some(), "no page: {}", n.label);
            let hots = find_hots(&n.label);
            assert!(hots.len() >= 8, "{}: only {} hotspots", n.label, hots.len());
            assert_eq!(
                hots.len(),
                cards(&n.label).len(),
                "{}: card label missing from page",
                n.label
            );
            assert!(
                hots.iter().all(|h| h.body.len() > 150),
                "{}: short card",
                n.label
            );
        }
    }
}

#[cfg(test)]
mod section_tests {
    use super::sections;

    #[test]
    fn splits_on_headings() {
        let s = sections("intro\n\n# A\nbody a\n\n# B\nbody b\n");
        assert_eq!(
            s,
            vec![("overview", "intro"), ("A", "body a"), ("B", "body b")]
        );
        assert_eq!(sections("plain"), vec![("overview", "plain")]);
        assert_eq!(sections("# A\nx"), vec![("A", "x")]);
    }
}
