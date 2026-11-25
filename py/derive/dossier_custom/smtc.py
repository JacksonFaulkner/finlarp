"""Semtech: signal integrity nearly doubles in two years and passes IoT, which shrinks after FY2024;
Asia Pacific takes a larger share of revenue, and the FY2024 operating margin collapses (gross margin
falls with it) before recovering to single digits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, short, tagged

TICKER = "SMTC"
SHORT = {"Signal Integrity Products Group": "Signal Integrity", "IoT Systems and Connectivity": "IoT",
         "Advanced Protection and Sensing Products": "Protection"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)))
    om = d.points("Operating margin, annual")
    gm = dict(d.points("Gross margin, annual"))
    lo = min(om, key=lambda p: p[1]) if om else None
    lo_tag = lo and {"i": om.index(lo), "u": 0.7,
                     "text": f"{lo[0]} {lo[1]:.0f}%" + (f" (gross {gm[lo[0]]:.0f}%)" if lo[0] in gm else "")}
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short(seg_tags(seg, ["Signal Integrity", "IoT"]), SHORT)),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=short([growth(seg_q, "Signal Integrity")], SHORT)),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["Asia Pacific"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Operating margin, annual", "%", om), lo_tag),
    ]
    return [story.scene(d.name("financials"), beats)]
