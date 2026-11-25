"""TeraWulf: no segment data; quarterly revenue stays in a narrow band while operating losses run
far larger than revenue, and the free cash outflow grows about fourfold in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, tagged

TICKER = "WULF"


def specs(d: Data) -> list[dict]:
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    lo = om and min(om, key=lambda p: p[1])
    burn = len(fcf) >= 2 and {"i": -1, "u": 0.75,
                              "text": f"{fcf[-2][0]} {story.money(fcf[-2][1])} -> {fcf[-1][0]} {story.money(fcf[-1][1])}"}
    rng = q and {"i": -1, "u": 0.75,
                 "text": f"{story.money(min(v for _, v in q))} to {story.money(max(v for _, v in q))} a quarter"}
    beats = [
        tagged(story.bars("Quarterly revenue", "$M", q), rng, bars_year_ago(q, u=0.55)),
        tagged(story.bars("Operating margin", "%", om),
               lo and {"i": om.index(lo), "u": 0.75, "text": f"{lo[0]} operating margin {lo[1]:.0f}%"}),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), burn),
    ]
    return [story.scene(d.name("financials"), beats)]
