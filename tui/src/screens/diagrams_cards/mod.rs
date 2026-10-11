// New-template detail cards for the SAND page chain. One file per card; each
// exports `pub const CARD: Card`. Opening (Enter) a card whose (page, label)
// is registered here shows: a big top visual + description, then a full-width
// tab row of 2-3 sections, each with text on the left and a small diagram on
// the right. Visual conventions are those of diagrams_art.rs / diagrams_vis.rs.

use super::diagrams_vis::Visual;

mod arc_furnace;
mod blend;
mod cast_crush;
mod crush;
mod quartzite;
mod tap;

pub struct Sec {
    pub title: &'static str,
    pub text: &'static str,
    pub vis: Visual,
}

pub struct Card {
    /// Big visual at the top: the card's main idea.
    pub top: Visual,
    /// What was clicked in, a few sentences under the top visual.
    pub desc: &'static str,
    /// 2-3 sub points.
    pub secs: &'static [Sec],
}

pub fn find(page: &str, label: &str) -> Option<&'static Card> {
    match (page, label) {
        ("SAND", "QUARTZITE") => Some(&quartzite::CARD),
        ("SAND", "CRUSH") => Some(&crush::CARD),
        ("SAND", "BLEND") => Some(&blend::CARD),
        ("SAND", "ARC FURNACE") => Some(&arc_furnace::CARD),
        ("SAND", "TAP") => Some(&tap::CARD),
        ("SAND", "CAST + CRUSH") => Some(&cast_crush::CARD),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const ALL: [&str; 6] = [
        "QUARTZITE",
        "CRUSH",
        "BLEND",
        "ARC FURNACE",
        "TAP",
        "CAST + CRUSH",
    ];

    #[test]
    fn every_card_is_well_formed() {
        for l in ALL {
            let c = find("SAND", l).unwrap_or_else(|| panic!("{l} missing"));
            assert!((2..=3).contains(&c.secs.len()), "{l}: 2-3 sections");
            assert!(!c.desc.trim().is_empty(), "{l}: desc");
            assert!(c.top.art.lines().count() >= 6, "{l}: top visual too small");
            for sp in c.top.spots {
                assert!(!c.top.placed().is_empty() || sp.needle.is_empty(), "{l}");
            }
            assert_eq!(
                c.top.placed().len(),
                c.top.spots.len(),
                "{l}: top spot not found"
            );
            for s in c.secs {
                assert!(!s.text.trim().is_empty(), "{l}/{}", s.title);
                assert_eq!(s.vis.placed().len(), s.vis.spots.len(), "{l}/{}", s.title);
            }
        }
    }
}
