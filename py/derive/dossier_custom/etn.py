"""Eaton: Electrical Americas grows into the largest segment and earns most of the operating income,
Electrical Global jumps in the latest quarter, and the vehicle business shrinks."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "ETN"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Electrical Americas", "Vehicle"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Electrical Americas")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Electrical Global")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
