"""Ciena: Networking Platforms (optical networking above all) drives a rebound after a down year,
the latest quarter is up sharply on a year earlier with the Americas taking most of it, and the
quarterly operating margin goes from low single digits to the high teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "CIEN"
NAMES = {"Platform Softwareand": "Platform Software and Services",
         "Blue Planet Automation Softwareand": "Blue Planet Automation Software and Services"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Networking Platforms"])),
        prod_q and story.towers("By product, same quarter a year apart", prod_q, tags=[growth(prod_q, "Optical")]),
        geo_q and story.towers("By region, same quarter a year apart", geo_q, tags=[growth(geo_q, "Americas")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
