"""Avnet: revenue rebounds in FY2026 after two down years, Taiwan overtakes the US as the largest
region while Germany shrinks, quarterly revenue accelerates to a new high, but gross margin keeps
sliding and free cash flow turns negative."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_swing, bars_year_ago, growth, seg_tags, shaped, tagged

TICKER = "AVT"
GEO = {"TW": "Taiwan", "CN": "China", "DE": "Germany", "SG": "Singapore", "BE": "Belgium", "Other Foreign": "Other"}


def _merged(hist: dict | None) -> dict | None:
    """Series sharing a display name summed into one (the filer's "Other Foreign" and the countries
    shaped() folds into "Other" are one bucket)."""
    if not hist:
        return None
    out: dict[str, list[float]] = {}
    for n, vs in hist["series"]:
        out[n] = [round(a + b, 1) for a, b in zip(out[n], vs)] if n in out else list(vs)
    return {**hist, "series": [[n, vs] for n, vs in out.items()]}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    geo = _merged(shaped(d.history(("StatementGeographicalAxis",)), GEO))
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    gm = d.points("Gross margin, annual")
    fcf = d.points("Free cash flow, annual")
    beats = [
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Taiwan", "Germany"])),
        seg and story.towers("Revenue by segment", seg, tags=[growth(seg, "Electronic")]),
        tagged(story.bars("Annual revenue", "$M", rev), bars_swing(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Gross margin, annual", "%", gm), bars_peak_to_last(gm, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_peak_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
