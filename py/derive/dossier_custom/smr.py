"""NuScale: revenue is small and almost all engineering-design work, it peaks in FY2024 and falls to
nearly nothing by mid-2026, while free cash flow burn jumps several-fold in FY2025. Margins are left
out: on near-zero revenue they run to thousands of percent."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_total, seg_tags, shaped, tagged

TICKER = "SMR"
NAMES = {"Power Plant and NPM Engineering Design": "Power plant and NPM engineering design",
         "E 2 Centers": "E2 Centers"}
SHORT = {"Power plant and NPM engineering design": "Engineering design"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    fcf_q = d.points("Free cash flow, quarterly")
    low = min(fcf, key=lambda p: p[1]) if fcf else None
    beats = [
        prod and story.towers("Revenue by product / service", prod,
                              tags=story.short(seg_tags(prod, ["Power plant"]), SHORT)),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        low and tagged(story.bars("Free cash flow, annual", "$M", fcf),
                       {"i": fcf.index(low), "u": 0.75, "text": f"{low[0]} burn {story.money(-low[1])}"}),
        tagged(story.bars("Free cash flow, quarterly", "$M", fcf_q), bars_total(fcf_q, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
