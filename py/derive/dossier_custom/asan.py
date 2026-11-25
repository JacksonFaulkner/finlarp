"""Asana: revenue roughly doubles from FY2022 with non-US growing faster than the US, the operating loss
narrows from about -70% of revenue to -25%, free cash flow turns positive, and gross margin edges down."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_peak_to_last, bars_swing, seg_tags, shaped,
                                         tagged)

TICKER = "ASAN"
GEO = {"Non Us": "Outside US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    gm = d.points("Gross margin, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Outside US"])),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
