"""Super Micro: FY2026 US revenue more than doubles and other countries grow fastest, quarterly revenue
more than doubles in Q2'26, gross margin dips then jumps in the latest quarter, and annual free
cash flow swings deeply negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped

TICKER = "SMCI"

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def _m(v: float) -> str:
    a = abs(v)
    return ("-" if v < 0 else "") + (f"${a / 1e3:.1f}B" if a >= 1e3 else f"${a:,.0f}M")


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Other Countries"])),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        _tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), _fcf_last(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]


def _fcf_last(pts: list[list]) -> dict | None:
    if len(pts) < 2:
        return None
    (pa, a), (pb, b) = pts[-2], pts[-1]
    return {"i": -1, "u": 0.75, "text": f"{pa} {_m(a)} -> {pb} {_m(b)}"}
