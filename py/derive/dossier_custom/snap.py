"""Snap: advertising is still most of revenue but other revenue grows nearly 4x in two years, Europe
is the fastest-growing region against a year earlier, operating losses narrow from about -30% of
revenue to about -9%, and annual free cash flow climbs from its FY2023 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "SNAP"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Other", "Advertising"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "Europe", u=0.6), growth(geo_q, "North America", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
