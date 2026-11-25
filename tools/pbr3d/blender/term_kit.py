"""Term overviews from a JSON spec: one Blender scene per x-diagrams term, no per-term code.

    blender -b --factory-startup --python tools/pbr3d/blender/term_kit.py -- SPEC.json [SPEC.json ...]

Each spec is one term (or a list). It writes tools/pbr3d/assets/term_<SLUG>.glb, the picture for
that term's Terms-tab overview. Beats are 8 s, the same rule as every diagram page
(docs/diagram-pages.md). Units are millimetres, Y up, the same as the other scenes.

Spec shape (all coordinates are [x, y, z] in mm, Y up, origin at the scene centre):

{
  "slug": "TRM_CAS_LATENCY",
  "beats": [
    {
      "caption": "one-line claim of this step (for the reader, not written into the scene)",
      "boxes":  [{"name": "bank", "lo": [-200, -120, -40], "hi": [200, 120, 0], "mat": "steel"}],
      "arrows": [{"from": [-300, 0, 0], "to": [-180, 0, 0], "mat": "accent"}],
      "tags":   [{"text": "column read: 11 cycles", "at": [0, 150, 0]}],
      "show":   ["bank"]            // optional: names of boxes/arrows visible this beat, default all
    }
  ],
  "camera": [[0, 0, 0, 900, 0.0, 0.1]]   // optional per beat: [tx, ty, tz, distance, yaw, pitch]
}

Materials: steel, charge, quartz, dim, accent, glow, alarm. Keep each beat to one idea. A box or
arrow that is not in a beat's "show" list (or any beat's list when "show" is absent in that beat)
is hidden for that beat. Tags are 2-4 per beat, each under about 35 characters.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sand_overview import beat, box, empty, label, show  # noqa: E402
from sand_zooms import camera, finish, start  # noqa: E402

BEAT_SECS = 8

def _mat(m, key):
    """Map a spec material name to a material from the shared dict, falling back to steel."""
    if key in m:
        return m[key]
    return m.get("steel")


def _extra_mats(m):
    """Extra colours the spec can name, added once per scene."""
    import bpy

    def mk(name, col, emit=None, strength=2.0, rough=0.6):
        mt = bpy.data.materials.new(name)
        mt.use_nodes = True
        bsdf = mt.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*col, 1.0)
        bsdf.inputs["Roughness"].default_value = rough
        if emit:
            bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
            bsdf.inputs["Emission Strength"].default_value = strength
        return mt

    m.setdefault("dim", mk("term_dim", (0.42, 0.44, 0.50), rough=0.8))
    m.setdefault("accent", mk("term_accent", (0.95, 0.75, 0.30), emit=(0.95, 0.75, 0.30), strength=2.5))
    m.setdefault("glow", mk("term_glow", (0.60, 0.85, 1.0), emit=(0.60, 0.85, 1.0), strength=3.0))
    m.setdefault("alarm", mk("term_alarm", (0.95, 0.35, 0.30), emit=(0.95, 0.35, 0.30), strength=2.0))


def _arrow(name, a, b, mat, parent, thick=2.0):
    """A straight stick from a to b plus a small head cube at b (boxes only, no curves)."""
    lo = [min(a[i], b[i]) - thick for i in range(3)]
    hi = [max(a[i], b[i]) + thick for i in range(3)]
    return box(name, lo, hi, mat, parent=parent)


def build_spec(spec):
    slug = spec["slug"]
    beats = spec["beats"]
    n = len(beats)
    m, root = start(slug, n, page="term")
    _extra_mats(m)

    names_seen = {}
    for i, b in enumerate(beats):
        # each part sits under a wrapper empty: show() sets scale, which would erase the box size
        for item in b.get("boxes", []):
            name = item["name"]
            if name in names_seen:
                continue
            wrap = empty(name, root)
            box(name, item["lo"], item["hi"], _mat(m, item.get("mat", "steel")), parent=wrap)
            names_seen[name] = (wrap, [])
        for item in b.get("arrows", []):
            name = item.get("name") or f"arrow{len(names_seen)}_{i}"
            if name in names_seen:
                continue
            wrap = empty(name, root)
            _arrow(name, item["from"], item["to"], _mat(m, item.get("mat", "accent")), wrap)
            names_seen[name] = (wrap, [])

    # visibility: every named part is on for each beat listed in its "show" (default: its beat)
    for i, b in enumerate(beats):
        shown = set(b["show"]) if "show" in b else set(
            [x["name"] for x in b.get("boxes", [])]
            + [x.get("name") or "" for x in b.get("arrows", [])]
        )
        for name, (obj, ivals) in names_seen.items():
            if name in shown:
                ivals.append(beat(i)[0])
    for name, (obj, ivals) in names_seen.items():
        show(obj, ivals)

    for i, b in enumerate(beats):
        for t in b.get("tags", []):
            label(t["text"], tuple(t["at"]), root, beat(i))

    if "camera" in spec:
        poses = [(tuple(p[:3]), p[3], p[4], p[5]) for p in spec["camera"]]
    else:
        poses = [((0.0, 0.0, 0.0), 900.0, 0.0, 0.1)] * n
    camera(root, poses)
    return m, root


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ok = bad = 0
    for path in argv:
        with open(path) as f:
            data = json.load(f)
        for spec in data if isinstance(data, list) else [data]:
            if "script" in spec:  # hand-built scene (blender/terms/*.py) owns this GLB
                print("skip", spec["slug"], "->", spec["script"])
                continue
            try:
                build_spec(spec)
                finish(spec["slug"], page="term")
                ok += 1
            except Exception as e:  # one bad spec does not stop the batch
                bad += 1
                print("FAILED", spec.get("slug"), e, file=sys.stderr)
    print(f"term_kit: {ok} built, {bad} failed")


if __name__ == "__main__":
    main()
