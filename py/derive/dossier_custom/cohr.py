"""Coherent: Datacenter and Communications doubles in two years while Industrial shrinks, North
America takes a larger share, quarterly revenue climbs every quarter, and free cash flow turns
negative as it does."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped, short

TICKER = "COHR"
GEO = {"CN": "China", "JP": "Japan", "Other Countries": "Other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["Datacenter", "Industrial"]), {"Datacenter and Communications": "Datacenter & Comms"})),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["North America"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Free cash flow, quarterly", "$M", d.points("Free cash flow, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
