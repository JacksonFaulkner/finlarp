"""Dycom: Communications keeps growing, a new Building Systems segment appears in FY2026 and makes up
about a fifth of the latest quarter, lifting quarterly revenue to a new step, while annual free cash
flow jumps in FY2026. (No gross or operating margin series in the Financials data.)"""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, growth, share, shaped, tagged

TICKER = "DY"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=[growth(seg, "Communications", u=0.55), share(seg, "Building Systems", u=0.85)]),
        seg_q and story.towers("Same quarter a year apart, by segment", seg_q,
                               tags=[growth(seg_q, "Communications", u=0.55),
                                     share(seg_q, "Building Systems", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
