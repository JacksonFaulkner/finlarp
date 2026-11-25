// TRANSCEIVER: the nine numbered sections, each a close-up picture from tools/pbr3d/blender/fiber_module_sections.py
// (GLB in tools/pbr3d/assets/fiber_module_section_<n>.glb). Three beats each, one idea per section:
// section N illustrates heading N of diagrams_pages/FIB_TRX.txt (what happens, the parts, the job in
// order, reach, lanes and speeds, power and heat, scale, who makes it, chokepoints), with facts from
// that write-up. The pictures are built from fiber_module_detail.py.

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

/// 1. What happens: one module holds both ends of the conversion.
const S1_B: &[Beat] = &[
    Beat::new("a pluggable slides into a cage", BEAT_MS)
        .note(
            "A pluggable transceiver slides into a cage on the switch's or server's front panel. Its edge connector, the gold fingers on the end of its circuit board, mates with a connector at the back of the cage and takes eight electrical lanes from the host chip.",
            "The grey finned module sliding in from the left into the cage, which is cut away on the near side. The black block at the back of the cage is the host's connector; copper traces run from it to the switch chip.",
        )
        .detail(
            "Pluggable: bought and swapped separately from the switch.",
            &["8 electrical lanes from the host chip", "Shell: OSFP or QSFP-DD"],
        ),
    Beat::new("inside: DSP, lasers, photodiodes, MPO", BEAT_MS)
        .note(
            "With the shell cut open, the parts sit in a line on one board. A DSP cleans the lanes, laser drivers and lasers make the light, photodiodes and TIAs read the light that comes back, lenses steer it, and an MPO connector at the front is where the fibre plugs in.",
            "The lid cut back to the rear. The tan package with the dark die is the DSP; the two open gold packages at the front hold the lasers (far) and the photodiodes (near); white fibres run from them to the black MPO port at the nose.",
        )
        .detail(
            "Every part is one step of electrical to optical, or back.",
            &["DSP, drivers and lasers transmit", "Photodiodes and TIAs receive", "Lenses and an MPO connector"],
        ),
    Beat::new("it sends and receives at once", BEAT_MS)
        .note(
            "The same module works both ways at the same time. On the transmit side the lasers turn lanes into light that leaves through the MPO; on the receive side light comes in through the same connector and the photodiodes turn it back into lanes.",
            "Cyan pulses into the eight lasers, which glow orange, and orange light out along the fibres; at the same time orange light comes in to the eight photodiodes and cyan pulses run on to the TIA.",
        )
        .detail(
            "One module is both ends of the conversion.",
            &["800G: 8 lanes each way", "Transmit and receive share one MPO"],
        ),
];

/// 2. The parts: form factors, optical ports, cable assemblies.
const S2_B: &[Beat] = &[
    Beat::new("OSFP and QSFP-DD: the two shells", BEAT_MS)
        .note(
            "800G and 1.6T modules come in two shells. OSFP (octal small form-factor pluggable) has 8 lanes and room for about 25 W, with fins built into its top. QSFP-DD (double-density QSFP) also has 8 lanes, in a smaller, cooler shell that relies on a heat sink on the cage.",
            "Left, the larger OSFP with its finned top; right, the flatter QSFP-DD with no fins, both with gold card edges at the back and blue pull tabs at the front.",
        )
        .detail(
            "Same 8 lanes, different size and heat budget.",
            &["OSFP: 8 lanes, room for ~25 W", "QSFP-DD: 8 lanes, smaller, cooler"],
        ),
    Beat::new("DR8's MPO and 2xFR4's duplex LCs", BEAT_MS)
        .note(
            "The optical port follows the optics. A DR8 module sends each lane down its own single-mode fibre, so it needs a multi-fibre MPO connector, 12 or 16 fibres in one plug. A 2xFR4 module puts four wavelengths on one fibre, so two duplex LC plugs are enough. SR8 does the DR8 job on multimode fibre over shorter reach.",
            "Left, a DR8 module with a black MPO plug and a yellow cable in its nose; right, a 2xFR4 module with two pairs of blue LC plugs and their yellow cords.",
        )
        .detail(
            "Fibre count is set by how many lanes share a fibre.",
            &["DR8: 8 single-mode fibres each way, ~500 m", "2xFR4: 4 wavelengths per fibre, 2 km", "MPO: 12 or 16 fibres in one plug"],
        ),
    Beat::new("DAC and AOC: cables with the ends built on", BEAT_MS)
        .note(
            "Not every link needs a separate module and fibre. A DAC (direct-attach copper) is a copper cable with module shells on its ends and no optics at all: cheapest, but only a few metres. An AOC (active optical cable) has transceivers built onto both ends of a fibre.",
            "Left, a module shell on a thick black copper cable carrying cyan signal; right, the same shell on a thin aqua fibre cable carrying orange light.",
        )
        .detail(
            "DAC for inside a rack, AOC and modules for longer runs.",
            &["DAC: no optics, a few metres, cheapest", "AOC: optics fixed onto the fibre"],
        ),
];

