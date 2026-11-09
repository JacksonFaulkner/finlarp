//! 3D scenes for the LITHO page, on the same template as the CELL page: an overview
//! with its notes on the picture, five lettered zooms and nine numbered sections.
//!
//!   rig.rs        the scanner every scene shares (source, reticle, lens, wafer, stage)
//!   overview.rs   one layer through the scanner, seven beats
//!   zoom_*.rs     a-e: close-ups of the overview's parts
//!   sec_*.rs      1-9: the write-up's sections
//!
//! It lives under `cell` to share its kit (`stage`, `callout`, the rasterizer).

mod overview;
mod rig;
mod sec_focus;
mod sec_makers;
mod sec_memory;
mod sec_multi;
mod sec_order;
mod sec_parts;
mod sec_print;
mod sec_resolution;
mod sec_risks;
mod zoom_lens;
mod zoom_overlay;
mod zoom_resist;
mod zoom_reticle;
mod zoom_scan;

use image::RgbaImage;

use super::stage::{self, Clock, Shot};
use super::{callout, rasterize, to_image, Notes};
use crate::{Cam, Canvas, Tri, View};

/// The focused scenes behind the LITHO page.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LithoZoom {
    /// a: the reticle, chrome on quartz, and a mask defect copied to every die
    Reticle,
    /// b: the lens: a wider light cone (higher NA) prints finer lines
    Lens,
    /// c: inside the resist: expose, develop, etch
    Resist,
    /// d: step and scan across the wafer, then High-NA half fields
    Scan,
    /// e: overlay: lining the new layer up on the one below
    Overlay,
    /// 1: what happens: light, lens, pattern
    Print,
    /// 2: the six parts, one in the spotlight at a time
    Parts,
    /// 3: one exposure, five steps
    Order,
    /// 4: resolution, CD = k1 x wavelength / NA, for three scanners
    Resolution,
    /// 5: depth of focus shrinking with NA^2
    Focus,
    /// 6: why it matters for memory: F sets the 6F^2 cell
    Memory,
    /// 7: multi-patterning: one pitch split over two exposures
    Multi,
    /// 8: who makes the scanners
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

impl LithoZoom {
    fn scene(self) -> SceneFns {
        match self {
            LithoZoom::Reticle => fns!(zoom_reticle, 3),
            LithoZoom::Lens => fns!(zoom_lens, 3),
            LithoZoom::Resist => fns!(zoom_resist, 3),
            LithoZoom::Scan => fns!(zoom_scan, 3),
            LithoZoom::Overlay => fns!(zoom_overlay, 3),
            LithoZoom::Print => fns!(sec_print, 3),
            LithoZoom::Parts => fns!(sec_parts, sec_parts::BEATS),
            LithoZoom::Order => fns!(sec_order, sec_order::BEATS),
            LithoZoom::Resolution => fns!(sec_resolution, 3),
            LithoZoom::Focus => fns!(sec_focus, 3),
            LithoZoom::Memory => fns!(sec_memory, 3),
            LithoZoom::Multi => fns!(sec_multi, 3),
            LithoZoom::Makers => fns!(sec_makers, 3),
            LithoZoom::Risks => fns!(sec_risks, 3),
        }
    }

    /// How many beats the scene's loop has.
    pub fn beats(self) -> usize {
        self.scene().beats
    }
}

/// One frame of a LITHO scene at `beat` and `local` (0..1 through the beat). `view`
/// is the user's orbit, measured from `View::default()`.
pub fn render_litho_zoom(z: LithoZoom, beat: usize, local: f64, view: &View, w: usize, h: usize, bg: [u8; 3]) -> RgbaImage {
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

/// Beats in the LITHO overview.
pub const LITHO_OVERVIEW_BEATS: usize = overview::BEATS;

/// One LITHO overview frame at `beat` and `local`: the scanner at the beat's angle,
/// turned by the user's `view`, its parts named and the beat's `notes` beside them.
pub fn render_litho_overview(
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

    const ZOOMS: [LithoZoom; 14] = [
        LithoZoom::Reticle,
        LithoZoom::Lens,
        LithoZoom::Resist,
        LithoZoom::Scan,
        LithoZoom::Overlay,
        LithoZoom::Print,
        LithoZoom::Parts,
        LithoZoom::Order,
        LithoZoom::Resolution,
        LithoZoom::Focus,
        LithoZoom::Memory,
        LithoZoom::Multi,
        LithoZoom::Makers,
        LithoZoom::Risks,
    ];
    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn zoom(z: LithoZoom, beat: usize, local: f64) -> RgbaImage {
        render_litho_zoom(z, beat, local, &View::default(), 320, 276, BG)
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
            let turned = render_litho_zoom(z, 1, 0.1, &v, 320, 276, BG);
            assert_ne!(a.as_raw(), turned.as_raw(), "{z:?} ignores the orbit");
        }
    }

    #[test]
    fn overview_has_no_cut_between_beats() {
        let f = |b: usize, l: f64| render_litho_overview(b, l, &View::default(), None, 320, 200, BG);
        for beat in 0..LITHO_OVERVIEW_BEATS {
            let d = mean_diff(&f(beat, 0.9995), &f((beat + 1) % LITHO_OVERVIEW_BEATS, 0.0));
            assert!(d < 0.6, "overview beat {beat} jumps by {d}");
        }
    }
}
