"""Klaviyo: revenue outside the US grows faster, so the US share slips, quarterly revenue keeps
climbing, the operating loss narrows toward breakeven, and free cash flow turns positive and grows."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, pct_tags, seg_tags, shaped, tagged

TICKER = "KVYO"
NAMES = {"EMEA Other Than UNITEDKINGDOM": "EMEA other than UK", "GB": "United Kingdom"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["US", "EMEA"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=seg_tags(geo_q, ["EMEA", "US"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
