"""Dexcom: revenue grows every year in the US and abroad, and quarterly gross and operating margins
widen, while annual free cash flow climbs past $1B."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "DXCM"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Non-US"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
