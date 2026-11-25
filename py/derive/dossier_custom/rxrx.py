"""Recursion: revenue is almost all license and service income and grows each year, with the UK going
from nothing to about half of FY2025 revenue; quarterly revenue is lumpy, and free cash flow is a
large outflow every year. Operating margins (losses many times revenue) are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_total, pct_tags, shaped, short, tagged

TICKER = "RXRX"
GEO = {"GB": "United Kingdom", "Other Countries": "Other"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=short(pct_tags(geo, ["United Kingdom"]), {"United Kingdom": "UK"})),
        tagged(story.bars("Annual revenue", "$M", rev), bars_first_to_last(rev, "$M")),
        story.bars("Quarterly revenue", "$M", q),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
