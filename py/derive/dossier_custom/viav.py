"""Viavi: Network and Service Enablement carries the FY2026 jump in revenue and its operating income
multiplies, the US grows fastest, and quarterly operating margin climbs to its high in the latest
quarter as revenue rises every quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "VIAV"
NAMES = {"Optical Security": "Optical Security and Performance", "Network and Service": "Network and Service Enablement",
         "CN": "China"}
SHORT = {"Network and Service Enablement": "NSE", "Optical Security and Performance": "OSP"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short(seg_tags(seg, ["Network and Service", "Optical Security"]), SHORT)),
        oi and story.towers("Segment operating income", oi, tags=short([growth(oi, "Network and Service")], SHORT)),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "EMEA"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
