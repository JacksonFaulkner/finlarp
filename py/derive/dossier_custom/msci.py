"""MSCI: Index is the largest segment and grows fastest, asset-based fees jump against the same
quarter a year earlier, and quarterly revenue rises steadily at an operating margin in the mid-50s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "MSCI"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[*seg_tags(seg, ["Index"]), share(seg, "Index", u=0.4)]),
        prod_q and story.towers("By revenue type, same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Asset Based"), growth(prod_q, "Recurring", u=0.4)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
