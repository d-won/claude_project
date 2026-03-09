import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';
import type { DCFResult } from '../types';

function fmt(val: number | null): string {
  if (val === null || val === undefined) return 'N/A';
  const abs = Math.abs(val);
  if (abs >= 1e12) return `${(val / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

const cardStyle = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: 20,
  marginBottom: 16,
};

export default function DCFView({ dcf }: { dcf: DCFResult }) {
  const upside = dcf.upside_downside_pct;
  const isUndervalued = upside > 0;

  return (
    <div>
      {/* Valuation Summary */}
      <div style={{
        ...cardStyle,
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20,
        background: isUndervalued
          ? 'rgba(52, 211, 153, 0.05)'
          : 'rgba(248, 113, 113, 0.05)',
        borderColor: isUndervalued
          ? 'rgba(52, 211, 153, 0.3)'
          : 'rgba(248, 113, 113, 0.3)',
      }}>
        <ValueBox
          label="내재가치"
          value={`${dcf.currency} ${dcf.intrinsic_value_per_share.toFixed(2)}`}
          color="var(--accent-blue)"
        />
        <ValueBox
          label="현재 주가"
          value={`${dcf.currency} ${dcf.current_price.toFixed(2)}`}
          color="var(--text-primary)"
        />
        <ValueBox
          label="괴리율"
          value={`${upside > 0 ? '+' : ''}${upside.toFixed(1)}%`}
          color={isUndervalued ? 'var(--accent-green)' : 'var(--accent-red)'}
        />
        <ValueBox
          label="기업가치"
          value={`${dcf.currency} ${fmt(dcf.enterprise_value)}`}
          color="var(--accent-purple)"
        />
      </div>

      {/* FCF Projections Chart */}
      <div style={cardStyle}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          잉여현금흐름(FCF) 추정
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={dcf.projections}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
            <YAxis stroke="var(--text-muted)" fontSize={12} tickFormatter={fmt} />
            <Tooltip
              contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8 }}
              formatter={(v: number, name: string) => [fmt(v), name]}
            />
            <Legend />
            <Bar dataKey="revenue" name="매출액" fill="var(--accent-blue)" opacity={0.4} />
            <Bar dataKey="free_cash_flow" name="FCF" fill="var(--accent-green)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Assumptions with Reasoning */}
      <div style={cardStyle}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          핵심 가정 및 근거
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {dcf.assumptions.map((a, i) => (
            <div key={i} style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-sm)',
              padding: 16,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{a.parameter}</span>
                <span style={{
                  fontWeight: 700, fontSize: 16, color: 'var(--accent-blue)',
                  background: 'rgba(74, 158, 255, 0.1)', padding: '2px 12px', borderRadius: 4,
                }}>
                  {a.value.toFixed(a.unit === 'x' ? 2 : 1)}{a.unit}
                </span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 8 }}>
                {a.reasoning}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                <strong>근거:</strong>
                <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
                  {a.evidence.map((e, j) => (
                    <li key={j} style={{ marginBottom: 2 }}>{e}</li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Projection Table */}
      <div style={{ ...cardStyle, overflow: 'auto' }}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          추정 상세 ({dcf.currency})
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['연도', '매출액', 'EBITDA', 'FCF', '할인계수', '현재가치'].map((h) => (
                <th key={h} style={{
                  padding: '10px 12px', textAlign: 'right', fontSize: 12,
                  fontWeight: 600, color: 'var(--text-secondary)',
                  borderBottom: '2px solid var(--border)',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dcf.projections.map((p) => (
              <tr key={p.year}>
                <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600, borderBottom: '1px solid var(--border)' }}>{p.year}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', borderBottom: '1px solid var(--border)' }}>{fmt(p.revenue)}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', borderBottom: '1px solid var(--border)' }}>{fmt(p.ebitda)}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', borderBottom: '1px solid var(--border)', color: 'var(--accent-green)' }}>{fmt(p.free_cash_flow)}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', borderBottom: '1px solid var(--border)' }}>{p.discount_factor.toFixed(4)}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right', borderBottom: '1px solid var(--border)', fontWeight: 600 }}>{fmt(p.present_value)}</td>
              </tr>
            ))}
            <tr style={{ background: 'rgba(74, 158, 255, 0.05)' }}>
              <td colSpan={4} style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 600 }}>영구가치 (현재가치)</td>
              <td></td>
              <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: 'var(--accent-blue)' }}>
                {fmt(dcf.terminal_value_pv)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Sensitivity Matrix */}
      <div style={{ ...cardStyle, overflow: 'auto' }}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
          민감도 분석 (주당 내재가치)
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
          WACC (행) vs 영구 성장률 (열)
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ padding: 8, fontSize: 12, color: 'var(--text-muted)', borderBottom: '2px solid var(--border)' }}>
                WACC \ 영구성장률
              </th>
              {dcf.sensitivity_matrix.terminal_growth_values.map((tg) => (
                <th key={tg} style={{ padding: 8, fontSize: 12, textAlign: 'center', color: 'var(--text-secondary)', borderBottom: '2px solid var(--border)' }}>
                  {tg}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dcf.sensitivity_matrix.wacc_values.map((wacc) => (
              <tr key={wacc}>
                <td style={{ padding: 8, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)' }}>
                  {wacc}
                </td>
                {dcf.sensitivity_matrix.terminal_growth_values.map((tg) => {
                  const val = dcf.sensitivity_matrix.intrinsic_values[wacc]?.[tg];
                  const isBase = wacc === dcf.sensitivity_matrix.wacc_values[2] && tg === dcf.sensitivity_matrix.terminal_growth_values[2];
                  return (
                    <td key={tg} style={{
                      padding: 8, fontSize: 13, textAlign: 'center',
                      borderBottom: '1px solid var(--border)',
                      fontWeight: isBase ? 700 : 400,
                      background: isBase ? 'rgba(74, 158, 255, 0.1)' : undefined,
                      color: val !== null && val !== undefined
                        ? (val > dcf.current_price ? 'var(--accent-green)' : 'var(--accent-red)')
                        : 'var(--text-muted)',
                    }}>
                      {val !== null && val !== undefined ? val.toFixed(2) : '-'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Methodology */}
      <div style={cardStyle}>
        <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
          방법론 참고사항
        </div>
        <ul style={{ margin: 0, padding: '0 0 0 20px' }}>
          {dcf.methodology_notes.map((note, i) => (
            <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, lineHeight: 1.5 }}>
              {note}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function ValueBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}
