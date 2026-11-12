// MELT + PULL sections 1-9, drawn in 3D by pbr3d in the same shaded style as the overview
// (tools/pbr3d/src/shot_sec.rs). Each section is four beats (section 1 has five), each beat a
// 3D picture: the puller in time order, its physics, and the figures as bars and plates.

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time};
use pbr3d::Shot;

const MIN_W: u16 = 100;
const MIN_H: u16 = 30;
const BEAT_MS: u64 = 5200;

const SEC1_BEATS: &[Beat] = &[
    Beat::new(
        "poly chunks and dopant are loaded into the crucible",
        BEAT_MS,
    )
    .note(
        "The charge goes into the crucible: solid polysilicon chunks from POLYSILICON, with the dopant added alongside.",
        "Chunks ▪ dropping into the crucible, then · dopant dust settling above them.",
    )
    .detail(
        "The charge is where the rod starts. What goes in as poly and dopant is what the rod is made of.",
        &[
            "Charge is poly chunks from POLYSILICON plus dopant (section 1)",
            "LOAD is the first of six stages (section 1)",
            "The finished rod is the INGOT node (section 1)",
        ],
    ),
    Beat::new(
        "the charge melts into one liquid pool under argon, at about 1414 C",
        BEAT_MS,
    )
    .note(
        "Heat melts the chunks from the floor up into a single liquid pool. Argon fills the chamber above the melt.",
        "The liquid rising from the floor, the ▪ chunks melting away, and argon ° sweeping in across the top.",
    )
    .detail(
        "The melt is the source for the whole rod. Every later stage pulls from this one pool.",
        &[
            "MELT is about 1414 C, under argon (section 1)",
            "Poly and dopant go from solid chunks to one melt (section 1)",
            "MELT is the second stage, after LOAD (section 1)",
        ],
    ),
    Beat::new(
        "a seed is dipped into the melt and a thin neck is pulled, 2-4 mm across",
        BEAT_MS,
    )
    .note(
        "The seed comes down to touch the melt, then is pulled up to draw a thin neck out of the liquid.",
        "The seed lowering, * sparks at contact, then the neck growing up under the seed.",
    )
    .detail(
        "The neck is thin and comes before the shoulder, so the rod has a narrow start before it widens.",
        &[
            "SEED + NECK: a 2-4 mm neck (section 1)",
            "The neck is pulled before the shoulder (section 1)",
            "The seed is the top of the rod on the wire (section 1 diagram)",
        ],
    ),
    Beat::new(
        "the shoulder widens, then the body grows slowly to 300 mm",
        BEAT_MS,
    )
    .note(
        "Once the neck is set, the rod widens into a shoulder at its lower end, then the body grows at a steady, slow pace.",
        "The shoulder spreading out below the neck, then the body lengthening beneath it toward the melt.",
    )
    .detail(
        "The body is the part of the rod that carries the wafers. Growing it slowly keeps the diameter steady.",
        &[
            "SHOULDER: widen (section 1)",
            "BODY: 300 mm, slow (section 1)",
            "The body grows down from the shoulder to the melt (section 1 diagram)",
        ],
    ),
    Beat::new(
        "the tail tapers the end, and the rod is lifted clear of the melt to cool",
        BEAT_MS,
    )
    .note(
        "At the end the diameter is reduced into a tail. The rod is then lifted out of the melt so it can cool.",
        "The bottom of the rod narrowing to a point, and a gap opening between the rod and the melt.",
    )
    .detail(
        "The tail is the last stage. The cooled rod is the INGOT node that the rest of the chain works from.",
        &[
            "TAIL: taper, cool (section 1)",
            "TAIL is the sixth and last stage (section 1)",
            "The finished rod is the INGOT node (section 1)",
        ],
    ),
];
const SEC2_BEATS: &[Beat] = &[
    Beat::new(
        "a water-cooled chamber holds argon near 2500 Pa around the crucible and melt",
        BEAT_MS,
    )
    .note(
        "The puller is a sealed, water-cooled steel chamber filled with argon at about 2500 Pa (COMSOL model). The quartz crucible holds the melt inside a graphite cup, and the seed hangs parked above it.",
        "Argon ° and · drifting down the left wall of the chamber, the seed parked at the top, and the ≈ melt in the crucible.",
    )
    .detail(
        "The chamber sets the gas and pressure the melt sees. Argon is the carrier that takes SiO and CO away from the melt surface.",
        &[
            "PULL CHAMBER: water-cooled steel, argon at ~2500 Pa (COMSOL model)",
            "Argon in at the top, down past the crystal, out at the bottom (page text)",
            "Pull shaft rotates and lifts the oriented seed crystal (page text)",
        ],
    ),
    Beat::new(
        "the pull shaft lowers a seed, then the neck, shoulder and body form as it lifts",
        BEAT_MS,
    )
    .note(
        "The seed is lowered onto the melt, then the shaft lifts. The dash neck, the shoulder and the body form in turn, and the crystal and crucible turn in opposite senses.",
        "The shaft tip rising as the crystal grows upward in stages, with its ▓▒ stripes shifting as it turns.",
    )
    .detail(
        "The crystal is grown by lifting it out of the melt. Each stage depends on the one below it, so a failed neck ends the whole pull.",
        &[
            "Neck 2-4 mm; dislocations grow out of it (page text)",
            "Shoulder widens to 300 mm; body up to about 2 m (page text)",
            "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
        ],
    ),
    Beat::new(
        "the crucible rises as the melt level drops, so the solid-melt interface stays at 1414 C",
        BEAT_MS,
    )
    .note(
        "As silicon freezes out, the melt level falls. The crucible is lifted on its shaft, which keeps the solid-melt interface at the same place.",
        "The melt surface row holding still while the crucible walls and floor move up two rows, with ≈ melt draining from the bottom.",
    )
    .detail(
        "A fixed interface keeps the freezing front flat, which keeps growth stable. The temperature at the interface sets where the crystal freezes.",
        &[
            "Solid-melt interface at 1414 C (page text, COMSOL model)",
            "Crucible lifted as the melt level drops so the interface stays put (page text)",
            "Quartz crucible holds the melt; graphite crucible surrounds it (page text)",
        ],
    ),
    Beat::new(
        "the heater and heat shield set the heat; argon carries SiO and CO out the base",
        BEAT_MS,
    )
    .note(
        "The graphite heater and its felt wrap the crucible, and a heat shield sits above the melt around the crystal. Argon sweeps down past the crystal and out the bottom, taking SiO and CO with it.",
        "The heater ▒ glowing, the ║ shield around the crystal, argon ° sweeping down the wall, and * SiO rising from the melt.",
    )
    .detail(
        "The hot zone sets the temperature the crystal sees, and the argon path decides what leaves the melt surface.",
        &[
            "Graphite heater around the crucible: 310 kW in the COMSOL model (page text)",
            "Graphite felt insulation outside the heater (page text)",
            "Heat shield above the melt around the crystal (page text)",
        ],
    ),
];
const SEC3_BEATS: &[Beat] = &[
    Beat::new(
        "growth: the seed touches the melt at its freezing point, and atoms attach in its orientation",
        BEAT_MS,
    )
    .note(
        "The seed is lowered until it touches the melt at the freezing point. Atoms attach at the solid-liquid front, in the same orientation as the seed, so pulling up extends one crystal.",
        "The seed coming down, then ▪ atoms at the front adding ▓ rows one at a time beneath it.",
    )
    .detail(
        "Matching the seed's orientation is what makes one single crystal instead of many grains.",
        &[
            "Melting point 1414 C in the COMSOL model",
            "1425 C on Wikipedia for semiconductor grade; sources differ by a few degrees",
            "Atoms attach in the seed's orientation (page text)",
        ],
    ),
    Beat::new(
        "mass flow: pull rate x cross-section x density is the silicon frozen per hour",
        BEAT_MS,
    )
    .note(
        "A 300 mm body frozen at a steady pull rate adds one slice per minute. The slice's volume is the cross-section times the pull rate, and its mass follows from the density.",
        "The body rising slice by slice, with a ═ band at the front; the rate label changes from 1.0 to 1.6 mm/min.",
    )
    .detail(
        "The pull rate sets how fast the crystal, and so the yield, comes out. The same arithmetic shows why faster pulls are worth the risk.",
        &[
            "300 mm body, 1.0 mm/min gives about 9.9 kg/h (computed on page)",
            "1.6 mm/min gives about 15.8 kg/h (computed on page)",
            "Density 2.33 g/cm3 is textbook",
        ],
    ),
    Beat::new(
        "oxygen: the quartz crucible dissolves into SiO, and some oxygen freezes into the crystal",
        BEAT_MS,
    )
    .note(
        "The melt dissolves the quartz wall, making SiO. Most of it evaporates, but some oxygen freezes into the crystal. Crucible rotation, melt depth, pull speed and magnetic fields tune how much.",
        "The crucible wall thinning to ░, * SiO rising from the wall, and · oxygen specks appearing in the crystal.",
    )
    .detail(
        "Oxygen is the main impurity the rotation and magnetic field are used to control. Too much makes the wafer brittle.",
        &[
            "SiO2 + Si to 2SiO; most SiO evaporates (textbook, unsourced)",
            "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
            "Rotation, melt depth, pull speed and magnetic fields tune oxygen (page text)",
        ],
    ),
    Beat::new(
        "segregation: the solute prefers the liquid, so the melt gets richer and the tail more doped",
        BEAT_MS,
    )
    .note(
        "Dopant such as boron or phosphorus prefers the liquid over the solid. As the crystal freezes out, the dopant stays behind, so the melt gets richer and each new slice carries more.",
        "The crystal shading from ░ at the head to ▓ at the tail, with · specks thickening in the melt below.",
    )
    .detail(
        "Segregation is why the tail of a crystal is the most doped and the most contaminated part.",
        &[
            "Boron or phosphorus is added to the melt (page text)",
            "The tail is more doped than the head (textbook, unsourced)",
            "The tail is cropped off in the INGOT step (page text)",
        ],
    ),
];
const SEC4_BEATS: &[Beat] = &[
    Beat::new(
        "the melt sits near 1414 C; the model's gradient along the rod runs 500 down to 100 C per metre",
        BEAT_MS,
    )
    .note(
        "The simulation puts the melt near 1414 C and the contact between 1403 and 1407.5 C. Along the rod the axial gradient falls from 500 to 100 C per metre. These are model outputs, not measurements.",
        "The rod shaded from ▓ at the melt to ░ at the top, with three labels appearing in turn.",
    )
    .detail(
        "The gradient is the model's input for stress and defect density, so these numbers are what the hot zone is designed around.",
        &[
            "Melt ~1414 C (COMSOL); contact 1403-1407.5 C in the model",
            "Axial gradient 500 down to 100 C per metre (model)",
            "Model reaches steady contact temperature after ~400 minutes",
        ],
    ),
    Beat::new(
        "furnace settings: argon at 100 L/min and 2500 Pa, a 310 kW heater, and counter-rotation",
        BEAT_MS,
    )
    .note(
        "The model's operating point: argon flow and furnace pressure, heater power, and crucible and crystal rotation. The page marks all of these as model values, not vendor specs.",
        "Three rows on the right filling in turn. The bars only reveal the rows; they are not a scale.",
    )
    .detail(
        "These are the knobs the model sets. Argon carries SiO and CO out of the chamber, and rotation drives the melt flow.",
        &[
            "Argon 100 L/min at 2500 Pa in the COMSOL model (model, not a vendor spec)",
            "Graphite heater at 310 kW (model)",
            "Crucible 5 rpm, crystal -5 rpm (model)",
        ],
    ),
    Beat::new(
        "a 300 mm wafer needs a 300 mm-plus body; the body can reach 2 m and several hundred kg",
        BEAT_MS,
    )
    .note(
        "The body has to be wider than the wafer and long enough to make a full ingot. The page lists 450 mm as a planned step that was stopped. Length and mass grow with the body.",
        "The rod growing to full height, a dotted 450 mm outline appearing beside it, and the 2 m label at the top.",
    )
    .detail(
        "Diameter and length set the mass, and the neck has to hold that mass. This is why the neck limit matters at this size.",
        &[
            "300 mm wafers need a 300 mm+ body (page text)",
            "450 mm was planned for 2018 and stopped in 2016 (page text)",
            "Why it stopped (general industry knowledge, not on the page): 2.25x the wafer area needs new tools at almost every step, and the market did not need the extra capacity",
            "Up to 2 m long and several hundred kg (Wikipedia)",
        ],
    ),
    Beat::new(
        "a 1.6 mm/min simulated pull shifts the interface 33 mm; the model settles after about 400 minutes",
        BEAT_MS,
    )
    .note(
        "The 2023 study simulated a 300 mm pull at 1.6 mm/min. That moves the interface 33 mm and changes growth time and power. The model needs about 400 minutes to reach a steady contact temperature.",
        "The timeline marker running to 400 minutes, and the readout rows appearing in turn.",
    )
    .detail(
        "Pull speed trades growth time against power and interface position. The study was aimed at photovoltaic silicon, so these are not microelectronics figures.",
        &[
            "1.6 mm/min simulated: interface shifts 33 mm (2023 study)",
            "Growth time -46.4%, power -4.97% at that rate (2023 study)",
            "Steady contact temperature after ~400 minutes (model)",
        ],
    ),
];
const SEC5_BEATS: &[Beat] = &[
    Beat::new(
        "the dash neck is pulled at up to 6.0 mm/min, the fastest figure in this section",
        BEAT_MS,
    )
    .note(
        "The thin dash neck is pulled up at its maximum rate. The bar is drawn to scale, with 6.0 mm/min as the full width.",
        "The top bar growing across the scale to its full width, with 6.0 beside it.",
    )
    .detail(
        "The speed is the point of the neck: a fast pull carries dislocations out through the surface before the body starts.",
        &[
            "Dash neck max 6.0 mm/min (US 6,866,713)",
            "The neck is pulled fast so dislocations exit the surface (section text)",
            "Dash-necked crystals are limited to about 100 kg (US 6,866,713)",
        ],
    ),
    Beat::new(
        "the 300 mm body in a 2023 simulation is pulled at 1.6 mm/min, far slower than the neck",
        BEAT_MS,
    )
    .note(
        "The body rate for a 300 mm crystal comes from a simulation. The bar is much shorter than the neck bar on the same scale.",
        "The second bar growing to 1.6, labelled as a simulation rather than a measured pull.",
    )
    .detail(
        "The body is grown slowly so the freezing interface stays flat and stable. Faster pulls push it convex or concave.",
        &[
            "300 mm simulated pull rate 1.6 mm/min (2023 simulation)",
            "The 2023 study was aimed at photovoltaic silicon (page text)",
            "Pull rates faster than 1.0-1.6 mm/min push the interface convex or concave (page text)",
        ],
    ),
    Beat::new(
        "the neck example at 2.4 mm/min and the dash-free neck at 0.5 mm/min or less fill out the range",
        BEAT_MS,
    )
    .note(
        "Two more bars grow in. The dash-free bar is marked with <= because 0.5 is a ceiling, not a measured value.",
        "The third bar at 2.4, and the fourth bar stopping short at <= 0.5.",
    )
    .detail(
        "The figures span more than a tenfold range, from 0.5 to 6.0 mm/min, so the neck method is a choice rather than one fixed rate.",
        &[
            "Neck example 2.4 mm/min (US 5,578,284)",
            "Dash-free neck at 0.5 mm/min or less (US 7,179,330)",
            "Figures come from patents and one simulation, not a survey (section text)",
        ],
    ),
    Beat::new(
        "the neck runs fast to purge dislocations; the body runs slow to keep the interface flat",
        BEAT_MS,
    )
    .note(
        "The two parts of the pull run at different speeds for different jobs. Fast particles stream along the neck track, slow ones along the body track.",
        "Quick ▪ moving along the neck track, and slow • moving along the body track below it.",
    )
    .detail(
        "Each speed matches its job: the neck trades speed for purging dislocations, and the body trades speed for a flat, stable interface.",
        &[
            "The neck runs fast to purge dislocations (section text)",
            "The body runs slow to keep the interface flat and stable (section text)",
            "Dash neck max 6.0 mm/min against 1.6 mm/min simulated for 300 mm (section text)",
        ],
    ),
];
const SEC6_BEATS: &[Beat] = &[
    Beat::new(
        "Report Prime estimate: Shin-Etsu leads 300 mm wafer share with 26.7%, SUMCO next at 25.0%",
        BEAT_MS,
    )
    .note(
        "Five wafer makers, each with its share of the 300 mm market in 2024 according to one market-research estimate. The bars grow from the same origin, so their lengths compare directly.",
        "The five bars growing from the left, each with its percentage at the end, and the estimate label on the top row.",
    )
    .detail(
        "The shares come from a single market-research estimate that the source itself rates as low reliability. The order is indicative; do not quote the numbers as measured.",
        &[
            "Shin-Etsu 26.7%, SUMCO 25.0%, GlobalWafers 15.0% (Report Prime, page text)",
            "Siltronic 11.7%, SK Siltron 9.2% (Report Prime, page text)",
            "Report Prime estimate, low reliability (page text)",
        ],
    ),
    Beat::new(
        "the top two hold about 51.7%, but the five listed shares add to 87.6%, not the 77% quoted",
        BEAT_MS,
    )
    .note(
        "The two largest makers are shaded. Their combined share is the top-two figure. The page also gives a top-five figure, which does not match the five bars it sits under.",
        "The top two bars shaded ▓, and the two summary lines under the axis of bars.",
    )
    .detail(
        "The section's own top-five number does not agree with its own list. Use the listed shares and check the source before quoting a concentration figure.",
        &[
            "Top two: 26.7 + 25.0 = 51.7% (page text)",
            "Listed five: 26.7 + 25.0 + 15.0 + 11.7 + 9.2 = 87.6%",
            "The page gives the top five as about 77% (page text)",
        ],
    ),
    Beat::new(
        "other sources disagree: Omdia, Envisioning and 2023 vendor blurbs give different concentrations",
        BEAT_MS,
    )
    .note(
        "Each marker is a figure from another source, placed on a 0-100% scale. Single points are one figure; bars are a range between two cited figures. The spread is the point: these sources do not agree.",
        "Four rows appearing one at a time on a 0-100% axis, with the labels at the right of each marker.",
    )
    .detail(
        "The sources differ in year, market size and method, so none of these numbers can be compared directly with the Report Prime bars.",
        &[
            "Omdia 2020: top five 94% of an $11.2B market (page text)",
            "Shin-Etsu + SUMCO above 55% (2020) or about 53% (Envisioning) (page text)",
            "Top five 82-85% in 2023 (vendor blurbs, page text)",
        ],
    ),
    Beat::new(
        "each maker grows its own crystals in-house, so the puller is the capital item",
        BEAT_MS,
    )
    .note(
        "Each company gets its own puller box, and its crystal grows up from the melt. The crystal fills in as the beat plays, showing that ownership of the crystal means owning the pullers.",
        "Five puller boxes, each with a ▓ crystal growing up from its base, and the capital-item line below.",
    )
    .detail(
        "Share of wafer revenue does not show how many pullers a maker runs or what they cost. Those figures are not in this section, so none are shown.",
        &[
            "Wafer makers grow their own crystals in-house (page text)",
            "The puller is the capital item (page text)",
            "Puller cost and count are not given in the section (gap)",
        ],
    ),
];
const SEC7_BEATS: &[Beat] = &[
    Beat::new(
        "the quartz crucible is consumed every pull, and its Spruce Pine supply can stop",
        BEAT_MS,
    )
    .note(
        "The crucible is worn away by the melt on every pull, so each pull needs a new one. High-purity quartz comes mostly from Spruce Pine, NC. If that supply stops, the pullers have nothing to hold the melt.",
        "The crucible wall eroding from the top as the pull runs, and the supply pipe from Spruce Pine going cold at the ╳ cut.",
    )
    .detail(
        "Quartz is the single consumable that every pull depends on. A supply outage idles the pullers even when the rest of the line works.",
        &[
            "Crucibles are consumed every pull (page text)",
            "High-purity quartz mostly from Spruce Pine, NC (page text, see SAND)",
            "A Spruce Pine outage idles pullers (page text)",
        ],
    ),
    Beat::new(
        "one dislocation anywhere in the body means the crystal is remelted",
        BEAT_MS,
    )
    .note(
        "A dislocation that survives into the body is a fault in the whole crystal, so the pull is ruined. The body drops back into the melt and the charge is melted again.",
        "The ▓ body with a / dislocation running through it, then the body sinking into the ≈ melt.",
    )
    .detail(
        "Yield is lost to a single defect. A large hot zone and a long cycle make each ruined pull more expensive to lose.",
        &[
            "A dislocation anywhere in the body means remelting (page text)",
            "Big hot zones and long cycles make a ruined pull expensive (page text)",
            "Cycle times are not sourced in this section",
        ],
    ),
    Beat::new(
        "oxygen and dopant uniformity across a 300 mm wafer is the hard control problem",
        BEAT_MS,
    )
    .note(
        "Across the diameter of a 300 mm crystal, the oxygen and dopant level varies from point to point. The varying level is shown as · low, + mid and * high. Crucible rotation is one control on this, and it is patented.",
        "The disc of wafer cells, with the scatter tightening as the control is applied, and the ↺ ↻ rotation labels.",
    )
    .detail(
        "Uniformity is the control that a 300 mm puller must hold. Crucible rotation is one of the levers, and it is covered by patents.",
        &[
            "Oxygen and dopant uniformity at 300 mm is the hard control problem (page text)",
            "Patents cover crucible rotation (page text)",
            "Oxygen is set by crucible rotation and melt depth (page text)",
        ],
    ),
    Beat::new(
        "demand is cyclical: SEMI's 2023 figures show wafer revenue and 300 mm shipments down",
        BEAT_MS,
    )
    .note(
        "The bars show SEMI's 2023 changes. Wafer revenue fell, and polished 300 mm shipments fell further, with epi 300 mm down less. Total area shipped fell the most. Each bar grows from the axis as the figure is read.",
        "Four bars growing to the right from the axis, each with its percent change at the end.",
    )
    .detail(
        "Demand swings give the pullers less work and pressure the margin on each pull. A fall in shipments is a risk to the whole chain.",
        &[
            "SEMI: 2023 silicon wafer revenue fell 10.9% to $12.3B (page text)",
            "Polished 300 mm shipments fell 13%; epi 300 mm fell 5% (page text)",
            "Total area 12,602 million sq in, down 14.3% (page text)",
        ],
    ),
];
const SEC8_BEATS: &[Beat] = &[
    Beat::new(
        "four listed wafer makers, each with its own exchange ticker",
        BEAT_MS,
    )
    .note(
        "The section lists four wafer makers with their tickers. The boxes appear in list order, so each name is read as it lands.",
        "Four boxes filling in, two per row, each with its ticker inside.",
    )
    .detail(
        "These tickers are the entry points for looking up the listed wafer makers. The section gives tickers only.",
        &[
            "Shin-Etsu Chemical 4063.T, SUMCO 3436.T (page text)",
            "GlobalWafers 6488.TWO, Siltronic SSG.DE, also WAF.DE (page text)",
            "No share, revenue or size figure appears in section 8 (page text)",
        ],
    ),
    Beat::new(
        "SK Siltron is not listed on its own: it is held by SK Inc",
        BEAT_MS,
    )
    .note(
        "SK Siltron appears inside the SK Inc box, which carries the listing (034730.KS). It is shown as a holding, not a separate ticker.",
        "A small SK Siltron box sliding into the SK Inc box, with the ticker on the parent.",
    )
    .detail(
        "The parent ticker is the one to look up for SK Siltron. Reading the section without this would suggest a missing listing.",
        &[
            "SK Siltron is held by SK Inc (034730.KS) (page text)",
            "The section gives no separate ticker for SK Siltron (page text)",
        ],
    ),
    Beat::new(
        "the puller makers are a separate list: PVA TePla and Ferrotec",
        BEAT_MS,
    )
    .note(
        "Pullers are the machines that grow the crystal. The section names two puller makers, and the crystal rises on its cable as they are read.",
        "A cable from the top of the frame, a crystal rising out of the melt, and two labels at its side.",
    )
    .detail(
        "Puller makers are kept apart from wafer makers in the section. A wafer maker and the puller it buys are different companies.",
        &[
            "Puller makers e.g. PVA TePla (TPL.DE) (page text)",
            "Ferrotec 6890.T is also named as a puller maker (page text)",
            "Puller makers are not in the wafer-maker list above (page text)",
        ],
    ),
    Beat::new(
        "the tickers and puller makers are general knowledge, not a fetched source",
        BEAT_MS,
    )
    .note(
        "The section closes by marking its own sourcing. All names are collected in one box, and a stamp flickers on to say they were not fetched.",
        "The six names in a box, and a flickering stamp that reads not from a fetched source.",
    )
    .detail(
        "The stamp is the only sourcing caveat for this section. Treat the tickers as a starting list to check, not as verified data.",
        &[
            "Tickers and puller makers are general knowledge (page text)",
            "Not from a fetched source (page text)",
            "The section's Sources heading is empty (page text)",
        ],
    ),
];
const SEC9_BEATS: &[Beat] = &[
    Beat::new(
        "model and simulation sources: the COMSOL furnace model and the 2023 pull-rate study",
        BEAT_MS,
    )
    .note(
        "Two cards cover the modelled numbers. [1] is COMSOL's thermal analysis of a Czochralski furnace; [4] is a journal study of a 300 mm pull-rate simulation.",
        "Cards [1] and [4] light up in turn, each one checked off once named.",
    )
    .detail(
        "Several figures on the page are tagged as model or study results, so they trace back to these two cards.",
        &[
            "[1] COMSOL, Thermal Analysis of a Czochralski Crystal Growth Furnace",
            "[4] 300 mm pull-rate simulation: Journal of Synthetic Crystals 52(4) 562 (2023)",
            "Model numbers on the page are tagged (model) (page text)",
        ],
    ),
    Beat::new(
        "patent sources: the neck rate and the 100 kg limit are named against patent texts",
        BEAT_MS,
    )
    .note(
        "Card [3] groups the patents cited for the dash neck: the neck pull rate and the roughly 100 kg limit on dash-necked crystals.",
        "Card [3] lights up, with the three patent numbers it lists.",
    )
    .detail(
        "The neck rate and the 100 kg limit both come from patent texts, so those are the claims to trace back to a patent.",
        &[
            "US 6,866,713: dash neck pulled to about 6 mm/min, limit about 100 kg",
            "US 5,578,284 is listed with it; it is cited for a slower neck method",
            "US 7,179,330 is listed with it; it is cited for the dash-free neck",
        ],
    ),
    Beat::new(
        "general reference: the Czochralski method and the wafer entry, both on Wikipedia",
        BEAT_MS,
    )
    .note(
        "Cards [2] and [8] are general reference: an encyclopedia entry on the Czochralski method and one on wafers.",
        "Cards [2] and [8] light up in turn, each one checked off once named.",
    )
    .detail(
        "The page cites Wikipedia for a few broad figures. Where the sources differ, the page says so.",
        &[
            "[2] Wikipedia, Czochralski method",
            "[8] Wikipedia, Wafer (electronics)",
            "Wikipedia is cited for 1425 C and about 1e18 oxygen per cm3 (page text)",
        ],
    ),
    Beat::new(
        "market sources: wafer shares, SEMI 2023 revenue and shipments, and Omdia 2020 shares",
        BEAT_MS,
    )
    .note(
        "Cards [5], [6] and [7] cover the market side: a wafer-share page, SEMI 2023 revenue and shipments, and Omdia 2020 shares via KED Global.",
        "Cards [5], [6] and [7] light up in turn, and the bar at the bottom fills to all eight.",
    )
    .detail(
        "These are market figures, not process figures. The years differ (2020 and 2023), so they should not be read as one period.",
        &[
            "[5] Wafer shares, reportprime",
            "[6] SEMI 2023 revenue and shipments, via a substack post",
            "[7] Omdia 2020 shares, via KED Global",
        ],
    ),
];

