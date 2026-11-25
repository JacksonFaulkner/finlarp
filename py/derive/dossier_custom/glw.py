"""Corning: Optical Communications grows into the largest share of revenue and keeps growing in the
latest quarter, solar and polysilicon nearly double, and operating margin climbs from single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "GLW"
NAMES = {"Optical Communications": "Optical Communications", "Specialty Materials": "Specialty Materials",
         "Display Products": "Display", "Automotive": "Automotive", "Life Science": "Life Science",
         "Polycrystalline Silicon and Solar": "Polysilicon and Solar", "Polycrystalline Silicon": "Polysilicon",
         "Electronics Glass": "Electronics Glass and Optics", "Product and Service Other": "Other"}


def _of_revenue(tags: list[dict]) -> list[dict]:
    """pct_tags text without the period range ('<name> a% -> b% of revenue'), to fit the frame."""
    return [{**t, "text": t["text"].split(" (")[0] + " of revenue"} for t in tags]


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by business", prod, tags=seg_tags(prod, ["Optical"])),
        prod and story.towers("Revenue share by business", prod, pct=True, tags=_of_revenue(pct_tags(prod, ["Optical"]))),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Optical", u=0.6), growth(prod_q, "Polysilicon", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
