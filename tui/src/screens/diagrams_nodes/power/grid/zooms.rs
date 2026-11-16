// GRID: lettered zoom-ins a-e. Each is the overview's scene with the camera held on one subject
// (tools/pbr3d/blender/power_grid_zooms.py, GLBs in tools/pbr3d/assets/power_grid_zoom_<letter>.glb):
// a transmission, b how much power AI uses, c the interconnection queue, d PUE, e behind the meter.

use super::super::super::blender::{BEAT_MS, Cell, page};
use crate::ui::anim::{Beat, Scene, Zoom};

static ZA: Cell = std::sync::OnceLock::new();
static ZB: Cell = std::sync::OnceLock::new();
static ZC: Cell = std::sync::OnceLock::new();
static ZD: Cell = std::sync::OnceLock::new();
static ZE: Cell = std::sync::OnceLock::new();

fn zoom_a() -> Box<dyn Scene> {
    page(
        &ZA,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_zoom_a.glb"),
        A_B,
    )
}

fn zoom_b() -> Box<dyn Scene> {
    page(
        &ZB,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_zoom_b.glb"),
        B_B,
    )
}

fn zoom_c() -> Box<dyn Scene> {
    page(
        &ZC,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_zoom_c.glb"),
        C_B,
    )
}

fn zoom_d() -> Box<dyn Scene> {
    page(
        &ZD,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_zoom_d.glb"),
        D_B,
    )
}

fn zoom_e() -> Box<dyn Scene> {
    page(
        &ZE,
        include_bytes!("../../../../../../tools/pbr3d/assets/power_grid_zoom_e.glb"),
        E_B,
    )
}

/// a transmission: from the plant's step-up to the substation gantry.
const A_B: &[Beat] = &[
    Beat::new("the plant to the tower", BEAT_MS)
        .note(
            "A turbine turns a generator at about 10 to 25 kV, and a step-up transformer raises the voltage to transmission level before the power leaves the plant. Silver bus carries it to the transformer, and the line takes it on.",
            "The plant at the left: a grey turbine hall with a tall stack, a blue generator, and a squat transformer with brown bushings. An arched silver bus runs from it to a lattice tower, and yellow beads leave the transformer.",
        )
        .detail(
            "Generator step-up, then the lines.",
            &["Generator: ~10-25 kV", "Lines: 115-345 kV"],
        ),
    Beat::new("tower to tower", BEAT_MS)
        .note(
            "Each circuit is three conductors carrying three-phase power, and the lines run tower to tower at hundreds of kilovolts. The conductors sag between towers, and beads move along all of them.",
            "Grey lattice towers in a row, silver conductors in sagging curves, and teal insulator strings at each arm. Yellow beads ride the lines.",
        )
        .detail(
            "THREE-PHASE: three conductors whose voltages peak in turn.",
            &["Three phases per circuit", "115-345 kV and up"],
        ),
    Beat::new("down to the gantry", BEAT_MS)
        .note(
            "The line ends on the substation's gantry at the campus edge, and a transformer steps the voltage down for the site. The utility's meter marks where the campus begins.",
            "The steel gantry carrying the conductors, a rigid bus on white post insulators, and the step-down transformer with brown bushings and cooling fins at its side.",
        )
        .detail(
            "Then the step-down, at the campus substation.",
            &["Step-down for the site", "Utility meter: where the campus begins"],
        ),
];

/// b how much power AI uses: the data hall and its racks.
const B_B: &[Beat] = &[
    Beat::new("176 TWh in 2023", BEAT_MS)
        .note(
            "US data centers used about 176 TWh in 2023, 4.4% of US electricity, up from 58 TWh in 2014. The growth is driven mostly by AI servers.",
            "The data hall cut open: rows of black racks with green status lights, a gold busway over each row, and cooling units on the roof.",
        )
        .detail(
            "Berkeley Lab's count for 2023.",
            &["4.4% of US electricity", "58 TWh in 2014"],
        ),
    Beat::new("325-580 TWh by 2028", BEAT_MS)
        .note(
            "Berkeley Lab projects 325-580 TWh by 2028, 6.7% to 12% of US electricity. The projection rests mostly on AI servers, so the same kind of hall takes more load.",
            "The hall with its rows of racks running along the wall, the gold busways feeding each row, and a tall dark cabinet standing beside it.",
        )
        .detail(
            "A projection, not a measurement.",
            &["325-580 TWh projected for 2028", "6.7-12% of US electricity"],
        ),
    Beat::new("one rack: about 120 kW", BEAT_MS)
        .note(
            "One GB200 NVL72 rack draws about 120 kW, so racks add up to a large load quickly. A large campus is hundreds of megawatts to over a gigawatt.",
            "A single rack, black with green lights, with its busway tap running down to it from the gold bus over the row.",
        )
        .detail(
            "Density is what makes the campus large.",
            &["~120 kW per NVL72 rack", "Campus: hundreds of MW to over 1 GW"],
        ),
];

