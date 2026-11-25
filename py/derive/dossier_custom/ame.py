"""AMETEK: the Electromechanical group grows faster than the larger Electronic Instruments group,
automation and engineered solutions lead the product lines, and Electromechanical operating income
rises fastest in the latest quarter against a year earlier."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped

TICKER = "AME"
SHORT = {"Electromechanical Group": "Electromechanical", "Electronic Instruments Group": "Electronic Instruments",
         "Automation and Engineered Solutions": "Automation & Engineered", "Process and Analytical Instrumentation": "Process & Analytical"}

def _short(tags, names: dict) -> list:
    """`tags` with long series names shortened in the callout text only (the legend keeps the full name)."""
    out = []
    for t in tags if isinstance(tags, list) else [tags]:
        if t:
            for full, short in names.items():
                t["text"] = t["text"].replace(full, short)
            out.append(t)
    return out


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    oi_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2, oi=True))
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=_short(seg_tags(seg, ["Electromechanical", "Electronic Instruments"]), SHORT)),
        prod and story.towers("Revenue by product line", prod, tags=_short(seg_tags(prod, ["Automation", "Process"]), SHORT)),
        oi_q and story.towers("Segment operating income, same quarter a year apart", oi_q,
                              tags=_short(seg_tags(oi_q, ["Electromechanical", "Electronic Instruments"]), SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
    ]
    return [story.scene(d.name("financials"), beats)]
