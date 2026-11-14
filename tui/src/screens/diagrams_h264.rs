// Bare-metal H.264 picture clips for the diagram scenes (Ghostty fork: kitty `f=264`).
//
// Offline: `fl render-video PAGE... --h264 --out DIR` renders every picture clip one beat at a
// time into an Annex B H.264 stream, 24 fps, no B-frames, SPS/PPS repeated, plus a clip.json:
//
//   DIR/<page-slug>/<clip>/clip.json          clip = overview | zoom-<key> | section-<n>
//   DIR/<page-slug>/<clip>/beat-<n>.h264
//
// Runtime: pages that opt in (`Node::clips`) play their clips when the terminal decodes `f=264`
// (probed at startup; FL_H264=1/0 forces it, e.g. inside tmux, which drops the reply). The beat's
// stream is sent once as a kitty image with a virtual placement and the terminal decodes and loops
// it itself, so the TUI renders nothing per tick.
//
// Each clip.json carries a fingerprint per beat: a 16x9 thumbnail of the beat's middle frame. The
// first time a clip shows, the TUI renders the same thumbnails from the live scene; a clip that no
// longer matches (scene, Blender export or caption changed) is stale. A missing or stale clip
// starts `fl render-video PAGE --h264` in the background and the page uses the frame path until
// the new clips land.
//
// The fork's contract, which the encoder must match: frames are timed at 24 fps from the stream
// order (no B-frames, or the decode order would not be the presentation order), the stream
// carries its own parameter sets, and the image size `s`/`v` is the stream's frame size.

use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::collections::HashSet;
use std::sync::{Mutex, OnceLock};
use std::time::{Duration, Instant};

use image::RgbaImage;

use ratatui::Frame;
use ratatui::layout::Rect;
use serde::{Deserialize, Serialize};

use super::diagrams_anim::scene_for;
use super::diagrams_kitty_anim::{Sink, base64, place, wrap};
use super::diagrams_video::slug;
use crate::ui::anim::{Scene, Time, Zoom};

/// Frames a second. The fork hardcodes the same rate (`video_fps` in renderer/image.zig).
pub const FPS: u32 = 24;
/// Frame size of the offline clips: 16:9, placed into the picture area by the terminal.
pub const W: u32 = 1280;
pub const H: u32 = 720;

/// Image ids of the slots. Apart from the frame path's ids (diagrams_kitty_anim, 0x00F4_0000).
const IMAGE_BASE: u32 = 0x00F5_0000;
const SLOTS: usize = 3;
/// Escape chunk size before base64 (kitty's limit is 4096 bytes of payload per escape).
const CHUNK: usize = 4096;

/// Kitty image id of the capability probe.
const PROBE_ID: u32 = 0x00F5_F264;
/// Fingerprint thumbnail: rendered at this size, then averaged down to PRINT_COLS x PRINT_ROWS.
const PRINT_W: u32 = 64;
const PRINT_H: u32 = 36;
const PRINT_COLS: u32 = 16;
const PRINT_ROWS: u32 = 9;
/// Largest mean difference (0-255) between two fingerprints that still counts as the same picture.
const PRINT_TOLERANCE: f64 = 4.0;
/// How often a missing clip is looked for again (another process may be rendering it).
const RECHECK: Duration = Duration::from_secs(3);

static SUPPORT: OnceLock<bool> = OnceLock::new();

/// Decides once, at startup, whether the terminal plays clips: FL_H264=1/0 forces it, else a
/// kitty terminal is asked whether it accepts `f=264`. Call before the event loop reads stdin.
#[cfg_attr(test, allow(dead_code))] // called from the screen, which tests build without it
pub fn init(kitty: bool) {
    if SUPPORT.get().is_some() {
        return;
    }
    let on = match std::env::var("FL_H264").as_deref() {
        Ok("1") => true,
        Ok("0") => false,
        _ => kitty && probe_stdio().unwrap_or(false),
    };
    let _ = SUPPORT.set(on);
}

/// Whether the terminal plays clips (see `init`). Without `init`, only FL_H264=1 turns it on.
pub fn enabled() -> bool {
    *SUPPORT.get_or_init(|| std::env::var("FL_H264").is_ok_and(|v| v == "1"))
}

