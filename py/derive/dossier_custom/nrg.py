"""NRG Energy: East grows into the largest segment while West shrinks, East's operating income swings
from a FY2023 loss to a profit, quarterly revenue spikes in Q1'26, and annual free cash flow turns
from negative in FY2023 to positive."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, bars_swing, seg_tags, series_bars, shaped, short, tagged

TICKER = "NRG"
NAMES = {"Vivint Smart Home": "Vivint Smart Home", "West Services": "West services and other"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    east = series_bars("East operating income", oi, "East")
    if east:
        (pa, a), (pb, b) = east["points"][0], east["points"][-1]
        east = tagged(east, {"i": -1, "u": 0.75, "text": f"{pa} {_money(a)} -> {pb} {_money(b)}"})
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["East", "West"]), {"West services and other": "West"})),
        east,
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_swing(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
