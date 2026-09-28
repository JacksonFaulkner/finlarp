// Spacing tokens. Components never hardcode padding / gaps: they read
// `theme.spacing`, which screens refresh from the frame size each draw
// (`theme.fit(area)`). Tuning a gap is then a one-line change here, and
// every screen tightens the same way when the popup is small.
//
//   Compact   narrow or short popups (< 100 cols or < 30 rows)
//   Normal    the usual full-screen tmux popup
//   Roomy     wide monitors (>= 170 cols)

use ratatui::layout::Rect;

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub enum Density {
    Compact,
    #[default]
    Normal,
    Roomy,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Spacing {
    pub density: Density,
    /// Blank columns inside a pane's left/right border.
    pub pad_x: u16,
    /// Blank lines between stacked blocks in a pane.
    pub block_gap: u16,
    /// Indent of rows under a block title.
    pub indent: u16,
    /// Blank columns between table columns.
    pub col_gap: u16,
    /// Blank columns either side of a tab label.
    pub tab_pad: u16,
}

impl Spacing {
    pub const fn of(density: Density) -> Self {
        match density {
            Density::Compact => Self {
                density,
                pad_x: 0,
                block_gap: 0,
                indent: 1,
                col_gap: 1,
                tab_pad: 1,
            },
            Density::Normal => Self {
                density,
                pad_x: 1,
                block_gap: 1,
                indent: 2,
                col_gap: 2,
                tab_pad: 1,
            },
            Density::Roomy => Self {
                density,
                pad_x: 2,
                block_gap: 1,
                indent: 3,
                col_gap: 3,
                tab_pad: 2,
            },
        }
    }

    /// Density breakpoints from the whole screen area.
    pub fn for_area(area: Rect) -> Self {
        let d = if area.width < 100 || area.height < 30 {
            Density::Compact
        } else if area.width >= 170 {
            Density::Roomy
        } else {
            Density::Normal
        };
        Self::of(d)
    }

    /// `area` minus `pad_x` on both sides.
    pub fn inset(&self, area: Rect) -> Rect {
        let p = self.pad_x.min(area.width / 2);
        Rect {
            x: area.x + p,
            width: area.width - 2 * p,
            ..area
        }
    }
}

impl Default for Spacing {
    fn default() -> Self {
        Self::of(Density::Normal)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn breakpoints() {
        assert_eq!(
            Spacing::for_area(Rect::new(0, 0, 80, 40)).density,
            Density::Compact
        );
        assert_eq!(
            Spacing::for_area(Rect::new(0, 0, 150, 20)).density,
            Density::Compact
        );
        assert_eq!(
            Spacing::for_area(Rect::new(0, 0, 150, 45)).density,
            Density::Normal
        );
        assert_eq!(
            Spacing::for_area(Rect::new(0, 0, 200, 50)).density,
            Density::Roomy
        );
    }

    #[test]
    fn inset_never_underflows() {
        let s = Spacing::of(Density::Roomy);
        assert_eq!(s.inset(Rect::new(0, 0, 3, 1)).width, 1);
        assert_eq!(s.inset(Rect::new(5, 0, 20, 1)), Rect::new(7, 0, 16, 1));
    }
}
