export function StateBandBadge({ band }: { band: string }) {
  const className =
    band === "Normal"
      ? "badge badge-normal"
      : band === "Sustained Overload Risk"
        ? "badge badge-risk"
        : "badge badge-high";

  return <span className={className}>{band}</span>;
}
