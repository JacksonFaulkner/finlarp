// The Z screen's diagram format: JSON files Claude writes into the Z folder while it
// explains something. One file is one diagram. The screen hot-reloads the folder, and
// `fl z check FILE` prints the same errors the screen would show, so Claude can fix a
// file before the user sees it.
//
// A diagram is one picture: 2D `art`, a 3D `scene`, or both, with its explanation `text`
// under it. There are no sections or zooms: everything the user needs is on that one
// picture, and explanations sit on it as part labels (a part's `name`). The full reference
// Claude gets is z_rules.md; keep the two in step.

use std::path::Path;

use serde::Deserialize;

#[derive(Debug, Clone, Deserialize, Default)]
#[serde(deny_unknown_fields)]
pub struct Diagram {
    pub title: String,
    #[serde(default)]
    pub caption: String,
    #[serde(default)]
    pub art: Vec<String>,
    pub scene: Option<Scene>,
    #[serde(default)]
    pub text: String,
}

#[derive(Debug, Clone, Copy, Deserialize, Default, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct Camera {
    /// Degrees around the vertical axis, 0 = looking from +Z.
    #[serde(default)]
    pub yaw: f64,
    /// Degrees above the horizon.
    #[serde(default = "default_pitch")]
    pub pitch: f64,
    #[serde(default = "one")]
    pub zoom: f64,
}

fn default_pitch() -> f64 {
    15.0
}
fn one() -> f64 {
    1.0
}

