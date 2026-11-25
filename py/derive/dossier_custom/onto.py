"""Onto Innovation: Taiwan and Korea become its largest markets while China roughly halves, the US
triples in the latest quarter against a year earlier, and quarterly operating margin falls to about
5% before recovering to about 18% as quarterly revenue reaches a new high."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged, total_of

TICKER = "ONTO"
NAMES = {"TW": "Taiwan", "KR": "Korea", "US": "US", "JP": "Japan", "CN": "China"}


def _fiscal_labels(hist: dict | None, annual: list[list]) -> dict | None:
    """Relabel each period with the Annual revenue block's label whose value equals the period's
    member total (fiscal 2025 ended 2026-01-03, so the segment facts call it FY2026)."""
    if not hist:
        return None
    periods = []
    for i, p in enumerate(hist["periods"]):
        tot = total_of(hist, i)
        yr = lambda lbl: int(lbl[2:]) if lbl[2:].isdigit() else 0  # noqa: E731
        hits = [x for x, v in annual if abs(v - tot) <= max(1.0, 0.002 * v) and abs(yr(x) - yr(p)) <= 1]
        periods.append(min(hits, key=lambda x: abs(yr(x) - yr(p))) if hits else p)
    return {**hist, "periods": periods}


def specs(d: Data) -> list[dict]:
    rev = d.points("Annual revenue")
    geo = _fiscal_labels(shaped(d.history(("StatementGeographicalAxis",)), NAMES), rev)
    geo_q = shaped(d.history(("StatementGeographicalAxis",), cadence="quarterly", n=2), NAMES)
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, quarterly")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Taiwan", "China"])),
        geo_q and story.towers("Regions, same quarter a year apart", geo_q, tags=[growth(geo_q, "US")]),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin", "%", om), bars_swing(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
