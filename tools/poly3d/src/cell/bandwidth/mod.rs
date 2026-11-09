//! 3D scenes for the BANDWIDTH page, on the CELL page's template: an overview with
//! its notes on the picture, five lettered zooms and nine numbered sections.
//!
//!   rig.rs        the memory system every scene shares (processor, channels, DIMMs,
//!                 an HBM stack, a peak-bandwidth gauge)
//!   overview.rs   how a peak bandwidth is built, seven beats
//!   zoom_*.rs     a-e: close-ups
//!   sec_*.rs      1-9: the write-up's sections (8 reuses the CELL page's makers;
//!                 timelines reuse the BANK page's)
//!
//! It lives under `cell` to share its kit (`stage`, `callout`, the rasterizer).

mod overview;
mod rig;
mod sec_gaps;
mod sec_kinds;
mod sec_numbers;
mod sec_order;
mod sec_parts;
mod sec_peak;
mod sec_risks;
mod sec_wall;
mod zoom_gaps;
mod zoom_hbm;
mod zoom_pin;
mod zoom_subch;
mod zoom_wall;

use image::RgbaImage;

use super::stage::{self, Clock, Shot};
use super::{callout, rasterize, to_image, Notes};
use crate::{Cam, Canvas, Tri, View};

/// The focused scenes behind the BANDWIDTH page.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BwZoom {
    /// a: one pin: two transfers per clock, then PAM4
    Pin,
    /// b: DDR5's two subchannels vs DDR4's one channel
    Subchannels,
    /// c: GDDR next to HBM
    Hbm,
    /// d: read/write turnaround and refresh gaps on the bus
    Gaps,
    /// e: the memory wall
    Wall,
    /// 1: what happens: rate x width x channels
    Peak,
    /// 2: the parts
    Parts,
    /// 3: computing peak bandwidth, in order
    Order,
    /// 4: DDR, GDDR and HBM per device
    Kinds,
    /// 5: effective vs peak
    GapsSec,
    /// 6: by the numbers
    Numbers,
    /// 7: the memory wall
    WallSec,
    /// 8: who makes it (shared with CELL)
    Makers,
    /// 9: chokepoints and risks
    Risks,
}

struct SceneFns {
    beats: usize,
    shot: fn(&Clock) -> Shot,
    solids: fn(&Clock, &mut Vec<Tri>),
    overlay: fn(&mut Canvas, &Cam, &Clock),
}

macro_rules! fns {
    ($m:ident, $beats:expr) => {
        SceneFns { beats: $beats, shot: $m::shot, solids: $m::solids, overlay: $m::overlay }
    };
}

impl BwZoom {
    fn scene(self) -> SceneFns {
        use super::sec_makers;
        match self {
            BwZoom::Pin => fns!(zoom_pin, 3),
            BwZoom::Subchannels => fns!(zoom_subch, 3),
            BwZoom::Hbm => fns!(zoom_hbm, 3),
            BwZoom::Gaps => fns!(zoom_gaps, 3),
            BwZoom::Wall => fns!(zoom_wall, 3),
            BwZoom::Peak => fns!(sec_peak, 3),
            BwZoom::Parts => fns!(sec_parts, sec_parts::BEATS),
            BwZoom::Order => fns!(sec_order, sec_order::BEATS),
            BwZoom::Kinds => fns!(sec_kinds, 3),
            BwZoom::GapsSec => fns!(sec_gaps, 3),
            BwZoom::Numbers => fns!(sec_numbers, 3),
            BwZoom::WallSec => fns!(sec_wall, 3),
            BwZoom::Makers => fns!(sec_makers, 3),
            BwZoom::Risks => fns!(sec_risks, 3),
        }
    }

    /// How many beats the scene's loop has.
    pub fn beats(self) -> usize {
        self.scene().beats
    }
}

/// One frame of a BANDWIDTH scene at `beat` and `local` (0..1 through the beat). `view`
/// is the user's orbit, measured from `View::default()`.
pub fn render_bw_zoom(z: BwZoom, beat: usize, local: f64, view: &View, w: usize, h: usize, bg: [u8; 3]) -> RgbaImage {
    let f = z.scene();
    let c = Clock { beat: beat.min(f.beats - 1), local: local.clamp(0.0, 1.0) };
    let cam = stage::camera(&(f.shot)(&c), view, w, h);
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    let mut tris: Vec<Tri> = Vec::new();
    (f.solids)(&c, &mut tris);
    rasterize(&mut cv, &cam, tris);
    (f.overlay)(&mut cv, &cam, &c);
    to_image(&cv)
}

/// Beats in the BANDWIDTH overview.
pub const BW_OVERVIEW_BEATS: usize = overview::BEATS;

