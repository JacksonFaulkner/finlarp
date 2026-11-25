"""Iron Mountain: records management is still most of revenue, but data center and information
destruction grow fastest, quarterly revenue rises every quarter, and annual free cash flow goes
deeper negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "IRM"


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue by service", prod, tags=seg_tags(prod, ["Data Center", "Information Destruction"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Data Center"), growth(prod_q, "Information Destruction", u=0.5)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
