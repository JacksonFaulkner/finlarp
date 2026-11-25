"""SAIC: Defense and Intelligence is about three quarters of revenue and annual revenue drifts lower,
fixed-price work loses share, but the latest quarter is up on a year earlier led by the DoD, with
the operating margin in a 6-9% band and free cash flow at a five-year high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, drop, pct_tags, seg_tags, shaped, short, tagged

TICKER = "SAIC"
PRICING = {"Cost Reimbursement": "Cost reimbursement", "Time and Materials": "Time and materials",
           "Fixed Price": "Fixed price"}


def specs(d: Data) -> list[dict]:
    seg = shaped(drop(d.history(("StatementBusinessSegmentsAxis",)), "Corporate"))
    price = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",)), PRICING)
    cust_q = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Defense", "Civilian"])),
        price and story.towers("Revenue share by contract type", price, pct=True,
                               tags=pct_tags(price, ["Fixed price", "Time and materials"])),
        cust_q and story.towers("Revenue by customer, same quarter a year apart", cust_q,
                                tags=short(seg_tags(cust_q, ["Department of Defense", "Other Federal"]),
                                           {"Department of Defense": "DoD", "Other Federal Government Agencies": "Other federal"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", om),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
