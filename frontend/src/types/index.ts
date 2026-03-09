export interface CompanyInfo {
  ticker: string;
  name: string;
  market: 'US' | 'KR' | 'JP' | 'EU';
  sector: string;
  industry: string;
  currency: string;
  exchange: string;
}

export interface FinancialStatement {
  year: number;
  revenue: number | null;
  cost_of_revenue: number | null;
  gross_profit: number | null;
  operating_income: number | null;
  net_income: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_equity: number | null;
  total_debt: number | null;
  cash_and_equivalents: number | null;
  operating_cash_flow: number | null;
  capital_expenditure: number | null;
  free_cash_flow: number | null;
  ebitda: number | null;
  depreciation: number | null;
  interest_expense: number | null;
  tax_expense: number | null;
  dividends_paid: number | null;
  shares_outstanding: number | null;
  eps: number | null;
  currency: string;
}

export interface FinancialMetrics {
  year: number;
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  interest_coverage: number | null;
  asset_turnover: number | null;
  revenue_growth: number | null;
  earnings_growth: number | null;
  fcf_margin: number | null;
}

export interface SWOTItem {
  point: string;
  evidence: string;
  data_reference: string | null;
}

export interface SWOTAnalysis {
  strengths: SWOTItem[];
  weaknesses: SWOTItem[];
  opportunities: SWOTItem[];
  threats: SWOTItem[];
  summary: string;
}

export interface InvestmentAnalysisItem {
  title: string;
  content: string;
  details: string[];
}

export interface PriceScenario {
  name: string;
  target_price: number;
  reasoning: string;
}

export interface TargetPriceAnalysis {
  current_price: number;
  target_price: number;
  upside_pct: number;
  methodology: string;
  assumptions: string[];
  scenarios: PriceScenario[];
}

export interface InvestmentAnalysis {
  investment_thesis: InvestmentAnalysisItem[];
  key_catalysts: InvestmentAnalysisItem[];
  target_price: TargetPriceAnalysis;
  key_risks: InvestmentAnalysisItem[];
  summary: string;
  recommendation: string;
}

export interface DCFAssumption {
  parameter: string;
  value: number;
  unit: string;
  reasoning: string;
  evidence: string[];
}

export interface DCFProjection {
  year: number;
  revenue: number;
  ebitda: number;
  free_cash_flow: number;
  discount_factor: number;
  present_value: number;
}

export interface DCFResult {
  assumptions: DCFAssumption[];
  projections: DCFProjection[];
  terminal_value: number;
  terminal_value_pv: number;
  enterprise_value: number;
  equity_value: number;
  shares_outstanding: number;
  intrinsic_value_per_share: number;
  current_price: number;
  upside_downside_pct: number;
  sensitivity_matrix: {
    wacc_values: string[];
    terminal_growth_values: string[];
    intrinsic_values: Record<string, Record<string, number | null>>;
  };
  methodology_notes: string[];
  currency: string;
}
