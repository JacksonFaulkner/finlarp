"""Ameren: Union Electric leads a FY2025 revenue rise and Ameren Transmission grows every year, but
Union Electric is lower in the latest quarter than a year earlier; quarterly revenue and margin swing
with the seasons, and free cash flow stays negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "AEE"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Union Electric", "Ameren Transmission"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Union Electric")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
