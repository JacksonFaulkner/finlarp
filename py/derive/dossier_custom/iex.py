"""IDEX: Health and Science Technologies is the largest segment and carries the growth, also in
the latest quarter on a year earlier, while Fluid and Metering is flat and the operating margin stays
around 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "IEX"
ABBR = {"Health and Science Technologies": "Health & Science", "Fluid and Metering Technologies": "Fluid & Metering"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Health and Science", "Fluid and Metering"]), ABBR)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Health and Science")], ABBR)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
