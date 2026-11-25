"""Trane Technologies: service grows faster than equipment, the Americas take a larger share while
Asia Pacific shrinks, and revenue and operating margin peak in the second and third quarters."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "TT"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue: product vs service", prod, tags=seg_tags(prod, ["Service", "Product"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=[{**t, "text": t["text"].split(" (")[0] + " of revenue"}
                                                                   for t in pct_tags(geo, ["Americas", "Asia Pacific"])]),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Americas", u=0.6),
                                                                        growth(geo_q, "EMEA", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
