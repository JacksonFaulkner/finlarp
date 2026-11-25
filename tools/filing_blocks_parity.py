"""Rust vs Python filing_blocks: parse every cached filing both ways and diff.

    cargo build --release --manifest-path tui/Cargo.toml
    uv run --project py python tools/filing_blocks_parity.py   (from the repo root)

G1 / G2 override the globs (default: data/docs/*/*.htm and *.html).
"""
import json, subprocess, sys, time, glob, os, gzip
sys.path.insert(0, "py")
from sources import filing_blocks as fb
files = sorted(set(glob.glob(os.environ.get("G1","data/docs/*/*.htm")) + glob.glob(os.environ.get("G2","data/docs/*/*.html"))))
ok = bad = 0; pyt = rst = 0.0
for f in files:
    url = "https://www.sec.gov/x/" + os.path.basename(f)
    h = open(f, errors="ignore").read()
    t = time.time()
    try: want = fb.document(h, {"url": url})
    except Exception as e: want = f"ERR {e}"
    pyt += time.time() - t
    t = time.time()
    r = subprocess.run(["tui/target/release/fl", "filing-blocks", f, url], capture_output=True, text=True)
    rst += time.time() - t
    got = json.loads(r.stdout) if r.returncode == 0 else f"ERR {r.stderr.strip()}"
    want = json.loads(json.dumps(want))
    if got == want: ok += 1; continue
    bad += 1
    print("DIFF", f)
    if isinstance(got, str) or isinstance(want, str):
        print("  ", str(got)[:200], "|", str(want)[:200]); continue
    gb, wb = got["blocks"], want["blocks"]
    for i, (a, b) in enumerate(zip(gb, wb)):
        if a != b:
            print("   block", i, "\n   rust:", json.dumps(a)[:400], "\n   py:  ", json.dumps(b)[:400]); break
    else:
        print("   len", len(gb), len(wb))
print(f"{ok} same, {bad} differ; python {pyt:.2f}s, rust (incl. process start) {rst:.2f}s, {len(files)} files")
