"""Quanta Services: Electric Power carries the growth, a year-apart quarter shows it accelerating,
fixed-price contracts take a larger share of the work, and the operating margin stays in single
digits while revenue climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "PWR"
NAMES = {"Fixed Price": "Fixed price", "Unit Price": "Unit price", "Cost Plus": "Cost plus"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    price = shaped(d.history(("ContractWithCustomerBasisOfPricingAxis",)), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Electric", "Underground"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Electric")]),
        price and story.towers("Revenue share by contract pricing", price, pct=True, tags=pct_tags(price, ["Fixed price"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
