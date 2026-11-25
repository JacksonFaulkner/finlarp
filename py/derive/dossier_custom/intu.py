"""Intuit: Global Business Solutions outgrows Consumer and earns most of the segment operating
income, revenue spikes every tax-season quarter, and the annual operating margin and free cash flow
both climb."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, share

TICKER = "INTU"


def _same_q(points: list[list]) -> list[dict]:
    """The latest quarter against the one four quarters earlier (tax season repeats yearly)."""
    if len(points) < 5 or not points[-5][1]:
        return []
    (pa, a), (pb, b) = points[-5], points[-1]
    return [{"i": len(points) - 1, "u": 0.75, "text": f"{pb} vs {pa}: {(b / a - 1) * 100:+.0f}%"}]


def _tax_peak(points: list[list]) -> list[dict]:
    if len(points) < 5:
        return []
    i = max(range(len(points)), key=lambda j: points[j][1])
    j = i - 4
    if j < 0 or not points[j][1]:
        return []
    return [{"i": i, "u": 0.8,
             "text": f"Peak {points[i][0]} ${points[i][1] / 1e3:.1f}B, {(points[i][1] / points[j][1] - 1) * 100:+.0f}% vs {points[j][0]}"}]


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    q = story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue"))
    if q:
        q["tags"], q["auto_tags"] = _tax_peak(q["points"]) + _same_q(q["points"]), False
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Global Business", "Consumer"])),
        oi and story.towers("Segment operating income", oi, tags=[share(oi, "Global Business")]),
        q,
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
