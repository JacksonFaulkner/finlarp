"""Generac: residential power products dip in FY2025 after a FY2024 jump, commercial and industrial
leads the latest quarter's year-over-year gain, and operating margin falls below zero in Q4 2025
before recovering to the high teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, seg_tags, shaped, short, tagged, without, yoy

TICKER = "GNRC"
SHORT = {"Residential Power Products": "Residential", "Commercial and Industrial Power Products": "C&I",
         "Commercial and Industrial": "C&I"}


def specs(d: Data) -> list[dict]:
    prod = shaped(without(d.history(("ProductOrServiceAxis",)), "Intersegment"))
    seg_q = shaped(without(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), "Intersegment"))
    q = d.points("Quarterly revenue")
    beats = [
        prod and story.towers("Revenue by product line", prod,
                              tags=short(seg_tags(prod, ["Residential"]), SHORT)),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=short([yoy(seg_q, "Commercial", u=0.55), yoy(seg_q, "Residential", u=0.85)], SHORT)),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
