"""Intuitive Surgical: instruments and accessories are most of the revenue and keep growing, system
sales grow fastest, and free cash flow roughly doubles in FY2025 while one recent quarter's operating
margin dips."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "ISRG"
NAMES = {"Instrumentsand": "Instruments and Accessories", "Service": "Service"}


def _yoy(h: dict | None) -> dict | None:
    """The latest quarter and the same quarter a year earlier, from a quarterly history."""
    if not h:
        return None
    last = h["periods"][-1]
    mon, yr = last.split()
    prev = f"{mon} {int(yr) - 1:02d}"
    if prev not in h["periods"]:
        return None
    i = h["periods"].index(prev)
    return {**h, "periods": [prev, last], "series": [[n, [vs[i], vs[-1]]] for n, vs in h["series"]]}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = _yoy(shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=4), NAMES))
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["Instruments", "Systems"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Systems")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
