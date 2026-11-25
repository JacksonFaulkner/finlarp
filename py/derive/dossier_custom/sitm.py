"""SiTime: revenue falls in FY2023 and then climbs, quarterly revenue more than doubles in a year,
gross margin rises into the 60s, and the operating loss narrows to a profit."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, tagged

TICKER = "SITM"


def specs(d: Data) -> list[dict]:
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    om = d.points("Operating margin, quarterly")
    beats = [
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin", "%", gm), bars_swing(gm)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
