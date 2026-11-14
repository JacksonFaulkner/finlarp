// MELT + PULL sections 1-9 in the picture-and-panel template, from the Blender scenes in
// tools/pbr3d/blender/melt_sections.py. Section 1 is five beats, the rest four; section 9 is the
// sources page.

use super::super::blender::{page, Cell, BEAT_MS};
use crate::ui::anim::{Beat, Scene};

const SEC1: &[Beat] = &[
    Beat::new("LOAD: polysilicon chunks and dopant go into the quartz crucible", BEAT_MS)
        .note(
            "The charge is solid polysilicon chunks from POLYSILICON with the dopant added alongside. LOAD is the first of six stages.",
            "grey chunks dropping into the crucible with blue dopant specks among them",
        )
        .detail(
            "What goes in as poly and dopant is what the rod is made of.",
            &["Charge is poly chunks from POLYSILICON plus dopant (section 1)", "LOAD is the first of six stages (section 1)"],
        ),
    Beat::new("MELT: the charge melts into one pool at about 1414 C under argon", BEAT_MS)
        .note(
            "The heater melts the chunks into a single liquid pool while argon sweeps the chamber. Every later stage pulls from this pool.",
            "the heater glowing, the chunks shrinking as the orange melt rises, and argon running down past the shield",
        )
        .detail(
            "The melt is the source for the whole rod.",
            &["MELT is about 1414 C, under argon (section 1)", "Poly and dopant go from solid chunks to one melt (section 1)"],
        ),
    Beat::new("SEED + NECK: a seed is dipped into the melt and a 2-4 mm neck is pulled", BEAT_MS)
        .note(
            "The seed comes down to touch the melt, then rises and draws a thin neck out of the liquid.",
            "the seed lowering to the surface, then a thin bright neck growing under it as it rises",
        )
        .detail(
            "The rod has a narrow start before it widens.",
            &["SEED + NECK: a 2-4 mm neck (section 1)", "The neck is pulled before the shoulder (section 1)"],
        ),
    Beat::new("SHOULDER + BODY: the crystal widens, then the 300 mm body grows slowly", BEAT_MS)
        .note(
            "Once the neck is set the crystal widens into a shoulder, then the body grows at a slow, steady pace while the crucible rises with the falling melt.",
            "the cone spreading on the melt, then the body lengthening up into the pull chamber",
        )
        .detail(
            "The body is the part that carries the wafers. Growing it slowly keeps the diameter steady.",
            &["SHOULDER: widen (section 1)", "BODY: 300 mm, slow (section 1)"],
        ),
    Beat::new("TAIL: the end tapers and the rod is lifted clear of the melt to cool", BEAT_MS)
        .note(
            "At the end the diameter is reduced into a tail, and the rod is lifted out of the melt so it can cool. The cooled rod is the INGOT node.",
            "the bottom of the rod narrowing to a cone, then a gap opening between the rod and the melt",
        )
        .detail(
            "The tail is the last stage; the rest of the chain works from the rod.",
            &["TAIL: taper, cool (section 1)", "The finished rod is the INGOT node (section 1)"],
        ),
];

