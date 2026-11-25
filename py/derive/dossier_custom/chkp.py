"""Check Point: security subscriptions grow into the largest line while software updates and
maintenance stay flat, revenue rises every year, and operating margin slides year after year."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_swing, pct_tags, seg_tags, shaped, short, tagged

TICKER = "CHKP"
GEO = {"IL": "Israel"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    om = d.points("Operating margin, annual")
    peak = max(om, key=lambda p: p[1]) if om else None
    om_tag = peak and peak != om[-1] and {"i": -1, "u": 0.75,
                                          "text": f"{peak[0]} {peak[1]:.1f}% -> {om[-1][0]} {om[-1][1]:.1f}%"}
    beats = [
        prod and story.towers("Revenue by product", prod,
                              tags=short(seg_tags(prod, ["Security Subscriptions", "Software Updates"]),
                                         {"Software Updates and Maintenance": "Updates & maint.",
                                          "Security Subscriptions": "Subscriptions"})),
        prod and story.towers("Revenue share by product", prod, pct=True, tags=pct_tags(prod, ["Security Subscriptions"])),
        geo and story.towers("Revenue by region", geo, tags=seg_tags(geo, ["Asia Pacific"])),
        story.bars("Annual revenue", "$M", d.points("Annual revenue")),
        tagged(story.bars("Operating margin", "%", om), om_tag or bars_swing(om)),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
