// Left navigation list over model::Section (List + ListState). Shows the
// ● new marker and right-aligned badge; selection clamps and scrolls itself.
//
//   SectionList      state (ListState) + movement helpers
//   SectionNav       the widget: `frame.render_stateful_widget(nav, area, &mut list)`
//   SectionList::render  convenience wrapper around the two

use ratatui::buffer::Buffer;
use ratatui::layout::Rect;
use ratatui::style::Stylize;
use ratatui::text::{Line, Span};
use ratatui::widgets::{HighlightSpacing, List, ListItem, ListState, StatefulWidget};
use ratatui::Frame;

use crate::model::Section;
use crate::ui::text;
use crate::ui::theme::Theme;

#[derive(Debug, Default)]
pub struct SectionList {
    pub state: ListState,
}

impl SectionList {
    pub fn new() -> Self {
        Self { state: ListState::default().with_selected(Some(0)) }
    }
    /// Selected index. May exceed the list length right after `next()`
    /// until the next render clamps it; use `selected_in(len)` when indexing.
    pub fn selected(&self) -> usize {
        self.state.selected().unwrap_or(0)
    }
    /// Selected index clamped to `len` (None when the list is empty).
    pub fn selected_in(&self, len: usize) -> Option<usize> {
        (len > 0).then(|| self.selected().min(len - 1))
    }
    pub fn next(&mut self) {
        self.state.select_next();
    }
    pub fn previous(&mut self) {
        self.state.select_previous();
    }
    pub fn first(&mut self) {
        self.state.select_first();
    }
    /// Select the last of `len` sections.
    pub fn last(&mut self, len: usize) {
        self.state.select(Some(len.saturating_sub(1)));
    }
    /// Select `i`, clamped to `len`.
    pub fn select(&mut self, i: usize, len: usize) {
        self.state.select(Some(i.min(len.saturating_sub(1))));
    }
    /// Clamp the selection to `len` items (call when the sections change).
    pub fn clamp(&mut self, len: usize) {
        let i = self.selected();
        self.state.select(Some(i.min(len.saturating_sub(1))));
    }

    pub fn render(&mut self, frame: &mut Frame, area: Rect, sections: &[Section], theme: &Theme, focused: bool) {
        frame.render_stateful_widget(SectionNav { sections, theme, focused }, area, self);
    }
}

/// Stateless description of the nav list; state is a `SectionList`.
pub struct SectionNav<'a> {
    pub sections: &'a [Section],
    pub theme: &'a Theme,
    /// Focused: selection is reversed; unfocused: selection is only bold.
    pub focused: bool,
}

const MARKER_W: usize = 2; // "● " or "  "
const SYMBOL_W: usize = 2; // highlight symbol "▌ "
const MIN_TITLE: usize = 6;

impl StatefulWidget for SectionNav<'_> {
    type State = SectionList;

    fn render(self, area: Rect, buf: &mut Buffer, state: &mut SectionList) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if self.sections.is_empty() || area.is_empty() {
            return;
        }
        state.clamp(self.sections.len());
        let inner = (area.width as usize).saturating_sub(SYMBOL_W);
        let items: Vec<ListItem> = self.sections.iter().map(|s| item(s, inner, th)).collect();
        let hl = if self.focused { th.selected() } else { th.title() };
        let list = List::new(items)
            .style(th.base())
            .highlight_style(hl)
            .highlight_symbol(Line::from("▌ ".fg(th.accent)))
            .highlight_spacing(HighlightSpacing::Always)
            .scroll_padding(1);
        StatefulWidget::render(list, area, buf, &mut state.state);
    }
}

