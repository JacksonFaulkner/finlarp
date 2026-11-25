"""Proto Labs: CNC machining grows past injection molding, the US segment earns the profit while Europe
loses more each year, quarterly revenue reaches a new high in Q2'26 and operating margin recovers from
a Q4'24 loss on a steady mid-40s gross margin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import (bars_first_to_last, bars_year_ago, seg_tags, series_bars, shaped,
                                         tagged)

TICKER = "PRLB"
NAMES = {"CNC Machining": "CNC Machining", "Injection Molding": "Injection Molding",
         "Three D Printing": "3D Printing", "A 3 D Printing": "3D Printing", "Other Products": "Other"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    eu = series_bars("Europe segment operating income", oi, "Europe")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by process", prod, tags=seg_tags(prod, ["CNC", "Injection"])),
        series_bars("United States segment operating income", oi, "United States"),
        eu and tagged(eu, bars_first_to_last(eu["points"], eu["unit"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q, "$M")),
        tagged(story.bars("Operating margin, quarterly", "%", om), bars_first_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
