// BANDWIDTH zoom-ins a-e in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/bandwidth_zooms.py: a one pin (clock, DDR edges, PAM4), b DDR5 subchannels,
// c GDDR next to HBM, d the bus as slots (turnarounds, refresh, row misses), e the memory wall.
// Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

pub const PIN_BEATS: &[Beat] = &[
    Beat::new("one transfer per clock: a clock sets the pace of one data pin", BEAT_MS)
        .note(
            "A clock runs above the pin. Sending one bit per clock gives one transfer per clock, the oldest way memory worked.",
            "a gold square-wave clock above a copper pin, with one green dot per clock cycle moving along the wire",
        )
        .detail(
            "The clock sets the pace; the rate per pin is the transfers per second on that wire.",
            &[
                "DDR4-3200 runs from a 1600 MHz clock (data rate detail)",
                "One transfer per clock edge, then two (section 1 data rate)",
            ],
        ),
    Beat::new("DDR: a transfer on each clock edge, so two per clock", BEAT_MS)
        .note(
            "Double data rate sends a bit on the rising edge and again on the falling edge. Green blocks appear under the wire, one for each edge.",
            "the clock as before, and a row of green blocks under the copper pin, one for every edge of the clock",
        )
        .detail(
            "DDR sends one transfer on each edge of the clock, which doubles the transfers at the same clock rate.",
            &[
                "DDR sends one on each clock edge (data rate detail)",
                "DDR4-3200: 3200 MT/s from a 1600 MHz clock (data rate detail)",
            ],
        ),
    Beat::new("DDR4-3200: 3200 million transfers a second on each pin", BEAT_MS)
        .note(
            "The same DDR pattern at the DDR4-3200 rate: a dense run of transfers each second on the one pin, the rate that the peak arithmetic starts from.",
            "a dense, steady run of green blocks under the wire, paced by the clock above",
        )
        .detail(
            "This is the first factor in the peak. Every other factor multiplies it.",
            &[
                "3200 MT/s on one pin (section 3)",
                "Per-pin rate is the first factor in peak bandwidth (section 1)",
            ],
        ),
    Beat::new("PAM4: four voltage levels, so each symbol carries two bits", BEAT_MS)
        .note(
            "Instead of two voltage levels, PAM4 uses four, so each symbol carries two bits. GDDR6X uses it to carry more bits on the same pin.",
            "four grey level lines across the wire, and blocks at four different heights, pink and green, alternating along it",
        )
        .detail(
            "PAM4 doubles the bits per symbol without doubling the symbol rate, at the cost of smaller margins between levels.",
            &[
                "PAM4: four levels, two bits per symbol (Micron GDDR6X PAM4 brief)",
                "GDDR6X uses PAM4 (section 4)",
            ],
        ),
];

pub const SUBCH_BEATS: &[Beat] = &[
    Beat::new("DDR4: one DIMM answers together, its chips in lockstep", BEAT_MS)
        .note(
            "All the chips on a DDR4 DIMM answer each request together. A channel is 64 data pins wide, and the chips together fill that width.",
            "a green DIMM with its black chips all lit at once, and copper lanes leaving its right edge with dots on them",
        )
        .detail(
            "One request at a time goes to the whole DIMM, since its chips share the channel's width.",
            &[
                "A DDR channel is 64 data pins wide (section 2)",
                "A DIMM's chips together fill one channel's width (section 2)",
            ],
        ),
    Beat::new("DDR5: the DIMM splits into two 32-bit subchannels", BEAT_MS)
        .note(
            "A DDR5 DIMM is split into two 32-bit subchannels, each with its own half of the chips. The two halves can work on different requests.",
            "the board divides into an orange half and a cyan half, each with its own chips and its own lanes",
        )
        .detail(
            "Two independent channels per DIMM let two requests move at once.",
            &[
                "DDR5-4800 DIMM: two 32-bit subchannels x 4.8 Gb/s (section 4)",
                "Two 40-bit independent channels per DIMM (Micron DDR5 modules)",
            ],
        ),
    Beat::new("two requests at once, one on each subchannel", BEAT_MS)
        .note(
            "Each subchannel serves its own request, so one DIMM handles two at the same time. More independent channels mean more requests in parallel.",
            "cyan dots on the cyan half's lanes and orange dots on the orange half's lanes, moving side by side",
        )
        .detail(
            "Each channel adds its own bandwidth, so parallel requests add up to the peak.",
            &[
                "Each channel adds its own bandwidth (channels detail)",
                "Two subchannels run side by side on one DIMM (page text)",
            ],
        ),
    Beat::new("DDR5-4800 DIMM: 2 x 32 x 4.8 / 8 = 38.4 GB/s", BEAT_MS)
        .note(
            "Two subchannels of 32 bits, each pin at 4.8 Gb/s, make the DIMM's peak: 38.4 GB/s. The DDR4-3200 channel gave 25.6 GB/s.",
            "both halves of the DIMM lit, with dots running along the lanes of each half",
        )
        .detail(
            "The arithmetic is the same as for the channel: rate per pin, times pins, divided by 8.",
            &[
                "2 x 32 x 4.8 / 8 = 38.4 GB/s (section 4)",
                "DDR4-3200 channel: 25.6 GB/s (section 3)",
            ],
        ),
];

