// Kitty animation for picture scenes (opt-in: FL_KITTY_ANIM=1).
//
// A beat's frames are uploaded once: the first is transmitted with a virtual placement (U=1) and
// the rest are added as animation frames (a=f). The terminal loops them on its own (a=a), so a
// running picture sends nothing per tick. The picture is shown through unicode placeholder cells;
// the placeholder's foreground colour names the image, so stepping to a beat that is already loaded
// only changes those cells. Three image slots hold the beat on screen, the one before and the one
// after; a slot is freed (a=d) before it is reused.
//
// Needs a kitty-graphics terminal with animation (kitty, Ghostty 1.4+). Inside tmux every escape is
// wrapped for passthrough.

use std::io::{self, Write};

use flate2::Compression;
use flate2::write::ZlibEncoder;
use image::RgbaImage;
use ratatui::Frame;
use ratatui::buffer::CellDiffOption;
use ratatui::layout::Rect;
use ratatui::style::Color;

use crate::ui::anim::Time;

/// Image ids of the three slots. Kept apart from the ids the picture path uses.
const IMAGE_BASE: u32 = 0x00F4_0000;
const SLOTS: usize = 3;
/// Animation frames a second, and frame pixels as a share of the cell area (the terminal scales the
/// frame up to the cells, so a half-size frame keeps the upload small).
pub const FPS: u32 = 8;
const SCALE: f64 = 0.5;
/// U+10EEEE, the kitty placeholder character.
const PLACEHOLDER: char = '\u{10EEEE}';

/// Kitty's row/column diacritics for placeholder cells (rowcolumn-diacritics.txt).
static DIACRITICS: [u32; 297] = [
    773, 781, 782, 784, 786, 829, 830, 831, 838, 842, 843, 844,
    848, 849, 850, 855, 859, 867, 868, 869, 870, 871, 872, 873,
    874, 875, 876, 877, 878, 879, 1155, 1156, 1157, 1158, 1159, 1426,
    1427, 1428, 1429, 1431, 1432, 1433, 1436, 1437, 1438, 1439, 1440, 1441,
    1448, 1449, 1451, 1452, 1455, 1476, 1552, 1553, 1554, 1555, 1556, 1557,
    1558, 1559, 1623, 1624, 1625, 1626, 1627, 1629, 1630, 1750, 1751, 1752,
    1753, 1754, 1755, 1756, 1759, 1760, 1761, 1762, 1764, 1767, 1768, 1771,
    1772, 1840, 1842, 1843, 1845, 1846, 1850, 1853, 1855, 1856, 1857, 1859,
    1861, 1863, 1865, 1866, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2035,
    2070, 2071, 2072, 2073, 2075, 2076, 2077, 2078, 2079, 2080, 2081, 2082,
    2083, 2085, 2086, 2087, 2089, 2090, 2091, 2092, 2093, 2385, 2387, 2388,
    3970, 3971, 3974, 3975, 4957, 4958, 4959, 6109, 6458, 6679, 6773, 6774,
    6775, 6776, 6777, 6778, 6779, 6780, 7019, 7021, 7022, 7023, 7024, 7025,
    7026, 7027, 7376, 7377, 7378, 7386, 7387, 7392, 7616, 7617, 7619, 7620,
    7621, 7622, 7623, 7624, 7625, 7627, 7628, 7633, 7634, 7635, 7636, 7637,
    7638, 7639, 7640, 7641, 7642, 7643, 7644, 7645, 7646, 7647, 7648, 7649,
    7650, 7651, 7652, 7653, 7654, 7678, 8400, 8401, 8404, 8405, 8406, 8407,
    8411, 8412, 8417, 8423, 8425, 8432, 11503, 11504, 11505, 11744, 11745, 11746,
    11747, 11748, 11749, 11750, 11751, 11752, 11753, 11754, 11755, 11756, 11757, 11758,
    11759, 11760, 11761, 11762, 11763, 11764, 11765, 11766, 11767, 11768, 11769, 11770,
    11771, 11772, 11773, 11774, 11775, 42607, 42620, 42621, 42736, 42737, 43232, 43233,
    43234, 43235, 43236, 43237, 43238, 43239, 43240, 43241, 43242, 43243, 43244, 43245,
    43246, 43247, 43248, 43249, 43696, 43698, 43699, 43703, 43704, 43710, 43711, 43713,
    65056, 65057, 65058, 65059, 65060, 65061, 65062, 68111, 68152, 119173, 119174, 119175,
    119176, 119177, 119210, 119211, 119212, 119213, 119362, 119363, 119364,
];

