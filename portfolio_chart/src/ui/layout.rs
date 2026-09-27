// Standard screen frames. Screens call one of these instead of hand-
// splitting Rects, so every screen has the same header / nav / detail /
// source-bar geometry and borders collapse into shared lines.
//
//   panes()        bare split, no borders (the screen draws its own chrome)
//   render_frame() the standard bordered frame: nav, detail and source bar
//                  overlap by one cell (Layout::spacing(-1)) and their
//                  borders merge (MergeStrategy::Exact) into ┬ ┴ ├ ┤, then
//                  returns the *inner* content areas to draw into.
//   popup()        centered overlay rect

use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::symbols::merge::MergeStrategy;
use ratatui::text::Line;
use ratatui::widgets::Block;
use ratatui::Frame;

use crate::ui::theme::Theme;

/// Areas of the standard master/detail screen:
///
///   ┌ header ───────────────────────────────┐
///   │ nav      │ detail                     │
///   ├──────────┴────────────────────────────┤
///   │ source bar                            │
///   └ footer (key hints) ───────────────────┘
#[derive(Debug, Clone, Copy, Default)]
pub struct Panes {
    pub header: Rect,
    pub nav: Rect,
    pub detail: Rect,
    pub source: Rect,
    pub footer: Rect,
}

#[derive(Debug, Clone, Copy)]
pub struct PaneOpts {
    /// Width of the nav column; 0 = no nav (detail spans the width).
    pub nav_width: u16,
    /// Height of the source bar; 0 = none.
    pub source_height: u16,
    pub header_height: u16,
    pub footer_height: u16,
}

impl Default for PaneOpts {
    fn default() -> Self {
        Self { nav_width: 24, source_height: 3, header_height: 1, footer_height: 1 }
    }
}

/// Which bordered pane has keyboard focus (its title is drawn in accent).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum Focus {
    Nav,
    #[default]
    Detail,
    Source,
}

/// Border titles for `render_frame`. Empty lines draw no title.
#[derive(Debug, Clone, Default)]
pub struct FrameTitles<'a> {
    pub nav: Line<'a>,
    pub detail: Line<'a>,
    /// Right-aligned on the detail pane's top border (e.g. "3/12", "audit").
    pub detail_right: Line<'a>,
    pub source: Line<'a>,
    pub focus: Focus,
}

/// Split `area` into `Panes` (outer rects, no borders drawn).
/// Heights/widths are clamped by the layout solver, so tiny areas are safe.
pub fn panes(area: Rect, opts: PaneOpts) -> Panes {
    let [header, body, source, footer] = area.layout(&Layout::vertical([
        Constraint::Length(opts.header_height),
        Constraint::Fill(1),
        Constraint::Length(opts.source_height),
        Constraint::Length(opts.footer_height),
    ]));
    let (nav, detail) = split_nav(body, opts.nav_width, 0);
    Panes { header, nav, detail, source, footer }
}

/// nav | detail, with `overlap` shared columns; nav_width 0 = no nav column.
fn split_nav(body: Rect, nav_width: u16, overlap: i16) -> (Rect, Rect) {
    if nav_width == 0 {
        return (Rect { width: 0, ..body }, body);
    }
    let [nav, detail] = body.layout(
        &Layout::horizontal([Constraint::Length(nav_width), Constraint::Fill(1)]).spacing(-overlap),
    );
    (nav, detail)
}

/// Draws the standard bordered frame and returns the inner content areas.
///
/// `header` and `footer` are unbordered lines above / below the box (the
/// screen draws the ticker line and `help::render_footer` there). nav,
/// detail and source are bordered blocks that share their border lines.
/// `source_height` counts the source block's own rows including its bottom
/// border (its top border is the detail pane's bottom), so the default of 3
/// gives two content lines.
pub fn render_frame<'a>(frame: &mut Frame, area: Rect, opts: PaneOpts, titles: &FrameTitles<'a>, theme: &Theme) -> Panes {
    let [header, body, footer] = area.layout(&Layout::vertical([
        Constraint::Length(opts.header_height),
        Constraint::Fill(1),
        Constraint::Length(opts.footer_height),
    ]));
    // the source block's top border overlaps the main blocks' bottom border
    let (main, source) = if opts.source_height > 0 {
        let [m, s] = body.layout(
            &Layout::vertical([Constraint::Fill(1), Constraint::Length(opts.source_height + 1)]).spacing(-1),
        );
        (m, s)
    } else {
        (body, Rect { height: 0, y: body.bottom(), ..body })
    };
    let (nav, detail) = split_nav(main, opts.nav_width, 1);

    let pane = |title: &Line<'a>, focused: bool| pane_block(title, focused, theme);
    let mut out = Panes { header, footer, ..Panes::default() };
    if nav.width > 0 {
        let b = pane(&titles.nav, titles.focus == Focus::Nav);
        out.nav = b.inner(nav);
        frame.render_widget(b, nav);
    } else {
        out.nav = Rect { width: 0, ..nav };
    }
    let b = pane(&titles.detail, titles.focus == Focus::Detail)
        .title_top(titles.detail_right.clone().style(theme.dim()).right_aligned());
    out.detail = b.inner(detail);
    frame.render_widget(b, detail);
    if source.height > 0 {
        let b = pane(&titles.source, titles.focus == Focus::Source);
        out.source = b.inner(source);
        frame.render_widget(b, source);
    } else {
        out.source = source;
    }
    out
}

