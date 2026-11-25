"""FPS: revenue nearly doubles in FY2026 as powertrain solutions more than triple and custom
products grow by about two thirds, and the operating margin climbs from a weak FY2025 Q4 to about
20% a year later. The Financials tab has no Q1 figures, so year-ago tags match quarter labels."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import money, seg_tags, shaped, tagged

TICKER = "FPS"


def _vs_label(points: list[list], unit: str, u: float = 0.75) -> dict | None:
    """Latest quarter vs the point with the same quarter label a year earlier (Q4'26 vs Q4'25):
    the series skips Q1s, so 'four points back' would not be a year."""
    if len(points) < 2:
        return None
    pb, b = points[-1]
    qa = f"{pb[:3]}{int(pb[3:]) - 1:02d}"
    a = next((v for p, v in points if p == qa), None)
    if a is None:
        return None
    if unit == "%":
        return {"i": -1, "u": u, "text": f"{pb} {b:.1f}% vs {qa} {a:.1f}%"}
    ch = f"{b / a:.1f}x" if a > 0 and b / a >= 2 else (f"{(b / a - 1) * 100:+.0f}%" if a > 0 else "")
    return {"i": -1, "u": u, "text": f"{pb} {money(b, unit)} vs {qa} {money(a, unit)} ({ch})"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        prod and story.towers("Revenue by product", prod, tags=seg_tags(prod, ["Powertrain", "Custom"])),
        tagged(story.bars("Quarterly revenue (no Q1 figures)", "$M", q), _vs_label(q, "$M")),
        tagged(story.bars("Operating margin (no Q1 figures)", "%", om), _vs_label(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
