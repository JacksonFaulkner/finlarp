"""SoFi: of the revenue tagged by segment, Financial Services grows past Technology Platform within
a year, and free cash flow is negative every year (FY2021-FY2025)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, growth, seg_tags, shaped, tagged

TICKER = "SOFI"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    fcf = d.points("Free cash flow, annual")
    neg = sum(v for _, v in fcf if v < 0)
    fcf_tag = fcf and {"i": -1, "u": 0.75, "text": f"{len(fcf)}-yr total {_money(neg)}"}
    beats = [
        seg and story.towers("Segment revenue (as tagged)", seg, tags=seg_tags(seg, ["Financial", "Technology"])),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=[growth(seg_q, "Financial", u=0.6), growth(seg_q, "Technology", u=0.8)]),
        story.bars("Annual revenue (as tagged)", "$M", d.points("Annual revenue")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), fcf_tag),
    ]
    return [story.scene(d.name("financials"), beats)]
