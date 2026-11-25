"""Vertiv: the Americas segment drives the growth and earns most of the segment operating income,
EMEA's income dips in FY2025 and its year-apart quarter is flat, and quarterly revenue climbs past $3B."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "VRT"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment (region)", seg, tags=seg_tags(seg, ["Americas", "EMEA"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "Americas", u=0.55), growth(oi, "EMEA", u=0.8)]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Americas", "EMEA"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
