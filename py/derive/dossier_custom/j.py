"""Jacobs: Infrastructure & Advanced Facilities drives a jump in revenue on a year earlier, mostly in
the US, while gross margin slides quarter after quarter and the operating margin dips to a loss in
Q2'26."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, shaped, short, tagged

TICKER = "J"
NAMES = {"Australiaand": "Australia and New Zealand", "Middle Eastand": "Middle East and Africa"}


def specs(d: Data) -> list[dict]:
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    beats = [
        seg_q and story.towers("Segments, same quarter a year apart", seg_q, tags=short([growth(seg_q, "Infrastructure")],
                                                                                {"Infrastructure Advanced Facilities": "Infrastructure"})),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=[growth(geo_q, "US")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin", "%", gm), bars_year_ago(gm, "%")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
