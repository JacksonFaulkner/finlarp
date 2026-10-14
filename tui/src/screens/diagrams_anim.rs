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

use std::time::Instant;

const ANIMS: &[(&str, &str)] = &[
    ("SAND", include_str!("diagrams_pages/SAND.anim.txt")),
    (
        "POLYSILICON",
        include_str!("diagrams_pages/POLYSILICON.anim.txt"),
    ),
    (
        "MELT + PULL",
        include_str!("diagrams_pages/MELT_PULL.anim.txt"),
    ),
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

/// The animation for a node page (keyed like VISUALS), if it has one.
pub fn anim_for(page: &str) -> Option<Anim> {
    ANIMS
        .iter()
        .find(|(k, _)| *k == page)
        .and_then(|(_, s)| parse(s))
}

impl Anim {
    /// Frame index for the time since `start`.
    pub fn frame_at(&self, start: Instant) -> usize {
        (start.elapsed().as_millis() as u64 / self.ms) as usize % self.frames.len()
    }
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
