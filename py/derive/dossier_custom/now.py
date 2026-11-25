"""ServiceNow: every region grows each year with North America the largest, quarterly revenue climbs
every quarter, but gross margin slides through the 70s and operating margin drops to a low in the
latest quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "NOW"


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2))
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["North America", "EMEA"])),
        geo_q and story.towers("Same quarter a year apart", geo_q, tags=[growth(geo_q, "North America")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
