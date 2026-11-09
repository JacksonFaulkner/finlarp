// Fiber tab pages (PAM4 DSP, LASER, OPTICAL FIBER, PHOTODIODE, TRANSCEIVER, CPO): one
// optical link in poly3d (`render_link`), on the Memory tab's template. Each node is its
// overview beats, five zooms and nine sections, all keyframes over the same rig, which
// has five stations the camera flies between (link, glass, lasers, photodiode, CPO).
// Sources: section 10 of each FIB_*.txt page.

use super::diagrams_scene_link::{link_node, LinkNode, LinkState, SecData, ZoomData, BASE, BEAT_MS, CPO, EML, GLASS, HOST, LINK, OVERVIEW_MS, P, PD, RX, SIPH, TX, VCSEL};
use crate::ui::anim::Beat;
use poly3d::LinkKey;

// ---- shared states ----------------------------------------------------------------

const FLOW: LinkState = LinkState { elec: 1.0, ..BASE };
const OPEN: LinkState = LinkState { shell: 0.0, elec: 1.0, ..BASE };
const GL: LinkState = LinkState { link: 0.0, glass: 1.0, ..BASE };
const LS: LinkState = LinkState { link: 0.0, laser: 1.0, ..BASE };
const PDS: LinkState = LinkState { link: 0.0, pd: 1.0, ..BASE };
const CP: LinkState = LinkState { link: 0.0, cpo: 1.0, elec: 1.0, ..BASE };
const EYE: LinkState = LinkState { shell: 0.0, elec: 1.0, eye: 1.0, ..BASE };
const BARS: LinkState = LinkState { elec: 1.0, bars: 1.0, ..BASE };

const FAR: f64 = 5200.0;
const MOD: f64 = 1150.0;
/// the eye floats over the DSP; this frames module and eye together
const EYE_AT: [f64; 3] = [-120.0, 150.0, 0.0];
const BAR_AT: [f64; 3] = [1200.0, 150.0, 0.0];

macro_rules! k {
    ($t:expr, $d:expr, $y:expr, $p:expr, $s:expr) => {
        LinkKey::at($t, $d, $y, $p, $s)
    };
}

// =================================================================== PAM4 DSP

const D_B: &[Beat] = &[
    Beat::new("the host sends eight electrical lanes", OVERVIEW_MS).note("The switch or GPU chip drives eight SerDes lanes across the board to the module.", "Cyan data runs from the purple chip along copper traces into the module.").detail("Each lane 100G or 200G.", &["8 lanes per module"]),
    Beat::new("each symbol is one of four levels", OVERVIEW_MS).note("PAM4 sends four levels per symbol, two bits each.", "Bars over the cable: each symbol's height is its level.").detail("Twice NRZ's data at the same rate.", &["PAM4: 2 bits/symbol", "200G lane: 106.25 GBd"]),
    Beat::new("the DSP sits inside the module", OVERVIEW_MS).note("Lid off: the DSP is the big chip between the edge connector and the lasers.", "The module opens; the teal DSP glows.").detail("Most of the module's power.", &["3 nm DSP for 1.6T"]),
    Beat::new("blur and noise close the eye", OVERVIEW_MS).note("Copper smears symbols together; overlaid, the levels' gaps (the eye) close.", "A cyan eye diagram over the DSP, almost shut.").detail("The receiver can't tell levels apart.", &["EQUALIZATION needed"]),
    Beat::new("equalization opens it again", OVERVIEW_MS).note("Filters in the DSP undo the blur until three clean eyes open.", "The eye opens.").detail("Then the driver sends clean symbols to the lasers.", &["Many-tap digital filters"]),
    Beat::new("FEC fixes what errors remain", OVERVIEW_MS).note("The far-end DSP corrects errors using the extra FEC bits.", "Data crosses the link into the receiving module.").detail("RS(544,514) at 100G lanes.", &["~2e-4 raw errors to near zero", "~5% overhead"]),
    Beat::new("take the DSP out: linear optics", OVERVIEW_MS).note("LPO removes the DSP; the host's SerDes drives the laser directly.", "The DSP shrinks away; data goes straight to the driver.").detail("Nokia: 1.6T LPO under 10 W, 75% less.", &["~16 pJ/bit vs ~6 pJ/bit (OCP)"]),
];
const D_K: &[LinkKey] = &[
    k!(HOST, 1700.0, 0.45, 0.55, FLOW).labels(&[(P::Asic, "switch chip"), (P::Trace, "8 SerDes lanes")]).notes(P::Trace, Some(P::Asic)),
    k!(BAR_AT, 2600.0, 0.30, 0.30, BARS).labels(&[(P::Symbols, "PAM4 levels")]).notes(P::Symbols, None),
    k!(TX, MOD, 0.50, 0.75, OPEN.spot(P::Dsp)).labels(&[(P::Dsp, "DSP")]).notes(P::Dsp, None),
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.1, ..EYE }).labels(&[(P::Eye, "closed eye")]).notes(P::Eye, Some(P::Dsp)),
    k!(EYE_AT, 1250.0, 0.25, 0.30, EYE).labels(&[(P::Eye, "three open eyes")]).notes(P::Eye, Some(P::Dsp)),
    k!(LINK, FAR, 0.40, 0.40, BARS).labels(&[(P::RxModule, "far-end DSP")]).notes(P::RxModule, Some(P::Cable)),
    k!(TX, MOD, 0.50, 0.75, LinkState { dsp: 0.0, ..OPEN }).labels(&[(P::Driver, "SerDes drives laser")]).notes(P::Driver, None),
];
const DA_B: &[Beat] = &[
    Beat::new("NRZ: two levels, one bit", BEAT_MS).note("Each symbol is high or low.", "Bars at two heights.").detail("The classic signal.", &["1 bit/symbol"]),
    Beat::new("PAM4: four levels, two bits", BEAT_MS).note("Two more levels in between double the data.", "Bars at four heights.").detail("Same symbol rate.", &["2 bits/symbol"]),
    Beat::new("the cost: levels a third as far apart", BEAT_MS).note("Noise matters more: about 9.5 dB more signal-to-noise.", "Three small eyes instead of one big one.").detail("Textbook.", &["~9.5 dB penalty"]),
];
const DA_K: &[LinkKey] = &[
    k!(BAR_AT, 2600.0, 0.30, 0.30, LinkState { pam4: 0.0, ..BARS }).title("NRZ", "2 levels, 1 bit per symbol"),
    k!(BAR_AT, 2600.0, 0.30, 0.30, BARS).title("PAM4", "4 levels, 2 bits per symbol"),
    k!(EYE_AT, 1250.0, 0.25, 0.30, EYE).title("PAM4 eye", "levels a third as far apart"),
];
const DB_B: &[Beat] = &[
    Beat::new("the eye: symbols overlaid", BEAT_MS).note("Lay every symbol on the last; gaps between levels are eyes.", "A closed eye.").detail("Copper blurs them shut.", &["Eye diagram"]),
    Beat::new("equalizing", BEAT_MS).note("Filters undo the blur.", "The eye half opens.").detail("EQUALIZATION.", &["Filters"]),
    Beat::new("open: easy decisions", BEAT_MS).note("Wide eyes mean few errors.", "Three open eyes.").detail("The DSP's job.", &["Open"]),
];
const DB_K: &[LinkKey] = &[
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.0, ..EYE }).title("closed", "blur and noise"),
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.5, ..EYE }).title("equalizing", "filters in the DSP"),
    k!(EYE_AT, 1250.0, 0.25, 0.30, EYE).title("open", "clean decisions"),
];
const DC_B: &[Beat] = &[
    Beat::new("some errors always get through", BEAT_MS).note("Even an open eye has a raw error rate.", "Data across the link.").detail("About 2 in 10,000 is allowed.", &["Raw BER ~2e-4"]),
    Beat::new("extra bits ride along", BEAT_MS).note("RS(544,514): 30 check symbols per 514 data.", "Symbols over the cable.").detail("~5% overhead.", &["FEC"]),
    Beat::new("the far DSP corrects them", BEAT_MS).note("The receiver fixes errors itself, no resend.", "Into the far module.").detail("Near error-free.", &["Corrected"]),
];
const DC_K: &[LinkKey] = &[
    k!(LINK, FAR, 0.40, 0.40, BARS).title("raw errors", "~2 in 10,000"),
    k!(BAR_AT, 2600.0, 0.30, 0.30, BARS).title("FEC", "RS(544,514), ~5% overhead"),
    k!(RX, MOD, 0.50, 0.75, LinkState { shell: 0.0, ..BARS }.spot(P::RxModule)).title("corrected", "at the far DSP"),
];
const DD_B: &[Beat] = &[
    Beat::new("the DSP is the hot chip", BEAT_MS).note("Most of a module's power goes to the DSP.", "The DSP glows hot.").detail("1.6T: up to ~25 W per module.", &["~16-19 pJ/bit"]),
    Beat::new("LPO: no DSP", BEAT_MS).note("The host's SerDes drives the optics directly.", "The DSP shrinks away.").detail("Nokia 1.6T DR8 LPO under 10 W.", &["~6 pJ/bit"]),
    Beat::new("the trade: interoperability", BEAT_MS).note("Without a retimer, every host must drive every module well.", "Data straight to the driver.").detail("Validated mostly at hyperscalers.", &["LRO keeps TX DSP"]),
];
const DD_K: &[LinkKey] = &[
    k!(TX, MOD, 0.50, 0.75, LinkState { heat: 1.0, ..OPEN }.spot(P::Dsp)).title("DSP power", "most of the module"),
    k!(TX, MOD, 0.50, 0.75, LinkState { dsp: 0.0, ..OPEN }).title("LPO", "no DSP, under 10 W"),
    k!(TX, MOD, 0.50, 0.75, LinkState { dsp: 0.0, ..OPEN }.spot(P::Driver)).title("interoperability", "host SerDes drives the laser"),
];
const DE_B: &[Beat] = &[
    Beat::new("100G lane: 53.125 GBd", BEAT_MS).note("PAM4 at 53 billion symbols per second.", "Symbols over the cable.").detail("800G modules.", &["8 x 100G"]),
    Beat::new("200G lane: 106.25 GBd", BEAT_MS).note("Twice the symbol rate, twice the bandwidth everywhere.", "Faster symbols.").detail("1.6T modules.", &["8 x 200G"]),
    Beat::new("a new DSP each step", BEAT_MS).note("Each lane-rate step needs a DSP on a newer node.", "The DSP.").detail("3 nm for 200G.", &["Sian3"]),
];
const DE_K: &[LinkKey] = &[
    k!(BAR_AT, 2600.0, 0.30, 0.30, LinkState { lanes: 4.0, ..BARS }).title("100G lane", "53.125 GBd PAM4"),
    k!(BAR_AT, 2600.0, 0.30, 0.30, BARS).title("200G lane", "106.25 GBd PAM4"),
    k!(TX, MOD, 0.50, 0.75, OPEN.spot(P::Dsp)).title("3 nm DSP", "for 200G lanes"),
];
const D_Z: [ZoomData; 5] = [('a', "NRZ vs PAM4", DA_B, DA_K), ('b', "the eye and equalization", DB_B, DB_K), ('c', "FEC", DC_B, DC_K), ('d', "DSP power and LPO", DD_B, DD_K), ('e', "baud rate: 100G to 200G lanes", DE_B, DE_K)];
const D_S: [SecData; 9] = [(DB_B, DB_K), (DA_B, DA_K), (DC_B, DC_K), (DA_B, DA_K), (DB_B, DB_K), (DC_B, DC_K), (DD_B, DD_K), (DE_B, DE_K), (DD_B, DD_K)];
link_node!(D_ZOOMS, D_SECTIONS, D_Z, D_S);
pub static DSP: LinkNode = LinkNode { page: "PAM4 DSP", beats: D_B, keys: D_K, zooms: &D_ZOOMS, zoom_data: &D_Z, sections: &D_SECTIONS, section_data: &D_S };

