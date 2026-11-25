"""IREN: AI cloud services grow from almost nothing beside bitcoin mining, quarterly revenue peaks in
Q1 FY2026 and then falls, and operating losses deepen through FY2026 as the operating margin sinks
far below zero."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, growth, pct_tags, shaped, tagged

TICKER = "IREN"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    worst = om and {"i": min(range(len(om)), key=lambda i: om[i][1]), "u": 0.75,
                    "text": f"Low {min(v for _, v in om):.0f}% in {min(om, key=lambda p: p[1])[0]}"}
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=[growth(seg, "AI Cloud", u=0.55), growth(seg, "Bitcoin", u=0.85)]),
        seg and story.towers("Revenue share by segment", seg, pct=True, tags=pct_tags(seg, ["AI Cloud"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_peak_to_last(q, "$M")),
        tagged(story.bars("Operating margin", "%", om), worst or None),
    ]
    return [story.scene(d.name("financials"), beats)]
