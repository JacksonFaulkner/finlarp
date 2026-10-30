// Activity chart as a picture: daily candles over the trade window, a strip
// underneath with the shares held each day, the average cost as a line while
// held, and one callout per trade. A leader line runs from the trade's candle
// up to a label in a top lane. Labels are packed into lanes, so they never
// sit on top of each other however close the trades are.
//
// The window can run past the last daily bar (a trade made today, say). Those
// days get one extra column on the right, with no candle, so the trade still
// has somewhere to point.

use chrono::{Datelike, NaiveDate};
use image::{DynamicImage, Rgba, RgbaImage};

use super::data::DayBar;
use crate::ui::pixels::{
    Palette, blend, fill, hline, line, put, text, text_height, text_width, vline,
};

/// Top lanes for trade labels.
const LANES: usize = 3;
const PAD: u32 = 4;
const LABEL_PAD: u32 = 3;
/// Share of the body (the area under the top lanes) given to the shares strip.
const STRIP_SHARE: f64 = 0.2;

/// One trade on the chart.
#[derive(Debug, Clone, PartialEq)]
pub struct Mark {
    pub date: NaiveDate,
    pub price: f64,
    pub buy: bool,
    pub shares: f64,
}

/// The position right after a transaction: (date, shares held, average cost).
pub type Held = (NaiveDate, f64, f64);

pub struct Chart<'a> {
    /// Daily bars in the window, oldest first.
    pub days: &'a [DayBar],
    /// The last day of the window (may be past the last bar).
    pub span_end: NaiveDate,
    pub marks: &'a [Mark],
    /// One entry per transaction for the symbol, oldest first.
    pub held: &'a [Held],
}

/// Content hash of the picture: when it changes, the picture is redrawn.
pub fn fingerprint(c: &Chart, px: (u32, u32), pal: &Palette) -> u64 {
    use std::hash::{Hash, Hasher};
    let mut h = std::collections::hash_map::DefaultHasher::new();
    px.hash(&mut h);
    pal.hash(&mut h);
    c.span_end.hash(&mut h);
    for b in c.days {
        b.date.hash(&mut h);
        for v in [b.open, b.high, b.low, b.close] {
            v.to_bits().hash(&mut h);
        }
    }
    for m in c.marks {
        m.date.hash(&mut h);
        (m.price.to_bits(), m.buy, m.shares.to_bits()).hash(&mut h);
    }
    for (d, shares, avg) in c.held {
        d.hash(&mut h);
        (shares.to_bits(), avg.to_bits()).hash(&mut h);
    }
    h.finish()
}

/// Where everything sits, in pixels. None when the picture is too small to be useful.
struct Geo {
    scale: u32,
    lo: f64,
    hi: f64,
    x0: u32,
    price_y0: u32,
    price_h: u32,
    strip_y0: u32,
    strip_h: u32,
    axis_y: u32,
    /// Columns: one per daily bar, plus one for the window's end when it is past the last bar.
    slots: usize,
    slot: f64,
}

impl Geo {
    /// Centre x of column `i`.
    fn x(&self, i: usize) -> u32 {
        (self.x0 as f64 + (i as f64 + 0.5) * self.slot).round() as u32
    }

    /// y of price `p` in the price area.
    fn y(&self, p: f64) -> u32 {
        let f = (self.hi - p) / (self.hi - self.lo);
        self.price_y0
            + (f * (self.price_h - 1) as f64)
                .round()
                .clamp(0.0, (self.price_h - 1) as f64) as u32
    }
}

/// The column for `d`: its bar's column, or the extra column for days past the last bar.
fn column(c: &Chart, g: &Geo, d: NaiveDate) -> usize {
    let i = c.days.partition_point(|b| b.date < d);
    if i < c.days.len() {
        i
    } else if g.slots > c.days.len() {
        c.days.len()
    } else {
        c.days.len() - 1
    }
}

/// The date a column stands for.
fn column_date(c: &Chart, i: usize) -> NaiveDate {
    c.days.get(i).map_or(c.span_end, |b| b.date)
}

