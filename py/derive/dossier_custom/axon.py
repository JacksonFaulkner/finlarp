"""Axon: software and services double in two years and pass TASER devices, platform solutions more than doubles year
over year in the latest quarter, international grows faster than the US, and operating margin hovers
near zero."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped

TICKER = "AXON"
GEO = {"Non Us": "Non-US"}
# the "Service" member equals the Software and Services segment line in the same filing
NAMES = {"Service": "Software and Services"}
SHORT = {"TASER Devices Professional": "TASER devices", "Software and Services": "Software & services"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=story.short(seg_tags(prod, ["Software", "TASER"]), SHORT)),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=story.short([growth(prod_q, "Platform", u=0.6), growth(prod_q, "Software", u=0.85)], SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Non-US"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
