// The 3D picture at the top of a memory R&D company page (dossier screen, "MEM:<TICKER>"):
// the selected tab names a diagrams node ("HBM STACK", "CELL", ...; py/derive/memory_page.py puts
// it in each section's `scene`), and this plays that node's Blender overview. Page scenes draw
// their beat text in a panel on the right of the frame; here the data below is the text, so the
// frame is rendered wide enough that its 3D part fills the slot and the panel is cropped off.

use std::time::{Duration, Instant};

use image::{DynamicImage, RgbaImage, imageops};
use pbr3d::math::V3;
use pbr3d::scene_gltf::Scene;
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui_image::picker::cap_parser::QueryStdioOptions;
use ratatui_image::picker::{Capability, Picker, ProtocolType};
use ratatui_image::protocol::kitty::StatefulKitty;
use ratatui_image::protocol::{StatefulProtocol, StatefulProtocolType};
use ratatui_image::{Resize, StatefulImage};
use serde::Deserialize;

use crate::ui::anim::Player;

/// Frames are re-rendered at most this often while a scene plays.
pub const FRAME: Duration = Duration::from_millis(100);
/// Inside tmux every frame (~180 KB of base64 for a full-width slot) is re-parsed and passed
/// through by tmux, so frames come less often there.
pub const FRAME_TMUX: Duration = Duration::from_millis(250);
/// Kitty image ids for the slot. Frames alternate between the two: the next frame uploads into the
/// id that is not on screen, and the cells switch to it only once the upload is complete, so the
/// picture is never blank while a replacement is in flight (which showed as flashing).
const IMAGE_IDS: [u32; 2] = [
    u32::from_be_bytes([0, 0xF1, 0x3E, 0x01]),
    u32::from_be_bytes([0, 0xF1, 0x3E, 0x02]),
];

/// What plays in the slot: a diagrams node's overview, or a custom memory-page GLB.
enum Source {
    Node(Player),
    Glb(std::sync::Arc<pbr3d::scene_gltf::Scene>),
}

/// Custom memory-page scenes (tools/pbr3d/blender/mem_*.py) are 3 beats of 8 s.
pub const GLB_LOOP_SECS: f32 = 24.0;

/// How long a flight to a map site (or back to the overview) takes.
pub const FLIGHT: Duration = Duration::from_millis(1600);
/// The camera over a site: this far above the land (degrees of the view's elevation).
const SITE_PITCH: f32 = 0.9;

/// Where custom scenes live; read at runtime so new scenes need no rebuild.
fn glb_path(name: &str) -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../tools/pbr3d/assets")
        .join(format!("{name}.glb"))
}

/// Parsed custom scenes, kept for the life of the process.
fn load_glb(name: &str) -> Option<std::sync::Arc<pbr3d::scene_gltf::Scene>> {
    use std::collections::HashMap;
    use std::sync::{Arc, Mutex, OnceLock};
    static CACHE: OnceLock<Mutex<HashMap<String, Arc<pbr3d::scene_gltf::Scene>>>> = OnceLock::new();
    let cache = CACHE.get_or_init(|| Mutex::new(HashMap::new()));
    if let Some(s) = cache.lock().ok()?.get(name) {
        return Some(s.clone());
    }
    let bytes = std::fs::read(glb_path(name)).ok()?;
    let scene = Arc::new(pbr3d::scene_gltf::Scene::from_glb(&bytes).ok()?);
    cache.lock().ok()?.insert(name.to_string(), scene.clone());
    Some(scene)
}

/// A custom scene at `secs`, `w` x `h`, with its `label:` tags pinned on (no caption panel).
pub fn glb_frame(scene: &pbr3d::scene_gltf::Scene, secs: f32, w: u32, h: u32) -> RgbaImage {
    let mut img = pbr3d::scene_gltf::render(scene, secs, w, h, crate::screens::diagrams_px::BG);
    let mut tags = pbr3d::caption::Tags::new();
    for (text, p) in scene.labels(secs) {
        if let Some((x, y)) = pbr3d::scene_gltf::project(scene, secs, w, h, p) {
            tags.add(&mut img, x, y, &text, w, h);
        }
    }
    img
}

