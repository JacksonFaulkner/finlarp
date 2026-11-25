"""Cadence: product and maintenance carry revenue while technology services nearly double, China is
flat over three years and then nearly doubles in a year, and operating margin dips in one quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "CDNS"
NAMES = {"Productandmaintenance": "Product and maintenance"}
GEO = {"CN": "China", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Product", "Technology"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "China"])),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q, tags=[growth(geo_q, "China")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
