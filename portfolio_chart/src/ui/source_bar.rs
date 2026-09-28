// The "where did this number come from" UI.
//
// SourceBar: one or two lines under the detail pane showing the selected
//   value's Source: document label + URL, or formula + input count.
// SourceInspector: popup (key `i`) for a derived value: the formula and a
//   selectable list of its inputs (recursively), each openable.
// Standard keys every screen binds to the selected Source (see
//   `source_action`): ↵ browser, v nvim docview, y copy URL, i inspect.

use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::Style;
use ratatui::text::{Line, Span, Text};
use ratatui::widgets::{
    Block, Clear, HighlightSpacing, List, ListItem, ListState, Paragraph, StatefulWidget, Widget,
};

use crate::app::{Action, NvimAction};
use crate::model::Source;
use crate::ui::text;
use crate::ui::theme::Theme;

/// Render `src` into `area` (see `SourceBar`).
pub fn render_source_bar(frame: &mut Frame, area: Rect, src: Option<&Source>, theme: &Theme) {
    frame.render_widget(
        SourceBar {
            src,
            theme,
            hints: None,
        },
        area,
    );
}

/// Same, with the screen's own key hints instead of the standard source keys
/// (for screens where ↵ does something else, e.g. search opens the chunk).
pub fn render_source_bar_with(
    frame: &mut Frame,
    area: Rect,
    src: Option<&Source>,
    hints: &[(&str, &str)],
    theme: &Theme,
) {
    frame.render_widget(
        SourceBar {
            src,
            theme,
            hints: Some(hints),
        },
        area,
    );
}

/// One or two lines describing a Source:
///
///   ◆ 10-Q filed 2026-08-28 · Revenue · Q2 FY2027   sec.gov/…/mrvl-20260801.htm
///   ↵ browser  v nvim  y copy                      (second line if there's room)
///
///   ƒ 2,739.3 / 2,006.1 − 1 · 2 inputs · YoY growth
///   ↵ …  i inputs
pub struct SourceBar<'a> {
    pub src: Option<&'a Source>,
    pub theme: &'a Theme,
    /// Overrides the standard hints derived from `src`.
    pub hints: Option<&'a [(&'a str, &'a str)]>,
}

impl Widget for SourceBar<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        (&self).render(area, buf);
    }
}

impl Widget for &SourceBar<'_> {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let th = self.theme;
        buf.set_style(area, th.base());
        if area.is_empty() {
            return;
        }
        let Some(src) = self.src else {
            Line::from(vec![
                Span::styled("✗ ", th.down()),
                Span::styled("no source", th.down()),
            ])
            .render(area, buf);
            return;
        };
        let w = area.width as usize;
        let hints = match self.hints {
            Some(keys) => key_spans(keys, th),
            None => hint_spans(src, th),
        };
        let hints_w: usize = hints.iter().map(|s| s.width()).sum();
        let two_lines = area.height >= 2;
        // one-line mode: keep hints right-aligned only if they leave room for the label
        let reserve = if !two_lines && hints_w + 20 <= w {
            hints_w + 2
        } else {
            0
        };
        let desc = describe(src, w.saturating_sub(reserve), th);
        desc.render(area, buf);
        let hint_line = Line::from(hints);
        if two_lines {
            let r = Rect {
                y: area.y + 1,
                height: 1,
                ..area
            };
            hint_line.render(r, buf);
        } else if reserve > 0 {
            hint_line.right_aligned().render(area, buf);
        }
    }
}

