"""NetScout: service and product revenue barely move over three years, then product jumps in the
latest quarter as US revenue climbs; quarterly revenue peaks every December quarter, and the annual
operating margin falls to a deep loss in FY2025 before swinging back to a profit."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "NTCT"
GEO = {"Rest of World": "Rest of world"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    qprod = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    qgeo = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Service", "Product"])),
        qprod and story.towers("Revenue by type, same quarter a year apart", qprod, tags=[growth(qprod, "Product")]),
        qgeo and story.towers("Revenue by region, same quarter a year apart", qgeo, tags=[growth(qgeo, "US")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
