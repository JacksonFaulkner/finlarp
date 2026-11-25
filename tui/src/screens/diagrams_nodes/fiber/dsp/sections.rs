// FIBER tab, PAM4 DSP: the numbered sections 1-9. Each is one close-up picture of one idea (Blender scene
// tools/pbr3d/blender/fiber_dsp_sections.py, GLBs in tools/pbr3d/assets/fiber_dsp_section_<n>.glb), three 8 s beats each.

use super::super::super::blender::{Cell, page};
use crate::ui::anim::{Beat, Scene};

const BEAT_MS: u64 = 8000;

static CELL_1: Cell = std::sync::OnceLock::new();
static CELL_2: Cell = std::sync::OnceLock::new();
static CELL_3: Cell = std::sync::OnceLock::new();
static CELL_4: Cell = std::sync::OnceLock::new();
static CELL_5: Cell = std::sync::OnceLock::new();
static CELL_6: Cell = std::sync::OnceLock::new();
static CELL_7: Cell = std::sync::OnceLock::new();
static CELL_8: Cell = std::sync::OnceLock::new();
static CELL_9: Cell = std::sync::OnceLock::new();

/// 1 What happens: a module cut open; blurred lanes in, the DSP cleans them, clean symbols to the laser and back.
const S1_B: &[Beat] = &[
    Beat::new("the module and its DSP", BEAT_MS)
        .note(
            "This is an optical module with its shell cut away. The host chip (a GPU or switch) sends data in over copper, eight SerDes lanes side by side, through the gold edge connector. Each lane is a PAM4 signal, four voltage levels and two bits per symbol, and by the time it gets here it is blurred and noisy.",
            "The grey finned shell along the back, the green module board, gold fingers at the left end, eight copper lanes running to the finned DSP package. Orange dots ride the lanes. On the right sit the laser, the photodiode and their fibres.",
        )
        .detail(
            "Every bit in and out of the module passes through the DSP.",
            &["8 SerDes lanes from the host", "PAM4: 4 levels, 2 bits per symbol", "100G lane: 53.125 GBd"],
        ),
    Beat::new("the DSP cleans every bit", BEAT_MS)
        .note(
            "Inside the package the DSP samples each lane, applies equalization to undo the blur, and checks the data with FEC. Out of it come clean, evenly spaced symbols again.",
            "The package cut open: the die's metal stack glows cyan on both cut faces. Orange dots still arrive on the left; cyan dots leave down a bump, a via and a ball on the cut face.",
        )
        .detail(
            "Sampling, equalization and FEC are the three jobs of the DSP.",
            &["Sample, equalize, check FEC", "A retimer: it resends the data clean", "Same work for every lane"],
        ),
    Beat::new("clean symbols out, both ways", BEAT_MS)
        .note(
            "The clean symbols run to the laser driver, and the laser puts them on the fibre as light. The receive side works the same in reverse: the weak, noisy signal from the photodiode comes back into the DSP to be cleaned before it goes to the host.",
            "Cyan dots run along the board to the black driver chip and the laser's can; orange pulses of light slide down the fibre. On the photodiode's trace behind, orange dots head back into the package.",
        )
        .detail(
            "One chip cleans both directions.",
            &["Transmit: to the laser driver", "Receive: from the photodiode", "Both pass through the DSP"],
        ),
];

