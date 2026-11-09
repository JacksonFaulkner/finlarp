// Power tab pages (GRID, SUBSTATION, SWITCHGEAR, UPS, RACK POWER, VRM): one power path
// in poly3d (`render_power`), on the Memory tab's template. Each node is its overview
// beats, five zooms and nine sections, all keyframes over the same rig, which has five
// stations the camera flies between (campus, transformer, backup room, rack, GPU board).
// Sources: section 10 of each PWR_*.txt page.

use super::diagrams_scene_pwr::{pwr_node, PwrNode, PwrState, SecData, ZoomData, BACKUP, BASE, BEAT_MS, BOARD, CAMPUS, GENS, HALL, OVERVIEW_MS, P, RACK, SUB, SWG, TOWERS, XFMR};
use crate::ui::anim::Beat;
use poly3d::PwrKey;

// ---- shared states ----------------------------------------------------------------

const XF: PwrState = PwrState { campus: 0.0, xfmr: 1.0, ..BASE };
const XC: PwrState = PwrState { cut: 1.0, ..XF };
const BK: PwrState = PwrState { campus: 0.0, backup: 1.0, ..BASE };
const OUT: PwrState = PwrState { outage: 1.0, ..BK };
const GENR: PwrState = PwrState { outage: 1.0, genset: 1.0, ..BK };
const RK: PwrState = PwrState { campus: 0.0, rack: 1.0, ..BASE };
const BD: PwrState = PwrState { campus: 0.0, board: 1.0, ..BASE };

const FAR: f64 = 7400.0;

macro_rules! k {
    ($t:expr, $d:expr, $y:expr, $p:expr, $s:expr) => {
        PwrKey::at($t, $d, $y, $p, $s)
    };
}

// =================================================================== GRID

const G_B: &[Beat] = &[
    Beat::new("a campus on the grid", OVERVIEW_MS).note("Transmission lines bring power to the substation; it flows through switchgear into the data hall.", "The whole campus: towers, substation yard, switchgear house, generators, data hall.").detail("Its size is set by its grid connection.", &["Campus: 100 MW to 1+ GW"]),
    Beat::new("transmission: 115 to 345 kV", OVERVIEW_MS).note("Steel towers carry three-phase lines at hundreds of kilovolts.", "Yellow power runs along the conductors, tower to tower.").detail("High voltage, low current, low loss.", &["115-345 kV"]),
    Beat::new("high voltage keeps loss small", OVERVIEW_MS).note("Loss goes with current squared; ten times the voltage is a hundredth of the loss.", "Close on a tower and its sagging conductors.").detail("I squared R.", &["10x volts = 1/100 loss"]),
    Beat::new("into the substation", OVERVIEW_MS).note("At the campus edge the lines drop to a gantry and into transformers.", "The substation yard.").detail("See SUBSTATION.", &["Step-down"]),
    Beat::new("data centers: 4.4% of US power", OVERVIEW_MS).note("US data centers used about 176 TWh in 2023; Berkeley Lab projects 6.7-12% of US power by 2028.", "The data hall, cooling units on its roof.").detail("LBNL, Dec 2024.", &["176 TWh (2023)", "325-580 TWh (2028)"]),
    Beat::new("waiting in the queue", OVERVIEW_MS).note("About 1,400 GW of generation waited to connect at the end of 2024; projects took 55 months.", "The towers and their lines.").detail("LBNL Queued Up 2025.", &["~1,400 GW queued", "55 months"]),
    Beat::new("PUE: how much reaches the chips", OVERVIEW_MS).note("Total site power over IT power; cooling and losses take the rest.", "Heat rises off the hall's roof.").detail("Efficient sites ~1.1-1.2.", &["PUE"]),
];
const G_K: &[PwrKey] = &[
    k!(CAMPUS, FAR, 0.45, 0.45, BASE).labels(&[(P::Pylon, "transmission"), (P::Yard, "substation"), (P::Hall, "data hall")]).notes(P::Yard, Some(P::Hall)),
    k!(TOWERS, 2400.0, 0.55, 0.25, BASE).labels(&[(P::Wire, "115-345 kV")]).notes(P::Wire, Some(P::Pylon)),
    k!([-2000.0, 450.0, -600.0], 1300.0, 0.75, 0.15, BASE.spot(P::Pylon)).labels(&[(P::Pylon, "tower")]).notes(P::Wire, None),
    k!(SUB, 2300.0, 0.50, 0.45, BASE.spot(P::Yard)).labels(&[(P::Yard, "substation"), (P::Xfmr, "transformers")]).notes(P::Yard, Some(P::Xfmr)),
    k!(HALL, 3600.0, 0.45, 0.45, BASE.spot(P::Hall)).labels(&[(P::Hall, "data hall")]).notes(P::Hall, None),
    k!(TOWERS, 2800.0, 0.40, 0.30, BASE.spot(P::Pylon)).labels(&[(P::Pylon, "the queue")]).notes(P::Pylon, None),
    k!(HALL, 3800.0, 0.40, 0.35, PwrState { heat: 1.0, ..BASE }).labels(&[(P::Hall, "IT + cooling")]).notes(P::Hall, None),
];
const GA_B: &[Beat] = &[
    Beat::new("power plant to tower", BEAT_MS).note("Stepped up to hundreds of kV.", "Lines arrive.").detail("Generator step-up.", &["Step-up"]),
    Beat::new("tower to tower", BEAT_MS).note("Three phases, two circuits.", "Conductors sag between towers.").detail("THREE-PHASE.", &["Lines"]),
    Beat::new("down to the gantry", BEAT_MS).note("Into the substation.", "The yard.").detail("Then step-down.", &["Gantry"]),
];
const GA_K: &[PwrKey] = &[
    k!([-2900.0, 400.0, -600.0], 1800.0, 0.60, 0.25, BASE).title("from the plant", "stepped up to transmission"),
    k!(TOWERS, 2400.0, 0.55, 0.25, BASE).title("transmission", "115-345 kV, three-phase"),
    k!(SUB, 2300.0, 0.50, 0.45, BASE).title("the gantry", "into the substation"),
];
const GB_B: &[Beat] = &[
    Beat::new("176 TWh in 2023", BEAT_MS).note("4.4% of US electricity.", "The data hall.").detail("LBNL.", &["4.4%"]),
    Beat::new("325-580 TWh by 2028", BEAT_MS).note("6.7% to 12%.", "The campus.").detail("Projection.", &["6.7-12%"]),
    Beat::new("one rack: ~120 kW", BEAT_MS).note("A campus: hundreds of MW.", "The hall.").detail("NVL72.", &["120 kW"]),
];
const GB_K: &[PwrKey] = &[
    k!(HALL, 3600.0, 0.45, 0.45, BASE.spot(P::Hall)).title("2023", "176 TWh, 4.4%"),
    k!(CAMPUS, FAR, 0.45, 0.45, BASE).title("2028", "325-580 TWh"),
    k!(HALL, 3000.0, 0.60, 0.40, BASE).title("density", "~120 kW per rack"),
];
const GC_B: &[Beat] = &[
    Beat::new("every project is studied", BEAT_MS).note("Before it connects.", "The lines.").detail("Grid operators.", &["Study"]),
    Beat::new("1,400 GW waiting", BEAT_MS).note("Plus 890 GW of storage.", "The towers.").detail("End of 2024.", &["Queue"]),
    Beat::new("55 months to build", BEAT_MS).note("Request to operation, 2024.", "The campus.").detail("LBNL.", &["55 months"]),
];
const GC_K: &[PwrKey] = &[
    k!(TOWERS, 2800.0, 0.40, 0.30, BASE).title("studies", "before connecting"),
    k!(TOWERS, 2800.0, 0.40, 0.30, BASE.spot(P::Pylon)).title("the queue", "~1,400 GW + 890 GW storage"),
    k!(CAMPUS, FAR, 0.45, 0.45, BASE).title("time", "55 months typical"),
];
const GD_B: &[Beat] = &[
    Beat::new("site power", BEAT_MS).note("Everything the campus draws.", "The campus.").detail("The numerator.", &["Total"]),
    Beat::new("IT power", BEAT_MS).note("What reaches the servers.", "The hall.").detail("The denominator.", &["IT"]),
    Beat::new("the rest is overhead", BEAT_MS).note("Cooling and conversion.", "Heat off the roof.").detail("PUE 1.2 = 20% extra.", &["PUE"]),
];
const GD_K: &[PwrKey] = &[
    k!(CAMPUS, FAR, 0.45, 0.45, BASE).title("site power", "everything drawn"),
    k!(HALL, 3600.0, 0.45, 0.45, BASE.spot(P::Hall)).title("IT power", "what the chips get"),
    k!(HALL, 3800.0, 0.40, 0.35, PwrState { heat: 1.0, ..BASE }).title("overhead", "cooling and losses"),
];
const GE_B: &[Beat] = &[
    Beat::new("the grid can't keep up", BEAT_MS).note("Years for lines and plants.", "The towers.").detail("Queues.", &["Wait"]),
    Beat::new("power on site", BEAT_MS).note("Gas turbines or engines.", "Generators running.").detail("Behind the meter.", &["On site"]),
    Beat::new("the trade", BEAT_MS).note("Open sooner, run your own plant.", "The campus.").detail("Fuel and permits.", &["Trade"]),
];
const GE_K: &[PwrKey] = &[
    k!(TOWERS, 2800.0, 0.40, 0.30, PwrState { outage: 0.6, ..BASE }).title("grid limits", "years to connect"),
    k!(GENS, 2600.0, 0.50, 0.35, PwrState { outage: 1.0, genset: 1.0, ..BASE }).title("on site", "behind the meter"),
    k!(CAMPUS, FAR, 0.45, 0.45, PwrState { genset: 1.0, ..BASE }).title("the trade", "your own plant"),
];
const G_Z: [ZoomData; 5] = [('a', "transmission", GA_B, GA_K), ('b', "how much power AI uses", GB_B, GB_K), ('c', "the interconnection queue", GC_B, GC_K), ('d', "PUE", GD_B, GD_K), ('e', "behind the meter", GE_B, GE_K)];
const G_S: [SecData; 9] = [(GA_B, GA_K), (GA_B, GA_K), (GA_B, GA_K), (GA_B, GA_K), (GB_B, GB_K), (GC_B, GC_K), (GD_B, GD_K), (GE_B, GE_K), (GC_B, GC_K)];
pwr_node!(G_ZOOMS, G_SECTIONS, G_Z, G_S);
pub static GRID_NODE: PwrNode = PwrNode { page: "GRID", beats: G_B, keys: G_K, zooms: &G_ZOOMS, zoom_data: &G_Z, sections: &G_SECTIONS, section_data: &G_S };

