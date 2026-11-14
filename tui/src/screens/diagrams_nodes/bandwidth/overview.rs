// BANDWIDTH overview: a processor with its memory controller, DDR channels to DIMMs, data dots on
// the lanes, an HBM stack beside the processor, a gauge of GB/s, and the memory wall bars, played
// back from the Blender scene (tools/pbr3d/blender/bandwidth_overview.py) in the picture-and-panel
// template. One pin, a 64-pin channel, four channels, the holes in real traffic, the bus turning
// around, HBM, and the memory wall. Zoom-ins a-e (tools/pbr3d/blender/bandwidth_zooms.py).
//
// Sources: JEDEC JESD238 (HBM3, 6.4 Gb/s, 819 GB/s per device); Micron GDDR6 flyer (32 DQ, 16 Gb/s);
// Micron GDDR6X PAM4 brief; Micron DDR5 modules; Gholami et al., AI and Memory Wall (arXiv 2403.14123).

use super::super::blender::{Cell, Page, BEAT_MS};
use super::zoom;
use crate::ui::anim::{Beat, Scene, Zoom};

const BEATS: &[Beat] = &[
    Beat::new("one pin: 3200 million transfers a second on a single data wire", BEAT_MS)
        .note(
            "Bandwidth starts with one data pin. DDR4-3200 moves 3200 million transfers a second on each pin. A channel is built from many such pins, so this is the first factor.",
            "one copper wire from the processor to a green DIMM, a few green dots moving along it, and the gauge on the right barely lifted",
        )
        .detail(
            "Peak bandwidth is transfers per second per pin times the number of data pins, divided by 8 bits per byte.",
            &[
                "DDR4-3200: 3200 MT/s per pin (section 3)",
                "Peak = MT/s x data pins / 8 (section 3)",
            ],
        ),
    Beat::new("a 64-pin channel: the wire becomes a ribbon and one channel peaks at 25.6 GB/s", BEAT_MS)
        .note(
            "A DDR channel is 64 data pins wide. All of them switch together, so the channel moves 64 bits per transfer. The gauge climbs to one channel's peak.",
            "the single wire turned into a ribbon of copper lanes running into the DIMM, with dots on every lane and the gauge climbing",
        )
        .detail(
            "The channel is the unit of bandwidth. The chips on its DIMM share the channel's width.",
            &[
                "64 data pins per DDR channel (section 2)",
                "3200 MT/s x 64 / 8 = 25.6 GB/s per channel (section 3)",
            ],
        ),
    Beat::new("four channels: each adds its own bandwidth, 102.4 GB/s peak", BEAT_MS)
        .note(
            "The processor's memory controller drives several channels at once, each with its own DIMM. Four channels give 102.4 GB/s peak.",
            "three more ribbons and DIMMs appear beside the first, dots on every lane, and the gauge climbs to the four-channel level",
        )
        .detail(
            "Servers add channels to add bandwidth, one controller driving them all.",
            &[
                "4 x 25.6 = 102.4 GB/s peak (section 3)",
                "The memory controller drives every channel (section 2)",
            ],
        ),
    Beat::new("real traffic has holes: peak is a ceiling, not what the workload gets", BEAT_MS)
        .note(
            "Refresh, waits for rows to open and banks to free up leave slots on the bus with no data, so real traffic runs below the peak.",
            "pink markers sit on the lanes at the places where no data passes, and the dots skip them",
        )
        .detail(
            "Peak is what the pins can do; effective bandwidth is what the workload gets.",
            &[
                "Effective bandwidth loses slots to turnarounds, refresh and waits (section 5)",
                "Real traffic gets less than the peak (section 1)",
            ],
        ),
    Beat::new("reads and writes share the wires, so the bus turns around", BEAT_MS)
        .note(
            "The same wires carry reads one way and writes the other. Switching direction leaves the bus idle for a moment each time.",
            "green dots run into the DIMMs, then orange dots come back along the same lanes, with pink markers at each switch",
        )
        .detail(
            "Each turnaround costs bus time, so controllers try to batch reads and writes.",
            &[
                "The bus turning around between reads and writes (section 5)",
                "Scheduling and conflicts are on the BANK node",
            ],
        ),
    Beat::new("HBM: very wide and very close to the processor", BEAT_MS)
        .note(
            "An HBM3 stack sits beside the processor on an interposer with 1024 data pins at 6.4 Gb/s, which gives 819 GB/s from one stack.",
            "a stack of thin silicon dies on a tan interposer beside the processor, a dense comb of short copper wires between them, and the gauge at full height",
        )
        .detail(
            "Many slower pins over short wires, instead of a few fast pins over long board wires.",
            &[
                "HBM3: 1024 pins x 6.4 Gb/s = 819 GB/s per device (JEDEC JESD238)",
                "GDDR6 chip: 64 GB/s (section 4)",
            ],
        ),
    Beat::new("the memory wall: compute has outgrown bandwidth", BEAT_MS)
        .note(
            "Over twenty years peak server compute grew about 3.0x every two years, and DRAM bandwidth about 1.6x. Many workloads now wait on memory rather than arithmetic.",
            "a tall pink compute bar far above a short cyan DRAM bandwidth bar; the bar heights are illustrative and not to scale",
        )
        .detail(
            "Bandwidth, not arithmetic, often sets the speed of large models.",
            &[
                "Compute 3.0x every two years, DRAM bandwidth 1.6x (Gholami et al., arXiv 2403.14123)",
                "About 60,000x against 100x over twenty years (section 7)",
            ],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "one pin: transfers per clock, then PAM4",
        build: || -> Box<dyn Scene> { zoom::pin() },
    },
    Zoom {
        key: 'b',
        label: "DDR5: two subchannels per DIMM",
        build: || -> Box<dyn Scene> { zoom::subch() },
    },
    Zoom {
        key: 'c',
        label: "GDDR next to HBM",
        build: || -> Box<dyn Scene> { zoom::gddr() },
    },
    Zoom {
        key: 'd',
        label: "where peak goes: turnarounds and refresh",
        build: || -> Box<dyn Scene> { zoom::gaps() },
    },
    Zoom {
        key: 'e',
        label: "the memory wall",
        build: || -> Box<dyn Scene> { zoom::wall() },
    },
];

static OVERVIEW: Cell = std::sync::OnceLock::new();

pub fn build() -> Box<dyn Scene> {
    Box::new(Page {
        cell: &OVERVIEW,
        glb: include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_overview.glb"),
        beats: BEATS,
        zooms: ZOOMS,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn overview_is_explained_and_keyed() {
        let s = build();
        assert_eq!(s.beats().len(), 7);
        super::super::super::blender::explained(s.as_ref(), "BANDWIDTH overview");
        let keys: String = s.zooms().iter().map(|z| z.key).collect();
        assert_eq!(keys, "abcde");
    }

    #[test]
    fn overview_draws_every_beat() {
        super::super::super::blender::draws_every_beat(build().as_ref(), "BANDWIDTH overview");
    }
}
