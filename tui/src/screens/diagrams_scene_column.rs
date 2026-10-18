// Shared distillation-column model for the POLYSILICON scenes. A column sorts a mixture by boiling point, so the
// scenes draw three species with their own glyphs and let them separate:
//
//   °  light  (H2, BCl3: boil far below TCS)       ●  TCS  (SiHCl3, 31.8 C, the product)       ■  SiCl4  (56.8 C, heavy)
//
// Liquid composition changes tray by tray (`liquid`); vapor leaving a tray is richer in the light species (`vapor`,
// relative volatility). Each hop between two trays is one stateless particle whose species comes from the tray it
// starts on, so the sorting shows up as the picture: mostly ■ moving between the bottom trays, mostly ●/° between
// the top ones.

use crate::ui::anim::{Canvas, Particles, ease_in_out, lerp};

pub const LEGEND: &str = "° light   ● TCS   ■ SiCl4";

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Mix {
    pub light: f32,
    pub tcs: f32,
    pub stc: f32,
}

impl Mix {
    pub const fn new(light: f32, tcs: f32, stc: f32) -> Self {
        Self { light, tcs, stc }
    }

    fn mul(self, o: Mix) -> Mix {
        Mix::new(self.light * o.light, self.tcs * o.tcs, self.stc * o.stc)
    }

    fn norm(self) -> Mix {
        let s = (self.light + self.tcs + self.stc).max(1e-6);
        Mix::new(self.light / s, self.tcs / s, self.stc / s)
    }

    fn blend(self, o: Mix, t: f32) -> Mix {
        Mix::new(
            lerp(self.light, o.light, t),
            lerp(self.tcs, o.tcs, t),
            lerp(self.stc, o.stc, t),
        )
    }
}

/// What a column leaves at its two ends once it has done its job.
#[derive(Debug, Clone, Copy)]
pub struct Profile {
    pub top: Mix,
    pub bottom: Mix,
}

/// The mixture entering from the fluidized bed.
pub const FEED: Mix = Mix::new(0.20, 0.55, 0.25);
/// The zoom column's feed: mostly TCS with a good share of SiCl4, so the split is easy to see.
pub const FEED_ZOOM: Mix = Mix::new(0.10, 0.55, 0.35);
/// Column 1: sends the light gases out the top.
pub const LIGHTS: Profile = Profile {
    top: Mix::new(0.80, 0.19, 0.01),
    bottom: Mix::new(0.0, 0.70, 0.30),
};
/// Column 2: splits TCS (up) from SiCl4 (down).
pub const STC_CUT: Profile = Profile {
    top: Mix::new(0.03, 0.96, 0.01),
    bottom: Mix::new(0.0, 0.08, 0.92),
};
/// Column 3: strips the last light boron compounds off the top.
pub const POLISH: Profile = Profile {
    top: Mix::new(0.35, 0.65, 0.0),
    bottom: Mix::new(0.0, 0.99, 0.01),
};
/// The zoom's single column: a TCS / SiCl4 split with a little light stuff at the top.
pub const ZOOM: Profile = Profile {
    top: Mix::new(0.06, 0.92, 0.02),
    bottom: Mix::new(0.0, 0.06, 0.94),
};

/// Liquid composition at height fraction `f` (0 = top, 1 = bottom). `sep` (0..1) is how far the separation has
/// developed: 0 = every tray still holds the feed, 1 = steady state.
pub fn liquid(profile: Profile, feed: Mix, f: f32, sep: f32) -> Mix {
    let s = ease_in_out(((f - 0.1) / 0.8).clamp(0.0, 1.0));
    let steady = profile.top.blend(profile.bottom, s);
    feed.blend(steady, sep.clamp(0.0, 1.0)).norm()
}

/// Vapor in equilibrium with a liquid: the volatile species are over-represented.
pub fn vapor(liquid: Mix) -> Mix {
    liquid.mul(Mix::new(6.0, 2.0, 0.6)).norm()
}

/// Species glyph for a random number r in [0, 1).
pub fn pick(m: Mix, r: f32) -> char {
    if r < m.light {
        '°'
    } else if r < m.light + m.tcs {
        '●'
    } else {
        '■'
    }
}

/// Rows of the trays in a column spanning `top..bot` (box top and bottom rows).
pub fn tray_rows(top: i32, bot: i32) -> Vec<i32> {
    let mut v = Vec::new();
    let mut y = top + 3;
    while y < bot - 1 {
        v.push(y);
        y += 3;
    }
    v
}

/// Height fraction of tray `i` of `n`.
pub fn tray_f(i: usize, n: usize) -> f32 {
    if n <= 1 {
        0.5
    } else {
        i as f32 / (n - 1) as f32
    }
}