// =================================================================== SUBSTATION

const S_B: &[Beat] = &[
    Beat::new("the substation yard", OVERVIEW_MS).note("Lines land on a gantry and feed big power transformers on a gravel pad.", "The yard: gantry, two transformers with bushings and radiators.").detail("115-345 kV in, 13.8-34.5 kV out.", &["Step-down"]),
    Beat::new("one power transformer", OVERVIEW_MS).note("A steel tank of oil holding the core and windings; bushings on top, radiators on the sides.", "A single transformer, close.").detail("Tens to hundreds of MVA.", &["POWER TRANSFORMER"]),
    Beat::new("cut open: core and windings", OVERVIEW_MS).note("Three steel limbs, each wrapped in a low-voltage coil inside a high-voltage coil.", "The tank front comes away.").detail("Laminated electrical steel.", &["3 limbs, 2 yokes"]),
    Beat::new("the field links the coils", OVERVIEW_MS).note("Alternating current in one winding makes a changing field in the core that induces voltage in the other.", "Cyan flux loops round the core.").detail("Same volts per turn.", &["TURNS RATIO"]),
    Beat::new("few amps in, many amps out", OVERVIEW_MS).note("High voltage enters at low current through tall bushings; low voltage leaves at high current.", "Few yellow dots in at the top; many orange ones out.").detail("Power stays the same.", &["V x I constant"]),
    Beat::new("oil and radiators carry the heat", OVERVIEW_MS).note("Under 1% is lost, but at this size that's a lot of heat.", "Heat rises off the radiators.").detail(">99% efficient.", &["Oil cooled"]),
    Beat::new("the longest wait on the grid", OVERVIEW_MS).note("Large power transformers averaged about 128 weeks in 2025.", "The transformer.").detail("Wood Mackenzie.", &["~128 weeks", "GSU ~144 weeks"]),
];
const S_K: &[PwrKey] = &[
    k!(SUB, 2300.0, 0.50, 0.45, BASE).labels(&[(P::Yard, "gantry"), (P::Xfmr, "transformers")]).notes(P::Xfmr, Some(P::Yard)),
    k!(XFMR, 2400.0, 0.55, 0.30, XF).labels(&[(P::Bushing, "bushings"), (P::Radiator, "radiators")]).notes(P::Tank, Some(P::Bushing)),
    k!(XFMR, 2000.0, 0.35, 0.20, XC).labels(&[(P::Core, "steel core"), (P::Hv, "windings")]).notes(P::Core, Some(P::Hv)),
    k!([0.0, 230.0, poly3d::PWR_XFMR_Z], 1500.0, 0.20, 0.10, XC.spot(P::Core)).labels(&[(P::Core, "magnetic flux")]).notes(P::Core, None),
    k!(XFMR, 2400.0, 0.35, 0.25, XC).labels(&[(P::Bushing, "high V, low I"), (P::Lv, "low V, high I")]).notes(P::Bushing, Some(P::Lv)),
    k!(XFMR, 2600.0, 0.60, 0.25, PwrState { heat: 1.0, ..XF }).labels(&[(P::Radiator, "radiators")]).notes(P::Radiator, None),
    k!(XFMR, 2600.0, 0.50, 0.30, XF.spot(P::Tank)).labels(&[(P::Tank, "~128 weeks")]).notes(P::Tank, None),
];
const SA_B: &[Beat] = &[
    Beat::new("the core", BEAT_MS).note("Laminated electrical steel.", "Three limbs, two yokes.").detail("Carries the field.", &["CORE"]),
    Beat::new("the low-voltage winding", BEAT_MS).note("Few turns, thick copper, inside.", "The inner coil.").detail("High current.", &["LV"]),
    Beat::new("the high-voltage winding", BEAT_MS).note("Many turns, outside.", "Disc coils.").detail("High voltage.", &["HV"]),
];
const SA_K: &[PwrKey] = &[
    k!(XFMR, 2000.0, 0.35, 0.20, XC.spot(P::Core)).title("core", "laminated steel"),
    k!(XFMR, 1800.0, 0.30, 0.20, XC.spot(P::Lv)).title("LV winding", "few turns, thick copper"),
    k!(XFMR, 1800.0, 0.40, 0.20, XC.spot(P::Hv)).title("HV winding", "many turns"),
];
const SB_B: &[Beat] = &[
    Beat::new("current makes a field", BEAT_MS).note("Alternating current in the HV coil.", "Flux in the core.").detail("Faraday.", &["Field"]),
    Beat::new("the field induces voltage", BEAT_MS).note("Same volts per turn in each coil.", "Flux loops.").detail("Turns ratio = voltage ratio.", &["Induction"]),
    Beat::new("230 kV to 34.5 kV", BEAT_MS).note("About 6.7 times fewer turns.", "Power in and out.").detail("Example.", &["6.7:1"]),
];
const SB_K: &[PwrKey] = &[
    k!([0.0, 230.0, poly3d::PWR_XFMR_Z], 1500.0, 0.20, 0.10, XC.spot(P::Hv)).title("field", "from the HV coil"),
    k!([0.0, 230.0, poly3d::PWR_XFMR_Z], 1500.0, 0.20, 0.10, XC.spot(P::Core)).title("induction", "same volts per turn"),
    k!(XFMR, 2400.0, 0.35, 0.25, XC).title("ratio", "230 kV to 34.5 kV"),
];
const SC_B: &[Beat] = &[
    Beat::new("losses in the steel", BEAT_MS).note("Magnetic losses, always on.", "The core.").detail("Even at no load.", &["Core loss"]),
    Beat::new("losses in the copper", BEAT_MS).note("Resistance, rising with load.", "The windings.").detail("I squared R.", &["Copper loss"]),
    Beat::new("oil to radiators", BEAT_MS).note("Hot oil rises, cools, sinks.", "Heat off the fins.").detail(">99% efficient.", &["Cooling"]),
];
const SC_K: &[PwrKey] = &[
    k!(XFMR, 2000.0, 0.35, 0.20, PwrState { heat: 0.4, ..XC }.spot(P::Core)).title("core loss", "always on"),
    k!(XFMR, 2000.0, 0.35, 0.20, PwrState { heat: 0.6, ..XC }.spot(P::Hv)).title("copper loss", "rises with load"),
    k!(XFMR, 2600.0, 0.60, 0.25, PwrState { heat: 1.0, ..XF }).title("cooling", "oil and radiators"),
];
const SD_B: &[Beat] = &[
    Beat::new("~50 weeks in 2021", BEAT_MS).note("Average transformer lead time.", "A transformer.").detail("Wood Mackenzie.", &["50 weeks"]),
    Beat::new("~120 weeks in 2024", BEAT_MS).note("More than doubled.", "The yard.").detail("Demand surge.", &["120 weeks"]),
    Beat::new("~128 weeks in 2025", BEAT_MS).note("GSUs about 144.", "The transformer.").detail("Q2 2025 survey.", &["128 weeks"]),
];
const SD_K: &[PwrKey] = &[
    k!(XFMR, 2600.0, 0.50, 0.30, XF).title("2021", "~50 weeks"),
    k!(SUB, 2300.0, 0.50, 0.45, BASE.spot(P::Xfmr)).title("2024", "~120 weeks"),
    k!(XFMR, 2600.0, 0.50, 0.30, XF.spot(P::Tank)).title("2025", "~128 weeks, GSU ~144"),
];
const SE_B: &[Beat] = &[
    Beat::new("grain-oriented steel", BEAT_MS).note("Crystals aligned with the field.", "The core.").detail("Lower losses.", &["GOES"]),
    Beat::new("few mills make it", BEAT_MS).note("One domestic US producer.", "The core.").detail("Cleveland-Cliffs.", &["Supply"]),
    Beat::new("custom, imported, scarce", BEAT_MS).note("Each unit built for its site.", "The yard.").detail("Tariffs worsen it.", &["Risk"]),
];
const SE_K: &[PwrKey] = &[
    k!(XFMR, 2000.0, 0.35, 0.20, XC.spot(P::Core)).title("electrical steel", "grain-oriented"),
    k!([0.0, 230.0, poly3d::PWR_XFMR_Z], 1500.0, 0.20, 0.10, XC.spot(P::Core)).title("supply", "few mills"),
    k!(SUB, 2300.0, 0.50, 0.45, BASE.spot(P::Xfmr)).title("custom units", "little spare stock"),
];
const S_Z: [ZoomData; 5] = [('a', "core and windings", SA_B, SA_K), ('b', "how the turns ratio works", SB_B, SB_K), ('c', "losses and cooling", SC_B, SC_K), ('d', "lead times", SD_B, SD_K), ('e', "electrical steel", SE_B, SE_K)];
const S_S: [SecData; 9] = [(SA_B, SA_K), (SA_B, SA_K), (SB_B, SB_K), (SB_B, SB_K), (SC_B, SC_K), (SD_B, SD_K), (SE_B, SE_K), (SD_B, SD_K), (SD_B, SD_K)];
pwr_node!(S_ZOOMS, S_SECTIONS, S_Z, S_S);
pub static SUB_NODE: PwrNode = PwrNode { page: "SUBSTATION", beats: S_B, keys: S_K, zooms: &S_ZOOMS, zoom_data: &S_Z, sections: &S_SECTIONS, section_data: &S_S };

