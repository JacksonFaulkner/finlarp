"""Xcel Energy: regulated electric is most of revenue, quarterly revenue swings with the seasons around
a flat-to-rising line, and free cash flow is negative every year and deepens sharply in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import shaped, share

TICKER = "XEL"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    fcf = story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual"))
    if fcf:
        neg = sum(v for _, v in fcf["points"] if v < 0)
        (p0, v0), (p1, v1) = fcf["points"][0], fcf["points"][-1]
        fcf["tags"] = [{"i": 0, "u": 0.55, "text": f"{p0} -{story._money(-v0)}" if v0 < 0 else f"{p0} {story._money(v0)}"},
                       {"i": -1, "u": 0.75, "text": f"{p1} -{story._money(-v1)}, {len(fcf['points'])}-yr total -{story._money(-neg)}"}]
        fcf["auto_tags"] = False  # the default latest tag would sit on the same bar
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[share(seg, "Regulated Electric")]),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        fcf,
    ]
    return [story.scene(d.name("financials"), beats)]
