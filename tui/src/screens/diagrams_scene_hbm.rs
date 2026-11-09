// HBM STACK page: a stack of DRAM dies beside the GPU, drawn in 3D by poly3d, on the
// CELL page's template. The overview walks the package, one stack (base die and eight
// DRAM dies), the microbumps between dies, a read down the TSVs, data crossing the
// interposer, taller stacks, and heat. Each zoom (a-e) is its own 3D scene: a a TSV
// cut open, b the base logic die, c channels, d microbumps vs hybrid bonding, e CoWoS.
// Sections 1-9 each have one.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: see section 10 of MEM_HBM_STACK.txt. JEDEC JESD238 (HBM3) and JESD270-4
// (HBM4); SemiEngineering, HBM4 sticks with microbumps; Tom's Hardware on the height
// limit and on CoWoS capacity; TrendForce on CoWoS.

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::HbmZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 6500;
const OVERVIEW_MS: u64 = 13000;

const BEATS: &[Beat] = &[
    Beat::new("the package: a GPU and HBM stacks on one silicon interposer", OVERVIEW_MS)
        .note(
            "High-end accelerators place stacks of DRAM right beside the GPU, on a slab of silicon called an interposer that carries thousands of short wires between them.",
            "A purple GPU in the middle, four stacks around it, all on a grey interposer over a green substrate.",
        )
        .detail(
            "Short wires make a very wide bus possible: 1024 bits per HBM3 stack.",
            &["HBM3: 1024 bits, 6.4 Gb/s, 819 GB/s per stack (JEDEC JESD238)"],
        ),
    Beat::new("one stack: a base logic die under eight DRAM dies", OVERVIEW_MS)
        .note(
            "Each stack is a base logic die with DRAM dies piled on top. Every DRAM die holds memory arrays; the base die talks to the GPU.",
            "The camera moves to one stack: a blue base die and eight orange DRAM dies.",
        )
        .detail("Stacking puts more memory in the same footprint beside the GPU.", &["8-high shown; HBM4 allows 4, 8, 12 or 16-high (JEDEC JESD270-4)"]),
    Beat::new("pulled apart: microbumps join each die to the next", OVERVIEW_MS)
        .note(
            "Between the dies are microbumps, tiny solder joints that connect one die to the next at each vertical wire.",
            "The dies separate; yellow bumps appear between them at every copper column.",
        )
        .detail("Bump pitch is around 40 um and heading towards 10 um.", &["Microbump pitch about 40 um, toward 10 um (SemiEngineering)"]),
    Beat::new("a read: data runs down the TSVs to the base die", OVERVIEW_MS)
        .note(
            "Through-silicon vias (TSVs) are copper wires running straight through each thinned die. A read on one die travels down them to the base die.",
            "One die lights up and yellow dots run down the copper columns to the base.",
        )
        .detail("TSVs only work because the dies are thinned to tens of micrometres.", &["Dies thinned to 30-50 um (SemiEngineering)"]),
    Beat::new("across the interposer to the GPU", OVERVIEW_MS)
        .note(
            "The base die's PHY drives the wide bus across the interposer to the GPU, millimetres away. All four stacks do it at once.",
            "The stack closes up; cyan dots stream from every stack across the interposer to the GPU.",
        )
        .detail("Several stacks multiply the bandwidth.", &["4 x 819 GB/s = 3.3 TB/s with HBM3"]),
    Beat::new("taller stacks: more capacity", OVERVIEW_MS)
        .note(
            "Adding dies adds capacity without taking more room beside the GPU. HBM4 allows up to 16-high: with 32 Gb dies, 64 GB in one stack.",
            "The stack grows from eight dies to sixteen.",
        )
        .detail("Height is capped, so taller stacks need thinner dies and joints.", &["HBM4 16-high x 32 Gb = 64 GB (JEDEC)", "Height limit raised 720 -> 775 um (press reports)"]),
    Beat::new("heat has to leave through the top", OVERVIEW_MS)
        .note(
            "The dies make heat, and in a tall stack the heat from the lower dies has to pass up through all the others to escape.",
            "The stack glows hotter towards the bottom and heat rises from the top; then it settles back to eight dies.",
        )
        .detail("Heat is one reason stack height and bonding are hard.", &["Heat path through the stack"]),
];