const SEC2: &[Beat] = &[
    Beat::new("a water-cooled steel chamber holds argon near 2500 Pa around the crucible and melt", BEAT_MS)
        .note(
            "The puller is a sealed, water-cooled steel chamber with a tall pull chamber above. Argon at about 2500 Pa flows down through it. The seed hangs parked above the melt.",
            "argon running down the pull chamber, the seed parked above the shield, and the melt in the crucible",
        )
        .detail(
            "The chamber sets the gas and pressure the melt sees. Argon carries SiO and CO away from the melt surface.",
            &[
                "Pull chamber: water-cooled steel, argon at about 2500 Pa (COMSOL model)",
                "Argon in at the top, down past the crystal, out at the bottom (page text)",
                "Pull shaft rotates and lifts the oriented seed (page text)",
            ],
        ),
    Beat::new("the seed is lowered, then neck, shoulder and body form as it lifts, both parts turning", BEAT_MS)
        .note(
            "The seed is lowered onto the melt, then lifted. The dash neck, the shoulder and the body form in turn, and the crystal and crucible turn in opposite directions.",
            "the crystal forming under the seed, the dark stripe on the body turning one way and the gold marker on the crucible rim the other",
        )
        .detail(
            "Each stage depends on the one below it, so a failed neck ends the whole pull.",
            &[
                "Neck 2-4 mm; dislocations grow out of it (page text)",
                "Shoulder widens to 300 mm; body up to about 2 m (page text)",
                "Crystal 5 rpm, crucible -5 rpm (COMSOL example)",
            ],
        ),
    Beat::new("the crucible rises as the melt level drops, so the interface stays at 1414 C", BEAT_MS)
        .note(
            "As silicon freezes out, the melt gets shallower. The crucible is lifted on its shaft so the solid-melt interface stays at the same height.",
            "the body growing up into the pull chamber while the crucible creeps up and the melt surface holds still",
        )
        .detail(
            "A fixed interface keeps the freezing front flat, which keeps growth stable.",
            &[
                "Solid-melt interface at 1414 C (page text, COMSOL model)",
                "Crucible lifted as the melt level drops (page text)",
                "Quartz crucible inside a graphite crucible (page text)",
            ],
        ),
    Beat::new("the heater and heat shield set the heat; argon carries SiO and CO out of the base", BEAT_MS)
        .note(
            "The graphite heater and its felt wrap the crucible, and a heat shield sits above the melt around the crystal. Argon sweeps down past the crystal and out of the bottom, taking SiO with it.",
            "the glowing heater, the grey shield round the crystal, argon running down and white SiO leaving the melt surface",
        )
        .detail(
            "The hot zone sets the temperature the crystal sees, and the argon path decides what leaves the melt surface.",
            &[
                "Graphite heater: 310 kW in the COMSOL model (page text)",
                "Graphite felt insulation outside the heater (page text)",
                "Heat shield above the melt around the crystal (page text)",
            ],
        ),
];

const SEC3: &[Beat] = &[
    Beat::new("growth: atoms attach at the freezing front in the seed's orientation", BEAT_MS)
        .note(
            "The seed meets the melt at its freezing point. Atoms from the liquid attach at the solid-liquid front in the same orientation as the crystal above, so pulling up extends one crystal.",
            "loose atoms from the orange liquid flying up into the next row of the grey lattice, row after row, as the lattice is pulled up",
        )
        .detail(
            "Matching the seed's orientation is what makes one single crystal instead of many grains.",
            &[
                "Melting point 1414 C in the COMSOL model",
                "1425 C on Wikipedia for semiconductor grade; sources differ by a few degrees",
                "Atoms attach in the seed's orientation (page text)",
            ],
        ),
    Beat::new("mass flow: pull rate x cross-section x density is the silicon frozen per hour", BEAT_MS)
        .note(
            "A 300 mm body adds one slice for each millimetre pulled. The slice's volume is the cross-section times the pull rate, and its mass follows from the density.",
            "slices freezing on one by one, each flashing gold as it forms, faster in the second half",
        )
        .detail(
            "The pull rate sets how fast silicon comes out, which is why faster pulls are worth the risk.",
            &[
                "300 mm body at 1.0 mm/min: about 9.9 kg/h (computed on page)",
                "1.6 mm/min: about 15.8 kg/h (computed on page)",
                "Density 2.33 g/cm3 is textbook",
            ],
        ),
    Beat::new("oxygen: the quartz crucible dissolves into SiO, and some oxygen freezes into the crystal", BEAT_MS)
        .note(
            "The melt dissolves the quartz wall, making SiO. Most of it evaporates, but some oxygen freezes into the crystal. Crucible rotation, melt depth, pull speed and magnetic fields tune how much.",
            "white bubbles leaving the crucible wall and rising out, then red specks appearing on the crystal",
        )
        .detail(
            "Oxygen is the main impurity the rotation and field are used to control. Too much makes the wafer brittle.",
            &[
                "SiO2 + Si gives 2SiO; most SiO evaporates (textbook, unsourced)",
                "Crystal ends up near 1e18 oxygen atoms per cm3 (Wikipedia)",
                "Rotation, melt depth, pull speed and fields tune oxygen (page text)",
            ],
        ),
    Beat::new("segregation: dopant prefers the liquid, so the melt gets richer and the tail more doped", BEAT_MS)
        .note(
            "Boron or phosphorus prefers the liquid over the solid. As the crystal freezes out the dopant stays behind, so the melt gets richer and each new slice carries more.",
            "bands freezing on from pale at the head to dark blue at the tail, while blue dopant specks multiply in the melt",
        )
        .detail(
            "Segregation is why the tail is the most doped and most contaminated part of the crystal.",
            &[
                "Boron or phosphorus is added to the melt (page text)",
                "The tail is more doped than the head (textbook, unsourced)",
                "The tail is cropped off in the INGOT step (page text)",
            ],
        ),
];

