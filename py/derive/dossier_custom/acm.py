"""AECOM: the Americas are about three quarters of revenue, but in the latest quarter Americas revenue
falls by about a fifth against a year earlier, led by guaranteed-maximum-price and cost-reimbursable
work, and gross and operating margin both turn negative in that quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_year_ago, drop, growth, seg_tags, shaped, share, tagged

TICKER = "ACM"
NAMES = {"Guaranteed Maximum Price": "Guaranteed max. price", "Cost Reimbursable": "Cost reimbursable",
         "Fixed Price": "Fixed price"}


def specs(d: Data) -> list[dict]:
    seg = shaped(drop(d.history(("StatementBusinessSegmentsAxis",)), "AECOM Capital"))
    seg_q = shaped(drop(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), "AECOM Capital"))
    price_q = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[share(seg, "Americas"), growth(seg, "International", u=0.85)]),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Americas"), growth(seg_q, "International", u=0.85)]),
        price_q and story.towers("Contract types, same quarter a year apart", price_q,
                                 tags=seg_tags(price_q, ["Guaranteed", "Cost"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
