"""American Tower: in the latest quarter against a year earlier, US and Canada property revenue
and income slip while Latin America and Africa/APAC grow, services revenue halves, and free cash
flow holds near $1B a quarter."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "AMT"
NAMES = {"Property US and Canada": "US and Canada", "Property Latin America": "Latin America",
         "Property Africa APAC": "Africa and APAC", "Property Europe": "Europe"}


def _regions(hist: dict | None) -> dict | None:
    """Drop the "Property" total, which overlaps the regional property members."""
    if not hist:
        return None
    ser = [s for s in hist["series"] if s[0] != "Property"]
    return {**hist, "series": ser} if len(ser) >= 2 else None


def specs(d: Data) -> list[dict]:
    # the Financials tab's revenue and margin series do not reconcile with segment revenue for AMT,
    # so the story uses segment facts and cash flow only
    rev = shaped(_regions(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2)), NAMES)
    oi = shaped(_regions(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True)), NAMES)
    beats = [
        rev and story.towers("Property regions and services, a year apart", rev,
                             tags=seg_tags(rev, ["US and Canada", "Services"])),
        oi and story.towers("Operating income, same quarter a year apart", oi,
                            tags=seg_tags(oi, ["US and Canada", "Latin America"])),
        story.bars("Free cash flow, quarterly", "$M", d.points("Free cash flow, quarterly")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