/// Fitted to `w` columns:
///   document:  "◆ label · host/…/doc"            (+ " · N inputs" if any)
///   derived:   "ƒ formula · N inputs · label"    (formula first: it is the value)
fn describe<'a>(src: &Source, w: usize, th: &Theme) -> Line<'a> {
    let n = src.inputs.len();
    let inputs = (n > 0).then(|| {
        Span::styled(
            format!("{n} input{}", if n == 1 { "" } else { "s" }),
            th.dim(),
        )
    });
    let url = src
        .url
        .as_deref()
        .map(|u| Span::styled(text::short_url(u), th.accent()));
    let mut parts: Vec<Span> = match &src.formula {
        Some(f) => {
            // formula capped so the label still shows something
            let f = text::truncate(f, (w * 3 / 5).max(8));
            let mut v = vec![
                Span::styled("ƒ ", th.derived()),
                Span::styled(f, th.derived()),
            ];
            v.extend(inputs.into_iter().chain(url));
            v.push(Span::styled(src.label.clone(), th.base()));
            v
        }
        None => {
            let tail_w: usize = url.iter().chain(inputs.iter()).map(|s| s.width() + 3).sum();
            let label_w = w.saturating_sub(2 + tail_w).max(w / 2);
            let mut v = vec![
                Span::styled("◆ ", th.accent()),
                Span::styled(text::truncate(&src.label, label_w), th.base()),
            ];
            v.extend(url.into_iter().chain(inputs));
            v
        }
    };
    // separators between everything after the icon + first part
    let mut spans = parts.drain(..2).collect::<Vec<_>>();
    for p in parts {
        spans.push(Span::styled(" · ", th.dim()));
        spans.push(p);
    }
    // final hard cut so nothing wraps or spills
    fit_spans(spans, w)
}

/// Truncate a span list to `w` columns, ending in … when cut.
fn fit_spans<'a>(spans: Vec<Span<'a>>, w: usize) -> Line<'a> {
    let mut out = Vec::new();
    let mut used = 0;
    for s in spans {
        let sw = s.width();
        if used + sw <= w {
            used += sw;
            out.push(s);
        } else {
            let t = text::truncate(&s.content, w.saturating_sub(used));
            if !t.is_empty() {
                out.push(Span::styled(t, s.style));
            }
            break;
        }
    }
    Line::from(out)
}

/// Key hints valid for `src` ("↵ browser" only if it has a URL, etc.).
fn hint_spans<'a>(src: &Source, th: &Theme) -> Vec<Span<'a>> {
    let mut keys: Vec<(&str, &str)> = Vec::new();
    if src.url.is_some() {
        keys.push(("↵", "browser"));
        keys.push(("v", "nvim"));
    }
    if src.url.is_some() || src.formula.is_some() {
        keys.push(("y", "copy"));
    }
    if !src.inputs.is_empty() || src.is_derived() {
        keys.push(("i", "inputs"));
    }
    key_spans(&keys, th)
}

fn key_spans<'a>(keys: &[(&str, &str)], th: &Theme) -> Vec<Span<'a>> {
    let mut spans = Vec::new();
    for (i, (k, d)) in keys.iter().enumerate() {
        if i > 0 {
            spans.push(Span::raw("  "));
        }
        spans.push(Span::styled(k.to_string(), th.accent()));
        spans.push(Span::styled(format!(" {d}"), th.dim()));
    }
    spans
}

/// Maps the standard source keys to an Action for `src`. Returns None if
/// the key isn't a source key, so screens can fall through to their own keys.
pub fn source_action(key: KeyEvent, src: Option<&Source>) -> Option<Action> {
    let src = src?;
    match key.code {
        KeyCode::Enter => src.url.clone().map(Action::OpenBrowser),
        KeyCode::Char('v') => src.doc_url().map(|u| {
            Action::Nvim(NvimAction::Docview {
                url: u.to_string(),
                quote: src.quote(),
            })
        }),
        KeyCode::Char('y') => src
            .url
            .clone()
            .or_else(|| src.formula.clone())
            .map(Action::Copy),
        _ => None,
    }
}

/// Popup listing a derived Source's formula and inputs.
///
/// Inputs that have inputs of their own can be drilled into (↵ / l); ⌫ / h
/// goes back up. `stack` holds the parents and their selected rows.
#[derive(Debug, Default)]
pub struct SourceInspector {
    pub source: Option<Source>,
    pub state: ListState,
    /// Parent sources (and the row selected in each) above `source`.
    pub stack: Vec<(Source, usize)>,
}

impl SourceInspector {
    pub fn open(&mut self, src: &Source) {
        self.source = Some(src.clone());
        self.state = ListState::default().with_selected(Some(0));
        self.stack.clear();
    }
    pub fn is_open(&self) -> bool {
        self.source.is_some()
    }
    pub fn close(&mut self) {
        self.source = None;
        self.stack.clear();
    }
    /// The currently highlighted input (or the source itself if it has none).
    pub fn selected(&self) -> Option<&Source> {
        let s = self.source.as_ref()?;
        s.inputs.get(self.state.selected().unwrap_or(0)).or(Some(s))
    }
    /// Number of rows in the list (the source itself when it has no inputs).
    fn rows(&self) -> usize {
        self.source.as_ref().map_or(0, |s| s.inputs.len().max(1))
    }

