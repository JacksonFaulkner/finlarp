"""USA Rare Earth: pre-revenue until its first sales show up in 2026, while the quarterly cash burn
grows many times over against the same quarters of 2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import tagged

TICKER = "USAR"


def _m(v: float) -> str:
    return f"-${-v:.1f}M" if v < 0 else f"${v:.1f}M"


def specs(d: Data) -> list[dict]:
    # Only four quarters are reported (Q1-Q2 of 2025 and of 2026), so the bars compare the same
    # quarters a year apart. Margins (-600% to -18,000%) are left out; the annual series have two
    # points only.
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, quarterly")
    burn = None
    if len(fcf) >= 3 and fcf[-3][1] < 0:
        (pa, a), (pb, b) = fcf[-3], fcf[-1]
        burn = {"i": -1, "u": 0.75, "text": f"burn {pa} {_m(-a)} -> {pb} {_m(-b)}"}
    first = next((i for i, (_, v) in enumerate(q) if v > 0), None)
    beats = [
        first is not None and tagged(story.bars("Quarterly revenue (reported quarters)", "$M", q),
                                     {"i": first, "u": 0.75, "text": f"first revenue {q[first][0]} {_m(q[first][1])}"}),
        tagged(story.bars("Free cash flow (reported quarters)", "$M", fcf), burn),
    ]
    return [story.scene(d.name("financials"), beats)]
