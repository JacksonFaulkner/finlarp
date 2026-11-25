"""Digital Realty: rental revenue grows steadily while fee income jumps, most of all in the latest
quarter against a year earlier, US revenue leads that quarter's growth, and quarterly revenue climbs
while the operating margin swings."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "DLR"
GEO = {"Non Us": "Outside the US"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Rental", "Fee Income"])),
        prod_q and story.towers("Revenue by type, same quarter a year apart", prod_q, tags=[growth(prod_q, "Fee Income")]),
        geo_q and story.towers("Revenue by region, same quarter a year apart", geo_q,
                               tags=seg_tags(geo_q, ["US", "Outside"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
