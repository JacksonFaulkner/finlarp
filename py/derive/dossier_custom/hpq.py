"""HP Inc.: Personal Systems grows while Printing shrinks, yet Printing still earns the larger share
of segment operating income; the latest quarter's Personal Systems jump comes with a lower gross
margin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share, without

TICKER = "HPQ"


def specs(d: Data) -> list[dict]:
    seg = shaped(without(d.history(("StatementBusinessSegmentsAxis",)), "Corporate"))
    oi = shaped(without(d.history(("StatementBusinessSegmentsAxis",), oi=True), "Corporate"))
    seg_q = shaped(without(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), "Corporate"))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Personal Systems", "Printing"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "Printing")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Personal Systems")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
