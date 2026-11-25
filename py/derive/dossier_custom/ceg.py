"""Constellation Energy: Mid-Atlantic and Midwest lead FY2025 growth, a new Calpine segment appears
in the latest quarter, operating margin swings from a loss to double digits, and free cash flow
turns positive in FY2025."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "CEG"
NAMES = {"Constellation Mid Atlantic": "Mid-Atlantic", "Constellation Midwest": "Midwest",
         "Constellation Other Regions": "Other regions", "Constellation New York": "New York",
         "Constellation ERCOT": "ERCOT", "Constellation Calpine": "Calpine"}


def _new(hist: dict | None, prefix: str) -> dict | None:
    """'<name> new: <money> in <period>' for a series that is zero in the first period."""
    k = next((k for k, (n, _) in enumerate(hist["series"]) if n.startswith(prefix)), None) if hist else None
    if k is None or hist["series"][k][1][0] != 0:
        return None
    name, vs = hist["series"][k]
    return {"i": -1, "s": k, "u": 0.7, "text": f"{name} new: {story._money(vs[-1], hist['unit'])} in {hist['periods'][-1]}"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by region", seg, tags=seg_tags(seg, ["Mid-Atlantic", "Midwest"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[_new(seg_q, "Calpine")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin, annual", "%", d.points("Operating margin, annual")),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
