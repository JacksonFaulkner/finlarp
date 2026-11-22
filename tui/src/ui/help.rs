// Key help: one `?` menu, no key hints on screen.
//
// Every screen declares its keys once, as `Key` rows, and returns them from
// `Screen::help`. The app draws them in a popup (KeyOverlay) when `?` is
// pressed; any key closes it. The global keys (`<space>` chords, `?` itself)
// are listed under the screen's own keys.
//
// The coverage test at the bottom of this file reads the screen sources and
// fails when a key is handled in code but not declared in its `help()` rows.
// Add the row in the same change as the key.

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

/// A section title inside a key list (the overlay draws it as a heading).
pub const fn section(title: &'static str) -> Key {
    Key {
        keys: "",
        desc: title,
    }
}

/// What a screen shows in the `?` menu: its title and its keys.
#[derive(Debug, Clone)]
pub struct Help {
    pub title: &'static str,
    pub keys: Vec<Key>,
}

impl Help {
    pub fn new(title: &'static str, keys: &[Key]) -> Self {
        Self {
            title,
            keys: keys.to_vec(),
        }
    }
}

/// Keys that work on every screen. The app draws them under each screen's own
/// list; the chord handling in app.rs must match these rows.
pub const GLOBAL_KEYS: &[Key] = &[
    key("?", "this menu"),
    key("spc y", "copy the visual selection"),
    key("spc a c", "toggle the Claude window"),
    key("spc a s", "add the selected value to Claude"),
    key("spc a w", "ask Claude about the open diagram"),
    key("spc t o", "lazygit in a new tmux window"),
    key("spc w q", "rebuild fl and restart"),
    key("^c", "quit"),
];

/// Keys every sourced screen shares (see ui::source_bar::source_action).
pub const SOURCE_KEYS: &[Key] = &[
    key("↵", "open source in browser"),
    key("v", "open source document in browser"),
    key("y", "copy source URL"),
    key("i", "inspect formula inputs"),
    key("a", "audit overlay"),
    key("esc / ⌫", "close the inspector / back up a level"),
];

/// Movement keys understood by `block_view::BlockView::on_key`.
pub const BLOCK_KEYS: &[Key] = &[
    key("j/k", "next / previous item"),
    key("g/G", "first / last item"),
    key("^d/^u", "half page down / up"),
    key("tab/S-tab", "next / previous block"),
    key("h/l", "previous / next table column"),
];

/// Full-screen overlay listing all keys (centered popup over `area`).
pub fn render_overlay(frame: &mut Frame, area: Rect, title: &str, keys: &[Key], theme: &Theme) {
    frame.render_widget(KeyOverlay { title, keys, theme }, area);
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
        let col_w = kw + dw + 2;
        // Two columns when one would be taller than the screen.
        let n = self.keys.len() as u16;
        let cols: u16 = if n + 2 > area.height && area.width >= 2 * col_w + 7 {
            2
        } else {
            1
        };
        let per = n.div_ceil(cols);
        let width = (cols * col_w + (cols - 1) * 3 + 4).max(tw).max(24);
        let height = per + 2;
        let r = crate::ui::layout::popup(area, width, height);
        if r.is_empty() {
            return;
        }
        Clear.render(r, buf);
        let row = |k: &Key| {
            if k.keys.is_empty() {
                Row::new([
                    Cell::from(Span::styled("──", th.dim())),
                    Cell::from(Span::styled(k.desc, th.title())),
                ])
            } else {
                Row::new([
                    Cell::from(Span::styled(k.keys, th.accent())),
                    Cell::from(Span::styled(k.desc, th.base())),
                ])
            }
        };
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
        let inner = block.inner(r);
        block.render(r, buf);
        let parts = ratatui::layout::Layout::horizontal(vec![Constraint::Fill(1); cols as usize])
            .spacing(3)
            .split(inner);
        for (i, part) in parts.iter().enumerate() {
            let chunk = self
                .keys
                .iter()
                .skip(i * per as usize)
                .take(per as usize)
                .map(row);
            Table::new(chunk, [Constraint::Length(kw), Constraint::Fill(1)])
                .column_spacing(2)
                .render(*part, buf);
        }
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
    fn overlay_lists_keys() {
        let th = Theme::default();
        let out = draw(60, 20, |f| {
            render_overlay(f, f.area(), "dossier keys", SOURCE_KEYS, &th)
        });
        assert!(out.contains("dossier keys"), "{out}");
        assert!(out.contains("inspect formula inputs"), "{out}");
        for (w, h) in [(10, 3), (1, 1), (0, 0)] {
            draw(w, h, |f| render_overlay(f, f.area(), "k", KEYS, &th));
            draw(w, h, |f| render_overlay(f, f.area(), "k", &[], &th));
        }
    }
}