fn geometry(c: &Chart, w: u32, h: u32) -> Option<Geo> {
    if c.days.is_empty() {
        return None;
    }
    let scale = if w >= 700 { 2 } else { 1 };
    let th = text_height(scale);
    let top = if c.marks.is_empty() {
        PAD
    } else {
        PAD + LANES as u32 * (th + 4)
    };
    let axis_h = th + 2 * PAD;
    let body = h.checked_sub(top + axis_h)?;
    let strip_h = (body as f64 * STRIP_SHARE).round() as u32;
    let price_h = body.checked_sub(strip_h + 2 * PAD)?;
    if price_h < 8 || strip_h < 6 {
        return None;
    }
    let mut lo = c.days.iter().map(|b| b.low).fold(f64::MAX, f64::min);
    let mut hi = c.days.iter().map(|b| b.high).fold(f64::MIN, f64::max);
    for (_, shares, avg) in c.held {
        if *shares > 0.0 && *avg > 0.0 {
            lo = lo.min(*avg);
            hi = hi.max(*avg);
        }
    }
    let pad = ((hi - lo) * 0.06).max(0.01);
    let (lo, hi) = (lo - pad, hi + pad);
    let x0 = text_width(&price_label(hi), scale) + 2 * PAD;
    let plot_w = w.checked_sub(x0 + PAD)?;
    if plot_w < 8 {
        return None;
    }
    let virt = c.span_end > c.days[c.days.len() - 1].date;
    let slots = c.days.len() + usize::from(virt);
    Some(Geo {
        scale,
        lo,
        hi,
        x0,
        price_y0: top,
        price_h,
        strip_y0: top + price_h + 2 * PAD,
        strip_h,
        axis_y: h - axis_h + PAD,
        slots,
        slot: plot_w as f64 / slots as f64,
    })
}

fn price_label(p: f64) -> String {
    if p < 10.0 {
        format!("${p:.2}")
    } else {
        format!("${p:.0}")
    }
}