/// 3. One module's job, in order.
const S3_B: &[Beat] = &[
    Beat::new("lanes arrive; the DSP retimes them", BEAT_MS)
        .note(
            "Step 1: the host's eight SerDes lanes arrive at the edge connector. Step 2: they run along the module board to the DSP, which cleans and retimes each one so the optics get sharp, evenly timed pulses.",
            "The lid off over the whole board. Cyan pulses run from the connector at the back along the copper traces into the DSP, whose die then glows cyan.",
        )
        .detail(
            "Retiming undoes the blur of the host's copper.",
            &["1. 8 SerDes lanes at the edge", "2. the DSP retimes them"],
        ),
    Beat::new("drivers and lasers make light; lenses couple it", BEAT_MS)
        .note(
            "Step 3: drivers and lasers turn each lane into light, one laser per lane. Step 4: lenses couple that light into fibres, which run to the MPO connector at the front of the module and out to the network.",
            "Cyan pulses from the DSP into the driver, which glows, then along gold leads to the eight lasers, which glow orange. Orange beams pass the row of lenses, and light runs along the white fibres out of the MPO.",
        )
        .detail(
            "Each lane becomes one beam in one fibre (DR8).",
            &["3. drivers and lasers", "4. lenses into the MPO's fibres"],
        ),
    Beat::new("light back to lanes; the controller reports", BEAT_MS)
        .note(
            "Step 5: in the other direction, photodiodes and TIAs turn incoming light back into lanes, which go through the DSP and out of the edge connector to the host. Step 6: the module's small controller reports its power, temperature and light levels to the host.",
            "Orange light in at the MPO onto the photodiodes, cyan pulses on through the TIA, the DSP and back out at the edge. The small black controller chip at the back glows cyan.",
        )
        .detail(
            "The host can see each module's health.",
            &["5. photodiodes and TIAs", "6. controller: power, temperature, light"],
        ),
];

/// 4. Reach decides the type.
const S4_B: &[Beat] = &[
    Beat::new("board copper, then DAC in the rack", BEAT_MS)
        .note(
            "On a board, signals ride copper traces from the switch chip to the cage. Within a rack, a few metres, a DAC copper cable is enough: cheap, but heavy and limited in reach. No light is involved yet.",
            "Switch A on the left: cyan pulses along its board traces from the ASIC to the cage, then along the thick black DAC cable hanging toward switch B.",
        )
        .detail(
            "Copper is cheapest wherever it reaches.",
            &["Board: copper traces", "Rack: DAC, a few metres"],
        ),
    Beat::new("across a row: multimode, ~100 m", BEAT_MS)
        .note(
            "Across a row of racks, up to about 100 m, links switch to light: an AOC, or SR8 modules over multimode fibre. Multimode fibre has a wide core and uses cheap short-wave lasers, but the light spreads, which caps the reach.",
            "The DAC is gone. MPO plugs sit in both modules and an aqua multimode cable hangs between them, orange light running along it. Below the cable, a fibre end face shows the wide 50 um core that lets light take many paths and smear.",
        )
        .detail(
            "Multimode: cheaper optics, shorter reach.",
            &["AOC or SR8: up to ~100 m", "SR8: 8 multimode fibres, 850 nm VCSELs"],
        ),
    Beat::new("across a building: single-mode, 500 m and 2 km", BEAT_MS)
        .note(
            "Across a building the link needs single-mode fibre: DR8 to 500 m, 2xFR4 to 2 km. Between buildings and cities, coherent modules (ZR) reach 80 km and beyond.",
            "A yellow single-mode cable between the two modules, orange light travelling along it. The end face below now shows a tiny 9 um core: one path, so pulses stay sharp for kilometres.",
        )
        .detail(
            "Reach decides the module, and the module decides the fibre.",
            &["DR8: 500 m", "2xFR4: 2 km", "ZR coherent: 80 km and beyond"],
        ),
];

