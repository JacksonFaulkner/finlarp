"""MongoDB: Atlas grows into roughly three quarters of revenue, quarterly revenue keeps rising, and
operating margin climbs from losses to positive in the latest quarter as free cash flow builds."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, shaped

TICKER = "MDB"
NAMES = {"Mongo DB Atlas": "MongoDB Atlas related"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    om = story.bars("Operating margin", "%", d.points("Operating margin, quarterly"))
    if om and (t := bars_swing(om["points"], "%")):
        om["tags"], om["auto_tags"] = [t], False
    beats = [
        prod and story.towers("Revenue by offering", prod, tags=[growth(prod, "MongoDB Atlas")]),
        prod and story.towers("Revenue share by offering", prod, pct=True, tags=pct_tags(prod, ["MongoDB Atlas"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        om,
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