/// One bordered pane of the standard frame; borders merge with neighbours.
fn pane_block<'a>(title: &Line<'a>, focused: bool, theme: &Theme) -> Block<'a> {
    let mut t = title.clone().style(if focused { theme.accent() } else { theme.dim() });
    // breathing room between the corner and the title text
    if t.width() > 0 {
        t.spans.insert(0, " ".into());
        t.spans.push(" ".into());
    }
    Block::bordered()
        .merge_borders(MergeStrategy::Exact)
        .border_style(theme.border())
        .style(theme.base())
        .title_top(t)
}

/// Centered popup rect of the given size, clamped to `area`.
pub fn popup(area: Rect, width: u16, height: u16) -> Rect {
    area.centered(Constraint::Length(width.min(area.width)), Constraint::Length(height.min(area.height)))
}

/// Centered popup sized as a percentage of `area`.
pub fn popup_pct(area: Rect, width_pct: u16, height_pct: u16) -> Rect {
    area.centered(Constraint::Percentage(width_pct.min(100)), Constraint::Percentage(height_pct.min(100)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::backend::TestBackend;
    use ratatui::Terminal;

    fn draw(w: u16, h: u16, opts: PaneOpts) -> (Terminal<TestBackend>, Panes) {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        let mut panes = Panes::default();
        let titles = FrameTitles { nav: "nav".into(), detail: "detail".into(), source: "src".into(), ..Default::default() };
        t.draw(|f| panes = render_frame(f, f.area(), opts, &titles, &Theme::default())).unwrap();
        (t, panes)
    }

    #[test]
    fn panes_without_nav() {
        let p = panes(Rect::new(0, 0, 80, 20), PaneOpts { nav_width: 0, ..Default::default() });
        assert_eq!(p.nav.width, 0);
        assert_eq!(p.detail.width, 80);
        assert_eq!(p.header.height, 1);
        assert_eq!(p.source.height, 3);
        assert_eq!(p.detail.height, 20 - 1 - 3 - 1);
    }

    #[test]
    fn frame_merges_borders() {
        let (t, p) = draw(40, 12, PaneOpts { nav_width: 10, ..Default::default() });
        let buf = t.backend().buffer();
        let row = |y: u16| (0..40).map(|x| buf[(x, y)].symbol().to_string()).collect::<String>();
        // top border of the box (row 1): nav/detail junction
        assert!(row(1).starts_with("┌ nav ─"), "{}", row(1));
        assert_eq!(buf[(9, 1)].symbol(), "┬");
        // detail bottom == source top, with the nav junction as ┴
        // footer 1, source block 3 rows + the shared line
        let join = 12 - 1 - 4;
        assert_eq!(buf[(0, join)].symbol(), "├");
        assert_eq!(buf[(9, join)].symbol(), "┴");
        assert_eq!(buf[(39, join)].symbol(), "┤");
        assert_eq!(p.nav, Rect::new(1, 2, 8, join - 2));
        assert_eq!(p.detail.x, 10);
        assert_eq!(p.source.height, 2);
        assert_eq!(p.footer.y, 11);
    }

    #[test]
    fn frame_tiny_and_no_nav() {
        for (w, h) in [(10, 3), (1, 1), (0, 0), (3, 10)] {
            draw(w, h, PaneOpts::default());
            draw(w, h, PaneOpts { nav_width: 0, source_height: 0, ..Default::default() });
        }
        let (_, p) = draw(30, 10, PaneOpts { nav_width: 0, source_height: 0, ..Default::default() });
        assert_eq!(p.nav.width, 0);
        assert_eq!(p.detail, Rect::new(1, 2, 28, 6));
    }

    #[test]
    fn popup_is_clamped() {
        let r = popup(Rect::new(0, 0, 20, 10), 50, 50);
        assert_eq!(r, Rect::new(0, 0, 20, 10));
        let r = popup(Rect::new(0, 0, 20, 10), 10, 4);
        assert_eq!(r, Rect::new(5, 3, 10, 4));
    }
}
