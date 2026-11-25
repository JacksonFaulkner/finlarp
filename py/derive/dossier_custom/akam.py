"""Akamai: security grows to over half of revenue while delivery shrinks, cloud infrastructure
is the fastest grower in the latest quarter, and operating margin falls from the low 20s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, seg_tags, shaped, short, tagged

TICKER = "AKAM"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ContractWithCustomerSalesChannelAxis",)))
    prod_q = shaped(d.history(("ContractWithCustomerSalesChannelAxis",), cadence="quarterly", n=2))
    om = d.points("Operating margin, annual")
    peak = max(om, key=lambda p: p[1]) if om else None
    om_tag = peak and peak != om[-1] and {"i": -1, "u": 0.75,
                                          "text": f"{peak[0]} {peak[1]:.1f}% -> {om[-1][0]} {om[-1][1]:.1f}%"}
    beats = [
        prod and story.towers("Revenue by solution", prod, tags=seg_tags(prod, ["Security", "Delivery"])),
        prod and story.towers("Revenue share by solution", prod, pct=True, tags=pct_tags(prod, ["Security"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Cloud Infrastructure"), growth(prod_q, "Delivery", u=0.5)],
                                           {"Cloud Infrastructure Services": "Cloud infrastructure",
                                            "Delivery and Other Cloud Applications": "Delivery and other"})),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), om_tag or bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
