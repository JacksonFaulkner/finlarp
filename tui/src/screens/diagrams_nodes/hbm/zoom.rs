// HBM STACK zoom-ins a-f in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/hbm_zooms.py: a a copper TSV cut open, b the base logic die, c the channels
// of one stack, d microbumps against hybrid bonding, e CoWoS packaging, f inside one DRAM die. Four beats each.

use super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene};

const TSV_BEATS: &[Beat] = &[
    Beat::new("copper columns run through the silicon", BEAT_MS)
        .note(
            "A cut through three dies over the base die: each die has copper TSVs running straight through it, joined to the next by microbumps.",
            "Orange dies with copper columns through them, yellow microbumps in the gaps, all on a blue base die.",
        )
        .detail(
            "Thousands of such columns make one stack act as one memory.",
            &["TSV: through-silicon via; microbumps join TSVs die to die (page section 2)"],
        ),
    Beat::new("a signal runs down the column", BEAT_MS)
        .note(
            "Data passes down a TSV, across a microbump, into the next TSV, and so on down to the base die.",
            "Cyan dots run down all three columns, through each bump and into the base die.",
        )
        .detail(
            "Each column is short, so a signal only crosses a thin die at a time.",
            &["Dies thinned to 30-50 um (SemiEngineering)"],
        ),
    Beat::new("thinner dies for taller stacks", BEAT_MS)
        .note(
            "Dies are ground thin, to 30-50 um, so more of them fit under the height limit and the TSVs stay short.",
            "The three dies thin down in the middle of the beat, then return to full thickness.",
        )
        .detail(
            "Thinning is what lets a stack hold more dies under the height limit.",
            &["Dies 30-50 um (SemiEngineering)", "Height limit 720 -> 775 um (press reports)"],
        ),
    Beat::new("the bumps shrink as the pitch falls", BEAT_MS)
        .note(
            "Microbumps are getting finer: their pitch is about 40 um and heading towards 10 um.",
            "The yellow bumps shrink in height between the dies.",
        )
        .detail(
            "The page gives the direction of the pitch, not a finished value.",
            &["Microbump pitch about 40 um, toward 10 um (SemiEngineering)"],
        ),
];

const BASE_BEATS: &[Beat] = &[
    Beat::new("the base logic die under the stack", BEAT_MS)
        .note(
            "Under the DRAM dies sits a logic die: the TSVs land on it, and small copper landing pads sit on its top face.",
            "The DRAM dies lift away, leaving the blue base die with its copper landing pads in a row.",
        )
        .detail(
            "The base die holds no memory arrays of its own; it is the interface and test logic.",
            &["Base die: interface (PHY) plus test logic (page section 2)"],
        ),
    Beat::new("the PHY drives the bus to the GPU", BEAT_MS)
        .note(
            "Along the edge facing the GPU, the PHY drives the wide bus across the interposer.",
            "A cyan dot leaves the PHY edge on the right of the base die and travels toward the purple GPU.",
        )
        .detail(
            "The PHY is the circuit that sends and receives the signals, so its width sets the bus width.",
            &["PHY: 1024 bits (HBM3), 2048 bits (HBM4)"],
        ),
    Beat::new("HBM4: foundry logic die (reported)", BEAT_MS)
        .note(
            "For HBM4 the base die is reportedly made at foundries such as TSMC on a logic process, not the DRAM process.",
            "A note appears over the base die; the block itself is the same blue slab.",
        )
        .detail(
            "Logic processes allow faster, denser interface circuits. This is reported, not confirmed on the page.",
            &["HBM4 base die on foundry logic (reported)"],
        ),
    Beat::new("test logic checks the stack", BEAT_MS)
        .note(
            "The base die carries test logic, and the finished stack is tested by reading through its TSVs.",
            "A yellow test field lights up on the top of the base die.",
        )
        .detail(
            "One bad die or joint spoils the stack, so test has to catch it.",
            &["Stack yield: one bad die or joint spoils the stack (page section 9)"],
        ),
];