// =================================================================== LASER

const EML_S: LinkState = LinkState { ..LS };
const L_B: &[Beat] = &[
    Beat::new("the lasers sit beside their driver", OVERVIEW_MS).note("Inside the module, the driver turns each clean symbol into a current for its laser.", "Lid off: a row of glowing lasers next to the driver chip.").detail("One laser per lane.", &["8 lanes, 8 lasers (DR8)"]),
    Beat::new("lenses steer light into fiber", OVERVIEW_MS).note("Each laser's light is focused by a lens into a fiber in the MPO connector.", "Red light runs laser, lens, connector.").detail("The core is ~8 um across.", &["1310 nm"]),
    Beat::new("EML: a laser and a modulator on one chip", OVERVIEW_MS).note("A DFB laser makes steady light; the modulator next to it dims it to each level.", "An InP chip: orange laser section, purple modulator, gold pads.").detail("Indium phosphide.", &["EML"]),
    Beat::new("out come four brightness levels", OVERVIEW_MS).note("After the modulator, light leaves in pulses at four PAM4 levels, through a lens into fiber.", "Steady light inside; pulsing light after the modulator.").detail("200G per lane for 1.6T.", &["106.25 GBd"]),
    Beat::new("silicon photonics: steady laser, silicon modulator", OVERVIEW_MS).note("A CW InP laser feeds a Mach-Zehnder modulator built in silicon: two arms that add or cancel.", "Light splits into two arms with gold electrodes, recombines, rises into fiber.").detail("Silicon can't emit light.", &["MACH-ZEHNDER"]),
    Beat::new("VCSEL: light out of the top", OVERVIEW_MS).note("A VCSEL emits straight up from between two mirror stacks into multimode fiber.", "A mesa of layered mirrors; light rises into an aqua fiber.").detail("Cheap, short reach.", &["850 nm, ~100 m"]),
    Beat::new("EMLs are scarce", OVERVIEW_MS).note("NVIDIA booked key EML capacity; lead times run past 2027.", "The EML chip.").detail("TrendForce, Dec 2025.", &["Lumentum, Coherent, Mitsubishi"]),
];
const L_K: &[LinkKey] = &[
    k!(TX, 900.0, 0.55, 0.70, OPEN.spot(P::Laser)).labels(&[(P::Laser, "lasers"), (P::Driver, "driver")]).notes(P::Laser, Some(P::Driver)),
    k!([150.0, 30.0, 0.0], 700.0, 0.45, 0.55, OPEN.spot(P::Lens)).labels(&[(P::Lens, "lenses"), (P::Connector, "MPO connector")]).notes(P::Lens, Some(P::Connector)),
    k!(EML, 1500.0, 0.50, 0.50, EML_S).labels(&[(P::Eml, "DFB laser"), (P::Eam, "modulator")]).notes(P::Eml, Some(P::Eam)),
    k!([-1300.0, 86.0, poly3d::LINK_LASER_Z], 1300.0, 0.30, 0.25, EML_S).labels(&[(P::Eam, "four levels out")]).notes(P::Eam, None),
    k!(SIPH, 1500.0, 0.45, 0.70, LS).labels(&[(P::Siph, "silicon chip"), (P::Mzm, "two arms")]).notes(P::Mzm, Some(P::Siph)),
    k!(VCSEL, 1500.0, 0.45, 0.30, LS).labels(&[(P::Vcsel, "VCSEL")]).notes(P::Vcsel, None),
    k!(EML, 1400.0, 0.60, 0.45, EML_S.spot(P::Eml)).labels(&[(P::Eml, "200G EML")]).notes(P::Eml, None),
];
const LA_B: &[Beat] = &[
    Beat::new("EML", BEAT_MS).note("Laser plus modulator on InP: single-mode workhorse.", "The EML chip.").detail("DR, FR modules.", &["EML"]),
    Beat::new("silicon photonics", BEAT_MS).note("CW laser plus silicon modulator.", "The silicon chip.").detail("Scales with silicon fabs.", &["SiPh"]),
    Beat::new("VCSEL", BEAT_MS).note("Surface-emitting, multimode, cheap.", "The VCSEL.").detail("~100 m.", &["VCSEL"]),
];
const LA_K: &[LinkKey] = &[
    k!(EML, 1500.0, 0.50, 0.50, EML_S).title("EML", "single-mode, InP"),
    k!(SIPH, 1500.0, 0.45, 0.70, LS).title("silicon photonics", "CW laser + modulator"),
    k!(VCSEL, 1500.0, 0.45, 0.30, LS).title("VCSEL", "multimode, 850 nm"),
];
const LB_B: &[Beat] = &[
    Beat::new("steady light from the DFB section", BEAT_MS).note("A grating locks it to one wavelength.", "The laser section glows.").detail("1310 nm.", &["DFB"]),
    Beat::new("the modulator dims it", BEAT_MS).note("A voltage makes it absorb more or less.", "Close on the modulator.").detail("Electro-absorption.", &["EAM"]),
    Beat::new("pulses into the fiber", BEAT_MS).note("Through a lens into the core.", "Pulses leave.").detail("Four levels.", &["PAM4 light"]),
];
const LB_K: &[LinkKey] = &[
    k!([-1800.0, 86.0, poly3d::LINK_LASER_Z], 900.0, 0.45, 0.45, EML_S.spot(P::Eml)).title("DFB laser", "steady 1310 nm"),
    k!([-1600.0, 86.0, poly3d::LINK_LASER_Z], 800.0, 0.45, 0.40, EML_S.spot(P::Eam)).title("modulator", "electro-absorption"),
    k!([-1300.0, 86.0, poly3d::LINK_LASER_Z], 1300.0, 0.30, 0.25, EML_S).title("into fiber", "four brightness levels"),
];
const LC_B: &[Beat] = &[
    Beat::new("light splits in two", BEAT_MS).note("A Y-junction halves the light.", "Two arms.").detail("Mach-Zehnder.", &["Split"]),
    Beat::new("a voltage delays one arm", BEAT_MS).note("Electrodes change the light's phase.", "Gold electrodes on the arms.").detail("Phase shift.", &["Electrodes"]),
    Beat::new("recombined: bright or dark", BEAT_MS).note("In phase they add; out of phase they cancel.", "Light rises into the fiber.").detail("Grating coupler.", &["Interference"]),
];
const LC_K: &[LinkKey] = &[
    k!([-200.0, 50.0, poly3d::LINK_LASER_Z], 1000.0, 0.40, 0.75, LS.spot(P::Mzm)).title("split", "two arms"),
    k!([0.0, 50.0, poly3d::LINK_LASER_Z], 900.0, 0.45, 0.80, LS.spot(P::Mzm)).title("phase shift", "voltage on one arm"),
    k!([300.0, 150.0, poly3d::LINK_LASER_Z], 1200.0, 0.45, 0.45, LS).title("recombine", "add or cancel"),
];
const LD_B: &[Beat] = &[
    Beat::new("1.6T needs 200G lasers", BEAT_MS).note("Eight lanes at 200G.", "The EML.").detail("Twice the bandwidth.", &["200G/lane"]),
    Beat::new("capacity booked past 2027", BEAT_MS).note("NVIDIA locked up key EML suppliers.", "The EML chip.").detail("TrendForce.", &["Shortage"]),
    Beat::new("the workaround: silicon photonics", BEAT_MS).note("CW lasers plus silicon modulators; still InP lasers.", "The silicon chip.").detail("Demand shifts, not gone.", &["CW laser"]),
];
const LD_K: &[LinkKey] = &[
    k!(EML, 1500.0, 0.50, 0.50, EML_S).title("200G lasers", "for 1.6T"),
    k!(EML, 1400.0, 0.60, 0.45, EML_S.spot(P::Eml)).title("shortage", "lead times past 2027"),
    k!(SIPH, 1500.0, 0.45, 0.70, LS.spot(P::Siph)).title("silicon photonics", "CW InP laser still needed"),
];
const LE_B: &[Beat] = &[
    Beat::new("one laser per lane", BEAT_MS).note("Eight lanes, eight lasers.", "The laser row.").detail("DR8.", &["8 lasers"]),
    Beat::new("driven by the driver chip", BEAT_MS).note("Clean symbols in, currents out.", "Driver and lasers.").detail("Beside the DSP.", &["Driver"]),
    Beat::new("light into the connector", BEAT_MS).note("Lenses into the MPO.", "Light to the connector.").detail("16 fibers.", &["MPO"]),
];
const LE_K: &[LinkKey] = &[
    k!(TX, 900.0, 0.55, 0.70, OPEN.spot(P::Laser)).title("lasers", "one per lane"),
    k!(TX, 900.0, 0.55, 0.70, OPEN.spot(P::Driver)).title("driver", "symbols to currents"),
    k!([150.0, 30.0, 0.0], 700.0, 0.45, 0.55, OPEN.spot(P::Connector)).title("connector", "into the fibers"),
];
const L_Z: [ZoomData; 5] = [('a', "EML, silicon photonics, VCSEL", LA_B, LA_K), ('b', "inside an EML", LB_B, LB_K), ('c', "a Mach-Zehnder modulator", LC_B, LC_K), ('d', "200G lasers and the shortage", LD_B, LD_K), ('e', "lasers in the module", LE_B, LE_K)];
const L_S: [SecData; 9] = [(LE_B, LE_K), (LA_B, LA_K), (LB_B, LB_K), (LA_B, LA_K), (LC_B, LC_K), (LD_B, LD_K), (LD_B, LD_K), (LA_B, LA_K), (LD_B, LD_K)];
link_node!(L_ZOOMS, L_SECTIONS, L_Z, L_S);
pub static LASER: LinkNode = LinkNode { page: "LASER", beats: L_B, keys: L_K, zooms: &L_ZOOMS, zoom_data: &L_Z, sections: &L_SECTIONS, section_data: &L_S };

