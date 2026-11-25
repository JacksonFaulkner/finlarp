"""Astera Labs: annual revenue grows about tenfold in three years, shipments move from mostly Taiwan
to Singapore and China, and the operating margin swings from deep losses to about 20%."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, shaped

TICKER = "ALAB"
GEO = {"SG": "Singapore", "CN": "China", "TW": "Taiwan", "Non Us": "Other non-US", "US": "US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    ann = story.bars("Annual revenue", "$M", d.points("Annual revenue"))
    if ann:
        (p0, a), (p1, b) = ann["points"][0], ann["points"][-1]
        ann["tags"] = [{"i": -1, "u": 0.8, "text": f"{p0} -> {p1}: {b / a:.1f}x"}]
        ann["auto_tags"] = False
    beats = [
        ann,
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Taiwan", "Singapore"])),
        geo_q and story.towers("By region, same quarter a year apart", geo_q, tags=[growth(geo_q, "China")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
