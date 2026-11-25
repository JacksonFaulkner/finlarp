"""Uranium Energy: revenue comes in lumps from inventory sales (most quarters book none), so the
story is the cash burn: free cash flow is negative in every quarter shown and in each fiscal year
since FY2023."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_total, tagged

TICKER = "UEC"


def specs(d: Data) -> list[dict]:
    # Margins are left out: on near-zero revenue the operating margin reaches -25,000% (FY2024).
    # Segment towers are left out: the mining segments report no revenue; it is all inventory sales.
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    fcf_q = d.points("Free cash flow, quarterly")
    fcf = d.points("Free cash flow, annual")
    zero = sum(1 for _, v in q if v == 0)
    low = min(fcf_q, key=lambda p: p[1]) if fcf_q else None
    hi = max(range(len(rev)), key=lambda i: rev[i][1]) if rev else 0
    beats = [
        rev and tagged(story.bars("Annual revenue", "$M", rev),
                       {"i": hi, "u": 0.75, "text": f"peak {rev[hi][0]} {story.money(rev[hi][1])}"}),
        q and tagged(story.bars("Quarterly revenue", "$M", q),
                     {"i": -1, "u": 0.75, "text": f"{zero} of {len(q)} quarters with no revenue"}),
        low and tagged(story.bars("Free cash flow, quarterly", "$M", fcf_q),
                       {"i": fcf_q.index(low), "u": 0.75, "text": f"{low[0]} burn {story.money(-low[1])}"}),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_total(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