/// A camera: eye and look-at target.
type View = (V3, V3);

/// One site of an interactive map: its text from `<scene>.sites.json`, its place in the scene.
#[derive(Debug, Clone, Deserialize)]
pub struct SiteText {
    pub id: String,
    pub name: String,
    pub text: String,
    pub src: String,
    /// The camera's distance from the site when flown to, in scene units.
    pub dist: f32,
}

#[derive(Deserialize)]
struct SiteFile {
    sites: Vec<SiteText>,
}

struct MapSite {
    text: SiteText,
    pos: V3,
}

/// An interactive map scene: the sites, which one is selected, and the camera. The camera holds
/// the overview until a flight to the selected site (Enter) or back home (o) ends.
struct Map {
    sites: Vec<MapSite>,
    overview: View,
    selected: usize,
    /// The site the camera is heading to; None is the overview.
    goal: Option<usize>,
    /// The view a flight started from, and when it started.
    flight: Option<(View, Instant)>,
    /// The view drawn last, the start of the next flight.
    shown: Option<View>,
}

/// What the caption under an interactive map shows.
pub struct MapCaption<'a> {
    /// 0-based index of the selected site, and how many there are.
    pub index: usize,
    pub count: usize,
    pub site: &'a SiteText,
    /// The camera is on this site (or is flying there).
    pub here: bool,
    pub flying: bool,
}

impl Map {
    /// The map for scene `name` (a `mem/` GLB): sites from its `.sites.json` sidecar, placed by
    /// the scene's `site:<id>` empties. None when there is no sidecar or no site matches.
    fn load(name: &str, scene: &Scene) -> Option<Map> {
        let path = glb_path(name).with_extension("sites.json");
        let file: SiteFile = serde_json::from_slice(&std::fs::read(path).ok()?).ok()?;
        let at = scene.sites(0.0);
        let sites: Vec<MapSite> = file
            .sites
            .into_iter()
            .filter_map(|text| {
                let pos = at.iter().find(|(id, _)| *id == text.id)?.1;
                Some(MapSite { text, pos })
            })
            .collect();
        if sites.is_empty() {
            return None;
        }
        let overview = scene
            .camera(0.0)
            .unwrap_or(([0.0, 500.0, 3000.0], [0.0, 0.0, 0.0]));
        Some(Map {
            sites,
            overview,
            selected: 0,
            goal: None,
            flight: None,
            shown: None,
        })
    }

    /// The camera over a site: `dist` away, SITE_PITCH above the land, looking at the site.
    fn site_view(site: &MapSite) -> View {
        let target = [site.pos[0], site.pos[1] + 4.0, site.pos[2]];
        let (d, cp, sp) = (site.text.dist, SITE_PITCH.cos(), SITE_PITCH.sin());
        ([target[0], target[1] + d * sp, target[2] + d * cp], target)
    }

    fn goal_view(&self) -> View {
        match self.goal {
            Some(i) => Self::site_view(&self.sites[i]),
            None => self.overview,
        }
    }

    /// The view to draw now: the goal, or part of the way there during a flight.
    fn view(&mut self) -> View {
        let goal = self.goal_view();
        let view = match self.flight {
            Some((from, start)) => {
                let u = (start.elapsed().as_secs_f32() / FLIGHT.as_secs_f32()).min(1.0);
                if u >= 1.0 {
                    self.flight = None;
                    goal
                } else {
                    let e = u * u * (3.0 - 2.0 * u);
                    (lerp(from.0, goal.0, e), lerp(from.1, goal.1, e))
                }
            }
            None => goal,
        };
        self.shown = Some(view);
        view
    }

    /// Head for `goal` (a site, or None for the overview) from wherever the camera is now.
    fn go(&mut self, goal: Option<usize>) {
        if self.goal == goal {
            return;
        }
        self.flight = Some((self.shown.unwrap_or(self.overview), Instant::now()));
        self.goal = goal;
    }

