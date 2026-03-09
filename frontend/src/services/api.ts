import axios from 'axios';
import type {
  CompanyInfo, FinancialStatement, FinancialMetrics,
  SWOTAnalysis, DCFResult,
} from '../types';

const api = axios.create({ baseURL: '/api' });

export async function searchCompanies(
  query: string, market?: string
): Promise<CompanyInfo[]> {
  const params: Record<string, string> = { q: query };
  if (market) params.market = market;
  const { data } = await api.get('/companies/search', { params });
  return data.results;
}

export async function getFinancials(ticker: string, years = 10): Promise<{
  company: CompanyInfo;
  statements: FinancialStatement[];
  metrics: FinancialMetrics[];
}> {
  const { data } = await api.get(`/companies/${encodeURIComponent(ticker)}/financials`, {
    params: { years },
  });
  return data;
}

export async function getSWOT(ticker: string, years = 10): Promise<{
  company: CompanyInfo;
  swot: SWOTAnalysis;
  data_years: number;
  period: string;
}> {
  const { data } = await api.post('/analysis/swot', { ticker, years });
  return data;
}

export async function getDCF(params: {
  ticker: string;
  years?: number;
  projection_years?: number;
  custom_wacc?: number | null;
  custom_growth_rate?: number | null;
  custom_terminal_growth?: number | null;
}): Promise<{
  company: CompanyInfo;
  dcf: DCFResult;
  data_years: number;
  period: string;
}> {
  const { data } = await api.post('/analysis/dcf', {
    ticker: params.ticker,
    years: params.years ?? 10,
    projection_years: params.projection_years ?? 5,
    custom_wacc: params.custom_wacc,
    custom_growth_rate: params.custom_growth_rate,
    custom_terminal_growth: params.custom_terminal_growth,
  });
  return data;
}
