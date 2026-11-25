"""Alphabet: Search and YouTube (Google Services) still dwarf everything, but Google Cloud is the
growth: revenue nearly doubles in a year and its operating income goes from a rounding error to
a real business."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "GOOGL"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Google Cloud", "Google Services"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Google Cloud")]),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Google Cloud"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
