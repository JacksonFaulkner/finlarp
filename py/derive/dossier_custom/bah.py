"""Booz Allen Hamilton: civil and commercial client revenue falls in FY2026 below its FY2024 level while
defense keeps growing, so annual revenue falls from its FY2025 high; civil keeps shrinking in the
latest quarter against a year earlier, and the annual operating margin comes off its FY2025 peak."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_peak_to_last, bars_year_ago, seg_tags, shaped, short, tagged

TICKER = "BAH"
SHORT = {"Civil and Commercial Clients": "Civil & commercial", "National Security Clients": "National security",
         "Defense Clients": "Defense"}


def specs(d: Data) -> list[dict]:
    cli = shaped(d.history(("MajorCustomersAxis",)))
    cli_q = shaped(d.history(("MajorCustomersAxis",), cadence="quarterly", n=2))
    rev = d.points("Annual revenue")
    q = d.points("Quarterly revenue")
    om = d.points("Operating margin, annual")
    beats = [
        cli and story.towers("Revenue by client group", cli, tags=short(seg_tags(cli, ["Civil", "Defense"]), SHORT)),
        cli_q and story.towers("Same quarter a year apart", cli_q, tags=short(seg_tags(cli_q, ["Civil", "National Security"]), SHORT)),
        tagged(story.bars("Annual revenue", "$M", rev), bars_peak_to_last(rev, "$M")),
        tagged(story.bars("Quarterly revenue", "$M", q), bars_year_ago(q)),
        tagged(story.bars("Operating margin, annual", "%", om), bars_peak_to_last(om, "%")),
    ]
    return [story.scene(d.name("financials"), beats)]
