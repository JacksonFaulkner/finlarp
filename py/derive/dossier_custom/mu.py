"""Micron: DRAM and NAND both more than triple in FY2026, the business units swing from a combined
FY2023 operating loss to tens of billions of income each, quarterly revenue climbs about sixfold in two
years, and gross margin goes from the high 30s to the mid 80s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, growth, seg_tags, shaped, share, total_of

TICKER = "MU"
NAMES = {"DRAM": "DRAM", "NAND": "NAND", "Other Product": "Other"}


def _swing(oi: dict) -> dict:
    """Total operating income first -> latest period (a loss reads as a loss; towers draw it as 0)."""
    a, b = total_of(oi, 0), total_of(oi)
    word = lambda v: f"loss {_money(-v)}" if v < 0 else _money(v)
    return {"i": -1, "s": len(oi["series"]) - 1, "u": 0.55, "text": f"Total {oi['periods'][0]} {word(a)} -> {oi['periods'][-1]} {word(b)}"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["DRAM", "NAND"])),
        prod_q and story.towers("Same quarter a year apart", prod_q, tags=[growth(prod_q, "DRAM")]),
        oi and story.towers("Operating income by business unit", oi, tags=[_swing(oi), share(oi, "CMBU", u=0.75)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