/// Whether the animated path is on.
pub fn enabled() -> bool {
    std::env::var("FL_KITTY_ANIM").is_ok_and(|v| v == "1")
}

/// What a slot holds: the scene it belongs to, its beat, and the cells it fills.
#[derive(Clone, Copy, Debug, PartialEq)]
struct Loaded {
    scene: u64,
    beat: usize,
    cols: u16,
    rows: u16,
}

/// Where the escapes go: the terminal, or a buffer in tests.
pub enum Sink {
    Stdout,
    #[cfg_attr(not(test), allow(dead_code))]
    Buffer(Vec<u8>),
}

pub struct Anim {
    slots: [Option<Loaded>; SLOTS],
    sink: Sink,
}

impl Default for Anim {
    fn default() -> Self {
        Self { slots: [None; SLOTS], sink: Sink::Stdout }
    }
}

impl Anim {
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn with_sink(sink: Sink) -> Self {
        Self { slots: [None; SLOTS], sink }
    }

    /// Escapes written to the buffer sink (tests).
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn written(&self) -> &[u8] {
        match &self.sink {
            Sink::Buffer(b) => b,
            Sink::Stdout => &[],
        }
    }

    fn emit(&mut self, bytes: &[u8]) {
        match &mut self.sink {
            Sink::Stdout => {
                let mut out = io::stdout().lock();
                let _ = out.write_all(bytes);
                let _ = out.flush();
            }
            Sink::Buffer(b) => b.extend_from_slice(bytes),
        }
    }

    /// Shows beat `beat` of a scene in `area`, looping its frames in the terminal. `render` draws
    /// one frame at the given time and pixel size. Returns false when the frames could not be drawn,
    /// so the caller falls back to the still path.
    #[allow(clippy::too_many_arguments)]
    pub fn paint(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        scene: u64,
        beat: usize,
        beat_ms: u64,
        cell_px: (u16, u16),
        tmux: bool,
        render: &mut dyn FnMut(&Time, u32, u32) -> Option<RgbaImage>,
    ) -> bool {
        if area.width == 0 || area.height == 0 || area.width as usize > DIACRITICS.len()
            || area.height as usize > DIACRITICS.len()
        {
            return false;
        }
        let slot = beat % SLOTS;
        let id = IMAGE_BASE + slot as u32;
        let want = Loaded { scene, beat, cols: area.width, rows: area.height };
        if self.slots[slot] != Some(want) {
            let n = frame_count(beat_ms);
            let (pw, ph) = (
                (f64::from(area.width) * f64::from(cell_px.0) * SCALE).round().max(1.0) as u32,
                (f64::from(area.height) * f64::from(cell_px.1) * SCALE).round().max(1.0) as u32,
            );
            let mut frames = Vec::with_capacity(n as usize);
            for k in 0..n {
                let t = Time {
                    ms: 0,
                    beat,
                    local: k as f32 / n as f32,
                    beat_start: 0,
                };
                match render(&t, pw, ph) {
                    Some(img) => frames.push(img),
                    None => return false,
                }
            }
            let mut bytes = Vec::new();
            if self.slots[slot].is_some() {
                bytes.extend(wrap(&format!("a=d,d=I,i={id},q=2"), tmux));
            }
            bytes.extend(encode(id, &frames, 1000 / FPS, area.width, area.height, tmux));
            self.emit(&bytes);
            self.slots[slot] = Some(want);
        }
        place(frame, area, id);
        true
    }
}

