// LITHO page: an exposure scanner, drawn in 3D by poly3d, on the CELL page's template.
// The overview walks one layer through the scanner: align, light the reticle, project
// it 4x smaller, scan one field, step across the wafer, develop, and strip for the next
// layer, with the camera gliding to the part each beat is about and the notes on the
// picture. Each zoom (a-e) is its own focused 3D scene: a the reticle, b the lens and
// NA, c inside the resist, d step and scan, e overlay. Sections 1-9 each have one too.
//
// Everything is continuous between beats and across the loop, so nothing cuts.
//
// Sources: see section 10 of MEM_LITHO.txt. ASML EXE:5000 product page (NA 0.55, 8 nm,
// 1.7x smaller than NXE); ASML "5 things you should know about High NA EUV" (2024:
// anamorphic optics, half-size fields); ASML annual report 2024 and 20-F FY2025
// (NXE:3800E 220 wph, matched overlay 0.9 nm); US 6,839,125 (k1 floor ~0.25).

use image::RgbaImage;

use super::diagrams_px as px;
use crate::ui::anim::{Beat, Canvas, Scene, Time, Zoom};
use poly3d::LithoZoom;

const MIN_W: u16 = 84;
const MIN_H: u16 = 26;
const BEAT_MS: u64 = 6500;
// the overview's notes sit on the picture and show once the camera settles
const OVERVIEW_MS: u64 = 13000;

const BEATS: &[Beat] = &[
    Beat::new("align: the sensor reads the marks on the wafer", OVERVIEW_MS)
        .note(
            "A wafer coated with photoresist sits on the wafer stage. The alignment sensor reads marks left by the layer below, so the stage knows exactly where that layer is.",
            "The green sensor beside the lens sends a beam down to the cross-shaped marks on the wafer.",
        )
        .detail(
            "This layer must land on the one below to within a few nanometres, so every exposure starts by measuring the wafer.",
            &[
                "Matched-machine overlay down to 0.9 nm on the NXE:3800E (ASML annual report 2024)",
                "One reticle per layer; every layer of the array is printed this way",
            ],
        ),
    Beat::new("the source lights the reticle", OVERVIEW_MS)
        .note(
            "The source sends light down through the reticle. The pattern is chrome on clear quartz: light passes the openings and stops on the chrome.",
            "Yellow light falls from the source onto the reticle and gets through only between the dark chrome bars.",
        )
        .detail(
            "The wavelength sets how fine a line can be printed. DUV uses 193 nm light, EUV 13.5 nm.",
            &["DUV ArF: 193 nm", "EUV: 13.5 nm"],
        ),
    Beat::new("the lens prints the image 4x smaller on the resist", OVERVIEW_MS)
        .note(
            "The projection lens collects the light from the reticle and focuses it on the wafer at a quarter of the size. Openings 30 units wide land 7.5 wide.",
            "The rays converge through the lens column, and a pink slit lights up on the wafer where the image lands.",
        )
        .detail(
            "Printing smaller than the mask keeps mask errors small too: a reticle defect shrinks with the image.",
            &[
                "Reduction: 4x on NXE EUV and DUV scanners",
                "High-NA EXE: 4x one way, 8x the other (anamorphic) (ASML, 2024)",
            ],
        ),
    Beat::new("scan: reticle and wafer move opposite ways under the slit", OVERVIEW_MS)
        .note(
            "The slit only covers a strip of the field. The wafer slides under it while the reticle slides the other way, 4x as far, so the whole field is painted strip by strip.",
            "The reticle glides along its rails, the wafer glides the opposite way, and pink lines grow across the first field.",
        )
        .detail(
            "Scanning lets a small, well-corrected slit of the lens print a large field.",
            &["Reticle moves 4x as far as the wafer (the reduction)"],
        ),
    Beat::new("step: the stage moves field to field across the wafer", OVERVIEW_MS)
        .note(
            "After each field the stage steps to the next and scans again, alternating direction so the reticle never flies back. The same pattern repeats across the wafer.",
            "The wafer hops field to field in rows, and the exposed fields fill in pink.",
        )
        .detail(
            "Throughput is money: a scanner that prints more wafers per hour costs less per layer.",
            &["NXE:3800E: 220 wafers per hour (ASML 20-F FY2025)", "NXE:3600D: 160 wafers per hour (ASML annual report 2024)"],
        ),
    Beat::new("develop: the exposed resist dissolves and the pattern stands", OVERVIEW_MS)
        .note(
            "The light changed the resist's chemistry, not its shape. Develop dissolves the exposed lines (positive resist), so the film below shows through where the light fell.",
            "Close over the wafer, the pink exposed lines turn cyan as the resist above them washes away.",
        )
        .detail(
            "The gaps are the pattern. The resist that stays protects the film while etch cuts the gaps into it.",
            &["Positive resist: the exposed part develops away"],
        ),
    Beat::new("the wafer goes to etch; fresh resist for the next layer", OVERVIEW_MS)
        .note(
            "Etch copies the gaps into the film, the resist is stripped, a new film goes on and the wafer is coated again. Then it comes back for the next layer.",
            "The pattern on the wafer fades back to fresh purple resist, ready for the loop to start again.",
        )
        .detail(
            "A DRAM wafer goes round this loop once per patterned layer, so litho cost is paid many times over.",
            &["Each layer has its own reticle and its own alignment to the layer below"],
        ),
];