    /// Descend into the highlighted input if it has inputs of its own.
    /// Returns false when there's nothing to drill into.
    pub fn drill(&mut self) -> bool {
        let i = self.state.selected().unwrap_or(0);
        let Some(cur) = self.source.as_mut() else {
            return false;
        };
        let Some(child) = cur.inputs.get(i).filter(|c| !c.inputs.is_empty()).cloned() else {
            return false;
        };
        let parent = std::mem::replace(cur, child);
        self.stack.push((parent, i));
        self.state = ListState::default().with_selected(Some(0));
        true
    }

    /// Back to the parent source; false at the top.
    pub fn up(&mut self) -> bool {
        let Some((parent, i)) = self.stack.pop() else {
            return false;
        };
        self.source = Some(parent);
        self.state = ListState::default().with_selected(Some(i));
        true
    }

    /// Handle keys while open: j/k/g/G move, ↵/l drill (or open in browser
    /// on a leaf), ⌫/h up, v/y on the selected input, esc/q/i close.
    pub fn on_key(&mut self, key: KeyEvent) -> Action {
        let n = self.rows();
        match key.code {
            KeyCode::Esc | KeyCode::Char('q') | KeyCode::Char('i') => self.close(),
            KeyCode::Char('j') | KeyCode::Down => {
                let i = self.state.selected().unwrap_or(0);
                self.state.select(Some((i + 1).min(n.saturating_sub(1))));
            }
            KeyCode::Char('k') | KeyCode::Up => self.state.select_previous(),
            KeyCode::Char('g') | KeyCode::Home => self.state.select_first(),
            KeyCode::Char('G') | KeyCode::End => self.state.select(Some(n.saturating_sub(1))),
            KeyCode::Backspace | KeyCode::Char('h') | KeyCode::Left => {
                self.up();
            }
            KeyCode::Char('l') | KeyCode::Right => {
                self.drill();
            }
            KeyCode::Enter if self.drill() => {}
            _ => return source_action(key, self.selected()).unwrap_or(Action::None),
        }
        Action::None
    }

    /// Draw the popup centered over `area` (Clear behind it).
    pub fn render(&mut self, frame: &mut Frame, area: Rect, theme: &Theme) {
        frame.render_stateful_widget(InspectorView { theme }, area, self);
    }
}

/// Widget half of `SourceInspector` (state = the inspector).
pub struct InspectorView<'a> {
    pub theme: &'a Theme,
}