/// Asks the terminal to validate a tiny `f=264` image (a=q stores nothing), followed by a primary
/// device attributes request that every terminal answers. The fork replies OK before the DA1
/// reply; a terminal without the format replies with an error, or not at all.
#[cfg_attr(test, allow(dead_code))] // called from the screen, which tests build without it
fn probe_stdio() -> io::Result<bool> {
    use ratatui::crossterm::terminal::{disable_raw_mode, enable_raw_mode, is_raw_mode_enabled};
    use std::io::Read;
    use std::os::fd::AsRawFd;
    let was_raw = is_raw_mode_enabled()?;
    if !was_raw {
        enable_raw_mode()?;
    }
    let result = (|| {
        let mut out = io::stdout().lock();
        out.write_all(format!("\x1b_Gi={PROBE_ID},s=16,v=16,a=q,t=d,f=264;AAAA\x1b\\\x1b[c").as_bytes())?;
        out.flush()?;
        drop(out);
        let stdin = io::stdin();
        let fd = stdin.as_raw_fd();
        let deadline = Instant::now() + Duration::from_millis(400);
        let mut got = Vec::new();
        let mut buf = [0u8; 256];
        while Instant::now() < deadline && !has_da1_reply(&got) {
            let left = deadline.saturating_duration_since(Instant::now()).as_millis() as i32;
            let mut pfd = libc::pollfd { fd, events: libc::POLLIN, revents: 0 };
            // SAFETY: one valid pollfd for the duration of the call.
            let ready = unsafe { libc::poll(&mut pfd, 1, left.max(1)) };
            if ready <= 0 {
                break;
            }
            let n = stdin.lock().read(&mut buf)?;
            if n == 0 {
                break;
            }
            got.extend_from_slice(&buf[..n]);
        }
        Ok(probe_ok(&got))
    })();
    if !was_raw {
        let _ = disable_raw_mode();
    }
    result
}

/// Whether the bytes hold a DA1 reply (`ESC [ ? ... c`), the probe's end marker.
fn has_da1_reply(b: &[u8]) -> bool {
    b.windows(3).position(|w| w == b"\x1b[?").is_some_and(|i| b[i..].contains(&b'c'))
}

/// Whether the probe's kitty reply is OK.
fn probe_ok(b: &[u8]) -> bool {
    let want = format!("\x1b_Gi={PROBE_ID};OK");
    b.windows(want.len()).any(|w| w == want.as_bytes())
}

/// A picture's fingerprint: a 16x9 grey thumbnail of a 64x36 render.
pub fn fingerprint(img: &RgbaImage) -> Vec<u8> {
    let (w, h) = (img.width().max(1), img.height().max(1));
    let mut out = Vec::with_capacity((PRINT_COLS * PRINT_ROWS) as usize);
    for r in 0..PRINT_ROWS {
        for c in 0..PRINT_COLS {
            let (x0, x1) = (c * w / PRINT_COLS, ((c + 1) * w / PRINT_COLS).max(c * w / PRINT_COLS + 1));
            let (y0, y1) = (r * h / PRINT_ROWS, ((r + 1) * h / PRINT_ROWS).max(r * h / PRINT_ROWS + 1));
            let (mut sum, mut n) = (0u64, 0u64);
            for y in y0..y1.min(h) {
                for x in x0..x1.min(w) {
                    let p = img.get_pixel(x, y).0;
                    sum += (u64::from(p[0]) * 299 + u64::from(p[1]) * 587 + u64::from(p[2]) * 114) / 1000;
                    n += 1;
                }
            }
            out.push((sum / n.max(1)) as u8);
        }
    }
    out
}

/// Whether two fingerprints are the same picture, give or take rendering noise.
pub fn same_print(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() || a.is_empty() {
        return false;
    }
    let diff: u64 = a.iter().zip(b).map(|(x, y)| u64::from(x.abs_diff(*y))).sum();
    diff as f64 / a.len() as f64 <= PRINT_TOLERANCE
}

/// The time of beat `b`'s middle frame, the one its fingerprint is taken from.
fn mid_time(beats_ms: &[u64], b: usize) -> Time {
    let start: u64 = beats_ms[..b].iter().sum();
    Time { ms: start + beats_ms[b] / 2, beat: b, local: 0.5, beat_start: start }
}

/// Where the clips live: FL_CLIPS, else data/clips in the finlarp checkout.
pub fn root() -> PathBuf {
    std::env::var_os("FL_CLIPS")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../data/clips")))
}

/// The directory of one clip of a page.
pub fn clip_dir(root: &Path, page: &str, clip: &str) -> PathBuf {
    root.join(slug(page)).join(clip)
}

/// One clip's sidecar, written next to its beat streams.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Meta {
    pub page: String,
    pub clip: String,
    pub w: u32,
    pub h: u32,
    pub fps: u32,
    pub beats: Vec<Beat>,
    /// One fingerprint per beat (see `fingerprint`); empty in clips from before they existed,
    /// which then count as stale.
    #[serde(default)]
    pub prints: Vec<Vec<u8>>,
}