const ZOOMS: &[Zoom] = &[
    Zoom {
        key: 'a',
        label: "the reticle: chrome on quartz, copied to every die",
        build: || -> Box<dyn Scene> { Box::new(ReticleZ) },
    },
    Zoom {
        key: 'b',
        label: "the lens: numerical aperture and the finest line",
        build: || -> Box<dyn Scene> { Box::new(LensZ) },
    },
    Zoom {
        key: 'c',
        label: "inside the resist: expose, develop, etch",
        build: || -> Box<dyn Scene> { Box::new(ResistZ) },
    },
    Zoom {
        key: 'd',
        label: "step and scan: field by field across the wafer",
        build: || -> Box<dyn Scene> { Box::new(ScanZ) },
    },
    Zoom {
        key: 'e',
        label: "overlay: lining up with the layer below",
        build: || -> Box<dyn Scene> { Box::new(OverlayZ) },
    },
];

/// The overview at `t`, turned by the user's `view`, with the beat's notes drawn on
/// the picture beside the parts they are about.
pub fn overview_frame(t: &Time, view: &poly3d::View, w: u32, h: u32) -> RgbaImage {
    let b = &BEATS[t.beat.min(BEATS.len() - 1)];
    let notes = poly3d::Notes {
        what: b.what,
        why: b.why,
        facts: b.facts,
    };
    poly3d::render_litho_overview(
        t.beat,
        t.local as f64,
        view,
        Some(&notes),
        w as usize,
        h as usize,
        px::BG,
    )
}

/// The LITHO overview: one layer through the scanner.
pub struct Litho;

impl Scene for Litho {
    fn size(&self) -> (u16, u16) {
        (MIN_W, MIN_H)
    }
    fn beats(&self) -> &[Beat] {
        BEATS
    }
    fn draw(&self, _c: &mut Canvas, _t: &Time) {}
    fn zooms(&self) -> &[Zoom] {
        ZOOMS
    }
    fn pixels(&self, t: &Time, w: u32, h: u32) -> Option<RgbaImage> {
        Some(overview_frame(t, &poly3d::View::default(), w, h))
    }
    fn notes_in_picture(&self) -> bool {
        true
    }
    fn rest_point(&self) -> f32 {
        0.4
    }
}

// ---- the zooms and sections: each a focused 3D scene from poly3d ---------------

/// The 3D scene behind zoom `key`: letters are parts of the overview, numbers the
/// page's sections.
pub fn zoom_scene(key: char) -> Option<LithoZoom> {
    Some(match key {
        'a' => LithoZoom::Reticle,
        'b' => LithoZoom::Lens,
        'c' => LithoZoom::Resist,
        'd' => LithoZoom::Scan,
        'e' => LithoZoom::Overlay,
        '1' => LithoZoom::Print,
        '2' => LithoZoom::Parts,
        '3' => LithoZoom::Order,
        '4' => LithoZoom::Resolution,
        '5' => LithoZoom::Focus,
        '6' => LithoZoom::Memory,
        '7' => LithoZoom::Multi,
        '8' => LithoZoom::Makers,
        '9' => LithoZoom::Risks,
        _ => return None,
    })
}

