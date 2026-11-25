"""Cipher Mining: a single bitcoin-mining segment whose revenue climbs to a peak in Q3 2025 and then
falls for three quarters; the operating loss grows to nearly twice revenue in FY2025 and free cash
burn grows every year. FY2022 (almost no revenue) is left out of the revenue and margin beats."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_peak_to_last, bars_total, tagged

TICKER = "CIFR"


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")[1:]  # FY2022: start-up year, margin on ~$3M revenue
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue (bitcoin mining)", "$M", rev[1:]), bars_first_to_last(rev[1:], "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
