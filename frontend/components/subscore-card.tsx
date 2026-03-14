export function SubscoreCard({
  title,
  score,
  description,
}: {
  title: string;
  score: number;
  description: string;
}) {
  return (
    <div className="subscore-card">
      <div className="muted">{title}</div>
      <div className="subscore-value">{Math.round(score)}</div>
      <p className="muted">{description}</p>
    </div>
  );
}
