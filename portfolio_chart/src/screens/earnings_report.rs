//! Hard-coded MRVL structured earnings report POC. This adapts the reviewed
//! JSON artifact into the same Section/Block/Source model used by the other
//! Ratatui screens, so rows keep their evidence quote and source URL.

use std::io;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent};
use ratatui::layout::{Constraint, Layout};
use ratatui::text::{Line, Span};
use ratatui::widgets::Paragraph;
use serde_json::Value;

use crate::app::{Action, Ctx, Screen};
use crate::model::{BarItem, Block, KvRow, Point, Row, Section, Source};
use crate::ui::block_view::BlockView;
use crate::ui::help::{self, Key, key};
use crate::ui::layout::{self, Focus, FrameTitles, PaneOpts, Panes};
use crate::ui::section_list::SectionList;
use crate::ui::source_bar::{SourceInspector, render_source_bar, source_action};
use crate::ui::theme::Theme;

const REPORT: &str = include_str!("../../../research/mrvl_poc/marvell_report.json");
const KEYS: &[Key] = &[
    key("j/k", "move"),
    key("J/K", "section"),
    key("tab", "focus"),
    key("↵", "browser"),
    key("i", "source quote"),
    key("?", "help"),
    key("q", "quit"),
];

pub struct EarningsReport {
    ticker: String,
    company: String,
    as_of: String,
    model: String,
    sections: Vec<Section>,
    nav: SectionList,
    view: BlockView,
    inspector: SourceInspector,
    focus_nav: bool,
    help: bool,
    theme: Theme,
    panes: Panes,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<EarningsReport> {
    let symbol = arg.unwrap_or_else(|| "MRVL".into()).to_uppercase();
    let mut report =
        parse_report(REPORT, ctx.theme).map_err(|e| io::Error::other(e.to_string()))?;
    if symbol != "MRVL" {
        return Err(io::Error::other(format!(
            "The hard-coded report POC currently contains MRVL, not {symbol}"
        )));
    }
    report.theme = ctx.theme;
    Ok(report)
}

fn parse_report(raw: &str, theme: Theme) -> Result<EarningsReport, serde_json::Error> {
    let doc: Value = serde_json::from_str(raw)?;
    let sources: Vec<SourceDef> = serde_json::from_value(doc["sources"].clone())?;
    let sections = doc["sections"]
        .as_array()
        .into_iter()
        .flatten()
        .map(|section| {
            let blocks = section["blocks"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|block| convert_block(block, &sources))
                .collect();
            Section {
                id: string(section, "id"),
                title: string(section, "title"),
                short: String::new(),
                blocks,
                new: false,
                badge: String::new(),
            }
        })
        .collect();
    Ok(EarningsReport {
        ticker: string(&doc, "ticker"),
        company: string(&doc, "company"),
        as_of: string(&doc, "as_of"),
        model: string(&doc, "model"),
        sections,
        nav: SectionList::new(),
        view: BlockView::new(),
        inspector: SourceInspector::default(),
        focus_nav: false,
        help: false,
        theme,
        panes: Panes::default(),
    })
}

#[derive(serde::Deserialize)]
struct SourceDef {
    source_id: String,
    label: String,
    url: String,
}

fn string(v: &Value, key: &str) -> String {
    v[key].as_str().unwrap_or_default().to_string()
}

fn source(item: &Value, sources: &[SourceDef]) -> Option<Source> {
    let evidence = &item["evidence"];
    let id = evidence["source_id"].as_str()?;
    let def = sources.iter().find(|s| s.source_id == id)?;
    let quote = evidence["quote"].as_str().unwrap_or_default();
    let status = item["status"].as_str().unwrap_or("reported");
    let mut src = Source::url(
        format!("{} · {}", status.to_uppercase(), def.label),
        format!("{}#:~:text={}", def.url, encode_fragment(quote)),
    );
    // Keep the evidence visible even in consumers that do not render URL fragments.
    if quote.is_empty() {
        src.url = Some(def.url.clone());
    }
    Some(src)
}

fn convert_block(v: &Value, sources: &[SourceDef]) -> Block {
    let title = string(v, "title");
    match v["type"].as_str().unwrap_or("text") {
        "table" => Block::Table {
            title,
            cols: v["cols"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|x| x.as_str().unwrap_or("").to_string())
                .collect(),
            rows: v["rows"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|r| Row {
                    cells: r["cells"]
                        .as_array()
                        .into_iter()
                        .flatten()
                        .map(|x| x.as_str().unwrap_or("").to_string())
                        .collect(),
                    new: false,
                    src: source(r, sources),
                })
                .collect(),
        },
        "kv" => Block::Kv {
            title,
            rows: v["rows"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|r| KvRow {
                    label: string(r, "label"),
                    value: string(r, "value"),
                    new: false,
                    src: source(r, sources),
                })
                .collect(),
        },
        "series" => Block::Series {
            title,
            unit: string(v, "unit"),
            points: v["points"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|p| Point {
                    x: string(p, "x"),
                    y: p["y"].as_f64(),
                    src: source(p, sources),
                })
                .collect(),
        },
        "bars" => Block::Bars {
            title,
            unit: string(v, "unit"),
            items: v["items"]
                .as_array()
                .into_iter()
                .flatten()
                .map(|i| BarItem {
                    label: string(i, "label"),
                    value: i["value"].as_f64().unwrap_or_default(),
                    compare: i["compare"].as_f64(),
                    src: source(i, sources),
                })
                .collect(),
        },
        _ => Block::Text {
            title,
            text: string(v, "text"),
            src: source(v, sources),
        },
    }
}

fn encode_fragment(s: &str) -> String {
    let mut out = String::new();
    for b in s.bytes() {
        if b.is_ascii_alphanumeric() || b"-._~".contains(&b) {
            out.push(b as char);
        } else {
            out.push_str(&format!("%{b:02X}"));
        }
    }
    out
}

impl EarningsReport {
    fn selected_source(&self) -> Option<&Source> {
        self.view.selected_source(
            self
                .sections
                .get(self.nav.selected())
                .map(|s| s.blocks.as_slice())
                .unwrap_or(&[]),
        )
    }
    fn selected(&self) -> usize {
        self.nav
            .selected()
            .min(self.sections.len().saturating_sub(1))
    }
}

impl Screen for EarningsReport {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let section_title = self
            .sections
            .get(self.selected())
            .map(|s| s.title.as_str())
            .unwrap_or("Report");
        let titles = FrameTitles {
            nav: Line::from("report"),
            detail: Line::from(section_title),
            source: Line::from("evidence"),
            focus: if self.focus_nav {
                Focus::Nav
            } else {
                Focus::Detail
            },
            ..Default::default()
        };
        let opts = PaneOpts {
            nav_width: if area.width < 88 {
                0
            } else {
                (area.width / 5).clamp(18, 28)
            },
            ..Default::default()
        };
        let p = layout::render_frame(frame, area, opts, &titles, &self.theme);
        self.panes = p;
        let header =
            Layout::horizontal([Constraint::Fill(1), Constraint::Length(24)]).split(p.header);
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(format!(" {} ", self.ticker), self.theme.accent()),
                Span::styled(self.company.clone(), self.theme.title()),
                Span::styled(format!(" · {}", self.as_of), self.theme.dim()),
            ]))
            .style(self.theme.base()),
            header[0],
        );
        frame.render_widget(
            Paragraph::new(format!("{} · STRUCTURED POC", self.model.to_uppercase()))
                .style(self.theme.dim())
                .right_aligned(),
            header[1],
        );
        if p.nav.width > 0 {
            self.nav
                .render(frame, p.nav, &self.sections, &self.theme, self.focus_nav);
        }
        let blocks = self
            .sections
            .get(self.selected())
            .map(|s| s.blocks.as_slice())
            .unwrap_or(&[]);
        self.view.render(frame, p.detail, blocks, &self.theme);
        render_source_bar(frame, p.source, self.selected_source(), &self.theme);
        help::render_footer(frame, p.footer, KEYS, None, &self.theme);
        if self.inspector.is_open() {
            self.inspector.render(frame, area, &self.theme);
        }
        if self.help {
            help::render_overlay(frame, area, "Marvell report keys", KEYS, &self.theme);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.inspector.is_open() {
            return self.inspector.on_key(key);
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => Action::Quit,
            KeyCode::Char('?') => {
                self.help = true;
                Action::None
            }
            KeyCode::Char('J') | KeyCode::PageDown => {
                self.nav.next();
                self.view.reset();
                Action::None
            }
            KeyCode::Char('K') | KeyCode::PageUp => {
                self.nav.previous();
                self.view.reset();
                Action::None
            }
            KeyCode::Tab => {
                self.focus_nav = !self.focus_nav;
                Action::None
            }
            KeyCode::Char('i') => {
                if let Some(s) = self.selected_source().cloned() {
                    self.inspector.open(&s);
                }
                Action::None
            }
            _ => {
                if let Some(action) = source_action(key, self.selected_source()) {
                    return action;
                }
                if self.focus_nav {
                    match key.code {
                        KeyCode::Char('j') | KeyCode::Down => self.nav.next(),
                        KeyCode::Char('k') | KeyCode::Up => self.nav.previous(),
                        _ => {}
                    }
                } else {
                    let blocks = self
                        .sections
                        .get(self.selected())
                        .map(|s| s.blocks.as_slice())
                        .unwrap_or(&[])
                        .to_vec();
                    self.view.on_key(key, &blocks);
                }
                Action::None
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::{Terminal, backend::TestBackend};
    #[test]
    fn report_json_maps_every_section_and_source_to_tui_models() {
        let report = parse_report(REPORT, Theme::default()).unwrap();
        assert_eq!(report.ticker, "MRVL");
        assert_eq!(report.sections.len(), 6);
        let blocks: Vec<_> = report.sections.iter().flat_map(|s| &s.blocks).collect();
        assert!(blocks.iter().any(|b| matches!(b, Block::Text { .. })));
        assert!(
            blocks
                .iter()
                .filter_map(|b| match b {
                    Block::Table { rows, .. } => Some(rows),
                    _ => None,
                })
                .flatten()
                .all(|r| r.src.as_ref().is_some_and(|s| s.url.is_some()))
        );
    }

    #[test]
    fn quote_fragment_is_encoded_for_safe_deep_link() {
        assert_eq!(
            encode_fragment("Revenue | $2,739.3"),
            "Revenue%20%7C%20%242%2C739.3"
        );
    }

    #[test]
    fn first_section_renders_as_a_selectable_sourced_report() {
        let mut report = parse_report(REPORT, Theme::default()).unwrap();
        let mut terminal = Terminal::new(TestBackend::new(140, 42)).unwrap();
        terminal.draw(|frame| report.draw(frame)).unwrap();
        let rendered = terminal
            .backend()
            .buffer()
            .content
            .iter()
            .map(|c| c.symbol())
            .collect::<String>();
        assert!(rendered.contains("Business model"));
        assert!(rendered.contains("How Marvell makes money"));
        assert!(rendered.contains("REPORTED"));
        assert!(report.selected_source().is_some());
    }
}
