"""Visa: every gross revenue line grows, but client incentives grow with them, outside the US rises
to most of revenue, and operating margin dips from the mid 60s before recovering."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, series_bars, shaped

TICKER = "V"
NAMES = {"Non Us": "Outside the US"}
LINES = {"Data Processing": "Data processing", "International Transaction": "International transactions"}


def _without(hist: dict | None, prefix: str) -> dict | None:
    """`hist` minus one series (e.g. a contra-revenue line that towers cannot stack)."""
    if not hist:
        return None
    return {**hist, "series": [s for s in hist["series"] if not s[0].startswith(prefix)]}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), LINES)
    gross = _without(prod, "Client Incentives")
    inc = series_bars("Client incentives (deducted from revenue)", prod, "Client Incentives")
    if inc and inc["points"][0][1]:
        a, b = inc["points"][0][1], inc["points"][-1][1]
        inc["tags"] = [{"i": -1, "u": 0.75, "text": f"{(b / a - 1) * 100:+.0f}% {inc['points'][0][0]} -> {inc['points'][-1][0]}"}]
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    beats = [
        gross and story.towers("Gross revenue by line", gross, tags=seg_tags(gross, ["Data processing", "International"])),
        inc,
        geo and story.towers("Revenue share, US vs outside", geo, pct=True, tags=pct_tags(geo, ["Outside"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
