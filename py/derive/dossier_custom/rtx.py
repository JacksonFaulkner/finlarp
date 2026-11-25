"""RTX: Pratt & Whitney becomes the largest segment and swings from an operating loss to a profit,
commercial aerospace grows its share of revenue against US government sales, and quarterly
operating margin rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, series_bars, shaped

TICKER = "RTX"
NAMES = {"Pratt and Whitney": "Pratt & Whitney"}
CUST = {"Commercial Aerospace": "Commercial aerospace and other", "US Government": "US government (excl. FMS)",
        "Foreign Military": "Foreign military sales via US gov.", "Foreign Government": "Foreign government direct"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    cust = shaped(d.history(("MajorCustomersAxis",)), CUST)
    pw = series_bars("Pratt & Whitney operating income", oi, "Pratt")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Pratt", "Raytheon"])),
        pw,
        cust and story.towers("Revenue share by customer", cust, pct=True,
                              tags=pct_tags(cust, ["Commercial", "US government"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
