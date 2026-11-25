"""Diodes: revenue falls from its FY2022 peak through FY2024 with both sales channels, then recovers;
the latest quarter is up through distributors and direct sales alike, quarterly revenue climbs from
its Q1 2025 low and the quarterly operating margin rebuilds from near zero."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, seg_tags, shaped, short, tagged

TICKER = "DIOD"
SHORT = {"Direct Sales": "Direct"}


def specs(d: Data) -> list[dict]:
    # The geographic axis is left out: its regions sum to about twice reported revenue.
    ch = shaped(d.history(("IncomeStatementLocationAxis",)))
    ch_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, quarterly")
    beats = [
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        ch and story.towers("Revenue by sales channel", ch, tags=short(seg_tags(ch, ["Distributor", "Direct"]), SHORT)),
        ch_q and story.towers("Same quarter a year apart, by channel", ch_q,
                              tags=short(seg_tags(ch_q, ["Distributor", "Direct"]), SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
