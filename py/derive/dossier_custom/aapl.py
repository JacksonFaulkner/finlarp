"""Apple: iPhone is flat while Services keeps compounding, Greater China's share slips, the
holiday quarter towers over the rest, and gross margin climbs toward 50%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags

TICKER = "AAPL"


def specs(d: Data) -> list[dict]:
    seg = d.history(("ProductOrServiceAxis",))
    region = d.history(("StatementBusinessSegmentsAxis",))
    seg_q = d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2)
    beats = [
        seg and story.towers("Revenue by product", seg, tags=seg_tags(seg, ["Service", "iPhone"])),
        region and story.towers("Revenue share by region", region, pct=True,
                                tags=pct_tags(region, ["Greater China", "Americas"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        seg_q and story.towers("Same quarter a year apart, by product", seg_q, tags=[growth(seg_q, "iPhone")]),
    ]
    return [story.scene(d.name("financials"), beats)]
