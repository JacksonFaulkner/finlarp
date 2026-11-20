// R&D tab, HBF: zoom-ins a-e, one file each (a.rs .. e.rs), each with its own Blender scene
// tools/pbr3d/blender/rnd_hbf_zoom_<letter>.py.

mod a;
mod b;
mod c;
mod d;
mod e;

use crate::ui::anim::Zoom;

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the stack cut open",
        build: a::build,
    },
    Zoom {
        key: 'b',
        label: "CBA bonding",
        build: b::build,
    },
    Zoom {
        key: 'c',
        label: "the UCIe link",
        build: c::build,
    },
    Zoom {
        key: 'd',
        label: "HBM against HBF",
        build: d::build,
    },
    Zoom {
        key: 'e',
        label: "reads and writes",
        build: e::build,
    },
];

#[cfg(test)]
mod tests {
    #[test]
    fn every_zoom_has_three_beats_or_is_a_placeholder() {
        for z in super::ZOOMS {
            let n = (z.build)().beats().len();
            assert!(n == 3 || n == 7, "zoom {}: {n} beats", z.key);
        }
    }
}
