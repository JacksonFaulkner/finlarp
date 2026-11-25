"""Sensata: US revenue shrinks over FY2023-FY2025 while China holds, the latest quarter grows on a
year earlier led by aerospace, defense and commercial equipment, and the operating margin climbs
back to a two-year high after a Q3'25 loss quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, short, tagged

TICKER = "ST"
NAMES = {"NL": "Netherlands", "CN": "China", "GB": "United Kingdom",
         "Aerospace Defense and Commercial": "Aerospace, Defense and Commercial Equipment"}

# Annual segment revenue for FY2023-FY2024 sums below the geographic total (the segment set of the
# latest year does not cover the earlier years), so annual segments are left out; regions agree.


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "China"])),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=short(seg_tags(seg_q, ["Aerospace", "Automotive"]),
                                          {"Aerospace, Defense and Commercial Equipment": "Aero/defense"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
