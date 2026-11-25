"""Salesforce: every subscription line grows each year with the platform line growing fastest,
the latest quarter's Data 360 line outgrows the apps, operating margin sits near 20%, and free cash
flow nearly triples in four years."""
from __future__ import annotations

from derive.dossier_custom import Data, story
from derive.dossier_custom.story import growth, seg_tags, shaped

TICKER = "CRM"
NAMES = {"Professional Servicesand": "Professional Services & Other",
         "Agentforce 360 Platform Slack": "Agentforce 360 Platform, Slack & Other"}


def specs(d: Data) -> list[dict]:
    prod = shaped(d.history(("ProductOrServiceAxis",)), NAMES)
    prod_q = shaped(d.history(("ProductOrServiceAxis",), cadence="quarterly", n=2), NAMES)
    beats = [
        prod and story.towers("Revenue by product line", prod, tags=seg_tags(prod, ["Agentforce 360", "Agentforce Service"])),
        prod_q and story.towers("Same quarter a year apart", prod_q,
                                tags=[growth(prod_q, "Data 360"), growth(prod_q, "Agentforce Apps", u=0.8)]),
        story.bars("Quarterly revenue", "$M", d.points("Quarterly revenue")),
        story.bars("Operating margin", "%", d.points("Operating margin, quarterly")),
        story.bars("Free cash flow", "$M", d.points("Free cash flow, annual")),
    ]
    return [story.scene(d.name("financials"), beats)]