/// 5. Lanes and speeds.
const S5_B: &[Beat] = &[
    Beat::new("8 lanes x 100G PAM4 = 800G", BEAT_MS)
        .note(
            "An 800G module carries eight 100G lanes, each using PAM4: four signal levels, two bits per symbol. A 1.6T module keeps eight lanes but runs each at 200G, which takes a 3 nm DSP.",
            "Eight cyan pulse trains running in from the card edge along the module traces to the DSP, whose die glows.",
        )
        .detail(
            "Speed comes from faster lanes, not more of them.",
            &["800G: 8 x 100G PAM4", "1.6T: 8 x 200G, 3 nm DSPs"],
        ),
    Beat::new("DR8: a fibre per lane, 16 in all", BEAT_MS)
        .note(
            "A DR8 module gives every lane its own fibre: 8 out and 8 in, 16 fibres in all, gathered into one MPO connector at the front.",
            "Eight lasers and eight photodiodes glowing; orange light running along all sixteen fibres, and the sixteen fibre ends lit in a row across the MPO face.",
        )
        .detail(
            "Simple optics, but fibre count scales with lanes.",
            &["DR8: 16 fibres via one MPO", "One laser and one fibre per lane"],
        ),
    Beat::new("2xFR4: four wavelengths per fibre", BEAT_MS)
        .note(
            "2xFR4 multiplexes four wavelengths onto each fibre. Each set of four lasers runs at slightly different colours, a mux block combines them into one fibre, and two such sets use only four fibres in all, on two duplex LC plugs.",
            "The 2xFR4 board: each group of four lasers glows in four false colours, the beams run into two clear mux blocks, and light leaves on just two fibres to the black LC ports.",
        )
        .detail(
            "Fewer fibres, more complex optics.",
            &["4 wavelengths per fibre (CWDM)", "2xFR4: 4 fibres instead of 16", "Colours here are false: all near 1310 nm"],
        ),
];

/// 6. Power and heat.
const S6_B: &[Beat] = &[
    Beat::new("the DSP's heat goes into the finned shell", BEAT_MS)
        .note(
            "A cut through the module shows where the power ends up. The DSP is the hottest chip; its heat passes through a thermal pad and a pedestal in the lid into the shell, and the OSFP's fins spread it into the air. Listings put 1.6T DSP modules at up to about 25-26 W each.",
            "A cross-section: the green module board, the DSP glowing orange, the pedestal above it, the lid and the comb of fins, with orange heat rising from the die into the fins.",
        )
        .detail(
            "Each module must shed its own heat.",
            &["1.6T DSP modules: up to ~25-26 W", "Heat path: pad, pedestal, lid, fins"],
        ),
    Beat::new("64 ports: over a kilowatt of optics", BEAT_MS)
        .note(
            "A big switch has 64 such ports, so its optics alone can draw over a kilowatt. The OSFP shells' fins and the switch's fans carry it away: air comes in at the front panel and runs along the fins.",
            "A row of four modules in their cages at the faceplate, orange heat rising off every finned top and pale air streaming along them.",
        )
        .detail(
            "Optics power grows with port count.",
            &["64 ports x ~25 W: over 1 kW", "Fins plus switch fans"],
        ),
    Beat::new("LPO: drop the DSP, cut the power", BEAT_MS)
        .note(
            "Linear (LPO) modules remove the DSP. The host chip's lanes run straight to the drivers and TIAs, which cuts module power roughly in half or more, at the cost of less signal margin.",
            "An open module board with no DSP: cyan pulses run from the card edge straight to the laser driver and TIA, which glow.",
        )
        .detail(
            "Power at scale pushes toward LPO and CPO.",
            &["LPO: roughly half the power or less", "No DSP in the module"],
        ),
];

/// 7. Scale: modules per GPU.
const S7_B: &[Beat] = &[
    Beat::new("GPUs connect up through switches", BEAT_MS)
        .note(
            "Large AI clusters connect every GPU through several tiers of switches. Here four GPU servers (lids off, two GPUs each) link up to two leaf switches, and each of those links has a module at both ends.",
            "The bottom row: four open servers with finned GPU heat sinks. Yellow fibres run up from their ports to the leaf switches above, orange light along them, and the module noses at both ends lit.",
        )
        .detail(
            "Every link starts and ends in a module.",
            &["Several tiers of switches", "A module at each end of every link"],
        ),
    Beat::new("switch to switch: more modules", BEAT_MS)
        .note(
            "Each leaf switch links up to the spine switches above it, and every switch-to-switch link needs a module at each end too. Each extra tier adds more links, and more modules, for the same GPUs.",
            "The top two tiers: yellow fibres from the leaf switches to the spines, light along them, and the module noses at both ends lit.",
        )
        .detail(
            "More tiers, more modules per GPU.",
            &["Switch-to-switch: 2 modules per link"],
        ),
    Beat::new("several modules per GPU", BEAT_MS)
        .note(
            "Count them: this small fabric of 8 GPUs already uses 32 modules. Real clusters have more tiers and more GPUs, so they use several modules per GPU, and volume, not just speed, is what drives the market.",
            "The whole fabric with every module nose lit and light on every link.",
        )
        .detail(
            "Volume drives the module market.",
            &["Here: 32 modules for 8 GPUs", "Clusters: several modules per GPU"],
        ),
];

