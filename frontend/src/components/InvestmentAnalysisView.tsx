import type { InvestmentAnalysis } from '../types';

const cardStyle = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: 20,
  marginBottom: 16,
};

const sectionColors = {
  thesis: { bg: 'rgba(74, 158, 255, 0.08)', border: 'rgba(74, 158, 255, 0.3)', accent: 'var(--accent-blue)' },
  catalyst: { bg: 'rgba(52, 211, 153, 0.08)', border: 'rgba(52, 211, 153, 0.3)', accent: 'var(--accent-green)' },
  target: { bg: 'rgba(168, 85, 247, 0.08)', border: 'rgba(168, 85, 247, 0.3)', accent: 'var(--accent-purple)' },
  risk: { bg: 'rgba(248, 113, 113, 0.08)', border: 'rgba(248, 113, 113, 0.3)', accent: 'var(--accent-red)' },
};

function fmt(val: number): string {
  const abs = Math.abs(val);
  if (abs >= 1e12) return `${(val / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

export default function InvestmentAnalysisView({ analysis }: { analysis: InvestmentAnalysis }) {
  const recColor = analysis.recommendation === '매수' ? 'var(--accent-green)'
    : analysis.recommendation === '매도' ? 'var(--accent-red)' : 'var(--accent-yellow)';

  const tp = analysis.target_price;
  const isUpside = tp.upside_pct > 0;

  return (
    <div>
      {/* Summary & Recommendation */}
      <div style={{
        ...cardStyle,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: isUpside ? 'rgba(52, 211, 153, 0.05)' : 'rgba(248, 113, 113, 0.05)',
        borderColor: isUpside ? 'rgba(52, 211, 153, 0.3)' : 'rgba(248, 113, 113, 0.3)',
      }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {analysis.summary}
          </div>
        </div>
        <div style={{ textAlign: 'center', minWidth: 140, marginLeft: 24 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>투자의견</div>
          <div style={{
            fontSize: 28, fontWeight: 700, color: recColor,
            background: `${recColor}15`, padding: '8px 20px', borderRadius: 8,
          }}>
            {analysis.recommendation}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>
            목표가 {fmt(tp.target_price)}
          </div>
          <div style={{
            fontSize: 14, fontWeight: 600,
            color: isUpside ? 'var(--accent-green)' : 'var(--accent-red)',
          }}>
            {isUpside ? '+' : ''}{tp.upside_pct.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* 투자 논리 */}
      <SectionHeader title="투자 논리" subtitle="해당 기업에 왜 투자해야 하는가 (또는 왜 아닌가)" color={sectionColors.thesis} />
      {analysis.investment_thesis.map((item, i) => (
        <AnalysisCard key={i} item={item} color={sectionColors.thesis} />
      ))}

      {/* 핵심 트리거 */}
      <SectionHeader title="핵심 트리거" subtitle="주가 상승/하락을 견인할 구체적 이벤트" color={sectionColors.catalyst} />
      {analysis.key_catalysts.map((item, i) => (
        <AnalysisCard key={i} item={item} color={sectionColors.catalyst} />
      ))}

      {/* 목표가 산출 */}
      <SectionHeader title="목표가 산출" subtitle="객관적 근거와 투명한 가정에 기반한 목표주가" color={sectionColors.target} />
      <TargetPriceCard analysis={analysis} />

      {/* 주요 리스크 */}
      <SectionHeader title="주요 리스크" subtitle="핵심 투자 논리의 반대 시나리오" color={sectionColors.risk} />
      {analysis.key_risks.map((item, i) => (
        <AnalysisCard key={i} item={item} color={sectionColors.risk} />
      ))}
    </div>
  );
}

function SectionHeader({ title, subtitle, color }: {
  title: string; subtitle: string; color: { accent: string };
}) {
  return (
    <div style={{ marginTop: 28, marginBottom: 12 }}>
      <div style={{ fontSize: 18, fontWeight: 700, color: color.accent, marginBottom: 4 }}>
        {title}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{subtitle}</div>
    </div>
  );
}

function AnalysisCard({ item, color }: {
  item: { title: string; content: string; details: string[] };
  color: { bg: string; border: string; accent: string };
}) {
  return (
    <div style={{
      background: color.bg,
      border: `1px solid ${color.border}`,
      borderRadius: 'var(--radius)',
      padding: 20,
      marginBottom: 12,
    }}>
      <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 8, color: 'var(--text-primary)' }}>
        {item.title}
      </div>
      <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 8 }}>
        {item.content}
      </div>
      {item.details.length > 0 && (
        <div style={{
          background: 'rgba(255,255,255,0.05)', padding: '10px 14px',
          borderRadius: 6, fontSize: 12, color: 'var(--text-muted)',
        }}>
          {item.details.map((d, i) => (
            <div key={i} style={{ marginBottom: 2, fontFamily: 'monospace' }}>
              {d}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TargetPriceCard({ analysis }: { analysis: InvestmentAnalysis }) {
  const tp = analysis.target_price;
  const isUpside = tp.upside_pct > 0;

  return (
    <div>
      {/* Price comparison */}
      <div style={{
        ...cardStyle,
        display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20,
        background: sectionColors.target.bg,
        borderColor: sectionColors.target.border,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>현재가</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
            {tp.current_price.toLocaleString()}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>목표가</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-purple)' }}>
            {tp.target_price.toLocaleString()}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>괴리율</div>
          <div style={{
            fontSize: 22, fontWeight: 700,
            color: isUpside ? 'var(--accent-green)' : 'var(--accent-red)',
          }}>
            {isUpside ? '+' : ''}{tp.upside_pct.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Methodology */}
      <div style={{ ...cardStyle }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: 'var(--accent-purple)' }}>
          산출 방법론
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 16 }}>
          {tp.methodology}
        </div>

        {tp.assumptions.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>
              핵심 가정
            </div>
            {tp.assumptions.map((a, i) => (
              <div key={i} style={{
                fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4,
                paddingLeft: 12, borderLeft: '2px solid var(--accent-purple)',
              }}>
                {a}
              </div>
            ))}
          </div>
        )}

        {/* Scenarios */}
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>
          시나리오별 목표가
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {tp.scenarios.map((s, i) => {
            const scenarioColor = i === 0 ? 'var(--accent-green)' : i === 2 ? 'var(--accent-red)' : 'var(--accent-blue)';
            return (
              <div key={i} style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius-sm)', padding: 14, textAlign: 'center',
              }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: scenarioColor, marginBottom: 8 }}>
                  {s.name}
                </div>
                <div style={{ fontSize: 20, fontWeight: 700, color: scenarioColor, marginBottom: 8 }}>
                  {s.target_price.toLocaleString()}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.4 }}>
                  {s.reasoning}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