const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "a TSV and its microbumps, cut open", build: || -> Box<dyn Scene> { Box::new(TsvZ) } },
    Zoom { key: 'b', label: "the base logic die", build: || -> Box<dyn Scene> { Box::new(BaseZ) } },
    Zoom { key: 'c', label: "channels: one stack, many buses", build: || -> Box<dyn Scene> { Box::new(ChannelsZ) } },
    Zoom { key: 'd', label: "microbumps vs hybrid bonding", build: || -> Box<dyn Scene> { Box::new(BondZ) } },
    Zoom { key: 'e', label: "CoWoS: more stacks, bigger interposer", build: || -> Box<dyn Scene> { Box::new(CowosZ) } },
];

/// The overview at `t`, turned by the user's `view`, with the beat's notes on it.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes { what: b.what, why: b.why, facts: b.facts };
    poly3d::render_hbm_overview(t.beat, t.local as f64, view, Some(&notes), w as usize, h as usize, px::BG)
}

/// The HBM STACK overview: the stack and its package.
pub struct MemHbm;

impl Scene for MemHbm {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }
    fn beats(&self) -> &[Beat] {
        BEATS
    }
    fn draw(&self, _c: &mut Canvas, _t: &Time) {}
    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
        Some(overview_frame(t, &poly3d::View::default(), w, h))
    }
    fn notes_in_picture(&self) -> bool {
        true
    }
    fn rest_point(&self) -> f32 {
        0.4
    }
}

/// The 3D scene behind zoom `key`: letters are parts of the overview, numbers the
/// page's sections.
pub fn zoom_scene(key: char) -> Option<HbmZoom> {
    Some(match key {
        'a' => HbmZoom::Tsv,
        'b' => HbmZoom::Base,
        'c' => HbmZoom::Channels,
        'd' => HbmZoom::Bond,
        'e' => HbmZoom::Cowos,
        '1' => HbmZoom::Stack,
        '2' => HbmZoom::Parts,
        '3' => HbmZoom::Build,
        '4' => HbmZoom::Gens,
        '5' => HbmZoom::Height,
        '6' => HbmZoom::BondSec,
        '7' => HbmZoom::CowosSec,
        '8' => HbmZoom::Makers,
        '9' => HbmZoom::Risks,
        _ => return None,
    })
}

macro_rules! zoom_scene_impl {
    ($name:ident, $beats:ident, $zoom:expr) => {
        pub struct $name;

        impl Scene for $name {
            fn size(&self) -> (u16, u16) {
                (MIN_W, MIN_H)
            }
            fn beats(&self) -> &[Beat] {
                $beats
            }
            fn draw(&self, _c: &mut Canvas, _t: &Time) {}
            fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
                Some(poly3d::render_hbm_zoom(
                    $zoom,
                    t.beat,
                    t.local as f64,
                    &poly3d::View::default(),
                    w as usize,
                    h as usize,
                    px::BG,
                ))
            }
        }
    };
}

const TSV_BEATS: &[Beat] = &[
    Beat::new("copper columns through the silicon", BEAT_MS)
        .note("A cut through two DRAM dies over the base die: each die has copper TSVs running straight through it.", "Orange dies with copper columns, yellow bumps between them.")
        .detail("Not to scale.", &["TSV: through-silicon via"]),
    Beat::new("a signal runs down the column", BEAT_MS)
        .note("Data passes down a TSV, across a microbump, into the next TSV, and so on to the base die.", "Yellow dots run down all three columns.")
        .detail("Thousands of such columns per stack.", &["Microbumps join TSVs die to die"]),
    Beat::new("thinner dies for taller stacks", BEAT_MS)
        .note("Dies are ground thin, to 30-50 um, so more fit under the height limit and the TSVs stay short.", "Both dies thin down, then return.")
        .detail("Bump pitch shrinks too.", &["Dies 30-50 um; bump pitch ~40 -> 10 um (SemiEngineering)"]),
];

