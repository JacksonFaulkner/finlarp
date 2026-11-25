"""Tyler Technologies: subscriptions grow while maintenance and software licenses shrink, recurring
revenue rises to most of the total, and gross and operating margins widen."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import pct_tags, seg_tags, shaped, short, tagged

TICKER = "TYL"
NAMES = {"Subscription and Circulation": "Subscriptions"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    rec = shaped(d.history(("MajorCustomersAxis",)))
    om = d.points("Operating margin, annual")
    beats = [
        prod and story.towers("Revenue by type", prod, tags=short(seg_tags(prod, ["Subscriptions", "Software Licenses"]),
                                                                   {"Software Licenses and Royalties": "Licenses"})),
        rec and story.towers("Recurring vs nonrecurring revenue", rec, pct=True, tags=pct_tags(rec, ["Recurring"])),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Gross margin", "%", d.points("Gross margin, quarterly")),
        tagged(story.bars("Operating margin, annual", "%", om), om and {"i": -1, "u": 0.75, "text": f"{om[0][0]} {om[0][1]:.1f}% -> {om[-1][0]} {om[-1][1]:.1f}%"}),
    ]
    return [story.scene(d.name("financials"), beats)]
