// Looping frame animations for node pages, shown in the node popup above the
// page art, like a GIF. Data lives in `diagrams_pages/<SLUG>.anim.txt`:
//
//   ms 300                  optional first line: milliseconds per frame
//   == caption for frame 1  starts a frame; the caption is shown under it
//   <art lines>
//   == caption for frame 2
//   <art lines>
//
// Frames use the same box-drawing conventions as the page art. An empty file
// means no animation. Frames are padded to one height so the page below
// does not jump.

use crate::ui::anim::{Beat, Canvas, Scene, Time};

const ANIMS: &[(&str, &str)] = &[
    ("INGOT", include_str!("diagrams_pages/INGOT.anim.txt")),
    (
        "SLICE + POLISH",
        include_str!("diagrams_pages/SLICE_POLISH.anim.txt"),
    ),
    ("WAFER", include_str!("diagrams_pages/WAFER.anim.txt")),
    ("DEPOSIT", include_str!("diagrams_pages/DEPOSIT.anim.txt")),
    ("COAT", include_str!("diagrams_pages/COAT.anim.txt")),
    ("EXPOSE", include_str!("diagrams_pages/EXPOSE.anim.txt")),
    ("DEVELOP", include_str!("diagrams_pages/DEVELOP.anim.txt")),
    ("ETCH", include_str!("diagrams_pages/ETCH.anim.txt")),
    ("IMPLANT", include_str!("diagrams_pages/IMPLANT.anim.txt")),
    ("CLEAN", include_str!("diagrams_pages/CLEAN.anim.txt")),
    ("KLAC", include_str!("diagrams_pages/KLAC.anim.txt")),
    (
        "WAFER SORT",
        include_str!("diagrams_pages/WAFER_SORT.anim.txt"),
    ),
    ("DICE", include_str!("diagrams_pages/DICE.anim.txt")),
    ("PICK", include_str!("diagrams_pages/PICK.anim.txt")),
    ("PACKAGE", include_str!("diagrams_pages/PACKAGE.anim.txt")),
    (
        "FINAL TEST",
        include_str!("diagrams_pages/FINAL_TEST.anim.txt"),
    ),
    ("SHIP", include_str!("diagrams_pages/SHIP.anim.txt")),
];

pub struct Anim {
    pub ms: u64,
    pub frames: Vec<(&'static str, Vec<&'static str>)>,
    pub height: usize,
}

pub fn parse(src: &'static str) -> Option<Anim> {
    let mut ms = 300;
    let mut frames: Vec<(&'static str, Vec<&'static str>)> = Vec::new();
    for line in src.lines() {
        if let Some(cap) = line.strip_prefix("==") {
            frames.push((cap.trim(), Vec::new()));
        } else if let Some(f) = frames.last_mut() {
            f.1.push(line);
        } else if let Some(v) = line.trim().strip_prefix("ms ") {
            ms = v.trim().parse().unwrap_or(ms).clamp(80, 5000);
        }
    }
    for f in &mut frames {
        while f.1.last().is_some_and(|l| l.trim().is_empty()) {
            f.1.pop();
        }
    }
    let height = frames.iter().map(|f| f.1.len()).max()?;
    (height > 0).then_some(Anim { ms, frames, height })
}

/// Zoom-ins that open in the full-screen 3D view (`F`), by page and key: a letter for a
/// zoom, a digit for a numbered section.
const ORBIT: &[(&str, char)] = &[
    ("POLYSILICON", 'c'),
];

/// Whether zoom `key` of `page` has a 3D model the full-screen view can orbit.
pub fn orbitable(page: &str, key: char) -> bool {
    // a page with Blender pictures plays them everywhere; nothing there is a 3D model to turn
    if super::diagrams_nodes::overview(page).is_some() {
        return false;
    }
    ORBIT.iter().any(|(p, k)| *p == page && *k == key)
        || (super::diagrams_scene_chip::node(page).is_some()
            && super::diagrams_scene_chip::keys_for(page, key).is_some())
        || super::diagrams_scene_pkg::keys_for(page, key).is_some()
        || super::diagrams_scene_link::keys_for(page, key).is_some()
        || super::diagrams_scene_pwr::keys_for(page, key).is_some()
}

/// The animation for a node page (keyed like VISUALS), if it has one.
pub fn anim_for(page: &str) -> Option<Anim> {
    ANIMS
        .iter()
        .find(|(k, _)| *k == page)
        .and_then(|(_, s)| parse(s))
}

/// Animated close-up for numbered section `i` of a node page, if the page has one.
pub fn section_anim(page: &str, i: usize) -> Option<fn() -> Box<dyn Scene>> {
    match page {
        _ if super::diagrams_scene_chip::node(page).is_some() => {
            super::diagrams_scene_chip::node(page).and_then(|n| n.sections.get(i).copied())
        }
        _ if super::diagrams_scene_pkg::node(page).is_some() => {
            super::diagrams_scene_pkg::node(page).and_then(|n| n.sections.get(i).copied())
        }
        _ if super::diagrams_scene_link::node(page).is_some() => {
            super::diagrams_scene_link::node(page).and_then(|n| n.sections.get(i).copied())
        }
        _ if super::diagrams_scene_pwr::node(page).is_some() => {
            super::diagrams_scene_pwr::node(page).and_then(|n| n.sections.get(i).copied())
        }
        _ => super::diagrams_nodes::section(page, i),
    }
}

/// Hand-drawn text frames played as a scene: one beat per frame.
pub struct TextScene {
    anim: Anim,
    beats: Vec<Beat>,
}

impl TextScene {
    pub fn new(anim: Anim) -> Self {
        let beats = anim
            .frames
            .iter()
            .map(|(caption, _)| Beat::new(caption, anim.ms))
            .collect();
        Self { anim, beats }
    }
}

