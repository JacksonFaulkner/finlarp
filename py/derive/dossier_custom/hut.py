"""Hut 8: high performance computing colocation and cloud revenue more than doubles while Power
shrinks, the US takes most of revenue as Canada falls, and quarterly revenue more than triples from
its early-2025 low. Segment figures are before intersegment eliminations. Margins and the annual
revenue series are left out (margins run to hundreds of percent; the annual series repeats FY2023)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, seg_tags, shaped, short, tagged

TICKER = "HUT"
SHORT = {"High Performance Computing Colocation and Cloud": "HPC colocation and cloud"}
GEO = {"US": "US", "CA": "Canada"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    q = d.points("Quarterly revenue")
    beats = [
        seg and story.towers("Segment revenue (before eliminations)", seg,
                             tags=short(seg_tags(seg, ["High Performance", "Power"]), SHORT)),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q,
                               tags=short([growth(seg_q, "High Performance", u=0.55),
                                           growth(seg_q, "Digital", u=0.8)], SHORT)),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["US", "Canada"])),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_swing(q, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