/// Draws the placeholder cells of image `id` over `area`: one per cell, its row and column in
/// diacritics, the id in the colour. The terminal fills them with the image's placement.
pub fn place(frame: &mut Frame, area: Rect, id: u32) {
    let (r, g, b) = (((id >> 16) & 255) as u8, ((id >> 8) & 255) as u8, (id & 255) as u8);
    let buf = frame.buffer_mut();
    let mut symbol = String::with_capacity(12);
    for row in 0..area.height {
        for col in 0..area.width {
            symbol.clear();
            symbol.push(PLACEHOLDER);
            symbol.push(diacritic(row));
            symbol.push(diacritic(col));
            if let Some(cell) = buf.cell_mut((area.x + col, area.y + row)) {
                cell.set_symbol(&symbol)
                    .set_fg(Color::Rgb(r, g, b))
                    .set_diff_option(CellDiffOption::ForcedWidth(
                        std::num::NonZeroU16::new(1).expect("1 is not zero"),
                    ));
            }
        }
    }
}

/// Frames in one beat at FPS, at least one.
pub fn frame_count(beat_ms: u64) -> u32 {
    ((beat_ms as f64 / 1000.0) * f64::from(FPS)).round().max(1.0) as u32
}

fn diacritic(i: u16) -> char {
    char::from_u32(DIACRITICS[usize::from(i)]).unwrap_or('\u{0305}')
}

/// The escapes that load a beat: the root frame with its placement, each further frame (a=f), the
/// root frame's gap, and the loop (a=a,s=3). Every escape is wrapped for tmux when `tmux`.
pub fn encode(id: u32, frames: &[RgbaImage], gap_ms: u32, cols: u16, rows: u16, tmux: bool) -> Vec<u8> {
    let mut out = Vec::new();
    let Some(first) = frames.first() else {
        return out;
    };
    let (w, h) = (first.width(), first.height());
    out.extend(transmit(
        &format!("a=T,U=1,f=32,s={w},v={h},c={cols},r={rows},i={id},o=z,q=2"),
        "",
        first.as_raw(),
        tmux,
    ));
    for img in &frames[1..] {
        out.extend(transmit(
            &format!("a=f,i={id},f=32,s={w},v={h},z={gap_ms},o=z,q=2"),
            &format!("a=f,i={id}"),
            img.as_raw(),
            tmux,
        ));
    }
    out.extend(wrap(&format!("a=a,i={id},r=1,z={gap_ms},q=2"), tmux));
    out.extend(wrap(&format!("a=a,i={id},s=3,q=2"), tmux));
    out
}

/// One image as chunked kitty escapes: zlib, then base64, at most 4096 bytes a chunk.
fn transmit(first_keys: &str, sub_keys: &str, raw: &[u8], tmux: bool) -> Vec<u8> {
    let mut enc = ZlibEncoder::new(Vec::new(), Compression::fast());
    let _ = enc.write_all(raw);
    let packed = enc.finish().unwrap_or_default();
    let data = base64(&packed);
    let mut out = Vec::new();
    let mut pos = 0;
    let mut first = true;
    loop {
        let end = (pos + 4096).min(data.len());
        let more = usize::from(end < data.len());
        let keys = if first { first_keys } else { sub_keys };
        let head = if keys.is_empty() {
            format!("m={more}")
        } else {
            format!("{keys},m={more}")
        };
        let chunk = &data[pos..end];
        out.extend(wrap(&format!("{head};{chunk}"), tmux).into_iter());
        pos = end;
        first = false;
        if more == 0 {
            break;
        }
    }
    out
}

/// One kitty escape body (no ESC _G prefix), as bytes, wrapped for tmux passthrough when needed.
pub(super) fn wrap(body: &str, tmux: bool) -> Vec<u8> {
    let inner = format!("G{body}");
    if tmux {
        let mut out = b"\x1bPtmux;".to_vec();
        for b in format!("\x1b_{inner}\x1b\\").bytes() {
            if b == 0x1b {
                out.push(0x1b);
            }
            out.push(b);
        }
        out.extend_from_slice(b"\x1b\\");
        out
    } else {
        format!("\x1b_{inner}\x1b\\").into_bytes()
    }
}