macro_rules! zoom_scene_impl {
    ($name:ident, $beats:ident, $zoom:expr) => {
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
                Some(poly3d::render_litho_zoom(
                    $zoom,
                    t.beat,
                    t.local as f64,
                    &poly3d::View::default(),
                    w as usize,
                    h as usize,
                    px::BG,
                ))
            }
        }
    };
}

const RETICLE_BEATS: &[Beat] = &[
    Beat::new("the pattern is chrome on clear quartz", BEAT_MS)
        .note(
            "A reticle is a quartz plate with the layer's pattern in chrome. Clear openings pass light; chrome blocks it.",
            "Dark chrome bars sit on the pale quartz plate, with clear gaps between them.",
        )
        .detail("Each layer of the array has its own reticle.", &["One reticle per layer"]),
    Beat::new("light gets through the openings only", BEAT_MS)
        .note(
            "Light falls on the whole plate. In the openings it carries on down to the dies; on the chrome it stops.",
            "Yellow dots pass the clear gaps and fall to the three dies; the ones landing on chrome go no further.",
        )
        .detail("The dies below are all printed from the same openings.", &["Same mask, every die"]),
    Beat::new("a speck on the mask prints on every die", BEAT_MS)
        .note(
            "Dirt in one opening blocks light there, so the same flaw appears on every die printed from the mask, until it is cleaned off.",
            "A pink speck appears in an opening, and a pink flaw shows up at the same spot on all three dies.",
        )
        .detail("A mask flaw is copied many times over, which is why masks are inspected and kept clean.", &["A reticle defect repeats on every die that uses it"]),
];

const LENS_BEATS: &[Beat] = &[
    Beat::new("NA 0.33: a narrow cone prints wide lines", BEAT_MS)
        .note(
            "Numerical aperture (NA) is the sine of the cone's half-angle. A narrow cone collects less of the light that carries fine detail, so lines come out wide.",
            "Light converges from the last lens element to a point on the wafer; the printed lines below are wide.",
        )
        .detail("CD = k1 x wavelength / NA: at EUV 13.5 nm, NA 0.33 and k1 0.4, about 16 nm.", &["EUV NXE: NA 0.33", "CD ~16 nm at k1 0.4"]),
    Beat::new("NA 0.55: a wider cone prints finer lines", BEAT_MS)
        .note(
            "A bigger lens at the same distance collects a wider cone. With NA 0.55 the same light prints lines about 10 nm wide.",
            "The lens grows, the cone opens, and the lines on the wafer narrow and multiply.",
        )
        .detail("High-NA EUV prints features 1.7x smaller than NXE (ASML).", &["High-NA EXE:5000: NA 0.55, 8 nm resolution (ASML)"]),
    Beat::new("the price: less depth stays in focus", BEAT_MS)
        .note(
            "The zone around the focus that stays sharp shrinks with NA squared. At NA 0.55 it is much shorter than at 0.33.",
            "A purple tube marks the in-focus zone; it shortens, then the lens closes back to 0.33.",
        )
        .detail("Higher NA needs flatter wafers and thinner resist.", &["DOF = k2 x wavelength / NA^2"]),
];