/// 2 The parts: the die's floor plan; SerDes and baud rate, the PAM4 and FEC encoders, the equaliser and the retimer's clock.
const S2_B: &[Beat] = &[
    Beat::new("SerDes lanes and the baud rate", BEAT_MS)
        .note(
            "Here the die is shown face up, out of its package. Down both edges are its SerDes, the fast electrical lanes between chips: eight toward the host and eight toward the optics. Each lane runs at a fixed baud rate, the number of symbols per second.",
            "The gold tiles down both edges light orange (host side) and blue (line side), with cyan dots streaming off them. The grey tray holds the die; the copper ring round its edge is the seal ring.",
        )
        .detail(
            "Baud rate times bits per symbol is the lane's speed.",
            &["SerDes: the fast chip-to-chip lanes", "100G lane: 53.125 GBd", "200G lane: 106.25 GBd"],
        ),
    Beat::new("PAM4 and FEC on the way out", BEAT_MS)
        .note(
            "The transmit blocks get the data ready for the line. The FEC encoder adds extra bits that let the far end fix errors, and the PAM4 encoder turns every two bits into one of four levels. A DAC then drives those levels out toward the laser driver.",
            "The back row of blocks glows orange: FEC encoder, PAM4 encoder, DAC. Cyan dots run across them from the host side to the line side.",
        )
        .detail(
            "PAM4 doubles the bits per symbol; FEC buys back the margin it costs.",
            &["PAM4: 4 levels, 2 bits per symbol", "FEC: extra bits to fix errors", "DAC: out to the laser driver"],
        ),
    Beat::new("equalization, and the retimer", BEAT_MS)
        .note(
            "The receive blocks clean up what comes in. Equalization filters undo the blur that copper and optics add to each symbol, and the FEC decoder fixes what is left. The clock block in the middle recovers the clock and resends the data clean, which makes the DSP a retimer. Linear pluggable optics (LPO) leave all of this out.",
            "The front row glows blue: the equaliser, the FEC decoder, the ADC by the line lanes. The small gold clock in the centre lights up. Orange dots run from the line side back to the host side.",
        )
        .detail(
            "This processing is where most of the module's power goes.",
            &["Equalization: undoes the blur", "Retimer: recovers the clock, resends clean", "Power per bit: picojoules per bit"],
        ),
];

/// 3 One symbol's trip, in order: steps 1-6 along the cut faces.
const S3_B: &[Beat] = &[
    Beat::new("1-2: sent, then smeared", BEAT_MS)
        .note(
            "Step 1: the host's SerDes puts a PAM4 symbol on a copper trace, which reaches the module through the edge connector. Step 2: the trace and the connector smear it into its neighbours, so it arrives at the DSP package blurred.",
            "A pair of copper traces on the green board, the near one glowing orange, with orange dots running along it toward the cut-open DSP package.",
        )
        .detail(
            "The smear is what the DSP is there to undo.",
            &["1: host SerDes sends", "2: trace + connector smear it", "PAM4 at 53.125 GBd (100G lane)"],
        ),
    Beat::new("3-4: equalized, FEC checked", BEAT_MS)
        .note(
            "The symbol climbs through the package into the die. Step 3: the DSP samples the signal and equalization separates the levels again. Step 4: the DSP checks the FEC and re-encodes it for the optical side.",
            "On the cut face, a via and a substrate layer light cyan, dots climb into a C4 bump, and the die's purple metal stack glows cyan along both cut faces.",
        )
        .detail(
            "From here on the symbol is clean again.",
            &["3: sample + equalize", "4: check + re-encode FEC", "Path: ball, via, bump, die"],
        ),
    Beat::new("5-6: to the laser, then the far end", BEAT_MS)
        .note(
            "Step 5: the clean symbol leaves the die and the laser driver turns it into a current for the laser. Step 6: at the far end of the fibre, the photodiode's signal goes through a DSP that does the same in reverse.",
            "Cyan dots leave the package down the other cut face and run along the board to the black driver chip and the laser; the laser chip lights and orange light pulses slide down the fibre.",
        )
        .detail(
            "Every link has a DSP at each end.",
            &["5: driver turns it into laser current", "6: the far end reverses it", "Light from here to the far end"],
        ),
];