const BASE_BEATS: &[Beat] = &[
    Beat::new("the base die under the stack", BEAT_MS)
        .note("Under the DRAM dies sits a logic die: the TSVs land on it in a central field.", "The DRAM dies lift as glass to show the base die and its copper landing field.")
        .detail("It holds no memory arrays of its own.", &["Base die = interface + test logic"]),
    Beat::new("the PHY drives the bus to the GPU", BEAT_MS)
        .note("Along the edge facing the GPU, the PHY drives the 1024-bit bus across the interposer.", "Cyan dots stream from the edge strip towards the GPU.")
        .detail("PHY: the physical-layer circuits that send and receive signals.", &["1024 bits (HBM3), 2048 (HBM4)"]),
    Beat::new("HBM4: base die on a foundry logic process", BEAT_MS)
        .note("For HBM4 the base die is reportedly made at foundries such as TSMC on a logic process, not the DRAM process.", "A note appears over the base die.")
        .detail("Logic processes allow faster, denser interface circuits.", &["HBM4 base die on foundry logic (reported)"]),
];

const CHANNELS_BEATS: &[Beat] = &[
    Beat::new("1024 bits from one HBM3 stack", BEAT_MS)
        .note("An HBM3 stack's interface is 1024 data bits wide.", "One wide cyan bus between the stack and the GPU.")
        .detail("Far wider than a 64-bit DDR channel.", &["HBM3: 1024 bits"]),
    Beat::new("split into 16 independent channels", BEAT_MS)
        .note("Those bits form 16 independent channels, each with its own commands, so many requests run at once.", "The bus splits into coloured bundles, each with its own rhythm.")
        .detail("HBM3 doubled the channels from 8 to 16.", &["HBM3: 16 channels (JEDEC)"]),
    Beat::new("HBM4: 32 channels, 2048 bits", BEAT_MS)
        .note("HBM4 doubles again: 2048 bits in 32 channels, each split into two pseudo-channels.", "The bundles double.")
        .detail("Up to 2 TB/s per stack at 8 Gb/s.", &["HBM4: 32 channels, 2048 bits (JEDEC JESD270-4)"]),
];

const BOND_BEATS: &[Beat] = &[
    Beat::new("microbumps: a gap at every joint", BEAT_MS)
        .note("Two 16-high stacks. On the left each die sits on microbumps, which leave a gap per die.", "Yellow bumps between every pair of dies.")
        .detail("Not to scale.", &["Microbump bonding"]),
    Beat::new("hybrid bonding: copper to copper", BEAT_MS)
        .note("Hybrid bonding joins copper pads directly with no bump, so the same dies make a shorter stack.", "The right stack's gaps close and it shrinks.")
        .detail("Harder and costlier to make with good yield.", &["Hybrid bonding postponed for HBM4 (SemiEngineering)"]),
    Beat::new("the height limit rose, so HBM4 kept microbumps", BEAT_MS)
        .note("Raising the stack height limit from 720 to 775 um let 16-high HBM4 keep microbumps for now.", "The pink limit plane moves up.")
        .detail("Hybrid bonding is expected beyond 16-high.", &["720 -> 775 um (press reports)"]),
];

const COWOS_BEATS: &[Beat] = &[
    Beat::new("one interposer for the GPU and four stacks", BEAT_MS)
        .note("In CoWoS the GPU and its HBM stacks share one silicon interposer.", "A GPU with four stacks on an interposer.")
        .detail("Chip-on-Wafer-on-Substrate, TSMC's packaging.", &["CoWoS (TSMC)"]),
    Beat::new("eight stacks need a bigger interposer", BEAT_MS)
        .note("More stacks for more bandwidth and capacity make the interposer larger.", "Four more stacks appear and the interposer grows.")
        .detail("Newer accelerators use more stacks.", &["More HBM per package"]),
    Beat::new("bigger interposers: fewer per wafer", BEAT_MS)
        .note("Interposers are cut from silicon wafers, so larger ones mean fewer per wafer and more packaging capacity per GPU.", "A wafer outlined with interposers; the count drops as they grow.")
        .detail("Counts here are illustrative.", &["Larger interposers lower packages per wafer (Tom's Hardware)"]),
];

