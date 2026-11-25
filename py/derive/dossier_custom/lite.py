"""Lumentum: revenue roughly triples in eight quarters with Mexico, Thailand and China shipments
growing fastest, gross margin doubles, and the operating margin swings from a loss to a profit."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "LITE"
GEO = {"TH": "Thailand", "HK": "Hong Kong", "MX": "Mexico", "CN": "China", "JP": "Japan",
       "Other Asia Pacific": "Other Asia Pacific", "Americas excluding": "Americas excl. US and Mexico"}


def _swing(b: dict | None) -> dict | None:
    if not b:
        return None
    (pa, a), (pb, v) = b["points"][0], b["points"][-1]
    if a < 0 < v:
        b["tags"], b["auto_tags"] = [{"i": len(b["points"]) - 1, "u": 0.8, "text": f"{pa} {a:.1f}% -> {pb} {v:.1f}%"}], False
    return b


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        geo and story.towers("Revenue by ship-to region", geo, tags=seg_tags(geo, ["Mexico", "Thailand"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        _swing(story.bars("Operating margin", "%", d.points("Operating margin, quarterly"))),
    ]
    return [story.scene(d.name("financials"), beats)]
