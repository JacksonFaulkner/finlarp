"""Autodesk: architecture/engineering/construction leads the growth, sales flip from mostly
through intermediaries to mostly direct within a year, and the operating margin climbs toward 30%
at a steady ~91% gross margin."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped

TICKER = "ADSK"
NAMES = {"Architecture Engineering Construction": "Architecture, Engineering, Construction & Ops",
         "Auto CA Dand Auto CADLT": "AutoCAD and AutoCAD LT Family"}


def _short(tag: dict | None, name: str, short: str) -> dict | None:
    """A computed tag with a long series name swapped for its initials, so it fits the frame."""
    return tag and {**tag, "text": tag["text"].replace(name, short)}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    chan = shaped(d.history(("ContractWithCustomerSalesChannelAxis",)))
    beats = [
        prod and story.towers("Revenue by product family", prod, tags=[_short(t, NAMES["Architecture Engineering Construction"], "AEC")
                                                                       for t in seg_tags(prod, ["Architecture", "Manufacturing"])]),
        chan and story.towers("Revenue share by sales channel", chan, pct=True, tags=pct_tags(chan, ["Direct"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
