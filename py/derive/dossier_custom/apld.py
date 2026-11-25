"""Applied Digital: the HPC Hosting segment appears in FY2026 and is already the larger one, its
operating income turns from losses to a profit, while free cash flow burn deepens every year.
Quarterly revenue (a negative quarter), margins (over 100%) and FY2026 annual revenue (does not
match the segment total) look broken in the Financials blocks, so they are left out."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import bars_first_to_last, bars_swing, growth, series_bars, shaped, share, short, tagged

TICKER = "APLD"


def specs(d: Data) -> list[dict]:
    seg = shaped(d.history(("StatementBusinessSegmentsAxis",)))
    oi = d.history(("StatementBusinessSegmentsAxis",), oi=True)
    hpc = series_bars("HPC Hosting operating income", oi, "HPC")
    fcf = d.points("Free cash flow, annual")
    beats = [
        seg and story.towers("Revenue by segment", seg,
                             tags=short([share(seg, "HPC", u=0.6), growth(seg, "Data Center", u=0.85)],
                                        {"Data Center Hosting Business": "Data Center Hosting"})),
        hpc and tagged(hpc, bars_swing(hpc["points"], "$M")),
        series_bars("Data Center Hosting operating income", oi, "Data Center"),
        tagged(story.bars("Free cash flow, annual", "$M", fcf), bars_first_to_last(fcf, "$M")),
    ]
    return [story.scene(d.name("financials"), beats)]