// =================================================================== OPTICAL FIBER

const END: [f64; 3] = [700.0, 300.0, poly3d::LINK_GLASS_Z];
const F_B: &[Beat] = &[
    Beat::new("a fiber joins the two modules", OVERVIEW_MS).note("The cable between sending and receiving modules is a single-mode fiber pair.", "The whole link: modules at each end, yellow cable between.").detail("Yellow jacket = single-mode.", &["DR 500 m, FR 2 km"]),
    Beat::new("inside: a hair of glass", OVERVIEW_MS).note("Strip the cable and there's a coated glass fiber 242 um across.", "A magnified fiber: white coating stripped back from the glass.").detail("Drawn 4 units per micron.", &["Coating 242 um", "Cladding 125 um"]),
    Beat::new("the core: about 8 um", OVERVIEW_MS).note("Light travels only in the core, a thin channel at the centre.", "Close on the end: a thin pink core inside the glass cladding.").detail("Corning SMF-28 Ultra.", &["Core 8.2 um", "Mode field 9.2 um at 1310"]),
    Beat::new("light stays in the core", OVERVIEW_MS).note("The core's index is a third of a percent higher; its edge reflects light back in.", "Pulses run down the core.").detail("Total internal reflection.", &["TIR"]),
    Beat::new("multimode: wider core, bouncing light", OVERVIEW_MS).note("A 50 um core lets light bounce along many paths; their lengths differ, so pulses smear.", "A wider core; light zigzags off the walls.").detail("Reach ~100 m.", &["Core 50 um"]),
    Beat::new("only 0.32 dB lost per km", OVERVIEW_MS).note("A little light scatters away each kilometre.", "Pulses fade along the fiber.").detail("Corning SMF-28 Ultra.", &["0.32 dB/km at 1310", "0.18 dB/km at 1550"]),
    Beat::new("5 microseconds every km", OVERVIEW_MS).note("Light in glass goes at two thirds of c; distance becomes delay.", "A longer link.").detail("Hollow-core: ~1/3 less.", &["~5 us/km"]),
];
const F_K: &[LinkKey] = &[
    k!(LINK, FAR, 0.40, 0.40, FLOW).labels(&[(P::Cable, "single-mode fiber"), (P::Module, "sender"), (P::RxModule, "receiver")]).notes(P::Cable, Some(P::Module)),
    k!(GLASS, 3600.0, 0.45, 0.30, GL).labels(&[(P::Coating, "coating 242 um"), (P::Cladding, "cladding 125 um")]).notes(P::Coating, Some(P::Cladding)),
    k!(END, 1300.0, 0.70, 0.25, GL).labels(&[(P::Core, "core 8.2 um")]).notes(P::Core, Some(P::Cladding)),
    k!(GLASS, 2600.0, 0.35, 0.20, GL).labels(&[(P::Core, "light in the core")]).notes(P::Core, None),
    k!(GLASS, 2600.0, 0.35, 0.15, LinkState { mm: 1.0, tir: 1.0, ..GL }).labels(&[(P::Core, "50 um core")]).notes(P::Core, Some(P::Cladding)),
    k!(GLASS, 3000.0, 0.40, 0.20, LinkState { loss: 1.0, ..GL }).labels(&[(P::Cladding, "fading")]).notes(P::Cladding, None),
    k!([2200.0, 60.0, 0.0], 7400.0, 0.40, 0.40, LinkState { span: 2.0, ..BARS }).labels(&[(P::Cable, "~5 us per km")]).notes(P::Cable, None),
];
const FA_B: &[Beat] = &[
    Beat::new("COATING: 242 um", BEAT_MS).note("Acrylate protects the glass.", "The white coating.").detail("Or 200 um.", &["Coating"]),
    Beat::new("CLADDING: 125 um", BEAT_MS).note("Lower-index glass around the core.", "The glass cladding.").detail("Standard across fibers.", &["Cladding"]),
    Beat::new("CORE: 8.2 um", BEAT_MS).note("Where the light goes.", "The pink core.").detail("Single-mode.", &["Core"]),
];
const FA_K: &[LinkKey] = &[
    k!(GLASS, 3600.0, 0.45, 0.30, GL.spot(P::Coating)).title("coating", "242 um"),
    k!(GLASS, 3000.0, 0.55, 0.30, GL.spot(P::Cladding)).title("cladding", "125 um glass"),
    k!(END, 1300.0, 0.70, 0.25, GL.spot(P::Core)).title("core", "8.2 um"),
];
const FB_B: &[Beat] = &[
    Beat::new("single-mode: one straight path", BEAT_MS).note("A narrow core guides one mode.", "Light straight down the core.").detail("Kilometres.", &["SMF"]),
    Beat::new("multimode: many paths", BEAT_MS).note("A 50 um core; light bounces.", "Zigzag rays.").detail("~100 m.", &["MMF"]),
    Beat::new("paths of different length smear pulses", BEAT_MS).note("Modal dispersion limits reach.", "Bouncing light.").detail("Why AI goes single-mode.", &["Dispersion"]),
];
const FB_K: &[LinkKey] = &[
    k!(GLASS, 2600.0, 0.35, 0.20, GL).title("single-mode", "one path"),
    k!(GLASS, 2600.0, 0.35, 0.15, LinkState { mm: 1.0, tir: 1.0, ..GL }).title("multimode", "many paths"),
    k!([200.0, 300.0, poly3d::LINK_GLASS_Z], 1500.0, 0.25, 0.10, LinkState { mm: 1.0, tir: 1.0, ..GL }).title("modal dispersion", "pulses smear"),
];
const FC_B: &[Beat] = &[
    Beat::new("higher index in the core", BEAT_MS).note("Only ~0.36% higher than the cladding.", "The core.").detail("Enough.", &["Index step"]),
    Beat::new("grazing light reflects", BEAT_MS).note("Shallow angles reflect completely.", "Rays bounce off the edge.").detail("Snell's law.", &["TIR"]),
    Beat::new("kilometres without escaping", BEAT_MS).note("The boundary acts as a mirror.", "Light runs on.").detail("Total internal reflection.", &["Trapped"]),
];
const FC_K: &[LinkKey] = &[
    k!(END, 1300.0, 0.70, 0.25, LinkState { mm: 1.0, ..GL }.spot(P::Core)).title("index step", "core slightly higher"),
    k!([200.0, 300.0, poly3d::LINK_GLASS_Z], 1500.0, 0.25, 0.10, LinkState { mm: 1.0, tir: 1.0, ..GL }).title("reflection", "at the core's edge"),
    k!(GLASS, 2600.0, 0.35, 0.15, LinkState { mm: 1.0, tir: 1.0, ..GL }).title("trapped", "total internal reflection"),
];
const FD_B: &[Beat] = &[
    Beat::new("0.32 dB per km at 1310 nm", BEAT_MS).note("About 7% of the light per km.", "Pulses fade.").detail("SMF-28 Ultra max.", &["0.32 dB/km"]),
    Beat::new("0.18 dB per km at 1550 nm", BEAT_MS).note("Lower loss for long haul.", "Less fade.").detail("Coherent links.", &["0.18 dB/km"]),
    Beat::new("connectors cost more than glass", BEAT_MS).note("2 km of glass loses under 1 dB; connectors ~0.5 dB each.", "The link.").detail("Keep them clean.", &["Budget"]),
];
const FD_K: &[LinkKey] = &[
    k!(GLASS, 3000.0, 0.40, 0.20, LinkState { loss: 1.0, ..GL }).title("1310 nm", "0.32 dB/km"),
    k!(GLASS, 3000.0, 0.40, 0.20, LinkState { loss: 0.55, ..GL }).title("1550 nm", "0.18 dB/km"),
    k!(LINK, FAR, 0.40, 0.40, FLOW.spot(P::Connector)).title("connectors", "most of the loss"),
];
const FE_B: &[Beat] = &[
    Beat::new("across a building", BEAT_MS).note("Hundreds of metres: a microsecond or two.", "A short link.").detail("Small next to electronics.", &["~5 us/km"]),
    Beat::new("across a campus", BEAT_MS).note("Kilometres add microseconds.", "A long link.").detail("GPUs wait.", &["Distance = delay"]),
    Beat::new("hollow-core: light in air", BEAT_MS).note("About a third less delay.", "The fiber.").detail("Microsoft (Lumenisity).", &["Hollow-core"]),
];
const FE_K: &[LinkKey] = &[
    k!(LINK, FAR, 0.40, 0.40, BARS).title("building", "~1-2 us"),
    k!([2200.0, 60.0, 0.0], 7400.0, 0.40, 0.40, LinkState { span: 2.0, ..BARS }).title("campus", "microseconds add up"),
    k!(GLASS, 3000.0, 0.45, 0.25, GL).title("hollow-core", "~1/3 less delay"),
];
const F_Z: [ZoomData; 5] = [('a', "coating, cladding, core", FA_B, FA_K), ('b', "single-mode vs multimode", FB_B, FB_K), ('c', "total internal reflection", FC_B, FC_K), ('d', "attenuation", FD_B, FD_K), ('e', "latency", FE_B, FE_K)];
const F_S: [SecData; 9] = [(FA_B, FA_K), (FA_B, FA_K), (FC_B, FC_K), (FC_B, FC_K), (FB_B, FB_K), (FD_B, FD_K), (FE_B, FE_K), (FA_B, FA_K), (FD_B, FD_K)];
link_node!(F_ZOOMS, F_SECTIONS, F_Z, F_S);
pub static FIBER: LinkNode = LinkNode { page: "OPTICAL FIBER", beats: F_B, keys: F_K, zooms: &F_ZOOMS, zoom_data: &F_Z, sections: &F_SECTIONS, section_data: &F_S };

