"""CrowdStrike: subscription revenue is nearly all of it and keeps growing, every region grows,
revenue rises every quarter at a mid-70s gross margin, yet GAAP operating margin stays at or below
zero in all but one quarter while free cash flow keeps climbing."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "CRWD"
NAMES = {"Subscription and Circulation": "Subscription"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    om = story.bars("Operating margin", "%", d.points("Operating margin, quarterly"))
    if om:
        below = sum(1 for _, v in om["points"] if v < 0)
        om["tags"] = [{"i": 2, "u": 0.8, "text": f"below zero in {below} of {len(om['points'])} quarters"}]
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Subscription"])),
        geo_q and story.towers("By region, same quarter a year apart", geo_q, tags=seg_tags(geo_q, ["US", "EMEA"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        om,
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