const RESIST_BEATS: &[Beat] = &[
    Beat::new("expose: light makes acid in the resist below the openings", BEAT_MS)
        .note(
            "Light through the openings changes the resist where it lands. In chemically amplified resist it releases acid there.",
            "Three columns of resist turn pink and fill with acid dots under the falling light.",
        )
        .detail("The shape has not changed yet: the pattern is hidden in the chemistry.", &["Exposure changes chemistry, not shape"]),
    Beat::new("develop: the exposed resist dissolves", BEAT_MS)
        .note(
            "Develop washes away the exposed columns (positive resist). The film below is now bare in the gaps.",
            "The pink columns sink away, leaving three trenches down to the cyan film.",
        )
        .detail("Over- or under-develop changes the line width, so develop is part of the CD.", &["Positive resist: exposed part removed"]),
    Beat::new("etch: the gaps are cut into the film", BEAT_MS)
        .note(
            "Etch removes film only where the resist is gone. The resist pattern is now copied into the film. Then a fresh film and resist go on.",
            "Ions rain into the trenches and the film under them is cut away; then the stack refills for the next layer.",
        )
        .detail("The resist only has to last through etch; the film keeps the pattern.", &["See the ETCH node in the Fab flow tab"]),
];

const SCAN_BEATS: &[Beat] = &[
    Beat::new("scan: the slit sweeps one field", BEAT_MS)
        .note(
            "The slit lights a thin strip. The wafer moves under it and the reticle moves the opposite way, 4x as far, painting one field.",
            "The reticle runs along its rails while the wafer runs the other way, and pink lines grow across one field.",
        )
        .detail("Only a slit of the lens is used, which keeps the optics' errors small.", &["Reticle travel = 4x wafer travel"]),
    Beat::new("step: field after field, scans alternating", BEAT_MS)
        .note(
            "The stage steps to the next field and scans again, each scan the opposite way to the last, until every field on the wafer is exposed.",
            "Looking down, the wafer hops in rows and the fields fill in one after another.",
        )
        .detail("Throughput sets the cost per layer.", &["NXE:3800E: 220 wafers per hour (ASML 20-F FY2025)"]),
    Beat::new("High-NA: half-size fields, twice the exposures", BEAT_MS)
        .note(
            "High-NA's anamorphic optics shrink 8x in one direction, so each field is half as tall and a wafer takes about twice as many exposures.",
            "An orange line splits each field in half.",
        )
        .detail("Half fields cost throughput, part of the price of finer lines.", &["High-NA fields are half the NXE size (ASML, 2024)"]),
];

const OVERLAY_BEATS: &[Beat] = &[
    Beat::new("the new layer sits off the one below", BEAT_MS)
        .note(
            "The layer below is already etched. If the wafer sits a little off, the new lines print beside the old ones instead of on them.",
            "Pink new lines float above the cyan old ones, shifted to one side.",
        )
        .detail("Every layer has to connect to the ones below, so a shift breaks contacts.", &["Overlay: how well this layer lines up with the last"]),
    Beat::new("the sensor reads the marks and the stage corrects", BEAT_MS)
        .note(
            "The alignment sensor measures marks printed in the old layer, and the stage moves the wafer until the new image lands on top.",
            "A green beam reads the marks, and the pink lines slide over until they sit on the cyan ones.",
        )
        .detail("Alignment happens on every wafer before it is exposed.", &["Alignment marks are printed with each layer"]),
    Beat::new("the budget is a few nanometres", BEAT_MS)
        .note(
            "Overlay error has to stay at a few nanometres or less, a small fraction of the line width. The next wafer arrives with its own offset.",
            "Close above the aligned lines; then the new layer drifts off again for the next wafer.",
        )
        .detail("Overlay error adds up with every extra exposure, which is one cost of multi-patterning.", &["NXE:3800E matched-machine overlay 0.9 nm (ASML annual report 2024)"]),
];

zoom_scene_impl!(ReticleZ, RETICLE_BEATS, LithoZoom::Reticle);
zoom_scene_impl!(LensZ, LENS_BEATS, LithoZoom::Lens);
zoom_scene_impl!(ResistZ, RESIST_BEATS, LithoZoom::Resist);
zoom_scene_impl!(ScanZ, SCAN_BEATS, LithoZoom::Scan);
zoom_scene_impl!(OverlayZ, OVERLAY_BEATS, LithoZoom::Overlay);

// ---- 1-9: the write-up's sections ---------------------------------------------

