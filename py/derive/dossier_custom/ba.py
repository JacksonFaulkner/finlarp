"""Boeing: Commercial Airplanes revenue falls in FY2024 and recovers in FY2025 but loses money every
year, operating margin swings below zero in several quarters, and free cash flow is negative in
FY2024 and FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import series_bars, shaped

TICKER = "BA"
NAMES = {"Boeing Defense Space Security": "Defense Space and Security"}


def _dip(h: dict, prefix: str) -> dict | None:
    """'<name> FYa $x -> FYb $y (-n%)' pinned on the lowest tower of one series."""
    k = next((j for j, (n, _) in enumerate(h["series"]) if n.startswith(prefix)), None)
    if k is None:
        return None
    name, vs = h["series"][k]
    i = min(range(len(vs)), key=vs.__getitem__)
    if i == 0 or vs[i - 1] <= 0:
        return None
    p = h["periods"]
    return {"i": i, "s": k, "u": 0.7, "text": f"{name} {p[i - 1]} ${vs[i - 1] / 1e3:.1f}B -> {p[i]} "
                                             f"${vs[i] / 1e3:.1f}B ({(vs[i] / vs[i - 1] - 1) * 100:+.0f}%)"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True), NAMES)
    ca = series_bars("Commercial Airplanes operating income", oi, "Commercial Airplanes")
    if ca:
        loss = -sum(v for _, v in ca["points"] if v < 0)
        ca["tags"] = [{"i": -1, "text": f"{len(ca['points'])}-year loss ${loss / 1e3:.1f}B", "u": 0.75}]
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=[_dip(seg, "Commercial Airplanes")]),
        ca,
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