impl StatefulWidget for InspectorView<'_> {
    type State = SourceInspector;

    fn render(self, area: Rect, buf: &mut Buffer, st: &mut SourceInspector) {
        let th = self.theme;
        let Some(src) = st.source.clone() else { return };
        let width = area.width.saturating_sub(4).min(110);
        let inner_w = width.saturating_sub(2) as usize;

        // header: breadcrumb, label, formula (wrapped), quote
        let mut head: Vec<Line> = Vec::new();
        if !st.stack.is_empty() {
            let crumbs: Vec<&str> = st.stack.iter().map(|(s, _)| s.label.as_str()).collect();
            head.push(Line::styled(
                text::truncate(&format!("{} ›", crumbs.join(" › ")), inner_w),
                th.dim(),
            ));
        }
        head.push(Line::styled(
            text::truncate(&src.label, inner_w),
            th.title(),
        ));
        if let Some(f) = &src.formula {
            for (i, l) in text::wrap(f, inner_w.saturating_sub(2))
                .into_iter()
                .take(4)
                .enumerate()
            {
                let lead = if i == 0 { "= " } else { "  " };
                head.push(Line::from(vec![
                    Span::styled(lead, th.dim()),
                    Span::styled(l, th.derived()),
                ]));
            }
        }
        if let Some(u) = src.url.as_deref() {
            head.push(Line::styled(
                text::truncate(&text::short_url(u), inner_w),
                th.accent(),
            ));
        }
        if let Some(q) = src.quote() {
            head.push(Line::styled(
                text::truncate(&format!("“{q}”"), inner_w),
                th.dim(),
            ));
        }

        let rows = st.rows();
        let list_h = (rows * 2).min(20) as u16;
        let height = (head.len() as u16 + 1 + list_h + 2).min(area.height);
        let r = crate::ui::layout::popup(area, width, height);
        Clear.render(r, buf);

        let title = if src.is_derived() {
            " ƒ formula inputs "
        } else {
            " source "
        };
        let block = Block::bordered()
            .border_style(th.accent())
            .style(th.base())
            .title_top(Line::styled(title, th.accent()))
            .title_bottom(Line::from(footer_hints(!st.stack.is_empty(), th)).right_aligned());
        let inner = block.inner(r);
        block.render(r, buf);

        let [head_r, sep_r, list_r] = inner.layout(&Layout::vertical([
            Constraint::Length(head.len() as u16),
            Constraint::Length(1),
            Constraint::Fill(1),
        ]));
        Paragraph::new(Text::from(head)).render(head_r, buf);
        Line::styled("─".repeat(sep_r.width as usize), th.border()).render(sep_r, buf);

        let items: Vec<ListItem> = if src.inputs.is_empty() {
            vec![input_item(&src, inner_w.saturating_sub(2), th)]
        } else {
            src.inputs
                .iter()
                .map(|i| input_item(i, inner_w.saturating_sub(2), th))
                .collect()
        };
        let list = List::new(items)
            .highlight_style(th.selected())
            .highlight_symbol(Line::styled("▌ ", th.accent()))
            .highlight_spacing(HighlightSpacing::Always);
        StatefulWidget::render(list, list_r, buf, &mut st.state);
    }
}

/// Two-line list entry: marker + label, then URL / formula dimmed.
fn input_item<'a>(s: &Source, w: usize, th: &Theme) -> ListItem<'a> {
    let (marker, style): (&str, Style) = if !s.inputs.is_empty() {
        ("› ", th.accent()) // drillable
    } else if s.is_derived() {
        ("ƒ ", th.derived())
    } else {
        ("◆ ", th.dim())
    };
    let first = Line::from(vec![
        Span::styled(marker, style),
        Span::styled(text::truncate(&s.label, w.saturating_sub(2)), th.base()),
    ]);
    let detail = match (&s.formula, s.url.as_deref()) {
        (Some(f), _) => format!("= {f}  · {} inputs", s.inputs.len()),
        (None, Some(u)) if !s.inputs.is_empty() => {
            format!("{} · {} inputs", text::short_url(u), s.inputs.len())
        }
        (None, Some(u)) => text::short_url(u),
        (None, None) => "no document".into(),
    };
    let second = Line::styled(
        format!("  {}", text::truncate(&detail, w.saturating_sub(2))),
        th.dim(),
    );
    ListItem::new(Text::from(vec![first, second]))
}