#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Beat {
    /// Length of the beat in milliseconds, as the scene times it.
    pub ms: u64,
    /// Frames in the stream (round(ms * fps / 1000), at least one).
    pub frames: u32,
}

/// Where a clip's pictures come from: the page's overview, or a build function (zoom-in or section).
#[derive(Clone, Copy)]
pub enum Src {
    Overview,
    Build(fn() -> Box<dyn Scene>),
}

/// One clip to render. Plain data, so worker threads can take it: the scene is built on the
/// thread that renders it.
pub struct Job {
    pub page: String,
    pub clip: String,
    pub src: Src,
}

/// Every picture clip of a page, in menu order: overview, zoom-ins, sections (as the HLS path).
pub fn jobs(page: &str) -> Vec<Job> {
    let mut out = Vec::new();
    let Some(scene) = scene_for(page) else {
        return out;
    };
    out.push(Job { page: page.to_string(), clip: "overview".into(), src: Src::Overview });
    for Zoom { key, build, .. } in scene.zooms() {
        out.push(Job { page: page.to_string(), clip: format!("zoom-{key}"), src: Src::Build(*build) });
    }
    for i in 0.. {
        match super::diagrams_anim::section_anim(page, i) {
            Some(build) => out.push(Job {
                page: page.to_string(),
                clip: format!("section-{}", i + 1),
                src: Src::Build(build),
            }),
            None => break,
        }
    }
    out
}

/// Renders one clip's beats. Returns None when the scene draws no picture (text scenes).
fn render_job(job: &Job, root: &Path, w: u32, h: u32, fps: u32) -> io::Result<Option<Meta>> {
    let scene: Box<dyn Scene> = match job.src {
        Src::Overview => match scene_for(&job.page) {
            Some(s) => s,
            None => return Ok(None),
        },
        Src::Build(f) => f(),
    };
    let beats = scene.beats();
    if beats.is_empty() {
        return Ok(None);
    }
    let probe = Time { ms: 0, beat: 0, local: 0.0, beat_start: 0 };
    if scene.pixels(&probe, w, h).is_none() {
        return Ok(None);
    }
    let dir = clip_dir(root, &job.page, &job.clip);
    std::fs::create_dir_all(&dir)?;
    let mut meta = Meta {
        page: job.page.clone(),
        clip: job.clip.clone(),
        w,
        h,
        fps,
        beats: Vec::with_capacity(beats.len()),
        prints: Vec::with_capacity(beats.len()),
    };
    let beats_ms: Vec<u64> = beats.iter().map(|b| b.ms).collect();
    let mut start = 0u64;
    for (b, beat) in beats.iter().enumerate() {
        let frames = ((beat.ms as f64 / 1000.0) * fps as f64).round().max(1.0) as u32;
        let path = dir.join(format!("beat-{b}.h264"));
        encode_beat(scene.as_ref(), b, start, frames, w, h, fps, &path)?;
        let thumb = scene
            .pixels(&mid_time(&beats_ms, b), PRINT_W, PRINT_H)
            .ok_or_else(|| io::Error::other("the fingerprint frame came back without a picture"))?;
        meta.prints.push(fingerprint(&thumb));
        meta.beats.push(Beat { ms: beat.ms, frames });
        start += beat.ms;
    }
    // the sidecar goes last and whole: a reader sees the old clip or the new one, never half
    let json = serde_json::to_string_pretty(&meta).map_err(io::Error::other)?;
    let tmp = dir.join("clip.json.tmp");
    std::fs::write(&tmp, json)?;
    std::fs::rename(&tmp, dir.join("clip.json"))?;
    Ok(Some(meta))
}

