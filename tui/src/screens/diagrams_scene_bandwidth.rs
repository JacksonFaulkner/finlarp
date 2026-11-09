// BANDWIDTH page: how much data memory can move, drawn in 3D by poly3d, on the CELL
// page's template. The overview builds a peak bandwidth: one pin's data rate, a
// 64-pin channel, four channels, the gaps that keep real traffic below peak, the bus
// turning around between reads and writes, an HBM stack (very wide, very close), and
// the memory wall. Each zoom (a-e) is its own 3D scene: a one pin (DDR, PAM4), b DDR5
// subchannels, c GDDR next to HBM, d where peak goes, e the memory wall. Sections 1-9
// each have one.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: see section 10 of MEM_BANDWIDTH.txt. JEDEC JESD238 HBM3 (6.4 Gb/s, 819 GB/s
// per device); Micron GDDR6 flyer (32 DQ, 16 Gb/s); Micron DDR5 (two 40-bit channels
// per DIMM, BL16); Micron GDDR6X PAM4 brief; Gholami et al., AI and Memory Wall
// (arXiv 2403.14123).

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::BwZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 6500;
const OVERVIEW_MS: u64 = 13000;

const BEATS: &[Beat] = &[
    Beat::new("one pin: so many transfers per second", OVERVIEW_MS)
        .note(
            "Bandwidth starts with one data pin. DDR4-3200 moves 3200 million transfers a second on each pin, one bit per transfer: 0.4 GB/s.",
            "One wire of the first channel carries green dots to the processor; the gauge on the left is low.",
        )
        .detail(
            "Peak bandwidth = transfers per second per pin x data pins / 8.",
            &["DDR4-3200: 3200 MT/s per pin", "3200 x 1 bit / 8 = 0.4 GB/s"],
        ),
    Beat::new("a channel: 64 data pins side by side", OVERVIEW_MS)
        .note(
            "A DDR channel is 64 data pins wide. All of them switch together, so the channel moves 64 bits per transfer: 25.6 GB/s.",
            "The other wires of the channel fill with dots and the gauge climbs.",
        )
        .detail("This is per channel; the chips on the DIMM share it.", &["3200 MT/s x 64 / 8 = 25.6 GB/s per channel"]),
    Beat::new("more channels: each adds its own 25.6 GB/s", OVERVIEW_MS)
        .note(
            "The processor's memory controller drives several channels at once, each with its own DIMM. Four channels give 102.4 GB/s peak.",
            "Three more channels and DIMMs appear; the gauge climbs again.",
        )
        .detail("Servers add channels to add bandwidth.", &["4 x 25.6 = 102.4 GB/s"]),
    Beat::new("real traffic has holes: peak is a ceiling", OVERVIEW_MS)
        .note(
            "Refresh, row misses and bank conflicts leave slots on the bus with no data, so real traffic runs below the peak.",
            "Pink markers appear in the streams where slots go empty.",
        )
        .detail("Peak is what the pins can do; effective is what the workload gets.", &["Refresh, row misses, conflicts (BANK node)"]),
    Beat::new("reads and writes share the wires: the bus turns around", OVERVIEW_MS)
        .note(
            "The same wires carry reads one way and writes the other. Switching direction leaves the bus idle for a moment each time.",
            "The dots stop, then run the other way in orange, then stop and turn back.",
        )
        .detail("Controllers batch reads and writes to turn around less often.", &["Turnarounds cost bus time"]),
    Beat::new("HBM: very wide and very close", OVERVIEW_MS)
        .note(
            "An HBM3 stack sits beside the processor with 1024 data pins at 6.4 Gb/s: 819 GB/s from one stack.",
            "A stack of dies rises at the front with a dense ribbon of wires; the gauge jumps.",
        )
        .detail("Many slower pins over short wires instead of a few fast ones over long wires.", &["HBM3: 6.4 Gb/s, 819 GB/s per device (JEDEC JESD238)"]),
    Beat::new("the memory wall: compute has outgrown bandwidth", OVERVIEW_MS)
        .note(
            "Over twenty years peak compute grew about 60,000x and DRAM bandwidth about 100x. Many workloads now wait on memory, not arithmetic.",
            "Two bars rise beside the gauge, compute far above bandwidth; then the system returns to one pin.",
        )
        .detail("Bandwidth, not FLOPS, often sets the speed of large models.", &["Compute 3.0x, DRAM bandwidth 1.6x every 2 years (Gholami et al.)"]),
];

