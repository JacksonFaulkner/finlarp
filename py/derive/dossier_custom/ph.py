"""Parker-Hannifin: Aerospace Systems grows while Diversified Industrial is flat, aerospace operating
income and its margin climb fastest, and the company's operating margin rises."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "PH"
AX = ("StatementBusinessSegmentsAxis",)


def _margin_tag(rev: dict, oi: dict, prefix: str, u: float = 0.85) -> dict | None:
    """'<name> margin a% -> b%': segment operating income over segment revenue, first vs last period."""
    k = next((j for j, (n, _) in enumerate(oi["series"]) if n.startswith(prefix)), None)
    r = next((vs for n, vs in rev["series"] if n.startswith(prefix)), None)
    if k is None or not r or rev["periods"] != oi["periods"] or not r[0] or not r[-1]:
        return None
    o = oi["series"][k][1]
    return {"i": -2, "s": k, "u": u,
            "text": f"{oi['series'][k][0]} margin {o[0] / r[0] * 100:.0f}% -> {o[-1] / r[-1] * 100:.0f}%"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(AX))
    oi = shaped(d.history(AX, oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Aerospace"])),
        oi and story.towers("Operating income by segment", oi,
                            tags=[growth(oi, "Aerospace", u=0.6), seg and _margin_tag(seg, oi, "Aerospace")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
