// Blender-authored pbr3d pictures for the fab pages. Each scene is one GLB from
// tools/pbr3d/blender played through pbr3d.
//
// `Page` is the picture-and-panel template (docs/diagram-pages.md): the scene on the left with its
// `label:` tags pinned on, the beat's text in a panel on the right (pbr3d::caption), 8 s beats.
// `Clip` is the older layout, with the caption drawn over the picture; pages still on it move to
// `Page` as they are ported.

use std::sync::OnceLock;

use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};

/// The parsed GLB, held once per scene for the life of the process.
pub type Cell = OnceLock<pbr3d::scene_gltf::Scene>;

/// One beat is this long, here and in the Blender files (their SEC), so the clips play in real time.
pub const BEAT_SECS: f32 = 8.0;
pub const BEAT_MS: u64 = 8000;

/// One picture in the template: its Blender scene (parsed once, on first draw), beats and zoom-ins.
pub struct Page {
    pub cell: &'static Cell,
    pub glb: &'static [u8],
    pub beats: &'static [Beat],
    pub zooms: &'static [Zoom],
}

impl Scene for Page {
    fn size(&self) -> (u16, u16) {
        (100, 30)
    }

    fn beats(&self) -> &[Beat] {
        self.beats
    }

    fn draw(&self, _c: &mut Canvas, _t: &Time) {}

    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<image::RgbaImage> {
        let scene = self.cell.get_or_init(|| {
            pbr3d::scene_gltf::Scene::from_glb(self.glb)
                .expect("a diagram page GLB is a valid export")
        });
        let secs = (t.beat as f32 + t.local) * BEAT_SECS;
        Some(picture(scene, secs, self.beats, t.beat, w, h))
    }

    fn zooms(&self) -> &[Zoom] {
        self.zooms
    }

    fn notes_in_picture(&self) -> bool {
        true
    }

    fn rest_point(&self) -> f32 {
        0.4
    }
}

/// A zoom or section `Page` with no zoom-ins of its own.
pub fn page(cell: &'static Cell, glb: &'static [u8], beats: &'static [Beat]) -> Box<dyn Scene> {
    Box::new(Page {
        cell,
        glb,
        beats,
        zooms: &[],
    })
}

/// The scene at `secs` rendered into the left of a `w` x `h` frame, its `label:` tags pinned on,
/// and beat `beat`'s text in the panel on the right.
fn picture(
    scene: &pbr3d::scene_gltf::Scene,
    secs: f32,
    beats: &[Beat],
    beat: usize,
    w: u32,
    h: u32,
) -> image::RgbaImage {
    let sw = pbr3d::caption::scene_width(w).max(1);
    let mut img = pbr3d::scene_gltf::render(scene, secs, sw, h, crate::screens::diagrams_px::BG);
    let mut tags = pbr3d::caption::Tags::new();
    for (text, p) in scene.labels(secs) {
        if let Some((x, y)) = pbr3d::scene_gltf::project(scene, secs, sw, h, p) {
            tags.add(&mut img, x, y, &text, sw, h);
        }
    }
    let Some(b) = beats.get(beat) else { return img };
    let panel = pbr3d::caption::Panel {
        step: (beat, beats.len()),
        head: b.caption,
        what: b.what,
        look: b.look,
        facts: b.facts,
    };
    pbr3d::caption::compose(&img, w, h, &panel)
}

/// One Blender scene: its embedded GLB, its beats, and (for an overview) its zoom-ins.
pub struct Clip {
    pub cell: &'static Cell,
    pub glb: &'static [u8],
    pub beats: &'static [Beat],
    pub zooms: &'static [Zoom],
}

impl Scene for Clip {
    fn size(&self) -> (u16, u16) {
        (100, 30)
    }

    fn beats(&self) -> &[Beat] {
        self.beats
    }

    fn draw(&self, _c: &mut Canvas, _t: &Time) {}

    fn zooms(&self) -> &[Zoom] {
        self.zooms
    }

    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<image::RgbaImage> {
        let clip = self.cell.get_or_init(|| {
            pbr3d::scene_gltf::Scene::from_glb(self.glb)
                .expect("a fab picture GLB is a valid export")
        });
        let secs = t.beat as f32 + t.local;
        let mut img = pbr3d::scene_gltf::render(clip, secs, w, h, crate::screens::diagrams_px::BG);
        caption(&mut img, self.beats, t.beat);
        Some(img)
    }

    fn notes_in_picture(&self) -> bool {
        true
    }

    fn rest_point(&self) -> f32 {
        0.4
    }
}

/// Builds one scene from its statics, GLB bytes and beats. Non-capturing closures around this
/// call are the fn pointers the node tables hold.
pub fn clip(cell: &'static Cell, glb: &'static [u8], beats: &'static [Beat]) -> Box<dyn Scene> {
    Box::new(Clip {
        cell,
        glb,
        beats,
        zooms: &[],
    })
}

/// Writes the beat's caption and notes onto its picture.
pub fn caption(img: &mut image::RgbaImage, beats: &[Beat], beat: usize) {
    let Some(b) = beats.get(beat) else { return };
    let notes = [
        format!("what's happening: {}", b.what),
        format!("look for: {}", b.look),
        format!("key numbers: {}", b.facts.join("; ")),
    ];
    pbr3d::text::overlay(img, b.caption, &notes);
}

/// The scene-filling test every fab page uses: every beat draws a picture off the background.
#[cfg(test)]
pub fn draws_every_beat(scene: &dyn Scene, what: &str) {
    use crate::ui::anim::Time;
    for beat in 0..scene.beats().len() {
        let t = Time {
            beat,
            local: 0.5,
            ms: 0,
            beat_start: 0,
        };
        let img = scene
            .pixels(&t, 160, 100)
            .unwrap_or_else(|| panic!("{what} draws a picture"));
        let bg = crate::screens::diagrams_px::BG;
        let drawn = img
            .pixels()
            .filter(|p| p.0[0] != bg[0] || p.0[1] != bg[1] || p.0[2] != bg[2])
            .count();
        assert!(
            drawn > 160 * 100 / 50,
            "{what} beat {beat} only {drawn} pixels off the background"
        );
    }
}

/// Every beat has a caption, both notes, a why and non-empty key numbers.
#[cfg(test)]
pub fn explained(scene: &dyn Scene, what: &str) {
    for (i, b) in scene.beats().iter().enumerate() {
        assert!(
            !b.caption.is_empty()
                && !b.what.is_empty()
                && !b.look.is_empty()
                && !b.why.is_empty()
                && !b.facts.is_empty()
                && b.facts.iter().all(|f| !f.is_empty()),
            "{what} beat {i}"
        );
    }
}