/// Keeps the `?` menus honest: every key a screen or the app handles must be
/// declared in a `key(…)` row. Reads the sources, so it runs in plain
/// `cargo test` and an agent adding a key sees it fail until the row exists.
#[cfg(test)]
mod coverage {
    use std::collections::BTreeMap;
    use std::fs;
    use std::path::{Path, PathBuf};

    /// Chars a screen group may handle without declaring them: `?` opens this
    /// menu everywhere, and the shared rows below are declared once in help.rs.
    const ALWAYS: &[&str] = &["?"];

    fn src() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("src")
    }

    /// The file text before its test module, so test literals don't count.
    fn code(path: &Path) -> String {
        let text = fs::read_to_string(path).unwrap_or_default();
        match text.find("#[cfg(test)]") {
            Some(i) => text[..i].to_string(),
            None => text,
        }
    }

    fn rs_files(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = fs::read_dir(dir) else {
            return;
        };
        for e in entries.flatten() {
            let p = e.path();
            if p.is_dir() {
                rs_files(&p, out);
            } else if p.extension().is_some_and(|x| x == "rs")
                && p.file_name().is_some_and(|n| n != "tests.rs")
            {
                out.push(p);
            }
        }
    }

    /// The chars named in `'x'` literals inside each `marker(...)` in `text`.
    fn literals(text: &str, marker: &str) -> Vec<char> {
        let mut out = Vec::new();
        for (i, _) in text.match_indices(marker) {
            let rest = &text[i + marker.len()..];
            let end = rest.find(')').unwrap_or(rest.len());
            let chars: Vec<char> = rest[..end].chars().collect();
            for w in chars.windows(3) {
                if w[0] == '\'' && w[2] == '\'' && w[1] != '\\' {
                    out.push(w[1]);
                }
            }
        }
        out
    }

    /// The text of `const NAME: … = &[ … ];` (or empty if absent).
    fn block<'a>(text: &'a str, name: &str) -> &'a str {
        let Some(i) = text.find(name) else {
            return "";
        };
        let rest = &text[i..];
        &rest[..rest.find("];").unwrap_or(rest.len())]
    }

    /// Tokens of every `key("…", …)` row in `text`, split the way a key reads:
    /// "j/k" → j k, "^d/^u" → d u, "spc a c" → spc a c, "-/_" → - _, "/" → /,
    /// "[ ]" → [ ], "]]" → ] (bracket runs name each bracket).
    fn tokens(text: &str) -> Vec<String> {
        let mut out = Vec::new();
        for (i, _) in text.match_indices("key(") {
            // rustfmt may break the call: `key(\n    "x",` still counts
            let before = text[..i].chars().last();
            if before.is_some_and(|c| c.is_alphanumeric() || c == '_') {
                continue;
            }
            let rest = text[i + 4..].trim_start();
            let Some(rest) = rest.strip_prefix('"') else {
                continue;
            };
            let Some(end) = rest.find('"') else {
                continue;
            };
            for word in rest[..end].split(' ') {
                if word.contains(['[', ']']) {
                    out.extend(word.chars().filter(|c| *c != '/').map(|c| c.to_string()));
                }
                if word.chars().count() == 1 {
                    out.push(word.to_string());
                }
                for part in word.split('/') {
                    if part.chars().count() == 1 {
                        out.push(part.to_string());
                    } else {
                        for t in part.split(['-', '^', '·', ',', '|']) {
                            if !t.is_empty() {
                                out.push(if t == "space" {
                                    "spc".into()
                                } else {
                                    t.to_string()
                                });
                            }
                        }
                    }
                }
            }
        }
        out
    }

    fn token_of(c: char) -> String {
        if c == ' ' {
            "spc".into()
        } else {
            c.to_string()
        }
    }

    /// Screen group of a file under src/screens: a directory is its own group
    /// (intraday/, search/, diagrams_lab/ is part of diagrams/); a top-level file
    /// is its own group, except the diagrams_* files, which are the diagrams screen.
    fn group(rel: &Path) -> String {
        let first = rel
            .components()
            .next()
            .unwrap()
            .as_os_str()
            .to_string_lossy();
        let stem = first.trim_end_matches(".rs");
        if stem.starts_with("diagrams") {
            "diagrams".to_string()
        } else {
            stem.to_string()
        }
    }

    #[test]
    fn every_handled_key_is_in_a_help_menu() {
        let help_src = fs::read_to_string(src().join("ui/help.rs")).unwrap();
        let shared: Vec<String> = tokens(block(&help_src, "const SOURCE_KEYS"))
            .into_iter()
            .chain(tokens(block(&help_src, "const BLOCK_KEYS")))
            .collect();
        let global: Vec<String> = tokens(block(&help_src, "const GLOBAL_KEYS"));

        let mut files = Vec::new();
        rs_files(&src().join("screens"), &mut files);
        // group -> (declared tokens, handled chars with the file they came from)
        let mut groups: BTreeMap<String, (Vec<String>, Vec<(char, String)>, bool)> =
            BTreeMap::new();
        for f in &files {
            let rel = f.strip_prefix(src().join("screens")).unwrap();
            let g = groups.entry(group(rel)).or_default();
            let text = code(f);
            g.0.extend(tokens(&text));
            if text.contains("impl Screen for") {
                g.2 = true;
            }
            for marker in ["KeyCode::Char(", "is_plain(&key, "] {
                for c in literals(&text, marker) {
                    g.1.push((c, rel.display().to_string()));
                }
            }
        }

        let mut errors = Vec::new();
        for (name, (declared, handled, is_screen)) in &groups {
            if *is_screen && !declared.iter().any(|t| !t.is_empty()) {
                errors.push(format!("screen group {name}: no key(…) rows in help()"));
            }
            for (c, file) in handled {
                let t = token_of(*c);
                let ok =
                    ALWAYS.contains(&t.as_str()) || declared.contains(&t) || shared.contains(&t);
                if !ok {
                    errors.push(format!(
                        "{file}: key {c:?} is handled but no help() row declares it; add key(\"{t}\", \"…\") to this screen's keys"
                    ));
                }
            }
        }

        // The app's own chords (space leader, ^c, ?) must be in GLOBAL_KEYS.
        let app = fs::read_to_string(src().join("app.rs")).unwrap();
        let app = app.split("#[cfg(test)]").next().unwrap();
        for c in literals(app, "is_plain(&key, ")
            .into_iter()
            .chain(literals(app, "KeyCode::Char("))
        {
            let t = token_of(c);
            if !global.contains(&t) {
                errors.push(format!(
                    "app.rs: chord key {c:?} is not in help::GLOBAL_KEYS; add key(\"spc …\", \"…\")"
                ));
            }
        }

        assert!(
            errors.is_empty(),
            "undeclared keys ({}):\n  {}",
            errors.len(),
            errors.join("\n  ")
        );
    }
}
