// R&D tab, HBF: numbered sections 1-9, one file each (s1.rs .. s9.rs). Section N illustrates
// heading N of diagrams_pages/RND_HBF.txt, from tools/pbr3d/blender/rnd_hbf_section_<n>.py. The
// Sources heading (10) is text only.

mod s1;
mod s2;
mod s3;
mod s4;
mod s5;
mod s6;
mod s7;
mod s8;
mod s9;

use super::super::Build;

pub const SECTIONS: [Build; 9] = [
    s1::build,
    s2::build,
    s3::build,
    s4::build,
    s5::build,
    s6::build,
    s7::build,
    s8::build,
    s9::build,
];

#[cfg(test)]
mod tests {
    #[test]
    fn every_section_has_three_beats_or_is_a_placeholder() {
        for (i, b) in super::SECTIONS.iter().enumerate() {
            let n = b().beats().len();
            assert!(n == 3 || n == 7, "section {}: {n} beats", i + 1);
        }
    }
}
