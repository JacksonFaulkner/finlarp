"""Roblox: revenue grows every year and quarter while the company stays loss-making; the quarterly
operating loss narrows and annual free cash flow climbs from slightly negative to well over a billion."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago

TICKER = "RBLX"


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        _tagged(story.bars("Operating margin (a loss every quarter)", "%", om), bars_swing(om, "%")),
        _tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
