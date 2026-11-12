// The diagram's side of Claude's tools, and the demo that runs through set questions.
//
// A tool call arrives from diagrams_ipc as a `Request`. Calls that change the picture
// parse into `Step`s, which are checked against where the walk-through will be by
// then (`Sim`) before anything runs: a zoom that does not exist, a beat past the end,
// a note pinned to a part the view does not label are all refused with the valid
// choices, so Claude can correct the call instead of drawing something wrong. A
// `sequence` is checked whole, then played from a queue (its waits are real time) and
// answered when the last step has run. `ask` and `ask_part` are answered by the key
// the user presses.
//
// This is a child module of `diagrams` (see the `#[path]` there), so it works on the
// screen's own fields.

use std::collections::HashMap;
use std::io::Write as _;
use std::path::PathBuf;
use std::sync::mpsc::Sender;
use std::time::{Duration, Instant};

use ratatui::crossterm::event::{KeyCode, KeyEvent};
use serde_json::{Value, json};

use super::super::diagrams_chat::{MAX_NOTES, Quiz, Step, Target, parse_step};
use super::super::diagrams_ipc::{self as ipc, Request, STEP_TOOLS};
use super::*;

/// A result owed to a tool call that could not be answered at once.
pub(super) enum Pending {
    /// A `sequence`: answered when the queue has played out.
    Sequence(Sender<Value>, usize),
    /// A `wait`: answered at the instant.
    Wait(Sender<Value>, Instant),
    /// `ask` / `ask_part`: answered by the user's key.
    Quiz(Sender<Value>),
}

/// What the tools keep between calls.
#[derive(Default)]
pub(super) struct Tools {
    pub server: Option<ipc::Server>,
    pub pending: Option<Pending>,
    /// Part names by (page, view): one list per beat. Rendered once, on first use.
    parts: HashMap<(String, String), Vec<Vec<String>>>,
    /// The picture's own part names are hidden (a recall exercise).
    pub names_hidden: bool,
    /// Tool calls and refused calls since the last question was asked.
    pub calls: usize,
    pub refused: usize,
    /// The refusals themselves, for the demo's log.
    pub errors: Vec<String>,
}

/// Where a walk-through is, step by step, while it is being checked.
struct Sim {
    label: String,
    page: String,
    /// "menu", "overview", a zoom's letter, a section's number, or "text" (a section
    /// without a picture).
    view: String,
    beat: usize,
    notes: Vec<String>,
}

/// The demo: a question, its answer, a rating, the next question.
pub(super) struct Demo {
    items: Vec<(String, String)>,
    i: usize,
    phase: Phase,
    typed: String,
    started: Instant,
    out: PathBuf,
    scores: Vec<(usize, u32)>,
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub(super) enum Phase {
    Answering,
    Rating,
    Done,
}

const DEMO: &str = include_str!("diagrams_demo.txt");

/// The demo's questions: (node, question).
pub(super) fn demo_items() -> Vec<(String, String)> {
    DEMO.lines()
        .filter(|l| !l.trim().is_empty() && !l.starts_with('#'))
        .filter_map(|l| l.split_once('|'))
        .map(|(n, q)| (n.trim().to_string(), q.trim().to_string()))
        .collect()
}

/// The 3D model of a page's overview at `time`, if its overview is one.
fn overview_model(page: &str, time: crate::ui::anim::Time) -> Option<Model> {
    Some(match page {
        "CELL" => Model::CellOverview(time),
        "LITHO" => Model::LithoOverview(time),
        "ARRAY" => Model::ArrayOverview(time),
        "BANK" => Model::BankOverview(time),
        "BANDWIDTH" => Model::BwOverview(time),
        "HBM STACK" => Model::HbmOverview(time),
        p => {
            if let Some(n) = super::super::diagrams_scene_chip::node(p) {
                Model::ChipOverview(n.beats, n.keys, time)
            } else if let Some(n) = super::super::diagrams_scene_pkg::node(p) {
                Model::PkgOverview(n.beats, n.keys, time)
            } else if let Some(n) = super::super::diagrams_scene_link::node(p) {
                Model::LinkOverview(n.beats, n.keys, time)
            } else if let Some(n) = super::super::diagrams_scene_pwr::node(p) {
                Model::PwrOverview(n.beats, n.keys, time)
            } else {
                return None;
            }
        }
    })
}

/// The scene a view of `page` plays, and the key its 3D model goes by (None: flat).
fn view_scene(page: &str, view: &str) -> Option<(Box<dyn Scene>, Option<char>)> {
    if view == "overview" {
        return scene_for(page).map(|s| (s, None));
    }
    let key = view.chars().next()?;
    if let Some(n) = view.parse::<usize>().ok().filter(|n| *n >= 1) {
        let build = section_anim(page, n - 1)?;
        let key = char::from_digit(n as u32, 10).filter(|k| orbitable(page, *k));
        return Some((build(), key));
    }
    let base = scene_for(page)?;
    let z = base.zooms().iter().find(|z| z.key == key)?;
    Some(((z.build)(), orbitable(page, key).then_some(key)))
}

fn ok(mut v: Value) -> Value {
    v["ok"] = json!(true);
    v
}

impl Diagrams {
    /// The page key of a node label (what scenes and write-ups are filed under).
    fn page_of(label: &str) -> String {
        page_key(label).unwrap_or(label.trim()).to_string()
    }

