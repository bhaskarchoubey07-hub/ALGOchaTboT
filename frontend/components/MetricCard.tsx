interface MetricCardProps {
  label: string;
  value: string;
  tone?: "positive" | "negative";
  footnote?: string;
}

export function MetricCard({ label, value, tone, footnote }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${tone || ""}`}>{value}</div>
      {footnote ? <div className="metric-footnote">{footnote}</div> : null}
    </div>
  );
}
