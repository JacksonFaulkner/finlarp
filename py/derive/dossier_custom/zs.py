"""Zscaler: no segment split is tagged, so the story is the Financials series: quarterly revenue
climbs every quarter at a steady ~77% gross margin, the operating loss narrows, and free cash flow
grows each year."""
from __future__ import annotations

from derive.dossier_custom import Data, story

TICKER = "ZS"


def specs(d: Data) -> list[dict]:
    q = d.points("Quarterly revenue")
    rev = story.bars("Quarterly revenue", "$M", q, tags=[story.bars_year_ago(q)] if len(q) >= 5 else None)
    if rev and rev.get("tags"):
        rev["auto_tags"] = False
    beats = [
        rev,
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