// =================================================================== SWITCHGEAR

const W_B: &[Beat] = &[
    Beat::new("from the yard to the switchgear house", OVERVIEW_MS).note("Medium-voltage cable runs from the transformers to a building full of breakers.", "Power flows from the yard to the switchgear house.").detail("13.8-34.5 kV.", &["MEDIUM VOLTAGE"]),
    Beat::new("split into feeds", OVERVIEW_MS).note("Breakers split the supply into feeds, each to a unit substation stepping down to 480 V.", "The switchgear house and its feeds to the hall.").detail("480 V in the US, 415 V elsewhere.", &["480 V"]),
    Beat::new("a fault: breakers open in milliseconds", OVERVIEW_MS).note("Relays spot a fault and trip the nearest breaker; the rest stays up.", "The switchgear house highlighted.").detail("Vacuum breakers at MV.", &["PROTECTION RELAY"]),
    Beat::new("two of everything", OVERVIEW_MS).note("2N: two full paths, each able to carry the whole load.", "The hall fed from the house.").detail("Each server takes one feed from each.", &["2N / N+1"]),
    Beat::new("generators wait outside", OVERVIEW_MS).note("A row of generators connects through transfer switches.", "The generator row along the hall.").detail("See UPS.", &["ATS"]),
    Beat::new("outage: generators take over", OVERVIEW_MS).note("The utility drops; generators start and the transfer switch moves the load.", "The lines go dark red; generators exhaust and feed the hall.").detail("Batteries bridge the seconds.", &["~10 s to start"]),
    Beat::new("utility back", OVERVIEW_MS).note("When the grid returns, the load transfers back and the generators cool down.", "Power from the lines again.").detail("Routine for a data center.", &["Transfer back"]),
];
const W_K: &[PwrKey] = &[
    k!([-700.0, 80.0, -450.0], 2600.0, 0.50, 0.50, BASE).labels(&[(P::Xfmr, "transformers"), (P::Switchgear, "switchgear")]).notes(P::Switchgear, Some(P::Xfmr)),
    k!([200.0, 60.0, -100.0], 2800.0, 0.45, 0.50, BASE).labels(&[(P::Switchgear, "MV breakers"), (P::Hall, "480 V to the hall")]).notes(P::Switchgear, Some(P::Hall)),
    k!(SWG, 1600.0, 0.55, 0.40, BASE.spot(P::Switchgear)).labels(&[(P::Switchgear, "relays + breakers")]).notes(P::Switchgear, None),
    k!([800.0, 80.0, 0.0], 3600.0, 0.45, 0.45, BASE).labels(&[(P::Hall, "two feeds")]).notes(P::Hall, Some(P::Switchgear)),
    k!(GENS, 2600.0, 0.50, 0.35, BASE.spot(P::Gen)).labels(&[(P::Gen, "generators")]).notes(P::Gen, None),
    k!(CAMPUS, FAR, 0.45, 0.45, PwrState { outage: 1.0, genset: 1.0, ..BASE }).labels(&[(P::Wire, "utility lost"), (P::Gen, "generators on")]).notes(P::Gen, Some(P::Wire)),
    k!(CAMPUS, FAR, 0.45, 0.45, BASE).labels(&[(P::Wire, "utility back")]).notes(P::Wire, None),
];
const WA_B: &[Beat] = &[
    Beat::new("main breaker", BEAT_MS).note("MV cable lands.", "The house.").detail("13.8-34.5 kV.", &["Main"]),
    Beat::new("feeder breakers", BEAT_MS).note("Split into circuits.", "Feeds out.").detail("One per block.", &["Feeders"]),
    Beat::new("unit substations to 480 V", BEAT_MS).note("Then UPS and hall.", "Into the hall.").detail("Low voltage.", &["480 V"]),
];
const WA_K: &[PwrKey] = &[
    k!(SWG, 1600.0, 0.55, 0.40, BASE.spot(P::Switchgear)).title("main breaker", "medium voltage in"),
    k!([200.0, 60.0, -100.0], 2800.0, 0.45, 0.50, BASE).title("feeders", "split into circuits"),
    k!(HALL, 3600.0, 0.45, 0.45, BASE.spot(P::Hall)).title("480 V", "unit substations"),
];
const WB_B: &[Beat] = &[
    Beat::new("a short circuit", BEAT_MS).note("Tens of thousands of amps.", "The house.").detail("Fault.", &["Fault"]),
    Beat::new("the relay trips", BEAT_MS).note("Within a cycle.", "Breakers.").detail("Coordinated.", &["Relay"]),
    Beat::new("only one feed drops", BEAT_MS).note("Upstream breakers wait.", "Power continues.").detail("Selectivity.", &["Selective"]),
];
const WB_K: &[PwrKey] = &[
    k!(SWG, 1600.0, 0.55, 0.40, PwrState { heat: 0.6, ..BASE }.spot(P::Switchgear)).title("fault", "huge current"),
    k!(SWG, 1400.0, 0.40, 0.35, BASE.spot(P::Switchgear)).title("relay", "trips the breaker"),
    k!([200.0, 60.0, -100.0], 2800.0, 0.45, 0.50, BASE).title("selective", "one feed drops"),
];
const WC_B: &[Beat] = &[
    Beat::new("path A", BEAT_MS).note("One full path.", "The hall.").detail("Carries all load.", &["A"]),
    Beat::new("path B", BEAT_MS).note("A second full path.", "The hall.").detail("2N.", &["B"]),
    Beat::new("service one, run on the other", BEAT_MS).note("No downtime.", "The house.").detail("Cost: double gear.", &["2N"]),
];
const WC_K: &[PwrKey] = &[
    k!([800.0, 80.0, 0.0], 3600.0, 0.45, 0.45, BASE).title("path A", "carries the whole load"),
    k!([800.0, 80.0, 0.0], 3600.0, 0.55, 0.45, BASE.spot(P::Hall)).title("path B", "and so does this"),
    k!(SWG, 1600.0, 0.55, 0.40, BASE.spot(P::Switchgear)).title("2N", "service without downtime"),
];
const WD_B: &[Beat] = &[
    Beat::new("utility fails", BEAT_MS).note("Lines go dead.", "Red lines.").detail("Outage.", &["Out"]),
    Beat::new("generators start", BEAT_MS).note("About 10 seconds.", "Exhaust.").detail("NFPA 110.", &["Start"]),
    Beat::new("the ATS transfers", BEAT_MS).note("Load to generators.", "Generators feed the hall.").detail("Then back.", &["Transfer"]),
];
const WD_K: &[PwrKey] = &[
    k!(TOWERS, 2800.0, 0.40, 0.30, PwrState { outage: 1.0, ..BASE }).title("outage", "utility lost"),
    k!(GENS, 2600.0, 0.50, 0.35, PwrState { outage: 1.0, genset: 1.0, ..BASE }).title("start", "~10 seconds"),
    k!(CAMPUS, FAR, 0.45, 0.45, PwrState { outage: 1.0, genset: 1.0, ..BASE }).title("transfer", "ATS to generators"),
];
const WE_B: &[Beat] = &[
    Beat::new("an arc in air", BEAT_MS).note("Thousands of degrees.", "The house.").detail("Arc flash.", &["Arc"]),
    Beat::new("enclosed gear", BEAT_MS).note("Built to contain it.", "The switchgear.").detail("Arc-resistant.", &["Contain"]),
    Beat::new("work de-energized", BEAT_MS).note("Or in rated gear.", "The house.").detail("NFPA 70E.", &["Safety"]),
];
const WE_K: &[PwrKey] = &[
    k!(SWG, 1400.0, 0.40, 0.35, PwrState { heat: 1.0, ..BASE }.spot(P::Switchgear)).title("arc flash", "thousands of degrees"),
    k!(SWG, 1600.0, 0.55, 0.40, BASE.spot(P::Switchgear)).title("enclosed", "arc-resistant gear"),
    k!(SWG, 1800.0, 0.70, 0.40, PwrState { flow: 0.0, ..BASE }).title("de-energized", "safe work"),
];
const W_Z: [ZoomData; 5] = [('a', "a feed: MV to 480 V", WA_B, WA_K), ('b', "breaking a fault", WB_B, WB_K), ('c', "redundancy: 2N", WC_B, WC_K), ('d', "generators and the ATS", WD_B, WD_K), ('e', "arc flash", WE_B, WE_K)];
const W_S: [SecData; 9] = [(WA_B, WA_K), (WA_B, WA_K), (WA_B, WA_K), (WB_B, WB_K), (WE_B, WE_K), (WC_B, WC_K), (WD_B, WD_K), (WA_B, WA_K), (WC_B, WC_K)];
pwr_node!(W_ZOOMS, W_SECTIONS, W_Z, W_S);
pub static SWG_NODE: PwrNode = PwrNode { page: "SWITCHGEAR", beats: W_B, keys: W_K, zooms: &W_ZOOMS, zoom_data: &W_Z, sections: &W_SECTIONS, section_data: &W_S };

