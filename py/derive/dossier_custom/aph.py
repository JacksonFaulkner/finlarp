"""Amphenol: Communications Solutions more than doubles and earns most of the operating income,
the latest quarter nearly doubles it again year on year, quarterly revenue more than doubles in
under two years, and operating margin climbs toward 30%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, total_of

TICKER = "APH"


def _usd(h: dict | None) -> dict | None:
    """Some filers tag USD with a custom unit id (UNIT_STANDARD_USD_...): show it as $M."""
    if h and h.get("unit", "").upper().startswith("UNIT_STANDARD_USD"):
        h["unit"] = "$M"
    return h


def _grown_share(h: dict, prefix: str) -> dict | None:
    """growth() tag with the latest share of the total appended, so one label says both."""
    t = growth(h, prefix)
    if t:
        t["text"] += f", {h['series'][t['s']][1][-1] / (total_of(h) or 1) * 100:.0f}% of the total"
    return t


def specs(d: Data) -> list[dict]:
    seg = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",))))
    oi = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",), oi=True)))
    seg_q = shaped(_usd(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Communications", "Harsh"])),
        oi and story.towers("Operating income by segment", oi, tags=[_grown_share(oi, "Communications")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Communications")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
