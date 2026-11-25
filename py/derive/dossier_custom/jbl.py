"""Jabil: Intelligent Infrastructure grows into the largest segment and nearly doubles its operating
income while Connected Living and Digital Commerce halves; the US share of revenue rises, and
operating margin roughly doubles from early FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, shaped, short, yoy

TICKER = "JBL"
GEO = {"US": "United States", "MX": "Mexico", "MY": "Malaysia", "CN": "China"}
SHORT = {"Connected Living and Digital Commerce": "Connected Living", "Intelligent Infrastructure": "Intel. Infra."}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    # two years only: Malaysia is first broken out in FY2025, so earlier years would show it as zero
    geo = shaped(d.history(("StatementGeographicalAxis",), n=2), GEO)
    om = d.points("Operating margin, quarterly")
    omb = story.bars("Operating margin", "%", om, tags=[t for t in [bars_swing(om)] if t])
    if omb and omb.get("tags"):
        omb["auto_tags"] = False
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short([growth(seg, "Intelligent", u=0.55), yoy(seg, "Connected", u=0.85)], SHORT)),
        oi and story.towers("Operating income by segment", oi,
                            tags=short([growth(oi, "Intelligent", u=0.55), yoy(oi, "Connected", u=0.85)], SHORT)),
        geo and story.towers("Revenue share by country", geo, pct=True, tags=pct_tags(geo, ["United States", "China"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        omb,
    ]
    return [story.scene(d.name("financials"), beats)]
