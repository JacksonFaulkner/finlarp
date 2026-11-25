"""Deere: equipment revenue falls two years running, large-ag (Production and Precision Agriculture)
operating income drops by more than half while Financial Services earns more, and the latest
quarter shows Construction and Forestry back above a year earlier."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "DE"
NAMES = {"Production and Precision": "Production & Precision Ag", "Small Agriculture": "Small Ag & Turf",
         "Construction and Forestry": "Construction & Forestry"}


def _usd(h: dict | None) -> dict | None:
    """Some filers tag USD with a custom unit id (UNIT_STANDARD_USD_...): show it as $M."""
    if h and h.get("unit", "").upper().startswith("UNIT_STANDARD_USD"):
        h["unit"] = "$M"
    return h


def specs(d: Data) -> list[dict]:
    seg = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",))), NAMES)
    oi = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",), oi=True)), NAMES)
    seg_q = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Production & Precision", "Construction"])),
        oi and story.towers("Operating income by segment", oi,
                            tags=[growth(oi, "Production & Precision"), growth(oi, "Financial Services", u=0.85)]),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Construction"), growth(seg_q, "Production & Precision", u=0.85)]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