    /// The selected site's name, pinned in the picture at the site.
    fn tag(&self) -> (String, V3) {
        let s = &self.sites[self.selected];
        (s.text.name.clone(), s.pos)
    }
}

fn lerp(a: V3, b: V3, t: f32) -> V3 {
    [
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ]
}

/// A map frame at `secs` from `view`, with the selected site's name pinned on it.
fn map_frame(scene: &Scene, secs: f32, view: View, tag: (String, V3), w: u32, h: u32) -> RgbaImage {
    let mut img = pbr3d::scene_gltf::render_view(
        scene,
        secs,
        Some(view),
        w,
        h,
        crate::screens::diagrams_px::BG,
    );
    let (text, p) = tag;
    if let Some((x, y)) = pbr3d::scene_gltf::project_view(scene, secs, Some(view), w, h, p) {
        pbr3d::caption::Tags::new().add(&mut img, x, y, &text, w, h);
    }
    img
}

struct Slot {
    page: String,
    source: Source,
    /// Set for a map scene (its GLB has `site:` empties and a sites sidecar).
    map: Option<Map>,
    start: Instant,
    proto: Option<StatefulProtocol>,
    sent: Option<Instant>,
    px: (u32, u32),
    /// Frames sent so far; its parity picks the image id.
    frames: u64,
}

#[derive(Default)]
pub struct MemoryScene {
    picker: Option<Picker>,
    slot: Option<Slot>,
}

impl MemoryScene {
    /// Queries the terminal's graphics support. Terminals without a pixel protocol get no picture
    /// (the page is still the data); call before the event loop reads stdin, like intraday does.
    pub fn query() -> Self {
        let options = QueryStdioOptions {
            kitty_compression: true,
            ..Default::default()
        };
        let picker = Picker::from_query_stdio_with_options(options)
            .ok()
            .filter(|p| p.protocol_type() != ProtocolType::Halfblocks);
        Self { picker, slot: None }
    }

    #[cfg(test)]
    pub fn with_picker(picker: Picker) -> Self {
        Self {
            picker: Some(picker),
            slot: None,
        }
    }

    /// The node playing now, if any.
    pub fn page(&self) -> Option<&str> {
        self.slot.as_ref().map(|s| s.page.as_str())
    }

    /// Switch to `page` (a diagrams node with a Blender overview); None or an unknown node clears.
    pub fn set_page(&mut self, page: Option<&str>) {
        if self.page() == page {
            return;
        }
        self.slot = page.and_then(|p| {
            let start = Instant::now();
            // "mem/<company>_<tab>" = a custom scene; anything else is a diagrams node
            let (source, map) = if p.starts_with("mem/") {
                let scene = load_glb(p)?;
                let map = Map::load(p, &scene);
                (Source::Glb(scene), map)
            } else {
                (
                    Source::Node(Player::new(super::diagrams_nodes::overview(p)?, start)),
                    None,
                )
            };
            Some(Slot {
                page: p.to_string(),
                source,
                map,
                start,
                proto: None,
                sent: None,
                px: (0, 0),
                frames: 0,
            })
        });
    }

    fn map_mut(&mut self) -> Option<&mut Map> {
        self.slot.as_mut()?.map.as_mut()
    }

    /// Whether the page is an interactive map (its keys are the map's: [ ] o and Enter).
    pub fn is_map(&self) -> bool {
        self.slot.as_ref().is_some_and(|s| s.map.is_some())
    }

    /// Select the site `delta` along from the current one (wrapping). Does not fly.
    pub fn map_step(&mut self, delta: isize) {
        if let Some(m) = self.map_mut() {
            let n = m.sites.len() as isize;
            m.selected = (m.selected as isize + delta).rem_euclid(n) as usize;
        }
    }

    /// Fly the camera to the selected site.
    pub fn map_fly(&mut self) {
        if let Some(m) = self.map_mut() {
            let i = m.selected;
            m.go(Some(i));
        }
    }

    /// Fly the camera back to the overview of the whole map.
    pub fn map_home(&mut self) {
        if let Some(m) = self.map_mut() {
            m.go(None);
        }
    }