// =================================================================== PHOTODIODE

const RXO: LinkState = LinkState { shell: 0.0, elec: 1.0, ..BASE };
const P_B: &[Beat] = &[
    Beat::new("light reaches the far module", OVERVIEW_MS).note("At the receiving end, light from each fiber lands on a photodiode beside its TIA.", "Lid off the receiving module: photodiodes and TIA chip.").detail("One photodiode per lane.", &["PIN photodiode"]),
    Beat::new("the photodiode chip", OVERVIEW_MS).note("An InGaAs absorber layer sits on an indium phosphide chip under a ring contact.", "A magnified photodiode: dark absorber, gold ring, fiber above.").detail("Silicon can't see 1310 nm.", &["InGaAs"]),
    Beat::new("each photon frees an electron and a hole", OVERVIEW_MS).note("The reverse bias sweeps electrons down and holes up to the contacts: a current.", "Red light falls in; cyan electrons and orange holes move apart.").detail("Close to 1 A per W.", &["Responsivity ~1 A/W"]),
    Beat::new("the TIA turns current into voltage", OVERVIEW_MS).note("Microamps go up a wire to the TIA, which outputs a voltage.", "Yellow current along the wire to the teal TIA, cyan signal out.").detail("Its noise sets sensitivity.", &["TIA"]),
    Beat::new("then into the DSP", OVERVIEW_MS).note("The voltage goes through the far DSP, which equalizes and decodes PAM4.", "The receiving module, data flowing to the host.").detail("Then out to the host chip.", &["Equalize, decode"]),
    Beat::new("noise blurs the four levels", OVERVIEW_MS).note("TIA and shot noise make the PAM4 levels harder to tell apart.", "A half-closed eye.").detail("PAM4 needs more light than NRZ.", &["Sensitivity"]),
    Beat::new("the link budget", OVERVIEW_MS).note("Laser power minus fiber and connector losses must stay above the receiver's sensitivity.", "The whole link.").detail("Connectors ~0.5 dB each.", &["0.32 dB/km fiber"]),
];
const P_K: &[LinkKey] = &[
    k!(RX, 900.0, 0.35, 0.70, RXO.spot(P::Pd)).labels(&[(P::Pd, "photodiodes"), (P::Tia, "TIA")]).notes(P::Pd, Some(P::Tia)),
    k!(PD, 1700.0, 0.50, 0.40, PDS).labels(&[(P::Absorber, "InGaAs absorber")]).notes(P::Absorber, None),
    k!([0.0, 100.0, poly3d::LINK_PD_Z], 900.0, 0.50, 0.25, PDS).labels(&[(P::Absorber, "electrons, holes")]).notes(P::Absorber, None),
    k!(PD, 1500.0, 0.45, 0.45, PDS.spot(P::Amp)).labels(&[(P::Amp, "TIA")]).notes(P::Amp, Some(P::Absorber)),
    k!(RX, 1300.0, 0.35, 0.60, RXO).labels(&[(P::RxModule, "receiving module")]).notes(P::RxModule, None),
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.35, ..EYE }).labels(&[(P::Eye, "noisy levels")]).notes(P::Eye, None),
    k!(LINK, FAR, 0.40, 0.40, FLOW).labels(&[(P::Cable, "fiber loss"), (P::Connector, "connector loss")]).notes(P::Cable, Some(P::Connector)),
];
const PA_B: &[Beat] = &[
    Beat::new("light falls in", BEAT_MS).note("From the fiber above.", "Light into the chip.").detail("1310 nm.", &["Light"]),
    Beat::new("absorbed in InGaAs", BEAT_MS).note("Each photon frees a pair.", "Carriers appear.").detail("Silicon is transparent here.", &["InGaAs"]),
    Beat::new("swept to the contacts", BEAT_MS).note("Electrons down, holes up: current.", "Carriers move.").detail("Reverse bias.", &["Current"]),
];
const PA_K: &[LinkKey] = &[
    k!([0.0, 400.0, poly3d::LINK_PD_Z], 1600.0, 0.50, 0.30, PDS).title("light in", "from the fiber"),
    k!([0.0, 100.0, poly3d::LINK_PD_Z], 900.0, 0.50, 0.25, PDS.spot(P::Absorber)).title("absorbed", "InGaAs"),
    k!([0.0, 100.0, poly3d::LINK_PD_Z], 900.0, 0.60, 0.35, PDS).title("swept out", "a current"),
];
const PB_B: &[Beat] = &[
    Beat::new("InGaAs on InP", BEAT_MS).note("For single-mode receivers.", "The absorber.").detail("0.9-1.7 um.", &["InGaAs"]),
    Beat::new("germanium on silicon", BEAT_MS).note("For silicon photonics.", "The silicon chip.").detail("Same fab as the modulators.", &["Ge"]),
    Beat::new("silicon can't see 1310 nm", BEAT_MS).note("Transparent past ~1.1 um.", "Silicon.").detail("Hence InGaAs or Ge.", &["Band gap"]),
];
const PB_K: &[LinkKey] = &[
    k!(PD, 1700.0, 0.50, 0.40, PDS.spot(P::Absorber)).title("InGaAs", "on indium phosphide"),
    k!(SIPH, 1500.0, 0.45, 0.70, LinkState { laser: 1.0, link: 0.0, ..BASE }.spot(P::Siph)).title("germanium", "on silicon"),
    k!(SIPH, 1700.0, 0.55, 0.55, LinkState { laser: 1.0, link: 0.0, ..BASE }).title("silicon", "transparent at 1310 nm"),
];
const PC_B: &[Beat] = &[
    Beat::new("microamps from the photodiode", BEAT_MS).note("A tiny current.", "Current along the wire.").detail("~1 A/W.", &["Photocurrent"]),
    Beat::new("the TIA", BEAT_MS).note("Current in, voltage out.", "The TIA chip.").detail("Bandwidth to match.", &["TIA"]),
    Beat::new("voltage out to the DSP", BEAT_MS).note("Tens of millivolts.", "Signal out.").detail("Or straight to the host (LPO).", &["Voltage"]),
];
const PC_K: &[LinkKey] = &[
    k!([250.0, 100.0, poly3d::LINK_PD_Z], 1200.0, 0.45, 0.45, PDS).title("photocurrent", "microamps"),
    k!([550.0, 40.0, poly3d::LINK_PD_Z], 900.0, 0.45, 0.45, PDS.spot(P::Amp)).title("TIA", "current to voltage"),
    k!([700.0, 40.0, poly3d::LINK_PD_Z], 1200.0, 0.40, 0.35, PDS).title("out", "to the DSP"),
];
const PD_B: &[Beat] = &[
    Beat::new("noise in every receiver", BEAT_MS).note("Thermal and shot noise.", "A blurred eye.").detail("Sets sensitivity.", &["Noise"]),
    Beat::new("PAM4 levels are close", BEAT_MS).note("A third as far apart as NRZ.", "Three small eyes.").detail("Needs more light.", &["PAM4"]),
    Beat::new("the DSP rescues it", BEAT_MS).note("Equalization and FEC.", "The eye opens.").detail("Or not, without a DSP.", &["DSP"]),
];
const PD_K: &[LinkKey] = &[
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.2, ..EYE }).title("noise", "blurs the levels"),
    k!(EYE_AT, 1250.0, 0.25, 0.30, LinkState { eq: 0.5, ..EYE }).title("close levels", "PAM4"),
    k!(EYE_AT, 1250.0, 0.25, 0.30, EYE).title("rescued", "equalization + FEC"),
];
const PE_B: &[Beat] = &[
    Beat::new("laser power in", BEAT_MS).note("What the transmitter launches.", "The sending module.").detail("Start of the budget.", &["Tx power"]),
    Beat::new("minus fiber and connectors", BEAT_MS).note("0.32 dB/km plus ~0.5 dB per connector.", "The cable.").detail("Connectors dominate indoors.", &["Losses"]),
    Beat::new("above sensitivity, with margin", BEAT_MS).note("What reaches the photodiode must be enough.", "The receiving module.").detail("Or errors rise.", &["Margin"]),
];
const PE_K: &[LinkKey] = &[
    k!(TX, MOD, 0.50, 0.70, OPEN.spot(P::Laser)).title("launch", "laser power"),
    k!(LINK, FAR, 0.40, 0.40, FLOW.spot(P::Cable)).title("losses", "fiber + connectors"),
    k!(RX, 900.0, 0.35, 0.70, RXO.spot(P::Pd)).title("received", "above sensitivity"),
];
const P_Z: [ZoomData; 5] = [('a', "photon to current", PA_B, PA_K), ('b', "InGaAs and germanium", PB_B, PB_K), ('c', "the TIA", PC_B, PC_K), ('d', "noise and sensitivity", PD_B, PD_K), ('e', "the link budget", PE_B, PE_K)];
const P_S: [SecData; 9] = [(PA_B, PA_K), (PA_B, PA_K), (PC_B, PC_K), (PB_B, PB_K), (PC_B, PC_K), (PD_B, PD_K), (PE_B, PE_K), (PB_B, PB_K), (PE_B, PE_K)];
link_node!(P_ZOOMS, P_SECTIONS, P_Z, P_S);
pub static PD_NODE: LinkNode = LinkNode { page: "PHOTODIODE", beats: P_B, keys: P_K, zooms: &P_ZOOMS, zoom_data: &P_Z, sections: &P_SECTIONS, section_data: &P_S };

