"""MACOM: telecom more than doubles over three years, data center rebounds to nearly double on a
year earlier, China and Hong Kong becomes the largest region in the latest quarter, and operating
margin nearly triples from its Q1'25 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "MTSI"
NAMES = {"Industrial Defense": "Industrial and defense", "Chinaand Hong Kong": "China and Hong Kong",
         "Asia Pacificexcluding China": "Asia Pacific excluding China"}


def specs(d: Data) -> list[dict]:
    mkt = shaped(d.history(("EndMarketAxis",)), NAMES)
    mkt_q = shaped(d.history(("EndMarketAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        mkt and story.towers("Revenue by end market", mkt, tags=seg_tags(mkt, ["Telecom", "Data Center"])),
        mkt_q and story.towers("End markets, same quarter a year apart", mkt_q, tags=[growth(mkt_q, "Data Center")]),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=[growth(geo_q, "China")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
