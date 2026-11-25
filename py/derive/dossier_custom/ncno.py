"""nCino: license and subscription revenue keeps growing while professional services stay flat, the UK
is the fastest-growing region, and the annual operating margin climbs from a deep loss to slightly
positive as free cash flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, tagged, yoy

TICKER = "NCNO"
GEO = {"GB": "United Kingdom", "Other Geographic Regions": "Other regions"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["License", "Professional"])),
        geo and story.towers("Revenue by region", geo, tags=[yoy(geo, "United Kingdom", u=0.6), yoy(geo, "US", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