// =================================================================== TRANSCEIVER

const T_B: &[Beat] = &[
    Beat::new("a module in the front panel", OVERVIEW_MS).note("A pluggable OSFP module slides into a cage on the switch's front panel.", "A finned metal module half inside the panel, fiber out the front.").detail("Room for ~25 W.", &["OSFP"]),
    Beat::new("lid off: the whole link end", OVERVIEW_MS).note("Inside: DSP, driver and lasers, photodiodes and TIA, lenses, and an MPO connector.", "The lid slides back.").detail("Same module sends and receives.", &["DSP, lasers, PDs, MPO"]),
    Beat::new("eight lanes each way", OVERVIEW_MS).note("A DR8 module has eight lasers and eight photodiodes, a fiber for each.", "Eight lasers in a row; light into the connector.").detail("16 fibers in one MPO.", &["8 x 200G = 1.6T"]),
    Beat::new("a module at each end", OVERVIEW_MS).note("Every link has two modules: one in each switch or server.", "The whole link: two hosts, two modules.").detail("Several per GPU in big clusters.", &["2 per link"]),
    Beat::new("copper for a few metres", OVERVIEW_MS).note("Inside a rack, direct-attach copper needs no optics at all.", "A short black copper cable, electrical data all the way.").detail("Cheapest, shortest.", &["DAC ~3 m"]),
    Beat::new("multimode across a row", OVERVIEW_MS).note("Up to ~100 m, VCSELs over multimode fiber.", "Aqua cable, longer.").detail("SR8.", &["SR8 ~100 m"]),
    Beat::new("single-mode across the building", OVERVIEW_MS).note("DR8 to 500 m, 2xFR4 to 2 km on single-mode fiber.", "A long yellow single-mode link.").detail("Innolight #1 in 2024 (LightCounting).", &["DR8 500 m", "2xFR4 2 km"]),
];
const T_K: &[LinkKey] = &[
    k!([0.0, 60.0, 0.0], 1500.0, 0.60, 0.40, FLOW).labels(&[(P::Module, "OSFP module"), (P::Panel, "front panel")]).notes(P::Module, Some(P::Panel)),
    k!(TX, MOD, 0.50, 0.75, OPEN).labels(&[(P::Dsp, "DSP"), (P::Laser, "lasers"), (P::Connector, "MPO")]).notes(P::Laser, Some(P::Dsp)),
    k!([100.0, 30.0, 0.0], 800.0, 0.55, 0.75, OPEN.spot(P::Laser)).labels(&[(P::Laser, "8 lasers")]).notes(P::Laser, Some(P::Connector)),
    k!(LINK, FAR, 0.40, 0.40, FLOW).labels(&[(P::Module, "module"), (P::RxModule, "module")]).notes(P::Module, Some(P::RxModule)),
    k!([700.0, 60.0, 0.0], 3600.0, 0.40, 0.45, LinkState { copper: 1.0, span: 0.3, ..FLOW }).labels(&[(P::Cable, "DAC copper")]).notes(P::Cable, None),
    k!([1100.0, 60.0, 0.0], 4300.0, 0.40, 0.40, LinkState { mm: 1.0, span: 0.7, ..FLOW }).labels(&[(P::Cable, "multimode")]).notes(P::Cable, None),
    k!([2200.0, 60.0, 0.0], 7400.0, 0.40, 0.40, LinkState { span: 2.0, ..FLOW }).labels(&[(P::Cable, "single-mode")]).notes(P::Cable, None),
];
const TA_B: &[Beat] = &[
    Beat::new("closed", BEAT_MS).note("A finned OSFP shell.", "The module.").detail("Fins shed heat.", &["OSFP"]),
    Beat::new("opening", BEAT_MS).note("The lid slides back.", "Half open.").detail("PCB inside.", &["PCB"]),
    Beat::new("everything inside", BEAT_MS).note("DSP, optics, connector.", "Open.").detail("One link end.", &["Inside"]),
];
const TA_K: &[LinkKey] = &[
    k!(TX, MOD, 0.50, 0.65, FLOW).title("OSFP", "closed"),
    k!(TX, MOD, 0.50, 0.70, LinkState { shell: 0.5, ..FLOW }).title("opening", "the lid slides"),
    k!(TX, MOD, 0.50, 0.75, OPEN).title("open", "DSP, lasers, connector"),
];
const TB_B: &[Beat] = &[
    Beat::new("DAC: copper, ~3 m", BEAT_MS).note("No optics.", "Copper.").detail("In the rack.", &["DAC"]),
    Beat::new("SR8: multimode, ~100 m", BEAT_MS).note("VCSELs.", "Aqua fiber.").detail("Across a row.", &["SR8"]),
    Beat::new("DR8 / 2xFR4: single-mode, 500 m-2 km", BEAT_MS).note("EMLs or silicon photonics.", "Yellow fiber.").detail("Across a building.", &["DR8, 2xFR4"]),
];
const TB_K: &[LinkKey] = &[
    k!([700.0, 60.0, 0.0], 3600.0, 0.40, 0.45, LinkState { copper: 1.0, span: 0.3, ..FLOW }).title("DAC", "copper, ~3 m"),
    k!([1100.0, 60.0, 0.0], 4300.0, 0.40, 0.40, LinkState { mm: 1.0, span: 0.7, ..FLOW }).title("SR8", "multimode, ~100 m"),
    k!([2200.0, 60.0, 0.0], 7400.0, 0.40, 0.40, LinkState { span: 2.0, ..FLOW }).title("DR8 / 2xFR4", "single-mode, 500 m - 2 km"),
];
const TC_B: &[Beat] = &[
    Beat::new("four lanes", BEAT_MS).note("4 x 200G = 800G.", "Four lasers.").detail("DR4.", &["4 lanes"]),
    Beat::new("eight lanes", BEAT_MS).note("8 x 200G = 1.6T.", "Eight lasers.").detail("DR8.", &["8 lanes"]),
    Beat::new("16 fibers in one MPO", BEAT_MS).note("Eight each way.", "The connector.").detail("Every mating costs loss.", &["MPO-16"]),
];
const TC_K: &[LinkKey] = &[
    k!([100.0, 30.0, 0.0], 800.0, 0.55, 0.75, LinkState { lanes: 4.0, ..OPEN }.spot(P::Laser)).title("4 lanes", "800G"),
    k!([100.0, 30.0, 0.0], 800.0, 0.55, 0.75, OPEN.spot(P::Laser)).title("8 lanes", "1.6T"),
    k!([150.0, 30.0, 0.0], 700.0, 0.45, 0.55, OPEN.spot(P::Connector)).title("MPO", "16 fibers"),
];
const TD_B: &[Beat] = &[
    Beat::new("~25 W per 1.6T module", BEAT_MS).note("The DSP is most of it.", "A hot module.").detail("Vendor listings.", &["~25 W"]),
    Beat::new("64 ports per switch", BEAT_MS).note("Over a kilowatt of optics.", "Modules in the panel.").detail("Fans and fins.", &[">1 kW"]),
    Beat::new("LPO halves it", BEAT_MS).note("No DSP.", "The DSP gone.").detail("Under 10 W (Nokia).", &["LPO"]),
];
const TD_K: &[LinkKey] = &[
    k!(TX, MOD, 0.50, 0.75, LinkState { heat: 1.0, ..OPEN }.spot(P::Dsp)).title("module power", "~25 W"),
    k!([0.0, 60.0, 0.0], 1500.0, 0.60, 0.40, LinkState { heat: 1.0, ..FLOW }).title("per switch", "over a kilowatt"),
    k!(TX, MOD, 0.50, 0.75, LinkState { dsp: 0.0, ..OPEN }).title("LPO", "under 10 W"),
];
const TE_B: &[Beat] = &[
    Beat::new("two modules per link", BEAT_MS).note("One at each end.", "The link.").detail("Always paired.", &["2 per link"]),
    Beat::new("several links per GPU", BEAT_MS).note("Tiers of switches multiply links.", "Long link.").detail("Volume drives the market.", &["Several per GPU"]),
    Beat::new("mostly made in China", BEAT_MS).note("Seven of the top ten makers.", "The module.").detail("LightCounting 2024.", &["Innolight #1"]),
];
const TE_K: &[LinkKey] = &[
    k!(LINK, FAR, 0.40, 0.40, FLOW).title("a link", "two modules"),
    k!([2200.0, 60.0, 0.0], 7400.0, 0.40, 0.40, LinkState { span: 2.0, ..FLOW }).title("a cluster", "several per GPU"),
    k!(TX, MOD, 0.50, 0.65, FLOW.spot(P::Module)).title("makers", "Innolight, Coherent, Eoptolink"),
];
const T_Z: [ZoomData; 5] = [('a', "inside the module", TA_B, TA_K), ('b', "reach: DAC, SR8, DR8, FR4", TB_B, TB_K), ('c', "lanes and the MPO", TC_B, TC_K), ('d', "power and heat", TD_B, TD_K), ('e', "scale and makers", TE_B, TE_K)];
const T_S: [SecData; 9] = [(TA_B, TA_K), (TA_B, TA_K), (TA_B, TA_K), (TB_B, TB_K), (TC_B, TC_K), (TD_B, TD_K), (TE_B, TE_K), (TE_B, TE_K), (TD_B, TD_K)];
link_node!(T_ZOOMS, T_SECTIONS, T_Z, T_S);
pub static TRX: LinkNode = LinkNode { page: "TRANSCEIVER", beats: T_B, keys: T_K, zooms: &T_ZOOMS, zoom_data: &T_Z, sections: &T_SECTIONS, section_data: &T_S };

