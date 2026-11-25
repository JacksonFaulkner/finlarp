"""Nokia: Network Infrastructure overtakes a shrinking Mobile Networks, AI cloud, mission-critical
enterprise and defense customers gain share from telecom providers, India's revenue roughly halves,
and the operating margin falls in the latest year. Figures are EUR (20-F)."""
from __future__ import annotations

import re

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, without

TICKER = "NOK"
UNIT = "EUR M"  # the Financials tab's series are the 20-F's EUR figures
NAMES = {"Network Infrastructure": "Network Infrastructure",
         "AI Cloud and Mission Critical": "AI Cloud, Mission Critical, Defense"}


def _fit(tags: list[dict]) -> list[dict]:
    """Drop the "(FYa -> FYb)" suffix from long share tags so they fit the frame (the towers show the years)."""
    return [{**t, "text": re.sub(r" \(FY\d+ -> FY\d+\)$", "", t["text"])} if len(t["text"]) > 45 else t for t in tags]


def specs(d: Data) -> list[dict]:
    seg = shaped(without(d.history(("SegmentsAxis",)), "Group Common"), NAMES)
    mkt = shaped(without(d.history(("MarketsOfCustomersAxis",)), "Other Customers"), NAMES)
    # Asia Pacific is the sum of Rest of APAC, India and Greater China; "IN" repeats India
    geo = shaped(without(d.history(("GeographicalAreasAxis",)), "Asia Pacific", "IN"))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Network Infrastructure", "Mobile"])),
        mkt and story.towers("Revenue share by customer type", mkt, pct=True, tags=_fit(pct_tags(mkt, ["AI Cloud"]))),
        geo and story.towers("Revenue by tagged region", geo, tags=[growth(geo, "India")]),
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
