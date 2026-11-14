// Renders the diagram pages to HLS video for streaming: `fl render-video PAGE... --out DIR`.
//
// Every picture scene on a page becomes one HLS VOD (overview, zoom-ins, numbered sections). The
// frames are the same pixels the terminal shows, captions and notes included, sampled at the
// screen's beat timing and piped into ffmpeg (libx264, fragmented MP4 segments). Scenes that draw
// text rather than a picture are skipped. A manifest.json in DIR lists every clip for the player.
//
//   DIR/<page-slug>/<clip>/index.m3u8 + init.mp4 + seg*.m4s
//   DIR/manifest.json
//
// Nothing here needs a terminal, so it runs headless (and in CI).

use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use serde::{Deserialize, Serialize};

use super::diagrams_anim::{scene_for, section_anim};
use crate::ui::anim::{Scene, Time};

/// Default video size and frame rate.
pub const W: u32 = 1280;
pub const H: u32 = 720;
pub const FPS: u32 = 24;

/// Pages rendered by `--all`: every page with picture scenes.
pub const ALL_PAGES: &[&str] = &[
    "SAND",
    "POLYSILICON",
    "MELT + PULL",
    "INGOT",
    "SLICE + POLISH",
    "WAFER",
];

/// One rendered clip, as the player lists it.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq)]
pub struct Entry {
    pub page: String,
    pub clip: String,
    pub title: String,
    /// Path of the playlist, relative to the manifest's directory.
    pub path: String,
    pub seconds: f64,
}

struct Options {
    pages: Vec<String>,
    out: PathBuf,
    only: Option<String>,
    fps: u32,
    w: u32,
    h: u32,
    /// Annex B H.264 per beat for the bare-metal path, instead of HLS (diagrams_h264).
    h264: bool,
}

/// Entry point for `fl render-video`. Returns the process exit code.
pub fn run_cli(args: &[String]) -> i32 {
    let opts = match parse(args) {
        Ok(o) => o,
        Err(msg) => {
            eprintln!("{msg}");
            eprintln!("usage: fl render-video (PAGE... | --all) --out DIR [--clip NAME] [--fps N] [--size WxH] [--h264]");
            return 2;
        }
    };
    if opts.h264 {
        let threads = std::thread::available_parallelism().map_or(2, |n| n.get()).min(4);
        let failed = super::diagrams_h264::render_pages(&opts.pages, &opts.out, opts.only.as_deref(), threads);
        return i32::from(failed > 0);
    }
    if let Err(e) = std::fs::create_dir_all(&opts.out) {
        eprintln!("render-video: cannot create {}: {e}", opts.out.display());
        return 1;
    }
    let mut entries = read_manifest(&opts.out);
    let mut failed = 0;
    for page in &opts.pages {
        for (clip, title, scene) in clips(page) {
            if let Some(only) = &opts.only
                && only != &clip
            {
                continue;
            }
            let dir = opts.out.join(slug(page)).join(&clip);
            eprintln!("render-video: {page} / {clip}");
            match render_clip(scene.as_ref(), &dir, opts.w, opts.h, opts.fps) {
                Ok(Some(seconds)) => {
                    let path = format!("{}/{}/index.m3u8", slug(page), clip);
                    entries.retain(|e| e.path != path);
                    entries.push(Entry {
                        page: page.clone(),
                        clip,
                        title,
                        path,
                        seconds,
                    });
                }
                Ok(None) => eprintln!("  skipped: no picture"),
                Err(e) => {
                    eprintln!("  failed: {e}");
                    failed += 1;
                }
            }
        }
    }
    if let Err(e) = write_manifest(&opts.out, &entries) {
        eprintln!("render-video: manifest: {e}");
        return 1;
    }
    if failed > 0 { 1 } else { 0 }
}

fn parse(args: &[String]) -> Result<Options, String> {
    let mut o = Options {
        pages: Vec::new(),
        out: PathBuf::new(),
        only: None,
        fps: FPS,
        w: W,
        h: H,
        h264: false,
    };
    let mut have_out = false;
    let mut all = false;
    let mut it = args.iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--out" => {
                o.out = PathBuf::from(it.next().ok_or("--out needs a directory")?);
                have_out = true;
            }
            "--clip" => o.only = Some(it.next().ok_or("--clip needs a name")?.clone()),
            "--fps" => {
                o.fps = it
                    .next()
                    .and_then(|v| v.parse().ok())
                    .filter(|f| (1..=60).contains(f))
                    .ok_or("--fps needs 1..60")?;
            }
            "--size" => {
                let v = it.next().ok_or("--size needs WxH")?;
                let (w, h) = v.split_once('x').ok_or("--size needs WxH")?;
                o.w = w.parse().map_err(|_| "bad --size width")?;
                o.h = h.parse().map_err(|_| "bad --size height")?;
            }
            "--all" => all = true,
            "--h264" => o.h264 = true,
            page => o.pages.push(page.to_string()),
        }
    }
    if !have_out {
        return Err("--out DIR is required".into());
    }
    if all {
        o.pages = ALL_PAGES.iter().map(|p| p.to_string()).collect();
    }
    if o.pages.is_empty() {
        return Err("name at least one page, or --all".into());
    }
    Ok(o)
}

