"""S&P Global: Ratings revenue grows fastest and Ratings earns the largest share of segment operating
income, and quarterly operating margin rises from about 40% to near 50%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "SPGI"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Ratings", "Market Intelligence"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Ratings")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Ratings")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
