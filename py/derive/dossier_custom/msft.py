"""Microsoft: Intelligent Cloud catches Productivity, server and cloud leads product growth, the
cloud segment's operating income climbs, while margins drift down a little with AI capex."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "MSFT"
NAMES = {"Microsoft Three Six Five Commercial": "Microsoft 365 Commercial",
         "Microsoft Three Six Five Consumer": "Microsoft 365 Consumer", "XBOX": "Xbox",
         "Linked in": "LinkedIn", "Server Products and Cloud": "Server products and cloud"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Intelligent Cloud", "Productivity"])),
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Server products", "Microsoft 365 Com"])),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "Intelligent Cloud")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
