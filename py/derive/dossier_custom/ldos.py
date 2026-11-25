"""Leidos: in the latest quarter Homeland grows fastest while Health shrinks on a year earlier,
commercial and non-US customers jump, and the annual operating margin recovers from its FY2023 low."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, short, tagged

TICKER = "LDOS"
NAMES = {"US Do D": "US DoD and US Intelligence Community", "US Do W": "US DoW and US Intelligence Community"}


def specs(d: Data) -> list[dict]:
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    cust_q = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        seg_q and story.towers("Segments, same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Homeland", "Health"])),
        cust_q and story.towers("Customers, same quarter a year apart", cust_q, tags=short([growth(cust_q, "Commercial")],
                                                                                 {"Commercial and Non US Customers": "Commercial and non-US"})),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_swing(om)),
    ]
    return [story.scene(d.name("financials"), beats)]
