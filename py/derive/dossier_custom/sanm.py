"""Sanmina: from FY2026 Q1 quarterly revenue jumps to well above its old run rate, carried by the
IMS segment, the Americas and the communications, cloud and AI end market, and the operating
margin climbs back from its FY2026 Q1 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, shaped, short, tagged

TICKER = "SANM"
NAMES = {"IMS Third Party": "IMS", "CPS Third Party": "CPS"}


def specs(d: Data) -> list[dict]:
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    mkt_q = shaped(d.history(("EndMarketAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg_q and story.towers("Segment revenue, same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "IMS", u=0.55), growth(seg_q, "CPS", u=0.8)]),
        mkt_q and story.towers("End markets, same quarter a year apart", mkt_q,
                               tags=short([growth(mkt_q, "Communications")],
                                          {"Communications Networks and Cloud and AI Infrastructure": "Comms, cloud, AI"})),
        geo_q and story.towers("Region, same quarter a year apart", geo_q, tags=[growth(geo_q, "Americas")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
