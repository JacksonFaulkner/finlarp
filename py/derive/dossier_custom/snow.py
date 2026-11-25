"""Snowflake: product revenue carries the growth year after year and in the latest quarter, while the
operating loss margin narrows quarter by quarter and free cash flow keeps rising."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "SNOW"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue: product vs services", prod, tags=seg_tags(prod, ["Product"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "Product")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
