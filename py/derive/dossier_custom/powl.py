"""Powell Industries: annual revenue more than doubles in four years with electricity and commercial
customers growing fastest, and the operating margin climbs from about zero to about a fifth of
revenue as gross margin widens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, seg_tags, shaped, short, tagged

TICKER = "POWL"
NAMES = {"Oil and Gas Service": "Oil and Gas", "Light Rail Traction Power Customer": "Light Rail Traction Power",
         "Other Customers": "Other customers"}


def specs(d: Data) -> list[dict]:
    mkt = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, annual")
    beats = [
        mkt and story.towers("Revenue by end market", mkt, tags=short(seg_tags(mkt, ["Electricity", "Commercial"]),
                                                                         {"Commercial and Other Industrial": "Commercial"})),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_first_to_last(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
