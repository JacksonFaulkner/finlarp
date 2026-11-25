"""Broadcom: VMware lifts infrastructure software in a year, then AI semiconductors more than double
in a year, operating margin climbs past 50%, and China's share of revenue falls."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "AVGO"
GEO = {"Chinaincluding Hong Kong": "China incl. Hong Kong", "All Other Geographies": "Other", "SG": "Singapore",
       "TW": "Taiwan"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Infrastructure Software", "Semiconductor"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Semiconductor")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China incl", "US"])),
    ]
    return [story.scene(d.name("financials"), beats)]
