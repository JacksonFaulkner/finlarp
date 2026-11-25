"""Tencent Music: online music grows each year while social entertainment shrinks by about 40%, so
total revenue barely moves through FY2024, yet gross and operating margins rise. Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, short, tagged

TICKER = "TME"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's RMB figures
SHORT = {"Social Entertainment Services and Others": "Social ent.", "Online Music Services": "Online music"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("ProductsAndServicesAxis",)))
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, annual")
    beats = [
        seg and story.towers("Revenue by service", seg,
                             tags=short(seg_tags(seg, ["Online Music", "Social Entertainment"]), SHORT)),
        seg and story.towers("Revenue share by service", seg, pct=True, tags=short(pct_tags(seg, ["Online Music"]), SHORT)),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