const CHANNELS_BEATS: &[Beat] = &[
    Beat::new("1024 bits from one HBM3 stack", BEAT_MS)
        .note(
            "An HBM3 stack's interface is 1024 data bits wide: one wide bus between the stack and the GPU.",
            "One wide cyan bus runs from the stack's PHY edge to the purple GPU.",
        )
        .detail(
            "Far wider than a DIMM, which is why the stack sits right beside the GPU.",
            &["HBM3: 1024 data pins (page section 4)"],
        ),
    Beat::new("split into 16 channels", BEAT_MS)
        .note(
            "Those bits form 16 independent channels, each with its own commands, so many requests run at once.",
            "The bus splits into sixteen parallel lines, all running to the GPU.",
        )
        .detail(
            "The HBM3 channel count went from 8 to 16 in the JEDEC update.",
            &["HBM3: 16 channels (PC Watch report on JESD238)"],
        ),
    Beat::new("HBM4: 32 channels, 2048 bits", BEAT_MS)
        .note(
            "HBM4 doubles again: 2048 bits in 32 channels, each split into two pseudo-channels.",
            "The lines double; the bundle is twice as dense as before.",
        )
        .detail(
            "Doubling the bits and channels is how the bandwidth per stack rises.",
            &["HBM4: 2048 bits, 32 channels (JEDEC JESD270-4)"],
        ),
    Beat::new("each channel runs on its own", BEAT_MS)
        .note(
            "Each channel has its own commands and runs on its own rhythm, so requests overlap across the bus.",
            "Pale dots move along the lanes at different times, none waiting on the others.",
        )
        .detail(
            "Independent channels are why many requests can run at once.",
            &["HBM3: 16 channels; HBM4: 32 channels (JEDEC)"],
        ),
];

const BOND_BEATS: &[Beat] = &[
    Beat::new("microbumps: a gap at every joint", BEAT_MS)
        .note(
            "Two 16-high stacks. On the left each die sits on microbumps, which leave a gap at every joint.",
            "The left stack has yellow bumps between every pair of dies; the right stack is the same before bonding.",
        )
        .detail(
            "Each joint adds height and must work for the stack to work.",
            &["Microbump pitch about 40 um, toward 10 um (SemiEngineering)"],
        ),
    Beat::new("hybrid bonding: copper to copper", BEAT_MS)
        .note(
            "Hybrid bonding joins copper pads directly with no bump, so the same dies make a shorter stack.",
            "The right stack's bumps vanish and its dies come down onto each other; the stack shortens.",
        )
        .detail(
            "It is harder to make with good yield, so HBM4 postponed it.",
            &["Hybrid bonding postponed for HBM4 (SemiEngineering)"],
        ),
    Beat::new("the height limit rose, so HBM4 kept microbumps", BEAT_MS)
        .note(
            "Raising the stack height limit from 720 to 775 um let 16-high HBM4 keep microbumps for now.",
            "The pink plane at the old limit cuts below the top of the 16-high stack; then it rises to the new limit.",
        )
        .detail(
            "Every extra die must fit under the limit, which is why dies are thinned.",
            &["720 -> 775 um (press reports)"],
        ),
    Beat::new("16-high under the raised limit", BEAT_MS)
        .note(
            "Hybrid bonding is expected beyond 16-high stacks; HBM4 stays with microbumps.",
            "Left: a 16-high stack with microbumps under the raised plane. Right: the shorter hybrid stack.",
        )
        .detail(
            "Hybrid bonding removes the bump height, which is why it is expected beyond 16-high.",
            &["Hybrid bonding expected beyond 16-high (SemiEngineering)"],
        ),
];

const COWOS_BEATS: &[Beat] = &[
    Beat::new("one interposer for the GPU and four stacks", BEAT_MS)
        .note(
            "In CoWoS the GPU and its HBM stacks share one silicon interposer, which sits on a package substrate.",
            "A purple GPU with four stacks on a grey interposer over a green substrate, seen from above.",
        )
        .detail(
            "Chip-on-Wafer-on-Substrate, TSMC's packaging.",
            &["CoWoS (TSMC; Tom's Hardware, TrendForce)"],
        ),
    Beat::new("eight stacks need a bigger interposer", BEAT_MS)
        .note(
            "More stacks for more bandwidth and capacity make the interposer larger.",
            "Four more stacks appear and the interposer widens to take them.",
        )
        .detail(
            "More stacks per package need a larger interposer.",
            &["More HBM per package needs a larger interposer (page section 7)"],
        ),
    Beat::new("bigger interposers: fewer per wafer", BEAT_MS)
        .note(
            "Interposers are cut from silicon wafers, so larger ones mean fewer fit on each wafer.",
            "A wafer of many small interposers, then fewer large ones; the count drops as they grow.",
        )
        .detail(
            "Fewer interposers fit each wafer as they grow.",
            &["Larger interposers lower packages per wafer (Tom's Hardware)"],
        ),
    Beat::new("the package sits on a substrate", BEAT_MS)
        .note(
            "The interposer sits on a package substrate that connects to the board.",
            "The whole package from the side: the stacks and GPU on the interposer, the substrate beneath.",
        )
        .detail(
            "Almost every high-end AI accelerator uses CoWoS, and its capacity has limited how many ship.",
            &["CoWoS capacity constraint (Tom's Hardware, TrendForce)"],
        ),
];

