"""Structured financial-statement extraction models for the earnings POC.

The model describes what a filing reports; it does not calculate derived
values. Keep the filing and table evidence beside each line item so extracted
values can be checked against the SEC filing and XBRL facts.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


Statement = Literal["income", "cash_flow", "balance_sheet"]
RowRole = Literal["detail", "subtotal", "total"]
LineItemKind = Literal[
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "research_and_development",
    "sales_general_and_administrative",
    "depreciation_and_amortization",
    "other_operating_expense",
    "total_operating_expenses",
    "operating_income",
    "interest_and_other_nonoperating",
    "nonoperating_total",
    "pretax_income",
    "income_tax",
    "net_income",
    "capital_expenditures",
    "debt_repayment",
    "debt_proceeds",
    "cash_from_operations",
    "cash_and_equivalents",
    "debt_balance",
    "other",
]


class EvidencePointer(BaseModel):
    """Pointer into a caller-supplied source catalog, never a model-invented URL."""

    source_id: str = Field(
        description="ID of a supplied filing/web source; the application resolves this to its trusted URL",
    )
    quote: str = Field(
        description="Short verbatim excerpt from that source supporting this exact value or claim",
    )


class StatementLineItem(BaseModel):
    """One filing row, preserving its original label and source evidence."""

    kind: LineItemKind
    row_role: RowRole = Field(
        description="detail contributes to a subtotal; subtotal/total already includes lower-level rows",
    )
    label: str = Field(description="Exact or near-exact row label in the filing")
    value: float | None = Field(
        description="Numeric value as shown; parenthesized amounts are negative; null if absent",
    )
    unit: str = Field(description="For example USD, USD/shares, or shares")
    period_start: str | None = Field(description="YYYY-MM-DD; null for point-in-time facts")
    period_end: str = Field(description="YYYY-MM-DD")
    statement: Statement
    evidence: EvidencePointer
    xbrl_concept: str | None = Field(
        default=None,
        description="Matching XBRL concept when visible in the supplied filing context",
    )


class EarningsStatementExtraction(BaseModel):
    """Quarterly statement rows extracted from one SEC filing."""

    ticker: str
    company: str
    form: Literal["10-Q", "10-K", "20-F", "40-F"]
    accession: str
    filing_source_id: str = Field(
        description="ID of the target filing in the caller-supplied source catalog",
    )
    filed: str = Field(description="Filing date, YYYY-MM-DD")
    fiscal_period: str = Field(description="Issuer fiscal label, such as FY2027 Q2")
    period_start: str = Field(description="Quarter start, YYYY-MM-DD")
    period_end: str = Field(description="Quarter end, YYYY-MM-DD")
    currency: str = "USD"
    line_items: list[StatementLineItem] = Field(default_factory=list)


# General per-security report panels. These discriminators mirror the
# finlarp Block enum; every factual leaf carries EvidencePointer.
PanelCategory = Literal[
    "business_model", "products", "end_markets", "customer_map",
    "financials", "cash_flow", "balance_sheet", "catalysts", "risks",
    "competitive_position", "other",
]
ClaimStatus = Literal["reported", "inferred", "derived"]


class SourcedRow(BaseModel):
    id: str = Field(description="Stable row key for selection and cross-panel linking")
    cells: list[str]
    status: ClaimStatus
    evidence: EvidencePointer


class SourcedKv(BaseModel):
    id: str
    label: str
    value: str
    status: ClaimStatus
    evidence: EvidencePointer


class SourcedPoint(BaseModel):
    id: str
    x: str
    y: float | None
    status: ClaimStatus
    evidence: EvidencePointer


class SourcedBar(BaseModel):
    id: str
    label: str
    value: float
    compare: float | None
    status: ClaimStatus
    evidence: EvidencePointer


class ReportTable(BaseModel):
    type: Literal["table"]
    title: str
    cols: list[str]
    rows: list[SourcedRow]


class ReportKv(BaseModel):
    type: Literal["kv"]
    title: str
    rows: list[SourcedKv]


class ReportSeries(BaseModel):
    type: Literal["series"]
    title: str
    unit: str
    points: list[SourcedPoint]


class ReportBars(BaseModel):
    type: Literal["bars"]
    title: str
    unit: str
    items: list[SourcedBar]


class ReportText(BaseModel):
    type: Literal["text"]
    title: str
    text: str
    status: ClaimStatus
    evidence: EvidencePointer


ReportBlock = Annotated[
    Union[ReportTable, ReportKv, ReportSeries, ReportBars, ReportText],
    Field(discriminator="type"),
]


class ReportSection(BaseModel):
    id: str
    title: str
    category: PanelCategory
    blocks: list[ReportBlock]


class SecurityReportPanels(BaseModel):
    """OpenAI-generated company-specific panels, each data item source-linked."""

    sections: list[ReportSection]
