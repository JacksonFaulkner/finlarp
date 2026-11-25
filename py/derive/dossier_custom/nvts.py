"""Navitas: annual revenue climbs to a FY2024 peak and then falls by almost half in FY2025, quarterly
revenue keeps sliding before ticking up in the latest two quarters, and free cash flow is negative in
every year shown. No segment split is reported; operating margins (losses several times revenue) are
left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_total, tagged

TICKER = "NVTS"


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