const PRINT_BEATS: &[Beat] = &[
    Beat::new("light passes the openings in the reticle", BEAT_MS)
        .note(
            "Lithography copies a pattern onto the wafer with light. The reticle holds the pattern; light goes through its openings.",
            "Yellow light falls from the source through the reticle's clear gaps.",
        )
        .detail("Every layer of a DRAM array is printed this way, once per layer.", &["One reticle per layer"]),
    Beat::new("the lens shrinks the image onto the resist", BEAT_MS)
        .note(
            "The lens focuses the image on the light-sensitive resist at a quarter of the size, and the resist changes where the light lands.",
            "The light converges through the lens and the centre field turns pink.",
        )
        .detail("The image is 4x smaller than the reticle.", &["Reduction: 4x"]),
    Beat::new("develop leaves the pattern in the resist", BEAT_MS)
        .note(
            "Develop removes the exposed resist and keeps the rest. The pattern now stands on the wafer, ready for etch.",
            "Close over the wafer, the pink lines turn cyan as the resist washes away.",
        )
        .detail("Etch copies it into the film below.", &["Positive resist: exposed part removed"]),
];

const PARTS_BEATS: &[Beat] = &[
    Beat::new("source: the wavelength", BEAT_MS)
        .note("The source sets the wavelength: 193 nm for DUV ArF, 13.5 nm for EUV.", "The source lights up and the rest goes grey.")
        .detail("A shorter wavelength prints finer lines.", &["DUV ArF 193 nm; EUV 13.5 nm"]),
    Beat::new("reticle: the pattern", BEAT_MS)
        .note("The reticle carries the layer's pattern in chrome on quartz, one per layer.", "The reticle keeps its colour; light passes its openings.")
        .detail("A flaw on it repeats on every die.", &["One reticle per layer"]),
    Beat::new("lens: NA and the 4x shrink", BEAT_MS)
        .note("The projection lens sets the numerical aperture and prints the image 4x smaller.", "The lens column glows as light runs through it to the wafer.")
        .detail("NA sets resolution and depth of focus together.", &["Reduction 4x; EUV NA 0.33 or 0.55"]),
    Beat::new("photoresist: where the image becomes a pattern", BEAT_MS)
        .note("The light-sensitive film on the wafer. In positive resist the exposed part develops away.", "The fields on the wafer turn pink.")
        .detail("Resist blur and random defects set a floor on line width, apart from the optics.", &["Positive resist"]),
    Beat::new("wafer stage: field by field", BEAT_MS)
        .note("The stage carries the wafer under the lens, one field at a time, scanning and stepping.", "The wafer stage traces a figure across its travel.")
        .detail("Its speed sets wafers per hour.", &["NXE:3800E: 220 wafers per hour (ASML)"]),
    Beat::new("alignment: overlay with the layer below", BEAT_MS)
        .note("The alignment sensor reads marks from the layer below so this layer lands on top of it.", "The green sensor's beam reads the marks on the wafer.")
        .detail("Overlay is how well this layer lines up with the last.", &["Matched overlay 0.9 nm (ASML annual report 2024)"]),
];

const ORDER_BEATS: &[Beat] = &[
    Beat::new("1. the source flashes; light passes the reticle", BEAT_MS)
        .note("Light from the source passes the openings in the reticle.", "Yellow dots fall from the source to the reticle's gaps.")
        .detail("Every exposure starts here.", &["The steps are numbered along the bottom"]),
    Beat::new("2. the lens projects the image, shrunk", BEAT_MS)
        .note("The lens focuses the light from the openings onto the resist, closer together than on the reticle.", "The light bends through the lens and lands on the resist.")
        .detail("A scanner shrinks 4x; this small model shows 2x.", &["Reduction: 4x in a scanner"]),
    Beat::new("3. the exposed resist changes", BEAT_MS)
        .note("Where light lands, the resist changes chemically: acid forms in it.", "Three columns of resist turn pink with acid dots.")
        .detail("The pattern is still hidden in the chemistry.", &["Exposure: chemistry, not shape"]),
    Beat::new("4. develop removes the exposed resist", BEAT_MS)
        .note("Develop dissolves the exposed columns (positive resist).", "The pink columns sink away to the film.")
        .detail("The pattern now stands in the resist.", &["Positive resist"]),
    Beat::new("5. etch copies the pattern into the film", BEAT_MS)
        .note("Etch cuts the gaps into the film below, then the stack is renewed for the next layer.", "Ions fall into the trenches and cut the film.")
        .detail("One layer done; the wafer comes back for the next.", &["See the ETCH node in the Fab flow tab"]),
];

