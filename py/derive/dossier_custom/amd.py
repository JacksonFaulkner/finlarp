"""AMD: Data Center passes Client and Gaming to become the largest segment and roughly doubles in a
year by mid-2026, Embedded shrinks, and the operating margin recovers from one loss quarter into the
high teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "AMD"
NAMES = {"Datacenter": "Data Center"}
GEO = {"CN": "China", "TW": "Taiwan", "SG": "Singapore", "Other Countries": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Data Center", "Embedded"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Data Center")]),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Client and Gaming", "Embedded"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China"])),
    ]
    return [story.scene(d.name("financials"), beats)]
