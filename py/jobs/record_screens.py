"""Record animated GIFs of the TUI screens for the docs.

Each screen runs in a detached tmux session at a fixed size. After every key in a script, the pane is captured with
colours (`capture-pane -e`), the ANSI is painted into a PNG with a monospace font, and the frames are written as a GIF.
A single character is typed literally and gets a short frame; a named key (Enter, Down) or a bare `J`-style jump gets
a longer one, so typing a query reads as typing.
Only screens that read public data are listed. The portfolio, notes, chat and godel screens show personal data;
chart and candles show portfolio history and mock bars, so none of those are recorded.

    uv run --with pillow python -m jobs.record_screens [--only dossier] [--out docs/screens]

Needs tmux and the release binary (`just build`). Reads the same DuckDB file as `fl`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BINARY = ROOT / "tui" / "target" / "release" / "fl"
FONT = "/System/Library/Fonts/Menlo.ttc"
# Menlo has no braille, arrows or CJK; these cover what the screens draw. Tried in order for any glyph Menlo lacks.
FALLBACKS = [
    "/System/Library/Fonts/Apple Braille.ttf",
    "/System/Library/Fonts/Apple Symbols.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
]
FONT_SIZE = 15
# A private-use code point no font maps, so it draws the font's "missing glyph" box.
MISSING = "\U0010fffd"
COLS, ROWS = 130, 38
BG = (17, 19, 24)
FG = (214, 218, 226)
PAD = 12

SGR = re.compile(r"\x1b\[([0-9;]*)m")

# xterm's 16 base colours; the rest of the 256 palette is computed.
BASE16 = [
    (0, 0, 0), (205, 49, 49), (13, 188, 121), (229, 229, 16), (36, 114, 200), (188, 63, 188), (17, 168, 205),
    (229, 229, 229), (102, 102, 102), (241, 76, 76), (35, 209, 139), (245, 245, 67), (59, 142, 234),
    (214, 112, 214), (41, 184, 219), (255, 255, 255),
]


@dataclass
class Spec:
    name: str
    args: list[str] = field(default_factory=list)
    # Keys sent before the first frame, to reach the view the GIF starts on.
    setup: list[str] = field(default_factory=list)
    # Keys sent one at a time; a frame is captured after each. "wait:N" captures N seconds of frames instead,
    # for animated scenes that play on their own.
    keys: list[str] = field(default_factory=list)


SPECS = [
    # The provenance demo: Revenue & segments, then `i` on a row to see the formula and its source.
    # Starts past "Latest", which lists tweets; the GIF stays on filings and SEC data.
    Spec("dossier", ["dossier", "NVDA"], setup=["J", "J"], keys=["j", "i", "i", "j", "j", "i"]),
    Spec("canslim", ["canslim", "NVDA"], keys=["j", "j", "j", "j"]),
    Spec("search", ["search"], keys=list("NVDA guidance") + ["Enter"]),
    Spec("universe", ["universe"], keys=["j", "j", "j", "Enter"]),
    Spec("events", ["events"], keys=["l", "l", "j", "l"]),
    Spec("earnings", ["earnings"], keys=["j", "j", "j", "j"]),
    # Polysilicon: its overview plays on its own, then zoom "a" plays the close-up.
    Spec("diagrams", ["diagrams"], keys=["l", "Enter", "Enter", "wait:6", "a", "wait:6"]),
    # The other diagram tabs, opened by their number and left to play.
    Spec("diagrams_chip", ["diagrams"], keys=["2", "wait:6"]),
    Spec("diagrams_packaging", ["diagrams"], keys=["3", "wait:6"]),
    Spec("diagrams_fiber", ["diagrams"], keys=["4", "wait:6"]),
    Spec("diagrams_power", ["diagrams"], keys=["5", "wait:6"]),
    Spec("diagrams_network", ["diagrams"], keys=["6", "wait:6"]),
]


def color(code: int) -> tuple[int, int, int]:
    if code < 16:
        return BASE16[code]
    if code < 232:
        n = code - 16
        steps = [0, 95, 135, 175, 215, 255]
        return steps[n // 36], steps[n // 6 % 6], steps[n % 6]
    v = 8 + (code - 232) * 10
    return v, v, v


def parse_line(line: str) -> list[tuple[str, tuple, tuple, bool, bool]]:
    """Cells of one captured line: (char, fg, bg, bold, reverse). Wide characters are followed by an empty cell."""
    cells: list[tuple[str, tuple, tuple, bool, bool]] = []
    fg: tuple | None = None
    bg: tuple | None = None
    bold = False
    reverse = False
    pos = 0
    for m in list(SGR.finditer(line)) + [None]:
        text = line[pos : m.start() if m else len(line)]
        for ch in text:
            cells.append((ch, fg or FG, bg or BG, bold, reverse))
            if unicodedata.east_asian_width(ch) in ("W", "F"):
                cells.append(("", fg or FG, bg or BG, bold, reverse))
        if m is None:
            break
        pos = m.end()
        params = [int(p) for p in m.group(1).split(";") if p] or [0]
        i = 0
        while i < len(params):
            p = params[i]
            if p == 0:
                fg, bg, bold, reverse = None, None, False, False
            elif p == 1:
                bold = True
            elif p == 22:
                bold = False
            elif p == 7:
                reverse = True
            elif p == 27:
                reverse = False
            elif p == 39:
                fg = None
            elif p == 49:
                bg = None
            elif 30 <= p <= 37:
                fg = BASE16[p - 30]
            elif 90 <= p <= 97:
                fg = BASE16[p - 90 + 8]
            elif 40 <= p <= 47:
                bg = BASE16[p - 40]
            elif 100 <= p <= 107:
                bg = BASE16[p - 100 + 8]
            elif p in (38, 48) and i + 1 < len(params):
                if params[i + 1] == 5 and i + 2 < len(params):
                    rgb = color(params[i + 2])
                    i += 2
                elif params[i + 1] == 2 and i + 4 < len(params):
                    rgb = tuple(params[i + 2 : i + 5])
                    i += 4
                else:
                    rgb = None
                if rgb is not None:
                    if p == 38:
                        fg = rgb
                    else:
                        bg = rgb
            i += 1
    return cells


class Painter:
    def __init__(self) -> None:
        # Menlo.ttc: face 0 regular, face 1 bold.
        self.fonts = {False: ImageFont.truetype(FONT, FONT_SIZE, index=0), True: ImageFont.truetype(FONT, FONT_SIZE, index=1)}
        self.fallbacks = [ImageFont.truetype(path, FONT_SIZE) for path in FALLBACKS if Path(path).exists()]
        self.cw = round(self.fonts[False].getlength("M"))
        ascent, descent = self.fonts[False].getmetrics()
        self.ch = ascent + descent + 2
        self.glyphs: dict[tuple[str, bool], ImageFont.FreeTypeFont] = {}

    def font_for(self, ch: str, bold: bool) -> ImageFont.FreeTypeFont:
        key = (ch, bold)
        if key not in self.glyphs:
            primary = self.fonts[bold]
            missing = primary.getbbox(MISSING)
            found = primary
            if primary.getbbox(ch) == missing:
                found = next((f for f in self.fallbacks if f.getbbox(ch) != f.getbbox(MISSING)), primary)
            self.glyphs[key] = found
        return self.glyphs[key]

    def paint(self, ansi: str) -> Image.Image:
        lines = ansi.split("\n")[:ROWS]
        w = COLS * self.cw + 2 * PAD
        h = ROWS * self.ch + 2 * PAD
        img = Image.new("RGB", (w, h), BG)
        draw = ImageDraw.Draw(img)
        for y, line in enumerate(lines):
            x = 0
            for ch, fg, bg, bold, reverse in parse_line(line)[:COLS]:
                if reverse:
                    fg, bg = bg, fg
                px, py = PAD + x * self.cw, PAD + y * self.ch
                if bg != BG:
                    draw.rectangle([px, py, px + self.cw - 1, py + self.ch - 1], fill=bg)
                if ch and ch != " ":
                    draw.text((px, py + 1), ch, font=self.font_for(ch, bold), fill=fg)
                x += 1
        return img


def tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True).stdout


def start(spec: Spec) -> str:
    session = f"gif-{spec.name}-{uuid.uuid4().hex[:6]}"
    cmd = " ".join([f"'{BINARY}'", *(f"'{a}'" for a in spec.args)])
    tmux("new-session", "-d", "-s", session, "-x", str(COLS), "-y", str(ROWS), cmd)
    return session


def capture(session: str) -> str:
    return tmux("capture-pane", "-p", "-e", "-t", session)


def record(spec: Spec, painter: Painter, out: Path) -> None:
    session = start(spec)
    frames: list[tuple[Image.Image, int]] = []
    try:
        time.sleep(2.5)
        for key in spec.setup:
            tmux("send-keys", "-t", session, key)
            time.sleep(0.6)
        frames.append((painter.paint(capture(session)), 1800))
        for key in spec.keys:
            if key.startswith("wait:"):
                t0 = time.monotonic()
                last = t0
                while time.monotonic() - t0 < float(key.removeprefix("wait:")):
                    time.sleep(0.12)
                    now = time.monotonic()
                    frames.append((painter.paint(capture(session)), round((now - last) * 1000)))
                    last = now
                continue
            typed = len(key) == 1
            tmux("send-keys", "-t", session, *(["-l"] if typed else []), key)
            time.sleep(0.25 if typed else 0.7)
            frames.append((painter.paint(capture(session)), 250 if typed else 900))
        frames.append((frames[-1][0], 2000))
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)

    first, *rest = [f for f, _ in frames]
    durations = [d for _, d in frames]
    out.parent.mkdir(parents=True, exist_ok=True)
    first.save(
        out,
        save_all=True,
        append_images=rest,
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"{out} ({len(frames)} frames)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", help="record only this screen (repeatable)")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "screens")
    args = ap.parse_args()
    if not BINARY.exists():
        raise SystemExit(f"{BINARY} missing: run `just build` first")
    painter = Painter()
    for spec in SPECS:
        if args.only and spec.name not in args.only:
            continue
        record(spec, painter, args.out / f"{spec.name}.gif")


if __name__ == "__main__":
    main()
