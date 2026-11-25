"""Rubrik: subscription revenue more than doubles in two years and is nearly all revenue, every
region grows, operating losses narrow from about half of revenue, and free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped

TICKER = "RBRK"
NAMES = {"Subscription": "Subscription", "Product and Service Other": "Other"}


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue: subscription vs other", prod, tags=seg_tags(prod, ["Subscription"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Americas", "EMEA"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Asia Pacific", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Operating margin (loss)", "%", om), bars_swing(om)),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
