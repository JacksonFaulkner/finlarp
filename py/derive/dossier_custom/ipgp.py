"""IPG Photonics: revenue falls from FY2021 to FY2024 and barely recovers in FY2025, led down by
high-power CW lasers and the European business outside Germany; quarterly revenue climbs back
through 2025-26, but the operating margin swings from the mid-20s to a loss in FY2024 and stays
near zero, and free cash flow turns slightly negative in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_low, bars_year_ago, pct_tags, seg_tags, shaped, short, tagged

TICKER = "IPGP"
NAMES = {"CN": "China", "DE": "Germany", "JP": "Japan"}
SHORT = {"High Power Continuous Wave CW Lasers": "High-power CW", "Pulsed Lasers": "Pulsed",
         "Other European Geographical Areas": "Other Europe"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=short(seg_tags(prod, ["High Power", "Pulsed"]), SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["Other European"]), SHORT)),
        tagged(story.bars("Annual revenue", "$M", rev), bars_low(rev, "$M"), bars_first_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_low(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
