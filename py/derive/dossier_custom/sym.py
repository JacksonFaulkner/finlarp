"""Symbotic: systems are nearly all revenue while services grow faster, non-US revenue jumps from
almost nothing in a year, and gross and operating margin both widen, operating margin turning positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped, short

TICKER = "SYM"
NAMES = {"Non Us": "Non-US"}

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by type", prod,
                              tags=short(seg_tags(prod, ["Systems", "Operation Services"]),
                                         {"Operation Services": "Op. services"})),
        geo_q and story.towers("Same quarter a year apart, by region", geo_q,
                               tags=[growth(geo_q, "Non-US", u=0.85), growth(geo_q, "US", u=0.5)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Gross margin", "%", gm), bars_swing(gm, "%")),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
