"""Talen Energy: electricity sales and capacity revenue both jump in a year, the PJM segment carries
nearly all of it, and quarterly revenue and operating margin swing hard from quarter to quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share, short, yoy

TICKER = "TLN"
NAMES = {"Electricity Sales": "Electricity sales and ancillary", "Operating Revenue Capacity": "Capacity",
         "Physical Electricity Sales Bilateral": "Bilateral electricity sales", "Product and Service Other": "Other"}
SHORT = {"Electricity sales and ancillary": "Electricity sales"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    beats = [
        prod and story.towers("Revenue by product", prod, tags=short(seg_tags(prod, ["Electricity", "Capacity"]), SHORT)),
        seg and story.towers("Revenue by segment", seg, tags=[share(seg, "PJM")]),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=short([growth(prod_q, "Capacity"),
                                                                                  yoy(prod_q, "Electricity", u=0.5)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
