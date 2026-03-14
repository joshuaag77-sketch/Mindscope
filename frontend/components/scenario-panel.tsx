const scenarioDescriptions: Record<string, string> = {
  overload:
    "The current normalized pattern sits closest to the overload centroid, so the score gets a small upward adjustment.",
  admin_fragmented:
    "Frequent context shifts and low continuity look closest to fragmented admin work.",
  meeting_heavy:
    "The current profile suggests interruption-heavy coordination rather than deep production work.",
  deep_work:
    "The current pattern resembles sustained, lower-fragmentation work and receives a downward adjustment.",
  procrastination:
    "The current pattern includes low-focus behavior but does not necessarily imply overload.",
  normal_work:
    "The current activity window looks close to the user's expected steady-state pattern.",
};

export function NearestScenarioPanel({ scenario }: { scenario: string }) {
  return (
    <div>
      <h2 className="panel-title">Nearest scenario</h2>
      <p className="muted">
        Scenario centroids act as a lightweight adjustment layer on top of the
        core scoring formula.
      </p>
      <ul className="scenario-list">
        <li>
          <strong>{scenario}</strong>
        </li>
        <li>{scenarioDescriptions[scenario] ?? scenarioDescriptions.normal_work}</li>
      </ul>
    </div>
  );
}
