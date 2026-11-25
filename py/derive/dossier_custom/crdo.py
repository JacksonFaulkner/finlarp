"""Credo: revenue billed to the US jumps in FY2026 and passes Hong Kong, China's share falls to almost
nothing in the latest quarter, and quarterly operating margin swings from a loss into the 20s-30s."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, growth, pct_tags, shaped

TICKER = "CRDO"
NAMES = {"US": "US", "HK": "Hong Kong", "CN": "China", "TW": "Taiwan", "MY": "Malaysia",
         "RESTOFTHEWORLD": "Rest of world"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), NAMES)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    om = story.bars("Operating margin", "%", d.points("Operating margin, quarterly"))
    if om and (t := bars_swing(om["points"], "%")):
        om["tags"], om["auto_tags"] = [t], False
    beats = [
        geo and story.towers("Revenue by billing region", geo, tags=[growth(geo, "US"), growth(geo, "Hong Kong", u=0.45)]),
        geo and story.towers("Revenue share by billing region", geo, pct=True, tags=pct_tags(geo, ["US", "Hong Kong"])),
        geo_q and story.towers("Same quarter a year apart", geo_q,
                               tags=[growth(geo_q, "US", u=0.8), growth(geo_q, "China", u=0.4)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        om,
    ]
    return [story.scene(d.name("financials"), beats)]