    /// The caption for the selected site, when the page is a map.
    pub fn map_caption(&self) -> Option<MapCaption<'_>> {
        let m = self.slot.as_ref()?.map.as_ref()?;
        Some(MapCaption {
            index: m.selected,
            count: m.sites.len(),
            site: &m.sites[m.selected].text,
            here: m.goal == Some(m.selected),
            flying: m.flight.is_some(),
        })
    }

    /// How often frames are rendered and sent: slower inside tmux.
    pub fn frame_interval(&self) -> Duration {
        if self.picker.as_ref().is_some_and(|p| p.tmux_detected()) {
            FRAME_TMUX
        } else {
            FRAME
        }
    }

    /// Whether a scene is playing (the screen keeps redrawing while it is).
    pub fn playing(&self) -> bool {
        self.picker.is_some() && self.slot.is_some()
    }

    /// Draws the current frame into `area`, rendering a new one when FRAME has passed or the
    /// slot changed size.
    pub fn draw(&mut self, frame: &mut Frame, area: Rect) {
        let (Some(picker), Some(slot)) = (self.picker.as_ref(), self.slot.as_mut()) else {
            return;
        };
        if area.width < 4 || area.height < 2 {
            return;
        }
        let font = picker.font_size();
        let px = (
            area.width as u32 * font.width as u32,
            area.height as u32 * font.height as u32,
        );
        let every = if picker.tmux_detected() {
            FRAME_TMUX
        } else {
            FRAME
        };
        let due = slot.sent.is_none_or(|t| t.elapsed() >= every) || slot.px != px;
        if due {
            let img = match &slot.source {
                Source::Node(player) => {
                    let t = player.time_at(slot.start.elapsed().as_millis() as u64);
                    scene_frame(player, &t, px)
                }
                Source::Glb(scene) => {
                    let secs = slot.start.elapsed().as_secs_f32() % GLB_LOOP_SECS;
                    let (w, h) = (px.0.max(1), px.1.max(1));
                    match slot.map.as_mut() {
                        Some(map) => {
                            let view = map.view();
                            Some(map_frame(scene, secs, view, map.tag(), w, h))
                        }
                        None => Some(glb_frame(scene, secs, w, h)),
                    }
                }
            };
            if let Some(img) = img {
                let id = IMAGE_IDS[(slot.frames % 2) as usize];
                slot.proto = Some(protocol(picker, DynamicImage::ImageRgba8(img), id));
                slot.frames += 1;
                slot.sent = Some(Instant::now());
                slot.px = px;
            }
        }
        if let Some(p) = slot.proto.as_mut() {
            frame.render_stateful_widget(
                StatefulImage::default().resize(Resize::Fit(None)),
                area,
                p,
            );
        }
    }
}

/// The scene's 3D part at `px`: the page frame is rendered so its scene width (the frame minus
/// the caption panel) is px.0, then the panel is cropped off.
pub fn scene_frame(
    player: &Player,
    t: &crate::ui::anim::Time,
    px: (u32, u32),
) -> Option<RgbaImage> {
    let (w, h) = (px.0.max(1), px.1.max(1));
    let full_w = ((w as f32) / (1.0 - pbr3d::caption::PANEL_FRAC)).ceil() as u32;
    let mut img = player.pixels(t, full_w, h)?;
    let sw = pbr3d::caption::scene_width(full_w).min(img.width());
    let sh = h.min(img.height());
    Some(imageops::crop(&mut img, 0, 0, sw, sh).to_image())
}

