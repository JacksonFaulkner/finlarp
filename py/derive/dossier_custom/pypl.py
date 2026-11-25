"""PayPal: transaction revenue is most of the business and grows slowly, the US grows while non-US
revenue slips in the latest quarter, and the quarterly operating margin drifts down."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped, short

TICKER = "PYPL"
NAMES = {"Transaction": "Transaction revenue", "Revenues from Other Value Added": "Other value added services",
         "Non Us": "Non-US"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Transaction", "Other value"]), {"Other value added services": "Value added services"})),
        geo_q and story.towers("US vs non-US, same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "US", u=0.55), growth(geo_q, "Non-US", u=0.75)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
