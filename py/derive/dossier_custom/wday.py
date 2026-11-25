"""Workday: subscription services carry all the growth while professional services stay flat,
quarterly revenue rises every quarter, and the annual operating margin turns from losses to
positive as free cash flow more than doubles."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "WDAY"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Subscription", "Professional"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
