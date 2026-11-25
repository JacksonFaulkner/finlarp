"""DocuSign: almost all revenue is subscriptions, revenue outside the US grows faster than at home,
and the operating margin turns from a loss to a profit while free cash flow more than doubles."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, shaped, tagged, yoy

TICKER = "DOCU"
GEO = {"Non Us": "Outside the US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Outside"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "Outside"), yoy(geo_q, "US", u=0.5)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
        story.bars("Free cash flow", "$M", fcf),
    ]
    return [story.scene(d.name("financials"), beats)]