/// Every picture clip on a page, in page order: the overview, its zoom-ins, and the sections.
fn clips(page: &str) -> Vec<(String, String, Box<dyn Scene>)> {
    let mut out: Vec<(String, String, Box<dyn Scene>)> = Vec::new();
    if let Some(scene) = scene_for(page) {
        for z in scene.zooms() {
            out.push((
                format!("zoom-{}", z.key),
                format!("{page}: {}", z.label),
                (z.build)(),
            ));
        }
        out.insert(0, ("overview".into(), format!("{page} overview"), scene));
    }
    for i in 0.. {
        match section_anim(page, i) {
            Some(build) => out.push((
                format!("section-{}", i + 1),
                format!("{page} section {}", i + 1),
                build(),
            )),
            None => break,
        }
    }
    out
}

/// Renders one clip to an HLS playlist. Returns its length in seconds, or None when the scene
/// draws text rather than a picture.
fn render_clip(
    scene: &dyn Scene,
    dir: &Path,
    w: u32,
    h: u32,
    fps: u32,
) -> io::Result<Option<f64>> {
    let beats = scene.beats();
    if beats.is_empty() {
        return Ok(None);
    }
    // a scene with no picture returns None for its first frame; skip it before starting ffmpeg
    let probe = Time { ms: 0, beat: 0, local: 0.0, beat_start: 0 };
    if scene.pixels(&probe, w, h).is_none() {
        return Ok(None);
    }
    std::fs::create_dir_all(dir)?;
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
            "-g",
            &(fps * 2).to_string(),
            "-keyint_min",
            &fps.to_string(),
            "-sc_threshold",
            "0",
            "-f",
            "hls",
            "-hls_time",
            "4",
            "-hls_playlist_type",
            "vod",
            "-hls_segment_type",
            "fmp4",
            "-hls_fmp4_init_filename",
            "init.mp4",
            "-hls_segment_filename",
        ])
        .arg(dir.join("seg%03d.m4s"))
        .arg(dir.join("index.m3u8"))
        .stdin(Stdio::piped())
        .stderr(Stdio::inherit())
        .spawn()?;
    let mut total_ms = 0u64;
    {
        let stdin = ff.stdin.as_mut().ok_or_else(|| io::Error::other("no ffmpeg stdin"))?;
        let mut start = 0u64;
        for (b, beat) in beats.iter().enumerate() {
            let n = ((beat.ms as f64 / 1000.0) * fps as f64).round().max(1.0) as u32;
            for k in 0..n {
                let local = k as f32 / n as f32;
                let t = Time {
                    ms: start + (beat.ms as f64 * local as f64) as u64,
                    beat: b,
                    local,
                    beat_start: start,
                };
                let img = scene
                    .pixels(&t, w, h)
                    .ok_or_else(|| io::Error::other("a frame came back without a picture"))?;
                stdin.write_all(img.as_raw())?;
            }
            start += beat.ms;
        }
        total_ms = total_ms.max(start);
    }
    let status = ff.wait()?;
    if !status.success() {
        return Err(io::Error::other(format!("ffmpeg exited with {status}")));
    }
    Ok(Some(total_ms as f64 / 1000.0))
}

fn read_manifest(dir: &Path) -> Vec<Entry> {
    std::fs::read_to_string(dir.join("manifest.json"))
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

fn write_manifest(dir: &Path, entries: &[Entry]) -> io::Result<()> {
    let json = serde_json::to_string_pretty(entries).map_err(io::Error::other)?;
    std::fs::write(dir.join("manifest.json"), json)
}

/// A page name as a path segment: lower case, spaces and + become dashes.
pub fn slug(page: &str) -> String {
    page.to_lowercase()
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
        .collect::<String>()
        .split('-')
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn slugs_are_path_safe() {
        assert_eq!(slug("SAND"), "sand");
        assert_eq!(slug("MELT + PULL"), "melt-pull");
        assert_eq!(slug("SLICE + POLISH"), "slice-polish");
    }

    #[test]
    fn parses_pages_and_options() {
        let args: Vec<String> = ["SAND", "WAFER", "--out", "/tmp/v", "--fps", "12", "--size", "640x360"]
            .iter()
            .map(|s| s.to_string())
            .collect();
        let o = parse(&args).unwrap();
        assert_eq!(o.pages, vec!["SAND", "WAFER"]);
        assert_eq!((o.fps, o.w, o.h), (12, 640, 360));
        assert!(parse(&["SAND".to_string()]).is_err(), "--out is required");
    }

    #[test]
    fn sand_has_its_overview_zooms_and_sections() {
        let names: Vec<String> = clips("SAND").into_iter().map(|c| c.0).collect();
        assert_eq!(names[0], "overview");
        assert!(names.contains(&"zoom-a".to_string()));
        assert!(names.contains(&"section-1".to_string()));
    }
}
