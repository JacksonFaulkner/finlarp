"""AvePoint: SaaS grows to about three quarters of revenue while termed licenses and maintenance
shrink, every region grows, revenue rises every quarter, and the operating margin goes from a
loss to a profit as free cash flow climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, growth, pct_tags, seg_tags, shaped, tagged

TICKER = "AVPT"
NAMES = {"SAAS": "SaaS"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["SaaS", "Termed"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["EMEA", "Asia Pacific"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
