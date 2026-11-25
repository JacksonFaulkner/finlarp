"""GE Vernova: US revenue grows while Europe and Asia shrink, product revenue jumps in a year in the
latest quarter, and margins and free cash flow climb from losses to profits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "GEV"
GEO = {"Americas excluding U. S.": "Americas excl. US"}


def specs(d: Data) -> list[dict]:
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    ps_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2))
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["US", "Europe"])),
        ps_q and story.towers("Same quarter a year apart", ps_q, tags=seg_tags(ps_q, ["Product", "Service"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
