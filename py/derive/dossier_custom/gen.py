"""Gen Digital: Trust Based Solutions more than doubles in a year and adds to segment operating
income, the Americas take the gain, revenue steps up from Q1'26, and gross margin slips."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped, short

TICKER = "GEN"
SHORT = {"Trust Based Solutions": "Trust Based", "Cyber Safety Platform": "Cyber Safety"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Trust Based", "Cyber Safety"]), SHORT)),
        oi and story.towers("Operating income by segment", oi, tags=short(seg_tags(oi, ["Trust Based", "Cyber Safety"]), SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Americas"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
