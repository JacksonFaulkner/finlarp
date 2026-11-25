"""V2X: revenue grows every year with the Army and Navy as the largest customers, Air Force revenue
doubles in the latest quarter against a year earlier, and the operating margin stays in low single
digits while free cash flow comes off its FY2024 high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_year_ago, growth, seg_tags,
                                         shaped, tagged)

TICKER = "VVX"
CUST = {"Other Customers": "Other customers"}


def specs(d: Data) -> list[dict]:
    cust = shaped(d.history(("MajorCustomersAxis",)), CUST)
    qcust = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2), CUST)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        cust and story.towers("Revenue by customer", cust, tags=seg_tags(cust, ["Navy", "Army"])),
        qcust and story.towers("Revenue by customer, same quarter a year apart", qcust,
                               tags=[growth(qcust, "Air Force", u=0.6), growth(qcust, "Army", u=0.85)]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
