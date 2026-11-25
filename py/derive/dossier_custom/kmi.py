"""Kinder Morgan: natural gas pipelines carry the growth while products pipelines shrink, natural gas
sales climb in FY2025, and the operating margin settles near 31% after FY2021-22."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "KMI"
NAMES = {"Co 2": "CO2", "Feebasedservices": "Fee-based services"}


def _span(pts: list[list], unit: str = "%") -> dict | None:
    if len(pts) < 2:
        return None
    return {"i": -1, "u": 0.8, "text": f"{pts[0][0]} {pts[0][1]:.0f}{unit} -> {pts[-1][0]} {pts[-1][1]:.0f}{unit}"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    om = d.points("Operating margin, annual")
    om_bars = story.bars("Operating margin, annual", "%", om)
    if om_bars and (t := _span(om)):
        om_bars["tags"], om_bars["auto_tags"] = [t], False
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Natural Gas Pipelines", "Products Pipelines"])),
        prod and story.towers("Revenue by product / service", prod,
                              tags=[growth(prod, "Natural Gas Sales", u=0.55), growth(prod, "Product Other", u=0.75)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        om_bars,
    ]
    return [story.scene(d.name("financials"), beats)]
