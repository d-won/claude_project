from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Market(str, Enum):
    US = "US"
    KR = "KR"
    JP = "JP"
    EU = "EU"


class CompanySearchRequest(BaseModel):
    query: str = Field(..., description="Company name or ticker symbol")
    market: Optional[Market] = Field(None, description="Filter by market")


class CompanyInfo(BaseModel):
    ticker: str
    name: str
    market: Market
    sector: str
    industry: str
    currency: str
    exchange: str


class FinancialDataRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol (e.g., AAPL, 005930.KS)")
    years: int = Field(default=10, ge=7, le=15, description="Number of years of data")


class DCFRequest(BaseModel):
    ticker: str
    years: int = Field(default=10, ge=7, le=15)
    projection_years: int = Field(default=5, ge=3, le=10)
    custom_wacc: Optional[float] = Field(None, ge=0.01, le=0.30)
    custom_growth_rate: Optional[float] = Field(None, ge=-0.10, le=0.50)
    custom_terminal_growth: Optional[float] = Field(None, ge=0.0, le=0.05)


class SWOTRequest(BaseModel):
    ticker: str
    years: int = Field(default=10, ge=7, le=15)


class FinancialStatement(BaseModel):
    year: int
    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cash_flow: Optional[float] = None
    ebitda: Optional[float] = None
    depreciation: Optional[float] = None
    interest_expense: Optional[float] = None
    tax_expense: Optional[float] = None
    dividends_paid: Optional[float] = None
    shares_outstanding: Optional[float] = None
    eps: Optional[float] = None
    currency: str = "USD"


class FinancialMetrics(BaseModel):
    year: int
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    roic: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    asset_turnover: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    fcf_margin: Optional[float] = None


class SWOTItem(BaseModel):
    point: str
    evidence: str
    data_reference: Optional[str] = None


class SWOTAnalysis(BaseModel):
    strengths: list[SWOTItem]
    weaknesses: list[SWOTItem]
    opportunities: list[SWOTItem]
    threats: list[SWOTItem]
    summary: str


class DCFAssumption(BaseModel):
    parameter: str
    value: float
    unit: str
    reasoning: str
    evidence: list[str]


class DCFProjection(BaseModel):
    year: int
    revenue: float
    ebitda: float
    free_cash_flow: float
    discount_factor: float
    present_value: float


class DCFResult(BaseModel):
    assumptions: list[DCFAssumption]
    projections: list[DCFProjection]
    terminal_value: float
    terminal_value_pv: float
    enterprise_value: float
    equity_value: float
    shares_outstanding: float
    intrinsic_value_per_share: float
    current_price: float
    upside_downside_pct: float
    sensitivity_matrix: dict
    methodology_notes: list[str]
    currency: str = "USD"
