"""Duke Energy: electric utilities are almost all revenue while gas grows fastest, operating margin
climbs year after year, and free cash flow stays below zero in most years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "DUK"
NAMES = {"Electric Utilitiesand": "Electric Utilities & Infra.",
         "Gas Utilitiesand": "Gas Utilities & Infra."}


def _below(b: dict | None, what: str) -> dict | None:
    """Tag a bars beat with how many of its points are below zero."""
    if not b:
        return None
    neg = sum(1 for _, v in b["points"] if v < 0)
    if neg:
        b["tags"] = [{"i": len(b["points"]) // 2, "u": 0.8, "text": f"below zero in {neg} of {len(b['points'])} {what}"}]
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Electric", "Gas"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        _below(story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")), "years"),
    ]
    return [story.scene(d.name("financials"), beats)]
