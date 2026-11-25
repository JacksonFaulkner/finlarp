"""NIQ: EMEA is the largest region and grows fastest in dollars, point-in-time revenue falls in the
latest quarter while over-time revenue grows, the operating margin swings around breakeven, and free
cash flow turns from an outflow to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, seg_tags, shaped, tagged

TICKER = "NIQ"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    timing_q = shaped(d.history(("TimingOfTransferOfGoodOrServiceAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    rng = om and {"i": -1, "u": 0.75,
                  "text": f"{min(v for _, v in om):.1f}% to {max(v for _, v in om):.1f}% over {len(om)} quarters"}
    beats = [
        seg and story.towers("Revenue by region segment", seg, tags=seg_tags(seg, ["EMEA", "Americas"])),
        timing_q and story.towers("Revenue timing, same quarter a year apart", timing_q,
                                  tags=seg_tags(timing_q, ["Point in time", "Over time"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), rng),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
