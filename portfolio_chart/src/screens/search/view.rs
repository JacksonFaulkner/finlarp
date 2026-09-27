// Rendering for the search screen. Geometry comes from ui::layout
// (render_frame: header = query input, nav = facets, detail = results +
// preview, source bar, footer); the detail pane is split here into results
// and preview, side by side when wide and stacked when narrow.

use ratatui::layout::{Constraint, Layout, Position, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph};
use ratatui::Frame;

use super::client::Hit;
use super::query;
use super::{FacetRow, Pane, Search, KEYS};
use crate::ui::help::{render_footer, render_overlay};
use crate::ui::layout::{render_frame, Focus, FrameTitles, PaneOpts};
use crate::ui::source_bar::render_source_bar_with;
use crate::ui::text;
use crate::ui::theme::Theme;

const PROMPT: &str = " search › ";
const PLACEHOLDER: &str = "t:TICK s:sector type:10k|risk|new|earn|guid|patent sec:mda since:2025 \"phrase\" -word";
/// Below this width the preview goes under the results.
const SIDE_BY_SIDE: u16 = 120;

fn type_style(kind: &str, theme: &Theme) -> Style {
    let s = match kind {
        "new_risk" => theme.down(),
        "earnings" | "guidance" => theme.up(),
        "filing" => theme.accent(),
        _ => theme.dim(),
    };
    s.add_modifier(Modifier::BOLD)
}

fn short_date(h: &Hit) -> &str {
    h.date.as_deref().map(|d| d.get(..10).unwrap_or(d)).unwrap_or("")
}

/// `text` as spans with `terms` highlighted over `base`.
fn hl_spans<'a>(text: &'a str, terms: &[String], base: Style, theme: &Theme) -> Vec<Span<'a>> {
    let hit = base.fg(theme.accent).add_modifier(Modifier::BOLD | Modifier::UNDERLINED);
    query::highlight(text, terms).into_iter().map(|(s, m)| Span::styled(s, if m { hit } else { base })).collect()
}

impl Search {
    pub(super) fn render(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let theme = self.theme;
        frame.render_widget(Block::new().style(theme.base()), area);
        let opts = PaneOpts {
            nav_width: if area.width >= 90 { 24 } else { 0 },
            source_height: 3,
            header_height: 1,
            footer_height: 1,
        };
        let status = match (&self.error, self.loading) {
            (Some(_), _) => String::new(),
            (None, true) if self.results.is_empty() => "searching…".into(),
            (None, _) => {
                let shown = self.results.len() as u64;
                let ms = self.ms.map(|m| format!(" · {m}ms")).unwrap_or_default();
                if self.total > shown { format!(" {shown} of {}{ms} ", self.total) } else { format!(" {shown}{ms} ") }
            }
        };
        let titles = FrameTitles {
            nav: Line::from(" facets "),
            detail: Line::from(" results "),
            detail_right: Line::from(status),
            source: Line::from(" source "),
            focus: match self.focus {
                Pane::Facets => Focus::Nav,
                Pane::Results | Pane::Preview | Pane::Input => Focus::Detail,
            },
        };
        let panes = render_frame(frame, area, opts, &titles, &theme);
        self.render_input(frame, panes.header);
        if panes.nav.width > 0 {
            self.render_facets(frame, panes.nav);
        }

        let wide = panes.detail.width >= SIDE_BY_SIDE - 24;
        let (results, preview, sep) = if wide {
            let [r, p] = Layout::horizontal([Constraint::Percentage(48), Constraint::Fill(1)]).areas(panes.detail);
            (r, p, Borders::LEFT)
        } else {
            let [r, p] = Layout::vertical([Constraint::Percentage(45), Constraint::Fill(1)]).areas(panes.detail);
            (r, p, Borders::TOP)
        };
        self.render_results(frame, results);
        let pb = Block::new().borders(sep).border_style(theme.border());
        let inner = pb.inner(preview);
        frame.render_widget(pb, preview);
        self.render_preview(frame, inner);

        let src = self.selected_source();
        let hints = [("↵", "chunk"), ("alt-v", "nvim"), ("ctrl-o", "browser"), ("y", "copy")];
        render_source_bar_with(frame, panes.source, src.as_ref(), &hints, &theme);
        let flash = self.flash.as_ref().map(|(m, _)| m.as_str());
        render_footer(frame, panes.footer, KEYS, flash, &theme);
        if self.show_help {
            render_overlay(frame, area, "search", KEYS, &theme);
        }
    }