fn protocol(picker: &Picker, img: DynamicImage, id: u32) -> StatefulProtocol {
    if picker.protocol_type() != ProtocolType::Kitty {
        return picker.new_resize_protocol(img);
    }
    let caps = picker.capabilities();
    StatefulProtocol::new(
        img,
        picker.font_size(),
        None,
        StatefulProtocolType::Kitty(StatefulKitty::new(
            id,
            picker.tmux_detected(),
            caps.contains(&Capability::KittyCompression),
            caps.contains(&Capability::KittySharedMemory),
        )),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Every scene the memory pages name (py/derive/memory_page.py SCENE_RULES) has a Blender
    /// overview, and its 3D part renders at the slot size with the caption panel cropped off.
    #[test]
    fn every_page_scene_renders_cropped() {
        for page in [
            "HBM STACK",
            "CELL",
            "BANK",
            "ARRAY",
            "BANDWIDTH",
            "WAFER",
            "LITHO",
            "ASSEMBLY",
        ] {
            let scene = crate::screens::diagrams_nodes::overview(page)
                .unwrap_or_else(|| panic!("{page}: no Blender overview"));
            let player = Player::new(scene, Instant::now());
            let t = player.time_at(1500);
            let img = scene_frame(&player, &t, (480, 240)).expect("a picture scene");
            assert_eq!(img.height(), 240, "{page}");
            assert!(
                (478..=482).contains(&img.width()),
                "{page}: 3D part only, width {}",
                img.width()
            );
            if let Ok(dir) = std::env::var("FL_SCENE_DIR") {
                img.save(format!("{dir}/{}.png", page.replace(' ', "_")))
                    .unwrap();
            }
        }
    }

    /// Preview a custom scene exactly as the slot draws it (wide, about 3:1):
    /// `FL_MEM_GLB=mem/sk_hynix_hbm FL_SCENE_DIR=<dir> cargo test --release mem_glb_dump`
    /// writes <dir>/<name>_b<beat>_<t>.png for each beat at 0.2 / 0.5 / 0.85 and a sheet.png.
    #[test]
    fn mem_glb_dump() {
        let (Ok(name), Ok(dir)) = (std::env::var("FL_MEM_GLB"), std::env::var("FL_SCENE_DIR"))
        else {
            return;
        };
        let scene =
            load_glb(&name).unwrap_or_else(|| panic!("{name}: no GLB at {:?}", glb_path(&name)));
        let (w, h) = (1140, 380);
        let mut sheet = RgbaImage::new(w * 3, h * 3);
        let stem = name.trim_start_matches("mem/");
        for beat in 0..3u32 {
            for (j, u) in [0.2f32, 0.5, 0.85].iter().enumerate() {
                let img = glb_frame(&scene, (beat as f32 + u) * 8.0, w, h);
                img.save(format!("{dir}/{stem}_b{beat}_{j}.png")).unwrap();
                imageops::overlay(&mut sheet, &img, (j as u32 * w) as i64, (beat * h) as i64);
            }
        }
        let small = imageops::resize(&sheet, w * 3 / 2, h * 3 / 2, imageops::FilterType::Triangle);
        small.save(format!("{dir}/{stem}_sheet.png")).unwrap();
    }

    /// Every custom scene a memory page names (tools/pbr3d/assets/mem/*.glb) loads and renders.
    #[test]
    fn every_custom_scene_named_by_a_page_loads() {
        let pages = [
            include_str!("fixtures/memory_SNDK.json"),
            include_str!("fixtures/memory_000660_KS.json"),
            include_str!("fixtures/memory_005930_KS.json"),
            include_str!("fixtures/memory_MU.json"),
            include_str!("fixtures/memory_688825_SS.json"),
            include_str!("fixtures/memory_YMTC.json"),
        ];
        let mut n = 0;
        for json in pages {
            let doc: serde_json::Value = serde_json::from_str(json).unwrap();
            for s in doc["sections"].as_array().unwrap() {
                let name = s["scene"].as_str().unwrap_or("");
                if let Some(rest) = name.strip_prefix("mem/") {
                    let scene =
                        load_glb(name).unwrap_or_else(|| panic!("{rest}: GLB missing or invalid"));
                    let img = glb_frame(&scene, 12.0, 240, 80);
                    assert_eq!(img.dimensions(), (240, 80), "{rest}");
                    n += 1;
                }
            }
        }
        assert!(n >= 60, "custom scenes found: {n}");
    }

    /// The fabs map of SK hynix: every site in the sidecar is placed by a `site:` empty.
    #[test]
    fn fabs_map_places_every_site() {
        let mut s = MemoryScene::default();
        s.set_page(Some("mem/sk_hynix_fabs"));
        assert!(s.is_map());
        let c = s.map_caption().expect("a map caption");
        assert_eq!(c.count, 11);
        assert_eq!(c.index, 0);
        assert!(!c.here && !c.flying, "starts at the overview");
        for site in s.slot.as_ref().unwrap().map.as_ref().unwrap().sites.iter() {
            assert!(
                site.text.dist > 40.0,
                "{}: flight distance past the near plane",
                site.text.id
            );
            assert!(
                !site.text.text.is_empty() && !site.text.src.is_empty(),
                "{}",
                site.text.id
            );
        }
    }

    #[test]
    fn map_keys_step_wrap_and_fly() {
        let mut s = MemoryScene::default();
        s.set_page(Some("mem/sk_hynix_fabs"));
        s.map_step(-1);
        assert_eq!(
            s.map_caption().unwrap().index,
            10,
            "wraps back to the last site"
        );
        s.map_step(1);
        assert_eq!(s.map_caption().unwrap().index, 0);
        s.map_step(1);
        s.map_fly();
        let c = s.map_caption().unwrap();
        assert!(c.here && c.flying, "Enter heads for the selected site");
        assert_eq!(c.index, 1);
        s.map_home();
        assert!(!s.map_caption().unwrap().here, "o heads home");
    }

    /// A finished flight sits exactly on its goal, and the overview is the scene's own camera.
    #[test]
    fn map_flight_lands_on_its_goal() {
        let mut s = MemoryScene::default();
        s.set_page(Some("mem/sk_hynix_fabs"));
        s.map_step(2);
        s.map_fly();
        let m = s.map_mut().unwrap();
        m.flight = m
            .flight
            .map(|(from, _)| (from, Instant::now() - FLIGHT * 2));
        let v = m.view();
        assert!(m.flight.is_none());
        assert_eq!(v, Map::site_view(&m.sites[2]));
        s.map_home();
        let m = s.map_mut().unwrap();
        m.flight = m
            .flight
            .map(|(from, _)| (from, Instant::now() - FLIGHT * 2));
        assert_eq!(m.view(), m.overview);
    }

    /// `FL_MAP_DUMP=<dir> cargo test --release fabs_map_dump`: the overview and each site's flight
    /// end, drawn at the slot size, as <dir>/map_<id>.png for a visual check.
    #[test]
    fn fabs_map_dump() {
        let Ok(dir) = std::env::var("FL_MAP_DUMP") else {
            return;
        };
        let scene = load_glb("mem/sk_hynix_fabs").expect("fabs map GLB");
        let map = Map::load("mem/sk_hynix_fabs", &scene).expect("fabs map sites");
        let (w, h) = (1140, 380);
        let mut views = vec![("overview".to_string(), map.overview, None)];
        for (i, site) in map.sites.iter().enumerate() {
            views.push((site.text.id.clone(), Map::site_view(site), Some(i)));
        }
        for (name, view, sel) in views {
            let tag = match sel {
                Some(i) => (map.sites[i].text.name.clone(), map.sites[i].pos),
                None => ("".to_string(), [0.0, 0.0, 0.0]),
            };
            let img = if sel.is_some() {
                map_frame(&scene, 0.0, view, tag, w, h)
            } else {
                pbr3d::scene_gltf::render_view(
                    &scene,
                    0.0,
                    Some(view),
                    w,
                    h,
                    crate::screens::diagrams_px::BG,
                )
            };
            img.save(format!("{dir}/map_{name}.png")).unwrap();
        }
    }

    #[test]
    fn set_page_ignores_unknown_nodes() {
        let mut s = MemoryScene::default();
        s.set_page(Some("NOT A NODE"));
        assert!(s.page().is_none());
        s.set_page(Some("HBM STACK"));
        assert_eq!(s.page(), Some("HBM STACK"));
        assert!(
            !s.playing(),
            "no picker in tests = no picture, page still shows data"
        );
    }
}
