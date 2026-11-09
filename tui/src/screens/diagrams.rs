// `fl diagrams [name]`: explainer diagrams (chip fab, fiber optics, data
// center power and cooling) as box-drawing art, one tab each.
//
//   fl diagrams                 browse
//   fl diagrams fiber           open on the tab whose name starts with "fiber"
//   fl diagrams pdf [dir]       headless: write one PDF per diagram (default ./diagrams-pdf)
//
// The art lives in diagrams_art.rs as plain text; this file colours it by
// character class so the same lines draw in the TUI and in the PDF export.

use std::io;
use std::path::Path;
use std::process::Command;
use std::time::{Duration, Instant};

use crate::ui::anim::Scene;
use ratatui::Frame;
use ratatui::buffer::Buffer;
use ratatui::crossterm::event::{KeyCode, KeyEvent, KeyModifiers};
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, Paragraph, Widget, Wrap};

use super::diagrams_anim::{orbitable, scene_for, section_anim};
use super::diagrams_art::{DIAGRAMS, Diagram};
use super::diagrams_desc::{cards, describe, page_key, visual};
use super::diagrams_mol::{Mol, mol_for};
use super::diagrams_scene_cell::zoom_scene;
use super::diagrams_scene_litho::zoom_scene as litho_zoom_scene;
use super::diagrams_scene_array::zoom_scene as array_zoom_scene;
use super::diagrams_scene_bank::zoom_scene as bank_zoom_scene;
use super::diagrams_scene_bandwidth::zoom_scene as bw_zoom_scene;
use super::diagrams_scene_hbm::zoom_scene as hbm_zoom_scene;
use super::diagrams_scene_poly_zoom::bell_jar_anim;
use super::diagrams_vis::{Placed, step as vis_step, visual_for};
use crate::app::{Action, Ctx, Screen};
use crate::ui::anim::Player;
use crate::ui::help::{Key, key, render_footer, render_overlay};
use crate::ui::text;
use crate::ui::theme::Theme;
use image::{DynamicImage, RgbaImage};
use ratatui_image::picker::cap_parser::QueryStdioOptions;
use ratatui_image::picker::{Picker, ProtocolType};
use ratatui_image::protocol::kitty::StatefulKitty;
use ratatui_image::protocol::{StatefulProtocol, StatefulProtocolType};
use ratatui_image::{FontSize, Resize, StatefulImage};

/// How long the auto-tour rests on each visual spot / atom before moving on.
const TOUR_MS: u128 = 2200;
/// Redraw interval while a page animation plays (~12 fps).
const FRAME: Duration = Duration::from_millis(80);

const KEYS: &[Key] = &[
    key("h/l", "previous / next node"),
    key("j/k", "node below / above (scrolls if none)"),
    key("tab/S-tab", "next / previous node"),
    key("enter", "open selected node's page"),
    key("H/L, [/]", "previous / next diagram"),
    key("1-6", "jump to diagram"),
    key("g/G", "top / bottom"),
    key("?", "this help"),
    key("q", "back"),
];

/// Where the cursor is inside a detail card: atom grid, a pane's tab strip, or its text.
#[derive(Clone, Copy, PartialEq)]
enum Focus {
    Grid,
    Tabs,
    Text,
    Visual,
}

/// What the node popup is showing. Pages with an animation open on the
/// full-size overview; the sections menu leads into the old pane view.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum PopupView {
    Overview,
    /// A close-up scene opened from the overview.
    Zoom,
    /// A zoom's 3D model, full screen; hjkl orbit it.
    Full,
    Menu,
    Pane,
}