// =================================================================== UPS

const U_B: &[Beat] = &[
    Beat::new("utility through the UPS to the racks", OVERVIEW_MS).note("Power passes the transfer switch, then the UPS's rectifier and inverter, into the racks.", "Yellow power from the utility pole, through the cabinets, to a row of racks.").detail("Double conversion.", &["AC > DC > AC"]),
    Beat::new("batteries stay charged", OVERVIEW_MS).note("The DC link keeps a bank of lithium-ion batteries topped up.", "Battery cabinets behind the UPS, charging.").detail("Minutes of runtime.", &["LITHIUM-ION"]),
    Beat::new("the utility drops", OVERVIEW_MS).note("The feed fails. The inverter keeps running from the batteries, with no break.", "The utility line goes red; orange battery power flows to the inverter.").detail("The racks never notice.", &["0 ms interruption"]),
    Beat::new("batteries carry the load", OVERVIEW_MS).note("For seconds to minutes, all the power comes from the batteries.", "Battery modules dim as they drain.").detail("Sized for minutes.", &["RUNTIME"]),
    Beat::new("the generator starts", OVERVIEW_MS).note("Within about ten seconds the diesel reaches voltage and frequency.", "Exhaust rises from the generator's stack.").detail("NFPA 110 Type 10.", &["~10 s", "2-3 MW per unit"]),
    Beat::new("the transfer switch moves the load", OVERVIEW_MS).note("The ATS connects the UPS input to the generator; batteries recharge.", "Power flows from the generator through the ATS.").detail("Then back when the utility returns.", &["TRANSFER SWITCH"]),
    Beat::new("two conversions cost a few percent", OVERVIEW_MS).note("Every watt is rectified and inverted, losing about 3-5%.", "Normal running, heat off the cabinets.").detail("Eco modes bypass when clean.", &["3-5% loss"]),
];
const U_K: &[PwrKey] = &[
    k!(BACKUP, 2900.0, 0.50, 0.40, BK).labels(&[(P::Utility, "utility"), (P::Ups, "UPS"), (P::Load, "racks")]).notes(P::Ups, Some(P::Load)),
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.55, 0.40, BK.spot(P::Battery)).labels(&[(P::Battery, "batteries")]).notes(P::Battery, Some(P::Ups)),
    k!(BACKUP, 2900.0, 0.50, 0.40, OUT).labels(&[(P::Utility, "utility lost"), (P::Battery, "batteries")]).notes(P::Battery, Some(P::Utility)),
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.55, 0.40, OUT.spot(P::Battery)).labels(&[(P::Battery, "draining")]).notes(P::Battery, None),
    k!([-1100.0, 200.0, poly3d::PWR_BACKUP_Z - 400.0], 2000.0, 0.50, 0.30, GENR.spot(P::Gen)).labels(&[(P::Gen, "generator")]).notes(P::Gen, None),
    k!(BACKUP, 2900.0, 0.50, 0.40, GENR).labels(&[(P::Ats, "transfer switch"), (P::Gen, "generator")]).notes(P::Ats, Some(P::Gen)),
    k!(BACKUP, 2700.0, 0.40, 0.35, PwrState { heat: 1.0, ..BK }.spot(P::Ups)).labels(&[(P::Ups, "3-5% loss")]).notes(P::Ups, None),
];
const UA_B: &[Beat] = &[
    Beat::new("rectifier", BEAT_MS).note("AC to DC.", "First cabinet.").detail("Conversion one.", &["Rectifier"]),
    Beat::new("DC link and batteries", BEAT_MS).note("DC charges the batteries.", "The batteries.").detail("Energy store.", &["DC"]),
    Beat::new("inverter", BEAT_MS).note("DC to clean AC.", "Out to the racks.").detail("Conversion two.", &["Inverter"]),
];
const UA_K: &[PwrKey] = &[
    k!([-720.0, 120.0, poly3d::PWR_BACKUP_Z], 1300.0, 0.40, 0.30, BK.spot(P::Ups)).title("rectifier", "AC to DC"),
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.55, 0.40, BK.spot(P::Battery)).title("DC link", "keeps batteries charged"),
    k!([-300.0, 120.0, poly3d::PWR_BACKUP_Z], 1600.0, 0.40, 0.30, BK.spot(P::Load)).title("inverter", "DC to clean AC"),
];
const UB_B: &[Beat] = &[
    Beat::new("0 s: utility lost", BEAT_MS).note("Batteries take over instantly.", "Red utility line.").detail("No break.", &["0 s"]),
    Beat::new("~10 s: generator up", BEAT_MS).note("Engine at speed.", "Exhaust.").detail("NFPA 110.", &["10 s"]),
    Beat::new("transfer: generator carries it", BEAT_MS).note("Batteries recharge.", "Generator power.").detail("Hours, on fuel.", &["Gen"]),
];
const UB_K: &[PwrKey] = &[
    k!(BACKUP, 2900.0, 0.50, 0.40, OUT).title("0 s", "batteries take over"),
    k!([-1100.0, 200.0, poly3d::PWR_BACKUP_Z - 400.0], 2000.0, 0.50, 0.30, GENR.spot(P::Gen)).title("~10 s", "generator at speed"),
    k!(BACKUP, 2900.0, 0.50, 0.40, GENR).title("transfer", "generator carries the load"),
];
const UC_B: &[Beat] = &[
    Beat::new("lithium-ion cabinets", BEAT_MS).note("Smaller, lighter than lead-acid.", "The cabinets.").detail("Longer life.", &["Li-ion"]),
    Beat::new("minutes, not hours", BEAT_MS).note("Just enough to bridge.", "Draining.").detail("Runtime.", &["Minutes"]),
    Beat::new("recharge after", BEAT_MS).note("From the generator or utility.", "Charging.").detail("Ready for the next.", &["Recharge"]),
];
const UC_K: &[PwrKey] = &[
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.55, 0.40, BK.spot(P::Battery)).title("lithium-ion", "cabinets of modules"),
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.55, 0.40, OUT.spot(P::Battery)).title("runtime", "minutes"),
    k!([-500.0, 120.0, poly3d::PWR_BACKUP_Z - 200.0], 1700.0, 0.45, 0.40, GENR.spot(P::Battery)).title("recharge", "on generator power"),
];
const UD_B: &[Beat] = &[
    Beat::new("a diesel and an alternator", BEAT_MS).note("About 2-3 MW each.", "The generator.").detail("Rows outside the hall.", &["2-3 MW"]),
    Beat::new("start in ten seconds", BEAT_MS).note("Type 10.", "Exhaust.").detail("NFPA 110.", &["10 s"]),
    Beat::new("fuel for a day or more", BEAT_MS).note("Tanks on site.", "Running.").detail("Permits limit hours.", &["Fuel"]),
];
const UD_K: &[PwrKey] = &[
    k!([-1100.0, 200.0, poly3d::PWR_BACKUP_Z - 400.0], 2000.0, 0.50, 0.30, BK.spot(P::Gen)).title("generator", "2-3 MW"),
    k!([-1100.0, 200.0, poly3d::PWR_BACKUP_Z - 400.0], 2000.0, 0.50, 0.30, GENR.spot(P::Gen)).title("start", "within ~10 s"),
    k!(GENS, 2600.0, 0.50, 0.35, PwrState { outage: 1.0, genset: 1.0, ..BASE }).title("a row of them", "fuel on site"),
];
const UE_B: &[Beat] = &[
    Beat::new("two conversions", BEAT_MS).note("Rectify, invert.", "The UPS.").detail("Each loses some.", &["2x"]),
    Beat::new("3-5% lost", BEAT_MS).note("As heat.", "Hot cabinets.").detail("Must be cooled too.", &["Heat"]),
    Beat::new("eco mode", BEAT_MS).note("Bypass when the utility is clean.", "Normal flow.").detail("~99%.", &["Eco"]),
];
const UE_K: &[PwrKey] = &[
    k!(BACKUP, 2700.0, 0.40, 0.35, BK.spot(P::Ups)).title("double conversion", "every watt, twice"),
    k!(BACKUP, 2700.0, 0.40, 0.35, PwrState { heat: 1.0, ..BK }.spot(P::Ups)).title("losses", "3-5% as heat"),
    k!(BACKUP, 2900.0, 0.50, 0.40, BK).title("eco mode", "bypass when clean"),
];
const U_Z: [ZoomData; 5] = [('a', "inside a UPS", UA_B, UA_K), ('b', "a power cut, second by second", UB_B, UB_K), ('c', "batteries and runtime", UC_B, UC_K), ('d', "generators", UD_B, UD_K), ('e', "efficiency", UE_B, UE_K)];
const U_S: [SecData; 9] = [(UB_B, UB_K), (UA_B, UA_K), (UB_B, UB_K), (UA_B, UA_K), (UC_B, UC_K), (UD_B, UD_K), (UE_B, UE_K), (UD_B, UD_K), (UE_B, UE_K)];
pwr_node!(U_ZOOMS, U_SECTIONS, U_Z, U_S);
pub static UPS_NODE: PwrNode = PwrNode { page: "UPS", beats: U_B, keys: U_K, zooms: &U_ZOOMS, zoom_data: &U_Z, sections: &U_SECTIONS, section_data: &U_S };

