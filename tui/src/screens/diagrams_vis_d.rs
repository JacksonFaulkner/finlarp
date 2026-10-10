// Visuals for KLAC, WAFER SORT, DICE and PICK (group D). The art and spots
// live in diagrams_pages/D.visuals.txt (generated text, parsed once):
//
//   @@ PAGE ## CARD ## SECTION
//   <art lines>
//   -- spots
//   needle ## nth ## 0|eol ## info
//
// `lookup` hands back the same `Visual { art, spots }` as the other vis files.

use std::sync::OnceLock;

#[allow(unused_imports)]
use super::diagrams_vis::{Spot, TO_EOL, Visual, spot};

const SRC: &str = include_str!("diagrams_pages/D.visuals.txt");

struct Entry {
    page: &'static str,
    card: &'static str,
    section: &'static str,
    art: &'static str,
    spots: &'static [Spot],
}

fn leak(s: &str) -> &'static str {
    Box::leak(s.to_string().into_boxed_str())
}

fn parse(src: &'static str) -> Vec<Entry> {
    let mut out = Vec::new();
    for block in src.split("\n@@ ").map(|b| b.trim_start_matches("@@ ")) {
        let block = block.trim_end();
        if block.is_empty() {
            continue;
        }
        let (head, rest) = block.split_once('\n').expect("visual block without art");
        let mut h = head.split(" ## ");
        let (page, card, section) = (
            h.next().expect("page"),
            h.next().expect("card"),
            h.next().expect("section"),
        );
        let (art, spot_text) = rest.split_once("\n-- spots\n").expect("missing -- spots");
        let spots: Vec<Spot> = spot_text
            .lines()
            .filter(|l| !l.trim().is_empty())
            .map(|l| {
                let mut f = l.splitn(4, " ## ");
                let needle = f.next().expect("needle");
                let nth: usize = f.next().expect("nth").trim().parse().expect("nth number");
                let width = match f.next().expect("width").trim() {
                    "eol" => TO_EOL,
                    w => w.parse().expect("width number"),
                };
                let info = f.next().expect("info");
                spot(leak(needle), nth, width, leak(info))
            })
            .collect();
        out.push(Entry {
            page,
            card,
            section,
            art: leak(&format!("{art}\n")),
            spots: Box::leak(spots.into_boxed_slice()),
        });
    }
    out
}

fn entries() -> &'static [Entry] {
    static E: OnceLock<Vec<Entry>> = OnceLock::new();
    E.get_or_init(|| parse(SRC))
}

pub fn lookup(page: &str, card: &str, section: &str) -> Option<Visual> {
    entries()
        .iter()
        .find(|e| e.page == page && e.card == card && e.section == section)
        .map(|e| Visual {
            art: e.art,
            spots: e.spots,
        })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::screens::diagrams_vis::check;

    #[test]
    fn every_group_d_visual_is_valid() {
        let all = entries();
        assert!(!all.is_empty());
        for e in all {
            let v = lookup(e.page, e.card, e.section).unwrap();
            assert!(
                !v.spots.is_empty(),
                "{}/{}/{}: no spots",
                e.page,
                e.card,
                e.section
            );
            check(&v, &format!("{}/{}/{}", e.page, e.card, e.section));
        }
    }

    #[test]
    fn every_content_section_has_a_visual() {
        // page key -> details file
        let pages: [(&str, &str); 4] = [
            ("KLAC", include_str!("diagrams_pages/KLAC.details.txt")),
            (
                "WAFER SORT",
                include_str!("diagrams_pages/WAFER_SORT.details.txt"),
            ),
            ("DICE", include_str!("diagrams_pages/DICE.details.txt")),
            ("PICK", include_str!("diagrams_pages/PICK.details.txt")),
        ];
        for (page, raw) in pages {
            let mut card = "";
            for line in raw.lines() {
                if let Some(head) = line.strip_prefix("== ") {
                    card = head.rsplit_once(" @").map_or(head, |(l, _)| l).trim();
                } else if let Some(sec) = line.strip_prefix("# ") {
                    let sec = sec.trim();
                    if sec != "Sources" {
                        assert!(
                            lookup(page, card, sec).is_some(),
                            "no visual for {page} / {card} / {sec}"
                        );
                    }
                }
            }
        }
    }
}
