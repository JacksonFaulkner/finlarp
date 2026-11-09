//! 3D scenes for the HBM STACK page, on the CELL page's template: an overview with
//! its notes on the picture, five lettered zooms and nine numbered sections.
//!
//!   rig.rs        the package every scene shares (substrate, interposer, GPU, four
//!                 HBM stacks; one stack can be opened up)
//!   overview.rs   the stack, seven beats
//!   zoom_*.rs     a-e: close-ups
//!   sec_*.rs      1-9: the write-up's sections (8 reuses the CELL page's makers)
//!
//! It lives under `cell` to share its kit (`stage`, `callout`, the rasterizer).

mod overview;
mod rig;
mod sec_build;
mod sec_cowos;
mod sec_gens;
mod sec_height;
mod sec_parts;
mod sec_risks;
mod sec_stack;
mod sec_bond;
mod zoom_base;
mod zoom_bond;
mod zoom_channels;
mod zoom_cowos;
mod zoom_tsv;

use image::RgbaImage;

use super::stage::{self, Clock, Shot};
use super::{callout, rasterize, to_image, Notes};
use crate::{Cam, Canvas, Tri, View};

/// The focused scenes behind the HBM STACK page.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum HbmZoom {
    /// a: a TSV and its microbumps, in section
    Tsv,
    /// b: the base logic die
    Base,
    /// c: channels: the stack split into independent channels
    Channels,
    /// d: microbumps vs hybrid bonding
    Bond,
    /// e: CoWoS: more stacks, bigger interposer
    Cowos,
    /// 1: what happens: DRAM stacked beside the processor
    Stack,
    /// 2: the parts
    Parts,
    /// 3: building a stack, in order
    Build,
    /// 4: generations: HBM3 and HBM4
    Gens,
    /// 5: height and heat
    Height,
    /// 6: bonding
    BondSec,
    /// 7: packaging (CoWoS)
    CowosSec,
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

impl HbmZoom {
    fn scene(self) -> SceneFns {
        use super::sec_makers;
        match self {
            HbmZoom::Tsv => fns!(zoom_tsv, 3),
            HbmZoom::Base => fns!(zoom_base, 3),
            HbmZoom::Channels => fns!(zoom_channels, 3),
            HbmZoom::Bond => fns!(zoom_bond, 3),
            HbmZoom::Cowos => fns!(zoom_cowos, 3),
            HbmZoom::Stack => fns!(sec_stack, 3),
            HbmZoom::Parts => fns!(sec_parts, sec_parts::BEATS),
            HbmZoom::Build => fns!(sec_build, sec_build::BEATS),
            HbmZoom::Gens => fns!(sec_gens, 3),
            HbmZoom::Height => fns!(sec_height, 3),
            HbmZoom::BondSec => fns!(sec_bond, 3),
            HbmZoom::CowosSec => fns!(sec_cowos, 3),
            HbmZoom::Makers => fns!(sec_makers, 3),
            HbmZoom::Risks => fns!(sec_risks, 3),
        }
    }

    /// How many beats the scene's loop has.
    pub fn beats(self) -> usize {
        self.scene().beats
    }
}

/// One frame of an HBM STACK scene at `beat` and `local` (0..1 through the beat). `view`
/// is the user's orbit, measured from `View::default()`.
pub fn render_hbm_zoom(z: HbmZoom, beat: usize, local: f64, view: &View, w: usize, h: usize, bg: [u8; 3]) -> RgbaImage {
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

/// Beats in the HBM STACK overview.
pub const HBM_OVERVIEW_BEATS: usize = overview::BEATS;

/// One HBM STACK overview frame at `beat` and `local`: the package at the beat's angle,
/// turned by the user's `view`, its parts named and the beat's `notes` beside them.
pub fn render_hbm_overview(
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

    const ZOOMS: [HbmZoom; 14] = [
        HbmZoom::Tsv,
        HbmZoom::Base,
        HbmZoom::Channels,
        HbmZoom::Bond,
        HbmZoom::Cowos,
        HbmZoom::Stack,
        HbmZoom::Parts,
        HbmZoom::Build,
        HbmZoom::Gens,
        HbmZoom::Height,
        HbmZoom::BondSec,
        HbmZoom::CowosSec,
        HbmZoom::Makers,
        HbmZoom::Risks,
    ];
    const BG: [u8; 3] = [0x28, 0x2a, 0x36];

    fn zoom(z: HbmZoom, beat: usize, local: f64) -> RgbaImage {
        render_hbm_zoom(z, beat, local, &View::default(), 320, 276, BG)
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
            let turned = render_hbm_zoom(z, 1, 0.1, &v, 320, 276, BG);
            assert_ne!(a.as_raw(), turned.as_raw(), "{z:?} ignores the orbit");
        }
    }

    #[test]
    fn overview_has_no_cut_between_beats() {
        let f = |b: usize, l: f64| render_hbm_overview(b, l, &View::default(), None, 320, 200, BG);
        for beat in 0..HBM_OVERVIEW_BEATS {
            let d = mean_diff(&f(beat, 0.9995), &f((beat + 1) % HBM_OVERVIEW_BEATS, 0.0));
            assert!(d < 0.6, "overview beat {beat} jumps by {d}");
        }
    }
}
