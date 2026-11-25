"""Zoom: revenue grows a few percent a year in every region, while operating margin rises from the
mid-teens to the mid-20s and free cash flow climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped

TICKER = "ZM"


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Americas", "EMEA"])),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
