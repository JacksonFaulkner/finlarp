// PACKAGING tab, INTERPOSER: the page's overview, lettered zoom-ins a-e and numbered sections 1-9, on the POWER VRM
// pattern: overview.rs (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from
// tools/pbr3d/blender/pkg_interposer_*.py (part kit: pkg_interposer_detail.py).

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "INTERPOSER",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use super::super::super::blender::{draws_every_beat, explained};

    #[test]
    fn overview_zooms_and_sections_are_explained() {
        let ov = (super::overview::build)();
        assert_eq!(ov.beats().len(), 7);
        explained(ov.as_ref(), "overview");
        let keys: String = super::zooms::ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in super::zooms::ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            explained(s.as_ref(), z.label);
            draws_every_beat(s.as_ref(), z.label);
        }
        for (i, f) in super::sections::SECTIONS.iter().enumerate() {
            let s = f();
            let what = format!("section {}", i + 1);
            assert_eq!(s.beats().len(), 3, "{what}");
            explained(s.as_ref(), &what);
            draws_every_beat(s.as_ref(), &what);
        }
    }
}
