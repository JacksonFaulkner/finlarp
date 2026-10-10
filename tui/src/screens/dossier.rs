// Per-ticker dossier (dossier_cache.dossier_json, built by py/derive/dossier.py).
//
//   ┌ MRVL Marvell Technology · Semiconductors · $235B ─── data ≥ 09-26 15:58 ┐
//   │ Latest        │ blocks of the selected section (BlockView, or a        │
//   │ Events      3 │ 2-per-row BlockGrid for GRID_SECTIONS)                 │
//   │ ...           │                                                        │
//   ├───────────────┴────────────────────────────────────────────────────────┤
//   │ source of the cursor item (↵ browser · v nvim · y copy · i inputs)     │
//   └ key hints ─────────────────────────────────────────────────────────────┘
//
// The first nav entry is synthesized here: "Latest" collects every dated item
// across the sections, newest first. `a` swaps each section for an audit view
// of the same values regrouped by the document they came from. Everything is
// drawn by src/ui components; this file is state + keys + composition.

use std::io;
use std::path::Path;

use chrono::NaiveDate;
use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Paragraph, Wrap};
use serde::Deserialize;

use crate::app::{Action, Ctx, NvimAction, Screen};
use crate::model::{Block, Row, Section, Source};
use crate::ui::block_grid::BlockGrid;
use crate::ui::block_view::BlockView;
use crate::ui::command_palette::{self, Command, Entry, Palette};
use crate::ui::help::{self, Key, SOURCE_KEYS, key};
use crate::ui::layout::{self, FrameTitles, PaneOpts, Panes};
use crate::ui::section_list::SectionList;
use crate::ui::source_bar::{SourceInspector, render_source_bar, source_action};
use crate::ui::theme::Theme;

/// Items younger than this get the ● marker in "Latest".
const NEW_DAYS: i64 = 30;
const LATEST_MAX: usize = 40;
/// Chart-heavy sections drawn as a grid (two blocks per row on a normal
/// popup); list-like sections stay in the single-column BlockView.
const GRID_SECTIONS: &[&str] = &["revenue", "patents"];

const NAV_KEYS: &[Key] = &[
    key("^p", "command palette"),
    key("j/k", "move"),
    key("J/K", "next / prev section"),
    key("tab h/l", "focus nav / detail / header"),
    key("/", "jump to section"),
    key("c", "CANSLIM for this ticker"),
    key("?", "help"),
    key("q", "quit"),
];
const FOOTER_KEYS: &[Key] = &[
    key("J/K", "section"),
    key("↵", "browser"),
    key("v", "nvim"),
    key("y", "copy"),
    key("i", "inputs"),
    key("a", "audit"),
    key("/", "jump"),
    key("c", "canslim"),
    key("?", "help"),
];