/// c the interconnection queue: projects waiting at the substation gate.
const C_B: &[Beat] = &[
    Beat::new("every project is studied", BEAT_MS)
        .note(
            "Every new plant or large load is studied before it may connect, and grid operators approve the connection only after the study. The study, not the chips, sets the timing.",
            "Projects lined up along the road to the substation gate: solar arrays, white battery containers, gas plants and wind turbines. A cyan ring circles the one under study at the gate.",
        )
        .detail(
            "The queue sets when a campus can connect.",
            &["Interconnection queue", "LBNL Queued Up 2025"],
        ),
    Beat::new("1,400 GW waiting", BEAT_MS)
        .note(
            "Berkeley Lab counted about 1,400 GW of generation and 890 GW of storage waiting in US queues at the end of 2024. Queued projects are not yet built.",
            "The board beside the gate: a grid of tiles, one gold tile lit each month as the queue moves forward.",
        )
        .detail(
            "Queued projects wait years for a connection.",
            &["~1,400 GW generation queued", "890 GW storage queued (end of 2024)"],
        ),
    Beat::new("55 months to build", BEAT_MS)
        .note(
            "The typical project built in 2024 took 55 months from request to operation. A campus waiting on a connection can wait years for its power.",
            "The campus at the far edge, with the board beside the gate counting the months.",
        )
        .detail(
            "Time from request to operation.",
            &["55 months, request to operation (2024)"],
        ),
];

/// d PUE: site power over IT power, and the overhead between them.
const D_B: &[Beat] = &[
    Beat::new("site power", BEAT_MS)
        .note(
            "Power usage effectiveness is total site power divided by the power that reaches IT equipment. Site power is everything the campus draws from the grid.",
            "The campus as a whole: the substation at its edge feeding the hall, the hall's racks, and cooling units on the roof.",
        )
        .detail(
            "The numerator of PUE.",
            &["PUE = site power / IT power"],
        ),
    Beat::new("IT power", BEAT_MS)
        .note(
            "IT power is what reaches the servers and racks, the part that does the computing. It runs along the busways into the racks.",
            "Yellow beads run along the gold busways into the rows of racks, their green lights glowing.",
        )
        .detail(
            "The denominator of PUE.",
            &["Efficient hyperscale sites ~1.1-1.2"],
        ),
    Beat::new("the rest is overhead", BEAT_MS)
        .note(
            "The rest goes to cooling and conversion losses. At a PUE of 1.2, 100 MW of IT needs 120 MW from the grid.",
            "Orange heat rising off the fans of the cooling units on the roof, with orange beads climbing a riser up to them.",
        )
        .detail(
            "PUE 1.2 means 20% overhead.",
            &["At PUE 1.2, 100 MW of IT needs 120 MW", "Efficient sites ~1.1-1.2"],
        ),
];

/// e behind the meter: a gas turbine on site, when the grid cannot connect in time.
const E_B: &[Beat] = &[
    Beat::new("the grid can't keep up", BEAT_MS)
        .note(
            "New transmission lines take years to permit and build, so the grid fills up before a campus can connect. A campus that cannot wait may bring its own plant.",
            "The grid's lattice towers and conductors running away in rows, with yellow beads along them, sparse where the lines are full.",
        )
        .detail(
            "New transmission takes about a decade to permit and build.",
            &["New lines: years to build", "Queues: years to connect"],
        ),
    Beat::new("power on site", BEAT_MS)
        .note(
            "A gas turbine burns natural gas to spin a generator on the campus itself. Its compressor, combustor and generator sit in one package beside the hall.",
            "A grey gas-turbine enclosure cut open: a row of compressor blades, the glowing combustor, and a blue generator, with a yellow fuel line running in from the right.",
        )
        .detail(
            "Behind the meter: power made on site.",
            &["Gas turbine: tens to hundreds of MW", "Turbine order books have grown long"],
        ),
    Beat::new("the trade", BEAT_MS)
        .note(
            "On site, the campus opens sooner but runs its own plant and fuel supply. The utility meter still marks where the grid ends and the site begins.",
            "The utility meter on one side, the data hall in the middle, and the gas plant with its stack at the right, with glowing beads rising from its top.",
        )
        .detail(
            "It opens sooner, at the cost of its own plant and fuel supply.",
            &["Behind the meter: own plant and fuel", "Gas turbine on site"],
        ),
];

pub const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "transmission",
        build: zoom_a,
    },
    Zoom {
        key: 'b',
        label: "how much power AI uses",
        build: zoom_b,
    },
    Zoom {
        key: 'c',
        label: "the interconnection queue",
        build: zoom_c,
    },
    Zoom {
        key: 'd',
        label: "PUE",
        build: zoom_d,
    },
    Zoom {
        key: 'e',
        label: "behind the meter",
        build: zoom_e,
    },
];
