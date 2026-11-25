"""Match Group: Hinge grows about 1.7x in two years and more than doubles its operating income while
Tinder's revenue and operating income slip, and quarterly operating margin rises on a year earlier.
Only FY2021 on is used: earlier XBRL history belongs to the predecessor IAC."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_year_ago, seg_tags, shaped, tagged

TICKER = "MTCH"
FIRST_YEAR = 2021  # the separation from IAC closed in 2020; earlier XBRL periods are IAC's


def _current(pts: list[list]) -> list[list]:
    return [p for p in pts if not str(p[0]).startswith("FY") or int(str(p[0])[2:]) >= FIRST_YEAR]


def _first_to_last(pts: list[list], u: float = 0.75) -> dict | None:
    if len(pts) < 2 or pts[0][1] <= 0:
        return None
    (pa, a), (pb, b) = pts[0], pts[-1]
    return {"i": -1, "u": u, "text": f"{pa} -> {pb}: {(b / a - 1) * 100:+.0f}%"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = shaped(d.history(("StatementBusinessSegmentsAxis",), oi=True))
    om = d.points("Operating margin, quarterly")
    fcf = _current(d.points("Free cash flow, annual"))
    beats = [
        seg and story.towers("Revenue by brand segment", seg, tags=seg_tags(seg, ["Hinge", "Tinder"])),
        oi and story.towers("Operating income by segment", oi, tags=seg_tags(oi, ["Hinge", "Tinder"])),
        tagged(story.bars("Operating margin", "%", om), bars_year_ago(om, "%")),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), _first_to_last(fcf)),
    ]
    return [story.scene(d.name("financials"), beats)]
