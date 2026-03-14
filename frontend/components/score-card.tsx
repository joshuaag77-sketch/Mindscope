import { StateBandBadge } from "@/components/state-band-badge";

export function OverloadScoreCard({
  score,
  band,
}: {
  score: number;
  band: string;
}) {
  return (
    <aside className="panel score-card">
      <span className="eyebrow">Current window</span>
      <h2 className="panel-title">Overload score</h2>
      <div className="score-value">{Math.round(score)}</div>
      <StateBandBadge band={band} />
      <p className="muted">
        This score is explainable and baseline-relative. It is designed to
        estimate overload risk, not diagnose stress.
      </p>
    </aside>
  );
}