    fn render_input(&self, frame: &mut Frame, area: Rect) {
        let theme = &self.theme;
        let err = self.error.as_deref().map(|e| format!(" {} ", text::truncate(e, (area.width / 2) as usize)));
        let busy = self.loading && !self.results.is_empty();
        let right = err.clone().unwrap_or_else(|| if busy { " searching… ".into() } else { String::new() });
        let [left, status] =
            Layout::horizontal([Constraint::Fill(1), Constraint::Length(text::width(&right) as u16)]).areas(area);
        let focused = self.focus == Pane::Input && !self.show_help;
        let prompt_style = if focused { theme.accent().add_modifier(Modifier::BOLD) } else { theme.dim() };
        let pw = text::width(PROMPT) as u16;
        let avail = left.width.saturating_sub(pw + 1) as usize;
        let scroll = self.input.visual_scroll(avail);
        let value = self.input.value();
        let body = if value.is_empty() {
            Span::styled(PLACEHOLDER, theme.dim())
        } else {
            let visible: String = value.chars().skip(scroll).collect();
            Span::styled(text::truncate(&visible, avail + 1), theme.base())
        };
        frame.render_widget(Paragraph::new(Line::from(vec![Span::styled(PROMPT, prompt_style), body])), left);
        let st = if err.is_some() { theme.down() } else { theme.accent() };
        frame.render_widget(Paragraph::new(right).style(st), status);
        if focused {
            let x = left.x + pw + (self.input.visual_cursor().saturating_sub(scroll)) as u16;
            frame.set_cursor_position(Position::new(x.min(left.right().saturating_sub(1)), left.y));
        }
    }

    fn render_facets(&mut self, frame: &mut Frame, area: Rect) {
        let theme = &self.theme;
        let q = self.input.value();
        let w = area.width as usize;
        let items: Vec<ListItem> = self
            .facets
            .iter()
            .map(|f| match f {
                FacetRow::Header(d) => ListItem::new(Line::styled(d.name().to_uppercase(), theme.dim())),
                FacetRow::Item { dim, value, count } => {
                    let active = query::is_active(q, *dim, value);
                    let label =
                        if *dim == query::Dim::Type { format!("{} {value}", query::badge(value)) } else { value.clone() };
                    let n = count.to_string();
                    let name_w = w.saturating_sub(n.len() + 3);
                    ListItem::new(Line::from(vec![
                        Span::styled(if active { "● " } else { "  " }, theme.accent()),
                        Span::styled(
                            text::fit(&label, name_w, false),
                            if active { theme.accent() } else { theme.base() },
                        ),
                        Span::styled(format!(" {n}"), theme.dim()),
                    ]))
                }
            })
            .collect();
        let hl = if self.focus == Pane::Facets { theme.selected() } else { theme.base() };
        let list = if items.is_empty() {
            List::new([ListItem::new(Line::styled("  (none)", theme.dim()))])
        } else {
            List::new(items)
        };
        frame.render_stateful_widget(list.style(theme.base()).highlight_style(hl), area, &mut self.facet_state);
    }