pub const GDDR_BEATS: &[Beat] = &[
    Beat::new("GDDR6: 32 fast pins per chip, on the graphics board", BEAT_MS)
        .note(
            "Graphics boards put GDDR6 chips beside the GPU on the board. Each chip has 32 data pins at up to 16 Gb/s, which is 64 GB/s.",
            "a black GDDR6 chip on the green board with copper lanes to the grey GPU die, and green dots moving along the lanes",
        )
        .detail(
            "Few fast pins over long board wires is the GDDR approach.",
            &[
                "GDDR6 chip: 32 pins x 16 Gb/s = 64 GB/s (section 4)",
                "GDDR6: 32 DQ per component, up to 16 Gb/s (Micron GDDR6 flyer)",
            ],
        ),
    Beat::new("HBM3: 1024 pins in one stack, beside the GPU", BEAT_MS)
        .note(
            "An HBM3 stack sits beside the GPU on an interposer, with 1024 data pins at 6.4 Gb/s, which makes 819 GB/s.",
            "a stack of thin silicon dies on a tan interposer next to the grey GPU die",
        )
        .detail(
            "One HBM3 stack is worth about thirteen GDDR6 chips in bandwidth.",
            &[
                "HBM3: 1024 pins x 6.4 Gb/s = 819 GB/s (section 4)",
                "HBM3: 819 GB/s per device (JEDEC JESD238)",
            ],
        ),
    Beat::new("short, dense wiring on the interposer makes the width possible", BEAT_MS)
        .note(
            "Only an interposer's short, fine wires can carry a thousand signals between two chips, so HBM trades pin speed for pin count.",
            "a dense comb of thin copper wires between the stack and the GPU, with green dots moving through it",
        )
        .detail(
            "Many slower pins over short wires, instead of a few fast pins over long board wires.",
            &[
                "HBM runs many slower pins over interposer wiring (section 4)",
                "HBM3 runs at 6.4 Gb/s per pin (section 2)",
            ],
        ),
    Beat::new("both at once: board wires for GDDR, interposer wires for HBM", BEAT_MS)
        .note(
            "GDDR runs few pins very fast over board wiring; HBM runs many slower pins over the short, dense wiring of an interposer. Both stream at once here.",
            "the GDDR chip and its long board lanes on the left, and the HBM stack with its comb on the right, both streaming",
        )
        .detail(
            "The two approaches trade pin speed against pin count and wiring length.",
            &[
                "GDDR runs few pins very fast over board wiring (section 4)",
                "HBM runs many slower pins over interposer wiring (section 4)",
            ],
        ),
];

pub const GAPS_BEATS: &[Beat] = &[
    Beat::new("reads stream steadily: every slot carries data, the peak case", BEAT_MS)
        .note(
            "A run of reads keeps the channel's data bus full. Peak assumes data in every bus slot, which is the case drawn here.",
            "a full row of green slots under a cyan peak lane, every slot carrying data",
        )
        .detail(
            "Block lengths in the picture are illustrative; the point is the share of slots that carry data.",
            &[
                "Peak assumes data in every bus slot (section 5)",
                "25.6 GB/s per DDR4-3200 channel (section 3)",
            ],
        ),
    Beat::new("a write, and back: the bus turns around and loses slots", BEAT_MS)
        .note(
            "Writes use the same wires the other way. Each switch between reads and writes leaves empty slots, and the bus is idle for a moment.",
            "pink turnaround slots frame an orange run of writes in the middle of the green reads",
        )
        .detail(
            "Real traffic loses slots to the bus turning around between reads and writes.",
            &[
                "Lost slots from turnarounds between reads and writes (section 5)",
                "Scheduling of reads and writes is on the BANK node",
            ],
        ),
    Beat::new("a refresh: a run of slots with no data at all", BEAT_MS)
        .note(
            "Refresh takes time away from data transfers, so the bus carries nothing for those slots. The cyan peak lane stays where it was.",
            "a block of grey empty slots between two green runs, under the unchanged cyan peak lane",
        )
        .detail(
            "Refresh is one of the reasons effective bandwidth sits below the peak.",
            &[
                "Refresh loses slots (section 5)",
                "Effective bandwidth is what the workload gets (section 5)",
            ],
        ),
    Beat::new("row misses and bank waits leave more holes: effective is what is left", BEAT_MS)
        .note(
            "Waits for rows to open or banks to free up leave more holes. Effective bandwidth is what is left of the green slots.",
            "pink holes scattered through the green run, and the filled green slots as the effective share",
        )
        .detail(
            "Two systems with the same peak can deliver very different effective bandwidth, depending on access patterns.",
            &[
                "Effective = peak minus slots lost to turnarounds, refresh and waits (section 5)",
                "Effective bandwidth depends on access patterns (section 9)",
            ],
        ),
];

