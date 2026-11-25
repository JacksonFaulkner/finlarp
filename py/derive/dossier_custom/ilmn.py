"""Illumina: revenue is flat, consumables carry it while instruments shrink, China's share falls
each year while Europe's rises, and gross margin holds in the mid-60s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "ILMN"
GEO = {"CN": "China"}

# Operating margin is left out: its Q3'24 point (~69%) is several times its neighbours and would
# dwarf the series.


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by product type", prod, tags=seg_tags(prod, ["Instruments", "Consumables"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "Europe"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