const STACK_BEATS: &[Beat] = &[
    Beat::new("DRAM stacked beside the processor", BEAT_MS)
        .note("HBM stacks DRAM dies on a base die and puts the stack next to the processor on an interposer.", "The package from above.")
        .detail("Very wide, very close memory.", &["1024 bits per HBM3 stack"]),
    Beat::new("the stack opened up", BEAT_MS)
        .note("Inside: a base logic die, DRAM dies, TSVs through them and microbumps between them.", "The stack pulls apart to show its joints.")
        .detail("Each part has its own zoom.", &["TSVs + microbumps"]),
    Beat::new("a read reaches the GPU", BEAT_MS)
        .note("Data runs down the TSVs to the base die and across the interposer to the GPU.", "Dots run down the stack and across to the GPU.")
        .detail("819 GB/s per HBM3 stack.", &["JEDEC JESD238"]),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("DRAM dies", BEAT_MS)
        .note("The memory itself, stacked 4 to 16 high.", "The DRAM dies keep their colour; the rest go grey.")
        .detail("Each die has its own banks and arrays.", &["24 or 32 Gb per die (HBM4)"]),
    Beat::new("base logic die", BEAT_MS)
        .note("The interface to the GPU, plus test logic; the TSVs land on it.", "The base die lights.")
        .detail("Moving to foundry logic for HBM4 (reported).", &["PHY + test"]),
    Beat::new("TSVs", BEAT_MS)
        .note("Copper wires straight through each die, carrying signals and power up and down.", "The stack opens and the copper columns light.")
        .detail("Only possible in thinned dies.", &["30-50 um dies"]),
    Beat::new("microbumps", BEAT_MS)
        .note("Tiny joints that connect each die's TSVs to the next die.", "The bumps between the dies light.")
        .detail("Pitch shrinking from ~40 um.", &["Microbumps (SemiEngineering)"]),
    Beat::new("silicon interposer", BEAT_MS)
        .note("A slab of silicon wiring the stacks to the GPU with thousands of short lines.", "The interposer and its wiring light.")
        .detail("Part of CoWoS packaging.", &["2.5D packaging"]),
    Beat::new("GPU", BEAT_MS)
        .note("The processor the stacks feed, millimetres away.", "The GPU lights; data streams to it.")
        .detail("Several stacks per GPU.", &["4 x 819 GB/s = 3.3 TB/s (HBM3)"]),
];

const BUILD_BEATS: &[Beat] = &[
    Beat::new("1. DRAM dies made and stacked one by one", BEAT_MS)
        .note("DRAM dies made on DRAM wafers are placed one at a time.", "Dies appear one after another on the base die.")
        .detail("Every die must be good: a bad one spoils the stack.", &["Known-good dies"]),
    Beat::new("2. thinned, with TSVs and bumps", BEAT_MS)
        .note("Each die is thinned and carries TSVs and microbumps.", "The stack shown pulled apart with its bumps.")
        .detail("30-50 um dies.", &["SemiEngineering"]),
    Beat::new("3. bonded onto the base die", BEAT_MS)
        .note("The dies are bonded down onto the base die into one stack.", "The gaps close.")
        .detail("Microbumps for HBM4.", &["Bonding"]),
    Beat::new("4. tested", BEAT_MS)
        .note("The finished stack is tested by reading through its TSVs.", "Dots run down the TSVs.")
        .detail("Bad stacks are rejected before packaging.", &["Stack test"]),
    Beat::new("5. mounted beside the GPU", BEAT_MS)
        .note("Stacks and GPU are mounted on the interposer and linked.", "Data flows across the interposer; then the stack is taken away for the next build.")
        .detail("CoWoS packaging (TSMC).", &["Interposer mount"]),
];

const GENS_BEATS: &[Beat] = &[
    Beat::new("data pins: 1024 to 2048", BEAT_MS)
        .note("HBM4 doubles the interface width of HBM3.", "Two bars: HBM4 twice as tall.")
        .detail("More pins, more channels.", &["JEDEC JESD238, JESD270-4"]),
    Beat::new("rate per pin: 6.4 to 8 Gbit/s", BEAT_MS)
        .note("The per-pin rate rises too, at the JEDEC baseline.", "Two bars, the second a quarter taller.")
        .detail("Vendors push beyond the baseline.", &["HBM3 6.4, HBM4 8 Gb/s"]),
    Beat::new("bandwidth per stack: 819 GB/s to 2 TB/s", BEAT_MS)
        .note("Width and rate together give up to 2 TB/s per HBM4 stack.", "Two bars, the second about 2.5x.")
        .detail("Capacity rises to 64 GB at 16-high.", &["2048 x 8 / 8 = 2048 GB/s"]),
];

