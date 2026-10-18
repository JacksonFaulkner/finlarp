// INGOT page in the MELT + PULL template. An overview with zoom-ins a-d, and one close-up per `# ` section of the page.

use super::Node;

mod overview;
mod sec_1;
mod sec_2;
mod sec_3;
mod sec_4;
mod sec_5;
mod sec_6;
mod sec_7;
mod sec_8;
mod sec_9;
mod sec_10;
mod zoom;

pub const NODE: Node = Node {
    page: "INGOT",
    overview: Some(overview::build),
    sections: &[
        sec_1::build,
        sec_2::build,
        sec_3::build,
        sec_4::build,
        sec_5::build,
        sec_6::build,
        sec_7::build,
        sec_8::build,
        sec_9::build,
        sec_10::build,
    ],
};