const SEC4: &[Beat] = &[
    Beat::new("the melt sits near 1414 C; the model's gradient up the rod runs 500 down to 100 C per metre", BEAT_MS)
        .note(
            "The simulation puts the melt near 1414 C and the contact between 1403 and 1407.5 C. Up the rod the axial gradient falls from 500 to 100 C per metre. These are model outputs, not measurements.",
            "the rod's bands appearing from the melt up, orange at the bottom fading to violet at the top",
        )
        .detail(
            "The gradient feeds the model's stress and defect estimates, so the hot zone is designed around these numbers.",
            &[
                "Melt about 1414 C (COMSOL); contact 1403-1407.5 C in the model",
                "Axial gradient 500 down to 100 C per metre (model)",
                "Model reaches steady contact temperature after about 400 minutes",
            ],
        ),
    Beat::new("furnace settings: argon at 100 L/min and 2500 Pa, a 310 kW heater, and counter-rotation", BEAT_MS)
        .note(
            "The model's operating point: argon flow, furnace pressure, heater power, and crystal and crucible rotation. The page marks all of these as model values, not vendor specs.",
            "four plates rising in turn, each with its value; their heights are not a scale",
        )
        .detail(
            "These are the knobs the model sets. Argon carries SiO and CO out, and rotation drives the melt flow.",
            &[
                "Argon 100 L/min at 2500 Pa (COMSOL model, not a vendor spec)",
                "Graphite heater at 310 kW (model)",
                "Crucible 5 rpm, crystal -5 rpm (model)",
            ],
        ),
    Beat::new("a 300 mm wafer needs a 300 mm-plus body, up to 2 m long and several hundred kg", BEAT_MS)
        .note(
            "The body has to be wider than the wafer and long enough to make a full ingot. 450 mm was a planned step that was stopped.",
            "the 300 mm body rising to 2 m beside a pale 450 mm outline",
        )
        .detail(
            "Diameter and length set the mass, and the neck has to hold that mass.",
            &[
                "300 mm wafers need a 300 mm+ body (page text)",
                "450 mm was planned for 2018 and stopped in 2016 (page text)",
                "Up to 2 m long and several hundred kg (Wikipedia)",
            ],
        ),
    Beat::new("a 1.6 mm/min simulated pull shifts the interface 33 mm; the model settles after about 400 minutes", BEAT_MS)
        .note(
            "The 2023 study simulated a 300 mm pull at 1.6 mm/min, which moved the interface 33 mm and changed growth time and power. The model needs about 400 minutes to reach a steady contact temperature.",
            "the gold marker running along the timeline to 400 minutes, with the study's figures above it",
        )
        .detail(
            "Pull speed trades growth time against power and interface position. The study was aimed at photovoltaic silicon.",
            &[
                "1.6 mm/min simulated: interface shifts 33 mm (2023 study)",
                "Growth time -46.4%, power -4.97% at that rate (2023 study)",
                "Steady contact temperature after about 400 minutes (model)",
            ],
        ),
];

