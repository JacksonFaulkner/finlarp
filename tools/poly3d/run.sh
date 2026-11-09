#!/usr/bin/env bash
# Render a poly3d clip: PNG frames -> mp4 + gif.
# Usage: tools/poly3d/run.sh [frames] [scene]   (defaults: 240 = 8 s at 30 fps, scene bell)
#   scene bell: the polysilicon bell-jar clip, also refreshes the docs GIF
#   scene cell: the 1T1C DRAM cell clip, writes out/cell_frames and out/poly_cell.{mp4,gif} only
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
frames="${1:-240}"
scene="${2:-bell}"
out="$here/out"
fps=30

case "$scene" in
  bell) frames_dir="$out/frames"; stem="poly_bell_jar" ;;
  cell) frames_dir="$out/cell_frames"; stem="poly_cell" ;;
  *) echo "usage: run.sh [frames] [bell|cell]" >&2; exit 2 ;;
esac

cd "$here"
cargo build --release --quiet
rm -rf "$frames_dir"
./target/release/poly3d --scene "$scene" --frames "$frames" --out "$frames_dir"

ffmpeg -y -loglevel error -framerate "$fps" -i "$frames_dir/%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart \
  "$out/$stem.mp4"

ffmpeg -y -loglevel error -framerate "$fps" -i "$frames_dir/%04d.png" \
  -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=256[p];[b][p]paletteuse=dither=none" \
  "$out/$stem.gif"

echo "mp4: $out/$stem.mp4"
echo "gif: $out/$stem.gif"

# The README copy: 640 px wide at 12 fps, about 2 MB, to stay light in the repo. The TUI cannot be
# recorded for this scene (`just gifs` only captures text), so this clip is the doc GIF.
# Only the bell clip goes there; the cell clip never overwrites it.
if [ "$scene" = bell ]; then
  docs_gif="$here/../../docs/screens/diagrams_bell_jar.gif"
  ffmpeg -y -loglevel error -framerate "$fps" -i "$frames_dir/%04d.png" \
    -vf "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
    "$docs_gif"
  echo "docs: $docs_gif"
fi