// =================================================================== RACK POWER

const R_B: &[Beat] = &[
    Beat::new("an AI rack", OVERVIEW_MS).note("A GB200 NVL72-style rack: compute and switch trays, power shelves top and bottom.", "A tall rack: purple compute trays, teal switch trays, grey power shelves.").detail("~120 kW.", &["72 GPUs per rack"]),
    Beat::new("AC into the power shelves", OVERVIEW_MS).note("415/480 V AC feeds the shelves; each holds six 5.5 kW supplies.", "Power drops into the top shelves.").detail("33 kW per shelf.", &["6 x 5.5 kW = 33 kW"]),
    Beat::new("DC down the busbar", OVERVIEW_MS).note("The shelves make about 50 V DC on a copper busbar down the back.", "Orange DC runs down the copper bar.").detail("Trays clip on.", &["~50 V DC"]),
    Beat::new("into every tray", OVERVIEW_MS).note("Each compute and switch tray takes its share from the busbar.", "DC crosses into the trays.").detail("Then the VRMs.", &["18 compute, 9 switch trays"]),
    Beat::new("thousands of amps", OVERVIEW_MS).note("120 kW at 50 V is about 2,400 A; a 192 kW peak is over 3,800 A.", "The busbar highlighted, trays hot.").detail("Thick copper.", &["~2,400 A"]),
    Beat::new("a row of racks", OVERVIEW_MS).note("A row of these draws a megawatt or more.", "Several racks side by side.").detail("1-2 MW per row.", &["1-2 MW"]),
    Beat::new("next: 800 V DC", OVERVIEW_MS).note("NVIDIA plans 800 V DC for 1 MW racks from 2027, with power in a sidecar rack.", "A sidecar power rack appears; the busbar thins.").detail("16x less current than 50 V.", &["800 VDC", "1 MW racks"]),
];
const R_K: &[PwrKey] = &[
    k!(RACK, 2600.0, 0.55, 0.25, RK).labels(&[(P::Tray, "compute trays"), (P::Shelf, "power shelves")]).notes(P::Tray, Some(P::Shelf)),
    k!([0.0, 950.0, poly3d::PWR_RACK_Z], 1500.0, 0.55, 0.35, RK.spot(P::Shelf)).labels(&[(P::Shelf, "33 kW shelves")]).notes(P::Shelf, None),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z - 100.0], 2300.0, 2.40, 0.20, RK.spot(P::Busbar)).labels(&[(P::Busbar, "DC busbar")]).notes(P::Busbar, None),
    k!(RACK, 2200.0, 0.45, 0.25, RK).labels(&[(P::Tray, "trays")]).notes(P::Tray, Some(P::Busbar)),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z - 100.0], 2300.0, 2.40, 0.20, PwrState { heat: 0.8, ..RK }.spot(P::Busbar)).labels(&[(P::Busbar, "~2,400 A")]).notes(P::Busbar, None),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z], 4200.0, 0.55, 0.30, PwrState { count: 5.0, ..RK }).labels(&[(P::Rack, "a row")]).notes(P::Rack, None),
    k!([160.0, 560.0, poly3d::PWR_RACK_Z], 3000.0, 0.50, 0.25, PwrState { hvdc: 1.0, ..RK }).labels(&[(P::Sidecar, "800 V sidecar")]).notes(P::Sidecar, Some(P::Busbar)),
];
const RA_B: &[Beat] = &[
    Beat::new("AC in", BEAT_MS).note("From the PDU.", "Power drops in.").detail("415/480 V.", &["AC"]),
    Beat::new("shelves convert", BEAT_MS).note("AC to ~50 V DC.", "The shelves.").detail("Six PSUs each.", &["PSU"]),
    Beat::new("busbar to trays", BEAT_MS).note("Copper down the back.", "DC flows.").detail("Clip-on trays.", &["Busbar"]),
];
const RA_K: &[PwrKey] = &[
    k!([0.0, 1100.0, poly3d::PWR_RACK_Z], 1600.0, 0.55, 0.30, RK).title("AC in", "415/480 V from the PDU"),
    k!([0.0, 950.0, poly3d::PWR_RACK_Z], 1500.0, 0.55, 0.35, RK.spot(P::Shelf)).title("power shelves", "AC to ~50 V DC"),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z - 100.0], 2300.0, 2.40, 0.20, RK.spot(P::Busbar)).title("busbar", "DC to every tray"),
];
const RB_B: &[Beat] = &[
    Beat::new("33 kW per shelf", BEAT_MS).note("Six 5.5 kW modules.", "A shelf.").detail("Vertiv.", &["33 kW"]),
    Beat::new("eight shelves, N+N", BEAT_MS).note("Half can fail.", "Top and bottom.").detail("NVIDIA DGX guide.", &["N+N"]),
    Beat::new("hot-swappable", BEAT_MS).note("Pull a PSU while running.", "The shelf.").detail("Service without downtime.", &["Swap"]),
];
const RB_K: &[PwrKey] = &[
    k!([0.0, 950.0, poly3d::PWR_RACK_Z], 1500.0, 0.55, 0.35, RK.spot(P::Shelf)).title("33 kW", "six 5.5 kW PSUs"),
    k!(RACK, 2600.0, 0.55, 0.25, RK.spot(P::Shelf)).title("N+N", "shelves top and bottom"),
    k!([0.0, 100.0, poly3d::PWR_RACK_Z], 1500.0, 0.50, 0.30, RK.spot(P::Shelf)).title("hot-swap", "while the rack runs"),
];
const RC_B: &[Beat] = &[
    Beat::new("cloud rack: 10-20 kW", BEAT_MS).note("Air cooled.", "A rack.").detail("Before AI.", &["10-20 kW"]),
    Beat::new("NVL72: ~120 kW", BEAT_MS).note("132 kW design, 192 kW peak.", "The rack, hot.").detail("HPE.", &["120-132 kW"]),
    Beat::new("next: 600 kW-1 MW", BEAT_MS).note("Kyber-class racks.", "A row.").detail("NVIDIA.", &["1 MW"]),
];
const RC_K: &[PwrKey] = &[
    k!(RACK, 2600.0, 0.55, 0.25, PwrState { flow: 0.3, ..RK }).title("cloud rack", "10-20 kW"),
    k!(RACK, 2600.0, 0.55, 0.25, PwrState { heat: 1.0, ..RK }).title("NVL72", "~120 kW, peaks ~192"),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z], 4200.0, 0.55, 0.30, PwrState { count: 5.0, heat: 0.6, ..RK }).title("next", "600 kW to 1 MW per rack"),
];
const RD_B: &[Beat] = &[
    Beat::new("50 V: thick copper", BEAT_MS).note("Thousands of amps.", "The busbar.").detail("Up to 200 kg at 1 MW.", &["Copper"]),
    Beat::new("800 V DC from the edge", BEAT_MS).note("13.8 kV AC converted once.", "Sidecar appears.").detail("Fewer conversions.", &["800 VDC"]),
    Beat::new("a sidecar power rack", BEAT_MS).note("Power gear beside the GPUs.", "The sidecar.").detail("From 2027.", &["Sidecar"]),
];
const RD_K: &[PwrKey] = &[
    k!([0.0, 560.0, poly3d::PWR_RACK_Z - 100.0], 2300.0, 2.40, 0.20, RK.spot(P::Busbar)).title("50 V", "thick copper"),
    k!([160.0, 560.0, poly3d::PWR_RACK_Z], 3000.0, 0.50, 0.25, PwrState { hvdc: 0.6, ..RK }).title("800 V DC", "converted at the edge"),
    k!([160.0, 560.0, poly3d::PWR_RACK_Z], 3000.0, 0.50, 0.25, PwrState { hvdc: 1.0, ..RK }.spot(P::Sidecar)).title("sidecar", "power beside the rack"),
];
const RE_B: &[Beat] = &[
    Beat::new("P = V x I", BEAT_MS).note("Lower voltage, more current.", "The rack.").detail("Physics.", &["P = VI"]),
    Beat::new("~2,400 A at 50 V", BEAT_MS).note("For 120 kW.", "The busbar.").detail("The Register.", &["2,400 A"]),
    Beat::new("~150 A at 800 V", BEAT_MS).note("Same power, 16x less.", "Thin bar, sidecar.").detail("Less copper.", &["16x less"]),
];
const RE_K: &[PwrKey] = &[
    k!(RACK, 2600.0, 0.55, 0.25, RK).title("P = V x I", "lower volts, more amps"),
    k!([0.0, 560.0, poly3d::PWR_RACK_Z - 100.0], 2300.0, 2.40, 0.20, PwrState { heat: 0.8, ..RK }.spot(P::Busbar)).title("50 V", "~2,400 A"),
    k!([160.0, 560.0, poly3d::PWR_RACK_Z], 3000.0, 0.50, 0.25, PwrState { hvdc: 1.0, ..RK }.spot(P::Busbar)).title("800 V", "~150 A"),
];
const R_Z: [ZoomData; 5] = [('a', "AC in, DC down the back", RA_B, RA_K), ('b', "power shelves", RB_B, RB_K), ('c', "kilowatts per rack", RC_B, RC_K), ('d', "800 V DC and the sidecar", RD_B, RD_K), ('e', "why so many amps", RE_B, RE_K)];
const R_S: [SecData; 9] = [(RA_B, RA_K), (RA_B, RA_K), (RA_B, RA_K), (RE_B, RE_K), (RB_B, RB_K), (RC_B, RC_K), (RD_B, RD_K), (RB_B, RB_K), (RE_B, RE_K)];
pwr_node!(R_ZOOMS, R_SECTIONS, R_Z, R_S);
pub static RACK_NODE: PwrNode = PwrNode { page: "RACK POWER", beats: R_B, keys: R_K, zooms: &R_ZOOMS, zoom_data: &R_Z, sections: &R_SECTIONS, section_data: &R_S };