fn footer_hints<'a>(nested: bool, th: &Theme) -> Vec<Span<'a>> {
    let mut keys = vec![("↵", "open/drill"), ("v", "nvim"), ("y", "copy")];
    if nested {
        keys.push(("⌫", "up"));
    }
    keys.push(("esc", "close"));
    let mut spans = vec![Span::raw(" ")];
    for (k, d) in keys {
        spans.push(Span::styled(k.to_string(), th.accent()));
        spans.push(Span::styled(format!(" {d} "), th.dim()));
    }
    spans
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    fn key(c: KeyCode) -> KeyEvent {
        KeyEvent::new(c, KeyModifiers::NONE)
    }

    fn derived() -> Source {
        let q2 = Source::url(
            "10-Q Q2 FY2027",
            "https://www.sec.gov/ix?doc=/Archives/edgar/data/1/2/mrvl-20260801.htm",
        );
        let q4 = Source::derived(
            "Q4 derived",
            "FY 5,767.3 − 9M 3,949.9",
            vec![
                Source::url("10-K FY", "https://www.sec.gov/a/b/k.htm"),
                Source::url("10-Q 9M", "https://www.sec.gov/a/b/q.htm"),
            ],
        );
        Source::derived("YoY growth", "2,739.3 / 2,006.1 − 1", vec![q2, q4])
    }

    fn screen(b: &Buffer) -> String {
        (0..b.area.height)
            .map(|y| {
                (0..b.area.width)
                    .map(|x| b[(x, y)].symbol().to_string())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn draw_bar(src: Option<&Source>, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
        t.draw(|f| render_source_bar(f, f.area(), src, &Theme::default()))
            .unwrap();
        screen(t.backend().buffer())
    }

    #[test]
    fn bar_shows_url_host_and_doc() {
        let s = Source::url(
            "10-Q filed 2026-08-28",
            "https://www.sec.gov/ix?doc=/Archives/edgar/data/1/2/mrvl-20260801.htm#:~:text=x",
        );
        let out = draw_bar(Some(&s), 80, 2);
        assert!(
            out.contains("◆ 10-Q filed 2026-08-28 · sec.gov/…/mrvl-20260801.htm"),
            "{out}"
        );
        assert!(out.contains("↵ browser  v nvim  y copy"), "{out}");
    }

    #[test]
    fn bar_shows_formula_and_inputs() {
        let out = draw_bar(Some(&derived()), 80, 1);
        assert!(
            out.contains("ƒ 2,739.3 / 2,006.1 − 1 · 2 inputs · YoY growth"),
            "{out}"
        );
        assert!(draw_bar(None, 40, 1).contains("no source"));
    }

    #[test]
    fn bar_tiny() {
        for (w, h) in [(10, 3), (1, 1), (0, 0)] {
            draw_bar(Some(&derived()), w, h);
            draw_bar(None, w, h);
        }
    }

    #[test]
    fn inspector_drills_and_acts() {
        let mut ins = SourceInspector::default();
        ins.open(&derived());
        assert_eq!(ins.selected().unwrap().label, "10-Q Q2 FY2027");
        // leaf: enter opens in browser, v sends to nvim docview
        assert!(matches!(
            ins.on_key(key(KeyCode::Enter)),
            Action::OpenBrowser(_)
        ));
        assert!(matches!(
            ins.on_key(key(KeyCode::Char('v'))),
            Action::Nvim(NvimAction::Docview { .. })
        ));
        // move to the derived input and drill in
        ins.on_key(key(KeyCode::Char('j')));
        ins.on_key(key(KeyCode::Char('j'))); // clamps at the last row
        assert_eq!(ins.selected().unwrap().label, "Q4 derived");
        assert_eq!(ins.on_key(key(KeyCode::Enter)), Action::None);
        assert_eq!(ins.source.as_ref().unwrap().label, "Q4 derived");
        assert_eq!(ins.selected().unwrap().label, "10-K FY");
        assert_eq!(
            ins.on_key(key(KeyCode::Char('y'))),
            Action::Copy("https://www.sec.gov/a/b/k.htm".into())
        );
        // back up restores the parent's selection
        ins.on_key(key(KeyCode::Backspace));
        assert_eq!(ins.selected().unwrap().label, "Q4 derived");
        ins.on_key(key(KeyCode::Esc));
        assert!(!ins.is_open());
    }

    #[test]
    fn inspector_renders_formula_and_inputs() {
        let mut ins = SourceInspector::default();
        ins.open(&derived());
        let mut t = Terminal::new(TestBackend::new(80, 24)).unwrap();
        t.draw(|f| ins.render(f, f.area(), &Theme::default()))
            .unwrap();
        let out = screen(t.backend().buffer());
        assert!(out.contains("ƒ formula inputs"), "{out}");
        assert!(out.contains("= 2,739.3 / 2,006.1 − 1"), "{out}");
        assert!(out.contains("▌ ◆ 10-Q Q2 FY2027"), "{out}");
        assert!(out.contains("› Q4 derived"), "{out}");
        ins.drill();
        ins.on_key(key(KeyCode::Char('j')));
        ins.drill();
        t.draw(|f| ins.render(f, f.area(), &Theme::default()))
            .unwrap();
        let out = screen(t.backend().buffer());
        assert!(out.contains("YoY growth ›"), "{out}");
        for (w, h) in [(10, 3), (1, 1), (0, 0)] {
            let mut t = Terminal::new(TestBackend::new(w, h)).unwrap();
            t.draw(|f| ins.render(f, f.area(), &Theme::default()))
                .unwrap();
        }
    }
}