/// 4 NRZ vs PAM4: two levels and one bit; four levels and two bits at the same baud rate; a third of the gap.
const S4_B: &[Beat] = &[
    Beat::new("NRZ: 2 levels, 1 bit a symbol", BEAT_MS)
        .note(
            "On an oscilloscope, NRZ sends one bit per symbol with two levels: low for 0, high for 1. Each step of the trace is one symbol.",
            "A scope with a gridded screen and two silver rungs. An orange trace steps between them symbol by symbol, a gold dot riding along it.",
        )
        .detail(
            "The older, simpler way to send bits.",
            &["NRZ: 2 levels", "1 bit per symbol", "The gap: the full swing"],
        ),
    Beat::new("PAM4: 4 levels, 2 bits a symbol", BEAT_MS)
        .note(
            "PAM4 sends two bits per symbol with four levels, which doubles the data at the same baud rate: the symbols are just as wide. A 100G lane runs PAM4 at 53.125 GBd and a 200G lane at 106.25 GBd.",
            "Four silver rungs now. A cyan trace steps between all four with the same step width as before, the gold dot riding along it.",
        )
        .detail(
            "Twice the bits without a faster symbol rate.",
            &["PAM4: 4 levels, 2 bits per symbol", "100G lane: 53.125 GBd", "200G lane: 106.25 GBd"],
        ),
    Beat::new("the cost: a third of the gap", BEAT_MS)
        .note(
            "The four levels fit in the same voltage swing, so the gap between neighbouring levels is a third of NRZ's. Noise matters more: the cost is about 9.5 dB of signal-to-noise.",
            "At the right, an orange bar spans NRZ's full gap; beside it, three short gold bars each span one PAM4 gap, a third of the height.",
        )
        .detail(
            "That lost margin is why PAM4 needs equalization and FEC.",
            &["PAM4 gap: 1/3 of NRZ's", "Cost: ~9.5 dB of SNR", "Same swing, more levels"],
        ),
];

/// 5 Equalization and the eye: a closed eye, the equaliser's taps, the eye open.
const S5_B: &[Beat] = &[
    Beat::new("many symbols make eyes", BEAT_MS)
        .note(
            "Overlay many symbols on top of each other and the levels form eyes: the open gaps where the receiver decides which level it saw. Copper and lasers blur symbols into each other and close the eyes.",
            "On the scope, dozens of orange traces overlaid, each crossing between levels; the levels have smeared into thick bands and the gaps between them have nearly closed. A gold dot probes the middle.",
        )
        .detail(
            "A closed eye means the receiver guesses wrong too often.",
            &["Eyes: gaps between the levels", "Copper and lasers close them", "PAM4: 3 eyes stacked"],
        ),
    Beat::new("the equaliser reshapes it", BEAT_MS)
        .note(
            "Equalization filters reshape the signal. In the DSP they are digital filters with many taps: each tap weighs a neighbouring symbol, and together they take back what leaked between symbols. Midway through, the eye opens.",
            "A panel at the right shows the taps as glowing bars growing about a centre line: one tall main tap, small ones beside it. The orange traces give way to thin cyan ones with clear gaps.",
        )
        .detail(
            "The taps undo the blur instead of trying to avoid it.",
            &["Digital filters with many taps", "Each tap weighs a neighbour", "The eye opens again"],
        ),
    Beat::new("3 open eyes: decide here", BEAT_MS)
        .note(
            "With the eyes open, the receiver samples each symbol at the centre of the eye and compares it with the gaps to decide its level. The wider the eyes, the fewer wrong decisions.",
            "Thin cyan traces with three gold diamonds marking the open eyes; a gold dot steps up through them at the sampling point.",
        )
        .detail(
            "Open eyes, then FEC fixes the rest.",
            &["3 eyes for 4 levels", "Sample at the eye's centre", "Errors left go to FEC"],
        ),
];

