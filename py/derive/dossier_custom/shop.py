"""Shopify: services revenue grows faster than subscriptions, revenue peaks every fourth quarter,
gross margin drifts down a few points, and free cash flow turns from negative to about $2B a year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "SHOP"
NAMES = {"Subscription and Circulation": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Service", "Subscription"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Service")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