    /// (tab, index) of the node called `name`: its label or page key, else a label
    /// holding it.
    pub(super) fn find_node(&self, name: &str) -> Option<(usize, usize)> {
        let want = name.trim();
        let find = |exact: bool| {
            self.nodes.iter().enumerate().find_map(|(tab, nodes)| {
                nodes
                    .iter()
                    .position(|n| {
                        let l = n.label.trim();
                        if exact {
                            l.eq_ignore_ascii_case(want)
                                || page_key(l).is_some_and(|k| k.eq_ignore_ascii_case(want))
                        } else {
                            l.to_ascii_lowercase().contains(&want.to_ascii_lowercase())
                        }
                    })
                    .map(|sel| (tab, sel))
            })
        };
        find(true).or_else(|| find(false))
    }

    fn node_names(&self) -> String {
        let all: Vec<&str> = self
            .nodes
            .iter()
            .flatten()
            .map(|n| n.label.trim())
            .collect();
        all.join(", ")
    }

    /// The view that is open, as tools name views.
    fn view_key(&self) -> String {
        match self.view {
            PopupView::Menu => "menu".to_string(),
            PopupView::Overview => "overview".to_string(),
            PopupView::Zoom | PopupView::Full => self
                .open_key()
                .map_or("overview".to_string(), |k| k.to_string()),
            PopupView::Pane => "text".to_string(),
        }
    }

    /// The part names `view` of `page` labels, one list per beat. Empty for a view
    /// without a 3D picture. Rendered small, once.
    fn part_names(&mut self, page: &str, view: &str) -> Vec<Vec<String>> {
        let key = (page.to_string(), view.to_string());
        if let Some(hit) = self.tools.parts.get(&key) {
            return hit.clone();
        }
        let mut out: Vec<Vec<String>> = Vec::new();
        if let Some((scene, model_key)) = view_scene(page, view) {
            let mut p = Player::new(scene, Instant::now());
            p.toggle_pause();
            let beats = p.shot().beats;
            for b in 0..beats {
                let cur = p.shot().beat;
                p.step_beat(b as i32 - cur as i32);
                let time = p.time_at(p.now_ms());
                let model = match (view, model_key) {
                    ("overview", _) => overview_model(page, time),
                    (_, Some(k)) => Some(model_at(page, k, &time)),
                    _ => None,
                };
                let Some(model) = model else {
                    break;
                };
                render_model(model, &poly3d::View::default(), 480, 300);
                out.push(poly3d::seen_names());
            }
        }
        self.tools.parts.insert(key, out.clone());
        out
    }

    /// Every name `view` labels on any beat.
    fn all_parts(&mut self, page: &str, view: &str) -> Vec<String> {
        let mut all: Vec<String> = Vec::new();
        for n in self.part_names(page, view).into_iter().flatten() {
            if !all.contains(&n) {
                all.push(n);
            }
        }
        all
    }

    fn sim(&self) -> Sim {
        let label = self.cur_label().unwrap_or_default();
        Sim {
            page: Self::page_of(&label),
            label,
            view: self.view_key(),
            beat: self
                .scene_player()
                .map_or(0, |p| p.time_at(p.now_ms()).beat),
            notes: self.chat.notes().iter().map(|n| n.id.clone()).collect(),
        }
    }

