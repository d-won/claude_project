import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchCompanies } from '../services/api';
import type { CompanyInfo } from '../types';

const MARKETS = [
  { value: '', label: '전체 시장' },
  { value: 'US', label: '미국' },
  { value: 'KR', label: '한국' },
  { value: 'JP', label: '일본' },
  { value: 'EU', label: '유럽' },
];

const EXAMPLES = [
  { ticker: 'AAPL', name: 'Apple Inc.', market: 'US' },
  { ticker: '005930.KS', name: 'Samsung Electronics', market: 'KR' },
  { ticker: '7203.T', name: 'Toyota Motor', market: 'JP' },
  { ticker: 'SAP.DE', name: 'SAP SE', market: 'EU' },
  { ticker: 'MSFT', name: 'Microsoft', market: 'US' },
  { ticker: '000660.KS', name: 'SK Hynix', market: 'KR' },
];

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [market, setMarket] = useState('');
  const [results, setResults] = useState<CompanyInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await searchCompanies(query.trim(), market || undefined);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const goToAnalysis = (ticker: string) => {
    navigate(`/analysis/${encodeURIComponent(ticker)}`);
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', padding: '60px 0 40px' }}>
        <h1 style={{ fontSize: 36, fontWeight: 700, marginBottom: 12 }}>
          글로벌 재무분석
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 16, maxWidth: 600, margin: '0 auto' }}>
          한국, 일본, 유럽, 미국 상장 기업을 분석하세요.
          7~15년 재무 데이터, 투자 분석, DCF 밸류에이션을 제공합니다.
        </p>
      </div>

      <form onSubmit={handleSearch} style={{
        display: 'flex', gap: 12, marginBottom: 32,
        background: 'var(--bg-card)', padding: 16, borderRadius: 'var(--radius)',
        border: '1px solid var(--border)',
      }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="티커 또는 기업명 입력 (예: AAPL, 005930.KS, 7203.T)"
          style={{
            flex: 1, padding: '12px 16px', background: 'var(--bg-secondary)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)', fontSize: 15, outline: 'none',
          }}
        />
        <select
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          style={{
            padding: '12px 16px', background: 'var(--bg-secondary)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)', fontSize: 14, minWidth: 120,
          }}
        >
          {MARKETS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 32px', background: 'var(--accent-blue)',
            color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)',
            fontSize: 15, fontWeight: 600, opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? '검색 중...' : '검색'}
        </button>
      </form>

      {!searched && (
        <div>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 16, textTransform: 'uppercase', letterSpacing: 1 }}>
            빠른 접근
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 12 }}>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.ticker}
                onClick={() => goToAnalysis(ex.ticker)}
                style={{
                  padding: '16px 20px', background: 'var(--bg-card)',
                  border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)', textAlign: 'left',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-blue)';
                  e.currentTarget.style.background = 'var(--bg-hover)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.background = 'var(--bg-card)';
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{ex.ticker}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{ex.name}</div>
                <div style={{
                  fontSize: 11, color: 'var(--accent-blue)', marginTop: 4,
                  background: 'rgba(74, 158, 255, 0.1)', display: 'inline-block',
                  padding: '2px 8px', borderRadius: 4,
                }}>{ex.market}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {searched && results.length > 0 && (
        <div>
          <h3 style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 16 }}>
            {results.length}건의 검색 결과
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {results.map((r) => (
              <button
                key={r.ticker}
                onClick={() => goToAnalysis(r.ticker)}
                style={{
                  padding: '16px 20px', background: 'var(--bg-card)',
                  border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)', textAlign: 'left',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-blue)';
                  e.currentTarget.style.background = 'var(--bg-hover)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)';
                  e.currentTarget.style.background = 'var(--bg-card)';
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, marginRight: 12 }}>{r.ticker}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{r.name}</span>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                    {r.sector} / {r.industry} | {r.exchange}
                  </div>
                </div>
                <div style={{
                  fontSize: 11, color: 'var(--accent-blue)',
                  background: 'rgba(74, 158, 255, 0.1)',
                  padding: '4px 12px', borderRadius: 4, fontWeight: 500,
                }}>{r.market}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {searched && !loading && results.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
          검색 결과가 없습니다. 다른 티커 또는 기업명을 입력해보세요.
        </div>
      )}
    </div>
  );
}
