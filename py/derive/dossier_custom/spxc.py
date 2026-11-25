"""SPX Technologies: HVAC leads the growth with cooling its largest product line, Canada grows to
about four times its FY2023 revenue, quarterly revenue rises about a fifth year over year, and the
operating margin roughly holds in the mid-teens after climbing from single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, growth, shaped, tagged, without, yoy

TICKER = "SPXC"
# leading words of the filer's own product-line names (the full names run past the legend)
NAMES = {"Package and Process Cooling": "Package and Process Cooling Equipment",
         "Hydronic Heating": "Hydronic Heating, Electrical Heating, Ventilation",
         "Communication Technologies": "Communication Technologies",
         "Underground Locators": "Underground Locators",
         "HVAC": "HVAC", "Detectionand Measurement": "Detection and Measurement"}
GEO = {"CA": "Canada", "GB": "United Kingdom", "CN": "China", "Other Foreign": "Other countries"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    geo = without(shaped(d.history(("StatementGeographicalAxis",)), GEO), "US")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by product line", prod,
                              tags=[yoy(prod, "Package and Process", u=0.55), yoy(prod, "Communication", u=0.8)]),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "HVAC", u=0.55), yoy(seg_q, "Detection", u=0.8)]),
        geo and story.towers("Revenue outside the US, by country", geo, tags=[growth(geo, "Canada")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