    /// Whether `step` can run where the walk-through is, moving `sim` on if so.
    fn check(&mut self, step: &Step, sim: &mut Sim) -> Result<(), String> {
        let pictured = !matches!(sim.view.as_str(), "menu" | "text");
        match step {
            Step::Open(name) => {
                let Some((tab, sel)) = self.find_node(name) else {
                    return Err(format!("no node {name:?}. Nodes: {}", self.node_names()));
                };
                sim.label = self.nodes[tab][sel].label.clone();
                sim.page = Self::page_of(&sim.label);
                sim.view = if scene_for(&sim.page).is_some() {
                    "overview".to_string()
                } else {
                    "text".to_string()
                };
                sim.beat = 0;
                sim.notes.clear();
            }
            Step::Goto(Target::Zoom(k)) => {
                let zooms: Vec<(char, &'static str)> = scene_for(&sim.page)
                    .map(|s| s.zooms().iter().map(|z| (z.key, z.label)).collect())
                    .unwrap_or_default();
                if !zooms.iter().any(|(z, _)| z == k) {
                    let list: Vec<String> =
                        zooms.iter().map(|(z, l)| format!("{z} = {l}")).collect();
                    return Err(if list.is_empty() {
                        format!("{} has no zoom-ins", sim.label.trim())
                    } else {
                        format!(
                            "{} has no zoom-in {k:?}. Zoom-ins: {}",
                            sim.label.trim(),
                            list.join("; ")
                        )
                    });
                }
                sim.view = k.to_string();
                sim.beat = 0;
            }
            Step::Goto(Target::Section(n)) => {
                let count = visual(&sim.label).map_or(0, |art| pane_ranges(art).len());
                if *n > count {
                    return Err(format!(
                        "{} has {count} sections, no section {n}",
                        sim.label.trim()
                    ));
                }
                sim.view = if section_anim(&sim.page, n - 1).is_some() {
                    n.to_string()
                } else {
                    "text".to_string()
                };
                sim.beat = 0;
            }
            Step::Goto(t @ (Target::Overview | Target::Menu)) => {
                if scene_for(&sim.page).is_none() {
                    return Err(format!(
                        "{} is text only: it has sections (goto section) but no overview",
                        sim.label.trim()
                    ));
                }
                sim.view = if *t == Target::Overview {
                    "overview"
                } else {
                    "menu"
                }
                .to_string();
                sim.beat = 0;
            }
            Step::Beat(n) => {
                let beats = view_scene(&sim.page, &sim.view).map_or(0, |(s, _)| s.beats().len());
                if beats == 0 {
                    return Err(format!(
                        "the {} view has no animation: goto the overview or a zoom-in first",
                        sim.view
                    ));
                }
                if *n > beats {
                    return Err(format!("this view has {beats} beats, no beat {n}"));
                }
                sim.beat = n - 1;
            }
            Step::Play | Step::Pause => {
                if view_scene(&sim.page, &sim.view).is_none() {
                    return Err(format!(
                        "the {} view has no animation: goto the overview or a zoom-in first",
                        sim.view
                    ));
                }
            }
            Step::Camera { .. } => {
                if self.part_names(&sim.page, &sim.view).is_empty() {
                    return Err(format!(
                        "the {} view of {} is not a 3D model: nothing to turn",
                        sim.view,
                        sim.label.trim()
                    ));
                }
            }
            Step::Note(note) => {
                if !pictured {
                    return Err(format!(
                        "notes do not show in the {} view: goto the overview or a zoom-in first",
                        sim.view
                    ));
                }
                if let Some(on) = &note.on {
                    self.check_part(on, sim)?;
                }
                if !sim.notes.contains(&note.id) {
                    if sim.notes.len() >= MAX_NOTES {
                        return Err(format!(
                            "{MAX_NOTES} notes are already up ({}): remove one first",
                            sim.notes.join(", ")
                        ));
                    }
                    sim.notes.push(note.id.clone());
                }
            }
            Step::Unnote(id) => {
                if !sim.notes.contains(id) {
                    return Err(format!(
                        "no note {id:?} is up. Notes up: {}",
                        if sim.notes.is_empty() {
                            "none".to_string()
                        } else {
                            sim.notes.join(", ")
                        }
                    ));
                }
                sim.notes.retain(|n| n != id);
            }
            Step::Clear => sim.notes.clear(),
            Step::Point(parts) => {
                if !pictured && !parts.is_empty() {
                    return Err(format!(
                        "there is no picture in the {} view to point at",
                        sim.view
                    ));
                }
                for p in parts {
                    self.check_part(p, sim)?;
                }
            }
            Step::Caption(_) | Step::Labels(_) | Step::Wait(_) => {}
        }
        Ok(())
    }

    /// Whether the view the walk-through is in labels a part `want` would match.
    fn check_part(&mut self, want: &str, sim: &Sim) -> Result<(), String> {
        let by_beat = self.part_names(&sim.page, &sim.view);
        let all = self.all_parts(&sim.page, &sim.view);
        if all.is_empty() {
            return Err(format!(
                "the {} view of {} has no named parts to pin to: leave \"on\" out, or use a view that has them (see `parts`)",
                sim.view,
                sim.label.trim()
            ));
        }
        if poly3d::match_name(&all, want).is_some() {
            return Ok(());
        }
        let here = by_beat.get(sim.beat).cloned().unwrap_or_default();
        Err(format!(
            "no part {want:?} in the {} view of {}. Parts on beat {}: {}. Parts on any beat: {}",
            sim.view,
            sim.label.trim(),
            sim.beat + 1,
            here.join(", "),
            all.join(", ")
        ))
    }

    /// Does `step` to the screen. It has been checked.
    pub(super) fn exec(&mut self, step: Step) {
        self.redraw = true;
        match step {
            Step::Open(name) => {
                if let Some((tab, sel)) = self.find_node(&name) {
                    self.tab = tab;
                    self.sel = sel;
                    self.scroll = 0;
                    self.popup = true;
                    self.open_popup();
                    if self.has_scene() {
                        self.view = PopupView::Overview;
                    }
                }
            }
            Step::Goto(target) => {
                self.detail = false;
                match target {
                    Target::Zoom(k) => {
                        if let Some(i) = self.zoom_for_key(k) {
                            self.open_zoom(i);
                        }
                    }
                    Target::Section(n) => self.open_section_or_pane(n - 1),
                    Target::Overview if self.has_scene() => {
                        self.zoom = None;
                        self.view = PopupView::Overview;
                    }
                    Target::Menu if self.has_scene() => {
                        self.zoom = None;
                        self.menu_sel = 0;
                        self.view = PopupView::Menu;
                    }
                    Target::Overview | Target::Menu => {}
                }
            }
            Step::Beat(n) => {
                if let Some(p) = self.scene_player_mut() {
                    let shot = p.shot();
                    let to = (n - 1).min(shot.beats.saturating_sub(1));
                    p.step_beat(to as i32 - shot.beat as i32);
                    if !p.is_paused() {
                        p.toggle_pause();
                    }
                }
            }
            Step::Play | Step::Pause => {
                let hold = step == Step::Pause;
                if let Some(p) = self.scene_player_mut()
                    && p.is_paused() != hold
                {
                    p.toggle_pause();
                }
            }
            Step::Camera {
                yaw,
                pitch,
                zoom,
                reset,
            } => {
                if reset {
                    self.orbit = poly3d::View::default();
                }
                self.orbit.orbit(yaw.to_radians(), pitch.to_radians());
                if (zoom - 1.0).abs() > 1e-6 {
                    self.orbit.zoom_by(zoom);
                }
            }
            Step::Note(note) => {
                self.chat.set_note(note);
                self.sync_notes();
            }
            Step::Unnote(id) => {
                self.chat.remove_note(&id);
                self.sync_notes();
            }
            Step::Clear => {
                self.chat.clear_notes();
                self.sync_notes();
            }
            Step::Point(parts) => {
                self.chat.set_marks(parts);
                self.sync_notes();
            }
            Step::Caption(text) => self.chat.set_caption(text),
            Step::Labels(show) => {
                self.tools.names_hidden = !show;
                self.sync_notes();
            }
            // the queue holds on a wait; one run directly has nothing behind it
            Step::Wait(_) => {}
        }
    }

    /// What the user is looking at, for a tool's result.
    fn state(&mut self) -> Value {
        let label = self.cur_label().unwrap_or_default();
        let page = Self::page_of(&label);
        let view = self.view_key();
        let zooms: Vec<Value> = self
            .zoom_list()
            .iter()
            .map(|(k, l)| json!({ "zoom": k.to_string(), "shows": l }))
            .collect();
        let mut s = json!({
            "tab": DIAGRAMS[self.tab].tab,
            "node": label.trim(),
            "view": view,
            "zoom_ins": zooms,
            "sections": self.pane_titles(),
            "notes_up": self.chat.notes().iter().map(|n| json!({
                "id": n.id, "on": n.on, "text": n.text,
            })).collect::<Vec<_>>(),
            "ringed": self.chat.marks(),
            "part_names_shown": !self.tools.names_hidden,
            "notes_visible_here": !matches!(view.as_str(), "menu" | "text"),
        });
        let in_scene = matches!(
            self.view,
            PopupView::Overview | PopupView::Zoom | PopupView::Full
        );
        if in_scene && let Some(p) = self.scene_player_mut() {
            let held = p.is_paused();
            let shot = p.shot();
            s["beat"] = json!({
                "n": shot.beat + 1,
                "of": shot.beats,
                "held": held,
                "caption": shot.caption,
                "whats_happening": shot.what,
                "why_it_matters": shot.why,
                "look_for": shot.look,
                "key_numbers": shot.facts,
            });
            let beat = shot.beat;
            let names = self.part_names(&page, &view);
            s["parts_on_picture"] = json!(names.get(beat).cloned().unwrap_or_default());
        }
        s
    }

    fn refuse(&mut self, reply: &Sender<Value>, msg: String) {
        self.tools.refused += 1;
        self.tools.errors.push(msg.clone());
        let _ = reply.send(ipc::fail(&msg));
    }

    /// Runs one tool call, or queues it and leaves its result pending.
    pub(super) fn call(&mut self, req: Request) {
        self.tools.calls += 1;
        self.redraw = true;
        let Request { tool, args, reply } = req;
        if !self.popup {
            return self.refuse(&reply, "the user has closed the node".into());
        }
        if self.tools.pending.is_some() {
            return self.refuse(
                &reply,
                "the last call is still running: wait for its result".into(),
            );
        }
        match tool.as_str() {
            "state" => {
                let _ = reply.send(ok(self.state()));
            }
            "parts" => {
                let label = self.cur_label().unwrap_or_default();
                let page = Self::page_of(&label);
                let views: Vec<String> = match args["view"].as_str().map(str::trim) {
                    Some(v) if !v.is_empty() => vec![v.to_ascii_lowercase()],
                    _ => std::iter::once("overview".to_string())
                        .chain(self.zoom_list().iter().map(|(k, _)| k.to_string()))
                        .collect(),
                };
                let mut out = serde_json::Map::new();
                for v in views {
                    let names = self.part_names(&page, &v);
                    out.insert(v, json!(names));
                }
                let _ = reply.send(ok(json!({
                    "node": label.trim(),
                    "parts_by_view_then_beat": out,
                    "note": "an empty list means that view has no named parts: use free notes there",
                })));
            }
            "list_nodes" => {
                let tabs: Vec<Value> = self
                    .nodes
                    .iter()
                    .enumerate()
                    .map(|(tab, nodes)| {
                        json!({
                            "tab": DIAGRAMS[tab].tab,
                            "about": DIAGRAMS[tab].title,
                            "nodes": nodes.iter().map(|n| json!({
                                "node": n.label.trim(),
                                "about": describe(&n.label).and_then(|d| d.split(". ").next()).unwrap_or(""),
                            })).collect::<Vec<_>>(),
                        })
                    })
                    .collect();
                let _ = reply.send(ok(json!({ "tabs": tabs })));
            }
            "read_section" => {
                let art = self.cur_label().and_then(|l| visual(&l)).unwrap_or("");
                let panes = pane_ranges(art);
                match args["n"]
                    .as_u64()
                    .filter(|n| *n >= 1 && *n as usize <= panes.len())
                {
                    Some(n) => {
                        let (a, b, _) = panes[n as usize - 1];
                        let text: Vec<&str> = art.lines().skip(a).take(b - a).collect();
                        let _ = reply.send(ok(json!({ "section": n, "text": text.join("\n") })));
                    }
                    None => self.refuse(&reply, format!("read_section: n is 1 to {}", panes.len())),
                }
            }
            "sequence" => {
                let Some(list) = args["steps"].as_array().filter(|l| !l.is_empty()) else {
                    return self.refuse(&reply, "sequence: steps is a non-empty list".into());
                };
                let mut steps = Vec::new();
                let mut sim = self.sim();
                for (i, raw) in list.iter().enumerate() {
                    let name = raw["do"].as_str().unwrap_or("");
                    let at = format!("step {} ({name})", i + 1);
                    if !STEP_TOOLS.contains(&name) {
                        return self.refuse(
                            &reply,
                            format!("{at}: \"do\" must be one of {}", STEP_TOOLS.join(", ")),
                        );
                    }
                    let step = match parse_step(name, raw) {
                        Ok(s) => s,
                        Err(e) => {
                            return self.refuse(&reply, format!("{at}: {e}. Nothing was run."));
                        }
                    };
                    if let Err(e) = self.check(&step, &mut sim) {
                        return self.refuse(&reply, format!("{at}: {e}. Nothing was run."));
                    }
                    steps.push(step);
                }
                let n = steps.len();
                self.queue.extend(steps);
                self.tools.pending = Some(Pending::Sequence(reply, n));
            }
            "wait" => match parse_step("wait", &args) {
                Ok(Step::Wait(ms)) => {
                    self.tools.pending = Some(Pending::Wait(
                        reply,
                        Instant::now() + Duration::from_millis(ms),
                    ));
                }
                Ok(_) => {}
                Err(e) => self.refuse(&reply, e),
            },
            "ask" => {
                let question = args["question"].as_str().unwrap_or("").trim().to_string();
                let choices: Vec<String> = args["choices"]
                    .as_array()
                    .map(|l| {
                        l.iter()
                            .filter_map(|c| c.as_str())
                            .map(|c| c.trim().to_string())
                            .filter(|c| !c.is_empty())
                            .collect()
                    })
                    .unwrap_or_default();
                if question.is_empty() || !(2..=4).contains(&choices.len()) {
                    return self.refuse(&reply, "ask: a question and 2 to 4 choices".into());
                }
                self.chat.quiz = Some(Quiz::Choice { question, choices });
                self.tools.pending = Some(Pending::Quiz(reply));
            }
            "ask_part" => {
                let question = args["question"].as_str().unwrap_or("").trim().to_string();
                let label = self.cur_label().unwrap_or_default();
                let (page, view) = (Self::page_of(&label), self.view_key());
                let beat = self
                    .scene_player()
                    .map_or(0, |p| p.time_at(p.now_ms()).beat);
                let names = self
                    .part_names(&page, &view)
                    .get(beat)
                    .cloned()
                    .unwrap_or_default();
                if question.is_empty() {
                    return self.refuse(&reply, "ask_part: a question is required".into());
                }
                if names.len() < 2 {
                    return self.refuse(
                        &reply,
                        format!(
                            "ask_part: the {view} view has no named parts on this beat to pick from: goto a view that has them (see `parts`)"
                        ),
                    );
                }
                // the picture holds still while the user picks
                self.exec(Step::Pause);
                self.chat.quiz = Some(Quiz::Part {
                    question,
                    names,
                    cur: 0,
                });
                self.sync_notes();
                self.tools.pending = Some(Pending::Quiz(reply));
            }
            name if STEP_TOOLS.contains(&name) => {
                let step = match parse_step(name, &args) {
                    Ok(s) => s,
                    Err(e) => return self.refuse(&reply, e),
                };
                let mut sim = self.sim();
                if let Err(e) = self.check(&step, &mut sim) {
                    return self.refuse(&reply, e);
                }
                self.exec(step);
                let _ = reply.send(ok(self.state()));
            }
            other => self.refuse(
                &reply,
                format!("no tool {other:?}; tools: {}", ipc::tool_names().join(", ")),
            ),
        }
    }

    /// Per tick: take in tool calls, play the queue, answer what has come due.
    pub(super) fn tools_tick(&mut self, now: Instant) {
        let mut reqs = Vec::new();
        if let Some(server) = &self.tools.server {
            while let Ok(r) = server.rx.try_recv() {
                reqs.push(r);
            }
        }
        for r in reqs {
            self.call(r);
        }
        if self.wait_until.is_some_and(|until| now >= until) {
            self.wait_until = None;
        }
        // steps run in order; a wait holds the ones behind it
        while self.wait_until.is_none() {
            match self.queue.pop_front() {
                Some(Step::Wait(ms)) => self.wait_until = Some(now + Duration::from_millis(ms)),
                Some(step) => self.exec(step),
                None => break,
            }
        }
        let due = match &self.tools.pending {
            Some(Pending::Sequence(..)) => self.queue.is_empty() && self.wait_until.is_none(),
            Some(Pending::Wait(_, at)) => now >= *at,
            _ => false,
        };
        if due {
            match self.tools.pending.take() {
                Some(Pending::Sequence(reply, n)) => {
                    let mut out = ok(self.state());
                    out["ran_steps"] = json!(n);
                    let _ = reply.send(out);
                }
                Some(Pending::Wait(reply, _)) => {
                    let _ = reply.send(ok(json!({})));
                }
                _ => {}
            }
        }
        self.demo_tick();
    }

    /// Drops everything an answer still has in flight: Claude, the queue, an open quiz.
    pub(super) fn stop_answer(&mut self) {
        self.chat.cancel();
        self.queue.clear();
        self.wait_until = None;
        if let Some(p) = self.tools.pending.take() {
            let (Pending::Sequence(reply, _) | Pending::Wait(reply, _) | Pending::Quiz(reply)) = p;
            let _ = reply.send(ipc::fail("stopped by the user"));
        }
        if self.chat.quiz.take().is_some() {
            self.sync_notes();
        }
    }

    /// Whether an answer is still arriving or playing.
    pub(super) fn answering(&self) -> bool {
        self.chat.busy()
            || !self.queue.is_empty()
            || self.wait_until.is_some()
            || self.tools.pending.is_some()
    }

    /// A key while a quiz is open. True if the quiz took it.
    pub(super) fn quiz_key(&mut self, key: KeyEvent) -> bool {
        let Some(quiz) = self.chat.quiz.clone() else {
            return false;
        };
        let answer = match (&quiz, key.code) {
            (_, KeyCode::Esc) => Some(json!({ "skipped": true })),
            (Quiz::Choice { choices, .. }, KeyCode::Char(c)) => {
                let i = (c.to_ascii_lowercase() as usize).wrapping_sub('a' as usize);
                match choices.get(i) {
                    Some(text) => Some(json!({
                        "picked": ((b'a' + i as u8) as char).to_string(),
                        "choice": text,
                    })),
                    // other keys still work the diagram while the question is up
                    None => return false,
                }
            }
            (Quiz::Part { names, cur, .. }, code) => {
                let n = names.len();
                let step = match code {
                    KeyCode::Char('l' | 'j') | KeyCode::Right | KeyCode::Down | KeyCode::Tab => 1,
                    KeyCode::Char('h' | 'k') | KeyCode::Left | KeyCode::Up | KeyCode::BackTab => {
                        n - 1
                    }
                    KeyCode::Enter | KeyCode::Char(' ') => {
                        0 // picked below
                    }
                    _ => return false,
                };
                if step == 0 {
                    Some(json!({ "picked": names[*cur] }))
                } else {
                    if let Some(Quiz::Part { cur, .. }) = &mut self.chat.quiz {
                        *cur = (*cur + step) % n;
                    }
                    self.sync_notes();
                    return true;
                }
            }
            _ => return false,
        };
        if let Some(a) = answer {
            self.chat.quiz = None;
            self.sync_notes();
            if let Some(Pending::Quiz(reply)) = self.tools.pending.take() {
                let _ = reply.send(ok(a));
            }
        }
        true
    }

    /// Sends `question` to Claude with the screen's context, opening the tools' socket
    /// on first use.
    pub(super) fn ask(&mut self, question: &str) {
        self.stop_answer();
        self.tools.calls = 0;
        self.tools.refused = 0;
        self.tools.errors.clear();
        // tests drive the tools directly: no socket, no Claude
        if cfg!(test) {
            return;
        }
        if self.tools.server.is_none() {
            match ipc::Server::start() {
                Ok(s) => self.tools.server = Some(s),
                Err(e) => {
                    self.chat.fail(format!("can't open the tool socket: {e}"));
                    return;
                }
            }
        }
        let context = self.chat_context();
        if let Some(server) = &self.tools.server {
            let path = server.path.clone();
            self.chat.send(question, &context, &path);
        }
    }

    // ---- the demo -------------------------------------------------------------

    /// Starts the demo at question `from` (1-based).
    pub(super) fn start_demo(&mut self, from: usize) {
        let items = demo_items();
        if items.is_empty() {
            return;
        }
        let out = if cfg!(test) {
            std::env::temp_dir().join(format!("fl-demo-test-{}.jsonl", std::process::id()))
        } else {
            crate::data_dir().join("diagram_demo").join("ratings.jsonl")
        };
        self.demo = Some(Demo {
            i: from.clamp(1, items.len()) - 1,
            items,
            phase: Phase::Answering,
            typed: String::new(),
            started: Instant::now(),
            out,
            scores: Vec::new(),
        });
        self.demo_begin();
    }

    /// Opens the current question's node and asks it.
    fn demo_begin(&mut self) {
        let Some(d) = &mut self.demo else {
            return;
        };
        let (node, question) = d.items[d.i].clone();
        d.phase = Phase::Answering;
        d.typed.clear();
        d.started = Instant::now();
        let banner = format!(
            "demo {}/{} \u{00B7} {node} \u{00B7} {question}",
            d.i + 1,
            d.items.len()
        );
        self.stop_answer();
        self.chat.prompt = None;
        self.exec(Step::Clear);
        self.exec(Step::Labels(true));
        self.orbit = poly3d::View::default();
        self.exec(Step::Open(node));
        self.chat.banner = banner;
        self.ask(&question);
    }

    fn demo_tick(&mut self) {
        let answering = self.answering();
        let Some(d) = &mut self.demo else {
            return;
        };
        if d.phase == Phase::Answering
            && !answering
            && d.started.elapsed() > Duration::from_millis(1500)
        {
            d.phase = Phase::Rating;
            // an answer that failed (no Claude, a usage limit) is asked again, not rated
            let ask = if self.chat.failed() {
                "no answer: r asks again, s skips"
            } else {
                "rate this answer 1-100:"
            };
            self.chat.prompt = Some((ask.to_string(), String::new()));
            self.redraw = true;
        }
    }

    /// Writes one rating, with what the answer did, as a JSON line.
    fn demo_record(&mut self, rating: Option<u32>) {
        let Some(d) = &mut self.demo else {
            return;
        };
        let (node, question) = &d.items[d.i];
        let line = json!({
            "at": chrono::Local::now().to_rfc3339(),
            "n": d.i + 1,
            "node": node,
            "question": question,
            "rating": rating,
            "seconds": d.started.elapsed().as_secs(),
            "tool_calls": self.tools.calls,
            "refused_calls": self.tools.refused,
            "refusals": self.tools.errors,
            "caption": self.chat.caption(),
            "notes_left_up": self.chat.notes().iter().map(|n| json!({
                "on": n.on, "title": n.title, "text": n.text,
            })).collect::<Vec<_>>(),
        });
        if let Some(r) = rating {
            d.scores.push((d.i, r));
        }
        if let Some(dir) = d.out.parent() {
            let _ = std::fs::create_dir_all(dir);
        }
        if let Ok(mut f) = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&d.out)
        {
            let _ = writeln!(f, "{line}");
        }
    }