const RES_BEATS: &[Beat] = &[
    Beat::new("DUV ArF immersion: 193 nm, NA 1.35", BEAT_MS)
        .note("Water between lens and wafer lets NA pass 1. At k1 0.4 the smallest line is about 57 nm.", "The DUV tile has the widest lines and the tallest bar.")
        .detail("Below a k1 of about 0.25 one exposure is not enough (US 6,839,125).", &["CD = k1 x wavelength / NA", "193 x 0.4 / 1.35 = ~57 nm"]),
    Beat::new("EUV: 13.5 nm, NA 0.33", BEAT_MS)
        .note("A 14x shorter wavelength at a smaller NA. At k1 0.4 the line is about 16 nm.", "The EUV tile's lines are much finer; its bar is short.")
        .detail("EUV needs vacuum and mirrors, since almost everything absorbs 13.5 nm light.", &["13.5 x 0.4 / 0.33 = ~16 nm"]),
    Beat::new("High-NA EUV: 13.5 nm, NA 0.55", BEAT_MS)
        .note("Same wavelength, a wider cone. At k1 0.4 the line is about 10 nm.", "The High-NA tile has the finest lines and the shortest bar.")
        .detail("ASML quotes 8 nm resolution, 1.7x smaller than NXE.", &["13.5 x 0.4 / 0.55 = ~10 nm", "EXE:5000: 8 nm (ASML)"]),
];

const FOCUS_BEATS: &[Beat] = &[
    Beat::new("NA 0.33: a long in-focus band", BEAT_MS)
        .note("The image stays sharp over a band of heights around the focus: DOF = k2 x wavelength / NA^2.", "A purple band brackets the focus on a flat wafer.")
        .detail("Illustrative k2 0.5: about 62 nm at EUV NA 0.33.", &["DOF = k2 x wavelength / NA^2"]),
    Beat::new("NA 0.55: the band shrinks with NA squared", BEAT_MS)
        .note("A wider cone prints finer lines but the sharp band gets much shorter: about 22 nm with the same k2.", "The cone opens and the purple band closes in.")
        .detail("0.55 squared is 2.8x 0.33 squared, so the band is 2.8x shorter.", &["(0.55 / 0.33)^2 = 2.8"]),
    Beat::new("a wafer that is not flat drifts out of focus", BEAT_MS)
        .note("Real wafers have height steps. Where the surface leaves the band, the image blurs.", "The wafer surface bends; slices outside the band turn orange.")
        .detail("Higher NA asks for flatter wafers and thinner resist.", &["Flatness budget falls with NA^2"]),
];

const MEMORY_BEATS: &[Beat] = &[
    Beat::new("one cell is 6F^2", BEAT_MS)
        .note("F is the feature size, set by the smallest line litho prints. A 1T1C cell with an open bit line covers 3F x 2F.", "One orange cell sits on a grid of F squares.")
        .detail("Counting in F compares layouts across processes.", &["1T1C cell: 6F^2 (see the CELL node, section 6)"]),
    Beat::new("shrink F by 0.7 and the cell area halves", BEAT_MS)
        .note("Area goes with F squared: 0.7 x 0.7 = 0.49.", "The grid tightens and the cell shrinks with it.")
        .detail("That is why every node is chasing a smaller F.", &["F x 0.7 -> area x 0.49"]),
    Beat::new("the same patch holds about twice the cells", BEAT_MS)
        .note("More cells per die means more bits per wafer, at roughly the same wafer cost.", "Every cell in the patch lights up; the count roughly doubles.")
        .detail("Overlay and pitch limits set how far this goes.", &["Cells per area ~ 1 / F^2"]),
];

