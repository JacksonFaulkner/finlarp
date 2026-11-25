"""AeroVironment: FY2026 revenue more than doubles as a new Space, Cyber and Directed Energy segment
arrives and precision strike sales keep climbing, the US government becomes the dominant customer,
and gross margin drops from the high 30s while the operating margin swings into losses."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, growth, pct_tags, seg_tags, share, shaped, short, tagged

TICKER = "AVAV"
NAMES = {"Space Cyber and Directed Energy": "Space, Cyber and Directed Energy",
         "Non U. s. Government": "Non-US government", "Product and Service Other": "Other"}
SHORT = {"Space, Cyber and Directed Energy": "Space, Cyber, DE", "Precision Strike and Defense Systems":
         "Precision Strike", "Uncrewed Aircraft Systems": "Uncrewed aircraft"}


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES)
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    cust = shaped(d.history(("MajorCustomersAxis",)), NAMES)
    gm = d.points("Gross margin, quarterly")
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short([growth(seg, "Autonomous", u=0.55), share(seg, "Space", u=0.85)], SHORT)),
        prod and story.towers("Revenue by product line", prod,
                              tags=short(seg_tags(prod, ["Precision Strike", "Uncrewed"]), SHORT)),
        cust and story.towers("Revenue share by customer", cust, pct=True, tags=pct_tags(cust, ["US Government"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        tagged(story.bars("Gross margin", "%", gm), bars_peak_to_last(gm, "%")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
    ]
    return [story.scene(d.name("financials"), beats)]
