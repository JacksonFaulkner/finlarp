"""Rigetti: annual revenue shrinks for three years and gross margin falls with it, quarterly revenue
picks up in 2026 from its Q1 2025 low, and the company burns cash every quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_total, tagged

TICKER = "RGTI"


def _m(v: float) -> str:
    """Small $M values with one decimal (story.money rounds $1.5M to $2M)."""
    return f"-${-v:.1f}M" if v < 0 else f"${v:.1f}M"


def _span(points: list[list], i: int) -> dict:
    (pa, a), (pb, b) = points[i], points[-1]
    return {"i": -1, "u": 0.75, "text": f"{pa} {_m(a)} -> {pb} {_m(b)}"}


def specs(d: Data) -> list[dict]:
    # Product towers are left out: the FY2024 product split has a third line that the FY2025 split
    # drops, so held-constant members would understate FY2024. Operating margin (-500% to -1,500%
    # on a few $M of revenue) is left out too; free cash flow tells the loss story.
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    fcf_q = d.points("Free cash flow, quarterly")
    fcf = d.points("Free cash flow, annual")
    low = min(fcf_q, key=lambda p: p[1]) if fcf_q else None
    beats = [
        rev and tagged(story.bars("Annual revenue", "$M", rev), _span(rev, max(range(len(rev)), key=lambda i: rev[i][1]))),
        q and tagged(story.bars("Quarterly revenue", "$M", q), _span(q, min(range(len(q)), key=lambda i: q[i][1]))),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_peak_to_last(gm, "%")),
        low and tagged(story.bars("Free cash flow, quarterly", "$M", fcf_q),
                       {"i": fcf_q.index(low), "u": 0.75, "text": f"{low[0]} burn {_m(-low[1])}"}),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
