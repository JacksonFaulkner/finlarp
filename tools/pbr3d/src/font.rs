//! A 5x7 capital-letter font, baked into the decal atlas that the chamber nameplate uses.

/// Each glyph: seven rows, the top row first; bit 4 is the left column.
fn glyph(c: char) -> [u8; 7] {
    match c {
        'A' => [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        'C' => [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
        'E' => [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
        'H' => [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        'I' => [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
        'K' => [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
        'L' => [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
        'M' => [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
        'O' => [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        'P' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
        'R' => [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
        'S' => [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
        'U' => [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        'Z' => [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
        '0' => [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
        '3' => [0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110],
        _ => [0; 7],
    }
}

/// Width and height of the atlas, and its RGBA8 pixels: a dark anodised plate with
/// engraved light lettering, two lines, scaled by `s`.
pub fn atlas(lines: &[&str], s: u32) -> (u32, u32, Vec<u8>) {
    let (w, h) = (512u32, 128u32);
    let plate = [22u8, 24, 28, 255];
    let ink = [196u8, 200, 206, 255];
    let mut px = vec![0u8; (w * h * 4) as usize];
    for y in 0..h {
        for x in 0..w {
            let edge = x < 6 || y < 6 || x >= w - 6 || y >= h - 6;
            let c = if edge { [60u8, 62, 68, 255] } else { plate };
            let i = ((y * w + x) * 4) as usize;
            px[i..i + 4].copy_from_slice(&c);
        }
    }
    let cw = 6 * s;
    let lh = 9 * s;
    let top = (h - lines.len() as u32 * lh) / 2;
    for (li, line) in lines.iter().enumerate() {
        let len = line.chars().count() as u32;
        let x0 = (w - len * cw) / 2;
        let y0 = top + li as u32 * lh;
        for (ci, ch) in line.chars().enumerate() {
            let g = glyph(ch);
            for (ry, row) in g.iter().enumerate() {
                for rx in 0..5u32 {
                    if row & (1 << (4 - rx)) == 0 {
                        continue;
                    }
                    for dy in 0..s {
                        for dx in 0..s {
                            let x = x0 + ci as u32 * cw + rx * s + dx;
                            let y = y0 + ry as u32 * s + dy;
                            let i = ((y * w + x) * 4) as usize;
                            px[i..i + 4].copy_from_slice(&ink);
                        }
                    }
                }
            }
        }
    }
    (w, h, px)
}
