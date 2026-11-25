"""MKS: semiconductor and electronics-and-packaging revenue grow while specialty industrial
shrinks, every division grows in the latest quarter year on year, operating margin jumps to 20%,
and China's share of revenue passes the US's."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, pct_tags, seg_tags, shaped, short

TICKER = "MKSI"
GEO = {"CN": "China", "US": "US", "KR": "Korea", "SG": "Singapore", "TW": "Taiwan", "JP": "Japan", "MY": "Malaysia",
       "Other Countries": "Other countries"}
SHORT = {"Electronics and Packaging": "Elec. & packaging", "Photonics Solutions Division": "Photonics",
         "Vacuum Solutions Division": "Vacuum", "Specialty Industrial": "Specialty industrial"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)))
    seg_q = shaped(d.history(("StatementBusinessSegmentsAxis",), cadence="quarterly", n=2))
    geo = shaped(d.history(("StatementGeographicalAxis",)), GEO)
    beats = [
        prod and story.towers("Revenue by end market", prod,
                              tags=short(seg_tags(prod, ["Electronics and Packaging", "Specialty Industrial"]), SHORT)),
        seg_q and story.towers("Divisions, same quarter a year apart", seg_q,
                               tags=short([growth(seg_q, "Photonics"), growth(seg_q, "Vacuum", u=0.85)], SHORT)),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        geo and story.towers("Revenue share by region", geo, pct=True, tags=pct_tags(geo, ["China", "US"])),
    ]
    return [story.scene(d.name("financials"), beats)]
