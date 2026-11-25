"""Baidu: Baidu Core is most of revenue and slips in FY2025 while iQIYI shrinks each year; Core's
operating income falls to a loss in FY2025, taking the operating margin and free cash flow negative.
Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, series_bars, shaped, short

TICKER = "BIDU"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's RMB figures
NAMES = {"I QIYI": "iQIYI"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    core = series_bars("Baidu Core operating income", oi, "Baidu Core")
    om = story.bars("Operating margin, annual", "%", d.points("Operating margin, annual"))
    fcf = story.bars("Free cash flow, annual", UNIT, d.points("Free cash flow, annual"))
    # (Quarterly series are left out: the 20-F filer's quarterly points are sparse 2011-2018 strays.)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Baidu Core", "iQIYI"]), {"Baidu Core Business": "Baidu Core"})),
        core,
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        om,
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
