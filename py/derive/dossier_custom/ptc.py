"""PTC: lifecycle management (PLM) and CAD both grow while perpetual licences fade, Europe grows
fastest of the regions, operating margin rises from the low 20s to the mid 30s in FY2025, and free
cash flow climbs every year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, seg_tags, shaped, short, tagged, yoy

TICKER = "PTC"
NAMES = {"Product Lifecycle Management": "Product lifecycle management (PLM)",
         "Computer Aided Design": "Computer-aided design (CAD)"}
SHORT = {"Product lifecycle management (PLM)": "PLM", "Computer-aided design (CAD)": "CAD"}  # tag text only


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=short(seg_tags(prod, ["Product lifecycle", "Computer-aided"]),
                                                                    SHORT)),
        geo and story.towers("Revenue by region", geo, tags=[yoy(geo, "Europe", u=0.6), yoy(geo, "Americas", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
