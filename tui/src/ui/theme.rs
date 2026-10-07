// Colours come from nvim's colorscheme (passed as #rrggbb CLI args by
// ui/tui.lua) so every screen blends with the editor. Screens
// never hardcode colours: they ask the theme for a semantic style.

use ratatui::layout::Rect;
use ratatui::style::{Color, Modifier, Style};

use crate::ui::spacing::Spacing;

#[derive(Debug, Clone, Copy)]
pub struct Theme {
    /// None = inherit the terminal background (transparent colorschemes).
    pub bg: Option<Color>,
    pub up: Color,
    pub down: Color,
    pub fg: Color,
    pub dim: Color,
    pub accent: Color,
    pub border: Color,
    pub spacing: Spacing,
    cursor_bg: Option<Color>,
}

impl Default for Theme {
    fn default() -> Self {
        Self {
            bg: None,
            up: Color::Rgb(0x4d, 0x93, 0x75),
            down: Color::Rgb(0xc2, 0x5c, 0x5c),
            fg: Color::White,
            dim: Color::DarkGray,
            accent: Color::Rgb(0xd7, 0xa6, 0x5f),
            border: Color::DarkGray,
            spacing: Spacing::default(),
            cursor_bg: Some(Color::Rgb(0x3d, 0x3f, 0x50)),
        }
    }
}

/// #rrggbb -> Color; None on anything unparseable (degrade, don't crash).
pub fn parse_hex(s: &str) -> Option<Color> {
    let s = s.trim_start_matches('#');
    if s.len() != 6 {
        return None;
    }
    let n = u32::from_str_radix(s, 16).ok()?;
    Some(Color::from_u32(n))
}

impl Theme {
    /// From the positional CLI args `<bg> <fg_up> <fg_down>`.
    pub fn from_args(bg: Option<&str>, up: Option<&str>, down: Option<&str>) -> Self {
        let d = Self::default();
        Self {
            bg: bg.and_then(parse_hex),
            up: up.and_then(parse_hex).unwrap_or(d.up),
            down: down.and_then(parse_hex).unwrap_or(d.down),
            cursor_bg: std::env::var("FINLARP_CURSOR_BG")
                .ok()
                .as_deref()
                .and_then(parse_hex)
                .or(d.cursor_bg),
            ..d
        }
    }

    /// Refresh shared spacing tokens at each draw so all panels adapt together.
    pub fn fit(&mut self, area: Rect) {
        self.spacing = Spacing::for_area(area);
    }

    pub fn base(&self) -> Style {
        let s = Style::new().fg(self.fg);
        match self.bg {
            Some(bg) => s.bg(bg),
            None => s,
        }
    }
    pub fn dim(&self) -> Style {
        self.base().fg(self.dim)
    }
    pub fn border(&self) -> Style {
        self.base().fg(self.border)
    }
    pub fn title(&self) -> Style {
        self.base().add_modifier(Modifier::BOLD)
    }
    pub fn accent(&self) -> Style {
        self.base().fg(self.accent)
    }
    /// Selected row / cell.
    pub fn selected(&self) -> Style {
        match self.cursor_bg {
            Some(bg) => self.base().bg(bg),
            None => self.base().add_modifier(Modifier::REVERSED),
        }
    }
    pub fn sel_bg(&self) -> Color {
        self.cursor_bg.unwrap_or(self.fg)
    }
    /// Keep foreground contrast when applying the cursor background to a semantic style.
    pub fn on_cursor(&self, style: Style) -> Style {
        match self.cursor_bg {
            Some(bg) => style.bg(bg),
            None => style.add_modifier(Modifier::REVERSED),
        }
    }
    /// Green for >= 0, red for < 0.
    pub fn signed(&self, v: f64) -> Style {
        self.base().fg(if v >= 0.0 { self.up } else { self.down })
    }
    pub fn up(&self) -> Style {
        self.base().fg(self.up)
    }
    pub fn down(&self) -> Style {
        self.base().fg(self.down)
    }
    /// Marker for recent (`new`) items.
    pub fn new_marker(&self) -> Style {
        self.accent()
    }
    /// Values that are computed (formula) rather than read from a document.
    pub fn derived(&self) -> Style {
        self.base().add_modifier(Modifier::ITALIC)
    }
    /// CANSLIM score color: low scores red, middling amber, high scores green.
    pub fn score(&self, value: f64) -> Style {
        let color = if value >= 70.0 {
            self.up
        } else if value >= 50.0 {
            self.accent
        } else {
            self.down
        };
        self.base().fg(color).add_modifier(Modifier::BOLD)
    }
    pub fn score_badge(&self, badge: &str) -> Style {
        match badge.rsplit(' ').next().and_then(|n| n.parse::<f64>().ok()) {
            Some(value) => self.score(value),
            None => self.dim(),
        }
    }
}
