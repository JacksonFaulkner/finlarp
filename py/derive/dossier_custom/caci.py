"""CACI: the Department of Defense is over half of revenue and grows fastest in dollars, fixed-price
work gains share over cost-plus, and the operating margin edges up quarter by quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, share, short

TICKER = "CACI"
PRICING = {"Cost Plus Fee": "Cost-plus", "Fixed Price": "Fixed price", "Time and Materials": "Time and materials"}


def specs(d: Data) -> list[dict]:
    cust = shaped(d.history(("MajorCustomersAxis",)))
    price = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",)), PRICING)
    price_q = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",), cadence="quarterly", n=2), PRICING)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        cust and story.towers("Revenue by customer", cust, tags=[*short([share(cust, "Department of Defense", u=0.6)], {"Department of Defense": "DoD"}),
                                                                *short([growth(cust, "Federal Civilian", u=0.8)], {"Federal Civilian Agencies": "Federal civilian"})]),
        price and story.towers("Revenue share by contract type", price, pct=True,
                               tags=pct_tags(price, ["Fixed price", "Cost-plus"])),
        price_q and story.towers("Contract type, same quarter a year apart", price_q,
                                 tags=seg_tags(price_q, ["Fixed price", "Cost-plus"])),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Domestic")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
