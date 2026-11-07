#!/usr/bin/env bash
# Render the polysilicon bell-jar clip: PNG frames -> mp4 + gif.
# Usage: tools/poly3d/run.sh [frames]   (default 240 = 8 s at 30 fps)
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
frames="${1:-240}"
out="$here/out"
fps=30

cd "$here"
cargo build --release --quiet
rm -rf "$out/frames"
./target/release/poly3d --frames "$frames" --out "$out/frames"

ffmpeg -y -loglevel error -framerate "$fps" -i "$out/frames/%04d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart \
  "$out/poly_bell_jar.mp4"

ffmpeg -y -loglevel error -framerate "$fps" -i "$out/frames/%04d.png" \
  -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=256[p];[b][p]paletteuse=dither=none" \
  "$out/poly_bell_jar.gif"

# The README copy: 640 px wide at 12 fps, about 2 MB, to stay light in the repo. The TUI cannot be
# recorded for this scene (`just gifs` only captures text), so this clip is the doc GIF.
docs_gif="$here/../../docs/screens/diagrams_bell_jar.gif"
ffmpeg -y -loglevel error -framerate "$fps" -i "$out/frames/%04d.png" \
  -vf "fps=12,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" \
  "$docs_gif"

echo "mp4: $out/poly_bell_jar.mp4"
echo "gif: $out/poly_bell_jar.gif"
echo "docs: $docs_gif"