/// 8. Who makes it.
const S8_B: &[Beat] = &[
    Beat::new("module makers: Innolight leads", BEAT_MS)
        .note(
            "LightCounting's 2024 ranking had Innolight first, with revenue up 114% to over $3.3 billion, and Eoptolink third at $1.2 billion, up 175%. Coherent (COHR) has long been a leader. Seven of the top ten module makers were Chinese.",
            "A finished module seated in its cage, tagged with the makers that ship most of them.",
        )
        .detail(
            "Chinese makers ship most of the volume.",
            &["Innolight: #1, over $3.3B, +114%", "Eoptolink: #3, $1.2B, +175%", "7 of the top 10 were Chinese"],
        ),
    Beat::new("the lasers come from a few suppliers", BEAT_MS)
        .note(
            "The module makers buy their key chips. Lumentum (LITE) and Broadcom supply the lasers, the EMLs that turn each lane into light. The DSP is the other bought-in chip.",
            "The lid lifts away: the eight lasers glow orange in their open package at the front, and the DSP's die glows cyan.",
        )
        .detail(
            "Laser supply is concentrated.",
            &["EMLs: Lumentum (LITE), Broadcom"],
        ),
    Beat::new("contract assembly: Fabrinet", BEAT_MS)
        .note(
            "Many modules are put together under contract. Fabrinet (FN) assembles modules for other companies: placing the optics, aligning the fibres and closing the shell.",
            "The finned lid coming down onto the open module and closing it.",
        )
        .detail(
            "Assembly is its own business.",
            &["Fabrinet (FN): contract assembly"],
        ),
];

/// 9. Chokepoints and risks.
const S9_B: &[Beat] = &[
    Beat::new("EMLs and DSPs set how many ship", BEAT_MS)
        .note(
            "Two parts limit how many modules can ship: the lasers (EMLs) and the DSPs. An EML-based 800G DR8 module needs eight EMLs and a DSP, so a shortage of either caps module output, whatever the demand.",
            "The open module board with the eight lasers and the DSP's die glowing red: the scarce parts.",
        )
        .detail(
            "Two chips gate the supply.",
            &["EML-based DR8: 8 EMLs each", "1 DSP per module"],
        ),
    Beat::new("made mostly in China and Southeast Asia", BEAT_MS)
        .note(
            "Most module volume is made in China and Southeast Asia, so supply is exposed to trade policy: tariffs or export rules can move prices and lead times for everyone building clusters.",
            "A black shipping tray of three finished modules, with pale markers drifting across it.",
        )
        .detail(
            "Geography is a risk.",
            &["Most volume: China, Southeast Asia", "Exposed to trade policy"],
        ),
    Beat::new("power pushes toward LPO and CPO", BEAT_MS)
        .note(
            "Module power at cluster scale pushes the industry toward LPO modules, without a DSP, and toward co-packaged optics (CPO), where optical engines sit on the switch chip's package and no pluggable module is needed.",
            "A CPO package: the switch ASIC under its heat sink, blue optical engines around it on the tan substrate, the engines light up in turn, cyan signal runs millimetres from the ASIC into them, and orange light leaves on every yellow ribbon.",
        )
        .detail(
            "The pluggable's own power is its biggest long-run risk.",
            &["LPO: no DSP", "CPO: optics on the package"],
        ),
];

pub fn section_1() -> Box<dyn Scene> {
    page(
        &CELL_1,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_1.glb"),
        S1_B,
    )
}

pub fn section_2() -> Box<dyn Scene> {
    page(
        &CELL_2,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_2.glb"),
        S2_B,
    )
}

pub fn section_3() -> Box<dyn Scene> {
    page(
        &CELL_3,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_3.glb"),
        S3_B,
    )
}

pub fn section_4() -> Box<dyn Scene> {
    page(
        &CELL_4,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_4.glb"),
        S4_B,
    )
}

pub fn section_5() -> Box<dyn Scene> {
    page(
        &CELL_5,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_5.glb"),
        S5_B,
    )
}

pub fn section_6() -> Box<dyn Scene> {
    page(
        &CELL_6,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_6.glb"),
        S6_B,
    )
}

pub fn section_7() -> Box<dyn Scene> {
    page(
        &CELL_7,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_7.glb"),
        S7_B,
    )
}

pub fn section_8() -> Box<dyn Scene> {
    page(
        &CELL_8,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_8.glb"),
        S8_B,
    )
}

pub fn section_9() -> Box<dyn Scene> {
    page(
        &CELL_9,
        include_bytes!("../../../../../../tools/pbr3d/assets/fiber_module_section_9.glb"),
        S9_B,
    )
}

pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section_1, section_2, section_3, section_4, section_5, section_6, section_7, section_8,
    section_9,
];