const SEC5: &[Beat] = &[
    Beat::new("the dash neck is pulled at up to 6.0 mm/min, the fastest figure on the page", BEAT_MS)
        .note(
            "The thin dash neck is pulled at its maximum rate. All four bars share one scale.",
            "the top gold bar growing out to 6.0",
        )
        .detail(
            "Speed is the point of the neck: a fast pull carries dislocations out before the body starts.",
            &["Dash neck max 6.0 mm/min (US 6,866,713)", "Dash-necked crystals are limited to about 100 kg (US 6,866,713)"],
        ),
    Beat::new("the 300 mm body in a 2023 simulation is pulled at 1.6 mm/min, far slower than the neck", BEAT_MS)
        .note(
            "The body rate for a 300 mm crystal comes from a simulation, not a measured pull. Its bar is much shorter on the same scale.",
            "the blue bar growing to 1.6 under the long neck bar",
        )
        .detail(
            "The body is grown slowly so the freezing interface stays flat and stable.",
            &["300 mm simulated pull rate 1.6 mm/min (2023 simulation)", "The study was aimed at photovoltaic silicon (page text)"],
        ),
    Beat::new("a neck example at 2.4 mm/min and the dash-free neck at 0.5 mm/min or less fill out the range", BEAT_MS)
        .note(
            "Two more bars grow in. The dash-free figure is a ceiling (<= 0.5), not a measured value.",
            "the third bar stopping at 2.4 and the short grey bar at 0.5",
        )
        .detail(
            "The figures span more than tenfold, from 0.5 to 6.0 mm/min, so the neck method is a choice.",
            &["Neck example 2.4 mm/min (US 5,578,284)", "Dash-free neck at 0.5 mm/min or less (US 7,179,330)"],
        ),
    Beat::new("the neck runs fast to purge dislocations; the body runs slow to keep the interface flat", BEAT_MS)
        .note(
            "The two parts of the pull run at different speeds for different jobs.",
            "bright packets racing along the neck bar and pale ones crawling along the body bar",
        )
        .detail(
            "Each speed matches its job: purging dislocations for the neck, a flat stable interface for the body.",
            &["Neck runs fast to purge dislocations (page text)", "Body runs slow to keep the interface flat (page text)"],
        ),
];

const SEC6: &[Beat] = &[
    Beat::new("Report Prime estimate: Shin-Etsu leads 300 mm wafer share at 26.7%, SUMCO next at 25.0%", BEAT_MS)
        .note(
            "Five wafer makers with their 2024 share of the 300 mm market, from one market-research estimate. The bars share one scale.",
            "five blue bars growing from the plinth, each with its share",
        )
        .detail(
            "The source rates itself low reliability; the order is indicative, not measured.",
            &[
                "Shin-Etsu 26.7%, SUMCO 25.0%, GlobalWafers 15.0% (Report Prime)",
                "Siltronic 11.7%, SK Siltron 9.2% (Report Prime)",
                "Report Prime estimate, low reliability (page text)",
            ],
        ),
    Beat::new("the top two hold about 51.7%, but the five listed shares add to 87.6%, not the 77% quoted", BEAT_MS)
        .note(
            "The two largest makers turn gold. The page's top-five figure does not match the five bars it sits under.",
            "the Shin-Etsu and SUMCO bars turning gold, and the two summary tags",
        )
        .detail(
            "Use the listed shares and check the source before quoting a concentration figure.",
            &["Top two: 26.7 + 25.0 = 51.7%", "Listed five: 87.6%; the page says about 77% (page text)"],
        ),
    Beat::new("other sources disagree: Omdia, Envisioning and 2023 vendor blurbs give different concentrations", BEAT_MS)
        .note(
            "Each marker is another source's figure on a 0-100% axis. A ball is one figure; a bar is a range between two.",
            "three gold markers appearing on stems above the 0-100% axis",
        )
        .detail(
            "The sources differ in year, market and method, so none compares directly with the Report Prime bars.",
            &[
                "Omdia 2020: top five 94% of an $11.2B market (page text)",
                "Shin-Etsu + SUMCO above 55% (2020) or about 53% (Envisioning)",
                "Top five 82-85% in 2023 (vendor blurbs, page text)",
            ],
        ),
    Beat::new("each maker grows its own crystals in-house, so the puller is the capital item", BEAT_MS)
        .note(
            "Each company gets a puller, and a crystal grows in each one. Owning the crystal means owning the pullers.",
            "five dark cabinets, a grey crystal rising out of the melt in each",
        )
        .detail(
            "Puller counts and costs are not in the section, so none are shown.",
            &["Wafer makers grow their own crystals in-house (page text)", "The puller is the capital item (page text)"],
        ),
];

