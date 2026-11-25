// A candle chart drawn as a picture, the way the intraday tiles draw theirs: bars go
// through `intraday::picture` into pixels, then out through the terminal's graphics
// protocol (kitty, sixel, iTerm). Any screen can hold one; `draw` returns false where the
// terminal has no graphics protocol so the caller falls back to its text chart.
//
// The terminal is asked what it supports when the chart is made (`probe`), which reads the
// answer on stdin, so make it in the screen's `open`, before the event loop starts reading.
// The picture is rebuilt only when the bars or the area change.

use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

use image::{DynamicImage, RgbaImage};
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui_image::picker::cap_parser::QueryStdioOptions;
use ratatui_image::picker::{Capability, Picker, ProtocolType};
use ratatui_image::protocol::StatefulProtocol;
use ratatui_image::protocol::StatefulProtocolType;
use ratatui_image::protocol::kitty::StatefulKitty;
use ratatui_image::{Resize, ResizeEncodeRender, StatefulImage};

use crate::screens::intraday::picture::{self, Pic};
use crate::ui::hcandles::{HBar, Session};
use crate::ui::pixels::Palette;
use crate::ui::theme::Theme;

pub struct PicChart {
    picker: Option<Picker>,
    pal: Palette,
    scratch: RgbaImage,
    /// The picture on screen and what it was built from.
    slot: Option<(u64, StatefulProtocol)>,
    /// Kitty image id base; two ids are used in turn so a resend never flashes blank.
    id: u32,
    which: u8,
}

impl PicChart {
    /// Asks the terminal for a graphics protocol. `id` tells this chart's kitty images
    /// apart from other charts on screen (any small number unique per screen).
    pub fn probe(theme: &Theme, id: u8) -> Self {
        let mut c = Self::none(theme, id);
        if cfg!(test) || std::env::var_os("FL_NO_PICS").is_some() {
            return c;
        }
        let options = QueryStdioOptions {
            kitty_compression: true,
            terminal_background_color_osc: true,
            ..Default::default()
        };
        c.picker = Picker::from_query_stdio_with_options(options)
            .ok()
            .filter(|p| p.protocol_type() != ProtocolType::Halfblocks);
        if let Some(bg) = c.picker.as_ref().and_then(|p| {
            p.capabilities().iter().find_map(|cap| match cap {
                Capability::Background(r, g, b) => Some([*r, *g, *b, 255]),
                _ => None,
            })
        }) {
            c.pal.bg = bg;
        }
        c
    }

    /// A chart that never draws (text fallbacks only).
    pub fn none(theme: &Theme, id: u8) -> Self {
        Self {
            picker: None,
            pal: Palette::from_theme(theme),
            scratch: RgbaImage::new(1, 1),
            slot: None,
            id: u32::from_be_bytes([0, 0xF1, 0xDC, id.wrapping_mul(2)]),
            which: 0,
        }
    }

    pub fn available(&self) -> bool {
        self.picker.is_some()
    }

    /// Draws `bars` (oldest first; only the newest that fit are shown) into `area`.
    /// False when there is no graphics protocol or nothing to draw.
    pub fn draw(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        bars: &[HBar],
        vwap: Option<f64>,
        prev_close: Option<f64>,
    ) -> bool {
        let Some(picker) = self.picker.as_ref() else {
            return false;
        };
        if bars.len() < 2 || area.width < 4 || area.height < 3 {
            return false;
        }
        let font = picker.font_size();
        let px = (
            area.width as u32 * u32::from(font.width),
            area.height as u32 * u32::from(font.height),
        );
        let key = {
            let mut h = DefaultHasher::new();
            px.hash(&mut h);
            (area.x, area.y).hash(&mut h);
            for b in bars {
                b.label.hash(&mut h);
                b.close.to_bits().hash(&mut h);
                b.high.to_bits().hash(&mut h);
                b.low.to_bits().hash(&mut h);
                b.volume.hash(&mut h);
            }
            vwap.map(f64::to_bits).hash(&mut h);
            prev_close.map(f64::to_bits).hash(&mut h);
            h.finish()
        };
        let resize = Resize::Fit(None);
        if self.slot.as_ref().is_none_or(|(k, _)| *k != key) {
            if self.scratch.dimensions() != px {
                self.scratch = RgbaImage::new(px.0.max(1), px.1.max(1));
            }
            let pic = Pic {
                bars,
                vwap,
                prev_close,
                sel: None,
                range: None,
            };
            picture::render_into(&mut self.scratch, &pic, &self.pal);
            let img = DynamicImage::ImageRgba8(self.scratch.clone());
            let id = self.id + self.which as u32 + 1;
            self.which ^= 1;
            let mut proto = protocol(picker, img, id);
            if let Some(size) = proto.needs_resize(&resize, area.into()) {
                proto.resize_encode(&resize, size);
            }
            self.slot = Some((key, proto));
        }
        if let Some((_, proto)) = self.slot.as_mut() {
            frame.render_stateful_widget(StatefulImage::default().resize(resize), area, proto);
        }
        true
    }
}

