"""Ultra Clean: products are most of revenue, Singapore and Malaysia grow while the US and China
shrink, revenue jumps in Q2'26 after six flat quarters, and a Q2'25 operating loss (confirmed in net
margin) leaves both segments with an operating loss for FY2025 on a gross margin stuck near 16%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_low, bars_year_ago, seg_tags, shaped, short, tagged,
                                         total_swing)

TICKER = "UCTT"
GEO = {"SG": "Singapore", "US": "United States", "AT": "Austria", "CN": "China", "KR": "South Korea",
       "MY": "Malaysia", "TW": "Taiwan", "Other Geographical Areas": "Other"}
SEG = {"Semiconductor Products and Solutions": "Products and Solutions",
       "Semiconductor Services Business": "Services"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), SEG)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        geo and story.towers("Revenue by country", geo, tags=seg_tags(geo, ["Malaysia", "China"])),
        oi and story.towers("Segment operating income", oi, tags=[total_swing(oi)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_low(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