const HEIGHT_BEATS: &[Beat] = &[
    Beat::new("8-high", BEAT_MS)
        .note("Eight DRAM dies on the base die, well under the height limit.", "An 8-high stack under the pink limit plane.")
        .detail("Height includes every die and joint.", &["Limit 720 um"]),
    Beat::new("12-high", BEAT_MS)
        .note("Four more dies add capacity and height, and the heat starts to build.", "The stack grows to 12 dies.")
        .detail("Thinner dies keep it under the limit.", &["30-50 um dies"]),
    Beat::new("16-high, under a raised limit", BEAT_MS)
        .note("Sixteen dies needed the limit raised from 720 to 775 um; the lower dies run hottest.", "The stack reaches 16; the plane rises; the bottom glows.")
        .detail("Heat leaves through the top.", &["720 -> 775 um (press reports)"]),
];

const BONDSEC_BEATS: &[Beat] = &[
    Beat::new("microbumps between the dies", BEAT_MS)
        .note("Opened up: microbumps sit between every pair of dies.", "The stack pulls apart; yellow bumps show.")
        .detail("Bump pitch ~40 um, shrinking.", &["SemiEngineering"]),
    Beat::new("bonded on bumps", BEAT_MS)
        .note("Closed, each joint still leaves a small gap.", "The stack closes up.")
        .detail("HBM4 keeps microbumps.", &["SemiEngineering"]),
    Beat::new("hybrid bonding: no gap", BEAT_MS)
        .note("Hybrid bonding joins copper directly; the gaps vanish and the stack gets shorter.", "The bumps disappear and the stack shrinks.")
        .detail("Expected beyond 16-high.", &["Hybrid bonding"]),
];

