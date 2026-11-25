"""AMC Entertainment: admissions and food and beverage make up most revenue in both US and
international markets, revenue dips in FY2024 and edges up in FY2025, every first quarter is the
seasonal low, and the operating margin climbs from deep losses toward breakeven while free cash
flow stays negative every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_total, bars_year_ago, growth, seg_tags, shaped,
                                         share, tagged)

TICKER = "AMC"
NAMES = {"Us Markets": "US Markets"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    qseg = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=[share(prod, "Admission", u=0.55), share(prod, "Food", u=0.85)]),
        qseg and story.towers("Revenue by segment, same quarter a year apart", qseg,
                              tags=[growth(qseg, "US", u=0.6), growth(qseg, "International", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
