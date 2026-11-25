"""Build template scenes from spec files (see tpl_kit.py), many per Blender process.

    blender -b --factory-startup --python tools/pbr3d/blender/tpl_run.py -- SPEC.json [SPEC.json ...]

A spec file holds one spec or a list of them; each writes tools/pbr3d/assets/tpl/<name>.glb.
A failing spec is reported and skipped so one bad ticker does not stop a batch.
"""

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tpl_kit  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ok = bad = 0
for path in argv:
    with open(path) as f:
        data = json.load(f)
    for spec in data if isinstance(data, list) else [data]:
        try:
            tpl_kit.build(spec)
            tpl_kit.finish(spec["name"])
            ok += 1
        except Exception:
            bad += 1
            print("FAILED", spec.get("name"), file=sys.stderr)
            traceback.print_exc()
print(f"tpl_run: {ok} built, {bad} failed")
