"""Mastercard: value-added services and solutions grow faster than the payment network and take a
larger share of revenue, international markets stay the bigger half, and operating margin rises to
about 60%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "MA"
NAMES = {"Value Added Services": "Value-added services"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by line", prod, tags=seg_tags(prod, ["Payment Network", "Value-added"])),
        prod and story.towers("Revenue share by line", prod, pct=True, tags=pct_tags(prod, ["Value-added"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Value-added")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
