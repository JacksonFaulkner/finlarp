"""DXC: annual revenue shrinks every year since FY2022, led by GIS while Insurance grows; in the latest
quarter GIS operating income falls by more than half and the quarterly operating margin drops to its
low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_low, growth, seg_tags, shaped, tagged)

TICKER = "DXC"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    qoi = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True))
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["GIS", "Insurance"])),
        qoi and story.towers("Segment operating income, same quarter a year apart", qoi, tags=[growth(qoi, "GIS")]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_low(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