macro_rules! sec_scene_impl {
    ($name:ident, $beats:ident, $n:expr) => {
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
                Some(pbr3d::render_shot(
                    Shot::Sec($n),
                    t.beat,
                    t.local,
                    0.0,
                    0.0,
                    1.0,
                    w,
                    h,
                    px::BG,
                ))
            }
        }
    };
}

sec_scene_impl!(Sec1, SEC1_BEATS, 1);
sec_scene_impl!(Sec2, SEC2_BEATS, 2);
sec_scene_impl!(Sec3, SEC3_BEATS, 3);
sec_scene_impl!(Sec4, SEC4_BEATS, 4);
sec_scene_impl!(Sec5, SEC5_BEATS, 5);
sec_scene_impl!(Sec6, SEC6_BEATS, 6);
sec_scene_impl!(Sec7, SEC7_BEATS, 7);
sec_scene_impl!(Sec8, SEC8_BEATS, 8);
sec_scene_impl!(Sec9, SEC9_BEATS, 9);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(Sec1),
    || Box::new(Sec2),
    || Box::new(Sec3),
    || Box::new(Sec4),
    || Box::new(Sec5),
    || Box::new(Sec6),
    || Box::new(Sec7),
    || Box::new(Sec8),
    || Box::new(Sec9),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_section_has_its_beats() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, vec![5, 4, 4, 4, 4, 4, 4, 4, 4]);
    }

    #[test]
    fn every_section_draws_a_picture() {
        for (i, f) in SECTIONS.iter().enumerate() {
            let scene = f();
            let t = Time {
                beat: 0,
                local: 0.5,
                ms: 0,
                beat_start: 0,
            };
            let img = scene
                .pixels(&t, 160, 100)
                .unwrap_or_else(|| panic!("section {} has no picture", i + 1));
            let bg = px::BG;
            let drawn = img
                .pixels()
                .filter(|p| p.0[0] != bg[0] || p.0[1] != bg[1] || p.0[2] != bg[2])
                .count();
            assert!(
                drawn > 160 * 100 / 10,
                "section {} only {drawn} pixels off the background",
                i + 1
            );
        }
    }
}
