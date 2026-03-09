import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getFinancials, getSWOT, getDCF } from '../services/api';
import type {
  CompanyInfo, FinancialStatement, FinancialMetrics,
  SWOTAnalysis, DCFResult,
} from '../types';
import {
  RevenueChart, MarginsChart, ReturnsChart,
  CashFlowChart, BalanceSheetChart, FinancialTable,
} from '../components/FinancialCharts';
import SWOTView from '../components/SWOTView';
import DCFView from '../components/DCFView';

type Tab = 'financials' | 'swot' | 'dcf';

export default function AnalysisPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const [tab, setTab] = useState<Tab>('financials');
  const [years, setYears] = useState(10);

  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [statements, setStatements] = useState<FinancialStatement[]>([]);
  const [metrics, setMetrics] = useState<FinancialMetrics[]>([]);
  const [swot, setSWOT] = useState<SWOTAnalysis | null>(null);
  const [dcf, setDCF] = useState<DCFResult | null>(null);

  const [loadingFin, setLoadingFin] = useState(false);
  const [loadingSwot, setLoadingSwot] = useState(false);
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
      setError(e?.response?.data?.detail || 'Failed to load financial data');
    } finally {
      setLoadingFin(false);
    }
  };

  const loadSWOT = async () => {
    if (!ticker) return;
    setLoadingSwot(true);
    try {
      const data = await getSWOT(ticker, years);
      setSWOT(data.swot);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to generate SWOT analysis');
    } finally {
      setLoadingSwot(false);
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
      setError(e?.response?.data?.detail || 'Failed to perform DCF valuation');
    } finally {
      setLoadingDcf(false);
    }
  };

  const handleTabChange = (newTab: Tab) => {
    setTab(newTab);
    if (newTab === 'swot' && !swot && !loadingSwot) loadSWOT();
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
          &larr; Back to Search
        </Link>
      </div>

      {company && (
        <div style={{
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
            <label style={{ fontSize: 13, color: 'var(--text-muted)' }}>Data years:</label>
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
                <option key={y} value={y}>{y} years</option>
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
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <button style={tabStyle('financials')} onClick={() => handleTabChange('financials')}>
          Financial Statements
        </button>
        <button style={tabStyle('swot')} onClick={() => handleTabChange('swot')}>
          SWOT Analysis
        </button>
        <button style={tabStyle('dcf')} onClick={() => handleTabChange('dcf')}>
          DCF Valuation
        </button>
      </div>

      {/* Financials Tab */}
      {tab === 'financials' && (
        loadingFin ? (
          <LoadingSpinner text="Loading financial data..." />
        ) : statements.length > 0 ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
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

      {/* SWOT Tab */}
      {tab === 'swot' && (
        loadingSwot ? (
          <LoadingSpinner text="Generating SWOT analysis..." />
        ) : swot ? (
          <SWOTView swot={swot} />
        ) : null
      )}

      {/* DCF Tab */}
      {tab === 'dcf' && (
        <div>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: 20, marginBottom: 20,
            display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-end',
          }}>
            <InputGroup
              label="Projection Years"
              value={projYears.toString()}
              onChange={(v) => setProjYears(Math.min(10, Math.max(3, parseInt(v) || 5)))}
              suffix="yrs"
            />
            <InputGroup
              label="Custom WACC (optional)"
              value={customWacc}
              onChange={setCustomWacc}
              placeholder="Auto"
              suffix="%"
            />
            <InputGroup
              label="Revenue Growth (optional)"
              value={customGrowth}
              onChange={setCustomGrowth}
              placeholder="Auto"
              suffix="%"
            />
            <InputGroup
              label="Terminal Growth (optional)"
              value={customTg}
              onChange={setCustomTg}
              placeholder="Auto"
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
              {loadingDcf ? 'Calculating...' : dcf ? 'Recalculate' : 'Run DCF'}
            </button>
          </div>

          {loadingDcf ? (
            <LoadingSpinner text="Performing DCF valuation..." />
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
