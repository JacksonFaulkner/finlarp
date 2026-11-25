"""Reddit: advertising revenue grows about 2.6x in two years, non-US revenue grows faster than US
in the latest quarter, and operating margin swings from near zero to the high 20s as free cash
flow turns positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, seg_tags, shaped

TICKER = "RDDT"
NAMES = {"Non Us": "Non-US", "Other Revenue": "Other"}


def _tagged(b: dict | None, tag: dict | None) -> dict | None:
    if b and tag:
        b["tags"], b["auto_tags"] = [tag], False
    return b


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue: advertising vs other", prod, tags=seg_tags(prod, ["Advertising"])),
        geo_q and story.towers("Same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "US", u=0.55), growth(geo_q, "Non-US", u=0.85)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        _tagged(story.bars("Operating margin", "%", om), bars_swing(om)),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
