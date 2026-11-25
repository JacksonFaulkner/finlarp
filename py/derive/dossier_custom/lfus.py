"""Littelfuse: Electronics rebounds in FY2025 and Transportation's segment operating income grows about
2.5x; Industrial jumps by half in the latest quarter against a year earlier. Two fourth quarters with
large operating losses (gross margin holds, so the charges sit below gross profit) pull the annual
operating margin from about 20% in FY2022 to under 2% in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "LFUS"


def _low(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    i = min(range(len(pts)), key=lambda j: pts[j][1])
    return {"i": i, "u": u, "text": f"Low {pts[i][0]} {pts[i][1]:.1f}%"}


def _last_step(hist: dict | None, prefix: str, u: float = 0.55) -> dict | None:
    """'<name> +n% in <last period>': the change over the latest period only."""
    k = next((k for k, (n, _) in enumerate((hist or {}).get("series", [])) if n.startswith(prefix)), None)
    if k is None or hist["series"][k][1][-2] <= 0:
        return None
    name, vs = hist["series"][k]
    return {"i": -1, "s": k, "u": u, "text": f"{name} {(vs[-1] / vs[-2] - 1) * 100:+.0f}% in {hist['periods'][-1]}"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    q = d.points("Quarterly revenue")
    om_q = d.points("Operating margin, quarterly")
    om = d.points("Operating margin, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[_last_step(seg, "Electronics"), growth(seg, "Industrial", u=0.85)]),
        oi and story.towers("Segment operating income", oi, tags=seg_tags(oi, ["Transportation", "Electronics"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Industrial")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om_q), _low(om_q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
