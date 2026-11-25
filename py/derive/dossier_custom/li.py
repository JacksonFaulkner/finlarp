"""Li Auto: revenue, nearly all from vehicle sales, peaks in FY2024 and falls back in FY2025, gross
margin slips to its lowest of the five years, operating margin turns slightly negative after two
profitable years, and free cash flow swings from a large FY2023 inflow to an FY2025 outflow.
Quarterly Financials data covers only two old quarters (20-F filer), so quarterly beats are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _find, money, shaped, tagged

TICKER = "LI"
UNIT = "CNY M"


def _peak_to_last(pts: list[list], unit: str, u: float = 0.75) -> dict | None:
    if len(pts) < 2:
        return None
    i = max(range(len(pts)), key=lambda j: pts[j][1])
    if i == len(pts) - 1:
        return None
    (pa, a), (pb, b) = pts[i], pts[-1]
    f = (lambda v: f"{v:.1f}%") if unit == "%" else (lambda v: money(v, unit))  # noqa: E731
    return {"i": -1, "u": u, "text": f"{pa} {f(a)} -> {pb} {f(b)}"}


def _last_step(hist: dict, prefix: str, u: float = 0.7) -> dict | None:
    k = _find(hist, prefix)
    if k is None or len(hist["periods"]) < 2:
        return None
    name, vs = hist["series"][k]
    if vs[-2] <= 0:
        return None
    return {"i": -1, "s": k, "u": u,
            "text": f"{name} {hist['periods'][-2]} -> {hist['periods'][-1]}: {(vs[-1] / vs[-2] - 1) * 100:+.0f}%"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    rev = d.points("Annual revenue")
    gm = d.points("Gross margin, annual")
    om = d.points("Operating margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=[_last_step(prod, "Vehicles")]),
        tagged(story.bars("Annual revenue", UNIT, rev), _peak_to_last(rev, UNIT)),
        tagged(story.bars("Gross margin, annual", "%", gm), _peak_to_last(gm, "%")),
        tagged(story.bars("Operating margin, annual", "%", om), _peak_to_last(om, "%")),
        tagged(story.bars("Free cash flow, annual", UNIT, fcf), _peak_to_last(fcf, UNIT)),
    ]
    return [story.scene(d.name("financials"), beats)]
