"""Zebra: Connected Frontline overtakes Asset Visibility and Automation in revenue and nearly doubles
its operating income from FY2023; the latest quarter is up on a year earlier in both segments and the
operating margin reaches its high of the last two years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "ZBRA"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Connected Frontline", "Asset Visibility"]),
                                                               {"Asset Visibility and Automation": "Asset Visibility"})),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Connected Frontline")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Connected Frontline"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