/// Everything that hops between trays: vapor up through the holes, liquid down the down-comer. The box is
/// `x0..=x1` (walls included). `live` slows the traffic to a trickle when the column is idle.
#[allow(clippy::too_many_arguments)]
pub fn draw_hops(
    c: &mut Canvas,
    (x0, x1): (i32, i32),
    trays: &[i32],
    profile: Profile,
    feed: Mix,
    sep: f32,
    ms: u64,
    seed: u64,
    live: bool,
) {
    let n = trays.len();
    for g in 0..n.saturating_sub(1) {
        let (ya, yb) = (trays[g], trays[g + 1]); // gap between tray g (above) and tray g+1 (below)
        let (every, life) = if live { (230, 900) } else { (1500, 900) };
        // vapor leaves tray g+1, so its species follows that tray's liquid
        let vm = vapor(liquid(profile, feed, tray_f(g + 1, n), sep));
        Particles::new(seed + g as u64 * 2, every, life).each(ms, |p| {
            let x = x0 + 2 + (p.rand(1) * (x1 - x0 - 4).max(1) as f32) as i32;
            let y = yb - 1 - (p.age * (yb - ya - 2).max(1) as f32).round() as i32;
            c.put_if_blank(x, y, pick(vm, p.rand(2)));
        });
        // liquid leaves tray g and runs down the down-comer on alternating sides
        let lm = liquid(profile, feed, tray_f(g, n), sep);
        let side = if g % 2 == 0 { x0 + 2 } else { x1 - 2 };
        Particles::new(seed + g as u64 * 2 + 1, every + 90, life + 200).each(ms, |p| {
            let y = ya + 1 + (p.age * (yb - ya - 1).max(1) as f32) as i32;
            if y < yb {
                c.put_if_blank(side, y, pick(lm, p.rand(2)));
            }
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tcs_climbs_and_sicl4_sinks_as_the_column_separates() {
        let top = liquid(ZOOM, FEED, 0.0, 1.0);
        let bottom = liquid(ZOOM, FEED, 1.0, 1.0);
        assert!(top.tcs > 0.9 && bottom.stc > 0.9);
        let mut prev = top.tcs;
        for i in 1..=10 {
            let m = liquid(ZOOM, FEED, i as f32 / 10.0, 1.0);
            assert!(m.tcs <= prev + 1e-4, "TCS never gets richer going down");
            prev = m.tcs;
        }
        // before the column has done anything every tray still holds the feed
        assert_eq!(liquid(ZOOM, FEED, 0.0, 0.0), liquid(ZOOM, FEED, 1.0, 0.0));
    }

    #[test]
    fn vapor_is_lighter_than_the_liquid_it_boils_from() {
        let l = liquid(ZOOM, FEED, 0.5, 1.0);
        let v = vapor(l);
        assert!(v.light >= l.light && v.stc <= l.stc);
        assert!((v.light + v.tcs + v.stc - 1.0).abs() < 1e-4);
    }

    #[test]
    fn pick_follows_the_mix() {
        let m = Mix::new(0.2, 0.5, 0.3);
        assert_eq!((pick(m, 0.1), pick(m, 0.4), pick(m, 0.9)), ('°', '●', '■'));
        let counts = |mix: Mix| {
            (0..1000).fold((0, 0), |(t, s), i| match pick(mix, i as f32 / 1000.0) {
                '●' => (t + 1, s),
                '■' => (t, s + 1),
                _ => (t, s),
            })
        };
        assert!(counts(liquid(ZOOM, FEED, 0.05, 1.0)).0 > counts(liquid(ZOOM, FEED, 0.95, 1.0)).0);
    }

    #[test]
    fn trays_fit_the_box() {
        assert_eq!(tray_rows(3, 12), vec![6, 9]);
        assert!(tray_rows(3, 29).iter().all(|y| *y > 3 && *y < 28));
    }

    #[test]
    fn hops_sort_the_species_by_height() {
        let mut c = Canvas::new(20, 40);
        let trays = tray_rows(0, 39);
        for ms in (0..6000).step_by(137) {
            draw_hops(&mut c, (2, 17), &trays, ZOOM, FEED, 1.0, ms, 7, true);
        }
        let count = |ch: char, rows: std::ops::Range<i32>| {
            rows.map(|y| (0..20).filter(|x| c.get(*x, y) == ch).count())
                .sum::<usize>()
        };
        let (upper, lower) = (0..18, 19..39);
        assert!(
            count('●', upper.clone()) > count('■', upper),
            "the top is mostly TCS"
        );
        assert!(
            count('■', lower.clone()) > count('●', lower),
            "the bottom is mostly SiCl4"
        );
    }
}