#[derive(Debug, Clone, Deserialize, Default)]
#[serde(deny_unknown_fields)]
pub struct Scene {
    #[serde(default)]
    pub parts: Vec<Part>,
    #[serde(default)]
    pub flows: Vec<Flow>,
    pub camera: Option<Camera>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Part {
    pub shape: String,
    pub name: Option<String>,
    /// Box: centre. Sphere: centre.
    pub at: Option<[f64; 3]>,
    /// Box: width (x), height (y), depth (z).
    pub size: Option<[f64; 3]>,
    /// Cylinder: end points.
    pub from: Option<[f64; 3]>,
    pub to: Option<[f64; 3]>,
    /// Cylinder and sphere radius.
    pub r: Option<f64>,
    #[serde(default)]
    pub color: Option<String>,
    #[serde(default)]
    pub glow: f32,
    #[serde(default)]
    pub glass: bool,
    /// Label offset from the part, as fractions of the picture height: [right, down].
    pub label: Option<[f64; 2]>,
    pub repeat: Option<Repeat>,
}

#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Repeat {
    pub n: usize,
    pub step: [f64; 3],
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Flow {
    pub path: Vec<[f64; 3]>,
    #[serde(default)]
    pub color: Option<String>,
    pub name: Option<String>,
}

/// The named colours, so Claude need not pick hex for every part.
pub const COLORS: &[(&str, [u8; 3])] = &[
    ("red", [0xe0, 0x55, 0x55]),
    ("orange", [0xf0, 0x9a, 0x40]),
    ("yellow", [0xf2, 0xd5, 0x5a]),
    ("green", [0x6c, 0xc6, 0x6a]),
    ("teal", [0x3f, 0xb8, 0xa8]),
    ("cyan", [0x6c, 0xd4, 0xf0]),
    ("blue", [0x5a, 0x8c, 0xe8]),
    ("purple", [0xa0, 0x78, 0xe0]),
    ("pink", [0xf0, 0x8c, 0xc0]),
    ("white", [0xe8, 0xea, 0xee]),
    ("grey", [0x8a, 0x8e, 0x98]),
    ("dark", [0x3a, 0x3d, 0x46]),
    ("copper", [0xc8, 0x7a, 0x48]),
    ("gold", [0xd8, 0xb0, 0x48]),
    ("silicon", [0x6e, 0x76, 0x88]),
    ("glass", [0x9e, 0xcc, 0xe8]),
];

pub fn parse_color(s: &str) -> Option<[f32; 3]> {
    let s = s.trim();
    let rgb = if let Some(hex) = s.strip_prefix('#') {
        if hex.len() != 6 {
            return None;
        }
        let v = u32::from_str_radix(hex, 16).ok()?;
        [(v >> 16) as u8, (v >> 8) as u8, v as u8]
    } else {
        COLORS.iter().find(|(n, _)| n.eq_ignore_ascii_case(s))?.1
    };
    Some(rgb.map(|c| c as f32 / 255.0))
}

const MAX_PARTS: usize = 400;
/// A part's name is its label on the picture. Long explanations make the picture unreadable;
/// keep the label short and put the detail in the diagram's text.
pub const MAX_LABEL: usize = 40;

/// The diagram in `json`, checked. Errors name the field and say what is valid, so Claude
/// can fix the file from the message alone.
pub fn parse(json: &str) -> Result<Diagram, Vec<String>> {
    let d: Diagram = serde_json::from_str(json).map_err(|e| vec![format!("JSON: {e}")])?;
    let errs = check(&d);
    if errs.is_empty() { Ok(d) } else { Err(errs) }
}

pub fn load(path: &Path) -> Result<Diagram, Vec<String>> {
    let text = std::fs::read_to_string(path)
        .map_err(|e| vec![format!("can't read {}: {e}", path.display())])?;
    parse(&text)
}

fn check(d: &Diagram) -> Vec<String> {
    let mut errs = Vec::new();
    if d.title.trim().is_empty() {
        errs.push("title: must not be empty".into());
    }
    if d.art.is_empty() && d.scene.is_none() && d.text.trim().is_empty() {
        errs.push("the diagram needs at least one of art, scene or text".into());
    }
    if let Some(s) = &d.scene {
        check_scene(s, "scene", &mut errs);
    }
    errs
}

fn check_scene(s: &Scene, at: &str, errs: &mut Vec<String>) {
    let total: usize = s
        .parts
        .iter()
        .map(|p| p.repeat.map_or(1, |r| r.n.max(1)))
        .sum();
    if total > MAX_PARTS {
        errs.push(format!(
            "{at}: {total} parts after repeats; at most {MAX_PARTS}"
        ));
    }
    if s.parts.is_empty() && s.flows.is_empty() {
        errs.push(format!("{at}: no parts or flows"));
    }
    for (i, p) in s.parts.iter().enumerate() {
        let at = format!("{at}.parts[{i}]");
        if let Some(n) = &p.name {
            if n.chars().count() > MAX_LABEL {
                errs.push(format!("{at}.name: {} characters; labels are at most {MAX_LABEL}. Shorten it and put the detail in the caption", n.chars().count()));
            }
        }
        let pos = |v: Option<f64>| v.is_some_and(|x| x > 0.0 && x.is_finite());
        match p.shape.as_str() {
            "box" => {
                if p.at.is_none() || !p.size.is_some_and(|s| s.iter().all(|&x| pos(Some(x)))) {
                    errs.push(format!(
                        "{at}: a box needs at [x,y,z] (its centre) and size [w,h,d], all sizes > 0"
                    ));
                }
            }
            "cylinder" => {
                if p.from.is_none() || p.to.is_none() || !pos(p.r) || p.from == p.to {
                    errs.push(format!("{at}: a cylinder needs from [x,y,z], to [x,y,z] (different points) and r > 0"));
                }
            }
            "sphere" => {
                if p.at.is_none() || !pos(p.r) {
                    errs.push(format!("{at}: a sphere needs at [x,y,z] and r > 0"));
                }
            }
            other => errs.push(format!(
                "{at}.shape: one of box, cylinder, sphere; got {other:?}"
            )),
        }
        if let Some(c) = &p.color {
            if parse_color(c).is_none() {
                errs.push(format!(
                    "{at}.color: #rrggbb or one of {}; got {c:?}",
                    color_names()
                ));
            }
        }
        if !(0.0..=1.0).contains(&p.glow) {
            errs.push(format!("{at}.glow: 0..1, got {}", p.glow));
        }
        if p.repeat.is_some_and(|r| r.n == 0 || r.n > 200) {
            errs.push(format!("{at}.repeat.n: 1..200"));
        }
    }
    for (i, f) in s.flows.iter().enumerate() {
        if f.path.len() < 2 {
            errs.push(format!("{at}.flows[{i}].path: at least 2 points"));
        }
        if let Some(c) = &f.color {
            if parse_color(c).is_none() {
                errs.push(format!(
                    "{at}.flows[{i}].color: #rrggbb or one of {}; got {c:?}",
                    color_names()
                ));
            }
        }
    }
}

fn color_names() -> String {
    COLORS.iter().map(|(n, _)| *n).collect::<Vec<_>>().join(" ")
}

/// The scene as the renderer takes it. Repeats expand here: a name with `{i}` becomes one
/// label per copy (1-based); a plain name labels only the first copy.
pub fn to_poly(s: &Scene) -> poly3d::SpecScene {
    let default = parse_color("silicon").unwrap_or([0.5; 3]);
    let mut parts = Vec::new();
    for p in &s.parts {
        let color = p.color.as_deref().and_then(parse_color).unwrap_or(default);
        let rep = p.repeat.unwrap_or(Repeat {
            n: 1,
            step: [0.0; 3],
        });
        for i in 0..rep.n.max(1) {
            let off = rep.step.map(|v| v * i as f64);
            let mv = |q: [f64; 3]| [q[0] + off[0], q[1] + off[1], q[2] + off[2]];
            let shape = match p.shape.as_str() {
                "box" => {
                    let (Some(c), Some(sz)) = (p.at, p.size) else {
                        continue;
                    };
                    let c = mv(c);
                    poly3d::SpecShape::Box {
                        lo: [c[0] - sz[0] / 2.0, c[1] - sz[1] / 2.0, c[2] - sz[2] / 2.0],
                        hi: [c[0] + sz[0] / 2.0, c[1] + sz[1] / 2.0, c[2] + sz[2] / 2.0],
                    }
                }
                "cylinder" => {
                    let (Some(a), Some(b), Some(r)) = (p.from, p.to, p.r) else {
                        continue;
                    };
                    poly3d::SpecShape::Cyl {
                        a: mv(a),
                        b: mv(b),
                        r,
                    }
                }
                "sphere" => {
                    let (Some(c), Some(r)) = (p.at, p.r) else {
                        continue;
                    };
                    poly3d::SpecShape::Sphere { c: mv(c), r }
                }
                _ => continue,
            };
            let name = p.name.as_ref().and_then(|n| {
                if n.contains("{i}") {
                    Some(n.replace("{i}", &(i + 1).to_string()))
                } else {
                    (i == 0).then(|| n.clone())
                }
            });
            parts.push(poly3d::SpecPart {
                shape,
                color,
                glow: p.glow,
                glass: p.glass,
                name,
                label_off: p.label.map(|[x, y]| (x, y)),
            });
        }
    }
    let flows = s
        .flows
        .iter()
        .map(|f| poly3d::SpecFlow {
            path: f.path.clone(),
            color: f
                .color
                .as_deref()
                .and_then(parse_color)
                .unwrap_or([1.0, 0.85, 0.35]),
            name: f.name.clone(),
        })
        .collect();
    poly3d::SpecScene { parts, flows }
}

/// `fl z check FILE...`: prints each file's errors; exit 1 if any file has one.
pub fn run_check(args: &[String]) -> i32 {
    if args.is_empty() {
        eprintln!("usage: fl z check FILE.json...");
        return 2;
    }
    let mut bad = false;
    for a in args {
        match load(Path::new(a)) {
            Ok(d) => println!(
                "ok  {a}: {:?}, {} parts",
                d.title,
                d.scene.as_ref().map_or(0, |s| s.parts.len())
            ),
            Err(errs) => {
                bad = true;
                println!("bad {a}:");
                for e in errs {
                    println!("  - {e}");
                }
            }
        }
    }
    i32::from(bad)
}

/// A diagram file drawn at `w` x `h` pixels with its own camera (the filing reader's
/// diagram panel). Err: the file does not load, or it has no 3D scene.
pub fn render_file(path: &Path, w: u32, h: u32, bg: [u8; 3]) -> Result<image::RgbaImage, String> {
    let d = load(path).map_err(|e| e.join("; "))?;
    let scene = d.scene.as_ref().ok_or("art-only diagram (no 3D scene)")?;
    let c = scene.camera.unwrap_or_default();
    let view = poly3d::View {
        yaw: c.yaw.to_radians(),
        pitch: c.pitch.to_radians().clamp(-0.3, 1.3),
        zoom: c.zoom.clamp(0.3, 6.0),
        pan: [0.0, 0.0],
    };
    Ok(poly3d::render_spec(&to_poly(scene), &view, 0.3, w as usize, h as usize, bg))
}

/// `fl z render FILE OUT.png`: the scene as the canvas draws it (default camera), so Claude
/// can look at its own picture before the user does.
pub fn run_render(args: &[String]) -> i32 {
    let (Some(file), Some(out)) = (args.first(), args.get(1)) else {
        eprintln!("usage: fl z render FILE.json OUT.png [ZOOM]");
        return 2;
    };
    let d = match load(Path::new(file)) {
        Ok(d) => d,
        Err(errs) => {
            for e in errs {
                eprintln!("  - {e}");
            }
            return 1;
        }
    };
    let Some(scene) = d.scene.as_ref() else {
        eprintln!("no scene in this diagram (art-only diagrams draw as text)");
        return 1;
    };
    let c = scene.camera.unwrap_or_default();
    // ZOOM multiplies the diagram's own zoom, as + and - do on the canvas
    let k = args.get(2).and_then(|z| z.parse::<f64>().ok()).unwrap_or(1.0);
    let view = poly3d::View {
        yaw: c.yaw.to_radians(),
        pitch: c.pitch.to_radians().clamp(-0.3, 1.3),
        zoom: (c.zoom * k).clamp(0.3, 6.0),
        pan: [0.0, 0.0],
    };
    let img = poly3d::render_spec(&to_poly(scene), &view, 0.3, 1200, 700, [0x28, 0x2a, 0x36]);
    match img.save(out) {
        Ok(()) => {
            println!("{out}");
            0
        }
        Err(e) => {
            eprintln!("can't write {out}: {e}");
            1
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const GOOD: &str = r##"{
      "title": "HBM stack",
      "caption": "8 DRAM dies on a base die, joined by TSVs",
      "scene": {
        "parts": [
          {"shape":"box","name":"base die","at":[0,0,0],"size":[10,1,8],"color":"dark"},
          {"shape":"box","name":"DRAM {i}","at":[0,1.2,0],"size":[10,0.8,8],"color":"blue","repeat":{"n":8,"step":[0,1,0]}},
          {"shape":"cylinder","name":"TSV","from":[3,0,0],"to":[3,9,0],"r":0.15,"color":"copper"},
          {"shape":"sphere","at":[0,-1,0],"r":0.3,"glass":true}
        ],
        "flows": [{"name":"data","path":[[3,0,0],[3,9,0]],"color":"#ffcc33"}]
      },
      "text": "why it matters"
    }"##;

    #[test]
    fn a_good_file_parses_and_repeats_expand() {
        let d = parse(GOOD).unwrap();
        let poly = to_poly(d.scene.as_ref().unwrap());
        assert_eq!(poly.parts.len(), 1 + 8 + 1 + 1);
        let names: Vec<String> = poly.parts.iter().filter_map(|p| p.name.clone()).collect();
        assert!(names.contains(&"DRAM 8".to_string()), "{names:?}");
        assert!(poly.flows.iter().any(|f| f.name.as_deref() == Some("data")));
    }

    #[test]
    fn errors_name_the_field_and_what_is_valid() {
        let errs = parse(r#"{"title":"x","scene":{"parts":[{"shape":"cone","at":[0,0,0]}]}}"#)
            .unwrap_err();
        assert!(
            errs[0].contains("scene.parts[0].shape") && errs[0].contains("cylinder"),
            "{errs:?}"
        );
        let errs = parse(r#"{"title":"x","scene":{"parts":[{"shape":"box","at":[0,0,0],"size":[1,1,1],"colour":"red"}]}}"#)
            .unwrap_err();
        assert!(errs[0].contains("unknown field `colour`"), "{errs:?}");
        // sections and zooms are gone from the format: a file that still has them says so
        let errs = parse(r#"{"title":"x","text":"t","sections":[{"title":"s"}]}"#).unwrap_err();
        assert!(errs[0].contains("unknown field `sections`"), "{errs:?}");
        let errs =
            parse(r#"{"title":"x","text":"t","zooms":[{"key":"a","title":"q","text":"t"}]}"#)
                .unwrap_err();
        assert!(errs[0].contains("unknown field `zooms`"), "{errs:?}");
    }

    #[test]
    fn labels_are_short_and_say_so() {
        let long = "x".repeat(MAX_LABEL + 1);
        let errs = parse(&format!(
            r#"{{"title":"x","scene":{{"parts":[{{"shape":"box","name":"{long}","at":[0,0,0],"size":[1,1,1]}}]}}}}"#
        ))
        .unwrap_err();
        assert!(
            errs[0].contains(".name:") && errs[0].contains("labels are at most"),
            "{errs:?}"
        );
        let ok = format!(
            r#"{{"title":"x","scene":{{"parts":[{{"shape":"box","name":"{}","at":[0,0,0],"size":[1,1,1]}}]}}}}"#,
            "x".repeat(MAX_LABEL)
        );
        assert!(parse(&ok).is_ok());
    }

    #[test]
    fn colors_by_name_or_hex() {
        assert_eq!(parse_color("#ff0000"), Some([1.0, 0.0, 0.0]));
        assert!(parse_color("Copper").is_some());
        assert!(parse_color("#fff").is_none());
        assert!(parse_color("mauve").is_none());
    }

    /// The format reference Claude gets must mention every shape, colour and field the
    /// parser accepts, or Claude can't use them.
    #[test]
    fn rules_document_the_format() {
        let rules = include_str!("z_rules.md");
        for word in [
            "box",
            "cylinder",
            "sphere",
            "repeat",
            "glow",
            "glass",
            "flows",
            "label",
            "camera",
            "fl z check",
            "one picture",
        ] {
            assert!(rules.contains(word), "z_rules.md lacks {word}");
        }
        for (n, _) in COLORS {
            assert!(rules.contains(n), "z_rules.md lacks colour {n}");
        }
    }
}
