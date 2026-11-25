"""Strategy (MicroStrategy): in the software business, subscription revenue more than doubles while
product support and licenses shrink, gross margin slips from ~70% to the mid-60s, and annual free
cash flow turns negative. (Operating margin is left out: bitcoin fair-value swings dwarf revenue.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "MSTR"
NAMES = {"Subscription and Circulation": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    fcf = story.bars("Free cash flow", "$M", d.points("Free cash flow, annual"))
    beats = [
        prod and story.towers("Software revenue by type", prod, tags=seg_tags(prod, ["Subscription", "License"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Subscription"), growth(prod_q, "Product Support", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
