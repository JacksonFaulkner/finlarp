# poly3d: performance rules for 3D diagram scenes

Every frame is rendered on the CPU, on the TUI's main thread, then kitty-encoded. While
H/J/K/L is held the camera changes every tick, so nothing is cached: each tick pays a full
render + encode. Budget: **30 ms per frame** (`MOTION_FRAME` in `tui/src/screens/diagrams.rs`)
at the half-resolution motion size (~1200x660). Today the slowest scene is ~17 ms.

## Measure before and after any scene change

```sh
# every orbitable scene, slowest first, yawing like a held key
cargo test --release --manifest-path tui/Cargo.toml bench_3d -- --ignored --nocapture
# (or: just bench-3d)  knobs: FL_BENCH_FILTER="TOP METAL"  FL_BENCH_SIZE=2400x1320
#                             FL_BENCH_FRAMES=12  FL_BENCH_TOP=40  FL_BENCH_JSON=out.jsonl
```

`FL_BENCH_JSON` writes one row per scene; diff two runs to prove a change helped.

The deterministic guard runs with the normal test suite (counters, not timings):

```sh
cargo test --manifest-path tui/Cargo.toml scenes_stay_inside_frame_budget
```

It fails if any beat of any orbitable scene exceeds the limits at the top of
`tui/src/screens/diagrams_bench.rs` (triangles, fill pixels per screen pixel, overdraw,
dot and line pixels). Don't raise a limit to make a new scene pass; fix the scene.

## Reading the bench columns

Timing comes from `poly3d::prof` (`src/prof.rs`), recorded at the shared chokepoints
(`rasterize`, `Canvas::fill_tri`, `Canvas::line`/`overlay`, `stage::dot`, `to_image`).
Use it in any ad-hoc test with `prof::begin()` ... render ... `prof::take()`.

| column  | high means                                   | fix |
|---------|----------------------------------------------|-----|
| build   | the scene's `solids()` code is slow          | hoist work out of per-frame code, fewer allocations |
| sort    | too many triangles                           | see `tris` |
| raster  | large or many triangles; check `px_tested`   | fewer/smaller tris, skip hidden parts |
| overlay | glass lines, dots, labels, callouts          | fewer segments, fewer particles |
| image   | float canvas to RGBA (scales with pixels)    | nothing scene-side |
| enc     | kitty zlib+base64 (scales with pixels)       | nothing scene-side |
| tris    | triangles submitted                          | lower `seg` on `push_tube`/`push_sphere`; 8-12 segments is plenty for thin wires |
| ovrdr   | pixel writes / screen pixels                 | >3: many stacked hidden layers; drop interior geometry nobody sees |
| linepx / dotpx | alpha line and dot pixels             | fewer meridians/rings in glass, fewer particles |

## Rules of thumb when building a scene

- Triangle count matters less than **pixels touched**. A few thousand triangles is fine;
  what kills frames is overdraw and huge triangles.
- Arrays of identical parts (bumps, cells, vias): use low `seg` (6-8) for spheres/tubes
  smaller than ~20 px on screen, and don't emit parts fully hidden inside others.
- Don't build geometry for alpha 0 or strength 0 parts; return early.
- Keep per-frame work in `solids()`/`overlay()` to geometry: no big `Vec` rebuilds of
  static tables, no string formatting per triangle.
- `fill_tri` walks only each row's covered span (not the bounding box). Keep it that way:
  the bbox walk was 50x slower on long thin wires (TOP METAL went 118 ms -> 17 ms).
  `span_fill_matches_bounding_box_fill` in `src/lib.rs` pins the output pixel-for-pixel.
