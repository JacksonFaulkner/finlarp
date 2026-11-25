"""Fluor: Urban Solutions grows to well over half of revenue while Energy Solutions shrinks, Asia
Pacific falls away, a Q3'25 loss quarter shows in both gross and operating margin, and free cash
flow swings from FY2024's high to an outflow in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, pct_tags, seg_tags, shaped, tagged

TICKER = "FLR"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Urban", "Energy"])),
        geo and story.towers("Revenue share by region", geo, pct=True,
                             tags=pct_tags(geo, ["Asia Pacific", "North America"])),
        seg_q and story.towers("Segments, same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["Urban", "Energy"])),
        story.bars("Quarterly revenue", "$M", q),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
