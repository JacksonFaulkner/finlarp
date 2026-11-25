"""Qualys: sales through intermediaries grow fast enough to overtake direct sales in the latest quarter,
non-US revenue gains share, and operating margin climbs every year from about 21% to about 33% as free
cash flow tops $300M."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_year_ago, growth, pct_tags, seg_tags, shaped, tagged

TICKER = "QLYS"
NAMES = {"Non Us": "Non-US", "Through intermediary": "Through intermediaries", "Direct to consumer": "Direct"}


def specs(d: Data) -> list[dict]:
    ch = shaped(d.history(("ContractWithCustomerSalesChannelAxis",)), NAMES)
    ch_q = shaped(d.history(("ContractWithCustomerSalesChannelAxis",), cadence="quarterly", n=2), NAMES)
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        ch and story.towers("Revenue by sales channel", ch, tags=seg_tags(ch, ["Through", "Direct"])),
        ch_q and story.towers("Channels, same quarter a year apart", ch_q,
                              tags=[growth(ch_q, "Through"), growth(ch_q, "Direct", u=0.85)]),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Non-US"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_first_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