    fn render_results(&mut self, frame: &mut Frame, area: Rect) {
        let theme = &self.theme;
        if self.results.is_empty() {
            let msg = match (&self.error, self.loading) {
                (Some(e), _) => e.clone(),
                (None, true) => "searching…".into(),
                (None, false) => "no matches".into(),
            };
            let style = if self.error.is_some() { theme.down() } else { theme.dim() };
            frame.render_widget(Paragraph::new(format!(" {msg}")).style(style).wrap(Default::default()), area);
            return;
        }
        let snip_w = area.width.saturating_sub(4) as usize;
        let items: Vec<ListItem> = self
            .results
            .iter()
            .map(|h| {
                let mut head = vec![
                    Span::styled(text::fit(&h.ticker, 6, false), theme.title()),
                    Span::raw(" "),
                    Span::styled(query::badge(&h.kind).to_string(), type_style(&h.kind, theme)),
                    Span::raw(" "),
                    Span::styled(format!("{:<10}", short_date(h)), theme.dim()),
                    Span::raw(" "),
                    Span::styled(h.section.clone().unwrap_or_default(), theme.base()),
                ];
                if let Some(f) = h.form.as_deref().filter(|f| *f != "patent") {
                    head.push(Span::styled(format!(" {f}"), theme.dim()));
                }
                if let Some(s) = h.score {
                    head.push(Span::styled(format!("  {s:.2}"), theme.dim()));
                }
                let snip = query::snippet(&h.text, &self.terms, snip_w);
                let mut body = vec![Span::raw("  ")];
                body.extend(hl_spans(&snip, &self.terms, theme.base(), theme).into_iter().map(|s| {
                    Span::styled(s.content.into_owned(), s.style)
                }));
                ListItem::new(vec![Line::from(head), Line::from(body)])
            })
            .collect();
        let hl = if matches!(self.focus, Pane::Results | Pane::Input) {
            theme.selected()
        } else {
            theme.base().add_modifier(Modifier::BOLD)
        };
        let list = List::new(items).style(theme.base()).highlight_symbol("▌").highlight_style(hl);
        frame.render_stateful_widget(list, area, &mut self.list);
    }

    fn render_preview(&mut self, frame: &mut Frame, area: Rect) {
        let theme = self.theme;
        // body height (area minus the preview's own header line)
        self.preview_height = area.height.saturating_sub(1);
        let Some(hit) = self.selected().cloned() else {
            self.preview_len = 0;
            return;
        };
        let (rows, loaded) = match self.context.get(&hit.id) {
            Some(r) => (r.clone(), true),
            None => (vec![hit.clone()], false),
        };
        let [head, body] = Layout::vertical([Constraint::Length(1), Constraint::Fill(1)]).areas(area);
        let focused = self.focus == Pane::Preview;
        let note = match (loaded, rows.len()) {
            (false, _) => "loading context…".to_string(),
            (true, 1) => "1 chunk".to_string(),
            (true, n) => format!("{n} chunks"),
        };
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" preview ", if focused { theme.accent() } else { theme.dim() }),
                Span::styled(format!("{} {} · {note}", hit.ticker, query::badge(&hit.kind)), theme.dim()),
            ])),
            head,
        );
        let w = body.width.saturating_sub(2).max(10) as usize;
        let mut lines: Vec<Line> = Vec::new();
        let mut match_line = 0u16;
        for r in &rows {
            let is_hit = r.id == hit.id;
            if is_hit {
                match_line = lines.len() as u16;
            }
            let meta = format!(
                "── {} {} · {} · {} #{} ",
                r.ticker,
                r.form.as_deref().unwrap_or(&r.kind),
                r.section.as_deref().unwrap_or(""),
                short_date(r),
                r.seq.unwrap_or(0)
            );
            let mut h = vec![Span::styled(meta, if is_hit { theme.title() } else { theme.dim() })];
            if is_hit && rows.len() > 1 {
                h.push(Span::styled("◀ match", theme.accent()));
            }
            lines.push(Line::from(h));
            let base = if is_hit { theme.base() } else { theme.dim() };
            for l in text::wrap(&r.text, w) {
                let spans: Vec<Span<'static>> = hl_spans(&l, &self.terms, base, &theme)
                    .into_iter()
                    .map(|s| Span::styled(s.content.into_owned(), s.style))
                    .collect();
                let mut v = vec![Span::raw(" ")];
                v.extend(spans);
                lines.push(Line::from(v));
            }
            lines.push(Line::default());
        }
        self.preview_len = lines.len() as u16;
        if loaded && self.preview_jump {
            self.preview_scroll = match_line;
            self.preview_jump = false;
        }
        self.preview_scroll = self.preview_scroll.min(self.preview_len.saturating_sub(self.preview_height));
        frame.render_widget(Paragraph::new(lines).style(theme.base()).scroll((self.preview_scroll, 0)), body);
    }
}