const DIE_BEATS: &[Beat] = &[
    Beat::new("one core die out of the stack", BEAT_MS)
        .note(
            "An 8-high stack of DRAM dies on its base die; one core die slides out to be looked at on its own.",
            "The orange stack with copper TSVs and yellow microbumps; the middle die slides out to the right.",
        )
        .detail(
            "Every DRAM die in the stack is a full memory chip of its own, thinned so the stack stays short.",
            &["Dies thinned to 30-50 um (SemiEngineering)", "Each die has its own banks and arrays (page section 2)"],
        ),
    Beat::new("a TSV field down the middle", BEAT_MS)
        .note(
            "Seen from above, the die has a strip of TSVs: the copper wires that carry data, commands and power down through it to the dies below.",
            "The die lies flat; a grey strip of copper TSV ends runs down its middle, and cyan signals light the TSVs row by row.",
        )
        .detail(
            "The floor plan here is schematic: makers place the TSVs differently, but every die needs a field of them.",
            &["TSVs: copper wires straight through each thinned die (page section 2)"],
        ),
    Beat::new("banks either side, grouped into channels", BEAT_MS)
        .note(
            "The rest of the die is banks. Each bank is a full array with its own row buffer, and groups of banks belong to the channels the stack exposes.",
            "Sixteen bank blocks appear either side of the strip, in four colours: each colour is one channel's banks.",
        )
        .detail(
            "Channels work independently, which is how one stack keeps a very wide bus busy.",
            &["Bank: a full array with its own row buffer (BANK node)", "HBM3 16 channels, HBM4 32 per stack (JEDEC)"],
        ),
    Beat::new("inside one bank: mats and cells", BEAT_MS)
        .note(
            "One bank opened up: it is tiled into mats, with sense-amp stripes between mat rows and word-line drivers between mat columns. Each mat is a grid of 1T1C cells.",
            "The bank splits into a 4 x 4 grid of mats with cyan sense-amp stripes and grey driver stripes; metal capacitors stand up on one mat.",
        )
        .detail(
            "Short bit lines keep the signal strong, so the array is cut into small mats with their own sense amps.",
            &["Mat: about 512 x 512 cells (ARRAY node)", "Cell: 1 transistor + 1 capacitor (CELL node)"],
        ),
];

fn tsv_glb() -> &'static [u8] {
    include_bytes!("../../../../../tools/pbr3d/assets/hbm_tsv.glb")
}

static TSV: Cell = std::sync::OnceLock::new();
static BASE: Cell = std::sync::OnceLock::new();
static CHANNELS: Cell = std::sync::OnceLock::new();
static BOND: Cell = std::sync::OnceLock::new();
static COWOS: Cell = std::sync::OnceLock::new();
static DIE: Cell = std::sync::OnceLock::new();

pub fn tsv() -> Box<dyn Scene> {
    page(&TSV, tsv_glb(), TSV_BEATS)
}

pub fn base() -> Box<dyn Scene> {
    page(
        &BASE,
        include_bytes!("../../../../../tools/pbr3d/assets/hbm_base.glb"),
        BASE_BEATS,
    )
}

pub fn channels() -> Box<dyn Scene> {
    page(
        &CHANNELS,
        include_bytes!("../../../../../tools/pbr3d/assets/hbm_channels.glb"),
        CHANNELS_BEATS,
    )
}

pub fn bond() -> Box<dyn Scene> {
    page(
        &BOND,
        include_bytes!("../../../../../tools/pbr3d/assets/hbm_bond.glb"),
        BOND_BEATS,
    )
}

pub fn cowos() -> Box<dyn Scene> {
    page(
        &COWOS,
        include_bytes!("../../../../../tools/pbr3d/assets/hbm_cowos.glb"),
        COWOS_BEATS,
    )
}

pub fn die() -> Box<dyn Scene> {
    page(
        &DIE,
        include_bytes!("../../../../../tools/pbr3d/assets/hbm_die.glb"),
        DIE_BEATS,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zooms_have_four_explained_beats_and_draw() {
        for (name, build) in [
            ("tsv", tsv as fn() -> Box<dyn Scene>),
            ("base", base),
            ("channels", channels),
            ("bond", bond),
            ("cowos", cowos),
            ("die", die),
        ] {
            let s = build();
            assert_eq!(s.beats().len(), 4, "{name}");
            super::super::super::blender::explained(s.as_ref(), name);
            super::super::super::blender::draws_every_beat(s.as_ref(), name);
        }
    }
}