    /// Moves to the next question, or ends the demo with its summary.
    fn demo_next(&mut self) {
        let Some(d) = &mut self.demo else {
            return;
        };
        if d.i + 1 < d.items.len() {
            d.i += 1;
            return self.demo_begin();
        }
        self.demo_finish();
    }

    fn demo_finish(&mut self) {
        let Some(d) = &mut self.demo else {
            return;
        };
        d.phase = Phase::Done;
        let n = d.scores.len();
        let summary = if n == 0 {
            "demo ended \u{00B7} nothing rated".to_string()
        } else {
            let mean = d.scores.iter().map(|(_, r)| *r as f64).sum::<f64>() / n as f64;
            let mut low = d.scores.clone();
            low.sort_by_key(|(_, r)| *r);
            let worst: Vec<String> = low
                .iter()
                .take(3)
                .map(|(i, r)| format!("#{} {} ({r})", i + 1, d.items[*i].0))
                .collect();
            format!(
                "demo ended \u{00B7} {n} rated \u{00B7} mean {mean:.0} \u{00B7} lowest: {}",
                worst.join(", ")
            )
        };
        let path = d.out.display().to_string();
        self.demo = None;
        self.stop_answer();
        self.chat.prompt = None;
        self.chat.banner = summary;
        self.chat.set_caption(format!("ratings saved to {path}"));
    }

