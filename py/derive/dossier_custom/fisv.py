"""Fiserv: Merchant and Financial Solutions split revenue almost evenly and both earn less operating
income in FY2025 than FY2024, product revenue falls in the latest quarter versus a year earlier,
and operating margin drops from the low 30s to under 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "FISV"

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def _peak_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    """Peak -> latest for a % series that has come off its high."""
    if len(pts) < 2:
        return None
    hi = max(range(len(pts)), key=lambda i: pts[i][1])
    if hi == len(pts) - 1:
        return None
    return {"i": -1, "u": u, "text": f"{pts[hi][0]} {pts[hi][1]:.1f}% -> {pts[-1][0]} {pts[-1][1]:.1f}%"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Merchant", "Financial"])),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Merchant", "Financial"])),
        prod_q and story.towers("Same quarter a year apart, by type", prod_q,
                                tags=[growth(prod_q, "Product", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Operating margin", "%", om), _peak_to_last(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
