# Diagram clips: the bare-metal picture template

Picture scenes (the Blender and poly3d 3D pages) reach the terminal in one of two ways:

- **Frame path** (default): the TUI renders each tick (`pixels`), zlib-compresses the RGBA,
  and sends it as a kitty image. About 10 ms of CPU per tick at 1200x660, plus the write.
- **Clip path** (`FL_H264=1`, Ghostty fork only): each beat is rendered once, offline, into an
  H.264 stream. The TUI sends that stream once per beat change. The terminal decodes it
  (VideoToolbox) and loops it. The TUI does no per-tick work.

This doc is the setup for the clip path. SAND is the reference page.

## Layout

```
data/clips/                              # gitignored; FL_CLIPS overrides the root
  <page-slug>/                           # slug(page): lower case, dashes ("melt-pull")
    <clip>/                              # overview | zoom-<key> | section-<n>
      clip.json                          # w, h, fps, and per-beat { ms, frames }
      beat-<n>.h264                      # Annex B stream for beat n
```

## The stream contract

The fork (`ghostty-media`, `src/renderer/image.zig`, `renderer/metal/VideoDecoder.zig`) assumes:

| Rule | Why |
|---|---|
| Annex B, one kitty image per beat (`f=264`) | `parseAnnexB`; the protocol is raw bytes |
| 24 fps, frame `k` at `k / 24` s | the fork hardcodes `video_fps = 24` and has no rate in the protocol |
| No B-frames (`-bf 0`) | frames are timed in stream order; B-frames would decode out of order |
| SPS/PPS repeated (`repeat-headers=1`) | the fork decodes from the stream alone |
| `s`/`v` equal the stream's frame size | `completeVideo` needs the size; placement scales it to `c` x `r` cells |
| The stream loops forever | `Player.feedNext` wraps at the end (`loop_offset`); a beat is the loop |

`diagrams_h264::encode_beat` produces all of this. Do not change the ffmpeg flags without
re-checking the table.

## How a page plays (SAND is the reference)

1. **Opt in:** `clips: true` on the page's `Node` (`diagrams_nodes/sand/mod.rs`). Pages
   without it never touch clips, so a half-finished page can't show old ones.
2. **Terminal check:** at startup the TUI asks a kitty terminal to validate a tiny `f=264`
   image, ending the query with a DA1 request. The fork answers OK. Stock Ghostty and kitty
   reject the format. `FL_H264=1` or `FL_H264=0` overrides the check; tmux needs `FL_H264=1`
   because it drops the reply.
3. **Freshness:** each `clip.json` stores a 16x9 thumbnail per beat (the beat's middle frame,
   rendered at 64x36). The first time a clip shows, the TUI renders the same thumbnails from
   the live scene and compares them. A changed Blender export, scene, caption or beat length
   makes the clip stale.
4. **Self-healing:** a missing or stale clip starts `fl render-video <PAGE> --h264` in the
   background, once per page per session, logging to `data/clips/<slug>.render.log`. The
   overview renders first. The footer shows "rendering clips", and the page uses the frame
   path until the new clips land. Streams and `clip.json` are written to a temp file and
   renamed into place, so playback never reads half a file.
5. **Where clips play:** the overview, zoom-ins, sections, and the menu preview beside the
   page list (which shows only text without clips).

## Adding a page

1. The page has a scene (`scene_for(page)`): an overview, zoom-ins, and/or sections. The
   SAND scenes are the model: `diagrams_nodes/sand/*`.
2. Render its clips:
   ```sh
   tui/target/release/fl render-video <PAGE> --h264 --out data/clips
   ```
   Clips are rendered in parallel (up to 4). Each clip prints its beat count and length.
3. Check one clip:
   ```sh
   ffprobe -v error -select_streams v:0 -count_frames \
     -show_entries stream=codec_name,profile,width,height,has_b_frames,nb_read_frames \
     data/clips/<page-slug>/overview/beat-0.h264
   # expect h264, High, 1280x720, has_b_frames=0, nb_read_frames = ms/1000 * 24
   ```
4. Run it in the fork with `FL_H264=1` and check the page.