const MULTI_BEATS: &[Beat] = &[
    Beat::new("too tight for one exposure: the lines merge", BEAT_MS)
        .note("When the pitch needs a k1 below about 0.25, one exposure cannot separate the lines.", "The lines swell into one orange smear.")
        .detail("k1 ~0.25 is the single-exposure floor (US 6,839,125).", &["k1 floor ~0.25"]),
    Beat::new("split it: mask A, then mask B in the gaps", BEAT_MS)
        .note("Print every other line with one mask, then the rest with a second (LELE). Spacer methods like SADP do similar with one litho step.", "Pink lines from mask A, then cyan lines from mask B between them.")
        .detail("Each pass prints a pitch the scanner can manage.", &["LELE: litho-etch, litho-etch", "SADP: self-aligned double patterning"]),
    Beat::new("the cost: another mask, more time, more error", BEAT_MS)
        .note("Any overlay error between the passes leaves the spacing uneven, and every extra pass adds cost and time.", "The cyan lines slide toward their pink neighbours.")
        .detail("Memory makers use several such layers.", &["Overlay error adds up per exposure"]),
];

const MAKERS_BEATS: &[Beat] = &[
    Beat::new("ASML (ASML): EUV and DUV", BEAT_MS)
        .note("ASML is the only maker of EUV scanners, and also makes DUV scanners.", "The ASML scanner carries a glowing EUV source.")
        .detail("Every EUV layer in the world runs on an ASML tool.", &["Only EUV scanner maker: ASML (ASML 20-F)"]),
    Beat::new("Nikon (7731.T): DUV", BEAT_MS)
        .note("Nikon makes DUV scanners.", "The Nikon scanner is in the spotlight.")
        .detail("DUV still prints most layers of a chip.", &["Nikon ticker: 7731.T"]),
    Beat::new("Canon (7751.T): DUV", BEAT_MS)
        .note("Canon makes DUV scanners.", "The Canon scanner is in the spotlight.")
        .detail("Resist makers are mostly in Japan.", &["Canon ticker: 7751.T"]),
];

const RISKS_BEATS: &[Beat] = &[
    Beat::new("one EUV maker, no second source", BEAT_MS)
        .note("EUV scanners come from one company, with sources and optics from very few suppliers.", "One glowing tower stands beside two empty glass plinths.")
        .detail("Any delay at ASML or its suppliers delays every EUV fab.", &["ASML: sole EUV scanner maker"]),
    Beat::new("stochastic defects: too few photons", BEAT_MS)
        .note("At small features and low doses, few photons land on each spot, and random breaks and bridges appear.", "Sparse yellow photons fall; pink defects pop up along the fine lines.")
        .detail("Raising the dose fixes it but slows the scanner.", &["Defects grow as doses fall"]),
    Beat::new("export controls fence off advanced scanners", BEAT_MS)
        .note("Export rules limit which advanced scanners can be sold where. Check the current rules.", "An orange fence stands in front of an advanced scanner.")
        .detail("A rule change can cut a maker off from a market overnight.", &["Check current export rules"]),
];

zoom_scene_impl!(SecPrint, PRINT_BEATS, LithoZoom::Print);
zoom_scene_impl!(SecParts, PARTS_BEATS, LithoZoom::Parts);
zoom_scene_impl!(SecOrder, ORDER_BEATS, LithoZoom::Order);
zoom_scene_impl!(SecRes, RES_BEATS, LithoZoom::Resolution);
zoom_scene_impl!(SecFocus, FOCUS_BEATS, LithoZoom::Focus);
zoom_scene_impl!(SecMemory, MEMORY_BEATS, LithoZoom::Memory);
zoom_scene_impl!(SecMulti, MULTI_BEATS, LithoZoom::Multi);
zoom_scene_impl!(SecMakers, MAKERS_BEATS, LithoZoom::Makers);
zoom_scene_impl!(SecRisks, RISKS_BEATS, LithoZoom::Risks);

