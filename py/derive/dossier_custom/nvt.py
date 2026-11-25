"""nVent: Enclosures drives the growth in revenue and operating income, Enclosures revenue jumps
by about 70% in the same quarter a year apart, quarterly revenue nearly doubles in two years, and
gross margin slips while revenue climbs."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, growth, seg_tags, shaped

TICKER = "NVT"
NAMES = {"Electricaland": "Electrical and Fastening Solutions"}
SHORT = {"Electrical and Fastening Solutions": "EFS"}

def _tagged(b: dict | None, *tags) -> dict | None:
    tags = [t for t in tags if t]
    if b and tags:
        b["tags"], b["auto_tags"] = tags, False
    return b


def _peak_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    """Peak -> latest for a % series that has come off its high."""
    if len(pts) < 2:
        return None
    hi = max(range(len(pts)), key=lambda i: pts[i][1])
    if hi == len(pts) - 1:
        return None
    return {"i": -1, "u": u, "text": f"{pts[hi][0]} {pts[hi][1]:.1f}% -> {pts[-1][0]} {pts[-1][1]:.1f}%"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=story.short(seg_tags(seg, ["Enclosures", "Electrical"]), SHORT)),
        oi and story.towers("Operating income by segment", oi, tags=story.short(seg_tags(oi, ["Enclosures", "Electrical"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q,
                               tags=story.short([growth(seg_q, "Enclosures", u=0.8), growth(seg_q, "Electrical", u=0.5)], SHORT)),
        _tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        _tagged(story.bars("Gross margin", "%", gm), _peak_to_last(gm)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
