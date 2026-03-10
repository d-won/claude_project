import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart, Area,
} from 'recharts';
import type { FinancialStatement, FinancialMetrics } from '../types';

function fmt(val: number | null): string {
  if (val === null || val === undefined) return 'N/A';
  const abs = Math.abs(val);
  if (abs >= 1e12) return `${(val / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  return val.toLocaleString();
}

function pct(val: number | null): string {
  if (val === null || val === undefined) return 'N/A';
  return `${(val * 100).toFixed(1)}%`;
}

const cardStyle = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: 24,
  marginBottom: 16,
};

const titleStyle = {
  fontSize: 16,
  fontWeight: 600 as const,
  marginBottom: 20,
  color: 'var(--text-primary)',
};

export function RevenueChart({ data }: { data: FinancialStatement[] }) {
  const chartData = data.map((s) => ({
    year: s.year,
    '매출액': s.revenue,
    '매출총이익': s.gross_profit,
    '순이익': s.net_income,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>매출액, 매출총이익 & 순이익</div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={fmt} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
            labelStyle={{ color: 'var(--text-primary)' }}
            formatter={(v: number) => fmt(v)}
          />
          <Legend />
          <Bar dataKey="매출액" fill="var(--accent-blue)" opacity={0.7} />
          <Bar dataKey="매출총이익" fill="var(--accent-purple)" opacity={0.7} />
          <Line dataKey="순이익" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 3 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MarginsChart({ data }: { data: FinancialMetrics[] }) {
  const chartData = data.map((m) => ({
    year: m.year,
    '매출총이익률': m.gross_margin ? +(m.gross_margin * 100).toFixed(1) : null,
    '영업이익률': m.operating_margin ? +(m.operating_margin * 100).toFixed(1) : null,
    '순이익률': m.net_margin ? +(m.net_margin * 100).toFixed(1) : null,
    'FCF 마진': m.fcf_margin ? +(m.fcf_margin * 100).toFixed(1) : null,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>수익성 지표 (%)</div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} unit="%" />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
            formatter={(v: number) => `${v}%`}
          />
          <Legend />
          <Line dataKey="매출총이익률" stroke="var(--accent-blue)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="영업이익률" stroke="var(--accent-purple)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="순이익률" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="FCF 마진" stroke="var(--accent-yellow)" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ReturnsChart({ data }: { data: FinancialMetrics[] }) {
  const chartData = data.map((m) => ({
    year: m.year,
    ROE: m.roe ? +(m.roe * 100).toFixed(1) : null,
    ROA: m.roa ? +(m.roa * 100).toFixed(1) : null,
    ROIC: m.roic ? +(m.roic * 100).toFixed(1) : null,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>수익률 지표 (%)</div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} unit="%" />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
            formatter={(v: number) => `${v}%`}
          />
          <Legend />
          <Line dataKey="ROE" stroke="var(--accent-blue)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="ROA" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="ROIC" stroke="var(--accent-purple)" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CashFlowChart({ data }: { data: FinancialStatement[] }) {
  const chartData = data.map((s) => ({
    year: s.year,
    '영업현금흐름': s.operating_cash_flow,
    '설비투자': s.capital_expenditure ? Math.abs(s.capital_expenditure) : null,
    '잉여현금흐름': s.free_cash_flow,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>현금흐름 분석</div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={fmt} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
            formatter={(v: number) => fmt(v)}
          />
          <Legend />
          <Area dataKey="영업현금흐름" fill="var(--accent-blue)" fillOpacity={0.2} stroke="var(--accent-blue)" strokeWidth={2} />
          <Bar dataKey="설비투자" fill="var(--accent-red)" opacity={0.5} />
          <Line dataKey="잉여현금흐름" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 4 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BalanceSheetChart({ data }: { data: FinancialStatement[] }) {
  const chartData = data.map((s) => ({
    year: s.year,
    '총자산': s.total_assets,
    '총부채': s.total_debt,
    '자본': s.total_equity,
    '현금': s.cash_and_equivalents,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>재무상태표 개요</div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
          <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={fmt} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
            formatter={(v: number) => fmt(v)}
          />
          <Legend />
          <Bar dataKey="총자산" fill="var(--accent-blue)" opacity={0.6} />
          <Bar dataKey="자본" fill="var(--accent-green)" opacity={0.6} />
          <Bar dataKey="총부채" fill="var(--accent-red)" opacity={0.6} />
          <Bar dataKey="현금" fill="var(--accent-yellow)" opacity={0.6} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function buildAllRows(currency: string) {
  return [
    // 손익계산서
    { label: '[ 손익계산서 ]', key: 'header' },
    { label: `매출액 (${currency})`, key: 'revenue', format: 'num' },
    { label: '  매출원가', key: 'cost_of_revenue', format: 'num' },
    { label: '매출총이익', key: 'gross_profit', format: 'num' },
    { label: '  판매비와관리비', key: 'selling_general_admin', format: 'num' },
    { label: '  연구개발비', key: 'research_development', format: 'num' },
    { label: '  감가상각비', key: 'depreciation', format: 'num' },
    { label: '영업이익', key: 'operating_income', format: 'num' },
    { label: '  영업외손익', key: 'other_income_expense', format: 'num' },
    { label: '  이자비용', key: 'interest_expense', format: 'num' },
    { label: '세전이익', key: 'pretax_income', format: 'num' },
    { label: '  법인세비용', key: 'tax_expense', format: 'num' },
    { label: '순이익', key: 'net_income', format: 'num' },
    { label: 'EBITDA', key: 'ebitda', format: 'num' },
    { label: 'EPS', key: 'eps', format: 'num' },
    // 재무상태표 - 자산
    { label: '[ 재무상태표 - 자산 ]', key: 'header_asset' },
    { label: '총자산', key: 'total_assets', format: 'num' },
    { label: '  유동자산', key: 'current_assets', format: 'num' },
    { label: '    현금및현금성자산', key: 'cash_and_equivalents', format: 'num' },
    { label: '    단기투자자산', key: 'short_term_investments', format: 'num' },
    { label: '    매출채권', key: 'accounts_receivable', format: 'num' },
    { label: '    재고자산', key: 'inventory', format: 'num' },
    { label: '  비유동자산', key: 'non_current_assets', format: 'num' },
    { label: '    유형자산(순액)', key: 'ppe_net', format: 'num' },
    { label: '    영업권/무형자산', key: 'goodwill_intangibles', format: 'num' },
    { label: '    장기투자자산', key: 'long_term_investments', format: 'num' },
    // 재무상태표 - 부채
    { label: '[ 재무상태표 - 부채 ]', key: 'header_liab' },
    { label: '총부채', key: 'total_liabilities', format: 'num' },
    { label: '  유동부채', key: 'current_liabilities', format: 'num' },
    { label: '    매입채무', key: 'accounts_payable', format: 'num' },
    { label: '    단기차입금', key: 'short_term_debt', format: 'num' },
    { label: '  비유동부채', key: 'non_current_liabilities', format: 'num' },
    { label: '    장기차입금', key: 'long_term_debt', format: 'num' },
    { label: '총차입금', key: 'total_debt', format: 'num' },
    // 재무상태표 - 자본
    { label: '[ 재무상태표 - 자본 ]', key: 'header_equity' },
    { label: '자본총계', key: 'total_equity', format: 'num' },
    { label: '  이익잉여금', key: 'retained_earnings', format: 'num' },
    { label: '발행주식수', key: 'shares_outstanding', format: 'num' },
    // 현금흐름표
    { label: '[ 현금흐름표 - 영업활동 ]', key: 'header_opcf' },
    { label: '영업현금흐름', key: 'operating_cash_flow', format: 'num' },
    { label: '  감가상각비(CF)', key: 'depreciation_cf', format: 'num' },
    { label: '  운전자본변동', key: 'change_in_working_capital', format: 'num' },
    { label: '[ 현금흐름표 - 투자활동 ]', key: 'header_invcf' },
    { label: '투자현금흐름', key: 'investing_cash_flow', format: 'num' },
    { label: '  설비투자(CAPEX)', key: 'capital_expenditure', format: 'num' },
    { label: '  투자자산매입', key: 'purchase_of_investments', format: 'num' },
    { label: '  투자자산매각', key: 'sale_of_investments', format: 'num' },
    { label: '[ 현금흐름표 - 재무활동 ]', key: 'header_fincf' },
    { label: '재무현금흐름', key: 'financing_cash_flow', format: 'num' },
    { label: '  차입금조달', key: 'debt_issuance', format: 'num' },
    { label: '  차입금상환', key: 'debt_repayment', format: 'num' },
    { label: '  자사주매입/발행', key: 'share_buyback_issuance', format: 'num' },
    { label: '  배당금지급', key: 'dividends_paid', format: 'num' },
    { label: '잉여현금흐름(FCF)', key: 'free_cash_flow', format: 'num' },
    // 주요 지표
    { label: '[ 주요 재무지표 ]', key: 'header_metrics' },
    { label: '매출총이익률', key: 'gross_margin', format: 'pct', metric: true },
    { label: '영업이익률', key: 'operating_margin', format: 'pct', metric: true },
    { label: '순이익률', key: 'net_margin', format: 'pct', metric: true },
    { label: 'ROE', key: 'roe', format: 'pct', metric: true },
    { label: 'ROA', key: 'roa', format: 'pct', metric: true },
    { label: 'ROIC', key: 'roic', format: 'pct', metric: true },
    { label: 'D/E 비율', key: 'debt_to_equity', format: 'ratio', metric: true },
    { label: '유동비율', key: 'current_ratio', format: 'ratio', metric: true },
    { label: '이자보상배율', key: 'interest_coverage', format: 'ratio', metric: true },
    { label: '총자산회전율', key: 'asset_turnover', format: 'ratio', metric: true },
    { label: '매출 성장률', key: 'revenue_growth', format: 'pct', metric: true },
    { label: '순이익 성장률', key: 'earnings_growth', format: 'pct', metric: true },
    { label: 'FCF 마진', key: 'fcf_margin', format: 'pct', metric: true },
  ];
}

function downloadCSV(statements: FinancialStatement[], metrics: FinancialMetrics[], currency: string) {
  const allRows = buildAllRows(currency);

  const header = ['항목', ...statements.map(s => s.year.toString())].join(',');
  const rows = allRows.map(row => {
    if (row.key.startsWith('header')) {
      return row.label;
    }
    const values = statements.map((s, i) => {
      const source = (row as any).metric ? metrics[i] : s;
      const val = source ? (source as any)[row.key] : null;
      if (val === null || val === undefined) return '';
      if (row.format === 'pct') return (val * 100).toFixed(1) + '%';
      if (row.format === 'ratio') return val.toFixed(2);
      return val.toString();
    });
    return [row.label, ...values].join(',');
  });

  const csv = '\uFEFF' + [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `financial_data_${statements[0]?.year || ''}_${statements[statements.length-1]?.year || ''}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export function FinancialTable({ statements, metrics, currency }: {
  statements: FinancialStatement[];
  metrics: FinancialMetrics[];
  currency: string;
}) {
  type RowDef = { label: string; key: string; format: (v: any) => string; metric?: boolean; section?: boolean; indent?: number };

  const sectionHeader = (label: string): RowDef => ({
    label, key: `section_${label}`, format: () => '', section: true,
  });

  const fmtEps = (v: number | null) => v !== null ? v.toLocaleString(undefined, { maximumFractionDigits: 0 }) : 'N/A';
  const fmtRatio = (v: number | null) => v !== null ? `${v.toFixed(2)}x` : 'N/A';
  const fmtRatio1 = (v: number | null) => v !== null ? `${v.toFixed(1)}x` : 'N/A';

  const rows: RowDef[] = [
    // 손익계산서
    sectionHeader('손익계산서'),
    { label: `매출액 (${currency})`, key: 'revenue', format: fmt },
    { label: '매출원가', key: 'cost_of_revenue', format: fmt, indent: 1 },
    { label: '매출총이익', key: 'gross_profit', format: fmt },
    { label: '판매비와관리비', key: 'selling_general_admin', format: fmt, indent: 1 },
    { label: '연구개발비', key: 'research_development', format: fmt, indent: 1 },
    { label: '감가상각비', key: 'depreciation', format: fmt, indent: 1 },
    { label: '영업이익', key: 'operating_income', format: fmt },
    { label: '영업외손익', key: 'other_income_expense', format: fmt, indent: 1 },
    { label: '이자비용', key: 'interest_expense', format: fmt, indent: 1 },
    { label: '세전이익', key: 'pretax_income', format: fmt },
    { label: '법인세비용', key: 'tax_expense', format: fmt, indent: 1 },
    { label: '순이익', key: 'net_income', format: fmt },
    { label: 'EBITDA', key: 'ebitda', format: fmt },
    { label: 'EPS', key: 'eps', format: fmtEps },

    // 재무상태표 - 자산
    sectionHeader('재무상태표 - 자산'),
    { label: '총자산', key: 'total_assets', format: fmt },
    { label: '유동자산', key: 'current_assets', format: fmt, indent: 1 },
    { label: '현금및현금성자산', key: 'cash_and_equivalents', format: fmt, indent: 2 },
    { label: '단기투자자산', key: 'short_term_investments', format: fmt, indent: 2 },
    { label: '매출채권', key: 'accounts_receivable', format: fmt, indent: 2 },
    { label: '재고자산', key: 'inventory', format: fmt, indent: 2 },
    { label: '비유동자산', key: 'non_current_assets', format: fmt, indent: 1 },
    { label: '유형자산(순액)', key: 'ppe_net', format: fmt, indent: 2 },
    { label: '영업권/무형자산', key: 'goodwill_intangibles', format: fmt, indent: 2 },
    { label: '장기투자자산', key: 'long_term_investments', format: fmt, indent: 2 },

    // 재무상태표 - 부채
    sectionHeader('재무상태표 - 부채'),
    { label: '총부채', key: 'total_liabilities', format: fmt },
    { label: '유동부채', key: 'current_liabilities', format: fmt, indent: 1 },
    { label: '매입채무', key: 'accounts_payable', format: fmt, indent: 2 },
    { label: '단기차입금', key: 'short_term_debt', format: fmt, indent: 2 },
    { label: '비유동부채', key: 'non_current_liabilities', format: fmt, indent: 1 },
    { label: '장기차입금', key: 'long_term_debt', format: fmt, indent: 2 },
    { label: '총차입금', key: 'total_debt', format: fmt },

    // 재무상태표 - 자본
    sectionHeader('재무상태표 - 자본'),
    { label: '자본총계', key: 'total_equity', format: fmt },
    { label: '이익잉여금', key: 'retained_earnings', format: fmt, indent: 1 },
    { label: '발행주식수', key: 'shares_outstanding', format: fmt },

    // 현금흐름표 - 영업활동
    sectionHeader('현금흐름표 - 영업활동'),
    { label: '영업현금흐름', key: 'operating_cash_flow', format: fmt },
    { label: '감가상각비(CF)', key: 'depreciation_cf', format: fmt, indent: 1 },
    { label: '운전자본변동', key: 'change_in_working_capital', format: fmt, indent: 1 },

    // 현금흐름표 - 투자활동
    sectionHeader('현금흐름표 - 투자활동'),
    { label: '투자현금흐름', key: 'investing_cash_flow', format: fmt },
    { label: '설비투자(CAPEX)', key: 'capital_expenditure', format: fmt, indent: 1 },
    { label: '투자자산매입', key: 'purchase_of_investments', format: fmt, indent: 1 },
    { label: '투자자산매각', key: 'sale_of_investments', format: fmt, indent: 1 },

    // 현금흐름표 - 재무활동
    sectionHeader('현금흐름표 - 재무활동'),
    { label: '재무현금흐름', key: 'financing_cash_flow', format: fmt },
    { label: '차입금조달', key: 'debt_issuance', format: fmt, indent: 1 },
    { label: '차입금상환', key: 'debt_repayment', format: fmt, indent: 1 },
    { label: '자사주매입/발행', key: 'share_buyback_issuance', format: fmt, indent: 1 },
    { label: '배당금지급', key: 'dividends_paid', format: fmt, indent: 1 },
    { label: '잉여현금흐름(FCF)', key: 'free_cash_flow', format: fmt },

    // 주요 지표
    sectionHeader('주요 재무지표'),
    { label: '매출총이익률', key: 'gross_margin', format: pct, metric: true },
    { label: '영업이익률', key: 'operating_margin', format: pct, metric: true },
    { label: '순이익률', key: 'net_margin', format: pct, metric: true },
    { label: 'ROE', key: 'roe', format: pct, metric: true },
    { label: 'ROA', key: 'roa', format: pct, metric: true },
    { label: 'ROIC', key: 'roic', format: pct, metric: true },
    { label: 'D/E 비율', key: 'debt_to_equity', format: fmtRatio, metric: true },
    { label: '유동비율', key: 'current_ratio', format: fmtRatio, metric: true },
    { label: '이자보상배율', key: 'interest_coverage', format: fmtRatio1, metric: true },
    { label: '총자산회전율', key: 'asset_turnover', format: fmtRatio, metric: true },
    { label: '매출 성장률', key: 'revenue_growth', format: pct, metric: true },
    { label: '순이익 성장률', key: 'earnings_growth', format: pct, metric: true },
    { label: 'FCF 마진', key: 'fcf_margin', format: pct, metric: true },
  ];

  const thStyle = {
    padding: '10px 12px',
    textAlign: 'right' as const,
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border)',
    position: 'sticky' as const,
    top: 0,
    background: 'var(--bg-card)',
  };

  const tdStyle = {
    padding: '8px 12px',
    textAlign: 'right' as const,
    fontSize: 13,
    borderBottom: '1px solid var(--border)',
    whiteSpace: 'nowrap' as const,
  };

  return (
    <div style={{ ...cardStyle, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div style={titleStyle as any}>재무 데이터 테이블</div>
        <button
          onClick={() => downloadCSV(statements, metrics, currency)}
          style={{
            padding: '8px 16px', background: 'var(--accent-green)',
            color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}
        >
          엑셀 다운로드
        </button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ ...thStyle, textAlign: 'left', position: 'sticky', left: 0, zIndex: 1 }}>항목</th>
            {statements.map((s) => (
              <th key={s.year} style={thStyle}>{s.year}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            if (row.section) {
              return (
                <tr key={row.key}>
                  <td
                    colSpan={statements.length + 1}
                    style={{
                      padding: '12px 12px 6px', fontWeight: 700, fontSize: 13,
                      color: 'var(--accent-blue)', borderBottom: '2px solid var(--border)',
                      background: 'var(--bg-card)', position: 'sticky' as const, left: 0,
                    }}
                  >
                    {row.label}
                  </td>
                </tr>
              );
            }
            return (
              <tr key={row.key}>
                <td style={{
                  ...tdStyle, textAlign: 'left',
                  fontWeight: row.indent ? 400 : 500,
                  color: row.indent ? 'var(--text-muted)' : 'var(--text-secondary)',
                  paddingLeft: 12 + (row.indent || 0) * 16,
                  fontSize: row.indent && row.indent >= 2 ? 12 : 13,
                  position: 'sticky', left: 0, background: 'var(--bg-card)', zIndex: 1,
                }}>
                  {row.label}
                </td>
                {statements.map((s, i) => {
                  const source = row.metric ? metrics[i] : s;
                  const val = source ? (source as any)[row.key] : null;
                  const formatted = row.format(val);
                  const isNeg = val !== null && val < 0;
                  return (
                    <td key={s.year} style={{ ...tdStyle, color: isNeg ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                      {formatted}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
