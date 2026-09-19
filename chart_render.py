"""Renders a multi-series % change overlay chart to a PNG.

Reads JSON on stdin: { "series": [ { "symbol": str, "closes": [float, ...] }, ... ],
"width_px": int, "height_px": int }. Writes { "path": str } on stdout — the PNG is
written to a temp file (caller is responsible for cleanup once displayed).

Kept as a separate script from config.py so importing matplotlib (a real
startup cost) only happens when a chart is actually opened, not on every quote/
screen call.
"""

from __future__ import annotations

import json
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Stable per-slot colors, matching colors.lua's SERIES table so a symbol's
# line color is the same whether you're looking at its tile border or here.
SERIES_COLORS = ["#7aa2f7", "#e6c265", "#c678dd", "#56b6c2"]

BG = "#1a1b26"
FG = "#c0caf5"
GRID = "#3b3f52"


def render(series: list[dict], width_px: int, height_px: int) -> str:
    dpi = 100
    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, s in enumerate(series):
        closes = s["closes"]
        base = closes[0]
        pct = [(c / base - 1) * 100 if base else 0 for c in closes]
        color = SERIES_COLORS[i % len(SERIES_COLORS)]
        ax.plot(pct, label=s["symbol"], color=color, linewidth=1.8)

    ax.axhline(0, color=GRID, linewidth=0.8, linestyle="--")
    ax.grid(True, color=GRID, linewidth=0.5, alpha=0.6)
    ax.tick_params(colors=FG, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.set_ylabel("% change", color=FG, fontsize=9)
    legend = ax.legend(loc="upper left", facecolor=BG, edgecolor=GRID, fontsize=9)
    for text in legend.get_texts():
        text.set_color(FG)

    fig.tight_layout()
    out_path = tempfile.NamedTemporaryFile(
        prefix="security_spread_chart_", suffix=".png", delete=False
    ).name
    fig.savefig(out_path, facecolor=BG)
    plt.close(fig)
    return out_path


def main() -> None:
    payload = json.loads(sys.stdin.read())
    path = render(payload["series"], payload["width_px"], payload["height_px"])
    print(json.dumps({"path": path}))


if __name__ == "__main__":
    main()