/// 6 FEC: a codeword with check symbols; errors land; the decoder fixes them.
const S6_B: &[Beat] = &[
    Beat::new("a codeword: data + check symbols", BEAT_MS)
        .note(
            "Even an open eye has errors, so FEC adds redundant symbols the receiver can use to correct them. Ethernet at 100G per lane uses a Reed-Solomon code, RS(544,514) or 'KP4': every 514 data symbols get 30 check symbols, 544 in all.",
            "On a test screen a codeword fills in cell by cell: blue-grey data cells, then two gold check cells at the end (drawn as 32 cells, not 544).",
        )
        .detail(
            "About 5% of the bits are there only to fix errors.",
            &["RS(544,514), 'KP4'", "514 data + 30 check symbols", "~5% overhead"],
        ),
    Beat::new("the link flips a few", BEAT_MS)
        .note(
            "Crossing the link, a few symbols come out wrong. Before FEC the raw error rate is about 2 in 10,000, far too many for a network to use as is.",
            "An orange bar sweeps across the codeword like noise on the link; behind it three cells turn pink-red.",
        )
        .detail(
            "Errors are rare but not rare enough.",
            &["Raw: ~2 errors in 10,000", "Spread at random", "Too many to use as is"],
        ),
    Beat::new("the decoder fixes them", BEAT_MS)
        .note(
            "The decoder uses the check symbols to find and correct the wrong ones (up to 15 bad 10-bit symbols per codeword), turning that raw error rate into a near-error-free link. The cost is the ~5% overhead and some added delay.",
            "A cyan bar sweeps across; as it passes each pink-red cell, the cell turns pale blue (fixed).",
        )
        .detail(
            "FEC fixes errors after the fact, without a resend.",
            &["Out: near error-free", "Cost: ~5% overhead", "Cost: some added delay"],
        ),
];

/// 7 Power, and taking the DSP out: the DSP module hot; LPO with the DSP lifted out; LRO on transmit only.
const S7_B: &[Beat] = &[
    Beat::new("the DSP's power", BEAT_MS)
        .note(
            "The DSP is most of a module's power. A 1.6T module with a 3 nm DSP is listed at up to about 25 W, and OCP figures put a 5 nm DSP module near 18.75 pJ/bit and a 3 nm one near 16.25 pJ/bit.",
            "The DSP package cut open with its die glowing orange, and orange heat puffs rising off its fins.",
        )
        .detail(
            "Power per bit is the number that matters at cluster scale.",
            &["1.6T, 3 nm DSP: up to ~25 W", "5 nm DSP module: ~18.75 pJ/bit", "3 nm DSP module: ~16.25 pJ/bit"],
        ),
    Beat::new("LPO: take the DSP out", BEAT_MS)
        .note(
            "Linear pluggable optics (LPO) remove the DSP and let the host's SerDes drive the optics directly: around 6.25 pJ/bit. Nokia lists a 1.6T DR8 LPO module under 10 W, 75% below a fully retimed one.",
            "The DSP package lifts off and disappears, leaving its copper pad footprint on the board. A cyan trace runs from the host lane straight to the driver chip, with dots along it.",
        )
        .detail(
            "Cutting the DSP cuts most of the module's power.",
            &["LPO: ~6.25 pJ/bit", "Nokia 1.6T DR8 LPO: under 10 W", "75% below fully retimed"],
        ),
    Beat::new("LRO, and the trade-off", BEAT_MS)
        .note(
            "LRO keeps the DSP only on the transmit side. The trade is interoperability: without a retimer, the host's SerDes must be good enough for every module it talks to.",
            "The package drops back into place; only its transmit path glows cyan, down the cut face and along the board to the driver and the laser.",
        )
        .detail(
            "Less power, but the host carries more of the burden.",
            &["LRO: DSP on transmit only", "LPO: no retimer at all", "Host SerDes quality matters more"],
        ),
];

