"""JD.com: JD Retail carries revenue and operating profit, New Business revenue nearly doubles in
FY2025 while its operating loss balloons, and annual operating margin and free cash flow fall back.
Figures are CNY (20-F)."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, seg_tags, series_bars, shaped

TICKER = "JD"
UNIT = "CNY M"  # the Financials tab's series are the 20-F's RMB figures
NAMES = {"Jd Retail": "JD Retail", "Jd Logistics": "JD Logistics"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    nb = series_bars("New Business operating income", oi, "New Business")
    if nb and len(nb["points"]) >= 2:
        (pa, a), (pb, b) = nb["points"][-2], nb["points"][-1]
        if b < 0:
            nb["tags"] = [{"i": -1, "u": 0.75,
                           "text": (f"Loss {pa} {_money(-a, UNIT)} -> {pb} {_money(-b, UNIT)}" if a < 0
                                    else f"{pb} loss {_money(-b, UNIT)}")}]
            nb["auto_tags"] = False
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["New Business", "JD Logistics"])),
        series_bars("JD Retail operating income", oi, "JD Retail"),
        nb,
        story.bars("Annual revenue", UNIT, d.points("Annual revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow", UNIT, d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
