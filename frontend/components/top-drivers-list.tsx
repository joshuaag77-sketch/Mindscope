export function TopDriversList({ drivers }: { drivers: string[] }) {
  return (
    <div>
      <h2 className="panel-title">Top drivers</h2>
      <p className="muted">
        The scoring engine surfaces the strongest overload-direction deviations.
      </p>
      <ul className="drivers-list">
        {drivers.map((driver) => (
          <li key={driver}>{driver}</li>
        ))}
      </ul>
    </div>
  );
}
