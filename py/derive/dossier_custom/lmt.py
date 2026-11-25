"""Lockheed Martin: Missiles and Fire Control grows fastest while Aeronautics, the largest segment,
earns less each year; Asia Pacific revenue grows while the Middle East shrinks, and two quarters
carry operating margins near 4%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "LMT"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Missiles", "Aeronautics"])),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Aeronautics")]),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Asia Pacific", "Middle East"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
