// Horizontal nav over model::Section: one row of tabs, for screens whose
// sections are few and short (CANSLIM's seven letters). The vertical
// SectionList is for long lists (dossier). Both share the selection index
// semantics so a screen can switch between them.
//
// Labels shrink to fit, widest first:
//   full    " C Current earnings  C 59 "
//   short   " C Earnings  C 59 "   (Section.short, when the producer sets one)
//   cut     " C Earn…  C 59 "      (short/title truncated, slack shared)
//   key     " C  C 59 "            (first word of the title + badge)
// The badge keeps its colour at every size; if even the key form doesn't
// fit, tabs are cut at the right edge and the selected one is kept visible.

use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::Modifier;
use ratatui::text::{Line, Span};
use ratatui::widgets::Widget;

use crate::model::Section;
use crate::ui::text;
use crate::ui::theme::Theme;

pub struct SectionTabs<'a> {
    pub sections: &'a [Section],
    pub selected: usize,
    pub theme: &'a Theme,
}

impl<'a> SectionTabs<'a> {
    pub fn new(sections: &'a [Section], selected: usize, theme: &'a Theme) -> Self {
        Self {
            sections,
            selected,
            theme,
        }
    }

    /// Title text per tab for a given total width.
    fn titles(&self, width: usize) -> Vec<String> {
        let n = self.sections.len().max(1);
        let pad = self.theme.spacing.tab_pad as usize;
        // per tab: pad + title + 2 + badge + pad, plus a 1-col separator between tabs
        let fixed: usize = self
            .sections
            .iter()
            .map(|s| 2 * pad + badge_w(s))
            .sum::<usize>()
            + (n - 1);
        let full: usize = self.sections.iter().map(|s| text::width(&s.title)).sum();
        if fixed + full <= width {
            return self.sections.iter().map(|s| s.title.clone()).collect();
        }
        let label = |s: &Section| {
            if s.short.is_empty() {
                s.title.clone()
            } else {
                s.short.clone()
            }
        };
        let short: usize = self.sections.iter().map(|s| text::width(&label(s))).sum();
        if fixed + short <= width {
            return self.sections.iter().map(label).collect();
        }
        // Water-fill: short titles keep their full width, the slack they leave
        // is shared among the long ones, so the strip uses the whole row.
        let budget = width.saturating_sub(fixed);
        let mut order: Vec<usize> = (0..n.min(self.sections.len())).collect();
        order.sort_by_key(|&i| text::width(&label(&self.sections[i])));
        let mut caps = vec![0; order.len()];
        let mut left = budget;
        for (k, &i) in order.iter().enumerate() {
            let share = left / (order.len() - k);
            caps[i] = text::width(&label(&self.sections[i])).min(share);
            left -= caps[i];
        }
        if caps.iter().all(|&c| c >= 6) {
            return self
                .sections
                .iter()
                .zip(caps)
                .map(|(s, c)| text::truncate(&label(s), c))
                .collect();
        }
        self.sections
            .iter()
            .map(|s| s.title.split_whitespace().next().unwrap_or("").to_string())
            .collect()
    }
}

fn badge_w(s: &Section) -> usize {
    if s.badge.is_empty() {
        0
    } else {
        2 + text::width(&s.badge)
    }
}

impl Widget for SectionTabs<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if area.is_empty() || self.sections.is_empty() {
            return;
        }
        let pad = " ".repeat(th.spacing.tab_pad as usize);
        let titles = self.titles(area.width as usize);
        let mut tabs: Vec<Vec<Span>> = Vec::with_capacity(titles.len());
        for (i, (s, title)) in self.sections.iter().zip(titles).enumerate() {
            let sel = i == self.selected;
            let base = if sel {
                th.selected().add_modifier(Modifier::BOLD)
            } else {
                th.base()
            };
            let mut spans = vec![Span::styled(format!("{pad}{title}"), base)];
            if !s.badge.is_empty() {
                spans.push(Span::styled("  ", base));
                let b = th.score_badge(&s.badge);
                spans.push(Span::styled(
                    s.badge.clone(),
                    if sel {
                        b.add_modifier(Modifier::REVERSED | Modifier::BOLD)
                    } else {
                        b
                    },
                ));
            }
            spans.push(Span::styled(pad.clone(), base));
            if s.new {
                spans.push(Span::styled("●", th.new_marker()));
            }
            tabs.push(spans);
        }
        // If still too wide, drop tabs from the left until the selected one fits.
        let w = |t: &Vec<Span>| t.iter().map(Span::width).sum::<usize>() + 1;
        let mut start = 0;
        while start < self.selected
            && tabs[start..=self.selected].iter().map(w).sum::<usize>() > area.width as usize
        {
            start += 1;
        }
        let mut line: Vec<Span> = Vec::new();
        if start > 0 {
            line.push(Span::styled("‹", th.dim()));
        }
        for (i, t) in tabs.into_iter().enumerate().skip(start) {
            if i > start {
                line.push(Span::styled("│", th.border()));
            }
            line.extend(t);
        }
        Line::from(line).render(area, buf);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::spacing::{Density, Spacing};
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;

    fn secs() -> Vec<Section> {
        [
            ("C Current earnings", "C Earnings", "C 59"),
            ("A Annual growth", "A Annual", "A 100"),
            ("N New high", "", "D 31"),
            ("M Market direction", "M Market", "A 100"),
        ]
        .iter()
        .map(|(t, sh, b)| Section {
            title: t.to_string(),
            short: sh.to_string(),
            badge: b.to_string(),
            ..Default::default()
        })
        .collect()
    }

    fn draw(w: u16, sel: usize) -> String {
        let mut theme = Theme::default();
        theme.spacing = Spacing::of(Density::Normal);
        let s = secs();
        let mut t = Terminal::new(TestBackend::new(w, 1)).unwrap();
        t.draw(|f| f.render_widget(SectionTabs::new(&s, sel, &theme), f.area()))
            .unwrap();
        t.backend()
            .buffer()
            .content()
            .iter()
            .map(|c| c.symbol())
            .collect()
    }

    #[test]
    fn full_labels_when_wide() {
        let out = draw(120, 0);
        assert!(out.contains("C Current earnings  C 59"), "{out}");
        assert!(out.contains("M Market direction  A 100"), "{out}");
    }

    #[test]
    fn uses_short_labels_before_cutting() {
        let out = draw(80, 0);
        assert!(
            out.contains("C Earnings  C 59") && out.contains("M Market  A 100"),
            "{out}"
        );
        assert!(!out.contains('…'), "{out}");
    }

    #[test]
    fn shrinks_but_keeps_badges() {
        let out = draw(60, 0);
        assert!(
            out.contains("C 59") && out.contains("D 31") && out.contains("A 100"),
            "{out}"
        );
        let out = draw(30, 3);
        assert!(out.contains("A 100"), "selected tab stays visible: {out}");
    }

    #[test]
    fn tiny_and_empty() {
        for w in [0, 1, 5] {
            draw(w, 2);
        }
        let theme = Theme::default();
        let mut t = Terminal::new(TestBackend::new(10, 1)).unwrap();
        t.draw(|f| f.render_widget(SectionTabs::new(&[], 0, &theme), f.area()))
            .unwrap();
    }
}