const SEC7: &[Beat] = &[
    Beat::new("the quartz crucible is consumed every pull, and its Spruce Pine supply can stop", BEAT_MS)
        .note(
            "The melt wears the crucible away on every pull, so each pull needs a new one. High-purity quartz comes mostly from Spruce Pine, NC.",
            "the inner wall of the crucible wearing down, quartz flowing from the Spruce Pine block, then a red X on the line",
        )
        .detail(
            "Quartz is the consumable every pull depends on. A supply outage idles the pullers.",
            &[
                "Crucibles are consumed every pull (page text)",
                "High-purity quartz mostly from Spruce Pine, NC (page text, see SAND)",
                "A Spruce Pine outage idles pullers (page text)",
            ],
        ),
    Beat::new("one dislocation anywhere in the body means the crystal is remelted", BEAT_MS)
        .note(
            "A dislocation that survives into the body ruins the crystal. The body is lowered back into the melt and the pull starts again.",
            "a red line down the body, then the body sinking back into the melt",
        )
        .detail(
            "Big hot zones and long cycles make each ruined pull expensive.",
            &["A dislocation anywhere in the body means remelting (page text)", "Cycle times are not sourced in this section"],
        ),
    Beat::new("oxygen and dopant uniformity across a 300 mm wafer is the hard control problem", BEAT_MS)
        .note(
            "Across a 300 mm wafer the oxygen and dopant level varies from point to point. Crucible rotation is one control, and it is patented.",
            "a wafer of uneven coloured cells of different heights that turns into one even layer",
        )
        .detail(
            "Uniformity is what a 300 mm puller must hold.",
            &["Uniformity at 300 mm is the hard control problem (page text)", "Patents cover crucible rotation (page text)"],
        ),
    Beat::new("demand is cyclical: SEMI's 2023 figures show wafer revenue and 300 mm shipments down", BEAT_MS)
        .note(
            "SEMI's 2023 changes hang down from the axis: revenue, polished 300 mm, epi 300 mm, and total area shipped.",
            "four bars dropping below the axis, the area bar in red the deepest",
        )
        .detail(
            "Demand swings give the pullers less work and squeeze each pull's margin.",
            &[
                "2023 wafer revenue fell 10.9% to $12.3B (SEMI)",
                "Polished 300 mm shipments -13%, epi 300 mm -5% (SEMI)",
                "Total area 12,602 million sq in, -14.3% (SEMI)",
            ],
        ),
];

const SEC8: &[Beat] = &[
    Beat::new(
        "four listed wafer makers, each with its exchange ticker",
        BEAT_MS,
    )
    .note(
        "The section lists four wafer makers with their tickers, dropping in in list order.",
        "four cards landing two by two, each with its ticker",
    )
    .detail(
        "The tickers are the entry points for looking these companies up.",
        &[
            "Shin-Etsu Chemical 4063.T, SUMCO 3436.T (page text)",
            "GlobalWafers 6488.TWO, Siltronic SSG.DE, also WAF.DE (page text)",
        ],
    ),
    Beat::new(
        "SK Siltron is not listed on its own: it is held by SK Inc",
        BEAT_MS,
    )
    .note(
        "SK Siltron sits inside SK Inc, which carries the listing (034730.KS).",
        "the blue SK Siltron block sliding into the SK Inc card",
    )
    .detail(
        "Look up the parent's ticker for SK Siltron.",
        &["SK Siltron is held by SK Inc (034730.KS) (page text)"],
    ),
    Beat::new(
        "the puller makers are a separate list: PVA TePla and Ferrotec",
        BEAT_MS,
    )
    .note(
        "Pullers are the machines that grow the crystal. The section names two puller makers.",
        "a crystal rising out of a crucible with the two maker tags beside it",
    )
    .detail(
        "A wafer maker and the puller it buys are different companies.",
        &[
            "PVA TePla (TPL.DE) (page text)",
            "Ferrotec 6890.T (page text)",
        ],
    ),
    Beat::new(
        "the tickers and puller makers are general knowledge, not a fetched source",
        BEAT_MS,
    )
    .note(
        "The section closes by marking its own sourcing with a stamp.",
        "the red stamp flickering on under the cards",
    )
    .detail(
        "Treat the tickers as a list to check, not verified data.",
        &[
            "Tickers and puller makers are general knowledge (page text)",
            "Not from a fetched source (page text)",
        ],
    ),
];

