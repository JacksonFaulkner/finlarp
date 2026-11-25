"""KLA: wafer inspection leads the growth, Taiwan and Korea take share while China's revenue stays
flat and its share falls, and quarterly revenue rises steadily."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "KLAC"
GEO = {"CN": "China", "TW": "Taiwan", "KR": "Korea", "JP": "Japan"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["Wafer Inspection", "Service"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "Taiwan"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Net margin", "%", d.points("Net margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
