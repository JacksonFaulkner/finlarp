#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
out="$root/artifacts/memory-model-showcase"
frames="$out/frames"
mkdir -p "$out"

cargo run --release --manifest-path "$root/tools/poly3d/Cargo.toml" --bin memory_showcase -- "$frames" 1920 1080
python3 "$root/tools/poly3d/memory_showcase_audio.py" "$out/sound-design.wav"
python3 "$root/tools/poly3d/memory_showcase_captions.py"

cat > "$out/voiceover.srt" <<'EOF'
1
00:00:00,000 --> 00:00:02,000
A DRAM cell stores one bit.

2
00:00:02,000 --> 00:00:04,000
First, the capacitor stores charge.

3
00:00:04,000 --> 00:00:06,000
The word line turns on the access transistor.

4
00:00:06,000 --> 00:00:08,000
Charge flows to the bit line; the chip senses a one.

5
00:00:08,000 --> 00:00:10,000
The sense amp restores it, ready for the next read.
EOF

cd "$out"
ffmpeg -y -loglevel error \
  -framerate 30 -i "captioned/%04d.png" \
  -i "sound-design.wav" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -af "volume=8dB,alimiter=limit=0.85" \
  -c:a aac -b:a 192k -shortest -movflags +faststart \
  "one-bit-first-10-seconds.mp4"

mkdir -p "$root/video/public/memory-showcase"
cp "$out/one-bit-first-10-seconds.mp4" "$root/video/public/memory-showcase/one-bit-first-10-seconds.mp4"

echo "Video: $out/one-bit-first-10-seconds.mp4"
echo "Remotion Studio asset: $root/video/public/memory-showcase/one-bit-first-10-seconds.mp4"
