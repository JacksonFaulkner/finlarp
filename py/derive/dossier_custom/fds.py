"""FactSet: revenue rises every quarter and every year across all three regional segments, but in
FY2026 segment operating income falls in the Americas and EMEA, and quarterly operating margin slides
from about 34% to about 25%; annual free cash flow still reaches a new high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _find, bars_year_ago, seg_tags, shaped, tagged

TICKER = "FDS"


def _last_step(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    k = _find(hist, prefix)
    if k is None or len(hist["periods"]) < 2:
        return None
    name, vs = hist["series"][k]
    if vs[-2] <= 0:
        return None
    return {"i": -1, "s": k, "u": u,
            "text": f"{name} {hist['periods'][-2]} -> {hist['periods'][-1]}: {(vs[-1] / vs[-2] - 1) * 100:+.0f}%"}


def _peak_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    i = max(range(len(pts)), key=lambda j: pts[j][1])
    if i == len(pts) - 1:
        return None
    return {"i": -1, "u": u, "text": f"{pts[i][0]} {pts[i][1]:.1f}% -> {pts[-1][0]} {pts[-1][1]:.1f}%"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Americas", "Asia"])),
        oi and story.towers("Operating income by segment", oi,
                            tags=[_last_step(oi, "Americas", u=0.6), _last_step(oi, "EMEA", u=0.85)]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), _peak_to_last(om)),
        story.bars("Free cash flow, annual", "$M", fcf),
    ]
    return [story.scene(d.name("financials"), beats)]
