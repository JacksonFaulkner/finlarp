#!/usr/bin/env bash
# Concurrency benchmark: run N full builds at once (Blender bake, contact sheet, montages) and
# time the whole batch. Each build works in its own scratch copy of the Blender scripts, so the
# scene files don't collide. Every step runs through observe.py (tools/pbr3d/runs.jsonl), and a
# summary line is appended too.
#
#   tools/pbr3d/bench_concurrent.sh <n> <scene:beats> [<scene:beats> ...]
#
# The n builds take the scenes round-robin, so `5 logic_die_overview:7 microbump_overview:7` runs
# three logic dies and two microbumps at once. Needs the page_sheet example built (cargo build).
# Env: BLENDER (default as context.sh), PBR3D_WHERE (label, default local), PBR3D_SAMPLES.
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <n> <scene:beats> [...]" >&2
  exit 2
fi
N=$1
shift
ROOT=$(git rev-parse --show-toplevel)
OBS="$ROOT/tools/pbr3d/observe.py"
SHEET="$ROOT/tools/pbr3d/target/release/examples/page_sheet"
export PBR3D_WHERE=${PBR3D_WHERE:-local}
export PBR3D_SAMPLES=${PBR3D_SAMPLES:-0.1,0.3,0.5,0.7,0.9}
if [ -z "${BLENDER:-}" ]; then
  if [ -x /snap/blender/current/blender ]; then BLENDER=/snap/blender/current/blender; else BLENDER=blender; fi
fi
[ -x "$SHEET" ] || { echo "build page_sheet first: cargo build --release --example page_sheet" >&2; exit 1; }

SPECS=("$@")
WORK=$(mktemp -d)
echo "bench: $N concurrent builds on $PBR3D_WHERE, work $WORK, blender '$("$BLENDER" --version | head -1)'"

build_one() { # build_one <index> <scene:beats>
  local i=$1 spec=$2 scene beats dir
  scene=${spec%%:*}
  beats=${spec##*:}
  dir="$WORK/build$i"
  mkdir -p "$dir/tools/pbr3d/blender" "$dir/tools/pbr3d/assets" "$dir/montage"
  cp "$ROOT"/tools/pbr3d/blender/*.py "$dir/tools/pbr3d/blender/"
  local tag="bench:n$N:$scene#$i"
  local t0 t1 t2
  t0=$(date +%s.%N)
  python3 "$OBS" --label "$tag:bake" --out "$dir/tools/pbr3d/assets/$scene.glb" \
    --meta "scene=$scene" --meta "build=$i" --meta "concurrent=$N" -- \
    "$BLENDER" -b --factory-startup --python "$dir/tools/pbr3d/blender/$scene.py" \
    >"$dir/bake.log" 2>&1
  t1=$(date +%s.%N)
  PBR3D_MONTAGE_DIR="$dir/montage" python3 "$OBS" --label "$tag:sheet" \
    --out "$dir/sheet.png" --meta "scene=$scene" --meta "build=$i" --meta "concurrent=$N" \
    --meta "samples=$PBR3D_SAMPLES" -- \
    "$SHEET" "$dir/tools/pbr3d/assets/$scene.glb" "$beats" "$dir/sheet.png" >/dev/null
  t2=$(date +%s.%N)
  echo "$t0 $t1 $t2" >"$dir/times"
}

pids=()
for ((i = 1; i <= N; i++)); do
  spec=${SPECS[$(( (i - 1) % ${#SPECS[@]} ))]}
  build_one "$i" "$spec" &
  pids+=($!)
done
fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done

# Summary: wall time of the whole batch (first start to last finish) and each build's span.
python3 - "$WORK" "$N" "$PBR3D_WHERE" "$ROOT/tools/pbr3d/runs.jsonl" "$fail" <<'PY'
import json, os, sys, datetime as dt
work, n, where, log, fail = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
starts, ends, spans = [], [], []
for i in range(1, n + 1):
    p = os.path.join(work, f"build{i}", "times")
    if not os.path.exists(p):
        continue
    t0, t1, t2 = map(float, open(p).read().split())
    starts.append(t0); ends.append(t2)
    spans.append({"build": i, "bake_s": round(t1 - t0, 3), "sheet_s": round(t2 - t1, 3), "span_s": round(t2 - t0, 3)})
total = round(max(ends) - min(starts), 3) if ends else None
rec = {
    "label": f"bench:n{n}:total",
    "where": where,
    "started": dt.datetime.fromtimestamp(min(starts), dt.timezone.utc).isoformat(timespec="milliseconds") if starts else None,
    "wall_s": total,
    "concurrent": n,
    "failed": fail == "1",
    "builds": spans,
}
print(f"batch wall {total}s for {n} concurrent builds on {where}")
for s in spans:
    print(f"  build {s['build']}: bake {s['bake_s']}s  sheet+montage {s['sheet_s']}s  span {s['span_s']}s")
os.makedirs(os.path.dirname(log), exist_ok=True)
with open(log, "a") as f:
    f.write(json.dumps(rec, sort_keys=True) + "\n")
PY
echo "scratch kept at $WORK"
exit "$fail"