pub struct Diagrams {
    theme: Theme,
    tab: usize,
    scroll: u16,
    body_h: u16,
    help: bool,
    nodes: Vec<Vec<Node>>,
    sel: usize,
    popup: bool,
    popup_scroll: u16,
    view: PopupView,
    menu_sel: usize,
    /// Scroll of the beat notes beside an animation (j/k), and the beat they were last scrolled on.
    notes_scroll: u16,
    notes_beat: Option<usize>,
    /// The open zoom-in: (index in the scene's zooms, its player).
    zoom: Option<(usize, Player)>,
    /// The open animation is a numbered section, not a zoom-in.
    zoom_section: bool,
    /// The animation previewed beside the menu: (menu row, its player).
    preview: Option<(usize, Player)>,
    /// The menu's right-hand preview (on) or the plain list (off); m toggles it.
    browse: bool,
    /// Active page section (pane) in the node popup.
    pane: usize,
    /// When the popup opened; drives the page animation's clock.
    anim_start: Instant,
    /// The open page's animation, keyed by page; `None` inside = page has none.
    player: Option<(&'static str, Option<Player>)>,
    /// Clock for the detail card's auto-tour: visual spots and atoms cycle on
    /// their own until the cursor moves into them, which freezes the tour.
    tour_start: Instant,
    hots: Vec<Hot>,
    hsel: usize,
    hot_moved: bool,
    detail: bool,
    /// Detail card sections (`# heading` split), tab, scroll and cursor.
    secs: Vec<(&'static str, &'static str)>,
    ptab: usize,
    pscroll: u16,
    /// Cursor row (wrapped line) in the text.
    pcur: u16,
    focus: Focus,
    /// Selected spot in the right-hand visual.
    vcur: usize,
    /// First visible row of the right-hand visual (J/K, follows the cursor).
    vscroll: u16,
    mol: Option<Mol>,
    /// New-template card (big top visual + sub sections), when one exists.
    card: Option<&'static super::diagrams_cards::Card>,
    mol_cur: usize,
    /// Terminal graphics: kitty when the terminal has it, else half-blocks.
    picker: Picker,
    /// Full-screen 3D camera (kept between opens; `0` resets it) and its last render.
    orbit: poly3d::View,
    full: Option<FullFrame>,
    /// Which of the two kitty image ids the next frame uses (see FULL_IMAGE_ID).
    full_turn: bool,
    /// Camera key held: its canonical key and last press. `live_until` is set while
    /// key repeat drives motion; `last_tick` is when the camera last advanced.
    held: Option<(char, Instant)>,
    live_until: Option<Instant>,
    last_tick: Instant,
    /// Until then the 3D view renders at motion resolution: set by every camera key, so
    /// taps and the gap before key repeat starts are as quick as held motion. One sharp
    /// frame follows once it passes.
    settle_until: Option<Instant>,
    /// SETTLE just passed: draw once more so the sharp frame shows even when paused.
    sharpen: bool,
}

/// What a 3D zoom draws: the bell jar, or one of the CELL page's focused scenes at a
/// beat and a position through it.
#[derive(Clone, Copy)]
enum Model {
    Jar(poly3d::Anim),
    Cell(poly3d::CellZoom, usize, f64),
    /// the CELL overview, with its notes on the picture
    CellOverview(crate::ui::anim::Time),
    /// one of the LITHO page's focused scenes at a beat and a position through it
    Litho(poly3d::LithoZoom, usize, f64),
    /// the LITHO overview, with its notes on the picture
    LithoOverview(crate::ui::anim::Time),
    /// one of the ARRAY page's focused scenes at a beat and a position through it
    Array(poly3d::ArrayZoom, usize, f64),
    /// the ARRAY overview, with its notes on the picture
    ArrayOverview(crate::ui::anim::Time),
    /// one of the BANK page's focused scenes at a beat and a position through it
    Bank(poly3d::BankZoom, usize, f64),
    /// the BANK overview, with its notes on the picture
    BankOverview(crate::ui::anim::Time),
    /// one of the BANDWIDTH page's focused scenes at a beat and a position through it
    Bw(poly3d::BwZoom, usize, f64),
    /// the BANDWIDTH overview, with its notes on the picture
    BwOverview(crate::ui::anim::Time),
    /// one of the HBM STACK page's focused scenes at a beat and a position through it
    Hbm(poly3d::HbmZoom, usize, f64),
    /// the HBM STACK overview, with its notes on the picture
    HbmOverview(crate::ui::anim::Time),
    /// a Chip-tab scene: its keyframes at a beat and a position through it
    Chip(&'static [poly3d::ChipKey], usize, f64),
    /// a Chip-tab overview: its beats (for the notes), keyframes, and time
    ChipOverview(&'static [crate::ui::anim::Beat], &'static [poly3d::ChipKey], crate::ui::anim::Time),
    /// a Packaging-tab scene: its keyframes at a beat and a position through it
    Pkg(&'static [poly3d::PkgKey], usize, f64),
    /// a Packaging-tab overview: its beats (for the notes), keyframes, and time
    PkgOverview(&'static [crate::ui::anim::Beat], &'static [poly3d::PkgKey], crate::ui::anim::Time),
    /// a Fiber-tab scene: its keyframes at a beat and a position through it
    Link(&'static [poly3d::LinkKey], usize, f64),
    /// a Fiber-tab overview: its beats (for the notes), keyframes, and time
    LinkOverview(&'static [crate::ui::anim::Beat], &'static [poly3d::LinkKey], crate::ui::anim::Time),
    /// a Power-tab scene: its keyframes at a beat and a position through it
    Pwr(&'static [poly3d::PwrKey], usize, f64),
    /// a Power-tab overview: its beats (for the notes), keyframes, and time
    PwrOverview(&'static [crate::ui::anim::Beat], &'static [poly3d::PwrKey], crate::ui::anim::Time),
}

/// The 3D model of zoom `key` on `page`, at the zoom's clock.
fn model_at(page: &str, key: char, t: &crate::ui::anim::Time) -> Model {
    match page {
        "CELL" => match zoom_scene(key) {
            Some(z) => Model::Cell(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        "LITHO" => match litho_zoom_scene(key) {
            Some(z) => Model::Litho(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        "ARRAY" => match array_zoom_scene(key) {
            Some(z) => Model::Array(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        "BANK" => match bank_zoom_scene(key) {
            Some(z) => Model::Bank(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        "BANDWIDTH" => match bw_zoom_scene(key) {
            Some(z) => Model::Bw(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        "HBM STACK" => match hbm_zoom_scene(key) {
            Some(z) => Model::Hbm(z, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        _ if super::diagrams_scene_chip::node(page).is_some() => match super::diagrams_scene_chip::keys_for(page, key) {
            Some(k) => Model::Chip(k, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        _ if super::diagrams_scene_pkg::node(page).is_some() => match super::diagrams_scene_pkg::keys_for(page, key) {
            Some(k) => Model::Pkg(k, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        _ if super::diagrams_scene_link::node(page).is_some() => match super::diagrams_scene_link::keys_for(page, key) {
            Some(k) => Model::Link(k, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        _ if super::diagrams_scene_pwr::node(page).is_some() => match super::diagrams_scene_pwr::keys_for(page, key) {
            Some(k) => Model::Pwr(k, t.beat, f64::from(t.local)),
            None => Model::Jar(bell_jar_anim(t)),
        },
        _ => Model::Jar(bell_jar_anim(t)),
    }
}

/// A model's state, quantised, with a slot telling the jar from the cell.
type ModelKey = [i64; 8];

fn model_key(m: Model) -> ModelKey {
    match m {
        Model::Jar(a) => {
            let mut k = [0i64; 8];
            k[..7].copy_from_slice(&scene_key(a));
            k
        }
        Model::Cell(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 1]
        }
        Model::CellOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 2]
        }
        Model::Litho(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 3]
        }
        Model::LithoOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 4]
        }
        Model::Array(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 5]
        }
        Model::ArrayOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 6]
        }
        Model::Bank(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 7]
        }
        Model::BankOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 8]
        }
        Model::Bw(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 9]
        }
        Model::BwOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 10]
        }
        Model::Hbm(z, beat, local) => {
            [z as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 11]
        }
        Model::HbmOverview(t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 0, 12]
        }
        Model::Chip(k, beat, local) => {
            [k.as_ptr() as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 13]
        }
        Model::ChipOverview(_, k, t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [k.as_ptr() as i64, t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 14]
        }
        Model::Pkg(k, beat, local) => {
            [k.as_ptr() as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 15]
        }
        Model::PkgOverview(_, k, t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [k.as_ptr() as i64, t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 16]
        }
        Model::Link(k, beat, local) => {
            [k.as_ptr() as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 17]
        }
        Model::LinkOverview(_, k, t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [k.as_ptr() as i64, t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 18]
        }
        Model::Pwr(k, beat, local) => {
            [k.as_ptr() as i64, beat as i64, (local * 400.0).round() as i64, 0, 0, 0, 0, 19]
        }
        Model::PwrOverview(_, k, t) => {
            let a = (poly3d::notes_alpha(f64::from(t.local)) * 40.0).round() as i64;
            [k.as_ptr() as i64, t.beat as i64, (t.ms / 40) as i64, a, 0, 0, 0, 20]
        }
    }
}

fn render_model(m: Model, view: &poly3d::View, w: usize, h: usize) -> RgbaImage {
    match m {
        Model::Jar(a) => poly3d::render(&poly3d::Params::default(), a, view, w, h, FULL_BG),
        Model::Cell(z, beat, local) => {
            poly3d::render_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::CellOverview(t) => {
            super::diagrams_scene_cell::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Litho(z, beat, local) => {
            poly3d::render_litho_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::LithoOverview(t) => {
            super::diagrams_scene_litho::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Array(z, beat, local) => {
            poly3d::render_array_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::ArrayOverview(t) => {
            super::diagrams_scene_array::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Bank(z, beat, local) => {
            poly3d::render_bank_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::BankOverview(t) => {
            super::diagrams_scene_bank::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Bw(z, beat, local) => {
            poly3d::render_bw_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::BwOverview(t) => {
            super::diagrams_scene_bandwidth::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Hbm(z, beat, local) => {
            poly3d::render_hbm_zoom(z, beat, local, view, w, h, FULL_BG)
        }
        Model::HbmOverview(t) => {
            super::diagrams_scene_hbm::overview_frame(&t, view, w as u32, h as u32)
        }
        Model::Chip(k, beat, local) => {
            poly3d::render_chip(k, beat, local, view, None, w, h, FULL_BG)
        }
        Model::ChipOverview(b, k, t) => {
            super::diagrams_scene_chip::frame(b, k, true, &t, view, w as u32, h as u32)
        }
        Model::Pkg(k, beat, local) => {
            poly3d::render_pkg(k, beat, local, view, None, w, h, FULL_BG)
        }
        Model::PkgOverview(b, k, t) => {
            super::diagrams_scene_pkg::frame(b, k, true, &t, view, w as u32, h as u32)
        }
        Model::Link(k, beat, local) => {
            poly3d::render_link(k, beat, local, view, None, w, h, FULL_BG)
        }
        Model::LinkOverview(b, k, t) => {
            super::diagrams_scene_link::frame(b, k, true, &t, view, w as u32, h as u32)
        }
        Model::Pwr(k, beat, local) => {
            poly3d::render_power(k, beat, local, view, None, w, h, FULL_BG)
        }
        Model::PwrOverview(b, k, t) => {
            super::diagrams_scene_pwr::frame(b, k, true, &t, view, w as u32, h as u32)
        }
    }
}

/// What one rendered 3D frame depends on: camera, model state (quantised), and pixel size.
type SceneKey = (poly3d::View, ModelKey, u32, u32);

/// The scene's state, quantised, so a frame re-renders only when something visible changed.
fn scene_key(a: poly3d::Anim) -> [i64; 7] {
    let q = |x: f64, scale: f64| (x * scale).round() as i64;
    [
        q(a.heat, 100.0),
        q(a.rod_d, 2.0),
        q(a.flow.pump, 100.0),
        q(a.flow.feed, 100.0),
        q(a.flow.exhaust, 100.0),
        q(a.flow.power, 100.0),
        q(a.phase, 40.0),
    ]
}

/// The full-screen view's last render: the camera and rod state it was drawn
/// for (and the size), plus its terminal encoding.
struct FullFrame {
    key: SceneKey,
    shown: Shown,
}

/// How a full-screen frame reaches the terminal.
enum Shown {
    /// Kitty / iTerm2 / sixel: the terminal scales the encoded image.
    Graphics(StatefulProtocol),
    /// No graphics protocol: sampled into half-block cells by `blit_halfblocks`.
    Blocks(RgbaImage),
}

/// The terminal's graphics protocol, queried the way the intraday screen does: kitty
/// compression on, shared memory with FL_KITTY=shm. Halfblocks when there is none.
///
/// Inside tmux the kitty reply never reaches us (tmux drops it), so the query alone falls back
/// to halfblocks even under Ghostty. Ghostty leaves its env vars in the tmux pane, so use kitty
/// directly when the outer terminal is Ghostty; the kitty frames go out through tmux passthrough.
fn query_picker() -> Picker {
    let mode = std::env::var("FL_KITTY").unwrap_or_default();
    let options = QueryStdioOptions {
        kitty_compression: !matches!(mode.as_str(), "raw" | "shm"),
        kitty_shared_memory_object: (mode == "shm")
            .then(QueryStdioOptions::probe_kitty_smo)
            .flatten(),
        ..Default::default()
    };
    let queried = Picker::from_query_stdio_with_options(options)
        .ok()
        .filter(|p| p.protocol_type() != ProtocolType::Halfblocks);
    if let Some(picker) = queried {
        return picker;
    }
    let ghostty = ["GHOSTTY_RESOURCES_DIR", "GHOSTTY_BIN_DIR"]
        .iter()
        .any(|v| std::env::var_os(v).is_some_and(|x| !x.is_empty()));
    let mut picker = Picker::halfblocks();
    if ghostty {
        picker.set_protocol_type(ProtocolType::Kitty);
    }
    picker
}

/// Kitty image ids for the full-screen view, used in turn. A frame uploads under the id the
/// screen is not showing, so the old picture stays up until the new one has fully arrived.
/// Reusing one id blanked the screen for the length of each upload.
const FULL_IMAGE_IDS: [u32; 2] = [
    u32::from_be_bytes([0, 0xF3, 0xD1, 0x01]),
    u32::from_be_bytes([0, 0xF3, 0xD1, 0x02]),
];

/// Kitty protocol for one frame, with the stable id. ratatui-image's own kitty protocol takes
/// a random id per send and never deletes the old image.
fn kitty_protocol(picker: &Picker, img: DynamicImage, font: FontSize, id: u32) -> StatefulProtocol {
    // zlib (o=z) is on: the query checks it, and Ghostty and kitty both support it. Without a
    // query (see query_picker) the capability list is empty, so it is not read here.
    StatefulProtocol::new(
        img,
        font,
        None,
        StatefulProtocolType::Kitty(StatefulKitty::new(id, picker.tmux_detected(), true, false)),
    )
}

/// Half-block fallback: each cell is `▀` with the top sample as its foreground
/// and the bottom sample as its background, so one cell holds two rows of pixels.
fn blit_halfblocks(img: &RgbaImage, area: Rect, buf: &mut Buffer) {
    let (iw, ih) = (img.width() as f64, img.height() as f64);
    let (cw, sub_h) = (area.width as f64, area.height as f64 * 2.0);
    let sample = |x: u32, sy: f64| {
        let y = ((sy * ih / sub_h) as u32).min(img.height() - 1);
        let p = img.get_pixel(x, y).0;
        Color::Rgb(p[0], p[1], p[2])
    };
    for cy in 0..area.height {
        for cx in 0..area.width {
            let x = (((cx as f64 + 0.5) * iw / cw) as u32).min(img.width() - 1);
            let top = sample(x, 2.0 * cy as f64 + 0.5);
            let bottom = sample(x, 2.0 * cy as f64 + 1.5);
            if let Some(cell) = buf.cell_mut((area.x + cx, area.y + cy)) {
                cell.set_symbol("\u{2580}").set_fg(top).set_bg(bottom);
            }
        }
    }
}

/// What a camera key moves. A tap moves one `step`. Holding the key moves at
/// `rate` per second, which is the speed cap, so a held key never lurches.
#[derive(Clone, Copy)]
enum Axis {
    Yaw,
    Pitch,
    Zoom,
    PanX,
    PanY,
}

impl Axis {
    /// One tap: radians, ln(zoom), or pixels.
    fn step(self) -> f64 {
        match self {
            Axis::Yaw | Axis::Pitch => 0.08,
            Axis::Zoom => 1.15f64.ln(),
            Axis::PanX | Axis::PanY => 40.0,
        }
    }
    /// The speed cap while held: radians/s, ln(zoom)/s, or pixels/s.
    fn rate(self) -> f64 {
        match self {
            Axis::Yaw => 1.2,
            Axis::Pitch => 0.8,
            Axis::Zoom => 0.7,
            Axis::PanX | Axis::PanY => 240.0,
        }
    }
}

/// Camera keys as (canonical key, axis, direction). Arrows act as hjkl.
fn camera_key(code: KeyCode) -> Option<(char, Axis, f64)> {
    let c = match code {
        KeyCode::Left => 'h',
        KeyCode::Right => 'l',
        KeyCode::Up => 'k',
        KeyCode::Down => 'j',
        KeyCode::Char('=') => '+',
        KeyCode::Char('_') => '-',
        KeyCode::Char(c) => c,
        _ => return None,
    };
    let (axis, dir) = match c {
        'h' => (Axis::Yaw, -1.0),
        'l' => (Axis::Yaw, 1.0),
        'k' => (Axis::Pitch, 1.0),
        'j' => (Axis::Pitch, -1.0),
        '+' => (Axis::Zoom, 1.0),
        '-' => (Axis::Zoom, -1.0),
        'H' => (Axis::PanX, -1.0),
        'L' => (Axis::PanX, 1.0),
        'K' => (Axis::PanY, -1.0),
        'J' => (Axis::PanY, 1.0),
        _ => return None,
    };
    Some((c, axis, dir))
}

/// Zoom turn keys: HJKL turn the model (lowercase stay the beats and notes), +/- zoom.
/// Returns the same canonical key, axis and direction as `camera_key`.
fn turn_key(c: char) -> Option<(char, Axis, f64)> {
    match c {
        'H' => Some(('h', Axis::Yaw, -1.0)),
        'L' => Some(('l', Axis::Yaw, 1.0)),
        'K' => Some(('k', Axis::Pitch, 1.0)),
        'J' => Some(('j', Axis::Pitch, -1.0)),
        '+' | '=' => Some(('+', Axis::Zoom, 1.0)),
        '-' | '_' => Some(('-', Axis::Zoom, -1.0)),
        _ => None,
    }
}

/// A press of the same key this soon after the last one is key repeat (held).
const REPEAT_GAP: Duration = Duration::from_millis(90);
/// Held motion carries on this long after the last repeat, bridging gaps between repeats.
const HOLD_ON: Duration = Duration::from_millis(120);
/// Longest time step applied in one tick, so a stalled frame never jumps the camera.
const MAX_DT: f64 = 0.1;
/// After the last camera key, how long frames stay at motion resolution before one sharp
/// frame. Longer than the OS key-repeat delay would be ideal, but taps should sharpen fast.
const SETTLE: Duration = Duration::from_millis(250);
/// Redraw interval while the camera moves (FRAME otherwise).
const MOTION_FRAME: Duration = Duration::from_millis(30);
/// Terminal background the 3D render is drawn on (Ghostty's Dracula).
const FULL_BG: [u8; 3] = [0x28, 0x2a, 0x36];
/// Largest 3D render, in pixels, for half-blocks. The terminal scales it to fit.
const FULL_MAX: (f64, f64) = (1280.0, 720.0);
/// Largest kitty render, in pixels (about 240 x 67 cells at 10 x 20). Bigger popups crop to this.
const FULL_MAX_KITTY: (f64, f64) = (2400.0, 1350.0);

/// A selectable spot on a node's page; (row, col) index the page art.
struct Hot {
    row: u16,
    col: u16,
    len: u16,
    label: &'static str,
    body: &'static str,
}

fn find_hots(label: &str) -> Vec<Hot> {
    let Some(art) = visual(label) else {
        return Vec::new();
    };
    let lines: Vec<&str> = art.lines().collect();
    let mut out: Vec<Hot> = cards(label)
        .into_iter()
        .filter_map(|c| {
            let row = match c.line {
                Some(n) => n
                    .checked_sub(1)
                    .filter(|&r| lines.get(r).is_some_and(|l| l.contains(c.label)))?,
                None => lines.iter().position(|l| l.contains(c.label))?,
            };
            let byte = lines[row].find(c.label)?;
            Some(Hot {
                row: row as u16,
                col: lines[row][..byte].chars().count() as u16,
                len: c.label.chars().count() as u16,
                label: c.label,
                body: c.body,
            })
        })
        .collect();
    out.sort_by_key(|h| (h.row, h.col));
    out
}

/// Greedy word wrap to `width` columns.
fn wrap_words(text: &str, width: usize) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    for w in text.split_whitespace() {
        if !cur.is_empty() && text::width(&cur) + 1 + text::width(w) > width {
            out.push(std::mem::take(&mut cur));
        }
        if !cur.is_empty() {
            cur.push(' ');
        }
        cur.push_str(w);
    }
    if !cur.is_empty() {
        out.push(cur);
    }
    out
}

/// A selectable box in the art: top-left cell, size, and its first label line.
struct Node {
    row: u16,
    col: u16,
    w: u16,
    h: u16,
    label: String,
}

/// Finds `┌─┐ / │ text │ / └─┘` boxes, plus `┌── text ──┘` banner lines.
fn find_nodes(art: &str) -> Vec<Node> {
    let g: Vec<Vec<char>> = art.lines().map(|l| l.chars().collect()).collect();
    let at = |r: usize, c: usize| g.get(r).and_then(|l| l.get(c)).copied().unwrap_or(' ');
    let mut out = Vec::new();
    for (r, line) in g.iter().enumerate() {
        for (c, &ch) in line.iter().enumerate() {
            if ch != '\u{250C}' {
                continue;
            }
            let mut x = c + 1;
            while x < line.len()
                && !matches!(at(r, x), '\u{2510}' | '\u{2518}' | '\u{250C}' | '\u{2502}')
            {
                x += 1;
            }
            match at(r, x) {
                '\u{2510}' if (c + 1..x).all(|i| at(r, i) == '\u{2500}') => {
                    let mut y = r + 1;
                    while at(y, c) == '\u{2502}' && at(y, x) == '\u{2502}' {
                        y += 1;
                    }
                    if y > r + 1 && at(y, c) == '\u{2514}' && at(y, x) == '\u{2518}' {
                        let label: String = (c + 1..x).map(|i| at(r + 1, i)).collect();
                        out.push(Node {
                            row: r as u16,
                            col: c as u16,
                            w: (x - c + 1) as u16,
                            h: (y - r + 1) as u16,
                            label: label.trim().to_string(),
                        });
                    }
                }
                '\u{2518}' => {
                    let label: String = (c + 1..x)
                        .map(|i| at(r, i))
                        .filter(|&ch| ch != '\u{2500}')
                        .collect();
                    if !label.trim().is_empty() {
                        out.push(Node {
                            row: r as u16,
                            col: c as u16,
                            w: (x - c + 1) as u16,
                            h: 1,
                            label: label.trim().to_string(),
                        });
                    }
                }
                _ => {}
            }
        }
    }
    out.sort_by_key(|n| (n.row, n.col));
    out
}

/// Splits a card body on `# heading` lines; text before the first heading is
/// an "overview" section. Always returns at least one section.
fn sections(body: &'static str) -> Vec<(&'static str, &'static str)> {
    let mut heads: Vec<(usize, usize, &'static str)> = Vec::new();
    let mut off = 0;
    for line in body.split_inclusive('\n') {
        if let Some(title) = line.trim_end().strip_prefix("# ") {
            heads.push((off, off + line.len(), title.trim()));
        }
        off += line.len();
    }
    let mut out = Vec::new();
    let first = heads.first().map_or(body.len(), |h| h.0);
    if heads.is_empty() || !body[..first].trim().is_empty() {
        out.push(("overview", body[..first].trim()));
    }
    for (i, &(_, end, title)) in heads.iter().enumerate() {
        let next = heads.get(i + 1).map_or(body.len(), |h| h.0);
        out.push((title, body[end..next].trim()));
    }
    out
}

/// Line ranges (start, end, heading line) of each `# ` section of a page's art.
/// Text before the first heading joins the first pane; no headings = one pane.
fn pane_ranges(art: &str) -> Vec<(usize, usize, usize)> {
    let n = art.lines().count();
    let heads: Vec<usize> = art
        .lines()
        .enumerate()
        .filter(|(_, l)| l.starts_with("# "))
        .map(|(i, _)| i)
        .collect();
    if heads.is_empty() {
        return vec![(0, n, 0)];
    }
    heads
        .iter()
        .enumerate()
        .map(|(k, &h)| {
            let start = if k == 0 { 0 } else { h };
            (start, heads.get(k + 1).copied().unwrap_or(n), h)
        })
        .collect()
}

pub fn open(ctx: &Ctx, arg: Option<String>) -> io::Result<Diagrams> {
    let tab = arg
        .as_deref()
        .map(str::to_lowercase)
        .and_then(|a| {
            DIAGRAMS
                .iter()
                .position(|d| d.tab.to_lowercase().starts_with(&a))
        })
        .unwrap_or(0);
    // Must run before the event loop reads stdin: the terminal answers the query on stdin.
    let picker = query_picker();
    Ok(Diagrams {
        theme: ctx.theme,
        picker,
        orbit: poly3d::View::default(),
        full: None,
        full_turn: false,
        held: None,
        live_until: None,
        settle_until: None,
        sharpen: false,
        last_tick: Instant::now(),
        tab,
        scroll: 0,
        body_h: 0,
        help: false,
        nodes: DIAGRAMS.iter().map(|d| find_nodes(d.art)).collect(),
        sel: 0,
        popup: false,
        popup_scroll: 0,
        view: PopupView::Pane,
        menu_sel: 0,
        notes_scroll: 0,
        notes_beat: None,
        zoom: None,
        zoom_section: false,
        preview: None,
        browse: false,
        pane: 0,
        anim_start: Instant::now(),
        player: None,
        tour_start: Instant::now(),
        hots: Vec::new(),
        hsel: 0,
        hot_moved: false,
        detail: false,
        secs: Vec::new(),
        ptab: 0,
        pscroll: 0,
        pcur: 0,
        focus: Focus::Text,
        vcur: 0,
        vscroll: 0,
        mol: None,
        card: None,
        mol_cur: 0,
    })
}

fn class_style(c: char, in_note: bool, t: &Theme) -> Style {
    match c {
        _ if in_note => t.dim().add_modifier(Modifier::ITALIC),
        '\u{2500}'..='\u{257F}' => t.border(),
        '▶' | '▼' | '◀' | '▲' | '●' | '▓' | '≈' => t.accent(),
        '█' | '▌' => t.up(),
        _ => t.base(),
    }
}

/// Art -> styled lines. `# ` lines are section headings; `(...)` is a note.
/// Animation art -> lines: the usual character classes plus chemistry colours (Si yellow, Cl green) wherever
/// the element symbols appear, so atoms in the close-ups and the labels around them read at a glance.
fn scene_lines(art: &str, t: &Theme) -> Vec<Line<'static>> {
    art.lines()
        .map(|line| {
            let cs: Vec<char> = line.chars().collect();
            let mut spans: Vec<Span<'static>> = Vec::new();
            let (mut run, mut run_style) = (String::new(), t.base());
            let mut depth = 0u32;
            let mut i = 0;
            while i < cs.len() {
                let c = cs[i];
                let next = cs.get(i + 1).copied();
                let (take, style) = match (c, next) {
                    ('(', _) => {
                        depth += 1;
                        (1, class_style(c, true, t))
                    }
                    ('S', Some('i')) if depth == 0 => (2, t.accent()),
                    ('C', Some('l')) if depth == 0 => (2, t.up()),
                    _ => (1, class_style(c, depth > 0, t)),
                };
                if style != run_style && !run.is_empty() {
                    spans.push(Span::styled(std::mem::take(&mut run), run_style));
                }
                run_style = style;
                run.extend(&cs[i..i + take]);
                if c == ')' {
                    depth = depth.saturating_sub(1);
                }
                i += take;
            }
            if !run.is_empty() {
                spans.push(Span::styled(run, run_style));
            }
            Line::from(spans)
        })
        .collect()
}

fn styled_lines<'a>(art: &'a str, t: &Theme) -> Vec<Line<'a>> {
    art.lines()
        .map(|line| {
            if let Some(h) = line.strip_prefix("# ") {
                return Line::from(Span::styled(
                    format!("▎{h}"),
                    t.accent().add_modifier(Modifier::BOLD),
                ));
            }
            let mut spans: Vec<Span> = Vec::new();
            let (mut run, mut run_style) = (String::new(), t.base());
            let mut depth = 0u32;
            for c in line.chars() {
                if c == '(' {
                    depth += 1;
                }
                let style = class_style(c, depth > 0, t);
                if style != run_style && !run.is_empty() {
                    spans.push(Span::styled(std::mem::take(&mut run), run_style));
                }
                run_style = style;
                run.push(c);
                if c == ')' {
                    depth = depth.saturating_sub(1);
                }
            }
            if !run.is_empty() {
                spans.push(Span::styled(run, run_style));
            }
            Line::from(spans)
        })
        .collect()
}

fn art_size(d: &Diagram) -> (u16, u16) {
    let w = d.art.lines().map(text::width).max().unwrap_or(0);
    (w as u16, d.art.lines().count() as u16)
}

fn tab_line(sel: usize, t: &Theme) -> Line<'static> {
    let mut spans = vec![Span::raw(" ")];
    for (i, d) in DIAGRAMS.iter().enumerate() {
        let label = format!(" {} {} ", i + 1, d.tab);
        spans.push(if i == sel {
            Span::styled(label, t.selected().add_modifier(Modifier::BOLD))
        } else {
            Span::styled(label, t.dim())
        });
        spans.push(Span::raw(" "));
    }
    Line::from(spans)
}

impl Diagrams {
    fn goto(&mut self, tab: usize) {
        self.tab = tab % DIAGRAMS.len();
        self.scroll = 0;
        self.sel = 0;
    }

    fn step_node(&mut self, delta: isize) {
        let n = self.nodes[self.tab].len();
        if n == 0 {
            return;
        }
        self.sel = (self.sel as isize + delta).rem_euclid(n as isize) as usize;
        let node = &self.nodes[self.tab][self.sel];
        let (top, bot) = (node.row, node.row + node.h);
        if top < self.scroll {
            self.scroll = top;
        } else if bot > self.scroll + self.body_h {
            self.scroll = bot.saturating_sub(self.body_h);
        }
    }

    /// Moves the selection to the nearest node in the next row down (dir > 0)
    /// or up (dir < 0), closest by column; returns false when there is none.
    fn step_row(&mut self, dir: i32) -> bool {
        let nodes = &self.nodes[self.tab];
        let Some(cur) = nodes.get(self.sel) else {
            return false;
        };
        let best = nodes
            .iter()
            .enumerate()
            .filter(|(_, n)| {
                if dir > 0 {
                    n.row > cur.row
                } else {
                    n.row < cur.row
                }
            })
            .min_by_key(|(_, n)| (n.row.abs_diff(cur.row), n.col.abs_diff(cur.col)));
        match best {
            Some((i, _)) => {
                let delta = i as isize - self.sel as isize;
                self.step_node(delta);
                true
            }
            None => false,
        }
    }

    fn draw_selection(&self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(n) = self.nodes[self.tab].get(self.sel) else {
            return;
        };
        let buf = frame.buffer_mut();
        for dy in 0..n.h {
            let Some(y) = (n.row + dy).checked_sub(self.scroll) else {
                continue;
            };
            if y >= area.height {
                continue;
            }
            for dx in 0..n.w {
                let x = n.col + dx;
                if x < area.width {
                    buf[(area.x + x, area.y + y)].set_style(t.selected());
                }
            }
        }
    }

    fn step_pane(&mut self, delta: isize) {
        let Some(n) = self.nodes[self.tab].get(self.sel) else {
            return;
        };
        let panes = pane_ranges(visual(&n.label).unwrap_or(""));
        self.pane = (self.pane as isize + delta).rem_euclid(panes.len() as isize) as usize;
        self.popup_scroll = 0;
        let (p0, p1, _) = panes[self.pane];
        if let Some(i) = self
            .hots
            .iter()
            .position(|h| (h.row as usize) >= p0 && (h.row as usize) < p1)
        {
            self.hsel = i;
        }
    }

    fn step_hot(&mut self, delta: isize) {
        let n = self.hots.len();
        if n > 0 {
            self.hsel = (self.hsel as isize + delta).rem_euclid(n as isize) as usize;
            self.hot_moved = true;
        }
    }

    /// Nearest spot in the next row down/up (closest by column).
    fn step_hot_row(&mut self, dir: i32) -> bool {
        let Some(cur) = self.hots.get(self.hsel) else {
            return false;
        };
        let best = self
            .hots
            .iter()
            .enumerate()
            .filter(|(_, h)| {
                if dir > 0 {
                    h.row > cur.row
                } else {
                    h.row < cur.row
                }
            })
            .min_by_key(|(_, h)| (h.row.abs_diff(cur.row), h.col.abs_diff(cur.col)));
        match best {
            Some((i, _)) => {
                self.hsel = i;
                self.hot_moved = true;
                true
            }
            None => false,
        }
    }

    /// A page animation is playing in the open popup.
    fn animating(&self) -> bool {
        if !self.popup || !self.has_scene() {
            return false;
        }
        match self.view {
            PopupView::Overview | PopupView::Zoom | PopupView::Full => {
                !self.scene_player().is_some_and(|p| p.is_paused())
            }
            // the preview beside the menu plays while an animation row is highlighted
            PopupView::Menu => self.browse && self.menu_has_anim(),
            PopupView::Pane => false,
        }
    }

    /// The player the overview or the zoom is showing.
    fn scene_player(&self) -> Option<&Player> {
        if matches!(self.view, PopupView::Zoom | PopupView::Full) {
            self.zoom.as_ref().map(|(_, p)| p)
        } else {
            self.player.as_ref().and_then(|(_, p)| p.as_ref())
        }
    }

    fn scene_player_mut(&mut self) -> Option<&mut Player> {
        if matches!(self.view, PopupView::Zoom | PopupView::Full) {
            self.zoom.as_mut().map(|(_, p)| p)
        } else {
            self.player.as_mut().and_then(|(_, p)| p.as_mut())
        }
    }

    /// p pauses / resumes, h/l (or arrows) jump a beat back / forward.
    fn playback_key(&mut self, code: KeyCode) -> bool {
        let Some(p) = self.scene_player_mut() else {
            return false;
        };
        match code {
            KeyCode::Char('p') => p.toggle_pause(),
            KeyCode::Char('l') | KeyCode::Right => p.step_beat(1),
            KeyCode::Char('h') | KeyCode::Left => p.step_beat(-1),
            KeyCode::Char('j') | KeyCode::Down => {
                self.notes_scroll = self.notes_scroll.saturating_add(2);
                return true;
            }
            KeyCode::Char('k') | KeyCode::Up => {
                self.notes_scroll = self.notes_scroll.saturating_sub(2);
                return true;
            }
            _ => return false,
        }
        if code != KeyCode::Char('p') {
            self.notes_scroll = 0;
        }
        true
    }

    fn has_scene(&self) -> bool {
        matches!(self.player, Some((_, Some(_))))
    }

    fn cur_label(&self) -> Option<String> {
        Some(self.nodes.get(self.tab)?.get(self.sel)?.label.clone())
    }

    /// Section titles of the open page, in menu order.
    fn pane_titles(&self) -> Vec<String> {
        let art = self.cur_label().and_then(|l| visual(&l)).unwrap_or("");
        pane_ranges(art)
            .iter()
            .enumerate()
            .map(|(i, p)| {
                let title = art.lines().nth(p.2).unwrap_or("");
                let title = title.strip_prefix("# ").unwrap_or(title).trim();
                if title.chars().next().is_some_and(|c| c.is_ascii_digit()) {
                    title.to_string()
                } else {
                    format!("{}. {title}", i + 1)
                }
            })
            .collect()
    }

    /// Menu -> section: show pane `i` with the usual spot cursor.
    fn open_pane(&mut self, i: usize) {
        let n = self.pane_titles().len();
        if n == 0 {
            return;
        }
        self.pane = i.min(n - 1);
        self.popup_scroll = 0;
        let art = self.cur_label().and_then(|l| visual(&l)).unwrap_or("");
        let (p0, p1, _) = pane_ranges(art)[self.pane];
        if let Some(h) = self
            .hots
            .iter()
            .position(|h| (h.row as usize) >= p0 && (h.row as usize) < p1)
        {
            self.hsel = h;
        }
        self.view = PopupView::Pane;
    }

    /// (key, label) of the open page's zoom-ins.
    fn zoom_list(&self) -> Vec<(char, &'static str)> {
        match &self.player {
            Some((_, Some(p))) => p.zooms().iter().map(|z| (z.key, z.label)).collect(),
            _ => Vec::new(),
        }
    }

    /// Menu index of the first section: the overview and the zoom-ins come first.
    fn menu_sections(&self) -> usize {
        1 + self.zoom_list().len()
    }

    fn open_zoom(&mut self, i: usize) {
        let Some((_, Some(p))) = &self.player else {
            return;
        };
        let Some(z) = p.zooms().get(i).copied() else {
            return;
        };
        self.zoom = Some((i, Player::new((z.build)(), Instant::now())));
        self.zoom_section = false;
        self.view = PopupView::Zoom;
    }

    /// The key of the open scene: its letter, or the digit of its numbered section.
    fn open_key(&self) -> Option<char> {
        let (i, _) = self.zoom.as_ref()?;
        if self.zoom_section {
            char::from_digit(*i as u32 + 1, 10)
        } else {
            self.zoom_list().get(*i).map(|(k, _)| *k)
        }
    }

    /// The 3D model of the open scene at `time`.
    fn open_model(&self, time: &crate::ui::anim::Time) -> Model {
        let page = self.player.as_ref().map_or("", |(p, _)| *p);
        model_at(page, self.open_key().unwrap_or(' '), time)
    }

    /// The page's overview is a 3D model HJKL can turn in place (CELL, LITHO, ARRAY, BANK, BANDWIDTH, HBM STACK).
    fn overview_orbits(&self) -> bool {
        matches!(&self.player, Some(("CELL" | "LITHO" | "ARRAY" | "BANK" | "BANDWIDTH" | "HBM STACK", Some(_))))
            || matches!(&self.player, Some((p, Some(_))) if super::diagrams_scene_chip::node(p).is_some() || super::diagrams_scene_pkg::node(p).is_some() || super::diagrams_scene_link::node(p).is_some() || super::diagrams_scene_pwr::node(p).is_some())
    }

    /// The open scene has a 3D model the full-screen view can orbit.
    fn can_orbit(&self) -> bool {
        let Some((page, _)) = &self.player else {
            return false;
        };
        self.open_key().is_some_and(|k| orbitable(page, k))
    }

    /// Keys in the full-screen 3D view: hjkl orbit, +/- zoom, HJKL pan, 0
    /// reset, p pause, q/Esc/F back to the zoom. These take priority over the
    /// zoom's beat keys.
    /// One camera key: a tap moves one step, a repeat starts held motion (full_tick).
    fn camera_step(&mut self, hit: (char, Axis, f64), now: Instant) {
        let (key, axis, dir) = hit;
        let repeat = matches!(
            self.held,
            Some((k, at)) if k == key && now.duration_since(at) < REPEAT_GAP
        );
        self.held = Some((key, now));
        self.settle_until = Some(now + SETTLE);
        if repeat {
            // motion runs in full_tick at the speed cap, not once per event
            self.live_until = Some(now + HOLD_ON);
        } else {
            self.apply(axis, dir * axis.step());
        }
    }

    fn full_key(&mut self, code: KeyCode, now: Instant) {
        if let Some(hit) = camera_key(code) {
            self.camera_step(hit, now);
            return;
        }
        match code {
            KeyCode::Char('q') | KeyCode::Esc | KeyCode::Char('F') => self.view = PopupView::Zoom,
            KeyCode::Char('0') => self.orbit = poly3d::View::default(),
            KeyCode::Char('p') => {
                if let Some((_, p)) = self.zoom.as_mut() {
                    p.toggle_pause();
                }
            }
            _ => {}
        }
    }

    /// Moves the camera along one axis by `amount` (radians, ln(zoom), or pixels).
    fn apply(&mut self, axis: Axis, amount: f64) {
        match axis {
            Axis::Yaw => self.orbit.orbit(amount, 0.0),
            Axis::Pitch => self.orbit.orbit(0.0, amount),
            Axis::Zoom => self.orbit.zoom_by(amount.exp()),
            Axis::PanX => self.orbit.pan_by(amount, 0.0),
            Axis::PanY => self.orbit.pan_by(0.0, amount),
        }
    }

    /// Whether the 3D view should render at motion resolution: the camera is moving, or
    /// a camera key went down within SETTLE.
    fn coarse(&self, now: Instant) -> bool {
        self.moving(now) || self.settle_until.is_some_and(|until| now < until)
    }

    /// Whether held-key motion is running at `now`.
    fn moving(&self, now: Instant) -> bool {
        self.live_until.is_some_and(|until| now < until)
    }

    /// Advances held-key motion by the time since the last tick, at the speed cap.
    fn full_tick(&mut self, now: Instant) {
        let dt = now.duration_since(self.last_tick).as_secs_f64().min(MAX_DT);
        self.last_tick = now;
        if !matches!(self.view, PopupView::Full | PopupView::Zoom | PopupView::Overview) || !self.moving(now) {
            return;
        }
        if let Some((key, _)) = self.held
            && let Some((_, axis, dir)) = camera_key(KeyCode::Char(key))
        {
            self.apply(axis, dir * axis.rate() * dt);
        }
    }

    /// Full-screen 3D view of the open zoom. The zoom's clock drives the rods
    /// and hjkl move the camera. The frame is re-rendered only when the camera,
    /// the rods' state, or the size changes.
    fn draw_full(&mut self, frame: &mut Frame, r: Rect, t: &Theme) {
        let Some((i, p)) = self.zoom.as_ref() else {
            return;
        };
        let time = p.time_at(p.now_ms());
        let paused = p.is_paused();
        let name = self.zoom_list().get(*i).map_or("", |(_, l)| *l);
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(
                format!(" {name} \u{00B7} full view "),
                t.title(),
            ))
            .title_bottom(Span::styled(
                format!(
                    " hjkl orbit  +/- zoom  HJKL pan  0 reset  {}  esc back ",
                    if paused { "p resume" } else { "p pause" }
                ),
                t.dim(),
            ));
        let inner = block.inner(r);
        frame.render_widget(Clear, r);
        frame.render_widget(block, r);
        let model = self.open_model(&time);
        let half = self.coarse(Instant::now());
        self.paint_3d(frame, inner, model, self.orbit, half);
    }

    /// Paints a 3D scene into `inner`. Kitty gets a frame sized to whole cells, at the
    /// terminal's pixels (half while `half`, for motion: the same cells at a quarter of the
    /// bytes). Half-blocks fill the area. The frame re-renders only when the scene changes.
    fn paint_3d(
        &mut self,
        frame: &mut Frame,
        inner: Rect,
        model: Model,
        view: poly3d::View,
        half: bool,
    ) {
        let font = self.picker.font_size();
        let kitty = self.picker.protocol_type() == ProtocolType::Kitty;
        let max = if kitty { FULL_MAX_KITTY } else { FULL_MAX };
        let mut px_font = font;
        let (area, w, h) = if kitty {
            if half {
                px_font = FontSize::new((font.width / 2).max(1), (font.height / 2).max(1));
            }
            let cols = inner.width.min((max.0 / font.width as f64) as u16);
            let rows = inner.height.min((max.1 / font.height as f64) as u16);
            let area = Rect::new(
                inner.x + (inner.width - cols) / 2,
                inner.y + (inner.height - rows) / 2,
                cols,
                rows,
            );
            (
                area,
                cols as u32 * px_font.width as u32,
                rows as u32 * px_font.height as u32,
            )
        } else {
            let (fw, fh) = (
                inner.width as f64 * font.width as f64,
                inner.height as f64 * font.height as f64,
            );
            let scale = (max.0 / fw.max(1.0)).min(max.1 / fh.max(1.0)).min(1.0);
            let scale = if half { scale * 0.5 } else { scale };
            let (w, h) = ((fw * scale).floor(), (fh * scale).floor());
            if w < 1.0 || h < 1.0 {
                return;
            }
            (inner, w as u32, h as u32)
        };
        if w == 0 || h == 0 {
            return;
        }
        let key: SceneKey = (view, model_key(model), w, h);
        if self.full.as_ref().is_none_or(|f| f.key != key) {
            let img = render_model(model, &view, w as usize, h as usize);
            let shown = match self.picker.protocol_type() {
                ProtocolType::Halfblocks => Shown::Blocks(img),
                ProtocolType::Kitty => {
                    self.full_turn = !self.full_turn;
                    let id = FULL_IMAGE_IDS[self.full_turn as usize];
                    Shown::Graphics(kitty_protocol(
                        &self.picker,
                        DynamicImage::ImageRgba8(img),
                        px_font,
                        id,
                    ))
                }
                _ => Shown::Graphics(
                    self.picker
                        .new_resize_protocol(DynamicImage::ImageRgba8(img)),
                ),
            };
            self.full = Some(FullFrame { key, shown });
        }
        match self.full.as_mut().map(|f| &mut f.shown) {
            Some(Shown::Graphics(proto)) => frame.render_stateful_widget(
                StatefulImage::default().resize(Resize::Fit(None)),
                area,
                proto,
            ),
            Some(Shown::Blocks(img)) => blit_halfblocks(img, area, frame.buffer_mut()),
            None => {}
        }
    }

    /// Show one pixel frame of a scene in `area`: a kitty image when the terminal has
    /// one, half-blocks otherwise. `img` is already sized to `area` in pixels.
    fn paint_px(&mut self, frame: &mut Frame, area: Rect, img: image::RgbaImage) {
        let proto_type = self.picker.protocol_type();
        if proto_type == ProtocolType::Halfblocks {
            blit_halfblocks(&img, area, frame.buffer_mut());
            return;
        }
        let font = self.picker.font_size();
        let mut proto = if proto_type == ProtocolType::Kitty {
            self.full_turn = !self.full_turn;
            let id = FULL_IMAGE_IDS[self.full_turn as usize];
            kitty_protocol(&self.picker, DynamicImage::ImageRgba8(img), font, id)
        } else {
            self.picker
                .new_resize_protocol(DynamicImage::ImageRgba8(img))
        };
        frame.render_stateful_widget(
            StatefulImage::default().resize(Resize::Fit(None)),
            area,
            &mut proto,
        );
    }

    /// The animation for numbered section `i` of the open page, if it has one.
    fn section_build(&self, i: usize) -> Option<fn() -> Box<dyn Scene>> {
        let (page, _) = self.player.as_ref()?;
        section_anim(page, i)
    }

    /// Menu -> numbered section with an animation: play it full size.
    fn open_section(&mut self, i: usize) {
        let Some(build) = self.section_build(i) else {
            return;
        };
        self.zoom = Some((i, Player::new(build(), Instant::now())));
        self.zoom_section = true;
        self.view = PopupView::Zoom;
    }

    /// Section `i` opens its animation when it has one, else its text.
    fn open_section_or_pane(&mut self, i: usize) {
        if self.section_build(i).is_some() {
            self.open_section(i);
        } else {
            self.open_pane(i);
        }
    }

    /// Whether the menu's highlighted row has an animation to preview.
    fn menu_has_anim(&self) -> bool {
        let s0 = self.menu_sections();
        self.menu_sel < s0 || self.section_build(self.menu_sel - s0).is_some()
    }

    /// The animation behind menu row `sel` (not the overview), if any.
    fn preview_build(&self, sel: usize) -> Option<fn() -> Box<dyn Scene>> {
        let s0 = self.menu_sections();
        if sel < s0 {
            let (_, p) = self.player.as_ref()?;
            let z = p.as_ref()?.zooms().get(sel.checked_sub(1)?).copied()?;
            Some(z.build)
        } else {
            self.section_build(sel - s0)
        }
    }

    /// Menu index of the zoom bound to `key`.
    fn zoom_for_key(&self, key: char) -> Option<usize> {
        self.zoom_list().iter().position(|(k, _)| *k == key)
    }

    /// Full-size animation (the page's overview, or a zoom-in): caption on
    /// top, the scene filling the popup, the beat's notes beside it (or under
    /// it when narrow), zoom keys and beat dots at the foot.
    fn draw_scene(&mut self, frame: &mut Frame, r: Rect, label: &str, t: &Theme) {
        let zooming = self.view == PopupView::Zoom;
        // the zoom's art is its 3D scene, drawn beside the beat's caption and notes
        let orbit3d = if zooming {
            self.can_orbit()
        } else {
            self.overview_orbits()
        };
        let zooms = self.zoom_list();
        let zoom_name = match &self.zoom {
            Some((i, _)) if self.zoom_section => {
                self.pane_titles().get(*i).cloned().unwrap_or_default()
            }
            Some((i, _)) => zooms.get(*i).map_or("", |(_, l)| *l).to_string(),
            None => String::new(),
        };
        let orbit_key = if zooming && self.can_orbit() {
            "HJKL turn  F full view  "
        } else if orbit3d {
            "HJKL turn  0 reset "
        } else {
            ""
        };
        frame.render_widget(Clear, r);
        let paused = self.scene_player().is_some_and(|p| p.is_paused());
        let in_picture = self.scene_player().is_some_and(|p| p.notes_in_picture());
        let play = match (paused, in_picture) {
            (true, true) => "p resume  h/l beat",
            (false, true) => "p pause  h/l beat",
            (true, false) => "p resume  h/l beat  j/k notes",
            (false, false) => "p pause  h/l beat  j/k notes",
        };
        let letters = match (zooms.first(), zooms.last()) {
            (Some((a, _)), Some((b, _))) if a != b => format!("{a}-{b} zoom"),
            (Some((a, _)), _) => format!("{a} zoom"),
            _ => String::new(),
        };
        let switch = if self.section_build(0).is_some() {
            format!("{letters}  1-9 section")
        } else {
            letters
        };
        let (title, hint) = if zooming {
            (
                format!(" {label} \u{00B7} {zoom_name} "),
                format!(" {orbit_key}esc menu  {switch}  {play} "),
            )
        } else {
            let keys = match (zooms.first(), zooms.last()) {
                (Some((a, _)), Some((b, _))) if a != b => format!(" {a}-{b} zoom in "),
                (Some((a, _)), _) => format!(" {a} zoom in "),
                _ => String::new(),
            };
            (
                format!(" {label} "),
                format!("{keys} {orbit_key} esc menu  1-9 sections  {play} "),
            )
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(title, t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(block, r);
        let chips_h = u16::from(!zooming && !zooms.is_empty());
        let player = if zooming {
            self.zoom.as_mut().map(|(_, p)| p)
        } else {
            self.player.as_mut().and_then(|(_, p)| p.as_mut())
        };
        let Some(p) = player else {
            return;
        };
        let [cap_r, body_r, chips_r, dots_r] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Min(0),
            Constraint::Length(chips_h),
            Constraint::Length(1),
        ])
        .areas(inner);
        let min_w = p.min_size().0;
        let side_w = inner.width.saturating_sub(min_w + 2).min(46);
        let side = side_w >= 28;
        let (art_r, note_r) = if in_picture {
            // the notes are on the picture: it takes the whole body
            (body_r, Rect::new(body_r.x, body_r.y + body_r.height, body_r.width, 0))
        } else if side {
            let [a, _, n] = Layout::horizontal([
                Constraint::Length(inner.width - side_w - 2),
                Constraint::Length(2),
                Constraint::Length(side_w),
            ])
            .areas(body_r);
            (a, n)
        } else {
            let notes_h = 9.min(body_r.height / 3);
            let [a, n] =
                Layout::vertical([Constraint::Min(0), Constraint::Length(notes_h)]).areas(body_r);
            (a, n)
        };
        p.fit(art_r.width, art_r.height);
        let shot = p.shot();
        let time = p.time_at(p.now_ms());
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(format!("\u{25B6} {}", shot.caption), t.accent()),
                Span::styled(format!("   {}/{}", shot.beat + 1, shot.beats), t.dim()),
                Span::styled(if paused { "   PAUSED" } else { "" }, t.accent()),
            ]))
            .style(t.base()),
            cap_r,
        );
        if orbit3d {
            let model = if zooming {
                self.open_model(&time)
            } else if matches!(&self.player, Some(("LITHO", _))) {
                Model::LithoOverview(time)
            } else if matches!(&self.player, Some(("ARRAY", _))) {
                Model::ArrayOverview(time)
            } else if matches!(&self.player, Some(("BANK", _))) {
                Model::BankOverview(time)
            } else if matches!(&self.player, Some(("BANDWIDTH", _))) {
                Model::BwOverview(time)
            } else if matches!(&self.player, Some(("HBM STACK", _))) {
                Model::HbmOverview(time)
            } else if let Some(n) = self.player.as_ref().and_then(|(p, _)| super::diagrams_scene_chip::node(p)) {
                Model::ChipOverview(n.beats, n.keys, time)
            } else if let Some(n) = self.player.as_ref().and_then(|(p, _)| super::diagrams_scene_pkg::node(p)) {
                Model::PkgOverview(n.beats, n.keys, time)
            } else if let Some(n) = self.player.as_ref().and_then(|(p, _)| super::diagrams_scene_link::node(p)) {
                Model::LinkOverview(n.beats, n.keys, time)
            } else if let Some(n) = self.player.as_ref().and_then(|(p, _)| super::diagrams_scene_pwr::node(p)) {
                Model::PwrOverview(n.beats, n.keys, time)
            } else {
                Model::CellOverview(time)
            };
            let half = !zooming && self.coarse(Instant::now());
            self.paint_3d(frame, art_r, model, self.orbit, zooming || half);
        } else if let Some(img) = {
            let font = self.picker.font_size();
            p.pixels(
                &time,
                u32::from(art_r.width) * u32::from(font.width),
                u32::from(art_r.height) * u32::from(font.height),
            )
        } {
            self.paint_px(frame, art_r, img);
        } else {
            let art = shot.lines.join("\n");
            let art_lines = scene_lines(&art, t);
            frame.render_widget(Paragraph::new(art_lines).style(t.base()), art_r);
        }
        let mut notes: Vec<Line> = Vec::new();
        for (head, body) in [
            ("WHAT'S HAPPENING", shot.what),
            ("WHY IT MATTERS", shot.why),
        ] {
            if body.is_empty() {
                continue;
            }
            if !notes.is_empty() {
                notes.push(Line::default());
            }
            notes.push(Line::from(Span::styled(head, t.accent())));
            notes.push(Line::from(Span::styled(body, t.base())));
        }
        if !shot.facts.is_empty() {
            notes.push(Line::default());
            notes.push(Line::from(Span::styled("KEY NUMBERS", t.accent())));
            for f in shot.facts {
                notes.push(Line::from(vec![
                    Span::styled("\u{25B8} ", t.dim()),
                    Span::styled(*f, t.base()),
                ]));
            }
        }
        if !shot.look.is_empty() {
            notes.push(Line::default());
            notes.push(Line::from(Span::styled("LOOK FOR", t.accent())));
            notes.push(Line::from(Span::styled(shot.look, t.base())));
        }
        if self.notes_beat != Some(shot.beat) {
            self.notes_beat = Some(shot.beat);
            self.notes_scroll = 0;
        }
        let para = Paragraph::new(notes)
            .style(t.base())
            .wrap(Wrap { trim: true });
        let overflow = (para.line_count(note_r.width) as u16).saturating_sub(note_r.height);
        self.notes_scroll = self.notes_scroll.min(overflow);
        frame.render_widget(para.scroll((self.notes_scroll, 0)), note_r);
        if overflow > 0 && note_r.height > 1 {
            let more = if self.notes_scroll < overflow {
                "\u{25BC} j/k scrolls the notes"
            } else {
                "\u{25B2} j/k scrolls the notes"
            };
            let bar = Rect::new(note_r.x, note_r.y + note_r.height - 1, note_r.width, 1);
            frame.render_widget(Clear, bar);
            frame.render_widget(Paragraph::new(Span::styled(more, t.dim())), bar);
        }
        if chips_h > 0 {
            let mut chips = vec![Span::styled("zoom in  ", t.dim())];
            for (k, l) in &zooms {
                chips.push(Span::styled(format!("[{k}] "), t.accent()));
                chips.push(Span::styled(format!("{l}   "), t.base()));
            }
            frame.render_widget(Paragraph::new(Line::from(chips)).style(t.base()), chips_r);
        }
        let dots: Vec<Span> = (0..shot.beats)
            .map(|i| {
                if i == shot.beat {
                    Span::styled("\u{25CF} ", t.accent())
                } else if i < shot.beat {
                    Span::styled("\u{25CF} ", t.dim())
                } else {
                    Span::styled("\u{00B7} ", t.dim())
                }
            })
            .collect();
        frame.render_widget(Paragraph::new(Line::from(dots)).style(t.base()), dots_r);
    }

    /// The page's main navigation: the overview, its zoom-ins and the write-up
    /// sections as one list on the left, with a live preview of the highlighted
    /// item on the right.
    fn draw_menu(&mut self, frame: &mut Frame, r: Rect, label: &str, t: &Theme) {
        frame.render_widget(Clear, r);
        let hint = if self.browse {
            " j/k move  enter open  a-d zoom  1-9 sections  m list  esc close "
        } else {
            " j/k move  enter open  a-d zoom  1-9 sections  m preview  esc close "
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(format!(" {label} \u{00B7} menu "), t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::new(2, 2, 1, 0));
        let inner = block.inner(r);
        frame.render_widget(block, r);
        let zooms = self.zoom_list();
        let titles = self.pane_titles();
        let s0 = self.menu_sections();
        self.menu_sel = self.menu_sel.min((s0 + titles.len()).saturating_sub(1));
        let mut lines: Vec<Line> = Vec::new();
        let mut sel_line = 0usize;
        let item = |i: usize, text: String, sel: usize, t: &Theme| {
            if i == sel {
                Line::from(Span::styled(
                    format!(" \u{25B6} {text} "),
                    t.selected().add_modifier(Modifier::BOLD),
                ))
            } else {
                Line::from(Span::styled(format!("   {text} "), t.base()))
            }
        };
        lines.push(Line::from(Span::styled(
            "WATCH \u{00B7} the whole process, or one close-up",
            t.accent(),
        )));
        if self.menu_sel == 0 {
            sel_line = lines.len();
        }
        lines.push(item(0, "overview".to_string(), self.menu_sel, t));
        for (i, (k, l)) in zooms.iter().enumerate() {
            if 1 + i == self.menu_sel {
                sel_line = lines.len();
            }
            lines.push(item(1 + i, format!("{k}  {l}"), self.menu_sel, t));
        }
        lines.push(Line::default());
        lines.push(Line::from(Span::styled(
            "SECTIONS \u{00B7} the full write-up",
            t.accent(),
        )));
        for (i, title) in titles.iter().enumerate() {
            if s0 + i == self.menu_sel {
                sel_line = lines.len();
            }
            lines.push(item(s0 + i, title.clone(), self.menu_sel, t));
        }

        let side = self.browse && inner.width >= 80;
        let list_w = if side {
            (inner.width * 2 / 5).max(40)
        } else {
            inner.width
        };
        let [list_r, gap_r, prev_r] = Layout::horizontal([
            Constraint::Length(list_w),
            Constraint::Length(if side { 3 } else { 0 }),
            Constraint::Min(0),
        ])
        .areas(inner);
        let off = (sel_line + 1).saturating_sub(list_r.height as usize) as u16;
        frame.render_widget(
            Paragraph::new(lines).style(t.base()).scroll((off, 0)),
            list_r,
        );
        if !side || prev_r.width < 20 || prev_r.height < 4 {
            return;
        }
        let rule = vec![Line::from(Span::styled(" \u{2502}", t.dim())); gap_r.height as usize];
        frame.render_widget(Paragraph::new(rule), gap_r);

        let name = match self.menu_sel {
            0 => "overview".to_string(),
            i if i < s0 => zooms.get(i - 1).map_or("", |z| z.1).to_string(),
            i => titles.get(i - s0).cloned().unwrap_or_default(),
        };
        let [head_r, body_r] =
            Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(prev_r);
        frame.render_widget(
            Paragraph::new(Span::styled(format!("preview \u{00B7} {name}"), t.dim())),
            head_r,
        );
        if self.menu_has_anim() {
            self.draw_preview_scene(frame, body_r, t);
        } else {
            let art = self.cur_label().and_then(|l| visual(&l)).unwrap_or("");
            let panes = pane_ranges(art);
            let Some(&(p0, p1, _)) = panes.get(self.menu_sel - s0) else {
                return;
            };
            let art_lines = styled_lines(art, t);
            let p1 = p1.min(art_lines.len());
            let body: Vec<Line> = art_lines[p0.min(p1)..p1].to_vec();
            frame.render_widget(Paragraph::new(body).style(t.base()), body_r);
        }
    }

    /// The highlighted animation (the overview or a zoom-in) playing in the preview.
    fn draw_preview_scene(&mut self, frame: &mut Frame, r: Rect, t: &Theme) {
        let sel = self.menu_sel;
        let p = if sel == 0 {
            self.player.as_mut().and_then(|(_, p)| p.as_mut())
        } else {
            if self.preview.as_ref().map(|(j, _)| *j) != Some(sel) {
                let Some(build) = self.preview_build(sel) else {
                    return;
                };
                self.preview = Some((sel, Player::new(build(), Instant::now())));
            }
            self.preview.as_mut().map(|(_, p)| p)
        };
        let Some(p) = p else {
            return;
        };
        let [cap_r, art_r] = Layout::vertical([Constraint::Length(1), Constraint::Min(0)]).areas(r);
        p.fit(art_r.width, art_r.height);
        let shot = p.shot();
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(format!("\u{25B6} {}", shot.caption), t.accent()),
                Span::styled(format!("   {}/{}", shot.beat + 1, shot.beats), t.dim()),
            ]))
            .style(t.base()),
            cap_r,
        );
        let art = shot.lines.join("\n");
        frame.render_widget(Paragraph::new(scene_lines(&art, t)).style(t.base()), art_r);
    }

    fn draw_popup(&mut self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(n) = self.nodes[self.tab].get(self.sel) else {
            return;
        };
        let label = n.label.clone();
        match self.view {
            PopupView::Overview | PopupView::Zoom if self.has_scene() => {
                return self.draw_scene(frame, area, &label, t);
            }
            PopupView::Full if self.has_scene() => return self.draw_full(frame, area, t),
            PopupView::Menu => return self.draw_menu(frame, area, &label, t),
            _ => {}
        }
        let text = describe(&n.label).unwrap_or("No description yet.");
        let art = visual(&n.label).unwrap_or("");
        let r = area;
        let wrap_w = r.width.saturating_sub(4).max(1) as usize;
        let desc = wrap_words(text, wrap_w);
        let mut lines: Vec<Line> = desc
            .into_iter()
            .map(|l| Line::from(Span::styled(l, t.base())))
            .collect();
        lines.push(Line::default());
        let panes = pane_ranges(art);
        self.pane = self.pane.min(panes.len() - 1);
        let art_lines = styled_lines(art, t);
        let inner_h = r.height.saturating_sub(2);
        if self.hot_moved {
            if let Some(h) = self.hots.get(self.hsel) {
                let row = h.row as usize;
                if let Some(p) = panes.iter().position(|p| row >= p.0 && row < p.1) {
                    if p != self.pane {
                        self.pane = p;
                        self.popup_scroll = 0;
                    }
                }
            }
        }
        let hh = (lines.len() as u16).min(inner_h.saturating_sub(8));
        let tabs_h = u16::from(panes.len() > 1);
        let pane_h = inner_h.saturating_sub(hh + tabs_h);
        let (p0, p1, _) = panes[self.pane];
        let p1 = p1.min(art_lines.len());
        let pane_lines: Vec<Line> = art_lines[p0.min(p1)..p1].to_vec();
        let total = pane_lines.len() as u16;
        if self.hot_moved {
            if let Some(h) = self.hots.get(self.hsel) {
                let y = (h.row as usize).saturating_sub(p0) as u16;
                if y < self.popup_scroll {
                    self.popup_scroll = y.saturating_sub(2);
                } else if y >= self.popup_scroll + pane_h {
                    self.popup_scroll = (y + 3).saturating_sub(pane_h);
                }
            }
            self.hot_moved = false;
        }
        self.popup_scroll = self.popup_scroll.min(total.saturating_sub(pane_h));
        frame.render_widget(Clear, r);
        let hint = if self.hots.is_empty() {
            " [/] pane  j/k scroll  g/G top/bottom  q close "
        } else {
            " [/] pane  h/l/tab spot  j/k spot above/below  enter details  ctrl-d/u scroll  q close "
        };
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(format!(" {} ", n.label), t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(block, r);
        let [head_r, tabs_r, pane_r] = Layout::vertical([
            Constraint::Length(hh),
            Constraint::Length(tabs_h),
            Constraint::Min(0),
        ])
        .areas(inner);
        frame.render_widget(Paragraph::new(lines).style(t.base()), head_r);
        if tabs_h > 0 {
            let mut spans = Vec::new();
            for (i, p) in panes.iter().enumerate() {
                let title = art.lines().nth(p.2).unwrap_or("");
                let title = title.strip_prefix("# ").unwrap_or(title);
                let num = title.split(['.', ' ']).next().unwrap_or("");
                if i == self.pane {
                    let name = title.split(':').next().unwrap_or(title);
                    spans.push(Span::styled(
                        format!(" {name} "),
                        t.selected().add_modifier(Modifier::BOLD),
                    ));
                } else {
                    let lab = if num.chars().all(|c| c.is_ascii_digit()) && !num.is_empty() {
                        num.to_string()
                    } else {
                        (i + 1).to_string()
                    };
                    spans.push(Span::styled(format!(" {lab} "), t.dim()));
                }
            }
            frame.render_widget(Paragraph::new(Line::from(spans)).style(t.base()), tabs_r);
        }
        frame.render_widget(
            Paragraph::new(pane_lines)
                .style(t.base())
                .scroll((self.popup_scroll, 0)),
            pane_r,
        );
        let buf = frame.buffer_mut();
        for (i, h) in self.hots.iter().enumerate() {
            let row = h.row as usize;
            if row < p0 || row >= p1 {
                continue;
            }
            let Some(y) = ((row - p0) as u16).checked_sub(self.popup_scroll) else {
                continue;
            };
            if y >= pane_r.height {
                continue;
            }
            let style = if i == self.hsel {
                t.selected().add_modifier(Modifier::BOLD)
            } else {
                t.accent().add_modifier(Modifier::UNDERLINED)
            };
            for dx in 0..h.len {
                let x = h.col + dx;
                if x < pane_r.width {
                    buf[(pane_r.x + x, pane_r.y + y)].set_style(style);
                }
            }
        }
        if self.detail {
            self.draw_detail(frame, area, t);
        }
    }

    fn draw_detail(&mut self, frame: &mut Frame, area: Rect, t: &Theme) {
        let Some(h) = self.hots.get(self.hsel) else {
            return;
        };
        let r = area;
        let hint =
            " hjkl move (l into the visual)  J/K scroll visual  H/L section  space page  q back ";
        let block = Block::new()
            .borders(Borders::ALL)
            .border_style(t.accent())
            .title(Span::styled(format!(" {} ", h.label), t.title()))
            .title_bottom(Span::styled(hint, t.dim()))
            .padding(ratatui::widgets::Padding::horizontal(1));
        let inner = block.inner(r);
        frame.render_widget(Clear, r);
        frame.render_widget(block, r);

        let ov = self.ptab == 0 && (self.card.is_some() || self.mol.is_some());
        let [tab_r, body] =
            Layout::vertical([Constraint::Length(2), Constraint::Min(1)]).areas(inner);
        let tabs: Vec<Span> = self
            .secs
            .iter()
            .enumerate()
            .map(|(i, (title, _))| {
                let label = format!(" {title} ");
                if i != self.ptab {
                    Span::styled(label, t.dim())
                } else if self.focus == Focus::Tabs {
                    Span::styled(label, t.selected().add_modifier(Modifier::BOLD))
                } else {
                    Span::styled(label, t.accent().add_modifier(Modifier::UNDERLINED))
                }
            })
            .collect();
        frame.render_widget(
            Paragraph::new(Line::from(tabs)).wrap(Wrap { trim: false }),
            tab_r,
        );

        // Overview tab: summary first, then the diagram (or atom grid) under it.
        if ov {
            if let Some(card) = self.card {
                let desc = wrap_words(card.desc, body.width.max(1) as usize);
                let mut lines: Vec<Line> = desc
                    .into_iter()
                    .map(|l| Line::from(Span::styled(l, t.base())))
                    .collect();
                lines.push(Line::default());
                lines.extend(styled_lines(card.top.art, t));
                let total = lines.len() as u16;
                self.vscroll = self.vscroll.min(total.saturating_sub(body.height));
                frame.render_widget(
                    Paragraph::new(lines)
                        .style(t.base())
                        .scroll((self.vscroll, 0)),
                    body,
                );
            } else if let Some(mol) = &self.mol {
                let mut head = vec![mol.formula_line(t), mol.mass_line(t), Line::default()];
                let cur = if self.focus == Focus::Grid {
                    self.mol_cur
                } else {
                    self.tour(mol.atoms.len())
                };
                head.extend(mol.lines(cur, t));
                head.push(Line::default());
                let info = wrap_words(mol.atoms[cur].info, body.width.max(1) as usize);
                for i in 0..4 {
                    head.push(Line::from(Span::styled(
                        info.get(i).cloned().unwrap_or_default(),
                        t.base(),
                    )));
                }
                frame.render_widget(Paragraph::new(head).style(t.base()), body);
            }
            return;
        }
        let body_full = body;

        // Left: section tabs + text with a line cursor. Right: that section's visual.
        let n = self.secs.len();
        let card = h.label;
        self.ptab = self.ptab.min(n.saturating_sub(1));
        let (sec_title, sec_text) = self.secs.get(self.ptab).copied().unwrap_or(("", ""));
        let page = self
            .nodes
            .get(self.tab)
            .and_then(|n| n.get(self.sel))
            .and_then(|n| page_key(&n.label))
            .unwrap_or("");
        let vis = match self.card {
            Some(c) => c.secs.get(self.ptab - 1).map(|s| s.vis),
            None => visual_for(page, card, sec_title),
        };
        const GAP: u16 = 3;
        let lw = if vis.is_some() && body.width >= 70 {
            body.width * 38 / 100
        } else {
            body.width
        };
        let body = body_full;
        let text_r = Rect::new(body.x, body.y, lw, body.height);
        let para = Paragraph::new(styled_lines(sec_text, t))
            .style(t.base())
            .wrap(Wrap { trim: false });
        let total = para.line_count(text_r.width) as u16;
        self.pcur = self.pcur.min(total.saturating_sub(1));
        // Keep the cursor row on screen.
        if self.pcur < self.pscroll {
            self.pscroll = self.pcur;
        } else if self.pcur >= self.pscroll + text_r.height {
            self.pscroll = self.pcur + 1 - text_r.height;
        }
        self.pscroll = self.pscroll.min(total.saturating_sub(text_r.height));
        frame.render_widget(para.scroll((self.pscroll, 0)), text_r);
        if self.focus == Focus::Text && text_r.height > 0 {
            let y = text_r.y + self.pcur - self.pscroll;
            let buf = frame.buffer_mut();
            for x in text_r.x..text_r.x + text_r.width {
                buf[(x, y)].set_style(t.selected());
            }
        }
        if let (Some(vis), true) = (&vis, lw < body.width) {
            let x = body.x + lw + GAP;
            let right = Rect::new(
                x,
                body.y,
                (body.x + body.width).saturating_sub(x),
                body.height,
            );
            let spots = vis.placed();
            self.vcur = self.vcur.min(spots.len().saturating_sub(1));
            let art_h = vis.art.lines().count() as u16;
            let focused = self.focus == Focus::Visual;
            let cur = if focused {
                self.vcur
            } else {
                self.tour(spots.len())
            };
            // Keep the cursor (or the tour's current spot) on screen.
            {
                if let Some(sp) = spots.get(cur) {
                    if sp.row < self.vscroll {
                        self.vscroll = sp.row;
                    } else if sp.row >= self.vscroll + right.height {
                        self.vscroll = sp.row + 1 - right.height;
                    }
                }
            }
            self.vscroll = self.vscroll.min(art_h.saturating_sub(right.height));
            let vs = self.vscroll;
            frame.render_widget(
                Paragraph::new(styled_lines(vis.art, t))
                    .style(t.base())
                    .scroll((vs, 0)),
                right,
            );
            let info_y = right.y + art_h.saturating_sub(vs).min(right.height) + 1;
            let info_h = (right.y + right.height).saturating_sub(info_y);
            if !spots.is_empty() {
                let buf = frame.buffer_mut();
                for (i, sp) in spots.iter().enumerate() {
                    let style = if i == cur {
                        t.selected().add_modifier(Modifier::BOLD)
                    } else {
                        t.accent().add_modifier(Modifier::UNDERLINED)
                    };
                    if sp.row < vs || sp.row - vs >= right.height {
                        continue;
                    }
                    for dx in 0..sp.len {
                        if sp.col + dx < right.width {
                            buf[(right.x + sp.col + dx, right.y + sp.row - vs)].set_style(style);
                        }
                    }
                }
                if let Some(sp) = spots.get(cur) {
                    let mut lines: Vec<Line> = Vec::new();
                    if !focused && spots.len() > 1 {
                        lines.push(Line::from(Span::styled(
                            format!("\u{25B6} {}/{}  l to stop here", cur + 1, spots.len()),
                            t.dim(),
                        )));
                    }
                    let room = (info_h as usize).saturating_sub(lines.len());
                    lines.extend(
                        wrap_words(sp.info, right.width.max(1) as usize)
                            .into_iter()
                            .take(room)
                            .map(|l| Line::from(Span::styled(l, t.base()))),
                    );
                    frame.render_widget(
                        Paragraph::new(lines),
                        Rect::new(right.x, info_y, right.width, info_h),
                    );
                }
            }
        }
    }

    /// Auto-tour index into `n` items, from the tour clock.
    fn tour(&self, n: usize) -> usize {
        (self.tour_start.elapsed().as_millis() / TOUR_MS) as usize % n.max(1)
    }

    fn cur_visual(&self) -> Option<super::diagrams_vis::Visual> {
        if let Some(c) = self.card {
            return c.secs.get(self.ptab.checked_sub(1)?).map(|s| s.vis);
        }
        let card = self.hots.get(self.hsel)?.label;
        let page = page_key(&self.nodes.get(self.tab)?.get(self.sel)?.label)?;
        visual_for(page, card, self.secs.get(self.ptab)?.0)
    }

    /// Keys inside a detail card. The cursor walks atom grid -> tab strip ->
    /// text with j/k; h/l move along the tab strip or the atom grid.
    fn detail_key(&mut self, key: KeyEvent) {
        let n = self.secs.len().max(1);
        let spots: Vec<Placed> = self.cur_visual().map(|v| v.placed()).unwrap_or_default();
        let set_tab = |s: &mut Self, tab: usize| {
            s.ptab = tab;
            if tab > 0 && s.focus == Focus::Grid {
                s.focus = Focus::Tabs;
            } else if tab == 0 && s.focus != Focus::Grid {
                s.focus = Focus::Tabs;
            }
            s.vcur = 0;
            s.vscroll = 0;
            s.tour_start = Instant::now();
            s.pcur = 0;
            s.pscroll = 0;
        };
        let (h, j, k, l) = (
            matches!(key.code, KeyCode::Char('h') | KeyCode::Left),
            matches!(key.code, KeyCode::Char('j') | KeyCode::Down),
            matches!(key.code, KeyCode::Char('k') | KeyCode::Up),
            matches!(key.code, KeyCode::Char('l') | KeyCode::Right),
        );
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => self.detail = false,
            KeyCode::Tab | KeyCode::Char('L') => set_tab(self, (self.ptab + 1) % n),
            KeyCode::BackTab | KeyCode::Char('H') => set_tab(self, (self.ptab + n - 1) % n),
            KeyCode::Char('J') => self.vscroll = self.vscroll.saturating_add(3),
            KeyCode::Char('K') => self.vscroll = self.vscroll.saturating_sub(3),
            KeyCode::Char(' ') | KeyCode::PageDown => self.pcur = self.pcur.saturating_add(8),
            KeyCode::PageUp => self.pcur = self.pcur.saturating_sub(8),
            _ => match self.focus {
                Focus::Grid => {
                    let Some(mol) = &self.mol else {
                        self.focus = Focus::Tabs;
                        return;
                    };
                    let (dx, dy) = (i32::from(l) - i32::from(h), i32::from(j) - i32::from(k));
                    let next = mol.step(self.mol_cur, dx, dy);
                    if j && next == self.mol_cur {
                        self.focus = Focus::Tabs;
                    } else {
                        self.mol_cur = next;
                    }
                }
                Focus::Tabs => {
                    if l {
                        set_tab(self, (self.ptab + 1).min(n - 1));
                    } else if h {
                        set_tab(self, self.ptab.saturating_sub(1));
                    } else if j {
                        if self.ptab > 0 || (self.card.is_none() && self.mol.is_none()) {
                            self.focus = Focus::Text;
                        }
                    } else if k && self.mol.is_some() && self.ptab == 0 {
                        self.focus = Focus::Grid;
                        self.mol_cur = self.tour(self.mol.as_ref().map_or(1, |m| m.atoms.len()));
                    }
                }
                Focus::Text => {
                    if j {
                        self.pcur = self.pcur.saturating_add(1);
                    } else if k {
                        if self.pcur == 0 {
                            self.focus = Focus::Tabs;
                        } else {
                            self.pcur -= 1;
                        }
                    } else if l && !spots.is_empty() {
                        self.focus = Focus::Visual;
                        self.vcur = self.tour(spots.len());
                    }
                }
                Focus::Visual => {
                    let (dx, dy) = (i32::from(l) - i32::from(h), i32::from(j) - i32::from(k));
                    let next = vis_step(&spots, self.vcur, dx, dy);
                    if h && next == self.vcur {
                        self.focus = Focus::Text;
                    } else {
                        self.vcur = next;
                    }
                }
            },
        }
    }

    fn max_scroll(&self) -> u16 {
        // title + blank + footer rows are outside the body
        art_size(&DIAGRAMS[self.tab]).1.saturating_sub(self.body_h)
    }
}

impl Screen for Diagrams {
    fn draw(&mut self, frame: &mut Frame) {
        let t = self.theme;
        let area = frame.area();
        frame.render_widget(Block::new().style(t.base()), area);
        let [tabs, title, body, tickers, foot] = Layout::vertical([
            Constraint::Length(1),
            Constraint::Length(2),
            Constraint::Min(1),
            Constraint::Length(1),
            Constraint::Length(1),
        ])
        .areas(area);
        let d = &DIAGRAMS[self.tab];
        self.body_h = body.height;
        self.scroll = self.scroll.min(self.max_scroll());

        frame.render_widget(Paragraph::new(tab_line(self.tab, &t)), tabs);
        frame.render_widget(
            Paragraph::new(Line::from(Span::styled(format!(" {}", d.title), t.title()))),
            title,
        );
        let art_area = body.inner(ratatui::layout::Margin::new(1, 0));
        frame.render_widget(
            Paragraph::new(styled_lines(d.art, &t))
                .style(t.base())
                .scroll((self.scroll, 0)),
            art_area,
        );
        self.draw_selection(frame, art_area, &t);
        frame.render_widget(
            Paragraph::new(Line::from(vec![
                Span::styled(" related: ", t.dim()),
                Span::styled(d.tickers, t.accent()),
            ])),
            tickers,
        );
        render_footer(frame, foot, KEYS, None, &t);
        if self.popup {
            self.draw_popup(frame, area, &t);
        }
        if self.help {
            render_overlay(frame, area, "diagrams", KEYS, &t);
        }
    }

    fn on_key(&mut self, key: KeyEvent) -> Action {
        if self.help {
            self.help = false;
            return Action::None;
        }
        if self.popup && self.detail {
            self.detail_key(key);
            return Action::None;
        }
        if self.popup && self.view == PopupView::Full {
            self.full_key(key.code, Instant::now());
            return Action::None;
        }
        if self.popup
            && matches!(self.view, PopupView::Overview | PopupView::Zoom)
            && self.has_scene()
            && self.playback_key(key.code)
        {
            return Action::None;
        }
        if self.popup && self.view == PopupView::Overview && self.has_scene() {
            match key.code {
                KeyCode::Char('q') => self.popup = false,
                // HJKL turn the 3D overview, +/- zoom, 0 resets the camera
                KeyCode::Char('0') if self.overview_orbits() => {
                    self.orbit = poly3d::View::default()
                }
                KeyCode::Char(c) if self.overview_orbits() && turn_key(c).is_some() => {
                    if let Some(hit) = turn_key(c) {
                        self.camera_step(hit, Instant::now());
                    }
                }
                KeyCode::Char('m') | KeyCode::Esc | KeyCode::Enter | KeyCode::Char(' ') => {
                    self.browse = key.code == KeyCode::Char('m');
                    self.menu_sel = 0;
                    self.zoom = None;
                    self.view = PopupView::Menu;
                }
                KeyCode::Char(c @ '1'..='9') => {
                    self.open_section_or_pane(c as usize - '1' as usize)
                }
                KeyCode::Char(c) => {
                    if let Some(i) = self.zoom_for_key(c) {
                        self.open_zoom(i);
                    }
                }
                _ => {}
            }
            return Action::None;
        }
        if self.popup && self.view == PopupView::Zoom {
            match key.code {
                KeyCode::Char('q') | KeyCode::Esc | KeyCode::Char('m') => {
                    self.browse |= key.code == KeyCode::Char('m');
                    let i = self.zoom.as_ref().map_or(0, |(i, _)| *i);
                    self.menu_sel = if self.zoom_section {
                        self.menu_sections() + i
                    } else {
                        1 + i
                    };
                    self.view = PopupView::Menu;
                }
                // numbers reach the sections from any scene, as letters reach the zooms
                KeyCode::Char(c @ '1'..='9') => self.open_section(c as usize - '1' as usize),
                KeyCode::Char('F') if self.can_orbit() => self.view = PopupView::Full,
                // HJKL turn the 3D model on the left; lowercase keep the beats and notes
                KeyCode::Char('0') if self.can_orbit() => self.orbit = poly3d::View::default(),
                KeyCode::Char(c) if self.can_orbit() && turn_key(c).is_some() => {
                    if let Some(hit) = turn_key(c) {
                        self.camera_step(hit, Instant::now());
                    }
                }
                KeyCode::Char(c) => {
                    if let Some(i) = self.zoom_for_key(c) {
                        self.open_zoom(i);
                    }
                }
                _ => {}
            }
            return Action::None;
        }
        if self.popup && self.view == PopupView::Menu {
            let s0 = self.menu_sections();
            let last = (s0 + self.pane_titles().len()).saturating_sub(1);
            match key.code {
                KeyCode::Char('q') | KeyCode::Esc => self.popup = false,
                KeyCode::Char('j') | KeyCode::Down | KeyCode::Tab => {
                    self.menu_sel = (self.menu_sel + 1).min(last);
                }
                KeyCode::Char('k') | KeyCode::Up | KeyCode::BackTab => {
                    self.menu_sel = self.menu_sel.saturating_sub(1);
                }
                KeyCode::Char('g') | KeyCode::Home => self.menu_sel = 0,
                KeyCode::Char('G') | KeyCode::End => self.menu_sel = last,
                KeyCode::Char('m') => self.browse = !self.browse,
                KeyCode::Enter | KeyCode::Char(' ') => match self.menu_sel {
                    0 => self.view = PopupView::Overview,
                    i if i < s0 => self.open_zoom(i - 1),
                    i => self.open_section_or_pane(i - s0),
                },
                KeyCode::Char(c @ '1'..='9') => {
                    self.open_section_or_pane(c as usize - '1' as usize)
                }
                KeyCode::Char(c) => {
                    if let Some(i) = self.zoom_for_key(c) {
                        self.open_zoom(i);
                    }
                }
                _ => {}
            }
            return Action::None;
        }
        if self.popup {
            let half = (self.body_h / 2).max(1);
            let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
            match key.code {
                KeyCode::Char('q') | KeyCode::Esc => {
                    if self.has_scene() {
                        self.menu_sel = self.menu_sections() + self.pane;
                        self.view = PopupView::Menu;
                    } else {
                        self.popup = false;
                    }
                }
                KeyCode::Char('m') if self.has_scene() => {
                    self.browse = true;
                    self.menu_sel = self.menu_sections() + self.pane;
                    self.view = PopupView::Menu;
                }
                KeyCode::Enter => {
                    if let Some(h) = self.hots.get(self.hsel) {
                        self.detail = true;
                        let page = self
                            .nodes
                            .get(self.tab)
                            .and_then(|n| n.get(self.sel))
                            .and_then(|n| page_key(&n.label))
                            .unwrap_or("");
                        self.card = super::diagrams_cards::find(page, h.label);
                        self.secs = match self.card {
                            Some(c) => c.secs.iter().map(|s| (s.title, s.text)).collect(),
                            None => sections(h.body),
                        };
                        let has_mol = self.card.is_none() && mol_for(h.label).is_some();
                        if self.card.is_some() || has_mol {
                            self.secs.insert(0, ("Overview", ""));
                        }
                        self.vscroll = 0;
                        self.ptab = 0;
                        self.pscroll = 0;
                        self.pcur = 0;
                        self.vcur = 0;
                        self.mol = if self.card.is_some() {
                            None
                        } else {
                            mol_for(h.label)
                        };
                        self.mol_cur = 0;
                        self.tour_start = Instant::now();
                        // Open on the tab strip so the atom grid auto-tours; k freezes it.
                        self.focus = if self.mol.is_some() || self.card.is_some() {
                            Focus::Tabs
                        } else {
                            Focus::Text
                        };
                    }
                }
                KeyCode::Char(c @ ('[' | ']')) => self.step_pane(if c == ']' { 1 } else { -1 }),
                KeyCode::Char('l') | KeyCode::Right | KeyCode::Tab => self.step_hot(1),
                KeyCode::Char('h') | KeyCode::Left | KeyCode::BackTab => self.step_hot(-1),
                KeyCode::Char('j') | KeyCode::Down => {
                    if !self.step_hot_row(1) {
                        self.popup_scroll = self.popup_scroll.saturating_add(1)
                    }
                }
                KeyCode::Char('k') | KeyCode::Up => {
                    if !self.step_hot_row(-1) {
                        self.popup_scroll = self.popup_scroll.saturating_sub(1)
                    }
                }
                KeyCode::Char('d') if ctrl => {
                    self.popup_scroll = self.popup_scroll.saturating_add(half)
                }
                KeyCode::Char('u') if ctrl => {
                    self.popup_scroll = self.popup_scroll.saturating_sub(half)
                }
                KeyCode::PageDown | KeyCode::Char(' ') => {
                    self.popup_scroll = self.popup_scroll.saturating_add(half * 2)
                }
                KeyCode::PageUp => self.popup_scroll = self.popup_scroll.saturating_sub(half * 2),
                KeyCode::Char('g') | KeyCode::Home => self.popup_scroll = 0,
                KeyCode::Char('G') | KeyCode::End => self.popup_scroll = u16::MAX,
                _ => {}
            }
            return Action::None;
        }
        let half = (self.body_h / 2).max(1);
        if key.modifiers.contains(KeyModifiers::CONTROL) {
            match key.code {
                KeyCode::Char('d') => self.scroll = self.scroll.saturating_add(half),
                KeyCode::Char('u') => self.scroll = self.scroll.saturating_sub(half),
                _ => {}
            }
            return Action::None;
        }
        match key.code {
            KeyCode::Char('q') | KeyCode::Esc => return Action::Quit,
            KeyCode::Char('?') => self.help = true,
            KeyCode::Char('L') | KeyCode::Char(']') => self.goto(self.tab + 1),
            KeyCode::Char('H') | KeyCode::Char('[') => self.goto(self.tab + DIAGRAMS.len() - 1),
            KeyCode::Char('l') | KeyCode::Right | KeyCode::Tab => self.step_node(1),
            KeyCode::Char('h') | KeyCode::Left | KeyCode::BackTab => self.step_node(-1),
            KeyCode::Enter => {
                self.popup = !self.nodes[self.tab].is_empty();
                self.popup_scroll = 0;
                self.pane = 0;
                self.anim_start = Instant::now();
                self.player = self.cur_label().and_then(|l| page_key(&l)).map(|page| {
                    (
                        page,
                        scene_for(page).map(|sc| Player::new(sc, self.anim_start)),
                    )
                });
                self.view = if self.has_scene() {
                    PopupView::Menu
                } else {
                    PopupView::Pane
                };
                self.menu_sel = 0;
                self.zoom = None;
                self.preview = None;
                self.browse = false;
                self.detail = false;
                self.hsel = 0;
                self.hots = self.nodes[self.tab]
                    .get(self.sel)
                    .map(|n| find_hots(&n.label))
                    .unwrap_or_default();
            }
            KeyCode::Char('j') | KeyCode::Down => {
                if !self.step_row(1) {
                    self.scroll = self.scroll.saturating_add(1)
                }
            }
            KeyCode::Char('k') | KeyCode::Up => {
                if !self.step_row(-1) {
                    self.scroll = self.scroll.saturating_sub(1)
                }
            }
            KeyCode::Char('g') | KeyCode::Home => self.scroll = 0,
            KeyCode::Char('G') | KeyCode::End => self.scroll = self.max_scroll(),
            KeyCode::Char(c @ '1'..='9') => {
                let i = c as usize - '1' as usize;
                if i < DIAGRAMS.len() {
                    self.goto(i);
                }
            }
            _ => {}
        }
        Action::None
    }

    fn shows_tape(&self) -> bool {
        false
    }

    fn tick(&mut self) -> Action {
        let now = Instant::now();
        self.full_tick(now);
        // the loop draws before each tick, so `sharpen` lives for exactly one draw
        self.sharpen = false;
        if self.settle_until.is_some_and(|until| now >= until) {
            self.settle_until = None;
            self.sharpen = true;
        }
        Action::None
    }

    fn needs_redraw(&self) -> bool {
        self.animating() || self.settle_until.is_some() || self.sharpen
    }

    fn poll_interval(&self) -> Duration {
        if matches!(self.view, PopupView::Full | PopupView::Zoom | PopupView::Overview) && self.coarse(Instant::now()) {
            MOTION_FRAME
        } else if self.animating() {
            FRAME
        } else {
            Duration::from_millis(100)
        }
    }
}

// ---- PDF export ------------------------------------------------------

const CELL_W: f64 = 8.43;
const CELL_H: f64 = 17.0;
const PAGE_BG: &str = "#1e1f29";

fn hex(c: Color, fallback: &str) -> String {
    match c {
        Color::Rgb(r, g, b) => format!("#{r:02x}{g:02x}{b:02x}"),
        Color::White => "#e6e6e6".into(),
        Color::DarkGray => "#6b6f85".into(),
        Color::Gray => "#a0a3b5".into(),
        _ => fallback.into(),
    }
}

fn xml(c: char) -> String {
    match c {
        '&' => "&amp;".into(),
        '<' => "&lt;".into(),
        '>' => "&gt;".into(),
        _ => c.to_string(),
    }
}

/// (left, right, up, down) arms of a box-drawing char: 0 none, 1 light,
/// 2 double. Drawn as strokes because font corner glyphs do not line up
/// with their straight neighbours.
fn box_arms(c: char) -> Option<(u8, u8, u8, u8)> {
    Some(match c {
        '─' => (1, 1, 0, 0),
        '│' => (0, 0, 1, 1),
        '┌' => (0, 1, 0, 1),
        '┐' => (1, 0, 0, 1),
        '└' => (0, 1, 1, 0),
        '┘' => (1, 0, 1, 0),
        '├' => (0, 1, 1, 1),
        '┤' => (1, 0, 1, 1),
        '┬' => (1, 1, 0, 1),
        '┴' => (1, 1, 1, 0),
        '┼' => (1, 1, 1, 1),
        '═' => (2, 2, 0, 0),
        '║' => (0, 0, 2, 2),
        '╔' => (0, 2, 0, 2),
        '╗' => (2, 0, 0, 2),
        '╚' => (0, 2, 2, 0),
        '╝' => (2, 0, 2, 0),
        _ => return None,
    })
}

fn box_strokes(x: f64, y: f64, arms: (u8, u8, u8, u8), color: &str) -> String {
    let (cx, cy) = (x + CELL_W / 2.0, y + CELL_H / 2.0 - 1.0);
    let mut s = String::new();
    let mut seg = |kind: u8, dx: f64, dy: f64| {
        let offs: &[f64] = match kind {
            0 => return,
            1 => &[0.0],
            _ => &[-1.6, 1.6],
        };
        let (ex, ey) = (cx + dx * CELL_W / 2.0, cy + dy * CELL_H / 2.0);
        for o in offs {
            // perpendicular offset: horizontal arms shift in y, vertical in x
            let (ox, oy) = if dy == 0.0 { (0.0, *o) } else { (*o, 0.0) };
            s.push_str(&format!(
                "<line x1='{:.2}' y1='{:.2}' x2='{:.2}' y2='{:.2}' stroke='{color}' stroke-width='1.1'/>",
                cx + ox,
                cy + oy,
                ex + ox,
                ey + oy
            ));
        }
    };
    seg(arms.0, -1.0, 0.0);
    seg(arms.1, 1.0, 0.0);
    seg(arms.2, 0.0, -1.0);
    seg(arms.3, 0.0, 1.0);
    s
}

/// One cell per glyph at a fixed pitch; box lines are strokes.
fn buffer_to_svg(buf: &Buffer) -> String {
    let (w, h) = (buf.area.width, buf.area.height);
    let mut svg = format!(
        "<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' \
         font-family='Menlo, DejaVu Sans Mono, monospace' font-size='14'>\
         <rect width='100%' height='100%' fill='{PAGE_BG}'/>",
        f64::from(w) * CELL_W,
        f64::from(h) * CELL_H
    );
    for y in 0..h {
        for x in 0..w {
            let cell = &buf[(x, y)];
            let sym = cell.symbol();
            if sym.trim().is_empty() {
                continue;
            }
            if let Some(arms) = sym.chars().next().and_then(box_arms) {
                svg.push_str(&box_strokes(
                    f64::from(x) * CELL_W,
                    f64::from(y) * CELL_H,
                    arms,
                    &hex(cell.fg, "#6b6f85"),
                ));
                continue;
            }
            let weight = if cell.modifier.contains(Modifier::BOLD) {
                " font-weight='bold'"
            } else {
                ""
            };
            let slant = if cell.modifier.contains(Modifier::ITALIC) {
                " font-style='italic'"
            } else {
                ""
            };
            svg.push_str(&format!(
                "<text x='{:.2}' y='{:.2}' fill='{}'{weight}{slant}>{}</text>",
                f64::from(x) * CELL_W,
                f64::from(y) * CELL_H + CELL_H - 4.0,
                hex(cell.fg, "#e6e6e6"),
                sym.chars().map(xml).collect::<String>(),
            ));
        }
    }
    svg.push_str("</svg>");
    svg
}

fn render_page(d: &Diagram, t: &Theme) -> Buffer {
    let (aw, ah) = art_size(d);
    let area = Rect::new(0, 0, aw + 4, ah + 5);
    let mut buf = Buffer::empty(area);
    let [title, body, tickers] = Layout::vertical([
        Constraint::Length(2),
        Constraint::Min(1),
        Constraint::Length(1),
    ])
    .areas(area.inner(ratatui::layout::Margin::new(2, 1)));
    Paragraph::new(Line::from(Span::styled(d.title, t.title()))).render(title, &mut buf);
    Paragraph::new(styled_lines(d.art, t)).render(body, &mut buf);
    Paragraph::new(Line::from(vec![
        Span::styled("related: ", t.dim()),
        Span::styled(d.tickers, t.accent()),
        Span::styled("   finlarp diagrams", t.dim()),
    ]))
    .render(tickers, &mut buf);
    buf
}

/// Writes `<dir>/NN-<tab>.pdf` for every diagram via rsvg-convert. Returns
/// the paths written.
pub fn export_pdfs(dir: &Path, t: &Theme) -> io::Result<Vec<String>> {
    // white-on-dark theme colours need an explicit bg; default() has fg=White
    let mut t = *t;
    t.bg = None;
    std::fs::create_dir_all(dir)?;
    let mut out = Vec::new();
    for (i, d) in DIAGRAMS.iter().enumerate() {
        let slug: String = d
            .tab
            .to_lowercase()
            .chars()
            .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
            .collect();
        let svg_path = dir.join(format!("{:02}-{slug}.svg", i + 1));
        let pdf_path = dir.join(format!("{:02}-{slug}.pdf", i + 1));
        std::fs::write(&svg_path, buffer_to_svg(&render_page(d, &t)))?;
        let status = Command::new("rsvg-convert")
            .args(["-f", "pdf", "-o"])
            .arg(&pdf_path)
            .arg(&svg_path)
            .status()
            .map_err(|e| io::Error::other(format!("rsvg-convert (brew install librsvg): {e}")))?;
        if !status.success() {
            return Err(io::Error::other(format!("rsvg-convert failed on {slug}")));
        }
        out.push(pdf_path.display().to_string());
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_diagram_fits_a_sane_page() {
        for d in DIAGRAMS {
            let (w, h) = art_size(d);
            assert!(w <= 140, "{} is {w} cols wide", d.tab);
            assert!(h >= 10, "{} is only {h} rows", d.tab);
        }
    }

    fn press(d: &mut Diagrams, code: KeyCode) {
        d.on_key(KeyEvent::new(code, KeyModifiers::NONE));
    }

    fn screen_text(d: &mut Diagrams, w: u16, h: u16) -> String {
        use ratatui::Terminal;
        use ratatui::backend::TestBackend;
        let mut term = Terminal::new(TestBackend::new(w, h)).expect("terminal");
        term.draw(|f| d.draw(f)).expect("draw");
        let buf = term.backend().buffer();
        (0..h)
            .map(|y| (0..w).map(|x| buf[(x, y)].symbol()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }

    #[test]
    fn sand_opens_on_the_menu_then_animation_then_section() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "SAND")
            .expect("SAND node");
        press(&mut d, KeyCode::Enter);
        assert_eq!(d.view, PopupView::Menu);
        let all = screen_text(&mut d, 170, 50);
        assert!(all.contains("WATCH") && all.contains("SECTIONS"), "{all}");
        assert!(
            !all.contains("preview \u{00B7}"),
            "the plain list has no preview: {all}"
        );
        press(&mut d, KeyCode::Char('m'));
        assert!(d.browse);
        let all = screen_text(&mut d, 170, 50);
        assert!(
            all.contains("off-gas and the bag filter") && all.contains("1."),
            "{all}"
        );
        // the highlighted overview plays in the preview beside the list
        assert!(
            all.contains("preview \u{00B7} overview") && all.contains("E1"),
            "{all}"
        );
        assert!(d.animating() && d.needs_redraw());

        // the preview follows the cursor: a zoom-in, then a section's text
        press(&mut d, KeyCode::Char('j'));
        let all = screen_text(&mut d, 170, 50);
        assert!(all.contains("gas cavity"), "{all}");
        assert!(d.animating());
        for _ in 0..4 {
            press(&mut d, KeyCode::Char('j')); // past the four zooms
        }
        assert!(!d.animating(), "a section preview is static");
        screen_text(&mut d, 170, 50);

        press(&mut d, KeyCode::Char('g'));
        press(&mut d, KeyCode::Enter);
        assert_eq!(d.view, PopupView::Overview);
        let all = screen_text(&mut d, 170, 50);
        assert!(
            all.contains("WHAT'S HAPPENING") && all.contains("LOOK FOR"),
            "{all}"
        );

        // zoom in on the cavity, switch zoom, back to the menu on that row
        assert!(all.contains("zoom in") && all.contains("[a]"), "{all}");
        press(&mut d, KeyCode::Char('a'));
        assert_eq!(d.view, PopupView::Zoom);
        assert!(d.animating() && d.needs_redraw());
        let all = screen_text(&mut d, 170, 50);
        assert!(
            all.contains("gas cavity") && all.contains("WHAT'S HAPPENING"),
            "{all}"
        );
        press(&mut d, KeyCode::Char('c')); // switch straight to the tapping zoom
        assert_eq!(d.zoom.as_ref().map(|z| z.0), Some(2));
        assert!(screen_text(&mut d, 170, 50).contains("tap hole"));
        press(&mut d, KeyCode::Esc);
        assert_eq!((d.view, d.menu_sel), (PopupView::Menu, 3));

        press(&mut d, KeyCode::Char('1'));
        assert_eq!((d.view, d.pane), (PopupView::Pane, 0));
        screen_text(&mut d, 170, 50); // pane view draws
        press(&mut d, KeyCode::Esc);
        assert_eq!((d.view, d.menu_sel), (PopupView::Menu, 5));
        press(&mut d, KeyCode::Char('3'));
        assert_eq!((d.view, d.pane), (PopupView::Pane, 2));
        press(&mut d, KeyCode::Esc);
        press(&mut d, KeyCode::Esc);
        assert!(!d.popup);
    }

    #[test]
    fn melt_section_opens_its_animation() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "MELT + PULL")
            .unwrap();
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('1'));
        assert_eq!(d.view, PopupView::Zoom);
        assert!(d.zoom_section);
        let all = screen_text(&mut d, 170, 50);
        assert!(all.contains("What happens"), "{all}");
        press(&mut d, KeyCode::Esc);
        assert_eq!((d.view, d.menu_sel), (PopupView::Menu, d.menu_sections()));
    }

    #[test]
    fn p_pauses_the_animation_and_h_l_step_beats() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "SAND")
            .unwrap();
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter); // menu -> overview
        assert!(d.animating() && d.needs_redraw());
        assert!(screen_text(&mut d, 170, 50).contains("p pause"));

