import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getFinancials, getInvestmentAnalysis, getDCF } from '../services/api';
import type {
  CompanyInfo, FinancialStatement, FinancialMetrics,
  InvestmentAnalysis, DCFResult,
} from '../types';
import {
  RevenueChart, MarginsChart, ReturnsChart,
  CashFlowChart, BalanceSheetChart, FinancialTable,
} from '../components/FinancialCharts';
import InvestmentAnalysisView from '../components/InvestmentAnalysisView';
import DCFView from '../components/DCFView';

type Tab = 'financials' | 'investment' | 'dcf';

export default function AnalysisPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [tab, setTab] = useState<Tab>('financials');
  const [years, setYears] = useState(10);

  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [statements, setStatements] = useState<FinancialStatement[]>([]);
  const [metrics, setMetrics] = useState<FinancialMetrics[]>([]);
  const [investmentAnalysis, setInvestmentAnalysis] = useState<InvestmentAnalysis | null>(null);
  const [dcf, setDCF] = useState<DCFResult | null>(null);

  const [loadingFin, setLoadingFin] = useState(false);
  const [loadingInvestment, setLoadingInvestment] = useState(false);
  const [loadingDcf, setLoadingDcf] = useState(false);
  const [error, setError] = useState('');

  // DCF custom params
  const [projYears, setProjYears] = useState(5);
  const [customWacc, setCustomWacc] = useState('');
  const [customGrowth, setCustomGrowth] = useState('');
  const [customTg, setCustomTg] = useState('');

  useEffect(() => {
    if (!ticker) return;
    loadFinancials();
  }, [ticker, years]);

  const loadFinancials = async () => {
    if (!ticker) return;
    setLoadingFin(true);
    setError('');
    try {
      const data = await getFinancials(ticker, years);
      setCompany(data.company);
      setStatements(data.statements);
      setMetrics(data.metrics);
    } catch (e: any) {
      setError(e?.response?.data?.detail || '재무 데이터를 불러오지 못했습니다');
    } finally {
      setLoadingFin(false);
    }
  };

  const loadInvestment = async () => {
    if (!ticker) return;
    setLoadingInvestment(true);
    try {
      const data = await getInvestmentAnalysis(ticker, years);
      setInvestmentAnalysis(data.analysis);
    } catch (e: any) {
      setError(e?.response?.data?.detail || '투자 분석을 생성하지 못했습니다');
    } finally {
      setLoadingInvestment(false);
    }
  };

  const loadDCF = async () => {
    if (!ticker) return;
    setLoadingDcf(true);
    try {
      const data = await getDCF({
        ticker,
        years,
        projection_years: projYears,
        custom_wacc: customWacc ? parseFloat(customWacc) / 100 : null,
        custom_growth_rate: customGrowth ? parseFloat(customGrowth) / 100 : null,
        custom_terminal_growth: customTg ? parseFloat(customTg) / 100 : null,
      });
      setDCF(data.dcf);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'DCF 밸류에이션을 수행하지 못했습니다');
    } finally {
      setLoadingDcf(false);
    }
  };

  const handleTabChange = (newTab: Tab) => {
    setTab(newTab);
    if (newTab === 'investment' && !investmentAnalysis && !loadingInvestment) loadInvestment();
    if (newTab === 'dcf' && !dcf && !loadingDcf) loadDCF();
  };

  const tabStyle = (t: Tab) => ({
    padding: '10px 24px',
    background: tab === t ? 'var(--accent-blue)' : 'transparent',
    color: tab === t ? '#fff' : 'var(--text-secondary)',
    border: tab === t ? 'none' : '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer' as const,
    transition: 'all 0.2s',
  });

  const marketFlag: Record<string, string> = {
    US: 'US', KR: 'KR', JP: 'JP', EU: 'EU',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Link to="/" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          &larr; 검색으로 돌아가기
        </Link>
      </div>

      {company && (
        <div className="company-header" style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          marginBottom: 24, flexWrap: 'wrap', gap: 16,
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
              <h1 style={{ fontSize: 28, fontWeight: 700 }}>{company.name}</h1>
              <span style={{
                fontSize: 12, padding: '4px 10px', borderRadius: 4,
                background: 'rgba(74, 158, 255, 0.1)', color: 'var(--accent-blue)', fontWeight: 600,
              }}>
                {marketFlag[company.market]} {company.ticker}
              </span>
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {company.sector} / {company.industry} | {company.exchange} | {company.currency}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <label style={{ fontSize: 13, color: 'var(--text-muted)' }}>데이터 기간:</label>
            <select
              value={years}
              onChange={(e) => setYears(Number(e.target.value))}
              style={{
                padding: '6px 12px', background: 'var(--bg-secondary)',
                border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)', fontSize: 13,
              }}
            >
              {[7, 8, 9, 10, 11, 12, 13, 14, 15].map((y) => (
                <option key={y} value={y}>{y}년</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {error && (
        <div style={{
          padding: 16, background: 'rgba(248, 113, 113, 0.1)',
          border: '1px solid rgba(248, 113, 113, 0.3)', borderRadius: 'var(--radius-sm)',
          color: 'var(--accent-red)', marginBottom: 16, fontSize: 14,
        }}>
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="tab-bar" style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <button style={tabStyle('financials')} onClick={() => handleTabChange('financials')}>
          재무제표
        </button>
        <button style={tabStyle('investment')} onClick={() => handleTabChange('investment')}>
          투자 분석
        </button>
        <button style={tabStyle('dcf')} onClick={() => handleTabChange('dcf')}>
          DCF 밸류에이션
        </button>
      </div>

      {/* Financials Tab */}
      {tab === 'financials' && (
        loadingFin ? (
          <LoadingSpinner text="재무 데이터 로딩 중..." />
        ) : statements.length > 0 ? (
          <div>
            <div className="chart-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <RevenueChart data={statements} />
              <MarginsChart data={metrics} />
              <CashFlowChart data={statements} />
              <ReturnsChart data={metrics} />
            </div>
            <BalanceSheetChart data={statements} />
            <FinancialTable
              statements={statements}
              metrics={metrics}
              currency={company?.currency || 'USD'}
            />
          </div>
        ) : null
      )}

      {/* Investment Analysis Tab */}
      {tab === 'investment' && (
        loadingInvestment ? (
          <LoadingSpinner text="투자 분석 생성 중..." />
        ) : investmentAnalysis ? (
          <InvestmentAnalysisView analysis={investmentAnalysis} />
        ) : null
      )}

      {/* DCF Tab */}
      {tab === 'dcf' && (
        <div>
          <div className="dcf-params" style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: 20, marginBottom: 20,
            display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end',
          }}>
            <InputGroup
              label="추정 기간"
              value={projYears.toString()}
              onChange={(v) => setProjYears(Math.min(10, Math.max(3, parseInt(v) || 5)))}
              suffix="년"
            />
            <InputGroup
              label="WACC (선택)"
              value={customWacc}
              onChange={setCustomWacc}
              placeholder="자동"
              suffix="%"
            />
            <InputGroup
              label="매출 성장률 (선택)"
              value={customGrowth}
              onChange={setCustomGrowth}
              placeholder="자동"
              suffix="%"
            />
            <InputGroup
              label="영구 성장률 (선택)"
              value={customTg}
              onChange={setCustomTg}
              placeholder="자동"
              suffix="%"
            />
            <button
              onClick={loadDCF}
              disabled={loadingDcf}
              style={{
                padding: '10px 24px', background: 'var(--accent-blue)',
                color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)',
                fontSize: 14, fontWeight: 600, height: 40,
                opacity: loadingDcf ? 0.6 : 1,
              }}
            >
              {loadingDcf ? '계산 중...' : dcf ? '재계산' : 'DCF 실행'}
            </button>
          </div>

          {loadingDcf ? (
            <LoadingSpinner text="DCF 밸류에이션 수행 중..." />
          ) : dcf ? (
            <DCFView dcf={dcf} />
          ) : null}
        </div>
      )}
    </div>
  );
}

function InputGroup({ label, value, onChange, placeholder, suffix }: {
  label: string; value: string; onChange: (v: string) => void;
  placeholder?: string; suffix?: string;
}) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
        {label}
      </label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            width: 80, padding: '8px 12px', background: 'var(--bg-secondary)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)', fontSize: 13, outline: 'none',
          }}
        />
        {suffix && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{suffix}</span>}
      </div>
    </div>
  );
}

function LoadingSpinner({ text }: { text: string }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: 80, color: 'var(--text-muted)',
    }}>
      <div style={{
        width: 40, height: 40, border: '3px solid var(--border)',
        borderTopColor: 'var(--accent-blue)', borderRadius: '50%',
        animation: 'spin 1s linear infinite', marginBottom: 16,
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={{ fontSize: 14 }}>{text}</div>
    </div>
  );
}
