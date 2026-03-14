export function RiskComposition({
  fragmentation,
  focusInstability,
  interruption,
}: {
  fragmentation: number;
  focusInstability: number;
  interruption: number;
}) {
  const total = Math.max(fragmentation + focusInstability + interruption, 1);
  const fragPct = (fragmentation / total) * 100;
  const focusPct = (focusInstability / total) * 100;
  const interruptPct = (interruption / total) * 100;

  return (
    <div>
      <h2 className="panel-title">Risk composition</h2>
      <p className="muted">How the final score is being driven right now.</p>
      <div className="composition-bar">
        <div className="composition-frag" style={{ width: `${fragPct}%` }} />
        <div className="composition-focus" style={{ width: `${focusPct}%` }} />
        <div className="composition-interrupt" style={{ width: `${interruptPct}%` }} />
      </div>
      <ul className="status-list">
        <li>Fragmentation: {Math.round(fragmentation)}</li>
        <li>Focus instability: {Math.round(focusInstability)}</li>
        <li>Interruption load: {Math.round(interruption)}</li>
      </ul>
    </div>
  );
}
