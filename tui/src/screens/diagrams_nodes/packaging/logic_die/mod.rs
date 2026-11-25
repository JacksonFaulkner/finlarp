// PACKAGING tab, LOGIC DIE: the page's overview, lettered zoom-ins a-e and numbered sections 1-9. overview.rs
// (the Blender overview), zooms.rs (zoom-ins a-e) and sections.rs (sections 1-9), drawn from
// tools/pbr3d/blender/pkg_logic_die_*.py (part kit pkg_logic_die_detail.py).

mod overview;
mod sections;
mod zooms;

use super::super::Node;

pub const NODE: Node = Node {
    page: "LOGIC DIE",
    overview: Some(overview::build),
    sections: &sections::SECTIONS,
    clips: false,
};

#[cfg(test)]
mod tests {
    use crate::screens::diagrams_nodes::blender;

    #[test]
    fn zooms_are_a_to_e_with_three_explained_beats() {
        let keys: String = super::zooms::ZOOMS.iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
        for z in super::zooms::ZOOMS {
            let s = (z.build)();
            assert_eq!(s.beats().len(), 3, "{}", z.label);
            blender::explained(s.as_ref(), z.label);
            blender::draws_every_beat(s.as_ref(), z.label);
        }
    }

    #[test]
    fn sections_have_three_explained_beats() {
        for (i, f) in super::sections::SECTIONS.iter().enumerate() {
            let s = f();
            let name = format!("section {}", i + 1);
            assert_eq!(s.beats().len(), 3, "{name}");
            blender::explained(s.as_ref(), &name);
            blender::draws_every_beat(s.as_ref(), &name);
        }
    }
}
