# Diagram pages: the picture-and-panel template

How to build a diagram page (overview, zoom-ins, numbered sections) in the template SAND uses.
Every picture is a Blender scene played back through pbr3d. The 3D scene fills the left of the
frame with short tags pinned to its parts, and the beat's text sits in a panel on the right.

```
┌────────────────────────────────────┬──────────────────────┐
│                                    │ STEP 2 OF 4          │
│   3D scene (Blender GLB)           │ caption (gold)       │
│        ┌──────────┐                │                      │
│   ●────┤ tag      │                │ what's happening     │
│        └──────────┘                │                      │
│                                    │ LOOK FOR ...         │
│   scene_width(w) = 64% of frame    │ KEY NUMBERS ...      │
└────────────────────────────────────┴──────────────────────┘
```

SAND is the reference: `tui/src/screens/diagrams_nodes/sand/` and
`tools/pbr3d/blender/sand_{overview,zooms,sections}.py`.

## The pieces

| Piece | Where | Job |
|---|---|---|
| Blender script | `tools/pbr3d/blender/<page>_*.py` | builds the scene, animation, camera and tags, exports a GLB |
| GLB | `tools/pbr3d/assets/<page>_*.glb` | embedded in `fl` with `include_bytes!` |
| `Page` | `sand/mod.rs` | a `Scene` that renders the GLB on the left, pins the tags, composes the panel |
| Beat text | `overview.rs`, `zoom.rs`, `sections.rs` | one `Beat` per step, the panel's content |
| `pbr3d::caption` | `tools/pbr3d/src/caption.rs` | `scene_width`, `Tags`, `compose` (the panel layout and font) |
| `Node` | `<page>/mod.rs`, listed in `diagrams_nodes/mod.rs` `NODES` | wires the overview and sections into the menu |

`Page` lives in `sand/mod.rs` for now. When a second page adopts the template, move `Page`,
`picture` and the test helpers to `diagrams_nodes/blender.rs` (replacing the old `Clip`, which
draws text over the picture) and import them from both pages.

## Timing: one rule

**One beat is 8 seconds**, both sides:

- Blender: `FPS = 24`, `SEC = 8`, so beat `i` covers frames `192*i .. 192*(i+1)`. Use
  `F(beat, u)` for "fraction `u` through `beat`" and never write frame numbers by hand.
- Rust: `BEAT_MS = 8000` on every `Beat`, and `Page::pixels` samples the GLB at
  `(beat + local) * BEAT_SECS`.

Beat counts must match between script and Rust (SAND: overview 6, zooms 4, sections 3). Each
`zoom.rs`/`sections.rs` has a test asserting its counts; keep it in step with the script.

## Step 1: the Blender scene

Start a script by importing the helpers rather than copying them (see `sand_zooms.py`):

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sand_overview as O
from sand_overview import F, P, ball, box, cut, disc, empty, fly, key, label, pivot, rel, show, ...
from sand_zooms import start, camera, finish, scale_keys, stream_of
```

| Helper | Use |
|---|---|
| `start(name, beats)` | fresh file, timeline, the shared materials dict `m`, root empty |
| `camera(root, poses)` | one `(target, distance, yaw, pitch)` per beat, slow push-in, cut at the beat boundary |
| `finish(name)` | saves `blender/<name>.blend` and exports `assets/<name>.glb` |
| `P(x, y, z)` | scene coordinates (mm, **Y up**) to Blender's Z-up |
| `box / disc / ball / rock / tube / cup / wall` | geometry; `wall` is a hollow cylinder (solidify) |
| `cut(obj, z)` | slices off everything in front of plane `z` and caps it, so the inside shows |
| `pivot(name, at)` + `rel(at, p)` | a group to scale or move about point `at`; build children in `rel` coords |
| `show(obj, intervals)` | on/off switch: visible during each `[f0, f1)` |
| `scale_keys(obj, keys, until=)` | scale keys; keys before `until` pop instead of ramp |
| `fly(obj, path, f0, f1)` | move a group along a polyline of offsets |
| `stream_of(...)` | a train of blobs (gas, drops, lumps) travelling a path through one beat |
| `label(text, at, parent, intervals)` | a tag the TUI pins at `at` while visible |

### Conventions

- **Units are millimetres, Y up.** Keep everything inside about 40 m of the camera (far plane).
- **Cut-away view.** Objects are cut at `z = 0` and the camera sits on `+z`. Stagger cut offsets
  front to back (`cut(..., 3.0)`, `6.0`, `9.0`, `12.0`) so cut faces don't z-fight. Boxes don't
  need `cut`; give them `z` from `-depth` to `0` and the front face is the cut plane.
- **Frame for the left pane.** The scene gets about 64% of the frame width, so it's roughly
  square. Vertical field of view is 0.52 rad, so the visible height ≈ `0.53 × distance`. Pick
  distances so the beat's subject fills the pane with some margin.
- **One idea per beat.** The camera holds one pose per beat. Change pose at beat boundaries only.
- **Tags.** 2 to 4 per beat, short (under ~35 characters), switched on only for the beat they
  explain (`beat(i)`, or a sub-interval). Values belong in tags: "China 4,000 kt",
  "11 MWh per tonne". The name limit is 63 characters including `label:`, and underscores become
  spaces. Avoid ending a tag in `.` plus three digits: that reads as Blender's `.001` suffix and
  is stripped.
- **Materials.** Use `m[...]` from `O.M()` (steel, charge, quartz, coke, silicon, cavity, arc,
  melt, sio, fume, ...) plus the extras `start` adds. Emission strength 2 to 4 for glowing
  things; large emissive surfaces wash out, so keep backdrops non-emissive.

### Gotchas (all hit while building SAND)

- **`label` under a pivot takes coordinates relative to the pivot.** Under a group empty that
  sits at the origin while building (and moves only by keys), absolute coordinates are fine.
- **Scale a pivot only along axes that pass through its children.** A pivot at `(x, 0, 0)` with
  a child at `z = -450`, scaled in z, slides the child. Put the pivot at the child's centre.
- **Hide before showing with all-axis `OFF`.** A bar keyed `(1, 1, OFF)` before it grows still
  draws as a flat plate. Key `(OFF, OFF, OFF)` and pass `until=f0` so it pops to `(1, 1, OFF)`
  and then ramps.
- **`show()` overwrites scale keys.** Don't use `show` and `scale_keys` on the same object; nest
  one empty inside the other.
- **`cut` bakes the object's transform** and assumes its parent is at the origin (or a pivot at
  `z = 0`) at build time.
- **Two keys on one frame** keep only the last one.
- **`cup` must not be `cut`.** `cut` fills every open boundary, which caps the cup's top.

### Build and preview

```sh
blender -b --factory-startup --python tools/pbr3d/blender/sand_zooms.py
blender -b --factory-startup --python tools/pbr3d/blender/sand_sections.py -- 5   # one section

