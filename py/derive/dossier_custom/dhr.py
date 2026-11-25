"""Danaher: revenue is nearly flat across three segments, Life Sciences operating income falls by
more than half while Diagnostics earns the most, and the latest quarter shows Diagnostics revenue
well above a year earlier."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "DHR"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Diagnostics"])),
        oi and story.towers("Operating income by segment", oi,
                            tags=[growth(oi, "Life Sciences"), share(oi, "Diagnostics", u=0.85)]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Diagnostics")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
