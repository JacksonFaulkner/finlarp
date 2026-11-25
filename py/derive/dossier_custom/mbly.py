"""Mobileye: revenue falls in FY2024 and only partly recovers, China's share of revenue shrinks,
gross margin dips with it and comes back, and free cash flow reaches a new high in FY2025.
Quarterly and annual operating margins include quarters below -500% in the Financials blocks,
so the operating margin is left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_swing, pct_tags,
                                         shaped, tagged)

TICKER = "MBLY"
NAMES = {"CN": "China", "US": "US", "DE": "Germany", "KR": "South Korea", "GB": "UK"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        geo and story.towers("Revenue share by customer location", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_swing(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
