"""Equinix: colocation is most of revenue and interconnection grows beside it, the Americas lead the
latest quarter's growth, operating margin rises, and free cash flow turns negative in the latest year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "EQIX"
NAMES = {"Non Recurring Revenues": "Non-recurring revenues"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    reg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue by type", prod, tags=seg_tags(prod, ["Colocation", "Interconnection"])),
        reg_q and story.towers("Region, same quarter a year apart", reg_q,
                               tags=[growth(reg_q, "Americas", u=0.6), growth(reg_q, "Asia Pacific", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
