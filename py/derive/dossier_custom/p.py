"""Everpure (fka Pure Storage): product and service revenue both grow, with product and non-US
revenue jumping in the latest quarter against a year earlier, gross margin holds near 70%, and the
operating margin stays thin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "P"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Product", "Service"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Product")]),
        geo_q and story.towers("US vs non-US, same quarter a year apart", geo_q, tags=[growth(geo_q, "Non-US")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
