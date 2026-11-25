"""Thomson Reuters: electronic software and services is almost all revenue and still growing while
print shrinks, annual revenue rises every year, and free cash flow climbs past $2B."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "TRI"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductsAndServicesAxis",)))
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Electronic", "Global Print"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
