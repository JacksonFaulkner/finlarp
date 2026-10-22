//! Spinner for work in flight: a throbber with an optional label, drawn in
//! the screen's own style. The owner keeps the `ThrobberState` and calls
//! `calc_next` once per frame while the work is pending.

use ratatui::{style::Style, text::Line};
use throbber_widgets_tui::{Throbber, ThrobberState};

/// One frame of the spinner as a line, e.g. `⠋ refreshing`.
pub fn line<'a>(state: &ThrobberState, label: &'a str, style: Style) -> Line<'a> {
    Throbber::default().label(label).style(style).to_line(state)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frame_carries_the_label_and_advances() {
        let mut state = ThrobberState::default();
        let first = line(&state, "refreshing", Style::new()).to_string();
        state.calc_next();
        let second = line(&state, "refreshing", Style::new()).to_string();
        assert!(first.ends_with("refreshing") && second.ends_with("refreshing"));
        assert_ne!(first, second);
    }
}