/// One BANDWIDTH overview frame at `beat` and `local`: the memory system at the beat's angle,
/// turned by the user's `view`, its parts named and the beat's `notes` beside them.
pub fn render_bw_overview(
    beat: usize,
    local: f64,
    view: &View,
    notes: Option<&Notes>,
    w: usize,
    h: usize,
    bg: [u8; 3],
) -> RgbaImage {
    let all = overview::stops();
    let n = all.len();
    let beat = beat % n;
    let c = Clock { beat, local: local.clamp(0.0, 1.0) };
    let keys: Vec<Shot> = all.iter().map(|s| s.shot).collect();
    let shot = stage::shot_glide(&keys, beat, c.local, super::GLIDE);
    let mut cam = stage::camera(&shot, view, w, h);
    if w as f64 > h as f64 * 1.3 {
        cam.cx -= w as f64 * 0.13;
    }
    let r = overview::rig_at(&c);
    let mut cv = Canvas::new(w, h, bg.map(|c| c as f32 / 255.0));
    let mut tris: Vec<Tri> = Vec::new();
    rig::solids(&r, &mut tris);
    rasterize(&mut cv, &cam, tris);
    rig::overlay(&mut cv, &cam, &r);
    let avoid = rig::names(&mut cv, &cam, &r);
    if let Some(nt) = notes {
        let stop = &all[beat];
        let mut boxes = Vec::new();
        if !nt.what.is_empty() {
            boxes.push(callout::Callout {
                title: "what's happening",
                body: vec![nt.what.to_string()],
                col: stage::ORANGE,
                anchor: Some(rig::at(stop.what, &r)),
                prefer: (0.7, 0.2),
            });
        }
        if !nt.why.is_empty() {
            boxes.push(callout::Callout {
                title: "why it matters",
                body: vec![nt.why.to_string()],
                col: stage::CYAN,
                anchor: stop.why.map(|q| rig::at(q, &r)),
                prefer: (0.75, 0.55),
            });
        }
        if !nt.facts.is_empty() {
            boxes.push(callout::Callout {
                title: "key numbers",
                body: nt.facts.iter().map(|f| format!("- {f}")).collect(),
                col: stage::PURPLE,
                anchor: None,
                prefer: (1.0, 1.0),
            });
        }
        callout::draw(&mut cv, &cam, &boxes, &avoid, super::notes_alpha(local));
    }
    to_image(&cv)
}

#[cfg(test)]
mod tests {
    use super::*;

    const ZOOMS: [BwZoom; 14] = [
        BwZoom::Pin,
        BwZoom::Subchannels,
        BwZoom::Hbm,
        BwZoom::Gaps,
        BwZoom::Wall,
        BwZoom::Peak,
        BwZoom::Parts,
        BwZoom::Order,
        BwZoom::Kinds,
        BwZoom::GapsSec,
        BwZoom::Numbers,
        BwZoom::WallSec,
        BwZoom::Makers,
        BwZoom::Risks,
    ];
    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn zoom(z: BwZoom, beat: usize, local: f64) -> RgbaImage {
        render_bw_zoom(z, beat, local, &View::default(), 320, 276, BG)
    }

    fn mean_diff(a: &RgbaImage, b: &RgbaImage) -> f64 {
        let sum: u64 = a.as_raw().iter().zip(b.as_raw()).map(|(x, y)| u64::from(x.abs_diff(*y))).sum();
        sum as f64 / a.as_raw().len() as f64
    }

    #[test]
    fn zooms_have_no_cut_between_beats() {
        for z in ZOOMS {
            let n = z.beats();
            for beat in 0..n {
                let d = mean_diff(&zoom(z, beat, 0.9995), &zoom(z, (beat + 1) % n, 0.0));
                assert!(d < 0.6, "{z:?} beat {beat} jumps by {d}");
            }
        }
    }

    #[test]
    fn zooms_change_over_a_beat_and_orbit() {
        for z in ZOOMS {
            let a = zoom(z, 1, 0.1);
            let b = zoom(z, 1, 0.8);
            assert!(mean_diff(&a, &b) > 0.3, "{z:?} barely moves");
            let mut v = View::default();
            v.orbit(0.5, 0.0);
            let turned = render_bw_zoom(z, 1, 0.1, &v, 320, 276, BG);
            assert_ne!(a.as_raw(), turned.as_raw(), "{z:?} ignores the orbit");
        }
    }

    #[test]
    fn overview_has_no_cut_between_beats() {
        let f = |b: usize, l: f64| render_bw_overview(b, l, &View::default(), None, 320, 200, BG);
        for beat in 0..BW_OVERVIEW_BEATS {
            let d = mean_diff(&f(beat, 0.9995), &f((beat + 1) % BW_OVERVIEW_BEATS, 0.0));
            assert!(d < 0.6, "overview beat {beat} jumps by {d}");
        }
    }
}