/// Encodes one beat into an Annex B stream at `path`. `start` is the beat's time in the clip.
#[allow(clippy::too_many_arguments)]
fn encode_beat(
    scene: &dyn Scene,
    b: usize,
    start: u64,
    frames: u32,
    w: u32,
    h: u32,
    fps: u32,
    path: &Path,
) -> io::Result<()> {
    let beat_ms = scene.beats()[b].ms;
    let gop = (fps * 2).to_string();
    let mut ff = Command::new("ffmpeg")
        .args([
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-s",
            &format!("{w}x{h}"),
            "-r",
            &fps.to_string(),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            // no B-frames: the fork times frames by stream order
            "-bf",
            "0",
            "-g",
            &gop,
            "-x264-params",
            "repeat-headers=1:scenecut=0",
            "-f",
            "h264",
        ])
        .arg(path.with_extension("h264.tmp"))
        .stdin(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()?;
    {
        let stdin = ff.stdin.as_mut().ok_or_else(|| io::Error::other("no ffmpeg stdin"))?;
        for k in 0..frames {
            let local = k as f32 / frames as f32;
            let t = Time {
                ms: start + (beat_ms as f64 * local as f64) as u64,
                beat: b,
                local,
                beat_start: start,
            };
            let img = scene
                .pixels(&t, w, h)
                .ok_or_else(|| io::Error::other("a frame came back without a picture"))?;
            stdin.write_all(img.as_raw())?;
        }
    }
    let status = ff.wait()?;
    if !status.success() {
        return Err(io::Error::other(format!("ffmpeg exited with {status}")));
    }
    // written beside and moved in whole, so a playing TUI never reads half a stream
    std::fs::rename(path.with_extension("h264.tmp"), path)
}

/// Renders the H.264 clips of `pages` into `out`, `threads` clips at a time. `only` keeps one
/// clip name. Prints one line per clip; returns how many failed.
pub fn render_pages(pages: &[String], out: &Path, only: Option<&str>, threads: usize) -> usize {
    let mut queue: Vec<Job> = pages
        .iter()
        .flat_map(|p| jobs(p))
        .filter(|j| only.is_none_or(|o| o == j.clip))
        .collect();
    // workers pop from the end: reversed, the overview (what a page opens on) is done first
    queue.reverse();
    let queue = Mutex::new(queue);
    let failed = Mutex::new(0usize);
    // one GPU device per worker: the shared renderer's lock would serialize them
    pbr3d::gpu::set_per_thread(true);
    std::thread::scope(|s| {
        for _ in 0..threads.max(1) {
            s.spawn(|| loop {
                let job = match queue.lock().ok().and_then(|mut q| q.pop()) {
                    Some(j) => j,
                    None => break,
                };
                eprintln!("render-video --h264: {} / {}", job.page, job.clip);
                match render_job(&job, out, W, H, FPS) {
                    Ok(Some(m)) => {
                        let secs: u64 = m.beats.iter().map(|b| b.ms).sum();
                        eprintln!("  {} beats, {:.1} s", m.beats.len(), secs as f64 / 1000.0);
                    }
                    Ok(None) => eprintln!("  skipped: no picture"),
                    Err(e) => {
                        eprintln!("  failed: {e}");
                        if let Ok(mut f) = failed.lock() {
                            *f += 1;
                        }
                    }
                }
            });
        }
    });
    failed.into_inner().unwrap_or(1)
}

/// The escapes that send one beat's stream as a kitty image with a virtual placement of
/// `cols` x `rows` cells. The stream is already compressed: no zlib, just base64 in chunks.
pub fn transmit(id: u32, stream: &[u8], w: u32, h: u32, cols: u16, rows: u16, tmux: bool) -> Vec<u8> {
    let data = base64(stream);
    let mut out = Vec::new();
    let mut pos = 0;
    let mut first = true;
    loop {
        let end = (pos + CHUNK).min(data.len());
        let more = usize::from(end < data.len());
        let head = if first {
            format!("a=T,U=1,f=264,s={w},v={h},c={cols},r={rows},i={id},q=2,m={more}")
        } else {
            format!("m={more}")
        };
        out.extend(wrap(&format!("{head};{}", &data[pos..end]), tmux));
        pos = end;
        first = false;
        if more == 0 {
            break;
        }
    }
    out
}

/// Largest whole-cell rectangle of a `w` x `h` picture that fits `area`, centred in it.
pub fn fit(area: Rect, cell_px: (u16, u16), w: u32, h: u32) -> Rect {
    let (cw, ch) = (f64::from(cell_px.0.max(1)), f64::from(cell_px.1.max(1)));
    let scale = (f64::from(area.width) * cw / f64::from(w)).min(f64::from(area.height) * ch / f64::from(h));
    let cols = ((f64::from(w) * scale / cw).floor().max(1.0) as u16).min(area.width);
    let rows = ((f64::from(h) * scale / ch).floor().max(1.0) as u16).min(area.height);
    let x = area.x + (area.width - cols) / 2;
    let y = area.y + (area.height - rows) / 2;
    Rect::new(x, y, cols, rows)
}

/// What a slot holds: the clip it belongs to, its beat, and the cells it fills.
#[derive(Clone, Copy, Debug, PartialEq)]
struct Loaded {
    key: u64,
    beat: usize,
    cols: u16,
    rows: u16,
}

/// One clip's sidecar as read from disk, and whether it still matches the live scene.
struct ClipState {
    dir: PathBuf,
    meta: Option<Meta>,
    /// None until the fingerprints are compared (on the clip's first paint).
    fresh: Option<bool>,
    read_at: Instant,
}

/// Plays beats of clips through kitty image slots, like the frame path does: a beat is sent when
/// it first shows, the terminal loops it, and a slot is freed before it is reused. Missing or
/// stale clips are re-rendered by a background `fl render-video`.
pub struct Playback {
    slots: [Option<Loaded>; SLOTS],
    clip: Option<ClipState>,
    sink: Sink,
    /// The background render, and the pages already asked for this session.
    render: Option<std::process::Child>,
    requested: HashSet<String>,
    /// Starts the background render; a no-op in tests.
    spawn: bool,
}

impl Default for Playback {
    fn default() -> Self {
        Self {
            slots: [None; SLOTS],
            clip: None,
            sink: Sink::Stdout,
            render: None,
            requested: HashSet::new(),
            spawn: true,
        }
    }
}

impl Playback {
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn with_sink(sink: Sink) -> Self {
        Self { sink, spawn: false, ..Self::default() }
    }

    /// Escapes written to the buffer sink (tests).
    #[cfg_attr(not(test), allow(dead_code))]
    pub fn written(&self) -> &[u8] {
        match &self.sink {
            Sink::Buffer(b) => b,
            Sink::Stdout => &[],
        }
    }

    fn emit(&mut self, bytes: &[u8]) {
        match &mut self.sink {
            Sink::Stdout => {
                let mut out = io::stdout().lock();
                let _ = out.write_all(bytes);
                let _ = out.flush();
            }
            Sink::Buffer(b) => b.extend_from_slice(bytes),
        }
    }

    /// Whether a background render is running.
    pub fn rendering(&self) -> bool {
        self.render.is_some()
    }

    /// Reaps a finished background render and forgets the cached sidecar, so new clips are read.
    fn poll_render(&mut self) {
        if let Some(child) = self.render.as_mut()
            && !matches!(child.try_wait(), Ok(None))
        {
            self.render = None;
            self.clip = None;
        }
    }

    /// Renders `page`'s clips in a background `fl render-video`, once a session per page.
    fn request_render(&mut self, page: &str) {
        if !self.spawn || self.render.is_some() || !self.requested.insert(page.to_string()) {
            return;
        }
        let root = root();
        let _ = std::fs::create_dir_all(&root);
        let log = std::fs::File::create(root.join(format!("{}.render.log", slug(page))));
        let Ok(exe) = std::env::current_exe() else {
            return;
        };
        let child = Command::new(exe)
            .args(["render-video", page, "--h264", "--out"])
            .arg(&root)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(log.map(Stdio::from).unwrap_or_else(|_| Stdio::null()))
            .spawn();
        self.render = child.ok();
    }

    /// The clip in `dir`, read once (and again every RECHECK while it is missing).
    fn state(&mut self, dir: &Path) -> &mut ClipState {
        let reread = match &self.clip {
            Some(c) => c.dir != dir || (c.meta.is_none() && c.read_at.elapsed() > RECHECK),
            None => true,
        };
        if reread {
            let meta = std::fs::read_to_string(dir.join("clip.json"))
                .ok()
                .and_then(|text| serde_json::from_str::<Meta>(&text).ok());
            self.clip = Some(ClipState { dir: dir.to_path_buf(), meta, fresh: None, read_at: Instant::now() });
        }
        self.clip.as_mut().expect("just set")
    }

    /// Shows beat `beat` of `page`'s clip `clip` inside `area`. `beats_ms` are the live scene's
    /// beat lengths and `render` draws it, for the staleness check. Returns false when the clip is
    /// missing or stale (and starts its re-render), so the caller draws the frame path instead.
    #[allow(clippy::too_many_arguments)]
    pub fn paint(
        &mut self,
        frame: &mut Frame,
        area: Rect,
        page: &str,
        clip: &str,
        beat: usize,
        beats_ms: &[u64],
        cell_px: (u16, u16),
        tmux: bool,
        render: &mut dyn FnMut(&Time, u32, u32) -> Option<RgbaImage>,
    ) -> bool {
        if area.width == 0 || area.height == 0 {
            return false;
        }
        self.poll_render();
        let dir = clip_dir(&root(), page, clip);
        let state = self.state(&dir);
        let fresh = match (&state.meta, state.fresh) {
            (None, _) => false,
            (Some(_), Some(f)) => f,
            (Some(meta), None) => {
                let f = clip_matches(meta, beats_ms, render);
                state.fresh = Some(f);
                f
            }
        };
        if !fresh {
            self.request_render(page);
            return false;
        }
        let Some(meta) = self.clip.as_ref().and_then(|c| c.meta.as_ref()) else {
            return false;
        };
        let (w, h) = (meta.w, meta.h);
        if beat >= meta.beats.len() {
            return false;
        }
        let key = clip_key(page, clip);
        let fitted = fit(area, cell_px, w, h);
        let slot = beat % SLOTS;
        let id = IMAGE_BASE + slot as u32;
        let want = Loaded { key, beat, cols: fitted.width, rows: fitted.height };
        if self.slots[slot] != Some(want) {
            let Ok(stream) = std::fs::read(dir.join(format!("beat-{beat}.h264"))) else {
                return false;
            };
            let mut bytes = Vec::new();
            if self.slots[slot].is_some() {
                bytes.extend(wrap(&format!("a=d,d=I,i={id},q=2"), tmux));
            }
            bytes.extend(transmit(id, &stream, w, h, fitted.width, fitted.height, tmux));
            self.emit(&bytes);
            self.slots[slot] = Some(want);
        }
        place(frame, fitted, id);
        true
    }
}

/// Whether a rendered clip still shows the live scene: same beats, same fingerprints.
fn clip_matches(
    meta: &Meta,
    beats_ms: &[u64],
    render: &mut dyn FnMut(&Time, u32, u32) -> Option<RgbaImage>,
) -> bool {
    if meta.beats.len() != beats_ms.len()
        || meta.prints.len() != beats_ms.len()
        || meta.beats.iter().zip(beats_ms).any(|(b, ms)| b.ms != *ms)
    {
        return false;
    }
    (0..beats_ms.len()).all(|b| {
        render(&mid_time(beats_ms, b), PRINT_W, PRINT_H).is_some_and(|img| same_print(&fingerprint(&img), &meta.prints[b]))
    })
}

/// The clip key for a picture: a hash of its page and clip name.
pub fn clip_key(page: &str, clip: &str) -> u64 {
    use std::hash::{Hash, Hasher};
    let mut hs = std::collections::hash_map::DefaultHasher::new();
    (page, clip).hash(&mut hs);
    hs.finish()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn transmit_chunks_and_keeps_the_keys_on_the_first_escape() {
        let stream: Vec<u8> = (0..10_000u32).map(|i| (i % 251) as u8).collect();
        let out = String::from_utf8(transmit(7, &stream, 1280, 720, 40, 12, false)).unwrap();
        let escapes: Vec<&str> = out.split("\x1b\\").filter(|s| !s.is_empty()).collect();
        assert!(escapes.len() > 1, "a 10 KB stream spans several chunks");
        assert!(escapes[0].starts_with("\x1b_Ga=T,U=1,f=264,s=1280,v=720,c=40,r=12,i=7,q=2,m=1;"));
        assert!(escapes[1].starts_with("\x1b_Gm="), "later chunks carry only m");
        assert!(escapes.last().unwrap().starts_with("\x1b_Gm=0;"), "the last chunk ends the image");
        let payload: String = escapes
            .iter()
            .map(|e| e.split_once(';').map(|(_, p)| p).unwrap_or(""))
            .collect();
        assert_eq!(payload, base64(&stream));
    }

    #[test]
    fn transmit_wraps_for_tmux() {
        let out = transmit(1, b"abc", 2, 2, 1, 1, true);
        assert!(out.starts_with(b"\x1bPtmux;"));
        assert!(out.ends_with(b"\x1b\\"));
    }

    #[test]
    fn fit_keeps_the_picture_shape_and_centres_it() {
        // 80x24 cells of 10x20 px: a 1280x720 picture is 16:9 in an 800x480 px area
        let area = Rect::new(0, 0, 80, 24);
        let r = fit(area, (10, 20), 1280, 720);
        assert_eq!((r.width, r.height), (80, 22), "limited by width: 800 px wide, 450 px tall");
        assert_eq!((r.x, r.y), (0, 1));
        // a tall, narrow area is limited by width
        let r = fit(Rect::new(5, 5, 20, 60), (10, 20), 1280, 720);
        assert_eq!(r.width, 20);
        assert!(r.height < 60 && r.y > 5);
    }

    #[test]
    fn jobs_list_overview_zooms_and_sections_in_order() {
        let names: Vec<String> = jobs("SAND").into_iter().map(|j| j.clip).collect();
        assert_eq!(names[0], "overview");
        assert!(names.contains(&"zoom-a".to_string()));
        assert!(names.contains(&"section-1".to_string()));
        assert!(jobs("NOT A PAGE").is_empty());
    }

    /// Per-tick cost of the frame path against the H.264 send, for SAND's overview.
    /// `cargo test --release bench_sand_per_tick -- --ignored --nocapture`
    #[test]
    #[ignore]
    fn bench_sand_per_tick() {
        use flate2::Compression;
        use flate2::write::ZlibEncoder;
        use std::time::Instant;
        let scene = scene_for("SAND").expect("SAND has a scene");
        let (w, h) = (1200u32, 660u32);
        let t = Time { ms: 0, beat: 2, local: 0.5, beat_start: 0 };
        let _ = scene.pixels(&t, w, h);
        let n = 30;
        let (mut render, mut zlib) = (0.0f64, 0.0f64);
        for k in 0..n {
            let t = Time { ms: 0, beat: 2, local: k as f32 / n as f32, beat_start: 0 };
            let s0 = Instant::now();
            let img = scene.pixels(&t, w, h).expect("a picture");
            render += s0.elapsed().as_secs_f64() * 1e3;
            let s1 = Instant::now();
            let mut enc = ZlibEncoder::new(Vec::new(), Compression::fast());
            std::io::Write::write_all(&mut enc, img.as_raw()).unwrap();
            let _ = enc.finish().unwrap();
            zlib += s1.elapsed().as_secs_f64() * 1e3;
        }
        let stream = std::fs::read(root().join("sand/overview/beat-2.h264")).unwrap_or_default();
        let s2 = Instant::now();
        let m = 20;
        let mut bytes = 0usize;
        for _ in 0..m {
            bytes = transmit(1, &stream, W, H, 80, 22, false).len();
        }
        let send = s2.elapsed().as_secs_f64() * 1e3 / m as f64;
        println!(
            "frame path per tick: render {:.1} ms + zlib {:.1} ms = {:.1} ms ({} KB raw RGBA per frame)",
            render / n as f64,
            zlib / n as f64,
            (render + zlib) / n as f64,
            (w * h * 4) / 1024
        );
        println!(
            "h264 path per beat change: {} KB stream, {:.2} ms to build {} KB of escapes; 0 ms per tick",
            stream.len() / 1024,
            send,
            bytes / 1024
        );
    }

    #[test]
    fn probe_reads_ok_before_the_da1_reply() {
        let ok = format!("\x1b_Gi={PROBE_ID};OK\x1b\\\x1b[?62;22c");
        assert!(has_da1_reply(ok.as_bytes()) && probe_ok(ok.as_bytes()));
        let refused = format!("\x1b_Gi={PROBE_ID};EINVAL:bad format\x1b\\\x1b[?62;22c");
        assert!(has_da1_reply(refused.as_bytes()) && !probe_ok(refused.as_bytes()));
        assert!(!has_da1_reply(b"\x1b_Gi=1;OK"), "no DA1 yet: keep reading");
    }

    #[test]
    fn fingerprints_tell_pictures_apart_but_forgive_noise() {
        let grad = RgbaImage::from_fn(64, 36, |x, y| image::Rgba([(x * 4) as u8, (y * 7) as u8, 90, 255]));
        let noisy = RgbaImage::from_fn(64, 36, |x, y| {
            let p = grad.get_pixel(x, y).0;
            image::Rgba([p[0].saturating_add(((x + y) % 3) as u8), p[1], p[2], 255])
        });
        let other = RgbaImage::from_fn(64, 36, |x, _| image::Rgba([255 - (x * 4) as u8, 0, 0, 255]));
        let a = fingerprint(&grad);
        assert_eq!(a.len(), 144);
        assert!(same_print(&a, &fingerprint(&noisy)));
        assert!(!same_print(&a, &fingerprint(&other)));
        assert!(!same_print(&a, &[]), "an old clip without prints is stale");
    }

    fn meta_for(prints: Vec<Vec<u8>>, ms: &[u64]) -> Meta {
        Meta {
            page: "T".into(),
            clip: "overview".into(),
            w: 64,
            h: 36,
            fps: FPS,
            beats: ms.iter().map(|&ms| Beat { ms, frames: 1 }).collect(),
            prints,
        }
    }

    #[test]
    fn a_clip_is_stale_when_the_scene_changed() {
        let red = |_: &Time, w: u32, h: u32| Some(RgbaImage::from_pixel(w, h, image::Rgba([200, 20, 20, 255])));
        let blue = |_: &Time, w: u32, h: u32| Some(RgbaImage::from_pixel(w, h, image::Rgba([20, 20, 200, 255])));
        let print = fingerprint(&red(&mid_time(&[1000], 0), PRINT_W, PRINT_H).unwrap());
        let meta = meta_for(vec![print.clone(), print], &[1000, 1000]);
        assert!(clip_matches(&meta, &[1000, 1000], &mut { red }));
        assert!(!clip_matches(&meta, &[1000, 1000], &mut { blue }), "the picture changed");
        assert!(!clip_matches(&meta, &[1000, 2000], &mut { red }), "a beat got longer");
        assert!(!clip_matches(&meta, &[1000], &mut { red }), "a beat was removed");
    }

    #[test]
    fn a_fresh_clip_streams_and_a_missing_one_falls_back() {
        let dir = std::env::temp_dir().join(format!("fl-h264-test-{}", std::process::id()));
        // SAFETY: tests that read FL_CLIPS run in this process only through this test.
        unsafe { std::env::set_var("FL_CLIPS", &dir) };
        let red = |_: &Time, w: u32, h: u32| Some(RgbaImage::from_pixel(w, h, image::Rgba([200, 20, 20, 255])));
        let print = fingerprint(&red(&mid_time(&[1000], 0), PRINT_W, PRINT_H).unwrap());
        let clip = clip_dir(&dir, "TEST PAGE", "overview");
        std::fs::create_dir_all(&clip).unwrap();
        std::fs::write(clip.join("clip.json"), serde_json::to_string(&meta_for(vec![print], &[1000])).unwrap()).unwrap();
        std::fs::write(clip.join("beat-0.h264"), b"\x00\x00\x00\x01stream").unwrap();

        let backend = ratatui::backend::TestBackend::new(40, 12);
        let mut term = ratatui::Terminal::new(backend).unwrap();
        let mut pb = Playback::with_sink(Sink::Buffer(Vec::new()));
        let mut shown = false;
        term.draw(|f| {
            shown = pb.paint(f, Rect::new(0, 0, 40, 12), "TEST PAGE", "overview", 0, &[1000], (10, 20), false, &mut { red });
        })
        .unwrap();
        assert!(shown);
        let sent = String::from_utf8_lossy(pb.written()).to_string();
        assert!(sent.contains("f=264,s=64,v=36"), "the beat went out as an f=264 image");

        let mut missing = false;
        term.draw(|f| {
            missing = !pb.paint(f, Rect::new(0, 0, 40, 12), "TEST PAGE", "zoom-a", 0, &[1000], (10, 20), false, &mut { red });
        })
        .unwrap();
        assert!(missing, "no clip on disk: the caller draws the frame path");
        let _ = std::fs::remove_dir_all(&dir);
    }

    /// The clips on disk match the live scenes, rendered here through the shared renderer the
    /// way the TUI checks them. Run after `fl render-video SAND --h264 --out data/clips`:
    /// `cargo test --release sand_clips_on_disk_are_fresh -- --ignored --nocapture`
    #[test]
    #[ignore]
    fn sand_clips_on_disk_are_fresh() {
        let root = PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/../data/clips"));
        for job in jobs("SAND") {
            let scene: Box<dyn Scene> = match job.src {
                Src::Overview => scene_for("SAND").unwrap(),
                Src::Build(f) => f(),
            };
            let text = std::fs::read_to_string(clip_dir(&root, "SAND", &job.clip).join("clip.json"))
                .unwrap_or_else(|_| panic!("{}: not rendered", job.clip));
            let meta: Meta = serde_json::from_str(&text).unwrap();
            let beats_ms: Vec<u64> = scene.beats().iter().map(|b| b.ms).collect();
            let worst = (0..beats_ms.len())
                .map(|b| {
                    let img = scene.pixels(&mid_time(&beats_ms, b), PRINT_W, PRINT_H).unwrap();
                    let (a, p) = (fingerprint(&img), &meta.prints[b]);
                    a.iter().zip(p).map(|(x, y)| u64::from(x.abs_diff(*y))).sum::<u64>() as f64 / a.len() as f64
                })
                .fold(0.0f64, f64::max);
            println!("{:<11} worst mean diff {worst:.2}", job.clip);
            assert!(clip_matches(&meta, &beats_ms, &mut |t, w, h| scene.pixels(t, w, h)), "{} is stale", job.clip);
        }
    }

    #[test]
    fn clip_keys_differ_per_clip() {
        assert_ne!(clip_key("SAND", "overview"), clip_key("SAND", "zoom-a"));
        assert_eq!(clip_key("SAND", "overview"), clip_key("SAND", "overview"));
    }
}