pub const WALL_BEATS: &[Beat] = &[
    Beat::new("peak compute: about 3.0x every two years", BEAT_MS)
        .note(
            "Peak server compute has grown about 3.0x every two years over twenty years. The bars climb a step at a time on a log-style scale, so each step adds the same amount.",
            "eleven pink bars climbing step by step, each one tallest so far; the heights are illustrative and not to scale",
        )
        .detail(
            "Compute growth outruns memory growth, which is the root of the memory wall.",
            &[
                "Compute about 3.0x every two years (Gholami et al., arXiv 2403.14123)",
                "About 60,000x in twenty years (section 7)",
            ],
        ),
    Beat::new("DRAM bandwidth 1.6x, interconnect 1.4x: far more slowly", BEAT_MS)
        .note(
            "DRAM bandwidth grew about 1.6x every two years, and interconnect about 1.4x. Their cyan and purple bars climb far more slowly than the pink compute bars.",
            "cyan and purple bars rising beside each pink bar, much shorter at every step",
        )
        .detail(
            "Over twenty years DRAM bandwidth grew about 100x and interconnect about 30x.",
            &[
                "DRAM bandwidth about 1.6x every two years (Gholami et al.)",
                "About 100x and 30x in twenty years (section 7)",
            ],
        ),
    Beat::new("the gap is the wall: each unit of compute has less bandwidth behind it", BEAT_MS)
        .note(
            "Each unit of compute now has far less bandwidth behind it, so workloads that read a lot of data per operation wait on memory.",
            "a gold bracket over the widening gap between the tallest pink bar and the cyan bar beside it",
        )
        .detail(
            "The gap between compute and bandwidth is the memory wall.",
            &[
                "About 60,000x compute against 100x DRAM bandwidth (section 7)",
                "Gholami et al., AI and Memory Wall (arXiv 2403.14123)",
            ],
        ),
    Beat::new("large models wait on memory rather than arithmetic", BEAT_MS)
        .note(
            "Workloads that read a lot of data per operation, such as serving large models, are limited by memory. The processor waits on the data.",
            "a dark processor block at the bottom left, with a tag under the bars for the workloads that wait",
        )
        .detail(
            "Serving large models is the case the page names as limited by memory.",
            &[
                "Workloads that read much data per operation are limited by memory (section 7)",
                "Gholami et al., AI and Memory Wall (arXiv 2403.14123)",
            ],
        ),
];

static PIN: Cell = std::sync::OnceLock::new();
static SUBCH: Cell = std::sync::OnceLock::new();
static GDDR: Cell = std::sync::OnceLock::new();
static GAPS: Cell = std::sync::OnceLock::new();
static WALL: Cell = std::sync::OnceLock::new();

pub fn pin() -> Box<dyn Scene> {
    page(
        &PIN,
        include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_pin.glb"),
        PIN_BEATS,
    )
}

pub fn subch() -> Box<dyn Scene> {
    page(
        &SUBCH,
        include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_subch.glb"),
        SUBCH_BEATS,
    )
}

pub fn gddr() -> Box<dyn Scene> {
    page(
        &GDDR,
        include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_gddr.glb"),
        GDDR_BEATS,
    )
}

pub fn gaps() -> Box<dyn Scene> {
    page(
        &GAPS,
        include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_gaps.glb"),
        GAPS_BEATS,
    )
}

pub fn wall() -> Box<dyn Scene> {
    page(
        &WALL,
        include_bytes!("../../../../../tools/pbr3d/assets/bandwidth_wall.glb"),
        WALL_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("pin", pin as fn() -> Box<dyn Scene>),
            ("subch", subch),
            ("gddr", gddr),
            ("gaps", gaps),
            ("wall", wall),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
