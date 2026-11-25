"""Marvell: Data Center grows to most of revenue while Communications and Other shrinks, Taiwan's
share of revenue jumps, and after one deep operating loss quarter the margin settles in the mid-teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "MRVL"
GEO = {"CN": "China", "TW": "Taiwan", "US": "US", "SG": "Singapore", "Other Countries": "Other countries"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by end market", prod, tags=seg_tags(prod, ["Data Center", "Communications"])),
        prod and story.towers("Revenue share by end market", prod, pct=True, tags=pct_tags(prod, ["Data Center"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan", "China"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
