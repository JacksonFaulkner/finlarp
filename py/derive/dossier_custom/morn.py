"""Morningstar: Credit is the fastest-growing segment and transaction-based revenue gains share,
quarterly revenue climbs about 10% on a year earlier, operating margin more than doubles from its
FY2022 low, and free cash flow climbs to about $440M."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, pct_tags, seg_tags, shaped, tagged

TICKER = "MORN"
NAMES = {"Pitch Book": "PitchBook", "Licensed Based": "License based", "Transaction Based": "Transaction based",
         "Asset Based": "Asset based"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Morningstar Credit", "PitchBook"])),
        prod and story.towers("Revenue share by type", prod, pct=True, tags=pct_tags(prod, ["Transaction"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
