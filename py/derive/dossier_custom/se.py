"""Sea Limited: Shopee e-commerce carries most of the revenue growth, the Monee financial services
segment more than doubles in two years, Latin America grows fastest of the disclosed regions, and
free cash flow swings from outflows to a growing inflow."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import seg_tags, shaped, short, with_unit

TICKER = "SE"
NAMES = {"E Commerce Shopee": "E-commerce (Shopee)", "Digital Financial Services Monee": "Digital Financial Services (Monee)",
         "Digital Entertainment Garena": "Digital Entertainment (Garena)"}
SHORT = {"E-commerce (Shopee)": "Shopee", "Digital Financial Services (Monee)": "Monee"}
UNIT = "$M"  # the segment facts' unit id is an opaque "U002" (USD filer) that the shared parser cannot read


def specs(d: Data) -> list[dict]:
    seg = with_unit(shaped(d.history(("StatementBusinessSegmentsAxis",)), NAMES), UNIT)
    geo = with_unit(shaped(d.history(("StatementGeographicalAxis",))), UNIT)
    # the Annual revenue block disagrees with the segment totals, so no revenue/margin bars here
    beats = [
        seg and story.towers("Revenue by segment", seg, tags=short(seg_tags(seg, ["E-commerce", "Digital Financial"]), SHORT)),
        geo and story.towers("Revenue by region (as disclosed)", geo, tags=seg_tags(geo, ["Latin America"])),
        story.bars("Free cash flow, annual", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