const ZOOMS: &[Zoom] = &[
    Zoom { key: 'a', label: "one pin: transfers per clock, then PAM4", build: || -> Box<dyn Scene> { Box::new(PinZ) } },
    Zoom { key: 'b', label: "DDR5: two subchannels per DIMM", build: || -> Box<dyn Scene> { Box::new(SubchZ) } },
    Zoom { key: 'c', label: "GDDR next to HBM", build: || -> Box<dyn Scene> { Box::new(HbmZ) } },
    Zoom { key: 'd', label: "where peak goes: turnarounds and refresh", build: || -> Box<dyn Scene> { Box::new(GapsZ) } },
    Zoom { key: 'e', label: "the memory wall", build: || -> Box<dyn Scene> { Box::new(WallZ) } },
];

/// The overview at `t`, turned by the user's `view`, with the beat's notes on it.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes { what: b.what, why: b.why, facts: b.facts };
    poly3d::render_bw_overview(t.beat, t.local as f64, view, Some(&notes), w as usize, h as usize, px::BG)
}

/// The BANDWIDTH overview: how a peak bandwidth is built.
pub struct MemBandwidth;

impl Scene for MemBandwidth {
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
pub fn zoom_scene(key: char) -> Option<BwZoom> {
    Some(match key {
        'a' => BwZoom::Pin,
        'b' => BwZoom::Subchannels,
        'c' => BwZoom::Hbm,
        'd' => BwZoom::Gaps,
        'e' => BwZoom::Wall,
        '1' => BwZoom::Peak,
        '2' => BwZoom::Parts,
        '3' => BwZoom::Order,
        '4' => BwZoom::Kinds,
        '5' => BwZoom::GapsSec,
        '6' => BwZoom::Numbers,
        '7' => BwZoom::WallSec,
        '8' => BwZoom::Makers,
        '9' => BwZoom::Risks,
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
                Some(poly3d::render_bw_zoom(
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

const PIN_BEATS: &[Beat] = &[
    Beat::new("one transfer per clock", BEAT_MS)
        .note("A clock runs above the pin. Sending one bit per cycle gives one transfer per clock.", "A square wave moves above the wire; one block per cycle rides along.")
        .detail("This is how the oldest memory worked.", &["1 transfer per clock"]),
    Beat::new("DDR: a transfer on each edge", BEAT_MS)
        .note("Double data rate sends a bit on the rising and the falling edge, two per cycle.", "Extra blocks grow in between, one per falling edge.")
        .detail("DDR4-3200: 3200 MT/s from a 1600 MHz clock.", &["2 transfers per clock"]),
    Beat::new("PAM4: four levels, two bits per symbol", BEAT_MS)
        .note("Instead of two voltage levels, PAM4 uses four, so each symbol carries two bits.", "The blocks take four different heights.")
        .detail("GDDR6X uses PAM4 to double the bits per symbol.", &["PAM4: 2 bits per symbol (Micron GDDR6X brief)"]),
];

const SUBCH_BEATS: &[Beat] = &[
    Beat::new("DDR4: one 64-bit channel, chips in lockstep", BEAT_MS)
        .note("All eight chips on a DDR4 DIMM answer every request together: a 64-byte line is 8 transfers of 8 bytes.", "All eight chips pulse together down the wires.")
        .detail("One request at a time per DIMM.", &["BL8 x 8 bytes = 64 bytes"]),
    Beat::new("DDR5: two independent 32-bit subchannels", BEAT_MS)
        .note("A DDR5 DIMM splits into two 32-bit subchannels (40 with ECC), each with half the chips.", "The halves turn orange and cyan and pulse on their own.")
        .detail("BL16 x 4 bytes = the same 64-byte line.", &["Two 40-bit independent channels per DIMM (Micron)", "DDR5 burst length 16"]),
    Beat::new("two requests at once", BEAT_MS)
        .note("Each subchannel serves its own request, so one DIMM handles two at the same time.", "Both halves stream different requests side by side.")
        .detail("More independent channels means more parallel requests.", &["DDR5-4800 DIMM: 2 x 32 x 4.8 / 8 = 38.4 GB/s"]),
];

const HBM_BEATS: &[Beat] = &[
    Beat::new("GDDR6: 32 fast pins per chip", BEAT_MS)
        .note("Graphics boards put GDDR6 chips around the GPU on the board. Each has 32 data pins at up to 16 Gb/s: 64 GB/s.", "Four green chips around the GPU send dots along board traces.")
        .detail("Fast pins over long board wires.", &["GDDR6: 32 DQ, up to 16 Gb/s (Micron)", "32 x 16 / 8 = 64 GB/s"]),
    Beat::new("HBM3: 1024 pins per stack, right beside the GPU", BEAT_MS)
        .note("An HBM3 stack sits next to the GPU on an interposer: 1024 data pins at 6.4 Gb/s, 819 GB/s.", "A stack of dies beside the GPU with a dense comb of short wires.")
        .detail("One stack is worth about thirteen GDDR6 chips.", &["HBM3: 819 GB/s per device (JEDEC JESD238)"]),
    Beat::new("short, dense wiring makes the width possible", BEAT_MS)
        .note("Only an interposer's short, fine wires can carry a thousand signals between two chips, so HBM trades pin speed for pin count.", "Both kinds stream at once; the interposer is named.")
        .detail("See HBM STACK for how the stack is built.", &["Wide and slow vs narrow and fast"]),
];

const GAPS_BEATS: &[Beat] = &[
    Beat::new("reads stream steadily", BEAT_MS)
        .note("A run of reads keeps the channel's data bus full.", "Green dots run from the DIMM to the processor.")
        .detail("This is the peak case.", &["25.6 GB/s per DDR4-3200 channel"]),
    Beat::new("a write, and back: the bus turns around", BEAT_MS)
        .note("Writes use the same wires the other way. Each switch leaves the bus empty for a moment.", "The dots stop, run back in orange, stop again, and turn back.")
        .detail("Batching reads and writes cuts turnarounds.", &["Turnaround: bus idle"]),
    Beat::new("a refresh: no data at all", BEAT_MS)
        .note("While the banks refresh, the channel carries nothing.", "The stream fades and pink markers fill the wires.")
        .detail("Refresh time grows with chip density (BANK node).", &["Refresh: bus idle"]),
];

const WALL_BEATS: &[Beat] = &[
    Beat::new("peak compute: 3.0x every two years", BEAT_MS)
        .note("Peak server compute has grown about 3.0x every two years for twenty years.", "Pink bars climb steeply across eleven two-year steps.")
        .detail("About 60,000x in twenty years.", &["Gholami et al., AI and Memory Wall (arXiv 2403.14123)"]),
    Beat::new("DRAM bandwidth 1.6x, interconnect 1.4x", BEAT_MS)
        .note("DRAM bandwidth grew about 1.6x every two years, interconnect 1.4x.", "Cyan and purple bars climb far more slowly.")
        .detail("About 100x and 30x in twenty years.", &["Gholami et al."]),
    Beat::new("the gap is the wall", BEAT_MS)
        .note("Each unit of compute now has far less bandwidth behind it, so many workloads wait on memory.", "A bracket marks the gap between the tallest bars.")
        .detail("Why HBM capacity and bandwidth are the bottleneck for AI hardware.", &["60,000x vs 100x"]),
];

const PEAK_BEATS: &[Beat] = &[
    Beat::new("one pin", BEAT_MS)
        .note("Start with one data pin at 3200 million transfers a second.", "One wire carries dots; the gauge reads 0.4 GB/s.")
        .detail("Rate per pin is the first factor.", &["0.4 GB/s"]),
    Beat::new("x 64 pins: one channel", BEAT_MS)
        .note("A channel puts 64 pins side by side.", "The channel fills; the gauge reads 25.6 GB/s.")
        .detail("Width is the second factor.", &["25.6 GB/s"]),
    Beat::new("x channels", BEAT_MS)
        .note("Several channels run in parallel.", "Four channels; the gauge reads 102.4 GB/s.")
        .detail("Channel count is the third.", &["102.4 GB/s"]),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("pin: the data rate", BEAT_MS)
        .note("One wire, so many transfers per second.", "One wire lights; the rest go grey.")
        .detail("DDR4-3200: 3200 MT/s.", &["MT/s = million transfers per second"]),
    Beat::new("channel: the width", BEAT_MS)
        .note("64 data pins side by side make one channel.", "The whole ribbon lights.")
        .detail("DDR5 splits it into two 32-bit halves.", &["64 data pins"]),
    Beat::new("DIMM: the chips behind it", BEAT_MS)
        .note("A DIMM's chips together fill the channel's width.", "The DIMM at the end lights.")
        .detail("Eight x8 chips make 64 bits.", &["8 chips x 8 pins = 64"]),
    Beat::new("controller: drives the channels", BEAT_MS)
        .note("The memory controller in the processor runs every channel.", "The processor block lights.")
        .detail("Its channel count caps the system's bandwidth.", &["One controller, many channels"]),
    Beat::new("channels: more in parallel", BEAT_MS)
        .note("Each extra channel adds its own bandwidth.", "Three more channels appear.")
        .detail("Servers have many channels.", &["4 x 25.6 = 102.4 GB/s"]),
    Beat::new("HBM: width at short range", BEAT_MS)
        .note("An HBM stack beside the processor gives 1024 pins.", "The stack and its dense ribbon appear.")
        .detail("819 GB/s per HBM3 stack.", &["JEDEC JESD238"]),
];

const ORDER_BEATS: &[Beat] = &[
    Beat::new("1. 3200 MT/s on one pin", BEAT_MS)
        .note("DDR4-3200 moves 3200 million transfers a second per pin.", "One wire carries dots; line 1 appears.")
        .detail("One bit per transfer.", &["3200 MT/s"]),
    Beat::new("2. x 64 pins", BEAT_MS)
        .note("A channel is 64 pins wide: 204,800 million bits a second.", "The channel fills; line 2 appears.")
        .detail("Every pin switches together.", &["3200 x 64 = 204,800 Mb/s"]),
    Beat::new("3. / 8 bits per byte", BEAT_MS)
        .note("Divide by 8 to turn bits into bytes.", "Line 3 appears beside the gauge.")
        .detail("GB/s, not Gb/s.", &["8 bits = 1 byte"]),
    Beat::new("4. = 25.6 GB/s per channel", BEAT_MS)
        .note("One DDR4-3200 channel peaks at 25.6 GB/s.", "The gauge climbs to 25.6.")
        .detail("Per channel, not per chip.", &["25.6 GB/s"]),
    Beat::new("5. x 4 channels = 102.4 GB/s", BEAT_MS)
        .note("Four channels make 102.4 GB/s peak.", "Three more channels appear; the gauge climbs.")
        .detail("Then the sum clears for the next pass.", &["102.4 GB/s"]),
];

const KINDS_BEATS: &[Beat] = &[
    Beat::new("DDR5-4800 DIMM: 38.4 GB/s", BEAT_MS)
        .note("Two 32-bit subchannels at 4.8 Gb/s per pin.", "The green bar is in the spotlight.")
        .detail("Main memory in PCs and servers.", &["2 x 32 x 4.8 / 8 = 38.4 GB/s"]),
    Beat::new("GDDR6 chip: 64 GB/s", BEAT_MS)
        .note("32 pins at 16 Gb/s each.", "The cyan bar is in the spotlight.")
        .detail("Graphics boards use many chips.", &["GDDR6: 32 DQ, 16 Gb/s (Micron)"]),
    Beat::new("HBM3 stack: 819 GB/s", BEAT_MS)
        .note("1024 pins at 6.4 Gb/s each.", "The orange bar towers over the rest.")
        .detail("AI accelerators use several stacks.", &["HBM3: 819 GB/s per device (JEDEC)"]),
];

const GAPSEC_BEATS: &[Beat] = &[
    Beat::new("peak: every slot full", BEAT_MS)
        .note("Peak assumes data in every bus slot. Real traffic starts with a run of reads.", "A full cyan peak lane; green reads begin below it.")
        .detail("Block lengths are illustrative.", &["Peak = rate x width"]),
    Beat::new("turnarounds around the writes", BEAT_MS)
        .note("Switching to writes and back leaves empty slots.", "Pink turnaround blocks frame an orange write run.")
        .detail("Bus idle each switch.", &["Turnaround"]),
    Beat::new("refresh and row misses", BEAT_MS)
        .note("Refresh and waits for rows to open leave more holes.", "Pink refresh and row-miss blocks break up the reads.")
        .detail("Effective bandwidth is what is left.", &["Effective < peak"]),
];

const NUMBERS_BEATS: &[Beat] = &[
    Beat::new("rate per pin", BEAT_MS)
        .note("DDR4-3200 3.2, DDR5-4800 4.8, GDDR6 16, HBM3 6.4 Gb/s per pin.", "Four bars: GDDR6 is the fastest per pin.")
        .detail("HBM's pins are slower than GDDR's.", &["Gb/s per pin"]),
    Beat::new("data pins", BEAT_MS)
        .note("64 for a DDR channel or DIMM, 32 for a GDDR6 chip, 1024 for an HBM3 stack.", "Four bars: HBM's towers.")
        .detail("Width is HBM's advantage.", &["Data pins per device"]),
    Beat::new("bandwidth per device", BEAT_MS)
        .note("25.6, 38.4, 64 and 819.2 GB/s.", "Four bars: rate x pins / 8.")
        .detail("Log scales throughout.", &["GB/s = Gb/s x pins / 8"]),
];

const WALLSEC_BEATS: &[Beat] = &[
    Beat::new("bandwidth per unit of compute, falling", BEAT_MS)
        .note("Divide DRAM bandwidth growth (1.6x) by compute growth (3.0x) every two years.", "Bars step down from cyan towards pink.")
        .detail("Log scale.", &["(1.6 / 3.0) per 2 years (Gholami et al.)"]),
    Beat::new("twenty years: about 1/600", BEAT_MS)
        .note("After twenty years each unit of compute has roughly 600x less bandwidth behind it.", "The last bar is a sliver.")
        .detail("60,000x vs 100x.", &["Gholami et al."]),
    Beat::new("large models wait on memory", BEAT_MS)
        .note("Workloads that read lots of data per operation, like serving large models, are limited by bandwidth.", "A note appears under the last bar.")
        .detail("This is the case for HBM.", &["Memory bandwidth can dominate decoder models (Gholami et al.)"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note("Micron makes DRAM, GDDR and HBM.", "The first wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["DRAM makers: Micron, SK hynix, Samsung"]),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note("SK hynix makes DRAM, GDDR and HBM.", "The second wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["SK hynix ticker: 000660.KS"]),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note("Samsung makes DRAM, GDDR and HBM.", "The third wafer is in the spotlight.")
        .detail("Market share is on the market pages.", &["Samsung ticker: 005930.KS"]),
];

const RISKS_BEATS: &[Beat] = &[
    Beat::new("the memory wall", BEAT_MS)
        .note("Compute keeps outgrowing bandwidth, so more hardware sits waiting on memory.", "A big processor fed through a thin pipe.")
        .detail("Every generation needs a bigger bandwidth jump.", &["3.0x vs 1.6x per 2 years"]),
    Beat::new("pins cost area and power", BEAT_MS)
        .note("Every extra pin needs package area, board routing and power to drive it.", "A package underside crowded with pins.")
        .detail("Faster pins cost more energy per bit.", &["Width and rate both have limits"]),
    Beat::new("HBM needs advanced packaging", BEAT_MS)
        .note("HBM's width depends on an interposer next to the processor, which needs specialised packaging capacity.", "An HBM stack beside a processor on a shared interposer.")
        .detail("See the HBM STACK node.", &["Interposer packaging"]),
];

zoom_scene_impl!(PinZ, PIN_BEATS, BwZoom::Pin);
zoom_scene_impl!(SubchZ, SUBCH_BEATS, BwZoom::Subchannels);
zoom_scene_impl!(HbmZ, HBM_BEATS, BwZoom::Hbm);
zoom_scene_impl!(GapsZ, GAPS_BEATS, BwZoom::Gaps);
zoom_scene_impl!(WallZ, WALL_BEATS, BwZoom::Wall);
zoom_scene_impl!(SecPeak, PEAK_BEATS, BwZoom::Peak);
zoom_scene_impl!(SecParts, PARTS_BEATS, BwZoom::Parts);
zoom_scene_impl!(SecOrder, ORDER_BEATS, BwZoom::Order);
zoom_scene_impl!(SecKinds, KINDS_BEATS, BwZoom::Kinds);
zoom_scene_impl!(SecGaps, GAPSEC_BEATS, BwZoom::GapsSec);
zoom_scene_impl!(SecNumbers, NUMBERS_BEATS, BwZoom::Numbers);
zoom_scene_impl!(SecWall, WALLSEC_BEATS, BwZoom::WallSec);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, BwZoom::Makers);
zoom_scene_impl!(SecRisks, RISKS_BEATS, BwZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecPeak),
    || Box::new(SecParts),
    || Box::new(SecOrder),
    || Box::new(SecKinds),
    || Box::new(SecGaps),
    || Box::new(SecNumbers),
    || Box::new(SecWall),
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
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), Box::new(MemBandwidth))];
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
        assert_eq!(BEATS.len(), poly3d::BW_OVERVIEW_BEATS);
        for z in ZOOMS {
            assert_eq!((z.build)().beats().len(), zoom_scene(z.key).unwrap().beats(), "zoom {}", z.key);
        }
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            assert_eq!(mk().beats().len(), zoom_scene(key).unwrap().beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("BANDWIDTH")
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
            .chain(PIN_BEATS)
            .chain(SUBCH_BEATS)
            .chain(HBM_BEATS)
            .chain(GAPS_BEATS)
            .chain(WALL_BEATS)
            .chain(PEAK_BEATS)
            .chain(PARTS_BEATS)
            .chain(ORDER_BEATS)
            .chain(KINDS_BEATS)
            .chain(GAPSEC_BEATS)
            .chain(NUMBERS_BEATS)
            .chain(WALLSEC_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISKS_BEATS);
        for b in all {
            assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}", b.caption);
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_bw_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_bw_frames() {
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