// =================================================================== VRM

const V_B: &[Beat] = &[
    Beat::new("a GPU board", OVERVIEW_MS).note("The GPU package sits mid-board, ringed by its voltage regulator phases.", "A green board: the GPU and HBM, rows of inductors either side, a converter brick.").detail("One per GPU.", &["16 phases shown"]),
    Beat::new("50 V in, 12 V out", OVERVIEW_MS).note("A converter brick steps the busbar's 50 V down to 12 V.", "Yellow power enters the brick at the board edge.").detail("The intermediate bus.", &["50 V > 12 V"]),
    Beat::new("12 V to each phase", OVERVIEW_MS).note("12 V runs to every phase; each switches hundreds of thousands of times a second.", "Orange power fans out to the phases.").detail("Staggered switching.", &["MULTIPHASE"]),
    Beat::new("~0.8 V at over a thousand amps", OVERVIEW_MS).note("A 1,000-1,200 W GPU at about 0.8 V draws 1,250-1,500 A, shared across the phases.", "Hot red current streams from the inductors into the GPU.").detail("P = V x I.", &["~0.8 V", "1,250-1,500 A"]),
    Beat::new("every millimetre costs watts", OVERVIEW_MS).note("Loss goes with current squared; at 1,500 A even micro-ohms matter.", "Heat rises off the inductors and the GPU.").detail("I squared R.", &["0.1 mOhm = 225 W"]),
    Beat::new("vertical power: under the GPU", OVERVIEW_MS).note("Moving the regulators under the GPU shortens the path to millimetres.", "The phases slide beneath the board, under the package.").detail("Infineon, Crescendo (2026).", &["VERTICAL POWER"]),
    Beat::new("from the grid to the transistor", OVERVIEW_MS).note("345 kV to 0.8 V: six steps, each losing a little, each a supply chain.", "The board, power flowing.").detail("See GRID.", &["~400,000x step-down"]),
];
const V_K: &[PwrKey] = &[
    k!(BOARD, 2000.0, 0.50, 0.55, BD).labels(&[(P::Gpu, "GPU"), (P::Phase, "VRM phases"), (P::Ibc, "50 V > 12 V")]).notes(P::Phase, Some(P::Gpu)),
    k!([-500.0, 20.0, poly3d::PWR_BOARD_Z - 270.0], 1000.0, 0.60, 0.45, BD.spot(P::Ibc)).labels(&[(P::Ibc, "converter brick")]).notes(P::Ibc, None),
    k!([0.0, 20.0, poly3d::PWR_BOARD_Z], 1700.0, 0.40, 0.70, BD.spot(P::Phase)).labels(&[(P::Phase, "phases")]).notes(P::Phase, Some(P::Ibc)),
    k!([150.0, 20.0, poly3d::PWR_BOARD_Z], 1100.0, 0.55, 0.45, BD).labels(&[(P::Gpu, "~0.8 V"), (P::Phase, "1,000+ A")]).notes(P::Gpu, Some(P::Phase)),
    k!(BOARD, 1800.0, 0.45, 0.45, PwrState { heat: 1.0, ..BD }).labels(&[(P::Phase, "I2R heat")]).notes(P::Phase, Some(P::Gpu)),
    k!(BOARD, 1800.0, 0.55, -0.35, PwrState { vertical: 1.0, ..BD }).labels(&[(P::Phase, "under the GPU")]).notes(P::Phase, Some(P::Gpu)),
    k!(BOARD, 2200.0, 0.45, 0.50, BD).labels(&[(P::Gpu, "0.8 V"), (P::Board, "from 345 kV")]).notes(P::Gpu, None),
];
const VA_B: &[Beat] = &[
    Beat::new("50 V from the busbar", BEAT_MS).note("Into the board.", "Board edge.").detail("Rack bus.", &["50 V"]),
    Beat::new("the converter brick", BEAT_MS).note("Down to 12 V.", "The brick.").detail("Intermediate bus.", &["12 V"]),
    Beat::new("12 V across the board", BEAT_MS).note("To the phases.", "Power fans out.").detail("Then the VRM.", &["Bus"]),
];
const VA_K: &[PwrKey] = &[
    k!([-560.0, 20.0, poly3d::PWR_BOARD_Z - 270.0], 900.0, 0.60, 0.40, BD).title("50 V in", "from the busbar"),
    k!([-500.0, 20.0, poly3d::PWR_BOARD_Z - 270.0], 1000.0, 0.60, 0.45, BD.spot(P::Ibc)).title("converter", "50 V to 12 V"),
    k!([0.0, 20.0, poly3d::PWR_BOARD_Z], 1700.0, 0.40, 0.70, BD).title("12 V bus", "to the phases"),
];
const VB_B: &[Beat] = &[
    Beat::new("one phase: stage + inductor", BEAT_MS).note("Tens of amps each.", "One phase.").detail("Power stage.", &["Phase"]),
    Beat::new("sixteen phases", BEAT_MS).note("Staggered, ripples cancel.", "All phases.").detail("Multiphase.", &["16"]),
    Beat::new("together: 1,000+ A", BEAT_MS).note("Into the GPU.", "Current converges.").detail("Infineon, 2019.", &["1,000 A"]),
];
const VB_K: &[PwrKey] = &[
    k!([340.0, 20.0, poly3d::PWR_BOARD_Z + 150.0], 600.0, 0.55, 0.40, BD.spot(P::Phase)).title("one phase", "power stage + inductor"),
    k!([0.0, 20.0, poly3d::PWR_BOARD_Z], 1700.0, 0.40, 0.70, BD.spot(P::Phase)).title("16 phases", "staggered"),
    k!([150.0, 20.0, poly3d::PWR_BOARD_Z], 1100.0, 0.55, 0.45, BD).title("1,000+ A", "into the GPU"),
];
const VC_B: &[Beat] = &[
    Beat::new("1,200 W", BEAT_MS).note("A Blackwell GPU.", "The GPU.").detail("Electronic Design.", &["1,200 W"]),
    Beat::new("at 0.8 V", BEAT_MS).note("Core voltage.", "The die.").detail("0.75-0.85 V.", &["0.8 V"]),
    Beat::new("= 1,500 A", BEAT_MS).note("P = V x I.", "Hot current.").detail("Physics.", &["1,500 A"]),
];
const VC_K: &[PwrKey] = &[
    k!([0.0, 20.0, poly3d::PWR_BOARD_Z], 900.0, 0.45, 0.50, BD.spot(P::Gpu)).title("1,200 W", "Blackwell-class GPU"),
    k!([0.0, 20.0, poly3d::PWR_BOARD_Z], 700.0, 0.55, 0.55, PwrState { heat: 0.5, ..BD }.spot(P::Gpu)).title("0.8 V", "core voltage"),
    k!([150.0, 20.0, poly3d::PWR_BOARD_Z], 1100.0, 0.55, 0.45, PwrState { heat: 0.8, ..BD }).title("1,500 A", "P = V x I"),
];
const VD_B: &[Beat] = &[
    Beat::new("current squared", BEAT_MS).note("Double current, four times loss.", "Heat.").detail("I squared R.", &["I2R"]),
    Beat::new("0.1 milliohm = 225 W", BEAT_MS).note("At 1,500 A.", "Hot inductors.").detail("Every mm counts.", &["225 W"]),
    Beat::new("shorten the path", BEAT_MS).note("Regulators closer to the chip.", "Phases move.").detail("Vertical.", &["Shorter"]),
];
const VD_K: &[PwrKey] = &[
    k!(BOARD, 1800.0, 0.45, 0.45, PwrState { heat: 0.6, ..BD }).title("I squared R", "loss rises with current squared"),
    k!(BOARD, 1800.0, 0.45, 0.45, PwrState { heat: 1.0, ..BD }.spot(P::Phase)).title("225 W", "in 0.1 milliohm at 1,500 A"),
    k!(BOARD, 1800.0, 0.55, 0.20, PwrState { vertical: 0.5, ..BD }).title("shorter", "regulators move closer"),
];
const VE_B: &[Beat] = &[
    Beat::new("lateral: beside the GPU", BEAT_MS).note("Current crosses the board.", "Phases beside.").detail("Today.", &["Lateral"]),
    Beat::new("moving under", BEAT_MS).note("Onto the board's back.", "Phases slide under.").detail("Vertical.", &["Moving"]),
    Beat::new("vertical: straight up", BEAT_MS).note("Millimetres to the chip.", "Phases beneath.").detail("2026 modules.", &["Vertical"]),
];
const VE_K: &[PwrKey] = &[
    k!(BOARD, 1800.0, 0.55, 0.30, BD).title("lateral", "beside the GPU"),
    k!(BOARD, 1800.0, 0.55, -0.10, PwrState { vertical: 0.5, ..BD }).title("moving", "to the back of the board"),
    k!(BOARD, 1800.0, 0.55, -0.35, PwrState { vertical: 1.0, ..BD }).title("vertical", "straight up into the GPU"),
];
const V_Z: [ZoomData; 5] = [('a', "50 V to 12 V", VA_B, VA_K), ('b', "multiphase", VB_B, VB_K), ('c', "why over a thousand amps", VC_B, VC_K), ('d', "I2R loss", VD_B, VD_K), ('e', "vertical power", VE_B, VE_K)];
const V_S: [SecData; 9] = [(VA_B, VA_K), (VB_B, VB_K), (VA_B, VA_K), (VC_B, VC_K), (VB_B, VB_K), (VD_B, VD_K), (VE_B, VE_K), (VB_B, VB_K), (VD_B, VD_K)];
pwr_node!(V_ZOOMS, V_SECTIONS, V_Z, V_S);
pub static VRM_NODE: PwrNode = PwrNode { page: "VRM", beats: V_B, keys: V_K, zooms: &V_ZOOMS, zoom_data: &V_Z, sections: &V_SECTIONS, section_data: &V_S };
