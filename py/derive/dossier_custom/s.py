"""SentinelOne: annual revenue grows about fivefold in four years with the non-US share rising,
operating losses narrow from over 100% of revenue to about a third, gross margin slips from its
peak, and free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, bars_swing, pct_tags, shaped, tagged

TICKER = "S"
NAMES = {"Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    rev = d.points("Annual revenue")
    om = d.points("Operating margin, annual")
    gm = d.points("Gross margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Non-US"])),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Gross margin, quarterly", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
