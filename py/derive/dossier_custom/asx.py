"""ASE Technology: testing grows fastest and packaging rebounds while electronic manufacturing
services shrink, Taiwan's share of revenue rises, and gross margin recovers from its FY2023 low.
Figures are NT$ (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "ASX"
UNIT = "NT$M"  # the Financials tab's series are the 20-F's NT$ figures
SEGS = {"Electronic Manufacturing": "Electronic mfg. service"}
GEO = {"TW": "Taiwan", "Other Geographical": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("SegmentsAxis",)), SEGS)
    geo = shaped(d.history(("GeographicalAreasAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Testing", "Electronic"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan", "US"])),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
