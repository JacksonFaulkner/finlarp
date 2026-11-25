"""Northrop Grumman: Aeronautics and Mission Systems grow while Space Systems shrinks, Aeronautics
swings from an operating loss to a profit, international customers take a larger share, and the
operating margin holds around 10-12% after one weak quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, series_bars, shaped

TICKER = "NOC"
NAMES = {"US Government": "US Government", "International": "International", "Other Customers": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    aero = series_bars("Aeronautics Systems operating income", oi, "Aeronautics")
    cust = shaped(d.history(("MajorCustomersAxis",)), NAMES)
    intl = [{**t, "text": t["text"].split(" (")[0] + " of revenue"} for t in (pct_tags(cust, ["International"]) if cust else [])]
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Aeronautics", "Space"])),
        aero,
        cust and story.towers("Revenue share by customer", cust, pct=True, tags=intl),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
