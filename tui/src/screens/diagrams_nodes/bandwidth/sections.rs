// BANDWIDTH sections 1-10 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/bandwidth_sections.py. Beat counts: 4, 5, 5, 4, 3, 3, 3, 3, 4, 3. Section 10
// is the sources page.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("one pin: 3200 million transfers a second is where peak starts", BEAT_MS)
        .note(
            "Bandwidth is how many bytes memory can move each second. Its peak starts with the data rate per pin; a DDR4-3200 pin moves 3200 million transfers a second.",
            "one copper wire from the grey processor to a green DIMM, a few green dots on it",
        )
        .detail(
            "Real traffic gets less than the peak, so this is a ceiling rather than a measured speed.",
            &[
                "DDR4-3200: 3200 MT/s per pin (section 1)",
                "Real traffic gets less than the peak (section 1)",
            ],
        ),
    Beat::new("a channel is 64 pins wide: one channel peaks at 25.6 GB/s", BEAT_MS)
        .note(
            "A channel is 64 pins wide, so one channel peaks at 25.6 GB/s. The single wire becomes a ribbon of lanes into the DIMM.",
            "the wire turned into a ribbon of copper lanes into a green DIMM, with dots on the lanes",
        )
        .detail(
            "Width is the second factor: 64 data pins for a DDR channel.",
            &[
                "3200 MT/s x 64 pins / 8 = 25.6 GB/s per channel (section 1)",
                "64 data pins for a DDR channel (section 2)",
            ],
        ),
    Beat::new("four channels: 102.4 GB/s peak", BEAT_MS)
        .note(
            "Four channels run in parallel, each with its own DIMM, so their peaks add. Four channels give 102.4 GB/s peak.",
            "four ribbons from the processor to four DIMMs, with dots on every lane",
        )
        .detail(
            "Channel count is the third factor in the peak.",
            &[
                "4 x 25.6 = 102.4 GB/s peak (section 1)",
                "Each channel adds its own bandwidth (section 1)",
            ],
        ),
    Beat::new("real traffic runs below the peak", BEAT_MS)
        .note(
            "Peak assumes data in every bus slot. Real traffic loses slots to turnarounds, refresh and waits, so the workload gets less than the peak.",
            "pink markers on the lanes at the places where no data passes",
        )
        .detail(
            "Effective bandwidth is what the workload gets; the BANK node covers the scheduling.",
            &[
                "Effective bandwidth is what the workload gets (section 5)",
                "Refresh and bank conflicts are on the BANK node",
            ],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("data rate: transfers per second on one pin", BEAT_MS)
        .note(
            "The data rate is how many transfers one pin makes per second. DDR sends one on each clock edge, so DDR4-3200 makes 3200 million transfers a second.",
            "one copper pin with a green dot moving along it, and nothing else in the scene",
        )
        .detail(
            "It is the first factor in bandwidth. GDDR6 pushes it to 16 Gb/s per pin.",
            &[
                "DDR4-3200: 3200 MT/s from a 1600 MHz clock (data rate detail)",
                "GDDR6: up to 16 Gb/s per pin (Micron GDDR6 flyer)",
            ],
        ),
    Beat::new("data pins: the width of the bus", BEAT_MS)
        .note(
            "Data pins are the width of the bus: how many bits move side by side on each transfer. A DDR channel has 64, a GDDR6 chip 32, an HBM3 stack 1024.",
            "a ribbon of copper lanes, eight shown, running from the processor side across the scene",
        )
        .detail(
            "Width is the second factor, and it is HBM's main advantage: many slower pins instead of a few fast ones.",
            &[
                "64 for a DDR channel, 32 for a GDDR6 chip, 1024 for an HBM3 stack (section 2)",
                "JEDEC JESD238 (HBM3); Micron GDDR6 flyer (32 DQ)",
            ],
        ),
    Beat::new("DIMM: the chips that together fill one channel's width", BEAT_MS)
        .note(
            "A DIMM is the chips that together fill one channel's width. The DIMM sits at the end of the channel and takes its lanes.",
            "a green DIMM with black chips on its front, at the far end of the copper lanes",
        )
        .detail(
            "The chips share the channel, so one channel's width is the sum of the chips' pins.",
            &[
                "A DIMM is the chips that fill one channel's width (section 2)",
                "DDR5-4800 DIMM: two 32-bit subchannels (section 4)",
            ],
        ),
    Beat::new("memory controller: drives every channel", BEAT_MS)
        .note(
            "The memory controller sits in the processor and drives each channel. Its channel count caps the system's peak bandwidth.",
            "the grey processor with a gold memory controller block, lanes leaving its right side toward the DIMM",
        )
        .detail(
            "Its scheduling decides how close real traffic gets to the peak.",
            &[
                "The memory controller sits in the processor and drives each channel (section 2)",
                "Scheduling is covered on the BANK node",
            ],
        ),
    Beat::new("HBM stack: 1024 data pins, very close to the processor", BEAT_MS)
        .note(
            "An HBM stack is a pile of DRAM dies beside the processor on an interposer, with 1024 data pins. HBM3 runs them at 6.4 Gb/s.",
            "a stack of silicon dies on a tan interposer beside the processor, and a dense comb of short copper wires running to it",
        )
        .detail(
            "One HBM3 stack gives 819 GB/s, the bandwidth of about thirteen GDDR6 chips.",
            &[
                "HBM3 stack: 1024 pins x 6.4 Gb/s (section 2)",
                "819 GB/s per HBM3 stack (JEDEC JESD238)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("1. 3200 MT/s on one pin", BEAT_MS)
        .note(
            "Start with one pin: DDR4-3200 moves 3200 million transfers a second on it. The first line of the calculation is that rate.",
            "one copper pin with green dots moving along it, and a cyan bar at the centre of the scene for the calculation",
        )
        .detail(
            "MT/s is million transfers per second (textbook).",
            &["3200 MT/s on one pin (section 3)", "MT/s is million transfers per second (textbook)"],
        ),
    Beat::new("2. x 64 pins = 204,800 Mb/s", BEAT_MS)
        .note(
            "A channel is 64 pins wide. Multiplying the rate by the width gives 204,800 million bits a second, before the conversion to bytes.",
            "a ribbon of 64-pin copper lanes with the cyan bar beneath it",
        )
        .detail(
            "Width is the second factor; the result is in bits, not bytes.",
            &["3200 MT/s x 64 pins = 204,800 Mb/s (section 3)", "Computed in bits per second (section 3)"],
        ),
    Beat::new("3. / 8 bits per byte", BEAT_MS)
        .note(
            "Divide by 8 to turn bits into bytes. Eight bits make one byte, so the number comes out in GB/s rather than Gb/s.",
            "eight green cubes side by side forming one block, the unit of a byte",
        )
        .detail(
            "Eight bits make one byte.",
            &["8 bits per byte (section 3)", "The result is in GB/s after this step (section 3)"],
        ),
    Beat::new("4. = 25.6 GB/s per channel", BEAT_MS)
        .note(
            "One DDR4-3200 channel peaks at 25.6 GB/s. The cyan bar reads a quarter of the scale of the four-channel bar that follows.",
            "a cyan bar standing a quarter of the way up the scale, with the byte block beneath it",
        )
        .detail(
            "Per channel, not per chip.",
            &["25.6 GB/s per channel (section 3)", "3200 MT/s x 64 / 8 = 25.6 GB/s (section 3)"],
        ),
    Beat::new("5. x 4 channels = 102.4 GB/s", BEAT_MS)
        .note(
            "Four channels make 102.4 GB/s peak. The cyan bar grows to full height, and the four lane ribbons sit beneath it.",
            "the cyan bar at full height, with four copper ribbons beneath it",
        )
        .detail(
            "The channel count is the third factor.",
            &["4 x 25.6 = 102.4 GB/s peak (section 3)", "Channel count is the third factor (section 3)"],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("DDR5-4800 DIMM: 38.4 GB/s", BEAT_MS)
        .note(
            "Two subchannels of 32 bits, each pin at 4.8 Gb/s, give the DIMM's peak. The DIMM is split into a cyan half and an orange half.",
            "a green DIMM divided into two halves: cyan chips on the left, orange chips on the right",
        )
        .detail(
            "Main memory in PCs and servers uses DDR DIMMs like this.",
            &[
                "2 x 32 x 4.8 / 8 = 38.4 GB/s (section 4)",
                "DDR5-4800 DIMM: two 32-bit subchannels x 4.8 Gb/s (section 4)",
            ],
        ),
    Beat::new("GDDR6 chip: 32 pins x 16 Gb/s = 64 GB/s", BEAT_MS)
        .note(
            "Graphics boards use GDDR6 chips on the board beside the GPU. Each chip has 32 pins at 16 Gb/s, which gives 64 GB/s.",
            "a black GDDR6 chip on the green board with copper lanes to the grey GPU die",
        )
        .detail(
            "Graphics boards use many chips, each with its own 32 pins.",
            &[
                "GDDR6: 32 DQ, up to 16 Gb/s (Micron GDDR6 flyer)",
                "32 x 16 / 8 = 64 GB/s (section 4)",
            ],
        ),
    Beat::new("HBM3 stack: 1024 pins x 6.4 Gb/s = 819 GB/s", BEAT_MS)
        .note(
            "One HBM3 stack has 1024 pins at 6.4 Gb/s each, which is 819 GB/s. AI accelerators use several stacks like this.",
            "a stack of silicon dies on a tan interposer beside the grey processor, the stack's wires running into it",
        )
        .detail(
            "The stack is wide and slow per pin; the interposer makes the width possible.",
            &[
                "HBM3: 819 GB/s per device (JEDEC JESD238)",
                "1024 pins x 6.4 Gb/s / 8 = 819 GB/s (section 4)",
            ],
        ),
    Beat::new("board wires for GDDR, the interposer for HBM", BEAT_MS)
        .note(
            "GDDR runs few pins very fast over the board's wiring. HBM runs many slower pins over the short, dense wiring of an interposer. GDDR6X adds PAM4.",
            "a GDDR chip with its long board lanes at left, an HBM stack on its interposer at right",
        )
        .detail(
            "GDDR6X uses PAM4, four voltage levels, to carry two bits per symbol.",
            &[
                "GDDR runs few pins very fast over board wiring (section 4)",
                "GDDR6X PAM4: two bits per symbol (Micron GDDR6X PAM4 brief)",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("peak: every bus slot full", BEAT_MS)
        .note(
            "Peak assumes data in every bus slot. Real traffic starts with a run of reads, which fill the slots.",
            "a cyan peak lane above a full row of green data slots",
        )
        .detail(
            "Block lengths in the picture are illustrative.",
            &["Peak assumes data in every bus slot (section 5)", "Peak = rate x width (section 1)"],
        ),
    Beat::new("turnarounds: the bus turns around between reads and writes", BEAT_MS)
        .note(
            "The same wires carry reads one way and writes the other. Each switch leaves empty slots while the bus turns around.",
            "pink turnaround slots framing an orange run of writes among the green reads",
        )
        .detail(
            "The bus is idle at each switch, which costs part of the peak.",
            &[
                "Real traffic loses slots to the bus turning around (section 5)",
                "Scheduling reads and writes is on the BANK node",
            ],
        ),
    Beat::new("refresh and row misses: effective is what is left", BEAT_MS)
        .note(
            "Refresh, and waits for rows to open or banks to free up, leave more holes. Effective bandwidth is the share of slots that still carry data.",
            "a grey run of empty slots for refresh, and pink holes for row misses, with the green slots left as the effective share",
        )
        .detail(
            "Effective bandwidth is what a workload actually gets.",
            &[
                "Refresh and waits for rows and banks lose slots (section 5)",
                "Effective bandwidth is what a workload gets (section 5)",
            ],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("rate per pin: GDDR6 is the fastest, HBM3 slower per pin", BEAT_MS)
        .note(
            "DDR4-3200 runs at 3.2 Gb/s per pin, DDR5-4800 at 4.8, GDDR6 at 16 and HBM3 at 6.4. GDDR6's pins are the fastest, HBM's the slowest of the four.",
            "four bars, the GDDR6 bar the tallest and the DDR4 bar the shortest",
        )
        .detail(
            "HBM's pins are slower than GDDR's; HBM makes up for it with width.",
            &["Gb/s per pin: 3.2, 4.8, 16, 6.4 (section 6)", "GDDR6 up to 16 Gb/s (Micron GDDR6 flyer)"],
        ),
    Beat::new("data pins: HBM's stack has far more", BEAT_MS)
        .note(
            "64 pins for a DDR channel or a DDR5 DIMM, 32 for a GDDR6 chip, 1024 for an HBM3 stack. The HBM bar towers over the rest.",
            "four bars, the HBM3 bar towering over the others",
        )
        .detail(
            "Width is HBM's advantage.",
            &["64, 2 x 32, 32, 1024 data pins (section 6)", "Width is HBM's main advantage (section 2)"],
        ),
    Beat::new("GB/s per device: 25.6, 38.4, 64 and 819", BEAT_MS)
        .note(
            "The four devices give 25.6 GB/s per channel, 38.4 per DDR5 DIMM, 64 per GDDR6 chip and 819 per HBM3 stack. Each is rate times pins, divided by 8.",
            "four bars at the same scale, the HBM3 bar full height and the DDR4 bar small",
        )
        .detail(
            "The bandwidth per device is the rate per pin times the pins, divided by 8.",
            &[
                "25.6 (channel), 38.4 (DIMM), 64 (chip), 819 (stack) GB/s (section 6)",
                "GB/s = Gb/s x pins / 8 (section 6)",
            ],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("compute: about 3.0x every two years", BEAT_MS)
        .note(
            "Peak server compute grew about 3.0x every two years over the last twenty years. The bars climb a step at a time, in a log-style picture.",
            "pink bars climbing across eleven two-year steps, each step taller than the last; heights illustrative",
        )
        .detail(
            "Compute growth is the fast curve in the memory wall.",
            &["Compute about 3.0x every two years (Gholami et al., arXiv 2403.14123)", "About 60,000x in twenty years (section 7)"],
        ),
    Beat::new("DRAM bandwidth about 1.6x and interconnect 1.4x", BEAT_MS)
        .note(
            "DRAM bandwidth grew about 1.6x every two years, and interconnect about 1.4x. Their cyan and purple bars climb far more slowly.",
            "cyan and purple bars beside each pink bar, much shorter at every step",
        )
        .detail(
            "Over twenty years DRAM bandwidth grew about 100x and interconnect about 30x.",
            &["DRAM 1.6x, interconnect 1.4x every two years (Gholami et al.)", "About 100x and 30x in twenty years (section 7)"],
        ),
    Beat::new("the gap is the wall", BEAT_MS)
        .note(
            "Each unit of compute now has far less bandwidth behind it, so many workloads wait on memory rather than on arithmetic.",
            "a gold bracket over the tallest pink bar, the cyan bar far below it",
        )
        .detail(
            "Bandwidth, not arithmetic, often sets the speed of large models.",
            &["About 60,000x against 100x (section 7)", "Gholami et al., AI and Memory Wall (arXiv 2403.14123)"],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new("Micron (MU)", BEAT_MS)
        .note(
            "Micron makes DRAM, GDDR and HBM. It is the first of the three makers on this page.",
            "the first card lit in gold: Micron (MU), the card on the left",
        )
        .detail(
            "Market share is covered on the market pages.",
            &[
                "DRAM, GDDR and HBM are made by Micron (MU) (section 8)",
                "Market share is on the market pages (section 8)",
            ],
        ),
    Beat::new("SK hynix (000660.KS)", BEAT_MS)
        .note(
            "SK hynix makes DRAM, GDDR and HBM as well. Its card is lit second, beside Micron's.",
            "the first two cards lit, Micron and then SK hynix (000660.KS) in the middle",
        )
        .detail(
            "The ticker is the Korean listing.",
            &[
                "SK hynix (000660.KS) (section 8)",
                "Market share is on the market pages (section 8)",
            ],
        ),
    Beat::new("Samsung (005930.KS)", BEAT_MS)
        .note(
            "Samsung makes DRAM, GDDR and HBM. All three makers are now lit.",
            "all three cards lit, with Samsung (005930.KS) on the right",
        )
        .detail(
            "Three makers make the DRAM, GDDR and HBM on this page.",
            &[
                "Samsung (005930.KS) (section 8)",
                "DRAM makers: Micron, SK hynix, Samsung (section 8)",
            ],
        ),
];

const SEC9: &[Beat] = &[
    Beat::new("the memory wall: compute keeps outgrowing bandwidth", BEAT_MS)
        .note(
            "Compute keeps outgrowing bandwidth, so more hardware sits waiting on memory. The processor on the right is fed through one thin pipe.",
            "a dark processor on the right, fed by a single thin copper pipe from memory on the left",
        )
        .detail(
            "Every generation needs a bigger bandwidth jump.",
            &["Compute 3.0x against DRAM 1.6x every two years (section 9)", "Gholami et al., AI and Memory Wall (arXiv 2403.14123)"],
        ),
    Beat::new("pins cost package area, board routing and power", BEAT_MS)
        .note(
            "Every extra pin needs package area, board routing and power to drive it. Faster pins cost more energy per bit.",
            "a grid of gold pins on the underside of a package, a long row of them",
        )
        .detail(
            "Width and rate both have limits.",
            &["Pins cost package area, board routing and power (section 9)", "Faster pins cost more energy per bit (section 9)"],
        ),
    Beat::new("HBM's width needs interposer packaging", BEAT_MS)
        .note(
            "HBM's width depends on an interposer beside the processor, which needs specialised packaging capacity. The stack sits on the same tan interposer as the processor.",
            "the grey processor and an HBM stack on a shared tan interposer, with the processor's gold controller block",
        )
        .detail(
            "See the HBM STACK node for how the stack is built.",
            &["HBM's width depends on interposer packaging (section 9)", "See the HBM STACK node (section 9)"],
        ),
    Beat::new("effective bandwidth depends on access patterns, not only the parts", BEAT_MS)
        .note(
            "Effective bandwidth depends on access patterns, not only on the parts. The same bus can carry a full run of data or one with holes, depending on how it is used.",
            "a row of green data slots with pink holes, the same parts giving a different pattern",
        )
        .detail(
            "Two systems with the same peak can deliver very different effective bandwidth.",
            &["Effective bandwidth depends on access patterns (section 9)", "Effective bandwidth is what the workload gets (section 5)"],
        ),
];

const SEC10: &[Beat] = &[
    Beat::new("sources: JEDEC and the Micron GDDR6 flyer", BEAT_MS)
        .note(
            "The HBM3 and GDDR6 figures come from the JEDEC HBM3 update and the Micron GDDR6 product flyer. Both cards are lit.",
            "source cards 1 and 2 lit in gold, the others dark",
        )
        .detail(
            "JEDEC JESD238: 6.4 Gb/s and 819 GB/s per device. Micron GDDR6: 32 DQ per component, up to 16 Gb/s.",
            &["[1] JEDEC, HBM3 update to the HBM standard (JESD238)", "[2] Micron, GDDR6 product flyer"],
        ),
    Beat::new("sources: Micron on GDDR6X and DDR5", BEAT_MS)
        .note(
            "The GDDR6X figure for PAM4 comes from Micron's technical brief, and the DDR5 module figures from Micron's DDR5 modules page.",
            "source cards 3 and 4 lit in gold",
        )
        .detail(
            "Micron GDDR6X: two bits per symbol. Micron DDR5 modules: two 40-bit independent channels per DIMM, BL16.",
            &["[3] Micron, GDDR6X PAM4 technical brief", "[4] Micron, DDR5 modules"],
        ),
    Beat::new("sources: Gholami et al. and the arithmetic", BEAT_MS)
        .note(
            "The memory-wall growth rates come from Gholami et al. The DDR4-3200 and DDR5-4800 peaks are arithmetic on the rate, pins and 8 bits per byte, with the BANK and HBM STACK nodes as cross-references.",
            "source cards 5 and 6 lit in gold",
        )
        .detail(
            "Gholami et al., AI and Memory Wall (arXiv 2403.14123, IEEE Micro).",
            &["[5] Gholami et al., AI and Memory Wall (arXiv 2403.14123)", "[6] Peaks are MT/s x data pins / 8; BANK and HBM STACK nodes"],
        ),
];

static CELLS: [Cell; 10] = [const { std::sync::OnceLock::new() }; 10];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/bandwidth_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
    section!(10, SEC10),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [4, 5, 5, 4, 3, 3, 3, 3, 4, 3]);
        for (i, f) in SECTIONS.iter().enumerate() {
            let s = f();
            super::super::super::blender::explained(s.as_ref(), &format!("section {}", i + 1));
            super::super::super::blender::draws_every_beat(
                s.as_ref(),
                &format!("section {}", i + 1),
            );
        }
    }
}
