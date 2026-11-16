// The 3D picture at the top of a memory R&D company page (dossier screen, "MEM:<TICKER>"):
// the selected tab names a diagrams node ("HBM STACK", "CELL", ...; py/derive/memory_page.py puts
// it in each section's `scene`), and this plays that node's Blender overview. Page scenes draw
// their beat text in a panel on the right of the frame; here the data below is the text, so the
// frame is rendered wide enough that its 3D part fills the slot and the panel is cropped off.

use std::time::{Duration, Instant};

use image::{DynamicImage, RgbaImage, imageops};
use ratatui::Frame;
use ratatui::layout::Rect;
use ratatui_image::picker::cap_parser::QueryStdioOptions;
use ratatui_image::picker::{Capability, Picker, ProtocolType};
use ratatui_image::protocol::kitty::StatefulKitty;
use ratatui_image::protocol::{StatefulProtocol, StatefulProtocolType};
use ratatui_image::{Resize, StatefulImage};

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

struct Slot {
    page: String,
    source: Source,
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
            let source = if p.starts_with("mem/") {
                Source::Glb(load_glb(p)?)
            } else {
                Source::Node(Player::new(super::diagrams_nodes::overview(p)?, start))
            };
            Some(Slot {
                page: p.to_string(),
                source,
                start,
                proto: None,
                sent: None,
                px: (0, 0),
                frames: 0,
            })
        });
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
        let px = (area.width as u32 * font.width as u32, area.height as u32 * font.height as u32);
        let every = if picker.tmux_detected() { FRAME_TMUX } else { FRAME };
        let due = slot.sent.is_none_or(|t| t.elapsed() >= every) || slot.px != px;
        if due {
            let img = match &slot.source {
                Source::Node(player) => {
                    let t = player.time_at(slot.start.elapsed().as_millis() as u64);
                    scene_frame(player, &t, px)
                }
                Source::Glb(scene) => {
                    let secs = slot.start.elapsed().as_secs_f32() % GLB_LOOP_SECS;
                    Some(glb_frame(scene, secs, px.0.max(1), px.1.max(1)))
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
            frame.render_stateful_widget(StatefulImage::default().resize(Resize::Fit(None)), area, p);
        }
    }
}

/// The scene's 3D part at `px`: the page frame is rendered so its scene width (the frame minus
/// the caption panel) is px.0, then the panel is cropped off.
pub fn scene_frame(player: &Player, t: &crate::ui::anim::Time, px: (u32, u32)) -> Option<RgbaImage> {
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
        for page in ["HBM STACK", "CELL", "BANK", "ARRAY", "BANDWIDTH", "WAFER", "LITHO", "ASSEMBLY"] {
            let scene = crate::screens::diagrams_nodes::overview(page)
                .unwrap_or_else(|| panic!("{page}: no Blender overview"));
            let player = Player::new(scene, Instant::now());
            let t = player.time_at(1500);
            let img = scene_frame(&player, &t, (480, 240)).expect("a picture scene");
            assert_eq!(img.height(), 240, "{page}");
            assert!((478..=482).contains(&img.width()), "{page}: 3D part only, width {}", img.width());
            if let Ok(dir) = std::env::var("FL_SCENE_DIR") {
                img.save(format!("{dir}/{}.png", page.replace(' ', "_"))).unwrap();
            }
        }
    }

    /// Preview a custom scene exactly as the slot draws it (wide, about 3:1):
    /// `FL_MEM_GLB=mem/sk_hynix_hbm FL_SCENE_DIR=<dir> cargo test --release mem_glb_dump`
    /// writes <dir>/<name>_b<beat>_<t>.png for each beat at 0.2 / 0.5 / 0.85 and a sheet.png.
    #[test]
    fn mem_glb_dump() {
        let (Ok(name), Ok(dir)) = (std::env::var("FL_MEM_GLB"), std::env::var("FL_SCENE_DIR")) else {
            return;
        };
        let scene = load_glb(&name).unwrap_or_else(|| panic!("{name}: no GLB at {:?}", glb_path(&name)));
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
                    let scene = load_glb(name).unwrap_or_else(|| panic!("{rest}: GLB missing or invalid"));
                    let img = glb_frame(&scene, 12.0, 240, 80);
                    assert_eq!(img.dimensions(), (240, 80), "{rest}");
                    n += 1;
                }
            }
        }
        assert!(n >= 60, "custom scenes found: {n}");
    }

    #[test]
    fn set_page_ignores_unknown_nodes() {
        let mut s = MemoryScene::default();
        s.set_page(Some("NOT A NODE"));
        assert!(s.page().is_none());
        s.set_page(Some("HBM STACK"));
        assert_eq!(s.page(), Some("HBM STACK"));
        assert!(!s.playing(), "no picker in tests = no picture, page still shows data");
    }
}