/// dossier_cache.dossier_json (see py/derive/dossier.py docstring).
#[derive(Debug, Clone, Default, Deserialize)]
pub struct DossierDoc {
    pub ticker: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub industry: Option<String>,
    #[serde(default)]
    pub country: Option<String>,
    #[serde(default)]
    pub market_cap: Option<f64>,
    #[serde(default)]
    pub employees: Option<f64>,
    #[serde(default)]
    pub header_src: Option<Source>,
    #[serde(default)]
    pub built_at: String,
    #[serde(default)]
    pub freshness: Vec<Freshness>,
    #[serde(default)]
    pub sections: Vec<Section>,
    #[serde(default)]
    pub unsourced: Vec<String>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Freshness {
    pub source: String,
    pub pulled: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Focus {
    Nav,
    Detail,
    Header,
}

pub struct Dossier {
    symbol: String,
    /// None = not cached / unreadable; `message` says why.
    doc: Option<DossierDoc>,
    message: String,
    /// "Latest" followed by the dossier's own sections.
    sections: Vec<Section>,
    /// Same sections regrouped by source document (audit mode).
    audit_sections: Vec<Section>,
    /// Per-section audit counts ("25 values · 6 docs · 4 computed · 0 unsourced").
    audit_notes: Vec<String>,
    nav: SectionList,
    view: BlockView,
    /// Used instead of `view` for GRID_SECTIONS (audit mode always uses `view`).
    grid: BlockGrid,
    inspector: SourceInspector,
    focus: Focus,
    /// Active `/` query plus the section to restore on esc.
    filter: Option<(String, usize)>,
    help: bool,
    palette: Palette,
    flash: Option<String>,
    theme: Theme,
    /// Inner areas from the last draw (tests read the source bar from it).
    panes: Panes,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Dossier> {
    let symbol = arg.unwrap_or_default().trim().to_uppercase();
    let res = if symbol.is_empty() {
        Err("no ticker given: finlarp … dossier SYMBOL".to_string())
    } else {
        load_json(&ctx.db_path, &symbol).and_then(|j| match j {
            Some(j) => Ok(j),
            None => Err(format!(
                "{symbol} has no cached dossier. Build it with:\n\n  py/derive/dossier.py {symbol}"
            )),
        })
    };
    Ok(match res {
        Ok(json) => Dossier::from_json(&symbol, &json, ctx.theme),
        Err(msg) => Dossier::empty(&symbol, msg, ctx.theme),
    })
}

fn load_json(db_path: &Path, symbol: &str) -> Result<Option<String>, String> {
    let conn = crate::db::open_read_only(db_path)?;
    let mut stmt = match conn.prepare("SELECT dossier_json FROM dossier_cache WHERE symbol = ?") {
        Ok(s) => s,
        Err(_) => return Ok(None), // table not created yet = nothing cached
    };
    let mut rows = stmt.query([symbol]).map_err(|e| e.to_string())?;
    match rows.next().map_err(|e| e.to_string())? {
        Some(r) => r.get::<_, Option<String>>(0).map_err(|e| e.to_string()),
        None => Ok(None),
    }
}

impl Dossier {
    fn empty(symbol: &str, message: String, theme: Theme) -> Self {
        Self {
            symbol: symbol.to_string(),
            doc: None,
            message,
            sections: Vec::new(),
            audit_sections: Vec::new(),
            audit_notes: Vec::new(),
            nav: SectionList::new(),
            view: BlockView::new(),
            grid: BlockGrid::new(),
            inspector: SourceInspector::default(),
            focus: Focus::Nav,
            filter: None,
            help: false,
            palette: Palette::default(),
            flash: None,
            theme,
            panes: Panes::default(),
        }
    }

    pub fn from_json(symbol: &str, json: &str, theme: Theme) -> Self {
        let doc: DossierDoc = match serde_json::from_str(json) {
            Ok(d) => d,
            Err(e) => {
                return Self::empty(
                    symbol,
                    format!(
                        "{symbol}: cached dossier is unreadable ({e}).\nRebuild: py/derive/dossier.py {symbol}"
                    ),
                    theme,
                );
            }
        };
        let today = chrono::Local::now().date_naive();
        let mut sections = vec![latest_section(&doc.sections, today)];
        sections.extend(doc.sections.iter().cloned());
        let (audit_sections, audit_notes) = sections.iter().map(audit_section).unzip();
        let mut s = Self::empty(symbol, String::new(), theme);
        s.sections = sections;
        s.audit_sections = audit_sections;
        s.audit_notes = audit_notes;
        s.doc = Some(doc);
        s
    }

    fn selected(&self) -> usize {
        self.nav
            .selected()
            .min(self.sections.len().saturating_sub(1))
    }

    /// Blocks of the selected section, in the current (normal / audit) view.
    fn blocks(&self) -> &[Block] {
        let list = if self.view.audit {
            &self.audit_sections
        } else {
            &self.sections
        };
        list.get(self.selected())
            .map(|s| s.blocks.as_slice())
            .unwrap_or(&[])
    }

    /// Selected section is drawn by `grid` rather than `view`.
    fn uses_grid(&self) -> bool {
        !self.view.audit
            && self
                .sections
                .get(self.selected())
                .is_some_and(|s| GRID_SECTIONS.contains(&s.id.as_str()))
    }

    fn selected_source(&self) -> Option<&Source> {
        match self.focus {
            Focus::Header => self.doc.as_ref()?.header_src.as_ref(),
            _ if self.uses_grid() => self.grid.selected_source(self.blocks()),
            _ => self.view.selected_source(self.blocks()),
        }
    }

    /// Detail-pane keys to whichever of view / grid draws the section.
    fn detail_key(&mut self, key: KeyEvent) -> bool {
        let blocks = self.blocks().to_vec();
        if self.uses_grid() {
            self.grid.on_key(key, &blocks, &self.theme)
        } else {
            self.view.on_key(key, &blocks)
        }
    }

    fn select_section(&mut self, i: usize) {
        let i = i.min(self.sections.len().saturating_sub(1));
        if i != self.selected() {
            self.nav.state.select(Some(i));
            self.view.reset();
            self.grid.reset();
        }
    }

    fn toggle_audit(&mut self) {
        self.view.audit = !self.view.audit;
        self.view.reset();
        self.grid.reset();
    }

    /// `/` query: select the first section whose title contains it.
    fn on_filter_key(&mut self, key: KeyEvent) {
        let Some((q, back)) = self.filter.as_mut() else {
            return;
        };
        match key.code {
            KeyCode::Esc => {
                let back = *back;
                self.filter = None;
                self.select_section(back);
                return;
            }
            KeyCode::Enter => {
                self.filter = None;
                self.focus = Focus::Detail;
                return;
            }
            KeyCode::Backspace => {
                q.pop();
            }
            KeyCode::Char(c) => q.push(c),
            _ => return,
        }
        let q = q.to_lowercase();
        if let Some(i) = self
            .sections
            .iter()
            .position(|s| s.title.to_lowercase().contains(&q))
        {
            self.select_section(i);
        }
    }

    fn pane_opts(area: Rect) -> PaneOpts {
        PaneOpts {
            nav_width: if area.width < 90 {
                0
            } else {
                (area.width / 5).clamp(12, 26)
            },
            ..PaneOpts::default()
        }
    }

    fn draw_header(&self, frame: &mut Frame, area: Rect, doc: &DossierDoc) {
        let t = &self.theme;
        let focused = self.focus == Focus::Header;
        let mut left = vec![
            Span::styled(
                format!(" {} ", doc.ticker),
                if focused { t.selected() } else { t.accent() },
            ),
            Span::styled(format!(" {}", doc.name), t.title()),
        ];
        let facts = [
            doc.industry.clone(),
            doc.country.clone(),
            doc.market_cap.map(|m| format!("mcap {}", money(m))),
            doc.employees.map(|e| format!("{e:.0} staff")),
        ];
        for f in facts.into_iter().flatten() {
            left.push(Span::styled(format!(" · {f}"), t.dim()));
        }
        let mut right = vec![Span::styled(
            format!("built {} ", short_ts(&doc.built_at)),
            t.dim(),
        )];
        if let Some(old) = doc.freshness.iter().min_by(|a, b| a.pulled.cmp(&b.pulled)) {
            right.push(Span::styled(
                format!("· data ≥ {} ({}) ", short_ts(&old.pulled), old.source),
                t.dim(),
            ));
        }
        let lw = left.iter().map(|s| s.width()).sum::<usize>() as u16;
        let rw = right.iter().map(|s| s.width()).sum::<usize>() as u16;
        // the ticker line wins; freshness only shows when both fit
        let rw = if lw + rw < area.width { rw } else { 0 };
        let [l, r] = Layout::horizontal([Constraint::Fill(1), Constraint::Length(rw)]).areas(area);
        frame.render_widget(Paragraph::new(Line::from(left)).style(t.base()), l);
        frame.render_widget(
            Paragraph::new(Line::from(right).right_aligned()).style(t.base()),
            r,
        );
    }
}

impl Screen for Dossier {
    fn claude_context(&self) -> Option<String> {
        self.selected_source().map(|s| s.to_context())
    }

    fn leader_ok(&self) -> bool {
        !self.palette.open
    }

    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        let theme = self.theme;
        let Some(doc) = self.doc.clone() else {
            let r = layout::popup(area, 64, 8);
            let msg = format!("{}\n\nq quit", self.message);
            frame.render_widget(
                Paragraph::new(msg)
                    .style(theme.base())
                    .wrap(Wrap { trim: false }),
                r,
            );
            return;
        };
        let sel = self.selected();
        let grid = self.uses_grid();
        let sections = if self.view.audit {
            &self.audit_sections
        } else {
            &self.sections
        };
        let title = sections.get(sel).map(|s| s.title.as_str()).unwrap_or("");
        let titles = FrameTitles {
            nav: Line::from("sections"),
            detail: Line::from(title),
            detail_right: match (self.view.audit, self.audit_notes.get(sel)) {
                (true, Some(n)) => Line::from(format!("AUDIT · {n}")),
                _ => Line::default(),
            },
            source: Line::from("source"),
            focus: match self.focus {
                Focus::Nav => layout::Focus::Nav,
                Focus::Detail => layout::Focus::Detail,
                Focus::Header => layout::Focus::Source, // header source is shown in the source pane
            },
        };
        let p = layout::render_frame(frame, area, Self::pane_opts(area), &titles, &theme);
        self.panes = p;
        self.draw_header(frame, p.header, &doc);
        // Disjoint field borrows: sections are read while nav / view mutate their own state.
        if p.nav.width > 0 {
            self.nav
                .render(frame, p.nav, sections, &theme, self.focus == Focus::Nav);
        }
        let blocks = sections
            .get(sel)
            .map(|s| s.blocks.as_slice())
            .unwrap_or(&[]);
        if p.nav.width == 0 && self.focus == Focus::Nav {
            self.nav.render(frame, p.detail, sections, &theme, true);
        } else if grid {
            self.grid.render_in_frame(frame, p.detail, blocks, &theme);
        } else {
            self.view.render(frame, p.detail, blocks, &theme);
        }
        render_source_bar(frame, p.source, self.selected_source(), &theme);
        let status = match &self.filter {
            Some((q, _)) => Some(format!("/{q}▏  ↵ go  esc cancel")),
            None => self.flash.clone().or_else(|| {
                (self.view.audit).then(|| {
                    format!(
                        "AUDIT · values grouped by source document · {} unsourced in dossier",
                        doc.unsourced.len()
                    )
                })
            }),
        };
        help::render_footer(frame, p.footer, FOOTER_KEYS, status.as_deref(), &theme);
        if self.inspector.is_open() {
            self.inspector.render(frame, area, &theme);
        }
        if self.help {
            let all: Vec<Key> = NAV_KEYS.iter().chain(SOURCE_KEYS).copied().collect();
            help::render_overlay(
                frame,
                area,
                &format!("{} dossier keys", self.symbol),
                &all,
                &theme,
            );
        }
        if self.palette.open {
            self.palette.render(frame, area, &theme);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        self.flash = None;
        if self.palette.open
            && let Some(command) = self.palette.handle(key)
        {
            return match command {
                Some(Command::Screen(screen)) => Action::Nvim(NvimAction::Screen {
                    screen: screen.into(),
                    arg: Some(self.symbol.clone()),
                }),
                Some(Command::Picker(screen)) => Action::Nvim(NvimAction::Picker {
                    screen: screen.into(),
                }),
                Some(Command::Section(i)) => {
                    self.select_section(i);
                    Action::None
                }
                _ => Action::None,
            };
        }
        if self.doc.is_none() {
            return Action::Quit;
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        if self.inspector.is_open() {
            return self.inspector.on_key(key);
        }
        if self.filter.is_some() {
            self.on_filter_key(key);
            return Action::None;
        }
        if key.code == KeyCode::Char('p') && key.modifiers.contains(KeyModifiers::CONTROL) {
            let mut entries = command_palette::destinations(&self.symbol, "dossier");
            entries.extend(self.sections.iter().enumerate().map(|(i, s)| {
                Entry::new(format!("Go to {}", s.title), "section", Command::Section(i))
            }));
            self.palette.show(entries);
            return Action::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char('a') => self.toggle_audit(),
            KeyCode::Char('J') => self.select_section(self.selected() + 1),
            KeyCode::Char('K') => self.select_section(self.selected().saturating_sub(1)),
            KeyCode::Char('/') => self.filter = Some((String::new(), self.selected())),
            KeyCode::Char('h') | KeyCode::Left if self.focus == Focus::Detail => {
                // grid: h moves to the container on the left; at the left edge it goes to nav
                let block = self.grid.cursor.block;
                let grid = self.uses_grid();
                if !self.detail_key(key) || (grid && self.grid.cursor.block == block) {
                    self.focus = Focus::Nav;
                }
            }
            KeyCode::Char('l') | KeyCode::Right if self.focus == Focus::Detail => {
                self.detail_key(key);
            }
            KeyCode::Char('h') | KeyCode::Left => self.focus = Focus::Nav,
            KeyCode::Char('l') | KeyCode::Right => self.focus = Focus::Detail,
            KeyCode::Tab => {
                self.focus = match self.focus {
                    Focus::Nav => Focus::Detail,
                    Focus::Detail => Focus::Header,
                    Focus::Header => Focus::Nav,
                }
            }
            KeyCode::BackTab => {
                self.focus = match self.focus {
                    Focus::Nav => Focus::Header,
                    Focus::Detail => Focus::Nav,
                    Focus::Header => Focus::Detail,
                }
            }
            KeyCode::Char('c') => {
                return Action::Nvim(NvimAction::Screen {
                    screen: "canslim".into(),
                    arg: Some(self.symbol.clone()),
                });
            }
            KeyCode::Char('i') => match self.selected_source().cloned() {
                Some(s) => self.inspector.open(&s),
                None => self.flash = Some("no source here".into()),
            },
            _ => {
                if let Some(a) = source_action(key, self.selected_source()) {
                    return a;
                }
                match self.focus {
                    Focus::Nav => match key.code {
                        KeyCode::Char('j') | KeyCode::Down => {
                            self.select_section(self.selected() + 1)
                        }
                        KeyCode::Char('k') | KeyCode::Up => {
                            self.select_section(self.selected().saturating_sub(1))
                        }
                        KeyCode::Char('g') | KeyCode::Home => self.select_section(0),
                        KeyCode::Char('G') | KeyCode::End => self.select_section(usize::MAX),
                        _ => {}
                    },
                    Focus::Detail => {
                        self.detail_key(key);
                    }
                    Focus::Header => {}
                }
            }
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }
}

// ---- derived views ---------------------------------------------------------

/// YYYY-MM-DD at the start of `s`.
fn date_at(s: &str) -> Option<NaiveDate> {
    NaiveDate::parse_from_str(s.get(..10)?, "%Y-%m-%d").ok()
}

/// First YYYY-MM-DD anywhere in `s` (e.g. a source label "10-K 2026-03-11 · Item 1A").
fn date_in(s: &str) -> Option<NaiveDate> {
    s.char_indices()
        .find_map(|(i, _)| s.get(i..).and_then(date_at))
}

/// "Latest": dated rows / points (first cell or x is a date), plus rows the
/// producer flagged `new` dated by their source label; newest first.
fn latest_section(sections: &[Section], today: NaiveDate) -> Section {
    let mut items: Vec<(NaiveDate, Row)> = Vec::new();
    let mut push = |date: NaiveDate, sec: &str, text: String, src: &Option<Source>| {
        let cells = vec![date.to_string(), sec.to_string(), text];
        let new = (today - date).num_days() < NEW_DAYS;
        items.push((
            date,
            Row {
                cells,
                new,
                bar: None,
                src: src.clone(),
            },
        ));
    };
    let label_date = |src: &Option<Source>| src.as_ref().and_then(|s| date_in(&s.label));
    for sec in sections {
        for b in &sec.blocks {
            match b {
                Block::Table { rows, .. } => {
                    for r in rows {
                        let first = r.cells.first().map(String::as_str).unwrap_or("");
                        if let Some(d) = date_at(first) {
                            push(d, &sec.title, join_cells(&r.cells[1..]), &r.src);
                        } else if let (true, Some(d)) = (r.new, label_date(&r.src)) {
                            push(d, &sec.title, join_cells(&r.cells), &r.src);
                        }
                    }
                }
                Block::Kv { rows, .. } => {
                    for r in rows.iter().filter(|r| r.new) {
                        if let Some(d) = label_date(&r.src) {
                            push(
                                d,
                                &sec.title,
                                format!("{}: {}", r.label.trim(), r.value),
                                &r.src,
                            );
                        }
                    }
                }
                Block::Series {
                    title,
                    unit,
                    points,
                } => {
                    for p in points {
                        if let (Some(d), Some(y)) = (date_at(&p.x), p.y) {
                            push(d, &sec.title, format!("{title} {} {unit}", num(y)), &p.src);
                        }
                    }
                }
                Block::Bars { .. } | Block::Text { .. } => {}
            }
        }
    }
    items.sort_by_key(|(d, _)| std::cmp::Reverse(*d));
    items.truncate(LATEST_MAX);
    let n_new = items.iter().filter(|(_, r)| r.new).count();
    Section {
        id: "latest".into(),
        title: "Latest".into(),
        short: String::new(),
        new: n_new > 0,
        badge: if n_new > 0 {
            n_new.to_string()
        } else {
            String::new()
        },
        blocks: vec![Block::Table {
            title: format!("Newest dated items across sections (● = under {NEW_DAYS} days)"),
            cols: vec!["date".into(), "section".into(), "item".into()],
            rows: items.into_iter().map(|(_, r)| r).collect(),
        }],
    }
}

/// The same values as `sec`, regrouped by the document they came from:
/// one table per Source::doc_url(), one for computed values (formula +
/// inputs, inspect with `i`), one for anything unsourced; plus a one-line
/// summary with the counts (drawn on the detail pane's border).
fn audit_section(sec: &Section) -> (Section, String) {
    let mut groups: Vec<(String, Vec<Row>)> = Vec::new();
    let mut computed: Vec<Row> = Vec::new();
    let mut unsourced: Vec<Row> = Vec::new();
    for b in &sec.blocks {
        for i in 0..b.len() {
            let (label, value) = describe(b, i);
            let src = b.source(i).cloned();
            let row = Row {
                cells: vec![label, value],
                new: false,
                bar: None,
                src: src.clone(),
            };
            match src.as_ref().and_then(|s| s.doc_url().map(str::to_string)) {
                Some(url) => match groups.iter_mut().find(|(u, _)| *u == url) {
                    Some((_, rows)) => rows.push(row),
                    None => groups.push((url, vec![row])),
                },
                None if src.as_ref().is_some_and(Source::is_derived) => computed.push(row),
                None => unsourced.push(row),
            }
        }
    }
    let n_vals: usize =
        groups.iter().map(|(_, r)| r.len()).sum::<usize>() + computed.len() + unsourced.len();
    let summary = format!(
        "{n_vals} values · {} docs · {} computed · {} unsourced",
        groups.len(),
        computed.len(),
        unsourced.len()
    );
    let cols = || vec!["item".to_string(), "value".to_string()];
    let mut blocks = Vec::new();
    if !unsourced.is_empty() {
        let title = format!("UNSOURCED ({})", unsourced.len());
        blocks.push(Block::Table {
            title,
            cols: cols(),
            rows: unsourced,
        });
    }
    if !computed.is_empty() {
        let title = format!("computed ({}) · formula + inputs, press i", computed.len());
        blocks.push(Block::Table {
            title,
            cols: cols(),
            rows: computed,
        });
    }
    for (url, rows) in groups {
        blocks.push(Block::Table {
            title: format!("{} × {url}", rows.len()),
            cols: cols(),
            rows,
        });
    }
    let sec = Section {
        id: sec.id.clone(),
        title: sec.title.clone(),
        short: sec.short.clone(),
        blocks,
        new: sec.new,
        badge: sec.badge.clone(),
    };
    (sec, summary)
}

/// (what, value) of the i-th item of a block, for the audit tables.
fn describe(b: &Block, i: usize) -> (String, String) {
    match b {
        Block::Table { rows, .. } => rows
            .get(i)
            .map(|r| {
                (
                    r.cells.first().cloned().unwrap_or_default(),
                    join_cells(r.cells.get(1..).unwrap_or(&[])),
                )
            })
            .unwrap_or_default(),
        Block::Kv { rows, .. } => rows
            .get(i)
            .map(|r| (r.label.trim().to_string(), r.value.clone()))
            .unwrap_or_default(),
        Block::Series {
            title,
            unit,
            points,
        } => points
            .get(i)
            .map(|p| {
                (
                    format!("{title} {}", p.x),
                    p.y.map(|y| format!("{} {unit}", num(y)))
                        .unwrap_or("—".into()),
                )
            })
            .unwrap_or_default(),
        Block::Bars { title, unit, items } => items
            .get(i)
            .map(|it| {
                (
                    format!("{title}: {}", it.label),
                    format!("{} {unit}", num(it.value)),
                )
            })
            .unwrap_or_default(),
        Block::Text { title, text, .. } => {
            let what = if title.is_empty() {
                "text".to_string()
            } else {
                title.clone()
            };
            (what, text.chars().take(80).collect())
        }
    }
}

fn join_cells(cells: &[String]) -> String {
    cells
        .iter()
        .map(|c| c.trim())
        .filter(|c| !c.is_empty())
        .collect::<Vec<_>>()
        .join(" · ")
}

/// 2739.3 -> "2,739.3"; whole numbers without decimals.
fn num(v: f64) -> String {
    let s = if v.fract() == 0.0 {
        format!("{:.0}", v.abs())
    } else {
        format!("{:.1}", v.abs())
    };
    let (int, frac) = s
        .split_once('.')
        .map_or((s.as_str(), None), |(i, f)| (i, Some(f)));
    let mut out = String::new();
    for (i, c) in int.chars().enumerate() {
        if i > 0 && (int.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(c);
    }
    let sign = if v < 0.0 { "-" } else { "" };
    frac.map_or(format!("{sign}{out}"), |f| format!("{sign}{out}.{f}"))
}

fn money(v: f64) -> String {
    let a = v.abs();
    for (div, suf) in [(1e12, "T"), (1e9, "B"), (1e6, "M")] {
        if a >= div {
            return format!("${:.1}{suf}", v / div);
        }
    }
    format!("${v:.0}")
}

/// "2026-09-27T10:13:24" -> "2026-09-27 10:13".
fn short_ts(ts: &str) -> String {
    ts.get(..16).unwrap_or(ts).replace('T', " ")
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::{KeyEventKind, KeyEventState, KeyModifiers};

    const MRVL: &str = include_str!("fixtures/dossier_MRVL.json");

    fn press(s: &mut Dossier, code: KeyCode) -> Action {
        s.on_key(KeyEvent {
            code,
            modifiers: KeyModifiers::NONE,
            kind: KeyEventKind::Press,
            state: KeyEventState::NONE,
        })
    }

    fn render(s: &mut Dossier, w: u16, h: u16) -> Terminal<TestBackend> {
        let mut term = Terminal::new(TestBackend::new(w, h)).expect("terminal");
        term.draw(|f| s.draw(f)).expect("draw");
        term
    }

    fn rows_text(term: &Terminal<TestBackend>, area: Rect) -> String {
        let buf = term.backend().buffer();
        (area.top()..area.bottom())
            .map(|y| {
                (area.left()..area.right())
                    .map(|x| buf[(x, y)].symbol())
                    .collect::<String>()
            })
            .collect::<Vec<_>>()
            .join("\n")
    }

    fn screen() -> Dossier {
        Dossier::from_json("MRVL", MRVL, Theme::default())
    }

    #[test]
    fn number_format() {
        assert_eq!(num(2739.3), "2,739.3");
        assert_eq!(num(-1234567.0), "-1,234,567");
        assert_eq!(num(12.0), "12");
    }

    #[test]
    fn parses_fixture_and_synthesizes_latest() {
        let s = screen();
        let doc = s.doc.as_ref().expect("fixture parses");
        assert_eq!(doc.ticker, "MRVL");
        assert_eq!(s.sections.len(), doc.sections.len() + 1);
        assert_eq!(s.sections[0].title, "Latest");
        let Block::Table { rows, .. } = &s.sections[0].blocks[0] else {
            panic!("latest is a table")
        };
        assert!(!rows.is_empty());
        assert!(
            rows.windows(2).all(|w| w[0].cells[0] >= w[1].cells[0]),
            "newest first"
        );
        assert!(rows.iter().all(|r| r.src.is_some()));
    }

    #[test]
    fn renders_wide_and_tiny() {
        let mut s = screen();
        let term = render(&mut s, 160, 45);
        let all = rows_text(&term, Rect::new(0, 0, 160, 45));
        assert!(all.contains("MRVL"));
        assert!(all.contains("Latest"));
        let mut s = screen();
        render(&mut s, 40, 12); // must not panic
        let mut s = screen();
        press(&mut s, KeyCode::Char('a'));
        render(&mut s, 40, 12);
        let mut e = Dossier::empty(
            "ZZZZ",
            "ZZZZ has no cached dossier".into(),
            Theme::default(),
        );
        let term = render(&mut e, 40, 12);
        assert!(rows_text(&term, Rect::new(0, 0, 40, 12)).contains("no cached"));
    }

    #[test]
    fn source_bar_follows_selection() {
        let mut s = screen();
        press(&mut s, KeyCode::Char('J')); // Latest -> Events
        assert_eq!(s.sections[s.selected()].id, "events");
        press(&mut s, KeyCode::Char('l'));
        press(&mut s, KeyCode::Char('j'));
        let want = s
            .view
            .selected_source(s.blocks())
            .expect("row has a source")
            .label
            .clone();
        let Block::Table { rows, .. } = &s.sections[1].blocks[0] else {
            panic!()
        };
        assert_eq!(
            rows[1].src.as_ref().map(|x| x.label.as_str()),
            Some(want.as_str())
        );
        let term = render(&mut s, 160, 45);
        let bar = rows_text(&term, s.panes.source);
        assert!(bar.contains(&want), "source bar {bar:?} lacks {want:?}");

        // header focus shows header_src
        press(&mut s, KeyCode::Tab);
        assert_eq!(s.focus, Focus::Header);
        assert_eq!(
            s.selected_source().map(|x| x.label.as_str()),
            Some("Yahoo Finance profile")
        );
    }

    #[test]
    fn section_nav_filter_and_actions() {
        let mut s = screen();
        press(&mut s, KeyCode::Char('K'));
        assert_eq!(s.selected(), 0, "clamps at top");
        for _ in 0..50 {
            press(&mut s, KeyCode::Char('J'));
        }
        assert_eq!(s.selected(), s.sections.len() - 1, "clamps at bottom");
        press(&mut s, KeyCode::Char('/'));
        for c in "pat".chars() {
            press(&mut s, KeyCode::Char(c));
        }
        assert_eq!(s.sections[s.selected()].id, "patents");
        press(&mut s, KeyCode::Esc);
        assert_eq!(s.selected(), s.sections.len() - 1, "esc restores");
        assert_eq!(
            press(&mut s, KeyCode::Char('c')),
            Action::Nvim(NvimAction::Screen {
                screen: "canslim".into(),
                arg: Some("MRVL".into())
            })
        );
        assert_eq!(press(&mut s, KeyCode::Char('q')), Action::Quit);
    }

    #[test]
    fn revenue_is_a_two_column_grid() {
        let mut s = screen();
        let revenue = s
            .sections
            .iter()
            .position(|x| x.id == "revenue")
            .expect("revenue section");
        s.select_section(revenue);
        press(&mut s, KeyCode::Char('l'));
        assert!(s.uses_grid());
        let term = render(&mut s, 140, 45);
        let detail = rows_text(&term, s.panes.detail);
        let first = detail.lines().next().unwrap_or("");
        assert!(
            first.contains("│") && s.grid.cursor.block == 0,
            "first two blocks share a row: {detail}"
        );
        let all = rows_text(&term, Rect::new(0, 0, 140, 45));
        assert!(
            all.contains("┬") && all.contains("┴"),
            "nav/source junctions kept: {all}"
        );

        // l: next container right; h twice: back, then out to nav
        press(&mut s, KeyCode::Char('l'));
        assert_eq!(s.grid.cursor.block, 1);
        assert_ne!(
            s.selected_source().map(|x| x.label.clone()),
            None,
            "grid selection drives the source bar"
        );
        press(&mut s, KeyCode::Char('h'));
        assert_eq!((s.grid.cursor.block, s.focus), (0, Focus::Detail));
        press(&mut s, KeyCode::Char('h'));
        assert_eq!(s.focus, Focus::Nav);

        // audit mode is a list again
        press(&mut s, KeyCode::Char('a'));
        assert!(!s.uses_grid());
    }

    #[test]
    fn audit_groups_by_document() {
        let mut s = screen();
        let revenue = s
            .sections
            .iter()
            .position(|x| x.id == "revenue")
            .expect("revenue section");
        s.select_section(revenue);
        press(&mut s, KeyCode::Char('a'));
        assert!(s.view.audit);
        let blocks = s.blocks();
        assert!(
            s.audit_notes[revenue].ends_with("0 unsourced"),
            "{}",
            s.audit_notes[revenue]
        );
        assert!(!blocks.iter().any(|b| b.title().starts_with("UNSOURCED")));
        let total: usize = s.sections[revenue].blocks.iter().map(Block::len).sum();
        let grouped: usize = blocks.iter().map(Block::len).sum();
        assert_eq!(total, grouped, "every value lands in exactly one group");
        for b in blocks.iter().filter(|b| !b.title().starts_with("computed")) {
            let urls: Vec<_> = (0..b.len())
                .filter_map(|i| b.source(i)?.doc_url())
                .collect();
            assert!(
                urls.windows(2).all(|w| w[0] == w[1]),
                "one document per group"
            );
        }
    }
}
