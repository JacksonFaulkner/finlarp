"""Block: Square grows while Cash App slips in FY2025, bitcoin revenue shrinks as a share while
financial solutions grow, and gross margin climbs about ten points in two years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "XYZ"


def _pp(b: dict | None) -> dict | None:
    """Gross margin first -> latest, in points."""
    if b:
        (p0, a), (p1, z) = b["points"][0], b["points"][-1]
        b["tags"], b["auto_tags"] = [{"i": -1, "u": 0.8, "text": f"{p0} {a:.1f}% -> {p1} {z:.1f}% ({z - a:+.1f} pts)"}], False
    return b


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Square", "Cash App"])),
        prod and story.towers("Revenue share by product", prod, pct=True,
                              tags=pct_tags(prod, ["Bitcoin", "Financial Solutions"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _pp(story.bars("Gross margin", "%", d.points("Gross margin, quarterly"))),
    ]
    return [story.scene(d.name("financials"), beats)]