        press(&mut d, KeyCode::Char('p'));
        assert!(
            !d.animating() && !d.needs_redraw(),
            "paused: no redraw ticks"
        );
        let a = screen_text(&mut d, 170, 50);
        assert!(a.contains("PAUSED") && a.contains("p resume"), "{a}");
        std::thread::sleep(std::time::Duration::from_millis(120));
        assert_eq!(screen_text(&mut d, 170, 50), a, "frame is frozen");

        // stepping while paused moves to the next beat and stays paused
        press(&mut d, KeyCode::Char('l'));
        let b = screen_text(&mut d, 170, 50);
        assert!(b.contains("2/8") && b.contains("PAUSED"), "{b}");
        press(&mut d, KeyCode::Char('h'));
        assert!(screen_text(&mut d, 170, 50).contains("1/8"));

        press(&mut d, KeyCode::Char('p'));
        assert!(d.animating() && !screen_text(&mut d, 170, 50).contains("PAUSED"));

        // zooms pause on their own player
        press(&mut d, KeyCode::Char('c'));
        assert_eq!(d.view, PopupView::Zoom);
        press(&mut d, KeyCode::Char('p'));
        assert!(!d.animating());
        assert!(d.scene_player().is_some_and(|p| p.is_paused()));
        press(&mut d, KeyCode::Esc);
        press(&mut d, KeyCode::Char('g'));
        press(&mut d, KeyCode::Char('m'));
        assert!(d.animating(), "the overview was not paused");
    }