const SEC9: &[Beat] = &[
    Beat::new("model and simulation sources: the COMSOL furnace model and the 2023 pull-rate study", BEAT_MS)
        .note(
            "Two cards cover the modelled numbers: COMSOL's thermal analysis of a Czochralski furnace, and a journal study of a 300 mm pull-rate simulation.",
            "cards [1] and [4] lighting up",
        )
        .detail(
            "Figures tagged (model) or (2023 study) on the page trace back to these two.",
            &["[1] COMSOL, Thermal Analysis of a Czochralski Crystal Growth Furnace", "[4] Journal of Synthetic Crystals 52(4) 562 (2023)"],
        ),
    Beat::new("patent sources: the neck rates and the 100 kg limit", BEAT_MS)
        .note(
            "Card [3] groups the patents cited for the dash neck: the neck pull rates and the roughly 100 kg limit.",
            "card [3] lighting up",
        )
        .detail(
            "The neck figures are claims to trace back to the patent texts.",
            &["US 6,866,713: neck to about 6 mm/min, limit about 100 kg", "US 5,578,284 (slower neck); US 7,179,330 (dash-free neck)"],
        ),
    Beat::new("general reference: the Czochralski method and the wafer entry, both on Wikipedia", BEAT_MS)
        .note(
            "Cards [2] and [8] are encyclopedia entries on the Czochralski method and on wafers.",
            "cards [2] and [8] lighting up",
        )
        .detail(
            "Wikipedia is cited for a few broad figures; where sources differ, the page says so.",
            &["[2] Wikipedia, Czochralski method", "[8] Wikipedia, Wafer (electronics)"],
        ),
    Beat::new("market sources: wafer shares, SEMI 2023, and Omdia 2020", BEAT_MS)
        .note(
            "Cards [5], [6] and [7] cover the market side: a wafer-share page, SEMI 2023 revenue and shipments, and Omdia 2020 shares via KED Global.",
            "cards [5], [6] and [7] lighting up, so all eight are lit",
        )
        .detail(
            "These are market figures from different years (2020 and 2023); don't read them as one period.",
            &["[5] Report Prime wafer shares", "[6] SEMI 2023 via a substack post; [7] Omdia 2020 via KED Global"],
        ),
];

static CELLS: [Cell; 9] = [const { std::sync::OnceLock::new() }; 9];

macro_rules! section {
    ($n:literal, $beats:ident) => {
        || {
            page(
                &CELLS[$n - 1],
                include_bytes!(concat!(
                    "../../../../../tools/pbr3d/assets/melt_sec",
                    $n,
                    ".glb"
                )),
                $beats,
            )
        }
    };
}

/// One picture per `# ` section of the page, in order.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    section!(1, SEC1),
    section!(2, SEC2),
    section!(3, SEC3),
    section!(4, SEC4),
    section!(5, SEC5),
    section!(6, SEC6),
    section!(7, SEC7),
    section!(8, SEC8),
    section!(9, SEC9),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sections_match_the_blender_beats_and_draw() {
        let counts: Vec<usize> = SECTIONS.iter().map(|f| f().beats().len()).collect();
        assert_eq!(counts, [5, 4, 4, 4, 4, 4, 4, 4, 4]);
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
