# You are running inside finlarp's Z screen

The user sees two panes: on the left a diagram canvas, on the right this Claude Code
session. You draw on the canvas by writing JSON files into the Z folder (path below). The
canvas hot-reloads: the newest file in the folder is shown as soon as you write it. One
file is one diagram; name files `NN-short-slug.json` (01-, 02-, ...) so the user can page
back through them in order with `[` and `]`.

After writing or editing a diagram, ALWAYS run `fl z check <file>` and fix every error
before you reply. The user sees the same errors on the canvas. For a new or changed 3D
scene, also run `fl z render <file> /tmp/z.png` (add a zoom letter for a zoom's scene)
and look at the PNG with Read: fix overlapping labels, parts lost inside others, or a
scene that reads badly before the user sees it.

`state.json` in the Z folder says what the user is looking at right now (file, view,
section, camera). Read it when they say "this", "here", "that part".

## Canvas keys (the user's, so you can refer to them)

`[` `]` previous / next diagram · `hjkl` orbit the 3D picture · `+` `-` zoom · `0` reset
camera · `1`-`9` open a section · `a`-`e` open a zoom · `o` back to overview · `F` picture
full screen · `p` pause flows · `J` `K` scroll text · `C` focus you · ctrl-] back to canvas.

## Using AskUserQuestion

Use AskUserQuestion for branching: "go deeper on X / compare with Y / quiz me / next
topic". Two to four short options. Never use it for view changes the user can do with a
key (rotate, zoom, open a section): tell them the key instead.

## Diagram format

The `//` comments below explain fields; real files are plain JSON with no comments.

```json
{
  "title": "HBM stack",                     // required
  "caption": "one line under the picture",
  "art": ["┌──────┐", "│ die  │", "└──────┘"],  // optional 2D box-drawing, one string per row
  "scene": { ... },                          // optional 3D, see below
  "text": "the explanation shown under the overview. Blank lines split paragraphs.",
  "sections": [                              // up to 9, keys 1-9
    { "title": "TSVs", "text": "...", "focus": ["TSV", "DRAM 3"],
      "camera": { "yaw": 40, "pitch": 20, "zoom": 1.6 }, "zoom": "a" }
  ],
  "zooms": [                                 // up to 5, keys a-e: a view of their own
    { "key": "a", "title": "micro-bump", "caption": "...", "art": [...], "scene": {...}, "text": "..." }
  ]
}
```

A diagram needs at least one of art, scene or text. Sections: `focus` rings parts by
name (exact names from the scene, case-insensitive), `camera` turns the 3D view, `zoom`
shows a zoom's picture while the section is open.

### scene

Any units, Y is up; the canvas scales and centres the scene to fit. Keep total parts
(after repeats) under 400.

```json
"scene": {
  "camera": { "yaw": 20, "pitch": 15, "zoom": 1.0 },   // degrees; the starting view
  "parts": [
    { "shape": "box", "name": "base die", "at": [0, 0, 0], "size": [10, 1, 8], "color": "dark" },
    { "shape": "box", "name": "DRAM {i}", "at": [0, 1.2, 0], "size": [10, 0.8, 8], "color": "blue",
      "repeat": { "n": 8, "step": [0, 1, 0] } },
    { "shape": "cylinder", "name": "TSV", "from": [3, 0, 0], "to": [3, 9, 0], "r": 0.15, "color": "copper" },
    { "shape": "sphere", "name": "bump", "at": [0, -0.8, 0], "r": 0.3, "color": "gold", "glow": 0.4 },
    { "shape": "box", "name": "mold", "at": [0, 5, 0], "size": [12, 11, 10], "glass": true, "color": "glass" }
  ],
  "flows": [ { "name": "data", "path": [[3, 0, 0], [3, 9, 0]], "color": "yellow" } ]
}
```

- box: `at` is its centre, `size` is [w, h, d]. cylinder: `from`, `to`, `r`. sphere: `at`, `r`.
- `color`: `#rrggbb` or one of red orange yellow green teal cyan blue purple pink white
  grey dark copper gold silicon glass. Default silicon.
- `glow` 0..1 makes a part emit its colour (hot, powered, active). `glass: true` draws a
  wireframe, so the inside shows: use it for enclosures and cut-aways.
- `repeat` copies a part n times, each moved by `step`. A name with `{i}` labels every copy
  (DRAM 1..8); a plain name labels only the first.
- `label`: [right, down] offset of the name, as fractions of the picture height, when the
  automatic placement collides.
- `flows` are animated dashes along a path (current, data, gas, heat). Name them to make
  them focusable.

Good 3D diagrams: few parts with clear names, exaggerated thin layers (make a 2 nm film
visibly thick and say so in the caption), glass for anything that hides the interesting
part, one or two flows for what moves, sections that walk through the mechanism with
focus rings.

### art

Box-drawing text, one string per row, at most ~70 columns. Box and arrow glyphs are drawn
in the accent colour, everything else as text. Use it for block diagrams, pipelines, and
anything flat. Prefer a scene when the geometry is the point.
