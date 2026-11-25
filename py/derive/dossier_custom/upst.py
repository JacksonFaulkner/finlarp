"""Upstart: revenue falls to a FY2023 low and roughly doubles by FY2025, quarterly revenue rises every
quarter but one, and the operating margin climbs from -50% to positive. Its product/service segment
facts cover only small fee lines, so there is no segment beat."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, bars_year_ago, tagged

TICKER = "UPST"


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om_a = d.points("Operating margin, annual")
    om_q = d.points("Operating margin, quarterly")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_swing(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_first_to_last(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om_a), bars_swing(om_a, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om_q), bars_year_ago(om_q, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
