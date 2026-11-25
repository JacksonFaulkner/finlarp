"""Hewlett Packard Enterprise: Server revenue grows while its operating income falls, Networking
jumps in FY2025, routing nearly quadruples in a year-apart quarter, and the operating margin dips
below zero before recovering."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "HPE"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Server", "Networking"])),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Server", "Networking"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Routing", "Server"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