// =================================================================== CPO

const PLUGS: LinkState = LinkState { engines: 0.0, ..CP };
const ENG: LinkState = LinkState { engines: 1.0, ..CP };
const ENGINE_AT: [f64; 3] = [380.0, 50.0, poly3d::LINK_CPO_Z + 170.0];
const C_B: &[Beat] = &[
    Beat::new("today: pluggables at the front panel", OVERVIEW_MS).note("The switch chip sits mid-board; its optics are pluggable modules at the front panel.", "A switch package; a row of modules at the panel.").detail("Tens of centimetres apart.", &["8 modules shown"]),
    Beat::new("long copper to every module", OVERVIEW_MS).note("At 200G per lane those traces lose so much signal that each module needs a DSP.", "Data runs the length of the copper traces.").detail("The DSPs cost power.", &["~25 W per 1.6T port"]),
    Beat::new("move the optics onto the package", OVERVIEW_MS).note("Co-packaged optics put optical engines on the package, millimetres from the chip.", "The modules vanish; engines appear around the chip.").detail("Traces shrink to millimetres.", &["CO-PACKAGED OPTICS"]),
    Beat::new("light leaves in fiber", OVERVIEW_MS).note("Fibers run from each engine to the panel; external lasers at the panel feed them.", "Red light out along yellow fibers; laser boxes at the panel.").detail("Lasers stay swappable.", &["2 lasers instead of 8 per 1.6T"]),
    Beat::new("micro-ring modulators", OVERVIEW_MS).note("Each engine uses 200G micro-rings on TSMC's COUPE stack.", "Close on an engine: a tiny glowing ring.").detail("A few microns across.", &["200G MRM"]),
    Beat::new("3.5x lower power", OVERVIEW_MS).note("No DSPs and short wires: NVIDIA claims 3.5x less power than pluggables.", "Engines on the package, cool.").detail("Ships 2H 2026.", &["3.5x (NVIDIA)", "~100 Tb/s switches"]),
    Beat::new("but harder to service", OVERVIEW_MS).note("A failed engine means replacing the switch board, not pulling a module.", "One engine highlighted.").detail("The main objection.", &["SERVICEABILITY"]),
];
const C_K: &[LinkKey] = &[
    k!(CPO, 3600.0, 0.40, 0.60, PLUGS).labels(&[(P::Switch, "switch chip"), (P::Plug, "pluggables")]).notes(P::Plug, Some(P::Switch)),
    k!(CPO, 3200.0, 0.30, 0.75, PLUGS).labels(&[(P::Plug, "long traces")]).notes(P::Plug, Some(P::Switch)),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2200.0, 0.40, 0.70, ENG).labels(&[(P::Engine, "optical engine")]).notes(P::Engine, Some(P::Switch)),
    k!(CPO, 3600.0, 0.40, 0.60, ENG).labels(&[(P::Engine, "engine"), (P::Els, "external lasers")]).notes(P::Engine, Some(P::Els)),
    k!(ENGINE_AT, 700.0, 0.40, 1.05, ENG.spot(P::Ring)).labels(&[(P::Ring, "micro-ring")]).notes(P::Ring, None),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2400.0, 0.45, 0.55, LinkState { heat: 0.3, ..ENG }).labels(&[(P::Switch, "switch + optics")]).notes(P::Switch, None),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2200.0, 0.40, 0.70, ENG.spot(P::Engine)).labels(&[(P::Engine, "soldered in")]).notes(P::Engine, None),
];
const CA_B: &[Beat] = &[
    Beat::new("pluggables", BEAT_MS).note("Modules at the panel.", "The panel row.").detail("Easy to swap.", &["Pluggable"]),
    Beat::new("moving in", BEAT_MS).note("Traces shorten.", "Half way.").detail("Engines appear.", &["Moving"]),
    Beat::new("co-packaged", BEAT_MS).note("Engines on the package.", "Engines.").detail("Millimetres.", &["CPO"]),
];
const CA_K: &[LinkKey] = &[
    k!(CPO, 3600.0, 0.40, 0.60, PLUGS).title("pluggables", "at the front panel"),
    k!(CPO, 3600.0, 0.40, 0.60, LinkState { engines: 0.5, ..CP }).title("moving in", "traces shorten"),
    k!(CPO, 3600.0, 0.40, 0.60, ENG).title("co-packaged", "engines on the package"),
];
const CB_B: &[Beat] = &[
    Beat::new("a photonic chip", BEAT_MS).note("Modulators, photodiodes, waveguides.", "The engine's base.").detail("Silicon photonics.", &["PIC"]),
    Beat::new("an electronic chip on top", BEAT_MS).note("Drivers and TIAs, stacked.", "The teal top chip.").detail("TSMC COUPE.", &["EIC"]),
    Beat::new("a micro-ring", BEAT_MS).note("A few microns, 200G.", "The ring.").detail("Needs heater tuning.", &["MRM"]),
];
const CB_K: &[LinkKey] = &[
    k!(ENGINE_AT, 900.0, 0.40, 0.55, ENG.spot(P::Engine)).title("photonic chip", "modulators, detectors"),
    k!(ENGINE_AT, 800.0, 0.50, 0.65, ENG.spot(P::Engine)).title("electronic chip", "stacked on top (COUPE)"),
    k!(ENGINE_AT, 700.0, 0.40, 1.05, ENG.spot(P::Ring)).title("micro-ring", "200G modulator"),
];
const CC_B: &[Beat] = &[
    Beat::new("external lasers at the panel", BEAT_MS).note("Pluggable laser boxes.", "The laser boxes.").detail("Swappable.", &["ELS"]),
    Beat::new("light out to the engines", BEAT_MS).note("Steady light by fiber.", "Fibers.").detail("Shared across lanes.", &["CW light"]),
    Beat::new("two lasers instead of eight", BEAT_MS).note("Per 1.6T link.", "Engines lit.").detail("Hot Chips 2025.", &["4x fewer"]),
];
const CC_K: &[LinkKey] = &[
    k!([1500.0, 40.0, poly3d::LINK_CPO_Z + 300.0], 1900.0, 0.40, 0.55, ENG.spot(P::Els)).title("external lasers", "at the panel"),
    k!(CPO, 3000.0, 0.40, 0.60, ENG).title("light to engines", "by fiber"),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2200.0, 0.40, 0.70, ENG).title("fewer lasers", "2 instead of 8"),
];
const CD_B: &[Beat] = &[
    Beat::new("pluggable port: ~25 W", BEAT_MS).note("DSP plus long traces.", "Hot pluggables.").detail("1.6T (report).", &["~25 W"]),
    Beat::new("CPO port: ~9 W", BEAT_MS).note("No DSP, short wires.", "Cool engines.").detail("Report.", &["~9 W"]),
    Beat::new("NVIDIA: 3.5x lower power", BEAT_MS).note("Its stated figure.", "The CPO switch.").detail("optics.org.", &["3.5x"]),
];
const CD_K: &[LinkKey] = &[
    k!(CPO, 3400.0, 0.40, 0.55, LinkState { heat: 1.0, ..PLUGS }).title("pluggable port", "~25 W"),
    k!(CPO, 3400.0, 0.40, 0.55, LinkState { heat: 0.35, ..ENG }).title("CPO port", "~9 W"),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2400.0, 0.45, 0.55, ENG.spot(P::Switch)).title("3.5x", "NVIDIA's claim"),
];
const CE_B: &[Beat] = &[
    Beat::new("a pluggable fails: pull it", BEAT_MS).note("Seconds to swap.", "A module.").detail("Today.", &["Easy"]),
    Beat::new("an engine fails: the board", BEAT_MS).note("Soldered to the package.", "An engine.").detail("CPO.", &["Hard"]),
    Beat::new("keep the lasers out", BEAT_MS).note("The likeliest failure stays swappable.", "External lasers.").detail("The compromise.", &["ELS"]),
];
const CE_K: &[LinkKey] = &[
    k!(CPO, 3600.0, 0.40, 0.60, PLUGS.spot(P::Plug)).title("pluggable", "swap in seconds"),
    k!([0.0, 40.0, poly3d::LINK_CPO_Z], 2200.0, 0.40, 0.70, ENG.spot(P::Engine)).title("engine", "replace the board"),
    k!([1500.0, 40.0, poly3d::LINK_CPO_Z + 300.0], 1900.0, 0.40, 0.55, ENG.spot(P::Els)).title("lasers outside", "still swappable"),
];
const C_Z: [ZoomData; 5] = [('a', "pluggables to co-packaged", CA_B, CA_K), ('b', "inside an optical engine", CB_B, CB_K), ('c', "external lasers", CC_B, CC_K), ('d', "power per port", CD_B, CD_K), ('e', "serviceability", CE_B, CE_K)];
const C_S: [SecData; 9] = [(CA_B, CA_K), (CB_B, CB_K), (CC_B, CC_K), (CD_B, CD_K), (CB_B, CB_K), (CC_B, CC_K), (CA_B, CA_K), (CB_B, CB_K), (CE_B, CE_K)];
link_node!(C_ZOOMS, C_SECTIONS, C_Z, C_S);
pub static CPO_NODE: LinkNode = LinkNode { page: "CPO", beats: C_B, keys: C_K, zooms: &C_ZOOMS, zoom_data: &C_Z, sections: &C_SECTIONS, section_data: &C_S };
