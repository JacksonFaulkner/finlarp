"""GlobalFoundries: among its business groups, smart mobile devices shrink while automotive and
communications infrastructure and datacenter grow, the US share of revenue falls, annual revenue sits below its FY2022 peak, and
gross margin recovers to the high 20s in the latest quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, short

TICKER = "GFS"
NAMES = {"Communications Infrastructure": "Communications Infrastructure and Datacenter",
         "Europe the Middle East": "EMEA", "Other Geographical": "Other",
         "Non Wafer": "Non-wafer and other"}
SHORT = {"Communications Infrastructure and Datacenter": "Comms/Datacenter"}


def specs(d: Data) -> list[dict]:
    grp = shaped(d.history(("BusinessGroupAxis",)), NAMES)
    geo = shaped(d.history(("GeographicalAreasAxis",)), NAMES)
    gm = d.points("Gross margin, quarterly")
    gmb = story.bars("Gross margin", "%", gm)
    if gmb and (t := bars_swing(gm)):
        gmb["tags"], gmb["auto_tags"] = [t], False
    beats = [
        grp and story.towers("Revenue by business group", grp,
                             tags=short(seg_tags(grp, ["Communications", "Smart Mobile"]), SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["US"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        gmb,
    ]
    return [story.scene(d.name("financials"), beats)]