    #[test]
    fn long_notes_scroll_with_j_k_and_reset_on_a_new_beat() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .unwrap();
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('p'));
        press(&mut d, KeyCode::Char('l')); // beat 2: the fluidized bed
        let tall = screen_text(&mut d, 175, 60);
        for head in [
            "WHAT'S HAPPENING",
            "WHY IT MATTERS",
            "KEY NUMBERS",
            "LOOK FOR",
        ] {
            assert!(tall.contains(head), "{head} missing on a tall screen");
        }
        let short = screen_text(&mut d, 175, 24);
        assert!(
            !short.contains("LOOK FOR") && short.contains("j/k scrolls the notes"),
            "{short}"
        );
        for _ in 0..8 {
            press(&mut d, KeyCode::Char('j'));
        }
        let scrolled = screen_text(&mut d, 175, 24);
        assert!(
            scrolled.contains("LOOK FOR") && !scrolled.contains("WHAT'S HAPPENING"),
            "{scrolled}"
        );
        press(&mut d, KeyCode::Char('l')); // next beat starts from the top again
        assert!(screen_text(&mut d, 175, 24).contains("WHAT'S HAPPENING"));
    }

    #[test]
    fn polysilicon_overview_and_zooms_open() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .expect("POLYSILICON node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        assert_eq!(d.view, PopupView::Overview);
        let all = screen_text(&mut d, 175, 48);
        assert!(
            all.contains("fluid bed") && all.contains("[c] the Siemens bell jar"),
            "{all}"
        );
        for (key, want) in [
            ('a', "fluidized bed reactor"),
            ('b', "reboiler"),
            ('c', "bell jar"),
            ('d', "growth rate"),
        ] {
            press(&mut d, KeyCode::Char(key));
            assert_eq!(d.view, PopupView::Zoom);
            let all = screen_text(&mut d, 175, 48);
            assert!(all.contains(want), "{key}: {all}");
            assert!(all.contains("WHAT'S HAPPENING"));
        }
    }

    /// A tap renders at motion resolution like held motion does, then sharpens after SETTLE.
    #[test]
    fn taps_render_coarse_until_the_camera_settles() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        let t0 = Instant::now();
        assert!(!d.coarse(t0));
        d.full_key(KeyCode::Char('h'), t0);
        assert!(!d.moving(t0), "a tap does not start held motion");
        assert!(d.coarse(t0 + Duration::from_millis(10)), "but it renders coarse");
        assert!(!d.coarse(t0 + SETTLE + Duration::from_millis(1)), "then sharp");
    }

    #[test]
    fn held_keys_move_at_the_speed_cap() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .expect("POLYSILICON node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('c'));
        press(&mut d, KeyCode::Char('F'));

        let ms = Duration::from_millis;
        let t0 = Instant::now();
        d.last_tick = t0;
        d.full_key(KeyCode::Char('j'), t0); // a tap: one step
        let tapped = d.orbit.pitch;
        d.full_key(KeyCode::Char('j'), t0 + ms(40)); // a repeat: motion starts, no jump
        assert_eq!(d.orbit.pitch, tapped, "a repeat press does not jump");
        d.full_tick(t0 + ms(40));
        d.full_tick(t0 + ms(100));
        let moved = tapped - d.orbit.pitch;
        assert!(
            (moved - 0.8 * 0.10).abs() < 1e-9,
            "held j moves at 0.8 rad/s, moved {moved}"
        );
        // the hold ends 120 ms after the last repeat: no drift once released
        d.full_tick(t0 + ms(400));
        assert!(
            (tapped - d.orbit.pitch - moved).abs() < 1e-9,
            "no drift after release"
        );

        // a stalled frame applies at most one capped step, never a lurch
        d.full_key(KeyCode::Char('j'), t0 + ms(500));
        d.full_key(KeyCode::Char('j'), t0 + ms(540)); // repeat: motion until t0+660
        d.last_tick = t0 + ms(540);
        let before = d.orbit.pitch;
        d.full_tick(t0 + ms(650)); // 110 ms since the last tick, clamped to 100 ms
        assert!(
            (before - d.orbit.pitch - 0.8 * 0.1).abs() < 1e-9,
            "a stall is capped at 0.8 rad/s"
        );
    }

    #[test]
    fn full_view_draws_kitty_frames_and_rebuilds_on_camera_moves() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .expect("POLYSILICON node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('c'));
        press(&mut d, KeyCode::Char('F'));
        let mut picker = Picker::halfblocks();
        picker.set_protocol_type(ProtocolType::Kitty);
        d.picker = picker;
        let _ = screen_text(&mut d, 175, 48);
        assert!(matches!(
            d.full.as_ref().map(|f| &f.shown),
            Some(Shown::Graphics(_))
        ));
        let before = d.full.as_ref().map(|f| f.key);
        d.full_key(KeyCode::Char('L'), Instant::now());
        let _ = screen_text(&mut d, 175, 48);
        assert_ne!(
            d.full.as_ref().map(|f| f.key),
            before,
            "a pan redraws the frame"
        );
        assert!(matches!(
            d.full.as_ref().map(|f| &f.shown),
            Some(Shown::Graphics(_))
        ));
    }

    #[test]
    fn zoom_hjkl_turn_the_model_and_lowercase_keep_the_beats() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .expect("POLYSILICON node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('c'));
        assert_eq!(d.view, PopupView::Zoom);
        let start = d.orbit;
        press(&mut d, KeyCode::Char('L'));
        assert!(d.orbit.yaw > start.yaw, "L turns right");
        press(&mut d, KeyCode::Char('K'));
        assert!(d.orbit.pitch > start.pitch, "K tilts up");
        press(&mut d, KeyCode::Char('0'));
        assert_eq!(d.orbit, poly3d::View::default(), "0 resets the turn");

        // lowercase still steps the beat, and does not turn the model
        let beat = |d: &mut Diagrams| d.zoom.as_mut().unwrap().1.shot().beat;
        let before = beat(&mut d);
        press(&mut d, KeyCode::Char('l'));
        assert_eq!(beat(&mut d), before + 1, "l steps the beat");
        assert_eq!(d.orbit, poly3d::View::default(), "l leaves the model alone");
    }

    #[test]
    fn halfblocks_sample_top_and_bottom_pixels_per_cell() {
        // top sub-row red, the rest black: cell row 0 is red over black
        let mut img = RgbaImage::from_pixel(4, 4, image::Rgba([0, 0, 0, 255]));
        for x in 0..4 {
            img.put_pixel(x, 0, image::Rgba([255, 0, 0, 255]));
        }
        let area = Rect::new(0, 0, 4, 2);
        let mut buf = Buffer::empty(area);
        blit_halfblocks(&img, area, &mut buf);
        assert_eq!(buf[(0, 0)].fg, Color::Rgb(255, 0, 0));
        assert_eq!(buf[(0, 0)].bg, Color::Rgb(0, 0, 0));
        assert_eq!(buf[(0, 1)].fg, Color::Rgb(0, 0, 0));
    }

    #[test]
    fn cell_zooms_are_3d_and_orbit_with_hjkl() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        for key in ['a', 'b', 'c', 'd', 'e'] {
            let mut d = open(&ctx, Some("memory".into())).unwrap();
            d.sel = d.nodes[d.tab]
                .iter()
                .position(|n| n.label == "CELL")
                .expect("CELL node");
            press(&mut d, KeyCode::Enter);
            press(&mut d, KeyCode::Enter);
            press(&mut d, KeyCode::Char(key));
            let zoom = screen_text(&mut d, 175, 48);
            assert!(zoom.contains("HJKL turn"), "{key}: zoom pane is 3D: {zoom}");
            press(&mut d, KeyCode::Char('F'));
            assert_eq!(d.view, PopupView::Full, "{key}");
            let all = screen_text(&mut d, 175, 48);
            assert!(all.contains("hjkl orbit"), "{key}: {all}");
            let start = d.orbit;
            press(&mut d, KeyCode::Char('l'));
            assert!(d.orbit.yaw > start.yaw, "{key}: l orbits right");
        }
    }

    #[test]
    fn cell_sections_are_3d_and_numbers_navigate() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("memory".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "CELL")
            .expect("CELL node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        for key in '1'..='9' {
            press(&mut d, KeyCode::Char(key));
            assert_eq!(d.view, PopupView::Zoom, "{key}");
            assert!(d.zoom_section, "{key}");
            let all = screen_text(&mut d, 175, 48);
            assert!(all.contains("HJKL turn"), "{key}: {all}");
            assert!(all.contains("1-9 section"), "{key}: {all}");
            assert!(d.can_orbit(), "{key}: HJKL turn it");
        }
        // one press, since quick repeats of a key count as holding it
        let start = d.orbit;
        press(&mut d, KeyCode::Char('L'));
        assert!(d.orbit.yaw > start.yaw, "L turns the model");
        // a letter goes back to a zoom, and a number returns from it
        press(&mut d, KeyCode::Char('a'));
        assert!(!d.zoom_section);
        press(&mut d, KeyCode::Char('3'));
        assert!(d.zoom_section);
        // the sources have no scene: from the menu they open as text
        press(&mut d, KeyCode::Esc);
        let s0 = d.menu_sections();
        d.menu_sel = s0 + 9;
        press(&mut d, KeyCode::Enter);
        assert_eq!(d.view, PopupView::Pane);
    }

    #[test]
    fn bell_jar_full_view_orbits_with_hjkl() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "POLYSILICON")
            .expect("POLYSILICON node");
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Enter);
        press(&mut d, KeyCode::Char('c'));
        press(&mut d, KeyCode::Char('F'));
        assert_eq!(d.view, PopupView::Full);
        let all = screen_text(&mut d, 175, 48);
        assert!(
            all.contains("full view") && all.contains("hjkl orbit"),
            "{all}"
        );
        assert!(d.animating(), "the 3D view keeps its clock running");

        let start = d.orbit;
        press(&mut d, KeyCode::Char('l'));
        assert!(d.orbit.yaw > start.yaw, "l orbits right");
        press(&mut d, KeyCode::Char('h'));
        press(&mut d, KeyCode::Char('h'));
        assert!(d.orbit.yaw < start.yaw, "h orbits left");
        press(&mut d, KeyCode::Char('k'));
        assert!(d.orbit.pitch > start.pitch, "k tilts up");
        press(&mut d, KeyCode::Char('L'));
        assert!(d.orbit.pan[0] > 0.0, "L pans right");
        press(&mut d, KeyCode::Char('+'));
        assert!(d.orbit.zoom > 1.0, "+ zooms in");
        let _ = screen_text(&mut d, 175, 48);
        assert!(d.full.is_some(), "the frame rendered");

        press(&mut d, KeyCode::Char('0'));
        assert_eq!(d.orbit, poly3d::View::default(), "0 resets the camera");

        press(&mut d, KeyCode::Char('q'));
        assert_eq!(d.view, PopupView::Zoom, "q returns to the zoom");

        // a zoom without a 3D model ignores F
        press(&mut d, KeyCode::Char('a'));
        press(&mut d, KeyCode::Char('F'));
        assert_eq!(d.view, PopupView::Zoom);
    }

    #[test]
    fn overview_survives_tiny_and_huge_terminals() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        let mut d = open(&ctx, Some("fab".into())).unwrap();
        d.sel = d.nodes[d.tab]
            .iter()
            .position(|n| n.label == "SAND")
            .unwrap();
        press(&mut d, KeyCode::Enter);
        for (w, h) in [(40, 10), (90, 20), (130, 30), (260, 80)] {
            screen_text(&mut d, w, h); // menu with its preview
        }
        press(&mut d, KeyCode::Enter);
        for (w, h) in [(40, 10), (90, 20), (130, 30), (260, 80)] {
            screen_text(&mut d, w, h);
        }
    }

    #[test]
    fn open_matches_tab_prefix() {
        let ctx = Ctx {
            db_path: Default::default(),
            theme: Theme::default(),
        };
        assert_eq!(open(&ctx, Some("fib".into())).unwrap().tab, 4);
        assert_eq!(open(&ctx, Some("mem".into())).unwrap().tab, 2);
        assert_eq!(open(&ctx, Some("zzz".into())).unwrap().tab, 0);
    }

    #[test]
    fn fab_nodes_all_described() {
        all_described(0, 20);
    }

    #[test]
    fn chip_nodes_all_described() {
        all_described(1, 10);
    }

    #[test]
    fn packaging_nodes_all_described() {
        all_described(3, 6);
    }

    #[test]
    fn fiber_nodes_all_described() {
        all_described(4, 6);
    }

    #[test]
    fn power_nodes_all_described() {
        all_described(5, 6);
    }

    #[test]
    fn memory_hbm_stack_node_is_complete() {
        let hots = find_hots("HBM STACK");
        assert!(hots.len() >= 8, "HBM STACK: only {} hotspots", hots.len());
        assert_eq!(hots.len(), cards("HBM STACK").len(), "HBM STACK: card label missing from page");
        assert!(hots.iter().all(|h| h.body.len() > 150), "HBM STACK: short card");
        assert!(scene_for("HBM STACK").is_some(), "HBM STACK: no animation");
    }

    #[test]
    fn memory_bandwidth_node_is_complete() {
        let hots = find_hots("BANDWIDTH");
        assert!(hots.len() >= 8, "BANDWIDTH: only {} hotspots", hots.len());
        assert_eq!(hots.len(), cards("BANDWIDTH").len(), "BANDWIDTH: card label missing from page");
        assert!(hots.iter().all(|h| h.body.len() > 150), "BANDWIDTH: short card");
        assert!(scene_for("BANDWIDTH").is_some(), "BANDWIDTH: no animation");
    }

    #[test]
    fn memory_bank_node_is_complete() {
        let hots = find_hots("BANK");
        assert!(hots.len() >= 8, "BANK: only {} hotspots", hots.len());
        assert_eq!(hots.len(), cards("BANK").len(), "BANK: card label missing from page");
        assert!(hots.iter().all(|h| h.body.len() > 150), "BANK: short card");
        assert!(scene_for("BANK").is_some(), "BANK: no animation");
    }

    #[test]
    fn memory_array_node_is_complete() {
        let hots = find_hots("ARRAY");
        assert!(hots.len() >= 8, "ARRAY: only {} hotspots", hots.len());
        assert_eq!(
            hots.len(),
            cards("ARRAY").len(),
            "ARRAY: card label missing from page"
        );
        assert!(hots.iter().all(|h| h.body.len() > 150), "ARRAY: short card");
        assert!(scene_for("ARRAY").is_some(), "ARRAY: no animation");
    }

    #[test]
    fn memory_litho_node_is_complete() {
        let hots = find_hots("LITHO");
        assert!(hots.len() >= 8, "LITHO: only {} hotspots", hots.len());
        assert_eq!(
            hots.len(),
            cards("LITHO").len(),
            "LITHO: card label missing from page"
        );
        assert!(hots.iter().all(|h| h.body.len() > 150), "LITHO: short card");
        assert!(scene_for("LITHO").is_some(), "LITHO: no animation");
    }

    #[test]
    fn memory_cell_node_is_complete() {
        let hots = find_hots("CELL");
        assert!(hots.len() >= 8, "CELL: only {} hotspots", hots.len());
        assert_eq!(
            hots.len(),
            cards("CELL").len(),
            "CELL: card label missing from page"
        );
        assert!(hots.iter().all(|h| h.body.len() > 150), "CELL: short card");
        assert!(scene_for("CELL").is_some(), "CELL: no animation");
    }

    fn all_described(tab: usize, want: usize) {
        let nodes = find_nodes(DIAGRAMS[tab].art);
        let labels: Vec<_> = nodes.iter().map(|n| n.label.as_str()).collect();
        assert_eq!(nodes.len(), want, "{labels:?}");
        for n in &nodes {
            assert!(describe(&n.label).is_some(), "no desc: {}", n.label);
            assert!(visual(&n.label).is_some(), "no page: {}", n.label);
            let hots = find_hots(&n.label);
            assert!(hots.len() >= 8, "{}: only {} hotspots", n.label, hots.len());
            assert_eq!(
                hots.len(),
                cards(&n.label).len(),
                "{}: card label missing from page",
                n.label
            );
            assert!(
                hots.iter().all(|h| h.body.len() > 150),
                "{}: short card",
                n.label
            );
        }
    }
}

#[cfg(test)]
#[path = "diagrams_bench.rs"]
mod bench;

#[cfg(test)]
mod section_tests {
    use super::sections;

    #[test]
    fn splits_on_headings() {
        let s = sections("intro\n\n# A\nbody a\n\n# B\nbody b\n");
        assert_eq!(
            s,
            vec![("overview", "intro"), ("A", "body a"), ("B", "body b")]
        );
        assert_eq!(sections("plain"), vec![("overview", "plain")]);
        assert_eq!(sections("# A\nx"), vec![("A", "x")]);
    }
}