const COWOSSEC_BEATS: &[Beat] = &[
    Beat::new("the interposer's short, dense wiring", BEAT_MS)
        .note("The interposer carries the wide buses between every stack and the GPU.", "Close on the wiring between stack and GPU.")
        .detail("Only silicon wiring is fine enough.", &["2.5D packaging"]),
    Beat::new("on a package substrate", BEAT_MS)
        .note("The interposer sits on a package substrate that connects to the board.", "The whole package from the side.")
        .detail("Chip-on-Wafer-on-Substrate.", &["CoWoS (TSMC)"]),
    Beat::new("packaging capacity sets output", BEAT_MS)
        .note("Almost every high-end AI accelerator uses CoWoS, and its capacity, not wafers, has limited how many ship.", "The package from above.")
        .detail("TSMC has been expanding it with outside assembly houses.", &["CoWoS capacity constraint (Tom's Hardware, TrendForce)"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note("Micron makes HBM.", "The first wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["HBM makers: SK hynix, Samsung, Micron"]),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note("SK hynix makes HBM.", "The second wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["SK hynix ticker: 000660.KS"]),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note("Samsung makes HBM.", "The third wafer is in the spotlight.")
        .detail("Packaging: TSMC (TSM), with ASE and Amkor.", &["Samsung ticker: 005930.KS"]),
];

const RISKS_BEATS: &[Beat] = &[
    Beat::new("packaging capacity", BEAT_MS)
        .note("Finished GPUs wait on interposer packaging; one supplier does most of it.", "GPU dies queue at a packaging line.")
        .detail("Capacity has been expanding but stayed tight.", &["CoWoS (TSMC)"]),
    Beat::new("stack yield falls with height", BEAT_MS)
        .note("A stack is only good if every die and joint is good, so yield drops as stacks grow.", "Bars for 8, 12 and 16-high at 99% per die.")
        .detail("99% per die is illustrative.", &["0.99^8 = 92%, ^12 = 89%, ^16 = 85%"]),
    Beat::new("heat in tall stacks", BEAT_MS)
        .note("Heat from the lower dies must pass through the whole stack.", "A 16-high stack glowing hot at the bottom.")
        .detail("Limits how fast and how tall stacks can go.", &["Heat path"]),
];

zoom_scene_impl!(TsvZ, TSV_BEATS, HbmZoom::Tsv);
zoom_scene_impl!(BaseZ, BASE_BEATS, HbmZoom::Base);
zoom_scene_impl!(ChannelsZ, CHANNELS_BEATS, HbmZoom::Channels);
zoom_scene_impl!(BondZ, BOND_BEATS, HbmZoom::Bond);
zoom_scene_impl!(CowosZ, COWOS_BEATS, HbmZoom::Cowos);
zoom_scene_impl!(SecStack, STACK_BEATS, HbmZoom::Stack);
zoom_scene_impl!(SecParts, PARTS_BEATS, HbmZoom::Parts);
zoom_scene_impl!(SecBuild, BUILD_BEATS, HbmZoom::Build);
zoom_scene_impl!(SecGens, GENS_BEATS, HbmZoom::Gens);
zoom_scene_impl!(SecHeight, HEIGHT_BEATS, HbmZoom::Height);
zoom_scene_impl!(SecBond, BONDSEC_BEATS, HbmZoom::BondSec);
zoom_scene_impl!(SecCowos, COWOSSEC_BEATS, HbmZoom::CowosSec);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, HbmZoom::Makers);
zoom_scene_impl!(SecRisks, RISKS_BEATS, HbmZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecStack),
    || Box::new(SecParts),
    || Box::new(SecBuild),
    || Box::new(SecGens),
    || Box::new(SecHeight),
    || Box::new(SecBond),
    || Box::new(SecCowos),
    || Box::new(SecMakers),
    || Box::new(SecRisks),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(beat: usize, local: f32) -> Time {
        Time { ms: 0, beat, local, beat_start: 0 }
    }

    fn scenes() -> Vec<(String, Box<dyn Scene>)> {
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), Box::new(MemHbm))];
        for z in ZOOMS {
            v.push((z.key.to_string(), (z.build)()));
        }
        for (i, mk) in SECTIONS.iter().enumerate() {
            v.push(((i + 1).to_string(), mk()));
        }
        v
    }

    #[test]
    fn every_frame_is_a_picture_that_moves() {
        for (name, scene) in scenes() {
            let p = Player::new(scene, Instant::now());
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(397) {
                let img = p.pixels(&p.time_at(ms), 160, 90).expect("pixel frame");
                assert_eq!(img.dimensions(), (160, 90), "{name}");
                seen.insert(img.into_raw());
            }
            assert!(seen.len() > 12, "{name}: {} distinct frames", seen.len());
        }
    }

    /// Text and picture agree on how many beats each scene has.
    #[test]
    fn beats_match_their_pictures() {
        assert_eq!(BEATS.len(), poly3d::HBM_OVERVIEW_BEATS);
        for z in ZOOMS {
            assert_eq!((z.build)().beats().len(), zoom_scene(z.key).unwrap().beats(), "zoom {}", z.key);
        }
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            assert_eq!(mk().beats().len(), zoom_scene(key).unwrap().beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("HBM STACK")
            .unwrap()
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(heads, SECTIONS.len() + 1, "one scene per section but the sources");
    }

    #[test]
    fn beats_have_text_for_the_popup() {
        let all = BEATS
            .iter()
            .chain(TSV_BEATS)
            .chain(BASE_BEATS)
            .chain(CHANNELS_BEATS)
            .chain(BOND_BEATS)
            .chain(COWOS_BEATS)
            .chain(STACK_BEATS)
            .chain(PARTS_BEATS)
            .chain(BUILD_BEATS)
            .chain(GENS_BEATS)
            .chain(HEIGHT_BEATS)
            .chain(BONDSEC_BEATS)
            .chain(COWOSSEC_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISKS_BEATS);
        for b in all {
            assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}", b.caption);
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_hbm_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_hbm_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else {
            return;
        };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for (name, scene) in scenes() {
            let beats = scene.beats().len();
            let p = Player::new(scene, Instant::now());
            for beat in 0..beats {
                let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                let img = p.pixels(&at(beat, 0.6), w, h).expect("pixel frame");
                img.save(dir.join(format!("{name}_{beat}.png"))).unwrap();
            }
        }
    }
}
