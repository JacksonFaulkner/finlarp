"""SpaceX: revenue jumps from one September quarter to the next, led by the SI segment and
Connectivity, and the operating margin swings from a loss to positive. Quarterly filings only so
far, so every beat is quarters."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "SPCX"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment, same quarter a year apart", seg, tags=seg_tags(seg, ["SI", "Connectivity"])),
        q and {"panel": "bars", "title": "Quarterly revenue", "unit": "$M", "points": q},
        om and {"panel": "bars", "title": "Operating margin", "unit": "%", "points": om},
    ]
    return [story.scene(d.name("financials"), beats)]
