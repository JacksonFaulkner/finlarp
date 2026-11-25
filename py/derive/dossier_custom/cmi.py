"""Cummins: Distribution grows while Components shrinks, power generation in the distribution
business roughly doubles as on-highway and heavy-duty truck sales fall, and Power Systems leads the
latest quarter's growth."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "CMI"
NAMES = {"Onhighway": "On-highway", "Emissionsolutions": "Emission solutions",
         "Mediumdutytruckandbus": "Medium-duty truck and bus", "Heavydutytruck": "Heavy-duty truck",
         "Lightdutyautomotive": "Light-duty automotive", "Offhighway": "Off-highway"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=seg_tags(seg, ["Distribution", "Components"])),
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["DBU Power Generation", "On-highway"])),
        seg_q and story.towers("Same quarter a year apart", seg_q, tags=[growth(seg_q, "Power Systems")]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
