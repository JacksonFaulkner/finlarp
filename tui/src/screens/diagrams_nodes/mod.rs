// Fab node pages in the MELT + PULL template. Each node module holds its
// overview scene (its zoom-ins hang off the scene) and one animated close-up
// per `# ` section of its page, in page order.

use crate::ui::anim::Scene;

mod clean;
mod coat;
mod deposit;
mod develop;
mod dice;
mod etch;
mod expose;
mod final_test;
mod implant;
mod ingot;
mod package;
mod pick;
mod polysilicon;
mod sand;
mod ship;
mod slice_polish;
mod wafer;
mod wafer_sort;

pub type Build = fn() -> Box<dyn Scene>;

/// One node page's animations.
pub struct Node {
    /// Page key, as in VISUALS ("SLICE + POLISH").
    pub page: &'static str,
    /// The page's overview scene; `None` keeps the older scene or text frames.
    pub overview: Option<Build>,
    /// One close-up per `# ` section of the page, in order; empty until written.
    pub sections: &'static [Build],
}

const NODES: &[Node] = &[
    sand::NODE,
    polysilicon::NODE,
    ingot::NODE,
    slice_polish::NODE,
    wafer::NODE,
    deposit::NODE,
    coat::NODE,
    expose::NODE,
    develop::NODE,
    etch::NODE,
    implant::NODE,
    clean::NODE,
    wafer_sort::NODE,
    dice::NODE,
    pick::NODE,
    package::NODE,
    final_test::NODE,
    ship::NODE,
];

fn node(page: &str) -> Option<&'static Node> {
    NODES.iter().find(|n| n.page == page)
}

/// The overview scene for a node page, when its module has one.
pub fn overview(page: &str) -> Option<Box<dyn Scene>> {
    node(page)?.overview.map(|b| b())
}

/// The close-up for section `i` of a node page, when its module has one.
pub fn section(page: &str, i: usize) -> Option<Build> {
    node(page)?.sections.get(i).copied()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    #[test]
    fn pages_exist_and_sections_match_headings() {
        for (i, n) in NODES.iter().enumerate() {
            assert!(
                NODES[..i].iter().all(|m| m.page != n.page),
                "{} listed twice",
                n.page
            );
            let art = super::super::diagrams_desc::visual(n.page)
                .unwrap_or_else(|| panic!("{}: no page", n.page));
            let heads = art.lines().filter(|l| l.starts_with("# ")).count();
            assert!(
                n.sections.is_empty() || n.sections.len() == heads,
                "{}: {} sections for {heads} headings",
                n.page,
                n.sections.len()
            );
        }
    }

    /// Every scene in the template: 3+ beats, every note filled, draws at any size.
    fn check(page: &str, what: &str, build: Build) {
        let mut p = Player::new(build(), Instant::now());
        let beats = p.shot_at(0).beats;
        assert!(beats >= 3, "{page} {what}: only {beats} beats");
        let (mw, mh) = p.min_size();
        for (w, h) in [(mw, mh), (120, 40), (200, 60)] {
            p.fit(w, h);
            let step = p.loop_ms() / (beats as u64 * 2);
            for k in 0..beats as u64 * 2 {
                let s = p.shot_at(k * step);
                assert!(
                    !s.caption.is_empty()
                        && !s.what.is_empty()
                        && !s.look.is_empty()
                        && !s.why.is_empty()
                        && !s.facts.is_empty(),
                    "{page} {what}: beat {} has an empty note",
                    s.beat
                );
            }
        }
    }

    #[test]
    fn every_scene_fills_the_template() {
        for n in NODES {
            if let Some(b) = n.overview {
                check(n.page, "overview", b);
                for z in b().zooms() {
                    check(n.page, z.label, z.build);
                }
            }
            for (i, b) in n.sections.iter().enumerate() {
                check(n.page, &format!("section {}", i + 1), *b);
            }
        }
    }
}
