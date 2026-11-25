"""Teradyne: Semiconductor Test carries the growth while Robotics shrinks, Taiwan triples into the
largest region, and the latest quarter's Semiconductor Test revenue more than doubles
a year on, lifting the operating margin into the 30s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "TER"
GEO = {"TW": "Taiwan", "CN": "China", "KR": "Korea", "US": "US", "MY": "Malaysia", "SG": "Singapore",
       "PH": "Philippines", "TH": "Thailand", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Semiconductor Test", "Robotics"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Semiconductor Test")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