impl PicChart {
    /// Any picture: `make(w, h)` draws it at the area's pixel size, and only when `key`
    /// (what the picture shows) or the area changed. False without a graphics protocol.
    pub fn draw_image(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        key: u64,
        make: impl FnOnce(u32, u32) -> Option<RgbaImage>,
    ) -> bool {
        let Some(picker) = self.picker.as_ref() else {
            return false;
        };
        if area.width < 4 || area.height < 2 {
            return false;
        }
        let font = picker.font_size();
        let px = (
            area.width as u32 * u32::from(font.width),
            area.height as u32 * u32::from(font.height),
        );
        let key = {
            let mut h = DefaultHasher::new();
            (key, px, area.x, area.y).hash(&mut h);
            h.finish()
        };
        let resize = Resize::Fit(None);
        if self.slot.as_ref().is_none_or(|(k, _)| *k != key) {
            let Some(img) = make(px.0, px.1) else {
                return false;
            };
            let id = self.id + self.which as u32 + 1;
            self.which ^= 1;
            let mut proto = protocol(picker, DynamicImage::ImageRgba8(img), id);
            if let Some(size) = proto.needs_resize(&resize, area.into()) {
                proto.resize_encode(&resize, size);
            }
            self.slot = Some((key, proto));
        }
        if let Some((_, proto)) = self.slot.as_mut() {
            frame.render_stateful_widget(StatefulImage::default().resize(resize), area, proto);
        }
        true
    }
}

/// Kitty gets a stable id (so the old picture is replaced, not piled up); other protocols
/// use ratatui-image's own.
fn protocol(picker: &Picker, img: DynamicImage, id: u32) -> StatefulProtocol {
    if picker.protocol_type() != ProtocolType::Kitty {
        return picker.new_resize_protocol(img);
    }
    let caps = picker.capabilities();
    StatefulProtocol::new(
        img,
        picker.font_size(),
        None,
        StatefulProtocolType::Kitty(StatefulKitty::new(
            id,
            picker.tmux_detected(),
            caps.contains(&Capability::KittyCompression),
            caps.contains(&Capability::KittySharedMemory),
        )),
    )
}

/// Candles from closes only (daily closes): each bar opens at the close before it, so the
/// body shows the day's move; high and low are the two ends.
pub fn bars_from_closes(closes: &[(String, f64)]) -> Vec<HBar> {
    let mut prev = closes.first().map(|c| c.1).unwrap_or(0.0);
    closes
        .iter()
        .map(|(label, c)| {
            let b = HBar {
                label: label.clone(),
                open: prev,
                high: prev.max(*c),
                low: prev.min(*c),
                close: *c,
                volume: 0,
                session: Session::Regular,
            };
            prev = *c;
            b
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn closes_become_candles_that_open_at_the_prior_close() {
        let b = bars_from_closes(&[("a".into(), 10.0), ("b".into(), 12.0), ("c".into(), 11.0)]);
        assert_eq!(b.len(), 3);
        assert_eq!((b[1].open, b[1].close, b[1].high, b[1].low), (10.0, 12.0, 12.0, 10.0));
        assert!(!b[2].is_up());
        let c = PicChart::none(&Theme::from_args(None, None, None), 1);
        assert!(!c.available());
    }
}
