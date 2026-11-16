#!/usr/bin/env bash
# Headless context build: bake Blender scenes, render their contact sheets, log every step.
# Runs on the worker or on the Mac (docs: the worker is a producer for local agents).
#
#   tools/pbr3d/context.sh <git-ref|local> <scene:beats> [<scene:beats> ...]
#
# For each scene: bakes tools/pbr3d/blender/<scene>.py to assets/<scene>.glb with Blender (in
# parallel), renders its contact sheet with pbr3d (one row per beat). Every bake and sheet runs
# through observe.py, which appends a record (wall/CPU time, exit, git sha, host, output hashes)
# to tools/pbr3d/runs.jsonl. If CONTEXT_BUCKET is set, the GLBs, sheets and this run's records are
# also uploaded to s3://$CONTEXT_BUCKET/<sha>/ and runs/. The scene script name must match its GLB
# name. `local` skips the git fetch and builds the working tree as it is.
#
# Env: CONTEXT_BUCKET (optional), BLENDER (default: the snap on the worker, else `blender` on PATH),
# PBR3D_WHERE (label for the records, default "local"; the worker sets "worker").
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: $0 <git-ref|local> <scene:beats> [...]" >&2
  exit 2
fi
REF=$1
shift
export PATH="${HOME:-/root}/.cargo/bin:$PATH"
export PBR3D_WHERE=${PBR3D_WHERE:-local}
export PBR3D_SAMPLES=${PBR3D_SAMPLES:-0.1,0.3,0.5,0.7,0.9}
if [ -z "${BLENDER:-}" ]; then
  if [ -x /snap/blender/current/blender ]; then BLENDER=/snap/blender/current/blender; else BLENDER=blender; fi
fi

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
OBS="$ROOT/tools/pbr3d/observe.py"
REPO_LOG="$ROOT/tools/pbr3d/runs.jsonl"

if [ "$REF" != "local" ]; then
  git fetch --depth 1 origin "$REF"
  git checkout -q -f FETCH_HEAD
fi
SHA=$(git rev-parse --short=12 HEAD)
[ "$REF" = "local" ] && SHA="$SHA-local"
OUT=$(mktemp -d)
RUNLOG="$OUT/runs.jsonl"
export PBR3D_RUNLOG="$RUNLOG"
BLENDER_VERSION=$("$BLENDER" --version 2>/dev/null | head -1 || echo unknown)
echo "build $SHA where=$PBR3D_WHERE blender='$BLENDER_VERSION' work=$OUT"
T_ALL0=$(date +%s)

# 1. Bake every scene in parallel, each through observe.py.
pids=()
scenes=()
for spec in "$@"; do
  scene=${spec%%:*}
  scenes+=("$spec")
  python3 "$OBS" --label "bake:$scene" --out "tools/pbr3d/assets/$scene.glb" \
    --meta "scene=$scene" --meta "blender=$BLENDER_VERSION" -- \
    "$BLENDER" -b --factory-startup --python "tools/pbr3d/blender/$scene.py" \
    >"$OUT/$scene.bake.log" 2>&1 &
  pids+=($!)
done
bake_fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || bake_fail=1
done
if [ "$bake_fail" -ne 0 ]; then
  echo "bake failed; logs in $OUT" >&2
  grep -l Traceback "$OUT"/*.bake.log >&2 || true
  exit 1
fi

# 2. Contact sheets with pbr3d, one observed step each.
cd "$ROOT/tools/pbr3d"
python3 "$OBS" --label "build:page_sheet" --meta "where=$PBR3D_WHERE" -- \
  cargo build --release --example page_sheet >/dev/null 2>&1
for spec in "${scenes[@]}"; do
  scene=${spec%%:*}
  beats=${spec##*:}
  frames_env=""
  if [ "${PBR3D_FRAMES:-0}" = "1" ]; then
    mkdir -p "$OUT/frames/$scene"
    frames_env="$OUT/frames/$scene"
  fi
  mkdir -p "$OUT/montage/$scene"
  PBR3D_FRAMES_DIR="$frames_env" PBR3D_MONTAGE_DIR="$OUT/montage/$scene" \
    python3 "$OBS" --label "sheet:$scene" --out "$OUT/${scene}_sheet.png" \
    --meta "scene=$scene" --meta "beats=$beats" --meta "samples=$PBR3D_SAMPLES" -- \
    ./target/release/examples/page_sheet "assets/$scene.glb" "$beats" "$OUT/${scene}_sheet.png" >/dev/null
done
cd "$ROOT"
T_ALL=$(( $(date +%s) - T_ALL0 ))
echo "total wall ${T_ALL}s for $# scene(s)"

# 3. Keep the records in the repo log, and upload them when there is a bucket.
cat "$RUNLOG" >>"$REPO_LOG"
if [ -n "${CONTEXT_BUCKET:-}" ]; then
  BUCKET=$CONTEXT_BUCKET
  manifest="$OUT/manifest.txt"
  : >"$manifest"
  for spec in "${scenes[@]}"; do
    scene=${spec%%:*}
    cp "tools/pbr3d/assets/$scene.glb" "$OUT/$scene.glb"
    for f in "$scene.glb" "${scene}_sheet.png"; do
      aws s3 cp "$OUT/$f" "s3://$BUCKET/$SHA/$f" --only-show-errors
      echo "s3://$BUCKET/$SHA/$f" >>"$manifest"
    done
  done
  aws s3 sync "$OUT/montage" "s3://$BUCKET/$SHA/montage/" --only-show-errors
  if [ -d "$OUT/frames" ]; then
    aws s3 sync "$OUT/frames" "s3://$BUCKET/$SHA/frames/" --only-show-errors
  fi
  aws s3 cp "$manifest" "s3://$BUCKET/$SHA/manifest.txt" --only-show-errors
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  aws s3 cp "$RUNLOG" "s3://$BUCKET/runs/$SHA-$stamp.jsonl" --only-show-errors
  cat "$manifest"
  echo "uploaded to s3://$BUCKET/$SHA/ and runs/$SHA-$stamp.jsonl"
else
  echo "no CONTEXT_BUCKET: outputs stay in tools/pbr3d/assets and $OUT (montages in $OUT/montage)"
fi
echo "done: $SHA"
