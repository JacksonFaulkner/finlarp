"""Dell: the Infrastructure Solutions Group passes Client Solutions in revenue and carries most of
the operating income, its quarter nearly doubles in a year, and quarterly revenue and operating
margin climb with it."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "DELL"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Infrastructure", "Client"])),
        oi and story.towers("Operating income by segment", oi,
                            tags=[share(oi, "Infrastructure"), growth(oi, "Client", u=0.8)]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Infrastructure")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
