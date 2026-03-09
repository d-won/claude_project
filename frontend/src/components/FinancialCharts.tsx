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
    Revenue: s.revenue,
    'Gross Profit': s.gross_profit,
    'Net Income': s.net_income,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>Revenue, Gross Profit & Net Income</div>
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
          <Bar dataKey="Revenue" fill="var(--accent-blue)" opacity={0.7} />
          <Bar dataKey="Gross Profit" fill="var(--accent-purple)" opacity={0.7} />
          <Line dataKey="Net Income" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 3 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MarginsChart({ data }: { data: FinancialMetrics[] }) {
  const chartData = data.map((m) => ({
    year: m.year,
    'Gross Margin': m.gross_margin ? +(m.gross_margin * 100).toFixed(1) : null,
    'Operating Margin': m.operating_margin ? +(m.operating_margin * 100).toFixed(1) : null,
    'Net Margin': m.net_margin ? +(m.net_margin * 100).toFixed(1) : null,
    'FCF Margin': m.fcf_margin ? +(m.fcf_margin * 100).toFixed(1) : null,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>Profitability Margins (%)</div>
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
          <Line dataKey="Gross Margin" stroke="var(--accent-blue)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="Operating Margin" stroke="var(--accent-purple)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="Net Margin" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 3 }} />
          <Line dataKey="FCF Margin" stroke="var(--accent-yellow)" strokeWidth={2} dot={{ r: 3 }} strokeDasharray="5 5" />
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
      <div style={titleStyle}>Return Metrics (%)</div>
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
    'Operating CF': s.operating_cash_flow,
    CAPEX: s.capital_expenditure ? Math.abs(s.capital_expenditure) : null,
    FCF: s.free_cash_flow,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>Cash Flow Analysis</div>
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
          <Area dataKey="Operating CF" fill="var(--accent-blue)" fillOpacity={0.2} stroke="var(--accent-blue)" strokeWidth={2} />
          <Bar dataKey="CAPEX" fill="var(--accent-red)" opacity={0.5} />
          <Line dataKey="FCF" stroke="var(--accent-green)" strokeWidth={2} dot={{ r: 4 }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BalanceSheetChart({ data }: { data: FinancialStatement[] }) {
  const chartData = data.map((s) => ({
    year: s.year,
    'Total Assets': s.total_assets,
    'Total Debt': s.total_debt,
    Equity: s.total_equity,
    Cash: s.cash_and_equivalents,
  }));

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>Balance Sheet Overview</div>
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
          <Bar dataKey="Total Assets" fill="var(--accent-blue)" opacity={0.6} />
          <Bar dataKey="Equity" fill="var(--accent-green)" opacity={0.6} />
          <Bar dataKey="Total Debt" fill="var(--accent-red)" opacity={0.6} />
          <Bar dataKey="Cash" fill="var(--accent-yellow)" opacity={0.6} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function FinancialTable({ statements, metrics, currency }: {
  statements: FinancialStatement[];
  metrics: FinancialMetrics[];
  currency: string;
}) {
  const rows = [
    { label: `Revenue (${currency})`, key: 'revenue', format: fmt },
    { label: `Gross Profit`, key: 'gross_profit', format: fmt },
    { label: `Operating Income`, key: 'operating_income', format: fmt },
    { label: `Net Income`, key: 'net_income', format: fmt },
    { label: `EBITDA`, key: 'ebitda', format: fmt },
    { label: `FCF`, key: 'free_cash_flow', format: fmt },
    { label: '', key: 'divider', format: () => '' },
    { label: 'Gross Margin', key: 'gross_margin', format: pct, metric: true },
    { label: 'Operating Margin', key: 'operating_margin', format: pct, metric: true },
    { label: 'Net Margin', key: 'net_margin', format: pct, metric: true },
    { label: 'ROE', key: 'roe', format: pct, metric: true },
    { label: 'D/E Ratio', key: 'debt_to_equity', format: (v: number | null) => v !== null ? `${v.toFixed(2)}x` : 'N/A', metric: true },
    { label: 'Rev Growth', key: 'revenue_growth', format: pct, metric: true },
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
      <div style={titleStyle}>Financial Data Table</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ ...thStyle, textAlign: 'left', position: 'sticky', left: 0, zIndex: 1 }}>Metric</th>
            {statements.map((s) => (
              <th key={s.year} style={thStyle}>{s.year}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            if (row.key === 'divider') {
              return (
                <tr key="divider">
                  <td colSpan={statements.length + 1} style={{ padding: 4, borderBottom: '2px solid var(--border-light)' }} />
                </tr>
              );
            }
            return (
              <tr key={row.key}>
                <td style={{
                  ...tdStyle, textAlign: 'left', fontWeight: 500, color: 'var(--text-secondary)',
                  position: 'sticky', left: 0, background: 'var(--bg-card)', zIndex: 1,
                }}>
                  {row.label}
                </td>
                {statements.map((s, i) => {
                  const source = (row as any).metric ? metrics[i] : s;
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