/// Standard base64 with padding.
pub(super) fn base64(data: &[u8]) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(data.len().div_ceil(3) * 4);
    for chunk in data.chunks(3) {
        let b = [chunk[0], *chunk.get(1).unwrap_or(&0), *chunk.get(2).unwrap_or(&0)];
        let n = (u32::from(b[0]) << 16) | (u32::from(b[1]) << 8) | u32::from(b[2]);
        out.push(T[(n >> 18) as usize & 63] as char);
        out.push(T[(n >> 12) as usize & 63] as char);
        out.push(if chunk.len() > 1 { T[(n >> 6) as usize & 63] as char } else { '=' });
        out.push(if chunk.len() > 2 { T[n as usize & 63] as char } else { '=' });
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn frame(v: u8) -> RgbaImage {
        RgbaImage::from_pixel(8, 4, image::Rgba([v, 0, 0, 255]))
    }

    #[test]
    fn base64_matches_the_standard() {
        assert_eq!(base64(b""), "");
        assert_eq!(base64(b"f"), "Zg==");
        assert_eq!(base64(b"fo"), "Zm8=");
        assert_eq!(base64(b"foo"), "Zm9v");
        assert_eq!(base64(b"foobar"), "Zm9vYmFy");
    }

    #[test]
    fn one_root_transmit_then_a_frame_per_frame_then_the_loop() {
        let frames: Vec<RgbaImage> = (0..4).map(|k| frame(k)).collect();
        let s = String::from_utf8(encode(9, &frames, 125, 10, 3, false)).unwrap();
        assert_eq!(s.matches("a=T,U=1").count(), 1, "one placed root frame");
        assert_eq!(s.matches("a=f,i=9").count(), 3, "three added frames");
        assert!(s.contains("a=a,i=9,r=1,z=125"), "the root gap is set");
        assert!(s.contains("a=a,i=9,s=3"), "the frames loop");
        assert!(s.contains("q=2"), "replies are quiet");
    }

    #[test]
    fn tmux_wraps_every_escape_and_doubles_the_inner_escapes() {
        let frames = vec![frame(1)];
        let s = encode(9, &frames, 125, 10, 3, true);
        let text = String::from_utf8_lossy(&s).to_string();
        assert!(text.starts_with("\x1bPtmux;"), "passthrough open");
        assert!(text.contains("\x1b\x1b_G"), "inner escape is doubled");
    }

    #[test]
    fn a_second_paint_of_the_same_beat_sends_nothing() {
        let mut anim = Anim::with_sink(Sink::Buffer(Vec::new()));
        let mut term = ratatui::Terminal::new(ratatui::backend::TestBackend::new(10, 4)).unwrap();
        let mut render = |_t: &Time, w: u32, h: u32| Some(RgbaImage::from_pixel(w, h, image::Rgba([9, 9, 9, 255])));
        term.draw(|f| {
            assert!(anim.paint(f, Rect::new(0, 0, 10, 4), 1, 0, 200, (10, 20), false, &mut render));
        })
        .unwrap();
        let first = anim.written().len();
        assert!(first > 0, "the first paint uploads the beat");
        term.draw(|f| {
            assert!(anim.paint(f, Rect::new(0, 0, 10, 4), 1, 0, 200, (10, 20), false, &mut render));
        })
        .unwrap();
        assert_eq!(anim.written().len(), first, "the second paint uploads nothing");
    }

    #[test]
    fn cells_name_the_image_through_the_colour() {
        let mut anim = Anim::with_sink(Sink::Buffer(Vec::new()));
        let mut term = ratatui::Terminal::new(ratatui::backend::TestBackend::new(6, 2)).unwrap();
        let mut render = |_t: &Time, w: u32, h: u32| Some(RgbaImage::from_pixel(w, h, image::Rgba([1, 2, 3, 255])));
        term.draw(|f| {
            anim.paint(f, Rect::new(0, 0, 6, 2), 1, 1, 200, (10, 20), false, &mut render);
        })
        .unwrap();
        let cell = &term.backend().buffer()[(0, 0)];
        assert!(cell.symbol().starts_with(PLACEHOLDER));
        assert_eq!(cell.fg, Color::Rgb(0xF4, 0x00, 0x01), "beat 1 is slot 1");
    }
}
