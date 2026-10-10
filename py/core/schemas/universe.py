"""The stock universe: one `Stock` per tracked ticker, stored in DuckDB (ai_universe*)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

Kind = Literal["stock", "etf", "foreign"]  # foreign = local-exchange line (005930.KS), not a US-listed ADR

WEIGHT_TOL = 0.01


class Stock(BaseModel):
    ticker: str
    name: str
    region: str
    kind: Kind = "stock"
    subs: dict[str, float]  # sub-bucket -> weight, sums to 1
    primary: dict[str, float] = {}  # derived from subs via the taxonomy, see with_primary()
    eligible: bool | None = None  # False hides it from the universe; None = unverified
    status: str | None = None
    category_confidence: str | None = None
    rationale: str | None = None
    source_url: str | None = None
    reviewed_on: str | None = None

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def _weights(self):
        if any(w <= 0 for w in self.subs.values()):
            raise ValueError(f"{self.ticker}: weights must be positive")
        total = sum(self.subs.values())
        if abs(total - 1) > WEIGHT_TOL:
            raise ValueError(f"{self.ticker}: sub weights sum to {total:.3f}, not 1")
        return self

    def check_taxonomy(self, taxonomy: dict[str, list[str]]) -> None:
        known = {sub for subs in taxonomy.values() for sub in subs}
        bad = sorted(set(self.subs) - known)
        if bad:
            raise ValueError(f"{self.ticker}: unknown buckets {bad}")

    def with_primary(self, taxonomy: dict[str, list[str]]) -> Stock:
        """Primary weights are never authored, only summed from subs."""
        parent = {sub: p for p, subs in taxonomy.items() for sub in subs}
        primary: dict[str, float] = {}
        for sub, w in self.subs.items():
            primary[parent[sub]] = round(primary.get(parent[sub], 0) + w, 6)
        return self.model_copy(update={"primary": primary})

    @property
    def dominant_sub(self) -> str:
        return max(self.subs.items(), key=lambda kv: kv[1])[0]


def infer_kind(ticker: str, quote_type: str | None = None) -> Kind:
    """A dotted ticker is a local-exchange line. US-listed ADRs (TSM, ASML) are plain stocks."""
    if quote_type == "ETF":
        return "etf"
    return "foreign" if "." in ticker else "stock"
