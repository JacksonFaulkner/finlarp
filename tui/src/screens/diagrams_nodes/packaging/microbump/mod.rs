// PACKAGING tab, MICROBUMP: the page's overview, lettered zoom-ins a-e and numbered sections 1-9, on the
// POWER/VRM pattern: overview.rs (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9),
// drawn from tools/pbr3d/blender/pkg_microbump_*.py.

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "MICROBUMP",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = super::zooms::ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in super::zooms::ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            explained(s.as_ref(), z.label);
            draws_every_beat(s.as_ref(), z.label);
        }
    }

    #[test]
    fn sections_have_three_explained_beats() {
        for (i, f) in super::sections::SECTIONS.iter().enumerate() {
            let s = f();
            let what = format!("section {}", i + 1);
            assert_eq!(s.beats().len(), 3, "{what}");
            explained(s.as_ref(), &what);
            draws_every_beat(s.as_ref(), &what);
        }
    }

    #[test]
    fn overview_has_seven_explained_beats() {
        let s = super::overview::build();
        assert_eq!(s.beats().len(), 7);
        explained(s.as_ref(), "overview");
    }
}