5. Set `clips: true` on its `Node`. Steps 2-3 are optional after that: a missing clip renders
   itself in the background the first time the page opens. To check that the clips on disk
   still match the scenes, see `sand_clips_on_disk_are_fresh` in `diagrams_h264.rs`, an ignored
   test you can copy for the new page.

## Running it

- Terminal: the Ghostty fork build (`ghostty-media`, `zig build run -Doptimize=ReleaseFast`).
  Stock Ghostty and kitty do not know `f=264`, so do not set `FL_H264=1` there: the picture
  area would stay empty.
- `fl`, then open the page. In the fork, clips turn on by themselves through the probe;
  inside tmux use `FL_H264=1 fl`. The overview plays on its beat; zoom-ins and sections use
  their own clips (`zoom-<key>`, `section-<n>`).
- `FL_CLIPS=/path fl` reads clips from elsewhere.

## Measured (SAND, 1280x720, 24 fps, veryfast, CRF 23)

| | Value |
|---|---|
| Offline render, all 15 SAND clips (6,720 frames) | 16 s wall on this Mac (4 workers, one GPU device each) |
| Stream size, overview beat 3 (5 s) | 734 KB (about 1.2 Mb/s) |
| Frame path, per tick (1200x660) | render 4.0 ms + zlib 4.4 ms = 8.5 ms, plus the write |
| Clip path, per tick | 0 ms |
| Clip path, per beat change | 0.7 ms to build about 0.9 MB of escapes, then the write |

Run `cargo test --release bench_sand_per_tick -- --ignored --nocapture` in `tui/` to repeat the
per-tick numbers.

## Where offline time goes

Encoding is not the cost: libx264 veryfast encodes a 120-frame beat in 0.18 s (about 660 fps).
h264_videotoolbox was slower on these short beats because of its setup cost. The GPU render is
the cost, so the offline render is GPU-bound at about 430 fps (1280x720).

Tools in `tools/pbr3d`:

```sh
cargo run --release --example scene_bench -- assets/sand_overview.glb 1280x720 60
#   setup+encode / GPU wait / readback copy per frame
PBR3D_PER_THREAD=1 cargo run --release --example thread_bench -- assets/sand_overview.glb 4 120
#   aggregate fps of N threads; PBR3D_SKIP=shadow,scene,depth,ao,bloom drops passes to cost them
cargo run --release --example frames_dump -- assets/sand_overview.glb /tmp/ref
#   frames to PSNR-compare before and after a shader change (ffmpeg -lavfi psnr)
```

GPU cost per pass, SAND overview at 1280x720, after the changes below: scene (4x MSAA) about
1.4 ms, AO about 0.9 ms, bloom about 0.2 ms, shadow map close to 0.

Changes made, and their effect (PSNR against the old frames stays above 63 dB; H.264 at CRF 23
is about 40 dB, so the difference is invisible):

| Change | Throughput |
|---|---|
| Baseline, shared renderer | 240 fps on one thread, 249 at 4 |
| One GPU device per worker (`pbr3d::gpu::set_per_thread`) | 321 at 4 |
| Separable depth-aware AO blur (14 taps, was a 49-tap box) and R16Float AO targets | 363 on one, 389 at 4 |
| 16 AO samples (was 24) | 370 on one, 433 at 4 |

Not done: 2x MSAA (Rgba16Float needs an adapter-specific feature for 2 samples), half-res AO,
and zero-copy IOSurface into VideoToolbox (the readback copy is 0.1 ms, so it would save little).

## Known gaps

- **Not yet seen in the fork.** The virtual placement (`a=T,U=1,f=264`) and the loop are
  written from the fork's code, not run. The first check is SAND in the fork.
- **Probe not run against the fork yet.** The OK/refuse logic is unit-tested, but nobody has
  seen the fork answer it. If SAND doesn't stream in the fork, try `FL_H264=1` to rule the
  probe out.
- **Loop seam.** A beat's last frame jumps to its first. The frame path has the same seam
  (its beat frames also loop).
- **Stream size over ssh.** About 1 MB per beat change. Fine locally; CRF or resolution is
  the knob if it is slow remotely.
- **Remaining pages.** Only SAND has clips so far.