/// 8 Who makes it: three DSP packages by maker; Credo's AEC; a TSMC wafer.
const S8_B: &[Beat] = &[
    Beat::new("Marvell, Broadcom, Credo", BEAT_MS)
        .note(
            "Marvell (MRVL) and Broadcom (AVGO) make most optical PAM4 DSPs. Broadcom's 3 nm Sian3 drives 200G-per-lane 1.6T modules. Credo (CRDO) makes DSPs too.",
            "Three cut-open DSP packages side by side on one board, tagged Marvell, Broadcom and Credo, with data dots running past them; a cable plug sits in front and a wafer behind.",
        )
        .detail(
            "A small group of chip companies supplies the DSPs.",
            &["Marvell (MRVL), Broadcom (AVGO)", "Broadcom Sian3: 3 nm, 200G/lane", "Credo (CRDO): DSPs too"],
        ),
    Beat::new("Credo's active electrical cable", BEAT_MS)
        .note(
            "Credo also makes active electrical cables (AECs): copper cables with a DSP in the plug that cleans the signal, so copper can reach further between racks.",
            "A cable plug with its shell cut open: a small green board with gold card-edge fingers and a DSP package on it, and two thick copper cables leaving the back with cyan dots running along them.",
        )
        .detail(
            "The same DSP job, in a cable instead of an optical module.",
            &["AEC: copper cable + DSP", "DSP sits in the plug", "Made by Credo (CRDO)"],
        ),
    Beat::new("all fabbed at TSMC", BEAT_MS)
        .note(
            "All of these DSPs are fabbed at TSMC, on its leading nodes: Broadcom's Sian3 is 3 nm.",
            "A silicon wafer on a dark chuck, covered in a grid of purple dies; the three packages sit in the foreground.",
        )
        .detail(
            "Every maker depends on the same foundry.",
            &["All fabbed at TSMC", "Sian3: 3 nm", "One die per DSP package"],
        ),
];

/// 9 Chokepoints and risks: a new DSP per lane-rate step; a DSP in every module; LPO leans on the host.
const S9_B: &[Beat] = &[
    Beat::new("a new DSP for every lane-rate step", BEAT_MS)
        .note(
            "Every lane-rate step, from 100G to 200G to 400G, needs a new DSP on a newer node. The design has to be redone and the chip made on a newer, more expensive process each time.",
            "Three dies on a tray with arrows between them: a 100G-per-lane die, a 200G-per-lane die, and a blank glass outline for 400G with a gold frame pulsing round it.",
        )
        .detail(
            "Each step waits on a new chip and a new node.",
            &["100G to 200G to 400G per lane", "Each step: a new DSP", "Each on a newer node"],
        ),
    Beat::new("DSP power adds up", BEAT_MS)
        .note(
            "DSP power grows with lanes, and every optical module has its own DSP. Tens of thousands of modules in a cluster add up.",
            "A switch faceplate packed with two rows of finned pluggable modules, each glowing orange at its sides where the DSP sits, with heat puffs rising above.",
        )
        .detail(
            "Module power is multiplied by the size of the cluster.",
            &["One DSP per module", "Tens of thousands per cluster", "1.6T module: up to ~25 W"],
        ),
    Beat::new("LPO leans on the host", BEAT_MS)
        .note(
            "LPO cuts power but makes links depend on the host chip's SerDes quality: with no retimer in the module, the host must drive the optics cleanly by itself.",
            "A host chip's package on its board, its die glowing; a trace runs straight to an LPO module whose red outline marks an empty DSP spot, with cyan dots going directly to the driver.",
        )
        .detail(
            "Saving power moves the risk onto the host chip.",
            &["LPO: no DSP in the module", "Host SerDes drives the optics", "Link quality rests on the host"],
        ),
];

fn section_1() -> Box<dyn Scene> {
    page(
        &CELL_1,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_1.glb"),
        S1_B,
    )
}

fn section_2() -> Box<dyn Scene> {
    page(
        &CELL_2,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_2.glb"),
        S2_B,
    )
}

fn section_3() -> Box<dyn Scene> {
    page(
        &CELL_3,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_3.glb"),
        S3_B,
    )
}

fn section_4() -> Box<dyn Scene> {
    page(
        &CELL_4,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_4.glb"),
        S4_B,
    )
}

fn section_5() -> Box<dyn Scene> {
    page(
        &CELL_5,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_5.glb"),
        S5_B,
    )
}

fn section_6() -> Box<dyn Scene> {
    page(
        &CELL_6,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_6.glb"),
        S6_B,
    )
}

fn section_7() -> Box<dyn Scene> {
    page(
        &CELL_7,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_7.glb"),
        S7_B,
    )
}

fn section_8() -> Box<dyn Scene> {
    page(
        &CELL_8,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_8.glb"),
        S8_B,
    )
}

fn section_9() -> Box<dyn Scene> {
    page(
        &CELL_9,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_dsp_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
