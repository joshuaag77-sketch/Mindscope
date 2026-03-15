"use client";

import { useEffect, useState } from "react";

type MetricSummary = {
  key: string;
  label: string;
  unit: string;
  overload_direction: "high" | "low";
  description: string;
  mean: number;
  std: number;
};

type HourlyEntry = {
  hour: number;
  [key: string]: number;
};

type BaselineSummary = {
  row_count: number;
  metrics: MetricSummary[];
  hourly: HourlyEntry[];
};

const METRIC_COLORS: Record<string, string> = {
  app_switch_count: "#c75a2d",
  distinct_app_count: "#b34236",
  focus_streak_minutes: "#2f7a52",
  afk_count: "#8f6a38",
  afk_minutes: "#c8891a",
  work_context_entropy: "#6b4c9a",
  work_reentry_count: "#3a7bb0",
};

function MetricBar({
  metric,
  maxMean,
}: {
  metric: MetricSummary;
  maxMean: number;
}) {
  const fillPct = Math.min((metric.mean / Math.max(maxMean, 0.01)) * 100, 100);
  const stdPct = Math.min(((metric.mean + metric.std) / Math.max(maxMean, 0.01)) * 100, 100);
  const color = METRIC_COLORS[metric.key] ?? "#c75a2d";
  const isBad = metric.overload_direction === "high";

  return (
    <div className="baseline-metric-card">
      <div className="baseline-metric-header">
        <div>
          <span className="baseline-metric-label">{metric.label}</span>
          <span className="baseline-metric-unit">{metric.unit}</span>
        </div>
        <div className="baseline-metric-value" style={{ color }}>
          {metric.mean.toFixed(1)}
          <span className="baseline-metric-std"> ±{metric.std.toFixed(1)}</span>
        </div>
      </div>
      <div className="baseline-bar-track">
        {/* std range */}
        <div
          className="baseline-bar-std"
          style={{ width: `${stdPct}%`, background: `${color}22` }}
        />
        {/* mean fill */}
        <div
          className="baseline-bar-fill"
          style={{ width: `${fillPct}%`, background: color }}
        />
      </div>
      <p className="baseline-metric-desc">{metric.description}</p>
      <span
        className={`baseline-direction-badge ${isBad ? "baseline-badge-high" : "baseline-badge-low"}`}
      >
        {isBad ? "↑ High = overload risk" : "↓ Low = overload risk"}
      </span>
    </div>
  );
}