cd tools/pbr3d
cargo run --release --example page_sheet -- assets/sand_tap.glb 4 /tmp/tap.png
```

`page_sheet` renders the left pane exactly as the TUI does (tags included) at 30% and 80% of
each beat, one row per beat. Look at every sheet before writing text: check that nothing is
cropped, tags don't pile up, nothing is hidden behind a cut face, and things that should be gone
really are.

## Step 2: the beat text

One `Beat` per step:

```rust
Beat::new("caption: the one-line claim of this step", BEAT_MS)
    .note(
        "what: two or three sentences on what is happening, in plain words",
        "look: what to watch for in the picture, naming colours and parts",
    )
    .detail(
        "why: why this step matters (kept for other views; the panel doesn't show it)",
        &["key number with its source", "key number", "key number"],
    ),
```

- The panel shows the step counter, caption, what, look and key numbers. The type shrinks to fit;
  below a floor size the last key numbers drop first, so put the most important first.
- **`look` must match the scene.** Write it after seeing the sheet: "the grey fume rising into
  the hood", not "fume is captured".
- **Numbers carry their source** (USGS, patent number, report name) and agree with the tags.
  Don't add figures that no source on the page backs.
- Tests require every field to be non-empty.

## Step 3: wire it up

```rust
// zoom.rs: one builder per zoom
static TAP: OnceLock<pbr3d::scene_gltf::Scene> = OnceLock::new();
pub fn tap() -> Box<dyn Scene> {
    Box::new(Page { cell: &TAP, glb: include_bytes!(".../assets/sand_tap.glb"), beats: TAP_BEATS, zooms: &[] })
}

// overview.rs: the overview lists the zooms by key
const ZOOMS: &[Zoom] = &[Zoom { key: 'c', label: "tapping the metal", build: zoom::tap }, ...];

// sections.rs: the section! macro fills in cell and GLB path by number
pub const SECTIONS: [fn() -> Box<dyn Scene>; 10] = [section!(1, SEC1_BEATS), ...];
```

The `Node` in `<page>/mod.rs` points at `overview::build` and `sections::SECTIONS`. Section
titles in the menu come from the page's `# ` headings, in order.

## Step 4: check

```sh
cd tui
cargo build --release
cargo test --release <page>
fl diagrams            # open the page, press a-d and the section numbers
```

The tests check beat counts, that every beat is explained, and that every beat renders a
picture with enough pixels off the background (this catches an empty scene, a camera pointing
at nothing, or a GLB that fails to parse).

If the page plays pre-rendered clips (`clips: true`, `FL_H264=1`), changed scenes make the
clips stale. See `docs/diagram-clips.md`.

## Size

SAND's 15 GLBs are about 8 MB, all embedded in `fl`. `finish` exports with
`export_force_sampling=True` at every frame (24 per second), which dominates file size for
long, animated scenes; the overview alone is 2.4 MB. Keep scenes lean: reuse materials, use
low vertex counts for small parts (`verts=12` tubes, `segs=12` balls), and prefer switching a
group on/off over many separately animated objects.

## Checklist for a new page

1. Write `<page>_overview.py`, `<page>_zooms.py` and `<page>_sections.py`, importing the helpers.
2. Export, then run `page_sheet` on every GLB and fix framing, tags and cut faces.
3. Write the beats against the sheets: caption, what, look, why, key numbers with sources.
4. Wire `Page`s into `overview.rs` (with `ZOOMS`), `zoom.rs` and `sections.rs`; keep the
   beat-count tests matching the scripts.
5. `cargo test --release <page>`, then look at it in `fl diagrams`.
