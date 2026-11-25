"""Amazon: AWS is a sixth of revenue but most of the operating income, advertising grows into a
major line, and the operating margin rises toward the mid-teens."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, share

TICKER = "AMZN"
NAMES = {"Third Party Seller": "Third-party seller services", "Advertising": "Advertising"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    beats = [
        prod and story.towers("Revenue by business line", prod, tags=seg_tags(prod, ["Amazon Web", "Advertising"])),
        oi and story.towers("Operating income by segment", oi, tags=[share(oi, "Amazon Web"), growth(oi, "North America", u=0.8)]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Amazon Web")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
