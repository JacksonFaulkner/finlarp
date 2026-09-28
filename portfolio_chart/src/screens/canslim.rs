// CANSLIM scorecard (canslim_cache.scorecard_json, built by views/canslim.py).
//
//   MRVL  CANSLIM scorecard  261.94  as of 2026-09-27         overall B 60
//   C Earnings  C 59 │ A Annual  A 100 │ N New high  D 31 │ …   (SectionTabs, H/L)
//   ┌ Headline ────────────┬ EPS estimate revision ─┐
//   │ …                    │ …                      │  the letter's blocks as a
//   ├ EPS actual vs est ───┼ Revenue ───────────────┤  BlockGrid: hjkl between
//   │ …                    │ …                      │  containers, j/k through items
//   ├──────────────────────┴────────────────────────┤
//   │ source of the cursor item (↵ browser · v nvim · y copy · i inputs) │
//   └ key hints ─────────────────────────────────────┘
//
// Python builds one model::Section per letter with every value sourced
// (Yahoo page / SEC filing / formula + inputs) and a grade badge; this file
// is state + keys + composition, all drawing is done by src/ui components.

use std::io;
use std::path::Path;

use ratatui::Frame;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Paragraph, Wrap};
use serde::Deserialize;

use crate::app::{Action, Ctx, EXIT_BACK_TO_PICKER, NvimAction, Screen};
use crate::model::{Block, Section, Source};
use crate::ui::block_grid::BlockGrid;
use crate::ui::command_palette::{self, Command, Entry, Palette};
use crate::ui::help::{self, Key, SOURCE_KEYS, key};
use crate::ui::layout::{self, Focus, FrameTitles, PaneOpts};
use crate::ui::section_list::SectionList;
use crate::ui::section_tabs::SectionTabs;
use crate::ui::source_bar::{SourceInspector, render_source_bar, source_action};
use crate::ui::theme::Theme;

const SCREEN_KEYS: &[Key] = &[
    key("^p", "command palette"),
    key("H/L", "previous / next letter"),
    key("1-7", "jump to letter C A N S L I M"),
    key("o", "inspect overall grade"),
    key(
        "h/j/k/l",
        "move between containers (j/k: through items first)",
    ),
    key("tab/S-tab", "next / previous container"),
    key("g/G", "first / last container"),
    key("^d/^u", "down / up 5 items"),
    key("r", "reload from cache"),
    key("s", "back to symbol picker"),
    key("?", "help"),
    key("q/esc", "quit"),
];
const FOOTER_KEYS: &[Key] = &[
    key("?", "help"),
    key("H/L", "letter"),
    key("hjkl", "move"),
    key("↵", "browser"),
    key("v", "nvim"),
    key("y", "copy"),
    key("i", "inputs"),
    key("a", "audit"),
    key("s", "picker"),
    key("q", "quit"),
];

