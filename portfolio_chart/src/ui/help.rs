// Key hints: a one-line footer and a `?` overlay listing every binding.
// Screens declare their keys once as a `&[Key]` and pass it to both.
//
//   Footer      widget: "j/k move  ↵ open  …" (keys accent, text dim); a
//               flash message replaces the hints while it's set
//   KeyOverlay  widget: centered popup table of every key (Clear behind)

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::layout::{Constraint, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Cell, Clear, Row, Table, Widget};

use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Clone, Copy)]
pub struct Key {
    pub keys: &'static str,
    pub desc: &'static str,
}

pub const fn key(keys: &'static str, desc: &'static str) -> Key {
    Key { keys, desc }
}

/// Keys every sourced screen shares (see ui::source_bar::source_action).
pub const SOURCE_KEYS: &[Key] = &[
    key("↵", "open source in browser"),
    key("v", "open source in nvim"),
    key("y", "copy source URL"),
    key("i", "inspect formula inputs"),
    key("a", "audit overlay"),
];

/// Movement keys understood by `block_view::BlockView::on_key`.
pub const BLOCK_KEYS: &[Key] = &[
    key("j/k", "next / previous item"),
    key("g/G", "first / last item"),
    key("^d/^u", "half page down / up"),
    key("tab/S-tab", "next / previous block"),
    key("h/l", "previous / next table column"),
];

/// Footer with as many hints as fit; `flash` (if any) takes priority.
pub fn render_footer(
    frame: &mut Frame,
    area: Rect,
    keys: &[Key],
    flash: Option<&str>,
    theme: &Theme,
) {
    frame.render_widget(Footer { keys, flash, theme }, area);
}

/// Full-screen overlay listing all keys (centered popup over `area`).
pub fn render_overlay(frame: &mut Frame, area: Rect, title: &str, keys: &[Key], theme: &Theme) {
    frame.render_widget(KeyOverlay { title, keys, theme }, area);
}

pub struct Footer<'a> {
    pub keys: &'a [Key],
    pub flash: Option<&'a str>,
    pub theme: &'a Theme,
}

impl Widget for Footer<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        (&self).render(area, buf);
    }
}

impl Widget for &Footer<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if area.is_empty() {
            return;
        }
        let w = area.width as usize;
        if let Some(msg) = self.flash.filter(|m| !m.is_empty()) {
            Line::styled(text::truncate(msg, w), th.accent()).render(area, buf);
            return;
        }
        // whole hints only: stop before one would be cut (screens list their
        // most important keys first, and put "? help" early to keep it visible)
        let mut spans: Vec<Span> = Vec::new();
        let mut used = 0;
        for k in self.keys {
            let hw = text::width(k.keys) + 1 + text::width(k.desc) + 2;
            if used + hw > w {
                break;
            }
            used += hw;
            spans.push(Span::styled(k.keys, th.accent()));
            spans.push(Span::styled(format!(" {}  ", k.desc), th.dim()));
        }
        Line::from(spans).render(area, buf);
    }
}

pub struct KeyOverlay<'a> {
    pub title: &'a str,
    pub keys: &'a [Key],
    pub theme: &'a Theme,
}

impl Widget for KeyOverlay<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        (&self).render(area, buf);
    }
}

impl Widget for &KeyOverlay<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        let kw = self
            .keys
            .iter()
            .map(|k| text::width(k.keys))
            .max()
            .unwrap_or(0) as u16;
        let dw = self
            .keys
            .iter()
            .map(|k| text::width(k.desc))
            .max()
            .unwrap_or(0) as u16;
        let tw = text::width(self.title) as u16 + 4;
        let width = (kw + dw + 2 + 4).max(tw).max(24);
        let height = self.keys.len() as u16 + 2;
        let r = crate::ui::layout::popup(area, width, height);
        if r.is_empty() {
            return;
        }
        Clear.render(r, buf);
        let rows = self.keys.iter().map(|k| {
            Row::new([
                Cell::from(Span::styled(k.keys, th.accent())),
                Cell::from(Span::styled(k.desc, th.base())),
            ])
        });
        let block = Block::bordered()
            .border_style(th.accent())
            .style(th.base())
            .title_top(Line::styled(format!(" {} ", self.title), th.title()))
            .title_bottom(
                Line::from(vec![
                    Span::styled(" ? ", th.accent()),
                    Span::styled("close ", th.dim()),
                ])
                .right_aligned(),
            );
        Table::new(rows, [Constraint::Length(kw), Constraint::Fill(1)])
            .column_spacing(2)
            .block(block)
            .render(r, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    const KEYS: &[Key] = &[
        key("j/k", "move"),
        key("↵", "open"),
        key("q", "quit"),
        key("?", "help"),
    ];

    fn draw(w: u16, h: u16, f: impl Fn(&mut Frame)) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|fr| f(fr)).unwrap();
        let b = t.backend().buffer();
        (0..h)
            .map(|y| {
                (0..w)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn footer_hints_and_flash() {
        let th = Theme::default();
        let out = draw(40, 1, |f| render_footer(f, f.area(), KEYS, None, &th));
        assert!(out.starts_with("j/k move  ↵ open  q quit  ? help"), "{out}");
        // only whole hints
        let out = draw(12, 1, |f| render_footer(f, f.area(), KEYS, None, &th));
        assert_eq!(out.trim_end(), "j/k move");
        let out = draw(40, 1, |f| {
            render_footer(f, f.area(), KEYS, Some("copied"), &th)
        });
        assert!(out.starts_with("copied"));
        assert!(!out.contains("move"));
    }

    #[test]
    fn overlay_lists_keys() {
        let th = Theme::default();
        let out = draw(60, 20, |f| {
            render_overlay(f, f.area(), "dossier keys", SOURCE_KEYS, &th)
        });
        assert!(out.contains("dossier keys"), "{out}");
        assert!(out.contains("i  inspect formula inputs"), "{out}");
        for (w, h) in [(10, 3), (1, 1), (0, 0)] {
            draw(w, h, |f| render_overlay(f, f.area(), "k", KEYS, &th));
            draw(w, h, |f| render_footer(f, f.area(), KEYS, Some("x"), &th));
            draw(w, h, |f| render_overlay(f, f.area(), "k", &[], &th));
        }
    }
}
