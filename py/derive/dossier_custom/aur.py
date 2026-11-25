"""Aurora: still pre-revenue in scale, it burns roughly $600M of free cash flow every year, the
quarterly burn reaches its largest in the latest quarter, and revenue only starts showing up from
Q2'25 in single-digit millions. Margins are left out (losses are hundreds of times revenue, so the
percentages are meaningless) and there are no segment splits."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import money, tagged

TICKER = "AUR"


def _total(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    return {"i": -1, "u": u, "text": f"{pts[0][0]}-{pts[-1][0]} total {money(sum(v for _, v in pts))}"}


def _first_revenue(pts: list[list], u: float = 0.75) -> dict | None:
    i = next((j for j, (_, v) in enumerate(pts) if v > 0), None)
    if i is None:
        return None
    return {"i": i, "u": u, "text": f"First revenue {pts[i][0]}: {money(pts[i][1])}"}


def _year_ago(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 5:
        return None
    (pa, a), (pb, b) = pts[-5], pts[-1]
    return {"i": -1, "u": u, "text": f"{pb} {money(b)} vs {pa} {money(a)}"}


def specs(d: Data) -> list[dict]:
    fcf = d.points("Free cash flow, annual")
    fcf_q = d.points("Free cash flow, quarterly")
    q = d.points("Quarterly revenue")
    beats = [
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _total(fcf)),
        tagged(story.bars("Free cash flow, quarterly", "$M", fcf_q), _year_ago(fcf_q)),
        tagged(story.bars("Quarterly revenue", "$M", q), _first_revenue(q)),
    ]
    return [story.scene(d.name("financials"), beats)]
