"""Tower Semiconductor: annual revenue peaks in FY2022, dips, and recovers in FY2025; gross margin
eases from its FY2022 high; free cash flow falls from FY2023 to negative in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import _money, tagged

TICKER = "TSEM"


def _peak_to_last(pts: list[list], unit: str, u: float = 0.75) -> dict | None:
    """'<peak period> <v> -> <last period> <v>' (private: the shared bars_swing goes low -> latest)."""
    if len(pts) < 2:
        return None
    hi = max(range(len(pts)), key=lambda i: pts[i][1])
    if hi == len(pts) - 1:
        return None
    f = (lambda v: f"{v:.1f}%") if unit == "%" else (lambda v: _money(v, unit))  # noqa: E731
    return {"i": -1, "u": u, "text": f"{pts[hi][0]} {f(pts[hi][1])} -> {pts[-1][0]} {f(pts[-1][1])}"}


def specs(d: Data) -> list[dict]:
    # the "quarterly" series hold one Q2 per year (20-F filer), so the story is told on annual figures
    gm = d.points("Gross margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Gross margin, annual", "%", gm), _peak_to_last(gm, "%")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
