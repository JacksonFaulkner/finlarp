"""Dropbox: revenue has stopped growing (US and non-US both flat, quarterly revenue flat for two years),
yet operating margin more than triples from its FY2022 low and free cash flow rises every year
but one to a new high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, seg_tags, shaped, tagged

TICKER = "DBX"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Non-US"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_first_to_last(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Gross margin", "%", gm), bars_first_to_last(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
