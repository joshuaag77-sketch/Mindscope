import { AlertStatus } from "@/lib/mock-data";

export function AlertStatusPanel({ alert }: { alert: AlertStatus }) {
  return (
    <div>
      <h2 className="panel-title">Alert status</h2>
      <p className="muted">
        Persistence matters more than a single spike, so the panel shows the
        current streak state.
      </p>
      <ul className="status-list">
        <li>Alert active: {alert.alertActive ? "Yes" : "No"}</li>
        <li>High streak: {alert.consecutiveHighWindows} windows</li>
        <li>Critical streak: {alert.consecutiveCriticalWindows} windows</li>
        <li>Rule: {alert.triggeredRule ?? "Not triggered"}</li>
      </ul>
    </div>
  );
}