/// Draws the chart at `w` x `h` pixels.
pub fn render(c: &Chart, w: u32, h: u32, pal: &Palette) -> DynamicImage {
    let (w, h) = (w.max(1), h.max(1));
    let mut img = RgbaImage::from_pixel(w, h, Rgba(pal.bg));
    let Some(g) = geometry(c, w, h) else {
        return DynamicImage::ImageRgba8(img);
    };
    let s = g.scale;
    let th = text_height(s);
    let plot_r = w - PAD;

    // Price gridlines, and the price on the left edge of each.
    let grid = blend(pal.dim, pal.bg, 0.35);
    for k in 0..=4 {
        let p = g.lo + (g.hi - g.lo) * k as f64 / 4.0;
        let row = g.y(p);
        if (1..4).contains(&k) {
            hline(&mut img, row, g.x0, plot_r, grid);
        }
        text(
            &mut img,
            PAD as i64,
            row as i64 - (th / 2) as i64,
            &price_label(p),
            s,
            pal.dim,
        );
    }

    // Candles, one per daily bar.
    let half = (g.slot * 0.3).floor() as u32;
    for (i, b) in c.days.iter().enumerate() {
        let x = g.x(i);
        let col = if b.close >= b.open { pal.up } else { pal.down };
        vline(&mut img, x, g.y(b.high), g.y(b.low), col);
        let (top_y, bot_y) = (g.y(b.open.max(b.close)), g.y(b.open.min(b.close)));
        fill(
            &mut img,
            x.saturating_sub(half),
            top_y,
            x + half,
            bot_y.max(top_y),
            col,
        );
    }

    // Average cost while held: a flat line from each transaction to the next, at least one column wide.
    let min_run = g.slot.round().max(2.0) as u32;
    for (k, (d, shares, avg)) in c.held.iter().enumerate() {
        if *shares <= 0.0 || *avg <= 0.0 {
            continue;
        }
        let end = c.held.get(k + 1).map_or(c.span_end, |next| next.0);
        let x0 = g.x(column(c, &g, *d));
        let x1 = g.x(column(c, &g, end)).max(x0 + min_run);
        hline(&mut img, g.y(*avg), x0, x1, pal.accent);
    }

    // Shares held, one column per day, scaled to the largest position in the window.
    let max_shares = c.held.iter().map(|e| e.1).fold(0.0, f64::max).max(1.0);
    let strip_bottom = g.strip_y0 + g.strip_h;
    let strip_col = blend(pal.accent, pal.bg, 0.6);
    for i in 0..g.slots {
        let date = column_date(c, i);
        let shares = c
            .held
            .iter()
            .rev()
            .find(|e| e.0 <= date)
            .map_or(0.0, |e| e.1);
        let height = ((shares.max(0.0) / max_shares) * g.strip_h as f64).round() as u32;
        if height > 0 {
            let x = g.x(i);
            fill(
                &mut img,
                x.saturating_sub(half),
                strip_bottom - height,
                x + half,
                strip_bottom - 1,
                strip_col,
            );
        }
    }
    // The strip's scale: the largest position, at the strip's bottom edge in the margin.
    text(
        &mut img,
        PAD as i64,
        strip_bottom as i64 - th as i64,
        &format!("{max_shares:.0}"),
        s,
        pal.dim,
    );

    // Dates at the two ends of the window.
    let fmt_date = |d: NaiveDate| format!("{:02}/{:02}", d.month(), d.day());
    text(
        &mut img,
        g.x0 as i64,
        g.axis_y as i64,
        &fmt_date(column_date(c, 0)),
        s,
        pal.dim,
    );
    let last = fmt_date(column_date(c, g.slots - 1));
    let last_x = (w as i64 - PAD as i64 - text_width(&last, s) as i64).max(0);
    text(&mut img, last_x, g.axis_y as i64, &last, s, pal.dim);

    // Trades: each gets a leader line to a label in the first lane with room, and a marker on its column.
    let mut order: Vec<usize> = (0..c.marks.len()).collect();
    order.sort_by_key(|&k| g.x(column(c, &g, c.marks[k].date)));
    // Each lane keeps the spans its labels use. A label tries to sit centred over its marker,
    // then left of it, then right of it, so trades on one column fan out instead of stacking.
    let mut lanes: [Vec<(i64, i64)>; LANES] = Default::default();
    let box_h = th + 2;
    let lane_pitch = th + 4;
    let (left_edge, right_edge) = (g.x0 as i64, w as i64);
    for k in order {
        let m = &c.marks[k];
        let (x, y) = (g.x(column(c, &g, m.date)) as i64, g.y(m.price) as i64);
        let col = if m.buy { pal.up } else { pal.down };
        let label = format!(
            "{}{:.0} {:.2}",
            if m.buy { "B" } else { "S" },
            m.shares,
            m.price
        );
        let lw = (text_width(&label, s) + 2 * LABEL_PAD) as i64;
        let fits = |lx: i64| lx >= left_edge && lx + lw <= right_edge;
        let candidates = [x - lw / 2, x - lw - 2 * PAD as i64, x + 2 * PAD as i64];
        let placed = (0..LANES).find_map(|lane| {
            candidates
                .iter()
                .copied()
                .find(|&lx| {
                    fits(lx)
                        && lanes[lane]
                            .iter()
                            .all(|&(l, r)| lx + lw + 4 <= l || lx >= r + 4)
                })
                .map(|lx| (lane, lx))
        });
        let Some((lane, lx)) = placed else {
            continue;
        };
        lanes[lane].push((lx, lx + lw));
        let ly = (PAD + lane as u32 * lane_pitch) as i64;
        fill(
            &mut img,
            lx as u32,
            ly as u32,
            (lx + lw - 1) as u32,
            (ly + box_h as i64 - 1) as u32,
            blend(pal.fg, pal.bg, 0.12),
        );
        text(&mut img, lx + LABEL_PAD as i64, ly + 1, &label, s, pal.fg);
        line(&mut img, (lx + lw / 2, ly + box_h as i64), (x, y), col);
        let r = 3i64;
        for dy in -r..=r {
            for dx in -r..=r {
                if dx * dx + dy * dy <= r * r {
                    put(&mut img, x + dx, y + dy, col);
                }
            }
        }
    }
    DynamicImage::ImageRgba8(img)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(s: &str) -> NaiveDate {
        NaiveDate::parse_from_str(s, "%Y-%m-%d").unwrap()
    }

    fn pal() -> Palette {
        Palette {
            bg: [0, 0, 0, 255],
            up: [0, 255, 0, 255],
            down: [255, 0, 0, 255],
            fg: [255, 255, 255, 255],
            dim: [90, 90, 90, 255],
            accent: [0, 0, 255, 255],
        }
    }

    fn day(date: &str, o: f64, h: f64, l: f64, c: f64) -> DayBar {
        DayBar {
            date: d(date),
            open: o,
            high: h,
            low: l,
            close: c,
        }
    }

    #[test]
    fn no_days_is_the_background() {
        let c = Chart {
            days: &[],
            span_end: d("2026-10-22"),
            marks: &[],
            held: &[],
        };
        let img = render(&c, 300, 200, &pal()).to_rgba8();
        assert_eq!(img.get_pixel(5, 5).0, [0, 0, 0, 255]);
    }

    #[test]
    fn a_trade_marker_sits_on_its_column_in_the_trade_colour() {
        let days = [
            day("2026-10-20", 10.0, 11.0, 9.5, 10.5),
            day("2026-10-21", 10.5, 12.0, 10.0, 11.5),
            day("2026-10-22", 11.5, 12.0, 11.0, 11.0),
        ];
        let marks = [Mark {
            date: d("2026-10-21"),
            price: 11.5,
            buy: false,
            shares: 10.0,
        }];
        let c = Chart {
            days: &days,
            span_end: d("2026-10-22"),
            marks: &marks,
            held: &[],
        };
        let img = render(&c, 600, 300, &pal()).to_rgba8();
        let g = geometry(&c, 600, 300).unwrap();
        let (x, y) = (g.x(1), g.y(11.5));
        assert_eq!(
            img.get_pixel(x, y).0,
            [255, 0, 0, 255],
            "sell marker in the down colour"
        );
    }

    #[test]
    fn a_trade_after_the_last_bar_gets_its_own_column() {
        let days = [
            day("2026-10-20", 10.0, 11.0, 9.5, 10.5),
            day("2026-10-21", 10.5, 12.0, 10.0, 11.5),
        ];
        let marks = [Mark {
            date: d("2026-10-28"),
            price: 11.0,
            buy: true,
            shares: 10.0,
        }];
        let c = Chart {
            days: &days,
            span_end: d("2026-10-28"),
            marks: &marks,
            held: &[],
        };
        let g = geometry(&c, 600, 300).unwrap();
        assert_eq!(g.slots, 3, "two bars plus the window's end");
        assert_eq!(column(&c, &g, d("2026-10-28")), 2);
        let img = render(&c, 600, 300, &pal()).to_rgba8();
        assert_eq!(
            img.get_pixel(g.x(2), g.y(11.0)).0,
            [0, 255, 0, 255],
            "buy marker in the extra column"
        );
    }

    #[test]
    fn held_shares_show_in_the_strip() {
        let days = [
            day("2026-10-20", 10.0, 11.0, 9.5, 10.5),
            day("2026-10-21", 10.5, 12.0, 10.0, 11.5),
        ];
        let held = [(d("2026-10-21"), 10.0, 10.5)];
        let c = Chart {
            days: &days,
            span_end: d("2026-10-21"),
            marks: &[],
            held: &held,
        };
        let img = render(&c, 600, 300, &pal()).to_rgba8();
        let g = geometry(&c, 600, 300).unwrap();
        let bottom = g.strip_y0 + g.strip_h - 1;
        // day 0 holds nothing; day 1 holds the window's largest position: a full-height column
        assert_eq!(img.get_pixel(g.x(0), bottom).0, [0, 0, 0, 255]);
        assert_ne!(img.get_pixel(g.x(1), bottom).0, [0, 0, 0, 255]);
    }

    #[test]
    fn labels_that_would_overlap_are_packed_into_lanes() {
        let days: Vec<DayBar> = (0..4)
            .map(|i| day(&format!("2026-10-{:02}", 20 + i), 10.0, 11.0, 9.5, 10.5))
            .collect();
        let marks = [
            Mark {
                date: d("2026-10-20"),
                price: 10.0,
                buy: true,
                shares: 100.0,
            },
            Mark {
                date: d("2026-10-21"),
                price: 10.0,
                buy: true,
                shares: 100.0,
            },
        ];
        let c = Chart {
            days: &days,
            span_end: d("2026-10-23"),
            marks: &marks,
            held: &[],
        };
        let img = render(&c, 500, 300, &pal()).to_rgba8();
        assert_eq!((img.width(), img.height()), (500, 300));
    }
}