/// "● Title ......... badge", fitted to `width` columns.
fn item<'a>(s: &Section, width: usize, th: &Theme) -> ListItem<'a> {
    let marker = if s.new { Span::styled("● ", th.new_marker()) } else { Span::raw("  ") };
    // the title yields to the badge (truncated with …), unless that would
    // leave the title under MIN_TITLE columns: then the badge is dropped
    let badge_w = if s.badge.is_empty() { 0 } else { text::width(&s.badge) + 1 };
    let room = width.saturating_sub(MARKER_W);
    let show_badge = badge_w > 0 && room >= badge_w + MIN_TITLE.min(text::width(&s.title));
    let title_w = if show_badge { room - badge_w } else { room };
    let title = text::fit(&s.title, title_w, false);
    let badge = if show_badge { s.badge.clone() } else { String::new() };
    let mut spans = vec![marker, Span::raw(title)];
    if !badge.is_empty() {
        spans.push(Span::raw(" "));
        spans.push(Span::styled(badge, th.accent()));
    }
    ListItem::new(Line::from(spans))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::backend::TestBackend;
    use ratatui::style::Modifier;
    use ratatui::Terminal;

    fn sections() -> Vec<Section> {
        vec![
            Section { id: "a".into(), title: "Events".into(), new: true, badge: "3 new".into(), ..Default::default() },
            Section { id: "b".into(), title: "Earnings & guidance".into(), ..Default::default() },
            Section { id: "c".into(), title: "Holders".into(), badge: "A+".into(), ..Default::default() },
        ]
    }

    fn render(list: &mut SectionList, secs: &[Section], w: u16, h: u16, focused: bool) -> Buffer {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| list.render(f, f.area(), secs, &Theme::default(), focused)).unwrap();
        t.backend().buffer().clone()
    }

    fn row(b: &Buffer, y: u16) -> String {
        (0..b.area.width).map(|x| b[(x, y)].symbol().to_string()).collect()
    }

    #[test]
    fn shows_marker_badge_and_selection() {
        let mut l = SectionList::new();
        let b = render(&mut l, &sections(), 24, 5, true);
        assert_eq!(row(&b, 0), "▌ ● Events         3 new");
        assert!(row(&b, 2).trim_end().ends_with("A+"));
        assert!(b[(4, 0)].modifier.contains(Modifier::REVERSED));
        assert!(!b[(4, 1)].modifier.contains(Modifier::REVERSED));
        // unfocused: bold, not reversed
        let b = render(&mut l, &sections(), 24, 5, false);
        assert!(b[(4, 0)].modifier.contains(Modifier::BOLD));
        assert!(!b[(4, 0)].modifier.contains(Modifier::REVERSED));
    }

    #[test]
    fn narrow_truncates_title_keeps_badge() {
        let secs = vec![
            Section { id: "m".into(), title: "M Market direction".into(), badge: "A+".into(), ..Default::default() },
            Section { id: "n".into(), title: "N New highs".into(), ..Default::default() },
        ];
        let mut l = SectionList::new();
        let b = render(&mut l, &secs, 16, 3, true);
        assert_eq!(row(&b, 0), "▌   M Market… A+");
        assert_eq!(row(&b, 1).trim_end(), "    N New highs");
        // too narrow for both: badge dropped, title kept
        let b = render(&mut l, &secs, 10, 3, true);
        assert_eq!(row(&b, 0), "▌   M Mar…");
    }

    #[test]
    fn selection_clamps() {
        let mut l = SectionList::new();
        l.last(3);
        l.next();
        render(&mut l, &sections(), 24, 5, true);
        assert_eq!(l.selected(), 2);
        l.first();
        assert_eq!(l.selected(), 0);
        l.select(99, 3);
        assert_eq!(l.selected_in(3), Some(2));
        assert_eq!(l.selected_in(0), None);
    }

    #[test]
    fn tiny_and_empty() {
        let mut l = SectionList::new();
        render(&mut l, &[], 10, 3, true);
        render(&mut l, &sections(), 10, 3, true);
        render(&mut l, &sections(), 1, 1, true);
        render(&mut l, &sections(), 0, 0, true);
    }
}
