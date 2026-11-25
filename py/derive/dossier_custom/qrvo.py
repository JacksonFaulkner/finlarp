"""Qorvo: High Performance Analog grows while Advanced Cellular shrinks, CSG's segment operating loss
narrows each year, and China's share of revenue falls as the US rises; in the latest quarter HPA is up
by half against a year earlier and China roughly halves. The Financials tab's revenue and margin series
stop in fiscal 2015 (predecessor data), so no quarterly revenue or margin beats are shown."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, money, pct_tags, seg_tags, shaped

TICKER = "QRVO"
GEO = {"CN": "China", "TW": "Taiwan", "US": "US"}


def _loss(hist: dict | None, prefix: str, u: float = 0.85) -> dict | None:
    """'<name> loss $a -> $b' for a segment whose operating income is negative in both end periods."""
    k = next((k for k, (n, _) in enumerate((hist or {}).get("series", [])) if n.startswith(prefix)), None)
    if k is None:
        return None
    name, vs = hist["series"][k]
    if vs[0] >= 0 or vs[-1] >= 0:
        return None
    return {"i": -1, "s": k, "u": u, "text": f"{name} loss {money(-vs[0])} -> {money(-vs[-1])}"}


def specs(d: Data) -> list[dict]:
    # n=3: the segment axis also carries two FY2013-14 periods with no member values
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",), n=3))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), n=3, oi=True))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), GEO)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["HPA", "ACG"])),
        oi and story.towers("Operating income by segment", oi, tags=[growth(oi, "HPA", u=0.55), _loss(oi, "CSG")]),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=seg_tags(seg_q, ["HPA", "ACG"])),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=[growth(geo_q, "China")]),
    ]
    return [story.scene(d.name("financials"), beats)]
