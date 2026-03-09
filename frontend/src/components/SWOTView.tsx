import type { SWOTAnalysis, SWOTItem } from '../types';

const cardColors = {
  strengths: { bg: 'rgba(52, 211, 153, 0.08)', border: 'rgba(52, 211, 153, 0.3)', icon: 'var(--accent-green)', label: 'STRENGTHS' },
  weaknesses: { bg: 'rgba(248, 113, 113, 0.08)', border: 'rgba(248, 113, 113, 0.3)', icon: 'var(--accent-red)', label: 'WEAKNESSES' },
  opportunities: { bg: 'rgba(74, 158, 255, 0.08)', border: 'rgba(74, 158, 255, 0.3)', icon: 'var(--accent-blue)', label: 'OPPORTUNITIES' },
  threats: { bg: 'rgba(251, 191, 36, 0.08)', border: 'rgba(251, 191, 36, 0.3)', icon: 'var(--accent-yellow)', label: 'THREATS' },
};

function SWOTCard({ type, items }: { type: keyof typeof cardColors; items: SWOTItem[] }) {
  const color = cardColors[type];
  return (
    <div style={{
      background: color.bg,
      border: `1px solid ${color.border}`,
      borderRadius: 'var(--radius)',
      padding: 20,
      minHeight: 200,
    }}>
      <div style={{
        fontSize: 12, fontWeight: 700, letterSpacing: 1.5,
        color: color.icon, marginBottom: 16,
      }}>
        {color.label}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {items.map((item, i) => (
          <div key={i}>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6, color: 'var(--text-primary)' }}>
              {item.point}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 4 }}>
              {item.evidence}
            </div>
            {item.data_reference && (
              <div style={{
                fontSize: 11, color: 'var(--text-muted)',
                background: 'rgba(255,255,255,0.05)', padding: '4px 8px',
                borderRadius: 4, display: 'inline-block', marginTop: 4,
                fontFamily: 'monospace',
              }}>
                {item.data_reference}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SWOTView({ swot }: { swot: SWOTAnalysis }) {
  return (
    <div>
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius)', padding: 20, marginBottom: 20,
      }}>
        <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--accent-blue)' }}>
          Summary
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          {swot.summary}
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 16,
      }}>
        <SWOTCard type="strengths" items={swot.strengths} />
        <SWOTCard type="weaknesses" items={swot.weaknesses} />
        <SWOTCard type="opportunities" items={swot.opportunities} />
        <SWOTCard type="threats" items={swot.threats} />
      </div>
    </div>
  );
}
