"""Tempus AI: diagnostics more than doubles in FY2025 and carries revenue to about four times FY2022,
while the operating loss narrows as a share of revenue."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, tagged

TICKER = "TEM"
NAMES = {"Insights Product": "Insights", "Trials Product": "Trials"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Diagnostics", "Insights"])),
        prod and story.towers("Revenue share by product", prod, pct=True, tags=pct_tags(prod, ["Diagnostics"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_swing(rev, "$M")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
