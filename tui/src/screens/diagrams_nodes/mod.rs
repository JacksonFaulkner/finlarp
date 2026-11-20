// Fab node pages in the MELT + PULL template. Each node module holds its
// overview scene (its zoom-ins hang off the scene) and one animated close-up
// per `# ` section of its page, in page order.

use crate::ui::anim::Scene;

mod array;
mod bandwidth;
mod bank;
pub(crate) mod blender;
mod cell;
mod chip;
mod clean;
mod coat;
mod deposit;
mod develop;
mod dice;
mod etch;
mod expose;
mod fiber;
mod final_test;
mod hbf;
mod hbm;
mod implant;
mod ingot;
mod litho;
mod math;
mod melt;
mod package;
mod packaging;
mod pick;
mod polysilicon;
mod power;
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
    /// Plays as pre-rendered H.264 clips in a terminal that decodes them (diagrams_h264): the
    /// overview, zoom-ins and sections are rendered once to data/clips, and re-rendered in the
    /// background when the scene changes. Opt in once the page's pictures are final.
    pub clips: bool,
}

const NODES: &[Node] = &[
    sand::NODE,
    polysilicon::NODE,
    melt::NODE,
    ingot::NODE,
    slice_polish::NODE,
    wafer::NODE,
    cell::NODE,
    litho::NODE,
    array::NODE,
    bank::NODE,
    bandwidth::NODE,
    hbm::NODE,
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
    packaging::logic_die::NODE,
    packaging::microbump::NODE,
    packaging::interposer::NODE,
    packaging::substrate::NODE,
    packaging::assembly::NODE,
    packaging::board::NODE,
    fiber::dsp::NODE,
    fiber::laser::NODE,
    fiber::fibre::NODE,
    fiber::photodiode::NODE,
    fiber::module::NODE,
    fiber::cpo::NODE,
    power::grid::NODE,
    power::substation::NODE,
    power::switchgear::NODE,
    power::ups::NODE,
    power::rack::NODE,
    power::vrm::NODE,
    final_test::NODE,
    ship::NODE,
    hbf::NODE,
];

fn node(page: &str) -> Option<&'static Node> {
    NODES
        .iter()
        .find(|n| n.page == page)
        .or_else(|| chip::NODES.iter().copied().find(|n| n.page == page))
        .or_else(|| math::NODES.iter().find(|n| n.page == page))
}

/// The overview scene for a node page, when its module has one.
pub fn overview(page: &str) -> Option<Box<dyn Scene>> {
    node(page)?.overview.map(|b| b())
}

/// Whether a node page plays as pre-rendered clips (see `Node::clips`).
pub fn clips(page: &str) -> bool {
    node(page).is_some_and(|n| n.clips)
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
            // A page whose last heading is its sources list may stop at the picture sections:
            // the sources page is text only (as in POLYSILICON's section 10 before its picture).
            let text_only_sources = art
                .lines()
                .rev()
                .find(|l| l.starts_with("# "))
                .is_some_and(|l| l.contains("Sources"));
            let want = if text_only_sources { heads - 1 } else { heads };
            assert!(
                n.sections.is_empty() || n.sections.len() == want || n.sections.len() == heads,
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

    /// Every FIBER overview and numbered section moves inside each of its beats:
    /// a beat that is still would read as a frozen page.
    #[test]
    fn fiber_pictures_move_in_every_beat() {
        use crate::ui::anim::Player;
        use std::collections::HashSet;
        use std::time::Instant;
        const FIBER: [&str; 6] = [
            "PAM4 DSP",
            "LASER",
            "OPTICAL FIBER",
            "PHOTODIODE",
            "TRANSCEIVER",
            "CPO",
        ];
        let mut stuck = Vec::new();
        for n in NODES.iter().filter(|n| FIBER.contains(&n.page)) {
            let mut scenes: Vec<(String, Box<dyn crate::ui::anim::Scene>)> = Vec::new();
            // Zoom-ins are held pictures by design (one frozen state, captions change), so only
            // the overview and the numbered sections must move.
            if let Some(b) = n.overview {
                scenes.push((format!("{} overview", n.page), b()));
            }
            for (i, b) in n.sections.iter().enumerate() {
                scenes.push((format!("{} section {}", n.page, i + 1), b()));
            }
            for (name, scene) in scenes {
                let mut p = Player::new(scene, Instant::now());
                let beats = p.shot_at(0).beats;
                for beat in 0..beats {
                    let mut seen = HashSet::new();
                    for k in 0..4u64 {
                        let ms = beat as u64 * 8000 + k * 2000 + 1000;
                        let img = p.pixels(&p.time_at(ms), 120, 72).expect("pixel frame");
                        seen.insert(img.into_raw());
                    }
                    if seen.len() < 2 {
                        stuck.push(format!("{name} beat {beat}"));
                    }
                }
            }
        }
        assert!(stuck.is_empty(), "frozen beats:\n{}", stuck.join("\n"));
    }
}
