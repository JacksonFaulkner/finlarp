"""Microchip: revenue across every product line drops sharply in FY2025 and only partly recovers,
then the latest quarter is well above the same quarter a year earlier, and the quarterly operating
margin climbs back from a loss to above 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, short

TICKER = "MCHP"
SHORT = {"Mixed Signal Microcontrollers": "Microcontrollers"}  # tag text only; legend keeps the name


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=short(seg_tags(prod, ["Mixed Signal", "Analog"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=short([growth(prod_q, "Mixed Signal"), growth(prod_q, "Analog", u=0.4)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