/// The parts of the scorecard this screen reads; the flat letter fields
/// (c/a/…) are for other readers, everything shown comes from `sections`.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct Scorecard {
    pub symbol: String,
    #[serde(default)]
    pub as_of: String,
    #[serde(default)]
    pub n: NewHigh,
    #[serde(default)]
    pub overall: Option<Overall>,
    #[serde(default)]
    pub sections: Vec<Section>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct NewHigh {
    #[serde(default)]
    pub price_current: Option<f64>,
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct Overall {
    pub score: i64,
    pub grade: String,
    #[serde(default)]
    pub src: Option<Source>,
}

pub struct Canslim {
    symbol: String,
    db_path: std::path::PathBuf,
    /// None = not cached / unreadable; `message` says why.
    card: Option<Scorecard>,
    message: String,
    nav: SectionList,
    view: BlockGrid,
    inspector: SourceInspector,
    help: bool,
    palette: Palette,
    flash: Option<String>,
    theme: Theme,
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Canslim> {
    let symbol = arg.unwrap_or_default().trim().to_uppercase();
    let mut s = Canslim::new(&symbol, ctx.db_path.clone(), ctx.theme);
    s.reload();
    Ok(s)
}

fn load_json(db_path: &Path, symbol: &str) -> Result<Option<String>, String> {
    // Read-only: nvim / canslim.py may hold the write lock.
    let conn = crate::db::open_read_only(db_path)?;
    let Ok(mut stmt) = conn.prepare("SELECT scorecard_json FROM canslim_cache WHERE symbol = ?")
    else {
        return Ok(None); // table not created yet = nothing cached
    };
    let mut rows = stmt.query([symbol]).map_err(|e| e.to_string())?;
    match rows.next().map_err(|e| e.to_string())? {
        Some(r) => r.get::<_, Option<String>>(0).map_err(|e| e.to_string()),
        None => Ok(None),
    }
}

impl Canslim {
    fn new(symbol: &str, db_path: std::path::PathBuf, theme: Theme) -> Self {
        Self {
            symbol: symbol.to_string(),
            db_path,
            card: None,
            message: String::new(),
            nav: SectionList::new(),
            view: BlockGrid::new(),
            inspector: SourceInspector::default(),
            help: false,
            palette: Palette::default(),
            flash: None,
            theme,
        }
    }

    /// Screen over an in-memory scorecard (tests).
    #[cfg(test)]
    pub fn from_json(symbol: &str, json: &str, theme: Theme) -> Self {
        let mut s = Self::new(symbol, Default::default(), theme);
        s.set_json(Some(json));
        s
    }

    fn set_json(&mut self, json: Option<&str>) {
        let sym = &self.symbol;
        let refresh = format!("views/canslim.py {sym} --force");
        self.card = None;
        match json.map(serde_json::from_str::<Scorecard>) {
            None => {
                self.message =
                    format!("No CANSLIM data cached for {sym}. Build it with:\n\n  {refresh}")
            }
            Some(Err(e)) => {
                self.message =
                    format!("{sym}: cached scorecard is unreadable ({e}).\nRebuild: {refresh}")
            }
            // Entries cached before values carried sources have no sections.
            Some(Ok(c)) if c.sections.is_empty() => {
                self.message = format!(
                    "{sym}: cached scorecard predates sourced sections.\nRebuild: {refresh}"
                )
            }
            Some(Ok(c)) => {
                self.nav.clamp(c.sections.len());
                self.card = Some(c);
            }
        }
        self.view.reset();
    }

    /// Cheap local DB re-read: picks up whatever a background canslim.py
    /// refresh wrote without relaunching the popup.
    fn reload(&mut self) {
        if self.symbol.is_empty() {
            self.message = "no symbol given: portfolio_chart … canslim SYMBOL".into();
            return;
        }
        match load_json(&self.db_path, &self.symbol) {
            Ok(j) => self.set_json(j.as_deref()),
            Err(e) => {
                self.card = None;
                self.message = format!("{}: {e}", self.symbol);
            }
        }
    }

    fn sections(&self) -> &[Section] {
        self.card
            .as_ref()
            .map(|c| c.sections.as_slice())
            .unwrap_or(&[])
    }

    fn selected(&self) -> usize {
        self.nav.selected_in(self.sections().len()).unwrap_or(0)
    }

    fn blocks(&self) -> &[Block] {
        self.sections()
            .get(self.selected())
            .map(|s| s.blocks.as_slice())
            .unwrap_or(&[])
    }

    fn selected_source(&self) -> Option<&Source> {
        self.view.selected_source(self.blocks())
    }

    fn select_letter(&mut self, i: usize) {
        let n = self.sections().len();
        if n > 0 && i.min(n - 1) != self.selected() {
            self.nav.select(i, n);
            self.view.reset();
        }
    }

    fn draw_header(&self, frame: &mut Frame, area: Rect, card: &Scorecard) {
        let t = &self.theme;
        let price = card
            .n
            .price_current
            .map(|p| format!("{p:.2}"))
            .unwrap_or_else(|| "—".into());
        let left = Line::from(vec![
            Span::styled(format!(" {} ", card.symbol), t.accent()),
            Span::styled(" CANSLIM scorecard ", t.title()),
            Span::styled(format!(" {price}"), t.base()),
            Span::styled(format!("  as of {}", card.as_of), t.dim()),
        ]);
        let right = match &card.overall {
            Some(o) => Line::from(vec![
                Span::styled("overall ", t.dim()),
                Span::styled(format!("{} {}", o.grade, o.score), t.score(o.score as f64)),
                Span::styled("  (o) ", t.dim()),
            ]),
            None => Line::styled("overall —  ", t.dim()),
        };
        let [l, r] = area.layout(&Layout::horizontal([
            Constraint::Fill(1),
            Constraint::Length(right.width() as u16),
        ]));
        frame.render_widget(Paragraph::new(left).style(t.base()), l);
        frame.render_widget(Paragraph::new(right.right_aligned()).style(t.base()), r);
    }
}

impl Screen for Canslim {
    fn draw(&mut self, frame: &mut Frame) {
        let area = frame.area();
        self.theme.fit(area);
        let theme = self.theme;
        frame.render_widget(Paragraph::new("").style(theme.base()), area);
        let Some(card) = self.card.clone() else {
            let r = layout::popup(area, 72, 8);
            let msg = format!("{}\n\nq quit · s picker", self.message);
            frame.render_widget(
                Paragraph::new(msg)
                    .style(theme.base())
                    .wrap(Wrap { trim: false }),
                r,
            );
            return;
        };
        let sel = self.selected();
        let section = card.sections.get(sel);
        let blocks = section.map(|s| s.blocks.as_slice()).unwrap_or(&[]);
        let items: usize = blocks.iter().map(Block::len).sum();
        let pos: usize = blocks
            .iter()
            .take(self.view.cursor.block)
            .map(Block::len)
            .sum::<usize>()
            + self.view.cursor.item
            + 1;
        let titles = FrameTitles {
            nav: Line::default(),
            detail: Line::from(format!(
                " {} ",
                section.map(|s| s.title.as_str()).unwrap_or("")
            )),
            detail_right: Line::from(format!(
                " {}{}/{} ",
                if self.view.audit { "audit · " } else { "" },
                pos.min(items),
                items
            )),
            source: Line::from(format!(
                " source · {}{}/{} ",
                if self.view.audit { "audit · " } else { "" },
                pos.min(items),
                items
            )),
            focus: Focus::Detail,
        };
        let opts = PaneOpts {
            nav_width: 0,
            tabs_height: 1,
            ..PaneOpts::default()
        };
        let p = layout::render_frame(frame, area, opts, &titles, &theme);
        self.draw_header(frame, p.header, &card);
        frame.render_widget(SectionTabs::new(&card.sections, sel, &theme), p.tabs);
        self.view.render_in_frame(frame, p.detail, blocks, &theme);
        render_source_bar(frame, p.source, self.view.selected_source(blocks), &theme);
        help::render_footer(frame, p.footer, FOOTER_KEYS, self.flash.as_deref(), &theme);
        if self.inspector.is_open() {
            self.inspector.render(frame, area, &theme);
        }
        if self.help {
            let all: Vec<Key> = SCREEN_KEYS.iter().chain(SOURCE_KEYS).copied().collect();
            help::render_overlay(
                frame,
                area,
                &format!(" {} CANSLIM keys ", self.symbol),
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
                    self.select_letter(i);
                    Action::None
                }
                _ => Action::None,
            };
        }
        if self.help {
            self.help = false;
            return Action::None;
        }
        if self.inspector.is_open() {
            return self.inspector.on_key(key);
        }
        if key.code == KeyCode::Char('p') && key.modifiers.contains(KeyModifiers::CONTROL) {
            let mut entries = command_palette::destinations(&self.symbol, "canslim");
            if let Some(card) = self.card.as_ref() {
                entries.extend(card.sections.iter().enumerate().map(|(i, s)| {
                    Entry::new(
                        format!("Go to {}", s.title),
                        format!("letter {}", i + 1),
                        Command::Section(i),
                    )
                }));
            }
            self.palette.show(entries);
            return Action::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('s') => return back_to_picker(),
            KeyCode::Char('r') => {
                self.reload();
                self.flash = Some(
                    if self.card.is_some() {
                        "reloaded"
                    } else {
                        "reload: nothing cached"
                    }
                    .into(),
                );
            }
            _ if self.card.is_none() => {}
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char('a') => {
                self.view.audit = !self.view.audit;
            }
            KeyCode::Char('L') | KeyCode::Char(']') => self.select_letter(self.selected() + 1),
            KeyCode::Char('H') | KeyCode::Char('[') => {
                self.select_letter(self.selected().saturating_sub(1))
            }
            KeyCode::Char(c @ '1'..='7') => self.select_letter(c as usize - '1' as usize),
            KeyCode::Char('o') => match self
                .card
                .as_ref()
                .and_then(|c| c.overall.as_ref()?.src.clone())
            {
                Some(s) => self.inspector.open(&s),
                None => self.flash = Some("no overall grade".into()),
            },
            KeyCode::Char('i') => match self.selected_source().cloned() {
                Some(s) => self.inspector.open(&s),
                None => self.flash = Some("no source here".into()),
            },
            _ => {
                if let Some(a) = source_action(key, self.selected_source()) {
                    return a;
                }
                let blocks = self.blocks().to_vec();
                let theme = self.theme;
                self.view.on_key(key, &blocks, &theme);
            }
        }
        Action::None
    }

    fn set_flash(&mut self, msg: String) {
        self.flash = Some(msg);
    }
}

/// `s`: reopen the fzf symbol picker in nvim. Through the action file when
/// ui/portfolio_chart.lua provided one, else the legacy exit-90 sentinel
/// its shell wrapper watches for.
fn back_to_picker() -> Action {
    if std::env::var_os("SECURITY_SPREAD_ACTION_FILE").is_some() {
        Action::Nvim(NvimAction::Picker {
            screen: "canslim".into(),
        })
    } else {
        Action::Exit(EXIT_BACK_TO_PICKER)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::Terminal;
    use ratatui::backend::TestBackend;
    use ratatui::crossterm::event::KeyModifiers;

    const FIXTURE: &str = include_str!("fixtures/canslim_MRVL.json");

    fn screen() -> Canslim {
        Canslim::from_json("MRVL", FIXTURE, Theme::default())
    }

    fn press(s: &mut Canslim, c: KeyCode) -> Action {
        s.on_key(KeyEvent::new(c, KeyModifiers::NONE))
    }

    fn render(s: &mut Canslim, w: u16, h: u16) -> String {
        let mut t = Terminal::new(TestBackend::new(w, h)).expect("test terminal");
        t.draw(|f| s.draw(f)).expect("draw");
        let buf = t.backend().buffer();
        (0..h)
            .map(|y| (0..w).map(|x| buf[(x, y)].symbol()).collect::<String>() + "\n")
            .collect()
    }

    #[test]
    fn fixture_has_seven_sourced_letters() {
        let s = screen();
        let card = s.card.as_ref().expect("fixture parses");
        let ids: Vec<&str> = card.sections.iter().map(|s| s.id.as_str()).collect();
        assert_eq!(ids, ["c", "a", "n", "s", "l", "i", "m"]);
        for sec in &card.sections {
            assert!(!sec.badge.is_empty(), "{} has a grade badge", sec.id);
            for b in &sec.blocks {
                for i in 0..b.len() {
                    let src = b
                        .source(i)
                        .unwrap_or_else(|| panic!("{} / {} item {i} unsourced", sec.id, b.title()));
                    assert!(
                        src.url.is_some() || src.formula.is_some(),
                        "{}: {src:?}",
                        sec.id
                    );
                }
            }
        }
        assert!(card.overall.as_ref().and_then(|o| o.src.as_ref()).is_some());
    }

    #[test]
    fn renders_header_nav_and_rule() {
        let mut s = screen();
        let out = render(&mut s, 160, 48);
        assert!(out.contains("MRVL"), "{out}");
        assert!(out.contains("CANSLIM"), "{out}");
        assert!(out.contains("overall"), "{out}");
        assert!(out.contains("Current earnings"), "{out}");
        // letters are a one-row tab strip under the header, every grade visible
        let tabs = out.lines().nth(1).unwrap_or("");
        for badge in ["C 59", "D 31", "F 17", "A 82", "A 100"] {
            assert!(tabs.contains(badge), "{badge} missing from tab row: {tabs}");
        }
        assert!(tabs.contains("M Market"), "{tabs}");
    }

    #[test]
    fn no_panic_at_small_sizes() {
        for (w, h) in [
            (0, 0),
            (1, 1),
            (10, 3),
            (20, 6),
            (40, 10),
            (80, 24),
            (3, 40),
        ] {
            let mut s = screen();
            for k in [
                KeyCode::Char('L'),
                KeyCode::Char('j'),
                KeyCode::Char('l'),
                KeyCode::Char('a'),
                KeyCode::Char('?'),
            ] {
                render(&mut s, w, h);
                press(&mut s, k);
            }
            render(&mut s, w, h);
        }
    }

    #[test]
    fn letter_keys_and_cursor_sources() {
        let mut s = screen();
        press(&mut s, KeyCode::Char('7'));
        assert_eq!(s.selected(), 6);
        press(&mut s, KeyCode::Char('L'));
        assert_eq!(s.selected(), 6, "clamps at M");
        press(&mut s, KeyCode::Char('H'));
        assert_eq!(s.selected(), 5);
        press(&mut s, KeyCode::Char('h'));
        assert_eq!(s.selected(), 5, "h moves between containers, not letters");
        // every item of every letter has a source
        for l in 0..7 {
            s.select_letter(l);
            for (bi, b) in s.blocks().to_vec().iter().enumerate() {
                for item in 0..b.len() {
                    s.view.cursor = crate::ui::block_view::Cursor { block: bi, item };
                    assert!(
                        s.selected_source().is_some(),
                        "letter {l} cursor {:?}",
                        s.view.cursor
                    );
                }
            }
        }
        press(&mut s, KeyCode::Char('o'));
        assert!(s.inspector.is_open());
        press(&mut s, KeyCode::Esc);
        assert!(!s.inspector.is_open());
        assert_eq!(press(&mut s, KeyCode::Char('q')), Action::Quit);
    }

    #[test]
    fn missing_or_legacy_cache_shows_message() {
        let mut s = Canslim::from_json(
            "ZZZ",
            r#"{"symbol":"ZZZ","as_of":"2026-01-01"}"#,
            Theme::default(),
        );
        assert!(s.card.is_none());
        assert!(render(&mut s, 80, 20).contains("canslim.py ZZZ --force"));
        let mut s = Canslim::from_json("ZZZ", "not json", Theme::default());
        assert!(s.card.is_none());
        render(&mut s, 30, 5);
        assert_eq!(press(&mut s, KeyCode::Char('q')), Action::Quit);
    }
}
