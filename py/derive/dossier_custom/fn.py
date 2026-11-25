"""Fabrinet: one reportable segment whose revenue jumps about a third in FY2026 and rises every
quarter, at an operating margin held near 10%, while free cash flow falls to almost nothing."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, tagged

TICKER = "FN"


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    yr = rev[-2:] if len(rev) >= 2 else []
    rng = om and {"i": -1, "u": 0.75,
                  "text": f"{min(v for _, v in om):.1f}% to {max(v for _, v in om):.1f}% over {len(om)} quarters"}
    hi = max(fcf, key=lambda p: p[1]) if fcf else None
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev),
               yr and {"i": -1, "u": 0.75, "text": f"{yr[1][0]} {(yr[1][1] / yr[0][1] - 1) * 100:+.0f}% vs {yr[0][0]}"}),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), rng),
        hi and tagged(story.bars("Free cash flow, annual", "$M", fcf),
                      {"i": -1, "u": 0.75, "text": f"{hi[0]} {story.money(hi[1])} -> {fcf[-1][0]} {story.money(fcf[-1][1])}"}),
    ]
    return [story.scene(d.name("financials"), beats)]