function HourlySparkline({
  metric,
  hourly,
}: {
  metric: MetricSummary;
  hourly: HourlyEntry[];
}) {
  if (hourly.length === 0) return null;
  const vals = hourly.map((h) => h[metric.key] ?? 0);
  const max = Math.max(...vals, 0.01);
  const color = METRIC_COLORS[metric.key] ?? "#c75a2d";
  const w = 320;
  const h = 60;
  const path = vals
    .map((v, i) => {
      const x = (i / Math.max(vals.length - 1, 1)) * w;
      const y = h - (v / max) * h;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <div className="hourly-spark-wrap">
      <span className="hourly-spark-label">{metric.label}</span>
      <svg viewBox={`0 0 ${w} ${h}`} className="hourly-spark-svg">
        <path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        {vals.map((v, i) => (
          <circle
            key={i}
            cx={(i / Math.max(vals.length - 1, 1)) * w}
            cy={h - (v / max) * h}
            r="3"
            fill={color}
          />
        ))}
      </svg>
      <div className="hourly-spark-axis">
        {hourly.filter((_, i) => i % 2 === 0).map((h) => (
          <span key={h.hour}>{h.hour}:00</span>
        ))}
      </div>
    </div>
  );
}

export function BaselineProfile() {
  const [data, setData] = useState<BaselineSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/baseline")
      .then((r) => r.json())
      .then((d: BaselineSummary) => setData(d))
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="panel" style={{ color: "var(--risk)" }}>
        Could not load baseline data — ensure the backend is running. ({error})
      </div>
    );
  }

  if (!data) {
    return <div className="panel muted">Loading baseline profile…</div>;
  }

  const maxMean = Math.max(...data.metrics.map((m) => m.mean), 1);

  return (
    <div>
      {/* Hero */}
      <section className="baseline-hero panel" style={{ marginBottom: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 10 }}>Ingested baseline</div>
        <h1 className="hero-title" style={{ fontFamily: "var(--font-heading)", fontSize: "clamp(2rem,4vw,3.2rem)" }}>
          Your personal activity baseline
        </h1>
        <p className="hero-body" style={{ marginTop: 12 }}>
          MindScope ingested <strong>{data.row_count} baseline windows</strong> from your
          historical ActivityWatch data. These values define your normal working rhythm — any
          live window that deviates significantly will raise your overload score.
        </p>
        <div className="kpi-strip" style={{ marginTop: 18 }}>
          <div className="kpi-item">
            <strong>Baseline windows</strong>
            <p className="muted">{data.row_count}</p>
          </div>
          <div className="kpi-item">
            <strong>Metrics tracked</strong>
            <p className="muted">{data.metrics.length}</p>
          </div>
          <div className="kpi-item">
            <strong>Hours profiled</strong>
            <p className="muted">{data.hourly.length}</p>
          </div>
        </div>
      </section>

      {/* Metric cards */}
      <section style={{ marginBottom: 28 }}>
        <h2 className="panel-title" style={{ marginBottom: 14 }}>Baseline metric means</h2>
        <p className="muted" style={{ marginBottom: 18 }}>
          Each bar shows your average value for that metric. The lighter extension shows ±1 std dev —
          your overload score rises when live readings exceed this range in the overload direction.
        </p>
        <div className="baseline-metric-grid">
          {data.metrics.map((m) => (
            <MetricBar key={m.key} metric={m} maxMean={maxMean} />
          ))}
        </div>
      </section>

      {/* Overload thresholds explanation */}
      <section className="panel" style={{ marginBottom: 28 }}>
        <h2 className="panel-title" style={{ marginBottom: 14 }}>How the alert fires</h2>
        <div className="baseline-threshold-grid">
          <div className="baseline-threshold-card baseline-threshold-critical">
            <div className="baseline-threshold-rule">critical_2x</div>
            <p>Score &gt; 85 for <strong>2 consecutive windows</strong></p>
            <p className="muted" style={{ fontSize: "0.9rem", marginTop: 6 }}>
              Each window is ~10 seconds of live data. Switch apps rapidly for 20+ seconds to trigger.
            </p>
          </div>
          <div className="baseline-threshold-card baseline-threshold-high">
            <div className="baseline-threshold-rule">high_3x</div>
            <p>Score &gt; 70 for <strong>3 consecutive windows</strong></p>
            <p className="muted" style={{ fontSize: "0.9rem", marginTop: 6 }}>
              Sustained moderate overload — stay above the High band for ~30 seconds.
            </p>
          </div>
        </div>
        <div className="baseline-demo-tip">
          <span className="eyebrow" style={{ fontSize: "0.78rem" }}>Demo tip</span>
          <p style={{ marginTop: 8 }}>
            Open <strong>5+ different apps</strong> (Chrome, VS Code, Excel, Terminal, Slack) and
            alt-tab between them rapidly for 30 seconds. Watch the Live Monitor — once the score
            crosses 85 twice in a row the alert fires and an email is sent.
          </p>
        </div>
      </section>

      {/* Hourly charts */}
      {data.hourly.length > 0 && (
        <section className="panel">
          <h2 className="panel-title" style={{ marginBottom: 6 }}>Hourly baseline profile</h2>
          <p className="muted" style={{ marginBottom: 18 }}>
            Your baseline changes through the day — MindScope matches each live window to the right
            hour context before scoring.
          </p>
          <div className="hourly-spark-grid">
            {data.metrics.map((m) => (
              <HourlySparkline key={m.key} metric={m} hourly={data.hourly} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
