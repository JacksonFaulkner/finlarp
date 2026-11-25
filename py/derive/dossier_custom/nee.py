"""NextEra Energy: the filings carry no segment revenue split here, so the story is the totals:
annual revenue rises over five years, and operating margin jumps in FY2023 and holds near a third."""
from __future__ import annotations

from derive.dossier_custom import Data, story

TICKER = "NEE"


def specs(d: Data) -> list[dict]:
    beats = [
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        story.bars("Net margin, annual", "%", d.points("Net margin, annual")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
    ]
    return [story.scene(d.name("financials"), beats)]