/// One scene per `# ` section of the page, in order. Section 10, the sources, stays text.
pub const SECTIONS: [fn() -> Box<dyn Scene>; 9] = [
    || Box::new(SecPrint),
    || Box::new(SecParts),
    || Box::new(SecOrder),
    || Box::new(SecRes),
    || Box::new(SecFocus),
    || Box::new(SecMemory),
    || Box::new(SecMulti),
    || Box::new(SecMakers),
    || Box::new(SecRisks),
];

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ui::anim::Player;
    use std::time::Instant;

    fn at(beat: usize, local: f32) -> Time {
        Time {
            ms: 0,
            beat,
            local,
            beat_start: 0,
        }
    }

    fn scenes() -> Vec<(String, Box<dyn Scene>)> {
        let mut v: Vec<(String, Box<dyn Scene>)> = vec![("overview".into(), Box::new(Litho))];
        for z in ZOOMS {
            v.push((z.key.to_string(), (z.build)()));
        }
        for (i, mk) in SECTIONS.iter().enumerate() {
            v.push(((i + 1).to_string(), mk()));
        }
        v
    }

    #[test]
    fn every_frame_is_a_picture_that_moves() {
        for (name, scene) in scenes() {
            let p = Player::new(scene, Instant::now());
            let mut seen = std::collections::HashSet::new();
            for ms in (0..p.loop_ms()).step_by(397) {
                let img = p.pixels(&p.time_at(ms), 160, 90).expect("pixel frame");
                assert_eq!(img.dimensions(), (160, 90), "{name}");
                seen.insert(img.into_raw());
            }
            assert!(seen.len() > 12, "{name}: {} distinct frames", seen.len());
        }
    }

    /// Text and picture agree on how many beats each scene has.
    #[test]
    fn beats_match_their_pictures() {
        assert_eq!(BEATS.len(), poly3d::LITHO_OVERVIEW_BEATS);
        for z in ZOOMS {
            assert_eq!((z.build)().beats().len(), zoom_scene(z.key).unwrap().beats(), "zoom {}", z.key);
        }
        for (key, mk) in ('1'..='9').zip(SECTIONS) {
            assert_eq!(mk().beats().len(), zoom_scene(key).unwrap().beats(), "section {key}");
        }
        let heads = super::super::diagrams_desc::visual("LITHO")
            .unwrap()
            .lines()
            .filter(|l| l.starts_with("# "))
            .count();
        assert_eq!(heads, SECTIONS.len() + 1, "one scene per section but the sources");
    }

    #[test]
    fn beats_have_text_for_the_popup() {
        let all = BEATS
            .iter()
            .chain(RETICLE_BEATS)
            .chain(LENS_BEATS)
            .chain(RESIST_BEATS)
            .chain(SCAN_BEATS)
            .chain(OVERLAY_BEATS)
            .chain(PRINT_BEATS)
            .chain(PARTS_BEATS)
            .chain(ORDER_BEATS)
            .chain(RES_BEATS)
            .chain(FOCUS_BEATS)
            .chain(MEMORY_BEATS)
            .chain(MULTI_BEATS)
            .chain(MAKERS_BEATS)
            .chain(RISKS_BEATS);
        for b in all {
            assert!(!b.caption.is_empty() && !b.what.is_empty(), "{}", b.caption);
        }
    }

    /// Writes one PNG per beat of every scene to $FL_PX_DUMP, for a visual check:
    /// `FL_PX_DUMP=/some/dir cargo test --release dump_litho_frames -- --ignored`.
    #[test]
    #[ignore]
    fn dump_litho_frames() {
        let Some(dir) = std::env::var_os("FL_PX_DUMP") else {
            return;
        };
        let dir = std::path::PathBuf::from(dir);
        std::fs::create_dir_all(&dir).unwrap();
        for (name, scene) in scenes() {
            let beats = scene.beats().len();
            let p = Player::new(scene, Instant::now());
            for beat in 0..beats {
                let t = at(beat, 0.6);
                let (w, h) = if name == "overview" { (1900, 1000) } else { (960, 576) };
                let img = p.pixels(&t, w, h).expect("pixel frame");
                img.save(dir.join(format!("{name}_{beat}.png"))).unwrap();
            }
        }
    }
}