    /// A key while the demo is on. True if the demo took it.
    pub(super) fn demo_key(&mut self, key: KeyEvent) -> bool {
        let Some(d) = &mut self.demo else {
            return false;
        };
        if d.phase != Phase::Rating {
            return false;
        }
        match key.code {
            KeyCode::Char(c @ '0'..='9') => {
                if d.typed.len() < 3 {
                    d.typed.push(c);
                }
            }
            KeyCode::Backspace => {
                d.typed.pop();
            }
            KeyCode::Enter => match d.typed.parse::<u32>() {
                Ok(r) if (1..=100).contains(&r) => {
                    self.demo_record(Some(r));
                    self.demo_next();
                    return true;
                }
                _ => d.typed.clear(),
            },
            KeyCode::Char('s') => {
                self.demo_record(None);
                self.demo_next();
                return true;
            }
            KeyCode::Char('r') => {
                self.demo_begin();
                return true;
            }
            KeyCode::Esc => {
                self.demo_finish();
                return true;
            }
            // every other key still works the diagram, to look round before rating
            _ => return false,
        }
        if let Some(d) = &self.demo
            && let Some((_, typed)) = &mut self.chat.prompt
        {
            *typed = d.typed.clone();
        }
        true
    }

    #[cfg(test)]
    pub(super) fn demo_phase(&self) -> Option<(usize, Phase)> {
        self.demo.as_ref().map(|d| (d.i, d.phase))
    }

    /// Test hook: the ratings file, and the question made old enough to be rated.
    #[cfg(test)]
    pub(super) fn demo_settle(&mut self) -> Option<PathBuf> {
        let d = self.demo.as_mut()?;
        d.started = Instant::now() - Duration::from_secs(5);
        Some(d.out.clone())
    }
}