impl Scene for TextScene {
    fn size(&self) -> (u16, u16) {
        let w = self
            .anim
            .frames
            .iter()
            .flat_map(|(_, f)| f.iter())
            .map(|l| l.chars().count())
            .max()
            .unwrap_or(0);
        (w as u16, self.anim.height as u16)
    }

    fn beats(&self) -> &[Beat] {
        &self.beats
    }

    fn draw(&self, c: &mut Canvas, t: &Time) {
        if let Some((_, lines)) = self.anim.frames.get(t.beat) {
            c.blit(0, 0, lines);
        }
    }
}

/// The scene for a node page (keyed like VISUALS), if it has one. Pages
/// with a procedural scene use it; the rest fall back to their text frames.
pub fn scene_for(page: &str) -> Option<Box<dyn Scene>> {
    if let Some(s) = super::diagrams_nodes::overview(page) {
        return Some(s);
    }
    if let Some(s) = super::diagrams_scene_chip::overview(page) {
        return Some(s);
    }
    if let Some(s) = super::diagrams_scene_pkg::overview(page) {
        return Some(s);
    }
    if let Some(s) = super::diagrams_scene_link::overview(page) {
        return Some(s);
    }
    if let Some(s) = super::diagrams_scene_pwr::overview(page) {
        return Some(s);
    }
    anim_for(page).map(|a| Box::new(TextScene::new(a)) as Box<dyn Scene>)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_frames() {
        let a = parse("ms 200\n== one\nab\n\n== two\nx\ny\nz\n").unwrap();
        assert_eq!(a.ms, 200);
        assert_eq!(a.frames.len(), 2);
        assert_eq!(a.frames[0], ("one", vec!["ab"]));
        assert_eq!(a.height, 3);
        assert!(parse("").is_none());
    }

    #[test]
    fn text_frames_play_as_a_scene() {
        use crate::ui::anim::Player;
        let a = parse("ms 200\n== one\nab\n\n== two\nx\ny\n").unwrap();
        let mut p = Player::new(Box::new(TextScene::new(a)), std::time::Instant::now());
        let s = p.shot_at(0);
        assert_eq!(
            (s.caption, s.lines.as_slice()),
            ("one", &["ab".to_string(), String::new()][..])
        );
        let s = p.shot_at(250);
        assert_eq!(s.caption, "two");
        assert_eq!(s.lines, vec!["x", "y"]);
    }

    #[test]
    fn sand_is_procedural_and_others_fall_back() {
        assert!(scene_for("SAND").is_some());
        assert!(scene_for("MELT + PULL").is_some());
        assert!(scene_for("WAFER").is_some());
        assert!(scene_for("NOPE").is_none());
    }

    /// The memory pages play their node's overview and sections, and their zoom-ins are
    /// node pictures, not 3D models the full view can orbit.
    #[test]
    fn memory_pages_play_their_node() {
        for page in ["CELL", "LITHO", "ARRAY", "BANK", "BANDWIDTH", "HBM STACK"] {
            let node = super::super::diagrams_nodes::overview(page)
                .unwrap_or_else(|| panic!("{page}: node has no overview"));
            let scene = scene_for(page).unwrap_or_else(|| panic!("{page}: no scene"));
            assert_eq!(
                scene.beats().len(),
                node.beats().len(),
                "{page}: overview beats differ from the node"
            );
            assert!(scene.beats().len() >= 3, "{page}: overview too short");
            assert!(!scene.zooms().is_empty(), "{page}: no zoom-ins");
            for key in 'a'..='f' {
                assert!(!orbitable(page, key), "{page} {key}: orbits");
            }
            for key in '1'..='9' {
                assert!(!orbitable(page, key), "{page} {key}: orbits");
            }
        }
    }

    /// One close-up per `# ` heading, reached by keys 1-9 then 0: ten headings need ten keys,
    /// nine headings stop at 9. Each close-up is 3 to 5 beats.
    #[test]
    fn section_keys_cover_every_heading() {
        use crate::ui::anim::Player;
        let want = [
            ("CELL", 10),
            ("LITHO", 10),
            ("ARRAY", 10),
            ("BANK", 10),
            ("BANDWIDTH", 10),
            ("HBM STACK", 10),
            ("INGOT", 10),
            ("SLICE + POLISH", 10),
            ("WAFER", 9),
        ];
        for (page, n) in want {
            let art = super::super::diagrams_desc::visual(page)
                .unwrap_or_else(|| panic!("{page}: no page"));
            let heads = art.lines().filter(|l| l.starts_with("# ")).count();
            assert_eq!(heads, n, "{page}: headings");
            for i in 0..n {
                let build = section_anim(page, i)
                    .unwrap_or_else(|| panic!("{page}: no section {}", i + 1));
                let beats = Player::new(build(), std::time::Instant::now())
                    .shot_at(0)
                    .beats;
                assert!((3..=5).contains(&beats), "{page} {}: {beats} beats", i + 1);
            }
            assert!(section_anim(page, n).is_none(), "{page}: extra section");
        }
    }

    #[test]
    fn all_anims_parse() {
        for (k, src) in ANIMS {
            if src.trim().is_empty() {
                continue;
            }
            let a = parse(src).unwrap_or_else(|| panic!("{k}: no frames"));
            assert!(a.frames.len() >= 4, "{k}: only {} frames", a.frames.len());
            for (cap, lines) in &a.frames {
                assert!(!cap.is_empty(), "{k}: frame without caption");
                for l in lines {
                    assert!(l.chars().count() <= 100, "{k}: line over 100 cols: {l}");
                }
            }
        }
    }
}
