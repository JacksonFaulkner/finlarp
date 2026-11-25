"""Fortinet: security subscriptions pass product sales as the largest line, then product revenue
jumps in the latest quarter year over year; EMEA is the largest region, and margins hold near 80%
gross and around 30% operating."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "FTNT"
NAMES = {"Technical Support": "Technical Support and Other"}
GEO = {"Europe Middle East and Africa": "EMEA", "Asia Pacific": "Asia Pacific and Japan"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Security Subscription", "Product"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Product")]),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
