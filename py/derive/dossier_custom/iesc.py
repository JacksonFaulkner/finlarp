"""IES Holdings: Communications nearly doubles in two years and overtakes Residential, which slips in
FY2025; Commercial and Industrial roughly doubles in the latest quarter against a year earlier, and the
annual operating margin rises from its FY2022 low to above 11%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, drop, seg_tags, shaped, short, tagged

TICKER = "IESC"
NAMES = {"Commercialand Industrial": "Commercial and Industrial"}


def specs(d: Data) -> list[dict]:
    # Corporate carries no revenue and only costs; left out of the towers
    seg = drop(shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES), "Corporate")
    oi = drop(shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES), "Corporate")
    seg_q = drop(shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES), "Corporate")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Communications", "Residential"])),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Communications", "Infrastructure"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short(seg_tags(seg_q, ["Commercial", "Communications"]),
                                                                         {"Commercial and Industrial": "Commercial & industrial"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
