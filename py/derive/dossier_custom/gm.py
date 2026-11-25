"""General Motors: North America is nearly all revenue while GM International shrinks and Cruise
revenue falls to almost nothing, quarterly revenue is flat, the operating margin dips to a loss in
Q4'25, and free cash flow jumps in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, series_bars, shaped, share

TICKER = "GM"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    cruise = series_bars("Cruise revenue", seg, "Cruise")
    if cruise:
        (p0, a), (p1, b) = cruise["points"][0], cruise["points"][-1]
        pk = max(cruise["points"], key=lambda p: p[1])
        cruise["tags"], cruise["auto_tags"] = [{"i": -1, "u": 0.8,
                                                "text": f"{pk[0]} ${pk[1]:,.0f}M -> {p1} ${b:,.0f}M"}], False
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[share(seg, "GM North America", u=0.55),
                                                              growth(seg, "GMI", u=0.8)]),
        cruise,
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
