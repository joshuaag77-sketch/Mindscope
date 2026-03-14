function buildPath(values: number[], width: number, height: number): string {
  if (values.length === 0) {
    return "";
  }
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 100);
  const range = Math.max(max - min, 1);
  return values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

export function TrendPlaceholder({
  values,
  labels,
}: {
  values: number[];
  labels: string[];
}) {
  const width = 820;
  const height = 220;
  const path = buildPath(values, width, height);
  const thresholdLines = [
    { value: 75, label: "Sustained" },
    { value: 60, label: "High" },
    { value: 40, label: "Elevated" },
  ];
  return (
    <div>
      <h2 className="panel-title">Recent trend</h2>
      <p className="muted">
        Live overload-risk trajectory from ActivityWatch-derived 10-minute
        windows.
      </p>
      <div className="trend-chart-wrap" aria-label="Overload score trend">
        <svg viewBox={`0 0 ${width} ${height}`} className="trend-chart">
          {thresholdLines.map((line) => {
            const y = height - (line.value / 100) * height;
            return (
              <g key={line.value}>
                <line x1={0} y1={y} x2={width} y2={y} className="trend-threshold" />
                <text x={6} y={Math.max(y - 4, 12)} className="trend-threshold-label">
                  {line.label}
                </text>
              </g>
            );
          })}
          <path d={path} className="trend-line" />
          {values.map((value, index) => {
            const x = (index / Math.max(values.length - 1, 1)) * width;
            const y = height - (value / 100) * height;
            return <circle key={`${value}-${index}`} cx={x} cy={y} r={3.5} className="trend-point" />;
          })}
        </svg>
        <div className="trend-labels">
          {labels.slice(-8).map((label, index) => (
            <span key={`${label}-${index}`}>{label}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
